from __future__ import annotations

import re
from typing import Any

import httpx

from ..config import settings
from ..models import DealInput


ASIN_RE = re.compile(r"(?:dp|gp/product)/([A-Z0-9]{10})")


async def fetch_amazon_deals(config: dict[str, Any]) -> list[DealInput]:
    amazon_cfg = config.get("amazon", {})
    links: list[str] = amazon_cfg.get("manual_links", [])
    if not links:
        return []

    deals: list[DealInput] = []
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True) as client:
        for link in links[:20]:
            asin_match = ASIN_RE.search(link)
            asin = asin_match.group(1) if asin_match else link[-10:]
            try:
                resp = await client.get(link, headers={"User-Agent": "SmartDealsBot/1.0"})
                status_ok = resp.status_code < 400
                title = "Amazon Item"
                if status_ok:
                    title_match = re.search(r"<title>(.*?)</title>", resp.text, re.I | re.S)
                    if title_match:
                        title = title_match.group(1).strip()
                else:
                    title = f"ASIN {asin}"
            except Exception:
                status_ok = False
                title = f"ASIN {asin}"
            deals.append(
                DealInput(
                    source="amazon",
                    product_id=asin,
                    title=title,
                    url=link,
                    current_price=0.0,
                    old_price=None,
                    seller_name="Amazon",
                    seller_reputation="high",
                    is_official_store=True,
                    shipping_free=False,
                    condition="new",
                    metadata={"validated": status_ok, "mode": "light"},
                )
            )
    return deals