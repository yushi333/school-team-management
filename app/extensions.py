from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
csrf = CSRFProtect()

# Note: database uses Python's built-in sqlite3 (see app/database.py)
#       scheduler is lazy-initialized in app/__init__.py

login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录。'
login_manager.session_protection = 'strong'
