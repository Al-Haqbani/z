import random
import time
import os
import requests
import hashlib

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


def post_with_backoff(
    url,
    *,
    headers=None,
    json=None,
    data=None,
    timeout=DEFAULT_TIMEOUT,
    retries=DEFAULT_RETRIES,
    silent=True,
    proxies=None,
):
    """POST request with backoff and UA rotation."""
    headers = headers or {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = random.choice(USER_AGENTS)
    backoff = 1.0
    for _ in range(retries):
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=json,
                data=data,
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


def save_screenshot(url: str, out_dir: str = "screenshots", silent: bool = True) -> str:
    """Fetch a screenshot for ``url`` using a public service and save it."""
    os.makedirs(out_dir, exist_ok=True)
    fname = hashlib.md5(url.encode()).hexdigest() + ".png"
    path = os.path.join(out_dir, fname)
    try:
        resp = request_with_backoff(
            f"https://image.thum.io/get/png/{url}", timeout=15, silent=silent
        )
        if resp and resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            return path
    except Exception:
        if not silent:
            raise
    return ""
