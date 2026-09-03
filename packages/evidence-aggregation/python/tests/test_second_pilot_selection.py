"""Mission 1.38 §43. The candidate matrix, and the architectural gap that stopped it.

**Most of these are negative**, because the mission acquired nothing: its
load-bearing requirement is one Claim with two or more Evidence rows, and no
source can produce that under the current interpreter.

The positive ones assert the finding itself, and they assert it **against the
real source files** rather than against the document that describes them. A
document claiming every template pins the measurement identity is worth nothing
if a template stops doing so; these read `observed_restatement.py` and
`claim_repositories.py` directly.

`unittest`, no third-party dependency, so this runs in the zero-dependency CI job
(ADR-009) beside its siblings.
"""

from __future__ import annotations

import ast
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
SELECTION = DOCS / "second-pilot-selection-v1.json"
AUDIT = DOCS / "calibration-feasibility-audit-v1.json"
INTERPRETER = (
    REPO_ROOT
    / "services"
    / "nlp"
    / "python"
    / "sros_nlp"
    / "interpreters"
    / "observed_restatement.py"
)
REPOSITORIES = REPO_ROOT / "services" / "nlp" / "python" / "sros_nlp" / "claim_repositories.py"

# The measurement-identifying fact each template carries beyond `source_id`.
# Convergence requires two Signals to agree on ALL of them, which makes them the
# same measurement -- the thing §13 forbids.
MEASUREMENT_IDENTITY_FACTS = {
    "source_reported_metric_period_change": {"metric_id", "geography_source_code"},
    "platform_counted_content_request_change": {"content_id", "audience_class"},
    "community_site_published_questions_carrying_tag": {"community_site", "community_tag"},
    "community_site_questions_without_accepted_answer": {"community_site", "community_tag"},
    "source_reported_term_frequency_change": {"term", "gram_size"},
    "source_reported_term_frequency_contrast": {"term_a", "term_b"},
    "source_reported_procurement_value_contrast": {"notice_ids", "classification_codes"},
}


def selection() -> dict:
    return json.loads(SELECTION.read_text(encoding="utf-8"))


def audit() -> dict:
    return json.loads(AUDIT.read_text(encoding="utf-8"))


def template_fact_keys() -> dict[str, set[str]]:
    """Every `facts = {...}` literal in the interpreter, keyed by its proposition.

    Parsed from the AST rather than scanned as text, so a docstring naming a
    fact cannot be mistaken for one (`testing-strategy.md` §23).
    """
    tree = ast.parse(INTERPRETER.read_text(encoding="utf-8"))
    found: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "facts" not in targets:
            continue
        keys = {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
        proposition = None
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            if (
                isinstance(key, ast.Constant)
                and key.value == "proposition"
                and isinstance(value, ast.Constant)
            ):
                proposition = value.value
        if proposition:
            found[proposition] = keys
    return found


class TheFindingHoldsAgainstTheRealCode(unittest.TestCase):
    """The mission's conclusion, asserted where it could break."""

    def test_every_template_puts_source_id_in_its_proposition_facts(self) -> None:
        """So two Signals from different sources can never converge. That half is
        correct rather than a defect: attribution IS the claim for an OBSERVED
        proposition."""
        templates = template_fact_keys()
        self.assertTrue(templates)
        for proposition, keys in templates.items():
            self.assertIn("source_id", keys, proposition)

    def test_every_template_also_pins_the_measurement_identity(self) -> None:
        """This is the half that blocks convergence WITHIN a source."""
        templates = template_fact_keys()
        self.assertEqual(set(templates), set(MEASUREMENT_IDENTITY_FACTS))
        for proposition, required in MEASUREMENT_IDENTITY_FACTS.items():
            self.assertTrue(
                required <= templates[proposition],
                f"{proposition}: expected {required}, found {templates[proposition]}",
            )

    def test_the_two_stack_exchange_templates_differ_only_in_the_proposition_value(self) -> None:
        """The sharpest illustration: identical key shapes, two propositions by
        deliberate design (Mission 1.36)."""
        templates = template_fact_keys()
        self.assertEqual(
            templates["community_site_published_questions_carrying_tag"],
            templates["community_site_questions_without_accepted_answer"],
        )

    def test_persistence_would_accept_convergence_if_it_ever_happened(self) -> None:
        """The gap is upstream of storage: `_persist_one` looks a draft up by
        proposition_key and attaches evidence to the claim it finds."""
        source = REPOSITORIES.read_text(encoding="utf-8")
        self.assertIn("WHERE c.workspace_id = %s AND c.proposition_key = %s", source)
        self.assertIn("_persist_evidence(conn, draft, claim_id, report)", source)

    def test_the_measured_closest_pair_is_one_field_away(self) -> None:
        finding = selection()["the_blocking_finding"]["evidence"]["measured"]
        self.assertEqual(finding["claims"], 28)
        self.assertEqual(finding["distinct_proposition_keys"], 28)
        self.assertEqual(finding["closest_pairs_differ_by"], 1)
        self.assertEqual(finding["the_single_differing_field"], "content_id")

    def test_the_gap_is_recorded_as_partly_correct_rather_than_simply_broken(self) -> None:
        """Deleting `source_id` would be the wrong repair, and the artifact says so."""
        finding = selection()["the_blocking_finding"]
        self.assertIn("attribution IS the claim", finding["why_it_is_also_partly_correct"])
        self.assertIn("not to delete source_id", finding["why_it_is_also_partly_correct"])


class TheCandidateMatrix(unittest.TestCase):
    """§3, §5, §31."""

    def test_between_three_and_seven_serious_candidates(self) -> None:
        self.assertGreaterEqual(len(selection()["candidates"]), 3)
        self.assertLessEqual(len(selection()["candidates"]), 7)

    def test_every_candidate_reports_every_required_column(self) -> None:
        required = {
            "candidate",
            "domain",
            "subject_scope",
            "authoritative_taxonomy",
            "canonical_identifier",
            "available_source_families",
            "multi_evidence_claim_path",
            "commercial_evidence_path",
            "governance_status",
            "collector_status",
            "calibration_diversity_contribution",
            "primary_limitation",
            "verdict",
        }
        for candidate in selection()["candidates"]:
            self.assertTrue(required <= set(candidate), candidate["candidate"])

    def test_no_candidate_carries_a_numeric_score(self) -> None:
        """§3. Ordinal reasoning, and no ranking number anywhere."""
        for candidate in selection()["candidates"]:
            for key, value in candidate.items():
                self.assertNotIsInstance(value, (int, float), f"{candidate['candidate']}.{key}")

    def test_the_verdicts_come_from_the_declared_set(self) -> None:
        permitted = {
            "SELECT",
            "QUALIFIED_ALTERNATIVE",
            "GOVERNANCE_BLOCKED",
            "WRONG_GRAIN",
            "NO_MULTI_EVIDENCE_PATH",
            "INSUFFICIENT_COMMERCIAL_PATH",
            "TOO_SIMILAR_TO_DOCKER",
        }
        for candidate in selection()["candidates"]:
            self.assertIn(candidate["verdict"], permitted, candidate["candidate"])

    def test_a_developer_tooling_candidate_was_considered_and_refused(self) -> None:
        """§1 forbids picking one for collector convenience; the refusal is
        recorded rather than left implicit."""
        verdicts = {c["candidate"]: c["verdict"] for c in selection()["candidates"]}
        similar = [c for c, v in verdicts.items() if v == "TOO_SIMILAR_TO_DOCKER"]
        self.assertTrue(similar)

    def test_the_preferred_consumer_domains_are_recorded_as_governance_blocked(self) -> None:
        """§33 prefers gaming and consumer; §4 makes governance a hard stop, and
        the matrix must show which one won."""
        blocked = [c for c in selection()["candidates"] if c["verdict"] == "GOVERNANCE_BLOCKED"]
        self.assertTrue(blocked)
        for candidate in blocked:
            self.assertIn("BLOCKED AT THE ELIGIBILITY GATE", candidate["governance_status"])

    def test_governance_was_read_from_the_live_catalog_not_from_history(self) -> None:
        """§4, §31."""
        state = selection()["governance_state_read_at_selection"]
        self.assertIn("live catalog", state["read_from"])
        self.assertEqual(
            set(state["eligible_resource_ready_and_collector_implemented"]),
            {"gdelt", "stack-exchange", "ted-eu", "wikimedia-pageviews"},
        )
        for blocked in ("steam", "product-hunt", "github", "reddit", "twitch", "google-play"):
            self.assertIn(blocked, state["blocked_at_the_eligibility_gate"])

    def test_no_candidate_claims_a_multi_evidence_path(self) -> None:
        """The finding, restated per candidate: none of them fails for a
        source-side reason."""
        for candidate in selection()["candidates"]:
            path = candidate["multi_evidence_claim_path"]
            self.assertTrue(
                path.startswith("BLOCKED") or path == "not reached", candidate["candidate"]
            )


class NothingWasAcquiredOrCreated(unittest.TestCase):
    """§38, §39, §41, §42. The mission's whole effect on canonical state is nil."""

    def test_no_pilot_was_selected_and_no_acquisition_ran(self) -> None:
        self.assertIsNone(selection()["selected_pilot"])
        self.assertFalse(selection()["acquisition_performed"])

    def test_the_outcome_is_the_architecture_gap(self) -> None:
        self.assertEqual(selection()["outcome"], "MULTI_EVIDENCE_CLAIM_ARCHITECTURE_GAP")

    def test_no_model_call_and_no_embedding(self) -> None:
        """§41, §42."""
        did_not = selection()["what_this_mission_did_not_do"]
        self.assertEqual(did_not["model_calls"], 0)
        self.assertEqual(did_not["embeddings"], 0)

    def test_docker_was_not_touched(self) -> None:
        self.assertIn("untouched", selection()["what_this_mission_did_not_do"]["docker"])

    def test_problem_family_was_not_used_to_merge_claims(self) -> None:
        """§40. Convergence must follow proposition-key semantics."""
        self.assertIn("PARKED", selection()["what_this_mission_did_not_do"]["problem_family"])
        text = json.dumps(selection())
        self.assertNotIn("SAME_PROBLEM_FAMILY", text)

    def test_no_reliability_assessment_was_created(self) -> None:
        """§20. Two, unchanged."""
        self.assertIn("Two, unchanged", selection()["what_this_mission_did_not_do"]["reliability"])
        self.assertEqual(audit()["totals"]["current_reliability_assessments"], 2)

    def test_no_score_and_no_ranking(self) -> None:
        """§39."""
        did_not = selection()["what_this_mission_did_not_do"]
        self.assertIn("scoring.scores does not exist", did_not["opportunity_score"])
        text = json.dumps(selection())
        for forbidden in ("OpportunityScore", "RankingScore", "PriorityScore"):
            self.assertNotIn(forbidden, text)

    def test_the_corpus_shape_did_not_move(self) -> None:
        """§37. Before equals after, because nothing was created."""
        # The corpus SHAPE, not its size. Mission 1.40 acquired a second pilot
        # and the counts moved; what did not move is the one thing this asserts.
        self.assertEqual({u["evidence_count"] for u in audit()["units"]}, {1})
        self.assertEqual(audit()["coverage"]["multi_evidence_claims"], 0)
        self.assertEqual(audit()["totals"]["claims"], audit()["totals"]["evidence_rows"])


class TheRepairIsLeftToItsOwnMission(unittest.TestCase):
    """§46. A gap of this kind is repaired before more acquisition, not during it."""

    def test_the_exact_gap_is_named(self) -> None:
        nxt = selection()["next_mission"]
        self.assertIn("one-to-one restatement", nxt["the_exact_gap"])
        self.assertTrue(nxt["not_started_by_this_mission"])

    def test_the_repair_questions_are_recorded_rather_than_answered(self) -> None:
        decisions = selection()["next_mission"]["what_the_repair_must_decide"]
        self.assertGreaterEqual(len(decisions), 3)
        joined = " ".join(decisions)
        self.assertIn("INFERRED", joined)
        self.assertIn("deterministic and source-bounded", joined)

    def test_identity_was_not_weakened_to_avoid_the_outcome(self) -> None:
        """§8 and §44 E both forbid it, and the artifact says which two fields
        would have had to go."""
        case = selection()["the_blocking_finding"]["a_concrete_convergence_that_should_be_possible"]
        self.assertIn("notice_ids", case["why_they_cannot"])
        self.assertIn("classification_codes", case["why_they_cannot"])
        self.assertIn("forbids weakening identity", case["why_this_mission_did_not_fix_it"])

    def test_a_concrete_convergence_case_is_given_rather_than_asserted(self) -> None:
        """§44 E requires that real Signals SHOULD legitimately converge. An
        abstract gap would not qualify."""
        case = selection()["the_blocking_finding"]["a_concrete_convergence_that_should_be_possible"]
        self.assertIn("TED", case["case"])
        self.assertTrue(case["why_they_should_converge"].strip())

    def test_the_carried_candidate_fails_only_on_the_architecture(self) -> None:
        carried = selection()["next_mission"]["candidate_to_carry_forward"]
        self.assertIn("CPV", carried)
        ted = next(c for c in selection()["candidates"] if "CPV" in c["candidate"])
        self.assertEqual(ted["verdict"], "NO_MULTI_EVIDENCE_PATH")
        self.assertIn("ELIGIBLE", ted["governance_status"])


class TheDocumentDoesNotOverclaim(unittest.TestCase):
    def test_no_cpv_division_label_was_supplied_from_memory(self) -> None:
        """Mission 1.33 recorded that the collector expands no CPV code into a
        label. Naming one here would be doing what the collector refuses."""
        text = json.dumps(selection())
        self.assertIn("expands no CPV code into a label", text)
        self.assertNotIn("recreation, culture", text)
        self.assertNotIn("education services", text)

    def test_no_taxonomy_was_invented(self) -> None:
        """§36. An SROS-only category would satisfy the requirement on paper."""
        for candidate in selection()["candidates"]:
            taxonomy = candidate["authoritative_taxonomy"]
            if taxonomy.startswith("NONE"):
                self.assertIn(candidate["verdict"], {"WRONG_GRAIN", "TOO_SIMILAR_TO_DOCKER"})


if __name__ == "__main__":
    unittest.main()
