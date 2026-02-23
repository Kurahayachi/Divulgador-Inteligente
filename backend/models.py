from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DealInput:
    source: str
    product_id: str
    title: str
    url: str
    current_price: float
    old_price: float | None = None
    currency: str = "BRL"
    seller_name: str | None = None
    seller_reputation: str | None = None
    is_official_store: bool = False
    shipping_free: bool = False
    sold_quantity: int | None = None
    condition: str = "new"
    category: str | None = None
    image_url: str | None = None
    brand: str | None = None
    model: str | None = None
    coupon: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ScoreResult:
    score: int
    reasons: list[str]
    verdict: str
    discount_percent: float
    below_avg_bonus: float
    scored_at: datetime