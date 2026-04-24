"""Client for The Muse public jobs API."""
from __future__ import annotations

import logging
from typing import Any, Optional

import requests

DEFAULT_BASE_URL = "https://www.themuse.com/api/public/jobs"

logger = logging.getLogger(__name__)


class MuseClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self.base_url = base_url or DEFAULT_BASE_URL
        self.timeout = timeout

    def fetch_jobs(self, category: str, pages: int) -> list[dict[str, Any]]:
        """Fetch ``pages`` pages of postings for ``category``; returns raw dicts.

        Failed pages are skipped with a warning rather than aborting the run.
        """
        results: list[dict[str, Any]] = []
        for page in range(pages):
            try:
                resp = requests.get(
                    self.base_url,
                    params={"category": category, "page": page},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.warning(
                    "muse fetch failed category=%s page=%s err=%s", category, page, exc
                )
                continue
            body = resp.json() if resp.content else {}
            results.extend(body.get("results") or [])
        return results

    @staticmethod
    def parse_job(raw: dict[str, Any]) -> dict[str, Any]:
        """Normalise a Muse API job dict into our persistence shape.

        ``source_id`` is the stringified upstream job id when present; the
        ``JobDataGateway`` uses it to skip postings we have already stored.
        """
        categories = raw.get("categories") or [{}]
        levels = raw.get("levels") or [{}]
        locations = raw.get("locations") or [{}]
        raw_id = raw.get("id")
        return {
            "source_id": str(raw_id) if raw_id is not None else None,
            "title": raw.get("name") or "Unknown",
            "company": (raw.get("company") or {}).get("name"),
            "category": categories[0].get("name"),
            "level": levels[0].get("name"),
            "location": locations[0].get("name"),
            # Full HTML description. The analyzer strips tags and mines this
            # for skill keywords (titles alone are too sparse to trend on).
            "description": raw.get("contents"),
        }
