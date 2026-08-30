"""Collection: the first real acquisition path (Mission 1.5).

    errors.py        the normalised acquisition error taxonomy
    transport.py     the HTTP boundary. The ONLY file here that may reach a network
    pacing.py        our own request pacing. Not a claim about anyone's rate limit
    records.py       what an observation is, and what identifies it
    world_bank.py    the World Bank Indicators collector
    repositories.py  persistence: idempotent, revision-aware, tenant-scoped

**A collector cannot run without an authorization.** `WorldBankCollector.collect`
takes an `AcquisitionAuthorizationContext` as its first argument and there is no
overload that makes one. Every resource passes `context.authorize_resource(...)`
before a socket opens, and a refusal costs zero network calls.

**There is no URL in any public signature.** A request names indicators,
countries and years; the collector composes the path, and the transport refuses
any host outside the allowlist the access profile authorised.

One collector exists. `sros_acquisition.IMPLEMENTED_COLLECTORS` says which, and
eligibility, enablement and implementation remain three separate facts.
"""

from .errors import (
    RETRYABLE_CODES,
    AcquisitionFailedError,
    AcquisitionFailure,
    is_retryable,
)
from .pacing import WORLD_BANK_PACING, PacingPolicy, RequestPacer
from .records import (
    CollectedObservation,
    RawRecordDraft,
    build_draft,
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
from .transport import (
    HttpRequest,
    HttpResponse,
    HttpxTransport,
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
    "COLLECTOR_ID",
    "COLLECTOR_VERSION",
    "RETRYABLE_CODES",
    "WORLD_BANK_PACING",
    "AcquisitionFailedError",
    "AcquisitionFailure",
    "CollectedObservation",
    "CollectionBounds",
    "CollectorResult",
    "HttpRequest",
    "HttpResponse",
    "HttpxTransport",
    "PacingPolicy",
    "PersistenceOutcome",
    "PersistenceReport",
    "RawRecordDraft",
    "RequestPacer",
    "Transport",
    "TransportConfig",
    "WorldBankCollector",
    "WorldBankRequest",
    "build_draft",
    "canonical_fingerprint",
    "canonical_number",
    "collector_enabled",
    "count_records",
    "host_of",
    "is_retryable",
    "observation_key",
    "persist_drafts",
    "read_observation_history",
]
