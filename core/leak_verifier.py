import logging
import requests
from .token_verifier import verify_token


def verify_url(url: str) -> bool:
    """Return True if the URL responds with status <400."""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        if resp.status_code == 405:
            resp = requests.get(url, allow_redirects=True, timeout=5)
        return resp.status_code < 400
    except Exception as exc:
        logging.warning("URL verify error for %s: %s", url, exc)
        return False


def verify_leak(leak_type: str, value: str) -> bool:
    """Generic verification for a leak value."""
    if value.startswith("http://") or value.startswith("https://"):
        return verify_url(value)
    # fall back to token verification for known tokens
    return verify_token(leak_type, value)
