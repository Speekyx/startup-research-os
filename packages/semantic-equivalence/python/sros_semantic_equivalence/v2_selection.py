"""The V2 selection rule, recorded before any real call.

Mission 1.27 §7 and §11. Two frozen criteria, and both exist to stop a
particular way of fooling oneself.

**Selection, on DEVELOPMENT.** A variant is eligible only if it demonstrates at
least one provisional true SAME, produces at most two provisional false SAME,
and does not collapse toward SAME. The first clause is what defeats a
constant-DIFFERENT classifier -- the lesson Mission 1.24 paid for -- and the
third is the mirror the other way: a variant that says SAME to everything also
"detects positives", and it is worth nothing.

**Provisional holdout, if a variant is frozen.** Stricter, and still exploratory:
passing means `EXPLORATORY_V2_PROMISING_PENDING_HUMAN_VALIDATION` and nothing
stronger. It can never yield MODEL_VALIDATED, PRODUCTION_READY or
HUMAN_VALIDATED, because the references are `AI_ASSISTED_PROVISIONAL` and the
surrounding development process has already had access to them.

**Every count here is agreement against a provisional reference**, never accuracy
against truth. With two provisional positives in the development split, a
positive-performance estimate is extremely unstable and no proportion computed
from it means anything.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "V2_SELECTION_RULE",
    "V2_HOLDOUT_CRITERION",
    "VariantResult",
    "SelectionRule",
    "HoldoutCriterion",
    "select_variant",
]


@dataclass(frozen=True)
class SelectionRule:
    """Frozen before the first real call. Not altered after seeing outputs."""

    min_true_same: int
    max_false_same: int
    max_same_share: float
    statement: str

    def eligible(self, result: VariantResult) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if result.true_same < self.min_true_same:
            reasons.append(
                f"{result.true_same} provisional true SAME; the rule requires "
                f"{self.min_true_same}. A variant that never says SAME cannot be selected"
            )
        if result.false_same > self.max_false_same:
            reasons.append(
                f"{result.false_same} provisional false SAME; the rule permits "
                f"{self.max_false_same}"
            )
        if result.scored and result.same_share > self.max_same_share:
            reasons.append(
                f"{result.same_predictions} of {result.scored} scored pairs called SAME "
                f"({result.same_share:.0%}); above {self.max_same_share:.0%} this is a "
                "collapse toward SAME, which detects positives the way a broken clock "
                "tells the time"
            )
        if not result.schema_valid:
            reasons.append("the variant did not return schema-valid structured output")
        return (not reasons, tuple(reasons))


@dataclass(frozen=True)
class HoldoutCriterion:
    """§11. Exploratory, and it says so in its own name."""

    min_non_uncertain: int
    min_reference_same: int
    min_true_same: int
    max_false_same: int
    statement: str


V2_SELECTION_RULE = SelectionRule(
    min_true_same=1,
    max_false_same=2,
    max_same_share=0.5,
    statement=(
        "Frozen before the first real call. A V2 candidate is eligible on DEVELOPMENT "
        "only if it produces at least 1 provisional true SAME_FAMILY, at most 2 "
        "provisional false SAME_FAMILY, calls SAME on no more than half the scored "
        "pairs, and returns schema-valid structured output through the authorised "
        "Gateway route.\n\n"
        "Among eligible variants the order is: more provisional true SAME; then fewer "
        "provisional false SAME; then fewer unnecessary ABSTAIN on non-UNCERTAIN "
        "references; then the simpler procedure. Ties beyond that go to the earlier "
        "variant, so the ordering is total and the choice is reproducible.\n\n"
        "If no variant is eligible the outcome is EXPLORATORY_V2_DEVELOPMENT_FAILED and "
        "the holdout is neither called nor inspected."
    ),
)

V2_HOLDOUT_CRITERION = HoldoutCriterion(
    min_non_uncertain=12,
    min_reference_same=4,
    min_true_same=2,
    max_false_same=1,
    statement=(
        "Frozen before any holdout call. The frozen candidate is provisionally "
        "promising only if the split holds at least 12 non-UNCERTAIN references and at "
        "least 4 provisional SAME_FAMILY references, and the classifier produces at "
        "least 2 provisional true SAME, at most 1 provisional false SAME, and does not "
        "collapse to a constant decision.\n\n"
        "Passing means EXPLORATORY_V2_PROMISING_PENDING_HUMAN_VALIDATION and nothing "
        "stronger. It is not MODEL_VALIDATED, not PRODUCTION_READY, not HUMAN_VALIDATED: "
        "the references are AI_ASSISTED_PROVISIONAL and the development process has "
        "already had access to them, so this measures provisional agreement rather than "
        "independent human validation."
    ),
)


@dataclass(frozen=True)
class VariantResult:
    """One variant's agreement with a provisional reference on one split."""

    variant: str
    version: str
    complexity_rank: int
    scored: int
    same_predictions: int
    different_predictions: int
    abstentions: int
    true_same: int
    false_same: int
    missed_same: int
    agreements: int
    abstain_on_scored: int
    schema_valid: bool = True
    schema_retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_units: float = 0.0

    @property
    def same_share(self) -> float:
        return self.same_predictions / self.scored if self.scored else 0.0

    def to_json(self) -> dict[str, object]:
        return {
            "variant": self.variant,
            "prompt_version": self.version,
            "scored_pairs": self.scored,
            "predictions": {
                "SAME_PROBLEM_FAMILY": self.same_predictions,
                "DIFFERENT_PROBLEM_FAMILY": self.different_predictions,
                "ABSTAIN": self.abstentions,
            },
            "provisional_true_same": self.true_same,
            "provisional_false_same": self.false_same,
            "provisional_missed_same": self.missed_same,
            "agreements": self.agreements,
            "abstain_on_non_uncertain_references": self.abstain_on_scored,
            "same_share_of_scored": round(self.same_share, 3),
            "schema_valid": self.schema_valid,
            "schema_retries": self.schema_retries,
            "usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cost_units": round(self.cost_units, 6),
            },
            "epistemic_note": (
                "Every count is agreement against an AI_ASSISTED_PROVISIONAL reference. "
                "Not accuracy, not validated accuracy, not a human benchmark."
            ),
        }


def select_variant(
    results: list[VariantResult], rule: SelectionRule = V2_SELECTION_RULE
) -> tuple[VariantResult | None, list[tuple[VariantResult, tuple[str, ...]]]]:
    """Apply the frozen rule. Returns the winner, or None, plus every refusal.

    The refusals are returned rather than logged away: a variant rejected for a
    reason nobody recorded is a variant somebody re-tries.
    """
    verdicts = [(result, rule.eligible(result)) for result in results]
    eligible = [result for result, (ok, _) in verdicts if ok]
    refused = [(result, reasons) for result, (ok, reasons) in verdicts if not ok]
    if not eligible:
        return None, refused
    winner = sorted(
        eligible,
        key=lambda r: (-r.true_same, r.false_same, r.abstain_on_scored, r.complexity_rank),
    )[0]
    return winner, refused
