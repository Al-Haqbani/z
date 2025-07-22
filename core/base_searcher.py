from utils.http_utils import request_with_backoff

class BaseSearcher:
    """Base class for platform searchers with common helpers."""

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def _headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def fetch_json(self, url, **kwargs):
        resp = request_with_backoff(url, headers=self._headers(), **kwargs)
        if resp and resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return None
        else:
            return None
