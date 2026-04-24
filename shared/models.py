"""SQLAlchemy models and plain Record dataclasses."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint

from .db import db


class Job(db.Model):
    """A raw job posting collected from The Muse."""

    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    # External identifier from the upstream API (e.g. The Muse job id). Nullable
    # so rows collected before this column existed remain valid. Unique so we
    # can reject duplicate ingests on the INSERT path.
    source_id = db.Column(db.String(100), unique=True, index=True, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200))
    category = db.Column(db.String(100))
    level = db.Column(db.String(50))
    location = db.Column(db.String(100))
    # Raw job description HTML from the upstream API. Nullable so older rows
    # collected before we captured descriptions remain valid. The analyzer
    # scans this (stripped of tags) for skill keywords.
    description = db.Column(db.Text, nullable=True)
    date_collected = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title!r} company={self.company!r}>"


class SkillTrend(db.Model):
    """Aggregated skill mention counts for a given ISO week (and optional category)."""

    __tablename__ = "skill_trends"
    __table_args__ = (
        UniqueConstraint("skill", "week", "category", name="uq_skill_week_category"),
    )

    id = db.Column(db.Integer, primary_key=True)
    skill = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    week = db.Column(db.String(10), nullable=False)  # e.g. "2026-W16"
    category = db.Column(db.String(100))


class CompanyTrend(db.Model):
    """Aggregated posting counts per company per ISO week (and optional category)."""

    __tablename__ = "company_trends"
    __table_args__ = (
        UniqueConstraint("company", "week", "category", name="uq_company_week_category"),
    )

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(200), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    week = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(100))


@dataclass(frozen=True)
class JobRecord:
    id: int
    title: str
    company: Optional[str]
    category: Optional[str]
    level: Optional[str]
    location: Optional[str]
    date_collected: datetime
    source_id: Optional[str] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class SkillTrendRecord:
    skill: str
    count: int
    week: str
    category: Optional[str] = None


@dataclass(frozen=True)
class CompanyTrendRecord:
    company: str
    count: int
    week: str
    category: Optional[str] = None
