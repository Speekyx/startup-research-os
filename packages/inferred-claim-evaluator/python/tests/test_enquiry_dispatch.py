"""Mission 1.64. The approved enquiry, its recipient, and three candidate reads.

Two things are worth testing here that were not testable before.

The first is that the approved enquiry still hashes to the approved value under
every plausible hashing boundary. An approval names a hash, and a renderer that
rewrote the document it approved would void it silently. That the document also
survives regeneration is enforced by two CI gates together rather than here: the
Mission 1.61 renderer's --check compares it against its record, and this mission's
validator recomputes its digest.

The second is negative: nothing was sent. The mission had an approved message, a
verified hash and a mail-capable connector in the environment, and it did not
dispatch, because the recipient is a string only a person can read off a page.

Nothing here is persisted and no measurement was retrieved to construct it.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.64-baseline-v1.json"
DISPATCH = DATA / "anchor-enquiry-dispatch-review-v1.json"
LIFECYCLE = DATA / "onyphe-datascan-record-lifecycle-v1.json"
PORTS = DATA / "onyphe-datascan-port-configuration-v1.json"
RETENTION = DATA / "onyphe-post-30d-field-retention-v1.json"
PACKAGE = DATA / "onyphe-package-final-recompute-v1.json"
READINESS = DATA / "apparatus-readiness-after-enquiry-dispatch-v1.json"

ENQUIRY_V1_JSON = DATA / "anchor-technical-lineage-enquiry-v1.json"
ENQUIRY_V1_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"
PACKET_MD = DATA / "anchor-enquiry-manual-dispatch-packet-v1.md"

APPROVED_SHA256 = "310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4"
ALL_RECORDS = (BASELINE, DISPATCH, LIFECYCLE, PORTS, RETENTION, PACKAGE, READINESS)
B_SLOTS = ("B1", "B2", "B3", "B4", "B5", "B6")


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


class TestApprovedEnquiryBytes(unittest.TestCase):
    def test_the_approved_document_still_hashes_to_the_approved_value(self) -> None:
        self.assertEqual(hashlib.sha256(ENQUIRY_V1_MD.read_bytes()).hexdigest(), APPROVED_SHA256)

    def test_the_hashing_boundary_is_documented_and_unambiguous(self) -> None:
        check = _load(BASELINE)["approved_enquiry_hash_verification"]
        self.assertEqual(check["approved_sha256"], APPROVED_SHA256)
        self.assertGreaterEqual(len(check["boundaries_tested"]), 3)
        for b in check["boundaries_tested"]:
            self.assertTrue(b["matches"], b["boundary"])
            self.assertEqual(b["digest"], APPROVED_SHA256)

    def test_every_plausible_hashing_boundary_agrees(self) -> None:
        raw = ENQUIRY_V1_MD.read_bytes()
        digests = {
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(ENQUIRY_V1_MD.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
            hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
        }
        self.assertEqual(digests, {APPROVED_SHA256})

    def test_the_document_was_not_edited(self) -> None:
        check = _load(BASELINE)["approved_enquiry_hash_verification"]
        for flag in (
            "bytes_changed",
            "renderer_rewrote_it",
            "subject_or_body_edited",
            "recipient_added_inside_hashed_body",
        ):
            self.assertFalse(check[flag], flag)

    def test_the_recipient_is_outside_the_frozen_range(self) -> None:
        v1 = _load(ENQUIRY_V1_JSON)
        self.assertEqual(v1["delivery"]["recipient_address"], "TO_BE_SUPPLIED_BY_OPERATOR")
        self.assertEqual(v1["status"], "AWAITING_OPERATOR_APPROVAL")


class TestNothingWasSent(unittest.TestCase):
    def test_no_enquiry_was_dispatched(self) -> None:
        sent = _load(DISPATCH)["a5_dispatch"]
        self.assertFalse(sent["sent"])
        self.assertIsNone(sent["sent_at"])
        self.assertEqual(sent["dispatch_count"], 0)
        self.assertEqual(_load(BASELINE)["request_accounting"]["OUTBOUND_ENQUIRIES_SENT"], 0)

    def test_no_recipient_address_exists_and_none_was_invented(self) -> None:
        r = _load(DISPATCH)["a3_recipient"]
        self.assertIsNone(r["exact_address"])
        self.assertFalse(r["supplied_by_operator"])
        self.assertFalse(r["address_invented"])
        self.assertFalse(r["address_inferred"])

    def test_no_conventional_mailbox_appears_in_any_record(self) -> None:
        for path in ALL_RECORDS:
            blob = json.dumps(_load(path))
            for guess in ("support@", "info@", "hello@", "security@", "contact@", "abuse@"):
                self.assertNotIn(guess, blob, f"{path.name} names {guess}")

    def test_the_obfuscation_was_not_decoded(self) -> None:
        r = _load(DISPATCH)["a3_recipient"]
        self.assertTrue(r["no_attempt_was_made_to_decode_the_obfuscation"])

    def test_a_mail_capable_connector_existing_is_not_authorisation(self) -> None:
        method = _load(DISPATCH)["a4_dispatch_method"]
        self.assertTrue(method["a_mail_capable_connector_exists_in_the_environment"])
        self.assertFalse(method["was_it_used"])
        self.assertGreaterEqual(len(method["why_not"]), 2)

    def test_no_credentials_were_written_or_invented(self) -> None:
        method = _load(DISPATCH)["a4_dispatch_method"]
        self.assertEqual(method["credentials_written"], 0)
        self.assertFalse(method["webmail_scraped"])
        self.assertFalse(method["browser_login_automated"])
        self.assertFalse(method["provider_api_credentials_invented"])


class TestDispatchIsNotAnAnswer(unittest.TestCase):
    def test_a8_did_not_move(self) -> None:
        a7 = _load(DISPATCH)["a7_sending_would_not_have_answered_anything"]
        self.assertEqual(a7["anchor_a8_before"], a7["anchor_a8_after"])
        self.assertFalse(a7["anchor_gate_changed_this_mission"])

    def test_no_provider_response_was_received(self) -> None:
        intake = _load(DISPATCH)["provider_response_intake_boundary"]
        self.assertFalse(intake["response_received"])

    def test_the_intake_contract_forbids_automatic_promotion(self) -> None:
        rules = _load(DISPATCH)["provider_response_intake_boundary"]["if_a_response_arrives"]
        self.assertEqual(rules["automatic_promotion_to_PASS"], "forbidden")
        self.assertIn("UNKNOWN", rules["ambiguous_answer"])
        self.assertIn("FUTURE_GOVERNANCE_INPUT", rules["licensing_content"])

    def test_the_message_is_still_current(self) -> None:
        a2 = _load(DISPATCH)["a2_the_approved_message_is_still_current"]
        self.assertEqual(a2["verdict"], "STILL_CURRENT")
        self.assertEqual(a2["answered_by_new_anchor_evidence"], 0)
        self.assertFalse(a2["superseded_before_send"])


class TestRecordLifecycle(unittest.TestCase):
    def test_the_lifecycle_remains_ambiguous(self) -> None:
        v = _load(LIFECYCLE)["verdict"]
        self.assertEqual(v["record_lifecycle"], "AMBIGUOUS")
        self.assertEqual(v["b2_result"], "PARTIAL")

    def test_an_ambiguous_lifecycle_cannot_pass_b2(self) -> None:
        v = _load(LIFECYCLE)["verdict"]
        if v["record_lifecycle"] in ("AMBIGUOUS", "UNKNOWN"):
            self.assertNotEqual(v["b2_result"], "PASS")

    def test_a_maintained_lifecycle_would_fail_b2(self) -> None:
        """The rule, held even though this apparatus is ambiguous."""
        v = _load(LIFECYCLE)["verdict"]
        if v["record_lifecycle"] == "MAINTAINED_SERVICE_STATE_LAST_SEEN":
            self.assertEqual(v["b2_result"], "FAIL")

    def test_converging_evidence_is_not_a_statement(self) -> None:
        for item in _load(LIFECYCLE)["new_first_party_evidence"]:
            if item.get("verbatim"):
                self.assertTrue(item["why_it_is_not_decisive"].strip(), item["verbatim"][:40])

    def test_the_discriminating_case_is_named(self) -> None:
        case = _load(LIFECYCLE)["the_discriminating_case_that_is_still_unaddressed"]
        self.assertTrue(case["case"].strip())
        self.assertEqual(case["which_one_the_documentation_states"], "Neither.")

    def test_no_empirical_query_resolved_the_ambiguity(self) -> None:
        block = _load(LIFECYCLE)["what_would_close_it"]["no_empirical_resolution_attempted"]
        for name in ("records_queried", "hosts_queried", "timestamps_compared"):
            self.assertEqual(block[name], 0, name)

    def test_an_absence_argument_carries_no_weight(self) -> None:
        items = _load(LIFECYCLE)["new_first_party_evidence"]
        absence = [i for i in items if "absence" in json.dumps(i).lower()]
        self.assertTrue(absence, "the absence argument should be recorded")
        for item in absence:
            self.assertIn("no weight", json.dumps(item).lower())


class TestPortConfiguration(unittest.TestCase):
    def test_only_one_category_section_exists(self) -> None:
        found = _load(PORTS)["what_was_found"]
        self.assertEqual(found["category_sections_on_the_page"], 1)
        self.assertFalse(found["a_datascan_section_exists"])

    def test_datascan_membership_is_unknown(self) -> None:
        self.assertEqual(_load(PORTS)["verdict"]["membership"], "PORT_22_DATASCAN_STATUS_UNKNOWN")

    def test_no_category_transfer_was_performed(self) -> None:
        t = _load(PORTS)["no_category_transfer_was_performed"]
        self.assertFalse(t["used"])
        self.assertTrue(t["the_symmetric_refusal"].strip())

    def test_configuration_is_not_time_addressable(self) -> None:
        self.assertEqual(
            _load(PORTS)["verdict"]["configuration_time_addressability"],
            "CONFIGURATION_TIME_NOT_ADDRESSABLE",
        )

    def test_unpublished_is_not_unestablishable(self) -> None:
        block = _load(PORTS)["is_this_a_configuration_gap_outcome"]
        self.assertFalse(block["selected"])
        self.assertTrue(block["why_not"].strip())


class TestRetention(unittest.TestCase):
    def test_truncation_is_not_removal_and_b3_stays_closed(self) -> None:
        kept = _load(RETENTION)["what_is_already_established_and_not_reopened"]
        self.assertTrue(kept["the_raw_field_is_truncated_not_removed"])
        self.assertFalse(kept["b3_reopened"])
        self.assertFalse(kept["contradictory_evidence_found"])

    def test_unnamed_removed_fields_are_not_guessed(self) -> None:
        v = _load(RETENTION)["verdict"]
        self.assertFalse(v["unnamed_removed_fields_inferred"])
        for key in ("ADDRESS", "OBSERVATION_TIME", "VANTAGE_FIELDS"):
            self.assertTrue(str(v[key]).endswith("UNKNOWN"), key)

    def test_both_directions_of_inference_were_refused(self) -> None:
        v = _load(RETENTION)["verdict"]
        self.assertTrue(v["why_not_inferred_present"].strip())
        self.assertTrue(v["why_not_inferred_absent"].strip())

    def test_no_per_field_annotation_exists(self) -> None:
        self.assertFalse(
            _load(RETENTION)["what_was_found"]["per_field_retention_annotations_exist"]
        )

    def test_finite_retention_is_a_scheduling_constraint(self) -> None:
        b = _load(RETENTION)["full_fidelity_bound"]
        self.assertTrue(b["finite_retention_is_a_scheduling_constraint"])
        self.assertTrue(b["MAX_FULL_FIDELITY_RETRIEVAL_DELAY"].strip())
        self.assertEqual(b["MAX_PREDICATE_SUFFICIENT_RETRIEVAL_DELAY"], "NOT_ESTABLISHED")

    def test_no_dates_chosen_and_no_records_fetched(self) -> None:
        b = _load(RETENTION)["full_fidelity_bound"]
        self.assertTrue(b["no_observation_dates_chosen"])
        self.assertTrue(b["no_records_fetched"])


class TestPackageAndReadiness(unittest.TestCase):
    def test_every_slot_was_recomputed(self) -> None:
        pkg = _load(PACKAGE)["package"]
        for slot in B_SLOTS:
            self.assertIn(slot, pkg)
            self.assertTrue(pkg[slot]["basis"].strip())
            self.assertIn("binding_blocker", pkg[slot])
            self.assertEqual(pkg[slot]["changed"], pkg[slot]["before"] != pkg[slot]["after"])

    def test_the_package_remains_unresolved(self) -> None:
        qual = _load(PACKAGE)["individual_qualification"]
        self.assertEqual(qual["verdict"], "INDIVIDUALLY_UNRESOLVED")
        self.assertEqual(sorted(qual["binding_blockers"]), ["B2", "B4"])

    def test_the_package_is_not_ranked_or_compared(self) -> None:
        qual = _load(PACKAGE)["individual_qualification"]
        self.assertTrue(qual["not_ranked"])
        self.assertTrue(qual["not_compared_to_the_anchor"])

    def test_zero_qualified_gives_not_ready(self) -> None:
        block = _load(READINESS)["readiness"]
        self.assertEqual(block["QUALIFIED_APPARATUS_COUNT"], 0)
        self.assertFalse(block["PAIR_ANALYSIS_READY"])
        self.assertTrue(block["this_is_a_status_not_a_selection"])

    def test_the_anchor_did_not_qualify_by_dispatch(self) -> None:
        entry = next(a for a in _load(READINESS)["apparatuses"] if a["name"] == "Netlas")
        self.assertEqual(entry["individual_status"], "INDIVIDUALLY_NOT_QUALIFIED")
        self.assertTrue(
            _load(READINESS)["readiness"]["sending_the_enquiry_would_not_have_changed_this"]
        )

    def test_no_pair_gate_was_evaluated(self) -> None:
        pair = _load(READINESS)["no_pair_work_was_performed"]
        for flag in (
            "same_frame_evaluated",
            "same_observation_window_evaluated",
            "vantage_compatibility_evaluated",
            "lineage_independence_evaluated",
            "shared_measurement_upstream_evaluated",
            "same_target_proposition_evaluated",
            "threshold_preregistrability_evaluated",
        ):
            self.assertFalse(pair[flag], flag)
        for counter in ("pairs_compared", "pairs_ranked", "pairs_selected"):
            self.assertEqual(pair[counter], 0, counter)

    def test_the_negative_controls_were_left_alone(self) -> None:
        c = _load(READINESS)["the_negative_controls_were_left_alone"]
        self.assertEqual(c["researched"], 0)
        self.assertEqual(c["rescue_attempted"], 0)
        for name in ("LeakIX", "The Shadowserver Foundation"):
            entry = next(a for a in _load(READINESS)["apparatuses"] if a["name"] == name)
            self.assertEqual(entry["individual_status"], "INDIVIDUALLY_NOT_QUALIFIED")
            self.assertFalse(entry["researched_this_mission"])

    def test_the_outcome_is_the_contact_channel_one(self) -> None:
        record = _load(READINESS)
        self.assertEqual(record["primary_outcome"], "ANCHOR_CONTACT_CHANNEL_STILL_NOT_ESTABLISHED")
        self.assertIsNone(_load(DISPATCH)["a3_recipient"]["exact_address"])

    def test_the_stop_condition_holds_in_every_field(self) -> None:
        for name, value in _load(READINESS)["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertFalse(value, name)


class TestDispatchPacket(unittest.TestCase):
    def test_the_packet_body_is_generated_from_the_frozen_enquiry(self) -> None:
        packet = PACKET_MD.read_text(encoding="utf-8")
        v1 = _load(ENQUIRY_V1_JSON)
        self.assertIn(v1["subject"], packet)
        self.assertIn(v1["preamble"], packet)
        self.assertIn(v1["closing"], packet)
        for q in v1["questions"]:
            self.assertIn(q["question"], packet)

    def test_the_packet_carries_the_approved_hash(self) -> None:
        self.assertIn(APPROVED_SHA256, PACKET_MD.read_text(encoding="utf-8"))

    def test_the_packet_recipient_slot_is_blank_and_says_so(self) -> None:
        packet = PACKET_MD.read_text(encoding="utf-8")
        self.assertIn("TO_BE_SUPPLIED_BY_OPERATOR", packet)
        self.assertIn("not established", packet)


class TestNothingWasRetrievedOrMutated(unittest.TestCase):
    def test_no_measurement_of_any_kind(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        for name in (
            "MEASUREMENT_QUERIES_EXECUTED",
            "TARGET_COUNTS_FETCHED",
            "HOST_RECORDS_FETCHED",
            "TARGET_BANNERS_FETCHED",
            "FACETS_FETCHED",
            "MEASUREMENT_DOWNLOADS",
            "TRIALS_STARTED",
            "PURCHASES",
        ):
            self.assertEqual(acct[name], 0, name)

    def test_no_canonical_mutation(self) -> None:
        for name, value in _load(BASELINE)["canonical_mutations"].items():
            if name.startswith("$"):
                continue
            self.assertIn(value, (0, 0.0, False), name)

    def test_no_model_call_and_no_embeddings(self) -> None:
        mut = _load(BASELINE)["canonical_mutations"]
        self.assertEqual(mut["model_calls"], 0)
        self.assertEqual(mut["model_cost_usd"], 0.0)
        self.assertEqual(mut["embeddings"], 0)

    def test_no_reliability_and_no_governance(self) -> None:
        mut = _load(BASELINE)["canonical_mutations"]
        self.assertEqual(mut["reliability_assessments_created"], 0)
        self.assertEqual(mut["reliability_values_assigned"], 0)
        self.assertEqual(mut["governance_reviews_created"], 0)
        self.assertEqual(mut["sources_registered"], 0)

    def test_the_baseline_recorded_no_drift(self) -> None:
        self.assertEqual(_load(BASELINE)["canonical_baseline"]["drift_from_mission_1_63"], "none")
        self.assertEqual(_load(BASELINE)["canonical_baseline"]["problem_family"], "PARKED")
        self.assertEqual(_load(BASELINE)["canonical_baseline"]["reference_profile"], "UNCALIBRATED")

    def test_earlier_mission_records_are_not_rewritten(self) -> None:
        prior = _load(DATA / "qualified-apparatus-readiness-v1.json")
        self.assertEqual(
            prior["primary_outcome"], "ANCHOR_ENQUIRY_STILL_REQUIRED_ONYPHE_UNRESOLVED"
        )

    def test_no_overclaim_or_preference_vocabulary(self) -> None:
        overclaims = ("installation", "customer", "subscription", "revenue", "adoption", "demand")
        preferences = ("best candidate", "preferred candidate", "strongest partner", "lead route")
        for path in ALL_RECORDS:
            for sentence in _prose(_load(path)):
                tokens = re.findall(r"[a-z0-9]+", sentence.lower())
                for term in overclaims:
                    self.assertNotIn(term, tokens, f"{path.name}: {sentence[:80]}")
                for word in preferences:
                    self.assertNotIn(word, sentence.lower(), f"{path.name}: {sentence[:80]}")


if __name__ == "__main__":
    unittest.main()
