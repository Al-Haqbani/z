import json
from pathlib import Path

PROGRAMS_FILE = Path(__file__).resolve().parent.parent / 'data' / 'bugbounty_programs.json'


def load_programs():
    if PROGRAMS_FILE.exists():
        with open(PROGRAMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def print_programs():
    programs = load_programs()
    if not programs:
        print("No bug bounty programs available.")
        return
    for p in programs:
        print(f"- {p['name']}\n  Scope: {p['scope']}\n  Report: {p['report_url']}\n")
