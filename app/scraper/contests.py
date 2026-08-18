"""Scrape upcoming contests from coding platforms."""

import re
import json
import html
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
TIMEOUT = 15


def scrape_codeforces_contests():
    """Fetch upcoming Codeforces contests via official API."""
    url = 'https://codeforces.com/api/contest.list'
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()
        if data.get('status') != 'OK':
            return []
        contests = []
        for c in data['result']:
            if c['phase'] not in ('BEFORE', 'CODING'):
                continue
            start = datetime.fromtimestamp(c.get('startTimeSeconds', 0), tz=timezone.utc)
            duration = c.get('durationSeconds', 0)
            end = datetime.fromtimestamp(c['startTimeSeconds'] + duration, tz=timezone.utc) if duration else None
            hours = duration // 3600
            mins = (duration % 3600) // 60
            contests.append({
                'platform': 'codeforces',
                'platform_contest_id': str(c['id']),
                'title': c.get('name', 'Codeforces Contest'),
                'contest_url': f'https://codeforces.com/contests/{c["id"]}',
                'start_time': start.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end.strftime('%Y-%m-%d %H:%M:%S') if end else None,
                'description': f'{hours}h{mins}min' if duration else '',
            })
        return contests
    except Exception as e:
        print(f"[ContestScraper] Codeforces error: {e}")
        return []


def scrape_atcoder_contests():
    """Scrape upcoming AtCoder contests from the contest page."""
    url = 'https://atcoder.jp/contests/'
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'lxml')
        contests = []
        for h3 in soup.find_all('h3'):
            text = h3.get_text()
            if 'Upcoming' not in text and '予定' not in text and 'Active' not in text:
                continue
            table = h3.find_next('table')
            if not table:
                continue
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                time_cell = cols[0].get_text(strip=True)
                title_link = cols[1].find('a') if len(cols) > 1 else None
                if not title_link:
                    continue
                title = title_link.get_text(strip=True)
                href = title_link.get('href', '')
                dur_text = cols[2].get_text(strip=True) if len(cols) > 2 else ''

                try:
                    start = datetime.strptime(time_cell, '%Y-%m-%d %H:%M:%S+0900')
                except ValueError:
                    continue

                dur_parts = dur_text.split(':')
                dur_min = int(dur_parts[0]) * 60 + int(dur_parts[1]) if len(dur_parts) == 2 else 120
                end = start + timedelta(minutes=dur_min)

                pid = href.rstrip('/').split('/')[-1]
                contests.append({
                    'platform': 'atcoder',
                    'platform_contest_id': pid,
                    'title': title,
                    'contest_url': f'https://atcoder.jp{href}',
                    'start_time': start.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end.strftime('%Y-%m-%d %H:%M:%S'),
                    'description': dur_text,
                })
            break
        return contests
    except Exception as e:
        print(f"[ContestScraper] AtCoder error: {e}")
        return []


def scrape_nowcoder_contests():
    """Scrape Nowcoder contests from the vip-index page.

    The page is server-rendered (no login / no JS needed): each contest is a
    div.platform-item carrying an HTML-escaped data-json attribute with
    contestName, contestStartTime and contestEndTime (millisecond timestamps).
    """
    contests = []
    try:
        url = 'https://ac.nowcoder.com/acm/contest/vip-index'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'lxml')
        for div in soup.select('div.platform-item.js-item[data-json]'):
            try:
                info = json.loads(html.unescape(div.get('data-json', '')))
            except (json.JSONDecodeError, TypeError):
                continue
            cid = info.get('contestId') or div.get('data-id')
            title = info.get('contestName')
            if not cid or not title:
                continue
            start_ms = info.get('contestStartTime')
            end_ms = info.get('contestEndTime')
            start_time = None
            end_time = None
            if start_ms:
                try:
                    start_time = datetime.fromtimestamp(int(start_ms) / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, OSError):
                    pass
            if end_ms:
                try:
                    end_time = datetime.fromtimestamp(int(end_ms) / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, OSError):
                    pass
            contests.append({
                'platform': 'nowcoder',
                'platform_contest_id': str(cid),
                'title': title,
                'contest_url': f'https://ac.nowcoder.com/acm/contest/{cid}',
                'start_time': start_time,
                'end_time': end_time,
                'description': '',
            })
    except Exception as e:
        print(f"[ContestScraper] Nowcoder error: {e}")
    return contests


def scrape_luogu_contests():
    """Scrape upcoming Luogu contests from the contest list page."""
    contests = []
    try:
        url = 'https://www.luogu.com.cn/contest/list'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        # Luogu injects data as raw JSON in a script tag:
        # <script>{"instance":"main","template":"contest.list",...}</script>
        match = re.search(
            r'<script[^>]*>\s*(\{"instance"\s*:\s*"main"\s*,\s*"template"\s*:\s*"contest\.list".*?\})\s*</script>',
            resp.text, re.DOTALL
        )
        if match:
            try:
                data = json.loads(match.group(1))
                results = data.get('data', {}).get('contests', {}).get('result', [])
                for c in results:
                    if not isinstance(c, dict):
                        continue
                    cid = str(c.get('id', ''))
                    cname = c.get('name', '')
                    st = c.get('startTime')
                    et = c.get('endTime')
                    start_time = datetime.fromtimestamp(st) if st else None
                    end_time = datetime.fromtimestamp(et) if et else None
                    contests.append({
                        'platform': 'luogu',
                        'platform_contest_id': cid,
                        'title': cname,
                        'contest_url': f'https://www.luogu.com.cn/contest/{cid}',
                        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else None,
                        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None,
                        'description': '',
                    })
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"[ContestScraper] Luogu parse error: {e}")
    except Exception as e:
        print(f"[ContestScraper] Luogu error: {e}")
    return contests


def scrape_leetcode_contests():
    """Scrape upcoming LeetCode contests. LeetCode doesn't have a public API
    for upcoming contests, so this returns an empty list for now.
    Admin can manually add LeetCode contests."""
    contests = []
    # LeetCode weekly contest is always Sunday 10:30 AM UTC+8
    # LeetCode biweekly contest is Saturday 10:30 PM UTC+8
    # Since LeetCode doesn't provide an easy API for upcoming contests,
    # we leave this for manual entry.
    return contests


def scrape_lanqiao_contests():
    """Scrape upcoming Lanqiao Cup contests. Lanqiao doesn't have a public API
    or structured contest listing, so this returns an empty list for now.
    Admin can manually add Lanqiao contests."""
    contests = []
    # Lanqiao official site: https://dasai.lanqiao.cn/
    # Contest schedule is usually announced via notices, not a structured listing.
    return contests


def scrape_all_contests():
    """Scrape upcoming contests from all platforms. Returns list of dicts."""
    all_contests = []
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)

    scrapers = [
        ('codeforces', scrape_codeforces_contests),
        ('atcoder', scrape_atcoder_contests),
        ('nowcoder', scrape_nowcoder_contests),
        ('luogu', scrape_luogu_contests),
        ('leetcode', scrape_leetcode_contests),
        ('lanqiao', scrape_lanqiao_contests),
    ]
    for name, scraper in scrapers:
        try:
            contests = scraper()
            for c in contests:
                # Filter: skip contests that ended more than 24h ago
                if c.get('start_time'):
                    try:
                        ct = datetime.strptime(c['start_time'], '%Y-%m-%d %H:%M:%S')
                        if ct < cutoff:
                            continue
                    except ValueError:
                        pass
                c['source'] = 'auto'
                all_contests.append(c)
            print(f"[ContestScraper] {name}: {len(contests)} found")
        except Exception as e:
            print(f"[ContestScraper] {name} failed: {e}")

    return all_contests
