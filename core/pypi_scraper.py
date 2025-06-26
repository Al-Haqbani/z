import re
import random
import time
import requests
from utils.http_utils import request_with_backoff

from .leak_detector import detect_leaks


class PyPiPackageSearcher:
    """Search PyPI for packages and scan descriptions for leaks."""

    SEARCH_URL = "https://pypi.org/search/"
    INFO_URL = "https://pypi.org/pypi/{pkg}/json"

    def __init__(self, silent=False, **_):
        self.silent = silent

    def _extract_names(self, html):
        pattern = r"/project/([^/]+)/"
        return re.findall(pattern, html)

    def search(self, keyword, result_callback=None, progress_callback=None, limit=20, **kwargs):
        leaks = []
        try:
            resp = request_with_backoff(self.SEARCH_URL, params={"q": keyword})
            if resp and resp.status_code == 200:
                names = self._extract_names(resp.text)[:limit]
                total = len(names)
                for idx, name in enumerate(names, 1):
                    if progress_callback:
                        progress_callback({"repo": name, "index": idx, "total": total})
                    info_resp = request_with_backoff(self.INFO_URL.format(pkg=name))
                    if info_resp and info_resp.status_code == 200:
                        description = info_resp.json().get("info", {}).get("description", "")
                        found = detect_leaks(description)
                        for leak_type, value in found:
                            item = {
                                "source": "PyPI",
                                "file": name,
                                "leak_type": leak_type,
                                "value": value,
                            }
                            leaks.append(item)
                            if result_callback:
                                result_callback(item, len(leaks))
                    time.sleep(random.uniform(1, 2))
                    if progress_callback:
                        progress_callback({"repo": name, "status": "done"})
            else:
                if not self.silent:
                    status = resp.status_code if resp else 'timeout'
                    text = resp.text[:100] if resp else ''
                    print(
                        f"PyPI search request failed: {status} {text}"
                    )
        except Exception as exc:
            if not self.silent:
                print(f"PyPI search error: {exc}")
        return leaks
