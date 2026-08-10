"""User model using sqlite3 backend."""
import hashlib
import os
from datetime import datetime
from flask_login import UserMixin
from app.database import query, execute


class User(UserMixin):
    """User class compatible with Flask-Login. Wraps a dict row."""

    def __init__(self, row_dict):
        self._data = row_dict

    @property
    def id(self):
        return self._data['id']

    @property
    def username(self):
        return self._data['username']

    @property
    def role(self):
        return self._data.get('role', 'member')

    @property
    def grade(self):
        return self._data.get('grade')

    @property
    def real_name(self):
        return self._data.get('real_name')

    @property
    def created_at(self):
        return self._data.get('created_at')

    def is_admin(self):
        return self.role == 'admin'

    @staticmethod
    def hash_password(password):
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + ':' + key.hex()

    @staticmethod
    def check_password(stored, password):
        try:
            salt_hex, key_hex = stored.split(':')
            salt = bytes.fromhex(salt_hex)
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return key.hex() == key_hex
        except (ValueError, AttributeError):
            return False

    def set_password(self, password):
        h = self.hash_password(password)
        execute("UPDATE users SET password_hash=? WHERE id=?", (h, self._data['id']))
        self._data['password_hash'] = h

    def check_pw(self, password):
        return self.check_password(self._data['password_hash'], password)

    def platform_handles(self):
        rows = query("SELECT * FROM platform_handles WHERE user_id=?", (self._data['id'],))
        return rows

    def get_handle(self, platform):
        r = query("SELECT handle FROM platform_handles WHERE user_id=? AND platform=?",
                  (self._data['id'], platform), one=True)
        return r['handle'] if r else None

    def scrape_results(self):
        return query("SELECT * FROM scrape_results WHERE user_id=?", (self._data['id'],))

    @staticmethod
    def find_by_id(user_id):
        r = query("SELECT * FROM users WHERE id=?", (user_id,), one=True)
        return User(r) if r else None

    @staticmethod
    def find_by_username(username):
        r = query("SELECT * FROM users WHERE username=?", (username,), one=True)
        return User(r) if r else None

    @staticmethod
    def create(username, password, role='member', real_name=None, grade=None):
        h = User.hash_password(password)
        uid = execute(
            "INSERT INTO users (username, password_hash, role, real_name, grade, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (username, h, role, real_name, grade, datetime.utcnow(), datetime.utcnow())
        )
        return User.find_by_id(uid)

    @staticmethod
    def all(order_by='created_at DESC'):
        rows = query(f"SELECT * FROM users ORDER BY {order_by}")
        return [User(r) for r in rows]

    @staticmethod
    def count():
        r = query("SELECT COUNT(*) as c FROM users", one=True)
        return r['c']

    def update(self, **kwargs):
        sets = ', '.join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values())
        execute(f"UPDATE users SET {sets}, updated_at=? WHERE id=?", values + [datetime.utcnow(), self._data['id']])
        for k, v in kwargs.items():
            self._data[k] = v

    def delete(self):
        execute("DELETE FROM users WHERE id=?", (self._data['id'],))

    @staticmethod
    def create_table():
        pass  # handled in database.py


# Flask-Login user loader
def load_user(user_id):
    return User.find_by_id(int(user_id))
