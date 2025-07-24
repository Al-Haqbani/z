import re
import requests
from urllib.parse import urljoin

_PATH_RE = re.compile(r"['\"](/[^'\"\s]{3,})['\"]")

GITHUB_RAW = "https://raw.githubusercontent.com/{repo}/{sha}/{path}"


def fetch_repo_paths(repo: str, token: str | None = None, *, branch='main', limit=100):
    """Fetch raw files from a repo and return hidden paths."""
    api = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f"token {token}"
    resp = requests.get(api, headers=headers, timeout=10)
    if resp.status_code != 200:
        return []
    data = resp.json()
    paths = []
    for item in data.get('tree', [])[:limit]:
        if item.get('type') == 'blob' and item['path'].endswith(('.js', '.ts', '.go', '.py')):
            raw_url = GITHUB_RAW.format(repo=repo, sha=branch, path=item['path'])
            r = requests.get(raw_url, headers=headers, timeout=10)
            if r.status_code == 200:
                paths.extend(_PATH_RE.findall(r.text))
    return list(set(paths))


def test_paths(domain: str, paths):
    results = []
    for p in paths:
        url = urljoin(domain if domain.startswith('http') else 'https://' + domain, p)
        try:
            g = requests.get(url, timeout=10).status_code
        except Exception:
            g = None
        try:
            po = requests.post(url, timeout=10).status_code
        except Exception:
            po = None
        results.append({'path': p, 'get': g, 'post': po})
    return results
