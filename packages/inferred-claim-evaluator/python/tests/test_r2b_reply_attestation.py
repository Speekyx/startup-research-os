"""Mission 1.76.4. The reply was sent, and a person is the only witness to it.

Four things this file defends.

AN EXECUTION IS NOT A NEW APPROVAL. The execution is excluded from the digest precisely so
it can move, so recording the send must leave `approval_sha256` byte-identical. That is the
strongest available proof this is the approved action being performed rather than a
different action being approved after the fact.

A SEND IS NOT A DELIVERY. The attestation establishes an act by the sender and is silent
on the outcome at the receiver, so deliveries stay 0 and `provider_contacted` stays false.

NOBODY KNOWS WHO RECEIVED IT. A reply in a thread types no address and the earlier sender
is NOT_ESTABLISHED, so no recipient is attested and none is guessed. This is the same
refusal the approval made, one step later.

THE ORDERING IS CHECKABLE. The approval was committed and merged eighteen hours before the
attested send, so "the approval came first" is read off the repository's own history rather
than asserted.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

APPROVAL = DATA / "globalping-r2b-dispatch-approval-v1.json"
PACKET = DATA / "globalping-r2b-enquiry-packet-v1.json"
V1_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
V2_APPROVAL = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
FROZEN_REPLY = DATA / "globalping-r2-provider-reply-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"
RENDERER = SCRIPTS / "render_r2b_dispatch_approval.py"
PAGE = DATA / "globalping-r2b-dispatch-approval-v1.md"

# Recorded by Mission 1.76.3, from the repository's own history.
APPROVAL_COMMITTED_AT = "2026-09-07T01:12:27+04:00"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_r2b_dispatch_approval", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheExecutionMovedAndTheApprovalDidNot(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)
        self.gate = gate()

    def test_the_approval_digest_is_unchanged_by_the_send(self):
        """The whole point of excluding the execution from the digest."""
        action = self.approval["approved_action"]
        self.assertEqual(
            self.gate._digest(action, self.approval["hash_covers"]), action["approval_sha256"]
        )
        self.assertEqual(
            action["approval_sha256"],
            "7df1876ca1e110004a4bd93f3e83a30036b3238a2beac3708b83c8e52188de7d",
        )

    def test_the_execution_is_excluded_from_the_digest(self):
        self.assertNotIn("execution", self.approval["hash_covers"])
        self.assertIn("execution", self.approval["hash_excludes"])

    def test_the_approval_still_names_the_frozen_packet(self):
        packet = load(PACKET)
        self.assertEqual(
            self.approval["approved_action"]["approved_content_sha256"], packet["content_sha256"]
        )
        self.assertEqual(packet["send_status"], "NOT_AUTHORIZED")
        self.assertFalse(packet["operator_approval_recorded"])

    def test_the_approval_was_recorded_by_the_mission_that_recorded_it(self):
        """A later mission that fills in an execution does not become the approval's author."""
        self.assertEqual(self.approval["mission"], "1.76.3")
        self.assertEqual(self.approval["execution"]["recorded_by_mission"], "1.76.4")


class TestTheSendIsAttestedAndNotChecked(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)
        self.execution = self.approval["execution"]

    def test_the_attestation_names_its_attester_and_its_statement(self):
        self.assertEqual(self.execution["attested_by"], "operator")
        self.assertIn("GP-R2-B-Q1", self.execution["attestation_statement"])
        self.assertTrue(self.execution["operator_attestation_recorded"])
        self.assertEqual(self.execution["attestation_level"], "OPERATOR_ATTESTED")

    def test_the_send_time_carries_an_explicit_offset(self):
        sent_at = self.execution["sent_at"]
        self.assertTrue(gate().TIMESTAMP.fullmatch(sent_at))
        self.assertIsNotNone(datetime.fromisoformat(sent_at).utcoffset())
        self.assertTrue(self.execution["sent_at_carries_an_explicit_offset"])

    def test_the_send_followed_the_approval_being_recorded(self):
        sent = datetime.fromisoformat(self.execution["sent_at"])
        committed = datetime.fromisoformat(APPROVAL_COMMITTED_AT)
        self.assertGreater(sent, committed)
        self.assertTrue(self.execution["sent_after_the_approval_was_recorded"])
        self.assertTrue(self.execution["how_that_ordering_is_established"].strip())

    def test_the_sender_is_a_mailbox_and_the_approval_binds_none(self):
        self.assertIn("@", self.execution["attested_sender"])
        self.assertTrue(self.execution["sender_supplied_only_by_the_attestation"])
        self.assertFalse(self.execution["sender_written_back_into_the_approval"])
        self.assertFalse(
            any("sender" in key for key in self.approval["approved_action"]),
            "the approval binds no sender, and writing one back would make a field the "
            "operator never approved read as though they had",
        )

    def test_the_subject_matches_and_the_body_was_not_compared(self):
        self.assertEqual(
            self.execution["attested_subject"],
            self.approval["approved_action"]["approved_subject"],
        )
        self.assertEqual(self.execution["body_used_per_attestation"], "THE_FROZEN_PACKET_BODY")
        self.assertFalse(self.execution["body_compared_by_this_repository"])

    def test_nothing_was_invented_to_fill_a_field(self):
        self.assertIsNone(self.execution["message_id"])
        self.assertFalse(self.execution["message_id_available"])
        self.assertIsNone(self.execution["attested_recipient"])

    def test_the_attestation_says_what_it_does_not_cover(self):
        covers = set(self.execution["attestation_covers"])
        uncovered = set(self.execution["attestation_does_not_cover"])
        self.assertFalse(covers & uncovered)
        for outside in ("delivery", "who received it", "a reply to it"):
            with self.subTest(item=outside):
                self.assertIn(outside, uncovered)


class TestNobodyKnowsWhoReceivedIt(unittest.TestCase):
    def setUp(self):
        self.execution = load(APPROVAL)["execution"]

    def test_no_recipient_is_attested_and_none_is_guessed(self):
        self.assertIsNone(self.execution["attested_recipient"])
        self.assertIn("NOT_ESTABLISHED", self.execution["why_no_recipient_is_attested"])

    def test_the_recipient_comparison_is_not_applicable_rather_than_a_match(self):
        """The approval bound a sentinel, so reporting a MATCH would invent an agreement
        between two things neither of which is an address."""
        self.assertEqual(self.execution["recipient_comparison"], "NOT_APPLICABLE")
        self.assertTrue(self.execution["why_the_recipient_comparison_is_not_applicable"].strip())

    def test_the_thread_match_says_what_established_it(self):
        self.assertTrue(self.execution["thread_matches_the_bound_thread"])
        self.assertIn("attestation", self.execution["how_the_thread_match_is_established"])

    def test_the_earlier_sender_is_still_not_established(self):
        self.assertFalse(load(FROZEN_REPLY)["attribution"]["sufficient_for_provider_authority"])


class TestASendIsNotADelivery(unittest.TestCase):
    def setUp(self):
        self.execution = load(APPROVAL)["execution"]
        self.delivery = self.execution["delivery"]

    def test_the_delivery_is_unconfirmed_and_nothing_established_it(self):
        self.assertEqual(self.delivery["delivery_status"], "UNCONFIRMED")
        self.assertIsNone(self.delivery["delivery_established_by"])
        self.assertEqual(self.execution["deliveries_confirmed"], 0)

    def test_the_provider_is_not_marked_contacted(self):
        self.assertFalse(self.execution["provider_contacted"])
        self.assertTrue(self.execution["why_provider_contacted_is_false"].strip())

    def test_silence_is_not_recorded_as_an_observation(self):
        self.assertTrue(self.delivery["absence_of_a_reported_bounce_is_not_evidence"])
        self.assertTrue(self.delivery["why_silence_is_not_evidence"].strip())
        self.assertFalse(self.execution["mailbox_read"])

    def test_the_state_can_still_move(self):
        self.assertTrue(self.delivery["a_later_bounce_would_move_this_to_FAILED"])
        self.assertTrue(self.delivery["a_later_delivery_confirmation_would_need_its_own_source"])

    def test_a_later_message_in_the_thread_would_not_confirm_this_one(self):
        self.assertTrue(
            self.delivery["a_reply_in_the_thread_would_not_confirm_delivery_of_THIS_message"]
        )
        self.assertTrue(self.delivery["why_not"].strip())

    def test_no_reply_is_recorded(self):
        self.assertFalse(self.execution["provider_replied"])
        self.assertFalse(self.execution["reply_recorded"])


class TestTheApprovalIsSpent(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)

    def test_one_reply_was_authorised_and_one_was_made(self):
        self.assertEqual(self.approval["approved_action"]["maximum_outward_replies"], 1)
        self.assertEqual(self.approval["execution"]["outward_replies_made"], 1)

    def test_the_approval_is_recorded_as_exhausted(self):
        self.assertTrue(self.approval["execution"]["approval_exhausted"])
        self.assertTrue(self.approval["execution"]["a_resend_requires_a_new_operator_approval"])

    def test_all_three_approvals_in_the_arc_are_now_spent(self):
        for path in (V1_APPROVAL, V2_APPROVAL):
            with self.subTest(approval=path.name):
                self.assertTrue(load(path)["execution"].get("approval_exhausted"))

    def test_this_repository_still_sent_nothing(self):
        execution = self.approval["execution"]
        self.assertEqual(execution["emails_sent_by_this_repository"], 0)
        self.assertFalse(execution["mail_connector_used"])
        self.assertFalse(execution["mailbox_read"])


class TestASentQuestionIsStillNotAnAnswer(unittest.TestCase):
    def test_r2_b_and_the_qualification_did_not_move(self):
        self.assertEqual(load(THIRD_PARTY)["verdict"], "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED")
        qualification = load(QUALIFICATION)
        gates = {g["dimension"]: g["status"] for g in qualification["gates"]}
        self.assertEqual(gates["C9_RIGHTS_FEASIBILITY"], "PARTIAL")
        self.assertEqual(
            qualification["tally"], {"PASS": 11, "PARTIAL": 1, "FAIL": 0, "UNKNOWN": 0}
        )
        self.assertEqual(qualification["verdict"], "COUNTERPART_UNRESOLVED")

    def test_no_residual_closed_and_nothing_was_recomputed(self):
        scope = load(APPROVAL)["scope"]
        self.assertEqual(scope["residuals_closed_by_this_mission"], 0)
        self.assertFalse(scope["qualification_recomputed"])

    def test_the_next_action_sets_no_deadline_and_reads_no_mailbox(self):
        action = load(APPROVAL)["recommended_next_action"]
        self.assertEqual(action["performed_by"], "OPERATOR")
        self.assertTrue(action["this_repository_may_not_perform_it"])
        self.assertTrue(action["no_deadline_was_agreed_with_the_provider"])
        self.assertTrue(action["silence_would_close_nothing"])
        self.assertTrue(action["mission_1_77_not_started"])


class TestTheGateRefusesTheAttestationShortcuts(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.approval = load(APPROVAL)

    def refused(self, approval):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_execution(approval)

    def mutate(self, **fields):
        approval = copy.deepcopy(self.approval)
        approval["execution"].update(fields)
        return approval

    def test_the_record_as_committed_passes(self):
        self.gate.validate()

    def test_sent_with_no_attestation_is_refused(self):
        self.refused(self.mutate(operator_attestation_recorded=False))

    def test_a_naked_local_send_time_is_refused(self):
        self.refused(self.mutate(sent_at="2026-09-07T19:19:30"))

    def test_a_send_before_its_approval_is_refused(self):
        self.refused(self.mutate(sent_at="2026-09-01T19:19:30+04:00"))

    def test_denying_the_ordering_is_refused(self):
        self.refused(self.mutate(sent_after_the_approval_was_recorded=False))

    def test_an_attested_recipient_is_refused(self):
        self.refused(self.mutate(attested_recipient="d@globalping.io"))

    def test_claiming_a_recipient_match_is_refused(self):
        self.refused(self.mutate(recipient_comparison="MATCH"))

    def test_a_sender_that_is_not_a_mailbox_is_refused(self):
        self.refused(self.mutate(attested_sender="the operator"))

    def test_writing_the_sender_back_into_the_approval_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approved_action"]["sender"] = "thib.chm@gmail.com"
        approval["approved_action"]["approval_sha256"] = self.gate._digest(
            approval["approved_action"], approval["hash_covers"]
        )
        self.refused(approval)

    def test_claiming_the_body_was_compared_is_refused(self):
        self.refused(self.mutate(body_compared_by_this_repository=True))

    def test_a_message_id_is_refused(self):
        self.refused(self.mutate(message_id="<CAF@mail.gmail.com>"))
        self.refused(self.mutate(message_id_available=True))

    def test_a_subject_that_is_not_the_approved_one_is_refused(self):
        self.refused(self.mutate(attested_subject="Something else"))

    def test_a_send_left_unexhausted_is_refused(self):
        self.refused(self.mutate(approval_exhausted=False))

    def test_permitting_a_resend_under_a_spent_approval_is_refused(self):
        self.refused(self.mutate(a_resend_requires_a_new_operator_approval=False))

    def test_an_attestation_that_covers_delivery_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["attestation_does_not_cover"] = [
            item
            for item in approval["execution"]["attestation_does_not_cover"]
            if item != "delivery"
        ]
        self.refused(approval)

    def test_an_attestation_both_covering_and_not_covering_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["attestation_covers"].append("delivery")
        self.refused(approval)


class TestTheGateRefusesInferringDelivery(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.approval = load(APPROVAL)

    def refused(self, approval):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_execution(approval)

    def delivery(self, **fields):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["delivery"].update(fields)
        return approval

    def test_a_counted_delivery_on_an_unconfirmed_state_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["deliveries_confirmed"] = 1
        self.refused(approval)

    def test_naming_a_source_for_an_unconfirmed_delivery_is_refused(self):
        self.refused(self.delivery(delivery_established_by="OPERATOR_SEND_ATTESTATION"))

    def test_a_provider_contact_without_a_confirmed_delivery_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["provider_contacted"] = True
        self.refused(approval)

    def test_treating_silence_as_evidence_is_refused(self):
        self.refused(self.delivery(absence_of_a_reported_bounce_is_not_evidence=False))

    def test_making_the_unconfirmed_state_final_is_refused(self):
        self.refused(self.delivery(a_later_bounce_would_move_this_to_FAILED=False))

    def test_letting_a_later_thread_message_confirm_this_one_is_refused(self):
        self.refused(
            self.delivery(a_reply_in_the_thread_would_not_confirm_delivery_of_THIS_message=False)
        )

    def test_a_confirmed_delivery_established_by_the_send_attestation_is_refused(self):
        for source in self.gate.THE_SEND_ATTESTATION:
            with self.subTest(source=source):
                approval = self.delivery(
                    delivery_status="CONFIRMED", delivery_established_by=source
                )
                approval["execution"]["deliveries_confirmed"] = 1
                self.refused(approval)

    def test_a_confirmed_delivery_naming_nothing_is_refused(self):
        approval = self.delivery(delivery_status="CONFIRMED", delivery_established_by=None)
        approval["execution"]["deliveries_confirmed"] = 1
        self.refused(approval)

    def test_a_failed_delivery_is_not_recorded_under_sent(self):
        """That outcome has its own execution status."""
        self.refused(self.delivery(delivery_status="FAILED"))

    def test_claiming_a_reply_came_back_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["provider_replied"] = True
        self.refused(approval)

    def test_a_confirmed_delivery_with_an_independent_source_is_accepted(self):
        """A gate that could only express one outcome would force the next one to be
        recorded as something it is not."""
        approval = self.delivery(
            delivery_status="CONFIRMED",
            delivery_established_by="A_NON_DELIVERY_REPORT_ABSENT_AND_A_PROVIDER_REPLY_QUOTING_IT",
        )
        approval["execution"]["deliveries_confirmed"] = 1
        approval["execution"]["provider_contacted"] = True
        self.gate._check_execution(approval)


class TestTheRenderedPage(unittest.TestCase):
    def setUp(self):
        self.text = PAGE.read_text(encoding="utf-8")

    def test_it_reports_the_send_and_the_unconfirmed_delivery(self):
        self.assertIn("Do not edit by hand", self.text)
        self.assertIn("SENT", self.text)
        self.assertIn("UNCONFIRMED", self.text)
        self.assertIn("2026-09-07T19:19:30+04:00", self.text)

    def test_it_does_not_claim_a_delivery_a_contact_or_a_reply(self):
        self.assertIn("A send is not a delivery", self.text)
        self.assertIn("| deliveries confirmed | 0 |", self.text)
        self.assertIn("| provider contacted | False |", self.text)
        self.assertIn("| provider replied | False |", self.text)

    def test_it_says_nobody_knows_who_received_it(self):
        self.assertIn("Nobody knows who received it", self.text)
        self.assertIn("| recipient | None |", self.text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "reports" / "mission-1.76.4-report.md").exists())


if __name__ == "__main__":
    unittest.main()
