import random
import time
from typing import List

from utils.http_utils import request_with_backoff
from .leak_detector import detect_leaks


class GitHubGistSearcher:
    """Search recent public GitHub gists for leaked secrets."""

    BASE_URL = "https://api.github.com/gists/public"

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def _headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def search(
        self,
        keyword: str,
        limit: int = 2,
        result_callback=None,
        progress_callback=None,
        **_,
    ):
        leaks: List[dict] = []
        page = 1
        fetched = 0
        headers = self._headers()
        while fetched < limit:
            resp = request_with_backoff(
                self.BASE_URL,
                headers=headers,
                params={"page": page, "per_page": 100},
            )
            if not resp or resp.status_code != 200:
                if not self.silent:
                    status = resp.status_code if resp else "timeout"
                    print(f"Gist API failed: {status}")
                break
            data = resp.json()
            if not data:
                break
            total = len(data)
            for idx, gist in enumerate(data, 1):
                if fetched >= limit:
                    break
                fetched += 1
                if progress_callback:
                    progress_callback({"gist": gist.get("html_url"), "index": idx, "total": total})
                for file_info in gist.get("files", {}).values():
                    raw_url = file_info.get("raw_url")
                    if not raw_url:
                        continue
                    f_resp = request_with_backoff(raw_url)
                    if f_resp and f_resp.status_code == 200:
                        text = f_resp.text
                        if keyword.lower() in text.lower():
                            for lt, val in detect_leaks(text):
                                item = {
                                    "source": "Gist",
                                    "file": raw_url,
                                    "leak_type": lt,
                                    "value": val,
                                }
                                leaks.append(item)
                                if result_callback:
                                    result_callback(item, len(leaks))
                time.sleep(random.uniform(1, 2))
                if progress_callback:
                    progress_callback({"gist": gist.get("html_url"), "status": "done"})
            page += 1
        return leaks
