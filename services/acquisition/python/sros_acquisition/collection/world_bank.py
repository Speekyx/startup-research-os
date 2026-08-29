"""The World Bank Indicators collector.

Mission 1.5. The first real collector, and the reference every later one follows.

**It cannot run without an authorization.** `collect` takes an
`AcquisitionAuthorizationContext` as its first argument, and there is no
overload, default or fallback that makes one. `build_authorization` produced it,
which means the canonical gate passed; a collector that could construct its own
would be a collector that could approve itself.

**It cannot reach a URL a caller chose.** A `WorldBankRequest` names indicators,
countries and a period. It has no field for a path, a host or a query fragment,
so there is nothing to smuggle one through. The collector composes every request
from validated parameters, and the transport refuses any host outside the
allowlist the access profile authorised.

**Every resource is authorised before a socket opens.** For each indicator the
collector looks up the authorized dataset — the licence, family and content
origin come from governance, never from the caller — builds a
`ResourceDescriptor` from it, and asks `context.authorize_resource(...)`. A
refusal ends that indicator with **zero** network calls.

What it does NOT do: normalize (§36), interpret, extract claims (§37), embed
(§38) or score (§39). It parses a documented response into observations and
stops.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sros_contracts import AcquisitionErrorCode, ResourceContentOrigin

from ..compliance.authorization import AcquisitionAuthorizationContext
from ..compliance.resources import ResourceDescriptor
from .errors import AcquisitionFailedError, AcquisitionFailure
from .pacing import WORLD_BANK_PACING, RequestPacer
from .records import CollectedObservation, RawRecordDraft, build_draft
from .transport import HttpRequest, HttpResponse, Transport, host_of

__all__ = [
    "COLLECTOR_ID",
    "COLLECTOR_VERSION",
    "CollectionBounds",
    "CollectorResult",
    "WorldBankCollector",
    "WorldBankRequest",
]

# §50. Bumped when the parse, the identity or the provenance shape changes --
# not when a message is reworded. Recorded on every row, so a future change
# cannot make old records unauditable.
COLLECTOR_ID = "world-bank-indicators"
COLLECTOR_VERSION = "1.0.0"

_SOURCE_ID = "world-bank"
# The World Bank Indicators API is a 2-element array: metadata, then rows.
_EXPECTED_ENVELOPE_LENGTH = 2
_MAX_PAGE_SIZE = 1000


def _as_int(value: object) -> int | None:
    """A pagination number, or `None` when the source did not send one.

    Returning `None` rather than a default is the point: a default of 1 would
    silently truncate a paginated result, and a default of "keep going" would
    loop. Both are worse than reporting that the metadata is unusable.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return None


@dataclass(frozen=True)
class CollectionBounds:
    """Hard bounds on one acquisition job (§16).

    Every one of them is finite and has a default. A malformed API or a wrong
    query must not be able to collect indefinitely, and "the operator will pass
    a limit" is not a bound — the default is.
    """

    max_pages: int = 10
    max_records: int = 5_000
    deadline: datetime | None = None

    def __post_init__(self) -> None:
        if self.max_pages < 1 or self.max_records < 1:
            raise ValueError("bounds must be at least 1; a bound of zero collects nothing")
        if self.deadline is not None and self.deadline.tzinfo is None:
            raise ValueError("deadline must be timezone-aware")


@dataclass(frozen=True)
class WorldBankRequest:
    """Intent, not a URL (§9).

    There is no `path`, no `host` and no `query` field. A caller says which
    indicators, which countries and which years; everything else is the
    collector's to construct. Adding a free-text field here would reopen exactly
    the escape §4 closes.
    """

    indicators: tuple[str, ...]
    countries: tuple[str, ...] = ("all",)
    start_year: int | None = None
    end_year: int | None = None
    per_page: int = 100

    def __post_init__(self) -> None:
        if not self.indicators:
            raise ValueError("at least one indicator is required")
        for indicator in self.indicators:
            # World Bank indicator codes are dotted alphanumerics. Validated
            # because this string becomes a path segment, and a segment that
            # could contain a slash or a query character would be a way to
            # reshape the request.
            if not indicator or not all(c.isalnum() or c in "._-" for c in indicator):
                raise ValueError(
                    f"indicator {indicator!r} is not a valid code. Only letters, digits, "
                    "dot, underscore and hyphen: this becomes a path segment"
                )
        for country in self.countries:
            if not country or not all(c.isalnum() for c in country):
                raise ValueError(
                    f"country {country!r} is not a valid code. Only letters and digits"
                )
        if not 1 <= self.per_page <= _MAX_PAGE_SIZE:
            raise ValueError(f"per_page must be between 1 and {_MAX_PAGE_SIZE}")
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.start_year > self.end_year
        ):
            raise ValueError("start_year must not be after end_year")

    def resource_id(self, indicator: str) -> str:
        return f"indicator/{indicator}"

    @property
    def date_range(self) -> str | None:
        if self.start_year is None and self.end_year is None:
            return None
        start = self.start_year if self.start_year is not None else self.end_year
        end = self.end_year if self.end_year is not None else self.start_year
        return f"{start}:{end}"


@dataclass
class CollectorResult:
    """What one acquisition produced, including what it refused and why."""

    source_id: str
    collector_id: str
    collector_version: str
    drafts: list[RawRecordDraft] = field(default_factory=list)
    failures: list[AcquisitionFailure] = field(default_factory=list)
    requests_made: int = 0
    pages_read: int = 0
    refused_resources: list[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return not self.failures

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "collector": f"{self.collector_id}@{self.collector_version}",
            "records": len(self.drafts),
            "requests_made": self.requests_made,
            "pages_read": self.pages_read,
            "refused_resources": list(self.refused_resources),
            "failures": [f.to_json() for f in self.failures],
        }


class WorldBankCollector:
    """Collects World Bank indicator observations, and nothing else."""

    collector_id = COLLECTOR_ID
    collector_version = COLLECTOR_VERSION
    source_id = _SOURCE_ID

    def __init__(
        self,
        transport: Transport,
        pacer: RequestPacer | None = None,
        now: Callable[[], datetime] | None = None,
        max_attempts: int = 3,
    ) -> None:
        self.transport = transport
        self.pacer = pacer or RequestPacer(WORLD_BANK_PACING)
        self.now = now or (lambda: datetime.now(UTC))
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.max_attempts = max_attempts

    # ------------------------------------------------------------ the entry point

    def collect(
        self,
        context: AcquisitionAuthorizationContext,
        request: WorldBankRequest,
        *,
        workspace_id: str,
        correlation_id: str,
        research_session_id: str | None = None,
        bounds: CollectionBounds | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> CollectorResult:
        """The only way to collect. The context is the first argument and required.

        There is no variant of this method that builds its own authorization,
        and none that accepts a URL. That is §4 enforced by the signature rather
        than by a reviewer noticing.
        """
        if context.source_id != self.source_id:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        f"this collector serves {self.source_id!r} and was handed an "
                        f"authorization for {context.source_id!r}. One source's approval "
                        "never authorises another's collection"
                    ),
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                )
            )

        limits = bounds or CollectionBounds()
        allowed_hosts = self._allowed_hosts(context, correlation_id)
        base_url = self._base_url(context, correlation_id)
        result = CollectorResult(
            source_id=self.source_id,
            collector_id=self.collector_id,
            collector_version=self.collector_version,
        )

        for indicator in request.indicators:
            if self._stop(result, limits, cancelled):
                break
            self._collect_indicator(
                context=context,
                request=request,
                indicator=indicator,
                base_url=base_url,
                allowed_hosts=allowed_hosts,
                result=result,
                limits=limits,
                workspace_id=workspace_id,
                correlation_id=correlation_id,
                research_session_id=research_session_id,
                cancelled=cancelled,
            )
        return result

    # ------------------------------------------------------------- authorization

    def _allowed_hosts(
        self, context: AcquisitionAuthorizationContext, correlation_id: str
    ) -> frozenset[str]:
        """The hosts the registry authorised. Never a literal, never a fallback.

        §10 forbids a second hard-coded domain. The set is derived from the
        access profiles on the context, so revoking a profile in the registry
        revokes the host — and a source with no endpoint recorded authorises no
        host at all rather than defaulting to a guess.
        """
        hosts = frozenset(
            host for access in context.access if (host := host_of(access.endpoint_url or ""))
        )
        if not hosts:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        "the authorized access profiles record no endpoint, so no host is "
                        "authorized. An unrecorded endpoint is not a licence to guess one"
                    ),
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                )
            )
        return hosts

    def _base_url(self, context: AcquisitionAuthorizationContext, correlation_id: str) -> str:
        for access in context.access:
            if access.endpoint_url:
                return access.endpoint_url
        raise AcquisitionFailedError(  # pragma: no cover - _allowed_hosts refuses first
            AcquisitionFailure(
                code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                detail="no authorized endpoint",
                source_id=self.source_id,
                correlation_id=correlation_id,
            )
        )

    def _authorize(
        self,
        context: AcquisitionAuthorizationContext,
        request: WorldBankRequest,
        indicator: str,
        correlation_id: str,
    ) -> tuple[str, AcquisitionFailure | None]:
        """Authorise one indicator, before anything opens a socket.

        The descriptor is built from the **authorized dataset entry**, not from
        anything the caller said. A caller cannot declare a licence, a dataset
        family or a content origin, so it cannot declare its way past the gate.
        """
        resource_id = request.resource_id(indicator)
        dataset = context.authorized_dataset(resource_id)
        if dataset is None:
            return resource_id, AcquisitionFailure(
                code=AcquisitionErrorCode.RESOURCE_NOT_PERMITTED,
                detail=(
                    f"{resource_id} is not an authorized dataset. Its licence, family and "
                    "content origin were never recorded, so there is nothing for the "
                    "resource gate to clear it against"
                ),
                source_id=self.source_id,
                correlation_id=correlation_id,
                resource_id=resource_id,
            )

        descriptor = ResourceDescriptor(
            source_id=self.source_id,
            resource_id=resource_id,
            licence=dataset.licence,
            content_origin=ResourceContentOrigin(dataset.content_origin),
            dataset_family=dataset.dataset_family,
            geographies=tuple(c for c in request.countries if c != "all"),
        )
        authorization = context.authorize_resource(descriptor)
        if not authorization.allowed:
            return resource_id, AcquisitionFailure(
                code=AcquisitionErrorCode.RESOURCE_NOT_PERMITTED,
                detail="; ".join(authorization.denial_reasons),
                source_id=self.source_id,
                correlation_id=correlation_id,
                resource_id=resource_id,
                context={"rules_evaluated": list(authorization.rules_evaluated)},
            )
        return resource_id, None

    # ---------------------------------------------------------------- collection

    def _collect_indicator(
        self,
        *,
        context: AcquisitionAuthorizationContext,
        request: WorldBankRequest,
        indicator: str,
        base_url: str,
        allowed_hosts: frozenset[str],
        result: CollectorResult,
        limits: CollectionBounds,
        workspace_id: str,
        correlation_id: str,
        research_session_id: str | None,
        cancelled: Callable[[], bool] | None,
    ) -> None:
        resource_id, refusal = self._authorize(context, request, indicator, correlation_id)
        if refusal is not None:
            # ZERO network calls for a refused resource (§41). The return is
            # before any request is composed, not merely before one is sent.
            result.failures.append(refusal)
            result.refused_resources.append(resource_id)
            return

        for page in self._pages(limits):
            if self._stop(result, limits, cancelled):
                return
            http_request = self._compose(request, indicator, page)
            try:
                response = self._fetch(base_url, http_request, allowed_hosts, correlation_id)
            except AcquisitionFailedError as exc:
                result.failures.append(
                    AcquisitionFailure(
                        code=exc.failure.code,
                        detail=exc.failure.detail,
                        source_id=self.source_id,
                        correlation_id=correlation_id,
                        resource_id=resource_id,
                        context={**exc.failure.context, "page": page},
                    )
                )
                return
            result.requests_made = self.pacer.requests_made
            result.pages_read += 1

            try:
                meta, rows = self._parse(response, resource_id, correlation_id, page)
            except AcquisitionFailedError as exc:
                result.failures.append(exc.failure)
                return

            collected_at = self.now()
            for row in rows:
                if len(result.drafts) >= limits.max_records:
                    return
                observation = self._observation(row, resource_id, indicator, meta)
                if observation is None:
                    continue
                result.drafts.append(
                    build_draft(
                        observation,
                        context,
                        workspace_id=workspace_id,
                        research_session_id=research_session_id,
                        correlation_id=correlation_id,
                        collector_id=self.collector_id,
                        collector_version=self.collector_version,
                        collected_at=collected_at,
                        page=page,
                        request_path=http_request.path,
                    )
                )

            total_pages = _as_int(meta.get("pages"))
            reported_page = _as_int(meta.get("page"))
            if total_pages is None or reported_page is None:
                # §43. Pagination metadata that is not a number is not a hint to
                # be worked around: without it the collector cannot know when to
                # stop, and guessing "one page" would silently truncate.
                result.failures.append(
                    AcquisitionFailure(
                        code=AcquisitionErrorCode.INVALID_RESPONSE,
                        detail=(
                            "the pagination metadata is not numeric, so there is no way to "
                            "know when the result ends"
                        ),
                        source_id=self.source_id,
                        correlation_id=correlation_id,
                        resource_id=resource_id,
                        context={"page": page},
                    )
                )
                return
            if reported_page != page:
                # §43. A source that keeps returning page 1 while we ask for 2
                # would otherwise loop until a bound stopped it, and the bound
                # would hide a real upstream fault.
                result.failures.append(
                    AcquisitionFailure(
                        code=AcquisitionErrorCode.INVALID_RESPONSE,
                        detail=(
                            f"asked for page {page} and the response says page "
                            f"{reported_page}; pagination is not advancing"
                        ),
                        source_id=self.source_id,
                        correlation_id=correlation_id,
                        resource_id=resource_id,
                        context={"page": page, "reported_page": reported_page},
                    )
                )
                return
            if page >= total_pages:
                return

    def _pages(self, limits: CollectionBounds) -> Iterator[int]:
        """A finite generator. There is no `while True` in this collector."""
        return iter(range(1, limits.max_pages + 1))

    def _stop(
        self,
        result: CollectorResult,
        limits: CollectionBounds,
        cancelled: Callable[[], bool] | None,
    ) -> bool:
        """§16 and §31, checked before each expensive step.

        A running HTTP request is not interrupted — this codebase does not claim
        it can be. What is guaranteed is that no NEW request starts after a
        cancellation, a deadline or a record ceiling.
        """
        if len(result.drafts) >= limits.max_records:
            return True
        if limits.deadline is not None and self.now() >= limits.deadline:
            result.failures.append(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.CANCELLED,
                    detail="the acquisition deadline passed before the next request",
                    source_id=self.source_id,
                )
            )
            return True
        if cancelled is not None and cancelled():
            result.failures.append(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.CANCELLED,
                    detail="the job was cancelled before the next request",
                    source_id=self.source_id,
                )
            )
            return True
        return False

    def _compose(self, request: WorldBankRequest, indicator: str, page: int) -> HttpRequest:
        """Build the request from validated parameters. Never from a string."""
        countries = ";".join(request.countries)
        query = {"format": "json", "per_page": str(request.per_page), "page": str(page)}
        date_range = request.date_range
        if date_range:
            query["date"] = date_range
        return HttpRequest(path=f"country/{countries}/indicator/{indicator}", query=query)

    # ------------------------------------------------------------------- fetching

    def _fetch(
        self,
        base_url: str,
        request: HttpRequest,
        allowed_hosts: frozenset[str],
        correlation_id: str,
    ) -> HttpResponse:
        """One page, with bounded retries.

        The loop is bounded by `max_attempts` and by the retryability of the
        code — a deterministic 4xx is not retried at all, because the same
        request produces the same rejection and repeating it is how a rate limit
        becomes a ban (§14).
        """
        last: AcquisitionFailure | None = None
        for attempt in range(1, self.max_attempts + 1):
            self.pacer.acquire()
            try:
                response = self.transport.get(base_url, request, allowed_hosts)
            except AcquisitionFailedError as exc:
                last = exc.failure
                if not last.retryable or attempt == self.max_attempts:
                    raise AcquisitionFailedError(
                        AcquisitionFailure(
                            code=last.code,
                            detail=last.detail,
                            source_id=self.source_id,
                            correlation_id=correlation_id,
                            context={**last.context, "attempts": attempt},
                        )
                    ) from None
                continue

            failure = self._status_failure(response, correlation_id)
            if failure is None:
                return response
            last = failure
            if not failure.retryable or attempt == self.max_attempts:
                raise AcquisitionFailedError(
                    AcquisitionFailure(
                        code=failure.code,
                        detail=failure.detail,
                        source_id=self.source_id,
                        correlation_id=correlation_id,
                        context={**failure.context, "attempts": attempt},
                    )
                )
        raise AcquisitionFailedError(  # pragma: no cover - the loop always raises or returns
            last
            or AcquisitionFailure(
                code=AcquisitionErrorCode.TEMPORARY_UPSTREAM,
                detail="retries exhausted",
                source_id=self.source_id,
                correlation_id=correlation_id,
            )
        )

    def _status_failure(
        self, response: HttpResponse, correlation_id: str
    ) -> AcquisitionFailure | None:
        """Map an HTTP status to a normalised code. The body never enters it (§33)."""
        status = response.status_code
        if 200 <= status < 300:
            return None
        if status == 429:
            code = AcquisitionErrorCode.RATE_LIMITED
            detail = "the source signalled too many requests"
        elif status >= 500:
            code = AcquisitionErrorCode.TEMPORARY_UPSTREAM
            detail = "the source reported a server-side failure"
        else:
            code = AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR
            detail = "the source rejected the request deterministically"
        return AcquisitionFailure(
            code=code,
            detail=f"{detail} (HTTP {status})",
            source_id=self.source_id,
            correlation_id=correlation_id,
            context={"status": status},
        )

    # -------------------------------------------------------------------- parsing

    def _parse(
        self, response: HttpResponse, resource_id: str, correlation_id: str, page: int
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """Read the documented envelope, or refuse it.

        The World Bank Indicators API answers with a two-element array:
        metadata, then rows. Anything else is reported as a contract change
        rather than worked around — §14 is explicit that a schema error is not
        retried, because another attempt produces the same shape.
        """
        try:
            payload = json.loads(response.text)
        except ValueError:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.PARSING_FAILURE,
                    detail="the response body is not valid JSON",
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                    resource_id=resource_id,
                    context={"page": page},
                )
            ) from None

        # The documented error envelope: a single object carrying `message`.
        if (
            isinstance(payload, list)
            and len(payload) == 1
            and isinstance(payload[0], dict)
            and "message" in payload[0]
        ):
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR,
                    detail=(
                        "the source returned its documented error envelope, which "
                        "means the request parameters were rejected"
                    ),
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                    resource_id=resource_id,
                    context={"page": page},
                )
            )

        if not isinstance(payload, list) or len(payload) != _EXPECTED_ENVELOPE_LENGTH:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.INVALID_RESPONSE,
                    detail=(
                        "the response is not the documented two-element envelope (metadata, rows)"
                    ),
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                    resource_id=resource_id,
                    context={"page": page},
                )
            )

        meta, rows = payload
        if not isinstance(meta, dict):
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.INVALID_RESPONSE,
                    detail="the response metadata is not an object",
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                    resource_id=resource_id,
                    context={"page": page},
                )
            )
        # A page with no data is `null`, not an error: a country/indicator pair
        # with nothing to report is a real answer.
        if rows is None:
            return meta, []
        if not isinstance(rows, list):
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.INVALID_RESPONSE,
                    detail="the response rows are neither a list nor null",
                    source_id=self.source_id,
                    correlation_id=correlation_id,
                    resource_id=resource_id,
                    context={"page": page},
                )
            )
        return meta, [row for row in rows if isinstance(row, dict)]

    def _observation(
        self,
        row: dict[str, object],
        resource_id: str,
        indicator: str,
        meta: dict[str, object],
    ) -> CollectedObservation | None:
        """One row into one observation, or `None` when it cannot be identified.

        A row with no country or no period has no observation key, so it cannot
        be stored, deduplicated or revised. Skipped rather than stored under a
        made-up identity.

        A row with a NULL value is kept: "the World Bank has no figure for this
        country and year" is a fact about the source, and dropping it would make
        an absence indistinguishable from never having asked.
        """
        raw_country = row.get("country")
        country: dict[str, object] = raw_country if isinstance(raw_country, dict) else {}
        geography = str(row.get("countryiso3code") or country.get("id") or "").strip()
        period = str(row.get("date") or "").strip()
        if not geography or not period:
            return None

        raw_value = row.get("value")
        value: float | None
        if raw_value is None:
            value = None
        elif isinstance(raw_value, int | float):
            value = float(raw_value)
        else:
            try:
                value = float(str(raw_value))
            except ValueError:
                return None

        decimals = row.get("decimal")
        return CollectedObservation(
            source_id=self.source_id,
            resource_id=resource_id,
            indicator=indicator,
            geography=geography,
            geography_name=str(country.get("value") or "") or None,
            period=period,
            value=value,
            unit=str(row.get("unit") or "") or None,
            obs_status=str(row.get("obs_status") or "") or None,
            decimals=int(decimals)
            if isinstance(decimals, int | str) and str(decimals).isdigit()
            else None,
            source_last_updated=str(meta.get("lastupdated") or "") or None,
        )
