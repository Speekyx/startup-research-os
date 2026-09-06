"""Mission 1.74.4. The designated address bounced, and a replacement is prepared.

The operator attested that the approved GP-R2-Q1 email was attempted exactly once and
rejected. Two things follow that are easy to get wrong in opposite directions.

A bounced attempt is NOT a contact: nobody received it, so `provider_contacted` stays
false and no attestation level applies, because the levels grade evidence that a message
WAS delivered. And the one-send approval is EXHAUSTED by the attempt, so neither a retry
to the same address nor a send to a new one is covered by it.

Then the replacement address. `d@globalping.io` was supplied by the operator, and a
supplied address is a claim about the world like any other -- Mission 1.65 judged a
recipient on provenance rather than on spelling, and refused to infer one from
convention. So it is established here because it is read off the provider's own
committed website source as a live mailto link, and corroborated by the rendered page
rather than resting on it (Mission 1.63).

And it is recorded as GENERAL CONTACT, not as the designated channel. Three provider
documents designate legal@globalping.io for Terms, privacy and data-protection
questions. Calling the footer address designated would assert a standing no provider
document gives it -- which is the same over-read this arc refused for a schema, for
product design and for a FAQ answer.

The subject and body are preserved exactly; only the recipient and the channel label
changed, so the digest differs and the exhausted approval cannot name this packet.
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

REVIEW = DATA / "globalping-r2-replacement-recipient-review-v1.json"
V2_PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
V1_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
R2_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
RENDERER = SCRIPTS / "render_r2_replacement_packet.py"
APPROVAL_RENDERER = SCRIPTS / "render_r2_dispatch_approval.py"
PAGE = DATA / "mission-1.74.4-r2-replacement-packet-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

DESIGNATED = "legal@globalping.io"
REPLACEMENT = "d@globalping.io"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(packet: dict) -> str:
    binding = {key: packet[key] for key in packet["hash_covers"]}
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class TestTheFailedDispatch(unittest.TestCase):
    """1 to 12. A bounce is not a send and is not a contact."""

    def setUp(self):
        self.execution = load(R2_APPROVAL)["execution"]

    def test_the_status_is_the_failure_status(self):
        self.assertEqual(self.execution["status"], "DISPATCH_ATTEMPTED_DELIVERY_FAILED")

    def test_one_attempt_and_no_delivery(self):
        self.assertEqual(self.execution["send_attempts"], 1)
        self.assertEqual(self.execution["sends_made"], 0)
        self.assertEqual(self.execution["deliveries_confirmed"], 0)

    def test_the_provider_was_not_contacted(self):
        self.assertFalse(self.execution["provider_contacted"])
        self.assertTrue(self.execution["why_provider_contacted_is_false"].strip())

    def test_no_attestation_level_applies_to_a_message_that_did_not_arrive(self):
        self.assertIsNone(self.execution["attestation_level"])
        self.assertTrue(self.execution["why_no_attestation_level"].strip())

    def test_the_attestation_is_of_a_failure_rather_than_of_a_send(self):
        self.assertTrue(self.execution["operator_attestation_recorded"])
        self.assertTrue(self.execution["attestation_is_of_a_failure_not_of_a_send"])
        self.assertTrue(self.execution["attestation_statement"].strip())

    def test_the_bounce_report_was_not_imported(self):
        self.assertFalse(self.execution["bounce_artifact_imported"])
        self.assertTrue(self.execution["why_the_bounce_was_not_imported"].strip())
        self.assertFalse(self.execution["mailbox_searched"])

    def test_the_one_send_approval_is_exhausted(self):
        self.assertTrue(self.execution["approval_exhausted"])
        self.assertFalse(self.execution["retry_to_the_same_recipient_authorised"])
        self.assertTrue(self.execution["replacement_requires_a_new_operator_approval"])
        self.assertTrue(self.execution["why_the_approval_is_exhausted"].strip())

    def test_this_repository_sent_nothing(self):
        self.assertEqual(self.execution["emails_sent_by_this_repository"], 0)
        self.assertFalse(self.execution["mail_connector_used"])

    def test_the_approval_digest_did_not_move(self):
        action = load(R2_APPROVAL)["approved_action"]
        binding = {key: action[key] for key in action["hash_covers"]}
        recomputed = hashlib.sha256(
            json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(recomputed, action["approval_sha256"])


class TestASuppliedAddressIsAClaim(unittest.TestCase):
    """13 to 22. Established on provenance, or not at all."""

    def setUp(self):
        self.review = load(REVIEW)

    def test_it_was_supplied_and_not_accepted_for_that_reason(self):
        self.assertTrue(self.review["supplied_by_the_operator"])
        self.assertFalse(self.review["accepted_because_supplied"])
        self.assertTrue(self.review["why"].strip())

    def test_it_is_established_on_the_committed_source(self):
        establishment = self.review["establishment"]
        self.assertTrue(establishment["address_is_established_first_party"])
        self.assertTrue(establishment["read_from_committed_source_rather_than_a_rendered_shell"])
        self.assertFalse(establishment["inferred_from_convention"])

    def test_the_rendered_page_only_corroborates(self):
        rendered = [
            s for s in self.review["surfaces_reviewed"] if s.get("role") == "CORROBORATION_ONLY"
        ]
        self.assertTrue(rendered)
        for surface in rendered:
            with self.subTest(surface=surface["surface"]):
                self.assertTrue(surface["why_corroboration_only"].strip())

    def test_a_single_letter_local_part_is_not_disqualifying(self):
        # Mission 1.65: a string rule refuses a correct address and admits a guessed one.
        establishment = self.review["establishment"]
        self.assertFalse(establishment["single_letter_local_part_treated_as_disqualifying"])
        self.assertTrue(establishment["why_not"].strip())

    def test_more_than_one_surface_was_reviewed(self):
        self.assertGreaterEqual(len(self.review["surfaces_reviewed"]), 4)
        self.assertEqual(
            len(self.review["surfaces_reviewed"]), self.review["surfaces_reviewed_count"]
        )

    def test_three_provider_documents_designate_the_original_address(self):
        designating = [
            s for s in self.review["surfaces_reviewed"] if DESIGNATED in s["addresses_found"]
        ]
        self.assertGreaterEqual(len(designating), 3)
        for surface in designating:
            with self.subTest(surface=surface["surface"]):
                self.assertFalse(surface["d_address_present"])


class TestAGeneralContactIsNotADesignation(unittest.TestCase):
    """23 to 30. The over-read this arc has refused four times."""

    def setUp(self):
        self.relevance = load(REVIEW)["relevance"]

    def test_it_is_not_the_terms_designated_channel(self):
        self.assertFalse(self.relevance["is_it_the_terms_designated_channel"])

    def test_the_designated_channel_did_not_move(self):
        self.assertEqual(self.relevance["the_terms_designated_channel_remains"], DESIGNATED)

    def test_the_classification_says_both_halves(self):
        self.assertEqual(
            self.relevance["classification"],
            "ESTABLISHED_FIRST_PARTY_GENERAL_CONTACT_NOT_THE_TERMS_DESIGNATED_CHANNEL",
        )

    def test_the_basis_is_recorded_as_weaker(self):
        self.assertTrue(self.relevance["weaker_than_the_original_basis"])
        self.assertTrue(self.relevance["why_it_is_still_the_relevant_remaining_route"].strip())

    def test_one_rejection_is_not_a_permanent_fact_about_an_address(self):
        review = load(REVIEW)
        self.assertEqual(
            review["legal_at_globalping_io_status"],
            "OPERATOR_ATTESTED_DELIVERY_REJECTED_ONCE",
        )
        self.assertEqual(review["not_recorded_as"], "PERMANENTLY_NONEXISTENT")

    def test_the_limits_and_the_tension_are_both_recorded(self):
        review = load(REVIEW)
        self.assertGreaterEqual(len(review["what_this_does_not_establish"]), 3)
        self.assertTrue(review["the_tension_recorded_rather_than_smoothed"].strip())


class TestTheReplacementPacket(unittest.TestCase):
    """31 to 42."""

    def setUp(self):
        self.v2 = load(V2_PACKET)
        self.v1 = load(V1_PACKET)

    def test_it_answers_to_its_own_recomputed_hash(self):
        self.assertEqual(digest(self.v2), self.v2["content_sha256"])

    def test_the_hash_differs_from_v1_because_the_recipient_changed(self):
        self.assertNotEqual(self.v2["content_sha256"], self.v1["content_sha256"])
        self.assertNotEqual(self.v2["recipient"], self.v1["recipient"])

    def test_the_subject_and_body_are_preserved_exactly(self):
        self.assertEqual(self.v2["subject"], self.v1["subject"])
        self.assertEqual(self.v2["body"], self.v1["body"])
        self.assertTrue(self.v2["subject_and_body_preserved_exactly"])

    def test_no_explanatory_sentence_was_added_and_the_record_says_why(self):
        self.assertTrue(self.v2["changing_them_was_not_strictly_required"])
        self.assertTrue(self.v2["why_no_explanatory_sentence_was_added"].strip())

    def test_the_recipient_is_the_reviewed_address(self):
        self.assertEqual(self.v2["recipient"], REPLACEMENT)
        self.assertEqual(self.v2["recipient"], load(REVIEW)["candidate_address"])
        self.assertFalse(self.v2["recipient_guessed"])
        self.assertTrue(self.v2["recipient_supplied_by_operator_and_independently_established"])

    def test_the_channel_label_changed_and_says_why(self):
        self.assertNotEqual(self.v2["channel"], self.v1["channel"])
        self.assertEqual(self.v2["channel"], "PROVIDER_PUBLISHED_GENERAL_CONTACT_CHANNEL")
        self.assertTrue(self.v2["why_the_channel_label_changed"].strip())

    def test_the_recipient_and_channel_are_bound_by_the_hash(self):
        for field in ("recipient", "channel", "subject", "body"):
            with self.subTest(field=field):
                self.assertIn(field, self.v2["hash_covers"])

    def test_it_is_unsent_and_unapproved(self):
        self.assertEqual(self.v2["send_status"], "NOT_AUTHORIZED")
        self.assertFalse(self.v2["operator_approval_recorded"])
        self.assertFalse(self.v2["sent"])
        self.assertFalse(self.v2["execution_record_created"])

    def test_v1_is_superseded_and_not_edited(self):
        self.assertEqual(self.v2["supersedes"], V1_PACKET.name)
        self.assertEqual(digest(self.v1), self.v1["content_sha256"])
        self.assertEqual(self.v1["recipient"], DESIGNATED)
        self.assertEqual(self.v1["send_status"], "NOT_AUTHORIZED")
        self.assertTrue(self.v2["supersedes_note"].strip())


class TestTheExhaustedApprovalCannotReach(unittest.TestCase):
    """43 to 47. The hash is what defeats the shared question id."""

    def test_the_two_packets_share_a_question_id(self):
        self.assertEqual(load(V2_PACKET)["question_id"], load(V1_PACKET)["question_id"])

    def test_and_the_approval_still_cannot_name_the_replacement(self):
        approval = load(R2_APPROVAL)["approved_action"]
        self.assertNotEqual(approval["approved_content_sha256"], load(V2_PACKET)["content_sha256"])
        self.assertEqual(approval["approved_content_sha256"], load(V1_PACKET)["content_sha256"])

    def test_the_approval_names_the_old_recipient(self):
        self.assertEqual(load(R2_APPROVAL)["approved_action"]["recipient"], DESIGNATED)

    def test_the_packet_records_that_no_approval_covers_it(self):
        v2 = load(V2_PACKET)
        self.assertTrue(v2["prior_approval_does_not_cover_this_packet"])
        self.assertTrue(v2["why"].strip())


class TestTheRenderer(unittest.TestCase):
    """48 to 53."""

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

    def test_the_page_reports_both_addresses_and_the_unsent_status(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn(REPLACEMENT, text)
        self.assertIn(DESIGNATED, text)
        self.assertIn("NOT_AUTHORIZED", text)


class TestGovernanceRecordsThis(unittest.TestCase):
    """54 to 57."""

    def test_the_manifest_lists_the_new_records_and_the_renderer(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for name in (REVIEW.name, V2_PACKET.name, RENDERER.name):
            with self.subTest(name=name):
                self.assertIn(name, text)

    def test_ci_runs_both_r2_gates(self):
        text = CI.read_text(encoding="utf-8")
        self.assertIn(RENDERER.name, text)
        self.assertIn(APPROVAL_RENDERER.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "architecture" / "mission-1.74.4-report.md").exists())


if __name__ == "__main__":
    unittest.main()
