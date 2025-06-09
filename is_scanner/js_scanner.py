import requests

from core.leak_detector import detect_leaks


def scan_js(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        return detect_leaks(resp.text)
    return []
