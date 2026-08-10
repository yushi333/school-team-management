"""Abstract base class for platform scrapers."""

from abc import ABC, abstractmethod
import time
import requests
from typing import Optional


class AbstractScraper(ABC):
    """Base class for all platform scrapers."""

    PLATFORM_NAME: str = ""
    BASE_URL: str = ""
    REQUEST_TIMEOUT: int = 15
    MAX_RETRIES: int = 2
    RETRY_DELAY: float = 2.0

    def __init__(self, handle: str):
        self.handle = handle.strip()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

    @abstractmethod
    def fetch_total_solved(self) -> int:
        """Return the number of problems solved by this user."""
        ...

    @abstractmethod
    def fetch_category_stats(self) -> dict:
        """Return dict like {'DP': 15, 'Greedy': 8, ...}."""
        ...

    def fetch_rating(self) -> Optional[int]:
        """Override to return the platform rating (e.g., CF rating)."""
        return None

    def scrape(self) -> dict:
        """Run the full scrape and return structured result."""
        result = {
            'platform': self.PLATFORM_NAME,
            'total_solved': 0,
            'rating': None,
            'category_stats': {},
            'error': None,
        }
        try:
            result['total_solved'] = self._retry(self.fetch_total_solved, 'total_solved')
        except Exception as e:
            result['error'] = f"total_solved failed: {e}"

        try:
            result['category_stats'] = self._retry(self.fetch_category_stats, 'category_stats')
        except Exception as e:
            if not result['error']:
                result['error'] = f"category_stats failed: {e}"

        try:
            result['rating'] = self.fetch_rating()
        except Exception:
            pass

        return result

    def _retry(self, func, label: str):
        """Retry a function with exponential backoff."""
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    time.sleep(self.RETRY_DELAY * (2 ** (attempt - 1)))
                return func()
            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                print(f"[{self.PLATFORM_NAME}] {label} attempt {attempt + 1} failed: {e}")
                continue
        raise last_error or Exception(f"All retries exhausted for {label}")

    def _get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with timeout."""
        return self.session.get(url, timeout=self.REQUEST_TIMEOUT, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.handle})>"
