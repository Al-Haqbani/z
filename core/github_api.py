import random
import time
import os
import requests
import re

from .leak_detector import detect_leaks
from utils.http_utils import request_with_backoff


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

    TOP_COMMON_QUERIES = [
        "AWS_ACCESS_KEY_ID",
        "xoxb-",
        "hf_",
        "api_org_",
        "slack_bot_token",
        "zendesk.com",
        "supabaseUrl",
        "vercel\.com", 
        "PRIVATE_KEY",
        "refreshToken"
    ]

    DOCKER_IMAGE_RE = re.compile(r"(?:FROM|docker\s+pull)\s+([\w./:-]+)")

    def __init__(self, token=None, silent=False, **_):
        self.tokens = []
        if token:
            if isinstance(token, list):
                self.tokens = [t for t in token if t]
            elif "," in str(token):
                self.tokens = [t.strip() for t in str(token).split(",") if t.strip()]
            else:
                self.tokens = [str(token).strip()]
        self.token_idx = 0
        self.token_reset = {t: 0 for t in self.tokens}
        self.last_token = None
        self.silent = silent
        self.docker_images = set()
        self._validate_tokens()

    def _validate_tokens(self):
        """Remove invalid tokens by calling the rate limit API."""
        valid = []
        for tok in list(self.tokens):
            headers = {"User-Agent": random.choice(self.USER_AGENTS), "Authorization": f"token {tok}"}
            try:
                resp = requests.get(f"{self.BASE_URL}/rate_limit", headers=headers, timeout=10)
                if resp.status_code == 200:
                    valid.append(tok)
                else:
                    if not self.silent:
                        print(f"GitHub token {tok[:4]}*** invalid (status {resp.status_code})")
            except Exception:
                if not self.silent:
                    print(f"GitHub token {tok[:4]}*** failed validation")
        self.tokens = valid
        self.token_reset = {t: 0 for t in self.tokens}
        self.token_idx = 0

    def _next_token(self):
        if not self.tokens:
            return None
        start = self.token_idx
        now = time.time()
        for _ in range(len(self.tokens)):
            token = self.tokens[self.token_idx % len(self.tokens)]
            if self.token_reset.get(token, 0) <= now:
                self.token_idx = (self.token_idx + 1) % len(self.tokens)
                return token
            self.token_idx = (self.token_idx + 1) % len(self.tokens)
        wait = max(1, min(self.token_reset.values()) - now)
        if not self.silent:
            print(f"All tokens rate limited, sleeping {int(wait)}s")
        time.sleep(wait)
        if not self.silent:
            print("Resuming GitHub requests")
        return self._next_token()

    def _headers(self, rotate=False):
        ua = random.choice(self.USER_AGENTS)
        headers = {"User-Agent": ua}
        if self.tokens:
            tok = self._next_token() if rotate else self.tokens[self.token_idx % len(self.tokens)]
            headers["Authorization"] = f"token {tok}"
            self.last_token = tok
        return headers

    def _fetch_json(self, url, *, params=None, retries=3):
        """Fetch JSON with token rotation and rate limit handling."""
        attempts = len(self.tokens) if self.tokens else 1
        for _ in range(retries):
            for _ in range(attempts):
                resp = request_with_backoff(
                    url,
                    headers=self._headers(rotate=True),
                    params=params,
                    silent=self.silent,
                )
                if resp and resp.status_code == 200:
                    try:
                        return resp.json()
                    except Exception:
                        return None
                if not resp:
                    # timeout or connection issue, rotate token and retry
                    continue
                if resp.status_code in (401, 403, 429):
                    remaining = int(resp.headers.get("X-RateLimit-Remaining", "1"))
                    reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
                    if resp.status_code == 401 and self.last_token:
                        if self.last_token in self.tokens:
                            self.tokens.remove(self.last_token)
                            self.token_reset.pop(self.last_token, None)
                            if not self.silent:
                                print(f"Removed invalid token {self.last_token[:4]}***")
                            if not self.tokens:
                                return None
                            attempts = len(self.tokens)
                            continue
                    if remaining == 0 and reset and self.last_token:
                        self.token_reset[self.last_token] = reset
                    continue
            time.sleep(1)
        return None

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
            data = cls(token=token)._fetch_json(url)
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
            data = cls(token=token)._fetch_json(url)
            if not data:
                break
            repos.extend([r.get("full_name") for r in data if r.get("full_name")])
            if len(data) < 100:
                break
            page += 1
        return repos

    def scan_repo(self, repo, token=None, silent=False, progress_callback=None, result_callback=None):
        """Scan every file in the given repository."""
        headers = {"User-Agent": random.choice(self.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        info = self._fetch_json(f"{self.BASE_URL}/repos/{repo}")
        if not info:
            return []
        branch = info.get("default_branch", "master")
        tree_url = f"{self.BASE_URL}/repos/{repo}/git/trees/{branch}?recursive=1"
        tree = self._fetch_json(tree_url)
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
            if progress_callback:
                progress_callback({"repo": repo, "path": path})
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
                if resp and resp.status_code == 200:
                    for img in self.DOCKER_IMAGE_RE.findall(resp.text):
                        self.docker_images.add(img.strip())
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
    def scan_repo_wiki(cls, repo, token=None, silent=False, result_callback=None):
        """Scan wiki pages of a repository for leaked secrets."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        tree_url = f"{cls.BASE_URL}/repos/{repo}.wiki/git/trees/master?recursive=1"
        tree = cls(token=token)._fetch_json(tree_url)
        if not tree:
            return []
        leaks = []
        for item in tree.get("tree", []):
            if item.get("type") != "blob":
                continue
            path = item.get("path")
            raw_url = f"https://raw.githubusercontent.com/wiki/{repo}/{path}"
            try:
                resp = request_with_backoff(raw_url, headers=headers)
                if resp and resp.status_code == 200:
                    for name, value in detect_leaks(resp.text):
                        leak = {
                            "source": "GitHub Wiki",
                            "file": raw_url,
                            "leak_type": name,
                            "value": value,
                        }
                        leaks.append(leak)
                        if result_callback:
                            result_callback(leak, len(leaks))
                time.sleep(random.uniform(0.5, 1.5))
            except Exception:
                if not silent:
                    print(f"GitHub wiki fetch error for {raw_url}")
        return leaks

    @classmethod
    def scan_repo_releases(cls, repo, token=None, silent=False, result_callback=None):
        """Scan release descriptions of a repo for leaked secrets."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        leaks = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/repos/{repo}/releases?per_page=100&page={page}"
            releases = cls(token=token)._fetch_json(url)
            if not releases:
                break
            for rel in releases:
                body = rel.get("body") or ""
                for name, value in detect_leaks(body):
                    item = {
                        "source": "GitHub Release",
                        "file": rel.get("html_url", ""),
                        "leak_type": name,
                        "value": value,
                    }
                    leaks.append(item)
                    if result_callback:
                        result_callback(item, len(leaks))
            if len(releases) < 100:
                break
            page += 1
        return leaks

    @classmethod
    def scan_actions_logs(cls, repo, token=None, silent=False, result_callback=None):
        """Download GitHub Actions logs and scan them for secrets."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        leaks = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/repos/{repo}/actions/runs?per_page=100&page={page}"
            data = cls(token=token)._fetch_json(url)
            if not data:
                break
            runs = data.get("workflow_runs", [])
            for run in runs:
                log_url = run.get("logs_url")
                if not log_url:
                    continue
                try:
                    resp = request_with_backoff(log_url, headers=headers)
                    if resp and resp.status_code == 200:
                        import zipfile
                        from io import BytesIO
                        try:
                            z = zipfile.ZipFile(BytesIO(resp.content))
                            for name in z.namelist():
                                text = z.read(name).decode(errors="ignore")
                                for lt, val in detect_leaks(text):
                                    item = {
                                        "source": "GitHub Actions",
                                        "file": log_url,
                                        "leak_type": lt,
                                        "value": val,
                                    }
                                    leaks.append(item)
                                    if result_callback:
                                        result_callback(item, len(leaks))
                        except Exception:
                            if not silent:
                                print(f"Log parse error for {log_url}")
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception:
                    if not silent:
                        print(f"GitHub actions log fetch error for {log_url}")
            if len(runs) < 100:
                break
            page += 1
        return leaks

    @classmethod
    def scan_repo_commits(cls, repo, token=None, silent=False, result_callback=None):
        """Scan commit history of a repository for leaked secrets."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        leaks = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/repos/{repo}/commits?per_page=100&page={page}"
            commits = cls(token=token)._fetch_json(url)
            if not commits:
                break
            for c in commits:
                sha = c.get("sha")
                detail = cls(token=token)._fetch_json(f"{cls.BASE_URL}/repos/{repo}/commits/{sha}")
                if not detail:
                    continue
                msg = detail.get("commit", {}).get("message", "")
                patch = "\n".join(f.get("patch", "") for f in detail.get("files", []))
                content = msg + "\n" + patch
                for name, value in detect_leaks(content):
                    item = {
                        "source": "GitHub",
                        "file": detail.get("html_url", ""),
                        "leak_type": name,
                        "value": value,
                    }
                    leaks.append(item)
                    if result_callback:
                        result_callback(item, len(leaks))
                time.sleep(random.uniform(0.5, 1.0))
            if len(commits) < 100:
                break
            page += 1
        return leaks

    @classmethod
    def scan_pull_requests(cls, repo, token=None, silent=False, result_callback=None):
        """Scan pull request diffs for secrets (including deleted files)."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        leaks = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/repos/{repo}/pulls?state=all&per_page=100&page={page}"
            prs = cls(token=token)._fetch_json(url)
            if not prs:
                break
            for pr in prs:
                num = pr.get("number")
                fpage = 1
                while True:
                    f_url = f"{cls.BASE_URL}/repos/{repo}/pulls/{num}/files?per_page=100&page={fpage}"
                    files = cls(token=token)._fetch_json(f_url)
                    if not files:
                        break
                    for f in files:
                        patch = f.get("patch", "")
                        for name, value in detect_leaks(patch):
                            item = {
                                "source": "GitHub",
                                "file": pr.get("html_url", ""),
                                "leak_type": name,
                                "value": value,
                            }
                            leaks.append(item)
                            if result_callback:
                                result_callback(item, len(leaks))
                    if len(files) < 100:
                        break
                    fpage += 1
            if len(prs) < 100:
                break
            page += 1
        return leaks

    @classmethod
    def get_repo_contributors(cls, repo, token=None):
        """Return a list of usernames contributing to the given repo."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        url = f"{cls.BASE_URL}/repos/{repo}/contributors"
        data = cls(token=token)._fetch_json(url)
        if not data:
            return []
        return [item.get("login") for item in data if item.get("login")]

    @classmethod
    def get_repo_commit_authors(cls, repo, token=None, limit=200):
        """Return a set of author usernames from commit history."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        users = set()
        page = 1
        fetched = 0
        while fetched < limit:
            url = f"{cls.BASE_URL}/repos/{repo}/commits?per_page=100&page={page}"
            data = cls(token=token)._fetch_json(url)
            if not data:
                break
            for c in data:
                author = c.get("author")
                if author and author.get("login"):
                    users.add(author["login"])
            fetched += len(data)
            if len(data) < 100:
                break
            page += 1
        return list(users)

    @classmethod
    def get_repo_collaborators(cls, repo, token=None):
        """Return a list of repository collaborators (requires token)."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        url = f"{cls.BASE_URL}/repos/{repo}/collaborators"
        data = cls(token=token)._fetch_json(url)
        if not data:
            return []
        return [item.get("login") for item in data if item.get("login")]

    @classmethod
    def get_repo_employees(cls, repo, token=None):
        """Return repository collaborators only."""
        return cls.get_repo_collaborators(repo, token)

    @classmethod
    def get_org_members(cls, org, token=None):
        """Return public members of a GitHub organization."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        members = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/orgs/{org}/members?per_page=100&page={page}"
            data = cls(token=token)._fetch_json(url)
            if not data:
                break
            members.extend([m.get("login") for m in data if m.get("login")])
            if len(data) < 100:
                break
            page += 1
        return members

    @classmethod
    def scan_user_gists(cls, username, keyword, token=None, silent=False, result_callback=None):
        """Scan a user's public gists for the keyword and secrets."""
        headers = {"User-Agent": random.choice(cls.USER_AGENTS)}
        if token:
            headers["Authorization"] = f"token {token}"
        leaks = []
        page = 1
        while True:
            url = f"{cls.BASE_URL}/users/{username}/gists?per_page=100&page={page}"
            data = cls(token=token)._fetch_json(url)
            if not data:
                break
            for g in data:
                for f in g.get("files", {}).values():
                    raw_url = f.get("raw_url")
                    if not raw_url:
                        continue
                    resp = request_with_backoff(raw_url, headers=headers)
                    if resp and resp.status_code == 200:
                        text = resp.text
                        if keyword.lower() in text.lower():
                            for name, value in detect_leaks(text):
                                item = {
                                    "source": "Gist",
                                    "file": raw_url,
                                    "leak_type": name,
                                    "value": value,
                                }
                                leaks.append(item)
                                if result_callback:
                                    result_callback(item, len(leaks))
            if len(data) < 100:
                break
            page += 1
            time.sleep(random.uniform(1, 2))
        return leaks

    def search(
        self,
        keyword,
        scan_commits=False,
        employees=None,
        organization=None,
        employees_only=False,
        deep_scan=False,
        full_scan=False,
        scan_history=False,
        scan_prs=False,
        scan_gists=False,
        top_common=False,
        repo=None,
        scan_wayback=False,
        scan_wiki=False,
        scan_releases=False,
        scan_actions=False,
        progress_callback=None,
        result_callback=None,
        **_,
    ):
        if not self.tokens:
            if not self.silent:
                print("GitHub token required for code search. Skipping GitHub results.")
            return []
        code_endpoint = f"{self.BASE_URL}/search/code"
        commit_endpoint = f"{self.BASE_URL}/search/commits"
        issue_endpoint = f"{self.BASE_URL}/search/issues"
        queries = [] if employees_only and employees else [keyword]
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
            if employees_only and employees:
                for user in employees:
                    base = f"{keyword} {d} user:{user}".strip()
                    if organization:
                        base += f" org:{organization}"
                    queries.append(base)
            else:
                base = f"{keyword} {d}".strip()
                if organization:
                    base += f" org:{organization}"
                if employees and not employees_only:
                    for user in employees:
                        queries.append(f"{base} user:{user}")
                else:
                    queries.append(base)
        if top_common:
            for pat in self.TOP_COMMON_QUERIES:
                q = f"{pat} {keyword}" if keyword else pat
                if organization:
                    q += f" org:{organization}"
                queries.append(q)
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
                                details = self._fetch_json(commit_url)
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
                repos.extend(self.get_org_repos(organization, self.tokens[0] if self.tokens else None))
            if employees:
                for user in employees:
                    repos.extend(self.get_user_repos(user, self.tokens[0] if self.tokens else None))
            total = len(repos)
            for i, r in enumerate(repos, 1):
                if progress_callback:
                    progress_callback({"repo": r, "index": i, "total": total})
                leaks.extend(
                    self.scan_repo(
                        r,
                        token=self.tokens[0] if self.tokens else None,
                        silent=self.silent,
                        progress_callback=progress_callback,
                        result_callback=result_callback,
                    )
                )
                if scan_history:
                    leaks.extend(
                        self.scan_repo_commits(
                            r,
                            token=self.tokens[0] if self.tokens else None,
                            silent=self.silent,
                            result_callback=result_callback,
                        )
                    )
                if scan_prs:
                    leaks.extend(
                        self.scan_pull_requests(
                            r,
                            token=self.tokens[0] if self.tokens else None,
                            silent=self.silent,
                            result_callback=result_callback,
                        )
                    )
                if scan_wayback:
                    leaks.extend(
                        self.scan_repo_wayback(
                            r, silent=self.silent, result_callback=result_callback
                        )
                    )
                if scan_wiki:
                    leaks.extend(
                        self.scan_repo_wiki(
                            r,
                            token=self.tokens[0] if self.tokens else None,
                            silent=self.silent,
                            result_callback=result_callback,
                        )
                    )
                if scan_releases:
                    leaks.extend(
                        self.scan_repo_releases(
                            r,
                            token=self.tokens[0] if self.tokens else None,
                            silent=self.silent,
                            result_callback=result_callback,
                        )
                    )
                if scan_actions:
                    leaks.extend(
                        self.scan_actions_logs(
                            r,
                            token=self.tokens[0] if self.tokens else None,
                            silent=self.silent,
                            result_callback=result_callback,
                        )
                    )
        if employees and scan_gists:
            for user in employees:
                leaks.extend(
                    self.scan_user_gists(
                        user,
                        keyword,
                        token=self.tokens[0] if self.tokens else None,
                        silent=self.silent,
                        result_callback=result_callback,
                    )
                )
        return leaks
