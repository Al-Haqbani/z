import requests
import random
import time

from .leak_detector import detect_leaks


def _fetch_json(url, headers):
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


class GitHubSearcher:
    BASE_URL = "https://api.github.com"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)"
    ]

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def _headers(self):
        ua = random.choice(self.USER_AGENTS)
        headers = {"User-Agent": ua}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    @classmethod
    def get_repo_contributors(cls, repo, token=None):
        """Return a list of usernames contributing to the given repo."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        url = f"{cls.BASE_URL}/repos/{repo}/contributors"
        data = _fetch_json(url, headers)
        if not data:
            return []
        return [item.get("login") for item in data if item.get("login")]

    def search(self, keyword, scan_commits=False, employees=None, **_):
        code_endpoint = f"{self.BASE_URL}/search/code"
        commit_endpoint = f"{self.BASE_URL}/search/commits"
        queries = [keyword]
        if employees:
            if isinstance(employees, str):
                employees = [e.strip() for e in employees.split(',') if e.strip()]
            for user in employees:
                queries.append(f"{keyword} user:{user}")
        leaks = []
        for q in queries:
            params = {"q": q, "per_page": 5}
            try:
                resp = requests.get(code_endpoint, headers=self._headers(), params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        raw_url = item.get("html_url", "").replace("blob/", "raw/")
                        file_resp = requests.get(raw_url, headers=self._headers())
                        if file_resp.status_code == 200:
                            found = detect_leaks(file_resp.text)
                            for name, value in found:
                                leaks.append({
                                    "source": "GitHub",
                                    "file": raw_url,
                                    "leak_type": name,
                                    "value": value,
                                })
                        time.sleep(random.uniform(1, 3))
                else:
                    if not self.silent:
                        print(
                            f"GitHub API request failed: {resp.status_code} {resp.text[:100]}"
                        )
            except Exception as exc:
                if not self.silent:
                    print(f"GitHub search error: {exc}")

            if scan_commits:
                headers = self._headers()
                headers["Accept"] = "application/vnd.github.cloak-preview"
                try:
                    c_resp = requests.get(commit_endpoint, headers=headers, params=params)
                    if c_resp.status_code == 200:
                        cdata = c_resp.json()
                        for item in cdata.get("items", []):
                            commit_url = item.get("url")
                            details = _fetch_json(commit_url, headers)
                            if not details:
                                continue
                            msg = details.get("commit", {}).get("message", "")
                            patch = "\n".join(f.get("patch", "") for f in details.get("files", []))
                            content = msg + "\n" + patch
                            for name, value in detect_leaks(content):
                                leaks.append({
                                    "source": "GitHub",
                                    "file": item.get("html_url", commit_url),
                                    "leak_type": name,
                                    "value": value,
                                })
                            time.sleep(random.uniform(1, 2))
                    else:
                        if not self.silent:
                            print(
                                f"GitHub commit search failed: {c_resp.status_code} {c_resp.text[:100]}"
                            )
                except Exception as exc:
                    if not self.silent:
                        print(f"GitHub commit search error: {exc}")
        return leaks
