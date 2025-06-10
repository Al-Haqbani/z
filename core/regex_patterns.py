"""Collection of regex patterns used for leak detection."""

from __future__ import annotations

import json
import os
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
        # ensure we loaded a list of dicts with name/regex keys
        if isinstance(patterns, list) and all(
            isinstance(p, dict) and "name" in p and "regex" in p for p in patterns
        ):
            return patterns
    except Exception:
        pass

    # Fallback minimal patterns
    return [
        {"name": "GitHub Token", "regex": r"ghp_[A-Za-z0-9]{36}"},
        {"name": "Slack Token", "regex": r"xox[baprs]-[A-Za-z0-9-]{10,48}"},
        {"name": "AWS Access Key", "regex": r"AKIA[0-9A-Z]{16}"},
    ]


LEAK_PATTERNS: List[Dict[str, str]] = _load_patterns()

