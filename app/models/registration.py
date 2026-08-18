"""Registration and DailyRanking helpers."""
from datetime import datetime, date
from app.database import query, execute


# ---- Registrations ----
def get_registrations(event_id):
    return query(
        "SELECT r.*, u.username, u.real_name, u.grade, u.avatar_path FROM registrations r "
        "JOIN users u ON r.user_id=u.id WHERE r.event_id=? ORDER BY r.registered_at ASC",
        (event_id,)
    )


def get_registration(event_id, user_id):
    return query(
        "SELECT * FROM registrations WHERE event_id=? AND user_id=?",
        (event_id, user_id), one=True
    )


def create_registration(event_id, user_id, contact_phone=None, contact_email=None, notes=None):
    return execute(
        "INSERT INTO registrations (event_id, user_id, contact_phone, contact_email, notes, registered_at) VALUES (?,?,?,?,?,?)",
        (event_id, user_id, contact_phone, contact_email, notes, datetime.utcnow())
    )


def delete_registration(event_id, user_id):
    execute("DELETE FROM registrations WHERE event_id=? AND user_id=?", (event_id, user_id))


def count_registrations_for_event(event_id):
    r = query("SELECT COUNT(*) as c FROM registrations WHERE event_id=?", (event_id,), one=True)
    return r['c']


def count_all_registrations():
    r = query("SELECT COUNT(*) as c FROM registrations", one=True)
    return r['c']


# ---- Daily Rankings ----
def get_today_ranking(user_id):
    today = date.today().isoformat()
    return query("SELECT * FROM daily_rankings WHERE user_id=? AND snapshot_date=?", (user_id, today), one=True)


def get_today_rankings():
    today = date.today().isoformat()
    return query("SELECT dr.*, u.username, u.real_name, u.grade, u.avatar_path, u.member_type FROM daily_rankings dr JOIN users u ON dr.user_id=u.id WHERE dr.snapshot_date=? ORDER BY dr.rank ASC", (today,))


def recompute_rankings():
    today = date.today().isoformat()
    execute("DELETE FROM daily_rankings WHERE snapshot_date=?", (today,))
    rows = query(
        "SELECT user_id, SUM(total_solved) as total FROM scrape_results GROUP BY user_id ORDER BY total DESC"
    )
    for rank, row in enumerate(rows, 1):
        execute(
            "INSERT INTO daily_rankings (user_id, total_solved, rank, snapshot_date) VALUES (?,?,?,?)",
            (row['user_id'], row['total'], rank, today)
        )
    return len(rows)
