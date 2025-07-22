import os
import requests


def send_telegram(text: str, token: str = None, chat_id: str = None):
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=5)
    except Exception:
        pass


def send_discord(text: str, webhook: str = None):
    webhook = webhook or os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        return
    try:
        requests.post(webhook, json={"content": text}, timeout=5)
    except Exception:
        pass
