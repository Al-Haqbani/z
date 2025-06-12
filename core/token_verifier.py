import requests


def verify_github_token(token: str) -> bool:
    """Check if a GitHub token is valid using the API."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_token(leak_type: str, value: str) -> bool:
    """Return True if the token looks valid via online checks."""
    lt = leak_type.lower()
    if "github" in lt or value.startswith(("ghp_", "gho_")):
        return verify_github_token(value)
    # Other token types could be added here
    return True
