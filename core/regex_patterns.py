LEAK_PATTERNS = [
    {"name": "GitHub Token", "regex": r"ghp_[A-Za-z0-9]{36}"},
    {"name": "Slack Token", "regex": r"xox[baprs]-[A-Za-z0-9-]{10,48}"},
    {"name": "AWS Access Key", "regex": r"AKIA[0-9A-Z]{16}"},
]
