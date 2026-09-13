"""Mission 1.84.12. The census of gate v1.3.0's semantic rules, the block rendered from it, prompt v1.3.0.

Five things this file defends, on synthetic data and never on V3's answer.

THE CENSUS IS COMPLETE. Every refusal site in the two frozen v1.3.0 modules maps to a census rule,
every enforced rule has a site, and every class-A rule is stated somewhere in prompt v1.3.0.

THE BLOCK IS RENDERED FROM FIRST-CLASS OBJECTS. A class-A input moved moves the block; a class-D list
moved leaves it byte-identical, so no phrase list, normalizer or pattern reaches the model.

SOURCE NAMES ARE SHOWN AS NAMES, and every string shown already occurs in the supplied statements.

PROMPT v1.3.0 MOVES NOTHING ELSE. v1.2.0's system region and trusted context are byte-identical
prefixes, and the untrusted statements and the task are v1.2.0's objects.

THE BRIEF'S CASES A TO G. The rule each needs is in the prompt, and the gate's verdict is recorded
honestly, including where a forbidden variant passes because the rule is an instruction only.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import pathlib
import re

import pytest
from sros_opportunity import semantic_generation_rules as sgr
from sros_opportunity.assertion_context import Disposition, ForbiddenConcept
from sros_opportunity.second_opportunity import (
    SECOND_OPPORTUNITY_SYSTEM_V1_2,
    render_second_opportunity_prompt_v1_2,
    second_opportunity_prompt_hash_v1_2,
)
from sros_opportunity.second_opportunity_prompt_v1_3 import (
    SECOND_OPPORTUNITY_SYSTEM_V1_3,
    SEMANTIC_GENERATION_RULES_BLOCK_V1_3,
    render_second_opportunity_prompt_v1_3,
    second_opportunity_prompt_hash_v1_3,
    unstated_semantic_rules_in,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"
MODULE = REPO_ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"
OBSERVED = "OBSERVED_OR_EVIDENCE_SUPPORTED"
HYPOTHESIS = "HYPOTHESIS_TO_VALIDATE"
UNKNOWN = "UNKNOWN_REQUIRES_EVIDENCE"


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fx():
    return _module(
        "synthetic_fixtures_for_rule_tests", SCRIPTS / "second_opportunity_synthetic_fixtures.py"
    )


@pytest.fixture(scope="module")
def gate_79():
    return _module(
        "gate_79_for_rule_tests",
        SCRIPTS / "render_second_opportunity_semantic_prompt_alignment.py",
    )


@pytest.fixture(scope="module")
def parts(fx):
    return render_second_opportunity_prompt_v1_3(
        fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
    )


# ================================================================== the census


class TestTheCensusIsComplete:
    def test_every_rule_has_a_unique_id_and_a_class(self):
        ids = [r.rule_id for r in sgr.SEMANTIC_RULE_CENSUS]
        assert len(ids) == len(set(ids))
        assert {r.rule_class for r in sgr.SEMANTIC_RULE_CENSUS} == {"A", "B", "C", "D"}

    def test_every_refusal_site_is_mapped_and_every_mapped_site_exists(self, gate_79):
        assert gate_79.refusal_sites() == sorted(sgr.REFUSAL_SITE_RULES)

    def test_every_enforced_rule_is_produced_by_a_site(self):
        produced = {rule for ids in sgr.REFUSAL_SITE_RULES.values() for rule in ids}
        for rule in sgr.SEMANTIC_RULE_CENSUS:
            if rule.enforcement == sgr.GATE_ENFORCED:
                assert rule.rule_id in produced, rule.rule_id

    def test_every_site_maps_to_a_census_rule(self):
        known = sgr.census_by_id()
        for ids in sgr.REFUSAL_SITE_RULES.values():
            assert all(rule in known for rule in ids)

    def test_only_a_class_a_rule_v1_2_does_not_state_carries_wording(self):
        for rule in sgr.SEMANTIC_RULE_CENSUS:
            if rule.instruction is not None:
                assert rule.rule_class == "A" and not rule.explicit_in_v1_2
                assert not re.search(r"\d", rule.instruction)

    def test_a_rule_cannot_claim_v1_2_states_it_without_quoting_it(self):
        rule = sgr.SEMANTIC_RULE_CENSUS[0]
        with pytest.raises(ValueError, match="explicit in v1.2.0"):
            dataclasses.replace(rule, v1_2_evidence=None)

    def test_an_enforced_rule_names_the_refusal_it_produces(self):
        rule = next(r for r in sgr.SEMANTIC_RULE_CENSUS if r.enforcement == sgr.GATE_ENFORCED)
        with pytest.raises(ValueError, match="names the refusal"):
            dataclasses.replace(rule, refusal_signature=None)

    def test_class_d_rules_are_mechanisms_and_carry_no_wording(self):
        for rule in sgr.SEMANTIC_RULE_CENSUS:
            if rule.rule_class == "D":
                assert rule.enforcement == sgr.GATE_MECHANISM
                assert rule.instruction is None
                assert rule.rule_id not in sgr.semantic_rule_lines()


# ================================================================== the renderer


class TestTheBlockIsRenderedFromFirstClassObjects:
    def test_rendering_is_deterministic(self):
        assert sgr.render_semantic_generation_rules() == sgr.render_semantic_generation_rules()
        assert sgr.render_semantic_generation_rules() == SEMANTIC_GENERATION_RULES_BLOCK_V1_3

    def test_the_block_carries_no_digit_and_no_pattern(self):
        block = SEMANTIC_GENERATION_RULES_BLOCK_V1_3
        assert not re.search(r"\d", block)
        assert not re.search(r"\\b|\(\?|\[a-z|\\s", block)

    def test_the_renderer_opens_no_file_and_reads_no_answer(self):
        source = (MODULE / "semantic_generation_rules.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {
            node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        }
        assert not names & {"open", "read_text", "read_bytes", "loads", "load"}
        for forbidden in ("parsed_output", "synthesis-response", "execution-record"):
            assert forbidden not in source

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda p: dataclasses.replace(
                p,
                field_policy=tuple(
                    dataclasses.replace(f, disposition=Disposition.HYPOTHESIS_TO_VALIDATE)
                    if f.field_name == "observed_need"
                    else f
                    for f in p.field_policy
                ),
            ),
            lambda p: dataclasses.replace(
                p,
                forbidden_concepts=(
                    *p.forbidden_concepts,
                    ForbiddenConcept("MUTATED_CONCEPT", ("mutated phrase",), "a mutated bound"),
                ),
            ),
            lambda p: dataclasses.replace(
                p,
                disjunction=dataclasses.replace(
                    p.disjunction, connectives=(*p.disjunction.connectives, "nor")
                ),
            ),
            lambda p: dataclasses.replace(
                p,
                metadata_decision={
                    **p.metadata_decision,
                    "metadata_may_not_support": [
                        *p.metadata_decision["metadata_may_not_support"],
                        "a mutated proposition",
                    ],
                },
            ),
            lambda p: dataclasses.replace(
                p,
                census=tuple(
                    dataclasses.replace(r, instruction=r.instruction + " mutated")
                    if r.rule_id == "SUBJECT_IS_THE_PACKET_IDENTITY"
                    else r
                    for r in p.census
                ),
            ),
        ],
        ids=["field_disposition", "concept_added", "connective", "metadata", "instruction"],
    )
    def test_a_class_a_input_moved_moves_the_block(self, mutate):
        policy = sgr.SEMANTIC_GENERATION_POLICY
        assert sgr.render_semantic_generation_rules(mutate(policy)) != (
            sgr.render_semantic_generation_rules(policy)
        )

    def test_a_concept_phrase_moved_leaves_the_block_byte_identical(self):
        policy = sgr.SEMANTIC_GENERATION_POLICY
        mutated = dataclasses.replace(
            policy,
            forbidden_concepts=tuple(
                dataclasses.replace(c, phrases=(*c.phrases, "mutated phrase"))
                for c in policy.forbidden_concepts
            ),
        )
        assert sgr.render_semantic_generation_rules(mutated) == (
            sgr.render_semantic_generation_rules(policy)
        )

    def test_the_gate_s_word_lists_never_reach_the_block(self, monkeypatch):
        from sros_opportunity import assertion_context, guards, second_opportunity

        before = sgr.render_semantic_generation_rules()
        monkeypatch.setattr(
            second_opportunity,
            "PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS",
            ("mutatedmarker",),
        )
        monkeypatch.setattr(guards, "VALIDATION_WORDS", frozenset({"mutated"}))
        monkeypatch.setattr(assertion_context, "CERTAINTY_MARKERS", ("mutatedly",))
        assert sgr.render_semantic_generation_rules() == before

    def test_the_gate_79_drift_check_moves_every_class_a_input_and_no_class_d_list(self, gate_79):
        drift = gate_79.drift()
        assert drift["CLASS_A_MOVED"] == len(drift["CLASS_A_MUTATIONS"]) >= 8
        assert drift["CLASS_D_MOVED"] == 0 and len(drift["CLASS_D_MUTATIONS"]) >= 7

    def test_a_field_pair_nobody_worded_is_refused_not_rendered(self):
        from sros_opportunity.assertion_context import Shape

        policy = sgr.SEMANTIC_GENERATION_POLICY
        mutated = dataclasses.replace(
            policy,
            field_policy=tuple(
                dataclasses.replace(f, shape=Shape.REQUEST)
                if f.field_name == "observed_need"
                else f
                for f in policy.field_policy
            ),
        )
        with pytest.raises(ValueError, match="no wording"):
            sgr.render_semantic_generation_rules(mutated)


# ================================================================== what the block says


class TestTheBlockStatesTheOperatorsRules:
    def test_a_source_name_is_provenance_never_evidence(self):
        block = SEMANTIC_GENERATION_RULES_BLOCK_V1_3
        assert "SOURCE NAMES ARE PROVENANCE, NEVER EVIDENCE." in block
        assert "a domain proposition, through any word inside a label" in block
        assert "a number, through any figure inside a label" in block

    def test_an_observed_statement_is_atomic_and_never_joins_alternatives(self):
        block = " ".join(SEMANTIC_GENERATION_RULES_BLOCK_V1_3.split())
        assert f"classified {OBSERVED} states exactly one proposition" in block
        assert 'never joins alternatives with "or" or "either ... or"' in block
        assert f"classify the joined statement {HYPOTHESIS} or {UNKNOWN}" in block

    def test_the_word_or_is_not_banned_everywhere(self):
        block = " ".join(SEMANTIC_GENERATION_RULES_BLOCK_V1_3.split())
        assert "every other field, may use the word in its ordinary sense" in block

    def test_the_block_names_no_historical_answer_and_no_source(self):
        added = SECOND_OPPORTUNITY_SYSTEM_V1_3[len(SECOND_OPPORTUNITY_SYSTEM_V1_2) :]
        assert "tender" not in added.lower()
        assert re.search(r"\bV3\b", added) is None
        assert "Tenders Electronic Daily" not in SECOND_OPPORTUNITY_SYSTEM_V1_3

    def test_the_system_region_is_the_same_for_every_packet(self, fx, parts):
        other = render_second_opportunity_prompt_v1_3(
            fx.packet(scoring=False),
            fx.statements(name="Other Register (synthetic)"),
            fx.EVIDENCE_TO_CLAIM,
            source_metadata=fx.metadata(name="Other Register (synthetic)"),
        )
        assert other.system_instructions == parts.system_instructions


# ================================================================== source names


class TestSourceNamesAreShownAsNames:
    def test_the_names_shown_are_the_registry_s_and_occur_in_the_statements(self, fx):
        labels = sgr.source_labels_in_statements(fx.packet(), fx.statements(), fx.metadata())
        texts = [label.text for label in labels]
        assert fx.NAME in texts and fx.RESOURCE in texts and fx.SOURCE in texts
        joined = " ".join(fx.statements().values())
        assert all(text in joined for text in texts)

    def test_a_label_not_in_the_statements_is_not_shown(self, fx):
        labels = sgr.source_labels_in_statements(fx.packet(), fx.statements(), fx.metadata())
        assert "Synthetic award notices" not in [label.text for label in labels]

    def test_an_undeclared_source_is_refused_by_name(self, fx):
        with pytest.raises(ValueError, match="no source metadata is declared"):
            sgr.render_source_label_block(
                fx.packet(), fx.statements(), fx.metadata(source="another-source")
            )

    def test_the_section_says_a_name_is_not_a_supplied_fact(self, parts, fx):
        assert "SOURCE NAMES." in parts.trusted_context
        assert "provenance, never evidence" in parts.trusted_context
        assert f'  "{fx.NAME}"' in parts.trusted_context


# ================================================================== prompt v1.3.0


class TestPromptVersion130MovesNothingElse:
    def test_v1_2_regions_are_prefixes_and_the_rest_is_identical(self, fx, parts):
        v1_2 = render_second_opportunity_prompt_v1_2(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM
        )
        assert parts.system_instructions.startswith(v1_2.system_instructions)
        assert parts.trusted_context.startswith(v1_2.trusted_context)
        assert parts.untrusted == v1_2.untrusted
        assert parts.task == v1_2.task
        assert parts.metadata["prompt_version"] == "1.3.0"

    def test_the_digest_moves_with_the_version(self, fx, parts):
        v1_2 = render_second_opportunity_prompt_v1_2(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM
        )
        assert second_opportunity_prompt_hash_v1_3(parts) != second_opportunity_prompt_hash_v1_2(
            v1_2
        )

    def test_the_metadata_channel_is_required(self, fx):
        with pytest.raises(TypeError):
            render_second_opportunity_prompt_v1_3(  # type: ignore[call-arg]
                fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM
            )

    def test_prompt_v1_3_leaves_no_class_a_rule_unstated(self, parts):
        assert unstated_semantic_rules_in(parts) == []

    def test_the_check_refuses_prompt_v1_2(self, fx):
        v1_2 = render_second_opportunity_prompt_v1_2(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM
        )
        missing = sgr.unstated_semantic_rules(
            v1_2.system_instructions, v1_2.trusted_context, v1_2.task
        )
        assert "OBSERVED_DISJUNCTION_FAILS_CLOSED" in missing
        assert "SOURCE_NAME_IS_NOT_A_SUPPLIED_WORD" in missing
        assert "OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED" in missing

    def test_a_rule_dropped_from_the_rendered_block_is_found_unstated(self, parts):
        line = sgr.semantic_rule_lines()["OBSERVED_DISJUNCTION_FAILS_CLOSED"][0]
        system = parts.system_instructions.replace(line, "")
        missing = sgr.unstated_semantic_rules(system, parts.trusted_context, parts.task)
        assert missing == ["OBSERVED_DISJUNCTION_FAILS_CLOSED"]


# ================================================================== the brief's cases


def _named(fx, name):
    return {"supplied": fx.statements(name=name), "names": fx.metadata(name=name)}


class TestTheBriefsCasesAToG:
    def test_a_a_name_containing_a_word_is_not_the_word_observed(self, fx):
        """The gate passes 'Contracts occur.' when 'contracts' is no gated word: the prompt's rule
        is broader than the gate's vocabulary, and the forbidden sentence is an instruction only."""
        plain = _named(fx, "Contracts Weekly (synthetic register)")
        assert fx.gate(fx.with_statement("Contracts occur.", OBSERVED), **plain).persist
        marked = _named(fx, "Supplier Contracts Weekly (synthetic register)")
        refused = fx.gate(fx.with_statement("Supplier contracts occur.", OBSERVED), **marked)
        assert not refused.persist
        assert "SOURCE_METADATA_LABEL_IS_NOT_FACTUAL_SUPPORT" in refused.refusal_reasons[0]

    def test_b_an_atomic_observed_statement_is_allowed(self, fx):
        answer = fx.with_statement("Notices under CPV class 7777 state amounts in EUR.", OBSERVED)
        assert fx.gate(answer).persist

    def test_c_an_observed_disjunction_is_refused(self, fx):
        answer = fx.with_statement(
            "Notices under CPV class 7777 state amounts in EUR or in another currency.", OBSERVED
        )
        decision = fx.gate(answer)
        assert not decision.persist
        assert (
            "DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY"
            in (decision.refusal_reasons[0])
        )

    def test_d_two_statements_are_preferred_and_pass(self, fx):
        answer = fx.good_output()
        answer["statement_classifications"] = [
            *answer["statement_classifications"],
            {
                "statement": "Notices under CPV class 7777 state amounts in EUR.",
                "classification": OBSERVED,
            },
            {
                "statement": "Whether any notice states another currency is unknown.",
                "classification": UNKNOWN,
            },
        ]
        assert fx.gate(answer).persist

    def test_e_incomplete_support_is_a_hypothesis_or_an_unknown(self, fx):
        joined = "Notices under CPV class 7777 state amounts in EUR or in another currency."
        assert fx.gate(fx.with_statement(joined, HYPOTHESIS)).persist
        assert fx.gate(fx.with_statement(joined, UNKNOWN)).persist

    def test_f_a_publishers_name_may_appear_whole(self, fx):
        marked = _named(fx, "Supplier Contracts Weekly (synthetic register)")
        answer = fx.with_statement(
            "Supplier Contracts Weekly reported notices under CPV class 7777.", OBSERVED
        )
        assert fx.gate(answer, **marked).persist

    def test_g_a_forbidden_concept_may_be_unknown_never_observed(self, fx):
        assert not fx.gate(fx.with_statement("Buyers are willing to pay.", OBSERVED)).persist
        assert fx.gate(
            fx.with_statement("Whether buyers are willing to pay is unknown.", UNKNOWN)
        ).persist

    def test_every_case_s_rule_is_in_prompt_v1_3(self, parts):
        rendered = sgr.semantic_rule_lines()
        system = set(parts.system_instructions.split("\n"))
        for rule in (
            "SOURCE_NAME_IS_NOT_A_SUPPLIED_WORD",
            "SOURCE_NAME_LICENSES_ITS_WHOLE_OCCURRENCE",
            "OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED",
            "OBSERVED_DISJUNCTION_FAILS_CLOSED",
        ):
            assert set(rendered[rule]) <= system, rule
