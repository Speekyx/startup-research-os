"""Source Registry (Mission 1.0, resolves D-07).

The mandatory gate between a candidate source and a collector:

    models.py       the governance model. Dependency-free
    catalog.py      loads docs/data/source-catalog-v1.json into that model
    eligibility.py  the gate itself, which fails closed and explains itself
    retention.py    effective retention, stricter constraint winning

**Public visibility is not permission.** Nothing here converts "reachable" into
"collectable", and the two things that could -- an approval with no evidence, and
a collector enabled on an unreviewed source -- are refused by the model, by the
validator and by the database.

Collection is NOT implemented. This package governs acquisition; it performs
none, and nothing in it opens a network connection.
"""

from .catalog import DEFAULT_CATALOG_PATH, SourceCatalog, find_catalog, load_catalog
from .eligibility import EligibilityResult, evaluate_eligibility, is_collector_eligible
from .models import (
    APPROVING_STATES,
    ASSESSED_ACTIVITIES,
    AUTHORITATIVE_EVIDENCE_TYPES,
    SIGNAL_FAMILIES,
    USER_BEHAVIORS,
    AccessProfile,
    BehaviorCoverage,
    Coverage,
    CoverageScope,
    PolicyEvidence,
    PolicyReview,
    RetentionOverride,
    ReviewCondition,
    SignalCoverage,
    SourceRecord,
    SourceRegistryError,
)
from .retention import (
    BASELINE_NORMALIZED_DAYS,
    BASELINE_RAW_DAYS,
    EffectiveRetention,
    resolve_retention,
)

__all__ = [
    "SourceRecord",
    "AccessProfile",
    "PolicyReview",
    "ReviewCondition",
    "PolicyEvidence",
    "RetentionOverride",
    "Coverage",
    "CoverageScope",
    "SignalCoverage",
    "BehaviorCoverage",
    "SIGNAL_FAMILIES",
    "USER_BEHAVIORS",
    "SourceRegistryError",
    "APPROVING_STATES",
    "AUTHORITATIVE_EVIDENCE_TYPES",
    "ASSESSED_ACTIVITIES",
    "SourceCatalog",
    "load_catalog",
    "find_catalog",
    "DEFAULT_CATALOG_PATH",
    "EligibilityResult",
    "evaluate_eligibility",
    "is_collector_eligible",
    "EffectiveRetention",
    "resolve_retention",
    "BASELINE_RAW_DAYS",
    "BASELINE_NORMALIZED_DAYS",
]
