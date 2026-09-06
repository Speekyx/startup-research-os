"""Mission 1.76.1. A reply arrived on R2, and R2 did not close.

Two independent reasons, and either alone would have been enough.

NOBODY KNOWS WHO SAID IT. R1's reply was a public GitHub comment whose author GitHub
itself places inside the owning organisation. A private email has no public surface: its
sender lives only in a mailbox. This mission attempted that read under an explicit
operator authorisation and the connector refused it, so the From address, the display name
and the Date are null -- and a header field with no retrieval behind it would be invented
provenance, which is the one thing a fabricated record supplies most convincingly.

IT ANSWERS THE HALF THAT WAS ALREADY CLOSED. The enquiry asked four things; the reply
answers commercial use, which Mission 1.74 closed on the provider's own FAQ. The
discriminator frozen before the send required an answer STATING that the Terms do or do
not cover third-party publicly reachable targets, and the reply contains no such
statement. A prohibition on proxying arguably presupposes one -- and Mission 1.74 graded
exactly that shape non-closing, because a presupposition is not a statement.

The second reason is the sharper one: an authorised mailbox read would fix the first and
leave the second exactly where it is.
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

FROZEN = DATA / "globalping-r2-provider-reply-v1.json"
REVIEW = DATA / "globalping-r2-reply-review-v1.json"
PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v2.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"
V2_DISPATCH = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
RENDERER = SCRIPTS / "render_r2_provider_reply.py"
PAGE = DATA / "globalping-r2-reply-evidence-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_r2_provider_reply", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheReplyIsFrozenWithoutBeingPromoted(unittest.TestCase):
    def setUp(self):
        self.frozen = load(FROZEN)

    def test_it_declares_itself_a_source_and_carries_no_verdict(self):
        self.assertEqual(self.frozen["record_kind"], "FROZEN_PROVIDER_REPLY_SOURCE")
        self.assertFalse(self.frozen["contains_interpretation"])
        for forbidden in ("verdict", "evidence_level"):
            with self.subTest(field=forbidden):
                self.assertNotIn(forbidden, self.frozen)

    def test_the_body_answers_to_its_own_hash(self):
        reply = self.frozen["reply"]
        self.assertEqual(
            reply["body_sha256"], hashlib.sha256(reply["body"].encode("utf-8")).hexdigest()
        )

    def test_the_body_is_marked_supplied_rather_than_retrieved(self):
        reply = self.frozen["reply"]
        self.assertEqual(reply["body_source"], "OPERATOR_SUPPLIED_TEXT")
        self.assertFalse(reply["body_retrieved_from_the_mailbox"])
        self.assertTrue(reply["why_the_body_is_still_frozen"].strip())

    def test_every_header_field_is_null(self):
        missing = self.frozen["message_fields_not_established"]
        for field in gate().HEADER_FIELDS:
            with self.subTest(field=field):
                self.assertIsNone(missing[field])
        self.assertFalse(missing["operator_supplied_any_of_them"])

    def test_the_mailbox_read_is_recorded_as_attempted_and_refused(self):
        provenance = self.frozen["provenance"]
        self.assertTrue(provenance["mailbox_read_attempted"])
        self.assertFalse(provenance["mailbox_read"])
        self.assertTrue(provenance["mailbox_access_authorised_by_the_operator"])
        self.assertEqual(provenance["results_returned"], 0)
        self.assertFalse(provenance["unrelated_mailbox_content_accessed"])

    def test_the_connector_execution_is_counted_rather_than_rounded_away(self):
        accounting = self.frozen["mission_accounting"]
        self.assertEqual(accounting["MAILBOX_READS"], 0)
        self.assertEqual(accounting["MAILBOX_MESSAGES_RETRIEVED"], 0)
        self.assertGreaterEqual(accounting["MAIL_CONNECTOR_EXECUTIONS"], 1)
        self.assertTrue(self.frozen["mail_connector_execution_note"].strip())

    def test_the_quoted_question_is_the_frozen_first_paragraph_and_not_the_whole_body(self):
        link = self.frozen["relationship_to_gp_r2_q1_v2"]
        packet = load(PACKET)
        self.assertTrue(link["subject_matches_the_frozen_subject"])
        self.assertTrue(link["quoted_question_is_the_frozen_first_paragraph"])
        self.assertFalse(link["quoted_question_is_the_whole_frozen_body"])
        self.assertEqual(link["packet_content_sha256"], packet["content_sha256"])

    def test_attribution_is_not_established(self):
        attribution = self.frozen["attribution"]
        self.assertEqual(attribution["attributable_to_globalping_or_jsdelivr"], "NOT_ESTABLISHED")
        self.assertEqual(attribution["first_party"], "NOT_ESTABLISHED")
        self.assertFalse(attribution["sufficient_for_provider_authority"])
        self.assertIn("bounce", attribution["why_consistency_is_not_attribution"])


class TestTheReviewReadsItHonestly(unittest.TestCase):
    def setUp(self):
        self.review = load(REVIEW)
        self.frozen = load(FROZEN)

    def test_the_reply_text_appears_in_the_source_and_not_in_the_interpretation(self):
        self.assertNotIn(self.frozen["reply"]["body"], REVIEW.read_text(encoding="utf-8"))
        self.assertFalse(self.review["source"]["reply_restated_in_this_record"])

    def test_provider_authority_is_not_established(self):
        attribution = self.review["question_1_attribution"]
        self.assertEqual(attribution["answer"], "NO")
        self.assertFalse(attribution["provider_authority_established"])
        self.assertEqual(attribution["level_reached"], "OPERATOR_SUPPLIED")
        self.assertEqual(
            attribution["level_required_to_close_a_rights_residual"], "RAW_MAILBOX_READ"
        )

    def test_two_of_the_four_clauses_are_addressed(self):
        responsiveness = self.review["question_2_responsiveness"]
        clauses = responsiveness["clauses_asked"]
        self.assertEqual(clauses["publicly_reachable_third_party_websites"], "NOT_ADDRESSED")
        self.assertEqual(clauses["bounded_HEAD_measurements"], "NOT_ADDRESSED")
        self.assertEqual(responsiveness["how_many_of_four_addressed"], 2)

    def test_the_counter_argument_is_stated_before_it_is_answered(self):
        responsiveness = self.review["question_2_responsiveness"]
        self.assertIn(
            "proxy", responsiveness["the_strongest_argument_that_it_answers_more"].lower()
        )
        self.assertIn("presupposition", responsiveness["why_that_argument_does_not_carry"])

    def test_the_frozen_discriminator_is_quoted_from_the_packet(self):
        permission = self.review["question_3_does_it_establish_permission"]
        self.assertEqual(
            permission["discriminator_frozen_before_the_send"],
            load(PACKET)["expected_answer_discriminator"],
        )
        self.assertFalse(permission["does_the_reply_contain_such_a_statement"])

    def test_it_answers_the_half_that_was_already_closed(self):
        permission = self.review["question_3_does_it_establish_permission"]
        self.assertEqual(permission["which_half_it_answers"], "R2-A, commercial use")
        self.assertEqual(permission["r2_a_status_before_this_reply"], "PERMITTED_WITHIN_TERMS")
        self.assertEqual(permission["what_it_adds_to_r2_b"], "nothing stated")

    def test_nothing_was_broadened(self):
        permission = self.review["question_3_does_it_establish_permission"]
        self.assertFalse(permission["broadened_into_permission_for_arbitrary_traffic"])
        self.assertFalse(permission["commercial_use_read_as_unlimited_use"])

    def test_all_three_limitations_are_recorded_and_none_removed(self):
        limits = self.review["question_4_limitations_stated_by_the_provider"]
        for limitation in gate().STATED_LIMITATIONS:
            with self.subTest(limitation=limitation):
                self.assertEqual(limits[limitation], "CLAIMED")
        self.assertEqual(limits["limitations_removed_by_this_review"], 0)
        self.assertTrue(limits["abuse_is_not_defined_by_the_reply"])

    def test_two_independent_reasons_keep_it_open(self):
        closes = self.review["question_5_does_it_close_the_residual"]
        self.assertEqual(closes["answer"], "NO")
        self.assertGreaterEqual(len(closes["two_independent_reasons"]), 2)
        self.assertTrue(closes["either_alone_would_be_enough"])

    def test_the_sharper_reason_is_named_as_such(self):
        permission = self.review["question_3_does_it_establish_permission"]
        self.assertIn("could not", permission["why_this_is_the_sharper_finding"])

    def test_the_follow_up_isolates_the_open_half_and_needs_its_own_approval(self):
        follow_up = self.review["what_would_close_r2_b"]
        self.assertTrue(follow_up["requires_a_new_operator_approval"])
        self.assertIn("compound", follow_up["why_the_last_enquiry_did_not_get_it"])


class TestNothingMoved(unittest.TestCase):
    def test_r2_b_and_the_closure_are_untouched(self):
        self.assertEqual(load(THIRD_PARTY)["verdict"], "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED")
        closure = load(CLOSURE)
        self.assertEqual(closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"], "UNRESOLVED")
        self.assertFalse(closure["residuals"][1]["closed"])

    def test_the_qualification_is_untouched(self):
        qualification = load(QUALIFICATION)
        gates = {g["dimension"]: g["status"] for g in qualification["gates"]}
        self.assertEqual(gates["C9_RIGHTS_FEASIBILITY"], "PARTIAL")
        self.assertEqual(
            qualification["tally"], {"PASS": 11, "PARTIAL": 1, "FAIL": 0, "UNKNOWN": 0}
        )
        self.assertEqual(qualification["verdict"], "COUNTERPART_UNRESOLVED")

    def test_the_dispatch_record_does_not_claim_a_provider_reply(self):
        execution = load(V2_DISPATCH)["execution"]
        self.assertEqual(execution["status"], "SENT")
        self.assertFalse(execution["provider_replied"])
        self.assertFalse(execution["provider_contacted"])

    def test_r1_was_not_examined(self):
        bounded = load(REVIEW)["bounded_to_r2"]
        self.assertFalse(bounded["r1_examined"])
        self.assertEqual(bounded["r1_verdict_unchanged"], "R1_PASS_PROVIDER_DECLARED_NO_REDIRECT")
        self.assertEqual(bounded["canonical_research_mutations"], 0)


class TestTheGateRefusesTheClosureItWasOfferedd(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.frozen = load(FROZEN)
        self.review = load(REVIEW)
        self.packet = load(PACKET)

    def refused_frozen(self, frozen):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_reply_is_frozen_as_supplied(frozen, self.packet)

    def refused_review(self, review):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_review_reads_it_honestly(review, self.frozen, self.packet)

    def test_the_records_as_committed_pass(self):
        self.gate._check_the_reply_is_frozen_as_supplied(self.frozen, self.packet)
        self.gate._check_the_review_reads_it_honestly(self.review, self.frozen, self.packet)
        self.gate._check_nothing_moved(self.review)
        self.gate._check_accounting(self.frozen)

    def test_a_sender_recorded_with_no_read_is_refused(self):
        frozen = copy.deepcopy(self.frozen)
        frozen["message_fields_not_established"]["sender_email_address"] = "d@globalping.io"
        self.refused_frozen(frozen)

    def test_a_timestamp_recorded_with_no_read_is_refused(self):
        frozen = copy.deepcopy(self.frozen)
        frozen["message_fields_not_established"]["sent_at"] = "2026-09-06T20:00:00Z"
        self.refused_frozen(frozen)

    def test_claiming_provider_authority_is_refused(self):
        frozen = copy.deepcopy(self.frozen)
        frozen["attribution"]["sufficient_for_provider_authority"] = True
        self.refused_frozen(frozen)

    def test_claiming_first_party_attribution_is_refused(self):
        frozen = copy.deepcopy(self.frozen)
        frozen["attribution"]["first_party"] = "ESTABLISHED"
        self.refused_frozen(frozen)

    def test_claiming_a_retrieval_is_refused(self):
        frozen = copy.deepcopy(self.frozen)
        frozen["provenance"]["retrieval_method"] = "RAW_MAILBOX_READ"
        self.refused_frozen(frozen)

    def test_promoting_the_level_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_1_attribution"]["level_reached"] = "RAW_MAILBOX_READ"
        self.refused_review(review)

    def test_lowering_the_bar_to_the_level_reached_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_1_attribution"]["level_required_to_close_a_rights_residual"] = (
            "OPERATOR_SUPPLIED"
        )
        self.refused_review(review)

    def test_recording_the_third_party_clause_as_answered_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_2_responsiveness"]["clauses_asked"][
            "publicly_reachable_third_party_websites"
        ] = "ADDRESSED"
        self.refused_review(review)

    def test_claiming_the_reply_states_target_coverage_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_3_does_it_establish_permission"][
            "does_the_reply_contain_such_a_statement"
        ] = True
        self.refused_review(review)

    def test_reading_commercial_use_as_unlimited_use_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_3_does_it_establish_permission"][
            "commercial_use_read_as_unlimited_use"
        ] = True
        self.refused_review(review)

    def test_dropping_a_stated_limitation_is_refused(self):
        for limitation in self.gate.STATED_LIMITATIONS:
            with self.subTest(limitation=limitation):
                review = copy.deepcopy(self.review)
                review["question_4_limitations_stated_by_the_provider"][limitation] = "ESTABLISHED"
                self.refused_review(review)

    def test_removing_a_limitation_outright_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_4_limitations_stated_by_the_provider"][
            "limitations_removed_by_this_review"
        ] = 1
        self.refused_review(review)

    def test_closing_r2_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_5_does_it_close_the_residual"]["answer"] = "YES"
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_nothing_moved(review)

    def test_making_the_two_reasons_jointly_necessary_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_5_does_it_close_the_residual"]["either_alone_would_be_enough"] = False
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_nothing_moved(review)

    def test_recomputing_the_qualification_is_refused(self):
        review = copy.deepcopy(self.review)
        review["question_6_qualification"]["qualification_recomputed"] = True
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_nothing_moved(review)

    def test_a_follow_up_needing_no_approval_is_refused(self):
        review = copy.deepcopy(self.review)
        review["what_would_close_r2_b"]["requires_a_new_operator_approval"] = False
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_nothing_moved(review)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the records do not carry', RENDERER.read_text("utf-8"))


class TestTheRendererAndGovernance(unittest.TestCase):
    def test_the_renderer_reads_no_mailbox_and_no_network(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in ("requests", "httpx", "smtplib", "imaplib", "urllib", "subprocess"):
            with self.subTest(module=banned):
                self.assertNotIn(f"import {banned}", source)

    def test_the_page_names_both_reasons(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("nobody knows who said it", text.lower())
        self.assertIn("already closed", text.lower())
        self.assertIn("OPERATOR_SUPPLIED", text)

    def test_ci_runs_the_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_manifest_lists_the_records(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (FROZEN, REVIEW, RENDERER):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "reports" / "mission-1.76.1-report.md").exists())


if __name__ == "__main__":
    unittest.main()
