"""SQLAlchemy singleton and Flask app factory.

All three Python services import `db` from here and use `create_app` to obtain
an application context (web-api runs it as a real web server; collector and
analyzer only need the context to talk to the database).
"""
from __future__ import annotations

import logging
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db = SQLAlchemy()
logger = logging.getLogger(__name__)


def _normalize_database_url(url: str) -> str:
    # Fly Postgres hands out URLs with the "postgres://" scheme which SQLAlchemy 2.x
    # no longer accepts. Swap it for the canonical "postgresql://" scheme.
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def create_app(name: str = "jmta", *, testing: bool = False) -> Flask:
    """Build a minimal Flask app wired up to the shared SQLAlchemy instance.

    Workers pass their own name (e.g. "collector") so logs disambiguate which
    service produced them. `testing=True` uses an in-memory SQLite DB so unit
    tests do not need a Postgres instance to boot.
    """
    app = Flask(name)

    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "DATABASE_URL is not set. Copy .env.example to .env for local dev, "
                "or run `fly postgres attach` to wire up the production DB."
            )
        app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_database_url(url)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def ensure_schema() -> None:
    """Create missing tables and apply lightweight, idempotent column adds.

    We intentionally keep this very small: for richer changes we would bring
    in Alembic. It runs on every worker boot so older ``jobs`` tables
    provisioned before we introduced newer columns get the columns added
    automatically.

    Must be called inside an active Flask app context.
    """
    db.create_all()

    engine = db.engine
    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("jobs")}

    if "source_id" not in columns:
        logger.info("adding missing column jobs.source_id")
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN source_id VARCHAR(100)"))
            # Postgres permits multiple NULLs in a UNIQUE index, so rows
            # collected before we introduced source_id (all NULL) coexist fine.
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS ix_jobs_source_id ON jobs (source_id)")
            )

    if "description" not in columns:
        logger.info("adding missing column jobs.description")
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN description TEXT"))
