from __future__ import annotations

import httpx


async def post_to_telegram(message: str, cfg: dict) -> tuple[str, str]:
    token = cfg.get("bot_token")
    chat_id = cfg.get("chat_id")
    if not token or not chat_id:
        return "skipped", "telegram_not_configured"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "disable_web_page_preview": False}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code >= 400:
        return "failed", resp.text
    body = resp.json()
    return "posted", str(body.get("result", {}).get("message_id", "ok"))