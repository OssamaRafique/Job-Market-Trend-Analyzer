"""Pure aggregation helpers for the data analyzer.

Kept free of database access so they can be unit-tested in isolation over a
list of plain JobRecord objects.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Iterable, Optional

# Skills extracted from job text (case-insensitive, lowercase).
KNOWN_SKILLS: frozenset[str] = frozenset(
    {
        # Languages
        "python", "typescript", "javascript", "java", "kotlin", "scala", "go",
        "rust", "ruby", "php", "swift", "c#", "c++",
        # Front end
        "react", "vue", "angular", "svelte", "next.js", "nuxt", "node",
        # Back end frameworks
        "django", "flask", "fastapi", "spring", "express", "nestjs", "rails",
        "graphql",
        # Data / analytics
        "sql", "postgres", "postgresql", "mysql", "mongodb", "redis",
        "snowflake", "databricks", "airflow", "dbt", "spark", "kafka", "hadoop",
        "tableau", "excel",
        # Cloud / infra
        "aws", "gcp", "azure", "kubernetes", "docker", "terraform", "ansible",
        "linux", "git",
        # ML / data science
        "pytorch", "tensorflow", "sklearn", "pandas", "numpy", "llm",
        # Process / business tools
        "agile", "scrum", "jira", "salesforce", "figma",
        # Roles / general
        "devops", "sre", "ml", "ai",
    }
)

# Tokens that frequently appear as two words or with punctuation. Map from the
# raw substring we search for, to the canonical skill key we store. Canonical
# keys do not have to be in ``KNOWN_SKILLS`` (we add them directly).
PHRASE_ALIASES: dict[str, str] = {
    "next.js": "next.js",
    "nextjs": "next.js",
    "node.js": "node",
    "nodejs": "node",
    "machine learning": "ml",
    "artificial intelligence": "ai",
    "power bi": "powerbi",
    "ci/cd": "ci/cd",
    "c.i./c.d.": "ci/cd",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9+#.]+")
HTML_TAG_RE = re.compile(r"<[^>]+>")
HTML_ENTITY_RE = re.compile(r"&[a-z#0-9]+;", re.IGNORECASE)


def _strip_html(text: str) -> str:
    """Flatten HTML to plain text for keyword matching."""
    no_tags = HTML_TAG_RE.sub(" ", text)
    return HTML_ENTITY_RE.sub(" ", no_tags)


def tokenize_text(text: str) -> set[str]:
    """Return the set of known skills mentioned in ``text`` (case-insensitive).

    Accepts either plain strings or HTML; tags are stripped before matching.
    """
    if not text:
        return set()
    lowered = _strip_html(text).lower()
    matched: set[str] = set()

    for phrase, canonical in PHRASE_ALIASES.items():
        if phrase in lowered:
            matched.add(canonical)

    for raw in TOKEN_RE.findall(lowered):
        if raw in KNOWN_SKILLS:
            matched.add(raw)
    return matched


# Kept for backward compatibility with earlier call sites and tests.
tokenize_title = tokenize_text


def week_key(dt: datetime) -> str:
    """Return the ISO week key for ``dt`` in the form ``YYYY-Www`` (e.g. ``2026-W16``)."""
    year, week, _ = dt.isocalendar()
    return f"{year:04d}-W{week:02d}"


def aggregate_skills(
    jobs: Iterable, *, include_categories: bool = True
) -> dict[tuple[str, str, Optional[str]], int]:
    """Count skill mentions per (skill, week) and, if enabled, per (skill, week, category).

    Scans both ``title`` and ``description`` (HTML-stripped) on each job, so
    skills that only appear in the long-form posting still get picked up.
    """
    counter: Counter[tuple[str, str, Optional[str]]] = Counter()
    for job in jobs:
        title = getattr(job, "title", "") or ""
        description = getattr(job, "description", "") or ""
        skills = tokenize_text(f"{title}\n{description}")
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
