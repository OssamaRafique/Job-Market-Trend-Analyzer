#!/usr/bin/env python3
"""Always-on consumer of the ``analyze_jobs`` queue.

Each message triggers a re-aggregation pass over the last ``ANALYZER_WINDOW_DAYS``
days of raw jobs, upserting ``skill_trends`` and ``company_trends``.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any

from analyzer import configure_logging, run_analysis

from shared.db import create_app, ensure_schema
from shared.gateway import JobDataGateway, TrendDataGateway
from shared.health_server import start_if_enabled as start_health_server
from shared.messaging import ANALYZE_JOBS, consume_forever


def handle_message(payload: dict[str, Any], log: logging.Logger) -> None:
    """Run one aggregation cycle in response to a queue message."""
    log.info("analyze_jobs payload=%s", payload)
    days = int(os.environ.get("ANALYZER_WINDOW_DAYS", "28"))
    app = create_app("analyzer-consumer")
    with app.app_context():
        ensure_schema()
        skills, companies = run_analysis(
            JobDataGateway(), TrendDataGateway(), days, log
        )
    log.info("analysis cycle complete skills=%d companies=%d", skills, companies)


def main() -> int:
    log = configure_logging()
    log.info("analyze_jobs consumer starting")
    start_health_server()
    consume_forever(ANALYZE_JOBS, lambda payload: handle_message(payload, log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
