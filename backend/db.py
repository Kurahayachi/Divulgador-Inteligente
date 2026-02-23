from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS app_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    product_id TEXT NOT NULL,
    similarity_key TEXT,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    current_price REAL NOT NULL,
    old_price REAL,
    currency TEXT NOT NULL DEFAULT 'BRL',
    seller_name TEXT,
    seller_reputation TEXT,
    is_official_store INTEGER DEFAULT 0,
    shipping_free INTEGER DEFAULT 0,
    sold_quantity INTEGER,
    condition TEXT,
    category TEXT,
    image_url TEXT,
    brand TEXT,
    model TEXT,
    coupon TEXT,
    metadata TEXT,
    score INTEGER,
    reasons TEXT,
    verdict TEXT,
    discount_percent REAL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    scored_at TEXT,
    posted_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_deals_source_product ON deals(source, product_id);

CREATE TABLE IF NOT EXISTS deal_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_source TEXT NOT NULL,
    product_id TEXT NOT NULL,
    price REAL NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    external_id TEXT,
    payload TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(deal_id) REFERENCES deals(id)
);

CREATE TABLE IF NOT EXISTS scan_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    message TEXT,
    stats TEXT
);
"""


def init_db() -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(settings.db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()