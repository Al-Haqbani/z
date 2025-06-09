import requests
import re
import random
import time

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

    def search(self, keyword, **kwargs):
        leaks = []
        try:
            resp = requests.get(self.SEARCH_URL, params={"q": keyword})
            if resp.status_code == 200:
                names = self._extract_names(resp.text)[:5]
                for name in names:
                    info_resp = requests.get(self.INFO_URL.format(pkg=name))
                    if info_resp.status_code == 200:
                        description = info_resp.json().get("info", {}).get("description", "")
                        found = detect_leaks(description)
                        for leak_type, value in found:
                            leaks.append({
                                "source": "PyPI",
                                "file": name,
                                "leak_type": leak_type,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 2))
        except Exception as exc:
            if not self.silent:
                print(f"PyPI search error: {exc}")
        return leaks
