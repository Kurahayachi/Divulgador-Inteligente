from __future__ import annotations

from typing import Any

import httpx

from ..config import settings
from ..models import DealInput


ML_API_BASE = "https://api.mercadolibre.com"


async def fetch_mercadolivre_deals(config: dict[str, Any]) -> list[DealInput]:
    queries = config.get("seed_keywords", [])
    category_map = config.get("seed_categories", [])
    if not queries:
        queries = ["RTX 5060", "Tênis New Balance"]

    headers = {}
    token = config.get("mercadolivre", {}).get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    deals: list[DealInput] = []
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        for q in queries[:5]:
            params = {"q": q, "limit": 10}
            if category_map:
                params["category"] = category_map[0]
            try:
                resp = await client.get(f"{ML_API_BASE}/sites/MLB/search", params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue
            for item in data.get("results", []):
                deals.append(
                    DealInput(
                        source="mercadolivre",
                        product_id=item.get("id") or item.get("catalog_product_id") or item.get("permalink", ""),
                        title=item.get("title", "Sem título"),
                        url=item.get("permalink", ""),
                        current_price=float(item.get("price") or 0),
                        old_price=float(item.get("original_price")) if item.get("original_price") else None,
                        seller_name=(item.get("seller") or {}).get("nickname"),
                        seller_reputation=((item.get("seller") or {}).get("seller_reputation") or {}).get("level_id"),
                        is_official_store=bool((item.get("official_store_id") or 0) > 0),
                        shipping_free=bool((item.get("shipping") or {}).get("free_shipping")),
                        sold_quantity=item.get("sold_quantity"),
                        condition=item.get("condition") or "new",
                        category=item.get("category_id"),
                        image_url=item.get("thumbnail"),
                        brand=((item.get("attributes") or [{}])[0] or {}).get("value_name"),
                        metadata={"raw": item},
                    )
                )
    return deals
