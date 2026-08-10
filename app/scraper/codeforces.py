"""Codeforces scraper using the official API."""

import time
from typing import Optional
from app.scraper.base import AbstractScraper
from app.scraper.category import normalize_tags


class CodeforcesScraper(AbstractScraper):
    PLATFORM_NAME = 'codeforces'
    BASE_URL = 'https://codeforces.com/api/'

    def fetch_total_solved(self) -> int:
        """Count unique accepted problems via CF API."""
        accepted = self._get_accepted_submissions()
        # Deduplicate by (contestId, index)
        unique_problems = set()
        for sub in accepted:
            problem = sub.get('problem', {})
            key = (problem.get('contestId'), problem.get('index'))
            if key[0] and key[1]:
                unique_problems.add(key)
        return len(unique_problems)

    def fetch_category_stats(self) -> dict:
        """Aggregate problem tags from accepted submissions."""
        accepted = self._get_accepted_submissions()
        tag_counts = {}
        seen = set()
        for sub in accepted:
            problem = sub.get('problem', {})
            key = (problem.get('contestId'), problem.get('index'))
            if key in seen or not key[0] or not key[1]:
                continue
            seen.add(key)
            for tag in problem.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return normalize_tags(tag_counts)

    def fetch_rating(self) -> Optional[int]:
        """Fetch user rating from CF API."""
        try:
            url = f'{self.BASE_URL}user.info?handles={self.handle}'
            resp = self._get(url)
            data = resp.json()
            if data.get('status') == 'OK':
                users = data.get('result', [])
                if users:
                    return users[0].get('rating')
        except Exception:
            pass
        return None

    def _get_accepted_submissions(self) -> list:
        """Fetch all accepted submissions from the CF API."""
        url = f'{self.BASE_URL}user.status?handle={self.handle}&from=1&count=10000'
        resp = self._get(url)
        data = resp.json()
        if data.get('status') != 'OK':
            raise Exception(f"CF API error: {data.get('comment', 'unknown')}")
        submissions = data.get('result', [])
        return [s for s in submissions if s.get('verdict') == 'OK']

    def scrape(self) -> dict:
        # Rate limiting: CF API requires ~1 request per 2 seconds
        time.sleep(0.5)
        return super().scrape()
