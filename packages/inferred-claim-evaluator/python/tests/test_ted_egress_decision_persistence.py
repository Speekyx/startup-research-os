"""Mission 1.83.1. The operator approved, and this is what the registry did about it.

Four things this file defends.

THE APPROVAL NAMES THIS PACKET AND NOTHING ELSE. The digest is recomputed from the packet's own
bound fields and equals both the value the operator cited and the value the record kept. The
frozen packet is byte-identical, its own approval flag still reads false, and the acceptance text
is the operator's verbatim, hashed, naming the packet, the decision and the subject.

THE REVIEW WAS APPENDED, NOT EDITED. v3 keeps every assessment, condition, open question and
evidence row. v4 carries them forward, moves exactly one assessment, adds the eight adopted
conditions verbatim, and adds a SEPARATE human condition rather than widening the existing one.

THE CONFIGURATION WAS RE-POINTED BY DOING THE RE-CHECK. The three capability conditions are
byte-identical between the two versions, and the one condition the successor adds is one no
configuration can answer.

A PERMISSION IS NOT AN ACT. Every gate now passes and zero bytes left the machine. Training,
fine-tuning, embeddings, redistribution and customer access each keep the state they had, and no
canonical research row moved.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

APPROVAL = DATA / "ted-egress-operator-decision-v1.json"
PERSISTENCE = DATA / "ted-egress-decision-persistence-v1.json"
PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"
EGRESS_REVIEW = DATA / "ted-selected-candidate-egress-review-v1.json"
CATALOG = DATA / "source-catalog-v1.json"
COMPLIANCE = DATA / "source-compliance-v1.json"
GATE = SCRIPTS / "render_ted_egress_decision_persistence.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

SUBJECT = "ted-eu:CPV-class:9261"
PROFILE = "local-private-research-v1"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_ted_egress_decision_persistence", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reviews() -> dict[int, dict]:
    source = next(s for s in load(CATALOG)["sources"] if s["source_id"] == "ted-eu")
    return {
        r["review_version"]: r for r in source["reviews"] if r["assessed_use_profile"] == PROFILE
    }


class TestTheApproval(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)
        self.packet = load(PACKET)

    def test_the_digest_was_recomputed_and_both_values_are_kept(self):
        module = gate()
        recomputed = module._egress_gate().packet_digest(self.packet)
        self.assertEqual(self.approval["DECISION_PACKET_SHA256_RECOMPUTED"], recomputed)
        self.assertEqual(self.approval["DECISION_PACKET_SHA256_STATED"], recomputed)
        self.assertTrue(self.approval["DECISION_PACKET_DIGEST_MATCHES"])
        self.assertEqual(self.packet["DECISION_PACKET_SHA256"], recomputed)

    def test_the_frozen_packet_still_records_no_approval(self):
        self.assertFalse(self.packet["approval_recorded"])
        self.assertFalse(self.approval["packet_edited_by_this_approval"])
        self.assertEqual(
            self.approval["DECISION_PACKET_FILE_SHA256"],
            hashlib.sha256(PACKET.read_bytes()).hexdigest(),
        )

    def test_the_acceptance_is_the_operators_words_and_hashes_to_its_digest(self):
        text = self.approval["ACCEPTANCE_TEXT"]
        self.assertEqual(
            self.approval["ACCEPTANCE_SHA256"],
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )
        for needle in (
            "TED-EGRESS-OPPSYNTH-V1",
            self.packet["DECISION_PACKET_SHA256"],
            "PERMIT_WITH_EXACT_CONDITIONS",
            SUBJECT,
            self.packet["REPRESENTATION_SHA256"],
        ):
            self.assertIn(needle, text)

    def test_the_decision_is_a_named_persons(self):
        self.assertEqual(self.approval["DECISION"], "PERMIT_WITH_EXACT_CONDITIONS")
        self.assertEqual(self.approval["decided_by_kind"], "NAMED_LOCAL_OPERATOR")
        self.assertTrue(str(self.approval["decided_by"]).strip())

    def test_the_eight_conditions_were_adopted_verbatim(self):
        self.assertEqual(self.approval["CONDITIONS_ADOPTED"], self.packet["CONDITIONS"])
        self.assertEqual(self.approval["conditions_adopted_count"], 8)

    def test_the_approval_is_spent_by_its_use(self):
        self.assertTrue(self.approval["spent"])
        self.assertIn("digest", self.approval["spent_note"])

    def test_it_names_ten_things_it_does_not_authorise(self):
        module = gate()
        self.assertEqual(set(self.approval["NOT_AUTHORIZED"]), set(module.NOT_AUTHORIZED))
        self.assertEqual(len(self.approval["NOT_AUTHORIZED"]), 10)


class TestTheAppend(unittest.TestCase):
    def setUp(self):
        self.reviews = reviews()
        self.record = load(PERSISTENCE)

    def test_v3_survives_and_v4_is_current(self):
        self.assertIn(3, self.reviews)
        self.assertIn(4, self.reviews)
        self.assertFalse(self.record["append_not_edit"]["v3_content_changed"])

    def test_v3_never_declared_the_activity_and_v4_does(self):
        self.assertNotIn("external_model_transmission", self.reviews[3])
        self.assertEqual(
            self.reviews[4]["external_model_transmission"], "PERMITTED_WITH_CONDITIONS"
        )

    def test_exactly_one_assessment_moved(self):
        v3, v4 = self.reviews[3], self.reviews[4]
        narrative = (
            "review_version",
            "reviewed_by",
            "reviewed_at",
            "conditions",
            "required_conditions",
            "open_questions",
            "review_notes",
            "evidence",
        )
        moved = [f for f in v3 if f not in narrative and v3[f] != v4.get(f)]
        self.assertEqual(moved, [])

    def test_v3s_conditions_are_carried_forward_verbatim(self):
        v3, v4 = self.reviews[3], self.reviews[4]
        self.assertEqual(v3["conditions"], v4["conditions"][: len(v3["conditions"])])
        self.assertEqual(v3["evidence"], v4["evidence"])

    def test_the_eight_adopted_conditions_reached_the_successor(self):
        joined = " ".join(self.reviews[4]["conditions"])
        for condition in load(PACKET)["CONDITIONS"]:
            self.assertIn(condition, joined)

    def test_the_new_condition_is_separate_rather_than_a_widening(self):
        v3_keys = {c["key"] for c in self.reviews[3]["required_conditions"]}
        v4_keys = {c["key"] for c in self.reviews[4]["required_conditions"]}
        self.assertTrue(v3_keys <= v4_keys)
        self.assertEqual(v4_keys - v3_keys, {"ted-external-model-transmission-accepted"})
        added = next(
            c
            for c in self.reviews[4]["required_conditions"]
            if c["key"] == "ted-external-model-transmission-accepted"
        )
        self.assertEqual(added["verification"], "HUMAN_CONFIRMATION")
        self.assertIn("BOUNDED QUERIES", added["description"])
        self.assertIn(
            "f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577", added["description"]
        )

    def test_the_successor_records_what_the_permission_does_not_resolve(self):
        v3, v4 = self.reviews[3], self.reviews[4]
        self.assertGreater(len(v4["open_questions"]), len(v3["open_questions"]))
        added = " ".join(v4["open_questions"][len(v3["open_questions"]) :])
        self.assertIn("H-36A", added)
        self.assertIn("enumerates no acts", added)


class TestTheReconciliation(unittest.TestCase):
    def test_the_configuration_is_pinned_to_the_successor(self):
        entry = next(
            s
            for s in load(COMPLIANCE)["sources"]
            if s["source_id"] == "ted-eu" and s["use_profile_id"] == PROFILE
        )
        self.assertEqual(entry["review_version"], 4)
        self.assertIn("PERFORMING the re-check", entry["review_version_note"])

    def test_the_capability_conditions_are_byte_identical_across_the_versions(self):
        r = reviews()
        v3 = {c["key"]: c for c in r[3]["required_conditions"]}
        v4 = {c["key"]: c for c in r[4]["required_conditions"]}
        for key in ("ted-attribution", "ted-official-route-only", "ted-personal-data-minimisation"):
            self.assertEqual(v3[key], v4[key], key)

    def test_the_record_states_why_the_re_point_is_honest(self):
        reconciliation = load(PERSISTENCE)["compliance_reconciliation"]
        self.assertTrue(reconciliation["re_check_performed"])
        self.assertTrue(reconciliation["capability_conditions_byte_identical"])
        self.assertEqual(reconciliation["required_conditions_removed"], [])
        self.assertEqual(reconciliation["added_condition_verification_kind"], "HUMAN_CONFIRMATION")


class TestTheConditions(unittest.TestCase):
    def setUp(self):
        self.conditions = load(PERSISTENCE)["conditions_after_persistence"]

    def test_every_condition_the_successor_requires_is_satisfied(self):
        kinds = {c["key"]: c["verification"] for c in reviews()[4]["required_conditions"]}
        for key, kind in kinds.items():
            self.assertIn(key, self.conditions)
            self.assertEqual(self.conditions[key]["verification"], kind)
            self.assertEqual(self.conditions[key]["result"], "SATISFIED")

    def test_no_machine_answered_a_human_condition(self):
        self.assertFalse(self.conditions["machine_recorded_a_human_condition"])
        self.assertFalse(self.conditions["verifier_cleared_a_human_condition"])
        for key, entry in self.conditions.items():
            if isinstance(entry, dict) and entry.get("verification") == "HUMAN_CONFIRMATION":
                self.assertEqual(entry["verifier"], "local-operator", key)

    def test_both_orphaned_confirmations_were_re_recorded_against_the_successor(self):
        self.assertEqual(self.conditions["human_confirmations_recorded"], 2)
        versions = {
            entry["verifier_version"]
            for entry in self.conditions.values()
            if isinstance(entry, dict) and entry.get("verification") == "HUMAN_CONFIRMATION"
        }
        self.assertEqual(versions, {"ted-v4-egress-approval-v1"})

    def test_the_identifier_names_which_text_and_is_not_the_v3_one(self):
        self.assertNotIn(
            "ted-v3-official-reuse-acknowledgement-v1",
            {
                entry["verifier_version"]
                for entry in self.conditions.values()
                if isinstance(entry, dict) and entry.get("verification") == "HUMAN_CONFIRMATION"
            },
        )

    def test_two_rows_rest_on_one_statement_and_the_record_says_so(self):
        self.assertTrue(self.conditions["human_confirmations_rest_on_one_statement"])
        self.assertIn("one act", self.conditions["one_statement_note"])


class TestAPermissionIsNotAnAct(unittest.TestCase):
    def setUp(self):
        self.record = load(PERSISTENCE)

    def test_every_gate_passes_now(self):
        gates = self.record["gates_after"]
        self.assertEqual(gates["source_transmission"], "PERMITTED_WITH_CONDITIONS")
        self.assertEqual(gates["profile_egress"], "PERMITTED_TO_APPROVED_PROVIDERS")
        self.assertEqual(gates["provider_posture"], "APPROVED")
        self.assertEqual(gates["inference_authorization"], "AUTHORIZED")
        self.assertEqual(gates["eligibility_before"], "BLOCKED")
        self.assertEqual(gates["eligibility_after"], "ELIGIBLE")
        self.assertEqual(gates["packet_gate_before"], "UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS")
        self.assertEqual(gates["packet_gate_after"], "AVAILABLE")

    def test_zero_bytes_left_the_machine(self):
        self.assertEqual(self.record["gates_after"]["bytes_transmitted_to_any_external_model"], 0)
        self.assertIn("not an act", self.record["gates_after"]["packet_gate_note"])

    def test_the_representation_is_the_one_that_was_approved(self):
        verification = self.record["verification_before_writing"]
        self.assertTrue(verification["REPRESENTATION_UNCHANGED"])
        self.assertEqual(
            verification["REPRESENTATION_SHA256_APPROVED"],
            verification["REPRESENTATION_SHA256_REMEASURED"],
        )
        self.assertEqual(
            verification["REPRESENTATION_SHA256_APPROVED"],
            load(EGRESS_REVIEW)["representation"]["REPRESENTATION_SHA256"],
        )

    def test_nothing_was_widened(self):
        scope = self.record["what_was_not_authorised"]
        self.assertEqual(scope["model_training"], "NOT_ASSESSED")
        self.assertEqual(scope["fine_tuning"], "NOT_ASSESSED")
        self.assertEqual(scope["embeddings"], "NOT_ASSESSED")
        self.assertEqual(scope["public_redistribution"], "NOT_PERMITTED")
        self.assertEqual(scope["customer_facing_source_data"], "NOT_PERMITTED")
        self.assertIn("REQUIRES_REVIEW", scope["commercial_profile_state"])
        self.assertEqual(scope["widened_by_this_mission"], 0)

    def test_only_governance_rows_moved(self):
        state = self.record["canonical_state"]
        before, after = dict(state["before"]), dict(state["after"])
        self.assertEqual(before.pop("source_reviews") + 1, after.pop("source_reviews"))
        self.assertEqual(before, after)
        self.assertEqual(state["CANONICAL_RESEARCH_MUTATION"], 0)
        self.assertEqual(state["governance_rows_written"]["source_policy_reviews"], 1)

    def test_no_model_no_acquisition_no_opportunity(self):
        for key, value in self.record["mission_accounting"].items():
            self.assertEqual(value, 0, key)

    def test_the_stale_preparation_is_recorded_rather_than_repaired(self):
        stale = self.record["known_consequence_not_repaired"]
        self.assertEqual(stale["artifact"], "docs/data/opportunity-preparation-v4.json")
        self.assertIn("never rewritten", stale["why_not_regenerated"])
        self.assertTrue(stale["records_that_stay_true_about_their_own_moment"])

    def test_the_candidate_and_the_parked_arc_are_untouched(self):
        candidate = self.record["selected_candidate_unchanged"]
        self.assertEqual(candidate["SELECTED_SUBJECT"], SUBJECT)
        self.assertFalse(candidate["candidate_ranking_reopened"])
        parked = self.record["parked_states_preserved"]
        self.assertFalse(parked["changed_by_this_mission"])
        self.assertFalse(parked["q1"]["RUN_AUTHORIZED"])
        self.assertEqual(parked["globalping"]["PASS"], 12)


class TestTheGate(unittest.TestCase):
    def test_it_validates_and_renders_the_shipped_records(self):
        module = gate()
        approval, record = module.validate()
        self.assertEqual(
            module.render_approval(approval),
            (DATA / "ted-egress-operator-decision-v1.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            module.render(record),
            (DATA / "ted-egress-decision-persistence-v1.md").read_text(encoding="utf-8"),
        )

    def test_it_derives_the_conditions_from_the_catalog_rather_than_pinning_them(self):
        """A gate that pinned today's five would make a successor adding none unrepresentable."""
        module = gate()
        self.assertFalse(hasattr(module, "REQUIRED_CONDITIONS"))
        self.assertEqual(module.CONDITION_KINDS, ("CAPABILITY", "HUMAN_CONFIRMATION"))

    def test_one_statement_is_checked_against_the_signed_identifiers(self):
        module = gate()
        record = load(PERSISTENCE)
        catalog = load(CATALOG)
        conditions = record["conditions_after_persistence"]
        conditions["ted-external-model-transmission-accepted"]["verifier_version"] = "another-text"
        with self.assertRaises(module.ValidationError):
            module._check_the_conditions(record, catalog)

    def test_separate_statements_stay_expressible(self):
        module = gate()
        record = load(PERSISTENCE)
        catalog = load(CATALOG)
        conditions = record["conditions_after_persistence"]
        conditions["ted-external-model-transmission-accepted"]["verifier_version"] = "another-text"
        conditions["human_confirmations_rest_on_one_statement"] = False
        module._check_the_conditions(record, catalog)

    def test_a_dropped_required_condition_is_refused(self):
        module = gate()
        record = load(PERSISTENCE)
        catalog = load(CATALOG)
        source = next(s for s in catalog["sources"] if s["source_id"] == "ted-eu")
        v4 = next(
            r
            for r in source["reviews"]
            if r["assessed_use_profile"] == PROFILE and r["review_version"] == 4
        )
        v4["required_conditions"] = [
            c for c in v4["required_conditions"] if c["key"] != "ted-attribution"
        ]
        with self.assertRaises(module.ValidationError):
            module._check_the_append(record, catalog, load(PACKET))

    def test_the_gate_is_registered_in_ci(self):
        self.assertIn(
            "render_ted_egress_decision_persistence.py --check", CI.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
