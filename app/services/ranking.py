from datetime import date
from app.models.registration import recompute_rankings as _recompute


def recompute_rankings():
    """Recompute the daily rankings snapshot from current scrape results."""
    count = _recompute()
    print(f"[Ranking] Recalculated rankings for {count} users on {date.today()}")
