import random
import time
from typing import List, Dict

from utils.http_utils import request_with_backoff

from .leak_detector import detect_leaks


class GrayHatSearcher:
    """Search GrayHatWarfare open buckets for files matching a keyword."""

    BASE_URL = "https://buckets.grayhatwarfare.com/api/v2/files"

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def search(self, keyword, result_callback=None, **kwargs) -> List[Dict[str, str]]:
        if not self.token:
            if not self.silent:
                print("GrayHatWarfare token required for bucket search")
            return []
        params = {"keywords": keyword, "full-path": 1, "limit": 20, "start": 0}
        headers = {"Authorization": f"Bearer {self.token}"}
        leaks = []
        try:
            resp = request_with_backoff(self.BASE_URL, headers=headers, params=params)
            if resp and resp.status_code == 200:
                data = resp.json()
                for item in data.get("files", []):
                    url = item.get("url")
                    bucket = item.get("bucket")
                    path = item.get("fullPath")
                    item_dict = {
                        "source": "GrayHatWarfare",
                        "file": url,
                        "leak_type": "Open Bucket File",
                        "value": f"{bucket}/{path}" if bucket and path else bucket or path,
                    }
                    leaks.append(item_dict)
                    if result_callback:
                        result_callback(item_dict, len(leaks))
                    if url and url.endswith(('.txt', '.log', '.json', '.env')):
                        f_resp = request_with_backoff(url)
                        if f_resp and f_resp.status_code == 200 and len(f_resp.text) < 20000:
                            for name, val in detect_leaks(f_resp.text):
                                item2 = {
                                    "source": "GrayHatWarfare",
                                    "file": url,
                                    "leak_type": name,
                                    "value": val,
                                }
                                leaks.append(item2)
                                if result_callback:
                                    result_callback(item2, len(leaks))
                    time.sleep(random.uniform(1, 2))
            else:
                if not self.silent:
                    status = resp.status_code if resp else 'timeout'
                    text = resp.text[:100] if resp else ''
                    print(f"GrayHatWarfare API failed: {status} {text}")
        except Exception as exc:
            if not self.silent:
                print(f"GrayHatWarfare search error: {exc}")
        return leaks
