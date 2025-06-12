import math
import re
from .regex_patterns import LEAK_PATTERNS


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
    for pattern in LEAK_PATTERNS:
        for match in re.findall(pattern["regex"], text):
            if isinstance(match, tuple):
                match = match[0]
            if len(match) < 8:
                continue
            if _entropy(match) < entropy_threshold:
                continue
            key = (pattern["name"], match)
            if key in seen:
                continue
            seen.add(key)
            results.append((pattern["name"], match))
    return results


def ai_guess_leak_risk(text):
    """Placeholder for AI-based leak prediction."""
    hints = []
    if "secret" in text.lower() or "token" in text.lower():
        hints.append("Potential secret in text")
    return hints
