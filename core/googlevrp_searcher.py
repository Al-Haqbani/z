import base64
import random
import time
from utils.http_utils import request_with_backoff
from .leak_detector import detect_leaks

class GoogleVRPSearcher:
    """Search googlesource.com repositories for leaked secrets."""

    def __init__(self, silent=False, **_):
        self.silent = silent

    def _fetch_json(self, url):
        resp = request_with_backoff(url)
        if resp and resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return None
        return None

    def _fetch_text(self, url):
        resp = request_with_backoff(url)
        if resp and resp.status_code == 200:
            return resp.text
        return ""

    def search(self, keyword, employees=None, result_callback=None, progress_callback=None, limit=5, **kwargs):
        leaks = []
        host = f"{keyword}.googlesource.com"
        repos = self._fetch_json(f"https://{host}/?format=JSON") or {}
        for idx, repo in enumerate(list(repos.keys())[:limit], 1):
            if progress_callback:
                progress_callback({"repo": repo, "index": idx, "total": len(repos)})
            readme_url = f"https://{host}/{repo}/+/refs/heads/master/README.md?format=TEXT"
            data = self._fetch_text(readme_url)
            if data:
                try:
                    text = base64.b64decode(data).decode('utf-8', errors='ignore')
                except Exception:
                    text = data
                for lt, val in detect_leaks(text):
                    item = {"source": "googlevrp", "file": readme_url, "leak_type": lt, "value": val}
                    leaks.append(item)
                    if result_callback:
                        result_callback(item, len(leaks))
            time.sleep(random.uniform(1, 2))
            if progress_callback:
                progress_callback({"repo": repo, "status": "done"})
        return leaks
