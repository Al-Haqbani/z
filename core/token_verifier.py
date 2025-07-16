try:
    import requests  # noqa: F401
except Exception:  # pragma: no cover - optional dependency
    requests = None

from utils.http_utils import request_with_backoff, post_with_backoff
from utils.logger import logger


def _get(url: str, *, headers=None, params=None) -> bool:
    if requests is None:
        return False
    resp = request_with_backoff(
        url, headers=headers, params=params, timeout=5, retries=3, silent=True
    )
    if resp is None:
        logger.debug("Verification request failed: %s", url)
        return False
    return resp.status_code == 200


def _post(url: str, *, headers=None, json=None) -> bool:
    if requests is None:
        return False
    resp = post_with_backoff(
        url, headers=headers, json=json, timeout=5, retries=3, silent=True
    )
    if resp is None:
        logger.debug("Verification POST failed: %s", url)
        return False
    return resp.status_code == 200


def verify_slack_token(token: str) -> bool:
    """Check Slack token via the API."""
    if not token:
        return False
    resp = post_with_backoff(
        "https://slack.com/api/auth.test",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
        retries=3,
    )
    return bool(resp and resp.status_code == 200 and resp.json().get("ok"))


def verify_github_token(token: str) -> bool:
    """Check if a GitHub token is valid using the API."""
    if not token:
        return False
    resp = request_with_backoff(
        "https://api.github.com/user",
        headers={"Authorization": f"token {token}"},
        timeout=5,
        retries=3,
    )
    return bool(resp and resp.status_code == 200)


def verify_discord_token(token: str) -> bool:
    """Check Discord bot token via the API."""
    if not token:
        return False
    resp = request_with_backoff(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bot {token}"},
        timeout=5,
        retries=3,
    )
    return bool(resp and resp.status_code == 200)


def verify_telegram_token(token: str) -> bool:
    """Validate Telegram bot token by calling getMe."""
    if not token:
        return False
    resp = request_with_backoff(
        f"https://api.telegram.org/bot{token}/getMe",
        timeout=5,
        retries=3,
    )
    return bool(resp and resp.status_code == 200 and resp.json().get("ok"))


def verify_huggingface_token(token: str) -> bool:
    """Check HuggingFace token via whoami-v2 endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://huggingface.co/api/whoami-v2",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_gitlab_token(token: str) -> bool:
    """Check GitLab personal access token via the API."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://gitlab.com/api/v4/user",
            headers={"PRIVATE-TOKEN": token},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_openai_key(token: str) -> bool:
    """Validate OpenAI API key by requesting the model list."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_replicate_key(token: str) -> bool:
    """Check Replicate API token by listing models."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.replicate.com/v1/models",
            headers={"Authorization": f"Token {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_stability_key(token: str) -> bool:
    """Validate Stability AI API token."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.stability.ai/v1/user/account",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_mistral_key(token: str) -> bool:
    """Check Mistral AI API key using the models endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.mistral.ai/v1/models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_zoom_jwt(token: str) -> bool:
    """Validate Zoom JWT token using the users API."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.zoom.us/v2/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_vercel_token(token: str) -> bool:
    """Check Vercel token via the users API."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.vercel.com/v2/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_railway_token(token: str) -> bool:
    """Check Railway token using the user endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://backboard.railway.app/v2/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False

def verify_cohere_key(token: str) -> bool:
    """Check Cohere API key using token check endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = post_with_backoff(
            "https://api.cohere.ai/token/check",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_asana_token(token: str) -> bool:
    """Validate Asana personal access token."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://app.asana.com/api/1.0/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_bugcrowd_token(token: str) -> bool:
    """Check Bugcrowd API token."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.bugcrowd.com/user",
            headers={"Authorization": f"Token {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_supabase_token(token: str) -> bool:
    """Check Supabase service token via the management API."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.supabase.com/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_salesforce_token(token: str) -> bool:
    """Validate Salesforce OAuth token via userinfo endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://login.salesforce.com/services/oauth2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_notion_token(token: str) -> bool:
    """Validate Notion integration token via the API."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.notion.com/v1/users/me",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
            },
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_facebook_token(token: str) -> bool:
    """Validate Facebook access token using the /me endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://graph.facebook.com/me",
            params={"access_token": token},
            timeout=5,
        )
        return resp.status_code == 200 and resp.json().get("id")
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
    if "cohere" in lt:
        return verify_cohere_key(value)
    if "bugcrowd" in lt:
        return verify_bugcrowd_token(value)
    if "supabase" in lt:
        return verify_supabase_token(value)
    if "salesforce" in lt:
        return verify_salesforce_token(value)
    if "kaggle" in lt:
        return verify_kaggle_key(value)
    if "anthropic" in lt:
        return verify_anthropic_key(value)
    if "gemini" in lt:
        return verify_gemini_key(value)
    if "replicate" in lt or value.startswith("r8_"):
        return verify_replicate_key(value)
    if "stability" in lt:
        return verify_stability_key(value)
    if "notion" in lt or value.startswith("ntn_"):
        return verify_notion_token(value)
    if "digitalocean" in lt:
        return verify_digitalocean_token(value)
    if "facebook" in lt:
        return verify_facebook_token(value)
    if "stripe" in lt or value.startswith("sk_live_"):
        return verify_stripe_key(value)
    if "google" in lt or value.startswith("AIza"):
        return verify_google_api_key(value)
    if value.startswith("ya29."):
        return verify_google_oauth_token(value)
    return False


def verify_google_api_key(token: str) -> bool:
    """Check Google API key by calling a discovery endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://content.googleapis.com/discovery/v1/apis",
            params={"key": token},
            timeout=5,
        )
        return resp.status_code == 200 and "items" in resp.json()
    except Exception:
        return False


def verify_google_oauth_token(token: str) -> bool:
    """Check Google OAuth token validity using tokeninfo."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": token},
            timeout=5,
        )
        return resp.status_code == 200 and "expires_in" in resp.json()
    except Exception:
        return False


POC_COMMANDS = {
    "github": "curl -H 'Authorization: token {token}' https://api.github.com/user",
    "slack": "curl -H 'Authorization: Bearer {token}' https://slack.com/api/auth.test",
    "discord": "curl -H 'Authorization: Bot {token}' https://discord.com/api/v10/users/@me",
    "telegram": "curl https://api.telegram.org/bot{token}/getMe",
    "huggingface": "curl -H 'Authorization: Bearer {token}' https://huggingface.co/api/whoami-v2",
    "gitlab": "curl -H 'PRIVATE-TOKEN: {token}' https://gitlab.com/api/v4/user",
    "openai": "curl -H 'Authorization: Bearer {token}' https://api.openai.com/v1/models",
    "mistral": "curl -H 'Authorization: Bearer {token}' https://api.mistral.ai/v1/models",
    "zoom": "curl -H 'Authorization: Bearer {token}' https://api.zoom.us/v2/users/me",
    "vercel": "curl -H 'Authorization: Bearer {token}' https://api.vercel.com/v2/user",
    "railway": "curl -H 'Authorization: Bearer {token}' https://backboard.railway.app/v2/user",
    "asana": "curl -H 'Authorization: Bearer {token}' https://app.asana.com/api/1.0/users/me",
    "bugcrowd": "curl -H 'Authorization: Token {token}' https://api.bugcrowd.com/user",
    "supabase": "curl -H 'Authorization: Bearer {token}' https://api.supabase.com/v1/projects",
    "salesforce": "curl -H 'Authorization: Bearer {token}' https://login.salesforce.com/services/oauth2/userinfo",
    "kaggle": "curl -H 'Authorization: Bearer {token}' https://www.kaggle.com/api/v1/datasets/list",
    "anthropic": "curl -H 'x-api-key: {token}' https://api.anthropic.com/v1/models",
    "gemini": "curl 'https://generativelanguage.googleapis.com/v1/models?key={token}'",
    "replicate": "curl -H 'Authorization: Token {token}' https://api.replicate.com/v1/models",
    "stability": "curl -H 'Authorization: Bearer {token}' https://api.stability.ai/v1/user/account",
    "notion": "curl -H 'Authorization: Bearer {token}' -H 'Notion-Version: 2022-06-28' https://api.notion.com/v1/users/me",
    "digitalocean": "curl -H 'Authorization: Bearer {token}' https://api.digitalocean.com/v2/account",
    "facebook": "curl 'https://graph.facebook.com/me?access_token={token}'",
    "stripe": "curl -H 'Authorization: Bearer {token}' https://api.stripe.com/v1/charges?limit=1",
    "cohere": "curl -H 'Authorization: Bearer {token}' https://api.cohere.ai/token/check",
    "google": "curl 'https://generativelanguage.googleapis.com/v1/models?key={token}'",
}


def get_poc_command(leak_type: str, token: str) -> str:
    """Return a sample curl command used for verification."""
    lt = leak_type.lower()
    for key, cmd in POC_COMMANDS.items():
        if key in lt:
            return cmd.format(token=token)
    return ""


def verify_digitalocean_token(token: str) -> bool:
    """Check DigitalOcean API token using the account endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.digitalocean.com/v2/account",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_stripe_key(token: str) -> bool:
    """Check Stripe secret key using a minimal API request."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.stripe.com/v1/charges",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 1},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_kaggle_key(token: str) -> bool:
    """Check Kaggle API key using the datasets API."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://www.kaggle.com/api/v1/datasets/list",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_anthropic_key(token: str) -> bool:
    """Validate Anthropic API key using the models endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": token},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def verify_gemini_key(token: str) -> bool:
    """Check Google Gemini API key via the models endpoint."""
    if not token or requests is None:
        return False
    try:
        resp = request_with_backoff(
            "https://generativelanguage.googleapis.com/v1/models",
            params={"key": token},
            timeout=5,
        )
        return resp.status_code == 200 and "models" in resp.json()
    except Exception:
        return False
