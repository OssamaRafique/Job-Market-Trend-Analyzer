"""Shared fixtures for gateway integration tests.

These tests require a real Postgres instance — set ``DATABASE_URL`` (and
``USE_REAL_DB=1``) before running pytest. Locally you can spin one up with

    docker-compose up -d postgres
    DATABASE_URL=postgresql://jmta:dev@localhost:5432/jmta USE_REAL_DB=1 pytest shared/
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _real_db_available() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("USE_REAL_DB") != "1":
        return False
    return url.startswith("postgresql://") or url.startswith("postgres://")


requires_real_db = pytest.mark.skipif(
    not _real_db_available(),
    reason="set DATABASE_URL and USE_REAL_DB=1 to run integration tests",
)


@pytest.fixture
def db_app():
    """Yield a Flask app bound to the real Postgres DB with a fresh schema."""
    from shared.db import create_app, db

    app = create_app("shared-tests")
    with app.app_context():
        db.drop_all()
        db.create_all()
        try:
            yield app
        finally:
            db.session.rollback()
            db.drop_all()
