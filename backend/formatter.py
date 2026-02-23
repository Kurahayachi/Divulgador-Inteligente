from __future__ import annotations


def brl(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_post_message(deal: dict) -> str:
    before_after = f"{brl(deal.get('old_price'))} ➜ {brl(deal.get('current_price'))}" if deal.get("old_price") else brl(deal.get("current_price"))
    reasons = deal.get("reasons") or []
    reason_line = reasons[0] if reasons else "Preço monitorado automaticamente."

    return (
        "📊 Análise Rápida\n"
        f"🛒 {deal.get('title')}\n"
        f"💵 {before_after}\n"
        f"🏪 {deal.get('seller_name') or 'Loja não informada'} | reputação: {deal.get('seller_reputation') or 'n/d'}\n"
        f"🎟 Cupom: {deal.get('coupon') or 'Sem cupom'}\n"
        f"🧠 Vale a pena? {deal.get('verdict')}. {reason_line}.\n"
        f"🔗 {deal.get('url')}"
    )