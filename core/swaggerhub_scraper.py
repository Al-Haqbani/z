import random
import time
import requests

from .leak_detector import detect_leaks

class SwaggerHubSearcher:
    """Search public SwaggerHub API specs for leaks."""

    BASE_URL = "https://api.swaggerhub.com"

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def _headers(self):
        headers = {"User-Agent": "Mozilla/5.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def search(self, keyword, **_):
        leaks = []
        params = {"specType": "API", "query": keyword, "limit": 5}
        try:
            resp = requests.get(f"{self.BASE_URL}/specs", params=params, headers=self._headers())
            if resp.status_code == 200:
                data = resp.json()
                for api in data.get("apis", []):
                    name = api.get("name")
                    spec_url = None
                    for prop in api.get("properties", []):
                        if prop.get("type") == "Swagger":
                            spec_url = prop.get("url")
                            break
                    if not spec_url:
                        continue
                    spec_resp = requests.get(spec_url)
                    if spec_resp.status_code == 200:
                        for leak_type, value in detect_leaks(spec_resp.text):
                            leaks.append({
                                "source": "SwaggerHub",
                                "file": name or spec_url,
                                "leak_type": leak_type,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 2))
            else:
                if not self.silent:
                    print(f"SwaggerHub API request failed: {resp.status_code} {resp.text[:100]}")
        except Exception as exc:
            if not self.silent:
                print(f"SwaggerHub search error: {exc}")
        return leaks
