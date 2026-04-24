"""JSON routes under /api/, consumed by the Next.js dashboard."""
from __future__ import annotations

from typing import Callable, Optional

from flask import Blueprint, jsonify, request

from shared.gateway import JobDataGateway, TrendDataGateway
from shared.models import CompanyTrendRecord, JobRecord, SkillTrendRecord

from .metrics import (
    categories_requests_total,
    collect_triggers_total,
    jobs_requests_total,
    levels_requests_total,
    trends_requests_total,
)

bp = Blueprint("api", __name__)


# Allow tests to inject fake gateway factories without touching a real DB.
_job_gateway_factory: Callable[[], JobDataGateway] = JobDataGateway
_trend_gateway_factory: Callable[[], TrendDataGateway] = TrendDataGateway


def set_gateway_factories(
    jobs: Optional[Callable[[], JobDataGateway]] = None,
    trends: Optional[Callable[[], TrendDataGateway]] = None,
) -> None:
    """Test hook: swap gateway factories."""
    global _job_gateway_factory, _trend_gateway_factory
    if jobs is not None:
        _job_gateway_factory = jobs
    if trends is not None:
        _trend_gateway_factory = trends


def reset_gateway_factories() -> None:
    global _job_gateway_factory, _trend_gateway_factory
    _job_gateway_factory = JobDataGateway
    _trend_gateway_factory = TrendDataGateway


def _clamp_int(value: Optional[str], default: int, *, minimum: int, maximum: int) -> int:
    try:
        n = int(value) if value is not None else default
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, n))


@bp.get("/categories")
def list_categories():
    categories_requests_total.inc()
    gateway = _job_gateway_factory()
    categories = gateway.distinct_categories()
    if not categories:
        # Seed with the same defaults the collector uses so the UI still has
        # something to show on a freshly provisioned database.
        categories = [
            "Software Engineering",
            "Data and Analytics",
            "Data Science",
            "Design and UX",
            "Product",
            "Project Management",
            "Account Management",
            "Sales",
            "Customer Service",
        ]
    return jsonify(categories)


@bp.get("/levels")
def list_levels():
    """Return the set of distinct experience levels actually present in the DB.

    The Muse API uses values like "Entry Level", "Mid Level", "Senior Level",
    "Internship", and "Management" — we surface them verbatim so the frontend
    Level filter exactly matches what `find_filtered` will accept.
    """
    levels_requests_total.inc()
    gateway = _job_gateway_factory()
    levels = gateway.distinct_levels()
    if not levels:
        # Match the upstream Muse vocabulary so the empty-DB case still works.
        levels = ["Entry Level", "Mid Level", "Senior Level", "Internship", "Management"]
    return jsonify(levels)


@bp.get("/trends/skills")
def skill_trends():
    trends_requests_total.labels(kind="skills").inc()
    weeks = _clamp_int(request.args.get("weeks"), default=4, minimum=1, maximum=12)
    category = request.args.get("category") or None
    trends = _trend_gateway_factory().list_skill_trends(weeks=weeks, category=category)
    return jsonify([_skill_to_dict(t) for t in trends])


@bp.get("/trends/companies")
def company_trends():
    trends_requests_total.labels(kind="companies").inc()
    weeks = _clamp_int(request.args.get("weeks"), default=4, minimum=1, maximum=12)
    category = request.args.get("category") or None
    trends = _trend_gateway_factory().list_company_trends(weeks=weeks, category=category)
    return jsonify([_company_to_dict(t) for t in trends])


@bp.get("/jobs")
def list_jobs():
    jobs_requests_total.inc()
    limit = _clamp_int(request.args.get("limit"), default=25, minimum=1, maximum=200)
    offset = _clamp_int(request.args.get("offset"), default=0, minimum=0, maximum=10_000)
    category = request.args.get("category") or None
    level = request.args.get("level") or None
    location = request.args.get("location") or None

    items, total = _job_gateway_factory().find_filtered(
        category=category,
        level=level,
        location=location,
        limit=limit,
        offset=offset,
    )
    return jsonify({"total": total, "items": [_job_to_dict(j) for j in items]})


@bp.post("/refresh")
def refresh():
    """Publish a message to the ``collect_jobs`` RabbitMQ queue."""
    from .queue_producer import publish_collect_jobs

    try:
        publish_collect_jobs()
        collect_triggers_total.labels(result="queued").inc()
        return jsonify(queued=True, message="collection job enqueued"), 202
    except Exception as exc:  # broker unreachable or not configured yet
        collect_triggers_total.labels(result="broker_unavailable").inc()
        return (
            jsonify(queued=False, message=f"broker unavailable: {exc}"),
            503,
        )


def _job_to_dict(job: JobRecord) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company or "",
        "category": job.category or "",
        "level": job.level or "",
        "location": job.location or "",
        "date_collected": job.date_collected.isoformat() if job.date_collected else None,
    }


def _skill_to_dict(row: SkillTrendRecord) -> dict:
    return {"skill": row.skill, "count": row.count, "week": row.week}


def _company_to_dict(row: CompanyTrendRecord) -> dict:
    return {"company": row.company, "count": row.count, "week": row.week}
