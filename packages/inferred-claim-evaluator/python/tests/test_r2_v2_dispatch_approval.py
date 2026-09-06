"""Mission 1.74.5. The second approval, and the first one stays spent.

The operator approved exactly one manual send of the v2 packet to d@globalping.io.
Three things this file defends.

A QUOTED DIGEST IS RECOMPUTED, NOT COPIED. The approval arrived carrying a content
hash. Copying it would make the approval name whatever the instruction said rather
than whatever the packet is, so the record stores both the stated and the recomputed
digest and the gate refuses them disagreeing -- which turns a quoted string into a
check that could have failed.

A SECOND APPROVAL IS NOT A RENEWAL OF A SPENT ONE. The recipient changed, and the
recipient is a bound field, so this authorises a different action. The earlier
approval stays exhausted, its attempt stays a failure, and its provider_contacted
stays false; the gate asserts all three, so a later edit that quietly rehabilitated
the bounce fails here rather than passing quietly.

THE CEILING BELONGS TO THE MEDIUM, NOT TO THE ADDRESS. The address changed and the
medium did not, so BYTE_VERIFIED stays unreachable: a mail client's outbox is
something no guard here can observe.

Mission 1.74.6 recorded the send and added the fourth.

A SEND IS NOT A DELIVERY. A send is an act by the sender; a delivery is an outcome at
the receiver. The attestation establishes the first and is silent on the second, so
the record carries an explicit delivery status, UNCONFIRMED forbids a counted
delivery and forbids provider_contacted, and CONFIRMED must name a source that is not
the attestation of sending. This arc supplies its own proof that the two come apart:
the v1 message was sent too, and then it bounced.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

APPROVAL = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
V2_PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
V1_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
RENDERER = SCRIPTS / "render_r2_v2_dispatch_approval.py"
PAGE = DATA / "mission-1.74.5-r2-v2-dispatch-approval-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

PLACEHOLDER_SENDER = "PLACEHOLDER_PERMITTED_FOR_MANUAL_SEND_ONLY"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    """The renderer, loaded as a module so its checks can be run against dicts.

    Importing it touches no file: it defines paths and constants, and `main` is
    guarded. Running its helpers directly is the difference between asserting that a
    refusal is spelled in the source and asserting that it fires.
    """
    spec = importlib.util.spec_from_file_location("render_r2_v2_dispatch_approval", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(mapping: dict, keys) -> str:
    binding = {key: mapping[key] for key in keys}
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class TestAQuotedDigestIsRecomputed(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)
        self.packet = load(V2_PACKET)

    def test_the_record_exists_and_carries_an_approval(self):
        self.assertEqual(self.approval["mission"], "1.74.5")
        self.assertTrue(self.approval["approval"]["approval_given"])
        self.assertTrue(self.approval["approval"]["approved_by"].strip())

    def test_the_packet_answers_to_its_own_hash(self):
        self.assertEqual(
            digest(self.packet, self.packet["hash_covers"]), self.packet["content_sha256"]
        )

    def test_the_stated_and_recomputed_digests_agree(self):
        stated = self.approval["approval"]["hash_as_stated_by_the_operator"]
        self.assertEqual(stated, self.packet["content_sha256"])
        self.assertEqual(
            self.approval["approved_action"]["approved_content_sha256"],
            self.packet["content_sha256"],
        )
        self.assertTrue(self.approval["approval"]["recomputed_hash_matches_the_stated_one"])

    def test_the_record_says_why_it_recomputed_rather_than_copied(self):
        self.assertTrue(self.approval["approval"]["hash_recomputed_from_the_packet_as_stored"])
        self.assertTrue(
            self.approval["approval"]["why_it_was_recomputed_rather_than_copied"].strip()
        )

    def test_the_packet_file_hash_matches_the_bytes_on_disk(self):
        self.assertEqual(
            self.approval["approval"]["packet_file_sha256"],
            hashlib.sha256(V2_PACKET.read_bytes()).hexdigest(),
        )

    def test_the_packet_was_not_edited(self):
        self.assertFalse(self.approval["approval"]["packet_edited_by_this_mission"])
        self.assertFalse(self.approval["approval"]["packet_content_sha256_changed"])
        self.assertEqual(
            self.approval["approval"]["approved_body_sha256"],
            hashlib.sha256(self.packet["body"].encode("utf-8")).hexdigest(),
        )


class TestTheApprovalStayedOutOfThePacket(unittest.TestCase):
    def setUp(self):
        self.packet = load(V2_PACKET)

    def test_the_packet_records_no_approval_and_no_send(self):
        self.assertFalse(self.packet["operator_approval_recorded"])
        self.assertFalse(self.packet["sent"])
        self.assertFalse(self.packet["execution_record_created"])

    def test_the_packets_own_send_status_is_unchanged(self):
        self.assertEqual(self.packet["send_status"], "NOT_AUTHORIZED")

    def test_the_approval_lives_in_its_own_document(self):
        block = load(APPROVAL)["approval"]
        self.assertTrue(block["approval_recorded_in_this_document_rather_than_in_the_packet"])
        self.assertTrue(block["why"].strip())


class TestTheActionIsBound(unittest.TestCase):
    def setUp(self):
        self.action = load(APPROVAL)["approved_action"]
        self.packet = load(V2_PACKET)

    def test_it_answers_to_its_own_hash(self):
        self.assertEqual(
            digest(self.action, self.action["hash_covers"]), self.action["approval_sha256"]
        )

    def test_it_excludes_its_digest_the_status_the_date_and_the_sender(self):
        for excluded in ("approval_sha256", "execution", "recorded_at", "sender"):
            with self.subTest(field=excluded):
                self.assertNotIn(excluded, self.action["hash_covers"])
                self.assertIn(excluded, self.action["hash_excludes"])

    def test_the_mechanism_is_the_manual_mail_channel(self):
        self.assertEqual(self.action["mechanism"], "OPERATOR_MANUAL_EMAIL")

    def test_the_recipient_channel_and_subject_come_from_the_packet(self):
        self.assertEqual(self.action["recipient"], self.packet["recipient"])
        self.assertEqual(self.action["recipient"], "d@globalping.io")
        self.assertEqual(self.action["channel"], self.packet["channel"])
        self.assertEqual(self.action["approved_subject"], self.packet["subject"])

    def test_it_names_the_right_packet_version(self):
        self.assertEqual(self.action["approves"], self.packet["question_id"])
        self.assertEqual(self.action["packet_version"], self.packet["packet_version"])
        self.assertEqual(self.action["packet_version"], 2)

    def test_exactly_one_send_is_authorised(self):
        self.assertEqual(self.action["maximum_sends"], 1)

    def test_the_sender_stays_open_at_the_operators_instruction(self):
        self.assertEqual(self.action["sender"], PLACEHOLDER_SENDER)
        self.assertFalse(self.action["sender_is_bound_by_the_hash"])
        self.assertFalse(self.action["every_binding_field_is_pinned"])
        self.assertTrue(self.action["sender_left_open_at_the_operators_explicit_instruction"])
        self.assertTrue(self.action["why_the_sender_is_not_pinned"].strip())


class TestTheDispatchWasPerformedAndAttested(unittest.TestCase):
    """One send happened. Every fact about it is the operator's word, and the record
    has to say that rather than reading as though something checked it."""

    def setUp(self):
        self.approval = load(APPROVAL)
        self.execution = self.approval["execution"]

    def test_the_status_is_sent_and_names_the_mission_that_moved_it(self):
        self.assertEqual(self.execution["status"], "SENT")
        self.assertEqual(self.execution["recorded_by_mission"], "1.74.6")
        self.assertEqual(self.approval["execution_recorded_by_mission"], "1.74.6")

    def test_the_approval_keeps_its_own_mission(self):
        self.assertEqual(self.approval["mission"], "1.74.5")

    def test_exactly_one_send_under_a_one_send_approval(self):
        self.assertEqual(self.execution["sends_made"], 1)
        self.assertEqual(self.execution["send_attempts"], 1)
        self.assertTrue(self.execution["dispatch_performed"])
        self.assertEqual(self.approval["approved_action"]["maximum_sends"], 1)

    def test_the_attestation_names_an_attester_and_a_statement(self):
        self.assertEqual(self.execution["attested_by"], "operator")
        self.assertTrue(self.execution["attestation_statement"].strip())
        self.assertTrue(self.execution["operator_attestation_recorded"])
        self.assertEqual(self.execution["attestation_level"], "OPERATOR_ATTESTED")

    def test_the_attested_recipient_and_subject_are_the_approved_ones(self):
        action = self.approval["approved_action"]
        self.assertEqual(self.execution["attested_recipient"], action["recipient"])
        self.assertEqual(self.execution["attested_subject"], action["approved_subject"])

    def test_the_sender_is_real_and_was_not_written_back_into_the_approval(self):
        self.assertNotEqual(self.execution["attested_sender"], PLACEHOLDER_SENDER)
        self.assertIn("@", self.execution["attested_sender"])
        self.assertEqual(self.approval["approved_action"]["sender"], PLACEHOLDER_SENDER)
        self.assertFalse(self.execution["sender_written_back_into_the_approval"])
        self.assertTrue(self.execution["sender_supplied_only_by_the_attestation"])

    def test_the_send_time_carries_an_offset_and_does_not_precede_the_approval(self):
        sent_at = self.execution["sent_at"]
        self.assertRegex(sent_at, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)$")
        self.assertTrue(self.execution["sent_at_carries_an_explicit_offset"])
        self.assertGreaterEqual(sent_at[:10], self.approval["recorded_at"])

    def test_no_message_id_was_invented(self):
        self.assertIsNone(self.execution["message_id"])
        self.assertFalse(self.execution["message_id_available"])
        self.assertTrue(self.execution["why_there_is_no_message_id"].strip())

    def test_the_body_that_left_was_not_compared_by_this_repository(self):
        self.assertEqual(self.execution["body_used_per_attestation"], "THE_FROZEN_PACKET_BODY")
        self.assertFalse(self.execution["body_compared_by_this_repository"])
        self.assertTrue(self.execution["why_the_body_was_not_compared"].strip())

    def test_the_attestation_says_what_it_does_not_cover(self):
        covers = self.execution["attestation_covers"]
        uncovered = self.execution["attestation_does_not_cover"]
        self.assertTrue(covers)
        self.assertIn("delivery", uncovered)
        self.assertIn("a reply", uncovered)
        self.assertEqual(set(covers) & set(uncovered), set())

    def test_the_approval_is_spent_by_the_send(self):
        self.assertTrue(self.execution["approval_exhausted"])
        self.assertTrue(self.execution["a_resend_requires_a_new_operator_approval"])

    def test_this_repository_sent_nothing_and_read_nothing(self):
        self.assertEqual(self.execution["emails_sent_by_this_repository"], 0)
        self.assertFalse(self.execution["mail_connector_used"])
        self.assertFalse(self.execution["mailbox_searched"])

    def test_no_reply_is_claimed(self):
        self.assertFalse(self.execution["provider_replied"])
        self.assertFalse(self.execution["reply_recorded"])
        self.assertTrue(self.execution["why_no_reply_is_recorded"].strip())

    def test_the_ceiling_belongs_to_the_medium(self):
        self.assertFalse(self.execution["byte_verification_is_possible_for_this_channel"])
        self.assertEqual(
            self.execution["attestation_levels_reachable_for_this_channel"],
            ["OPERATOR_ATTESTED"],
        )
        self.assertIn("NONE", self.execution["upgrade_path"])
        self.assertTrue(self.execution["why_byte_verification_is_unreachable_here"].strip())


class TestASendIsNotADelivery(unittest.TestCase):
    """The send is attested. The delivery is not, and the record may not close the gap."""

    def setUp(self):
        self.execution = load(APPROVAL)["execution"]
        self.delivery = self.execution["delivery"]

    def test_the_delivery_is_unconfirmed(self):
        self.assertEqual(self.delivery["delivery_status"], "UNCONFIRMED")
        self.assertIsNone(self.delivery["delivery_established_by"])
        self.assertEqual(self.execution["deliveries_confirmed"], 0)

    def test_the_provider_is_not_marked_contacted(self):
        self.assertFalse(self.execution["provider_contacted"])
        self.assertTrue(self.execution["why_provider_contacted_is_false"].strip())

    def test_silence_is_not_treated_as_evidence(self):
        self.assertTrue(self.delivery["absence_of_a_reported_bounce_is_not_evidence"])
        self.assertTrue(self.delivery["why_silence_is_not_evidence"].strip())

    def test_the_state_can_still_move(self):
        self.assertTrue(self.delivery["a_later_bounce_would_move_this_to_FAILED"])
        self.assertTrue(self.delivery["a_later_delivery_confirmation_would_need_its_own_source"])

    def test_the_reason_names_the_v1_bounce_as_the_proof_the_two_come_apart(self):
        self.assertIn("bounce", self.delivery["why_delivery_is_unconfirmed"])


class TestTheGateRefusesADeliveryItCannotSee(unittest.TestCase):
    """Run the gate's own checks against mutated copies, rather than reading its source.

    A refusal spelled in a module is not a refusal until something calls it.
    """

    def setUp(self):
        self.gate = gate()
        self.approval = load(APPROVAL)
        self.execution = copy.deepcopy(self.approval["execution"])

    def refused(self, execution):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_delivery_was_not_inferred(execution)

    def test_the_record_as_committed_passes(self):
        self.gate._check_delivery_was_not_inferred(self.execution)
        self.gate._check_the_send_is_attested(self.approval, self.execution)

    def test_an_unconfirmed_delivery_may_not_count_one(self):
        self.execution["deliveries_confirmed"] = 1
        self.refused(self.execution)

    def test_an_unconfirmed_delivery_may_not_mark_a_contact(self):
        self.execution["provider_contacted"] = True
        self.refused(self.execution)

    def test_a_delivery_may_not_be_established_by_the_attestation_of_sending(self):
        for source in (
            "OPERATOR_SEND_ATTESTATION",
            "THE_ATTESTATION_OF_SENDING",
            "OPERATOR_ATTESTED",
        ):
            with self.subTest(source=source):
                execution = copy.deepcopy(self.execution)
                execution["delivery"]["delivery_status"] = "CONFIRMED"
                execution["delivery"]["delivery_established_by"] = source
                execution["deliveries_confirmed"] = 1
                self.refused(execution)

    def test_a_confirmed_delivery_must_name_a_source(self):
        self.execution["delivery"]["delivery_status"] = "CONFIRMED"
        self.execution["deliveries_confirmed"] = 1
        self.refused(self.execution)

    def test_a_delivery_confirmed_by_another_source_is_representable(self):
        self.execution["delivery"]["delivery_status"] = "CONFIRMED"
        self.execution["delivery"]["delivery_established_by"] = "a reply from the provider"
        self.execution["deliveries_confirmed"] = 1
        self.execution["provider_contacted"] = True
        self.gate._check_delivery_was_not_inferred(self.execution)

    def test_a_failed_delivery_is_not_recorded_under_sent(self):
        self.execution["delivery"]["delivery_status"] = "FAILED"
        self.refused(self.execution)

    def test_an_undefined_delivery_status_is_refused(self):
        self.execution["delivery"]["delivery_status"] = "DELIVERED"
        self.refused(self.execution)

    def refused_send(self, execution, approval=None):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_send_is_attested(approval or self.approval, execution)

    def test_the_placeholder_may_not_be_attested_as_the_sender(self):
        self.execution["attested_sender"] = PLACEHOLDER_SENDER
        self.refused_send(self.execution)

    def test_the_sender_may_not_be_written_back_into_the_approval(self):
        approval = copy.deepcopy(self.approval)
        approval["approved_action"]["sender"] = "thib.chm@gmail.com"
        self.refused_send(self.execution, approval)

    def test_a_message_id_is_refused(self):
        self.execution["message_id"] = "<CA+abc@mail.gmail.com>"
        self.refused_send(self.execution)

    def test_a_send_time_without_an_offset_is_refused(self):
        self.execution["sent_at"] = "2026-09-06T19:39:00"
        self.refused_send(self.execution)

    def test_a_send_attested_before_its_approval_is_refused(self):
        self.execution["sent_at"] = "2026-09-05T19:39:00+04:00"
        self.refused_send(self.execution)

    def test_a_second_send_under_a_one_send_approval_is_refused(self):
        self.execution["sends_made"] = 2
        self.refused_send(self.execution)

    def test_a_claimed_body_comparison_is_refused(self):
        self.execution["body_compared_by_this_repository"] = True
        self.refused_send(self.execution)

    def test_an_attestation_that_covers_delivery_is_refused(self):
        self.execution["attestation_does_not_cover"] = ["a reply"]
        self.refused_send(self.execution)

    def test_a_reply_may_not_be_claimed_here(self):
        record = copy.deepcopy(self.approval)
        record["execution"]["provider_replied"] = True
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_execution(record)

    def test_a_bounce_after_this_send_stays_representable(self):
        record = copy.deepcopy(self.approval)
        execution = record["execution"]
        execution["status"] = "DISPATCH_ATTEMPTED_DELIVERY_FAILED"
        execution["attestation_level"] = None
        self.gate._check_execution(record)


class TestASecondApprovalIsNotARenewal(unittest.TestCase):
    """31 to 40. The spent approval is not rehabilitated."""

    def setUp(self):
        self.link = load(APPROVAL)["relationship_to_the_exhausted_approval"]
        self.prior = load(V1_APPROVAL)

    def test_the_prior_approval_was_not_reused_or_edited(self):
        self.assertFalse(self.link["prior_approval_reused"])
        self.assertFalse(self.link["prior_approval_edited_by_this_mission"])
        self.assertTrue(self.link["this_is_a_second_approval_not_a_renewal"])
        self.assertTrue(self.link["why"].strip())

    def test_the_prior_attempt_is_still_a_failure(self):
        self.assertEqual(self.prior["execution"]["status"], "DISPATCH_ATTEMPTED_DELIVERY_FAILED")
        self.assertFalse(self.link["prior_attempt_reinterpreted_as_delivered"])

    def test_the_prior_bounce_still_contacted_nobody(self):
        self.assertFalse(self.prior["execution"]["provider_contacted"])
        self.assertFalse(self.link["prior_provider_contacted_expected"])

    def test_the_prior_approval_is_still_exhausted(self):
        self.assertTrue(self.prior["execution"]["approval_exhausted"])

    def test_the_prior_approval_still_answers_to_its_own_hash(self):
        action = self.prior["approved_action"]
        self.assertEqual(digest(action, action["hash_covers"]), action["approval_sha256"])

    def test_the_two_approvals_name_different_documents_and_recipients(self):
        approval = load(APPROVAL)["approved_action"]
        prior = self.prior["approved_action"]
        self.assertNotEqual(prior["approved_content_sha256"], approval["approved_content_sha256"])
        self.assertNotEqual(prior["recipient"], approval["recipient"])
        self.assertNotEqual(prior["approval_sha256"], approval["approval_sha256"])

    def test_the_prior_record_gained_only_an_appended_forward_pointer(self):
        pointer = self.prior["forward_pointer"]
        self.assertEqual(pointer["continued_by"], APPROVAL.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(pointer["appended_by_mission"], "1.74.5")
        self.assertTrue(pointer["this_approval_was_not_reused"])
        self.assertTrue(pointer["approval_sha256_unchanged"])


class TestScopeAndAccounting(unittest.TestCase):
    def setUp(self):
        self.approval = load(APPROVAL)

    def test_only_the_v2_packet_is_approved(self):
        self.assertEqual(self.approval["scope"]["approved_enquiries"], ["GP-R2-Q1 v2"])
        self.assertFalse(self.approval["scope"]["r1_touched"])

    def test_an_approval_to_ask_is_not_an_answer(self):
        scope = self.approval["scope"]
        self.assertEqual(scope["residuals_closed_by_this_mission"], 0)
        self.assertTrue(scope["an_approval_to_ask_is_not_an_answer"])
        self.assertFalse(scope["qualification_recomputed"])
        self.assertEqual(
            scope["r2_verdict_unchanged"],
            "R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED",
        )

    def test_a_sent_question_is_not_an_answer_either(self):
        scope = self.approval["scope"]
        self.assertTrue(scope["a_sent_question_is_not_an_answer"])
        self.assertFalse(scope["r2_closed"])
        self.assertFalse(scope["qualification_recomputed_from_the_fact_of_dispatch"])
        self.assertTrue(scope["why_dispatch_changes_no_verdict"].strip())

    def test_the_counters_stay_zero_because_they_count_this_repository(self):
        accounting = self.approval["mission_accounting"]
        self.assertEqual(accounting["EMAILS_SENT"], 0)
        self.assertEqual(accounting["PROVIDER_CONTACTS"], 0)
        self.assertEqual(self.approval["execution"]["emails_sent_by_this_repository"], 0)
        self.assertEqual(self.approval["execution"]["sends_made"], 1)

    def test_every_counter_is_zero(self):
        for counter, value in self.approval["mission_accounting"].items():
            with self.subTest(counter=counter):
                self.assertEqual(value, 0)

    def test_no_parallel_arc_was_touched(self):
        parallel = self.approval["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        self.assertEqual(parallel["netlas_contact_state"], "STILL_PENDING")
        for flag in ("scanner_arc_reopened", "adr_039_weakened", "mission_1_74_records_edited"):
            with self.subTest(flag=flag):
                self.assertFalse(parallel[flag])

    def test_the_next_action_belongs_to_the_operator(self):
        action = self.approval["recommended_next_action"]
        self.assertEqual(action["performed_by"], "OPERATOR")
        self.assertTrue(action["this_repository_may_not_perform_it"])
        self.assertTrue(action["attestation_is_the_only_evidence_this_channel_can_produce"])
        self.assertTrue(action["mission_1_75_not_started"])

    def test_a_bounce_would_exhaust_this_approval_too(self):
        checks = self.approval["integrity_checks_frozen_before_any_send"]
        self.assertTrue(checks["an_attempt_that_bounces_exhausts_this_approval_too"])
        for flag, value in checks.items():
            if flag.startswith("$"):
                continue
            with self.subTest(rule=flag):
                self.assertTrue(value)


class TestTheRenderer(unittest.TestCase):
    def setUp(self):
        self.source = RENDERER.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_it_cannot_send_mail_or_spawn_a_process(self):
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for banned in ("smtplib", "email", "subprocess", "os", "socket", "requests", "httpx"):
            with self.subTest(module=banned):
                self.assertNotIn(banned, imported)

    def test_it_reads_no_clock(self):
        for banned in ("datetime.now", "utcnow", "time.time("):
            with self.subTest(call=banned):
                self.assertNotIn(banned, self.source)

    def test_it_defines_a_validation_error_and_a_validate(self):
        names = {
            node.name
            for node in ast.walk(self.tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }
        self.assertIn("ValidationError", names)
        self.assertIn("validate", names)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the record does not carry', self.source)

    def test_the_page_reports_the_dispatch_and_both_approvals(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("SENT", text)
        self.assertIn("d@globalping.io", text)
        self.assertIn("legal@globalping.io", text)
        self.assertIn("DISPATCH_ATTEMPTED_DELIVERY_FAILED", text)

    def test_the_page_separates_the_send_from_the_delivery(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("A send is not a delivery", text)
        self.assertIn("UNCONFIRMED", text)
        self.assertIn("recorded by Mission 1.74.6", text)
        self.assertIn(load(APPROVAL)["execution"]["attested_sender"], text)


class TestGovernanceRecordsThis(unittest.TestCase):
    def test_the_manifest_lists_the_record_and_the_renderer(self):
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertIn(APPROVAL.name, text)
        self.assertIn(RENDERER.name, text)

    def test_ci_runs_the_new_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "architecture" / "mission-1.74.5-report.md").exists())

    def test_the_dispatch_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "architecture" / "mission-1.74.6-report.md").exists())


if __name__ == "__main__":
    unittest.main()
