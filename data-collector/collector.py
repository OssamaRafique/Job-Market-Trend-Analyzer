#!/usr/bin/env python3
"""Data Collector for the Job Market Trend Analyzer.

One invocation = one collection: fetch N pages per category from The Muse API,
parse, and persist via JobDataGateway. Exits 0 after commit.
"""
from __future__ import annotations

import logging
import os
import sys

from muse_client import MuseClient

from shared.db import create_app, ensure_schema
from shared.gateway import JobDataGateway
from shared.health_server import start_if_enabled as start_health_server

DEFAULT_CATEGORIES = "Software Engineer,Data and Analytics,Data Science,DevOps and Sysadmin"


def _notify_analyzer(total: int, log: logging.Logger) -> None:
    """Publish an ``analyze_jobs`` message so the analyzer can run.

    No-op when ``AMQP_URL`` is unset.
    """
    if not os.environ.get("AMQP_URL"):
        return
    try:
        from shared.messaging import ANALYZE_JOBS, publish

        publish(ANALYZE_JOBS, {"trigger": "collector", "ingested": total})
    except Exception:
        log.exception("failed to publish analyze_jobs (continuing)")


def configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    return logging.getLogger("collector")


def load_categories() -> list[str]:
    raw = os.environ.get("COLLECTOR_CATEGORIES", DEFAULT_CATEGORIES)
    return [c.strip() for c in raw.split(",") if c.strip()]


def collect_all(
    client: MuseClient,
    gateway: JobDataGateway,
    categories: list[str],
    pages: int,
    log: logging.Logger,
) -> int:
    total = 0
    for category in categories:
        raw = client.fetch_jobs(category, pages)
        parsed = [MuseClient.parse_job(job) for job in raw]
        saved = gateway.create_many(parsed)
        log.info(
            "category=%s fetched=%d saved=%d", category, len(raw), saved
        )
        total += saved
    return total


def main() -> int:
    log = configure_logging()
    log.info("collector starting")

    start_health_server()

    categories = load_categories()
    pages = int(os.environ.get("COLLECTOR_PAGES", "5"))
    log.info("categories=%s pages=%d", categories, pages)

    app = create_app("collector")
    with app.app_context():
        ensure_schema()
        client = MuseClient(base_url=os.environ.get("MUSE_API_URL"))
        gateway = JobDataGateway()
        total = collect_all(client, gateway, categories, pages, log)

    _notify_analyzer(total, log)

    log.info("collector done total=%d", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
