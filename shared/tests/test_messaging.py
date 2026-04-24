"""Unit tests for ``shared.messaging``.

These tests swap :mod:`shared.messaging._pika` for a fake module so we can
verify publish/consume wiring without needing a running broker (or even the
``pika`` package installed).
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from shared import messaging


class FakeChannel:
    def __init__(self):
        self.declared = []
        self.published = []
        self.qos = None
        self.consumer = None
        self.consuming = False
        self.acks = []
        self.nacks = []

    def queue_declare(self, queue, durable=False, **_):
        self.declared.append((queue, durable))

    def basic_publish(self, *, exchange, routing_key, body, properties=None):
        self.published.append(
            {
                "exchange": exchange,
                "routing_key": routing_key,
                "body": body,
                "delivery_mode": getattr(properties, "delivery_mode", None),
            }
        )

    def basic_qos(self, prefetch_count):
        self.qos = prefetch_count

    def basic_consume(self, queue, on_message_callback, auto_ack):
        self.consumer = (queue, on_message_callback, auto_ack)

    def basic_ack(self, delivery_tag):
        self.acks.append(delivery_tag)

    def basic_nack(self, delivery_tag, requeue):
        self.nacks.append((delivery_tag, requeue))

    def start_consuming(self):
        self.consuming = True
        queue, cb, _ = self.consumer
        for i, (body, should_raise) in enumerate(self._scripted):
            method = SimpleNamespace(delivery_tag=i + 1)
            cb(self, method, None, body)
            if should_raise and not self.nacks:
                raise AssertionError("handler raised but nack not recorded")

    _scripted: list[tuple[bytes, bool]] = []


class FakeConnection:
    def __init__(self, channel):
        self._channel = channel

    def channel(self):
        return self._channel

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def close(self):
        pass


@pytest.fixture
def fake_pika(monkeypatch):
    channel = FakeChannel()

    class FakeBasicProperties:
        def __init__(self, delivery_mode=None):
            self.delivery_mode = delivery_mode

    fake_module = SimpleNamespace(
        URLParameters=lambda url: {"url": url},
        BlockingConnection=lambda params: FakeConnection(channel),
        BasicProperties=FakeBasicProperties,
    )
    monkeypatch.setattr(messaging, "_pika", lambda: fake_module)
    monkeypatch.setenv("AMQP_URL", "amqp://guest:guest@localhost:5672/")
    return channel


def test_publish_declares_durable_queue_and_serializes_payload(fake_pika):
    messaging.publish("collect_jobs", {"trigger": "test", "count": 1})

    assert fake_pika.declared == [("collect_jobs", True)]
    assert len(fake_pika.published) == 1
    published = fake_pika.published[0]
    assert published["routing_key"] == "collect_jobs"
    assert json.loads(published["body"]) == {"trigger": "test", "count": 1}
    assert published["delivery_mode"] == 2


def test_publish_without_amqp_url_raises(monkeypatch):
    monkeypatch.delenv("AMQP_URL", raising=False)
    with pytest.raises(RuntimeError, match="AMQP_URL"):
        messaging.publish("collect_jobs", {})


def test_decode_body_handles_empty_and_bad_payloads():
    assert messaging.decode_body(b"") == {}
    assert messaging.decode_body(b"not-json") == {}
    assert messaging.decode_body(b'{"ok": true}') == {"ok": True}


def test_consume_forever_acks_on_handler_success(fake_pika):
    FakeChannel._scripted = [(b'{"trigger": "test"}', False)]
    received = []

    def handler(payload):
        received.append(payload)

    messaging.consume_forever("analyze_jobs", handler)

    assert received == [{"trigger": "test"}]
    assert fake_pika.acks == [1]
    assert fake_pika.nacks == []
    assert fake_pika.qos == 1


def test_consume_forever_nacks_on_handler_failure(fake_pika):
    FakeChannel._scripted = [(b'{"x": 1}', True)]
    handler = MagicMock(side_effect=RuntimeError("boom"))

    messaging.consume_forever("analyze_jobs", handler)

    assert fake_pika.acks == []
    assert fake_pika.nacks == [(1, True)]
    handler.assert_called_once()
