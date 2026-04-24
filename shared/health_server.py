"""Lightweight HTTP health server for worker processes.

Start it in a background thread when ``HEALTH_PORT`` is set:

    from shared.health_server import start_if_enabled
    start_if_enabled()
"""
from __future__ import annotations

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logger = logging.getLogger(__name__)


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (http.server mandates this name)
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # noqa: A002 (shadowing is http.server's fault)
        logger.debug("health %s", format % args)


def _run(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    logger.info("health server listening on :%d", port)
    server.serve_forever()


def start_if_enabled() -> None:
    port_raw = os.environ.get("HEALTH_PORT")
    if not port_raw:
        return
    try:
        port = int(port_raw)
    except ValueError:
        logger.warning("HEALTH_PORT=%r is not an integer; skipping", port_raw)
        return
    thread = threading.Thread(target=_run, args=(port,), daemon=True, name="health-server")
    thread.start()
