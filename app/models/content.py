"""Tutorial, OnlineContest, CampusEvent helpers."""
from datetime import datetime
from app.database import query, execute


# ---- Tutorials ----
def get_tutorials(order_by='created_at DESC'):
    return query(f"SELECT t.*, u.real_name as poster_name, u.username as poster_username FROM tutorials t LEFT JOIN users u ON t.posted_by=u.id ORDER BY {order_by}")


def get_tutorial(tid):
    return query("SELECT t.*, u.real_name as poster_name, u.username as poster_username FROM tutorials t LEFT JOIN users u ON t.posted_by=u.id WHERE t.id=?", (tid,), one=True)


def create_tutorial(title, description, video_url, posted_by):
    return execute("INSERT INTO tutorials (title, description, video_url, posted_by, created_at) VALUES (?,?,?,?,?)",
                   (title, description, video_url, posted_by, datetime.utcnow()))


def delete_tutorial(tid):
    execute("DELETE FROM tutorials WHERE id=?", (tid,))


def count_tutorials():
    r = query("SELECT COUNT(*) as c FROM tutorials", one=True)
    return r['c']


# ---- Online Contests ----
def get_online_contests(order_by='start_time ASC'):
    return query(f"SELECT * FROM online_contests ORDER BY {order_by}")


def create_online_contest(title, platform, contest_url, start_time, end_time, description, posted_by,
                          source='manual', platform_contest_id=None):
    return execute(
        "INSERT INTO online_contests (title, platform, contest_url, start_time, end_time, description, source, platform_contest_id, posted_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (title, platform, contest_url, start_time, end_time, description, source, platform_contest_id, posted_by, datetime.utcnow())
    )


def upsert_online_contest(platform, platform_contest_id, title, contest_url, start_time, end_time, description):
    """Insert or update an auto-scraped contest, keyed by platform + platform_contest_id."""
    existing = query(
        "SELECT id FROM online_contests WHERE platform=? AND platform_contest_id=?",
        (platform, platform_contest_id), one=True
    )
    if existing:
        execute(
            "UPDATE online_contests SET title=?, contest_url=?, start_time=?, end_time=?, description=? WHERE id=?",
            (title, contest_url, start_time, end_time, description, existing['id'])
        )
        return existing['id']
    else:
        return execute(
            "INSERT INTO online_contests (title, platform, contest_url, start_time, end_time, description, source, platform_contest_id, created_at) VALUES (?,?,?,?,?,?,'auto',?,?)",
            (title, platform, contest_url, start_time, end_time, description, platform_contest_id, datetime.utcnow())
        )


def delete_online_contest(cid):
    execute("DELETE FROM online_contests WHERE id=?", (cid,))


def count_online_contests():
    r = query("SELECT COUNT(*) as c FROM online_contests", one=True)
    return r['c']


def cleanup_old_contests():
    """Delete auto-scraped contests that ended more than 3 days ago."""
    execute(
        "DELETE FROM online_contests WHERE source='auto' AND end_time IS NOT NULL AND end_time < datetime('now','-3 days')"
    )


# ---- Campus Events ----
def get_campus_events(order_by='event_date ASC'):
    rows = query(f"SELECT ce.*, u.real_name as poster_name, u.username as poster_username FROM campus_events ce LEFT JOIN users u ON ce.posted_by=u.id ORDER BY {order_by}")
    return rows


def get_campus_event(eid):
    return query("SELECT ce.*, u.real_name as poster_name, u.username as poster_username FROM campus_events ce LEFT JOIN users u ON ce.posted_by=u.id WHERE ce.id=?", (eid,), one=True)


def create_campus_event(title, content, location, event_date, registration_deadline, is_open, posted_by, wuyu_type='zhiyu'):
    return execute(
        "INSERT INTO campus_events (title, content, location, event_date, registration_deadline, is_open, wuyu_type, posted_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (title, content, location, event_date, registration_deadline, 1 if is_open else 0, wuyu_type, posted_by, datetime.utcnow())
    )


def update_campus_event(eid, **kwargs):
    if not kwargs:
        return
    sets = ', '.join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [eid]
    execute(f"UPDATE campus_events SET {sets} WHERE id=?", values)


def delete_campus_event(eid):
    execute("DELETE FROM campus_events WHERE id=?", (eid,))


def count_campus_events():
    r = query("SELECT COUNT(*) as c FROM campus_events", one=True)
    return r['c']


# ---- Awards ----
def get_awards(order_by='created_at DESC'):
    return query(f"SELECT a.*, u.real_name as uploader_name, u.username as uploader_username FROM awards a LEFT JOIN users u ON a.uploaded_by=u.id ORDER BY {order_by}")


def get_award(aid):
    return query("SELECT a.*, u.real_name as uploader_name, u.username as uploader_username FROM awards a LEFT JOIN users u ON a.uploaded_by=u.id WHERE a.id=?", (aid,), one=True)


def create_award(title, description, file_path, file_type, original_filename, uploaded_by, wuyu_type='zhiyu'):
    return execute(
        "INSERT INTO awards (title, description, file_path, file_type, original_filename, wuyu_type, uploaded_by, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (title, description, file_path, file_type, original_filename, wuyu_type, uploaded_by, datetime.utcnow())
    )


def delete_award(aid):
    execute("DELETE FROM awards WHERE id=?", (aid,))


def count_awards():
    r = query("SELECT COUNT(*) as c FROM awards", one=True)
    return r['c']
