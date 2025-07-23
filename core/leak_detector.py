import re
from .regex_patterns import LEAK_PATTERNS


def detect_leaks(text):
    """Return list of (name, value) for each pattern found in text."""
    results = []
    for pattern in LEAK_PATTERNS:
        for match in re.findall(pattern["regex"], text):
            results.append((pattern["name"], match))
    return results


def ai_guess_leak_risk(text):
    """Placeholder for AI-based leak prediction."""
    hints = []
    if "secret" in text.lower() or "token" in text.lower():
        hints.append("Potential secret in text")
    return hints
