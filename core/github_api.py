import requests
import random
import time

from .leak_detector import detect_leaks


class GitHubSearcher:
    BASE_URL = "https://api.github.com"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)"
    ]

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def _headers(self):
        ua = random.choice(self.USER_AGENTS)
        headers = {"User-Agent": ua}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def search(self, keyword, scan_commits=False, **_):
        endpoint = f"{self.BASE_URL}/search/code"
        params = {"q": keyword, "per_page": 5}
        leaks = []
        try:
            resp = requests.get(endpoint, headers=self._headers(), params=params)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("items", []):
                    raw_url = item.get("html_url", "").replace("blob/", "raw/")
                    file_resp = requests.get(raw_url, headers=self._headers())
                    if file_resp.status_code == 200:
                        found = detect_leaks(file_resp.text)
                        for name, value in found:
                            leaks.append({
                                "source": "GitHub",
                                "file": raw_url,
                                "leak_type": name,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 3))
        except Exception as exc:
            if not self.silent:
                print(f"GitHub search error: {exc}")
        return leaks
