import base64
import json
import os
import requests
from typing import Any

try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # pragma: no cover - optional dependency
    AESGCM = None  # type: ignore


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def upload_json_tree(data: Any, password: str = "secret") -> str | None:
    """Upload JSON data to jsontr.ee and return the share link."""
    if AESGCM is None:
        raise RuntimeError("cryptography package required for jsontr.ee uploads")
    session = requests.Session()
    # get CSRF token
    r = session.get("https://jsontr.ee/")
    if r.status_code != 200:
        raise RuntimeError("failed to connect to jsontr.ee")
    csrf = session.cookies.get("csrftoken")
    if not csrf:
        raise RuntimeError("missing csrf token")
    # encrypt data
    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = PBKDF2HMAC(hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = kdf.derive(password.encode())
    aesgcm = AESGCM(key)
    enc = aesgcm.encrypt(iv, json.dumps(data).encode(), None)
    payload = {
        "body": json.dumps({
            "iv": _b64(iv),
            "salt": _b64(salt),
            "data": _b64(enc),
        })
    }
    headers = {"X-CSRFToken": csrf, "Content-Type": "application/json"}
    resp = session.post("https://jsontr.ee/api/tree/save/", headers=headers, json=payload)
    if resp.status_code == 200 and resp.json().get("uuid"):
        uuid = resp.json()["uuid"]
        return f"https://jsontr.ee/link/{uuid}/"
    return None
