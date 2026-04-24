"""Unit tests for the pure aggregation helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from aggregations import (
    KNOWN_SKILLS,
    aggregate_companies,
    aggregate_skills,
    tokenize_title,
    week_key,
)


@dataclass
class FakeJob:
    title: str
    company: Optional[str]
    category: Optional[str]
    date_collected: datetime


def test_week_key_format():
    assert week_key(datetime(2026, 4, 20)) == "2026-W17"  # Monday of W17


def test_tokenize_title_finds_known_skills():
    assert "python" in tokenize_title("Senior Python Engineer")
    assert "react" in tokenize_title("React Developer")
    assert "kubernetes" in tokenize_title("Kubernetes Operator")


def test_tokenize_title_is_case_insensitive():
    assert "python" in tokenize_title("PYTHON Engineer")
    assert "typescript" in tokenize_title("TypeScript wizard")


def test_tokenize_title_handles_empty_and_unknown():
    assert tokenize_title("") == set()
    assert tokenize_title("CEO Office Manager") == set()


def test_tokenize_title_resolves_aliases():
    # Alias: "nextjs" and "next.js" both map to "next.js"
    assert "next.js" in tokenize_title("Next.js Engineer")
    assert "node" in tokenize_title("Node.js Backend")


def test_aggregate_skills_counts_global_and_per_category():
    when = datetime(2026, 4, 20)
    jobs = [
        FakeJob("Senior Python Developer", "A", "Software Engineer", when),
        FakeJob("Python Data Engineer", "B", "Data and Analytics", when),
        FakeJob("React Engineer", "C", "Software Engineer", when),
    ]
    result = aggregate_skills(jobs)
    assert result[("python", "2026-W17", None)] == 2
    assert result[("python", "2026-W17", "Software Engineer")] == 1
    assert result[("python", "2026-W17", "Data and Analytics")] == 1
    assert result[("react", "2026-W17", None)] == 1


def test_aggregate_skills_skips_jobs_with_no_known_skill():
    when = datetime(2026, 4, 20)
    jobs = [FakeJob("Project Manager", "A", "Product", when)]
    assert aggregate_skills(jobs) == {}


def test_aggregate_companies_counts_postings_per_week():
    jobs = [
        FakeJob("Engineer", "Acme", "Software Engineer", datetime(2026, 4, 20)),
        FakeJob("Analyst", "Acme", "Data and Analytics", datetime(2026, 4, 20)),
        FakeJob("Designer", "Figma", "Design and UX", datetime(2026, 4, 14)),  # W16
    ]
    result = aggregate_companies(jobs)
    assert result[("Acme", "2026-W17", None)] == 2
    assert result[("Acme", "2026-W17", "Software Engineer")] == 1
    assert result[("Acme", "2026-W17", "Data and Analytics")] == 1
    assert result[("Figma", "2026-W16", None)] == 1


def test_aggregate_companies_ignores_blank_company():
    jobs = [FakeJob("Dev", None, "Software Engineer", datetime(2026, 4, 20))]
    assert aggregate_companies(jobs) == {}


def test_known_skills_contains_core_skills():
    for required in ["python", "javascript", "aws", "kubernetes", "sql"]:
        assert required in KNOWN_SKILLS
