import random
import time
import requests
from utils.http_utils import request_with_backoff

from .leak_detector import detect_leaks


class NPMPackageSearcher:
    """Search NPM registry for packages and scan READMEs."""

    BASE_URL = "https://registry.npmjs.org"

    def __init__(self, silent=False, **_):
        self.silent = silent

    def search(self, keyword, result_callback=None, **kwargs):
        leaks = []
        search_url = f"{self.BASE_URL}/-/v1/search"
        params = {"text": keyword, "size": 5}
        try:
            resp = request_with_backoff(search_url, params=params)
            if resp and resp.status_code == 200:
                data = resp.json()
                for obj in data.get("objects", []):
                    pkg_name = obj.get("package", {}).get("name")
                    details_resp = request_with_backoff(f"{self.BASE_URL}/{pkg_name}")
                    if details_resp and details_resp.status_code == 200:
                        readme = details_resp.json().get("readme", "")
                        found = detect_leaks(readme)
                        for leak_type, value in found:
                            item = {
                                "source": "NPM",
                                "file": pkg_name,
                                "leak_type": leak_type,
                                "value": value,
                            }
                            leaks.append(item)
                            if result_callback:
                                result_callback(item, len(leaks))
                    time.sleep(random.uniform(1, 2))
            else:
                if not self.silent:
                    status = resp.status_code if resp else 'timeout'
                    text = resp.text[:100] if resp else ''
                    print(
                        f"NPM API request failed: {status} {text}"
                    )
        except Exception as exc:
            if not self.silent:
                print(f"NPM search error: {exc}")
        return leaks
