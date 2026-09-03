"""Whether a packet could support an opportunity hypothesis at all.

Mission 1.28 §12, pre-registered as `opportunity-sufficiency@1.0.0`.

    at least 2 eligible Evidence rows
    AND at least 2 distinct COUNTING evidence dimensions

**Formable is not scoring-ready and is not validated.** It says only that a
question can be asked without manufacturing its answer. `HYPOTHESIS_FORMABLE`
over a packet whose every row is `ELIGIBLE_CONTEXT` stays entirely unscorable,
and `scoring_ready` reports that separately rather than being folded into the
same word.

**No dimension is required.** There is deliberately no rule that a hypothesis
must carry `WILLINGNESS_TO_PAY`, or any other named member. A requirement that
every opportunity contain every dimension would make the engine unable to record
anything the current portfolio can observe, which is a gate designed to produce a
predetermined answer.

**One qualifier, and it is decisive for the current corpus, so it is declared
here rather than buried.** Diversity is counted over `COUNTING_DIMENSIONS`, which
excludes `TREND_OR_CHANGE`. Every Evidence row in this repository is derived from
a Signal, a Signal is by definition a derivation over two or more observations,
and so every row describes a change: a dimension the whole corpus carries cannot
distinguish a packet with two kinds of evidence from one measurement repeated six
times. `evaluate` returns the count under **both** readings, and
`mission-1.28-report.md` reports both, because the qualifier was chosen with the
26 real rows already inspected -- as Mission 1.28 §3 instructed -- and a rule
chosen after seeing the data has to be visible enough to be overruled.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .eligibility import PacketEligibility
from .packet import OpportunityEvidencePacket

__all__ = [
    "SUFFICIENCY_PROCEDURE_VERSION",
    "SUFFICIENCY_V1",
    "HypothesisStatus",
    "SufficiencyRule",
    "SufficiencyResult",
    "evaluate",
]

SUFFICIENCY_PROCEDURE_VERSION = "opportunity-sufficiency@1.0.0"


class HypothesisStatus(enum.Enum):
    HYPOTHESIS_FORMABLE = "HYPOTHESIS_FORMABLE"
    HYPOTHESIS_INSUFFICIENT_EVIDENCE = "HYPOTHESIS_INSUFFICIENT_EVIDENCE"
    HYPOTHESIS_REQUIRES_REVIEW = "HYPOTHESIS_REQUIRES_REVIEW"


@dataclass(frozen=True)
class SufficiencyRule:
    min_eligible_rows: int
    min_distinct_dimensions: int
    statement: str


SUFFICIENCY_V1 = SufficiencyRule(
    min_eligible_rows=2,
    min_distinct_dimensions=2,
    statement=(
        "Pre-registered for Mission 1.28. A packet is HYPOTHESIS_FORMABLE only if it "
        "holds at least 2 Evidence rows that are ELIGIBLE_CONTEXT or ELIGIBLE_SCORING, "
        "and those rows together carry at least 2 distinct counting dimensions, where "
        "TREND_OR_CHANGE does not count because every Evidence row in this repository "
        "carries it by construction.\n\n"
        "Formable means a question can be asked without manufacturing its answer. It is "
        "NOT scoring-ready, NOT validated, and NOT a finding that an opportunity "
        "exists. A packet whose rows are all NON_SCORABLE can be FORMABLE and can "
        "still contribute nothing to any score.\n\n"
        "A packet holding rows nobody has assessed is HYPOTHESIS_REQUIRES_REVIEW rather "
        "than insufficient: unanswered is not the same as answered no, and merging them "
        "would let an open question look like a settled one."
    ),
)


@dataclass(frozen=True)
class SufficiencyResult:
    status: HypothesisStatus
    reasons: tuple[str, ...]
    eligible_rows: int
    scoring_eligible_rows: int
    distinct_counting_dimensions: int
    #: The same count under the literal §12 wording, with TREND_OR_CHANGE
    #: counted. Reported so the qualifier's effect is visible rather than
    #: implicit.
    distinct_dimensions_literal: int
    requires_review_rows: int

    @property
    def scoring_ready(self) -> bool:
        """Always False while any row lacks a reviewed reliability.

        Separate from `status` on purpose: §12 says formability alone must not
        make a packet scoring-ready, and two properties that must not imply each
        other should not share a field.
        """
        return self.scoring_eligible_rows >= SUFFICIENCY_V1.min_eligible_rows


def evaluate(
    packet: OpportunityEvidencePacket,
    rule: SufficiencyRule = SUFFICIENCY_V1,
    requires_review_rows: int = 0,
) -> SufficiencyResult:
    eligible = packet.eligibility_counts.get(
        PacketEligibility.ELIGIBLE_CONTEXT.value, 0
    ) + packet.eligibility_counts.get(PacketEligibility.ELIGIBLE_SCORING.value, 0)
    scoring = packet.scoring_eligible_count
    counting = len(packet.counting_dimensions)
    literal = len(packet.dimensions)

    reasons: list[str] = []
    if eligible < rule.min_eligible_rows:
        reasons.append(
            f"{eligible} eligible Evidence rows; the rule requires {rule.min_eligible_rows}"
        )
    if counting < rule.min_distinct_dimensions:
        detail = ", ".join(sorted(d.value for d in packet.counting_dimensions)) or "none"
        reasons.append(
            f"{counting} distinct counting dimensions ({detail}); the rule requires "
            f"{rule.min_distinct_dimensions}"
        )

    if reasons:
        status = HypothesisStatus.HYPOTHESIS_INSUFFICIENT_EVIDENCE
    elif requires_review_rows:
        status = HypothesisStatus.HYPOTHESIS_REQUIRES_REVIEW
        reasons.append(
            f"{requires_review_rows} candidate rows are REQUIRES_REVIEW and were "
            "excluded; the packet meets the rule without them, so the unanswered "
            "questions are worth answering before a hypothesis is formed"
        )
    else:
        status = HypothesisStatus.HYPOTHESIS_FORMABLE
        reasons.append(
            f"{eligible} eligible rows carrying {counting} counting dimensions. "
            f"{scoring} of them are scoring-eligible, so this packet is formable and "
            "not scoring-ready."
        )

    return SufficiencyResult(
        status=status,
        reasons=tuple(reasons),
        eligible_rows=eligible,
        scoring_eligible_rows=scoring,
        distinct_counting_dimensions=counting,
        distinct_dimensions_literal=literal,
        requires_review_rows=requires_review_rows,
    )
