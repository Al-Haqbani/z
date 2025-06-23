import os


def get_token(name: str, env_var: str):
    """Return a token or list of tokens from env or user input."""
    token = os.environ.get(env_var)
    if not token:
        token = input(
            f"{name} Token (comma separated for multiple, press Enter to skip): "
        ).strip()
    if not token:
        return None
    # Allow a comma separated list
    if "," in token:
        return [t.strip() for t in token.split(",") if t.strip()]
    return token.strip()


def get_github_token() -> str | None:
    """Backward compatible helper for obtaining the GitHub token."""
    return get_token("GitHub", "GITHUB_TOKEN")
