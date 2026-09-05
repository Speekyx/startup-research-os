"""Mission 1.61 §62. The anchor lineage records, the partner recovery, the enquiry.

These assert the properties a later mission would most easily bend. The one this
mission paid for is the difference between LEVEL 1 and LEVEL 2: an apparatus
saying it scans is not an apparatus saying nothing else feeds its records, and
the gate passes only on the second. Both statements appear in this mission, from
two different apparatuses, which is why the distinction is tested rather than
described.

Nothing here is persisted, no measurement was retrieved to construct it, and no
test asserts a count of anything in the world.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

BASELINE = DATA / "anchor-documentation-confirmation-baseline-v1.json"
LINEAGE = DATA / "anchor-lineage-review-v1.json"
OPERATIONAL = DATA / "anchor-operational-reviewability-v1.json"
VANTAGE = DATA / "anchor-vantage-model-v1.json"
PORTWINDOW = DATA / "anchor-port-window-coverage-v1.json"
PARTNERS = DATA / "partner-documentation-recovery-v1.json"
CLOSURE = DATA / "anchor-lineage-and-documentation-closure-v1.json"
ENQUIRY = DATA / "anchor-technical-lineage-enquiry-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
ENQUIRY_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"

MISSION_1_60_PARTNERS = ("The Shadowserver Foundation", "ONYPHE", "LeakIX")
GATES = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")
QUALIFYING = ("PASS", "PASS_WITH_STATED_BOUNDS")


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _prose(node: object) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            out.extend(_prose(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_prose(item))
    elif isinstance(node, str):
        out.append(node)
    return out


class TestBaseline(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(BASELINE)

    def test_mission_1_60_is_recorded_merged_with_its_commit(self) -> None:
        pre = self.record["repository_precondition"]
        self.assertTrue(pre["mission_1_60_merged"])
        self.assertTrue(pre["merge_commit"].strip())

    def test_the_baseline_records_no_drift(self) -> None:
        self.assertEqual(self.record["canonical_baseline"]["drift_from_mission_1_60"], "none")

    def test_the_inferred_claim_is_still_one_and_still_alone(self) -> None:
        base = self.record["canonical_baseline"]
        self.assertEqual(base["inferred_claims"], 1)
        self.assertEqual(base["claims_carrying_both_directions"], 0)
        self.assertEqual(base["independence_groups"], 0)

    def test_the_scope_is_exactly_four_subjects(self) -> None:
        scope = self.record["scope_freeze"]
        self.assertEqual(scope["subject_count"], 4)
        self.assertEqual(tuple(scope["partners"]), MISSION_1_60_PARTNERS)
        self.assertEqual(scope["new_candidates_evaluated"], 0)

    def test_the_dropped_apparatus_was_not_revived(self) -> None:
        dropped = self.record["scope_freeze"]["dropped_apparatus"]
        self.assertFalse(dropped["reconsidered"])
        self.assertEqual(dropped["retained_as"], "NEGATIVE_CONTROL")

    def test_every_budget_was_respected(self) -> None:
        ledger = self.record["documentation_ledger"]
        self.assertLessEqual(ledger["used_anchor"], ledger["budget_anchor"])
        self.assertLessEqual(ledger["used_partners"], ledger["budget_partners"])
        self.assertLessEqual(ledger["used_total"], ledger["budget_total"])
        self.assertEqual(ledger["used_total"], len(ledger["requests"]))

    def test_every_load_bearing_retrieval_is_first_party(self) -> None:
        for entry in self.record["documentation_ledger"]["requests"]:
            if entry["load_bearing"]:
                self.assertTrue(entry["first_party"], entry["url"])

    def test_no_measurement_value_was_retrieved(self) -> None:
        exposure = self.record["value_exposure"]
        self.assertFalse(exposure["target_measurement_retrieved"])
        self.assertFalse(exposure["host_records_retrieved"])
        self.assertFalse(exposure["banners_retrieved"])
        self.assertEqual(exposure["queries_executed"], 0)

    def test_no_trial_of_any_cost_was_started(self) -> None:
        exposure = self.record["value_exposure"]
        self.assertEqual(exposure["trials_started"], 0)
        self.assertFalse(exposure["demo_console_used"])
        self.assertFalse(exposure["search_preview_used"])

    def test_every_canonical_counter_is_zero(self) -> None:
        for name, value in self.record["canonical_mutations"].items():
            if name.startswith("$"):
                continue
            self.assertIn(value, (0, 0.0, False), name)


class TestLineageA7(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(LINEAGE)

    def test_a7_passes_at_level_2(self) -> None:
        verdict = self.record["gate_a7_verdict"]
        self.assertEqual(verdict["verdict"], "PASS")
        self.assertEqual(verdict["level_reached"], "LEVEL_2")
        self.assertEqual(verdict["previous_verdict"], "PARTIAL")

    def test_level_2_rests_on_two_verbatim_quotations(self) -> None:
        level2 = self.record["level_2_evidence"]
        self.assertTrue(level2["verbatim_affirmative_statement"].strip())
        self.assertTrue(level2["verbatim_exception_clause"].strip())
        self.assertTrue(level2["retrieved_twice"])

    def test_the_exception_list_is_closed(self) -> None:
        level2 = self.record["level_2_evidence"]
        self.assertTrue(level2["exception_list_is_closed"])
        self.assertIn("only exceptions", level2["verbatim_exception_clause"])

    def test_every_exception_was_checked_against_the_predicate(self) -> None:
        check = self.record["do_the_exceptions_touch_the_load_bearing_predicate"]
        self.assertTrue(check["exceptions"])
        for item in check["exceptions"]:
            self.assertIn("bears_on_predicate", item)
            self.assertFalse(item["bears_on_predicate"], item["name"])
            self.assertTrue(item["why"].strip())

    def test_the_predicate_is_the_protocol_native_one(self) -> None:
        predicate = self.record["do_the_exceptions_touch_the_load_bearing_predicate"][
            "load_bearing_predicate"
        ]
        self.assertIn("SSH-", predicate)
        self.assertIn("22", predicate)

    def test_a7_did_not_pass_on_an_inference(self) -> None:
        self.assertTrue(self.record["gate_a7_verdict"]["affirmative_not_inferred"])

    def test_lineage_is_not_frame_exhaustiveness(self) -> None:
        two = self.record["two_exhaustiveness_questions_that_are_not_one"]
        self.assertTrue(two["LINEAGE_EXHAUSTIVENESS"]["answered_here"])
        self.assertFalse(two["SCAN_OR_FRAME_EXHAUSTIVENESS"]["answered_here"])
        self.assertEqual(two["SCAN_OR_FRAME_EXHAUSTIVENESS"]["gate"], "A5")

    def test_the_finding_states_it_is_not_a_coverage_claim(self) -> None:
        bounds = self.record["bounds_on_this_finding"]
        self.assertTrue(bounds["it_is_not_a_coverage_claim"].strip())
        self.assertTrue(bounds["it_is_not_an_independent_verification"].strip())
        self.assertTrue(bounds["it_is_not_independence_from_a_partner"].strip())

    def test_level_0_is_named_an_absence(self) -> None:
        self.assertIn("ABSENCE", self.record["evidence_levels"]["LEVEL_0"].upper())


class TestOperationalA8(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(OPERATIONAL)

    def test_there_are_exactly_eleven_questions_numbered_in_order(self) -> None:
        questions = self.record["eleven_questions"]
        self.assertEqual(len(questions), 11)
        self.assertEqual([q["n"] for q in questions], list(range(1, 12)))

    def test_the_tally_matches_the_questions(self) -> None:
        questions = self.record["eleven_questions"]
        tally = self.record["tally"]
        for key, state in (
            ("answered", "ANSWERED"),
            ("partially_answered", "PARTIALLY_ANSWERED"),
            ("not_answered", "NOT_ANSWERED"),
        ):
            self.assertEqual(tally[key], sum(1 for q in questions if q["status"] == state), key)
        self.assertEqual(
            tally["answered"] + tally["partially_answered"] + tally["not_answered"],
            tally["total"],
        )

    def test_a8_does_not_pass_while_a_question_is_unanswered(self) -> None:
        verdict = self.record["gate_a8_verdict"]["verdict"]
        if self.record["tally"]["not_answered"]:
            self.assertNotIn(verdict, QUALIFYING)

    def test_a8_says_why_it_is_not_a_fail(self) -> None:
        self.assertTrue(self.record["gate_a8_verdict"]["why_not_FAIL"].strip())

    def test_every_answered_question_names_its_document(self) -> None:
        for q in self.record["eleven_questions"]:
            if q["status"] != "NOT_ANSWERED":
                self.assertTrue(q["source_url"].strip(), q["n"])

    def test_sampling_is_unanswered_and_says_why_that_matters(self) -> None:
        sampling = next(
            q for q in self.record["eleven_questions"] if q["question"].startswith("SAMPLING")
        )
        self.assertEqual(sampling["status"], "NOT_ANSWERED")
        self.assertIn("SAMPLING_IS_LOAD_BEARING", sampling["why_this_matters"])

    def test_no_reliability_value_was_assigned(self) -> None:
        gate = self.record["what_this_gate_is_and_is_not"]
        self.assertTrue(gate["no_value_assigned"])
        self.assertEqual(gate["reliability_assessments_created"], 0)

    def test_the_default_surface_is_named_as_the_rejected_temporal_object(self) -> None:
        bound = self.record["a2_bound_discovered_this_mission"]
        self.assertIn("MAINTAINED_CURRENT_STATE_LAST_CHANGE", json.dumps(bound))
        self.assertTrue(bound["does_a2_still_pass"])
        self.assertTrue(bound["the_bound_that_must_be_carried"].strip())

    def test_port_22_inclusion_advanced_on_mission_1_60(self) -> None:
        coverage = next(
            q for q in self.record["eleven_questions"] if q["question"].startswith("PORT COVERAGE")
        )
        self.assertEqual(coverage["status"], "ANSWERED")
        self.assertTrue(coverage["advance_on_mission_1_60"])


class TestVantage(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(VANTAGE)

    def test_vantage_moved_from_not_established_to_not_documented(self) -> None:
        cls = self.record["anchor_classification"]
        self.assertEqual(cls["verdict"], "VANTAGE_NOT_DOCUMENTED")
        self.assertEqual(cls["previous_verdict"], "VANTAGE_NOT_ESTABLISHED")
        self.assertTrue(cls["moved"])

    def test_not_documented_means_somebody_looked(self) -> None:
        cls = self.record["anchor_classification"]
        self.assertGreaterEqual(len(cls["documents_consulted"]), 2)
        self.assertTrue(cls["record_side_check"].strip())

    def test_the_trap_vantage_would_recreate_is_named(self) -> None:
        why = self.record["why_vantage_is_asked_before_pairing"]
        self.assertIn("FRAME_INSIDE_THE_DEFINITION", json.dumps(why))


class TestPortWindow(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(PORTWINDOW)

    def test_current_inclusion_and_window_addressability_are_two_answers(self) -> None:
        verdict = self.record["verdict"]
        self.assertEqual(verdict["current_inclusion_of_port_22"], "ESTABLISHED")
        self.assertEqual(verdict["window_addressability_of_port_22"], "PORT_22_NOT_ESTABLISHED")
        self.assertTrue(verdict["these_are_two_answers_and_not_one"].strip())

    def test_no_recorded_removals_is_not_read_as_a_guarantee(self) -> None:
        removals = self.record["findings"]["removals"]
        self.assertEqual(removals["status"], "NONE_RECORDED")
        self.assertTrue(removals["what_this_is_not"].strip())

    def test_a_dated_size_is_not_a_dated_membership(self) -> None:
        self.assertEqual(self.record["findings"]["dated_expansion_record"]["status"], "PARTIAL")

    def test_the_route_is_not_blocked_and_carries_a_bound(self) -> None:
        cost = self.record["what_this_costs_the_route"]
        self.assertFalse(cost["does_it_block_a_threshold"])
        self.assertTrue(cost["the_bound_that_must_be_carried"].strip())


class TestPartners(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(PARTNERS)

    def test_the_partner_set_is_the_frozen_three(self) -> None:
        self.assertEqual(tuple(p["name"] for p in self.record["partners"]), MISSION_1_60_PARTNERS)

    def test_every_partner_had_its_documentation_recovered(self) -> None:
        for entry in self.record["partners"]:
            self.assertEqual(entry["b6_previous"], "DOCUMENTATION_NOT_RETRIEVABLE")
            self.assertEqual(entry["b6_now"], "RETRIEVED")
            self.assertTrue(entry["working_paths"])
            self.assertTrue(entry["why_the_earlier_path_failed"].strip())

    def test_every_partner_was_assessed_on_all_six_slots(self) -> None:
        for entry in self.record["partners"]:
            for slot in ("B1", "B2", "B3", "B4", "B5", "B6"):
                self.assertIn(slot, entry["package"], entry["name"])
                self.assertTrue(entry["package"][slot]["status"].strip())

    def test_no_partner_is_qualified_ranked_or_selected(self) -> None:
        verdict = self.record["verdict"]
        self.assertEqual(verdict["partners_qualified"], 0)
        self.assertEqual(verdict["partners_ranked"], 0)
        self.assertEqual(verdict["partners_disqualified"], 0)
        self.assertIsNone(verdict["pair_selected"])

    def test_no_partner_reached_level_2_lineage(self) -> None:
        for entry in self.record["partners"]:
            for slot in entry["package"].values():
                self.assertNotEqual(slot.get("lineage_level"), "LEVEL_2", entry["name"])

    def test_an_open_source_list_is_recorded_as_level_1(self) -> None:
        """The contrast that pays for the new registry rule."""
        shadow = next(p for p in self.record["partners"] if p["name"].startswith("The Shadow"))
        self.assertEqual(shadow["package"]["B1"]["lineage_level"], "LEVEL_1")
        self.assertTrue(shadow["package"]["B1"]["why_not_LEVEL_2"].strip())

    def test_the_declined_preference_is_named(self) -> None:
        self.assertTrue(self.record["why_no_preference_is_expressed"]["the_temptation"].strip())


class TestClosure(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(CLOSURE)

    def test_the_outcome_names_both_halves(self) -> None:
        self.assertEqual(
            self.record["primary_outcome"], "ANCHOR_LINEAGE_CONFIRMED_OPERATIONAL_QUESTIONS_REMAIN"
        )
        self.assertEqual(self.record["secondary_outcome"], "PARTNER_DOCUMENTATION_RECOVERED")

    def test_the_gate_table_counts_match_its_verdicts(self) -> None:
        table = self.record["anchor_gate_table"]
        self.assertEqual(
            table["pass_count"], sum(1 for g in GATES if table[g]["verdict"] == "PASS")
        )
        self.assertEqual(
            table["partial_count"], sum(1 for g in GATES if table[g]["verdict"] == "PARTIAL")
        )

    def test_only_a8_blocks_now(self) -> None:
        table = self.record["anchor_gate_table"]
        self.assertEqual(table["which_gates_block"], ["A8"])
        self.assertEqual(table["blocking_gates_previously"], ["A7", "A8"])

    def test_the_apparatus_still_does_not_individually_qualify(self) -> None:
        table = self.record["anchor_gate_table"]
        self.assertFalse(table["individually_qualifies"])
        self.assertTrue(table["why_not"].strip())

    def test_the_gate_table_agrees_with_the_gate_records(self) -> None:
        table = self.record["anchor_gate_table"]
        self.assertEqual(table["A7"]["verdict"], _load(LINEAGE)["gate_a7_verdict"]["verdict"])
        self.assertEqual(table["A8"]["verdict"], _load(OPERATIONAL)["gate_a8_verdict"]["verdict"])

    def test_a2_carries_its_non_default_bound(self) -> None:
        self.assertTrue(self.record["anchor_gate_table"]["A2"]["bound_added"].strip())

    def test_no_pair_was_selected_and_no_pair_gate_evaluated(self) -> None:
        self.assertIsNone(self.record["selected_pair"])
        self.assertFalse(self.record["pair_gates_evaluated"])

    def test_every_stop_condition_holds(self) -> None:
        for name, value in self.record["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertFalse(value, name)

    def test_the_enquiry_hash_matches_the_rendered_document(self) -> None:
        digest = hashlib.sha256(ENQUIRY_MD.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        self.assertEqual(self.record["drafted_enquiry"]["sha256"], digest)

    def test_the_approval_string_names_the_hash(self) -> None:
        drafted = self.record["drafted_enquiry"]
        self.assertEqual(
            drafted["approval_string"], f"APPROVE MISSION 1.61 ENQUIRY {drafted['sha256']}"
        )
        self.assertFalse(drafted["sent"])


class TestEnquiry(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(ENQUIRY)

    def test_the_enquiry_is_drafted_and_not_sent(self) -> None:
        self.assertEqual(self.record["status"], "AWAITING_OPERATOR_APPROVAL")
        self.assertFalse(self.record["delivery"]["sent"])
        self.assertIsNone(self.record["delivery"]["sent_at"])

    def test_no_recipient_address_was_invented(self) -> None:
        self.assertEqual(self.record["delivery"]["recipient_address"], "TO_BE_SUPPLIED_BY_OPERATOR")

    def test_no_approval_has_been_recorded(self) -> None:
        self.assertFalse(self.record["operator_approval"]["approval_recorded"])

    def test_the_enquiry_asks_only_about_questions_the_documents_did_not_answer(self) -> None:
        answered = {
            q["question"].split(".")[0].strip().upper()
            for q in _load(OPERATIONAL)["eleven_questions"]
            if q["status"] == "ANSWERED"
        }
        for q in self.record["questions"]:
            self.assertNotIn(q["topic"].strip().upper(), answered, q["n"])

    def test_the_enquiry_body_requests_no_data_access_or_price(self) -> None:
        body = " ".join(
            [self.record["subject"], self.record["preamble"], self.record["closing"]]
            + [q["question"] + " " + q["why_we_ask"] for q in self.record["questions"]]
        ).lower()
        for ask in ("how many hosts", "free trial", "pricing", "api key", "send us a sample"):
            self.assertNotIn(ask, body, ask)

    def test_a_drafted_enquiry_is_not_evidence(self) -> None:
        self.assertTrue(self.record["what_this_enquiry_is_not"]["not_evidence"].strip())


class TestRegistry(unittest.TestCase):
    def test_the_registry_carries_both_new_requirements(self) -> None:
        names = {item["name"] for item in _load(CONTRACT)["requirement_registry"]["requirements"]}
        self.assertIn("ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE", names)
        self.assertIn("LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS", names)

    def test_every_registry_entry_names_the_mission_that_paid_for_it(self) -> None:
        for item in _load(CONTRACT)["requirement_registry"]["requirements"]:
            self.assertTrue(item["from"].strip(), item["name"])
            self.assertTrue(item["rule"].strip(), item["name"])

    def test_the_nine_earlier_requirements_survive(self) -> None:
        names = {item["name"] for item in _load(CONTRACT)["requirement_registry"]["requirements"]}
        for earlier in (
            "SOURCE_EXCLUSIVE_METRIC",
            "RELIABILITY_REVIEWABILITY",
            "FRAME_INSIDE_THE_DEFINITION",
            "AFFIRMATIVE_LINEAGE_REQUIRED",
            "PRODUCT_RELEVANCE",
            "READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT",
            "OBSERVATION_ADDRESSABLE_EXPOSURE",
            "THE_TEMPORAL_OBJECT_TEST",
            "SAMPLING_IS_LOAD_BEARING",
        ):
            self.assertIn(earlier, names)


class TestNoOverclaims(unittest.TestCase):
    """A count of addresses answering on a port is not a market statement."""

    RECORDS = (BASELINE, LINEAGE, OPERATIONAL, VANTAGE, PORTWINDOW, PARTNERS, CLOSURE, ENQUIRY)
    FORBIDDEN = ("installation", "customer", "subscription", "revenue", "adoption", "demand")

    def test_no_record_uses_market_vocabulary(self) -> None:
        for path in self.RECORDS:
            for sentence in _prose(_load(path)):
                tokens = re.findall(r"[a-z0-9]+", sentence.lower())
                for term in self.FORBIDDEN:
                    self.assertNotIn(term, tokens, f"{path.name}: {sentence[:90]}")

    def test_mission_1_60_records_are_not_rewritten(self) -> None:
        """The historical record still says what it found, and is not edited to agree."""
        selection = _load(DATA / "observation-addressable-scanner-pair-selection-v1.json")
        self.assertEqual(
            selection["primary_outcome"], "APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED"
        )
        anchor = _load(DATA / "anchor-scanner-requalification-v1.json")
        self.assertEqual(anchor["which_gates_block"], ["A7", "A8"])


if __name__ == "__main__":
    unittest.main()
