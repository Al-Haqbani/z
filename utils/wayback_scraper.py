import requests


def get_archived_js_links(domain):
    url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*.js&output=json&fl=original&collapse=urlkey"
    links = []
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            links = [entry[0] for entry in data[1:]]
    except Exception:
        pass
    return links
