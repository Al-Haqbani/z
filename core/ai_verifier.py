try:
    from transformers import pipeline
except Exception:  # pragma: no cover - optional dependency
    pipeline = None

_classifier = None


def is_valid_leak(value):
    """Return True if AI verification deems the leak valid."""
    if pipeline is None:
        return True
    global _classifier
    if _classifier is None:
        try:
            _classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
            )
        except Exception:
            return True
    try:
        result = _classifier(f"Potential credential: {value}")[0]
        return result["label"] == "POSITIVE" and result["score"] > 0.6
    except Exception:
        return True
