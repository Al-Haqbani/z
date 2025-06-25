import requests


def verify_slack_token(token: str) -> bool:
    """Check Slack token via the API."""
    if not token:
        return False
    try:
        resp = requests.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200 and resp.json().get("ok")
    except Exception:
        return False


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


def verify_discord_token(token: str) -> bool:
    """Check Discord bot token via the API."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bot {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_telegram_token(token: str) -> bool:
    """Validate Telegram bot token by calling getMe."""
    if not token:
        return False
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=5,
        )
        return resp.status_code == 200 and resp.json().get("ok")
    except Exception:
        return False


def verify_huggingface_token(token: str) -> bool:
    """Check HuggingFace token via whoami-v2 endpoint."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://huggingface.co/api/whoami-v2",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_gitlab_token(token: str) -> bool:
    """Check GitLab personal access token via the API."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://gitlab.com/api/v4/user",
            headers={"PRIVATE-TOKEN": token},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_openai_key(token: str) -> bool:
    """Validate OpenAI API key by requesting the model list."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_mistral_key(token: str) -> bool:
    """Check Mistral AI API key using the models endpoint."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://api.mistral.ai/v1/models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_zoom_jwt(token: str) -> bool:
    """Validate Zoom JWT token using the users API."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://api.zoom.us/v2/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_vercel_token(token: str) -> bool:
    """Check Vercel token via the users API."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://api.vercel.com/v2/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_railway_token(token: str) -> bool:
    """Check Railway token using the user endpoint."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://backboard.railway.app/v2/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_asana_token(token: str) -> bool:
    """Validate Asana personal access token."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://app.asana.com/api/1.0/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_bugcrowd_token(token: str) -> bool:
    """Check Bugcrowd API token."""
    if not token:
        return False
    try:
        resp = requests.get(
            "https://api.bugcrowd.com/user",
            headers={"Authorization": f"Token {token}"},
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
    if "slack" in lt or value.startswith("xox"):
        return verify_slack_token(value)
    if "discord" in lt:
        return verify_discord_token(value)
    if "telegram" in lt or value.count(":") == 1:
        # Telegram bot tokens contain a single ':'
        return verify_telegram_token(value)
    if "huggingface" in lt or value.startswith("hf_"):
        return verify_huggingface_token(value)
    if "gitlab" in lt or value.startswith("glpat-"):
        return verify_gitlab_token(value)
    if "openai" in lt or value.startswith("sk-"):
        return verify_openai_key(value)
    if "mistral" in lt:
        return verify_mistral_key(value)
    if "zoom" in lt:
        return verify_zoom_jwt(value)
    if "vercel" in lt:
        return verify_vercel_token(value)
    if "railway" in lt:
        return verify_railway_token(value)
    if "asana" in lt:
        return verify_asana_token(value)
    if "bugcrowd" in lt:
        return verify_bugcrowd_token(value)
    return False
