"""Evidence Aggregation V1 — the reference implementation.

Mission 1.1 §35. This package is the executable form of
`docs/domain/evidence-aggregation-framework-v1.md`. It exists to test the
specification, run synthetic sensitivity cases, prove reproducibility, and act
as an oracle for whatever implements aggregation later.

**This is NOT `services/scoring`.** It computes no Opportunity Score, reads no
database, contacts no network and is wired into no request path. `services/scoring`
remains unavailable for production research until a CALIBRATED profile exists
(§41), and that is a separate gate from the algorithm being defined.

    items.py         one evidence record and its contribution strength
    recency.py       freshness. Half-life per profile, never a global constant
    independence.py  provenance grouping, so duplicates cannot multiply
    saturation.py    bounded accumulation across independent groups
    masses.py        the four-mass decomposition and the Evidence Score
    levels.py        EvidenceLevel eligibility. Category gates 4 and 5
    profile.py       the versioned parameter set, and its calibration status
    result.py        the reproducible result and its explanation
    engine.py        aggregate()
    sensitivity.py   the synthetic harness

**Three things this module deliberately does not have.**

*No per-source reliability constant.* There is no table mapping a platform to a
number, and a test asserts that no registered source id appears anywhere in this
package. Reliability is a property of an evidence record against a specific
claim, not of the platform it came from (§7). A source's POLICY status —
whether Mission 1.0 says we may collect it — is a different question again, and
must never become an epistemic weight.

*No invented defaults.* A missing input makes a record NON-SCORABLE. It stays in
the set, it is reported, it counts towards coverage, and it contributes nothing
numeric. An unknown number stays unknown.

*No probabilities.* `q`, the strengths and the masses are bounded
contribution values. `EvidenceScore = 82` does not mean an 82% chance the claim
is true, and nothing here may be presented as though it did.

Dependencies: the standard library and `sros_contracts`. Nothing else, so this
runs in the zero-dependency CI job where a broken environment cannot silently
reduce it to nothing (ADR-009).
"""

from .engine import aggregate
from .errors import (
    AggregationError,
    InvalidFactorError,
    UncalibratedProfileError,
)
from .independence import GroupKind, IndependenceGroup, group_by_independence
from .items import (
    ITEM_QUALITY_COMPONENTS,
    EvidenceItem,
    ItemContribution,
    NonScorableReason,
    evaluate_item,
)
from .levels import LEVEL_NAMES, EvidenceLevelAssessment, assess_evidence_level
from .masses import ALGORITHM_VERSION, MassDecomposition, decompose, evidence_score
from .profile import (
    REFERENCE_PROFILE_V1,
    EvidenceAggregationProfile,
    LevelThresholds,
)
from .recency import MISSING_TEMPORAL_PARAMETER, freshness, half_life_decay
from .result import EvidenceAggregationResult, GroupExplanation
from .saturation import saturate

__all__ = [
    "ALGORITHM_VERSION",
    "ITEM_QUALITY_COMPONENTS",
    "LEVEL_NAMES",
    "MISSING_TEMPORAL_PARAMETER",
    "REFERENCE_PROFILE_V1",
    "AggregationError",
    "EvidenceAggregationProfile",
    "EvidenceAggregationResult",
    "EvidenceItem",
    "EvidenceLevelAssessment",
    "GroupExplanation",
    "GroupKind",
    "IndependenceGroup",
    "InvalidFactorError",
    "ItemContribution",
    "LevelThresholds",
    "MassDecomposition",
    "NonScorableReason",
    "UncalibratedProfileError",
    "aggregate",
    "assess_evidence_level",
    "decompose",
    "evaluate_item",
    "evidence_score",
    "freshness",
    "group_by_independence",
    "half_life_decay",
    "saturate",
]
