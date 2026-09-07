"""Mission 1.76.3. An approved question, and nothing sent.

Four things this file defends.

A QUOTED DIGEST IS RECOMPUTED AND A RESTATED BODY IS COMPARED. The approval arrived
carrying both, and copying either would make the approval name whatever the instruction
said rather than whatever the packet is. This arc has already found a supplied quotation
differing from stored bytes by a trailing space.

THE APPROVAL SITS BESIDE THE PACKET. Marking the frozen document APPROVED would change the
artifact the operator read, and the packet's own gate asserts it records no approval.

THE THREAD IS BOUND, BECAUSE NO ADDRESS EXISTS TO BIND. A reply inherits its recipient, the
sender of the message being answered is still NOT_ESTABLISHED, and binding a sentinel would
make the digest read as though an address had been pinned.

AN APPROVAL TO ASK IS NOT AN ANSWER. Nothing was performed, no residual closed, and the
operator's own exclusion list is stored so a later reading cannot widen this approval by
forgetting what it excluded.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

APPROVAL = DATA / "globalping-r2b-dispatch-approval-v1.json"
PACKET = DATA / "globalping-r2b-enquiry-packet-v1.json"
V1_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
V2_APPROVAL = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
FROZEN_REPLY = DATA / "globalping-r2-provider-reply-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v2.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"
RENDERER = SCRIPTS / "render_r2b_dispatch_approval.py"
PAGE = DATA / "globalping-r2b-dispatch-approval-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_r2b_dispatch_approval", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheDigestWasRecomputedAndTheBodyCompared(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)
        self.packet = load(PACKET)
        self.gate = gate()

    def test_the_operators_hash_recomputes_from_the_packet_as_stored(self):
        recomputed = self.gate._digest(self.packet, self.packet["hash_covers"])
        self.assertEqual(recomputed, self.packet["content_sha256"])
        self.assertEqual(recomputed, self.approval["approval"]["hash_as_stated_by_the_operator"])
        self.assertEqual(recomputed, self.approval["approved_action"]["approved_content_sha256"])

    def test_the_record_says_it_recomputed_rather_than_copied(self):
        block = self.approval["approval"]
        self.assertTrue(block["hash_recomputed_from_the_packet_as_stored"])
        self.assertTrue(block["recomputed_hash_matches_the_stated_one"])
        self.assertTrue(block["why_it_was_recomputed_rather_than_copied"].strip())

    def test_the_approved_body_is_byte_identical_to_the_frozen_body(self):
        digest = hashlib.sha256(self.packet["body"].encode("utf-8")).hexdigest()
        self.assertEqual(self.approval["approval"]["approved_body_sha256"], digest)
        self.assertTrue(
            self.approval["approval"]["approved_body_is_byte_identical_to_the_frozen_body"]
        )
        self.assertTrue(
            self.approval["approval"]["why_the_body_was_compared_and_not_assumed"].strip()
        )

    def test_the_packet_file_is_the_one_the_approval_names(self):
        self.assertEqual(
            self.approval["approval"]["packet_file_sha256"],
            hashlib.sha256(PACKET.read_bytes()).hexdigest(),
        )
        self.assertFalse(self.approval["approval"]["packet_edited_by_this_mission"])
        self.assertFalse(self.approval["approval"]["packet_content_sha256_changed"])


class TestTheApprovalStayedOutOfThePacket(unittest.TestCase):
    def setUp(self):
        self.packet = load(PACKET)
        self.approval = load(APPROVAL)

    def test_the_packet_still_records_no_authorisation(self):
        self.assertEqual(self.packet["send_status"], "NOT_AUTHORIZED")
        self.assertFalse(self.packet["operator_approval_recorded"])
        self.assertFalse(self.packet["sent"])
        self.assertFalse(self.packet["execution_record_created"])

    def test_the_approval_lives_beside_it_and_says_why(self):
        block = self.approval["approval"]
        self.assertTrue(block["approval_given"])
        self.assertTrue(block["approved_by"].strip())
        self.assertTrue(block["approval_recorded_in_this_document_rather_than_in_the_packet"])
        self.assertIn("THIS DOCUMENT RECORDS NO", block["why"])

    def test_the_packet_field_does_not_mean_no_approval_exists(self):
        """The packet's NOT_AUTHORIZED means this document records no authorisation. An
        approval exists, in this record, and the two statements are both true."""
        self.assertEqual(self.packet["send_status"], "NOT_AUTHORIZED")
        self.assertTrue(self.approval["approval"]["approval_given"])


class TestTheActionIsBoundAndTheRecipientIsNot(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)
        self.packet = load(PACKET)
        self.gate = gate()

    def test_the_action_answers_to_its_own_hash(self):
        action = self.approval["approved_action"]
        self.assertEqual(
            self.gate._digest(action, self.approval["hash_covers"]), action["approval_sha256"]
        )

    def test_the_hash_excludes_itself_the_execution_the_date_and_the_recipient(self):
        for excluded in ("approval_sha256", "execution", "recorded_at", "recipient"):
            with self.subTest(field=excluded):
                self.assertNotIn(excluded, self.approval["hash_covers"])
                self.assertIn(excluded, self.approval["hash_excludes"])

    def test_the_action_names_this_packet_and_this_mechanism(self):
        action = self.approval["approved_action"]
        self.assertEqual(action["approves"], self.packet["question_id"])
        self.assertEqual(action["packet_version"], self.packet["packet_version"])
        self.assertEqual(action["approved_subject"], self.packet["subject"])
        self.assertEqual(action["thread_binding"], self.packet["thread_binding"])
        self.assertEqual(action["mechanism"], "OPERATOR_MANUAL_REPLY_IN_EXISTING_EMAIL_THREAD")
        self.assertEqual(action["maximum_outward_replies"], 1)

    def test_the_recipient_is_a_sentinel_and_is_not_bound(self):
        self.assertEqual(self.approval["recipient"], self.gate.RECIPIENT_SENTINEL)
        self.assertNotIn("@", self.approval["recipient"])
        self.assertFalse(self.approval["recipient_is_bound_by_the_hash"])
        self.assertIn("NOT_ESTABLISHED", self.approval["why_the_recipient_is_not_bound"])

    def test_the_thread_is_bound_by_three_digests(self):
        binding = self.approval["approved_action"]["thread_binding"]
        for field in (
            "thread_subject",
            "prior_enquiry_packet_content_sha256",
            "prior_reply_body_sha256",
        ):
            with self.subTest(field=field):
                self.assertTrue(str(binding[field]).strip())


class TestTheOperatorsExclusionsAreRecorded(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)

    def test_every_excluded_item_is_recorded_false(self):
        excluded = self.approval["explicitly_not_authorised"]
        for item in gate().NOT_AUTHORISED:
            with self.subTest(item=item):
                self.assertIs(excluded[item], False)

    def test_the_approval_says_what_it_does_not_lift(self):
        lifts = self.approval["what_this_approval_does_not_lift"]
        self.assertIn(
            "NOT_ESTABLISHED",
            lifts["the_mailbox_read_that_would_establish_the_earlier_sender"],
        )
        self.assertTrue(lifts["the_attribution_of_whatever_comes_back"].strip())

    def test_approving_the_question_does_not_improve_its_answer(self):
        reply = load(FROZEN_REPLY)
        self.assertFalse(reply["attribution"]["sufficient_for_provider_authority"])


class TestOneReplyWasSentAndNothingMore(unittest.TestCase):
    """Re-pointed by Mission 1.76.4. This class asserted the execution was pending and
    empty, which was true until the approved action was performed. What it defends is the
    property rather than the state: exactly the authorised number of replies, and no
    delivery, contact or answer claimed on top of them."""

    def setUp(self):
        self.execution = load(APPROVAL)["execution"]
        self.action = load(APPROVAL)["approved_action"]

    def test_exactly_the_authorised_number_of_replies_was_made(self):
        self.assertEqual(self.execution["status"], "SENT")
        self.assertEqual(
            self.execution["outward_replies_made"], self.action["maximum_outward_replies"]
        )
        self.assertGreaterEqual(
            self.execution["send_attempts"], self.execution["outward_replies_made"]
        )
        self.assertTrue(self.execution["approval_exhausted"])

    def test_no_delivery_contact_or_answer_is_claimed(self):
        self.assertEqual(self.execution["deliveries_confirmed"], 0)
        self.assertFalse(self.execution["provider_contacted"])
        self.assertFalse(self.execution["provider_replied"])
        self.assertFalse(self.execution["reply_recorded"])

    def test_the_send_is_attested_and_nothing_stronger(self):
        self.assertTrue(self.execution["operator_attestation_recorded"])
        self.assertEqual(self.execution["attestation_level"], "OPERATOR_ATTESTED")

    def test_this_repository_sent_nothing_and_read_nothing(self):
        self.assertEqual(self.execution["emails_sent_by_this_repository"], 0)
        self.assertFalse(self.execution["mail_connector_used"])
        self.assertFalse(self.execution["mailbox_read"])

    def test_byte_verification_is_unreachable_for_this_channel(self):
        """Mission 1.66's ceiling belongs to the MEDIUM. A thread is not a fresh message
        and the observability is identical: a mail client's outbox is unobservable here."""
        self.assertFalse(self.execution["byte_verification_is_possible_for_this_channel"])
        self.assertEqual(
            self.execution["attestation_levels_reachable_for_this_channel"],
            ["OPERATOR_ATTESTED"],
        )
        self.assertIn("NONE", self.execution["upgrade_path"])
        self.assertIn("attestation", self.execution["reachable_only_through"])

    def test_the_integrity_rules_were_frozen_before_any_send(self):
        checks = load(APPROVAL)["integrity_checks_frozen_before_any_send"]
        for flag, value in checks.items():
            if flag.startswith("$"):
                continue
            with self.subTest(rule=flag):
                self.assertIs(value, True)


class TestItIsAThirdApprovalAndNotARenewal(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)
        self.packet = load(PACKET)
        self.gate = gate()

    def test_neither_spent_approval_reaches_this_packet(self):
        for path in (V1_APPROVAL, V2_APPROVAL):
            action = load(path)["approved_action"]
            with self.subTest(approval=path.name):
                self.assertNotEqual(
                    action["approved_content_sha256"], self.packet["content_sha256"]
                )
                self.assertNotEqual(action["approves"], self.packet["question_id"])
                self.assertNotEqual(
                    action["approval_sha256"], self.approval["approved_action"]["approval_sha256"]
                )

    def test_the_spent_approvals_still_answer_to_their_own_hashes(self):
        for path in (V1_APPROVAL, V2_APPROVAL):
            action = load(path)["approved_action"]
            with self.subTest(approval=path.name):
                self.assertEqual(
                    self.gate._digest(action, action["hash_covers"]), action["approval_sha256"]
                )

    def test_the_record_names_both_and_reuses_neither(self):
        link = self.approval["relationship_to_the_spent_approvals"]
        self.assertTrue(link["this_is_a_third_approval_not_a_renewal"])
        self.assertEqual(len(link["prior_approvals"]), 2)
        for entry in link["prior_approvals"]:
            with self.subTest(record=entry["record"]):
                self.assertFalse(entry["reused"])


class TestAnApprovalToAskIsNotAnAnswer(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)

    def test_no_residual_closed_and_nothing_was_recomputed(self):
        scope = self.approval["scope"]
        self.assertEqual(scope["residuals_closed_by_this_mission"], 0)
        self.assertFalse(scope["qualification_recomputed"])
        self.assertFalse(scope["r1_touched"])
        self.assertFalse(scope["r2_a_touched"])
        self.assertTrue(scope["an_approval_to_ask_is_not_an_answer"])

    def test_r2_b_the_closure_and_the_qualification_are_untouched(self):
        self.assertEqual(load(THIRD_PARTY)["verdict"], "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED")
        self.assertEqual(
            load(CLOSURE)["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"], "UNRESOLVED"
        )
        qualification = load(QUALIFICATION)
        gates = {g["dimension"]: g["status"] for g in qualification["gates"]}
        self.assertEqual(gates["C9_RIGHTS_FEASIBILITY"], "PARTIAL")
        self.assertEqual(
            qualification["tally"], {"PASS": 11, "PARTIAL": 1, "FAIL": 0, "UNKNOWN": 0}
        )
        self.assertEqual(qualification["verdict"], "COUNTERPART_UNRESOLVED")

    def test_every_outward_counter_is_zero(self):
        accounting = self.approval["mission_accounting"]
        for counter in gate().HARD_ZERO:
            with self.subTest(counter=counter):
                self.assertEqual(accounting[counter], 0)

    def test_the_next_action_belongs_to_the_operator(self):
        action = self.approval["recommended_next_action"]
        self.assertEqual(action["performed_by"], "OPERATOR")
        self.assertTrue(action["this_repository_may_not_perform_it"])
        self.assertTrue(action["mission_1_77_not_started"])


class TestTheGateRefusesTheShortcuts(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.approval = load(APPROVAL)
        self.packet = load(PACKET)

    def rebind(self, approval):
        action = approval["approved_action"]
        action["approval_sha256"] = self.gate._digest(action, approval["hash_covers"])
        return approval

    def refused(self, checker, *args):
        with self.assertRaises(self.gate.ValidationError):
            checker(*args)

    def test_the_record_as_committed_passes(self):
        self.gate.validate()

    def test_a_copied_rather_than_recomputed_digest_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approval"]["hash_as_stated_by_the_operator"] = "0" * 64
        self.refused(self.gate._check_it_names_the_packet, approval, self.packet)

    def test_naming_a_body_that_is_not_the_frozen_one_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approval"]["approved_body_sha256"] = hashlib.sha256(b"other").hexdigest()
        self.refused(self.gate._check_it_names_the_packet, approval, self.packet)

    def test_denying_a_match_the_records_own_digests_show_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approval"]["approved_body_is_byte_identical_to_the_frozen_body"] = False
        self.refused(self.gate._check_it_names_the_packet, approval, self.packet)

    def test_an_approval_written_into_the_packet_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["operator_approval_recorded"] = True
        self.refused(self.gate._check_the_approval_stayed_out_of_the_packet, self.approval, packet)

    def test_a_packet_edited_to_claim_it_was_sent_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["sent"] = True
        self.refused(self.gate._check_the_approval_stayed_out_of_the_packet, self.approval, packet)

    def test_claiming_the_approval_lives_in_the_packet_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approval"]["approval_recorded_in_this_document_rather_than_in_the_packet"] = False
        self.refused(self.gate._check_the_approval_stayed_out_of_the_packet, approval, self.packet)

    def test_an_address_written_into_the_recipient_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["recipient"] = "d@globalping.io"
        self.refused(self.gate._check_the_action_is_bound, approval, self.packet)

    def test_hashing_the_recipient_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["hash_covers"] = sorted([*approval["hash_covers"], "recipient"])
        approval["approved_action"]["recipient"] = self.gate.RECIPIENT_SENTINEL
        self.refused(self.gate._check_the_action_is_bound, self.rebind(approval), self.packet)

    def test_a_second_outward_reply_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approved_action"]["maximum_outward_replies"] = 2
        self.refused(self.gate._check_the_action_is_bound, self.rebind(approval), self.packet)

    def test_a_different_mechanism_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approved_action"]["mechanism"] = "OPERATOR_MANUAL_EMAIL"
        self.refused(self.gate._check_the_action_is_bound, self.rebind(approval), self.packet)

    def test_an_edited_action_that_was_not_rebound_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["approved_action"]["approved_subject"] = "Something else"
        self.refused(self.gate._check_the_action_is_bound, approval, self.packet)

    def test_flipping_any_excluded_item_true_is_refused(self):
        for item in self.gate.NOT_AUTHORISED:
            with self.subTest(item=item):
                approval = copy.deepcopy(self.approval)
                approval["explicitly_not_authorised"][item] = True
                self.refused(self.gate._check_the_exclusions_hold, approval)

    def test_dropping_an_excluded_item_is_refused(self):
        for item in self.gate.NOT_AUTHORISED:
            with self.subTest(item=item):
                approval = copy.deepcopy(self.approval)
                approval["explicitly_not_authorised"].pop(item)
                self.refused(self.gate._check_the_exclusions_hold, approval)

    def pending(self):
        """The pre-send state, which must stay representable and stay strict."""
        approval = copy.deepcopy(self.approval)
        approval["execution"].update(
            {
                "status": "PENDING_MANUAL_OPERATOR_ACTION",
                "outward_replies_made": 0,
                "send_attempts": 0,
                "deliveries_confirmed": 0,
                "operator_attestation_recorded": False,
                "attestation_level": None,
            }
        )
        return approval

    def test_the_pending_state_is_still_representable(self):
        self.gate._check_execution(self.pending())

    def test_a_pending_execution_recording_a_send_is_refused(self):
        approval = self.pending()
        approval["execution"]["outward_replies_made"] = 1
        self.refused(self.gate._check_execution, approval)

    def test_a_pending_execution_recording_an_attestation_is_refused(self):
        approval = self.pending()
        approval["execution"]["operator_attestation_recorded"] = True
        self.refused(self.gate._check_execution, approval)

    def test_a_pending_execution_recording_a_provider_contact_is_refused(self):
        approval = self.pending()
        approval["execution"]["provider_contacted"] = True
        self.refused(self.gate._check_execution, approval)

    def test_byte_verified_is_refused_for_this_channel(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["attestation_levels_reachable_for_this_channel"] = [
            "OPERATOR_ATTESTED",
            "BYTE_VERIFIED",
        ]
        self.refused(self.gate._check_execution, approval)

    def test_claiming_byte_verification_is_possible_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["byte_verification_is_possible_for_this_channel"] = True
        self.refused(self.gate._check_execution, approval)

    def test_this_repository_sending_mail_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["emails_sent_by_this_repository"] = 1
        self.refused(self.gate._check_execution, approval)

    def test_a_mailbox_read_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["mailbox_read"] = True
        self.refused(self.gate._check_execution, approval)

    def test_weakening_an_integrity_rule_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["integrity_checks_frozen_before_any_send"][
            "one_approval_authorises_exactly_one_outward_reply"
        ] = False
        self.refused(self.gate._check_execution, approval)

    def test_recording_this_as_a_renewal_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["relationship_to_the_spent_approvals"][
            "this_is_a_third_approval_not_a_renewal"
        ] = False
        self.refused(self.gate._check_it_is_a_third_approval, approval, self.packet)

    def test_reusing_a_spent_approval_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["relationship_to_the_spent_approvals"]["prior_approvals"][0]["reused"] = True
        self.refused(self.gate._check_it_is_a_third_approval, approval, self.packet)

    def test_closing_a_residual_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["scope"]["residuals_closed_by_this_mission"] = 1
        self.refused(self.gate._check_nothing_moved, approval)

    def test_recomputing_the_qualification_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["scope"]["qualification_recomputed"] = True
        self.refused(self.gate._check_nothing_moved, approval)

    def test_any_outward_counter_above_zero_is_refused(self):
        for counter in self.gate.HARD_ZERO:
            with self.subTest(counter=counter):
                approval = copy.deepcopy(self.approval)
                approval["mission_accounting"][counter] = 1
                self.refused(self.gate._check_nothing_moved, approval)

    def test_letting_this_repository_perform_the_reply_is_refused(self):
        approval = copy.deepcopy(self.approval)
        approval["recommended_next_action"]["this_repository_may_not_perform_it"] = False
        self.refused(self.gate._check_nothing_moved, approval)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the records do not carry', RENDERER.read_text("utf-8"))


class TestTheOtherStatesStayRepresentable(unittest.TestCase):
    """A gate that only accepts the state we happen to be in is not a gate. Mission 1.76.3
    proved SENT was reachable while the record was pending; Mission 1.76.4 proves the
    reverse, plus the bounce this approval can still suffer."""

    def setUp(self):
        self.gate = gate()
        self.approval = load(APPROVAL)

    def test_the_sent_record_as_committed_is_accepted(self):
        self.gate._check_execution(self.approval)

    def test_a_failed_dispatch_is_accepted(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"].update(
            {"status": "DISPATCH_ATTEMPTED_DELIVERY_FAILED", "send_attempts": 1}
        )
        self.gate._check_execution(approval)

    def test_a_sent_reply_may_not_exceed_the_one_it_authorises(self):
        approval = copy.deepcopy(self.approval)
        approval["execution"]["outward_replies_made"] = 2
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_execution(approval)


class TestTheRendererAndGovernance(unittest.TestCase):
    def test_the_renderer_cannot_send_or_read_mail(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in ("smtplib", "imaplib", "requests", "httpx", "urllib", "subprocess"):
            with self.subTest(module=banned):
                self.assertNotIn(f"import {banned}", source)

    def test_the_page_reports_the_execution_state_and_the_sentinel(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn(load(APPROVAL)["execution"]["status"], text)
        self.assertIn(gate().RECIPIENT_SENTINEL, text)
        self.assertIn("GP-R2-B-Q1", text)

    def test_ci_runs_the_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_manifest_lists_the_record_and_the_renderer(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (APPROVAL, RENDERER):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_reports_exist(self):
        for name in ("mission-1.76.3-report.md", "mission-1.76.4-report.md"):
            with self.subTest(report=name):
                self.assertTrue((REPO_ROOT / "docs" / "reports" / name).exists())


if __name__ == "__main__":
    unittest.main()
