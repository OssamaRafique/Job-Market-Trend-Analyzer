"""In-memory fake gateways for route unit tests."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from shared.models import CompanyTrendRecord, JobRecord, SkillTrendRecord


@dataclass
class FakeJobDataGateway:
    jobs: list[JobRecord] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)

    def find_filtered(
        self,
        *,
        category: Optional[str] = None,
        level: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[JobRecord], int]:
        items = list(self.jobs)
        if category:
            items = [j for j in items if j.category == category]
        if level:
            items = [j for j in items if j.level == level]
        if location:
            needle = location.lower()
            items = [j for j in items if j.location and needle in j.location.lower()]
        total = len(items)
        return items[offset : offset + limit], total

    def distinct_categories(self) -> list[str]:
        return list(self.categories)

    def find_recent(self, days: int = 7) -> list[JobRecord]:
        return list(self.jobs)


@dataclass
class FakeTrendDataGateway:
    skills: list[SkillTrendRecord] = field(default_factory=list)
    companies: list[CompanyTrendRecord] = field(default_factory=list)
    upsert_skill_calls: list[tuple] = field(default_factory=list)
    upsert_company_calls: list[tuple] = field(default_factory=list)

    def list_skill_trends(
        self, *, weeks: int = 4, category: Optional[str] = None
    ) -> list[SkillTrendRecord]:
        if category:
            return [r for r in self.skills if r.category == category]
        return [r for r in self.skills if r.category is None]

    def list_company_trends(
        self, *, weeks: int = 4, category: Optional[str] = None
    ) -> list[CompanyTrendRecord]:
        if category:
            return [r for r in self.companies if r.category == category]
        return [r for r in self.companies if r.category is None]

    def upsert_skill_trend(
        self, *, skill: str, count: int, week: str, category: Optional[str] = None
    ) -> SkillTrendRecord:
        rec = SkillTrendRecord(skill=skill, count=count, week=week, category=category)
        self.upsert_skill_calls.append((skill, count, week, category))
        return rec

    def upsert_company_trend(
        self, *, company: str, count: int, week: str, category: Optional[str] = None
    ) -> CompanyTrendRecord:
        rec = CompanyTrendRecord(company=company, count=count, week=week, category=category)
        self.upsert_company_calls.append((company, count, week, category))
        return rec


def sample_jobs() -> list[JobRecord]:
    now = datetime(2026, 4, 20, 12, 0, 0)
    return [
        JobRecord(1, "Python Engineer", "Acme", "Software Engineer", "Senior", "Remote", now),
        JobRecord(2, "Data Scientist", "Nebula", "Data Science", "Mid", "NYC", now),
        JobRecord(3, "React Engineer", "Acme", "Software Engineer", "Junior", "Remote", now),
    ]
