"""Mission 1.52 §32. What the aggregator has to do to accept the new layer.

The answer is nothing, and this file is the demonstration rather than the claim.
`aggregate()` takes a claim id, a sequence of items and a profile, and **no
claim type at all** -- so an INFERRED Claim's Evidence cannot be treated
differently from an OBSERVED Claim's, because there is no parameter through
which it could be.

Two things are proved here that Mission 1.49's fixtures did not:

*A refusal is kept out by the PRODUCER, not by the type.* `EvidenceDirection`
does have a `NEUTRAL` member -- retained for provenance and coverage, and
contributing to neither strength -- so nothing in this layer would refuse a
refusal mapped onto it. The mapping is impossible one step earlier instead:
`EvaluationResult` has no NEUTRAL, and a refusal carries no `EvidenceDecision`
at all, so the evaluator has nothing to hand over. Naming where the guarantee
actually lives matters, because a NEUTRAL row would be counted and weightless --
invisible in the numbers while visible in the counts, which is exactly the shape
ADR-037 refuses.

*The dependency runs in neither direction.* This suite imports only
`sros_contracts` and `sros_evidence_aggregation` -- the packages the
zero-dependency runner puts on its path -- so an import of the evaluator here
would not merely be forbidden, it would fail to resolve. §34's boundary is doing
the work; the tests below record what it means.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import unittest
from datetime import UTC, datetime

from sros_contracts import ClaimTemporality, EvidenceDirection, EvidenceIndependenceState
from sros_evidence_aggregation import REFERENCE_PROFILE_V1, aggregate
from sros_evidence_aggregation.items import EvidenceItem

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
AGGREGATION_PACKAGE = REPO_ROOT / "packages" / "evidence-aggregation" / "python"
MOMENT = datetime(2026, 9, 4, tzinfo=UTC)
CLAIM = "m-ge-100"

# Fixture-owned, and deliberately not 0.5, 0.55, 0.6 or 0.65 -- the four reviewed
# values in this repository. Nothing here may be mistaken for one of them.
FIXTURE_RELIABILITY = 0.42


def item(
    evidence_id: str,
    direction: EvidenceDirection,
    *,
    reliability: float | None = FIXTURE_RELIABILITY,
    state: EvidenceIndependenceState = EvidenceIndependenceState.UNKNOWN,
    group: str | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=direction,
        relevance=1.0,
        directness=1.0,
        reliability=reliability,
        extraction_confidence=1.0,
        independence_state=state,
        independence_group_id=group,
        observed_at=None,
    )


def run(*items: EvidenceItem):
    return aggregate(
        CLAIM,
        items,
        REFERENCE_PROFILE_V1,
        temporality=ClaimTemporality.EVERGREEN,
        now=MOMENT,
        allow_uncalibrated=True,
    )


class TheAggregatorCannotBranchOnClaimType(unittest.TestCase):
    """The compatibility claim, proved from the signature rather than asserted."""

    def test_aggregate_takes_no_claim_type_parameter(self):
        self.assertNotIn("claim_type", inspect.signature(aggregate).parameters)

    def test_an_evidence_item_carries_no_claim_type_either(self):
        """Mission 1.13 dropped `claim_type` from `scoring.evidence` because two
        answers to one question eventually disagree. It is still absent, which is
        why an INFERRED Claim's Evidence needs no new column and no new branch."""
        self.assertNotIn("claim_type", {f for f in EvidenceItem.__dataclass_fields__})

    def test_the_package_names_no_claim_type_member_at_all(self):
        for module in (AGGREGATION_PACKAGE / "sros_evidence_aggregation").glob("*.py"):
            tree = ast.parse(module.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    with self.subTest(module=module.name):
                        self.assertNotEqual(node.value.id, "ClaimType")


class ARefusalIsKeptOutUpstreamRatherThanRefusedHere(unittest.TestCase):
    def test_neutral_really_is_a_member_of_this_vocabulary(self):
        """Asserted rather than assumed away. A row somebody RECORDS may be
        NEUTRAL; what ADR-037 forbids is a GENERATED one, which is Mission
        1.13.1's rule and is enforced where the row is produced."""
        self.assertIn("NEUTRAL", {member.value for member in EvidenceDirection})

    def test_the_two_directional_members_are_the_evaluator_vocabulary(self):
        """Written as literals rather than imported: this suite cannot see the
        evaluator package, and that is the point of §32."""
        directional = {member.value for member in EvidenceDirection} - {"NEUTRAL"}
        self.assertEqual(directional, {"SUPPORTS", "CONTRADICTS"})

    def test_a_neutral_row_would_be_counted_and_weightless(self):
        """Which is why mapping a refusal onto it would be worse than dropping
        it: `raw_evidence_count` rises, both strengths stay flat, and a reader
        sees an observation that bears on the Claim without bearing either way."""
        neutral = run(item("e1", EvidenceDirection.NEUTRAL))
        self.assertEqual(neutral.raw_evidence_count, 1)
        self.assertEqual(neutral.neutral_evidence_count, 1)
        self.assertEqual(neutral.masses.support_strength, 0.0)
        self.assertEqual(neutral.masses.contradiction_strength, 0.0)


class TheDependencyRunsInNeitherDirection(unittest.TestCase):
    def test_the_aggregation_package_does_not_import_the_evaluator(self):
        for module in (AGGREGATION_PACKAGE / "sros_evidence_aggregation").glob("*.py"):
            with self.subTest(module=module.name):
                self.assertNotIn(
                    "sros_inferred_claim_evaluator", module.read_text(encoding="utf-8")
                )

    def test_the_aggregation_package_does_not_declare_it_as_a_dependency(self):
        manifest = (AGGREGATION_PACKAGE / "pyproject.toml").read_text(encoding="utf-8")
        self.assertNotIn("inferred-claim-evaluator", manifest)


class TheFirstInferredEvidenceIsNonScorableAndThatIsCorrect(unittest.TestCase):
    """ADR-036: a new `proposition_kind` with `claim_type = INFERRED` is a NEW
    reliability scope, so nothing is inherited by proposition similarity and the
    first rows resolve NO_APPLICABLE_ASSESSMENT."""

    def test_an_item_with_no_reliability_is_not_scorable(self):
        result = run(item("e1", EvidenceDirection.SUPPORTS, reliability=None))
        self.assertEqual(result.scorable_evidence_count, 0)
        self.assertEqual(result.raw_evidence_count, 1)

    def test_the_absence_is_not_a_middling_value(self):
        """`q = min(components)` must never see a number nobody made. An absent
        reliability produces no score rather than 0.5."""
        absent = run(item("e1", EvidenceDirection.SUPPORTS, reliability=None))
        supplied = run(item("e1", EvidenceDirection.SUPPORTS, reliability=0.5))
        self.assertNotEqual(absent.masses.support_strength, supplied.masses.support_strength)
        self.assertEqual(absent.masses.support_strength, 0.0)


class TwoWitnessesOnOneInferredProposition(unittest.TestCase):
    """The shape ADR-036 exists to make reachable: two source-attributed
    observations on ONE proposition, agreeing or disagreeing."""

    def test_a_support_and_a_contradiction_inhabit_one_claim(self):
        result = run(
            item("e1", EvidenceDirection.SUPPORTS),
            item("e2", EvidenceDirection.CONTRADICTS),
        )
        self.assertGreater(result.masses.support_strength, 0.0)
        self.assertGreater(result.masses.contradiction_strength, 0.0)
        self.assertGreater(result.masses.conflict_mass, 0.0)

    def test_the_masses_still_sum_to_one(self):
        result = run(
            item("e1", EvidenceDirection.SUPPORTS),
            item("e2", EvidenceDirection.CONTRADICTS),
        )
        self.assertTrue(result.masses.sums_to_one())

    def test_two_unknown_provenance_supports_stay_one_group(self):
        """Volume rises and strength does not. Two witnesses of unestablished
        provenance are not corroboration, whatever layer produced them."""
        result = run(
            item("e1", EvidenceDirection.SUPPORTS),
            item("e2", EvidenceDirection.SUPPORTS),
        )
        self.assertEqual(result.support_group_count, 1)
        self.assertAlmostEqual(result.masses.support_strength, FIXTURE_RELIABILITY, places=9)


if __name__ == "__main__":
    unittest.main()
