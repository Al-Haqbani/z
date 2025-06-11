import random
import time
import requests

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
            resp = requests.get(f"{self.BASE_URL}/search", headers=self._headers(), params=params)
            if resp.status_code == 200:
                return resp.json()
            if not self.silent:
                print(f"GitLab API {scope} search failed: {resp.status_code} {resp.text[:100]}")
        except Exception as exc:
            if not self.silent:
                print(f"GitLab {scope} search error: {exc}")
        return []

    def search(self, keyword, scan_commits=False, **_):
        leaks = []
        blob_results = self._search_scope(keyword, "blobs")
        for item in blob_results:
            project = item.get("project_id")
            file_path = item.get("filename")
            ref = item.get("ref") or "master"
            if not project or not file_path:
                continue
            raw_url = f"{self.BASE_URL}/projects/{project}/repository/files/{requests.utils.quote(file_path, safe='')}/raw?ref={ref}"
            try:
                raw_resp = requests.get(raw_url, headers=self._headers())
                if raw_resp.status_code == 200:
                    for leak_type, value in detect_leaks(raw_resp.text):
                        leaks.append({
                            "source": "GitLab",
                            "file": raw_url,
                            "leak_type": leak_type,
                            "value": value,
                        })
            except Exception as exc:
                if not self.silent:
                    print(f"GitLab raw fetch error: {exc}")
            time.sleep(random.uniform(1, 2))

        if scan_commits:
            commit_results = self._search_scope(keyword, "commits")
            for item in commit_results:
                msg = item.get("message", "")
                for leak_type, value in detect_leaks(msg):
                    leaks.append({
                        "source": "GitLab",
                        "file": item.get("web_url", ""),
                        "leak_type": leak_type,
                        "value": value,
                    })
        return leaks
