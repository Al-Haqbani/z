import os
import re
from .subdomain_enum import enumerate_subdomains


def build_wordlist(keyword: str, include_subdomains: bool = True, repos=None) -> str:
    """Generate a simple wordlist based on the target keyword, subdomains, and repository names.

    Returns the path to the created wordlist file.
    """
    words = set()

    def add_word(w: str):
        w = w.strip()
        if not w:
            return
        words.add(w.lower())
        words.add(w.upper())
        words.add(w.capitalize())

    base_parts = re.split(r"[^a-zA-Z0-9]+", keyword)
    for part in base_parts:
        add_word(part)

    if include_subdomains:
        for sub in enumerate_subdomains(keyword):
            parts = re.split(r"[^a-zA-Z0-9]+", sub)
            for p in parts:
                add_word(p)

    if repos:
        for repo in repos:
            name = repo.split('/')[-1]
            for part in re.split(r"[^a-zA-Z0-9]+", name):
                add_word(part)

    os.makedirs('wordlists', exist_ok=True)
    path = os.path.join('wordlists', f"{keyword}_wordlist.txt")
    with open(path, 'w', encoding='utf-8') as f:
        for w in sorted(words):
            f.write(w + '\n')
    return path
