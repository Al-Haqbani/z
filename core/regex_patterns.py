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
                    re.compile(reg)
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
        {"name": "Generic API Key", "regex": r"(?i)(?:api[_-]?key|access[_-]?token)[=:\s]*['\"]?([A-Za-z0-9_\-]{20,})"},
        {"name": "Generic Password", "regex": r"(?i)(?:password|secret|token)[=:\s]*['\"]?([A-Za-z0-9_\-]{8,})"},
    ]


LEAK_PATTERNS: List[Dict[str, str]] = _load_patterns()

