"""Nowcoder (牛客) scraper using page DOM parsing."""

from typing import Optional
from bs4 import BeautifulSoup
from app.scraper.base import AbstractScraper


class NowcoderScraper(AbstractScraper):
    PLATFORM_NAME = 'nowcoder'
    BASE_URL = 'https://ac.nowcoder.com'

    def fetch_total_solved(self) -> int:
        """Extract practice problem count from profile page."""
        try:
            url = f'{self.BASE_URL}/acm/contest/profile/{self.handle}'
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, 'lxml')

            # Look for solved/accepted count in stat elements
            # Common patterns in Nowcoder profile pages:
            # - A number in a stat card
            # - Text like "已解决 X 题"
            text = soup.get_text()

            import re
            # Try "已解决" pattern
            match = re.search(r'已解决[：:\s]*(\d+)', text)
            if match:
                return int(match.group(1))

            # Try "通过" pattern
            match = re.search(r'通过[：:\s]*(\d+)', text)
            if match:
                return int(match.group(1))

            # Try finding numbers near "AC" or "Solved"
            match = re.search(r'(\d+)\s*(?:题|Problem|AC)', text)
            if match:
                return int(match.group(1))

        except Exception as e:
            print(f"[Nowcoder] Error for handle {self.handle}: {e}")

        return 0

    def fetch_category_stats(self) -> dict:
        """Nowcoder tag data is limited on profile pages.

        The platform groups problems by contest rather than algorithm tags.
        We return an empty dict for now; if tag data becomes available
        via contest history parsing, it can be added later.
        """
        return {}

    def fetch_rating(self) -> Optional[int]:
        """Nowcoder has a rating system; try to extract it."""
        try:
            url = f'{self.BASE_URL}/acm/contest/profile/{self.handle}'
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, 'lxml')
            text = soup.get_text()

            import re
            match = re.search(r'(?:rating|Rating|等级)[：:\s]*(\d+)', text)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None
