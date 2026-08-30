"""The Signal contract for Startup Research OS.

`docs/data/signal-contract-v1.md`, `docs/data/signal-taxonomy-v1.md`,
`docs/data/signal-temporal-semantics-v1.md`, ADR-020.

**This package contains no extractor.** It defines what a Signal IS -- its
identity, its lineage, its scope, its temporal basis, the canonical facts a
derivation may require and the refusals it may return. `SIGNAL_EXTRACTORS` is
empty and `nlp.signals` holds 0 rows.

It is the model package the way `sros_evidence_aggregation` is the framework
package: it is imported by tests and by whatever implements the thing, and it is
not a runtime dependency of a service until one exists.
"""

from __future__ import annotations

from .facts import (
    FACT_RULES,
    LEXICAL_FREQUENCY_OBSERVATION,
    NUMERIC_OBSERVATION,
    ORDER_ESTABLISHED_WITHOUT_TIMEZONE,
    FactRule,
    withheld_facts,
)
from .model import (
    MINIMUM_DISTINCT_OBSERVATIONS,
    ORDERED_BASES,
    SIGNAL_NAMESPACE,
    SIGNAL_SCHEMA_ID,
    SIGNAL_SCHEMA_VERSION,
    AssessedInput,
    InputAssessment,
    ObservationInput,
    SignalDerivation,
    SignalDerivationRefusal,
    SignalDraft,
    SignalMagnitude,
    SignalRefusedError,
    SignalScope,
    SignalWindow,
    assess_inputs,
    build_signal,
    canonical_decimal_text,
    canonical_fingerprint,
    canonical_json,
)
from .types import (
    SIGNAL_EXTRACTORS,
    SIGNAL_TYPE_REGISTRY,
    SIGNAL_TYPES,
    SignalTypeSpec,
    record_kind_for,
)

__all__ = [
    "FACT_RULES",
    "LEXICAL_FREQUENCY_OBSERVATION",
    "MINIMUM_DISTINCT_OBSERVATIONS",
    "NUMERIC_OBSERVATION",
    "ORDERED_BASES",
    "ORDER_ESTABLISHED_WITHOUT_TIMEZONE",
    "SIGNAL_EXTRACTORS",
    "SIGNAL_NAMESPACE",
    "SIGNAL_SCHEMA_ID",
    "SIGNAL_SCHEMA_VERSION",
    "SIGNAL_TYPES",
    "SIGNAL_TYPE_REGISTRY",
    "AssessedInput",
    "FactRule",
    "InputAssessment",
    "ObservationInput",
    "SignalDerivation",
    "SignalDerivationRefusal",
    "SignalDraft",
    "SignalMagnitude",
    "SignalRefusedError",
    "SignalScope",
    "SignalTypeSpec",
    "SignalWindow",
    "assess_inputs",
    "build_signal",
    "canonical_decimal_text",
    "canonical_fingerprint",
    "canonical_json",
    "record_kind_for",
    "withheld_facts",
]
