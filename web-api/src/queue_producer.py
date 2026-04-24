"""RabbitMQ producer used by ``POST /api/refresh``."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from shared.messaging import COLLECT_JOBS, publish


def publish_collect_jobs(payload: Optional[dict[str, Any]] = None) -> None:
    """Enqueue a job for the data-collector worker to pick up."""
    body = payload or {}
    body.setdefault("trigger", "api")
    body.setdefault("requested_at", datetime.now(timezone.utc).isoformat())
    publish(COLLECT_JOBS, body)
