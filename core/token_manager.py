import os


def get_token(name: str, env_var: str) -> str | None:
    """Prompt the user for a token if not provided via environment variable."""
    token = os.environ.get(env_var)
    if not token:
        token = input(f"{name} Token (press Enter to skip): ").strip() or None
    return token


def get_github_token() -> str | None:
    """Backward compatible helper for obtaining the GitHub token."""
    return get_token("GitHub", "GITHUB_TOKEN")
