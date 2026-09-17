"""HTTP transport for provider adapters.

Mission 0.4 §20. The seam that makes provider adapters **fully testable without
a network, an API key or a bill**.

**Why raw HTTP rather than the vendor SDKs.** ADR-006 forbids a provider SDK
outside `providers/`, and permits one inside. Using none at all is stronger and
cheaper here:

  * `uv.lock` gains no vendor dependency, so a provider's release cadence cannot
    break this repository's install;
  * both adapters speak the same `HttpTransport` protocol, so the fake below is
    the *whole* mock surface — no per-SDK stubbing, no monkeypatching of client
    internals;
  * the request each adapter builds is visible in the test as a dict, which is
    what §37 asks to assert on.

The cost, stated plainly: streaming, retries-with-jitter inside an SDK, and
provider-specific helpers must be implemented here rather than inherited. None
of those is needed yet, and the gateway already owns retry policy.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

__all__ = [
    "HttpResponse",
    "HttpTransport",
    "UrllibTransport",
    "FakeTransport",
    "TransportError",
]


class TransportError(RuntimeError):
    """A transport-level failure with no HTTP status: DNS, refused, reset."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    headers: dict[str, str] = field(default_factory=dict)

    def json(self) -> dict[str, Any]:
        """Parse the body, or raise a transport error naming what came back.

        A provider returning HTML from a proxy or a captive portal is a real
        failure mode, and `json.JSONDecodeError` alone does not say which
        provider produced it.
        """
        try:
            parsed = json.loads(self.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            preview = self.body[:200].decode("utf-8", errors="replace")
            raise TransportError(
                f"response was not JSON (status {self.status}): {preview!r}"
            ) from exc
        if not isinstance(parsed, dict):
            raise TransportError(f"expected a JSON object, got {type(parsed).__name__}")
        return parsed

    def header(self, name: str) -> str | None:
        lowered = name.lower()
        for key, value in self.headers.items():
            if key.lower() == lowered:
                return value
        return None


class HttpTransport(Protocol):
    """One method, because one method is all a provider adapter needs."""

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> HttpResponse: ...


class UrllibTransport:
    """The real transport. Standard library only.

    Returns non-2xx responses rather than raising on them: the adapter maps a
    status to an internal error category (§21), and that mapping belongs with
    the provider that knows what its statuses mean.
    """

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> HttpResponse:
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(  # noqa: S310 - https endpoint from provider config
            url,
            data=payload,
            headers={"content-type": "application/json", **headers},
            method="POST",
        )
        if not url.startswith("https://"):
            # Provider endpoints are configuration, and configuration reaches
            # production. An API key on a plaintext connection is a leaked key.
            raise TransportError(f"refusing to send credentials over a non-HTTPS URL: {url!r}")

        # urllib's `timeout` bounds each socket operation, not the request: a
        # connection that trickles bytes or stalls between reads can run far past
        # it (Mission 1.85.9: 763 s against 240 s). The exchange therefore runs on
        # a worker thread, and the caller waits for the whole request at most
        # `timeout_seconds`. The worker is told to stop, and stops at its next
        # read or when its shrunken socket timeout fires; its result is discarded.
        deadline = time.monotonic() + timeout_seconds
        cancelled = threading.Event()
        outcome: list[HttpResponse | BaseException] = []

        def exchange() -> None:
            try:
                outcome.append(_exchange(request, timeout_seconds, deadline, cancelled))
            except BaseException as exc:  # noqa: BLE001 - re-raised on the caller's thread
                outcome.append(exc)

        worker = threading.Thread(target=exchange, name="sros-llm-transport", daemon=True)
        worker.start()
        worker.join(max(0.0, deadline - time.monotonic()))
        if worker.is_alive() or not outcome:
            cancelled.set()
            raise TimeoutError(f"request to {url} exceeded {timeout_seconds}s")

        result = outcome[0]
        if isinstance(result, HttpResponse):
            return result
        try:
            raise result
        except TimeoutError as exc:
            raise TimeoutError(f"request to {url} exceeded {timeout_seconds}s") from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, TimeoutError):
                raise TimeoutError(f"request to {url} exceeded {timeout_seconds}s") from exc
            raise TransportError(f"transport failure calling {url}: {reason}") from exc
        except (OSError, http.client.HTTPException) as exc:
            # A reset, an abort or a truncated body after the connection opened:
            # urllib raises these raw rather than as URLError. Unwrapped, they
            # escape the adapter's error mapping and stop a whole run as
            # unexpected (Mission 1.85.9, call 24: ConnectionResetError).
            raise TransportError(
                f"transport failure calling {url}: {type(exc).__name__}: {exc}"
            ) from exc


_READ_CHUNK_BYTES = 64 * 1024


def _exchange(
    request: urllib.request.Request,
    timeout_seconds: float,
    deadline: float,
    cancelled: threading.Event,
) -> HttpResponse:
    """Send the request and read the whole body, never reading past `deadline`."""
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body = _read_until(response, deadline, cancelled)
            return HttpResponse(
                status=response.status,
                body=body,
                headers={k.lower(): v for k, v in response.headers.items()},
            )
    except urllib.error.HTTPError as exc:
        # A 4xx/5xx is data for the adapter, not an exception here.
        with exc:
            return HttpResponse(
                status=exc.code,
                body=_read_until(exc, deadline, cancelled),
                headers={k.lower(): v for k, v in (exc.headers or {}).items()},
            )


def _read_until(response: Any, deadline: float, cancelled: threading.Event) -> bytes:
    """Read the body in chunks, checking the deadline before every read.

    The socket timeout is lowered to the time left before each read, so a single
    stalled read cannot outlast the request either. Reaching the socket is
    best effort: `http.client` does not expose it, and a response without one
    still stops at the next chunk boundary.
    """
    chunks: list[bytes] = []
    while True:
        remaining = deadline - time.monotonic()
        if cancelled.is_set() or remaining <= 0:
            raise TimeoutError("the request deadline passed while reading the body")
        _set_socket_timeout(response, remaining)
        chunk = response.read(_READ_CHUNK_BYTES)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _set_socket_timeout(response: Any, seconds: float) -> None:
    fp: Any = getattr(response, "fp", None)
    # An HTTPError wraps the HTTPResponse that holds the socket.
    fp = getattr(fp, "fp", fp)
    sock = getattr(getattr(fp, "raw", None), "_sock", None)
    settimeout = getattr(sock, "settimeout", None)
    if callable(settimeout):
        with contextlib.suppress(OSError):
            settimeout(max(seconds, 0.001))


@dataclass
class FakeTransport:
    """A scripted transport for tests.

    Queue `HttpResponse` objects to return, or exception instances to raise.
    Every call is recorded, so a test can assert on the request an adapter
    actually built — which is the point of §37's "request translation".
    """

    responses: deque[HttpResponse | BaseException] = field(default_factory=deque)
    calls: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def returning(cls, *items: HttpResponse | BaseException) -> FakeTransport:
        return cls(responses=deque(items))

    @classmethod
    def json_ok(cls, *payloads: dict[str, Any]) -> FakeTransport:
        return cls.returning(*(HttpResponse(200, json.dumps(p).encode("utf-8")) for p in payloads))

    def queue(self, items: Iterable[HttpResponse | BaseException]) -> None:
        self.responses.extend(items)

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> HttpResponse:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        if not self.responses:
            raise AssertionError(
                f"FakeTransport received an unscripted call to {url}. "
                "A provider adapter made more requests than the test expected, "
                "which is usually a retry loop that should not exist."
            )
        item = self.responses.popleft()
        if isinstance(item, BaseException):
            raise item
        return item

    @property
    def last_body(self) -> dict[str, Any]:
        return dict(self.calls[-1]["body"])
