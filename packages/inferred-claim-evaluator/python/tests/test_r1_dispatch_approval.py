"""Mission 1.74.1. One enquiry approved for dispatch, and nothing posted.

The operator approved GP-R1-Q1 and only GP-R1-Q1, by a named mechanism:
OPERATOR_MANUAL_GITHUB_ISSUE, one public issue on jsdelivr/globalping under @Speekyx,
carrying the frozen title and body. This repository does not perform it.

The distinction the whole file defends is Mission 1.66's: AN APPROVAL IS NOT AN
EXECUTION. It is unusually easy to lose here, because once the approval exists every
field an execution record would need is already known -- mechanism, target, identity,
title and body are all pinned -- so a record could fill itself in completely and be
entirely fictional. SENT is reachable only through an explicit operator attestation.

Two things differ from the ONYPHE arc, and both are recorded rather than assumed.
The approval binds EVERY field of the action, where Mission 1.65 could bind only three
of four because a manual email's sender is not determined until the send; a public
repository is determined in advance. And BYTE_VERIFIED is reachable here, because a
public issue has a durable URL, where a mail client's outbox is something no gate can
observe. That ceiling was a property of the channel, not of manual sending.

R2 is untouched, both packets are byte-identical, and Mission 1.74's records are not
rewritten.
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

APPROVAL = DATA / "globalping-r1-dispatch-approval-v1.json"
R1_PACKET = DATA / "globalping-r1-enquiry-packet-v1.json"
R2_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v2.json"
RENDERER = SCRIPTS / "render_r1_dispatch_approval.py"
PAGE = DATA / "mission-1.74.1-r1-dispatch-approval-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def packet_digest(packet: dict) -> str:
    binding = {key: packet[key] for key in packet["hash_covers"]}
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class TestTheApprovalExists(unittest.TestCase):
    """1 to 5."""

    def test_the_record_exists_and_names_this_mission(self):
        self.assertTrue(APPROVAL.exists())
        self.assertEqual(load(APPROVAL)["mission"], "1.74.1")

    def test_the_page_and_the_renderer_exist(self):
        self.assertTrue(PAGE.exists())
        self.assertTrue(RENDERER.exists())

    def test_an_approval_is_actually_carried(self):
        approval = load(APPROVAL)["approval"]
        self.assertTrue(approval["approval_given"])
        self.assertTrue(approval["approved_by"].strip())


class TestItNamesThePacketAsStored(unittest.TestCase):
    """6 to 12. The approval names a document by its hash, recomputed not asserted."""

    def setUp(self):
        self.approval = load(APPROVAL)
        self.packet = load(R1_PACKET)

    def test_the_packet_still_answers_to_its_own_hash(self):
        self.assertEqual(packet_digest(self.packet), self.packet["content_sha256"])

    def test_the_approval_names_that_exact_hash(self):
        self.assertEqual(
            self.approval["approved_action"]["approved_content_sha256"],
            packet_digest(self.packet),
        )

    def test_the_hash_was_recomputed_rather_than_asserted(self):
        self.assertTrue(self.approval["approval"]["hash_recomputed_from_the_packet_as_stored"])

    def test_the_packet_file_hash_matches_the_bytes_on_disk(self):
        self.assertEqual(
            self.approval["approval"]["packet_file_sha256"],
            hashlib.sha256(R1_PACKET.read_bytes()).hexdigest(),
        )

    def test_the_approved_body_digest_matches_the_packet_body(self):
        self.assertEqual(
            self.approval["approval"]["approved_body_sha256"],
            hashlib.sha256(self.packet["body"].encode("utf-8")).hexdigest(),
        )

    def test_the_packet_was_not_edited(self):
        self.assertFalse(self.approval["approval"]["packet_edited_by_this_mission"])
        self.assertFalse(self.approval["approval"]["packet_content_sha256_changed"])


class TestTheApprovalStayedOutOfThePacket(unittest.TestCase):
    """13 to 17. Mission 1.66: marking a frozen document APPROVED changes it."""

    def setUp(self):
        self.packet = load(R1_PACKET)

    def test_the_packet_records_no_approval(self):
        self.assertFalse(self.packet["operator_approval_recorded"])

    def test_the_packet_records_no_send(self):
        self.assertFalse(self.packet["sent"])
        self.assertFalse(self.packet["execution_record_created"])

    def test_the_packets_own_send_status_is_unchanged(self):
        self.assertEqual(self.packet["send_status"], "NOT_AUTHORIZED")

    def test_the_approval_lives_in_its_own_document(self):
        approval = load(APPROVAL)["approval"]
        self.assertTrue(approval["approval_recorded_in_this_document_rather_than_in_the_packet"])
        self.assertTrue(approval["why"].strip())

    def test_that_field_means_this_document_records_none(self):
        # The packet saying NOT_AUTHORIZED is not a claim that no authorisation exists.
        self.assertIn("THIS DOCUMENT RECORDS NO", RENDERER.read_text(encoding="utf-8"))


class TestTheActionIsBound(unittest.TestCase):
    """18 to 27. The digest binds the ACTION, not the document."""

    def setUp(self):
        self.action = load(APPROVAL)["approved_action"]
        self.packet = load(R1_PACKET)

    def test_the_approval_answers_to_its_own_hash(self):
        binding = {key: self.action[key] for key in self.action["hash_covers"]}
        digest = hashlib.sha256(
            json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(digest, self.action["approval_sha256"])

    def test_it_excludes_its_own_digest_the_status_and_the_date(self):
        for excluded in ("approval_sha256", "execution", "recorded_at"):
            with self.subTest(field=excluded):
                self.assertNotIn(excluded, self.action["hash_covers"])
                self.assertIn(excluded, self.action["hash_excludes"])

    def test_every_field_of_the_action_is_pinned(self):
        for field in (
            "approves",
            "approved_content_sha256",
            "mechanism",
            "target_repository",
            "identity",
            "approved_title",
            "maximum_public_posts",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.action["hash_covers"])
        self.assertTrue(self.action["every_binding_field_is_pinned"])

    def test_the_mechanism_target_and_identity_are_the_approved_ones(self):
        self.assertEqual(self.action["mechanism"], "OPERATOR_MANUAL_GITHUB_ISSUE")
        self.assertEqual(self.action["target_repository"], "jsdelivr/globalping")
        self.assertEqual(self.action["identity"], "@Speekyx")

    def test_the_title_is_the_packets_subject(self):
        self.assertEqual(self.action["approved_title"], self.packet["subject"])

    def test_it_approves_the_enquiry_the_packet_carries(self):
        self.assertEqual(self.action["approves"], self.packet["question_id"])
        self.assertEqual(self.action["approves"], "GP-R1-Q1")

    def test_the_channel_matches_the_packet(self):
        self.assertTrue(self.action["channel_matches_the_packet"])
        self.assertEqual(self.packet["channel"], "PUBLIC_TECHNICAL_CHANNEL")

    def test_exactly_one_public_post_is_authorised(self):
        self.assertEqual(self.action["maximum_public_posts"], 1)

    def test_the_difference_from_mission_1_66_is_recorded(self):
        self.assertTrue(self.action["why_that_differs_from_mission_1_66"].strip())


class TestAnApprovalIsNotAnExecution(unittest.TestCase):
    """28 to 38. Nothing was posted, and nothing here could post it."""

    def setUp(self):
        self.execution = load(APPROVAL)["execution"]

    def test_the_status_is_pending_manual_operator_action(self):
        self.assertEqual(self.execution["status"], "PENDING_MANUAL_OPERATOR_ACTION")

    def test_no_public_post_was_made(self):
        self.assertEqual(self.execution["public_posts_made"], 0)
        self.assertIsNone(self.execution["issue_url"])

    def test_this_repository_created_no_issue(self):
        self.assertFalse(self.execution["issue_created_by_this_repository"])
        self.assertFalse(self.execution["gh_issue_create_invoked"])
        self.assertEqual(self.execution["github_api_calls_made_by_this_repository"], 0)

    def test_no_attestation_exists_yet(self):
        self.assertFalse(self.execution["operator_attestation_recorded"])
        self.assertIsNone(self.execution["attestation_level"])

    def test_both_attestation_levels_are_defined(self):
        self.assertEqual(
            self.execution["attestation_levels_defined"], ["OPERATOR_ATTESTED", "BYTE_VERIFIED"]
        )

    def test_byte_verification_is_possible_for_this_channel(self):
        self.assertTrue(self.execution["byte_verification_is_possible_for_this_channel"])
        self.assertTrue(self.execution["why_byte_verification_is_possible_here"].strip())

    def test_the_upgrade_path_and_the_only_route_to_sent_are_stated(self):
        self.assertTrue(self.execution["upgrade_path"].strip())
        self.assertTrue(self.execution["reachable_only_through"].strip())


class TestTheIntegrityRulesAreFrozen(unittest.TestCase):
    """39 to 45. Frozen before any post, which is the only time they mean anything."""

    def setUp(self):
        self.checks = load(APPROVAL)["integrity_checks_frozen_before_any_post"]

    def test_every_rule_holds(self):
        for flag, value in self.checks.items():
            if flag.startswith("$"):
                continue
            with self.subTest(rule=flag):
                self.assertTrue(value)

    def test_a_duplicate_is_reported_rather_than_tidied_away(self):
        self.assertTrue(
            self.checks["a_second_post_is_reported_as_a_duplicate_not_silently_accepted"]
        )

    def test_a_divergence_never_repairs_the_approval(self):
        self.assertTrue(self.checks["a_divergence_never_repairs_this_approval"])
        self.assertTrue(self.checks["a_divergence_is_recorded_beside_it"])


class TestOneApprovalCoversOneEnquiry(unittest.TestCase):
    """46 to 54. R2 was prepared alongside it and is not approved."""

    def setUp(self):
        self.scope = load(APPROVAL)["scope"]

    def test_exactly_one_enquiry_is_approved(self):
        self.assertEqual(self.scope["approved_enquiries"], ["GP-R1-Q1"])

    def test_r2_is_not_approved(self):
        self.assertFalse(self.scope["r2_approved"])
        self.assertFalse(self.scope["r2_packet_edited"])
        self.assertTrue(self.scope["why_r2_is_not_covered"].strip())

    def test_the_r2_packet_is_untouched_on_disk(self):
        r2 = load(R2_PACKET)
        self.assertEqual(r2["send_status"], "NOT_AUTHORIZED")
        self.assertFalse(r2["operator_approval_recorded"])
        self.assertFalse(r2["sent"])

    def test_r2_dispatch_needs_its_own_approval(self):
        self.assertTrue(
            load(APPROVAL)["recommended_next_action"]["r2_dispatch_requires_its_own_approval"]
        )

    def test_an_approval_to_ask_is_not_an_answer(self):
        self.assertEqual(self.scope["residuals_closed_by_this_mission"], 0)
        self.assertTrue(self.scope["an_approval_to_ask_is_not_an_answer"])
        self.assertEqual(self.scope["r1_verdict_unchanged"], "R1_PARTIAL_IMPLEMENTATION_ONLY")

    def test_the_qualification_was_not_recomputed(self):
        self.assertFalse(self.scope["qualification_recomputed"])
        qualification = load(QUALIFICATION)
        tally = qualification["tally"]
        self.assertEqual((tally["PASS"], tally["PARTIAL"], tally["FAIL"]), (10, 2, 0))
        self.assertEqual(qualification["verdict"], "COUNTERPART_UNRESOLVED")


class TestMission174WasNotRewritten(unittest.TestCase):
    """55 to 58. A later approval does not correct a mission that observed honestly."""

    def test_the_closure_still_reports_nothing_sent(self):
        closure = load(CLOSURE)
        self.assertEqual(closure["enquiries"]["enquiries_sent"], 0)
        self.assertFalse(closure["enquiries"]["operator_approval_recorded"])

    def test_the_closure_still_reports_two_residuals(self):
        self.assertEqual(load(CLOSURE)["residuals_remaining"], 2)

    def test_the_record_says_1_74_was_not_edited(self):
        self.assertFalse(load(APPROVAL)["parallel_state_untouched"]["mission_1_74_records_edited"])

    def test_that_field_is_not_a_contradiction(self):
        # 1.74 recorded that IT authorised no dispatch. That stays true: the approval
        # arrived afterwards and lives in its own document.
        closure = load(CLOSURE)
        self.assertFalse(closure["enquiries"]["dispatch_authorised_by_this_mission"])
        self.assertTrue(load(APPROVAL)["approval"]["approval_given"])


class TestNothingMoved(unittest.TestCase):
    """59 to 63."""

    def setUp(self):
        self.approval = load(APPROVAL)

    def test_every_hard_zero_counter_is_zero(self):
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
            "mission_1_74_records_edited",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(parallel[flag])

    def test_the_next_action_belongs_to_the_operator(self):
        action = self.approval["recommended_next_action"]
        self.assertEqual(action["performed_by"], "OPERATOR")
        self.assertTrue(action["this_repository_may_not_perform_it"])
        self.assertTrue(action["mission_1_75_not_started"])

    def test_no_predicate_was_frozen_and_no_target_value_retrieved(self):
        self.assertFalse(self.approval["exact_predicate_frozen"])
        self.assertEqual(self.approval["target_values_retrieved"], 0)


class TestTheRenderer(unittest.TestCase):
    """64 to 70. Deterministic, offline, and it does not reach GitHub."""

    def setUp(self):
        self.source = RENDERER.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_it_imports_nothing_that_reaches_a_network(self):
        forbidden = {
            "requests",
            "httpx",
            "urllib",
            "urllib3",
            "socket",
            "http",
            "aiohttp",
            "psycopg",
            "sqlalchemy",
            "github",
        }
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name.split(".")[0], forbidden)
            elif isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn(node.module.split(".")[0], forbidden)

    def test_it_cannot_create_an_issue(self):
        # Structural rather than a text scan: the phrase "gh issue create" appears in this
        # module's own documentation and in the rendered table, which is exactly the shape
        # (testing-strategy.md §23) where a substring check fails on the prose doing the
        # work. What matters is that nothing here can spawn a process or open a socket.
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for banned in ("subprocess", "os", "shutil", "socket", "requests", "httpx"):
            with self.subTest(module=banned):
                self.assertNotIn(banned, imported)

    def test_it_makes_no_process_spawning_call(self):
        spawners = {
            "system",
            "popen",
            "spawn",
            "spawnl",
            "spawnv",
            "execv",
            "run",
            "check_call",
            "check_output",
            "call",
            "Popen",
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

    def test_the_page_is_marked_generated_and_reports_the_pending_status(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("PENDING_MANUAL_OPERATOR_ACTION", text)
        self.assertIn("jsdelivr/globalping", text)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the record does not carry', self.source)


class TestGovernanceRecordsThis(unittest.TestCase):
    """71 to 74."""

    def test_the_manifest_lists_the_record_and_the_renderer(self):
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertIn(APPROVAL.name, text)
        self.assertIn(RENDERER.name, text)

    def test_ci_runs_the_new_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_report_exists(self):
        report = REPO_ROOT / "docs" / "architecture" / "mission-1.74.1-report.md"
        self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()
