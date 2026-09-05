"""Mission 1.57 §43, §44. The route contract and its decision rules.

Two groups.

**The records.** The negative controls, the independence standard, the selection
rule and the counters, read from the checked-in artifacts. Nothing here reads the
database: CI's integration job starts from an empty one, and a test asserting
that 44 Claims exist would be asserting that the deployment is never empty.

**The arithmetic.** The two symbolic exits from the B-2 identity, driven through
the REAL aggregation primitives on non-empty fixtures. Mission 1.43 established
that with one provenance group the full aggregator IS the pass-through baseline,
and the claim this route rests on is that two ESTABLISHED independent supports
escape it. That is executed rather than asserted.

The fixture reliability values are deliberately `0.42` and `0.71` -- values no
reviewer has ever recorded -- so no reading of this file can mistake them for the
reviewed `0.5`, `0.55`, `0.6` or `0.65`. They are never persisted.
"""

from __future__ import annotations

import json
import pathlib
import unittest

from sros_contracts import EvidenceDirection, EvidenceIndependenceState
from sros_evidence_aggregation.independence import group_by_independence
from sros_evidence_aggregation.items import EvidenceItem, ItemContribution

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
BASELINE = DOCS / "independence-capable-route-baseline-v1.json"
REQUIREMENTS = DOCS / "independence-capable-apparatus-requirements-v1.json"
CANDIDATES = DOCS / "independence-capable-route-candidates-v1.json"
FEASIBILITY = DOCS / "independence-capable-route-feasibility-v1.json"
BROADENED = DOCS / "apparatus-search-broadened-v1.json"

# Not 0.5, 0.55, 0.6 or 0.65. Nothing reviewed carries these.
FIXTURE_A = 0.42
FIXTURE_B = 0.71


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


BASELINE_RECORD = _load(BASELINE)
REQUIREMENTS_RECORD = _load(REQUIREMENTS)
CANDIDATES_RECORD = _load(CANDIDATES)
FEASIBILITY_RECORD = _load(FEASIBILITY)


def _contributions(items: list[EvidenceItem]) -> dict[str, ItemContribution]:
    """Scorable contributions whose `q` is the reliability, which is what
    `q = min(components)` yields when every other component is 1.0 -- the shape
    every real Evidence row in this repository has had so far."""
    return {
        item.evidence_id: ItemContribution(
            evidence_id=item.evidence_id,
            direction=item.direction,
            components={
                "relevance": item.relevance,
                "directness": item.directness,
                "reliability": item.reliability,
                "extraction_confidence": item.extraction_confidence,
                "freshness": 1.0,
            },
            scorable=True,
            q=item.reliability,
            limiting_component="reliability",
        )
        for item in items
    }


def _groups(items: list[EvidenceItem], direction: EvidenceDirection = EvidenceDirection.SUPPORTS):
    return group_by_independence(items, _contributions(items), direction)


def _support(
    evidence_id: str, reliability: float, state: EvidenceIndependenceState
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=EvidenceDirection.SUPPORTS,
        relevance=1.0,
        directness=1.0,
        reliability=reliability,
        extraction_confidence=1.0,
        independence_state=state,
        independence_group_id=None,
        observed_at=None,
    )


class TestTheNegativeControlsStillFail(unittest.TestCase):
    """§7 and §44. A route the repository has already refuted may not come back
    because the architecture changed underneath it."""

    def setUp(self) -> None:
        self.controls = CANDIDATES_RECORD["negative_controls"]

    def test_the_republication_control_is_still_dependent(self) -> None:
        control = self.controls["world_bank_plus_fred"]
        self.assertEqual(control["verdict"], "DEPENDENT_REPUBLICATION")
        self.assertIn("Source Code SP.POP.TOTL", control["basis"])

    def test_the_common_upstream_control_is_still_dependent(self) -> None:
        control = self.controls["world_bank_plus_eurostat"]
        self.assertIn("COMMON_UPSTREAM_SOURCE", control["verdict"])
        self.assertFalse(control["promoted_by_the_inferred_layer"])

    def test_the_inferred_layer_is_not_offered_as_a_reason_to_promote_it(self) -> None:
        """The one way this mission could have gone wrong: reopening a route
        refuted on PROVENANCE because the CLAIM ARCHITECTURE changed."""
        changed = REQUIREMENTS_RECORD["what_changed_since_mission_1_48"]
        self.assertIn("does not", changed["what_did_not_change"])
        self.assertIn("republication", changed["what_did_not_change"])

    def test_a_second_publication_of_one_measurement_is_still_not_a_witness(self) -> None:
        control = self.controls["wikimedia_alternative_publication_route"]
        self.assertEqual(control["verdict"], "SAME_MEASUREMENT_UPSTREAM")
        self.assertFalse(control["searched_for"])

    def test_no_control_carries_an_independence_verdict(self) -> None:
        for name, control in self.controls.items():
            if name.startswith("$"):
                continue
            self.assertNotIn("INDEPENDENT", control["verdict"], name)


class TestTheIndependenceStandardIsHardToMeet(unittest.TestCase):
    """§15. The standard is affirmative, and the failure mode it guards against
    is reasoning from an organisation chart."""

    def setUp(self) -> None:
        self.standard = REQUIREMENTS_RECORD["independence_proof_standard"]

    def test_partial_evidence_yields_unknown(self) -> None:
        self.assertEqual(self.standard["partial_evidence_verdict"], "UNKNOWN")

    def test_separate_organisations_is_named_insufficient(self) -> None:
        self.assertTrue(
            any("separate organisations" in item for item in self.standard["insufficient"])
        )

    def test_absence_of_a_found_dependency_is_named_insufficient(self) -> None:
        self.assertTrue(any("no dependency" in item for item in self.standard["insufficient"]))

    def test_every_route_claiming_independence_carries_two_sided_basis(self) -> None:
        for route in CANDIDATES_RECORD["candidate_routes"]:
            if route["provenance_relation"] != "KNOWN_INDEPENDENT":
                continue
            self.assertGreaterEqual(len(route["independence_basis"]), 2, route["route_id"])

    def test_an_unproven_independence_is_recorded_as_unknown(self) -> None:
        """The route this mission rejected on semantics was NOT recorded as
        independent, even though it probably is: the proof was never assembled,
        and a likely independence recorded as an established one is exactly the
        shortcut the standard refuses."""
        rejected = next(
            r for r in CANDIDATES_RECORD["candidate_routes"] if r["route_id"].startswith("ROUTE-B")
        )
        self.assertEqual(rejected["provenance_relation"], "UNKNOWN")
        self.assertIn(
            "affirmative documentation",
            rejected["why_provenance_is_unknown_rather_than_independent"],
        )


class TestTheSelectionRule(unittest.TestCase):
    """§46. A route may be selected only on its own merits."""

    def test_the_selected_route_is_independent(self) -> None:
        selected = FEASIBILITY_RECORD["selected_route"]
        route = next(r for r in CANDIDATES_RECORD["candidate_routes"] if r["route_id"] == selected)
        self.assertEqual(route["provenance_relation"], "KNOWN_INDEPENDENT")

    def test_the_selected_route_fails_no_matrix_column(self) -> None:
        matrix = CANDIDATES_RECORD["decision_matrix"]
        row = matrix["rows"][FEASIBILITY_RECORD["selected_route"]]
        failures = [c for c, v in zip(matrix["columns"], row, strict=True) if v == "FAIL"]
        self.assertEqual(failures, [])

    def test_it_is_reliability_reviewable_on_both_sides(self) -> None:
        route = next(
            r
            for r in CANDIDATES_RECORD["candidate_routes"]
            if r["route_id"] == FEASIBILITY_RECORD["selected_route"]
        )
        for side in ("apparatus_a", "apparatus_b"):
            self.assertEqual(route[side]["reliability_reviewability"], "YES", side)

    def test_it_was_not_selected_by_elimination(self) -> None:
        self.assertTrue(FEASIBILITY_RECORD["not_selected_by_elimination"].strip())

    def test_the_source_exclusive_claim_was_not_selected(self) -> None:
        """§3. The Mission 1.56 Claim measures a quantity only its own platform
        can measure, and a mission looking for a second witness would find it the
        most convenient thing in the repository to reach for."""
        exclusive = BASELINE_RECORD["first_claim_is_not_the_route"]
        self.assertEqual(exclusive["second_independent_measurement_possible"], "NO")
        self.assertEqual(exclusive["flag"], "SOURCE_EXCLUSIVE_METRIC")
        self.assertNotIn("wikimedia", FEASIBILITY_RECORD["selected_route"].lower())

    def test_the_reservation_is_recorded_rather_than_hidden(self) -> None:
        """A route selected on the gates while failing a stated PREFERENCE has to
        say so where the operator will read it."""
        reservation = FEASIBILITY_RECORD["the_reservation_the_operator_should_weigh"]
        self.assertTrue(reservation["flag"].strip())
        self.assertTrue(reservation["the_transferability_limitation"].strip())


class TestNothingWasDoneToTheDeployment(unittest.TestCase):
    """§39 and §41. A feasibility mission mutates nothing."""

    def test_every_mutation_counter_is_zero(self) -> None:
        counters = FEASIBILITY_RECORD["counters"]
        for name in (
            "canonical_mutations",
            "sources_registered",
            "collectors_implemented",
            "threshold_registrations_created",
            "claims_created",
            "evidence_created",
            "reliability_assessments_created",
            "independence_groups_created",
            "scores_created",
            "opportunity_changes",
        ):
            self.assertEqual(counters[name], 0, name)

    def test_no_research_data_was_requested_and_no_value_fetched(self) -> None:
        self.assertEqual(FEASIBILITY_RECORD["counters"]["research_data_requests"], 0)
        self.assertEqual(FEASIBILITY_RECORD["counters"]["measurement_values_fetched"], 0)
        self.assertEqual(CANDIDATES_RECORD["external_discovery"]["research_data_requests"], 0)

    def test_no_model_was_called(self) -> None:
        self.assertEqual(FEASIBILITY_RECORD["counters"]["model_calls"], 0)
        self.assertEqual(FEASIBILITY_RECORD["counters"]["embeddings"], 0)
        self.assertEqual(FEASIBILITY_RECORD["counters"]["model_cost_usd"], 0.0)

    def test_the_pilot_claim_is_untouched(self) -> None:
        self.assertFalse(BASELINE_RECORD["first_inferred_claim"]["modified_by_this_mission"])
        self.assertFalse(FEASIBILITY_RECORD["counters"]["mission_1_56_claim_modified"])

    def test_the_threshold_is_not_registered_here(self) -> None:
        self.assertFalse(
            FEASIBILITY_RECORD["threshold_strategy"]["registration_created_by_this_mission"]
        )

    def test_no_reliability_value_was_assigned(self) -> None:
        scopes = FEASIBILITY_RECORD["reliability_scopes_prepared_not_assigned"]
        self.assertEqual(scopes["reliability_values_assigned"], 0)
        for side in ("apparatus_a_scope", "apparatus_b_scope"):
            self.assertNotIn("reliability", scopes[side])


class TestTheValueInspectionRule(unittest.TestCase):
    """§18. The property most easily destroyed, and destroyed silently."""

    def test_the_rule_states_its_reason(self) -> None:
        rule = REQUIREMENTS_RECORD["value_inspection_rule"]
        self.assertIn("RETRIEVAL", rule["why"])
        self.assertTrue(rule["consequence_if_broken"].strip())

    def test_a_preregistrable_route_forbids_fetching_first(self) -> None:
        threshold = FEASIBILITY_RECORD["threshold_strategy"]
        self.assertEqual(threshold["classification"], "PREREGISTRABLE_BEFORE_BOTH_MEASUREMENTS")
        self.assertTrue(any("no measurement value" in c for c in threshold["conditions"]))

    def test_no_external_norm_was_manufactured(self) -> None:
        """§19. A median, an average or a round number is not a published norm."""
        self.assertIn(
            "NOT_ESTABLISHED",
            FEASIBILITY_RECORD["threshold_strategy"]["source_native_or_external_norm_available"],
        )

    def test_the_next_mission_is_told_what_it_may_not_do(self) -> None:
        nxt = FEASIBILITY_RECORD["next_mission_recommendation"]
        self.assertTrue(any("fetch a measurement value" in item for item in nxt["it_must_not"]))


class TestTheTwoExitsAreReal(unittest.TestCase):
    """§33. Driven through the REAL grouping primitive on non-empty fixtures,
    because the whole route rests on this arithmetic differing from B-2."""

    def test_two_established_independent_supports_form_two_groups(self) -> None:
        items = [
            _support("ev-a", FIXTURE_A, EvidenceIndependenceState.KNOWN_INDEPENDENT),
            _support("ev-b", FIXTURE_B, EvidenceIndependenceState.KNOWN_INDEPENDENT),
        ]
        groups = _groups(items)
        self.assertEqual(len(groups), 2)

    def test_two_unknown_provenance_supports_collapse_into_one(self) -> None:
        """The control. Without it the test above would pass for a grouper that
        never merges anything -- and UNKNOWN collapsing is exactly what makes
        Mission 1.44.1's four Wikimedia witnesses one group."""
        items = [
            _support("ev-a", FIXTURE_A, EvidenceIndependenceState.UNKNOWN),
            _support("ev-b", FIXTURE_B, EvidenceIndependenceState.UNKNOWN),
        ]
        groups = _groups(items)
        self.assertEqual(len(groups), 1)

    def test_saturation_over_two_groups_exceeds_the_strongest_member(self) -> None:
        """S = 1 - (1-gA)(1-gB) > max(gA, gB) for positive strengths. This is the
        exact inequality that makes the full aggregator differ from the B-2
        reliability pass-through, which reports the strongest member."""
        saturated = 1 - (1 - FIXTURE_A) * (1 - FIXTURE_B)
        self.assertGreater(saturated, max(FIXTURE_A, FIXTURE_B))

    def test_saturation_over_one_group_is_that_group(self) -> None:
        """Mission 1.43's algebra, restated as the reason a second witness is
        needed at all: with one group there is nothing for saturation to do."""
        self.assertAlmostEqual(1 - (1 - FIXTURE_A), FIXTURE_A)

    def test_one_claim_can_carry_both_directions(self) -> None:
        items = [
            _support("ev-a", FIXTURE_A, EvidenceIndependenceState.KNOWN_INDEPENDENT),
            EvidenceItem(
                evidence_id="ev-b",
                direction=EvidenceDirection.CONTRADICTS,
                relevance=1.0,
                directness=1.0,
                reliability=FIXTURE_B,
                extraction_confidence=1.0,
                independence_state=EvidenceIndependenceState.KNOWN_INDEPENDENT,
                independence_group_id=None,
                observed_at=None,
            ),
        ]
        directions = {item.direction for item in items}
        self.assertEqual(directions, {EvidenceDirection.SUPPORTS, EvidenceDirection.CONTRADICTS})
        self.assertEqual(len(_groups(items, EvidenceDirection.SUPPORTS)), 1)
        self.assertEqual(len(_groups(items, EvidenceDirection.CONTRADICTS)), 1)

    def test_the_fixture_values_are_not_reviewed_values(self) -> None:
        """A fixture that shares a number with a reviewed assessment is a fixture
        somebody will eventually quote as a finding."""
        for reviewed in (0.5, 0.55, 0.6, 0.65):
            self.assertNotEqual(FIXTURE_A, reviewed)
            self.assertNotEqual(FIXTURE_B, reviewed)


class TestTheContractNeedsNoChange(unittest.TestCase):
    """§34 and §35."""

    def test_identity_excludes_every_witness_fact(self) -> None:
        fit = FEASIBILITY_RECORD["inferred_contract_fit"]
        for excluded in ("source A", "source B", "measurement values", "evidence direction"):
            self.assertIn(excluded, fit["excluded_from_identity"])
        for identity in ("canonical_subject_id", "threshold_value", "unit"):
            self.assertIn(identity, fit["target_identity_fields"])

    def test_there_is_no_schema_gap(self) -> None:
        fit = FEASIBILITY_RECORD["inferred_contract_fit"]
        self.assertEqual(fit["verdict"], "SUFFICIENT")
        self.assertEqual(fit["schema_gap"], "none")

    def test_cross_source_observed_convergence_was_not_reopened(self) -> None:
        self.assertEqual(
            FEASIBILITY_RECORD["inferred_contract_fit"]["cross_source_observed_revival"],
            "NOT_ATTEMPTED",
        )


class TestTheComplementarityRefusal(unittest.TestCase):
    """§21. The one held pair, and why the new architecture does not rescue it."""

    def test_the_held_pair_is_complementary_not_corroborating(self) -> None:
        pair = CANDIDATES_RECORD["held_pair_analysis"]["pair"]
        self.assertEqual(pair["verdict"], "COMPLEMENTARY_NOT_CORROBORATING")
        self.assertEqual(pair["gate_1_same_external_construct"], "FAIL")

    def test_no_held_pair_passed(self) -> None:
        self.assertFalse(CANDIDATES_RECORD["held_pair_analysis"]["held_pair_passed"])

    def test_the_architecture_change_is_scoped_honestly(self) -> None:
        pair = CANDIDATES_RECORD["held_pair_analysis"]["pair"]
        self.assertIn(
            "did not make a request a question",
            pair["what_the_new_architecture_did_and_did_not_change"],
        )

    def test_the_frame_trap_is_named(self) -> None:
        traps = {t["trap"] for t in REQUIREMENTS_RECORD["named_traps"]}
        self.assertIn("FRAME_INSIDE_THE_DEFINITION", traps)


if __name__ == "__main__":
    unittest.main()


class TestTheWithdrawnSelection(unittest.TestCase):
    """Mission 1.58. The operator withdrew Mission 1.57's route and made product
    relevance binding. What is tested here is that the withdrawal was recorded as
    a DECISION rather than applied as an edit."""

    def setUp(self) -> None:
        if not BROADENED.exists():
            self.skipTest("no selection has been withdrawn")
        self.record = _load(BROADENED)

    def test_the_earlier_selection_is_still_readable(self) -> None:
        """A supersession that deleted `selected_route` would hide what the
        operator decided against, which is the whole content of the decision."""
        self.assertTrue(FEASIBILITY_RECORD["selected_route"])
        self.assertEqual(
            self.record["operator_decision"]["withdrawn_route"],
            FEASIBILITY_RECORD["selected_route"],
        )

    def test_the_earlier_record_points_at_its_successor(self) -> None:
        superseded = FEASIBILITY_RECORD["selection_superseded"]
        self.assertEqual(superseded["status"], "WITHDRAWN_BY_OPERATOR")
        self.assertEqual(
            superseded["superseded_by"], "docs/data/apparatus-search-broadened-v1.json"
        )

    def test_a_rule_change_is_not_filed_as_an_error(self) -> None:
        decision = self.record["operator_decision"]
        self.assertTrue(decision["the_withdrawn_route_was_not_wrong"].strip())
        self.assertIn("rule change", decision["what_this_changes"])

    def test_the_structural_finding_survives_the_withdrawal(self) -> None:
        """The route was withdrawn. The law about where measurement occurs was
        not, and a reader must not take the whole mission as retracted."""
        survives = self.record["operator_decision"]["what_this_does_not_change"]
        self.assertTrue(any("structural finding" in item for item in survives))
        self.assertTrue(any("negative controls" in item for item in survives))

    def test_the_earlier_gates_are_carried_forward_not_replaced(self) -> None:
        amended = self.record["amended_gate_set"]
        self.assertEqual(amended["carried_forward"], 15)
        for gate in amended["added"]:
            self.assertGreater(gate["n"], 15)

    def test_the_new_gate_states_what_it_costs(self) -> None:
        """A gate that narrows the search and does not say what the narrowing
        costs is a gate nobody can weigh."""
        for gate in self.record["amended_gate_set"]["added"]:
            self.assertTrue(gate["the_cost_of_this_gate"].strip())


class TestTheBroadenedSearch(unittest.TestCase):
    def setUp(self) -> None:
        if not BROADENED.exists():
            self.skipTest("no broadened search exists")
        self.record = _load(BROADENED)
        self.route = self.record["candidate_route"]

    def test_no_route_was_selected_on_partial_gates(self) -> None:
        """The gate set is conjunctive. Selecting the best route found is not
        the same as selecting one that qualifies, and the operator asking for a
        broadened search is not a reason to lower the bar."""
        unresolved = [
            name
            for name, verdict in self.route["gate_results"].items()
            if verdict not in ("PASS", "NOT_APPLICABLE")
        ]
        self.assertTrue(unresolved)
        self.assertFalse(self.route["selected"])
        self.assertTrue(self.route["why_not_selected"].strip())

    def test_every_open_gate_names_how_to_close_it(self) -> None:
        for entry in self.route["open_gates"]:
            self.assertTrue(entry["closable_by"].strip(), entry["gate"])

    def test_the_open_gates_match_the_unresolved_results(self) -> None:
        unresolved = {
            int(name.split("_")[0])
            for name, verdict in self.route["gate_results"].items()
            if verdict not in ("PASS", "NOT_APPLICABLE")
        }
        self.assertEqual({e["gate"] for e in self.route["open_gates"]}, unresolved)

    def test_the_selected_class_is_product_relevant(self) -> None:
        pursued = [c for c in self.record["classes_surveyed"] if c["verdict"] == "PURSUED"]
        self.assertEqual(len(pursued), 1)
        self.assertNotEqual(pursued[0]["opportunity_dimension"].strip(), "")
        self.assertEqual(pursued[0]["exists_independently_of_a_measurer"], "YES")

    def test_an_absence_of_evidence_was_not_read_as_evidence(self) -> None:
        """Mission 1.57 corrected exactly this error in its own record. The
        correction is applied here rather than forgotten: one apparatus states
        its provenance affirmatively and the other only by omission, and the
        gate reads PARTIAL rather than PASS."""
        self.assertEqual(
            self.route["gate_results"]["10_first_party_lineage_documentation"], "PARTIAL"
        )
        self.assertIn("ABSENCE", self.route["apparatus_b"]["upstream_lineage"])

    def test_the_reading_versus_measuring_trap_is_named(self) -> None:
        trap = self.record["the_new_trap"]
        self.assertEqual(trap["trap"], "READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT")
        self.assertTrue(trap["found_by"].strip())

    def test_nothing_was_mutated_and_no_value_fetched(self) -> None:
        counters = self.record["counters"]
        for name in (
            "research_data_requests",
            "measurement_values_fetched",
            "model_calls",
            "embeddings",
            "canonical_mutations",
            "sources_registered",
            "reviews_created",
            "claims_created",
            "evidence_created",
        ):
            self.assertEqual(counters[name], 0, name)

    def test_the_next_mission_is_epistemics_before_governance(self) -> None:
        """Mission 1.57 recommended governance first for a route whose
        epistemics were closed. Here they are not, and paying for a licence
        before gate 5 closes would be paying to discover a semantic problem."""
        nxt = self.record["next_mission_recommendation"]
        self.assertIn("epistemics are NOT closed", nxt["why_this_and_not_governance_first"])
        self.assertTrue(any("fetch a measurement value" in i for i in nxt["it_must_not"]))
