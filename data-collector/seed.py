#!/usr/bin/env python3
"""One-shot demo seeder: wipe the DB and backfill 5 weeks of job history.

Intended for peer-review / demo runs so reviewers see a populated dashboard
without waiting for five ingest cycles.

What it does:
  1. TRUNCATE jobs, skill_trends, company_trends.
  2. Fetch jobs from The Muse across the configured categories.
  3. Distribute the insertion times uniformly across the last ``WEEKS_BACK``
     ISO weeks (so ``date_collected`` is backdated).
  4. Publish an ``analyze_jobs`` RabbitMQ message so the analyzer rebuilds
     skill_trends and company_trends from the freshly seeded jobs.

Run from inside the data-collector container, where ``DATABASE_URL`` and
``AMQP_URL`` are already attached as Fly secrets:

    fly ssh console -a job-market-trend-analyzer-collector -C "python seed.py"
"""
from __future__ import annotations

import logging
import os
import random
import sys
from datetime import datetime, timedelta

from muse_client import MuseClient

from shared.db import create_app, db, ensure_schema
from shared.gateway import JobDataGateway
from shared.models import CompanyTrend, Job, SkillTrend

DEFAULT_CATEGORIES = (
    "Software Engineer,Data and Analytics,Data Science,DevOps and Sysadmin"
)
WEEKS_BACK = int(os.environ.get("SEED_WEEKS_BACK", "5"))
PAGES_PER_CATEGORY = int(os.environ.get("SEED_PAGES", "3"))
SEED_RNG = int(os.environ.get("SEED_RANDOM_SEED", "0"))


def configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    return logging.getLogger("seed")


def load_categories() -> list[str]:
    raw = os.environ.get("SEED_CATEGORIES") or os.environ.get(
        "COLLECTOR_CATEGORIES", DEFAULT_CATEGORIES
    )
    return [c.strip() for c in raw.split(",") if c.strip()]


def wipe(log: logging.Logger) -> None:
    log.info("wiping skill_trends, company_trends, jobs")
    db.session.query(SkillTrend).delete()
    db.session.query(CompanyTrend).delete()
    db.session.query(Job).delete()
    db.session.commit()


def backdate(now: datetime, weeks_back: int, rng: random.Random) -> datetime:
    """Return a uniformly random datetime within the last ``weeks_back`` weeks."""
    seconds = rng.uniform(0, weeks_back * 7 * 24 * 3600)
    return now - timedelta(seconds=seconds)


def notify_analyzer(total: int, log: logging.Logger) -> None:
    if not os.environ.get("AMQP_URL"):
        log.warning(
            "AMQP_URL is unset; skill/company trends will not rebuild automatically"
        )
        return
    from shared.messaging import ANALYZE_JOBS, publish

    publish(ANALYZE_JOBS, {"trigger": "seed", "ingested": total})
    log.info("published analyze_jobs (ingested=%d)", total)


def main() -> int:
    log = configure_logging()
    log.info(
        "seed starting weeks_back=%d pages=%d seed=%d",
        WEEKS_BACK,
        PAGES_PER_CATEGORY,
        SEED_RNG,
    )

    rng = random.Random(SEED_RNG) if SEED_RNG else random.Random()
    categories = load_categories()

    app = create_app("seed")
    with app.app_context():
        ensure_schema()
        wipe(log)

        client = MuseClient(base_url=os.environ.get("MUSE_API_URL"))
        gateway = JobDataGateway()
        now = datetime.utcnow()
        total = 0
        for category in categories:
            raw = client.fetch_jobs(category, PAGES_PER_CATEGORY)
            parsed: list[dict] = []
            for j in raw:
                rec = MuseClient.parse_job(j)
                rec["date_collected"] = backdate(now, WEEKS_BACK, rng)
                parsed.append(rec)
            saved = gateway.create_many(parsed)
            total += saved
            log.info(
                "category=%s fetched=%d saved=%d", category, len(raw), saved
            )

        log.info("seed inserted %d jobs across %d weeks", total, WEEKS_BACK)

    notify_analyzer(total, log)
    log.info("seed done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
