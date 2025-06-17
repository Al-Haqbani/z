import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from utils.http_utils import request_with_backoff


class ReconSearcher:
    """Discover and verify URLs referencing a company or domain."""

    WAYBACK_URL = "https://web.archive.org/cdx/search/cdx"
    DEFAULT_SERVICES = [
        "slack.com",
        "docs.google.com",
        "groups.google.com",
        "drive.google.com",
    ]

    def __init__(self, services=None, silent=False, **_):
        self.silent = silent
        self.services = services or self._load_services()

    @classmethod
    def _load_services(cls) -> List[str]:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "recon_services.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return data.get("services", cls.DEFAULT_SERVICES)
            except Exception:
                pass
        return list(cls.DEFAULT_SERVICES)

    def _query_wayback(self, keyword: str, domain: str) -> List[Dict[str, str]]:
        params = {
            "url": f"*{domain}*{keyword}*",
            "output": "json",
            "fl": "original,statuscode",
            "collapse": "urlkey",
            "limit": 50,
        }
        urls = []
        try:
            resp = request_with_backoff(self.WAYBACK_URL, params=params)
            if resp and resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data[0], list) and data[0][0] == "original":
                    data = data[1:]
                for row in data:
                    if len(row) >= 2:
                        urls.append({"url": row[0], "archive_status": row[1], "domain": domain, "source": "archive"})
        except Exception as exc:
            if not self.silent:
                print(f"Wayback query failed for {domain}: {exc}")
        return urls

    def _verify_live(self, items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        results = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            future_map = {
                ex.submit(request_with_backoff, it["url"], timeout=5, retries=1): it
                for it in items
            }
            for fut in as_completed(future_map):
                item = future_map[fut]
                try:
                    resp = fut.result()
                    status = resp.status_code if resp else None
                except Exception:
                    status = None
                item["live_status"] = status
                results.append(item)
        return results

    def search(self, keyword: str, **kwargs) -> List[Dict[str, str]]:
        all_urls = []
        for domain in self.services:
            all_urls.extend(self._query_wayback(keyword, domain))
        if not all_urls:
            return []
        verified = self._verify_live(all_urls)
        results = [
            {
                "source": "Recon",
                "file": item["url"],
                "leak_type": f"URL ({item['domain']})",
                "value": str(item.get("live_status")),
                "status_code": item.get("live_status"),
                "discovery": item["source"],
            }
            for item in verified
        ]
        return results
