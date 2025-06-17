import random
import time
import requests
from utils.http_utils import request_with_backoff

from .leak_detector import detect_leaks


class PastebinSearcher:
    """Search Pastebin dumps using the psbdmp.ws API."""

    SEARCH_URL = "https://psbdmp.ws/api/search/"
    DUMP_URL = "https://psbdmp.ws/api/dump/"

    def __init__(self, silent=False, **_):
        self.silent = silent

    def search(self, keyword, **kwargs):
        leaks = []
        try:
            resp = request_with_backoff(f"{self.SEARCH_URL}{keyword}")
            if resp and resp.status_code == 200:
                ids = resp.json()[:5]
                for paste_id in ids:
                    dump_resp = request_with_backoff(f"{self.DUMP_URL}{paste_id}")
                    if dump_resp and dump_resp.status_code == 200:
                        content = dump_resp.json().get("data", "")
                        found = detect_leaks(content)
                        for leak_type, value in found:
                            leaks.append({
                                "source": "Pastebin",
                                "file": paste_id,
                                "leak_type": leak_type,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 2))
            else:
                if not self.silent:
                    status = resp.status_code if resp else 'timeout'
                    text = resp.text[:100] if resp else ''
                    print(
                        f"Pastebin API request failed: {status} {text}"
                    )
        except Exception as exc:
            if not self.silent:
                print(f"Pastebin search error: {exc}")
        return leaks
