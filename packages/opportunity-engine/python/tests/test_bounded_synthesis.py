"""Mission 1.31 §19. Every gate, asserted before the provider was ever called.

The mission's rule is that these run and pass FIRST. A gate written after seeing
the answer is not a gate, and one that has never been exercised against a hostile
output is a comment.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest
from sros_opportunity import (
    AUDIT_VERSION,
    MANDATORY_UNSUPPORTED_REPORT,
    PERSISTENCE_GATE_VERSION,
    SYNTHESIS_OUTPUT_SCHEMA,
    SYNTHESIS_PROCEDURE_VERSION,
    SYNTHESIS_PROMPT_VERSION,
    SYNTHESIS_SYSTEM,
    EvidenceDimension,
    HypothesisStatus,
    OpportunityStatus,
    PacketEligibility,
    StatementSupport,
    audit_synthesis,
    build_packet,
    check_statement,
    evaluate,
    evaluate_persistence,
    render_synthesis_prompt,
    synthesis_prompt_hash,
)

from .test_opportunity_engine import facets

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1] / "sros_opportunity"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"

STATEMENTS = {
    "c1": (
        'Stack Exchange published 88 questions carrying its own tag "docker" on '
        '"stackoverflow", created between source timestamps "1709280363" and "1709612240".'
    ),
    "c2": (
        'Wikimedia Analytics (Pageviews) counted 36 more requests for "Docker_(software)" '
        'on "en.wikipedia.org" on "2024-03-06" than on "2024-03-05", under its own '
        'requester class "user".'
    ),
}
EVIDENCE_TO_CLAIM = {"e1": "c1", "e2": "c2"}


def packet():
    rows = (
        (
            facets(
                evidence_id="e1",
                claim_id="c1",
                source_id="stack-exchange",
                source_family="forum",
                signal_type_id="community_question_volume",
                dimensions=frozenset({EvidenceDimension.PROBLEM_OR_NEED}),
                dimension_bound="a count of public questions carrying one site tag",
            ),
            PacketEligibility.ELIGIBLE_CONTEXT,
        ),
        (
            facets(
                evidence_id="e2",
                claim_id="c2",
                dimensions=frozenset(
                    {EvidenceDimension.AUDIENCE_OR_USAGE, EvidenceDimension.TREND_OR_CHANGE}
                ),
            ),
            PacketEligibility.ELIGIBLE_CONTEXT,
        ),
    )
    return build_packet(None, "subject:docker", rows)


def good_output(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "decision": "FORM_HYPOTHESIS",
        "subject": "docker",
        "target_actor_if_supported": "UNKNOWN_NOT_SUPPORTED",
        "observed_need": "People published questions asking for help with the subject.",
        "candidate_intervention_class": "Assistance for people asking such questions.",
        "hypothesis_statement": (
            "It may be worth investigating interventions that assist people who publish "
            "questions about the subject."
        ),
        "supported_dimensions": ["PROBLEM_OR_NEED", "AUDIENCE_OR_USAGE"],
        "unsupported_dimensions": [d.value for d in MANDATORY_UNSUPPORTED_REPORT],
        "supporting_evidence_ids": ["e1", "e2"],
        "supporting_claim_ids": ["c1", "c2"],
        "source_families": ["forum", "knowledge"],
        "independence_status": "UNKNOWN for all rows; source-family diversity only.",
        "reliability_status": "NON_SCORABLE, MISSING_RELIABILITY for every row.",
        "evidence_bound_reasoning_summary": "Two bounded statements were supplied.",
        "critical_uncertainties": ["nothing establishes a buyer"],
        "commercial_claims_supported": [],
        "commercial_claims_not_supported": ["willingness to pay"],
    }
    base.update(overrides)
    return base


def gate(output: dict[str, object]):
    return evaluate_persistence(
        output, packet(), STATEMENTS, EVIDENCE_TO_CLAIM, MANDATORY_UNSUPPORTED_REPORT
    )


class TestOnlyAFormablePacketEntersSynthesis:
    def test_the_real_packet_is_formable_before_anything_is_sent(self) -> None:
        assert evaluate(packet()).status is HypothesisStatus.HYPOTHESIS_FORMABLE

    def test_a_one_dimension_packet_is_not_formable(self) -> None:
        rows = (
            (
                facets(evidence_id="e1", claim_id="c1"),
                PacketEligibility.ELIGIBLE_CONTEXT,
            ),
            (
                facets(evidence_id="e2", claim_id="c2"),
                PacketEligibility.ELIGIBLE_CONTEXT,
            ),
        )
        assert (
            evaluate(build_packet(None, "s", rows)).status
            is HypothesisStatus.HYPOTHESIS_INSUFFICIENT_EVIDENCE
        )


class TestTheBoundaryHolds:
    """§8, §9. The package cannot reach a provider, and the prompt keeps regions apart."""

    def test_the_package_imports_no_gateway_or_provider(self) -> None:
        forbidden = ("sros_llm_gateway", "anthropic", "openai", "httpx", "psycopg")
        for path in sorted(PACKAGE_ROOT.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    for bad in forbidden:
                        assert not name.startswith(bad), f"{path.name} imports {name}"

    def test_source_derived_statements_occupy_the_untrusted_region_only(self) -> None:
        parts = render_synthesis_prompt(packet(), STATEMENTS, EVIDENCE_TO_CLAIM)
        assert len(parts.untrusted) == 2
        for statement in STATEMENTS.values():
            assert statement not in parts.system_instructions
            assert statement not in parts.task
            assert statement not in parts.trusted_context
            assert any(statement == content for content, _ in parts.untrusted)

    def test_every_untrusted_block_is_labelled_with_its_ids(self) -> None:
        parts = render_synthesis_prompt(packet(), STATEMENTS, EVIDENCE_TO_CLAIM)
        labels = {label for _, label in parts.untrusted}
        assert labels == {"evidence=e1 claim=c1", "evidence=e2 claim=c2"}

    def test_the_prompt_withdraws_prior_knowledge_explicitly(self) -> None:
        assert "USE ONLY THE SUPPLIED EVIDENCE" in SYNTHESIS_SYSTEM
        assert "prior knowledge" in SYNTHESIS_SYSTEM.lower()

    def test_no_numeric_confidence_is_requested(self) -> None:
        properties = SYNTHESIS_OUTPUT_SCHEMA["properties"]
        assert isinstance(properties, dict)
        assert "confidence" not in properties
        for field in properties.values():
            assert field["type"] != "number", field

    def test_the_prompt_is_versioned_and_hashed(self) -> None:
        assert SYNTHESIS_PROCEDURE_VERSION == "opportunity-synthesis@1.0.0"
        assert SYNTHESIS_PROMPT_VERSION == "1.0.0"
        assert len(synthesis_prompt_hash()) == 64

    def test_the_prompt_carries_the_independence_and_reliability_facts(self) -> None:
        """§2, §3. The model is TOLD, rather than left to notice."""
        parts = render_synthesis_prompt(packet(), STATEMENTS, EVIDENCE_TO_CLAIM)
        assert "independence is UNKNOWN" in parts.task
        assert "NON_SCORABLE" in parts.task
        assert "MISSING_RELIABILITY" in parts.task

    def test_the_prompt_lists_the_mandatory_unsupported_dimensions(self) -> None:
        parts = render_synthesis_prompt(packet(), STATEMENTS, EVIDENCE_TO_CLAIM)
        for dimension in MANDATORY_UNSUPPORTED_REPORT:
            assert dimension.value in parts.task or dimension.value in parts.trusted_context

    def test_the_prompt_supplies_what_each_dimension_never_means(self) -> None:
        parts = render_synthesis_prompt(packet(), STATEMENTS, EVIDENCE_TO_CLAIM)
        assert "never means" in parts.trusted_context


class TestTheFrozenPersistenceGate:
    """§12. Every clause, exercised against an output designed to violate it."""

    def test_a_clean_output_passes(self) -> None:
        decision = gate(good_output())
        assert decision.persist, decision.refusal_reasons
        assert decision.gate_version == PERSISTENCE_GATE_VERSION

    def test_insufficient_evidence_creates_nothing_and_is_not_a_failure(self) -> None:
        decision = gate(good_output(decision="INSUFFICIENT_EVIDENCE"))
        assert not decision.persist
        assert "correct and expected outcome" in " ".join(decision.refusal_reasons)

    def test_an_evidence_id_outside_the_packet_is_refused(self) -> None:
        decision = gate(good_output(supporting_evidence_ids=["e1", "e2", "smuggled"]))
        assert not decision.persist
        assert any("not in the packet" in r for r in decision.refusal_reasons)

    def test_a_claim_id_outside_the_packet_is_refused(self) -> None:
        decision = gate(good_output(supporting_claim_ids=["c1", "c2", "c99"]))
        assert not decision.persist
        assert any("Claim ids not in the packet" in r for r in decision.refusal_reasons)

    def test_evidence_cited_without_its_claim_is_refused(self) -> None:
        decision = gate(good_output(supporting_claim_ids=["c1"]))
        assert not decision.persist
        assert any("without its Claim" in r for r in decision.refusal_reasons)

    def test_a_dimension_the_packet_does_not_carry_is_refused(self) -> None:
        decision = gate(good_output(supported_dimensions=["PROBLEM_OR_NEED", "WILLINGNESS_TO_PAY"]))
        assert not decision.persist
        assert any("does not carry" in r for r in decision.refusal_reasons)

    def test_omitting_a_mandatory_unsupported_dimension_is_refused(self) -> None:
        """§6. A dimension nobody mentioned reads as one nobody checked."""
        partial = [d.value for d in MANDATORY_UNSUPPORTED_REPORT][:3]
        decision = gate(good_output(unsupported_dimensions=partial))
        assert not decision.persist
        assert any("requires an explicit unsupported report" in r for r in decision.refusal_reasons)

    def test_claiming_independence_is_refused(self) -> None:
        decision = gate(good_output(independence_status="two independent sources corroborate this"))
        assert not decision.persist
        assert any("independence" in r.lower() for r in decision.refusal_reasons)

    def test_dropping_the_reliability_limitation_is_refused(self) -> None:
        decision = gate(good_output(reliability_status="reliability is fine"))
        assert not decision.persist
        assert any("NON_SCORABLE" in r for r in decision.refusal_reasons)

    def test_every_failure_is_reported_not_only_the_first(self) -> None:
        decision = gate(
            good_output(
                supporting_evidence_ids=["nope"],
                independence_status="independent sources",
                reliability_status="fine",
            )
        )
        assert len(decision.refusal_reasons) >= 3


class TestTheDeterministicAudit:
    """§21. No LLM judges this, and the checks say something the model did not."""

    def test_the_audit_is_versioned(self) -> None:
        assert audit_synthesis(good_output(), packet(), STATEMENTS).audit_version == AUDIT_VERSION

    def test_a_number_nobody_supplied_is_unsupported(self) -> None:
        """The sharpest instrument: scale claims arrive as figures."""
        audit = audit_synthesis(
            good_output(hypothesis_statement="There are 20000000 developers using this."),
            packet(),
            STATEMENTS,
        )
        failed = {f.field_name for f in audit.failed}
        assert "hypothesis_statement" in failed

    def test_a_number_the_statements_supplied_is_fine(self) -> None:
        audit = audit_synthesis(
            good_output(observed_need="88 questions were published."), packet(), STATEMENTS
        )
        assert all(f.field_name != "observed_need" for f in audit.failed)

    def test_model_prior_knowledge_cannot_satisfy_a_dimension(self) -> None:
        """§7. Every one of these is probably true in the world and none was supplied."""
        for sentence in (
            "Kubernetes competes with this subject.",
            "Enterprise users pay for tooling here.",
            "Container security is a major pain point.",
            "This is a popular technology.",
        ):
            audit = audit_synthesis(
                good_output(hypothesis_statement=sentence), packet(), STATEMENTS
            )
            assert any(f.field_name == "hypothesis_statement" for f in audit.failed), sentence

    def test_unsupported_commercial_vocabulary_is_bound_exceeded(self) -> None:
        audit = audit_synthesis(
            good_output(hypothesis_statement="Buyers would pay for this."),
            packet(),
            STATEMENTS,
        )
        failed = [f for f in audit.failed if f.field_name == "hypothesis_statement"]
        assert failed and failed[0].verdict is StatementSupport.BOUND_EXCEEDED

    def test_validation_vocabulary_is_bound_exceeded(self) -> None:
        audit = audit_synthesis(
            good_output(hypothesis_statement="This is a validated opportunity."),
            packet(),
            STATEMENTS,
        )
        assert any(
            f.verdict is StatementSupport.BOUND_EXCEEDED and f.field_name == "hypothesis_statement"
            for f in audit.failed
        )

    def test_an_unknown_actor_is_not_factual_rather_than_unsupported(self) -> None:
        audit = audit_synthesis(good_output(), packet(), STATEMENTS)
        actor = next(f for f in audit.fields if f.field_name == "target_actor_if_supported")
        assert actor.verdict is StatementSupport.NOT_FACTUAL

    def test_an_audit_failure_blocks_persistence(self) -> None:
        decision = gate(good_output(hypothesis_statement="There are 20000000 users."))
        assert not decision.persist
        assert any("audited UNSUPPORTED" in r for r in decision.refusal_reasons)


class TestNothingIsPromotedAndNothingIsScored:
    """§13, §17, §18."""

    def test_no_validated_status_exists(self) -> None:
        values = {s.value for s in OpportunityStatus}
        assert values == {
            "OPPORTUNITY_HYPOTHESIS",
            "HYPOTHESIS_WITHDRAWN",
            "HYPOTHESIS_SUPERSEDED",
        }

    def test_a_formable_packet_is_still_not_scoring_ready(self) -> None:
        result = evaluate(packet())
        assert result.status is HypothesisStatus.HYPOTHESIS_FORMABLE
        assert result.scoring_ready is False
        assert result.scoring_eligible_rows == 0

    def test_the_synthesis_modules_create_no_score_or_rank(self) -> None:
        banned = ("_score", "rank", "weight", "priority", "probability", "percentile")
        for name in ("synthesis.py", "validation.py"):
            tree = ast.parse((PACKAGE_ROOT / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    for bad in banned:
                        assert bad not in node.name.lower(), f"{name}: {node.name}"

    def test_the_parked_classifier_is_unreachable(self) -> None:
        for name in ("synthesis.py", "validation.py"):
            tree = ast.parse((PACKAGE_ROOT / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "semantic_equivalence" not in alias.name
                if isinstance(node, ast.ImportFrom):
                    assert "semantic_equivalence" not in (node.module or "")

    def test_recurrence_may_not_be_claimed_from_a_question_count(self) -> None:
        """§18. The explicit regression boundary: 88 questions is not recurrence."""
        decision = gate(
            good_output(
                supported_dimensions=["PROBLEM_OR_NEED", "RECURRENCE_OR_FREQUENCY"],
                unsupported_dimensions=[
                    d.value
                    for d in MANDATORY_UNSUPPORTED_REPORT
                    if d is not EvidenceDimension.RECURRENCE_OR_FREQUENCY
                ],
            )
        )
        assert not decision.persist
        assert any("does not carry" in r for r in decision.refusal_reasons)


class TestTheTransmittedRepresentationIsUnchanged:
    """§9. Mission 1.29's allowlist is reused and not broadened."""

    def test_the_allowlist_is_the_mission_1_29_one(self) -> None:
        from sros_opportunity import PERMITTED_PAYLOAD_KEYS, TRANSMISSION_REPRESENTATION_VERSION

        assert TRANSMISSION_REPRESENTATION_VERSION == (
            "opportunity-transmission-representation@1.0.0"
        )
        assert (
            frozenset(
                {
                    "packet_id",
                    "subject",
                    "procedures",
                    "source_families",
                    "dimensions",
                    "dimension_bounds",
                    "independence",
                    "claims",
                    "evidence_ids",
                }
            )
            == PERMITTED_PAYLOAD_KEYS
        )

    def test_a_raw_source_record_still_cannot_leave(self) -> None:
        from sros_opportunity import check_representation

        assert check_representation({"packet_id": "p", "raw_record": {"body": "..."}})

    def test_the_synthesis_prompt_carries_no_raw_source_payload(self) -> None:
        parts = render_synthesis_prompt(packet(), STATEMENTS, EVIDENCE_TO_CLAIM)
        blob = parts.system_instructions + parts.trusted_context + parts.task
        blob += " ".join(content for content, _ in parts.untrusted)
        for forbidden in ("<html", "question_id", "owner", "accepted_answer_id", "view_count"):
            assert forbidden not in blob, forbidden


class TestTheRunArtifactIsHonest:
    """§20 and §22, over whatever the committed run recorded."""

    def _artifact(self) -> dict | None:
        path = DOCS / "opportunity-synthesis-run-v1.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def test_the_run_records_at_most_one_initial_call(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("no run artifact yet; the call has not been made")
        assert artifact["logical_calls"] == 1
        assert artifact["schema_retries"] <= 1

    def test_the_run_stayed_under_the_ceiling(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("no run artifact yet")
        assert artifact["cost_units"] <= 0.25
        assert artifact["hard_maximum_cost_units"] <= 0.25

    def test_the_run_records_the_prompt_hash_that_the_code_still_produces(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("no run artifact yet")
        assert artifact["prompt_sha256"] == synthesis_prompt_hash()

    def test_the_run_resolved_authorization_before_serialization(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("no run artifact yet")
        assert artifact["egress"]["availability"] == "AVAILABLE"
        assert artifact["authorization_resolved_before_serialization"] is True


class TestTheGuardCanSeeNegation:
    """guard@1.1.0 / audit@1.1.0, added after Mission 1.31's own run was rejected.

    The defect it fixes: a token scan reading an enumeration of ABSENCES as a set
    of assertions. Version 1.0.0 refused the model's reasoning summary for saying
    that nothing established whether anyone would pay -- which is precisely what
    §6 and §16 asked it to say.

    **The recorded verdict for that run is NOT revised.** §12 forbids weakening a
    gate after seeing the answer, and these tests protect the corrected guard for
    the next mission rather than rescuing this one.
    """

    #: The exact clause the frozen gate refused, from the committed run artifact.
    REJECTED_SENTENCE = (
        "No statement in the packet establishes who these actors are, whether any need "
        "recurred, whether money moved, whether anyone would pay, whether a buyer "
        "exists, whether competitors already serve this space, whether any channel is "
        "reachable, whether any solution gap or dissatisfaction exists, or any "
        "regulatory driver."
    )

    def test_the_sentence_that_was_rejected_now_passes(self) -> None:
        assert not check_statement(self.REJECTED_SENTENCE, frozenset())

    def test_the_same_terms_still_fail_when_asserted(self) -> None:
        for asserted in (
            "Buyers would pay for this.",
            "Competitors already serve this space.",
            "There is market demand for this.",
        ):
            assert check_statement(asserted, frozenset()), asserted

    def test_a_denial_does_not_license_a_later_sentence(self) -> None:
        """The scope is one sentence. A denial cannot cover the next claim."""
        text = "No evidence establishes willingness to pay. Buyers would pay 40 EUR."
        assert check_statement(text, frozenset())

    def test_a_denial_marker_after_the_term_does_not_clear_it(self) -> None:
        """Order matters: a marker scopes what FOLLOWS it."""
        assert check_statement("Buyers would pay, which is not established.", frozenset())

    def test_external_knowledge_markers_are_denial_aware_too(self) -> None:
        from sros_opportunity import audit_synthesis

        cleared = audit_synthesis(
            good_output(
                hypothesis_statement=(
                    "Nothing supplied establishes whether competitors serve this space."
                )
            ),
            packet(),
            STATEMENTS,
        )
        assert all(f.field_name != "hypothesis_statement" for f in cleared.failed)

        flagged = audit_synthesis(
            good_output(hypothesis_statement="Competitors serve this space."),
            packet(),
            STATEMENTS,
        )
        assert any(f.field_name == "hypothesis_statement" for f in flagged.failed)

    def test_the_versions_record_that_this_changed(self) -> None:
        from sros_opportunity.guards import GUARD_VERSION

        assert GUARD_VERSION == "opportunity-claim-guard@1.2.0"
        assert AUDIT_VERSION == "opportunity-synthesis-audit@1.2.0"

    def test_the_committed_run_keeps_its_original_verdict(self) -> None:
        """The artifact records the 1.0.0 decision and is not re-evaluated."""
        path = DOCS / "opportunity-synthesis-run-v1.json"
        if not path.exists():
            pytest.skip("no run artifact")
        artifact = json.loads(path.read_text(encoding="utf-8"))
        assert artifact["persistence"]["audit_version"] == "opportunity-synthesis-audit@1.0.0"
        assert artifact["persistence"]["persist"] is False


class TestMission1311PreCallRequirements:
    """Mission 1.31.1 §1. The five cases that must pass BEFORE the provider is called.

    They are listed in the brief as a precondition, so they are a gate rather
    than a regression suite: if any fails, the call does not happen.

    Running them found that `guard@1.1.0` handled four of the five. The fifth is
    a denial whose marker FOLLOWS its term -- *competitors are not established* --
    because 1.1.0 only cleared a marker that preceded one. `@1.2.0` adds that
    single grammatical form and nothing else.
    """

    #: (text, must_be_flagged). The five from §1, in order.
    REQUIRED = (
        ("No evidence establishes willingness to pay.", False),
        ("No evidence establishes willingness to pay. Buyers would pay 40 EUR.", True),
        ("Competitors are not established by the evidence.", False),
        ("Competitors already serve this market.", True),
        ("Buyers would pay, which is not established.", True),
    )

    def test_the_five_required_cases(self) -> None:
        for text, must_flag in self.REQUIRED:
            flagged = bool(check_statement(text, frozenset()))
            assert flagged is must_flag, text

    def test_a_denial_marker_after_an_assertion_does_not_clear_it(self) -> None:
        """§1 case 5, stated as its own property because it is the one the
        subject-of-its-own-denial form could most easily break."""
        for text in (
            "Buyers would pay, which is not established.",
            "Revenue would follow, but nothing is established.",
            "Competitors serve this space, although that is not evidenced.",
        ):
            assert check_statement(text, frozenset()), text

    def test_a_term_may_be_the_subject_of_its_own_denial(self) -> None:
        for text in (
            "Competitors are not established by the evidence.",
            "Willingness to pay is not established.",
            "Buyers are not identified anywhere in the packet.",
            "Market demand is never established here.",
        ):
            assert not check_statement(text, frozenset()), text

    def test_the_phrase_position_is_the_word_not_the_character_before_it(self) -> None:
        """An off-by-one found by these cases and fixed before the call.

        The pattern captures the character preceding the word so that
        `supermarket` cannot match `market`, which makes `match.start()` point
        one byte early. Every term not at the start of a sentence had its tail
        misaligned, so `market demand is never established` cleared while
        `demand is never established` did not."""
        from sros_opportunity.guards import _phrase_position

        assert _phrase_position("market demand is here", "demand") == 7
        assert _phrase_position("demand is here", "demand") == 0

    def test_the_token_boundary_still_holds(self) -> None:
        """The reason `_phrase_position` looks the way it does at all."""
        assert not check_statement("Supermarkets appear in the corpus.", frozenset())

    def test_the_guard_and_audit_versions_moved_together(self) -> None:
        from sros_opportunity.guards import GUARD_VERSION

        assert GUARD_VERSION == "opportunity-claim-guard@1.2.0"
        assert AUDIT_VERSION == "opportunity-synthesis-audit@1.2.0"

    def test_mission_1_31_keeps_its_historical_verdict(self) -> None:
        """§0. The earlier run is evidence and is not re-evaluated."""
        artifact = json.loads(
            (DOCS / "opportunity-synthesis-run-v1.json").read_text(encoding="utf-8")
        )
        assert artifact["persistence"]["audit_version"] == "opportunity-synthesis-audit@1.0.0"
        assert artifact["persistence"]["persist"] is False
        assert artifact["mission"] == "1.31"


class TestMission1311RunArtifact:
    """§18 and §19, over the re-run's own artifact."""

    def _artifact(self) -> dict | None:
        path = DOCS / "opportunity-synthesis-run-v1.1.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def test_it_is_a_separate_artifact_from_mission_1_31(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("the re-run has not happened yet")
        assert artifact["mission"] == "1.31.1"
        assert (DOCS / "opportunity-synthesis-run-v1.json").exists()

    def test_the_packet_is_the_same_one(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("the re-run has not happened yet")
        historical = json.loads(
            (DOCS / "opportunity-synthesis-run-v1.json").read_text(encoding="utf-8")
        )
        assert artifact["packet_id"] == historical["packet_id"]
        assert artifact["evidence_ids"] == historical["evidence_ids"]
        assert artifact["claim_ids"] == historical["claim_ids"]

    def test_the_semantic_prompt_did_not_change(self) -> None:
        """§2. No prompt tuning: the same hash the code still produces."""
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("the re-run has not happened yet")
        historical = json.loads(
            (DOCS / "opportunity-synthesis-run-v1.json").read_text(encoding="utf-8")
        )
        assert artifact["prompt_sha256"] == synthesis_prompt_hash()
        assert artifact["prompt_sha256"] == historical["prompt_sha256"]

    def test_one_call_and_the_ceiling_held(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("the re-run has not happened yet")
        assert artifact["logical_calls"] == 1
        assert artifact["schema_retries"] <= 1
        assert artifact["cost_units"] <= 0.25
        assert artifact["hard_maximum_cost_units"] <= 0.25

    def test_it_was_audited_by_the_corrected_gate(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("the re-run has not happened yet")
        assert artifact["persistence"]["audit_version"] == "opportunity-synthesis-audit@1.2.0"

    def test_egress_resolved_before_serialization(self) -> None:
        artifact = self._artifact()
        if artifact is None:
            pytest.skip("the re-run has not happened yet")
        assert artifact["egress"]["availability"] == "AVAILABLE"
        assert artifact["authorization_resolved_before_serialization"] is True
