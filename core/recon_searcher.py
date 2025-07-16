import os
import json
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from utils.http_utils import request_with_backoff
from utils.subdomain_enum import enumerate_subdomains
from is_scanner.js_scanner import run_smart_scan


class ReconSearcher:
    """Discover and verify URLs referencing a company or domain."""

    WAYBACK_URL = "https://web.archive.org/cdx/search/cdx"
    DEFAULT_SERVICES = [
        "slack.com",
        "docs.google.com",
        "groups.google.com",
        "drive.google.com",
    ]

    def __init__(self, services=None, silent=False, github_token=None, gitlab_token=None,
                 scan_subdomains=False, scan_js=True, **_):
        self.silent = silent
        self.github_token = github_token
        self.gitlab_token = gitlab_token
        self.scan_subdomains = scan_subdomains
        self.scan_js = scan_js
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

    def _headers(self, token: str | None = None) -> Dict[str, str]:
        headers = {"User-Agent": random.choice(["Mozilla/5.0", "Safari/537", "Chrome/97"]) }
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _query_github(self, keyword: str) -> List[Dict[str, str]]:
        if not self.github_token:
            return []
        url = "https://api.github.com/search/code"
        params = {"q": keyword, "per_page": 20}
        urls: List[Dict[str, str]] = []
        try:
            resp = request_with_backoff(url, params=params, headers=self._headers(self.github_token))
            if resp and resp.status_code == 200:
                for item in resp.json().get("items", []):
                    raw_url = item.get("html_url", "").replace("blob/", "raw/")
                    f_resp = request_with_backoff(raw_url, headers=self._headers(self.github_token))
                    if f_resp and f_resp.status_code == 200:
                        for m in re.findall(r"https?://[^\s'\"]+", f_resp.text):
                            if keyword.lower() in m.lower():
                                urls.append({"url": m, "domain": "github", "source": "github"})
        except Exception as exc:
            if not self.silent:
                print(f"GitHub recon error: {exc}")
        return urls

    def _query_gitlab(self, keyword: str) -> List[Dict[str, str]]:
        if not self.gitlab_token:
            return []
        url = "https://gitlab.com/api/v4/search"
        params = {"scope": "blobs", "search": keyword}
        urls: List[Dict[str, str]] = []
        try:
            resp = request_with_backoff(url, params=params, headers=self._headers(self.gitlab_token))
            if resp and resp.status_code == 200:
                for item in resp.json():
                    file_url = item.get("url")
                    if not file_url:
                        continue
                    f_resp = request_with_backoff(file_url, headers=self._headers(self.gitlab_token))
                    if f_resp and f_resp.status_code == 200:
                        for m in re.findall(r"https?://[^\s'\"]+", f_resp.text):
                            if keyword.lower() in m.lower():
                                urls.append({"url": m, "domain": "gitlab", "source": "gitlab"})
        except Exception as exc:
            if not self.silent:
                print(f"GitLab recon error: {exc}")
        return urls

    def _verify_live(self, items: List[Dict[str, str]], progress_callback=None) -> List[Dict[str, str]]:
        results = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            future_map = {
                ex.submit(request_with_backoff, it["url"], timeout=5, retries=1): it
                for it in items
            }
            total = len(future_map)
            for idx, fut in enumerate(as_completed(future_map), 1):
                item = future_map[fut]
                try:
                    resp = fut.result()
                    status = resp.status_code if resp else None
                except Exception:
                    status = None
                item["live_status"] = status
                item["timestamp"] = int(time.time())
                results.append(item)
                if progress_callback:
                    progress_callback({"verify_index": idx, "verify_total": total})
        return results

    def search(
        self,
        keyword: str,
        result_callback=None,
        progress_callback=None,
        **kwargs,
    ) -> List[Dict[str, str]]:
        all_urls = []
        for idx, domain in enumerate(self.services, 1):
            if progress_callback:
                progress_callback({"domain": domain, "index": idx, "total": len(self.services)})
            all_urls.extend(self._query_wayback(keyword, domain))
        all_urls.extend(self._query_github(keyword))
        all_urls.extend(self._query_gitlab(keyword))

        # enumerate subdomains and verify availability
        sub_results = []
        js_leaks = []
        if self.scan_subdomains:
            subs = enumerate_subdomains(keyword)
            sub_items = [{"url": f"https://{s}", "domain": s, "source": "subdomain"} for s in subs]
            if sub_items:
                sub_results = self._verify_live(sub_items, progress_callback=progress_callback)
            # optional JS scan on each subdomain
            if self.scan_js:
                for s in subs:
                    if progress_callback:
                        progress_callback({"js_domain": s})
                    for r in run_smart_scan(s, include_subdomains=False):
                        js_leaks.append({
                            "source": "JS", "file": r["url"], "leak_type": r["leak_type"],
                            "value": r["value"], "domain": s
                        })

        if not all_urls:
            return []
        verified = self._verify_live(all_urls, progress_callback=progress_callback)
        verified.extend(sub_results)
        results = []
        for item in verified:
            res_item = {
                "source": "Recon",
                "file": item["url"],
                "leak_type": f"URL ({item['domain']})",
                "value": str(item.get("live_status")),
                "status_code": item.get("live_status"),
                "discovery": item["source"],
                "timestamp": item.get("timestamp"),
            }
            results.append(res_item)
            if result_callback:
                result_callback(res_item, len(results))
        # include JS leaks gathered from subdomains
        for js in js_leaks:
            results.append(js)
            if result_callback:
                result_callback(js, len(results))
        return results
