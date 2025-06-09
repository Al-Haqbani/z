import requests
import random
import time

from .leak_detector import detect_leaks

class DockerHubSearcher:
    """Search Docker Hub repositories for leaked secrets."""

    BASE_URL = "https://hub.docker.com/v2"

    def __init__(self, silent=False):
        self.silent = silent

    def search(self, keyword, **kwargs):
        search_url = f"{self.BASE_URL}/search/repositories/?page_size=5&query={keyword}"
        leaks = []
        try:
            resp = requests.get(search_url)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    namespace = item.get("namespace")
                    name = item.get("name")
                    readme_url = f"{self.BASE_URL}/repositories/{namespace}/{name}/readme/"
                    readme_resp = requests.get(readme_url)
                    if readme_resp.status_code == 200:
                        content = readme_resp.json().get("content", "")
                        found = detect_leaks(content)
                        for leak_type, value in found:
                            leaks.append({
                                "source": "DockerHub",
                                "file": f"{namespace}/{name}",
                                "leak_type": leak_type,
                                "value": value,
                            })
                    time.sleep(random.uniform(1, 2))
        except Exception as exc:
            if not self.silent:
                print(f"DockerHub search error: {exc}")
        return leaks
