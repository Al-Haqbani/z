import requests
from urllib.parse import urljoin

DEFAULT_WORDLIST = [
    '/api', '/api/v1', '/api/v2', '/api/login', '/api/auth',
    '/api/user', '/api/users', '/api/admin', '/api/test'
]

def fuzz_api(domain: str, *, paths=None, timeout=10):
    paths = paths or DEFAULT_WORDLIST
    results = []
    for p in paths:
        url = urljoin(domain if domain.startswith('http') else 'https://' + domain, p)
        try:
            r = requests.get(url, timeout=timeout)
            results.append({'path': p, 'status': r.status_code})
        except Exception:
            results.append({'path': p, 'status': None})
    return results
