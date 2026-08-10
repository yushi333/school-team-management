"""Platform handle and scrape result helpers."""
import json
from datetime import datetime
from app.database import query, execute


def get_handles(user_id):
    return query("SELECT * FROM platform_handles WHERE user_id=?", (user_id,))


def set_handle(user_id, platform, handle):
    existing = query(
        "SELECT id FROM platform_handles WHERE user_id=? AND platform=?",
        (user_id, platform), one=True
    )
    if existing:
        execute("UPDATE platform_handles SET handle=? WHERE id=?", (handle, existing['id']))
    else:
        execute("INSERT INTO platform_handles (user_id, platform, handle) VALUES (?,?,?)",
                (user_id, platform, handle))


def delete_handle(user_id, platform):
    execute("DELETE FROM platform_handles WHERE user_id=? AND platform=?", (user_id, platform))


def get_scrape_results(user_id):
    return query("SELECT * FROM scrape_results WHERE user_id=?", (user_id,))


def upsert_scrape_result(user_id, platform, total_solved=0, rating=None, category_stats=None):
    existing = query(
        "SELECT id FROM scrape_results WHERE user_id=? AND platform=?",
        (user_id, platform), one=True
    )
    cat_json = json.dumps(category_stats, ensure_ascii=False) if category_stats else None
    if existing:
        execute(
            "UPDATE scrape_results SET total_solved=?, rating=?, category_stats=?, scraped_at=? WHERE id=?",
            (total_solved, rating, cat_json, datetime.utcnow(), existing['id'])
        )
    else:
        execute(
            "INSERT INTO scrape_results (user_id, platform, total_solved, rating, category_stats, scraped_at) VALUES (?,?,?,?,?,?)",
            (user_id, platform, total_solved, rating, cat_json, datetime.utcnow())
        )


def get_category_dict(category_stats_json):
    if category_stats_json:
        try:
            return json.loads(category_stats_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}
