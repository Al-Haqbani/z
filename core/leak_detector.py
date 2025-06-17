import math
import re
from typing import List, Tuple

from .regex_patterns import LEAK_PATTERNS

_COMPILED_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (p["name"], re.compile(p["regex"], re.IGNORECASE)) for p in LEAK_PATTERNS
]

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


def detect_leaks(text, entropy_threshold: float = 3.0):
    """Return list of (name, value) for each pattern found in text.

    A simple entropy check filters obvious false positives.
    """
    results = []
    seen = set()

    if _MASTER_REGEX:
        candidates = [m.group(0) for m in _MASTER_REGEX.finditer(text)]
    else:
        candidates = [text]

    for cand in candidates:
        for name, regex in _COMPILED_PATTERNS:
            m = regex.search(cand)
            if not m:
                continue
            val = m.group(1) if m.groups() else m.group(0)
            if len(val) < 8 or _entropy(val) < entropy_threshold:
                continue
            key = (name, val)
            if key in seen:
                continue
            seen.add(key)
            results.append((name, val))
            break

    return results


def ai_guess_leak_risk(text):
    """Placeholder for AI-based leak prediction."""
    hints = []
    if "secret" in text.lower() or "token" in text.lower():
        hints.append("Potential secret in text")
    return hints
