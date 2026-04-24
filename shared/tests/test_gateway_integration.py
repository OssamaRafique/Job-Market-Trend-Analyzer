"""Integration tests for JobDataGateway and TrendDataGateway."""
from __future__ import annotations

from datetime import datetime, timedelta

import os

import pytest


def _real_db_available() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("USE_REAL_DB") != "1":
        return False
    return url.startswith("postgresql://") or url.startswith("postgres://")


requires_real_db = pytest.mark.skipif(
    not _real_db_available(),
    reason="set DATABASE_URL and USE_REAL_DB=1 to run integration tests",
)

pytestmark = [pytest.mark.integration, requires_real_db]


def test_job_gateway_create_and_find(db_app):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    gateway.create(
        title="Python Engineer",
        company="Acme",
        category="Software Engineer",
        level="Senior",
        location="Remote",
    )
    items, total = gateway.find_filtered(category="Software Engineer")
    assert total == 1
    assert items[0].title == "Python Engineer"


def test_job_gateway_create_many(db_app):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    saved = gateway.create_many(
        [
            {"title": "A", "company": "X", "category": "Software Engineer", "level": "S", "location": "R"},
            {"title": "B", "company": "Y", "category": "Data Science", "level": "M", "location": "R"},
        ]
    )
    assert saved == 2
    assert gateway.count() == 2


def test_job_gateway_create_many_skips_duplicate_source_ids(db_app):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    first = gateway.create_many(
        [
            {"source_id": "muse-1", "title": "A", "company": "X", "category": "SE", "level": "S", "location": "R"},
            {"source_id": "muse-2", "title": "B", "company": "Y", "category": "SE", "level": "S", "location": "R"},
        ]
    )
    assert first == 2

    second = gateway.create_many(
        [
            {"source_id": "muse-2", "title": "B-dup", "company": "Y", "category": "SE", "level": "S", "location": "R"},
            {"source_id": "muse-3", "title": "C", "company": "Z", "category": "SE", "level": "S", "location": "R"},
        ]
    )
    assert second == 1
    assert gateway.count() == 3


def test_job_gateway_create_many_dedupes_within_same_batch(db_app):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    saved = gateway.create_many(
        [
            {"source_id": "dup", "title": "A", "company": "X", "category": "SE", "level": "S", "location": "R"},
            {"source_id": "dup", "title": "A-again", "company": "X", "category": "SE", "level": "S", "location": "R"},
            {"source_id": None, "title": "no-source", "company": "Y", "category": "SE", "level": "S", "location": "R"},
        ]
    )
    assert saved == 2
    assert gateway.count() == 2


def test_job_gateway_distinct_categories(db_app):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    gateway.create_many(
        [
            {"title": "A", "company": "X", "category": "Software Engineer", "level": "", "location": ""},
            {"title": "B", "company": "Y", "category": "Data Science", "level": "", "location": ""},
            {"title": "C", "company": "Z", "category": "Software Engineer", "level": "", "location": ""},
        ]
    )
    categories = gateway.distinct_categories()
    assert sorted(categories) == ["Data Science", "Software Engineer"]


def test_job_gateway_find_recent_respects_window(db_app):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    gateway.create(
        title="Old", company="X", category="SE", level="S", location="R",
        date_collected=datetime.utcnow() - timedelta(days=30),
    )
    gateway.create(
        title="New", company="Y", category="SE", level="S", location="R",
        date_collected=datetime.utcnow(),
    )
    recent = gateway.find_recent(days=7)
    assert len(recent) == 1
    assert recent[0].title == "New"


def test_job_gateway_find_filtered_location_partial_match(db_app):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    gateway.create_many(
        [
            {"title": "A", "company": "X", "category": "SE", "level": "S", "location": "Remote, US"},
            {"title": "B", "company": "Y", "category": "SE", "level": "S", "location": "Berlin, DE"},
        ]
    )
    items, total = gateway.find_filtered(location="remote")
    assert total == 1
    assert items[0].title == "A"


def test_trend_gateway_upsert_is_idempotent(db_app):
    from shared.gateway import TrendDataGateway

    gateway = TrendDataGateway()
    gateway.upsert_skill_trend(skill="python", count=10, week="2026-W17")
    gateway.upsert_skill_trend(skill="python", count=15, week="2026-W17")

    rows = gateway.list_skill_trends(weeks=4)
    assert len(rows) == 1
    assert rows[0].count == 15


def test_trend_gateway_distinguishes_category(db_app):
    from shared.gateway import TrendDataGateway

    gateway = TrendDataGateway()
    gateway.upsert_skill_trend(skill="python", count=10, week="2026-W17")
    gateway.upsert_skill_trend(
        skill="python", count=5, week="2026-W17", category="Software Engineer"
    )

    se = gateway.list_skill_trends(weeks=4, category="Software Engineer")
    assert len(se) == 1
    assert se[0].count == 5


def test_trend_gateway_latest_weeks_only(db_app):
    from shared.gateway import TrendDataGateway

    gateway = TrendDataGateway()
    gateway.upsert_skill_trend(skill="python", count=1, week="2026-W10")
    gateway.upsert_skill_trend(skill="python", count=2, week="2026-W15")
    gateway.upsert_skill_trend(skill="python", count=3, week="2026-W17")

    rows = gateway.list_skill_trends(weeks=2)
    weeks = {r.week for r in rows}
    assert weeks == {"2026-W15", "2026-W17"}


def test_company_trend_upsert_and_list(db_app):
    from shared.gateway import TrendDataGateway

    gateway = TrendDataGateway()
    gateway.upsert_company_trend(company="Acme", count=4, week="2026-W17")
    rows = gateway.list_company_trends(weeks=4)
    assert rows[0].company == "Acme"
    assert rows[0].count == 4
