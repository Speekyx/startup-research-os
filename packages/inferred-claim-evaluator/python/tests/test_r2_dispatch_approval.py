"""Mission 1.74.2. The second enquiry approved, and the ceiling that comes with it.

The operator approved GP-R2-Q1 by OPERATOR_MANUAL_EMAIL to legal@globalping.io, the
address the Terms designate in section 16. This repository sends nothing.

The point of this file is that the rules INVERT against Mission 1.74.1, and both
inversions are properties of the CHANNEL rather than of manual sending:

    R1  public GitHub issue   every field pinned      BYTE_VERIFIED reachable
    R2  manual email          sender NOT pinned       BYTE_VERIFIED unreachable

A public repository and a GitHub identity are determined before the act, so R1's hash
could bind all four fields. A mail client's sender is not determined until the send --
Mission 1.65 stated that cost in advance, and here it recurs. And a mail client's
outbox is something no guard here can observe, so Mission 1.66's OPERATOR_ATTESTED
ceiling stands: this gate REFUSES BYTE_VERIFIED, where R1's requires it be possible.

Two approvals now exist and they are not one. Each names its own enquiry, mechanism
and recipient, and each authorises exactly one act. Mission 1.74's records are not
rewritten, and the R1 approval's binding fields are untouched -- it gained one
appended forward pointer and its digest still recomputes.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
R2_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
R1_PACKET = DATA / "globalping-r1-enquiry-packet-v1.json"
R1_APPROVAL = DATA / "globalping-r1-dispatch-approval-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v2.json"
RENDERER = SCRIPTS / "render_r2_dispatch_approval.py"
R1_RENDERER = SCRIPTS / "render_r1_dispatch_approval.py"
PAGE = DATA / "mission-1.74.2-r2-dispatch-approval-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

PLACEHOLDER_SENDER = "PLACEHOLDER_PERMITTED_FOR_MANUAL_SEND_ONLY"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(mapping: dict, keys) -> str:
    binding = {key: mapping[key] for key in keys}
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class TestTheApprovalExists(unittest.TestCase):
    """1 to 4."""

    def test_the_record_exists_and_names_this_mission(self):
        self.assertTrue(APPROVAL.exists())
        self.assertEqual(load(APPROVAL)["mission"], "1.74.2")

    def test_the_page_and_the_renderer_exist(self):
        self.assertTrue(PAGE.exists())
        self.assertTrue(RENDERER.exists())

    def test_an_approval_is_actually_carried(self):
        approval = load(APPROVAL)["approval"]
        self.assertTrue(approval["approval_given"])
        self.assertTrue(approval["approved_by"].strip())


class TestItNamesThePacketAsStored(unittest.TestCase):
    """5 to 10."""

    def setUp(self):
        self.approval = load(APPROVAL)
        self.packet = load(R2_PACKET)

    def test_the_packet_still_answers_to_its_own_hash(self):
        self.assertEqual(
            digest(self.packet, self.packet["hash_covers"]), self.packet["content_sha256"]
        )

    def test_the_approval_names_that_exact_hash(self):
        self.assertEqual(
            self.approval["approved_action"]["approved_content_sha256"],
            self.packet["content_sha256"],
        )

    def test_the_packet_file_hash_matches_the_bytes_on_disk(self):
        self.assertEqual(
            self.approval["approval"]["packet_file_sha256"],
            hashlib.sha256(R2_PACKET.read_bytes()).hexdigest(),
        )

    def test_the_approved_body_digest_matches_the_packet_body(self):
        self.assertEqual(
            self.approval["approval"]["approved_body_sha256"],
            hashlib.sha256(self.packet["body"].encode("utf-8")).hexdigest(),
        )

    def test_the_packet_was_not_edited(self):
        self.assertFalse(self.approval["approval"]["packet_edited_by_this_mission"])
        self.assertFalse(self.approval["approval"]["packet_content_sha256_changed"])
        self.assertTrue(self.approval["approval"]["hash_recomputed_from_the_packet_as_stored"])


class TestTheApprovalStayedOutOfThePacket(unittest.TestCase):
    """11 to 14."""

    def setUp(self):
        self.packet = load(R2_PACKET)

    def test_the_packet_records_no_approval_and_no_send(self):
        self.assertFalse(self.packet["operator_approval_recorded"])
        self.assertFalse(self.packet["sent"])
        self.assertFalse(self.packet["execution_record_created"])

    def test_the_packets_own_send_status_is_unchanged(self):
        self.assertEqual(self.packet["send_status"], "NOT_AUTHORIZED")

    def test_the_approval_lives_in_its_own_document(self):
        approval = load(APPROVAL)["approval"]
        self.assertTrue(approval["approval_recorded_in_this_document_rather_than_in_the_packet"])
        self.assertTrue(approval["why"].strip())


class TestTheActionIsBoundOnThreeFieldsOfFour(unittest.TestCase):
    """15 to 24. The Mission 1.65 cost, and it recurs here."""

    def setUp(self):
        self.action = load(APPROVAL)["approved_action"]
        self.packet = load(R2_PACKET)

    def test_the_approval_answers_to_its_own_hash(self):
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

    def test_the_recipient_is_the_terms_designated_address(self):
        self.assertEqual(self.action["recipient"], "legal@globalping.io")
        self.assertEqual(self.action["recipient"], self.packet["recipient"])
        self.assertFalse(self.packet["recipient_guessed"])

    def test_the_subject_and_channel_come_from_the_packet(self):
        self.assertEqual(self.action["approved_subject"], self.packet["subject"])
        self.assertEqual(self.action["channel"], self.packet["channel"])
        self.assertEqual(self.action["channel"], "PROVIDER_DESIGNATED_TERMS_CHANNEL")

    def test_it_approves_the_enquiry_the_packet_carries(self):
        self.assertEqual(self.action["approves"], self.packet["question_id"])
        self.assertEqual(self.action["approves"], "GP-R2-Q1")

    def test_exactly_one_send_is_authorised(self):
        self.assertEqual(self.action["maximum_sends"], 1)

    def test_the_sender_is_a_placeholder_and_is_not_bound(self):
        self.assertEqual(self.action["sender"], PLACEHOLDER_SENDER)
        self.assertFalse(self.action["sender_is_bound_by_the_hash"])
        self.assertFalse(self.action["every_binding_field_is_pinned"])

    def test_the_cost_of_the_unpinned_sender_is_stated(self):
        self.assertTrue(self.action["why_the_sender_is_not_pinned"].strip())
        self.assertTrue(self.action["why_that_differs_from_mission_1_74_1"].strip())


class TestTheCeilingInvertsAgainstR1(unittest.TestCase):
    """25 to 32. The finding this mission exists to record."""

    def setUp(self):
        self.execution = load(APPROVAL)["execution"]

    def test_byte_verification_is_unreachable_for_this_channel(self):
        self.assertFalse(self.execution["byte_verification_is_possible_for_this_channel"])

    def test_only_operator_attested_is_reachable(self):
        self.assertEqual(
            self.execution["attestation_levels_reachable_for_this_channel"],
            ["OPERATOR_ATTESTED"],
        )

    def test_r1_reaches_the_level_this_one_cannot(self):
        # The two gates must not agree here, or one of them is asserting something false.
        r1 = load(R1_APPROVAL)["execution"]
        self.assertTrue(r1["byte_verification_is_possible_for_this_channel"])
        self.assertIn("BYTE_VERIFIED", r1["attestation_levels_defined"])

    def test_the_reason_is_recorded_and_names_the_channel(self):
        self.assertTrue(self.execution["why_byte_verification_is_unreachable_here"].strip())

    def test_there_is_no_upgrade_path_and_it_says_so(self):
        self.assertIn("NONE", self.execution["upgrade_path"])

    def test_the_r1_gate_requires_what_this_gate_refuses(self):
        r1_source = R1_RENDERER.read_text(encoding="utf-8")
        r2_source = RENDERER.read_text(encoding="utf-8")
        self.assertIn("byte_verification_is_possible_for_this_channel", r1_source)
        self.assertIn("byte_verification_is_possible_for_this_channel", r2_source)
        # R1 refuses a denial; R2 refuses a claim. Opposite polarity, same field.
        self.assertIn("the record denies that a public issue can be byte-verified", r1_source)
        self.assertIn("the record claims a manual mail send can be byte-verified", r2_source)


class TestAnApprovalIsNotAnExecution(unittest.TestCase):
    """33 to 40."""

    def setUp(self):
        self.execution = load(APPROVAL)["execution"]

    def test_the_status_is_pending(self):
        self.assertEqual(self.execution["status"], "PENDING_MANUAL_OPERATOR_ACTION")

    def test_nothing_was_sent(self):
        self.assertEqual(self.execution["sends_made"], 0)
        self.assertEqual(self.execution["emails_sent_by_this_repository"], 0)

    def test_no_mail_connector_was_used(self):
        self.assertFalse(self.execution["mail_connector_used"])
        self.assertTrue(self.execution["mail_connector_note"].strip())

    def test_no_mailbox_was_searched(self):
        self.assertFalse(self.execution["mailbox_searched"])

    def test_no_attestation_exists_yet(self):
        self.assertFalse(self.execution["operator_attestation_recorded"])
        self.assertIsNone(self.execution["attestation_level"])

    def test_the_only_route_to_sent_is_stated(self):
        self.assertTrue(self.execution["reachable_only_through"].strip())


class TestTheIntegrityRulesAreFrozen(unittest.TestCase):
    """41 to 44."""

    def setUp(self):
        self.checks = load(APPROVAL)["integrity_checks_frozen_before_any_send"]

    def test_every_rule_holds(self):
        for flag, value in self.checks.items():
            if flag.startswith("$"):
                continue
            with self.subTest(rule=flag):
                self.assertTrue(value)

    def test_a_duplicate_send_is_reported_rather_than_tidied_away(self):
        self.assertTrue(
            self.checks["a_second_send_is_reported_as_a_duplicate_not_silently_accepted"]
        )

    def test_a_non_placeholder_sender_is_manual_send_only(self):
        self.assertTrue(
            self.checks["a_sender_other_than_the_placeholder_is_admitted_only_under_manual_send"]
        )


class TestTwoApprovalsAreNotOne(unittest.TestCase):
    """45 to 54."""

    def setUp(self):
        self.scope = load(APPROVAL)["scope"]

    def test_this_one_approves_exactly_one_enquiry(self):
        self.assertEqual(self.scope["approved_enquiries"], ["GP-R2-Q1"])

    def test_both_are_now_approved_separately_and_the_record_says_why_that_matters(self):
        self.assertTrue(self.scope["both_enquiries_now_approved_separately"])
        self.assertTrue(self.scope["and_that_is_not_one_approval_covering_both"].strip())

    def test_the_r1_approvals_binding_fields_are_untouched(self):
        action = load(R1_APPROVAL)["approved_action"]
        self.assertEqual(digest(action, action["hash_covers"]), action["approval_sha256"])
        self.assertFalse(self.scope["r1_approval_edited"])

    def test_the_r1_record_gained_only_an_appended_forward_pointer(self):
        r1 = load(R1_APPROVAL)
        pointer = r1["forward_pointer"]
        self.assertEqual(pointer["continued_by"], APPROVAL.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(pointer["appended_by_mission"], "1.74.2")
        self.assertTrue(pointer["approval_sha256_unchanged"])

    def test_the_snapshot_records_what_1_74_2_observed_and_is_not_a_live_constraint(self):
        # Corrected in Mission 1.74.3. This field was named r1_execution_state_unchanged
        # and compared LIVE, which refused the very transition the R1 approval was built
        # to make. It is a snapshot of history; R1 has since legitimately reached SENT.
        self.assertEqual(
            self.scope["r1_execution_state_when_this_was_written"],
            "PENDING_MANUAL_OPERATOR_ACTION",
        )
        self.assertEqual(load(R1_APPROVAL)["execution"]["status"], "SENT")

    def test_r1_stayed_within_what_r1_authorised(self):
        r1 = load(R1_APPROVAL)
        self.assertLessEqual(
            r1["execution"]["public_posts_made"],
            r1["approved_action"]["maximum_public_posts"],
        )

    def test_the_r1_packet_is_untouched(self):
        packet = load(R1_PACKET)
        self.assertEqual(packet["send_status"], "NOT_AUTHORIZED")
        self.assertFalse(packet["sent"])
        self.assertFalse(packet["operator_approval_recorded"])

    def test_an_approval_to_ask_is_not_an_answer(self):
        self.assertEqual(self.scope["residuals_closed_by_this_mission"], 0)
        self.assertTrue(self.scope["an_approval_to_ask_is_not_an_answer"])
        self.assertFalse(self.scope["qualification_recomputed"])

    def test_the_qualification_is_unchanged(self):
        qualification = load(QUALIFICATION)
        tally = qualification["tally"]
        self.assertEqual((tally["PASS"], tally["PARTIAL"], tally["FAIL"]), (10, 2, 0))
        self.assertEqual(qualification["verdict"], "COUNTERPART_UNRESOLVED")


class TestMission174WasNotRewritten(unittest.TestCase):
    """55 to 57."""

    def test_the_closure_still_reports_nothing_sent_and_two_residuals(self):
        closure = load(CLOSURE)
        self.assertEqual(closure["enquiries"]["enquiries_sent"], 0)
        self.assertEqual(closure["residuals_remaining"], 2)
        self.assertFalse(closure["enquiries"]["dispatch_authorised_by_this_mission"])

    def test_the_record_says_neither_earlier_mission_was_edited(self):
        parallel = load(APPROVAL)["parallel_state_untouched"]
        self.assertFalse(parallel["mission_1_74_records_edited"])
        self.assertFalse(parallel["mission_1_74_1_approval_fields_edited"])


class TestNothingMoved(unittest.TestCase):
    """58 to 61."""

    def setUp(self):
        self.approval = load(APPROVAL)

    def test_every_counter_is_zero(self):
        for counter, value in self.approval["mission_accounting"].items():
            with self.subTest(counter=counter):
                self.assertEqual(value, 0)

    def test_no_parallel_arc_was_touched(self):
        parallel = self.approval["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        self.assertEqual(parallel["netlas_contact_state"], "STILL_PENDING")
        for flag in (
            "onyphe_mailbox_searched",
            "netlas_enquiry_sent",
            "scanner_arc_reopened",
            "adr_039_weakened",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(parallel[flag])

    def test_the_next_action_belongs_to_the_operator(self):
        action = self.approval["recommended_next_action"]
        self.assertEqual(action["performed_by"], "OPERATOR")
        self.assertTrue(action["this_repository_may_not_perform_it"])
        self.assertTrue(action["attestation_is_the_only_evidence_this_channel_can_produce"])
        self.assertTrue(action["mission_1_75_not_started"])

    def test_no_predicate_was_frozen_and_no_target_value_retrieved(self):
        self.assertFalse(self.approval["exact_predicate_frozen"])
        self.assertEqual(self.approval["target_values_retrieved"], 0)


class TestTheRenderer(unittest.TestCase):
    """62 to 67."""

    def setUp(self):
        self.source = RENDERER.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_it_cannot_send_mail(self):
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for banned in ("smtplib", "email", "subprocess", "os", "socket", "requests", "httpx"):
            with self.subTest(module=banned):
                self.assertNotIn(banned, imported)

    def test_it_makes_no_process_spawning_call(self):
        spawners = {
            "system",
            "popen",
            "run",
            "check_call",
            "check_output",
            "Popen",
            "sendmail",
            "send_message",
        }
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                with self.subTest(call=node.func.attr):
                    self.assertNotIn(node.func.attr, spawners)

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

    def test_the_page_reports_the_pending_status_and_the_placeholder_sender(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("PENDING_MANUAL_OPERATOR_ACTION", text)
        self.assertIn("legal@globalping.io", text)
        self.assertIn(PLACEHOLDER_SENDER, text)


class TestGovernanceRecordsThis(unittest.TestCase):
    """68 to 70."""

    def test_the_manifest_lists_the_record_and_the_renderer(self):
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertIn(APPROVAL.name, text)
        self.assertIn(RENDERER.name, text)

    def test_ci_runs_both_approval_gates(self):
        text = CI.read_text(encoding="utf-8")
        self.assertIn(RENDERER.name, text)
        self.assertIn(R1_RENDERER.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "architecture" / "mission-1.74.2-report.md").exists())


if __name__ == "__main__":
    unittest.main()
