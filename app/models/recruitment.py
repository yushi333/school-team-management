"""TeamRecruitment helpers."""
from datetime import datetime
from app.database import query, execute


# ---- Team Recruitments ----
def get_recruitments(wuyu_type=None, order_by='created_at DESC'):
    sql = ("SELECT tr.*, u.real_name as poster_name, u.username as poster_username, "
           "(SELECT COUNT(*) FROM recruitment_members rm WHERE rm.recruitment_id=tr.id) as member_count "
           "FROM team_recruitments tr LEFT JOIN users u ON tr.posted_by=u.id")
    params = []
    if wuyu_type:
        sql += " WHERE tr.wuyu_type=?"
        params.append(wuyu_type)
    sql += f" ORDER BY {order_by}"
    return query(sql, params)


def get_recruitment(rid):
    return query(
        "SELECT tr.*, u.real_name as poster_name, u.username as poster_username, "
        "(SELECT COUNT(*) FROM recruitment_members rm WHERE rm.recruitment_id=tr.id) as member_count "
        "FROM team_recruitments tr LEFT JOIN users u ON tr.posted_by=u.id WHERE tr.id=?",
        (rid,), one=True)


def create_recruitment(title, competition_type, recruit_count, requirement, wuyu_type,
                       description=None, posted_by=None, is_open=1):
    return execute(
        "INSERT INTO team_recruitments (title, competition_type, recruit_count, requirement, wuyu_type, description, is_open, posted_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (title, competition_type, recruit_count, requirement, wuyu_type, description,
         1 if is_open else 0, posted_by, datetime.utcnow()))


def update_recruitment(rid, **kwargs):
    if not kwargs:
        return
    sets = ', '.join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [rid]
    execute(f"UPDATE team_recruitments SET {sets} WHERE id=?", values)


def delete_recruitment(rid):
    execute("DELETE FROM team_recruitments WHERE id=?", (rid,))  # members CASCADE


def count_recruitments():
    r = query("SELECT COUNT(*) as c FROM team_recruitments", one=True)
    return r['c']


# ---- Recruitment Members ----
def get_members(recruitment_id):
    return query(
        "SELECT rm.*, u.username, u.real_name, u.grade FROM recruitment_members rm "
        "JOIN users u ON rm.user_id=u.id WHERE rm.recruitment_id=? ORDER BY rm.joined_at ASC",
        (recruitment_id,))


def get_member(recruitment_id, user_id):
    return query("SELECT * FROM recruitment_members WHERE recruitment_id=? AND user_id=?",
                 (recruitment_id, user_id), one=True)


def join_recruitment(recruitment_id, user_id):
    return execute(
        "INSERT INTO recruitment_members (recruitment_id, user_id, joined_at) VALUES (?,?,?)",
        (recruitment_id, user_id, datetime.utcnow()))


def leave_recruitment(recruitment_id, user_id):
    execute("DELETE FROM recruitment_members WHERE recruitment_id=? AND user_id=?", (recruitment_id, user_id))


def count_members(recruitment_id):
    r = query("SELECT COUNT(*) as c FROM recruitment_members WHERE recruitment_id=?", (recruitment_id,), one=True)
    return r['c']
