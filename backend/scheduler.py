from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings

scheduler = AsyncIOScheduler()


def start_scheduler(scan_func):
    if scheduler.running:
        return
    scheduler.add_job(scan_func, "interval", minutes=settings.scheduler_interval_minutes, id="periodic_scan")
    scheduler.start()