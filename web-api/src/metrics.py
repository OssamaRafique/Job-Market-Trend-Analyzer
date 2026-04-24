"""Prometheus metrics for the web-api."""
from __future__ import annotations

from prometheus_client import Counter

jobs_requests_total = Counter(
    "jmta_jobs_requests_total",
    "Number of /api/jobs requests served",
)

trends_requests_total = Counter(
    "jmta_trends_requests_total",
    "Number of /api/trends/* requests served",
    ["kind"],  # skills | companies
)

categories_requests_total = Counter(
    "jmta_categories_requests_total",
    "Number of /api/categories requests served",
)

collect_triggers_total = Counter(
    "jmta_collect_triggers_total",
    "Number of POST /api/refresh calls",
    ["result"],  # queued | broker_unavailable
)
