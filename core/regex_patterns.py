"""Collection of regex patterns used for leak detection."""

from __future__ import annotations

import json
import tomli
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
    gitleaks_path = os.path.join(os.path.dirname(__file__), "..", "data", "gitleaks.toml")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = f.read()
        try:
            patterns = json.loads(raw)
        except json.JSONDecodeError:
            fixed = re.sub(r"\\(?![\\\"/bfnrtu])", r"\\\\", raw)
            try:
                patterns = json.loads(fixed)
            except json.JSONDecodeError:
                patterns = None
        if not patterns and os.path.exists(gitleaks_path):
            try:
                with open(gitleaks_path, "rb") as gf:
                    data = tomli.load(gf)
                patterns = [
                    {
                        "name": r.get("id", "unknown"),
                        "regex": r.get("regex", "")
                    }
                    for r in data.get("rules", []) if "regex" in r
                ]
            except Exception as exc:
                logger.warning("Failed to load gitleaks patterns: %s", exc)
                patterns = None
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
        logger.warning("Failed to load pattern files: %s", exc)

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
        {"name": "Twitch Client ID", "regex": r"(?i)twitch[\w\s]{0,20}client[_-]?id[=:\s]*['\"]?([a-z0-9]{15,})"},
        {"name": "Twitch Client Secret", "regex": r"(?i)twitch[\w\s]{0,20}client[_-]?secret[=:\s]*['\"]?([a-z0-9]{30,})"},
        {"name": "Okta API Token", "regex": r"00[a-zA-Z0-9]{20,}"},
        {"name": "Azure Client Secret", "regex": r"(?i)azure[\w\s]{0,20}client[_-]?secret[=:\s]*['\"]?([A-Za-z0-9-_]{20,})"},
    ]


LEAK_PATTERNS: List[Dict[str, str]] = _load_patterns()
extra_file = os.getenv("EMPLOLEAKS_EXTRA_PATTERNS")
if extra_file:
    try:
        add_patterns_from_file(extra_file)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to load patterns from %s: %s", extra_file, exc)

# Map of pattern name -> severity string
LEAK_SEVERITY = {}
for pat in LEAK_PATTERNS:
    sev = pat.get("severity")
    if not sev:
        name_low = pat["name"].lower()
        if "token" in name_low or "key" in name_low:
            sev = "high"
        else:
            sev = "medium"
    LEAK_SEVERITY[pat["name"]] = sev

def get_severity(name: str) -> str:
    """Return configured severity for a leak type."""
    return LEAK_SEVERITY.get(name, "medium")


def add_patterns_from_file(path: str) -> None:
    """Append additional patterns from a JSON file."""
    global LEAK_PATTERNS, _COMPILED_PATTERNS, _MASTER_REGEX, LEAK_SEVERITY
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
                entry = {"name": p["name"], "regex": reg}
                if "severity" in p:
                    entry["severity"] = p["severity"]
                new_patterns.append(entry)
        if new_patterns:
            LEAK_PATTERNS.extend(new_patterns)
            for np in new_patterns:
                sev = np.get("severity")
                if not sev:
                    name_low = np["name"].lower()
                    sev = "high" if ("token" in name_low or "key" in name_low) else "medium"
                LEAK_SEVERITY[np["name"]] = sev
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

