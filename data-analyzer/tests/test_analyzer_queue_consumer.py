"""Tests for the analyzer-consumer handle_message wiring."""
from __future__ import annotations

import logging
from unittest.mock import patch

import analyzer_consumer


def test_handle_message_runs_analysis(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ANALYZER_WINDOW_DAYS", "14")

    log = logging.getLogger("test")

    with patch(
        "analyzer_consumer.run_analysis", return_value=(3, 5)
    ) as run_analysis_mock:
        analyzer_consumer.handle_message({"trigger": "collector"}, log)

    run_analysis_mock.assert_called_once()
    _, _, days_arg, _ = run_analysis_mock.call_args.args
    assert days_arg == 14
