LEAK_PATTERNS = [
    {"name": "GitHub Token", "regex": r"ghp_[A-Za-z0-9]{36}"},
    {"name": "Slack Token", "regex": r"xox[baprs]-[A-Za-z0-9-]{10,48}"},
    {"name": "AWS Access Key", "regex": r"AKIA[0-9A-Z]{16}"},
    {"name": "AWS Secret Key", "regex": r"(?i)aws(.{0,20})?(?:['\"][0-9a-zA-Z\/+=]{40}['\"])"},
    {"name": "Google API Key", "regex": r"AIza[0-9A-Za-z\-_]{35}"},
    {"name": "Stripe Secret", "regex": r"sk_live_[0-9a-zA-Z]{24}"},
    {"name": "Twilio API Key", "regex": r"SK[0-9a-fA-F]{32}"},
    {"name": "SendGrid Key", "regex": r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}"},
    {"name": "Facebook Access Token", "regex": r"EAACEdEose0cBA[0-9A-Za-z]+"},
]
