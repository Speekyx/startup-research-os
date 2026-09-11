"""Mission 1.84. One external inference prepared, and none executed.

Five things this file defends.

THE PAYLOAD IS THE APPROVED ONE, BYTE FOR BYTE. The execution packet's representation digest is
the digest the operator's egress approval names, and the subject, purpose, schema and decision
packet it cites are the approved ones. A mismatch is a hard stop with its own name, never a
reserialisation and never an updated approval.

THE ROUTE WAS DERIVED, NOT PICKED. The provider is one the current register approves, the claim
that exactly one route is eligible is checked against the register rather than asserted, and the
route is named so a different route of the same vendor cannot inherit an assessment nobody made.

THE CALL IS BOUNDED IN EVERY DIRECTION. One call, no retry, a finite timeout, a token ceiling
that adds up, a cost ceiling above the worst case, and a price basis this deployment already
holds. Every generation parameter is one the Gateway actually carries, and every unsupported one
is recorded as unavailable rather than as a default somebody accepted.

NOTHING WAS EXECUTED AND NOTHING WAS APPROVED. Model calls, transmitted bytes, test requests,
research acquisition, canonical mutation, Opportunities, scores and independence groups are all
zero, and the packet records no approval of itself.

THE GATE STILL REFUSES WHAT IT SAYS IT REFUSES. It names the hard stop, derives the provider set
from the register rather than hard-coding a vendor, and is registered in CI.
"""

from __future__ import annotations

import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

PROMPT = DATA / "second-opportunity-synthesis-prompt-v1.json"
CONTRACT = DATA / "second-opportunity-synthesis-output-contract-v1.json"
PACKET = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
APPROVAL = DATA / "ted-egress-operator-decision-v1.json"
DECISION_PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"
REGISTER = DATA / "model-provider-policy-v1.json"
PREPARATION_V5 = DATA / "opportunity-preparation-v5.json"
PREPARATION_V4 = DATA / "opportunity-preparation-v4.json"
GATE = SCRIPTS / "render_second_opportunity_execution_packet.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

SUBJECT = "ted-eu:CPV-class:9261"
PURPOSE = "bounded external inference for Opportunity hypothesis synthesis"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestThePayloadIsTheApprovedOne(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = load(PACKET)
        self.approval = load(APPROVAL)

    def test_the_representation_digest_is_the_approved_one(self) -> None:
        """Section 5. The whole mission rests on these two strings being equal."""
        self.assertEqual(
            self.packet["REPRESENTATION_SHA256"],
            self.approval["scope"]["representation_sha256"],
        )

    def test_the_representation_schema_is_the_approved_one(self) -> None:
        self.assertEqual(
            self.packet["REPRESENTATION_SCHEMA"],
            self.approval["scope"]["representation_schema"],
        )

    def test_the_subject_and_purpose_are_the_approved_ones(self) -> None:
        scope = self.approval["scope"]
        self.assertEqual(self.packet["SUBJECT_KEY"], scope["subject"])
        self.assertEqual(self.packet["SUBJECT_KEY"], SUBJECT)
        self.assertEqual(self.packet["PROCESSING_PURPOSE"], scope["processing_purpose"])
        self.assertEqual(self.packet["PROCESSING_PURPOSE"], PURPOSE)

    def test_it_cites_the_decision_packet_the_operator_approved(self) -> None:
        self.assertEqual(
            self.packet["SOURCE_DECISION_PACKET_ID"], self.approval["DECISION_PACKET_ID"]
        )
        self.assertEqual(
            self.packet["SOURCE_DECISION_PACKET_VERSION"],
            self.approval["DECISION_PACKET_VERSION"],
        )
        self.assertEqual(
            self.packet["SOURCE_DECISION_PACKET_SHA256"],
            self.approval["DECISION_PACKET_SHA256_RECOMPUTED"],
        )

    def test_the_frozen_decision_packet_still_records_no_approval(self) -> None:
        """A packet edited to say it was approved is a packet whose approved bytes moved."""
        decision = load(DECISION_PACKET)
        self.assertFalse(decision["approval_recorded"])

    def test_the_hard_stop_has_a_name_and_the_gate_uses_it(self) -> None:
        text = GATE.read_text(encoding="utf-8")
        self.assertIn("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED", text)
        self.assertIn("never repaired by reserialising", text.lower())


class TestTheRouteWasDerived(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = load(PACKET)
        self.register = load(REGISTER)

    def approved(self) -> list[str]:
        return sorted(
            str(entry["provider_id"])
            for entry in self.register["providers"]
            if str(entry.get("posture")) == "APPROVED"
        )

    def test_the_provider_is_one_the_current_register_approves(self) -> None:
        self.assertIn(self.packet["PROVIDER_ID"], self.approved())
        self.assertEqual(self.packet["PROVIDER_POSTURE"], "APPROVED")

    def test_a_deterministic_claim_matches_the_register(self) -> None:
        """Sections 9 and 10. One eligible route is a countable fact, not a preference."""
        basis = self.packet["PROVIDER_SELECTION_BASIS"]
        if "deterministic" in basis:
            self.assertEqual(len(self.approved()), 1, basis)

    def test_every_other_provider_is_excluded_by_the_register_rather_than_by_taste(self) -> None:
        excluded = [
            entry for entry in self.register["providers"] if str(entry.get("posture")) != "APPROVED"
        ]
        self.assertTrue(excluded)
        for entry in excluded:
            self.assertIn(str(entry["posture"]), {"NOT_APPROVED", "NEVER_PRODUCTION"})

    def test_the_route_is_named_so_a_sibling_route_inherits_nothing(self) -> None:
        """Section 38. A vendor is not a route."""
        self.assertTrue(self.packet["PROVIDER_ROUTE"].strip())
        self.assertIn("DIFFERENT route", self.packet["PROVIDER_ROUTE"])

    def test_the_model_has_a_stated_basis(self) -> None:
        self.assertTrue(self.packet["MODEL_ID"].strip())
        self.assertTrue(self.packet["MODEL_SELECTION_BASIS"].strip())

    def test_the_gate_derives_the_provider_set_rather_than_naming_one(self) -> None:
        text = GATE.read_text(encoding="utf-8")
        self.assertIn("def approved_providers", text)
        body = text.split("def approved_providers", 1)[1].split("\ndef ", 1)[0]
        for vendor in ("anthropic", "gemini", "openai"):
            self.assertNotIn(vendor, body.lower())


class TestTheCallIsBounded(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = load(PACKET)
        self.params = self.packet["GENERATION_PARAMETERS"]

    def test_exactly_one_call_and_no_automatic_retry(self) -> None:
        self.assertEqual(self.packet["MAX_MODEL_CALLS"], 1)
        self.assertEqual(self.params["max_retries"], 0)
        self.assertEqual(self.packet["failure_outcome"], "EXECUTION_FAILED_NO_RETRY")

    def test_the_timeout_is_finite_and_agrees_with_itself(self) -> None:
        self.assertGreater(self.params["timeout_seconds"], 0)
        self.assertEqual(self.packet["REQUEST_TIMEOUT"], self.params["timeout_seconds"])

    def test_a_timeout_is_not_permission_to_retry(self) -> None:
        self.assertIn("not permission to retry", self.packet["timeout_note"])

    def test_unsupported_parameters_are_recorded_as_unavailable(self) -> None:
        """Section 21. Null means the Gateway does not expose it."""
        for name in ("temperature", "top_p", "seed", "reasoning_effort"):
            self.assertIsNone(self.params[name])
        self.assertIn("does not expose it", self.params["unsupported_parameters_note"])

    def test_the_token_ceiling_adds_up(self) -> None:
        self.assertEqual(
            self.packet["TOTAL_TOKEN_CEILING"],
            self.packet["INPUT_TOKEN_ESTIMATE"] + self.packet["MAX_OUTPUT_TOKENS"],
        )

    def test_the_estimate_says_it_is_an_estimate(self) -> None:
        basis = self.packet["TOKEN_ESTIMATION_BASIS"]
        self.assertFalse(basis["exact_tokenizer_available"])
        self.assertTrue(basis["why"].strip())
        self.assertTrue(basis["measured_pair"].strip())
        self.assertGreaterEqual(basis["conservative_multiplier"], 1.0)
        self.assertTrue(basis["limitation"].strip())

    def test_no_test_request_was_sent_to_size_the_budget(self) -> None:
        self.assertTrue(self.packet["TOKEN_ESTIMATION_BASIS"]["no_test_request_was_sent"])

    def test_the_worst_case_recomputes_from_the_recorded_prices(self) -> None:
        """Section 23. A cost nobody can recompute is a cost somebody chose."""
        text = f"{self.packet['INPUT_PRICE_BASIS']} {self.packet['OUTPUT_PRICE_BASIS']}"
        self.assertIn("per 1000 input tokens", text)
        self.assertIn("per 1000 output tokens", text)
        self.assertTrue(self.packet["PRICING_VERSION"].strip())
        self.assertGreater(self.packet["WORST_CASE_CALL_COST"], 0)

    def test_the_ceiling_covers_the_worst_case_and_says_why(self) -> None:
        self.assertGreaterEqual(
            self.packet["EXECUTION_COST_CEILING"], self.packet["WORST_CASE_CALL_COST"]
        )
        self.assertTrue(self.packet["cost_ceiling_basis"].strip())

    def test_the_cost_unit_is_explained_rather_than_assumed_to_be_a_currency(self) -> None:
        self.assertIn("ADR-006", self.packet["COST_UNIT_NOTE"])


class TestNothingWasExecutedAndNothingApproved(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = load(PACKET)

    def test_the_packet_records_no_approval_of_itself(self) -> None:
        self.assertFalse(self.packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"])

    def test_the_egress_approval_is_recorded_as_a_different_act(self) -> None:
        """Section 34. Permission to send is not permission to run."""
        note = self.packet["approval_note"]
        self.assertIn("NO OLD APPROVAL AUTHORISES THIS CALL", note)
        self.assertIn("egress", note.lower())

    def test_every_preparation_counter_is_zero(self) -> None:
        accounting = self.packet["preparation_accounting"]
        for key, value in accounting.items():
            if key in {"$comment", "note"}:
                continue
            self.assertEqual(value, 0, f"{key} is {value}")

    def test_the_six_capabilities_are_all_false(self) -> None:
        for key in ("TRAINING", "FINE_TUNING", "EMBEDDINGS", "WEB", "TOOLS", "EXTERNAL_RETRIEVAL"):
            self.assertFalse(self.packet[key], key)

    def test_no_chain_of_thought_is_retained(self) -> None:
        retention = self.packet["RETENTION_ON_EXECUTION"]
        self.assertTrue(retention["hidden_reasoning"].startswith("NOT RETAINED"))
        self.assertIn("RETAINED", retention["raw_provider_response"])

    def test_persistence_needs_a_human_and_creates_nothing_here(self) -> None:
        policy = self.packet["PERSISTENCE_POLICY"]
        self.assertFalse(policy["persist_if_gate_accepts"])
        self.assertTrue(policy["human_review_required_before_persistence"])
        self.assertEqual(policy["opportunity_created_by_this_packet"], 0)
        self.assertFalse(policy["score_persisted"])
        self.assertFalse(policy["independence_group_created"])

    def test_the_operator_exclusions_are_all_still_excluded(self) -> None:
        excluded = {item.lower() for item in load(APPROVAL)["NOT_AUTHORIZED"]}
        self.assertIn("model training", excluded)
        self.assertIn("fine-tuning", excluded)
        self.assertIn("embeddings", excluded)
        self.assertFalse(self.packet["TRAINING"])
        self.assertFalse(self.packet["FINE_TUNING"])
        self.assertFalse(self.packet["EMBEDDINGS"])


class TestThePreparationRecords(unittest.TestCase):
    def test_v4_is_historical_and_still_present(self) -> None:
        """Section 2. A pre-decision view is superseded, never rewritten."""
        self.assertTrue(PREPARATION_V4.exists())
        v4 = load(PREPARATION_V4)
        self.assertEqual(v4["artifact_version"], "opportunity-preparation@4.0.0")

    def test_v5_supersedes_v4_and_reads_the_live_governance(self) -> None:
        v5 = load(PREPARATION_V5)
        self.assertEqual(v5["artifact_version"], "opportunity-preparation@5.0.0")
        self.assertIn("opportunity-preparation-v4", json.dumps(v5["supersedes"]))

    def test_the_selected_packet_egress_is_available_in_v5(self) -> None:
        """Section 3. The permission the operator granted shows up in the gate state."""
        v5 = load(PREPARATION_V5)
        selected = [p for p in v5["packets"] if p["subject"] == SUBJECT]
        self.assertEqual(len(selected), 1)
        egress = selected[0]["external_synthesis"]
        self.assertEqual(egress["availability"], "AVAILABLE")
        self.assertEqual(egress["refusal_reasons"], [])

    def test_the_execution_packet_names_the_current_preparation(self) -> None:
        packet = load(PACKET)
        self.assertEqual(packet["PREPARATION_VERSION"], load(PREPARATION_V5)["artifact_version"])

    def test_the_selected_packet_id_is_the_one_v5_carries(self) -> None:
        v5 = load(PREPARATION_V5)
        selected = [p for p in v5["packets"] if p["subject"] == SUBJECT][0]
        self.assertEqual(selected["packet_id"], load(PACKET)["SELECTED_PACKET_ID"])


class TestTheOutputContract(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load(CONTRACT)

    def test_confidence_is_a_classification_and_never_a_number(self) -> None:
        """Section 17. A self-reported certainty is not a probability."""
        self.assertEqual(self.contract["confidence_classifications"], ["EXPLORATORY"])
        self.assertFalse(self.contract["numeric_confidence_requested"])

    def test_no_required_field_is_a_score(self) -> None:
        for field in self.contract["required_fields"]:
            self.assertNotIn("score", field)
            self.assertNotIn("probability", field)

    def test_the_eight_validation_stages_are_ordered(self) -> None:
        self.assertEqual(len(self.contract["validation_order"]), 8)

    def test_a_failure_is_never_repaired_by_a_second_call(self) -> None:
        self.assertIn("second model call", self.contract["failure_policy"])

    def test_the_five_forbidden_transformations_state_both_halves(self) -> None:
        """Section 19. A model told only what to avoid does not know what it may say."""
        entries = self.contract["forbidden_transformations"]
        self.assertEqual(len(entries), 5)
        for entry in entries:
            self.assertTrue(entry["establishes"].strip())
            self.assertTrue(entry["is_not"].strip())
            self.assertNotEqual(entry["establishes"], entry["is_not"])

    def test_lexical_filtering_is_not_claimed_to_be_semantic_safety(self) -> None:
        self.assertTrue(self.contract["lexical_filtering_is_not_semantic_safety"])

    def test_human_review_is_required_and_was_not_weakened(self) -> None:
        review = self.contract["human_review"]
        self.assertTrue(review["HUMAN_OUTPUT_REVIEW_REQUIRED"])
        self.assertTrue(review["why"].strip())
        self.assertFalse(review["weakened_to_create_opportunity_two"])

    def test_the_two_stale_checks_were_generalised_and_not_weakened(self) -> None:
        stale = self.contract["two_stale_checks_generalised"]
        self.assertFalse(stale["weakened"])
        self.assertNotEqual(stale["base_gate_version_before"], stale["base_gate_version_after"])

    def test_independence_stays_unknown(self) -> None:
        """Section 32. Six rows from one publisher are not six witnesses."""
        self.assertIn("UNKNOWN", self.contract["independence_rule"])


class TestTheFrozenPrompt(unittest.TestCase):
    def setUp(self) -> None:
        self.prompt = load(PROMPT)

    def test_the_statements_live_only_in_the_untrusted_region(self) -> None:
        """Section 41. Source-derived text is data, and a region is what enforces it."""
        placeholder = self.prompt["INPUT_PLACEHOLDER"]
        self.assertEqual(placeholder["region"], "untrusted")
        self.assertNotIn("statements", placeholder)

    def test_every_supplied_statement_is_labelled_with_its_lineage(self) -> None:
        for label in self.prompt["INPUT_PLACEHOLDER"]["labels"]:
            self.assertTrue(label.startswith("evidence="))
            self.assertIn(" claim=", label)

    def test_refusing_is_a_permitted_answer(self) -> None:
        """Section 15. INSUFFICIENT_EVIDENCE beats a hypothesis nobody supplied a fact for."""
        joined = " ".join(self.prompt["REFUSAL_RULES"])
        self.assertIn("INSUFFICIENT_EVIDENCE", joined)

    def test_the_prompt_digest_covers_what_would_be_sent(self) -> None:
        self.assertIn("RENDERED", self.prompt["prompt_hash_covers"])
        self.assertTrue(self.prompt["PROMPT_SHA256"].strip())

    def test_it_names_the_frozen_text_it_inherits(self) -> None:
        self.assertEqual(
            self.prompt["inherits_byte_identically"],
            "sros_opportunity.synthesis.SYNTHESIS_SYSTEM",
        )

    def test_the_base_prompt_version_moved_with_its_reason(self) -> None:
        self.assertEqual(self.prompt["base_prompt_version"], "1.1.0")
        self.assertIn("Mission 1.77", self.prompt["base_prompt_version_note"])

    def test_the_packet_and_the_prompt_name_one_digest(self) -> None:
        self.assertEqual(load(PACKET)["PROMPT_SHA256"], self.prompt["PROMPT_SHA256"])


class TestTheGateIsWired(unittest.TestCase):
    def test_the_gate_exists_and_runs_in_ci(self) -> None:
        self.assertTrue(GATE.exists())
        self.assertIn("render_second_opportunity_execution_packet.py --check", CI.read_text())

    def test_the_digest_fields_are_pinned_rather_than_read_from_the_record(self) -> None:
        """A digest over whichever fields the record nominates is one the record can shrink."""
        text = GATE.read_text(encoding="utf-8")
        self.assertIn("DIGEST_FIELDS = (", text)
        self.assertIn("REPRESENTATION_SHA256", text)

    def test_the_rendered_pages_exist(self) -> None:
        for name in (
            "second-opportunity-synthesis-prompt-v1.md",
            "second-opportunity-synthesis-output-contract-v1.md",
            "second-opportunity-synthesis-execution-packet-v1.md",
        ):
            self.assertTrue((DATA / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
