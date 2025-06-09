import requests
import random
import time

from .leak_detector import detect_leaks


class HuggingFaceSearcher:
    """Search HuggingFace models for leaked secrets."""

    BASE_URL = "https://huggingface.co/api/models"

    def __init__(self, silent=False):
        self.silent = silent

    def search(self, keyword, **kwargs):
        leaks = []
        params = {"search": keyword, "limit": 5}
        try:
            resp = requests.get(self.BASE_URL, params=params)
            if resp.status_code == 200:
                for item in resp.json():
                    model_id = item.get("modelId")
                    card_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
                    card_resp = requests.get(card_url)
                    if card_resp.status_code == 200:
                        found = detect_leaks(card_resp.text)
                        for leak_type, value in found:
                            leaks.append({
                                "source": "HuggingFace",
                                "file": model_id,
                                "leak_type": leak_type,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 2))
        except Exception as exc:
            if not self.silent:
                print(f"HuggingFace search error: {exc}")
        return leaks
