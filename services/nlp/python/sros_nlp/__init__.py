"""Deterministic signal extraction.

`docs/data/signal-derivation-runtime-v1.md`,
`docs/data/numeric-period-change-extractor-v1.md`,
`docs/data/lexical-frequency-contrast-extractor-v1.md`.

Two extractors, both arithmetic over canonical observations. **No model, no
embedding, no clustering, no classifier and no network** -- the boundary
`validate_signals.py` asserts by parsing every import in this package.

`packages/signal-model` says what a Signal IS; this derives one. The dependency
runs one way and the model contains no extractor.
"""

from __future__ import annotations

from .extractors import (
    EXTRACTOR_REGISTRY,
    IMPLEMENTED_EXTRACTORS,
    CandidateGroup,
    DerivationRequest,
    GroupOutcome,
    GroupRefusal,
    LexicalFrequencyContrastExtractor,
    NumericPeriodChangeExtractor,
    SignalExtractor,
    select_extractor,
)
from .job import (
    MAX_DERIVATION_GROUPS,
    MAX_DERIVATION_RECORDS,
    SIGNAL_RETENTION_DAYS,
    SignalDerivationJobPayload,
    SignalDerivationJobResult,
    run_signal_derivation_job,
)
from .observations import NormalizedObservation, decimal_from
from .repositories import (
    DerivationRunRecord,
    SignalOutcome,
    SignalPersistenceReport,
    count_signals,
    persist_run,
    persist_signals,
    read_normalized_observations,
)

__all__ = [
    "EXTRACTOR_REGISTRY",
    "IMPLEMENTED_EXTRACTORS",
    "MAX_DERIVATION_GROUPS",
    "MAX_DERIVATION_RECORDS",
    "SIGNAL_RETENTION_DAYS",
    "CandidateGroup",
    "DerivationRequest",
    "DerivationRunRecord",
    "GroupOutcome",
    "GroupRefusal",
    "LexicalFrequencyContrastExtractor",
    "NormalizedObservation",
    "NumericPeriodChangeExtractor",
    "SignalDerivationJobPayload",
    "SignalDerivationJobResult",
    "SignalExtractor",
    "SignalOutcome",
    "SignalPersistenceReport",
    "count_signals",
    "decimal_from",
    "persist_run",
    "persist_signals",
    "read_normalized_observations",
    "run_signal_derivation_job",
    "select_extractor",
]
