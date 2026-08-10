"""Luogu (洛谷) scraper using page JSON extraction."""

import re
import json
from typing import Optional
from app.scraper.base import AbstractScraper


class LuoguScraper(AbstractScraper):
    PLATFORM_NAME = 'luogu'
    BASE_URL = 'https://www.luogu.com.cn'

    def fetch_total_solved(self) -> int:
        """Extract passed problem count from user page."""
        data = self._extract_user_data()
        if data:
            return data.get('passedProblemCount', 0) or data.get('submittedProblemCount', 0) or 0
        return 0

    def fetch_category_stats(self) -> dict:
        """Try to extract problem tags from user data.

        Note: Luogu doesn't expose per-tag breakdown on the user profile page.
        We attempt to extract it if available; otherwise return empty dict.
        Category stats for Luogu are best obtained by scraping the user's
        passed problems list, which is expensive. This is done in the
        orchestrator on a weekly basis.
        """
        data = self._extract_user_data()
        if not data:
            return {}

        # Try to get tag info from the user data
        tags = data.get('tags', {})
        if isinstance(tags, dict):
            result = {}
            for tag, count in tags.items():
                if isinstance(count, (int, float)) and count > 0:
                    result[tag] = int(count)
            if result:
                return result

        # Fallback: try passed problems breakdown
        passed_problems = data.get('passedProblems', [])
        if passed_problems:
            # Unfortunately this usually gives problem IDs, not tags
            pass

        return {}

    def fetch_rating(self) -> Optional[int]:
        """Luogu doesn't have a numeric rating like CF."""
        data = self._extract_user_data()
        if data:
            return data.get('rating')
        return None

    def _extract_user_data(self) -> Optional[dict]:
        """Extract the JSON user data from the Luogu page."""
        try:
            url = f'{self.BASE_URL}/user/{self.handle}'
            resp = self._get(url)
            # Luogu injects user data as JSON in a script tag
            # Look for: window._feInjection or JSON.parse('...')
            patterns = [
                r'window\._feInjection\s*=\s*(\{.*?\});\s*\n',
                r'JSON\.parse\(\'(.+?)\'\)',
                r'decodeURIComponent\("(.+?)"\)',
            ]
            for pattern in patterns:
                match = re.search(pattern, resp.text, re.DOTALL)
                if match:
                    try:
                        json_str = match.group(1)
                        # Try to parse directly
                        data = json.loads(json_str)
                        # Walk into the data to find user info
                        if 'currentData' in data:
                            return data['currentData'].get('user', {})
                        if 'user' in data:
                            return data['user']
                        return data
                    except (json.JSONDecodeError, KeyError):
                        continue

            # Fallback: look for specific data in the page
            match = re.search(r'"passedProblemCount":(\d+)', resp.text)
            if match:
                return {'passedProblemCount': int(match.group(1))}

        except Exception as e:
            print(f"[Luogu] Error extracting data for {self.handle}: {e}")

        return None
