#!/usr/bin/env python3
"""Always-on consumer of the ``collect_jobs`` queue.

Each message triggers a fresh collector run. After each successful run the
collector's ``main()`` also publishes onto ``analyze_jobs`` so the analyzer
worker picks up immediately downstream.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any

from collector import collect_all, configure_logging, load_categories
from muse_client import MuseClient

from shared.db import create_app, ensure_schema
from shared.gateway import JobDataGateway
from shared.health_server import start_if_enabled as start_health_server
from shared.messaging import ANALYZE_JOBS, COLLECT_JOBS, consume_forever, publish


def handle_message(payload: dict[str, Any], log: logging.Logger) -> None:
    """Run one collection cycle in response to a queue message."""
    log.info("collect_jobs payload=%s", payload)

    categories = load_categories()
    pages = int(os.environ.get("COLLECTOR_PAGES", "5"))
    app = create_app("collector-consumer")
    with app.app_context():
        ensure_schema()
        client = MuseClient(base_url=os.environ.get("MUSE_API_URL"))
        total = collect_all(client, JobDataGateway(), categories, pages, log)

    publish(ANALYZE_JOBS, {"trigger": "collector", "ingested": total})
    log.info("collect cycle complete total=%d", total)


def main() -> int:
    log = configure_logging()
    log.info("collect_jobs consumer starting")
    start_health_server()
    consume_forever(COLLECT_JOBS, lambda payload: handle_message(payload, log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
