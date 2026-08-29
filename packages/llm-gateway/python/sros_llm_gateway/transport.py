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

import json
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
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
                return HttpResponse(
                    status=response.status,
                    body=response.read(),
                    headers={k.lower(): v for k, v in response.headers.items()},
                )
        except urllib.error.HTTPError as exc:
            # A 4xx/5xx is data for the adapter, not an exception here.
            return HttpResponse(
                status=exc.code,
                body=exc.read(),
                headers={k.lower(): v for k, v in (exc.headers or {}).items()},
            )
        except TimeoutError as exc:
            raise TimeoutError(f"request to {url} exceeded {timeout_seconds}s") from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, TimeoutError):
                raise TimeoutError(f"request to {url} exceeded {timeout_seconds}s") from exc
            raise TransportError(f"transport failure calling {url}: {reason}") from exc


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
