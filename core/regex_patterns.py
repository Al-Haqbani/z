"""Collection of regex patterns used for leak detection."""

from __future__ import annotations

import json
import os
import re
from typing import List, Dict


def _load_patterns() -> List[Dict[str, str]]:
    """Load leak patterns from the bundled JSON file.

    If the JSON file can't be read for some reason, a small fallback
    set of patterns is returned so the tool still works.
    """

    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "leak_patterns.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            patterns = json.load(f)
        cleaned = []
        if isinstance(patterns, list):
            for p in patterns:
                if not isinstance(p, dict) or "name" not in p or "regex" not in p:
                    continue
                reg = p["regex"].replace("\\z", "\\Z")
                try:
                    re.compile(reg, re.IGNORECASE)
                except re.error:
                    continue
                cleaned.append({"name": p["name"], "regex": reg})
        if cleaned:
            return cleaned
    except Exception:
        pass

    # Fallback minimal patterns
    return [
        {"name": "GitHub Token", "regex": r"ghp_[A-Za-z0-9]{36}"},
        {"name": "Slack Token", "regex": r"xox[baprs]-[A-Za-z0-9-]{10,48}"},
        {"name": "AWS Access Key", "regex": r"AKIA[0-9A-Z]{16}"},
        {"name": "Bearer Token", "regex": r"Bearer [A-Za-z0-9\-_]{20,}"},
        {"name": "HuggingFace Token", "regex": r"hf_[A-Za-z0-9]{34}"},
        {"name": "Zendesk Secret", "regex": r"(?i)zendesk[\w\s]{0,20}['\"]([a-z0-9]{40})"},
        {"name": "Bitbucket App Password", "regex": r"(?i)bitbucket[_-]?app[_-]?password[=:\s]*['\"]?([A-Za-z0-9]{20,})"},
        {"name": "Generic API Key", "regex": r"(?i)(?:api[_-]?key|access[_-]?token)[=:\s]*['\"]?([A-Za-z0-9_\-]{20,})"},
        {"name": "Generic Password", "regex": r"(?i)(?:password|secret|token)[=:\s]*['\"]?([A-Za-z0-9_\-]{8,})"},
        {"name": "RSA Private Key", "regex": r"-----BEGIN RSA PRIVATE KEY-----"},
        {"name": "DSA Private Key", "regex": r"-----BEGIN DSA PRIVATE KEY-----"},
        {"name": "EC Private Key", "regex": r"-----BEGIN EC PRIVATE KEY-----"},
        {"name": "PGP Private Key", "regex": r"-----BEGIN PGP PRIVATE KEY BLOCK-----"},
        {"name": "JWT", "regex": r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*"},
        {"name": "Bearer JWT", "regex": r"Bearer [A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_.+/=]*"},
        {"name": "Google API Key", "regex": r"AIza[0-9A-Za-z-_]{35}"},
        {"name": "Google OAuth Token", "regex": r"ya29\.[0-9A-Za-z-_]+"},
    ]


LEAK_PATTERNS: List[Dict[str, str]] = _load_patterns()


def get_pattern_names() -> List[str]:
    """Return the names of all available leak patterns."""
    return [p["name"] for p in LEAK_PATTERNS]


def get_pattern_list() -> List[tuple[int, str]]:
    """Return list of (index, name) pairs for selection."""
    return [(i + 1, p["name"]) for i, p in enumerate(LEAK_PATTERNS)]

