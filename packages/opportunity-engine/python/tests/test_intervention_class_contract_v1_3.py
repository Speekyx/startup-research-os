"""Mission 1.84.27. The intervention-class contract: schema v1.3.0, its grounding, gate v1.6.0, prompt v1.7.0.

Every case here is synthetic: the Mission 1.84.11 fixture packet, its statements and registry names,
and class values written over them. No historical answer is read. What these pin:

* schema v1.3.0 is v1.2.0 with exactly one leaf moved, the class field's description, which states the
  existing sentinel; the strict projection carries it and nothing else moves;
* absence has one representation, the exact sentinel; empty, blank and near-miss values are refused;
* an established class is one short noun phrase of plain words, each taken from the statements of the
  claims the answer cites, never from a source's name, a dimension's name or an uncited claim;
* gate v1.6.0 is gate v1.5.0's verdict, called once, with only structure renamed and the class grounded;
* prompt v1.7.0 states the contract, drops the sentence that forced a class, and documents the one
  instruction it keeps stricter than the gate.
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib
import re

import pytest
from sros_llm_gateway.providers.anthropic_strict import (
    ANTHROPIC_STRICT_TOOL_PROFILE_V1,
    project_strict_input_schema,
)
from sros_opportunity import generation_contract_policy as contract
from sros_opportunity import intervention_class_grounding as grounding
from sros_opportunity import second_opportunity_prompt_v1_6 as prompt_v1_6
from sros_opportunity import second_opportunity_prompt_v1_7 as prompt_v1_7
from sros_opportunity.second_opportunity_gate_v1_5 import (
    COMPONENT_VERSIONS_V1_5,
    evaluate_second_opportunity_output_v1_5,
)
from sros_opportunity.second_opportunity_gate_v1_6 import (
    CHANGED_COMPONENTS,
    CLASS_GROUNDING_REASON_PREFIX,
    COMPONENT_VERSIONS_V1_6,
    OPERATOR_DECISION_V1_6,
    evaluate_second_opportunity_output_v1_6,
)
from sros_opportunity.second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    semantic_schema_diff,
)
from sros_opportunity.second_opportunity_schema_v1_3 import (
    INTERVENTION_CLASS_DESCRIPTION,
    INTERVENTION_CLASS_NOT_ESTABLISHED,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3,
)
from sros_opportunity.synthesis import SynthesisPromptParts

SUITE = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = SUITE / "sros_opportunity"
SENTINEL = INTERVENTION_CLASS_NOT_ESTABLISHED


def _fixture():
    spec = importlib.util.spec_from_file_location(
        "frozen_v1_3_fixture_for_contract_v1_3", SUITE / "tests" / "test_semantic_gate_v1_3.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FX = _fixture()
C0, C1 = FX.CLAIMS
E0, E1 = FX.EVIDENCE


def _output(value: object, claims=(C0, C1), evidence=(E0, E1), **changes: object) -> dict:
    return FX.good_output(
        candidate_intervention_class=value,
        supporting_claim_ids=list(claims),
        supporting_evidence_ids=list(evidence),
        **changes,
    )


def _gates(output: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    arguments = {"trusted_context": FX.TRUSTED, "source_metadata": FX.META}
    old = evaluate_second_opportunity_output_v1_5(
        output, FX.PACKET, FX.STATEMENTS, FX.E2C, **arguments
    ).refusal_reasons
    new = evaluate_second_opportunity_output_v1_6(
        output, FX.PACKET, FX.STATEMENTS, FX.E2C, **arguments
    ).refusal_reasons
    return old, new


def _class_reasons(reasons: tuple[str, ...]) -> list[str]:
    return [r for r in reasons if r.startswith(CLASS_GROUNDING_REASON_PREFIX)]


# ============================================================================= schema


class TestSchemaV13:
    def test_exactly_one_leaf_moves(self) -> None:
        diff = semantic_schema_diff(
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3
        )
        assert [path for path, _, _ in diff] == [
            "properties.candidate_intervention_class.description"
        ]
        assert diff[0][2] == INTERVENTION_CLASS_DESCRIPTION

    def test_the_description_states_the_existing_sentinel(self) -> None:
        assert SENTINEL == "UNKNOWN_NOT_SUPPORTED"
        assert f"the exact string {SENTINEL}" in INTERVENTION_CLASS_DESCRIPTION
        target = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3["properties"]["target_actor_if_supported"]  # type: ignore[index]
        assert SENTINEL in target["description"]

    def test_the_strict_projection_carries_the_description_and_nothing_else_moves(self) -> None:
        old = project_strict_input_schema(
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2, ANTHROPIC_STRICT_TOOL_PROFILE_V1
        )
        new = project_strict_input_schema(
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3, ANTHROPIC_STRICT_TOOL_PROFILE_V1
        )
        assert not old.blockers and not new.blockers
        assert old.schema is not None and new.schema is not None
        diff = semantic_schema_diff(old.schema, new.schema)
        assert [path for path, _, _ in diff] == [
            "properties.candidate_intervention_class.description"
        ]
        assert (old.optional_parameters, old.union_parameters) == (
            new.optional_parameters,
            new.union_parameters,
        )


# ============================================================================= absence


class TestAbsenceHasOneRepresentation:
    def test_the_exact_sentinel_passes_both_gates(self) -> None:
        old, new = _gates(_output(SENTINEL))
        assert old == new == ()

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
            f" {SENTINEL} ",
            SENTINEL.lower(),
            "NOT_ESTABLISHED",
            "NOT ESTABLISHED",
            "None",
            "N/A",
            f"{SENTINEL}: notice review",
            "Unknown - not supported",
        ],
    )
    def test_anything_else_meaning_none_is_refused(self, value: str) -> None:
        old, new = _gates(_output(value))
        assert _class_reasons(new), value
        assert [r for r in new if r not in old] == _class_reasons(new)

    @pytest.mark.parametrize(
        "value",
        ["no intervention class is supported", "not published notices", "no market study"],
    )
    def test_a_denial_is_not_a_class(self, value: str) -> None:
        _, new = _gates(_output(value))
        assert any("deny rather than name" in r for r in _class_reasons(new))


# ============================================================================= grounding


class TestAnEstablishedClassIsGrounded:
    @pytest.mark.parametrize(
        ("value", "claims", "evidence"),
        [
            ("published notices", (C1,), (E1,)),
            ("stated amounts of notices", (C0, C1), (E0, E1)),
            ("notice amounts", (C0, C1), (E0, E1)),
            ("classified notices", (C0, C1), (E0, E1)),
            ("set of notices from the resource", (C0, C1), (E0, E1)),
        ],
    )
    def test_cited_words_are_admitted(self, value, claims, evidence) -> None:
        _, new = _gates(_output(value, claims, evidence))
        assert new == ()

    @pytest.mark.parametrize(
        ("value", "why"),
        [
            ("notice monitoring", "occur in no statement"),
            ("published notices review", "occur in no statement"),
            ("procurement analytics", "occur in no statement"),
            ("register notices", "occur in no statement"),
            ("contract notices", "occur in no statement"),
            ("economic value notices", "occur in no statement"),
            ("marketplace for notices", "occur in no statement"),
            ("market activity", "occur in no statement"),
            ("market activity review", "occur in no statement"),
            ("Market Activity monitoring", "occur in no statement"),
            ("notices exceeded the smallest amount", "state something"),
            ("CPV notices", "are codes"),
            ("of the and", "names nothing"),
            ("stated amounts of notices in the bounded set of the resource", "short category"),
        ],
    )
    def test_uncited_invented_and_dimension_words_are_refused(self, value, why) -> None:
        old, new = _gates(_output(value))
        reasons = _class_reasons(new)
        assert any(why in r for r in reasons), (value, reasons)

    @pytest.mark.parametrize(
        "value",
        [
            "market_activity notices",
            "TOTAL_VALUE",
            "BT-161 notices",
            "notices under CPV class 5555",
            "Márket review",
            "mar​ket notices",
            "mаrket notices",
            "ｍａｒｋｅｔ notices",
            "publishеd notices",
            "SaaS­ platform",
            "published notices review; buyers are willing to pay",
        ],
    )
    def test_characters_outside_plain_words_are_refused(self, value: str) -> None:
        _, new = _gates(_output(value))
        assert any("not one noun phrase in plain words" in r for r in _class_reasons(new)), value

    def test_a_word_only_in_an_uncited_claim_is_refused(self) -> None:
        _, cited = _gates(_output("published notices", (C1,), (E1,)))
        _, uncited = _gates(_output("published notices", (C0,), (E0,)))
        assert cited == ()
        assert any("'published'" in r for r in _class_reasons(uncited))

    def test_a_word_only_in_a_source_name_is_refused(self) -> None:
        assert "register" in FX.NAME.lower()
        assert not re.search(r"\bregister\b", " ".join(grounding_content()))
        _, new = _gates(_output("register notices"))
        assert any("'register'" in r for r in _class_reasons(new))

    def test_no_cited_claim_means_no_established_class(self) -> None:
        _, new = _gates(_output("published notices", (), ()))
        assert any("names none of this packet's claims" in r for r in _class_reasons(new))

    def test_the_grammatical_lists_hold_no_domain_word_and_no_negator(self) -> None:
        assert not grounding.CLASS_FUNCTION_WORDS & grounding.CLASS_NEGATORS
        closed = {
            "a", "an", "the", "of", "for", "in", "on", "to", "with", "by", "from", "at",
            "into", "under", "per", "via", "and", "or",
        }  # fmt: skip
        assert closed == grounding.CLASS_FUNCTION_WORDS

    def test_insufficient_evidence_is_not_held_to_a_class(self) -> None:
        _, new = _gates(_output("", decision="INSUFFICIENT_EVIDENCE"))
        assert not _class_reasons(new)


def grounding_content() -> list[str]:
    from sros_opportunity.support_origin import build_typed_support_universe

    universe = build_typed_support_universe(FX.PACKET, FX.STATEMENTS, FX.TRUSTED, FX.META)
    return [s.content.lower() for s in universe.statements]


# ============================================================================= gate v1.6.0


class TestGateV16:
    def test_components_move_exactly_as_declared(self) -> None:
        moved = {
            k
            for k in set(COMPONENT_VERSIONS_V1_5) | set(COMPONENT_VERSIONS_V1_6)
            if COMPONENT_VERSIONS_V1_5.get(k) != COMPONENT_VERSIONS_V1_6.get(k)
        }
        assert moved == set(CHANGED_COMPONENTS)
        assert "D4_NOT_AUTHORISED" in OPERATOR_DECISION_V1_6

    def test_the_successor_calls_gate_v1_5_0_exactly_once(self) -> None:
        tree = ast.parse((PACKAGE / "second_opportunity_gate_v1_6.py").read_text(encoding="utf-8"))
        calls = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and getattr(n.func, "id", None) == "evaluate_second_opportunity_output_v1_5"
        ]
        assert len(calls) == 1

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("observed_need", "Buyers are willing to pay for software."),
            ("observed_need", "Whether a need or software exists is unknown."),
            ("evidence_bound_reasoning_summary", "The hypothesis is not validated."),
            ("commercial_claims_not_supported", ["Authorities want software platforms."]),
            ("critical_uncertainties", ["Whether a notice analytics service is wanted."]),
            ("recommended_next_evidence", ["Evidence of whether authorities use software."]),
        ],
    )
    def test_every_other_field_reads_exactly_as_under_v1_5_0(self, field, value) -> None:
        old, new = _gates(_output(SENTINEL, **{field: value}))
        assert old == new

    def test_structure_is_named_by_the_successor_schema(self) -> None:
        output = _output(SENTINEL)
        output["unexpected"] = "x"
        old, new = _gates(output)
        assert any(r.startswith("second-opportunity-synthesis-output@1.2.0: ") for r in old)
        assert any(r.startswith("second-opportunity-synthesis-output@1.3.0: ") for r in new)
        assert len(old) == len(new)


# ============================================================================= prompt v1.7.0


class TestPromptV17:
    PARTS = SynthesisPromptParts(
        system_instructions=prompt_v1_7.SECOND_OPPORTUNITY_SYSTEM_V1_7,
        trusted_context="",
        untrusted=(),
        task="",
        metadata={},
    )

    def test_every_contract_constraint_and_rule_is_stated(self) -> None:
        assert prompt_v1_7.unstated_constraints_in(self.PARTS) == []
        assert prompt_v1_7.unstated_headroom_in(self.PARTS) == []
        assert prompt_v1_7.unstated_contract_rules_in(self.PARTS) == []

    def test_prompt_v1_6_0_leaves_the_contract_unstated(self) -> None:
        missing = contract.unstated_contract_rules(prompt_v1_6.SECOND_OPPORTUNITY_SYSTEM_V1_6)
        assert "CLASS_ABSENCE_IS_THE_SENTINEL" in missing
        assert "DENIALS_BELONG_IN_THE_FRAMED_FIELDS" in missing

    def test_the_sentence_that_forced_a_class_is_gone(self) -> None:
        forcing = "name a more neutral class grounded in what they do supply"
        assert forcing in " ".join(prompt_v1_6.SECOND_OPPORTUNITY_SYSTEM_V1_6.split())
        assert forcing not in " ".join(prompt_v1_7.SECOND_OPPORTUNITY_SYSTEM_V1_7.split())

    def test_the_sentinel_and_its_completeness_are_stated(self) -> None:
        flat = " ".join(prompt_v1_7.SECOND_OPPORTUNITY_SYSTEM_V1_7.split())
        assert f"the exact string {SENTINEL}" in flat
        assert "the hypothesis stays valid without a class" in flat

    def test_the_block_carries_no_digit(self) -> None:
        assert not re.search(r"\d", prompt_v1_7.GENERATION_CONTRACT_BLOCK_V1_7)

    def test_the_stricter_instruction_is_documented_as_such(self) -> None:
        by_id = {rule.rule_id: rule for rule in contract.CONTRACT_RULES}
        assert by_id["DENIALS_BELONG_IN_THE_FRAMED_FIELDS"].enforcement == (
            contract.INSTRUCTION_BEYOND_THE_GATE
        )
        assert "stricter than the audit, deliberately" in " ".join(
            prompt_v1_7.GENERATION_CONTRACT_BLOCK_V1_7.split()
        )

    def test_the_prompt_binds_the_successor_contract(self) -> None:
        assert prompt_v1_7.PROMPT_V1_7_OUTPUT_SCHEMA is SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3
        assert prompt_v1_7.PROMPT_V1_7_SEMANTIC_GATE_VERSION == (
            "second-opportunity-output-gate@1.6.0"
        )
        assert prompt_v1_7.SECOND_OPPORTUNITY_PROMPT_VERSION_V1_7 == "1.7.0"

    @pytest.mark.parametrize(
        ("field", "value", "refused"),
        [
            ("observed_need", "Authorities need software.", True),
            ("evidence_bound_reasoning_summary", "The hypothesis is not validated.", True),
            ("commercial_claims_not_supported", ["Authorities want software platforms."], False),
            ("critical_uncertainties", ["Whether authorities want software."], False),
        ],
    )
    def test_what_the_contract_block_says_the_gate_does(self, field, value, refused) -> None:
        _, new = _gates(_output(SENTINEL, **{field: value}))
        assert bool(new) is refused
