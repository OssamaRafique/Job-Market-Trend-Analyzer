"""End-to-end integration tests for the web-api.

Hits a real Postgres via ``DATABASE_URL`` — not a fake. Exercises the full
Flask app with real gateways, asserting the JSON shape the React frontend
consumes.
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


def _real_db_available() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("USE_REAL_DB") != "1":
        return False
    return url.startswith("postgresql://") or url.startswith("postgres://")


requires_real_db = pytest.mark.skipif(
    not _real_db_available(),
    reason="set DATABASE_URL and USE_REAL_DB=1 to run integration tests",
)


@pytest.fixture
def api_client():
    # Make sure the Flask test flag does not sneak in and steer us to sqlite.
    os.environ["FLASK_TESTING"] = "0"

    from shared.db import db
    from src.app import build_app

    app = build_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.rollback()
        db.drop_all()


@requires_real_db
def test_health_endpoint_ok(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "healthy"}


@requires_real_db
def test_jobs_endpoint_returns_inserted_rows(api_client):
    from shared.gateway import JobDataGateway

    JobDataGateway().create(
        title="Senior Python Developer",
        company="Acme",
        category="Software Engineer",
        level="Senior",
        location="Remote",
    )

    resp = api_client.get("/api/jobs")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Senior Python Developer"
    assert data["items"][0]["company"] == "Acme"
    # Contract (lib/types.ts): date_collected is ISO 8601
    assert "T" in data["items"][0]["date_collected"]


@requires_real_db
def test_trends_endpoints_return_written_rows(api_client):
    from shared.gateway import TrendDataGateway

    trends = TrendDataGateway()
    trends.upsert_skill_trend(skill="python", count=10, week="2026-W17")
    trends.upsert_company_trend(company="Acme", count=3, week="2026-W17")

    skills = api_client.get("/api/trends/skills?weeks=4").get_json()
    companies = api_client.get("/api/trends/companies?weeks=4").get_json()

    assert {"skill": "python", "count": 10, "week": "2026-W17"} in skills
    assert {"company": "Acme", "count": 3, "week": "2026-W17"} in companies


@requires_real_db
def test_categories_endpoint_reads_distinct_categories(api_client):
    from shared.gateway import JobDataGateway

    gateway = JobDataGateway()
    gateway.create_many(
        [
            {"title": "A", "company": "X", "category": "Software Engineer", "level": "", "location": ""},
            {"title": "B", "company": "Y", "category": "Data Science", "level": "", "location": ""},
        ]
    )
    resp = api_client.get("/api/categories")
    data = resp.get_json()
    assert "Software Engineer" in data
    assert "Data Science" in data
