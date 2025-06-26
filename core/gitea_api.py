import os
import random
import time
from typing import List, Optional

from .leak_detector import detect_leaks
from utils.http_utils import request_with_backoff


class GiteaSearcher:
    """Search self-hosted Gitea instances for leaked secrets."""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None, silent: bool = False, **_):
        self.base_url = base_url or os.environ.get("GITEA_URL", "https://gitea.com/api/v1")
        self.token = token
        self.silent = silent

    def _headers(self):
        headers = {"User-Agent": "EmploLeaksGuardian"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _search_repos(self, keyword: str) -> List[str]:
        url = f"{self.base_url}/repos/search"
        params = {"q": keyword, "limit": 10}
        data = request_with_backoff(url, headers=self._headers(), params=params)
        if not data or data.status_code != 200:
            if not self.silent:
                status = data.status_code if data else 'timeout'
                print(f"Gitea repo search failed: {status}")
            return []
        try:
            payload = data.json()
            return [repo.get("full_name") for repo in payload.get("data", []) if repo.get("full_name")]
        except Exception:
            return []

    def _search_code(self, repo: str, keyword: str):
        url = f"{self.base_url}/repos/{repo}/search"
        params = {"q": keyword, "kind": "code"}
        data = request_with_backoff(url, headers=self._headers(), params=params)
        if not data or data.status_code != 200:
            return []
        try:
            payload = data.json()
            return payload.get("data", [])
        except Exception:
            return []

    def search(self, keyword: str, result_callback=None, **kwargs):
        leaks = []
        repos = self._search_repos(keyword)
        for repo in repos:
            items = self._search_code(repo, keyword)
            for itm in items:
                raw_url = itm.get("html_url", "").replace("blob/", "raw/")
                resp = request_with_backoff(raw_url, headers=self._headers())
                if resp and resp.status_code == 200:
                    for name, value in detect_leaks(resp.text):
                        item = {
                            "source": "Gitea",
                            "file": raw_url,
                            "leak_type": name,
                            "value": value,
                        }
                        leaks.append(item)
                        if result_callback:
                            result_callback(item, len(leaks))
                time.sleep(random.uniform(1, 2))
        return leaks
