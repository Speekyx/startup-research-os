"""`UrllibTransport` failure modes against a local socket server.

Mission 1.85.9, call 24: a request with a 240 s timeout ran for 763 s and then
raised a raw `ConnectionResetError`, which no adapter mapped, so the evaluation
runner stopped the whole run as an unexpected error. These tests pin both halves:

  * a reset, before or during the response, is a `TransportError`, and the
    Anthropic adapter turns it into a retryable `ProviderTemporaryError`;
  * a server that trickles bytes, so that no single socket operation ever times
    out, still cannot hold a request past its `timeout_seconds`.

**No network, no provider key.** The server listens on loopback, and
`urllib.request.urlopen` is patched only to rewrite the `https://` scheme the
transport insists on into `http://`, so the real urllib and socket code runs.
"""

from __future__ import annotations

import contextlib
import json
import socket
import struct
import threading
import time
import unittest
import urllib.request
from collections.abc import Callable
from typing import Any
from unittest import mock

from sros_contracts import LlmTier
from sros_llm_gateway import (
    ErrorCategory,
    LlmRequest,
    ProviderTemporaryError,
    ProviderTimeoutError,
    RenderedPrompt,
    TransportError,
    UntrustedText,
    UrllibTransport,
    category_of,
    is_retryable,
)
from sros_llm_gateway.providers import AnthropicProvider

_REAL_URLOPEN = urllib.request.urlopen

# Generous against a 1 s timeout on a loaded CI runner, and still far below
# what a per-operation timeout lets a trickling server reach (unbounded).
TIMEOUT_SECONDS = 1.0
MATERIAL_OVERRUN_SECONDS = 1.5


def _plain_http_urlopen(request: urllib.request.Request, timeout: float) -> Any:
    request.full_url = request.full_url.replace("https://", "http://", 1)
    return _REAL_URLOPEN(request, timeout=timeout)


def _read_request(conn: socket.socket) -> None:
    """Consume the request line, headers and the Content-Length body."""
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(65536)
        if not chunk:
            return
        data += chunk
    head, _, body = data.partition(b"\r\n\r\n")
    length = 0
    for line in head.split(b"\r\n")[1:]:
        name, _, value = line.partition(b":")
        if name.strip().lower() == b"content-length":
            length = int(value.strip())
    while len(body) < length:
        chunk = conn.recv(65536)
        if not chunk:
            return
        body += chunk


def _reset(conn: socket.socket) -> None:
    """Close with SO_LINGER 0, which sends RST instead of FIN."""
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    conn.close()


class LocalServer:
    """One loopback listener; each connection is handled by `handler` on a thread."""

    def __init__(self, handler: Callable[[socket.socket, threading.Event], None]) -> None:
        self.stop = threading.Event()
        self._handler = handler
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(4)
        self._listener.settimeout(0.1)
        self.port = self._listener.getsockname()[1]
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    @property
    def url(self) -> str:
        return f"https://127.0.0.1:{self.port}/v1/messages"

    def _serve(self) -> None:
        while not self.stop.is_set():
            try:
                conn, _ = self._listener.accept()
            except (TimeoutError, OSError):
                continue
            conn.settimeout(None)
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        try:
            self._handler(conn, self.stop)
        except OSError:
            pass
        finally:
            with contextlib.suppress(OSError):
                conn.close()

    def close(self) -> None:
        self.stop.set()
        self._listener.close()
        self._thread.join(timeout=2)


# ------------------------------------------------------------------ handlers


def respond(status: int, payload: bytes) -> Callable[[socket.socket, threading.Event], None]:
    def handler(conn: socket.socket, stop: threading.Event) -> None:
        _read_request(conn)
        reason = {200: "OK", 500: "Internal Server Error"}[status]
        conn.sendall(
            f"HTTP/1.1 {status} {reason}\r\ncontent-type: application/json\r\n"
            f"content-length: {len(payload)}\r\nconnection: close\r\n\r\n".encode("ascii")
            + payload
        )

    return handler


def reset_before_response(conn: socket.socket, stop: threading.Event) -> None:
    _read_request(conn)
    _reset(conn)


def reset_mid_body(conn: socket.socket, stop: threading.Event) -> None:
    _read_request(conn)
    conn.sendall(b"HTTP/1.1 200 OK\r\ncontent-length: 10000\r\n\r\n" + b"{" * 100)
    time.sleep(0.05)
    _reset(conn)


def trickle_body(conn: socket.socket, stop: threading.Event) -> None:
    """Headers at once, then one body byte every 0.2 s: no read ever times out."""
    _read_request(conn)
    conn.sendall(b"HTTP/1.1 200 OK\r\ncontent-length: 100000\r\n\r\n")
    while not stop.is_set():
        conn.sendall(b" ")
        time.sleep(0.2)


def trickle_headers(conn: socket.socket, stop: threading.Event) -> None:
    """A header line that never ends, one byte every 0.2 s."""
    _read_request(conn)
    conn.sendall(b"HTTP/1.1 200 OK\r\nx-slow: ")
    while not stop.is_set():
        conn.sendall(b"a")
        time.sleep(0.2)


def stall_silently(conn: socket.socket, stop: threading.Event) -> None:
    _read_request(conn)
    stop.wait(30)


# --------------------------------------------------------------------- tests


class _ServerCase(unittest.TestCase):
    def serve(self, handler: Callable[[socket.socket, threading.Event], None]) -> LocalServer:
        server = LocalServer(handler)
        self.addCleanup(server.close)
        patcher = mock.patch.object(urllib.request, "urlopen", _plain_http_urlopen)
        patcher.start()
        self.addCleanup(patcher.stop)
        return server

    def post(self, server: LocalServer, timeout_seconds: float = TIMEOUT_SECONDS) -> Any:
        return UrllibTransport().post_json(server.url, {}, {"ping": 1}, timeout_seconds)


class UrllibTransportResponses(_ServerCase):
    def test_a_complete_response_is_returned_whole(self) -> None:
        payload = json.dumps({"ok": True, "pad": "x" * 200_000}).encode("utf-8")
        response = self.post(self.serve(respond(200, payload)))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, payload)
        self.assertEqual(response.header("Content-Type"), "application/json")

    def test_an_error_status_is_data_with_its_body(self) -> None:
        payload = b'{"error": {"message": "internal"}}'
        response = self.post(self.serve(respond(500, payload)))
        self.assertEqual(response.status, 500)
        self.assertEqual(response.body, payload)


class UrllibTransportResets(_ServerCase):
    def test_a_reset_before_the_response_is_a_transport_error(self) -> None:
        server = self.serve(reset_before_response)
        with self.assertRaises(TransportError) as ctx:
            self.post(server)
        self.assertIsInstance(ctx.exception.__cause__, OSError)

    def test_a_reset_while_reading_the_body_is_a_transport_error(self) -> None:
        server = self.serve(reset_mid_body)
        with self.assertRaises(TransportError):
            self.post(server)

    def test_a_raw_connection_reset_from_urlopen_is_wrapped(self) -> None:
        # The exact shape of call 24, independent of how the OS reports a reset.
        def resetting(request: urllib.request.Request, timeout: float) -> Any:
            raise ConnectionResetError(10054, "An existing connection was forcibly closed")

        with (
            mock.patch.object(urllib.request, "urlopen", resetting),
            self.assertRaises(TransportError) as ctx,
        ):
            UrllibTransport().post_json("https://example.invalid/", {}, {}, TIMEOUT_SECONDS)
        self.assertIsInstance(ctx.exception.__cause__, ConnectionResetError)

    def test_a_reset_raised_by_read_is_wrapped(self) -> None:
        class ResettingResponse:
            status = 200
            headers: dict[str, str] = {}

            def __enter__(self) -> ResettingResponse:
                return self

            def __exit__(self, *exc: object) -> None:
                return None

            def read(self, amt: int | None = None) -> bytes:
                raise ConnectionResetError(10054, "reset during read")

        with (
            mock.patch.object(urllib.request, "urlopen", lambda r, timeout: ResettingResponse()),
            self.assertRaises(TransportError) as ctx,
        ):
            UrllibTransport().post_json("https://example.invalid/", {}, {}, TIMEOUT_SECONDS)
        self.assertIsInstance(ctx.exception.__cause__, ConnectionResetError)

    def test_the_anthropic_adapter_maps_a_reset_to_a_retryable_temporary_error(self) -> None:
        server = self.serve(reset_before_response)
        provider = AnthropicProvider(api_key="k", endpoint=server.url)
        with self.assertRaises(ProviderTemporaryError) as ctx:
            provider.complete(_request(TIMEOUT_SECONDS), "m")
        self.assertIs(category_of(ctx.exception), ErrorCategory.TEMPORARY)
        self.assertTrue(is_retryable(ctx.exception))


class UrllibTransportDeadline(_ServerCase):
    def assert_bounded(self, handler: Callable[[socket.socket, threading.Event], None]) -> None:
        server = self.serve(handler)
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            self.post(server)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, TIMEOUT_SECONDS + MATERIAL_OVERRUN_SECONDS)
        self.assertGreaterEqual(elapsed, TIMEOUT_SECONDS * 0.9)

    def test_a_trickling_body_cannot_outlast_the_request_timeout(self) -> None:
        self.assert_bounded(trickle_body)

    def test_trickling_headers_cannot_outlast_the_request_timeout(self) -> None:
        self.assert_bounded(trickle_headers)

    def test_a_silent_server_times_out(self) -> None:
        self.assert_bounded(stall_silently)

    def test_the_timeout_is_not_a_transport_error(self) -> None:
        server = self.serve(trickle_body)
        with self.assertRaises(TimeoutError) as ctx:
            self.post(server)
        self.assertNotIsInstance(ctx.exception, TransportError)
        self.assertIn(f"exceeded {TIMEOUT_SECONDS}s", str(ctx.exception))

    def test_the_anthropic_adapter_maps_the_deadline_to_a_timeout(self) -> None:
        server = self.serve(trickle_body)
        provider = AnthropicProvider(api_key="k", endpoint=server.url)
        started = time.monotonic()
        with self.assertRaises(ProviderTimeoutError) as ctx:
            provider.complete(_request(TIMEOUT_SECONDS), "m")
        self.assertLess(time.monotonic() - started, TIMEOUT_SECONDS + MATERIAL_OVERRUN_SECONDS)
        self.assertIs(category_of(ctx.exception), ErrorCategory.TIMEOUT)


def _request(timeout_seconds: float) -> LlmRequest:
    return LlmRequest(
        tier=LlmTier.BALANCED_MODEL,
        task="classify.signal",
        prompt_template_id="signal-classify",
        prompt_template_version="1.0.0",
        workspace_id="00000000-0000-4000-8000-000000000001",
        research_session_id="00000000-0000-4000-8000-0000000000aa",
        correlation_id="corr-1",
        prompt=RenderedPrompt(
            system_instructions="You classify statements.",
            trusted_context="",
            task="Classify the statement.",
            untrusted=(UntrustedText("the export button fails", "review-42"),),
        ),
        timeout_seconds=timeout_seconds,
    )


if __name__ == "__main__":
    unittest.main()
