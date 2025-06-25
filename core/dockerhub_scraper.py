import random
import time
import requests
from utils.http_utils import request_with_backoff

from .leak_detector import detect_leaks

class DockerHubSearcher:
    """Search Docker Hub repositories for leaked secrets."""

    BASE_URL = "https://hub.docker.com/v2"

    def __init__(self, silent=False, **_):
        self.silent = silent

    def search(self, keyword, employees=None, result_callback=None, progress_callback=None, limit=20, **kwargs):
        queries = [keyword]
        if employees:
            queries.extend(employees)

        for query in queries:
            search_url = f"{self.BASE_URL}/search/repositories/?page_size={limit}&query={query}"
            try:
                resp = request_with_backoff(search_url)
                if resp and resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])[:limit]
                    total = len(results)
                    for idx, item in enumerate(results, 1):
                        namespace = item.get("namespace")
                        name = item.get("name")
                        if progress_callback:
                            progress_callback({"repo": f"{namespace}/{name}", "index": idx, "total": total})
                        readme_url = f"{self.BASE_URL}/repositories/{namespace}/{name}/readme/"
                        readme_resp = request_with_backoff(readme_url)
                        if readme_resp and readme_resp.status_code == 200:
                            content = readme_resp.json().get("content", "")
                            found = detect_leaks(content)
                            for leak_type, value in found:
                                item = {
                                    "source": "DockerHub",
                                    "file": f"{namespace}/{name}",
                                    "leak_type": leak_type,
                                    "value": value,
                                }
                                leaks.append(item)
                                if result_callback:
                                    result_callback(item, len(leaks))
                        time.sleep(random.uniform(1, 2))
                        if progress_callback:
                            progress_callback({"repo": f"{namespace}/{name}", "status": "done"})
                else:
                    if not self.silent:
                        status = resp.status_code if resp else 'timeout'
                        text = resp.text[:100] if resp else ''
                        print(f"DockerHub API request failed: {status} {text}")
            except Exception as exc:
                    print(f"DockerHub search error: {exc}")
                        text = resp.text[:100] if resp else ''
                        print(f"DockerHub API request failed: {status} {text}")
            except Exception as exc:
                if not self.silent:
                    print(f"DockerHub search error: {exc}")
        return leaks
