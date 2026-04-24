#!/usr/bin/env python3
"""Flask REST API for the Job Market Trend Analyzer.

Exposes JSON endpoints under /api/ consumed by the Next.js dashboard, plus /health
and /metrics for Fly.io health checks and Prometheus scraping.
"""
from __future__ import annotations

import os

from flask import Flask
from flask_cors import CORS

from shared.db import create_app as create_shared_app
from shared.db import ensure_schema

from .health import bp as health_bp
from .routes import bp as api_bp


def build_app() -> Flask:
    testing = os.environ.get("FLASK_TESTING") == "1"
    app = create_shared_app("web-api", testing=testing)

    origins_env = os.environ.get("CORS_ORIGINS", "*")
    origins = [o.strip() for o in origins_env.split(",") if o.strip()] or "*"
    CORS(app, resources={r"/api/*": {"origins": origins}})

    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        ensure_schema()

    return app


app = build_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
