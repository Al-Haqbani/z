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

    def _walk_tree(self, host, repo, path="", files=None, limit=100):
        if files is None:
            files = []
        if len(files) >= limit:
            return files
        meta = self._fetch_json(f"https://{host}/{repo}/+/{path}?format=JSON") or {}
        for name, info in meta.items():
            if name == "log":
                continue
            if info.get("type") == "file":
                files.append(f"https://{host}/{repo}/+/{path}{name}?format=TEXT")
                if len(files) >= limit:
                    break
            elif info.get("type") == "dir":
                self._walk_tree(host, repo, f"{path}{name}/", files, limit)
                if len(files) >= limit:
                    break
        return files

    def search(self, keyword, employees=None, result_callback=None, progress_callback=None, limit=5, file_limit=100, **kwargs):
        leaks = []
        host = f"{keyword}.googlesource.com"
        repos = self._fetch_json(f"https://{host}/?format=JSON") or {}
        for idx, repo in enumerate(list(repos.keys())[:limit], 1):
            if progress_callback:
                progress_callback({"repo": repo, "index": idx, "total": len(repos)})

            files = self._walk_tree(host, repo, limit=file_limit)
            for fidx, file_url in enumerate(files, 1):
                data = self._fetch_text(file_url)
                if data:
                    try:
                        text = base64.b64decode(data).decode("utf-8", errors="ignore")
                    except Exception:
                        text = data
                    for lt, val in detect_leaks(text):
                        item = {"source": "googlevrp", "file": file_url, "leak_type": lt, "value": val}
                        leaks.append(item)
                        if result_callback:
                            result_callback(item, len(leaks))
                if progress_callback:
                    progress_callback({"repo": repo, "file_index": fidx, "file_total": len(files)})
                if not self.silent:
                    time.sleep(random.uniform(0.5, 1.5))

            if progress_callback:
                progress_callback({"repo": repo, "status": "done"})
        return leaks
