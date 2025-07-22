import random
import time
import os
from typing import List, Dict, Optional

from utils.http_utils import request_with_backoff, save_screenshot

class ShortURLSearcher:
    """Search GrayHatWarfare short URLs for company/domain matches."""

    BASE_URL = "https://shorteners.grayhatwarfare.com/api"

    def __init__(self, token: Optional[str] = None, silent: bool = False, **_):
        self.token = token
        self.silent = silent

    def search(
        self,
        keyword: str,
        *,
        domains: Optional[List[str]] = None,
        result_callback=None,
        progress_callback=None,
        screenshot_dir=None,
        screenshot_prefix=None,
        **kwargs,
    ) -> List[Dict[str, str]]:
        if not self.token:
            if not self.silent:
                print("GrayHat shorteners API token required")
            return []
        queries = []
        if keyword:
            queries.append(keyword)
        if domains:
            queries.extend(domains)
        leaks = []
        count = 0
        for q in queries:
            page = 1
            while True:
                params = {"search": q, "page": page, "key": self.token}
                resp = request_with_backoff(self.BASE_URL, params=params)
                if not resp or resp.status_code != 200:
                    if not self.silent:
                        status = resp.status_code if resp else 'timeout'
                        print(f"Shorteners API failed: {status}")
                    break
                data = resp.json()
                items = data.get("data") or data.get("results") or []
                if not items:
                    break
                total = len(items)
                for item in items:
                    count += 1
                    short_url = item.get("short") or item.get("short_url")
                    long_url = item.get("url") or item.get("long_url")
                    created = (
                        item.get("created")
                        or item.get("created_at")
                        or item.get("timestamp")
                    )
                    size = item.get("size") or item.get("length") or item.get("bytes")
                    match_type = "none"
                    matched = False
                    if keyword and long_url and keyword.lower() in long_url.lower():
                        match_type = "company"
                        matched = True
                    if domains and long_url:
                        for dom in domains:
                            if dom.lower() in long_url.lower():
                                match_type = "domain"
                                matched = True
                                break
                    record = {
                        "source": "GrayHatShort",
                        "file": short_url or "",
                        "leak_type": "short-url",
                        "value": long_url or "",
                        "match": match_type,
                    }
                    if screenshot_dir and long_url:
                        shot = save_screenshot(long_url, screenshot_dir, silent=self.silent)
                        if shot:
                            name = os.path.basename(shot)
                            if screenshot_prefix:
                                record["screenshot"] = screenshot_prefix + name
                            else:
                                record["screenshot"] = shot
                    if created:
                        record["created"] = created
                    if size:
                        record["size"] = size
                    leaks.append(record)
                    if result_callback:
                        result_callback(record, count)
                    if progress_callback:
                        progress_callback({"index": count, "total": total})
                page += 1
                if page > data.get("total_pages", page):
                    break
                time.sleep(random.uniform(1, 2))
        return leaks
