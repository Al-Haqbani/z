"""Smart JavaScript scanner used by EmploLeaksGuardian.

This module can fetch JavaScript files from multiple sources such as
Wayback Machine archives and optional subdomains. It then runs the leak
detection routines on the retrieved content. The logic is intentionally
kept lightweight so that it can run without heavy dependencies.
"""

from __future__ import annotations

import random
import time
from typing import Iterable, List, Dict

import requests

from core.leak_detector import detect_leaks
from utils.subdomain_enum import enumerate_subdomains
from utils.wayback_scraper import get_archived_js_links
from utils.linkfinder_wrapper import extract_links


def scan_js(url: str) -> List[tuple]:
    """Fetch a single JS file and return detected leaks."""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return detect_leaks(resp.text)
    except Exception:
        pass
    return []


def run_smart_scan(
    domain: str,
    *,
    include_subdomains: bool = False,
    use_wayback: bool = True,
    use_linkfinder: bool = False,
) -> List[Dict[str, str]]:
    """Run a full smart scan against the given domain.

    Parameters
    ----------
    domain: str
        The target domain to inspect.
    include_subdomains: bool
        If True, gather subdomains from crt.sh and scan them as well.
    use_wayback: bool
        If True, download archived JS files from the Wayback Machine.
        Otherwise only attempts to fetch ``https://<domain>/``.
    use_linkfinder: bool
        When enabled, newly discovered JS links from LinkFinder will be
        followed for deeper inspection.
    """

    domains: List[str] = [domain]
    if include_subdomains:
        domains.extend(enumerate_subdomains(domain))

    js_urls: List[str] = []
    for d in domains:
        if use_wayback:
            js_urls.extend(get_archived_js_links(d)[:20])
        else:
            js_urls.append(f"https://{d}")

    results: List[Dict[str, str]] = []
    seen: set[str] = set()
    idx = 0
    while idx < len(js_urls):
        url = js_urls[idx]
        idx += 1
        if url in seen:
            continue
        seen.add(url)
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            text = resp.text
        except Exception:
            continue

        for leak_type, value in detect_leaks(text):
            results.append({"url": url, "leak_type": leak_type, "value": value})

        if use_linkfinder:
            for new_url in extract_links(text):
                if new_url.endswith(".js") and new_url not in seen:
                    js_urls.append(new_url)

        time.sleep(random.uniform(1, 2))

    return results


def run_file_scan(path: str, *, use_linkfinder: bool = False) -> List[Dict[str, str]]:
    """Scan a list of JavaScript URLs or file paths from ``path``.

    Each line of the file should contain a URL to a JS file or a local
    path. The content is downloaded or read and scanned for leaks. When
    ``use_linkfinder`` is True, any additional JS links found within the
    file will also be fetched and scanned.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            js_urls = [l.strip() for l in fh if l.strip()]
    except Exception:
        return []

    results: List[Dict[str, str]] = []
    seen: set[str] = set()
    idx = 0
    while idx < len(js_urls):
        url = js_urls[idx]
        idx += 1
        if url in seen:
            continue
        seen.add(url)
        text = ""
        try:
            if url.startswith("http://") or url.startswith("https://"):
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    continue
                text = resp.text
            else:
                with open(url, "r", encoding="utf-8") as jf:
                    text = jf.read()
        except Exception:
            continue

        for leak_type, value in detect_leaks(text):
            results.append({"url": url, "leak_type": leak_type, "value": value})

        if use_linkfinder:
            for new_url in extract_links(text):
                if new_url.endswith(".js") and new_url not in seen:
                    js_urls.append(new_url)
        time.sleep(random.uniform(0.5, 1.5))
    return results
