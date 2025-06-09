import requests
import random
import time

from .leak_detector import detect_leaks


class RedditSearcher:
    """Search Reddit posts for leaked secrets."""

    BASE_URL = "https://www.reddit.com/search.json"

    def __init__(self, silent=False):
        self.silent = silent

    def _headers(self):
        return {"User-Agent": "EmploLeaksGuardian/0.1"}

    def search(self, keyword, **kwargs):
        leaks = []
        params = {"q": keyword, "limit": 5}
        try:
            resp = requests.get(self.BASE_URL, headers=self._headers(), params=params)
            if resp.status_code == 200:
                data = resp.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    text = f"{post.get('title', '')}\n{post.get('selftext', '')}"
                    found = detect_leaks(text)
                    for leak_type, value in found:
                        leaks.append({
                            "source": "Reddit",
                            "file": post.get("permalink"),
                            "leak_type": leak_type,
                            "value": value,
                        })
                    time.sleep(random.uniform(1, 2))
        except Exception as exc:
            if not self.silent:
                print(f"Reddit search error: {exc}")
        return leaks
