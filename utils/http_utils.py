import random
import time
import os
import requests

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

# Optional proxy support via EMPLOLEAKS_PROXY
PROXY_URL = os.environ.get("EMPLOLEAKS_PROXY")
PROXIES = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

# Allow customizing request timeout and retries with environment variables
DEFAULT_TIMEOUT = int(os.environ.get("EMPLOLEAKS_TIMEOUT", 30))
DEFAULT_RETRIES = int(os.environ.get("EMPLOLEAKS_RETRIES", 8))


def request_with_backoff(url, *, headers=None, params=None, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, silent=True, proxies=None):
    """Perform GET request with exponential backoff and UA rotation.

    A proxy can be provided via the ``proxies`` argument or the ``EMPLOLEAKS_PROXY``
    environment variable.
    """
    headers = headers or {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = random.choice(USER_AGENTS)
    backoff = 1.0
    for _ in range(retries):
        try:
            resp = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                proxies=proxies or PROXIES,
            )
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
