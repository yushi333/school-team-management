"""Orchestrator: coordinate scraping across all platforms for all users."""

import json
from datetime import datetime
from app.models.user import User
from app.models.platform import get_handles, upsert_scrape_result
from app.models.content import upsert_online_contest, cleanup_old_contests
from app.scraper.codeforces import CodeforcesScraper
from app.scraper.atcoder import AtCoderScraper
from app.scraper.luogu import LuoguScraper
from app.scraper.nowcoder import NowcoderScraper
from app.scraper.contests import scrape_all_contests


# Platforms that can be auto-scraped (leetcode/lanqiao are manual entry)
SCRAPER_MAP = {
    'codeforces': CodeforcesScraper,
    'atcoder': AtCoderScraper,
    'luogu': LuoguScraper,
    'nowcoder': NowcoderScraper,
}


def scrape_all():
    """Main daily job: scrape user stats + upcoming contests + recompute rankings."""
    print(f"[Scraper] Starting daily scrape at {datetime.utcnow()}")
    scrape_all_users()
    scrape_contests()
    from app.models.registration import recompute_rankings
    recompute_rankings()
    print(f"[Scraper] Daily job complete.")


def scrape_all_users():
    """Scrape all platforms for all users who have set handles."""
    print(f"[Scraper] --- User stats scraping ---")

    users = User.all()
    total_handles = 0
    success_count = 0
    error_count = 0

    for user in users:
        handles = get_handles(user.id)
        if not handles:
            continue

        for handle in handles:
            platform = handle['platform']
            handle_value = handle['handle'].strip()
            if not handle_value:
                continue

            total_handles += 1
            scraper_cls = SCRAPER_MAP.get(platform)
            if not scraper_cls:
                continue

            try:
                scraper = scraper_cls(handle_value)
                result = scraper.scrape()
                if result.get('error'):
                    error_count += 1
                else:
                    success_count += 1
                    _save_result(user.id, platform, result)
            except Exception as e:
                print(f"[Scraper] Error {platform}/{handle_value}: {e}")
                error_count += 1

    print(f"[Scraper] User stats done. Handles: {total_handles}, OK: {success_count}, Err: {error_count}")


def scrape_contests():
    """Scrape upcoming contests from all platforms and save to DB."""
    print(f"[Scraper] --- Contest scraping ---")
    try:
        contests = scrape_all_contests()
        saved = 0
        for c in contests:
            upsert_online_contest(
                platform=c['platform'],
                platform_contest_id=c.get('platform_contest_id', ''),
                title=c['title'],
                contest_url=c.get('contest_url', ''),
                start_time=c.get('start_time'),
                end_time=c.get('end_time'),
                description=c.get('description', ''),
            )
            saved += 1
        cleanup_old_contests()
        print(f"[Scraper] Contests saved: {saved}")
    except Exception as e:
        print(f"[Scraper] Contest scraping error: {e}")


def scrape_single_user(user_id: int):
    """Scrape all platforms for a single user. Useful for testing."""
    user = User.find_by_id(user_id)
    if not user:
        print(f"[Scraper] User {user_id} not found")
        return

    handles = get_handles(user_id)
    for handle in handles:
        platform = handle['platform']
        handle_value = handle['handle'].strip()
        if not handle_value:
            continue

        scraper_cls = SCRAPER_MAP.get(platform)
        if not scraper_cls:
            continue

        try:
            scraper = scraper_cls(handle_value)
            result = scraper.scrape()
            if not result.get('error'):
                _save_result(user_id, platform, result)
            print(f"[Scraper] {platform}: {result.get('total_solved', 0)} solved")
        except Exception as e:
            print(f"[Scraper] Error for {platform}: {e}")


def _save_result(user_id: int, platform: str, result: dict):
    """Save or update a ScrapeResult row."""
    category_stats = result.get('category_stats', None)
    upsert_scrape_result(
        user_id=user_id,
        platform=platform,
        total_solved=result.get('total_solved', 0),
        rating=result.get('rating'),
        category_stats=category_stats,
    )
