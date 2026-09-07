"""Mission 1.76.5. Twenty-two characters closed R2-B, and that is not a reason to check less.

Four things this file defends.

THE EVIDENCE AND THE CONCLUSION LIVE IN SEPARATE DOCUMENTS. The frozen reply carries no
verdict and no evidence level; the review cites it by hash. A single document holding both
can adjust the first to suit the second with nothing in it showing the adjustment.

THE DISCRIMINATOR IS READ LIVE. It was frozen in Mission 1.76.2 and sent in 1.76.4, and the
review's quoted branch text must equal the packet's, so a discriminator softened after the
answer arrived fails here rather than passing quietly.

THE PERMISSION IS EXACTLY AS WIDE AS THE QUESTION. The answer is anaphoric, so its scope
lives in the question and is the thing most easily lost.

A CLOSED RESIDUAL AUTHORISES NOTHING TO RUN. Twelve of twelve dimensions pass and no
construct, corpus, measurement, independence group or score exists.
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

REPLY = DATA / "globalping-r2b-provider-reply-v1.json"
REVIEW = DATA / "globalping-r2b-reply-review-v1.json"
PACKET = DATA / "globalping-r2b-enquiry-packet-v1.json"
APPROVAL = DATA / "globalping-r2b-dispatch-approval-v1.json"
SCOPE_V1 = DATA / "globalping-third-party-target-scope-review-v1.json"
SCOPE_V2 = DATA / "globalping-third-party-target-scope-review-v2.json"
CLOSURE_V2 = DATA / "globalping-residual-closure-v2.json"
CLOSURE_V3 = DATA / "globalping-residual-closure-v3.json"
QUAL_V3 = DATA / "globalping-counterpart-qualification-v3.json"
QUAL_V4 = DATA / "globalping-counterpart-qualification-v4.json"
R1_REVIEW = DATA / "globalping-r1-reply-review-v1.json"
RENDERER = SCRIPTS / "render_r2b_reply_review.py"
PAGE = DATA / "globalping-r2b-reply-review-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_r2b_reply_review", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selection_authorises_nothing(case, path):
    """Re-pointed by Mission 1.76.6. These files asserted the selection artifact did not
    exist, which was true until Mission 1.76.6 selected Q1. What each defends is that its own
    mission selected nothing, and that whatever selection exists authorises no run."""
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    case.assertEqual(record["state"], "CLASS_SELECTED")
    case.assertFalse(record["states_kept_apart"]["CONSTRUCT_SELECTED"])
    case.assertFalse(record["states_kept_apart"]["RUN_AUTHORIZED"])
    case.assertFalse(record["corpus_frozen"])
    case.assertEqual(record["measurements_executed"], 0)


class TestTheReplyIsFrozenAndSaysNothingAboutItself(unittest.TestCase):
    def setUp(self):
        self.reply = load(REPLY)

    def test_it_answers_to_its_own_hash(self):
        body = self.reply["reply"]
        self.assertEqual(
            hashlib.sha256(body["body"].encode("utf-8")).hexdigest(), body["body_sha256"]
        )
        self.assertEqual(body["body"], "Yes it's not a problem")
        self.assertEqual(body["body_length_characters"], 22)

    def test_the_apostrophe_is_recorded_because_a_curly_one_would_hash_differently(self):
        self.assertEqual(self.reply["reply"]["apostrophe_codepoint"], "U+0027")
        self.assertTrue(self.reply["reply"]["body_is_pure_ascii"])

    def test_it_carries_no_verdict_and_no_evidence_level(self):
        for banned in ("verdict", "evidence_level", "closes_r2_b", "gates"):
            with self.subTest(field=banned):
                self.assertNotIn(banned, self.reply)

    def test_the_operator_quotation_was_compared_rather_than_adopted(self):
        body = self.reply["reply"]
        self.assertEqual(body["body_as_stated_by_the_operator"], body["body"])
        self.assertTrue(body["operator_statement_matches_the_extracted_bytes"])
        self.assertIn("1.65", body["why_that_comparison_was_made"])

    def test_no_transport_header_was_invented(self):
        headers = self.reply["headers_as_displayed"]
        self.assertIsNone(headers["message_id"])
        for absent in (
            "message_id_available",
            "received_chain_available",
            "dkim_or_spf_result_available",
        ):
            with self.subTest(field=absent):
                self.assertFalse(headers[absent])

    def test_no_offset_was_invented_for_a_displayed_time(self):
        headers = self.reply["headers_as_displayed"]
        self.assertTrue(headers["displayed_time_carries_no_offset"])
        self.assertNotIn("+", headers["displayed_reply_time_normalised"])
        self.assertNotIn("Z", headers["displayed_reply_time_normalised"])

    def test_the_export_is_fingerprinted_and_not_committed(self):
        provenance = self.reply["provenance"]
        self.assertEqual(len(provenance["artifact_sha256"]), 64)
        self.assertFalse(provenance["artifact_committed_to_this_repository"])
        self.assertFalse(provenance["gmail_permalink_recorded"])
        self.assertFalse(provenance["summarising_model_in_the_extraction_path"])

    def test_the_export_pdf_is_not_in_the_repository(self):
        self.assertEqual(list(REPO_ROOT.glob("**/Gmail*.pdf")), [])


class TestTheCorroborationsAndTheDiscrepancy(unittest.TestCase):
    def setUp(self):
        self.reply = load(REPLY)

    def test_the_sent_body_matches_the_frozen_packet_up_to_wrapping(self):
        match = self.reply["corroborations"]["the_sent_follow_up_matches_the_frozen_packet_body"]
        self.assertEqual(match["match"], "WHITESPACE_NORMALISED_IDENTICAL")
        self.assertFalse(match["byte_identical"])
        self.assertIn("1.74.3", match["why_not_byte_identical"])

    def test_the_earlier_reply_is_corroborated_by_a_later_document(self):
        match = self.reply["corroborations"]["the_earlier_reply_matches_what_mission_1_76_1_froze"]
        frozen = load(DATA / "globalping-r2-provider-reply-v1.json")
        self.assertEqual(match["frozen_body_sha256"], frozen["reply"]["body_sha256"])
        self.assertEqual(match["match"], "WHITESPACE_NORMALISED_IDENTICAL")

    def test_the_send_time_discrepancy_is_recorded_and_not_resolved(self):
        discrepancy = self.reply["discrepancy_recorded_rather_than_resolved"]
        self.assertFalse(discrepancy["resolved"])
        self.assertEqual(discrepancy["attested_by_the_operator"], "2026-09-07T19:19:30+04:00")
        self.assertEqual(discrepancy["displayed_by_the_export"], "2026-09-07 19:26")
        self.assertFalse(discrepancy["does_it_bear_on_r2_b"])

    def test_both_send_times_survive_in_the_execution(self):
        execution = load(APPROVAL)["execution"]
        self.assertEqual(execution["sent_at"], "2026-09-07T19:19:30+04:00")
        self.assertEqual(execution["displayed_sent_time"], "2026-09-07 19:26")
        self.assertTrue(execution["displayed_sent_time_differs_from_the_attested_one"])


class TestTheDiscriminatorWasNotSoftened(unittest.TestCase):
    def setUp(self):
        self.review = load(REVIEW)
        self.packet = load(PACKET)

    def test_the_quoted_branch_text_is_the_packets_own(self):
        branches = self.packet["expected_answer_discriminator"][
            "closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"
        ]
        scope = self.review["gates"]["THIRD_PARTY_TARGET_SCOPE"]
        self.assertEqual(scope["branch_text"], branches[scope["which_discriminator_branch"]])

    def test_all_seven_excluded_routes_are_still_excluded(self):
        excluded = self.packet["expected_answer_discriminator"]["does_not_close_r2_b"]
        self.assertEqual(len(excluded), 7)
        self.assertIn("implication or presupposition", excluded)

    def test_the_explicitness_requirement_is_intact(self):
        self.assertTrue(
            self.packet["expected_answer_discriminator"][
                "the_answer_must_address_third_party_target_scope_explicitly"
            ]
        )

    def test_an_anaphoric_answer_is_distinguished_from_a_presupposition(self):
        """A presupposition is implied by a statement about something else. An anaphoric
        answer is a statement about the question, and nothing is inferred to reach it."""
        responsiveness = self.review["gates"]["SEMANTIC_RESPONSIVENESS"]
        self.assertTrue(responsiveness["the_referent_is_supplied_by_the_question_not_inferred"])
        self.assertIn(
            "presupposition",
            responsiveness["why_this_is_not_the_presupposition_route_the_discriminator_refuses"],
        )
        self.assertTrue(responsiveness["unambiguity_test"].strip())

    def test_the_packet_asked_exactly_one_question(self):
        self.assertEqual(self.packet["body"].count("?"), 1)


class TestThePermissionIsAsWideAsTheQuestion(unittest.TestCase):
    def setUp(self):
        self.review = load(REVIEW)

    def test_every_limitation_survives_the_yes(self):
        limits = self.review["gates"]["LIMITS_PRESERVED"]
        self.assertEqual(limits["dropped_by_this_review"], 0)
        for limitation in gate().LIMITATIONS:
            with self.subTest(limitation=limitation):
                self.assertIn(limitation, limits["limitations"])

    def test_the_answer_is_not_read_as_unconditional(self):
        self.assertIn(
            "conditional", self.review["gates"]["LIMITS_PRESERVED"]["why_they_survive_a_yes"]
        )

    def test_nothing_beyond_head_is_established(self):
        bounded = self.review["gates"]["BOUNDED_HEAD_SCOPE"]
        self.assertTrue(bounded["the_permission_is_exactly_as_wide_as_the_question"])
        for item in gate().NOT_ESTABLISHED:
            with self.subTest(item=item):
                self.assertIn(item, bounded["not_established_by_this_answer"])

    def test_permitted_rather_than_conditionally_permitted_and_the_record_says_why(self):
        scope = self.review["gates"]["THIRD_PARTY_TARGET_SCOPE"]
        self.assertEqual(scope["status"], "PERMITTED")
        self.assertIn("ADDITIONAL", scope["why_not_conditionally_permitted"])


class TestAuthorityWasEstablishedAndBounded(unittest.TestCase):
    def setUp(self):
        self.review = load(REVIEW)

    def test_the_basis_is_the_provider_published_address(self):
        self.assertEqual(self.review["gates"]["SENDER_EMAIL"], "d@globalping.io")
        recipient = load(DATA / "globalping-r2-replacement-recipient-review-v1.json")
        self.assertTrue(recipient["establishment"]["address_is_established_first_party"])
        self.assertEqual(recipient["candidate_address"], "d@globalping.io")

    def test_the_github_username_link_is_corroboration_only(self):
        """Identifying a display name with a username is an inference, and Mission 1.74.4
        recorded exactly such a thing as corroboration only."""
        authority = self.review["gates"]["PROVIDER_AUTHORITY_ESTABLISHED"]
        self.assertEqual(authority["corroboration"]["treated_as"], "CORROBORATION_ONLY")
        self.assertTrue(authority["corroboration"]["why_not_the_basis"].strip())

    def test_it_is_recorded_as_weaker_than_r1(self):
        authority = self.review["gates"]["PROVIDER_AUTHORITY_ESTABLISHED"]
        weaker = authority["weaker_than_r1_and_the_record_says_so"]
        self.assertIn("MEMBER", weaker["r1_basis"])
        self.assertTrue(weaker["why_r1_is_stronger"].strip())

    def test_what_is_not_established_is_written_down(self):
        identity = self.review["gates"]["SENDER_IDENTITY_ESTABLISHED"]
        self.assertGreaterEqual(len(identity["what_is_not_established"]), 3)

    def test_it_closes_an_item_the_1_74_4_record_left_open(self):
        recipient = load(DATA / "globalping-r2-replacement-recipient-review-v1.json")
        self.assertIn(
            "that d@globalping.io is monitored, or answered",
            recipient["what_this_does_not_establish"],
        )


class TestTheEvidenceLevel(unittest.TestCase):
    def setUp(self):
        self.level = load(REVIEW)["evidence_level"]

    def test_every_condition_holds_and_carries_a_basis(self):
        conditions = self.level["conditions_all_of_which_must_hold"]
        for condition, basis in gate().LEVEL_CONDITIONS:
            with self.subTest(condition=condition):
                self.assertTrue(conditions[condition])
                self.assertTrue(str(conditions[basis]).strip())

    def test_it_is_a_sibling_of_the_r1_level_rather_than_that_level_stretched(self):
        r1 = load(R1_REVIEW)["question_4_evidence_level"]
        self.assertEqual(self.level["sibling_of"], r1["evidence_level"])
        self.assertNotEqual(self.level["level"], r1["evidence_level"])

    def test_the_condition_that_differs_is_named_with_what_replaces_it(self):
        differs = self.level["the_condition_that_differs_from_r1"]
        self.assertIn("durable_and_citable", differs["r1_condition"])
        self.assertTrue(differs["this_level_is_weaker_than_r1_and_the_record_says_so"])
        self.assertIn("1.45", differs["what_replaces_it"])

    def test_the_r1_level_conditions_were_not_edited(self):
        """They were written before this reply existed, which is what makes applying them
        a check rather than a description."""
        r1 = load(R1_REVIEW)["question_4_evidence_level"]
        self.assertEqual(r1["evidence_level"], "R1_A2_SOLICITED_RESPONSIVE_PROVIDER_ANSWER")
        self.assertTrue(r1["is_a_closing_level"])
        self.assertIn(
            "author_association MEMBER",
            r1["conditions_all_of_which_must_hold"]["attributable_basis"],
        )


class TestTheClosureChain(unittest.TestCase):
    def test_each_predecessor_gained_one_forward_pointer_and_nothing_else(self):
        for path, successor, field, value in (
            (SCOPE_V1, SCOPE_V2.name, "verdict", "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED"),
            (CLOSURE_V2, CLOSURE_V3.name, "residuals_remaining", 1),
            (QUAL_V3, QUAL_V4.name, "verdict", "COUNTERPART_UNRESOLVED"),
        ):
            with self.subTest(record=path.name):
                record = load(path)
                self.assertEqual(record["superseded_by"], successor)
                self.assertEqual(record[field], value)
                self.assertTrue(str(record["superseded_note"]).strip())

    def test_r2_b_closed_and_no_residual_remains(self):
        closure = load(CLOSURE_V3)
        self.assertEqual(closure["residuals_remaining"], 0)
        self.assertEqual(
            closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"], "PROVIDER_DECLARED_PERMITTED"
        )
        self.assertTrue(
            closure["r2_pass_requires_both"]["B_third_party_targets_within_permitted_use"]
        )

    def test_it_closed_on_a_declaration_and_not_on_documentation(self):
        scope = load(SCOPE_V2)
        self.assertFalse(scope["declared_not_documented"]["closed_on_documentation"])
        self.assertTrue(scope["declared_not_documented"]["the_terms_still_read_as_they_did"])

    def test_c9_moved_and_no_other_dimension_did(self):
        before = {g["dimension"]: g["status"] for g in load(QUAL_V3)["gates"]}
        after = {g["dimension"]: g["status"] for g in load(QUAL_V4)["gates"]}
        self.assertEqual(set(before), set(after))
        moved = [d for d in before if before[d] != after[d]]
        self.assertEqual(moved, ["C9_RIGHTS_FEASIBILITY"])
        self.assertEqual(after["C9_RIGHTS_FEASIBILITY"], "PASS")

    def test_the_tally_counts_the_gates(self):
        qual = load(QUAL_V4)
        counted = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0}
        for row in qual["gates"]:
            counted[row["status"]] += 1
        self.assertEqual(qual["tally"], counted)
        self.assertEqual(qual["tally"], {"PASS": 12, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0})
        self.assertEqual(qual["verdict"], "COUNTERPART_RESOLVED")

    def test_c9_passes_with_a_stated_bound(self):
        c9 = next(g for g in load(QUAL_V4)["gates"] if g["dimension"] == "C9_RIGHTS_FEASIBILITY")
        self.assertTrue(c9["stated_bound"].strip())
        self.assertIn("DECLARATION", c9["stated_bound"])
        self.assertTrue(c9["weaker_than_r1_evidence"])


class TestAClosedResidualAuthorisesNothing(unittest.TestCase):
    def setUp(self):
        self.qual = load(QUAL_V4)["what_qualification_does_not_authorise"]

    def test_nothing_is_selected_frozen_run_grouped_or_scored(self):
        for flag in (
            "no_construct_is_selected",
            "no_quantity_class_is_selected",
            "no_corpus_is_frozen",
            "no_measurement_was_run",
            "no_independence_group_exists",
            "no_score_is_issued",
        ):
            with self.subTest(flag=flag):
                self.assertTrue(self.qual[flag])

    def test_any_quantity_class_selection_authorises_nothing(self):
        """Re-pointed by Mission 1.76.6. Mission 1.76.5 selected no class and its own
        accounting still says so; a later selection may exist and must authorise no run."""
        selection_authorises_nothing(self, DATA / "selected-quantity-class-v1.json")

    def test_a_run_still_needs_operator_approval(self):
        self.assertTrue(any("approval" in item for item in self.qual["a_run_still_needs"]))

    def test_the_classification_is_not_a_legal_conclusion(self):
        classification = load(CLOSURE_V3)["project_governance_classification"]
        self.assertTrue(classification["this_is_not_a_legal_conclusion"])
        self.assertTrue(classification["what_would_reopen_it"])


class TestTheGateRefusesTheShortcuts(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.review = load(REVIEW)
        self.reply = load(REPLY)
        self.packet = load(PACKET)

    def refused(self, checker, *args):
        with self.assertRaises(self.gate.ValidationError):
            checker(*args)

    def test_the_records_as_committed_pass(self):
        self.gate.validate()

    def test_a_frozen_reply_carrying_a_verdict_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["verdict"] = "THIRD_PARTY_TARGET_SCOPE_PERMITTED"
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_an_edited_reply_body_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["reply"]["body"] = "Yes, and anything else you like"
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_an_invented_message_id_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["headers_as_displayed"]["message_id"] = "<CAF@mail.gmail.com>"
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_an_invented_offset_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["headers_as_displayed"]["displayed_time_carries_no_offset"] = False
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_committing_the_export_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["provenance"]["artifact_committed_to_this_repository"] = True
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_a_summarising_extraction_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["provenance"]["summarising_model_in_the_extraction_path"] = True
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_a_reply_from_another_address_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["headers_as_displayed"]["sender_email"] = "someone@example.com"
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_resolving_the_send_time_discrepancy_is_refused(self):
        reply = copy.deepcopy(self.reply)
        reply["discrepancy_recorded_rather_than_resolved"]["resolved"] = True
        self.refused(
            self.gate._check_the_reply_is_frozen_and_says_nothing_about_itself, reply, self.packet
        )

    def test_a_softened_discriminator_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["expected_answer_discriminator"][
            "closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"
        ]["PERMITTED"] = "anything vaguely affirmative"
        self.refused(self.gate._check_the_discriminator_was_not_softened, self.review, packet)

    def test_dropping_the_explicitness_requirement_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["expected_answer_discriminator"][
            "the_answer_must_address_third_party_target_scope_explicitly"
        ] = False
        self.refused(self.gate._check_the_discriminator_was_not_softened, self.review, packet)

    def test_recording_the_referent_as_inferred_is_refused(self):
        review = copy.deepcopy(self.review)
        review["gates"]["SEMANTIC_RESPONSIVENESS"][
            "the_referent_is_supplied_by_the_question_not_inferred"
        ] = False
        self.refused(self.gate._check_the_discriminator_was_not_softened, review, self.packet)

    def test_dropping_a_limitation_is_refused(self):
        for limitation in self.gate.LIMITATIONS:
            with self.subTest(limitation=limitation):
                review = copy.deepcopy(self.review)
                review["gates"]["LIMITS_PRESERVED"]["limitations"] = [
                    item
                    for item in review["gates"]["LIMITS_PRESERVED"]["limitations"]
                    if item != limitation
                ]
                self.refused(self.gate._check_the_permission_is_as_wide_as_the_question, review)

    def test_widening_the_activity_is_refused(self):
        for item in self.gate.NOT_ESTABLISHED:
            with self.subTest(item=item):
                review = copy.deepcopy(self.review)
                review["gates"]["BOUNDED_HEAD_SCOPE"]["not_established_by_this_answer"] = [
                    entry
                    for entry in review["gates"]["BOUNDED_HEAD_SCOPE"][
                        "not_established_by_this_answer"
                    ]
                    if entry != item
                ]
                self.refused(self.gate._check_the_permission_is_as_wide_as_the_question, review)

    def test_reading_the_permission_as_wider_than_the_question_is_refused(self):
        review = copy.deepcopy(self.review)
        review["gates"]["BOUNDED_HEAD_SCOPE"][
            "the_permission_is_exactly_as_wide_as_the_question"
        ] = False
        self.refused(self.gate._check_the_permission_is_as_wide_as_the_question, review)

    def test_promoting_the_github_link_to_the_basis_is_refused(self):
        review = copy.deepcopy(self.review)
        review["gates"]["PROVIDER_AUTHORITY_ESTABLISHED"]["corroboration"]["treated_as"] = "BASIS"
        self.refused(self.gate._check_authority_was_established_and_bounded, review)

    def test_a_level_condition_asserted_with_no_basis_is_refused(self):
        for condition, basis in self.gate.LEVEL_CONDITIONS:
            with self.subTest(condition=condition):
                review = copy.deepcopy(self.review)
                review["evidence_level"]["conditions_all_of_which_must_hold"][basis] = "  "
                self.refused(self.gate._check_the_evidence_level, review)

    def test_a_level_condition_that_does_not_hold_is_refused(self):
        for condition, _ in self.gate.LEVEL_CONDITIONS:
            with self.subTest(condition=condition):
                review = copy.deepcopy(self.review)
                review["evidence_level"]["conditions_all_of_which_must_hold"][condition] = False
                self.refused(self.gate._check_the_evidence_level, review)

    def test_hiding_that_the_level_is_weaker_than_r1_is_refused(self):
        review = copy.deepcopy(self.review)
        review["evidence_level"]["the_condition_that_differs_from_r1"][
            "this_level_is_weaker_than_r1_and_the_record_says_so"
        ] = False
        self.refused(self.gate._check_the_evidence_level, review)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the records do not carry', RENDERER.read_text("utf-8"))


class TestTheRendererAndGovernance(unittest.TestCase):
    def test_the_renderer_reaches_no_network_and_no_mailbox(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in ("smtplib", "imaplib", "requests", "httpx", "urllib", "subprocess"):
            with self.subTest(module=banned):
                self.assertNotIn(f"import {banned}", source)

    def test_the_page_quotes_the_reply_and_reports_the_closure(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("Yes it's not a problem", text)
        self.assertIn("COUNTERPART_RESOLVED", text)
        self.assertIn("12 / 0 / 0", text)

    def test_the_page_says_what_the_answer_does_not_establish(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("It does not establish", text)
        self.assertIn("A qualified counterpart is not a running one", text)

    def test_ci_runs_the_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_manifest_lists_the_new_records(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (REPLY, REVIEW, RENDERER):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "reports" / "mission-1.76.5-report.md").exists())


if __name__ == "__main__":
    unittest.main()
