import random
import time
import os
import requests

from .leak_detector import detect_leaks
from utils.http_utils import request_with_backoff


def _fetch_json(url, headers):
    resp = request_with_backoff(url, headers=headers)
    if resp and resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return None
    return None


class GitHubSearcher:
    BASE_URL = "https://api.github.com"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)"
    ]

    DORKS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "github_dorks.txt")
    try:
        with open(DORKS_FILE, "r", encoding="utf-8") as f:
            DORKS = [line.strip() for line in f if line.strip()]
    except Exception:
        DORKS = []

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
    def get_org_repos(cls, org, token=None):
        """Return a list of repo names within the organization."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        repos = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/orgs/{org}/repos?per_page=100&page={page}"
            data = _fetch_json(url, headers)
            if not data:
                break
            repos.extend([r.get("full_name") for r in data if r.get("full_name")])
            if len(data) < 100:
                break
            page += 1
        return repos

    @classmethod
    def get_user_repos(cls, username, token=None):
        """Return a list of repo names for the given user."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        repos = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/users/{username}/repos?per_page=100&page={page}"
            data = _fetch_json(url, headers)
            if not data:
                break
            repos.extend([r.get("full_name") for r in data if r.get("full_name")])
            if len(data) < 100:
                break
            page += 1
        return repos

    @classmethod
    def scan_repo(cls, repo, token=None, silent=False, progress_callback=None, result_callback=None):
        """Scan every file in the given repository."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        info = _fetch_json(f"{cls.BASE_URL}/repos/{repo}", headers)
        if not info:
            return []
        branch = info.get("default_branch", "master")
        tree_url = f"{cls.BASE_URL}/repos/{repo}/git/trees/{branch}?recursive=1"
        tree = _fetch_json(tree_url, headers)
        if not tree:
            return []
        leaks = []
        if progress_callback:
            progress_callback({"repo": repo, "status": "start"})
        for item in tree.get("tree", []):
            if item.get("type") != "blob":
                continue
            path = item.get("path")
            raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
            try:
                resp = request_with_backoff(raw_url, headers=headers)
                if resp and resp.status_code == 200:
                    for name, value in detect_leaks(resp.text):
                        item = {
                            "source": "GitHub",
                            "file": raw_url,
                            "leak_type": name,
                            "value": value,
                        }
                        leaks.append(item)
                        if result_callback:
                            result_callback(item, len(leaks))
                time.sleep(random.uniform(0.5, 1.5))
            except Exception:
                if not silent:
                    print(f"GitHub file fetch error for {raw_url}")
        if progress_callback:
            progress_callback({"repo": repo, "status": "done"})
        return leaks

    @classmethod
    def scan_repo_wayback(cls, repo, silent=False, result_callback=None):
        """Scan archived versions of repo files via the Wayback Machine."""
        from utils.wayback_scraper import get_archived_repo_files

        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        leaks = []
        for url in get_archived_repo_files(repo)[:200]:
            wb_url = f"https://web.archive.org/web/{url}"
            try:
                resp = request_with_backoff(wb_url, headers=headers)
                if resp and resp.status_code == 200:
                    for name, value in detect_leaks(resp.text):
                        item = {
                            "source": "Wayback",
                            "file": wb_url,
                            "leak_type": name,
                            "value": value,
                        }
                        leaks.append(item)
                        if result_callback:
                            result_callback(item, len(leaks))
                time.sleep(random.uniform(0.5, 1.5))
            except Exception:
                if not silent:
                    print(f"Wayback fetch error for {wb_url}")
        return leaks

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

    def search(
        self,
        keyword,
        scan_commits=False,
        employees=None,
        organization=None,
        deep_scan=False,
        full_scan=False,
        repo=None,
        scan_wayback=False,
        progress_callback=None,
        result_callback=None,
        **_,
    ):
        if not self.token:
            if not self.silent:
                print("GitHub token required for code search. Skipping GitHub results.")
            return []
        code_endpoint = f"{self.BASE_URL}/search/code"
        commit_endpoint = f"{self.BASE_URL}/search/commits"
        issue_endpoint = f"{self.BASE_URL}/search/issues"
        queries = [keyword]
        if organization:
            queries = [f"{keyword} org:{organization}"]
        if employees:
            if isinstance(employees, str):
                employees = [e.strip() for e in employees.split(',') if e.strip()]
            for user in employees:
                q = f"{keyword} user:{user}"
                if organization:
                    q += f" org:{organization}"
                queries.append(q)
        # Add GitDorker dorks combined with the keyword
        for d in self.DORKS:
            base = f"{keyword} {d}".strip()
            if organization:
                base += f" org:{organization}"
            queries.append(base)
        leaks = []
        for q in queries:
            page = 1
            while True:
                params = {"q": q, "per_page": 100, "page": page}
                try:
                    resp = request_with_backoff(code_endpoint, headers=self._headers(), params=params)
                    if resp and resp.status_code == 200:
                        data = resp.json()
                        items = data.get("items", [])
                        for item in items:
                            raw_url = item.get("html_url", "").replace("blob/", "raw/")
                            file_resp = request_with_backoff(raw_url, headers=self._headers())
                            if file_resp and file_resp.status_code == 200:
                                for name, value in detect_leaks(file_resp.text):
                                    item = {
                                        "source": "GitHub",
                                        "file": raw_url,
                                        "leak_type": name,
                                        "value": value,
                                    }
                                    leaks.append(item)
                                    if result_callback:
                                        result_callback(item, len(leaks))
                            time.sleep(random.uniform(1, 3))
                        if len(items) < 100:
                            break
                        page += 1
                    else:
                        if not self.silent:
                            status = resp.status_code if resp else 'timeout'
                            text = resp.text[:100] if resp else ''
                            print(
                                f"GitHub API request failed: {status} {text}"
                            )
                        break
                except Exception as exc:
                    if not self.silent:
                        print(f"GitHub search error: {exc}")
                    break

            if scan_commits:
                headers = self._headers()
                headers["Accept"] = "application/vnd.github.cloak-preview"
                try:
                    c_page = 1
                    while True:
                        c_resp = request_with_backoff(
                            commit_endpoint,
                            headers=headers,
                            params={"q": q, "per_page": 100, "page": c_page},
                        )
                        if c_resp and c_resp.status_code == 200:
                            cdata = c_resp.json()
                            items = cdata.get("items", [])
                            for item in items:
                                commit_url = item.get("url")
                                details = _fetch_json(commit_url, headers)
                                if not details:
                                    continue
                                msg = details.get("commit", {}).get("message", "")
                                patch = "\n".join(f.get("patch", "") for f in details.get("files", []))
                                content = msg + "\n" + patch
                                for name, value in detect_leaks(content):
                                    item = {
                                        "source": "GitHub",
                                        "file": item.get("html_url", commit_url),
                                        "leak_type": name,
                                        "value": value,
                                    }
                                    leaks.append(item)
                                    if result_callback:
                                        result_callback(item, len(leaks))
                                time.sleep(random.uniform(1, 2))
                            if len(items) < 100:
                                break
                            c_page += 1
                        else:
                            if not self.silent:
                                status = c_resp.status_code if c_resp else 'timeout'
                                text = c_resp.text[:100] if c_resp else ''
                                print(
                                    f"GitHub commit search failed: {status} {text}"
                                )
                            break
                except Exception as exc:
                    if not self.silent:
                        print(f"GitHub commit search error: {exc}")

            if deep_scan:
                try:
                    i_resp = request_with_backoff(issue_endpoint, headers=self._headers(), params={"q": q, "per_page": 100})
                    if i_resp and i_resp.status_code == 200:
                        for item in i_resp.json().get("items", []):
                            body = item.get("body", "") or ""
                            for name, value in detect_leaks(body):
                                leak_item = {
                                    "source": "GitHub",
                                    "file": item.get("html_url", ""),
                                    "leak_type": name,
                                    "value": value,
                                }
                                leaks.append(leak_item)
                                if result_callback:
                                    result_callback(leak_item, len(leaks))
                    elif not self.silent:
                        status = i_resp.status_code if i_resp else 'timeout'
                        text = i_resp.text[:100] if i_resp else ''
                        print(
                            f"GitHub issue search failed: {status} {text}"
                        )
                except Exception as exc:
                    if not self.silent:
                        print(f"GitHub issue search error: {exc}")

        if full_scan or repo:
            repos = []
            if repo:
                repos.append(repo)
            if organization:
                repos.extend(self.get_org_repos(organization, self.token))
            if employees:
                for user in employees:
                    repos.extend(self.get_user_repos(user, self.token))
            total = len(repos)
            for i, r in enumerate(repos, 1):
                if progress_callback:
                    progress_callback({"repo": r, "index": i, "total": total})
                leaks.extend(
                    self.scan_repo(
                        r,
                        token=self.token,
                        silent=self.silent,
                        progress_callback=progress_callback,
                        result_callback=result_callback,
                    )
                )
                if scan_wayback:
                    leaks.extend(
                        self.scan_repo_wayback(
                            r, silent=self.silent, result_callback=result_callback
                        )
                    )
        return leaks
