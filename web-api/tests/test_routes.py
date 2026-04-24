"""Flask test-client coverage for the JSON routes."""
from __future__ import annotations

import pytest

from shared.models import CompanyTrendRecord, SkillTrendRecord

from fakes import (
    FakeJobDataGateway,
    FakeTrendDataGateway,
    sample_jobs,
)


@pytest.fixture
def app():
    from src import routes
    from src.app import build_app

    application = build_app()
    application.config["TESTING"] = True

    jobs_fake = FakeJobDataGateway(
        jobs=sample_jobs(),
        categories=["Software Engineer", "Data Science"],
    )
    trends_fake = FakeTrendDataGateway(
        skills=[
            SkillTrendRecord("python", 12, "2026-W17", None),
            SkillTrendRecord("react", 8, "2026-W17", None),
        ],
        companies=[
            CompanyTrendRecord("Acme", 5, "2026-W17", None),
            CompanyTrendRecord("Nebula", 2, "2026-W17", None),
        ],
    )
    routes.set_gateway_factories(jobs=lambda: jobs_fake, trends=lambda: trends_fake)

    yield application, jobs_fake, trends_fake

    routes.reset_gateway_factories()


@pytest.fixture
def client(app):
    application, *_ = app
    return application.test_client()


def test_health_is_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "healthy"}


def test_metrics_endpoint_serves_prometheus_payload(client):
    # Hit a handful of routes so counters have non-zero values.
    client.get("/api/jobs")
    client.get("/api/trends/skills")
    client.get("/api/categories")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "jmta_jobs_requests_total" in body
    assert "jmta_trends_requests_total" in body
    assert "jmta_categories_requests_total" in body
    assert resp.mimetype.startswith("text/plain")


def test_categories_route_returns_distinct_categories(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    assert resp.get_json() == ["Software Engineer", "Data Science"]


def test_categories_falls_back_to_defaults_when_empty(app):
    from src import routes

    application, *_ = app
    routes.set_gateway_factories(jobs=lambda: FakeJobDataGateway(categories=[]))
    client = application.test_client()
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "Software Engineer" in data
    assert len(data) > 0


def test_jobs_returns_paginated_shape(client):
    resp = client.get("/api/jobs?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Python Engineer"
    assert "date_collected" in data["items"][0]


def test_jobs_filters_by_category(client):
    resp = client.get("/api/jobs?category=Software%20Engineer")
    data = resp.get_json()
    assert data["total"] == 2
    titles = [item["title"] for item in data["items"]]
    assert "Python Engineer" in titles
    assert "React Engineer" in titles


def test_jobs_clamps_bad_limit_to_default(client):
    resp = client.get("/api/jobs?limit=9999")
    data = resp.get_json()
    assert len(data["items"]) <= 200


def test_skill_trends_returns_array_of_points(client):
    resp = client.get("/api/trends/skills?weeks=4")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert data[0] == {"skill": "python", "count": 12, "week": "2026-W17"}


def test_company_trends_returns_array_of_points(client):
    resp = client.get("/api/trends/companies?weeks=4")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0] == {"company": "Acme", "count": 5, "week": "2026-W17"}


def test_trends_clamp_weeks_to_valid_range(client):
    resp = client.get("/api/trends/skills?weeks=999")
    assert resp.status_code == 200


def test_refresh_returns_503_when_broker_missing(client, monkeypatch):
    monkeypatch.delenv("AMQP_URL", raising=False)
    resp = client.post("/api/refresh")
    assert resp.status_code == 503
    data = resp.get_json()
    assert data["queued"] is False


def test_refresh_publishes_to_collect_jobs_when_broker_configured(client, monkeypatch):
    """When AMQP_URL is set the route publishes through the producer seam."""
    monkeypatch.setenv("AMQP_URL", "amqp://guest:guest@localhost:5672/")

    calls = []

    def fake_publish(queue, payload, **kwargs):
        calls.append((queue, payload))

    # The route imports publish via the module-level alias in queue_producer,
    # so patch at that seam (where the name is *used*).
    from src import queue_producer

    monkeypatch.setattr(queue_producer, "publish", fake_publish)

    resp = client.post("/api/refresh")

    assert resp.status_code == 202
    data = resp.get_json()
    assert data["queued"] is True
    assert len(calls) == 1
    queue, payload = calls[0]
    assert queue == "collect_jobs"
    assert payload["trigger"] == "api"
    assert "requested_at" in payload
