"""Mission 1.66. An approval arrived, and the action it authorises has not happened.

The thing worth testing here is the gap between a permission and an event.

Once an approval exists, every field an execution record needs is already known:
recipient, subject, body, channel, all frozen in the envelope the approval names.
So a dispatch log could fill itself in completely and be entirely fictional. The
tests below are mostly about what the record REFUSES to say: that `SENT` cannot
be reached from an approval, that an awaiting record carries no actual sender or
time, and that a matching body and recipient do not make an automated send the
action that was approved, because the channel is one of the seven fields the hash
binds.

The second half is about what this repository cannot do. Every earlier decision
it stopped at happened INSIDE it, where a terminal guard could require a person.
A manual outbound send happens in a mail client nothing here can observe, so no
guard can establish it. The repository records an attestation, and the vocabulary
says so: `OPERATOR_ATTESTED` is not `BYTE_VERIFIED`, and one may never be
promoted into the other.

Nothing here is persisted, nothing was sent, and no mailbox was read.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.66-baseline-v1.json"
EXECUTION = DATA / "onyphe-enquiry-dispatch-execution-v1.json"
VERDICT = DATA / "approved-dispatch-execution-v1.json"

ONYPHE_ENVELOPE = DATA / "onyphe-dispatch-envelope-v1.json"
ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
NETLAS_ENVELOPE = DATA / "netlas-dispatch-envelope-v1.json"
NETLAS_ENQUIRY_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"

APPROVED_ENVELOPE_SHA256 = "12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2"
APPROVED_CONTENT_SHA256 = "0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f"
NETLAS_APPROVED_SHA256 = "310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4"
APPROVAL_STRING = f"APPROVE MISSION 1.65 DISPATCH {APPROVED_ENVELOPE_SHA256}"

APPROVED_RECIPIENT = "contact@onyphe.io"
APPROVED_CHANNEL = "OPERATOR_MANUAL_SEND"
APPROVED_SUBJECT = "Three questions about datascan record semantics and scan configuration"

BINDING_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "outbound_channel",
    "sender_identity",
    "subject",
    "content_version",
)

ALL_RECORDS = (BASELINE, EXECUTION, VERDICT)


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


class TestTheApprovalNamesSomethingThatStillExists(unittest.TestCase):
    """An approval names a hash. If the bytes moved, it names nothing."""

    def test_the_approved_content_hash_recomputes(self) -> None:
        self.assertEqual(
            hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest(), APPROVED_CONTENT_SHA256
        )

    def test_the_approved_envelope_hash_recomputes(self) -> None:
        envelope = _load(ONYPHE_ENVELOPE)
        content = hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest()
        self.assertEqual(_envelope_digest(envelope, content), APPROVED_ENVELOPE_SHA256)

    def test_the_recorded_approval_is_the_string_the_operator_gave(self) -> None:
        approval = _load(EXECUTION)["operator_approval"]
        self.assertEqual(approval["exact_string"], APPROVAL_STRING)
        self.assertEqual(approval["names_envelope_sha256"], APPROVED_ENVELOPE_SHA256)
        self.assertIs(approval["hash_recomputed_and_matches"], True)

    def test_a_wrong_hash_would_not_be_this_approval(self) -> None:
        # The approval is a hash, so it is refutable by arithmetic rather than by
        # opinion: any other envelope produces a different string.
        envelope = _load(ONYPHE_ENVELOPE)
        altered = dict(envelope)
        altered["recipient_address"] = "someone@example.invalid"
        other = _envelope_digest(altered, APPROVED_CONTENT_SHA256)
        self.assertNotEqual(other, APPROVED_ENVELOPE_SHA256)
        self.assertNotIn(other, APPROVAL_STRING)


class TestAnApprovalIsNotAnExecution(unittest.TestCase):
    """The whole mission. A permission is not an event."""

    def setUp(self) -> None:
        self.record = _load(EXECUTION)

    def test_the_approval_was_given(self) -> None:
        self.assertIs(self.record["operator_approval"]["APPROVAL_GIVEN"], True)

    def test_and_the_action_has_not_been_performed(self) -> None:
        self.assertEqual(self.record["execution_status"], "APPROVED_AWAITING_MANUAL_EXECUTION")
        self.assertIs(self.record["execution"]["SENT"], False)
        self.assertEqual(self.record["execution"]["send_count"], 0)

    def test_they_are_recorded_in_separate_sections(self) -> None:
        self.assertIn("operator_approval", self.record)
        self.assertIn("execution", self.record)
        self.assertNotIn("SENT", self.record["operator_approval"])
        self.assertNotIn("exact_string", self.record["execution"])

    def test_the_record_states_that_one_is_not_the_other(self) -> None:
        self.assertTrue(self.record["operator_approval"]["approval_is_not_execution"].strip())

    def test_no_execution_field_was_filled_in_from_the_approval(self) -> None:
        # Every one of these is already known from the envelope. That is exactly
        # why a record could look complete and be fiction.
        ex = self.record["execution"]
        for field in (
            "actual_recipient",
            "actual_channel",
            "actual_sender",
            "actual_subject",
            "sent_at",
            "message_id",
        ):
            self.assertIsNone(ex[field], field)

    def test_no_operator_confirmation_was_given(self) -> None:
        self.assertIs(self.record["operator_confirmation"]["CONFIRMATION_GIVEN"], False)

    def test_the_record_says_what_would_satisfy_the_confirmation(self) -> None:
        satisfy = self.record["operator_confirmation"]["what_would_satisfy_it"]
        self.assertTrue(satisfy)
        joined = " ".join(satisfy).lower()
        self.assertIn("sender", joined)
        self.assertIn("manual", joined)


class TestTheRepositoryCannotVerifyAManualSend(unittest.TestCase):
    """The distinction that makes an attestation level necessary."""

    def setUp(self) -> None:
        self.record = _load(EXECUTION)

    def test_the_record_states_why_no_guard_can_observe_it(self) -> None:
        cannot = self.record["the_repository_cannot_verify_a_manual_send"]
        for field in ("observation", "consequence", "which_is_why"):
            self.assertTrue(cannot[field].strip(), field)

    def test_body_verification_is_not_applicable_because_nothing_was_sent(self) -> None:
        self.assertEqual(
            self.record["execution"]["body_post_send_verification"],
            "NOT_APPLICABLE_NOTHING_SENT",
        )

    def test_attestation_and_byte_verification_are_different_words(self) -> None:
        # They must stay two states. Collapsing them is how an attestation is
        # later quoted as proof.
        cannot = self.record["the_repository_cannot_verify_a_manual_send"]
        self.assertIn("BYTE_VERIFIED", cannot["which_is_why"])
        self.assertIn("OPERATOR_ATTESTED", cannot["which_is_why"])

    def test_no_message_id_is_claimed(self) -> None:
        self.assertEqual(
            self.record["execution"]["message_id_status"], "NOT_APPLICABLE_NOTHING_SENT"
        )
        self.assertIsNone(self.record["execution"]["message_id"])


class TestTheApprovalTimeWasNotInvented(unittest.TestCase):
    """A bound that is true beats a moment that is made up."""

    def setUp(self) -> None:
        self.approval = _load(EXECUTION)["operator_approval"]

    def test_the_exact_time_is_not_established(self) -> None:
        self.assertEqual(self.approval["approval_time"], "NOT_ESTABLISHED")

    def test_a_true_lower_bound_is_recorded_instead(self) -> None:
        # The hash the approval names did not exist on main before the merge.
        self.assertEqual(self.approval["approval_time_lower_bound"], "2026-09-05T17:09:39Z")
        self.assertTrue(self.approval["what_the_lower_bound_is"].strip())

    def test_and_the_record_says_why(self) -> None:
        self.assertTrue(self.approval["why_the_exact_time_is_not_recorded"].strip())


class TestTheFrozenEnvelopeWasNotMutated(unittest.TestCase):
    """The approved artifact records what was approved, and nothing later."""

    def setUp(self) -> None:
        self.envelope = _load(ONYPHE_ENVELOPE)

    def test_the_approval_was_not_written_into_the_document_it_approves(self) -> None:
        # Mission 1.56's shape: marking a frozen document approved changes the
        # bytes that were approved, even where the hash would survive it.
        self.assertIs(self.envelope["approval_recorded"], False)

    def test_the_sender_placeholder_was_not_replaced(self) -> None:
        self.assertIs(self.envelope["sender_identity_is_a_placeholder"], True)
        self.assertEqual(self.envelope["sender_identity"], "OPERATOR_CHOSEN_MAILBOX_AT_SEND_TIME")

    def test_the_envelope_records_no_send(self) -> None:
        self.assertIs(self.envelope["sent"], False)
        self.assertIsNone(self.envelope["sent_at"])
        self.assertEqual(self.envelope["dispatch_count"], 0)

    def test_every_mutation_flag_is_false(self) -> None:
        frozen = _load(EXECUTION)["the_frozen_envelope_was_not_mutated"]
        for flag in (
            "envelope_edited",
            "binding_fields_edited",
            "sender_placeholder_replaced_in_envelope",
            "approval_written_into_the_envelope",
            "enquiry_content_edited",
        ):
            self.assertIs(frozen[flag], False, flag)

    def test_the_record_explains_the_guard_that_now_does_a_second_job(self) -> None:
        # Mission 1.65 asserted `approval_recorded` false to mean it stopped
        # before approval. It now also keeps the approval out of the frozen
        # document, and a reader must not read the first from the second.
        frozen = _load(EXECUTION)["the_frozen_envelope_was_not_mutated"]
        self.assertTrue(frozen["a_guard_that_now_does_a_second_job"].strip())


class TestTheIntegrityChecksWereFrozenBeforeAnySend(unittest.TestCase):
    """A standard chosen after seeing what happened is not a standard."""

    def setUp(self) -> None:
        self.checks = _load(EXECUTION)["integrity_checks_that_will_apply_when_a_send_is_reported"]

    def test_they_name_the_approved_recipient_channel_and_subject(self) -> None:
        self.assertEqual(self.checks["recipient_must_equal"], APPROVED_RECIPIENT)
        self.assertEqual(self.checks["channel_must_equal"], APPROVED_CHANNEL)
        self.assertEqual(self.checks["subject_must_equal"], APPROVED_SUBJECT)
        self.assertEqual(self.checks["body_must_hash_to"], APPROVED_CONTENT_SHA256)

    def test_one_approval_authorises_one_send(self) -> None:
        self.assertEqual(self.checks["send_count_must_equal"], 1)
        self.assertEqual(self.checks["duplicate_code"], "DUPLICATE_DISPATCH_OCCURRED")

    def test_a_matching_body_does_not_rescue_a_wrong_channel(self) -> None:
        self.assertTrue(self.checks["why_a_matching_body_does_not_rescue_a_wrong_channel"].strip())

    def test_a_divergence_does_not_repair_the_envelope(self) -> None:
        self.assertIn("NOT", self.checks["on_divergence"])

    def test_a_sent_message_cannot_be_unsent(self) -> None:
        self.assertTrue(self.checks["no_automatic_cleanup_exists"].strip())

    def test_the_channel_is_one_of_the_fields_the_hash_binds(self) -> None:
        # Which is the reason a connector send is a different action rather than
        # the same action by another route.
        self.assertIn("outbound_channel", BINDING_FIELDS)


class TestNoConnectorWasUsed(unittest.TestCase):
    """The one way this mission could have quietly gone wrong."""

    def test_zero_connector_executions(self) -> None:
        self.assertEqual(_load(EXECUTION)["no_connector_was_used"]["connector_executions"], 0)
        self.assertEqual(_load(VERDICT)["counters"]["connector_executions"], 0)
        self.assertEqual(_load(BASELINE)["request_accounting"]["CONNECTOR_EXECUTIONS"], 0)

    def test_the_temptation_is_named_rather_than_left_unsaid(self) -> None:
        self.assertTrue(_load(EXECUTION)["no_connector_was_used"]["the_temptation_named"].strip())

    def test_the_route_to_authorising_one_is_a_new_envelope(self) -> None:
        refused = _load(VERDICT)["what_would_have_completed_the_action_and_was_refused"]
        self.assertIn("hash", refused["how_it_could_be_authorised"])
        self.assertTrue(refused["why_it_was_refused"].strip())


class TestNothingWasSentAndNothingWasReceived(unittest.TestCase):
    """And the difference between not received and not looked for."""

    def setUp(self) -> None:
        self.reply = _load(EXECUTION)["provider_response"]

    def test_no_reply_is_held_and_none_was_interpreted(self) -> None:
        self.assertIs(self.reply["response_received"], False)
        self.assertIs(self.reply["response_frozen"], False)
        self.assertIs(self.reply["response_interpreted"], False)

    def test_the_claim_made_is_the_weaker_true_one(self) -> None:
        # Not "no reply exists" -- only that the repository holds none and the
        # operator's mailbox was not read.
        self.assertIs(self.reply["repository_holds_a_reply"], False)
        self.assertIs(self.reply["operator_mailbox_searched"], False)
        self.assertTrue(self.reply["why_that_distinction_is_kept"].strip())

    def test_no_follow_up_was_sent(self) -> None:
        self.assertIs(self.reply["follow_up_sent"], False)
        self.assertEqual(_load(VERDICT)["counters"]["follow_ups_sent"], 0)

    def test_no_mailbox_was_searched_and_the_baseline_says_why(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["MAILBOX_SEARCHES"], 0)
        self.assertTrue(acct["why_no_mailbox_search"].strip())


class TestNetlasIsUntouched(unittest.TestCase):
    """One approval names one envelope, and reaches no other action."""

    def test_the_approved_netlas_body_still_hashes_to_its_approved_value(self) -> None:
        self.assertEqual(
            hashlib.sha256(NETLAS_ENQUIRY_MD.read_bytes()).hexdigest(), NETLAS_APPROVED_SHA256
        )

    def test_no_netlas_recipient_appeared(self) -> None:
        envelope = _load(NETLAS_ENVELOPE)
        self.assertIsNone(envelope["recipient_address"])
        self.assertIsNone(envelope["envelope_sha256"])
        self.assertIs(envelope["approvable"], False)

    def test_netlas_was_not_sent_and_the_onyphe_approval_was_not_reused(self) -> None:
        netlas = _load(VERDICT)["netlas_untouched"]
        self.assertIs(netlas["sent"], False)
        self.assertIs(netlas["onyphe_approval_reused_for_netlas"], False)
        for flag in ("address_guessed", "obfuscation_decoded"):
            self.assertIs(netlas[flag], False, flag)
        self.assertEqual(_load(VERDICT)["counters"]["netlas_enquiries_sent"], 0)

    def test_its_content_approval_is_still_valid(self) -> None:
        self.assertEqual(_load(VERDICT)["netlas_untouched"]["content_approval"], "VALID")


class TestADispatchMovesNoApparatusGate(unittest.TestCase):
    """And an unsent dispatch is not even a dispatch."""

    def test_onyphe_gates_are_where_mission_1_64_left_them(self) -> None:
        onyphe = _load(EXECUTION)["apparatus_state_unchanged"]["ONYPHE"]
        self.assertEqual(onyphe["B2"], "PARTIAL")
        self.assertEqual(onyphe["B4"], "PARTIAL")
        self.assertEqual(onyphe["port_22_membership"], "UNKNOWN")
        self.assertEqual(onyphe["post_30d_location_fields"], "UNKNOWN")
        self.assertIs(onyphe["changed"], False)

    def test_netlas_gates_are_unchanged(self) -> None:
        netlas = _load(EXECUTION)["apparatus_state_unchanged"]["Netlas"]
        self.assertEqual(netlas["A7"], "PASS")
        self.assertEqual(netlas["A8"], "PARTIAL")
        self.assertIs(netlas["changed"], False)

    def test_no_apparatus_qualifies_and_pairing_is_not_ready(self) -> None:
        for record in (EXECUTION, VERDICT):
            key = (
                "apparatus_state_unchanged" if record is EXECUTION else "apparatus_states_unchanged"
            )
            states = _load(record)[key]
            self.assertEqual(states["qualified_count"], 0)
            self.assertIs(states["pair_analysis_ready"], False)

    def test_no_pair_work_was_performed(self) -> None:
        pair = _load(VERDICT)["no_pair_work_was_performed"]
        for counter in ("pairs_compared", "pairs_ranked", "pairs_selected"):
            self.assertEqual(pair[counter], 0, counter)
        for flag in (
            "same_frame_evaluated",
            "vantage_compatibility_evaluated",
            "lineage_independence_evaluated",
            "shared_measurement_upstream_evaluated",
            "same_target_proposition_evaluated",
            "threshold_preregistrability_evaluated",
        ):
            self.assertIs(pair[flag], False, flag)


class TestNothingCanonicalMoved(unittest.TestCase):
    """Email provenance is process evidence, never a research row."""

    def test_every_canonical_mutation_counter_is_zero(self) -> None:
        for name, value in _load(BASELINE)["canonical_mutations"].items():
            if name.startswith("$"):
                continue
            self.assertIn(value, (0, 0.0, False), name)

    def test_the_baseline_matches_what_mission_1_65_left(self) -> None:
        base = _load(BASELINE)["canonical_baseline"]
        self.assertEqual(base["raw_records"], 325)
        self.assertEqual(base["normalized_records"], 325)
        self.assertEqual(base["signals"], 33)
        self.assertEqual(base["claims"], 44)
        self.assertEqual(base["evidence"], 58)
        self.assertEqual(base["evidence_supports"], 57)
        self.assertEqual(base["evidence_contradicts"], 1)
        self.assertEqual(base["registered_sources"], 29)
        self.assertEqual(base["drift_from_mission_1_65"], "none")

    def test_no_source_was_registered_because_a_provider_was_contacted(self) -> None:
        self.assertEqual(_load(VERDICT)["counters"]["sources_registered"], 0)
        self.assertEqual(_load(VERDICT)["counters"]["governance_reviews_created"], 0)

    def test_no_reliability_value_and_no_calibration(self) -> None:
        counters = _load(VERDICT)["counters"]
        self.assertEqual(counters["reliability_values_assigned"], 0)
        self.assertEqual(counters["independence_groups_created"], 0)
        self.assertEqual(counters["reference_profile"], "UNCALIBRATED")

    def test_problem_family_stays_parked(self) -> None:
        self.assertEqual(_load(VERDICT)["counters"]["problem_family"], "PARKED")

    def test_no_model_was_called(self) -> None:
        self.assertEqual(_load(VERDICT)["counters"]["model_calls"], 0)
        self.assertEqual(_load(VERDICT)["counters"]["embeddings"], 0)

    def test_no_measurement_was_retrieved(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        for name in (
            "RESEARCH_DATA_REQUESTS",
            "MEASUREMENT_QUERIES",
            "COUNTS_FETCHED",
            "HOST_RECORDS_FETCHED",
            "BANNERS_FETCHED",
            "FACETS_FETCHED",
            "DOWNLOADS",
            "TRIALS",
            "PURCHASES",
        ):
            self.assertEqual(acct[name], 0, name)


class TestTheOutcomeIsNotForced(unittest.TestCase):
    """Awaiting execution is the correct answer, not a shortfall."""

    def setUp(self) -> None:
        self.verdict = _load(VERDICT)

    def test_the_outcome_matches_the_execution_status(self) -> None:
        self.assertEqual(
            self.verdict["primary_outcome"],
            "ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION",
        )
        self.assertEqual(_load(EXECUTION)["execution_status"], "APPROVED_AWAITING_MANUAL_EXECUTION")

    def test_the_record_says_this_is_not_a_failure(self) -> None:
        self.assertTrue(self.verdict["this_is_not_a_failure"].strip())

    def test_outcome_a_was_refused_for_a_stated_reason(self) -> None:
        why = self.verdict["why_this_outcome_and_not_another"]["why_not_A"]
        self.assertIn("approval", why.lower())

    def test_the_general_rule_is_stated(self) -> None:
        two = self.verdict["the_two_facts_this_mission_keeps_apart"]
        self.assertTrue(two["the_general_rule"].strip())
        self.assertTrue(two["and_the_new_half"].strip())
        self.assertGreaterEqual(len(two["earlier_instances"]), 3)

    def test_the_next_action_is_outside_this_repository(self) -> None:
        nxt = self.verdict["next_action"]
        self.assertEqual(nxt["who_acts_next"], "the operator")
        self.assertIs(nxt["no_new_mission_is_needed_until_that_happens"], True)
        self.assertTrue(nxt["do_not_poll"].strip())

    def test_the_stop_condition_holds_in_every_clause(self) -> None:
        for name, value in self.verdict["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertIs(value, False, name)


class TestNoRecordOverclaims(unittest.TestCase):
    """A dispatch log is not a market finding."""

    def test_no_record_uses_commercial_or_adoption_vocabulary(self) -> None:
        for path in ALL_RECORDS:
            for sentence in _prose(_load(path)):
                tokens = set(re.findall(r"[a-z0-9]+", sentence.lower()))
                for term in (
                    "installation",
                    "customer",
                    "subscription",
                    "revenue",
                    "adoption",
                    "demand",
                ):
                    self.assertNotIn(term, tokens, f"{path.name}: {sentence[:80]!r}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
