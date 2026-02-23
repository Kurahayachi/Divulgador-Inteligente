from __future__ import annotations

from datetime import timedelta

from .models import ScoreResult
from .utils import now_utc


def score_deal(deal: dict, config: dict, avg_price_30d: float | None) -> ScoreResult:
    reasons: list[str] = []
    score = 50

    blocked_words = [w.lower() for w in config.get("blocked_words", [])]
    discount_rule = float(config.get("min_discount_percent", 20))
    title = (deal.get("title") or "").lower()
    condition = (deal.get("condition") or "new").lower()
    seller_rep = (deal.get("seller_reputation") or "").lower()

    current = float(deal.get("current_price") or 0)
    old = float(deal.get("old_price") or 0) if deal.get("old_price") else 0
    discount_percent = round(((old - current) / old) * 100, 2) if old > 0 and current > 0 else 0.0

    if deal.get("is_official_store"):
        score += 30
        reasons.append("Loja oficial")
    if any(k in seller_rep for k in ["green", "5", "high"]):
        score += 20
        reasons.append("Reputação alta")
    if (deal.get("sold_quantity") or 0) >= 100:
        score += 10
        reasons.append("Alta quantidade vendida")
    if discount_percent >= discount_rule:
        score += 20
        reasons.append(f"Desconto >= {discount_rule:.0f}%")
    if deal.get("shipping_free"):
        score += 10
        reasons.append("Frete grátis")

    if any(word in title for word in blocked_words):
        score -= 50
        reasons.append("Contém palavra bloqueada")
    if condition != "new":
        score -= 40
        reasons.append("Produto não é novo")
    if any(k in seller_rep for k in ["low", "red"]):
        score -= 30
        reasons.append("Reputação baixa")
    if current > 0 and old > 0 and current <= old * 0.4 and any(k in seller_rep for k in ["low", "red"]):
        score -= 20
        reasons.append("Variação suspeita")

    below_avg_bonus = 0.0
    if avg_price_30d and current > 0:
        diff = ((avg_price_30d - current) / avg_price_30d) * 100
        if diff >= 15:
            below_avg_bonus = 15
            score += 15
            reasons.append("Preço muito abaixo da média de 30 dias")

    score = max(0, min(100, score))
    verdict = "Vale a pena" if score >= 70 else "Avaliar com cautela"
    return ScoreResult(
        score=score,
        reasons=reasons,
        verdict=verdict,
        discount_percent=discount_percent,
        below_avg_bonus=below_avg_bonus,
        scored_at=now_utc() + timedelta(0),
    )