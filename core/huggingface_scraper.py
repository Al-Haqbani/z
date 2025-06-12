import random
import time
import requests
from utils.http_utils import request_with_backoff

from .leak_detector import detect_leaks


class HuggingFaceSearcher:
    """Search HuggingFace models for leaked secrets."""

    BASE_URL = "https://huggingface.co/api/models"

    def __init__(self, silent=False, **_):
        self.silent = silent

    def search(self, keyword, **kwargs):
        leaks = []
        params = {"search": keyword, "limit": 5}
        try:
            resp = request_with_backoff(self.BASE_URL, params=params)
            if resp and resp.status_code == 200:
                for item in resp.json():
                    model_id = item.get("modelId")
                    card_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
                    card_resp = request_with_backoff(card_url)
                    if card_resp and card_resp.status_code == 200:
                        found = detect_leaks(card_resp.text)
                        for leak_type, value in found:
                            leaks.append({
                                "source": "HuggingFace",
                                "file": model_id,
                                "leak_type": leak_type,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 2))
            else:
                if not self.silent:
                    status = resp.status_code if resp else 'timeout'
                    text = resp.text[:100] if resp else ''
                    print(
                        f"HuggingFace API request failed: {status} {text}"
                    )
        except Exception as exc:
            if not self.silent:
                print(f"HuggingFace search error: {exc}")
        return leaks
