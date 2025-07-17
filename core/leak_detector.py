import math
import re
from typing import List, Tuple

from .regex_patterns import LEAK_PATTERNS

_COMPILED_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (p["name"], re.compile(p["regex"], re.IGNORECASE)) for p in LEAK_PATTERNS
]

# selected pattern names, or None for all
_ACTIVE_PATTERNS: List[str] | None = None


def set_active_patterns(names: List[str] | None) -> None:
    """Limit detection to the given pattern names."""
    global _ACTIVE_PATTERNS
    _ACTIVE_PATTERNS = names

def _build_master_regex() -> re.Pattern | None:
    parts = []
    for p in LEAK_PATTERNS:
        parts.append(f"({p['regex']})")
    try:
        return re.compile("|".join(parts), re.MULTILINE | re.IGNORECASE)
    except re.error:
        return None

_MASTER_REGEX = _build_master_regex()


def _entropy(value: str) -> float:
    """Calculate Shannon entropy of the provided string."""
    if not value:
        return 0.0
    freq = {}
    for char in value:
        freq[char] = freq.get(char, 0) + 1
    ent = 0.0
    for c in freq.values():
        p = c / len(value)
        ent -= p * math.log2(p)
    return ent


def detect_leaks(text, entropy_threshold: float = 3.0, patterns: List[str] | None = None):
    """Return list of (name, value) for each pattern found in text.

    A simple entropy check filters obvious false positives.
    """
    results = []
    seen = set()

    active = _ACTIVE_PATTERNS if patterns is None else patterns
    if active:
        patterns_list = [(n, r) for n, r in _COMPILED_PATTERNS if n in active]
    else:
        patterns_list = _COMPILED_PATTERNS

    for name, regex in patterns_list:
        for m in regex.finditer(text):
            val = m.group(1) if m.groups() else m.group(0)
            if len(val) < 8 or _entropy(val) < entropy_threshold:
                continue
            if name.startswith("Generic") and not any(c.isdigit() for c in val):
                continue
            key = (name, val)
            if key in seen:
                continue
            seen.add(key)
            results.append((name, val))

    return results


def ai_guess_leak_risk(text):
    """Placeholder for AI-based leak prediction."""
    hints = []
    if "secret" in text.lower() or "token" in text.lower():
        hints.append("Potential secret in text")
    return hints
