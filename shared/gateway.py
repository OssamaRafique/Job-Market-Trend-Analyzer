"""Data Gateway classes - the only layer that touches the ORM."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlalchemy import and_, func, select

from .db import db
from .models import (
    CompanyTrend,
    CompanyTrendRecord,
    Job,
    JobRecord,
    SkillTrend,
    SkillTrendRecord,
)


def _to_job_record(job: Job) -> JobRecord:
    return JobRecord(
        id=job.id,
        title=job.title,
        company=job.company,
        category=job.category,
        level=job.level,
        location=job.location,
        date_collected=job.date_collected,
        source_id=job.source_id,
    )


def _to_skill_record(trend: SkillTrend) -> SkillTrendRecord:
    return SkillTrendRecord(
        skill=trend.skill, count=trend.count, week=trend.week, category=trend.category
    )


def _to_company_record(trend: CompanyTrend) -> CompanyTrendRecord:
    return CompanyTrendRecord(
        company=trend.company, count=trend.count, week=trend.week, category=trend.category
    )


class JobDataGateway:
    """CRUD + finders for the `jobs` table."""

    def create(
        self,
        *,
        title: str,
        company: Optional[str],
        category: Optional[str],
        level: Optional[str],
        location: Optional[str],
        date_collected: Optional[datetime] = None,
        source_id: Optional[str] = None,
    ) -> JobRecord:
        job = Job(
            source_id=source_id,
            title=title,
            company=company,
            category=category,
            level=level,
            location=location,
            date_collected=date_collected or datetime.utcnow(),
        )
        db.session.add(job)
        db.session.commit()
        return _to_job_record(job)

    def create_many(self, jobs: Iterable[dict]) -> int:
        """Insert jobs, skipping rows whose ``source_id`` already exists.

        Rows without a ``source_id`` are always inserted (the caller did not
        provide an external identifier, so we cannot safely dedupe them).
        Returns the number of rows actually inserted.
        """
        now = datetime.utcnow()
        incoming = list(jobs)
        if not incoming:
            return 0

        source_ids = {
            str(j["source_id"])
            for j in incoming
            if j.get("source_id") is not None
        }
        existing: set[str] = set()
        if source_ids:
            stmt = select(Job.source_id).where(Job.source_id.in_(source_ids))
            existing = {row[0] for row in db.session.execute(stmt).all() if row[0]}

        rows: list[Job] = []
        seen_in_batch: set[str] = set()
        for j in incoming:
            sid = j.get("source_id")
            sid_str = str(sid) if sid is not None else None
            if sid_str and (sid_str in existing or sid_str in seen_in_batch):
                continue
            if sid_str:
                seen_in_batch.add(sid_str)
            rows.append(
                Job(
                    source_id=sid_str,
                    title=j["title"],
                    company=j.get("company"),
                    category=j.get("category"),
                    level=j.get("level"),
                    location=j.get("location"),
                    date_collected=j.get("date_collected") or now,
                )
            )

        if not rows:
            return 0
        db.session.add_all(rows)
        db.session.commit()
        return len(rows)

    def find_by_id(self, job_id: int) -> Optional[JobRecord]:
        job = db.session.get(Job, job_id)
        return _to_job_record(job) if job else None

    def find_filtered(
        self,
        *,
        category: Optional[str] = None,
        level: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[JobRecord], int]:
        stmt = select(Job)
        count_stmt = select(func.count()).select_from(Job)
        if category:
            stmt = stmt.where(Job.category == category)
            count_stmt = count_stmt.where(Job.category == category)
        if level:
            stmt = stmt.where(Job.level == level)
            count_stmt = count_stmt.where(Job.level == level)
        if location:
            needle = f"%{location.lower()}%"
            stmt = stmt.where(func.lower(Job.location).like(needle))
            count_stmt = count_stmt.where(func.lower(Job.location).like(needle))
        stmt = stmt.order_by(Job.date_collected.desc()).limit(limit).offset(offset)
        items = [_to_job_record(j) for j in db.session.execute(stmt).scalars()]
        total = db.session.execute(count_stmt).scalar_one()
        return items, total

    def find_recent(self, days: int = 7) -> list[JobRecord]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = select(Job).where(Job.date_collected >= cutoff)
        return [_to_job_record(j) for j in db.session.execute(stmt).scalars()]

    def distinct_categories(self) -> list[str]:
        stmt = (
            select(Job.category)
            .where(Job.category.is_not(None))
            .distinct()
            .order_by(Job.category)
        )
        return [row[0] for row in db.session.execute(stmt).all() if row[0]]

    def count(self) -> int:
        return db.session.execute(select(func.count()).select_from(Job)).scalar_one()

    def delete_all(self) -> int:
        rows = db.session.query(Job).delete()
        db.session.commit()
        return rows


class TrendDataGateway:
    """Upserts and queries for skill_trends and company_trends."""

    def upsert_skill_trend(
        self, *, skill: str, count: int, week: str, category: Optional[str] = None
    ) -> SkillTrendRecord:
        stmt = select(SkillTrend).where(
            and_(
                SkillTrend.skill == skill,
                SkillTrend.week == week,
                SkillTrend.category.is_(category) if category is None else SkillTrend.category == category,
            )
        )
        existing = db.session.execute(stmt).scalar_one_or_none()
        if existing:
            existing.count = count
        else:
            existing = SkillTrend(skill=skill, count=count, week=week, category=category)
            db.session.add(existing)
        db.session.commit()
        return _to_skill_record(existing)

    def upsert_company_trend(
        self, *, company: str, count: int, week: str, category: Optional[str] = None
    ) -> CompanyTrendRecord:
        stmt = select(CompanyTrend).where(
            and_(
                CompanyTrend.company == company,
                CompanyTrend.week == week,
                CompanyTrend.category.is_(category)
                if category is None
                else CompanyTrend.category == category,
            )
        )
        existing = db.session.execute(stmt).scalar_one_or_none()
        if existing:
            existing.count = count
        else:
            existing = CompanyTrend(company=company, count=count, week=week, category=category)
            db.session.add(existing)
        db.session.commit()
        return _to_company_record(existing)

    def list_skill_trends(
        self, *, weeks: int = 4, category: Optional[str] = None
    ) -> list[SkillTrendRecord]:
        stmt = select(SkillTrend).order_by(SkillTrend.week.desc(), SkillTrend.count.desc())
        # When no category is requested, return the global rollup only (the
        # aggregator stores a NULL-category row per (skill, week) alongside
        # per-category rows); mixing them would look like duplicates.
        if category:
            stmt = stmt.where(SkillTrend.category == category)
        else:
            stmt = stmt.where(SkillTrend.category.is_(None))
        latest_weeks = self._latest_weeks(SkillTrend, weeks, category)
        if not latest_weeks:
            return []
        stmt = stmt.where(SkillTrend.week.in_(latest_weeks))
        return [_to_skill_record(t) for t in db.session.execute(stmt).scalars()]

    def list_company_trends(
        self, *, weeks: int = 4, category: Optional[str] = None
    ) -> list[CompanyTrendRecord]:
        latest_weeks = self._latest_weeks(CompanyTrend, weeks, category)
        if not latest_weeks:
            return []
        stmt = (
            select(CompanyTrend)
            .where(CompanyTrend.week.in_(latest_weeks))
            .order_by(CompanyTrend.week.desc(), CompanyTrend.count.desc())
        )
        if category:
            stmt = stmt.where(CompanyTrend.category == category)
        else:
            stmt = stmt.where(CompanyTrend.category.is_(None))
        return [_to_company_record(t) for t in db.session.execute(stmt).scalars()]

    def _latest_weeks(self, model, weeks: int, category: Optional[str]) -> list[str]:
        stmt = select(model.week).distinct().order_by(model.week.desc()).limit(weeks)
        if category:
            stmt = stmt.where(model.category == category)
        else:
            stmt = stmt.where(model.category.is_(None))
        return [row[0] for row in db.session.execute(stmt).all()]

    def clear_week(self, week: str) -> int:
        skills = db.session.query(SkillTrend).filter(SkillTrend.week == week).delete()
        companies = db.session.query(CompanyTrend).filter(CompanyTrend.week == week).delete()
        db.session.commit()
        return skills + companies
