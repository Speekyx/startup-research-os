"""Mission 1.84.23. The generation-surface policy: rendered from first-class objects, proved against the gate.

Everything here runs over the live policy objects and the synthetic fixture packet, against the frozen
gate v1.4.0. Only the last class reads V9's record, to prove that nothing of its answer reached the
policy. Nothing here reaches a network.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import inspect
import json
import pathlib
import re
from typing import Any

import pytest
from sros_opportunity import generation_surface_policy as policy_module
from sros_opportunity.assertion_context import (
    CERTAINTY_MARKERS,
    Disposition,
    Shape,
    SupportCategory,
    is_request_shaped,
)
from sros_opportunity.generation_surface_policy import (
    CANONICAL_REQUEST_HEADS,
    GENERATION_SURFACE_POLICY,
    GENERATION_SURFACE_POLICY_VERSION,
    IMPERATIVE_CONTRASTS,
    SURFACE_RULE_IDS,
    UNRESOLVED_CONSTRUCTIONS,
    class_only_supported_fields,
    render_generation_surface_block,
    request_fields,
    supported_assertion_fields,
    surface_rule_lines,
    surface_tagged_lines,
    unstated_surface_rules,
)
from sros_opportunity.guards import VALIDATION_WORDS
from sros_opportunity.second_opportunity_gate_v1_2 import (
    SECOND_OPPORTUNITY_FIELD_POLICY,
    build_trusted_context,
)
from sros_opportunity.second_opportunity_gate_v1_4 import evaluate_second_opportunity_output_v1_4
from sros_opportunity.semantic_generation_rules import census_by_id

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "infrastructure" / "scripts"
V9_RECORD = ROOT / "docs" / "data" / "second-opportunity-synthesis-execution-record-v9.json"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fx() -> Any:
    return _module(
        "fixtures_for_surface_policy_tests", SCRIPTS / "second_opportunity_synthetic_fixtures.py"
    )


@pytest.fixture(scope="module")
def gate_87() -> Any:
    return _module(
        "gate_87_for_surface_tests", SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"
    )


def _verdict(fx: Any, field: str, value: Any) -> Any:
    packet = fx.packet()
    return evaluate_second_opportunity_output_v1_4(
        fx.good_output(**{field: value}),
        packet,
        dict(fx.statements()),
        {**fx.EVIDENCE_TO_CLAIM, fx.EXTRA_ROW[0]: fx.EXTRA_ROW[1]},
        trusted_context=build_trusted_context(packet),
        source_metadata=fx.metadata(),
    )


class TestTheRenderedObjects:
    def test_the_asserting_fields_are_the_field_policy_s(self):
        expected = [
            fc.field_name
            for fc in SECOND_OPPORTUNITY_FIELD_POLICY
            if fc.disposition is Disposition.SUPPORTED_ASSERTION
        ]
        assert supported_assertion_fields() == expected
        assert "candidate_intervention_class" in expected

    def test_the_class_field_is_asserted_and_names_a_class_only(self):
        assert class_only_supported_fields() == ["candidate_intervention_class"]

    def test_the_request_fields_are_future_evidence_requests_in_request_shape(self):
        policy = {fc.field_name: fc for fc in SECOND_OPPORTUNITY_FIELD_POLICY}
        assert request_fields() == ["recommended_next_evidence"]
        for field in request_fields():
            assert policy[field].disposition is Disposition.FUTURE_EVIDENCE_REQUEST
            assert policy[field].shape is Shape.REQUEST

    def test_every_support_channel_is_worded(self):
        block = render_generation_surface_block()
        for channel in SupportCategory:
            assert " ".join(policy_module.SUPPORT_CHANNEL_WORDING[channel].split()) in " ".join(
                block.split()
            )

    def test_every_rule_is_stated_on_tagged_lines(self):
        stated = set(surface_rule_lines())
        assert set(SURFACE_RULE_IDS) <= stated
        assert stated - set(SURFACE_RULE_IDS) == {policy_module.PROMOTION_RULE_ID}
        promotion = surface_rule_lines()[policy_module.PROMOTION_RULE_ID]
        assert promotion == surface_rule_lines()["NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST"]
        assert all(rules for line, rules in surface_tagged_lines() if line.startswith("  "))

    def test_the_block_is_deterministic_and_carries_no_digit(self):
        block = render_generation_surface_block()
        assert block == render_generation_surface_block()
        assert not re.search(r"\d", block)

    def test_a_dropped_line_leaves_its_rule_unstated(self):
        block = render_generation_surface_block()
        assert unstated_surface_rules(block) == []
        dropped = surface_rule_lines()["NO_IMPERATIVE_FUTURE_EVIDENCE_REQUEST"][0]
        system = "\n".join(line for line in block.split("\n") if line != dropped)
        assert "NO_IMPERATIVE_FUTURE_EVIDENCE_REQUEST" in unstated_surface_rules(system)

    def test_an_unworded_support_channel_is_refused(self, monkeypatch):
        monkeypatch.delitem(
            policy_module.SUPPORT_CHANNEL_WORDING, SupportCategory.SOURCE_STATEMENTS
        )
        with pytest.raises(ValueError, match="no wording for the support channel"):
            render_generation_surface_block()

    def test_a_head_that_is_not_a_noun_and_of_is_refused(self):
        with pytest.raises(ValueError, match="request head"):
            dataclasses.replace(GENERATION_SURFACE_POLICY, request_heads=("Investigate",))

    def test_a_contrast_whose_request_side_is_an_instruction_is_refused(self):
        with pytest.raises(ValueError, match="request side"):
            dataclasses.replace(
                GENERATION_SURFACE_POLICY,
                imperative_contrasts=(("Evidence of whether X", "Investigate whether X"),),
            )

    def test_the_promotion_rule_must_be_a_class_a_rule_on_requests(self):
        internal = next(r for r in census_by_id().values() if r.rule_class == "D")
        with pytest.raises(ValueError, match="class-A rule"):
            dataclasses.replace(GENERATION_SURFACE_POLICY, promotion_rule=internal)

    def test_the_policy_is_versioned(self):
        assert (
            GENERATION_SURFACE_POLICY_VERSION
            == "second-opportunity-generation-surface-policy@1.0.0"
        )
        assert GENERATION_SURFACE_POLICY.version == GENERATION_SURFACE_POLICY_VERSION


class TestEquivalenceWithTheFrozenGate:
    @pytest.mark.parametrize("head", CANONICAL_REQUEST_HEADS)
    @pytest.mark.parametrize("construction", UNRESOLVED_CONSTRUCTIONS)
    def test_every_canonical_form_is_read_as_a_request(self, head, construction):
        assert is_request_shaped(f"{head} {construction} X")

    @pytest.mark.parametrize(("wrong", "right"), IMPERATIVE_CONTRASTS)
    def test_each_contrast_is_read_as_the_policy_says(self, wrong, right):
        assert not is_request_shaped(wrong)
        assert is_request_shaped(right)

    @pytest.mark.parametrize(
        "verb",
        ["Investigate", "Find", "Identify", "Determine", "Obtain", "Check", "Verify", "Observe"],
    )
    def test_an_instruction_is_never_read_as_a_request(self, verb):
        assert not is_request_shaped(f"{verb} whether X")


CASES = (
    (
        "candidate_intervention_class",
        "A comparison of the stated amounts in published notices.",
        None,
    ),
    ("candidate_intervention_class", "Software for buyers.", "audited UNSUPPORTED"),
    (
        "candidate_intervention_class",
        "A class to be tested: a subscription product.",
        "audited UNSUPPORTED",
    ),
    (
        "recommended_next_evidence",
        ["Evidence of whether the same authorities publish comparable notices again."],
        None,
    ),
    (
        "recommended_next_evidence",
        ["Observation of the frequency of such notices across periods."],
        None,
    ),
    (
        "recommended_next_evidence",
        ["Identification of the suppliers associated with these notices."],
        None,
    ),
    (
        "recommended_next_evidence",
        ["Investigate whether the same authorities publish comparable notices again."],
        "it is not request-shaped",
    ),
    (
        "recommended_next_evidence",
        ["Payments under these notices are established."],
        "it is not request-shaped",
    ),
    (
        "recommended_next_evidence",
        ["Evidence of the confirmed payments under these notices."],
        "promote a FUTURE_EVIDENCE_REQUEST to a conclusion",
    ),
)


class TestSyntheticConformance:
    @pytest.mark.parametrize(("field", "value", "reason"), CASES)
    def test_the_frozen_gate_judges_each_case_as_the_policy_says(self, fx, field, value, reason):
        decision = _verdict(fx, field, value)
        reasons = list(decision.refusal_reasons)
        if reason is None:
            assert decision.persist is True and reasons == []
        else:
            assert decision.persist is False
            assert reasons and all(r.startswith(field) and reason in r for r in reasons)

    def test_the_gate_is_the_frozen_one(self, gate_87):
        assert gate_87.implementation_sha256() == gate_87.FROZEN_IMPLEMENTATION_SHA256


class TestNothingOfV9AndNoScannerList:
    def test_the_policy_reads_no_file(self):
        tree = ast.parse(inspect.getsource(policy_module))
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        assert not names & {"open", "read_text", "read_bytes", "load", "loads"}
        strings = [
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
        ]
        assert not [s for s in strings if re.search(r"docs/data|\.json\b|response-v", s)]

    def test_the_policy_imports_no_private_pattern_and_no_gate_list(self):
        tree = ast.parse(inspect.getsource(policy_module))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        assert not [name for name in imported if name.startswith("_")]
        assert not imported & {"CERTAINTY_MARKERS", "VALIDATION_WORDS", "is_request_shaped"}

    def test_the_block_names_no_member_of_a_gate_list(self):
        tokens = set(re.findall(r"[a-z]+", render_generation_surface_block().lower()))
        assert not tokens & (set(CERTAINTY_MARKERS) | set(VALIDATION_WORDS))

    def test_the_quoted_heads_are_exactly_the_canonical_ones(self):
        block = render_generation_surface_block()
        assert re.findall(r'"([A-Z][a-z]+ of) \.\.\."', block) == list(CANONICAL_REQUEST_HEADS)

    def test_no_sentence_of_v9_s_answer_reached_the_block(self):
        record = json.loads(V9_RECORD.read_text(encoding="utf-8"))
        texts = [str(d["text"]) for d in record["SEMANTIC_REFUSAL_DETAILS"]]
        assert len(texts) == 7
        block = render_generation_surface_block()
        source = inspect.getsource(policy_module)

        def shingles(text: str) -> set[str]:
            words = re.findall(r"[a-z0-9]+", text.lower())
            return {" ".join(words[i : i + 6]) for i in range(len(words) - 5)}

        for text in texts:
            assert text not in block and text not in source
            assert not shingles(text) & shingles(block)
