"""Health and /metrics endpoints."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return jsonify(status="healthy"), 200


@bp.get("/metrics")
def metrics():
    payload = generate_latest(REGISTRY)
    return Response(payload, mimetype=CONTENT_TYPE_LATEST)
