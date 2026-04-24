"""RabbitMQ helpers shared across the three Python services."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable, Optional

COLLECT_JOBS = "collect_jobs"
ANALYZE_JOBS = "analyze_jobs"

logger = logging.getLogger(__name__)


def _pika():
    """Lazy-import pika so tests can run without it installed."""
    import pika  # type: ignore[import-not-found]

    return pika


def _resolve_url(url: Optional[str] = None) -> str:
    resolved = url or os.environ.get("AMQP_URL")
    if not resolved:
        raise RuntimeError("AMQP_URL is required for RabbitMQ operations")
    return resolved


def _connection_params(url: Optional[str] = None):
    return _pika().URLParameters(_resolve_url(url))


def publish(queue: str, payload: dict[str, Any], *, url: Optional[str] = None) -> None:
    """Publish a single persistent message to ``queue``."""
    resolved = _resolve_url(url)
    pika = _pika()
    params = pika.URLParameters(resolved)
    with pika.BlockingConnection(params) as conn:
        channel = conn.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    logger.info("published queue=%s payload=%s", queue, payload)


def decode_body(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("could not decode message body=%r", body[:200])
        return {}


def consume_forever(
    queue: str,
    handler: Callable[[dict[str, Any]], None],
    *,
    url: Optional[str] = None,
) -> None:
    """Block forever, dispatching each message on ``queue`` to ``handler``.

    ``handler`` should raise if processing fails — the message is nack'd back
    onto the queue for redelivery. On success it's ack'd.
    """
    resolved = _resolve_url(url)
    pika = _pika()
    params = pika.URLParameters(resolved)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_qos(prefetch_count=1)

    def _on_message(ch, method, _properties, body):  # noqa: ANN001 (pika callback sig)
        payload = decode_body(body)
        try:
            handler(payload)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("ack queue=%s", queue)
        except Exception:
            logger.exception("handler failed for queue=%s; requeueing", queue)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_consume(queue=queue, on_message_callback=_on_message, auto_ack=False)
    logger.info("consuming queue=%s", queue)
    channel.start_consuming()
