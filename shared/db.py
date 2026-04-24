"""SQLAlchemy singleton and Flask app factory.

All three Python services import `db` from here and use `create_app` to obtain
an application context (web-api runs it as a real web server; collector and
analyzer only need the context to talk to the database).
"""
from __future__ import annotations

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
