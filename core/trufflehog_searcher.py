import json
import subprocess
import os
import random
from .github_api import GitHubSearcher

class TruffleHogSearcher:
    """Run trufflehog against GitHub repositories."""

    def __init__(self, token=None, silent=False, **_):
        self.token = token
        self.silent = silent

    def _scan_repo(self, repo, result_callback=None):
        url = f"https://github.com/{repo}"
        cmd = ["trufflehog", "--json", url]
        env = os.environ.copy()
        if self.token:
            env["GITHUB_TOKEN"] = self.token
        results = []
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                val = data.get("stringsFound") or []
                for secret in val:
                    item = {
                        "source": "TruffleHog",
                        "file": f"{url}/{data.get('path','')}",
                        "leak_type": "trufflehog-match",
                        "value": secret,
                    }
                    results.append(item)
                    if result_callback:
                        result_callback(item, len(results))
            proc.communicate()
            if proc.returncode != 0 and not self.silent:
                err = proc.stderr.read()
                print(f"TruffleHog exited with {proc.returncode}: {err}")
        except FileNotFoundError:
            if not self.silent:
                print("trufflehog command not found. Install it via 'pip install trufflehog'.")
        except Exception as exc:
            if not self.silent:
                print(f"TruffleHog scan error for {repo}: {exc}")
        return results

    def search(self, keyword, employees=None, organization=None, repo=None, progress_callback=None, result_callback=None, **kwargs):
        repos = []
        if repo:
            repos.append(repo)
        if organization:
            repos.extend(GitHubSearcher.get_org_repos(organization, token=self.token))
        if employees:
            for user in employees:
                repos.extend(GitHubSearcher.get_user_repos(user, token=self.token))
        repos = [r for r in repos if keyword.lower() in r.lower()]
        leaks = []
        total = len(repos)
        for idx, r in enumerate(repos, 1):
            if progress_callback:
                progress_callback({"repo": r, "index": idx, "total": total})
            leaks.extend(self._scan_repo(r, result_callback=result_callback))
        return leaks
