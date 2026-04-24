"""Tests for the collector-consumer handle_message wiring.

We stub out the underlying work (``collect_all``) and the outbound publish so
the test stays in-process and does not hit Postgres, RabbitMQ, or The Muse.
"""
from __future__ import annotations

import logging
from unittest.mock import patch

import collector_consumer


def test_handle_message_runs_collection_and_publishes_analyze_jobs(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("COLLECTOR_PAGES", "1")
    monkeypatch.setenv(
        "COLLECTOR_CATEGORIES", "Software Engineer,Data Science"
    )

    log = logging.getLogger("test")

    with patch(
        "collector_consumer.collect_all", return_value=42
    ) as collect_all_mock, patch(
        "collector_consumer.publish"
    ) as publish_mock:
        collector_consumer.handle_message({"trigger": "api"}, log)

    assert collect_all_mock.call_count == 1
    passed_categories = collect_all_mock.call_args.args[2]
    assert passed_categories == ["Software Engineer", "Data Science"]

    publish_mock.assert_called_once()
    queue_name, payload = publish_mock.call_args.args
    assert queue_name == "analyze_jobs"
    assert payload == {"trigger": "collector", "ingested": 42}


def test_handle_message_propagates_collector_failures(monkeypatch):
    """Failures must propagate so ``consume_forever`` can nack the message."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    log = logging.getLogger("test")

    with patch(
        "collector_consumer.collect_all", side_effect=RuntimeError("muse down")
    ), patch("collector_consumer.publish") as publish_mock:
        try:
            collector_consumer.handle_message({}, log)
        except RuntimeError:
            pass
        else:  # pragma: no cover - defensive
            raise AssertionError("expected RuntimeError to propagate")

    publish_mock.assert_not_called()
