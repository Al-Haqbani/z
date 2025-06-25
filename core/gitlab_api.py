import random
import time
import requests
from utils.http_utils import request_with_backoff

from .leak_detector import detect_leaks


class GitLabSearcher:
    """Search GitLab public code and commits for leaked secrets."""

    BASE_URL = "https://gitlab.com/api/v4"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)",
    ]

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def _headers(self):
        ua = random.choice(self.USER_AGENTS)
        headers = {"User-Agent": ua}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    def _search_scope(self, keyword, scope):
        params = {"scope": scope, "search": keyword, "per_page": 20}
        try:
            resp = request_with_backoff(f"{self.BASE_URL}/search", headers=self._headers(), params=params)
            if resp and resp.status_code == 200:
                return resp.json()
            if not self.silent:
                status = resp.status_code if resp else 'timeout'
                text = resp.text[:100] if resp else ''
                print(f"GitLab API {scope} search failed: {status} {text}")
        except Exception as exc:
            if not self.silent:
                print(f"GitLab {scope} search error: {exc}")
        return []

    def search(self, keyword, scan_commits=False, result_callback=None, progress_callback=None, limit=20, **_):
        leaks = []
        blob_results = self._search_scope(keyword, "blobs")[:limit]
        total = len(blob_results)
        for idx, item in enumerate(blob_results, 1):
            if progress_callback:
                progress_callback({"repo": item.get("project_id"), "index": idx, "total": total})
            project = item.get("project_id")
            file_path = item.get("filename")
            ref = item.get("ref") or "master"
            if not project or not file_path:
                continue
            raw_url = f"{self.BASE_URL}/projects/{project}/repository/files/{requests.utils.quote(file_path, safe='')}/raw?ref={ref}"
            try:
                raw_resp = request_with_backoff(raw_url, headers=self._headers())
                if raw_resp and raw_resp.status_code == 200:
                    for leak_type, value in detect_leaks(raw_resp.text):
                        item_dict = {
                            "source": "GitLab",
                            "file": raw_url,
                            "leak_type": leak_type,
                            "value": value,
                        }
                        leaks.append(item_dict)
                        if result_callback:
                            result_callback(item_dict, len(leaks))
            except Exception as exc:
                if not self.silent:
                    print(f"GitLab raw fetch error: {exc}")
            time.sleep(random.uniform(1, 2))
            if progress_callback:
                progress_callback({"repo": item.get("project_id"), "status": "done"})

        if scan_commits:
            commit_results = self._search_scope(keyword, "commits")
            for item in commit_results:
                msg = item.get("message", "")
                for leak_type, value in detect_leaks(msg):
                    item_dict = {
                        "source": "GitLab",
                        "file": item.get("web_url", ""),
                        "leak_type": leak_type,
                        "value": value,
                    }
                    leaks.append(item_dict)
                    if result_callback:
                        result_callback(item_dict, len(leaks))
        return leaks
