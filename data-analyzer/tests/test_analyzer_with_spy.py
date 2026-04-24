"""Analyzer integration-within-the-process test using Spy + Fake gateways."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from analyzer import run_analysis


@dataclass
class JobFixture:
    id: int
    title: str
    company: Optional[str]
    category: Optional[str]
    level: Optional[str]
    location: Optional[str]
    date_collected: datetime


class FakeJobDataGateway:
    def __init__(self, jobs):
        self._jobs = jobs

    def find_recent(self, days: int):
        return list(self._jobs)


@dataclass
class SpyTrendDataGateway:
    upsert_skill_calls: list[tuple] = field(default_factory=list)
    upsert_company_calls: list[tuple] = field(default_factory=list)

    def upsert_skill_trend(self, *, skill, count, week, category=None):
        self.upsert_skill_calls.append((skill, count, week, category))

    def upsert_company_trend(self, *, company, count, week, category=None):
        self.upsert_company_calls.append((company, count, week, category))


def _make_jobs():
    when = datetime(2026, 4, 20, 12, 0, 0)  # W17
    return [
        JobFixture(1, "Senior Python Engineer", "Acme", "Software Engineer", "S", "Remote", when),
        JobFixture(2, "Python Developer", "Acme", "Software Engineer", "M", "Remote", when),
        JobFixture(3, "React Engineer", "Nebula", "Software Engineer", "M", "Remote", when),
        JobFixture(4, "Data Scientist (PyTorch)", "Nebula", "Data Science", "S", "NYC", when),
    ]


def test_analyzer_invokes_upsert_per_skill_and_company_tuple():
    jobs = FakeJobDataGateway(_make_jobs())
    trends = SpyTrendDataGateway()
    log = logging.getLogger("test")

    skill_count, company_count = run_analysis(jobs, trends, days=28, log=log)

    # Global python count: 2 (two jobs mention it)
    assert ("python", "2026-W17", None) in {
        (s, w, c) for (s, _n, w, c) in trends.upsert_skill_calls
    }
    # Each (skill, week, category) tuple becomes one upsert call
    assert len(trends.upsert_skill_calls) == skill_count
    assert len(trends.upsert_company_calls) == company_count


def test_spy_records_expected_company_counts():
    jobs = FakeJobDataGateway(_make_jobs())
    trends = SpyTrendDataGateway()
    run_analysis(jobs, trends, days=28, log=logging.getLogger("test"))

    # Global Acme count: 2 postings, Nebula: 2
    globals_ = {
        (c, cat): n for (c, n, _w, cat) in trends.upsert_company_calls if cat is None
    }
    assert globals_[("Acme", None)] == 2
    assert globals_[("Nebula", None)] == 2


def test_analyzer_handles_empty_job_list():
    trends = SpyTrendDataGateway()
    skill_count, company_count = run_analysis(
        FakeJobDataGateway([]), trends, days=28, log=logging.getLogger("test")
    )
    assert skill_count == 0
    assert company_count == 0
    assert trends.upsert_skill_calls == []
    assert trends.upsert_company_calls == []
