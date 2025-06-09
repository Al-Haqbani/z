import requests
import random
import time

from .leak_detector import detect_leaks


class NPMPackageSearcher:
    """Search NPM registry for packages and scan READMEs."""

    BASE_URL = "https://registry.npmjs.org"

    def __init__(self, silent=False, **_):
        self.silent = silent

    def search(self, keyword, **kwargs):
        leaks = []
        search_url = f"{self.BASE_URL}/-/v1/search"
        params = {"text": keyword, "size": 5}
        try:
            resp = requests.get(search_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for obj in data.get("objects", []):
                    pkg_name = obj.get("package", {}).get("name")
                    details_resp = requests.get(f"{self.BASE_URL}/{pkg_name}")
                    if details_resp.status_code == 200:
                        readme = details_resp.json().get("readme", "")
                        found = detect_leaks(readme)
                        for leak_type, value in found:
                            leaks.append({
                                "source": "NPM",
                                "file": pkg_name,
                                "leak_type": leak_type,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 2))
        except Exception as exc:
            if not self.silent:
                print(f"NPM search error: {exc}")
        return leaks
