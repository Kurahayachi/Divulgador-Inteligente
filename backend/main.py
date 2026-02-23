from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import get_conn, init_db
from .formatter import format_post_message
from .poster.telegram import post_to_telegram
from .poster.whatsapp import post_whatsapp
from .scoring import score_deal
from .scheduler import start_scheduler
from .security import get_current_user, login
from .sources.amazon import fetch_amazon_deals
from .sources.mercadolivre import fetch_mercadolivre_deals
from .utils import json_dump, json_load, now_utc, similarity_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("smartdeals")

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def default_config() -> dict:
    return {
        "mode": "MANUAL",
        "approval_threshold": 70,
        "categories_allowed": ["gamer", "moda", "casa"],
        "blocked_words": ["réplica", "usado", "seminovo"],
        "price_min": 10,
        "price_max": 15000,
        "min_discount_percent": 20,
        "cooldown_days": 7,
        "daily_post_limit": 15,
        "seed_keywords": ["RTX 5060", "Tênis New Balance"],
        "seed_categories": [],
        "mercadolivre": {"client_id": "", "client_secret": "", "redirect_uri": "", "refresh_token": "", "access_token": ""},
        "amazon": {"pa_api_access_key": "", "pa_api_secret": "", "partner_tag": "", "region": "BR", "manual_links": []},
        "telegram": {"bot_token": "", "chat_id": ""},
        "whatsapp": {"provider": "draft", "phone_number_id": "", "token": "", "to_numbers": []},
    }


def get_config() -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT payload FROM app_config WHERE id=1").fetchone()
        if not row:
            cfg = default_config()
            conn.execute(
                "INSERT INTO app_config(id, payload, updated_at) VALUES (1, ?, ?)",
                (json_dump(cfg), now_utc().isoformat()),
            )
            conn.commit()
            return cfg
        return json_load(row["payload"], default_config())


def save_config(payload: dict) -> dict:
    current = get_config()
    current.update(payload)
    with get_conn() as conn:
        conn.execute(
            "UPDATE app_config SET payload=?, updated_at=? WHERE id=1",
            (json_dump(current), now_utc().isoformat()),
        )
        conn.commit()
    return current


def avg_price_last_30_days(conn, source: str, product_id: str) -> float | None:
    since = (now_utc() - timedelta(days=30)).isoformat()
    row = conn.execute(
        "SELECT AVG(price) AS avg_price FROM deal_price_history WHERE deal_source=? AND product_id=? AND captured_at>=?",
        (source, product_id, since),
    ).fetchone()
    return float(row["avg_price"]) if row and row["avg_price"] else None


def apply_scoring(conn, deal_id: int, cfg: dict):
    deal = conn.execute("SELECT * FROM deals WHERE id=?", (deal_id,)).fetchone()
    if not deal:
        return
    avg_price = avg_price_last_30_days(conn, deal["source"], deal["product_id"])
    result = score_deal(dict(deal), cfg, avg_price)
    status = "pending_approval" if cfg.get("mode", "MANUAL") == "MANUAL" else "scored"
    if cfg.get("mode") == "AUTO" and result.score >= int(cfg.get("approval_threshold", 70)):
        status = "approved"
    conn.execute(
        """
        UPDATE deals SET score=?, reasons=?, verdict=?, discount_percent=?, scored_at=?, status=?, updated_at=?
        WHERE id=?
        """,
        (
            result.score,
            json_dump(result.reasons),
            result.verdict,
            result.discount_percent,
            result.scored_at.isoformat(),
            status,
            now_utc().isoformat(),
            deal_id,
        ),
    )


async def collect_and_process() -> dict:
    cfg = get_config()
    started = now_utc().isoformat()
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO scan_runs(started_at,status) VALUES (?,?)", (started, "running"))
        run_id = cur.lastrowid
        conn.commit()

    ml_deals = await fetch_mercadolivre_deals(cfg)
    amazon_deals = await fetch_amazon_deals(cfg)
    incoming = ml_deals + amazon_deals

    new_count = 0
    scored_count = 0
    with get_conn() as conn:
        for d in incoming:
            if d.current_price and (d.current_price < cfg.get("price_min", 0) or d.current_price > cfg.get("price_max", 1e9)):
                continue
            created = now_utc().isoformat()
            sim_key = similarity_key(d.title, d.brand, d.model)
            exists = conn.execute(
                "SELECT id FROM deals WHERE source=? AND product_id=?",
                (d.source, d.product_id),
            ).fetchone()
            if exists:
                continue
            near_dup = conn.execute("SELECT id FROM deals WHERE similarity_key=?", (sim_key,)).fetchone()
            if near_dup:
                continue
            cur = conn.execute(
                """
                INSERT INTO deals(source,product_id,similarity_key,title,url,current_price,old_price,currency,seller_name,seller_reputation,
                is_official_store,shipping_free,sold_quantity,condition,category,image_url,brand,model,coupon,metadata,status,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    d.source,
                    d.product_id,
                    sim_key,
                    d.title,
                    d.url,
                    d.current_price,
                    d.old_price,
                    d.currency,
                    d.seller_name,
                    d.seller_reputation,
                    int(d.is_official_store),
                    int(d.shipping_free),
                    d.sold_quantity,
                    d.condition,
                    d.category,
                    d.image_url,
                    d.brand,
                    d.model,
                    d.coupon,
                    json_dump(d.metadata or {}),
                    "new",
                    created,
                    created,
                ),
            )
            new_count += 1
            deal_id = cur.lastrowid
            conn.execute(
                "INSERT INTO deal_price_history(deal_source,product_id,price,captured_at) VALUES (?,?,?,?)",
                (d.source, d.product_id, d.current_price, created),
            )
            apply_scoring(conn, deal_id, cfg)
            scored_count += 1

        if cfg.get("mode") == "AUTO":
            deals = conn.execute(
                "SELECT * FROM deals WHERE status='approved' AND posted_at IS NULL ORDER BY score DESC LIMIT ?",
                (int(cfg.get("daily_post_limit", 15)),),
            ).fetchall()
            for deal in deals:
                await publish_deal(conn, dict(deal), cfg)

        conn.execute(
            "UPDATE scan_runs SET finished_at=?, status=?, message=?, stats=? WHERE id=?",
            (now_utc().isoformat(), "finished", "ok", json_dump({"new": new_count, "scored": scored_count}), run_id),
        )
        conn.commit()

    return {"new": new_count, "scored": scored_count}


async def publish_deal(conn, deal: dict, cfg: dict) -> dict:
    payload = dict(deal)
    payload["reasons"] = json_load(payload.get("reasons"), [])
    message = format_post_message(payload)

    telegram_status, telegram_external = await post_to_telegram(message, cfg.get("telegram", {}))
    conn.execute(
        "INSERT INTO posts(deal_id,channel,status,external_id,payload,created_at) VALUES (?,?,?,?,?,?)",
        (deal["id"], "telegram", telegram_status, telegram_external, json_dump({"message": message}), now_utc().isoformat()),
    )

    wa_results = await post_whatsapp(message, cfg.get("whatsapp", {}))
    for item in wa_results:
        conn.execute(
            "INSERT INTO posts(deal_id,channel,status,external_id,payload,created_at) VALUES (?,?,?,?,?,?)",
            (
                deal["id"],
                "whatsapp",
                item["status"],
                item["external_id"],
                json_dump({"message": message}),
                now_utc().isoformat(),
            ),
        )

    conn.execute("UPDATE deals SET posted_at=?, status=?, updated_at=? WHERE id=?", (now_utc().isoformat(), "posted", now_utc().isoformat(), deal["id"]))
    return {"telegram": telegram_status, "whatsapp": wa_results}


@app.on_event("startup")
async def startup_event():
    init_db()
    get_config()
    start_scheduler(collect_and_process)


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


app.post("/auth/login")(login)


@app.get("/config")
def read_config(_: str = Depends(get_current_user)):
    cfg = get_config()
    return cfg


@app.put("/config")
def update_config(payload: dict, _: str = Depends(get_current_user)):
    return save_config(payload)


@app.post("/sources/test")
async def test_sources(_: str = Depends(get_current_user)):
    cfg = get_config()
    ml = await fetch_mercadolivre_deals(cfg)
    amz = await fetch_amazon_deals(cfg)
    return {"mercadolivre_count": len(ml), "amazon_count": len(amz)}


@app.post("/scan/run")
async def run_scan(_: str = Depends(get_current_user)):
    return await collect_and_process()


@app.get("/deals")
def list_deals(
    status: str | None = None,
    q: str | None = None,
    min_score: int | None = Query(None, ge=0, le=100),
    source: str | None = None,
    _: str = Depends(get_current_user),
):
    query = "SELECT * FROM deals WHERE 1=1"
    params = []
    if status:
        query += " AND status=?"
        params.append(status)
    if q:
        query += " AND title LIKE ?"
        params.append(f"%{q}%")
    if min_score is not None:
        query += " AND score>=?"
        params.append(min_score)
    if source:
        query += " AND source=?"
        params.append(source)
    query += " ORDER BY created_at DESC LIMIT 300"

    with get_conn() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {**dict(r), "reasons": json_load(r["reasons"], []), "metadata": json_load(r["metadata"], {})}
            for r in rows
        ]


@app.post("/deals/{deal_id}/approve")
async def approve_deal(deal_id: int, _: str = Depends(get_current_user)):
    with get_conn() as conn:
        conn.execute("UPDATE deals SET status='approved', updated_at=? WHERE id=?", (now_utc().isoformat(), deal_id))
        deal = conn.execute("SELECT * FROM deals WHERE id=?", (deal_id,)).fetchone()
        if not deal:
            raise HTTPException(404, "Deal não encontrado")
        cfg = get_config()
        result = await publish_deal(conn, dict(deal), cfg)
        conn.commit()
        return result


@app.post("/deals/{deal_id}/reject")
def reject_deal(deal_id: int, _: str = Depends(get_current_user)):
    with get_conn() as conn:
        conn.execute("UPDATE deals SET status='rejected', updated_at=? WHERE id=?", (now_utc().isoformat(), deal_id))
        conn.commit()
    return {"status": "rejected"}


@app.post("/deals/{deal_id}/post")
async def force_post(deal_id: int, _: str = Depends(get_current_user)):
    cfg = get_config()
    with get_conn() as conn:
        deal = conn.execute("SELECT * FROM deals WHERE id=?", (deal_id,)).fetchone()
        if not deal:
            raise HTTPException(404, "Deal não encontrado")
        result = await publish_deal(conn, dict(deal), cfg)
        conn.commit()
        return result


@app.get("/posts")
def list_posts(_: str = Depends(get_current_user)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT 300").fetchall()
        return [dict(r) for r in rows]


@app.get("/runs")
def scan_runs(_: str = Depends(get_current_user)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM scan_runs ORDER BY id DESC LIMIT 100").fetchall()
        return [{**dict(r), "stats": json_load(r["stats"], {})} for r in rows]