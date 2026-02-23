from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_price(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    value = str(value).strip().replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return round(float(value), 2)
    except ValueError:
        return None


def slugify_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def similarity_key(title: str, brand: str | None, model: str | None) -> str:
    base = f"{slugify_text(title)}|{slugify_text(brand or '')}|{slugify_text(model or '')}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def json_dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def json_load(data: str | None, default: Any) -> Any:
    if not data:
        return default
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return default