"""Unit tests for MuseClient.parse_job — pure, no I/O."""
from __future__ import annotations

from muse_client import MuseClient


def test_parse_job_happy_path():
    raw = {
        "id": 12345,
        "name": "Senior Python Developer",
        "company": {"name": "Acme"},
        "categories": [{"name": "Software Engineer"}],
        "levels": [{"name": "Senior Level"}],
        "locations": [{"name": "Remote"}],
        "contents": "<p>We are looking for...</p>",
    }
    result = MuseClient.parse_job(raw)
    assert result == {
        "source_id": "12345",
        "title": "Senior Python Developer",
        "company": "Acme",
        "category": "Software Engineer",
        "level": "Senior Level",
        "location": "Remote",
        "description": "<p>We are looking for...</p>",
    }


def test_parse_job_missing_fields_defaults():
    result = MuseClient.parse_job({})
    assert result["title"] == "Unknown"
    assert result["company"] is None
    assert result["category"] is None
    assert result["level"] is None
    assert result["location"] is None
    assert result["source_id"] is None
    assert result["description"] is None


def test_parse_job_stringifies_numeric_source_id():
    result = MuseClient.parse_job({"id": 42, "name": "x"})
    assert result["source_id"] == "42"


def test_parse_job_uses_first_category_when_multiple():
    raw = {
        "name": "DevOps Engineer",
        "company": {"name": "Cloud Co"},
        "categories": [{"name": "DevOps and Sysadmin"}, {"name": "Software Engineer"}],
        "levels": [],
        "locations": [{"name": "Berlin, DE"}],
    }
    result = MuseClient.parse_job(raw)
    assert result["category"] == "DevOps and Sysadmin"
    assert result["level"] is None
    assert result["location"] == "Berlin, DE"


def test_parse_job_handles_null_company_key():
    raw = {"name": "Contractor", "company": None, "categories": [], "levels": [], "locations": []}
    result = MuseClient.parse_job(raw)
    assert result["company"] is None
    assert result["title"] == "Contractor"
