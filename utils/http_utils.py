import random
import time
import requests

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]


def request_with_backoff(url, *, headers=None, params=None, timeout=30, retries=8, silent=True):
    """Perform GET request with exponential backoff and UA rotation."""
    headers = headers or {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = random.choice(USER_AGENTS)
    backoff = 1.0
    for _ in range(retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code >= 500:
                time.sleep(backoff)
                backoff *= 2
                continue
            return resp
        except Exception:
            if not silent:
                raise
            time.sleep(backoff)
            backoff *= 2
    return None
