from transformers import pipeline

_classifier = None


def is_valid_leak(value):
    """Use a small sentiment model as a rough heuristic to verify secrets."""
    global _classifier
    if _classifier is None:
        try:
            _classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
            )
        except Exception:
            return False
    try:
        result = _classifier(f"Potential credential: {value}")[0]
        return result["label"] == "POSITIVE" and result["score"] > 0.6
    except Exception:
        return False
