import random
import time
import requests
from utils.http_utils import request_with_backoff
from .leak_detector import detect_leaks


class BitbucketSearcher:
    """Search Bitbucket public repositories for leaks."""

    BASE_URL = "https://api.bitbucket.org/2.0"
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
            if ":" in self.token:
                # Basic auth with username:password or app token
                import base64
                b64 = base64.b64encode(self.token.encode()).decode()
                headers["Authorization"] = f"Basic {b64}"
            else:
                headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _fetch_json(self, url, *, params=None):
        try:
            resp = request_with_backoff(url, headers=self._headers(), params=params)
            if resp and resp.status_code == 200:
                return resp.json()
            if not self.silent:
                status = resp.status_code if resp else 'timeout'
                text = resp.text[:100] if resp else ''
                print(f"Bitbucket API request failed: {status} {text}")
        except Exception as exc:
            if not self.silent:
                print(f"Bitbucket request error: {exc}")
        return None

    def _list_repos(self, keyword, limit=5):
        repos = []
        page = 1
        while len(repos) < limit:
            url = f"{self.BASE_URL}/repositories?q=name~\"{keyword}\"&page={page}"
            data = self._fetch_json(url)
            if not data:
                break
            repos.extend(data.get("values", []))
            if not data.get("next"):
                break
            page += 1
        return repos[:limit]

    def search(self, keyword, full_scan=False, result_callback=None, **_):
        leaks = []
        repos = self._list_repos(keyword, limit=3 if not full_scan else 10)
        for repo in repos:
            full_name = repo.get("full_name")
            if not full_name:
                continue
            branch = repo.get("mainbranch", {}).get("name", "master")
            files_url = f"{self.BASE_URL}/repositories/{full_name}/src/{branch}/"
            tree = self._fetch_json(files_url)
            if not tree:
                continue
            for f in tree.get("values", []):
                if f.get("type") != "commit_file":
                    continue
                path = f.get("path")
                raw_url = f"{self.BASE_URL}/repositories/{full_name}/raw/{branch}/{path}"
                try:
                    resp = request_with_backoff(raw_url, headers=self._headers())
                    if resp and resp.status_code == 200:
                        for ltype, value in detect_leaks(resp.text):
                            item = {
                                "source": "Bitbucket",
                                "file": raw_url,
                                "leak_type": ltype,
                                "value": value,
                            }
                            leaks.append(item)
                            if result_callback:
                                result_callback(item, len(leaks))
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception:
                    if not self.silent:
                        print(f"Bitbucket fetch error for {raw_url}")
        return leaks
