"""Nowcoder (牛客) scraper using problem tracker API.

Endpoint:
    https://www.nowcoder.com/problem/tracker/ranks?userId={uid}

The user enters their numeric UID (not username), e.g. 654602760.
The API returns:
    {"msg":"OK","code":0,"data":{"ranks":[{"count":1205,"name":"..."}]}}
"""

from typing import Optional


class NowcoderScraper:
    PLATFORM_NAME = 'nowcoder'
    API_URL = 'https://www.nowcoder.com/problem/tracker/ranks?userId={uid}'

    def __init__(self, handle: str):
        self.handle = handle.strip()

    def scrape(self) -> dict:
        """Fetch total_solved from Nowcoder tracker API.

        Returns a dict with 'total_solved', 'rating', 'category_stats', 'error'.
        When 'error' is truthy, the orchestrator discards this result to avoid
        overwriting manual data with zeroes.
        """
        import requests

        result = {
            'total_solved': 0,
            'rating': None,
            'category_stats': {},
            'error': None,
        }

        try:
            url = self.API_URL.format(uid=self.handle)
            resp = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.nowcoder.com/',
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if data.get('code') == 0 and data.get('data', {}).get('ranks'):
                rank = data['data']['ranks'][0]
                count = rank.get('count', 0)
                name = rank.get('name', '')
                result['total_solved'] = int(count)
                print(f"[Nowcoder] UID {self.handle} → {name} · {count} 题")
            elif data.get('code') == 0:
                # API OK but no rank data — UID likely invalid or has no problem record
                result['error'] = f"API OK but no rank data for this UID"
                print(f"[Nowcoder] UID {self.handle}: no rank data (invalid UID?)")
            else:
                result['error'] = f"API error code {data.get('code')}: {data.get('msg', 'unknown')}"
                print(f"[Nowcoder] UID {self.handle}: {result['error']}")

        except Exception as e:
            result['error'] = str(e)
            print(f"[Nowcoder] UID {self.handle}: request failed - {e}")

        return result

    def fetch_total_solved(self) -> int:
        """Direct call — used for testing."""
        r = self.scrape()
        return r['total_solved'] if not r.get('error') else 0

    def fetch_category_stats(self) -> dict:
        return {}

    def fetch_rating(self) -> Optional[int]:
        return None
