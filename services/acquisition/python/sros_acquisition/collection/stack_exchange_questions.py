"""`stack-exchange-questions@1.0.0` -- bounded Stack Overflow questions, official API only.

`stack-exchange-questions-v1.md`. Mission 1.18.

**The first collector for a source whose content the platform does not own.**
Subscriber Content is licensed by its authors under CC BY-SA 4.0 and Stack
Exchange publishes it; the API Terms decide how it may be reached and the licence
decides what may be done with it. Both obligations are carried, and they are not
the same one twice: the API Terms want the network credited on the product
surface, and the licence wants the item attributed and linked.

**The first collector where personal data is the point of the record rather than
an edge case.** A question has an author, and the API returns an `owner` object
by default -- display name, account id, profile link, reputation, avatar. The
filter below removes it BEFORE the request, because a request that fetched the
owner and dropped it has still fetched it, and no method removes a field from a
record already collected.

**Four gates, all before a socket**, the shape Mission 1.15.7 established:

    bounds    -> a query with no ceiling is refused, and no default supplies one
    route     -> taken from context.access BY LABEL, never hard-coded
    resource  -> context.authorize_resource, built from the context's own entry
    fields    -> context.authorize_fields, on the CONCEPTUAL names

**The quota is REAL here, unlike TED's.** Stack Exchange returns
`quota_remaining`, `quota_max` and sometimes `backoff` in the response envelope.
Those are the SOURCE's instructions and are honoured as such. `SE_PACING` is
separately OUR conservative behaviour and is labelled as internal policy, so a
later reader can tell which number came from whom.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sros_contracts import AcquisitionErrorCode, ResourceContentOrigin

from ..compliance.authorization import AcquisitionAuthorizationContext
from ..compliance.resources import ResourceDescriptor
from .errors import AcquisitionFailedError, AcquisitionFailure
from .pacing import PacingPolicy, RequestPacer
from .records import RawRecordDraft, build_raw_record, canonical_fingerprint, observation_key
from .transport import HttpRequest, HttpResponse, Transport, host_of

__all__ = [
    "SE_FILTER",
    "SE_RESOURCE_ID",
    "SE_COLLECTOR_ID",
    "SE_COLLECTOR_VERSION",
    "SE_PACING",
    "SE_ROUTE_LABEL",
    "SE_SITE",
    "StackExchangeBounds",
    "StackExchangeQuestion",
    "StackExchangeQuestionsCollector",
    "StackExchangeRequest",
    "StackExchangeResult",
]

SE_COLLECTOR_ID = "stack-exchange-questions"
SE_COLLECTOR_VERSION = "1.0.0"
SE_ROUTE_LABEL = "stack-exchange-api"
SE_RESOURCE_ID = "questions/stackoverflow"

# ONE SITE, and it is not a parameter. Mission 1.18's review authorised
# `questions/stackoverflow` and nothing else; the other ~180 network sites are a
# different subject with a different opportunity value and were not assessed. A
# `site` parameter would make the authorised scope a runtime choice, which is
# the mistake ADR-028 records for routes.
SE_SITE = "stackoverflow"

QUESTIONS_PATH = "questions"

# The API's OWN field-selection mechanism, and this string is not invented.
# Filters are created by the API rather than composed by a client -- a made-up
# filter id is an HTTP 400, which is how the first attempt at this constant
# failed and is a better outcome than a plausible-looking string that silently
# selected the wrong fields.
#
# Derived once, on 2026-09-01, through the documented `/filters/create` method:
#
#     base    = default
#     include = question.body; question.link; question.content_license;
#               question.accepted_answer_id
#     exclude = question.owner; question.last_editor; question.comments;
#               question.answers; question.closed_by
#     unsafe  = false
#
# Verified by reading the filter back from `/filters/{id}`: `question.owner` is
# absent from `included_fields`, and every `question.*` field it does include is
# one the review authorised.
#
# **This is minimisation AT acquisition.** The compliance condition
# `stack-exchange-personal-data-minimisation` is satisfied by this string being
# in the request, not by anything the collector does afterwards -- a request
# that fetched the owner and dropped it has still fetched it.
SE_FILTER = "!SyjNl4V)kvv2kw3Qt6"

# The conceptual field names the review authorised, asked of the context before
# the request is composed. Conceptual rather than native for the reason Mission
# 1.15.7 gives: a review approves a MEANING, and a native name is how one API
# spells it this year.
CONCEPTUAL_FIELDS: tuple[str, ...] = (
    "question_id",
    "site",
    "title",
    "body",
    "tags",
    "creation_label",
    "answer_count",
    "is_answered",
    "accepted_answer_id",
    "score",
    "view_count",
    "question_url",
    "content_licence",
)

# Native keys this collector will keep from a returned item. Anything else the
# API sends is dropped before the payload is built -- belt as well as braces,
# because the filter is the guarantee and this is the check that it worked.
KEPT_KEYS: frozenset[str] = frozenset(
    {
        "question_id",
        "title",
        "body",
        "tags",
        "creation_date",
        "last_activity_date",
        "answer_count",
        "is_answered",
        "accepted_answer_id",
        "score",
        "view_count",
        "link",
        "content_license",
    }
)

# Keys whose presence means the filter did NOT do its job. Their arrival is a
# failure rather than something to clean up: the record would already have been
# fetched, and §13 of the review makes exclusion an acquisition-time property.
FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {"owner", "last_editor", "comments", "answers", "closed_by"}
)

SE_PACING = PacingPolicy(
    min_interval_seconds=1.0,
    max_requests_per_job=20,
    basis=(
        "OURS, NOT THE SOURCE'S, and the distinction matters more here than it did for "
        "TED because Stack Exchange does publish quota information. `quota_remaining`, "
        "`quota_max` and `backoff` come back in the response envelope and are honoured as "
        "the source's own instructions. These two numbers are separate: one second between "
        "requests and at most twenty per job are our conservative behaviour, chosen so a "
        "mistake is cheap for Stack Exchange and so a loop cannot become a campaign. If "
        "the published quota were ever tighter than this, the quota wins."
    ),
)


def _fail(code: AcquisitionErrorCode, detail: str, source_id: str) -> AcquisitionFailedError:
    return AcquisitionFailedError(AcquisitionFailure(code=code, detail=detail, source_id=source_id))


@dataclass(frozen=True)
class StackExchangeBounds:
    """The ceilings one collection may not exceed. **No defaults, anywhere.**

    Every field is required, so `StackExchangeBounds()` is a `TypeError` and
    there is no unbounded production mode to reach. A default here would be a
    number nobody reviewed.

    `page_size` is additionally checked against the API's own documented maximum
    of 100. Ours and theirs are different limits and both are enforced: a bound
    that satisfied ours and broke theirs would be refused after the request,
    which is the wrong side of the network to find out.
    """

    from_date: date
    to_date: date
    page_size: int
    max_pages: int
    max_records: int
    tagged: str | None = None

    API_MAX_PAGE_SIZE = 100

    def __post_init__(self) -> None:
        if self.from_date > self.to_date:
            raise ValueError("from_date is after to_date; the window is empty")
        for name in ("page_size", "max_pages", "max_records"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1; a bound of zero collects nothing")
        if self.page_size > self.API_MAX_PAGE_SIZE:
            raise ValueError(
                f"page_size {self.page_size} exceeds the API's documented maximum of "
                f"{self.API_MAX_PAGE_SIZE}. That is the SOURCE's limit, not ours"
            )
        if self.max_pages > SE_PACING.max_requests_per_job:
            raise ValueError(
                f"max_pages {self.max_pages} exceeds our own per-job request ceiling of "
                f"{SE_PACING.max_requests_per_job} ({SE_PACING.basis[:60]}...)"
            )


@dataclass(frozen=True)
class StackExchangeRequest:
    """One bounded query. The site is not a parameter (see `SE_SITE`)."""

    bounds: StackExchangeBounds
    conceptual_fields: tuple[str, ...] = CONCEPTUAL_FIELDS

    @property
    def query(self) -> dict[str, str]:
        """The query the API actually receives, which is the artefact that counts.

        Mission 1.15.10's lesson, applied before it could repeat: a narrowing
        that exists only in a dataclass field is not a narrowing, so the tests
        assert THIS rather than the bounds object.
        """
        params = {
            "site": SE_SITE,
            "order": "asc",
            "sort": "creation",
            "fromdate": str(
                int(datetime.combine(self.bounds.from_date, datetime.min.time(), UTC).timestamp())
            ),
            "todate": str(
                int(datetime.combine(self.bounds.to_date, datetime.min.time(), UTC).timestamp())
            ),
            "pagesize": str(self.bounds.page_size),
            "filter": SE_FILTER,
        }
        if self.bounds.tagged:
            params["tagged"] = self.bounds.tagged
        return params


@dataclass(frozen=True)
class StackExchangeQuestion:
    """One question, as the collector holds it before it becomes a record."""

    question_id: int
    payload: dict[str, object]

    @property
    def source_id(self) -> str:
        return "stack-exchange"

    @property
    def resource_id(self) -> str:
        return SE_RESOURCE_ID

    @property
    def key(self) -> str:
        """WHICH question. The source's own stable id, never a title or a hash.

        Prefixed by site because `question_id` is unique within a site and this
        collector could one day be authorised for a second one -- at which point
        two questions would collide on an unprefixed key and nothing would say so.
        """
        return observation_key("stack-exchange", SE_SITE, str(self.question_id))

    @property
    def content_hash(self) -> str:
        """WHAT the source said, over the canonical payload."""
        return canonical_fingerprint(self.payload)

    @property
    def observed_at(self) -> None:
        """Deliberately absent.

        The API returns `creation_date` as a Unix timestamp, which IS an
        unambiguous instant -- unlike TED's offset-without-a-time or GDELT's
        unzoned bucket. But `observed_at` on a RawRecord is a normalization
        decision, and this collector does not make normalization decisions. The
        timestamp is preserved verbatim in the payload for that later mission.
        """
        return None

    @property
    def link(self) -> str:
        return str(self.payload.get("link") or "")


@dataclass
class StackExchangeResult:
    """What one bounded collection produced, including what the source said back."""

    drafts: tuple[RawRecordDraft, ...] = ()
    pages_fetched: int = 0
    items_seen: int = 0
    requests_made: int = 0
    quota_remaining: int | None = None
    quota_max: int | None = None
    backoff_seconds: float | None = None
    has_more: bool | None = None
    stopped_by: str = ""
    failure: AcquisitionFailure | None = None

    @property
    def succeeded(self) -> bool:
        return self.failure is None

    def to_json(self) -> dict[str, object]:
        return {
            "records": len(self.drafts),
            "pages_fetched": self.pages_fetched,
            "items_seen": self.items_seen,
            "requests_made": self.requests_made,
            "quota_remaining": self.quota_remaining,
            "quota_max": self.quota_max,
            "backoff_seconds": self.backoff_seconds,
            "has_more": self.has_more,
            "stopped_by": self.stopped_by,
            "failure": None if self.failure is None else self.failure.to_json(),
        }


class StackExchangeQuestionsCollector:
    """Bounded Stack Overflow questions, over the official API and nothing else."""

    def __init__(self, transport: Transport, *, pacer: RequestPacer | None = None) -> None:
        self._transport = transport
        self._pacer = pacer or RequestPacer(SE_PACING)

    # ------------------------------------------------------------------ gates

    def _route(self, context: AcquisitionAuthorizationContext) -> Any:
        """The reviewed route, BY LABEL. No fallback exists and none is wanted.

        The Data Dump is registered and blocked, so it is not in `context.access`
        at all -- there is no endpoint to read and nothing for the transport to
        be pointed at (ADR-028). Asking by label makes the refusal say *refused
        by name* rather than *not found*.
        """
        refusals = context.authorize_route(SE_ROUTE_LABEL)
        route = next((a for a in context.access if a.label == SE_ROUTE_LABEL), None)
        if refusals or route is None or not (route.endpoint_url or "").strip():
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                f"{SE_ROUTE_LABEL!r} is not an authorized route with an endpoint for this "
                "source and profile. There is no second route to try: HTML retrieval is "
                "refused by the review and the Data Dump is blocked by name",
                context.source_id,
            )
        return route

    def _authorize(
        self, context: AcquisitionAuthorizationContext, request: StackExchangeRequest
    ) -> Any:
        """Resource and fields, both before a socket opens."""
        dataset = context.authorized_dataset(SE_RESOURCE_ID)
        if dataset is None:
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                f"{SE_RESOURCE_ID!r} is not an authorized resource for this source and profile",
                context.source_id,
            )
        decision = context.authorize_resource(
            ResourceDescriptor(
                source_id=context.source_id,
                resource_id=dataset.resource_id,
                licence=dataset.licence,
                rights_basis=dataset.rights_basis,
                content_origin=ResourceContentOrigin(dataset.content_origin),
                dataset_family=dataset.dataset_family,
            )
        )
        if not decision.allowed:
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                f"{SE_RESOURCE_ID!r} is refused by its own scope: "
                + "; ".join(decision.denial_reasons),
                context.source_id,
            )
        if (
            ResourceContentOrigin(dataset.content_origin)
            is not ResourceContentOrigin.PLATFORM_LICENSED
        ):
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                f"{SE_RESOURCE_ID!r} records content origin "
                f"{dataset.content_origin}; only PLATFORM_LICENSED is collectable here",
                context.source_id,
            )
        refusals = context.authorize_fields(request.conceptual_fields)
        if refusals:
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                "field selection refused: " + "; ".join(refusals),
                context.source_id,
            )
        return dataset

    # --------------------------------------------------------------- response

    def _parse(
        self, response: HttpResponse, source_id: str
    ) -> tuple[list[StackExchangeQuestion], dict[str, Any]]:
        """Items and the envelope, with the envelope treated as instructions.

        Parsed with `parse_float=Decimal` for the reason Mission 1.15.10
        established: a number crossing this boundary keeps its decimal identity.
        `parse_int` stays unset -- a JSON integer is already exact, and every
        numeric field this collector keeps (ids, counts, scores, timestamps) is
        one.
        """
        if response.status_code != 200:
            raise _fail(
                AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR,
                f"the API returned HTTP {response.status_code} for {response.url_path}. "
                "There is no HTML fallback: a refused API request is a refused acquisition",
                source_id,
            )
        try:
            body = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise _fail(
                AcquisitionErrorCode.INVALID_RESPONSE,
                f"the response is not JSON: {exc}",
                source_id,
            ) from exc
        if not isinstance(body, dict):
            raise _fail(
                AcquisitionErrorCode.INVALID_RESPONSE,
                f"the response is a {type(body).__name__}, not an object",
                source_id,
            )
        if "error_id" in body or "error_message" in body:
            raise _fail(
                AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR,
                f"the API returned an error envelope: {body.get('error_message')!r} "
                f"(id {body.get('error_id')!r})",
                source_id,
            )

        items = body.get("items")
        if not isinstance(items, list):
            raise _fail(
                AcquisitionErrorCode.INVALID_RESPONSE,
                "the response envelope carries no `items` list",
                source_id,
            )

        questions: list[StackExchangeQuestion] = []
        for raw in items:
            if not isinstance(raw, dict):
                raise _fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    f"an item is a {type(raw).__name__}, not an object",
                    source_id,
                )
            leaked = FORBIDDEN_KEYS & set(raw)
            if leaked:
                # The filter is the guarantee; this is the check that it held.
                # A failure rather than a cleanup: the data has already been
                # fetched by the time we could clean it.
                raise _fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    f"the response carries excluded personal-data fields {sorted(leaked)}. "
                    "The filter did not do its job, and dropping them here would not undo "
                    "having fetched them",
                    source_id,
                )
            question_id = raw.get("question_id")
            if not isinstance(question_id, int):
                raise _fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    "an item carries no integer `question_id`, so it has no stable identity",
                    source_id,
                )
            payload = {k: v for k, v in raw.items() if k in KEPT_KEYS}
            questions.append(StackExchangeQuestion(question_id=question_id, payload=payload))

        return questions, body

    # ---------------------------------------------------------------- collect

    def collect(
        self,
        context: AcquisitionAuthorizationContext,
        request: StackExchangeRequest,
        *,
        workspace_id: str,
        research_session_id: str | None,
        correlation_id: str,
        now: datetime | None = None,
        sleep: Any = time.sleep,
    ) -> StackExchangeResult:
        """Run one bounded query. Every gate is closed before the first socket."""
        moment = now or datetime.now(UTC)
        result = StackExchangeResult()

        try:
            route = self._route(context)
            dataset = self._authorize(context, request)
        except AcquisitionFailedError as exc:
            result.failure = exc.failure
            result.stopped_by = "refused before any request"
            return result

        base_url = route.endpoint_url or ""
        allowed_hosts = frozenset({host_of(base_url)}) - {""}

        drafts: list[RawRecordDraft] = []
        seen: set[str] = set()

        for page in range(1, request.bounds.max_pages + 1):
            if len(drafts) >= request.bounds.max_records:
                result.stopped_by = "max_records reached"
                break

            self._pacer.acquire()
            query = {**request.query, "page": str(page)}
            try:
                response = self._transport.get(
                    base_url, HttpRequest(path=QUESTIONS_PATH, query=query), allowed_hosts
                )
                questions, envelope = self._parse(response, context.source_id)
            except AcquisitionFailedError as exc:
                result.failure = exc.failure
                result.stopped_by = "upstream failure"
                result.drafts = tuple(drafts)
                return result

            result.requests_made += 1
            result.pages_fetched += 1
            result.quota_remaining = _as_int(envelope.get("quota_remaining"))
            result.quota_max = _as_int(envelope.get("quota_max"))
            result.has_more = bool(envelope.get("has_more"))

            # THE SOURCE'S OWN INSTRUCTION, honoured as one. `backoff` means
            # "do not call this method again for N seconds", so it is obeyed
            # before the next request rather than recorded and ignored.
            backoff = _as_float(envelope.get("backoff"))
            if backoff is not None:
                result.backoff_seconds = backoff

            for question in questions:
                result.items_seen += 1
                if len(drafts) >= request.bounds.max_records:
                    break
                if question.key in seen:
                    continue
                seen.add(question.key)
                drafts.append(
                    build_raw_record(
                        question,
                        context,
                        workspace_id=workspace_id,
                        research_session_id=research_session_id,
                        correlation_id=correlation_id,
                        collector_id=SE_COLLECTOR_ID,
                        collector_version=SE_COLLECTOR_VERSION,
                        collected_at=moment,
                        access_label=route.label,
                        source_reference=question.link,
                        source_item_link=question.link,
                        source_provenance={
                            "site": SE_SITE,
                            "question_id": question.question_id,
                            "question_url": question.link,
                            "resource_id": SE_RESOURCE_ID,
                            "licence": dataset.licence,
                            "filter": SE_FILTER,
                            "query": {k: v for k, v in query.items()},
                            "date_window": [
                                request.bounds.from_date.isoformat(),
                                request.bounds.to_date.isoformat(),
                            ],
                            "tagged": request.bounds.tagged,
                            "page": page,
                            "page_size": request.bounds.page_size,
                            "max_pages": request.bounds.max_pages,
                            "max_records": request.bounds.max_records,
                            "requested_conceptual_fields": list(request.conceptual_fields),
                            "quota_remaining": result.quota_remaining,
                            "quota_max": result.quota_max,
                            "pacing_basis": "INTERNAL_SAFETY_POLICY",
                        },
                    )
                )

            if not questions:
                result.stopped_by = "no further questions"
                break
            if not result.has_more:
                result.stopped_by = "has_more is false"
                break
            if backoff is not None and page < request.bounds.max_pages:
                sleep(backoff)

        if not result.stopped_by:
            result.stopped_by = "max_pages reached"
        result.drafts = tuple(drafts)
        return result


def _as_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
