"""Collection: the first real acquisition path (Mission 1.5).

    errors.py        the normalised acquisition error taxonomy
    transport.py     the HTTP boundary. The ONLY file here that may reach a network
    pacing.py        our own request pacing. Not a claim about anyone's rate limit
    records.py       what an observation is, and what identifies it
    world_bank.py       the World Bank Indicators collector
    gdelt_web_ngram.py  the GDELT WEB-NGRAM collector (Mission 1.9.3)
    ted_search_api.py   the TED Official Search API collector (Mission 1.15.7)
    repositories.py  persistence: idempotent, revision-aware, tenant-scoped

**A collector cannot run without an authorization.** `WorldBankCollector.collect`
takes an `AcquisitionAuthorizationContext` as its first argument and there is no
overload that makes one. Every resource passes `context.authorize_resource(...)`
before a socket opens, and a refusal costs zero network calls.

**There is no URL in any public signature.** A request names indicators,
countries and years; the collector composes the path, and the transport refuses
any host outside the allowlist the access profile authorised.

**Three collectors exist**, and what they share is deliberate rather than
generic. Both are gated the same way, both build records through
`build_raw_record`, and both classify HTTP statuses through `code_for_status`.
They differ where the sources differ: one reads a paginated JSON API through
`Transport.get`, the other streams a gzipped bulk file through
`StreamingTransport.download`. There is no "bulk source engine" between them,
because two sources are not yet a pattern.

`sros_acquisition.IMPLEMENTED_COLLECTORS` says which sources have one, and
eligible, resource-ready, implemented and enabled remain four separate facts.
"""

from .errors import (
    RETRYABLE_CODES,
    AcquisitionFailedError,
    AcquisitionFailure,
    code_for_status,
    is_retryable,
)
from .gdelt_web_ngram import (
    GRAM_KINDS,
    GdeltWebNgramCollector,
    NgramBounds,
    NgramFileReport,
    NgramObservation,
    WebNgramRequest,
    WebNgramResult,
    validate_bucket_label,
)
from .pacing import WEB_NGRAM_PACING, WORLD_BANK_PACING, PacingPolicy, RequestPacer
from .records import (
    CollectedObservation,
    RawRecordDraft,
    SourceObservation,
    build_draft,
    build_raw_record,
    canonical_fingerprint,
    canonical_number,
    observation_key,
)
from .repositories import (
    PersistenceOutcome,
    PersistenceReport,
    collector_enabled,
    count_records,
    persist_drafts,
    read_observation_history,
)
from .ted_search_api import (
    CONCEPTUAL_FIELDS,
    DEFAULT_CONCEPTUAL_FIELDS,
    EFORMS_PUBLICATION_START,
    NOTICE_TYPES,
    TED_COLLECTOR_ID,
    TED_COLLECTOR_VERSION,
    TED_PACING,
    TED_ROUTE_LABEL,
    TedNotice,
    TedSearchApiCollector,
    TedSearchBounds,
    TedSearchRequest,
    TedSearchResult,
)
from .ted_search_api import (
    RESOURCE_ID as TED_RESOURCE_ID,
)
from .transport import (
    DownloadLimits,
    HttpRequest,
    HttpResponse,
    HttpxTransport,
    JsonPostTransport,
    JsonRequest,
    StreamingTransport,
    Transport,
    TransportConfig,
    host_of,
)
from .world_bank import (
    COLLECTOR_ID,
    COLLECTOR_VERSION,
    CollectionBounds,
    CollectorResult,
    WorldBankCollector,
    WorldBankRequest,
)

__all__ = [
    "AcquisitionFailedError",
    "AcquisitionFailure",
    "build_draft",
    "build_raw_record",
    "canonical_fingerprint",
    "canonical_number",
    "code_for_status",
    "CollectedObservation",
    "CollectionBounds",
    "collector_enabled",
    "COLLECTOR_ID",
    "COLLECTOR_VERSION",
    "CollectorResult",
    "CONCEPTUAL_FIELDS",
    "count_records",
    "DEFAULT_CONCEPTUAL_FIELDS",
    "DownloadLimits",
    "EFORMS_PUBLICATION_START",
    "GdeltWebNgramCollector",
    "GRAM_KINDS",
    "host_of",
    "HttpRequest",
    "HttpResponse",
    "HttpxTransport",
    "is_retryable",
    "JsonPostTransport",
    "JsonRequest",
    "NgramBounds",
    "NgramFileReport",
    "NgramObservation",
    "NOTICE_TYPES",
    "observation_key",
    "PacingPolicy",
    "persist_drafts",
    "PersistenceOutcome",
    "PersistenceReport",
    "RawRecordDraft",
    "read_observation_history",
    "RequestPacer",
    "RETRYABLE_CODES",
    "SourceObservation",
    "StreamingTransport",
    "TED_COLLECTOR_ID",
    "TED_COLLECTOR_VERSION",
    "TED_PACING",
    "TED_RESOURCE_ID",
    "TED_ROUTE_LABEL",
    "TedNotice",
    "TedSearchApiCollector",
    "TedSearchBounds",
    "TedSearchRequest",
    "TedSearchResult",
    "Transport",
    "TransportConfig",
    "validate_bucket_label",
    "WEB_NGRAM_PACING",
    "WebNgramRequest",
    "WebNgramResult",
    "WORLD_BANK_PACING",
    "WorldBankCollector",
    "WorldBankRequest",
]
