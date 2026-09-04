"""The inputs and outputs of a deterministic INFERRED evaluation.

Every type here is a frozen value object. The evaluator is a pure function over
them: it reaches no database, no network and no model, and it holds no state.

**What this module deliberately does not contain.**

*No equivalence engine.* `SemanticEquivalenceDecision` is an INPUT. Judging that
a source-native measurement measures the target's quantity is a documentary
judgement a person makes, and Mission 1.46 found a shared year label covering two
different reference dates -- so nothing here infers equivalence from identifiers,
labels or matching strings.

*No independence.* Independence is a property of Evidence provenance and is
adjudicated elsewhere (ADR-036 invariant I10). A dependent republication still
SUPPORTS the same proposition; it simply stays one provenance group later, which
is the aggregator's business and not this module's.

*No reliability.* Reliability is resolved late from a reviewed assessment against
a five-part scope. It is not an input here and not an output.

*No confidence on the arithmetic.* `110 >= 100` is exact. The only uncertain step
is the semantic correspondence, and its confidence arrives ON the equivalence
decision rather than being invented by the comparison (ADR-037).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

__all__ = [
    "DerivationDraft",
    "EquivalenceDimension",
    "EquivalenceVerdict",
    "EvaluationResult",
    "EvidenceDecision",
    "InferredClaimDraft",
    "MeasurementWitness",
    "SemanticEquivalenceDecision",
    "TargetProposition",
    "ThresholdOperator",
    "ThresholdProvenanceStatus",
    "ThresholdRegistration",
]


class EvaluationResult(StrEnum):
    """What one measurement does to one proposition.

    Four members and no fifth. `NEUTRAL` is deliberately absent: it would assert
    that an observation bears on the Claim without bearing either way, which is a
    positive finding and a different thing from not knowing (ADR-037).
    """

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    # The measurement bears on a DIFFERENT proposition. Never CONTRADICTS: a
    # measurement of another quantity is not a disagreement about this one.
    NOT_APPLICABLE = "NOT_APPLICABLE"
    # Whether it bears on this proposition could not be established. Never
    # SUPPORTS, and never quietly the middle of a scale.
    UNKNOWN = "UNKNOWN"


class ThresholdOperator(StrEnum):
    """The smallest useful closed set. Each member has a test case; none was
    added speculatively."""

    GTE = "GTE"
    GT = "GT"
    LTE = "LTE"
    LT = "LT"


class ThresholdProvenanceStatus(StrEnum):
    """How the bound came to be, mirroring migration 0034 exactly.

    It changes CALIBRATION ELIGIBILITY and never logical entailment: a post-hoc
    bound with a measurement of 110 genuinely supports `M >= 100`.
    """

    PREREGISTERED = "PREREGISTERED"
    SOURCE_NATIVE = "SOURCE_NATIVE"
    EXTERNAL_NORM = "EXTERNAL_NORM"
    POST_HOC = "POST_HOC"
    UNKNOWN = "UNKNOWN"


CALIBRATION_ELIGIBLE_STATUSES = frozenset(
    {
        ThresholdProvenanceStatus.PREREGISTERED,
        ThresholdProvenanceStatus.SOURCE_NATIVE,
        ThresholdProvenanceStatus.EXTERNAL_NORM,
    }
)


class EquivalenceVerdict(StrEnum):
    EQUIVALENT = "EQUIVALENT"
    NOT_EQUIVALENT = "NOT_EQUIVALENT"
    UNKNOWN = "UNKNOWN"


class EquivalenceDimension(StrEnum):
    """The dimensions ADR-037 froze. A decision that checked fewer than all of
    them is refused, so a reviewer cannot establish equivalence by looking at
    the easy half."""

    CANONICAL_SUBJECT = "CANONICAL_SUBJECT"
    METRIC_DEFINITION = "METRIC_DEFINITION"
    TIME_BOUND = "TIME_BOUND"
    POPULATION = "POPULATION"
    GEOGRAPHY = "GEOGRAPHY"
    UNIT = "UNIT"
    ADJUSTMENT = "ADJUSTMENT"
    METHODOLOGY_SEMANTICS = "METHODOLOGY_SEMANTICS"


ALL_EQUIVALENCE_DIMENSIONS = frozenset(EquivalenceDimension)


@dataclass(frozen=True)
class MeasurementWitness:
    """One source-native measurement, and the provenance that makes it one.

    `retrieved_at` is here for one reason: the preregistration rule compares a
    threshold's `recorded_at` against the moment THIS SYSTEM obtained the
    measurement, never against when it was published (ADR-037 §23).
    """

    workspace_id: str
    signal_id: str
    source_id: str
    resource_id: str
    record_kind_id: str
    canonical_subject_id: str
    source_native_metric_id: str
    metric_definition_id: str
    measurement_value: Decimal
    unit: str
    time_bound: str
    population_or_geography: str
    retrieved_at: datetime
    observed_claim_id: str | None = None
    adjustment: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.measurement_value, Decimal):
            raise TypeError(
                "measurement_value must be a Decimal. A float comparison against a "
                "threshold introduces a binary artifact exactly at the boundary the "
                "proposition is about, and migration 0034 stores NUMERIC for the same "
                "reason"
            )


@dataclass(frozen=True)
class TargetProposition:
    """A source-independent THRESHOLD_STATE proposition.

    It carries NO source_id, NO measurement value and NO direction, which is what
    lets several witnesses -- agreeing or disagreeing -- reach one Claim
    (ADR-036).
    """

    proposition_kind: str
    canonical_subject_id: str
    metric_definition_id: str
    time_bound: str
    population_or_geography: str
    unit: str
    threshold_operator: ThresholdOperator
    threshold_value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.threshold_value, Decimal):
            raise TypeError("threshold_value must be a Decimal, never a float")


@dataclass(frozen=True)
class ThresholdRegistration:
    """A frozen bound with its provenance, mirroring one row of
    `research.threshold_registrations`."""

    registration_id: str
    workspace_id: str
    metric_definition_id: str
    scope_subject_id: str
    scope_population: str
    scope_time_bound: str
    unit: str
    threshold_operator: ThresholdOperator
    threshold_value: Decimal
    provenance_status: ThresholdProvenanceStatus
    recorded_at: datetime
    recorded_by: str
    provenance_reference: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.threshold_value, Decimal):
            raise TypeError("threshold_value must be a Decimal, never a float")

    @property
    def calibration_eligible(self) -> bool:
        """DERIVED, never stored. Migration 0034 has no `calibration_eligible`
        column because two authorities for one fact eventually disagree."""
        return self.provenance_status in CALIBRATION_ELIGIBLE_STATUSES


@dataclass(frozen=True)
class SemanticEquivalenceDecision:
    """An already-established judgement that this measurement bears on this
    proposition. An INPUT, never something the evaluator derives.

    It carries `interpretation_confidence` because that is the only honest source
    for it: the field asks how confident we are that the WORDING faithfully
    states what the Signals showed, and for a deterministic threshold Claim the
    one uncertain step is exactly this correspondence (ADR-037 §17). The
    arithmetic never supplies it.
    """

    basis_id: str
    verdict: EquivalenceVerdict
    dimensions_checked: frozenset[EquivalenceDimension]
    reviewed_by: str
    reviewed_at: datetime
    interpretation_confidence: float | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.basis_id.strip():
            raise ValueError("a semantic-equivalence decision names the basis it rests on")
        if self.verdict is EquivalenceVerdict.EQUIVALENT:
            missing = ALL_EQUIVALENCE_DIMENSIONS - set(self.dimensions_checked)
            if missing:
                raise ValueError(
                    "EQUIVALENT requires every frozen dimension to have been checked; "
                    f"missing {sorted(d.value for d in missing)}. Establishing equivalence "
                    "on the easy half is how two different quantities become one"
                )
            if self.interpretation_confidence is None:
                raise ValueError(
                    "EQUIVALENT must carry an interpretation_confidence. It is the "
                    "reviewer's confidence in the correspondence, and the evaluator has "
                    "no honest way to invent it"
                )
        if self.interpretation_confidence is not None and not (
            0.0 <= self.interpretation_confidence <= 1.0
        ):
            raise ValueError("interpretation_confidence is a unit interval value")


@dataclass(frozen=True)
class EvidenceDecision:
    """What Evidence a result implies. `direction` is None for a refusal, and
    that is the whole point: NOT_APPLICABLE and UNKNOWN produce no Evidence row
    rather than a NEUTRAL one."""

    signal_id: str
    direction: str | None
    source_id: str


@dataclass(frozen=True)
class InferredClaimDraft:
    """An in-memory source-independent Claim. Never persisted here."""

    proposition_key: str
    proposition_facts: dict[str, str]
    claim_type: str
    interpretation_kind: str
    model_version: None
    interpretation_confidence: float
    origin_detail: str


@dataclass(frozen=True)
class DerivationDraft:
    """One row of `research.claim_derivations`, minus the binding it cannot have
    yet.

    `claim_revision_id` is absent BY CONSTRUCTION rather than by oversight: the
    revision does not exist when the evaluation runs, and inventing an id here
    would be fabricating the thing the record is supposed to prove. Binding is a
    later phase, and for a refusal there may be no revision to bind to at all --
    which is the contract gap this mission reports.
    """

    workspace_id: str
    input_signal_id: str
    input_observed_claim_id: str | None
    derivation_rule_id: str
    derivation_rule_version: str
    evaluator_version: str
    measurement_value: Decimal
    threshold_registration_id: str | None
    evaluation_result: EvaluationResult
    semantic_equivalence_basis_id: str
    interpretation_kind: str
    model_version: None
    rationale: str


@dataclass(frozen=True)
class EvaluationOutcome:
    """Everything one evaluation determined, and nothing it did not.

    No database write is implied. `claim_draft` and `evidence_decision` are
    present only for a directional result.
    """

    result: EvaluationResult
    rationale: str
    derivation: DerivationDraft
    proposition_key: str | None = None
    claim_draft: InferredClaimDraft | None = None
    evidence_decision: EvidenceDecision | None = None
    calibration_eligible: bool | None = None
    refusal_reason: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_directional(self) -> bool:
        return self.result in (EvaluationResult.SUPPORTS, EvaluationResult.CONTRADICTS)
