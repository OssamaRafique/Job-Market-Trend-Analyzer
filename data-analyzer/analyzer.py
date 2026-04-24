#!/usr/bin/env python3
"""Data Analyzer for the Job Market Trend Analyzer.

One invocation = re-aggregate the last ``ANALYZER_WEEKS`` weeks of raw jobs
into skill_trends and company_trends. Existing rows for those weeks are
overwritten (idempotent).
"""
from __future__ import annotations

import logging
import os
import sys

from aggregations import aggregate_companies, aggregate_skills

from shared.db import create_app, db
from shared.gateway import JobDataGateway, TrendDataGateway
from shared.health_server import start_if_enabled as start_health_server


def configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    return logging.getLogger("analyzer")


def run_analysis(
    jobs_gateway: JobDataGateway,
    trends_gateway: TrendDataGateway,
    days: int,
    log: logging.Logger,
) -> tuple[int, int]:
    jobs = jobs_gateway.find_recent(days=days)
    log.info("loaded jobs count=%d days=%d", len(jobs), days)

    skill_counts = aggregate_skills(jobs)
    company_counts = aggregate_companies(jobs)

    for (skill, week, category), count in skill_counts.items():
        trends_gateway.upsert_skill_trend(
            skill=skill, count=count, week=week, category=category
        )

    for (company, week, category), count in company_counts.items():
        trends_gateway.upsert_company_trend(
            company=company, count=count, week=week, category=category
        )

    log.info(
        "analysis done skills=%d companies=%d",
        len(skill_counts),
        len(company_counts),
    )
    return len(skill_counts), len(company_counts)


def main() -> int:
    log = configure_logging()
    log.info("analyzer starting")

    start_health_server()

    days = int(os.environ.get("ANALYZER_WINDOW_DAYS", "28"))

    app = create_app("analyzer")
    with app.app_context():
        db.create_all()
        run_analysis(JobDataGateway(), TrendDataGateway(), days, log)

    log.info("analyzer done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
