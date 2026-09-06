"""Mission 1.74.7. The provider answered, and the answer is frozen before it is read.

Four things this file defends.

THE FROZEN SOURCE AND THE INTERPRETATION ARE TWO DOCUMENTS. One may only record what the
public surface says; the other may reason. A single document that held both could quietly
adjust the evidence to suit the conclusion, and neither half would show it.

A SUPPLIED STRING IS A CLAIM. The reply was quoted in the instruction and it is frozen
from the stored bytes, which differ from the quotation by one trailing space. The
difference changes no meaning, which is exactly why it is worth recording: a record that
adopted the quotation silently here would have adopted it just as silently where it
mattered.

A SOLICITED ANSWER IS NOT A STATEMENT SOMEBODY FOUND. Mission 1.74 refused to upgrade on
an incidental maintainer remark, and that refusal stands untouched. What closed R1 was
ASKED FOR, answers the exact frozen predicate, is attributable, is citable, and was read
raw -- five conditions, and failing any one drops it back to the incidental level.

A CLOSED RESIDUAL IS NOT A QUALIFIED COUNTERPART. C6 moves to PASS and the tally to
11/1/0, and the verdict stays COUNTERPART_UNRESOLVED, because C9 is still PARTIAL on R2.
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

FROZEN = DATA / "globalping-r1-provider-reply-v1.json"
REVIEW = DATA / "globalping-r1-reply-review-v1.json"
REDIRECT_V2 = DATA / "globalping-redirect-contract-review-v2.json"
REDIRECT_V1 = DATA / "globalping-redirect-contract-review-v1.json"
R1_PACKET = DATA / "globalping-r1-enquiry-packet-v1.json"
R1_DISPATCH = DATA / "globalping-r1-dispatch-approval-v1.json"
QUALIFICATION_V3 = DATA / "globalping-counterpart-qualification-v3.json"
CLOSURE_V2 = DATA / "globalping-residual-closure-v2.json"
RENDERER = SCRIPTS / "render_globalping_residuals.py"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    """The renderer as a module, so its checks run against dicts rather than its source."""
    spec = importlib.util.spec_from_file_location("render_globalping_residuals", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheReplyIsFrozenBeforeItIsRead(unittest.TestCase):
    def setUp(self):
        self.frozen = load(FROZEN)
        self.reply = self.frozen["reply"]

    def test_the_source_record_declares_itself_a_source_and_carries_no_interpretation(self):
        self.assertEqual(self.frozen["record_kind"], "FROZEN_PROVIDER_REPLY_SOURCE")
        self.assertFalse(self.frozen["contains_interpretation"])
        for forbidden in ("verdict", "evidence_level", "evidence_level_assigned"):
            with self.subTest(field=forbidden):
                self.assertNotIn(forbidden, self.frozen)

    def test_the_reply_answers_to_its_own_hash(self):
        self.assertEqual(
            self.reply["body_sha256"],
            hashlib.sha256(self.reply["body"].encode("utf-8")).hexdigest(),
        )

    def test_a_supplied_string_is_a_claim_and_the_stored_bytes_win(self):
        self.assertFalse(self.reply["operator_quotation_matches_the_stored_bytes"])
        self.assertNotEqual(self.reply["body_as_quoted_by_the_operator"], self.reply["body"])
        self.assertTrue(self.reply["body_has_trailing_whitespace"])
        self.assertTrue(self.reply["difference_from_the_operator_quotation"].strip())
        self.assertTrue(self.reply["why_the_stored_bytes_win"].strip())

    def test_the_quotation_is_the_reply_apart_from_that_whitespace(self):
        self.assertEqual(self.reply["body"].rstrip(), self.reply["body_as_quoted_by_the_operator"])

    def test_the_comment_was_not_edited_after_posting(self):
        self.assertFalse(self.reply["body_edited_after_posting"])
        self.assertTrue(self.reply["how_that_is_known"].strip())

    def test_the_retrieval_was_raw_and_public(self):
        provenance = self.frozen["provenance"]
        self.assertEqual(provenance["retrieval_method"], "RAW_GITHUB_REST_API_READ")
        self.assertFalse(provenance["went_through_a_summarising_extraction"])
        self.assertFalse(provenance["html_to_markdown_conversion_performed"])
        self.assertTrue(provenance["endpoints_are_public"])
        self.assertFalse(provenance["undocumented_endpoint_used"])
        self.assertFalse(provenance["credential_value_read_or_recorded"])
        for endpoint in provenance["endpoints_read"]:
            with self.subTest(endpoint=endpoint):
                self.assertTrue(endpoint.startswith("GET "))

    def test_no_retrieval_timestamp_was_typed_in(self):
        self.assertFalse(self.frozen["provenance"]["retrieved_at_recorded"])
        self.assertTrue(self.frozen["provenance"]["why_no_retrieval_timestamp"].strip())

    def test_the_location_is_permalinked_and_singular(self):
        location = self.frozen["location"]
        self.assertEqual(location["repository"], "jsdelivr/globalping")
        self.assertEqual(location["issue_number"], 907)
        self.assertIn("#issuecomment-", location["comment_permalink"])
        self.assertTrue(location["this_is_the_only_comment"])

    def test_the_author_is_placed_inside_the_owning_organisation(self):
        author = self.frozen["author"]
        self.assertEqual(author["author_association"], "MEMBER")
        self.assertTrue(author["listed_in_the_owning_organisations_public_members"])
        self.assertTrue(author["profile_company_is_self_declared_not_verified"])
        self.assertFalse(author["is_the_author_of_the_question"])

    def test_the_reply_sits_under_the_question_this_project_froze(self):
        link = self.frozen["relationship_to_gp_r1_q1"]
        packet = load(R1_PACKET)
        self.assertEqual(link["question_id"], "GP-R1-Q1")
        self.assertTrue(link["issue_body_is_byte_identical_to_the_frozen_packet_body"])
        self.assertTrue(link["issue_title_matches_the_packet_subject"])
        self.assertEqual(
            link["packet_body_sha256"],
            hashlib.sha256(packet["body"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(link["issue_body_sha256"], link["packet_body_sha256"])

    def test_nothing_was_measured_to_obtain_it(self):
        accounting = self.frozen["mission_accounting"]
        for counter in (
            "GLOBALPING_API_EXECUTIONS",
            "GLOBALPING_MEASUREMENTS_CREATED",
            "TARGET_HTTP_REQUESTS",
            "SROS_FETCHER_RUNS",
            "GITHUB_COMMENTS_CREATED",
            "CREDENTIAL_READS",
            "CANONICAL_MUTATIONS",
        ):
            with self.subTest(counter=counter):
                self.assertEqual(accounting[counter], 0)
        self.assertEqual(accounting["PUBLIC_API_READS"], 4)


class TestTheInterpretationIsASeparateDocument(unittest.TestCase):
    def setUp(self):
        self.review = load(REVIEW)
        self.frozen = load(FROZEN)

    def test_it_declares_itself_an_interpretation_and_cites_the_source_by_hash(self):
        self.assertEqual(self.review["record_kind"], "REVIEWED_INTERPRETATION")
        source = self.review["source"]
        self.assertFalse(source["reply_restated_in_this_record"])
        self.assertEqual(source["reply_body_sha256"], self.frozen["reply"]["body_sha256"])
        self.assertEqual(
            source["frozen_reply_file_sha256"], hashlib.sha256(FROZEN.read_bytes()).hexdigest()
        )

    def test_the_reply_text_appears_in_the_source_and_not_in_the_interpretation(self):
        body = self.frozen["reply"]["body"].strip()
        self.assertNotIn(body, REVIEW.read_text(encoding="utf-8"))

    def test_attribution_is_graded_rather_than_pooled(self):
        attribution = self.review["question_1_attribution"]
        self.assertEqual(attribution["answer"], "YES")
        self.assertTrue(attribution["provider_authority_established"])
        strengths = {s["signal"]: s["strength"] for s in attribution["signals"]}
        self.assertEqual(strengths["profile company field"], "WEAK")
        self.assertIn("STRONG", strengths.values())
        self.assertIn("authorised to bind", attribution["what_this_does_not_establish"])

    def test_both_halves_are_examined_separately(self):
        semantics = self.review["question_2_and_3_semantics"]
        self.assertTrue(semantics["clause_1"]["established"])
        self.assertTrue(semantics["clause_2"]["established"])
        self.assertEqual(semantics["redirect_response_returned"], "ESTABLISHED")
        self.assertEqual(semantics["redirect_not_followed"], "ESTABLISHED")
        self.assertTrue(semantics["both_required_semantics_established"])

    def test_the_weaker_clause_is_settled_by_the_stronger_one(self):
        semantics = self.review["question_2_and_3_semantics"]
        self.assertTrue(semantics["clause_1"]["weakness_examined"].strip())
        self.assertIn("forecloses", semantics["why_the_two_clauses_settle_each_other"])

    def test_the_answer_is_not_read_as_broader_than_the_question(self):
        semantics = self.review["question_2_and_3_semantics"]
        self.assertFalse(semantics["treated_as_broader_than_the_question"])
        limits = " ".join(semantics["what_the_reply_does_not_establish"])
        self.assertIn("HEAD", limits)
        self.assertIn("chains", limits)

    def test_the_new_level_is_defined_by_conditions_rather_than_by_judgement(self):
        level = self.review["question_4_evidence_level"]
        self.assertEqual(level["evidence_level"], "R1_A2_SOLICITED_RESPONSIVE_PROVIDER_ANSWER")
        conditions = level["conditions_all_of_which_must_hold"]
        for condition in (
            "solicited",
            "responsive_to_the_exact_predicate",
            "attributable_to_the_provider",
            "durable_and_citable",
            "retrieved_without_a_summarising_extraction",
        ):
            with self.subTest(condition=condition):
                self.assertTrue(conditions[condition])
        self.assertEqual(
            level["if_any_condition_failed_the_level_would_be"],
            "PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL",
        )

    def test_it_closes_because_mission_1_74_said_in_advance_that_it_would(self):
        level = self.review["question_4_evidence_level"]
        self.assertTrue(level["is_a_closing_level"])
        self.assertIn("technical channel", level["closable_by_as_frozen_in_mission_1_74"])
        self.assertEqual(
            level["closable_by_as_frozen_in_mission_1_74"], load(REDIRECT_V1)["closable_by"]
        )

    def test_the_incidental_guard_is_left_alone(self):
        level = self.review["question_4_evidence_level"]
        self.assertTrue(level["the_incidental_statement_guard_is_unchanged"])
        self.assertIn("ASKED FOR", level["why_that_guard_still_holds"])

    def test_the_label_narrows_the_discriminator_rather_than_reinterpreting_it(self):
        verdict = self.review["question_4_verdict"]
        self.assertEqual(verdict["verdict"], "R1_PASS_PROVIDER_DECLARED_NO_REDIRECT")
        self.assertTrue(verdict["discriminator_decision_honoured"])
        self.assertFalse(verdict["discriminator_label_used_verbatim"])
        self.assertIn("NARROWING", verdict["why_the_label_differs"])
        self.assertEqual(
            verdict["discriminator_frozen_before_the_send"],
            load(R1_PACKET)["expected_answer_discriminator"],
        )

    def test_what_remains_open_even_at_pass_is_written_down(self):
        self.assertIn(
            "declared and not specified",
            self.review["question_4_verdict"]["what_remains_open_even_at_pass"],
        )

    def test_the_tally_moves_and_the_verdict_does_not(self):
        block = self.review["question_5_qualification"]
        self.assertEqual(block["c6_before"], "PARTIAL")
        self.assertEqual(block["c6_after"], "PASS")
        self.assertEqual(block["c9_after"], "PARTIAL")
        self.assertEqual(block["tally_after"], {"PASS": 11, "PARTIAL": 1, "FAIL": 0, "UNKNOWN": 0})
        self.assertFalse(block["verdict_changed"])
        self.assertEqual(block["verdict_after"], "COUNTERPART_UNRESOLVED")

    def test_the_review_stayed_inside_r1(self):
        bounded = self.review["bounded_to_r1"]
        self.assertFalse(bounded["r2_examined"])
        self.assertFalse(bounded["r2_dispatch_state_altered"])
        self.assertFalse(bounded["r2_reply_claimed"])
        self.assertEqual(bounded["globalping_measurements_run"], 0)
        self.assertEqual(bounded["target_http_requests"], 0)
        self.assertFalse(bounded["quantity_class_selected"])
        self.assertFalse(bounded["construct_selected"])
        self.assertEqual(bounded["evidence_independence_groups_created"], 0)

    def test_the_chain_is_four_separate_documents(self):
        chain = self.review["chain"]
        self.assertTrue(chain["each_step_is_a_separate_document"])
        self.assertFalse(chain["interpretation_written_into_the_frozen_source"])
        self.assertEqual(
            len(
                {
                    chain["frozen_source_record"],
                    chain["reviewed_interpretation"],
                    chain["gate_result"],
                }
            ),
            3,
        )


class TestTheGateRefusesWhatWouldNotHaveClosedIt(unittest.TestCase):
    """A refusal spelled in a module is not a refusal until something calls it."""

    def setUp(self):
        self.gate = gate()
        self.redirect = load(REDIRECT_V2)

    def refused(self, redirect):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_solicited_answer(redirect)

    def test_the_record_as_committed_passes(self):
        self.gate._check_solicited_answer(self.redirect)
        self.gate._check_r1(self.redirect)

    def test_each_missing_condition_is_refused_on_its_own(self):
        for condition in self.gate.SOLICITED_ANSWER_CONDITIONS:
            with self.subTest(condition=condition):
                redirect = copy.deepcopy(self.redirect)
                redirect["solicited_provider_answer"][condition] = False
                self.refused(redirect)

    def test_an_unestablished_half_is_refused(self):
        for half in ("redirect_response_returned", "redirect_not_followed"):
            with self.subTest(half=half):
                redirect = copy.deepcopy(self.redirect)
                redirect["solicited_provider_answer"][half] = "SUGGESTED"
                self.refused(redirect)

    def test_an_answer_read_as_broader_than_the_question_is_refused(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["solicited_provider_answer"]["treated_as_broader_than_the_question"] = True
        self.refused(redirect)

    def test_a_stated_limit_is_required(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["solicited_provider_answer"]["what_it_does_not_establish"] = "   "
        self.refused(redirect)

    def test_a_reply_the_frozen_record_does_not_hold_is_refused(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["solicited_provider_answer"]["reply_body_sha256"] = "0" * 64
        self.refused(redirect)

    def test_a_different_author_in_the_gate_record_is_refused(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["solicited_provider_answer"]["author_login"] = "someone-else"
        self.refused(redirect)

    def test_the_gate_record_may_not_restate_the_reply(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["solicited_provider_answer"]["reply_restated_here"] = True
        self.refused(redirect)

    def test_a_non_closing_level_cannot_produce_a_passing_verdict(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["evidence_level"] = "PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL"
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_r1(redirect)

    def test_a_documented_verdict_is_refused_while_no_surface_documents_it(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["verdict"] = "R1_PASS_DOCUMENTED_NO_REDIRECT"
        redirect["evidence_level"] = "R1_A_NORMATIVE_PROVIDER_CONTRACT"
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_r1(redirect)

    def test_an_incidental_statement_still_cannot_be_graded_as_closing(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["provider_statements_found"][0]["evidence_level"] = (
            "R1_A2_SOLICITED_RESPONSIVE_PROVIDER_ANSWER"
        )
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_r1(redirect)

    def test_an_answer_recorded_without_resting_the_verdict_on_it_is_refused(self):
        redirect = copy.deepcopy(self.redirect)
        redirect["verdict"] = "R1_PARTIAL_IMPLEMENTATION_ONLY"
        redirect["evidence_level"] = "R1_C_IMPLEMENTATION_OBSERVED"
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_r1(redirect)

    def test_the_supersession_check_passes_as_committed(self):
        self.gate._check_supersession()


class TestClosingOneResidualQualifiesNothing(unittest.TestCase):
    def test_the_tally_moved_and_the_verdict_did_not(self):
        qualification = load(QUALIFICATION_V3)
        self.assertEqual(qualification["tally"]["PASS"], 11)
        self.assertEqual(qualification["tally"]["PARTIAL"], 1)
        self.assertEqual(qualification["verdict"], "COUNTERPART_UNRESOLVED")
        self.assertTrue(qualification["tally_changed"])
        self.assertFalse(qualification["verdict_changed"])

    def test_r2_was_not_touched(self):
        closure = load(CLOSURE_V2)
        residuals = {r["id"]: r for r in closure["residuals"]}
        self.assertFalse(closure["r2_touched_by_this_mission"])
        self.assertEqual(
            residuals["R2"]["verdict"],
            "R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED",
        )
        self.assertFalse(residuals["R2"]["closed"])

    def test_the_r1_dispatch_reached_byte_verified_on_this_read(self):
        execution = load(R1_DISPATCH)["execution"]
        self.assertEqual(execution["attestation_level"], "BYTE_VERIFIED")
        self.assertTrue(execution["raw_body_compared"])
        self.assertEqual(execution["byte_verification"]["performed_by_mission"], "1.74.7")
        self.assertEqual(execution["github_api_write_calls_made_by_this_repository"], 0)


class TestGovernanceRecordsThis(unittest.TestCase):
    def test_the_manifest_lists_the_two_new_records(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (FROZEN, REVIEW, REDIRECT_V2, CLOSURE_V2, QUALIFICATION_V3):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "architecture" / "mission-1.74.7-report.md").exists())


if __name__ == "__main__":
    unittest.main()
