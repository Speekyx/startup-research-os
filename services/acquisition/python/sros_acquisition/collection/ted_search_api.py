"""The TED Official Search API collector. Mission 1.15.7.

    POST https://api.ted.europa.eu/v3/notices/search

**One route, and no other.** `ted-open-data-sparql` is an authorised route at
source level and this collector does not implement it. There is no fallback: if
the Search API fails, the collection fails. A fallback between two authorised
routes sounds harmless and is not -- it turns a route the review reasoned about
into a route the runtime picked, and the next fallback added is the one to a
route the review refused.

**Four gates, in this order, all before a socket opens** (§13):

    bounds        -> a query with no ceiling is refused, and there is no default
    route         -> taken from `context.access` by LABEL, never hard-coded
    resource      -> `context.authorize_resource`, built from the context's own entry
    fields        -> `context.authorize_fields`, on the CONCEPTUAL names

The field gate runs before the request body is composed, because the Search API
has a `fields` parameter: an obligation about what is *retrieved* cannot be met
by discarding afterwards, and there is deliberately no method here that removes
a field from a collected notice.

**Two vocabularies, mapped explicitly.** Policy authorises conceptual fields
(`buyer_organisation_name`); TED returns source-native ones
(`organisation-name-buyer`). `CONCEPTUAL_FIELDS` is the whole mapping, it is
closed, and a native field that no conceptual field maps to cannot be requested
-- which is what stops "useful" fields from arriving without a review.

**The monetary semantics are the field names** (§26). TED publishes
`total-value`, `tender-value`, `estimated-value-lot` and
`framework-maximum-value-lot` as four different things, each with its own
currency companion. They are kept apart, under their own names, and no
`price_paid` exists anywhere in this module. No currency is converted.

**Pagination is bounded and has no exhaustion mode.** The API offers
`paginationMode: ITERATION`, which retrieves every notice for a query with no
limit. This collector sends `PAGE_NUMBER` and never sends an
`iterationNextToken`: scroll mode is the shape §37 forbids, and a collector that
could reach it would only need a flag flipped.

**The rate limit is UNKNOWN and stays that way.** Everything in `TED_PACING` and
`TedSearchBounds` is an `INTERNAL_SAFETY_POLICY` chosen by us for a source that
publishes no quota. None of it is a claim about what TED permits.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sros_contracts import AcquisitionErrorCode, ResourceContentOrigin

from ..compliance import AcquisitionAuthorizationContext
from ..compliance.resources import ResourceDescriptor
from .errors import AcquisitionFailedError, AcquisitionFailure, code_for_status
from .pacing import PacingPolicy, RequestPacer
from .records import RawRecordDraft, build_raw_record, canonical_fingerprint, observation_key
from .transport import HttpResponse, JsonPostTransport, JsonRequest, host_of

__all__ = [
    "CONCEPTUAL_FIELDS",
    "DEFAULT_CONCEPTUAL_FIELDS",
    "EFORMS_PUBLICATION_START",
    "MAX_FIELDS_PER_PAGE",
    "MAX_NOTICES_PER_PAGE",
    "MAX_RETRIEVABLE_NOTICES",
    "NOTICE_TYPES",
    "RESOURCE_ID",
    "SEARCH_PATH",
    "TED_COLLECTOR_ID",
    "TED_COLLECTOR_VERSION",
    "TED_PACING",
    "TED_ROUTE_LABEL",
    "TedNotice",
    "TedSearchApiCollector",
    "TedSearchBounds",
    "TedSearchRequest",
    "TedSearchResult",
]

TED_COLLECTOR_ID = "ted-search-api"
# 1.0.0: the first version. A version bump here is what makes a changed payload
# shape or a changed field selection reportable rather than absorbed.
TED_COLLECTOR_VERSION = "1.0.0"

# The route this collector binds to, by LABEL. It is resolved out of
# `context.access`, which after Mission 1.15.6 carries only reviewed routes --
# so a blocked label is not in the tuple, has no endpoint, and cannot be reached.
TED_ROUTE_LABEL = "ted-search-api"

# The one resource Mission 1.15.7 authorised. Named rather than parameterised:
# a collector that took a resource id from its caller would let the caller pick
# which review applies.
RESOURCE_ID = "notices/eforms-contract-and-award"

SEARCH_PATH = "v3/notices/search"

# The Publications Office's own coverage documentation gives 1 March 2023 as the
# start of eForms publication. A window that began earlier would be asking for
# notices this resource does not cover.
EFORMS_PUBLICATION_START = date(2023, 3, 1)

# The two eForms notice families this resource contains. Both values were
# validated against the API's own `checkQuerySyntax` mode, which rejects an
# unsupported value for `notice-type` by name.
NOTICE_TYPES = ("cn-standard", "can-standard")

# Documented by TED, quoted rather than chosen: the pagination mode of the
# public search API retrieves at most 15k notices for a query, at most 250 per
# page, and at most 10k fields per page where fields-per-page is the field count
# multiplied by the page size. These are the SOURCE's limits. Exceeding one is an
# error the API returns, so they are checked here to fail before the network
# rather than after it.
MAX_RETRIEVABLE_NOTICES = 15_000
MAX_NOTICES_PER_PAGE = 250
MAX_FIELDS_PER_PAGE = 10_000

# OURS, not TED's (§17). TED publishes no rate limit, the registry records it as
# UNKNOWN, and none of these numbers is a quota anybody granted. They are the
# conservative behaviour of a client that does not know what it is allowed.
TED_PACING = PacingPolicy(
    min_interval_seconds=1.0,
    max_requests_per_job=20,
    basis=(
        "TED publishes no rate limit and the registry records it as UNKNOWN, so there is "
        "no source quota to honour and none is invented. One second between requests and "
        "at most twenty requests per job are OUR conservative behaviour towards a source "
        "whose tolerance we do not know: slow enough that a mistake is cheap for TED, and "
        "bounded so a loop cannot become a campaign. If TED ever publishes a limit, that "
        "is a review fact and this constant is not where it goes."
    ),
)


# --------------------------------------------------------------- field mapping


@dataclass(frozen=True)
class ConceptualField:
    """One authorised conceptual field and the TED fields that represent it.

    `native` is the closed list this collector may request for that concept.
    `carried_by_name` marks a concept TED expresses through the IDENTITY of a
    field rather than through a value of its own -- there is exactly one, and it
    is the one that matters most.
    """

    conceptual: str
    native: tuple[str, ...]
    rationale: str
    carried_by_name: bool = False


# Every entry's `conceptual` name appears in `data_minimisation.allowed` for
# `ted-eu` under `local-private-research-v1`, and every `native` name appears
# both in the Search API's `fields` enum and in its response schema. The
# excluded contact block has no entry here and cannot acquire one by accident:
# a conceptual field the minimisation profile refuses is refused by the gate
# before this table is ever consulted.
CONCEPTUAL_FIELDS: tuple[ConceptualField, ...] = (
    ConceptualField(
        "notice_id",
        ("publication-number", "notice-identifier", "notice-version"),
        "The three facts that identify a notice as TED identifies it: the OJ S "
        "publication number, the notice's own identifier, and its version. All "
        "three, because identity is what §23 forbids reconstructing from page "
        "position, and a version is what distinguishes a corrected notice from "
        "the notice it corrects.",
    ),
    ConceptualField(
        "publication_date",
        ("publication-date",),
        "When TED published the notice. The field the bounded query filters on.",
    ),
    ConceptualField(
        "award_date",
        ("winner-decision-date",),
        "The date of the award decision. Distinct from the contract date and "
        "from the publication date, and never inferred from either.",
    ),
    ConceptualField(
        "contract_date",
        ("contract-conclusion-date",),
        "The date the contract was concluded. A different event from the award "
        "decision, kept separate for the same reason the monetary fields are.",
    ),
    ConceptualField(
        "buyer_organisation_name",
        ("organisation-name-buyer",),
        "The buying ORGANISATION. An organisation name is not a natural person, "
        "and the natural-person contact block is excluded by the review and "
        "absent from this table.",
    ),
    ConceptualField(
        "supplier_organisation_name",
        ("organisation-name-tenderer",),
        "The tendering ORGANISATION. Same boundary as the buyer.",
    ),
    ConceptualField(
        "cpv_code",
        ("classification-cpv",),
        "The CPV classification, as the source publishes it. No CPV is expanded, "
        "rolled up or translated here.",
    ),
    ConceptualField(
        "procurement_classification",
        ("contract-nature", "notice-type", "form-type"),
        "What KIND of procurement and what kind of notice. `notice-type` and "
        "`form-type` are requested rather than assumed from the query: a record "
        "that cannot say which family it belongs to would have to be classified "
        "by the filter that fetched it, which is provenance by inference.",
    ),
    ConceptualField(
        "monetary_amount",
        (
            "total-value",
            "tender-value",
            "estimated-value-lot",
            "framework-maximum-value-lot",
        ),
        "FOUR DIFFERENT THINGS, kept apart under their own names. A total value, "
        "a tender value, an estimated lot value and a framework maximum are not "
        "interchangeable, and flattening them into one number is precisely the "
        "`price_paid` failure Mission 1.15.3 forbids.",
    ),
    ConceptualField(
        "monetary_amount_type",
        (),
        "TED carries the semantic in the field NAME, so there is no separate "
        "value to request -- the type of `framework-maximum-value-lot` is that "
        "it is a framework maximum for a lot. It is required alongside "
        "`monetary_amount` rather than optional, and preserving the native names "
        "verbatim is how it is satisfied. An amount whose kind is unrecorded is "
        "what the review's own note calls a not-usable amount.",
        carried_by_name=True,
    ),
    ConceptualField(
        "currency",
        (
            "total-value-cur",
            "tender-value-cur",
            "estimated-value-cur-lot",
            "framework-maximum-value-cur-lot",
        ),
        "One currency companion per monetary field, matched by name. No "
        "conversion, no normalisation to EUR, and no currency inferred from a "
        "country.",
    ),
    ConceptualField(
        "country_code",
        ("organisation-country-buyer", "place-of-performance-country-lot"),
        "Where the buyer is and where the contract is performed -- two different "
        "questions, and a record carrying only one of them would invite the "
        "reader to treat it as both.",
    ),
    ConceptualField(
        "region_code",
        ("place-of-performance-subdiv-lot",),
        "The NUTS subdivision of the place of performance, as published. Not "
        "mapped to any internal geography here; that is normalization's job and "
        "normalization does not exist for TED.",
    ),
    ConceptualField(
        "award_status",
        ("winner-selection-status",),
        "Whether a winner was selected. Requested because a contract award "
        "notice with no award outcome is a different fact from one with it, and "
        "absence would otherwise be indistinguishable from not having asked.",
    ),
)

_BY_CONCEPT = {entry.conceptual: entry for entry in CONCEPTUAL_FIELDS}

# The V1 selection: every conceptual field the review authorises. It is a
# starting point a caller may narrow, never widen -- `authorize_fields` refuses
# anything outside the allowed set, whatever this constant says.
DEFAULT_CONCEPTUAL_FIELDS: tuple[str, ...] = tuple(e.conceptual for e in CONCEPTUAL_FIELDS)


def native_fields_for(conceptual: Sequence[str]) -> tuple[str, ...]:
    """The TED field names one conceptual selection maps to, in a stable order.

    Raises for a conceptual name this table does not carry. That is not the
    authorization check -- `authorize_fields` is -- but a second, narrower
    refusal: a concept the review allows and this collector cannot express must
    stop the request rather than quietly drop the field.
    """
    native: list[str] = []
    for name in conceptual:
        entry = _BY_CONCEPT.get(name)
        if entry is None:
            raise ValueError(
                f"{name!r} has no TED field mapping. A conceptual field this "
                "collector cannot express must not be silently omitted from the "
                "request: the record would be missing a fact somebody asked for"
            )
        native.extend(n for n in entry.native if n not in native)
    return tuple(native)


# ------------------------------------------------------------------ the bounds


@dataclass(frozen=True)
class TedSearchBounds:
    """The ceilings one collection may not exceed. **No defaults, anywhere.**

    §16. Every field is required, so `TedSearchBounds()` is a `TypeError` and
    there is no unbounded production mode to reach. A default here would be a
    number nobody reviewed, applied to a source whose rate limit is UNKNOWN, on
    the first mission that touches it.

    These are `INTERNAL_SAFETY_POLICY`. TED's own documented limits are checked
    separately in `__post_init__` and are the SOURCE's; a bound that satisfied
    ours and broke theirs would be refused by the API after the request, which
    is the wrong side of the network to find out.
    """

    date_start: date
    date_end: date
    max_pages: int
    max_records: int
    page_size: int

    def __post_init__(self) -> None:
        if self.date_start < EFORMS_PUBLICATION_START:
            raise ValueError(
                f"date_start {self.date_start.isoformat()} precedes the start of eForms "
                f"publication ({EFORMS_PUBLICATION_START.isoformat()}); this resource does "
                "not cover it, and asking anyway would be asking for a corpus nobody "
                "authorised"
            )
        if self.date_end < self.date_start:
            raise ValueError("date_end precedes date_start; that window contains nothing")
        for name in ("max_pages", "max_records", "page_size"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1; a ceiling of zero is not a bound")
        if self.page_size > MAX_NOTICES_PER_PAGE:
            raise ValueError(
                f"page_size {self.page_size} exceeds the {MAX_NOTICES_PER_PAGE} notices per "
                "page TED documents for the public search API"
            )
        if self.max_records > MAX_RETRIEVABLE_NOTICES:
            raise ValueError(
                f"max_records {self.max_records} exceeds the {MAX_RETRIEVABLE_NOTICES} "
                "retrievable notices TED documents for pagination mode. Retrieving more "
                "would need ITERATION mode, which this collector deliberately cannot reach"
            )

    def refusals_for_fields(self, field_count: int) -> tuple[str, ...]:
        """Why this page size cannot carry this many fields, or nothing.

        TED's fields-per-page limit is `page_size * field_count`, so the two
        bounds interact and neither can be checked alone.
        """
        product = self.page_size * field_count
        if product > MAX_FIELDS_PER_PAGE:
            return (
                f"page_size {self.page_size} x {field_count} fields = {product}, over the "
                f"{MAX_FIELDS_PER_PAGE} fields per page TED documents. Reduce the page size "
                "or the field selection; the field selection is the reviewed one",
            )
        return ()


@dataclass(frozen=True)
class TedSearchRequest:
    """One bounded research query. Bounds are required, not defaulted."""

    bounds: TedSearchBounds
    conceptual_fields: tuple[str, ...] = DEFAULT_CONCEPTUAL_FIELDS
    notice_types: tuple[str, ...] = NOTICE_TYPES

    def __post_init__(self) -> None:
        if not self.conceptual_fields:
            raise ValueError(
                "a request naming no field is not a request; the source refuses it too"
            )
        if not self.notice_types:
            raise ValueError("a request naming no notice type would ask for every family")
        unknown = tuple(t for t in self.notice_types if t not in NOTICE_TYPES)
        if unknown:
            raise ValueError(
                f"notice types {list(unknown)} are outside this resource. It contains "
                f"{list(NOTICE_TYPES)} and nothing else, and widening it is a review act"
            )

    @property
    def expert_query(self) -> str:
        """The expert query, composed here and never supplied by a caller.

        A caller-supplied query string would be a caller-supplied scope: the
        date window, the notice families and the ordering are the reviewed shape
        of this resource, and a raw query parameter would route around all three.
        """
        types = " ".join(self.notice_types)
        return (
            f"(notice-type IN ({types}))"
            f" AND (publication-date>={_ted_date(self.bounds.date_start)})"
            f" AND (publication-date<={_ted_date(self.bounds.date_end)})"
            " SORT BY publication-date"
        )


def _ted_date(value: date) -> str:
    """TED's expert-search date literal: `YYYYMMDD`, validated against the API."""
    return value.strftime("%Y%m%d")


# ------------------------------------------------------------------ the notice


@dataclass(frozen=True)
class TedNotice:
    """One notice, as TED returned it. A `SourceObservation`.

    **The payload is the source's own structure, unaltered.** No field is
    renamed, no monetary amount is flattened, no currency is converted, no
    language is chosen and no lot is collapsed. Everything this class does is
    identify the notice and hand the payload on.
    """

    resource_id: str
    publication_number: str
    notice_identifier: str | None
    notice_version: int | None
    fields: Mapping[str, object]
    retrieved_at: datetime
    source_id: str = "ted-eu"

    @property
    def key(self) -> str:
        """The source-native identity. Never the page, never the position.

        `publication-number` is TED's own OJ S identifier for the notice and is
        required. The identifier and the version join it where the source
        published them, because a corrected notice and the notice it corrects
        are two source-distinct objects and a key that ignored the version would
        silently make the second overwrite the first.
        """
        parts = [self.source_id, "notice", self.publication_number]
        if self.notice_identifier:
            parts.append(self.notice_identifier)
        if self.notice_version is not None:
            parts.append(f"v{self.notice_version}")
        return observation_key(*parts)

    @property
    def payload(self) -> dict[str, object]:
        return dict(self.fields)

    @property
    def content_hash(self) -> str:
        return canonical_fingerprint(self.payload)

    @property
    def observed_at(self) -> datetime | None:
        """Deliberately `None`. Mission 1.15.7.

        `publication-date` is a real, source-published date and it is IN the
        payload. It is not promoted to `observed_at` here, because
        `observed_at` is the canonical instant a later stage compares across
        sources, and the temporal semantics of a TED publication date have not
        been established -- no timezone, no certification, and no mission has
        asked. H-29's discipline, applied to a second source before anybody
        needs it: a plausible instant is worse than a declared absence.
        """
        return None


@dataclass
class TedSearchResult:
    """What one bounded collection produced, and what stopped it."""

    drafts: tuple[RawRecordDraft, ...] = ()
    pages_fetched: int = 0
    notices_seen: int = 0
    total_notice_count: int | None = None
    stopped_by: str = "window exhausted"
    failure: AcquisitionFailure | None = None

    @property
    def succeeded(self) -> bool:
        return self.failure is None

    def to_json(self) -> dict[str, object]:
        return {
            "drafts": len(self.drafts),
            "pages_fetched": self.pages_fetched,
            "notices_seen": self.notices_seen,
            "total_notice_count": self.total_notice_count,
            "stopped_by": self.stopped_by,
            "failure": self.failure.to_json() if self.failure else None,
        }


# --------------------------------------------------------------- the collector


class TedSearchApiCollector:
    """Bounded acquisition from the TED Search API, and nothing else.

    There is no constructor that makes an authorization, no parameter that takes
    a URL, and no method that takes a raw expert query. `collect` requires an
    `AcquisitionAuthorizationContext` positionally.
    """

    def __init__(
        self,
        transport: JsonPostTransport,
        *,
        pacer: RequestPacer | None = None,
    ) -> None:
        self._transport = transport
        self._pacer = pacer or RequestPacer(TED_PACING)

    def collect(
        self,
        context: AcquisitionAuthorizationContext,
        request: TedSearchRequest,
        *,
        workspace_id: str,
        research_session_id: str | None,
        correlation_id: str,
        now: datetime | None = None,
    ) -> TedSearchResult:
        """Run one bounded query. Every gate is closed before the first socket."""
        moment = now or datetime.now(UTC)
        result = TedSearchResult()

        try:
            route = self._route(context)
            native = self._authorize(context, request)
        except AcquisitionFailedError as exc:
            result.failure = exc.failure
            result.stopped_by = "refused before any request"
            return result

        allowed_hosts = frozenset({host_of(route.endpoint_url or "")}) - {""}
        base_url = route.endpoint_url or ""

        drafts: list[RawRecordDraft] = []
        seen: set[str] = set()
        for page in self._pages(request.bounds):
            self._pacer.acquire()
            try:
                response = self._transport.post_json(
                    base_url,
                    JsonRequest(path=SEARCH_PATH, body=self._body(request, native, page)),
                    allowed_hosts,
                )
                notices, total = self._parse(response, moment)
            except AcquisitionFailedError as exc:
                result.failure = exc.failure
                result.stopped_by = "upstream failure"
                result.drafts = tuple(drafts)
                return result

            result.pages_fetched += 1
            result.total_notice_count = total
            if not notices:
                result.stopped_by = "no further notices"
                break

            for notice in notices:
                result.notices_seen += 1
                if notice.key in seen:
                    # Pagination mode is documented as stateless and inconsistent
                    # across pages when an OJ S is released mid-collection, so a
                    # repeat is expected rather than exceptional. Skipped inside
                    # one run and counted; persistence has its own idempotency.
                    continue
                seen.add(notice.key)
                drafts.append(
                    build_raw_record(
                        notice,
                        context,
                        workspace_id=workspace_id,
                        research_session_id=research_session_id,
                        correlation_id=correlation_id,
                        collector_id=TED_COLLECTOR_ID,
                        collector_version=TED_COLLECTOR_VERSION,
                        collected_at=moment,
                        access_label=route.label,
                        source_reference=(
                            f"TED notice {notice.publication_number} via {route.label}"
                        ),
                        source_provenance={
                            "publication_number": notice.publication_number,
                            "notice_identifier": notice.notice_identifier,
                            "notice_version": notice.notice_version,
                            "expert_query": request.expert_query,
                            "requested_conceptual_fields": list(request.conceptual_fields),
                            "requested_native_fields": list(native),
                            "notice_types": list(request.notice_types),
                            "date_window": [
                                request.bounds.date_start.isoformat(),
                                request.bounds.date_end.isoformat(),
                            ],
                            "page": result.pages_fetched,
                            "pagination_mode": "PAGE_NUMBER",
                            "acquisition_bounds_origin": "INTERNAL_SAFETY_POLICY",
                            "rate_limit": "UNKNOWN",
                        },
                    )
                )
                if len(drafts) >= request.bounds.max_records:
                    result.stopped_by = f"max_records ({request.bounds.max_records}) reached"
                    result.drafts = tuple(drafts)
                    return result

            if len(notices) < request.bounds.page_size:
                result.stopped_by = "last page of the window"
                break
        else:
            result.stopped_by = f"max_pages ({request.bounds.max_pages}) reached"

        result.drafts = tuple(drafts)
        return result

    # ------------------------------------------------------------- the gates

    def _route(self, context: AcquisitionAuthorizationContext) -> Any:
        """The access profile for `ted-search-api`, by label, or a refusal.

        By label and never by position. `context.access[0]` would work today and
        would silently authorise whichever route the registry happened to list
        first -- the hazard `GdeltWebNgramCollector._route` records and the one
        Mission 1.15.6 found already live for TED.
        """
        refusals = context.authorize_route(TED_ROUTE_LABEL)
        route = next((a for a in context.access if a.label == TED_ROUTE_LABEL), None)
        if refusals or route is None:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        f"route {TED_ROUTE_LABEL!r} is not available in this authorization: "
                        + ("; ".join(refusals) if refusals else "it is not in context.access")
                        + ". This collector implements one route and does not fall back"
                    ),
                    source_id=context.source_id,
                )
            )
        if not (route.endpoint_url or "").strip():
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        f"route {TED_ROUTE_LABEL!r} records no endpoint, so there is no host "
                        "to allowlist and nothing to reach"
                    ),
                    source_id=context.source_id,
                )
            )
        return route

    def _authorize(
        self, context: AcquisitionAuthorizationContext, request: TedSearchRequest
    ) -> tuple[str, ...]:
        """The resource gate, then the field gate. Both before any request."""
        dataset = context.authorized_dataset(RESOURCE_ID)
        if dataset is None:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        f"{RESOURCE_ID!r} is not an authorized resource for "
                        f"{context.source_id} under {context.use_profile_id!r}. A collector "
                        "builds its descriptor from the context's own entry and never from "
                        "what it would like to be true"
                    ),
                    source_id=context.source_id,
                )
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
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail="resource refused: " + "; ".join(decision.denial_reasons),
                    source_id=context.source_id,
                )
            )

        refusals = context.authorize_fields(request.conceptual_fields)
        if refusals:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail="field selection refused: " + "; ".join(refusals),
                    source_id=context.source_id,
                )
            )
        if "monetary_amount" in request.conceptual_fields and (
            "monetary_amount_type" not in request.conceptual_fields
        ):
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        "monetary_amount was requested without monetary_amount_type. TED "
                        "carries the semantic in the field name, and an amount whose kind "
                        "is unrecorded is the flattening into price_paid the review forbids"
                    ),
                    source_id=context.source_id,
                )
            )

        try:
            native = native_fields_for(request.conceptual_fields)
        except ValueError as exc:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=str(exc),
                    source_id=context.source_id,
                )
            ) from None
        if not native:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail=(
                        "the selection maps to no TED field, so the request would name none "
                        "and the source would choose what to return"
                    ),
                    source_id=context.source_id,
                )
            )
        bound_refusals = request.bounds.refusals_for_fields(len(native))
        if bound_refusals:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                    detail="; ".join(bound_refusals),
                    source_id=context.source_id,
                )
            )
        return native

    # ------------------------------------------------------------- the request

    def _pages(self, bounds: TedSearchBounds) -> Iterator[int]:
        """Page numbers, bounded. There is no exhaustion iterator here."""
        return iter(range(1, bounds.max_pages + 1))

    def _body(
        self, request: TedSearchRequest, native: Sequence[str], page: int
    ) -> dict[str, object]:
        """The request body, composed field by field.

        `paginationMode` is stated rather than left to its default, and
        `iterationNextToken` is never present: scroll mode is one key away and
        naming the mode we are in is what keeps that visible in a diff.
        """
        return {
            "query": request.expert_query,
            "fields": list(native),
            "page": page,
            "limit": request.bounds.page_size,
            "scope": "ALL",
            "paginationMode": "PAGE_NUMBER",
            "checkQuerySyntax": False,
        }

    # ------------------------------------------------------------- the response

    def _parse(
        self, response: HttpResponse, moment: datetime
    ) -> tuple[tuple[TedNotice, ...], int | None]:
        """Notices and the total, or a failure. Never a partial success."""
        status = code_for_status(response.status_code)
        if status is not None:
            # The BODY is never copied into the detail (§33, `code_for_status`).
            # A status number is a safe diagnostic; a third party's response text
            # is arbitrary content, and a 400 from the expert-query parser echoes
            # the query back. The mapped message is ours.
            code, message = status
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=code,
                    detail=f"{message} (HTTP {response.status_code})",
                    source_id="ted-eu",
                    context={"status": response.status_code, "path": response.url_path},
                )
            )
        try:
            body = json.loads(response.text)
        except ValueError:
            raise AcquisitionFailedError(
                AcquisitionFailure(
                    code=AcquisitionErrorCode.INVALID_RESPONSE,
                    detail="the response body is not JSON",
                    source_id="ted-eu",
                    context={"path": response.url_path},
                )
            ) from None
        if not isinstance(body, dict):
            raise self._drift("the response is not a JSON object", response)
        if "notices" not in body:
            # §32: a required structural field disappearing is a contract change
            # and must be visible. Reading a missing `notices` as an empty page
            # would turn it into "no results", which is a sentence about the
            # world rather than about the API.
            raise self._drift("the response carries no 'notices' key", response)
        raw = body.get("notices")
        if raw is None:
            raw = []
        if not isinstance(raw, list):
            raise self._drift("'notices' is not a list", response)

        total = body.get("totalNoticeCount")
        if total is not None and not isinstance(total, int):
            raise self._drift("'totalNoticeCount' is present and not an integer", response)

        notices = tuple(self._notice(item, response, moment) for item in raw)
        return notices, total

    def _notice(self, item: object, response: HttpResponse, moment: datetime) -> TedNotice:
        if not isinstance(item, dict):
            raise self._drift("a notice entry is not an object", response)
        publication_number = _one(item.get("publication-number"))
        if not publication_number:
            # §31. A notice with no source-native identity cannot be persisted:
            # the record id derives from the observation key, so an unidentified
            # notice would either collide with another or invent an identity.
            raise self._drift(
                "a notice carries no 'publication-number', so it has no source identity",
                response,
            )
        version = _one(item.get("notice-version"))
        return TedNotice(
            resource_id=RESOURCE_ID,
            publication_number=str(publication_number),
            notice_identifier=(
                str(_one(item.get("notice-identifier")))
                if _one(item.get("notice-identifier"))
                else None
            ),
            notice_version=int(version)
            if isinstance(version, int | str) and _digit(version)
            else None,
            # Verbatim. Every array stays an array, so a notice with several
            # lots keeps all of them and nothing is collapsed on the way in.
            fields=dict(item),
            retrieved_at=moment,
        )

    def _drift(self, what: str, response: HttpResponse) -> AcquisitionFailedError:
        """A response-contract change, reported rather than absorbed."""
        return AcquisitionFailedError(
            AcquisitionFailure(
                code=AcquisitionErrorCode.INVALID_RESPONSE,
                detail=(
                    f"{what}. This is a response-contract change, not an empty result: "
                    "turning it into nulls would hide a breaking source change behind "
                    "records that look complete"
                ),
                source_id="ted-eu",
                context={"path": response.url_path},
            )
        )


def _one(value: object) -> object:
    """The single value of a field TED may publish as a scalar or an array.

    The response schema declares some fields scalar and some as arrays of one,
    and a collector that assumed either shape would break on the other. This
    unwraps a one-element list and leaves everything else alone -- a longer list
    is a real multiplicity (several lots, several languages) and is never
    reduced here.
    """
    if isinstance(value, list):
        return value[0] if len(value) == 1 else None
    return value


def _digit(value: object) -> bool:
    return isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit())
