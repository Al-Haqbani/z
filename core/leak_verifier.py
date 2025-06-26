from utils.logger import logger
import requests
from .token_verifier import verify_token, get_poc_command


def verify_url(url: str) -> bool:
    """Return True if the URL responds with status <400."""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        if resp.status_code == 405:
            resp = requests.get(url, allow_redirects=True, timeout=5)
        return resp.status_code < 400
    except Exception as exc:
        logger.warning("URL verify error for %s: %s", url, exc)
        return False


def verify_leak(leak_type: str, value: str):
    """Verify a leak and return (status, poc)."""
    if value.startswith("http://") or value.startswith("https://"):
        ok = verify_url(value)
        poc = f"curl -I {value}" if ok else ""
        return ok, poc
    ok = verify_token(leak_type, value)
    poc = get_poc_command(leak_type, value) if ok else ""
    return ok, poc
