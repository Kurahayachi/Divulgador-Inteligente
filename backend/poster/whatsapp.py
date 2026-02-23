from __future__ import annotations

from urllib.parse import quote

import httpx


def draft_whatsapp(message: str) -> str:
    return f"https://wa.me/?text={quote(message)}"


async def post_whatsapp(message: str, cfg: dict) -> list[dict]:
    provider = cfg.get("provider", "draft")
    if provider == "draft":
        return [{"status": "draft", "external_id": draft_whatsapp(message)}]

    token = cfg.get("token")
    phone_number_id = cfg.get("phone_number_id")
    numbers = cfg.get("to_numbers", [])
    if not token or not phone_number_id or not numbers:
        return [{"status": "failed", "external_id": "whatsapp_cloud_not_configured"}]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"

    results = []
    async with httpx.AsyncClient(timeout=20) as client:
        for number in numbers:
            payload = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "text",
                "text": {"preview_url": False, "body": message},
            }
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code >= 400:
                results.append({"status": "failed", "external_id": resp.text})
            else:
                results.append(
                    {
                        "status": "posted",
                        "external_id": str(resp.json().get("messages", [{}])[0].get("id", "ok")),
                    }
                )
    return results