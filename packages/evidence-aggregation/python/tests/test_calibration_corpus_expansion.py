"""Mission 1.43 §35, §36, §37. Corpus expansion, and what it may not invent.

Three groups, and the third is the one this mission was told to add.

**§35, before acquisition.** The plan was frozen in its own commit before the
contract was written, so these assert what was preregistered rather than what
came out.

**§36, after persistence.** Measured properties of the real rows, read from the
checked-in shape artifacts rather than from a database, because CI's integration
job starts from an empty one.

**§37, the branch that no data has entered.** Mission 1.42.1 shipped
`group.members` where the attribute is `member_evidence_ids`, and it survived
because `max(..., default=0)` never evaluated its generator over an empty group
list. So every reporting expression this mission added is executed here against
**non-empty, real-shaped fixtures** -- more than one member, established
independence, contradiction -- none of which the live corpus contains. The
fixtures are test data and are never persisted; §37 is explicit that this is a
testing requirement and not a licence to fabricate canonical rows.
"""

from __future__ import annotations

import json
import pathlib
import unittest
from datetime import UTC, datetime

from sros_contracts import (
    ClaimTemporality,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)
from sros_evidence_aggregation import REFERENCE_PROFILE_V1, EvidenceItem, aggregate

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
PLAN = DOCS / "calibration-corpus-expansion-plan-v1.json"
BEFORE = DOCS / "calibration-corpus-baseline-v1.json"
AFTER = DOCS / "calibration-corpus-shape-after-v1.json"
RUN = DOCS / "calibration-corpus-expansion-run-v1.json"
CONTRACTS = DOCS / "proposition-convergence-contract-v1.json"

CONVERGENT_KIND = "platform_counted_content_request_change_witnessed"
DETAILED_KIND = "platform_counted_content_request_change"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ThePlanWasFrozenFirst(unittest.TestCase):
    """§35. What was preregistered, asserted from the plan itself."""

    def test_the_plan_declares_it_was_frozen_before_any_derivation(self):
        self.assertIs(load(PLAN)["frozen_before_any_derivation"], True)

    def test_the_route_needs_no_acquisition(self):
        bounds = load(PLAN)["bounds"]
        self.assertIs(bounds["network_acquisition_required"], False)
        self.assertEqual(bounds["new_records"], 0)
        self.assertEqual(bounds["new_normalized_records"], 0)
        self.assertEqual(bounds["new_signals"], 0)

    def test_the_selected_route_is_materially_different_from_the_ted_shape(self):
        plan = load(PLAN)
        ted = [route for route in plan["candidate_routes"] if route["source"] == "ted-eu"]
        self.assertEqual(len(ted), 1)
        self.assertEqual(ted[0]["verdict"], "TOO_SIMILAR_TO_CURRENT_CORPUS")
        selected = [r for r in plan["candidate_routes"] if r["verdict"] == "SELECT"]
        self.assertEqual(len(selected), 1)
        self.assertNotEqual(selected[0]["source"], "ted-eu")

    def test_the_target_is_semantic_rather_than_a_row_count(self):
        target = load(PLAN)["preregistered_target"]
        for key in ("TARGET_A", "TARGET_B"):
            self.assertNotRegex(target[key], r"\b\d+ rows\b")
        self.assertIn("MORE THAN TWO Evidence rows", target["TARGET_B"])

    def test_contradiction_independence_temporality_are_explicitly_not_targeted(self):
        excluded = " ".join(load(PLAN)["preregistered_target"]["not_targeted"]).lower()
        for phrase in ("contradiction", "established independence", "temporality"):
            self.assertIn(phrase, excluded)

    def test_no_numeric_importance_score_is_assigned(self):
        matrix = load(PLAN)["gap_matrix"]
        defined = set(matrix["calibration_value_definitions"])
        for dimension in matrix["dimensions"]:
            self.assertIn(dimension["calibration_value"], defined)

    def test_the_plan_records_live_governance_rather_than_an_old_report(self):
        governance = load(PLAN)["live_governance"]
        self.assertEqual(governance["use_profile"], "local-private-research-v1")
        self.assertTrue(governance["eligible_now"])
        # The selected source is NOT currently acquisition-eligible, which is why
        # re-derivation is the only open door rather than merely the cheaper one.
        blocked = {e["source_id"] for e in governance["approved_with_unsatisfied_conditions"]}
        self.assertIn("wikimedia-pageviews", blocked)


class TheContractSaysWhatItAsserts(unittest.TestCase):
    """§12, §13. Identity and witness, classified by the ADR-035 test."""

    @staticmethod
    def contract() -> dict:
        entries = [
            c for c in load(CONTRACTS)["contracts"] if c["proposition_kind"] == CONVERGENT_KIND
        ]
        assert len(entries) == 1
        return entries[0]

    def test_the_day_labels_are_witness_and_everything_else_is_identity(self):
        contract = self.contract()
        self.assertEqual(set(contract["witness_fields"]), {"period_label_from", "period_label_to"})
        for field in ("source_id", "content_platform", "content_id", "audience_class", "direction"):
            self.assertIn(field, contract["identity_fields"])

    def test_identity_and_witness_are_disjoint(self):
        contract = self.contract()
        self.assertEqual(set(contract["identity_fields"]) & set(contract["witness_fields"]), set())

    def test_the_requester_class_stays_identity(self):
        """Mission 1.19 made it REQUIRED because the same item over the same
        period carries a different count per class. Dropping it here would merge
        two measurements under one name."""
        self.assertIn("audience_class", self.contract()["identity_fields"])

    def test_direction_stays_identity(self):
        """An increase and a decrease are two assertions, exactly as the
        procurement contract's `relation` is."""
        self.assertIn("direction", self.contract()["identity_fields"])

    def test_the_contract_disclaims_trend_and_audience(self):
        excluded = " ".join(self.contract()["does_not_establish"]).lower()
        for phrase in ("trend", "demand", "adoption", "independent"):
            self.assertIn(phrase, excluded)
        self.assertIn("a person read anything", excluded)

    def test_the_existing_procurement_contract_is_untouched(self):
        entries = [
            c
            for c in load(CONTRACTS)["contracts"]
            if c["proposition_kind"] == "source_published_classification_value_contrast_witnessed"
        ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["version"], "1.0.0")
        self.assertEqual(set(entries[0]["witness_fields"]), {"notice_ids", "classification_codes"})


class WhatTheExpansionActuallyProduced(unittest.TestCase):
    """§36. Measured deltas and structural properties, never pinned totals."""

    def test_no_acquisition_and_no_new_signal(self):
        run = load(RUN)
        self.assertEqual(run["network_acquisitions"], 0)
        self.assertEqual(run["signals_derived"], 0)
        for counter in ("raw_records", "normalized_records", "signals"):
            self.assertNotIn(counter, run["deltas"])

    def test_only_claims_revisions_and_evidence_moved(self):
        self.assertEqual(set(load(RUN)["deltas"]), {"claims", "claim_revisions", "evidence"})

    def test_no_reliability_assessment_and_no_independence_group_was_created(self):
        deltas = load(RUN)["deltas"]
        for counter in (
            "reliability_assessments",
            "reliability_basis_rows",
            "independence_groups",
            "evidence_reliability_written",
            "opportunities",
        ):
            self.assertNotIn(counter, deltas)

    def test_the_preregistered_targets_were_observed(self):
        claims = load(RUN)["convergent_claims"]
        self.assertTrue(claims)
        # TARGET_A: multi-Evidence outside public procurement.
        self.assertTrue(any(c["evidence_count"] > 1 for c in claims))
        # TARGET_B: a group larger than any the corpus had formed.
        self.assertTrue(any(c["evidence_count"] > 2 for c in claims))

    def test_group_cardinality_varies_for_the_first_time(self):
        before = load(BEFORE)["diversity"]["evidence_counts"]
        after = load(AFTER)["diversity"]["evidence_counts"]
        self.assertEqual(set(before), {"1", "2"})
        self.assertTrue(set(after) - set(before))
        self.assertGreater(max(int(k) for k in after), max(int(k) for k in before))

    def test_multi_evidence_is_no_longer_one_source_family(self):
        after = load(AFTER)
        families = {unit["source_family"] for unit in after["units"] if unit["evidence_count"] > 1}
        self.assertGreater(len(families), 1)

    def test_the_new_kind_is_a_new_proposition_kind(self):
        before = load(BEFORE)["diversity"]["proposition_kinds"]
        after = load(AFTER)["diversity"]["proposition_kinds"]
        self.assertNotIn(CONVERGENT_KIND, before)
        self.assertIn(CONVERGENT_KIND, after)

    def test_the_detailed_claims_were_not_disturbed(self):
        before = load(BEFORE)["diversity"]["proposition_kinds"]
        after = load(AFTER)["diversity"]["proposition_kinds"]
        self.assertEqual(before[DETAILED_KIND], after[DETAILED_KIND])

    def test_nothing_manufactured_contradiction_independence_or_temporality(self):
        after = load(AFTER)["mechanisms_exercised"]
        self.assertEqual(after["claims_with_contradiction"], 0)
        self.assertEqual(after["claims_with_established_independence"], 0)
        self.assertEqual(after["claims_temporally_sensitive"], 0)
        self.assertEqual(after["claims_with_claim_feature"], 0)

    def test_the_new_claims_are_non_scorable_and_that_is_reported(self):
        """§16. A new proposition kind is a new reliability scope, and no value
        may be invented or copied to make it bind."""
        units = [u for u in load(AFTER)["units"] if u["proposition_kind"] == CONVERGENT_KIND]
        self.assertTrue(units)
        for unit in units:
            self.assertEqual(unit["aggregation_status"], "UNAVAILABLE")
            self.assertEqual(unit["distinct_reliability_values"], [])
            self.assertEqual(unit["independence_states"], ["UNKNOWN"])

    def test_reliability_values_are_unchanged(self):
        self.assertEqual(
            load(BEFORE)["diversity"]["distinct_reliability_values"],
            load(AFTER)["diversity"]["distinct_reliability_values"],
        )

    def test_the_aggregator_still_never_differs_from_pass_through(self):
        """The honest limit. Adding rows could not change this, and the plan
        said so before the rows existed."""
        for artifact in (BEFORE, AFTER):
            self.assertEqual(
                load(artifact)["mechanisms_exercised"][
                    "claims_where_aggregator_differs_from_pass_through"
                ],
                0,
            )
            self.assertEqual(
                load(artifact)["mechanisms_exercised"]["claims_with_more_than_one_support_group"],
                0,
            )


class BranchesNoLiveDataEnters(unittest.TestCase):
    """§37. Every new reporting expression, executed on non-empty fixtures.

    These are TEST fixtures. Nothing here is persisted, and none of these shapes
    exists in the canonical corpus -- which is exactly why the expressions that
    read them have never run against real rows.
    """

    @staticmethod
    def _item(
        evidence_id: str,
        *,
        direction: EvidenceDirection = EvidenceDirection.SUPPORTS,
        reliability: float = 0.6,
        independence: EvidenceIndependenceState = EvidenceIndependenceState.UNKNOWN,
        group: str | None = None,
        source_id: str = "fixture-source",
    ) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=evidence_id,
            direction=direction,
            relevance=1.0,
            directness=1.0,
            reliability=reliability,
            extraction_confidence=1.0,
            observation_category=EvidenceObservationCategory.UNCATEGORISED,
            independence_state=independence,
            independence_group_id=group,
            observed_at=datetime(2026, 9, 1, tzinfo=UTC),
            source_id=source_id,
        )

    def _report(self, items: list[EvidenceItem]) -> dict:
        """Exactly the expressions the mission's reporting scripts evaluate.

        Written out here rather than imported because the scripts need a
        database; what must be exercised is the ATTRIBUTE ACCESS, and a typo is a
        typo in either place.
        """
        result = aggregate(
            "fixture-claim",
            items,
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality.EVERGREEN,
            allow_uncalibrated=True,
        )
        qs = [c.q for c in result.contributions if c.q is not None]
        pass_through = max(qs) if qs else None
        return {
            "status": result.status.value,
            "scorable": result.scorable_evidence_count,
            "support_groups": result.support_group_count,
            "contradiction_groups": result.contradiction_group_count,
            # The Mission 1.42.1 defect lived here.
            "max_group_members": max(
                (len(g.member_evidence_ids) for g in result.groups.support), default=0
            ),
            "collapsed": sum(g.collapsed_member_count for g in result.groups.support),
            "established_groups": sum(
                1 for g in result.groups.support if g.kind.value == "INDEPENDENT"
            ),
            "group_json": [g.to_json() for g in result.groups.support],
            "limiting": sorted(
                {c.limiting_component for c in result.contributions if c.limiting_component}
            ),
            "masses": result.masses.to_json(),
            "level": result.level.level,
            "level_json": result.level.to_json(),
            "pass_through": pass_through,
            "support_strength": result.masses.support_strength,
        }

    def test_every_expression_runs_over_a_group_with_several_members(self):
        report = self._report([self._item("a"), self._item("b"), self._item("c")])
        self.assertEqual(report["support_groups"], 1)
        self.assertEqual(report["max_group_members"], 3)
        self.assertEqual(report["collapsed"], 2)
        self.assertTrue(report["group_json"])
        self.assertEqual(report["limiting"], ["reliability"])

    def test_every_expression_runs_with_established_independence(self):
        """Two INDEPENDENT groups: a shape the live corpus has never held, and
        the only one that can make the aggregator differ from pass-through."""
        # No group id: the model refuses KNOWN_INDEPENDENT alongside one,
        # because claiming independence and group membership at once is two
        # answers to the same question.
        items = [
            self._item(
                "a",
                independence=EvidenceIndependenceState.KNOWN_INDEPENDENT,
                source_id="fixture-source-1",
            ),
            self._item(
                "b",
                independence=EvidenceIndependenceState.KNOWN_INDEPENDENT,
                source_id="fixture-source-2",
            ),
        ]
        report = self._report(items)
        self.assertGreater(report["support_groups"], 1)
        self.assertEqual(report["established_groups"], 2)
        # The point of the fixture: with two groups, saturation combines them and
        # the full aggregator stops agreeing with the strongest single item.
        self.assertGreater(report["support_strength"], report["pass_through"])

    def test_every_expression_runs_with_contradiction_present(self):
        items = [
            self._item("a"),
            self._item("b", direction=EvidenceDirection.CONTRADICTS),
        ]
        report = self._report(items)
        self.assertEqual(report["contradiction_groups"], 1)
        self.assertGreater(report["masses"]["contradicted_mass"], 0.0)
        self.assertGreater(report["masses"]["conflict_mass"], 0.0)

    def test_the_empty_case_still_reports_rather_than_raising(self):
        """The branch that DID run in production, kept so the guard stays honest."""
        report = self._report([self._item("a", reliability=None)])  # type: ignore[arg-type]
        self.assertEqual(report["max_group_members"], 0)
        self.assertEqual(report["support_groups"], 0)
        self.assertIsNone(report["pass_through"])

    def test_the_level_assessment_attribute_is_the_real_one(self):
        """`result.level.level`, not `result.level.evidence_level` -- which is
        what this mission's own first draft read, caught immediately because the
        data was not empty."""
        report = self._report([self._item("a")])
        self.assertIsInstance(report["level"], int)
        self.assertIn("evidence_level", report["level_json"])


if __name__ == "__main__":
    unittest.main()
