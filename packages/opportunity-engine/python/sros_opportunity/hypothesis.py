"""The opportunity hypothesis: what it is, and what it structurally cannot be.

Mission 1.28 §2, §14, §18.

An opportunity hypothesis says: *a product or intervention serving actor X with
need Y through value proposition Z may be worth investigating, because evidence
A, B and C bears on specific dimensions of that idea.* It is a question worth
asking, recorded with what supports it and what does not.

**It is not** a market-size claim, a prediction, a recommendation to build, a
Claim copied into another table, or an LLM brainstorm. Nothing here guarantees
demand, revenue, willingness to pay, market size, adoption or product-market fit,
and `guards.py` refuses the vocabulary that would imply any of them.

**The status enum contains no validated state, and that is the enforcement.**
Mission 1.28 §18 asks for the distinction in code rather than in prose, so
`VALIDATED_OPPORTUNITY` is not a value that exists to be set: there is no
constant, no database CHECK member and no migration that admits one. A future
mission wanting one has to add it deliberately, which is the point.

**Unsupported dimensions are a required field.** A hypothesis that listed only
what supports it would be a sales document. `unsupported_dimensions` is validated
non-empty for every hypothesis this engine can currently produce, because the
portfolio answers two of fourteen questions.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .dimensions import EvidenceDimension
from .guards import check_no_validation_language, check_statement

__all__ = [
    "HYPOTHESIS_PROCEDURE_VERSION",
    "OpportunityStatus",
    "OpportunityHypothesis",
    "UnsupportedClaimError",
]

HYPOTHESIS_PROCEDURE_VERSION = "opportunity-hypothesis@1.0.0"


class OpportunityStatus(enum.Enum):
    """Every state an Opportunity row may hold.

    Three values, all hypothesis-grade. There is deliberately no
    `VALIDATED_OPPORTUNITY`, no `PROVEN_MARKET`, no `WINNING_IDEA`, no
    `PRODUCT_MARKET_FIT` and no `HIGH_CONFIDENCE_BUSINESS`: those are not states
    this engine can reach, so they are not states this enum can express. The
    database CHECK constraint carries the same three values, so the refusal
    survives a caller that bypasses this module.
    """

    OPPORTUNITY_HYPOTHESIS = "OPPORTUNITY_HYPOTHESIS"
    HYPOTHESIS_WITHDRAWN = "HYPOTHESIS_WITHDRAWN"
    HYPOTHESIS_SUPERSEDED = "HYPOTHESIS_SUPERSEDED"


class UnsupportedClaimError(ValueError):
    """Raised when a hypothesis asserts something its evidence does not support."""


@dataclass(frozen=True)
class OpportunityHypothesis:
    """One hypothesis, its support, and its stated limits.

    Construction validates. A hypothesis that violates §11 or §18 cannot be
    built, so it cannot be persisted, serialised or reported -- rather than being
    built and then checked somewhere a later caller might skip.
    """

    hypothesis_id: str
    packet_id: str
    status: OpportunityStatus

    target_actor: str
    observed_need_or_change: str
    candidate_intervention: str
    hypothesis_statement: str
    reasoning_summary: str

    supported_dimensions: frozenset[EvidenceDimension]
    unsupported_dimensions: frozenset[EvidenceDimension]

    key_evidence_ids: tuple[str, ...]
    key_claim_ids: tuple[str, ...]
    source_families: tuple[str, ...]

    uncertainties: tuple[str, ...]
    epistemic_limitations: tuple[str, ...]

    use_profile_id: str
    procedure_version: str = HYPOTHESIS_PROCEDURE_VERSION
    #: Present only when a model participated. Absent means deterministic, and
    #: `claim-model-v1.md`'s rule applies unchanged: DETERMINISTIC forbids a
    #: model version, because "deterministic" promises regenerability.
    model_version: str | None = None
    prompt_version: str | None = None
    revision: int = 1
    #: Structurally empty and it stays that way (Mission 1.28 §15). The type is
    #: the empty tuple, so a score cannot be added without changing the type --
    #: which is the point: ranking is a later mission with its own decisions, and
    #: a field that merely DEFAULTED to empty would fill up quietly.
    scores: tuple[()] = ()

    def __post_init__(self) -> None:
        if self.status is not OpportunityStatus.OPPORTUNITY_HYPOTHESIS and self.revision == 1:
            raise ValueError(
                "a hypothesis is created as OPPORTUNITY_HYPOTHESIS; withdrawal and "
                "supersession are later revisions, never an initial state"
            )
        if not self.key_evidence_ids:
            raise UnsupportedClaimError(
                f"{self.hypothesis_id}: no supporting Evidence ids. A hypothesis with "
                "no evidence is an idea, and this engine does not record ideas."
            )
        if not self.key_claim_ids:
            raise UnsupportedClaimError(
                f"{self.hypothesis_id}: no supporting Claim ids. Evidence is "
                "claim-relative, so evidence citing no claim cites nothing."
            )
        if not self.unsupported_dimensions:
            raise UnsupportedClaimError(
                f"{self.hypothesis_id}: unsupported_dimensions is empty. A hypothesis "
                "supported on every dimension is not a hypothesis, and the portfolio "
                "currently answers two of fourteen questions."
            )
        if self.supported_dimensions & self.unsupported_dimensions:
            raise ValueError(
                f"{self.hypothesis_id}: a dimension is listed as both supported and unsupported"
            )
        if self.model_version is not None and self.prompt_version is None:
            raise ValueError(
                f"{self.hypothesis_id}: a model-assisted hypothesis must record the "
                "prompt version too; a model version alone cannot be reproduced"
            )

        prose = " ".join(
            (
                self.hypothesis_statement,
                self.observed_need_or_change,
                self.candidate_intervention,
                self.reasoning_summary,
            )
        )
        violations = check_statement(prose, self.supported_dimensions)
        violations += check_no_validation_language(prose)
        if violations:
            raise UnsupportedClaimError(
                f"{self.hypothesis_id}: " + "; ".join(f"{v.term}: {v.message}" for v in violations)
            )

    @property
    def is_validated(self) -> bool:
        """Always False, and there is no code path that returns True.

        Kept as an explicit property rather than left undefined, so a consumer
        asking the question gets an answer instead of inventing one from the
        presence of a row.
        """
        return False
