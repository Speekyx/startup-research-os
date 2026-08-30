"""Normalization: RawRecord to canonical observation (Mission 1.6).

    errors.py        why a record could not be produced, distinct from why one
                     is degraded
    geography.py     classifying a source geography code, from reviewed data
    model.py         the canonical model, its identities and its fingerprint
    normalizers.py   the adapter boundary, and how one is selected
    world_bank.py    the World Bank Indicators normalizer
    repositories.py  reading raw records, persisting normalized ones
    job.py           one bounded, tenant-scoped, idempotent normalization pass

**This layer renames and reshapes. It does not decide.** Normalization answers
*what does this source observation structurally represent*, and stops. Signal
extraction interprets meaning, claim extraction makes assertions and scoring
evaluates them -- three later stages, none of them here.

**No network, no model, no NLP.** Everything a normalizer needs is already
persisted, and `validate_normalization.py` asserts mechanically that this
package imports no HTTP client, no LLM gateway, no embedding library and no
transport module. A rule that depends on a reviewer noticing is a rule with a
half-life.

**Selection fails closed.** `(source_id, collector_id)` selects an adapter, and
an unregistered pair is refused rather than handed to whichever adapter happens
to exist. `sros_acquisition.IMPLEMENTED_NORMALIZERS` says which sources can be
normalized -- one, and eligibility, enablement, collection and normalization
remain four separate facts.
"""

from .errors import (
    RETRYABLE_NORMALIZATION_CODES,
    NormalizationFailedError,
    NormalizationFailure,
    is_retryable,
)
from .geography import (
    DEFAULT_GEOGRAPHY_MAP_PATH,
    GeographyEntry,
    GeographyMap,
    find_geography_map,
    load_geography_map,
)
from .job import (
    MAX_NORMALIZATION_BATCH,
    NormalizationJobPayload,
    NormalizationJobResult,
    run_normalization_job,
)
from .model import (
    NORMALIZATION_SCHEMA_ID,
    NORMALIZATION_SCHEMA_VERSION,
    RECORD_KIND_REGISTRY,
    RECORD_KINDS,
    CanonicalGeography,
    CanonicalLanguage,
    CanonicalObservation,
    CanonicalPeriod,
    CanonicalValue,
    LexicalFrequencyObservation,
    NormalizationCounts,
    NormalizedRecordDraft,
    NumericObservation,
    QualityAssessment,
    QualityReason,
    RawRecordView,
    RecordKind,
    build_normalized,
    canonical_decimal_text,
    canonical_fingerprint,
    canonical_json,
    decimal_from,
    year_period,
)
from .normalizers import (
    NORMALIZER_REGISTRY,
    NormalizationContext,
    Normalizer,
    NormalizerResult,
    NormalizerSpec,
    register_normalizer,
    select_normalizer,
    supported_sources,
)
from .repositories import (
    NormalizationOutcome,
    PersistenceReport,
    count_normalized,
    persist_normalized,
    read_normalized_history,
    read_raw_records,
)
from .world_bank import (
    WORLD_BANK_NORMALIZER_ID,
    WORLD_BANK_NORMALIZER_VERSION,
    WorldBankNumericNormalizer,
)

# Registration happens HERE, at import of the package, rather than as a side
# effect of importing `world_bank` -- so the set of adapters is one readable
# list rather than something assembled by whichever modules a caller happened to
# touch. The same reason `IMPLEMENTED_COLLECTORS` is a literal.
WORLD_BANK_NORMALIZER_SPEC = NormalizerSpec(
    normalizer_id=WORLD_BANK_NORMALIZER_ID,
    normalizer_version=WORLD_BANK_NORMALIZER_VERSION,
    source_id="world-bank",
    collector_id="world-bank-indicators",
    supported_collector_versions=frozenset({"1.0.0", "1.1.0"}),
    schema_id=NORMALIZATION_SCHEMA_ID,
    schema_version=NORMALIZATION_SCHEMA_VERSION,
    build=lambda context: WorldBankNumericNormalizer(context.geography, context.retention),
)

if WORLD_BANK_NORMALIZER_SPEC.key not in NORMALIZER_REGISTRY:
    register_normalizer(WORLD_BANK_NORMALIZER_SPEC)

__all__ = [
    "DEFAULT_GEOGRAPHY_MAP_PATH",
    "MAX_NORMALIZATION_BATCH",
    "NORMALIZATION_SCHEMA_ID",
    "NORMALIZATION_SCHEMA_VERSION",
    "NORMALIZER_REGISTRY",
    "RECORD_KINDS",
    "RECORD_KIND_REGISTRY",
    "RETRYABLE_NORMALIZATION_CODES",
    "WORLD_BANK_NORMALIZER_ID",
    "WORLD_BANK_NORMALIZER_SPEC",
    "WORLD_BANK_NORMALIZER_VERSION",
    "CanonicalGeography",
    "CanonicalLanguage",
    "CanonicalObservation",
    "CanonicalPeriod",
    "CanonicalValue",
    "GeographyEntry",
    "GeographyMap",
    "NormalizationContext",
    "NormalizationCounts",
    "NormalizationFailedError",
    "NormalizationFailure",
    "NormalizationJobPayload",
    "NormalizationJobResult",
    "NormalizationOutcome",
    "Normalizer",
    "NormalizerResult",
    "NormalizerSpec",
    "NormalizedRecordDraft",
    "LexicalFrequencyObservation",
    "NumericObservation",
    "PersistenceReport",
    "QualityAssessment",
    "QualityReason",
    "RawRecordView",
    "RecordKind",
    "WorldBankNumericNormalizer",
    "build_normalized",
    "canonical_decimal_text",
    "canonical_fingerprint",
    "canonical_json",
    "count_normalized",
    "decimal_from",
    "find_geography_map",
    "is_retryable",
    "load_geography_map",
    "persist_normalized",
    "read_normalized_history",
    "read_raw_records",
    "register_normalizer",
    "run_normalization_job",
    "select_normalizer",
    "supported_sources",
    "year_period",
]
