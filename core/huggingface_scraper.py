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

    def search(self, keyword, result_callback=None, progress_callback=None, limit=20, **kwargs):
        leaks = []
        params = {"search": keyword, "limit": limit}
        try:
            resp = request_with_backoff(self.BASE_URL, params=params)
            if resp and resp.status_code == 200:
                models = resp.json()[:limit]
                total = len(models)
                for idx, item in enumerate(models, 1):
                    model_id = item.get("modelId")
                    if progress_callback and model_id:
                        progress_callback({"repo": model_id, "index": idx, "total": total})
                    card_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
                    card_resp = request_with_backoff(card_url)
                    if card_resp and card_resp.status_code == 200:
                        found = detect_leaks(card_resp.text)
                        for leak_type, value in found:
                            item = {
                                "source": "HuggingFace",
                                "file": model_id,
                                "leak_type": leak_type,
                                "value": value,
                            }
                            leaks.append(item)
                            if result_callback:
                                result_callback(item, len(leaks))
                    time.sleep(random.uniform(1, 2))
                    if progress_callback and model_id:
                        progress_callback({"repo": model_id, "status": "done"})
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
