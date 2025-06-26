"""Collection of regex patterns used for leak detection."""

from __future__ import annotations

import json
import os
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def _load_patterns() -> List[Dict[str, str]]:
    """Load leak patterns from the bundled JSON file.

    If the JSON file can't be read for some reason, a small fallback
    set of patterns is returned so the tool still works.
    """

    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "leak_patterns.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = f.read()
        try:
            patterns = json.loads(raw)
        except json.JSONDecodeError:
            # if the file contains invalid escape sequences like \z
            fixed = re.sub(r"\\(?![\\\"/bfnrtu])", r"\\\\", raw)
            patterns = json.loads(fixed)
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
    except Exception as exc:
        logger.warning("Failed to load %s: %s. Using fallback patterns", json_path, exc)

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
        {"name": "Salesforce OAuth Token", "regex": r"00D[A-Za-z0-9]{12}!+[A-Za-z0-9]{24,40}"},
        {"name": "Twilio API Key", "regex": r"SK[0-9a-fA-F]{32}"},
    ]


LEAK_PATTERNS: List[Dict[str, str]] = _load_patterns()


def add_patterns_from_file(path: str) -> None:
    """Append additional patterns from a JSON file."""
    global LEAK_PATTERNS, _COMPILED_PATTERNS, _MASTER_REGEX
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        new_patterns = []
        for p in data:
            if isinstance(p, dict) and "name" in p and "regex" in p:
                reg = p["regex"].replace("\\z", "\\Z")
                try:
                    re.compile(reg, re.IGNORECASE)
                except re.error:
                    continue
                new_patterns.append({"name": p["name"], "regex": reg})
        if new_patterns:
            LEAK_PATTERNS.extend(new_patterns)
            _COMPILED_PATTERNS[:] = [
                (p["name"], re.compile(p["regex"], re.IGNORECASE))
                for p in LEAK_PATTERNS
            ]
            _MASTER_REGEX = re.compile(
                "|".join(f"({p['regex']})" for p in LEAK_PATTERNS),
                re.MULTILINE | re.IGNORECASE,
            )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to load extra patterns from %s: %s", path, exc)


def get_pattern_names() -> List[str]:
    """Return the names of all available leak patterns."""
    return [p["name"] for p in LEAK_PATTERNS]


def get_pattern_list() -> List[tuple[int, str]]:
    """Return list of (index, name) pairs for selection."""
    return [(i + 1, p["name"]) for i, p in enumerate(LEAK_PATTERNS)]

