"""AtCoder scraper using the Kenkoooo (AtCoder Problems) API."""

from typing import Optional
from app.scraper.base import AbstractScraper


class AtCoderScraper(AbstractScraper):
    PLATFORM_NAME = 'atcoder'
    # Kenkoooo unofficial API - reliable and widely used
    API_BASE = 'https://kenkoooo.com/atcoder/atcoder-api/v3/'

    def fetch_total_solved(self) -> int:
        """Fetch AC count from AtCoder Problems API."""
        url = f'{self.API_BASE}user/ac_count?user={self.handle}'
        resp = self._get(url)
        data = resp.json()
        return data.get('count', 0)

    def fetch_category_stats(self) -> dict:
        """AtCoder doesn't have algorithm tags. Return difficulty distribution instead."""
        url = f'{self.API_BASE}user/ac_count?user={self.handle}'
        resp = self._get(url)
        data = resp.json()
        # This API may return per-difficulty counts
        # Remove 'count' to get only difficulty keys
        stats = {}
        for key, value in data.items():
            if key != 'count' and isinstance(value, (int, float)):
                if value > 0:
                    stats[f'Diff-{key}'] = int(value)
        return stats

    def fetch_rating(self) -> Optional[int]:
        """Try to get AtCoder rating from profile page."""
        try:
            url = f'https://atcoder.jp/users/{self.handle}'
            resp = self._get(url)
            # Simple regex-based extraction from profile page
            import re
            # Look for rating in the page
            match = re.search(r'<th[^>]*>Rating</th>\s*<td[^>]*>.*?(\d+)', resp.text, re.DOTALL)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None
