"""Pure aggregation helpers for the data analyzer.

Kept free of database access so they can be unit-tested in isolation over a
list of plain JobRecord objects.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Iterable, Optional

# Skills extracted from job titles (case-insensitive, lowercase).
KNOWN_SKILLS: frozenset[str] = frozenset(
    {
        # Languages
        "python", "typescript", "javascript", "java", "kotlin", "scala", "go",
        "rust", "ruby", "php", "swift", "c#", "c++",
        # Front end
        "react", "vue", "angular", "svelte", "next.js", "nuxt",
        # Back end frameworks
        "django", "flask", "fastapi", "spring", "express", "nestjs", "rails",
        # Data / analytics
        "sql", "postgres", "postgresql", "mysql", "mongodb", "redis",
        "snowflake", "databricks", "airflow", "dbt", "spark", "kafka", "hadoop",
        # Cloud / infra
        "aws", "gcp", "azure", "kubernetes", "docker", "terraform", "ansible",
        # ML / data science
        "pytorch", "tensorflow", "sklearn", "pandas", "numpy", "llm",
        # Roles / general
        "devops", "sre", "ml", "ai",
    }
)

# Tokens that frequently appear as two words or with punctuation. Map from the
# raw substring we search for, to the canonical skill key we store.
PHRASE_ALIASES: dict[str, str] = {
    "next.js": "next.js",
    "nextjs": "next.js",
    "node.js": "node",
    "nodejs": "node",
    "machine learning": "ml",
    "data science": "ml",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9+#.]+")


def tokenize_title(title: str) -> set[str]:
    """Return the set of known skills mentioned in ``title`` (case-insensitive)."""
    if not title:
        return set()
    lowered = title.lower()
    matched: set[str] = set()

    for phrase, canonical in PHRASE_ALIASES.items():
        if phrase in lowered:
            matched.add(canonical)

    for raw in TOKEN_RE.findall(lowered):
        if raw in KNOWN_SKILLS:
            matched.add(raw)
    return matched


def week_key(dt: datetime) -> str:
    """Return the ISO week key for ``dt`` in the form ``YYYY-Www`` (e.g. ``2026-W16``)."""
    year, week, _ = dt.isocalendar()
    return f"{year:04d}-W{week:02d}"


def aggregate_skills(
    jobs: Iterable, *, include_categories: bool = True
) -> dict[tuple[str, str, Optional[str]], int]:
    """Count skill mentions per (skill, week) and, if enabled, per (skill, week, category).

    Returns a dict keyed by (skill, week, category) where ``category`` is
    ``None`` for the global rollup. Callers pass iterable of JobRecord-like
    objects exposing ``title``, ``category``, and ``date_collected``.
    """
    counter: Counter[tuple[str, str, Optional[str]]] = Counter()
    for job in jobs:
        skills = tokenize_title(getattr(job, "title", "") or "")
        if not skills:
            continue
        week = week_key(getattr(job, "date_collected") or datetime.utcnow())
        category = getattr(job, "category", None)
        for skill in skills:
            counter[(skill, week, None)] += 1
            if include_categories and category:
                counter[(skill, week, category)] += 1
    return dict(counter)


def aggregate_companies(
    jobs: Iterable, *, include_categories: bool = True
) -> dict[tuple[str, str, Optional[str]], int]:
    """Count postings per (company, week) and, if enabled, per (company, week, category)."""
    counter: Counter[tuple[str, str, Optional[str]]] = Counter()
    for job in jobs:
        company = getattr(job, "company", None)
        if not company:
            continue
        week = week_key(getattr(job, "date_collected") or datetime.utcnow())
        category = getattr(job, "category", None)
        counter[(company, week, None)] += 1
        if include_categories and category:
            counter[(company, week, category)] += 1
    return dict(counter)
