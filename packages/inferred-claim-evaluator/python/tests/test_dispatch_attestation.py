"""Mission 1.66.1. The send happened, and a person is the only witness to it.

Mission 1.66 reported the approved action as awaiting execution. That was true
when it ran. The operator then performed it and attested afterwards, so this
mission appends a state rather than correcting a mistake, and the tests below are
mostly about keeping those two things apart.

The half worth reading twice is the evidence level. Every other link in this
chain answers to arithmetic: the content has a hash, the approval names that
hash, and the action the approval authorises is fixed by seven bound fields. The
one fact that the message actually left the operator's mailbox rests on a person
saying so, because no other evidence for it exists. **The most consequential link
is the weakest**, and the only honest response is to label it accurately and
refuse to let it be quoted as anything stronger.

Nothing here is persisted, this repository sent nothing, and no mailbox was read.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

ATTESTATION = DATA / "onyphe-manual-dispatch-attestation-v1.json"
MISSION_1_66_EXECUTION = DATA / "onyphe-enquiry-dispatch-execution-v1.json"
MISSION_1_66_VERDICT = DATA / "approved-dispatch-execution-v1.json"
MISSION_1_66_BASELINE = DATA / "mission-1.66-baseline-v1.json"

ONYPHE_ENVELOPE = DATA / "onyphe-dispatch-envelope-v1.json"
ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
NETLAS_ENVELOPE = DATA / "netlas-dispatch-envelope-v1.json"

APPROVED_ENVELOPE_SHA256 = "12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2"
APPROVED_CONTENT_SHA256 = "0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f"
APPROVED_RECIPIENT = "contact@onyphe.io"
APPROVED_CHANNEL = "OPERATOR_MANUAL_SEND"
APPROVED_SUBJECT = "Three questions about datascan record semantics and scan configuration"
APPROVED_SENDER_PLACEHOLDER = "OPERATOR_CHOSEN_MAILBOX_AT_SEND_TIME"

BINDING_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "outbound_channel",
    "sender_identity",
    "subject",
    "content_version",
)


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


def _envelope_digest(envelope: dict, content_sha: str) -> str:
    binding = {f: envelope.get(f) for f in BINDING_FIELDS}
    binding["enquiry_content_sha256"] = content_sha
    blob = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class TestTheApprovedArtifactsStillAnswerToTheirHashes(unittest.TestCase):
    """An attestation about bytes that moved attests to nothing."""

    def test_the_approved_content_hash_still_recomputes(self) -> None:
        self.assertEqual(
            hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest(), APPROVED_CONTENT_SHA256
        )

    def test_the_approved_envelope_hash_still_recomputes(self) -> None:
        content = hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest()
        self.assertEqual(
            _envelope_digest(_load(ONYPHE_ENVELOPE), content), APPROVED_ENVELOPE_SHA256
        )

    def test_the_attestation_names_those_hashes(self) -> None:
        approved = _load(ATTESTATION)["the_action_that_was_approved"]
        self.assertEqual(approved["dispatch_envelope_sha256"], APPROVED_ENVELOPE_SHA256)
        self.assertEqual(approved["enquiry_content_sha256"], APPROVED_CONTENT_SHA256)
        self.assertIs(approved["both_hashes_recomputed_this_mission"], True)


class TestMission166WasNotRewritten(unittest.TestCase):
    """It recorded a moment. A later event does not correct it."""

    def test_its_execution_record_still_says_awaiting(self) -> None:
        record = _load(MISSION_1_66_EXECUTION)
        self.assertEqual(record["execution_status"], "APPROVED_AWAITING_MANUAL_EXECUTION")
        self.assertIs(record["execution"]["SENT"], False)
        self.assertEqual(record["execution"]["send_count"], 0)

    def test_its_execution_record_still_carries_no_confirmation(self) -> None:
        self.assertIs(
            _load(MISSION_1_66_EXECUTION)["operator_confirmation"]["CONFIRMATION_GIVEN"], False
        )

    def test_its_verdict_still_says_awaiting_execution(self) -> None:
        self.assertEqual(
            _load(MISSION_1_66_VERDICT)["primary_outcome"],
            "ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION",
        )

    def test_its_baseline_is_untouched(self) -> None:
        base = _load(MISSION_1_66_BASELINE)["canonical_baseline"]
        self.assertEqual(base["drift_from_mission_1_65"], "none")
        self.assertEqual(base["claims"], 44)

    def test_a_forward_pointer_was_appended_rather_than_the_record_edited(self) -> None:
        # Without it, a reader meeting the 1.66 record alone would take a
        # historical state for the current one.
        pointer = _load(MISSION_1_66_EXECUTION)["superseded_by"]
        self.assertEqual(pointer["record"], "onyphe-manual-dispatch-attestation-v1")
        self.assertIn("SENT", pointer["state_it_records"])
        self.assertTrue(pointer["what_this_record_still_says"].strip())
        self.assertTrue(pointer["why_this_record_was_not_edited"].strip())

    def test_the_pointer_is_visible_on_the_rendered_page(self) -> None:
        page = (DATA / "onyphe-enquiry-dispatch-execution-v1.md").read_text(encoding="utf-8")
        self.assertIn("Superseded by", page)
        self.assertIn("onyphe-manual-dispatch-attestation-v1", page)

    def test_the_history_is_a_chain_rather_than_a_correction(self) -> None:
        history = _load(ATTESTATION)["the_history_this_appends_to"]
        states = [s["state"] for s in history["chain"]]
        self.assertEqual(states[-1], "OPERATOR_ATTESTED_SENT")
        self.assertIn("APPROVED_AWAITING_MANUAL_EXECUTION", states)
        self.assertTrue(history["mission_1_66_was_correct_when_it_ran"].strip())


class TestTheAttestationIsRecordedExactly(unittest.TestCase):
    """Nothing derived, completed or tidied."""

    def setUp(self) -> None:
        self.attest = _load(ATTESTATION)["the_attestation"]

    def test_the_status_is_sent(self) -> None:
        self.assertEqual(_load(ATTESTATION)["execution_status"], "SENT")

    def test_the_sender_is_recorded(self) -> None:
        self.assertEqual(self.attest["actual_sender"], "thib.chm@gmail.com")

    def test_the_recipient_channel_and_subject_are_the_approved_ones(self) -> None:
        self.assertEqual(self.attest["actual_recipient"], APPROVED_RECIPIENT)
        self.assertEqual(self.attest["actual_channel"], APPROVED_CHANNEL)
        self.assertEqual(self.attest["actual_subject"], APPROVED_SUBJECT)

    def test_it_names_who_attested_and_from_what(self) -> None:
        self.assertEqual(self.attest["attested_by"], "thibchm")
        self.assertEqual(self.attest["attestation_source"], "OPERATOR_STATEMENT")

    def test_a_missing_message_id_is_allowed_and_explained(self) -> None:
        # A webmail send commonly exposes none to the sender. Refusing to record
        # the send for want of one would punish an honest report.
        self.assertIsNone(self.attest["message_id"])
        self.assertEqual(self.attest["message_id_status"], "NOT_AVAILABLE")
        self.assertTrue(self.attest["why_no_message_id"].strip())

    def test_no_provider_internal_identifier_was_invented(self) -> None:
        self.assertNotIn("mail.gmail.com", json.dumps(_load(ATTESTATION)))


class TestOperatorAttestedIsNotByteVerified(unittest.TestCase):
    """The weakest link carries the most consequential fact, and says so."""

    def setUp(self) -> None:
        self.record = _load(ATTESTATION)
        self.evidence = self.record["evidence_level_and_why_it_is_not_higher"]

    def test_the_level_is_the_weaker_one(self) -> None:
        self.assertEqual(self.record["verification_basis"], "OPERATOR_ATTESTED")
        self.assertEqual(self.evidence["level"], "OPERATOR_ATTESTED")
        self.assertEqual(self.evidence["is_not"], "BYTE_VERIFIED")

    def test_no_sent_message_artifact_was_imported(self) -> None:
        self.assertIs(self.evidence["sent_message_artifact_imported"], False)
        self.assertIs(self.evidence["repository_observed_the_send"], False)

    def test_the_record_says_what_stronger_evidence_would_take(self) -> None:
        # A weaker level stated with its upgrade path is a position; one stated
        # without is a shrug.
        required = self.evidence["what_would_be_required_for_byte_verification"]
        self.assertIn("hash", required.lower())
        self.assertIn(APPROVED_CONTENT_SHA256[:8], required)

    def test_the_asymmetry_between_the_links_is_named(self) -> None:
        self.assertTrue(self.evidence["the_asymmetry_worth_naming"].strip())

    def test_the_repository_did_not_observe_the_send_and_explains_why(self) -> None:
        self.assertTrue(self.evidence["why_the_repository_could_not_observe_it"].strip())


class TestTheExecutionMatchesTheApprovedAction(unittest.TestCase):
    """Field by field, against the envelope rather than against memory."""

    def setUp(self) -> None:
        self.matching = _load(ATTESTATION)["execution_matching"]

    def test_recipient_channel_and_subject_match(self) -> None:
        for field, approved in (
            ("recipient", APPROVED_RECIPIENT),
            ("channel", APPROVED_CHANNEL),
            ("subject", APPROVED_SUBJECT),
        ):
            self.assertEqual(self.matching[field]["approved"], approved, field)
            self.assertEqual(self.matching[field]["actual"], approved, field)
            self.assertEqual(self.matching[field]["verdict"], "MATCH", field)

    def test_the_overall_verdict_is_a_match(self) -> None:
        self.assertEqual(self.matching["verdict"], "EXECUTION_MATCHES_APPROVED_DISPATCH")

    def test_the_sender_is_admitted_by_the_placeholder_rather_than_by_a_match(self) -> None:
        sender = self.matching["sender"]
        self.assertEqual(sender["approved"], APPROVED_SENDER_PLACEHOLDER)
        self.assertEqual(sender["actual"], "thib.chm@gmail.com")
        self.assertEqual(sender["verdict"], "ALLOWED_BY_APPROVED_PLACEHOLDER")
        self.assertNotEqual(sender["verdict"], "MATCH")
        self.assertTrue(sender["why_this_is_not_a_divergence"].strip())


class TestTheStatedCostWasActuallyPaid(unittest.TestCase):
    """Mission 1.65 wrote the cost down before anyone knew whether it mattered."""

    def setUp(self) -> None:
        self.cost = _load(ATTESTATION)["the_stated_cost_that_was_actually_paid"]

    def test_the_envelope_bound_three_fields_of_four(self) -> None:
        envelope = _load(ONYPHE_ENVELOPE)
        self.assertIs(envelope["sender_identity_is_a_placeholder"], True)
        self.assertTrue(envelope["its_cost_stated"].strip())

    def test_the_record_names_what_was_stated_and_what_it_means_now(self) -> None:
        for field in ("what_was_stated", "what_that_means_now", "why_it_is_worth_recording"):
            self.assertTrue(self.cost[field].strip(), field)

    def test_the_actual_sender_lives_in_execution_provenance_only(self) -> None:
        # The envelope must not learn the mailbox after the fact.
        envelope_blob = json.dumps(_load(ONYPHE_ENVELOPE))
        self.assertNotIn("thib.chm@gmail.com", envelope_blob)
        self.assertIn("thib.chm@gmail.com", json.dumps(_load(ATTESTATION)))


class TestTheTimingIsPossibleAndThatIsAllItIs(unittest.TestCase):
    """A consistency check can refute an attestation; it cannot confirm one."""

    def setUp(self) -> None:
        self.timing = _load(ATTESTATION)["timing_consistency"]

    def test_the_send_follows_the_approval(self) -> None:
        self.assertGreater(self.timing["attested_send_utc"], self.timing["approval_not_before"])
        self.assertIs(self.timing["send_after_approval"], True)

    def test_the_send_follows_mission_1_66_reporting_it_awaiting(self) -> None:
        self.assertGreater(self.timing["attested_send_utc"], self.timing["mission_1_66_merged_at"])
        self.assertIs(self.timing["send_after_mission_1_66_reported_awaiting"], True)

    def test_the_two_time_fields_agree(self) -> None:
        attest = _load(ATTESTATION)["the_attestation"]
        self.assertEqual(attest["sent_at_utc"], self.timing["attested_send_utc"])
        self.assertTrue(attest["sent_at"].endswith("+04:00"))

    def test_the_record_says_what_the_check_does_not_establish(self) -> None:
        self.assertTrue(self.timing["what_this_does_not_establish"].strip())


class TestExactlyOnce(unittest.TestCase):
    """One approval, one send, and no cleanup exists for a second."""

    def setUp(self) -> None:
        self.once = _load(ATTESTATION)["exactly_once"]

    def test_one_send_and_no_duplicate(self) -> None:
        self.assertEqual(self.once["send_count"], 1)
        self.assertEqual(self.once["duplicate_send_count"], 0)

    def test_nothing_was_resent_and_no_follow_up_was_sent(self) -> None:
        self.assertIs(self.once["resent_during_this_mission"], False)
        self.assertIs(self.once["follow_up_sent"], False)

    def test_a_later_message_is_a_new_action_needing_its_own_approval(self) -> None:
        self.assertIn("NEW", self.once["the_rule"])

    def test_a_duplicate_would_be_reported_rather_than_normalised(self) -> None:
        self.assertIn("DUPLICATE_DISPATCH_OCCURRED", self.once["if_another_send_is_discovered"])


class TestTheFrozenEnvelopeIsUntouched(unittest.TestCase):
    """It records the permission. The attestation records the event."""

    def test_the_sender_placeholder_survives_the_send(self) -> None:
        envelope = _load(ONYPHE_ENVELOPE)
        self.assertEqual(envelope["sender_identity"], APPROVED_SENDER_PLACEHOLDER)
        self.assertIs(envelope["sender_identity_is_a_placeholder"], True)

    def test_the_envelope_was_not_marked_sent(self) -> None:
        envelope = _load(ONYPHE_ENVELOPE)
        self.assertIs(envelope["sent"], False)
        self.assertIsNone(envelope["sent_at"])
        self.assertEqual(envelope["dispatch_count"], 0)
        self.assertIs(envelope["approval_recorded"], False)

    def test_every_mutation_flag_is_false(self) -> None:
        frozen = _load(ATTESTATION)["the_frozen_envelope_is_untouched"]
        for flag in (
            "envelope_edited",
            "binding_fields_edited",
            "sender_placeholder_replaced",
            "approval_written_into_the_envelope",
            "enquiry_content_edited",
            "envelope_marked_sent",
        ):
            self.assertIs(frozen[flag], False, flag)

    def test_the_record_says_why_the_envelope_does_not_record_the_send(self) -> None:
        self.assertTrue(
            _load(ATTESTATION)["the_frozen_envelope_is_untouched"][
                "why_the_envelope_does_not_record_the_send"
            ].strip()
        )


class TestNotCheckedIsNotNoResponse(unittest.TestCase):
    """The mailbox was not inspected, and the record claims only that."""

    def setUp(self) -> None:
        self.reply = _load(ATTESTATION)["provider_response"]

    def test_the_status_is_not_checked(self) -> None:
        self.assertEqual(self.reply["status"], "NOT_CHECKED_AFTER_DISPATCH")

    def test_and_it_names_the_stronger_claim_it_declines_to_make(self) -> None:
        self.assertEqual(self.reply["is_not"], "NO_RESPONSE_EXISTS")

    def test_no_mailbox_was_searched(self) -> None:
        self.assertIs(self.reply["mailbox_searched"], False)
        self.assertEqual(_load(ATTESTATION)["counters"]["mailbox_searches"], 0)
        self.assertTrue(self.reply["why_not_checked"].strip())

    def test_no_reply_was_frozen_or_interpreted(self) -> None:
        self.assertIs(self.reply["response_frozen"], False)
        self.assertIs(self.reply["response_interpreted"], False)

    def test_the_record_says_what_happens_when_a_reply_arrives(self) -> None:
        plan = self.reply["what_happens_when_a_reply_arrives"]
        self.assertIn("verbatim", plan)
        self.assertIn("separate mission", plan)


class TestASentQuestionIsNotAnAnswer(unittest.TestCase):
    """The sentence three missions have repeated, used for its actual case."""

    def setUp(self) -> None:
        self.apparatus = _load(ATTESTATION)["apparatus_state_unchanged"]

    def test_onyphe_gates_did_not_move(self) -> None:
        onyphe = self.apparatus["ONYPHE"]
        self.assertEqual(onyphe["B2"], "PARTIAL")
        self.assertEqual(onyphe["B4"], "PARTIAL")
        self.assertEqual(onyphe["port_22_membership"], "UNKNOWN")
        self.assertEqual(onyphe["post_30d_location_fields"], "UNKNOWN")
        self.assertIs(onyphe["changed"], False)

    def test_no_apparatus_changed(self) -> None:
        for name in ("ONYPHE", "Netlas", "LeakIX", "The Shadowserver Foundation"):
            self.assertIs(self.apparatus[name]["changed"], False, name)

    def test_no_apparatus_qualifies_and_pairing_is_not_ready(self) -> None:
        self.assertEqual(self.apparatus["qualified_count"], 0)
        self.assertIs(self.apparatus["pair_analysis_ready"], False)

    def test_the_rule_names_the_sent_case_explicitly(self) -> None:
        self.assertIn("SENT", self.apparatus["rule"])


class TestNothingElseMoved(unittest.TestCase):
    """A dispatch is process evidence, never a research row."""

    def test_this_repository_sent_nothing(self) -> None:
        counters = _load(ATTESTATION)["counters"]
        self.assertEqual(counters["emails_sent_by_this_repository"], 0)
        self.assertEqual(counters["connector_executions"], 0)
        self.assertEqual(counters["follow_ups_sent"], 0)

    def test_netlas_is_untouched(self) -> None:
        netlas = _load(ATTESTATION)["netlas_untouched"]
        self.assertEqual(netlas["content_approval"], "VALID")
        self.assertEqual(netlas["recipient"], "NOT_ESTABLISHED")
        self.assertIs(netlas["sent"], False)
        self.assertIs(netlas["onyphe_approval_reused_for_netlas"], False)
        self.assertIsNone(_load(NETLAS_ENVELOPE)["recipient_address"])

    def test_the_canonical_baseline_is_what_mission_1_66_left(self) -> None:
        base = _load(ATTESTATION)["canonical_baseline_unchanged"]
        self.assertEqual(base["raw_records"], 325)
        self.assertEqual(base["normalized_records"], 325)
        self.assertEqual(base["signals"], 33)
        self.assertEqual(base["claims"], 44)
        self.assertEqual(base["evidence"], 58)
        self.assertEqual(base["reliability_assessments"], 4)
        self.assertEqual(base["registered_sources"], 29)
        self.assertEqual(base["drift"], "none")

    def test_no_canonical_row_no_source_no_reliability_no_pairing(self) -> None:
        counters = _load(ATTESTATION)["counters"]
        for name in (
            "canonical_mutations",
            "sources_registered",
            "governance_reviews_created",
            "reliability_values_assigned",
            "independence_groups_created",
            "apparatus_gates_changed",
            "pairs_compared",
            "migrations_created",
            "model_calls",
            "embeddings",
        ):
            self.assertEqual(counters[name], 0, name)

    def test_the_profile_and_problem_family_are_unchanged(self) -> None:
        counters = _load(ATTESTATION)["counters"]
        self.assertEqual(counters["reference_profile"], "UNCALIBRATED")
        self.assertEqual(counters["problem_family"], "PARKED")

    def test_the_stop_condition_holds_in_every_clause(self) -> None:
        for name, value in _load(ATTESTATION)["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertIs(value, False, name)


class TestTheFirstOutwardActionAndWhoseItWas(unittest.TestCase):
    """Prepared here, performed by a person."""

    def test_the_record_says_the_repository_did_not_perform_it(self) -> None:
        first = _load(ATTESTATION)["what_this_is_the_first_of"]
        self.assertIn("operator sent it", first["and_it_was_not_completed_by_this_repository"])
        self.assertTrue(first["observation"].strip())

    def test_the_outcome_is_the_attested_one(self) -> None:
        record = _load(ATTESTATION)
        self.assertEqual(record["primary_outcome"], "ONYPHE_MANUAL_DISPATCH_ATTESTED")
        self.assertTrue(record["primary_outcome_statement"].strip())


class TestNoRecordOverclaims(unittest.TestCase):
    """A sent question is not a market finding."""

    def test_the_record_uses_no_commercial_or_adoption_vocabulary(self) -> None:
        for sentence in _prose(_load(ATTESTATION)):
            tokens = set(re.findall(r"[a-z0-9]+", sentence.lower()))
            for term in (
                "installation",
                "customer",
                "subscription",
                "revenue",
                "adoption",
                "demand",
            ):
                self.assertNotIn(term, tokens, sentence[:80])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
