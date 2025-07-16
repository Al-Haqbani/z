import os
import json


def load_config(path: str | None = None) -> dict:
    """Load config JSON from path or environment variable."""
    path = path or os.environ.get("EMPLOLEAKS_CONFIG") or "config.json"
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
