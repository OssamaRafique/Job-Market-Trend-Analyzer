"""Tests for MuseClient.fetch_jobs - mocked at the requests.get boundary.

Mocks (not Fakes) are the right tool here: we want to verify that the client
makes the right HTTP calls, handles errors, and stops when the upstream does.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from muse_client import DEFAULT_BASE_URL, MuseClient


def _response(json_body: dict, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.content = b"{}"
    resp.json.return_value = json_body
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status}")
    return resp


def test_fetch_jobs_requests_each_page():
    page_bodies = [
        {"results": [{"name": "A"}, {"name": "B"}]},
        {"results": [{"name": "C"}]},
    ]
    responses = [_response(body) for body in page_bodies]

    with patch("muse_client.requests.get", side_effect=responses) as mocked_get:
        client = MuseClient()
        results = client.fetch_jobs(category="Software Engineer", pages=2)

    assert [r["name"] for r in results] == ["A", "B", "C"]
    assert mocked_get.call_count == 2

    first_call = mocked_get.call_args_list[0]
    assert first_call.args[0] == DEFAULT_BASE_URL
    assert first_call.kwargs["params"] == {"category": "Software Engineer", "page": 0}
    assert first_call.kwargs["timeout"] == 10.0


def test_fetch_jobs_uses_custom_base_url():
    with patch("muse_client.requests.get", return_value=_response({"results": []})) as mocked_get:
        client = MuseClient(base_url="http://example.test/jobs")
        client.fetch_jobs("Data Science", 1)
    assert mocked_get.call_args.args[0] == "http://example.test/jobs"


def test_fetch_jobs_skips_failed_page_and_continues():
    # First page raises, second page succeeds. We expect only second page results.
    responses = [
        requests.ConnectionError("boom"),
        _response({"results": [{"name": "survivor"}]}),
    ]

    with patch("muse_client.requests.get", side_effect=responses):
        client = MuseClient()
        results = client.fetch_jobs(category="Software Engineer", pages=2)

    assert len(results) == 1
    assert results[0]["name"] == "survivor"


def test_fetch_jobs_returns_empty_on_http_error():
    resp = _response({}, status=500)
    with patch("muse_client.requests.get", return_value=resp):
        client = MuseClient()
        results = client.fetch_jobs("Product", 1)
    assert results == []


def test_fetch_jobs_handles_missing_results_key():
    with patch("muse_client.requests.get", return_value=_response({})):
        client = MuseClient()
        results = client.fetch_jobs("Product", 1)
    assert results == []
