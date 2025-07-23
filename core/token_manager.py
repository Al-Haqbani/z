import os


def get_github_token():
    """Return GitHub token from env or user input."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        token = input("GitHub Token (press Enter to skip): ").strip() or None
    return token
