"""The HTTP boundary. The only file in this package that may reach a network.

Mission 1.5 §10 and §11.

**One file, and CI pins it there.** Every other module in `sros_acquisition` is
still forbidden from importing an HTTP client, which is the same guard Mission
1.0 introduced — narrowed rather than deleted, exactly as the D-03 aggregation
guard was narrowed in Mission 1.2. Narrowing it to a single named file is a
stronger statement than the old blanket ban: it says where the network is, not
merely that it is absent.

**A request is built from an authorized resource, never from a URL.** There is
no function here that takes a URL string from a caller. `HttpRequest` carries a
host, a path and a query mapping; the host is checked against an allowlist the
authorization context supplies, and a redirect that leaves it is refused rather
than followed. §10 requires the escape to be impossible, not discouraged.

**httpx is imported inside the function that needs it**, the same way psycopg is
in the registry CLI. ADR-009's argument holds: the registry model, the
compliance layer and every zero-dependency validator must keep running with
nothing installed, and they would not if this module imported a client at
module scope.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse

from sros_contracts import AcquisitionErrorCode

from .errors import AcquisitionFailedError, AcquisitionFailure

__all__ = [
    "HttpRequest",
    "HttpResponse",
    "HttpxTransport",
    "Transport",
    "TransportConfig",
    "host_of",
]

# Identifies this client to the source. §11: a collector that will not say who
# it is cannot be contacted when it misbehaves, which is a worse position for
# everyone than being identifiable.
DEFAULT_USER_AGENT = "startup-research-os/1.0 (+https://github.com/Speekyx/startup-research-os)"


def host_of(url: str) -> str:
    """The host of an absolute URL, lowercased. Empty when there is not one."""
    return (urlparse(url).hostname or "").lower()


@dataclass(frozen=True)
class TransportConfig:
    """Timeouts and bounds. Every one of them is required to have a value.

    A transport with no read timeout does not fail; it hangs, holds a worker
    slot, and is discovered when the queue has stopped moving.
    """

    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 20.0
    total_timeout_seconds: float = 30.0
    user_agent: str = DEFAULT_USER_AGENT
    max_response_bytes: int = 8 * 1024 * 1024

    def __post_init__(self) -> None:
        for name in (
            "connect_timeout_seconds",
            "read_timeout_seconds",
            "total_timeout_seconds",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive; an absent timeout is a hang")
        if self.max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")


@dataclass(frozen=True)
class HttpRequest:
    """A request the collector composed. Never a caller-supplied URL.

    `path` and `query` are separate so nothing can smuggle a host, a scheme or a
    second query string through a single string field. The transport assembles
    them against the authorized base URL and nothing else.
    """

    path: str
    query: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.path.startswith(("http://", "https://", "//")):
            raise ValueError(
                "path is a path, not a URL. A collector composes requests from an "
                "authorized base; accepting an absolute URL here would be the escape "
                "hatch §4 forbids"
            )
        if ".." in self.path:
            raise ValueError("path must not traverse; '..' cannot appear")


@dataclass(frozen=True)
class HttpResponse:
    """What came back. The body is text; parsing belongs to the collector."""

    status_code: int
    text: str
    elapsed_seconds: float
    url_path: str


class Transport(Protocol):
    """Injectable so the test suite never needs the public internet (§11, §42).

    `allowed_hosts` is passed per call rather than configured once: the
    allowlist comes from the authorization context, and a transport that
    remembered a host from a previous job could serve the wrong one.
    """

    def get(
        self, base_url: str, request: HttpRequest, allowed_hosts: frozenset[str]
    ) -> HttpResponse: ...


class HttpxTransport:
    """The real transport. Refuses anything outside the allowlist.

    Redirects are **not followed**. §10 requires that a redirect cannot be used
    to escape to an unauthorized host, and the safe way to guarantee that is to
    treat a redirect as a response the collector has to reason about rather than
    as a hop the client silently takes. The World Bank Indicators API does not
    redirect for the paths this collector composes; if it starts, that is a
    change worth noticing rather than absorbing.
    """

    def __init__(self, config: TransportConfig | None = None) -> None:
        self.config = config or TransportConfig()

    def get(
        self, base_url: str, request: HttpRequest, allowed_hosts: frozenset[str]
    ) -> HttpResponse:
        url = self._compose(base_url, request, allowed_hosts)
        client = self._client()
        try:
            response = client.get(url, params=dict(request.query))
        except Exception as exc:  # noqa: BLE001 - normalised deliberately, see below
            # The library's exception text is NOT copied into the failure. §33:
            # a third party has no obligation to keep secrets out of its own
            # messages, and the type name is enough for an operator.
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=self._code_for(exc),
                    detail=(
                        f"the request did not complete ({type(exc).__name__}); "
                        f"connect {self.config.connect_timeout_seconds}s, "
                        f"read {self.config.read_timeout_seconds}s"
                    ),
                    source_id="",
                    context={"path": request.path},
                )
            ) from None
        finally:
            client.close()

        # A redirect never becomes a second request. Reported as what it is.
        if 300 <= response.status_code < 400:
            location = response.headers.get("location", "")
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.INVALID_RESPONSE,
                    detail=(
                        f"the source redirected to host "
                        f"{host_of(location) or 'an unparseable location'!r}, which this "
                        "collector does not follow: a redirect is the documented way out "
                        "of a host allowlist"
                    ),
                    source_id="",
                    context={"status": response.status_code, "path": request.path},
                )
            )

        text = response.text
        if len(text.encode("utf-8")) > self.config.max_response_bytes:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.INVALID_RESPONSE,
                    detail=(
                        f"the response exceeded {self.config.max_response_bytes} bytes; "
                        "an unbounded body is a memory bound nobody set"
                    ),
                    source_id="",
                    context={"path": request.path},
                )
            )
        return HttpResponse(
            status_code=response.status_code,
            text=text,
            elapsed_seconds=response.elapsed.total_seconds() if response.elapsed else 0.0,
            url_path=request.path,
        )

    def _compose(self, base_url: str, request: HttpRequest, allowed_hosts: frozenset[str]) -> str:
        """Assemble the URL and refuse a host the registry did not authorise.

        Checked here as well as at the collector, on purpose. This is the last
        place before a socket, and a guard that only exists further up is a
        guard a future caller can route around.
        """
        if not allowed_hosts:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        "no host allowlist was supplied. An empty allowlist is not "
                        "permission to reach anything"
                    ),
                    source_id="",
                )
            )
        base = base_url if base_url.endswith("/") else base_url + "/"
        host = host_of(base)
        if host not in allowed_hosts:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        f"host {host!r} is not in the authorized set "
                        f"{sorted(allowed_hosts)}, which comes from the access profile "
                        "the review approved"
                    ),
                    source_id="",
                )
            )
        if not base.startswith("https://"):
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail="the authorized endpoint is not https",
                    source_id="",
                )
            )
        return base + request.path.lstrip("/")

    def _client(self) -> Any:
        """Imported here, not at module scope (ADR-009). See the module docstring."""
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.TEMPORARY_UPSTREAM,
                    detail=(
                        "httpx is not installed, so no request can be made. Install the "
                        "workspace dependencies (uv sync --all-packages)"
                    ),
                    source_id="",
                )
            ) from exc
        return httpx.Client(
            timeout=httpx.Timeout(
                self.config.total_timeout_seconds,
                connect=self.config.connect_timeout_seconds,
                read=self.config.read_timeout_seconds,
            ),
            # Never followed. See the class docstring.
            follow_redirects=False,
            headers={"User-Agent": self.config.user_agent, "Accept": "application/json"},
        )

    @staticmethod
    def _code_for(exc: BaseException) -> AcquisitionErrorCode:
        """Map a client exception to a normalised code by NAME.

        By name rather than by class, so this module does not have to import
        httpx at module scope in order to reference its exception types — which
        is the whole reason the import is lazy.
        """
        name = type(exc).__name__
        if "Timeout" in name:
            return AcquisitionErrorCode.NETWORK_TIMEOUT
        if "Connect" in name or "Network" in name or "Protocol" in name or "Remote" in name:
            return AcquisitionErrorCode.TEMPORARY_UPSTREAM
        return AcquisitionErrorCode.TEMPORARY_UPSTREAM
