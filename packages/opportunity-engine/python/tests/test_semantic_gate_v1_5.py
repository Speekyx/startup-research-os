"""Mission 1.84.26. The semantic output gate v1.5.0: the assertion scope repaired for D1 and D2 only.

Every case here is synthetic: the Mission 1.84.11 fixture packet, its statements and its registry
names, and sentences written over a placeholder subject. No historical answer is read or quoted. What
these pin:

* D1: a noun list governed by one leading `whether` or denial keeps that scope when its last item is
  followed by the sentence's predicate, and a genuinely coordinated proposition with its own subject
  still splits;
* D2: a gated modifier inside an explicitly denied subject noun phrase is not asserted, bounded to that
  noun phrase, and an asserted continuation stays asserted;
* the seam: the successor's reading loop over v1.2.0's own splitter and state reader IS the v1.3.0
  audit's `classify`, so every divergence is attributable to D1 or D2;
* the re-binding: every v1.5.0 audit function is v1.3.0's syntax tree with only its declared renames,
  and every helper it does not re-bind is v1.3.0's object;
* identity: gate v1.5.0's components are v1.4.0's with exactly the assertion-scope chain moved, and
  gate v1.4.0 and everything it is built from are untouched.
"""

from __future__ import annotations

import ast
import pathlib

import pytest
from sros_opportunity import assertion_audit_v1_3 as audit_v1_3
from sros_opportunity import assertion_audit_v1_5 as audit_v1_5
from sros_opportunity import assertion_scope_v1_5 as scope
from sros_opportunity import second_opportunity_gate_v1_3 as gate_v1_3
from sros_opportunity.assertion_context import OccurrenceState
from sros_opportunity.second_opportunity_gate_v1_4 import (
    COMPONENT_VERSIONS_V1_4,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
    evaluate_second_opportunity_output_v1_4,
)
from sros_opportunity.second_opportunity_gate_v1_5 import (
    CHANGED_COMPONENTS,
    COMPONENT_VERSIONS_V1_5,
    OPERATOR_DECISION_V1_5,
    PREDECESSOR_GATE_VERSION,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_5,
    evaluate_second_opportunity_output_v1_5,
)

SUITE = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = SUITE / "sros_opportunity"


def _fixture():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "frozen_v1_3_fixture_for_v1_5", SUITE / "tests" / "test_semantic_gate_v1_3.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FX = _fixture()


def asserted(text: str, phrase: str) -> bool:
    return scope.is_asserted(text, phrase)


def asserted_before(text: str, phrase: str) -> bool:
    return audit_v1_3.is_asserted(text, phrase)


def verdicts(field: str, value: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
    output = FX.good_output(**{field: value})
    arguments = {"trusted_context": FX.TRUSTED, "source_metadata": FX.META}
    old = evaluate_second_opportunity_output_v1_4(
        output, FX.PACKET, FX.STATEMENTS, FX.E2C, **arguments
    )
    new = evaluate_second_opportunity_output_v1_5(
        output, FX.PACKET, FX.STATEMENTS, FX.E2C, **arguments
    )
    return old.refusal_reasons, new.refusal_reasons


# ============================================================================= D1


class TestD1AScopedListKeepsItsScope:
    @pytest.mark.parametrize(
        "text",
        [
            "Whether a need or software exists is unknown.",
            "Whether a need, a problem, or software exists is unknown.",
            "Whether a need, a problem or software exists is unknown.",
            "Whether a need and software exist is unknown.",
            "Whether this reflects a need, problem, or software gap is not established.",
            "Whether this reflects a need, problem or software gap is not established.",
            "Whether this reflects a need or software gap is not established.",
            "Whether this reflects a need, problem, or software gap is unknown.",
            "It is unknown whether a need, a problem, or software exists.",
            "No need, problem, or software gap is established.",
            "No need or software exists.",
            "None of the need, the problem, or the software gap is established.",
            "The packet does not show that a need or software exists.",
            "None of the notices show that a need, problem, or software gap exists.",
        ],
    )
    def test_the_last_item_stays_under_the_scope(self, text: str) -> None:
        assert asserted_before(text, "software"), "v1.4.0 over-refused this, which D1 repairs"
        assert not asserted(text, "software")

    @pytest.mark.parametrize(
        "text",
        [
            "No evidence establishes a need, problem, or software gap.",
            "It is not established whether this reflects a need, problem, or software gap.",
            "Neither a need nor software exists.",
        ],
    )
    def test_what_was_already_one_scope_stays_one_scope(self, text: str) -> None:
        assert not asserted_before(text, "software")
        assert not asserted(text, "software")

    @pytest.mark.parametrize(
        ("text", "phrase"),
        [
            ("No evidence establishes software demand, and buyers are willing to pay.", "buyers"),
            ("No statement establishes a need, and buyers are willing to pay.", "willing to pay"),
            ("No evidence establishes demand and buyers are willing to pay.", "willing to pay"),
            ("No evidence establishes demand, a need, and buyers are willing to pay.", "buyers"),
            ("No evidence establishes a need, and the market is large.", "market"),
            ("No evidence establishes a need, and software demand exists.", "software"),
            (
                "No evidence establishes a need, and they are willing to pay for software.",
                "software",
            ),
            ("Whether a need exists is unknown, and software demand exists.", "software"),
            ("It is unknown whether a need exists, and software is sold widely.", "software"),
            ("No need, no gap, and buyers are willing to pay.", "buyers"),
            ("No need, people spend, and software exists.", "software"),
            ("There is no need, and software demand exists.", "software"),
            ("Nothing establishes a need, and software exists.", "software"),
            ("No vendors bid or buyers are willing to pay.", "willing to pay"),
            ("No staff bid or buyers are willing to pay.", "willing to pay"),
            ("Whether a need exists or software is sold is unknown.", "software"),
            ("Whether buyers need a tool or software is sold is unknown.", "software"),
        ],
    )
    def test_a_coordinated_proposition_with_its_own_subject_still_splits(
        self, text: str, phrase: str
    ) -> None:
        assert asserted_before(text, phrase)
        assert asserted(text, phrase)

    @pytest.mark.parametrize(
        "text",
        [
            "A need or software exists.",
            "A need, a problem, or software exists.",
            "Buyers want this, and software demand exists.",
            "A need exists, and software demand is large.",
        ],
    )
    def test_a_list_under_no_scope_is_asserted(self, text: str) -> None:
        assert asserted(text, "software")

    def test_the_genuine_clause_is_its_own_clause(self) -> None:
        text = "No evidence establishes software demand, and buyers are willing to pay."
        assert [c.boundary for c in scope.scoped_clauses(text)] == ["start", "coord"]

    def test_the_scoped_list_is_one_clause(self) -> None:
        text = "Whether a need or software exists is unknown."
        assert [(c.boundary, c.text) for c in scope.scoped_clauses(text)] == [
            ("start", "whether a need or software exists is unknown.")
        ]

    def test_a_sentence_with_no_scope_anchor_splits_exactly_as_v1_2_0(self) -> None:
        for text in (
            "Buyers pay, and vendors sell software.",
            "A need exists; software demand is large.",
            "The notices differ, but buyers are willing to pay.",
            "Demand is visible, and it is large.",
        ):
            assert scope.scoped_clauses(text) == scope.clauses_v1_2(text)


# ============================================================================= D2


class TestD2AModifierInsideADeniedSubjectIsNotAsserted:
    @pytest.mark.parametrize(
        ("text", "phrase"),
        [
            ("Software gap is not established.", "software"),
            ("Market gap is not established.", "market"),
            ("Underserved segment is not established.", "underserved"),
            ("Software gaps are not established.", "software"),
            ("Software gap is not established by these statements.", "software"),
            ("Software gap remains unknown.", "software"),
            ("Software gap has not been established.", "software"),
            ("A software gap does not exist.", "software"),
            ("The market gap cannot be shown.", "market"),
            ("Competitor weakness is not established.", "competitor"),
        ],
    )
    def test_the_modifier_is_denied_with_its_subject(self, text: str, phrase: str) -> None:
        assert asserted_before(text, phrase), "v1.4.0 left this UNDETERMINED and refused it"
        assert not asserted(text, phrase)
        states = {o.state for o in scope.classify(text, phrase)}
        assert states == {OccurrenceState.DENIED}

    @pytest.mark.parametrize(
        ("text", "phrase"),
        [
            ("Software gap is not established, but software demand probably exists.", "software"),
            ("No evidence establishes software demand, but buyers are willing to pay.", "buyers"),
            ("Software gap is not established, but the market clearly needs a solution.", "market"),
            ("A software gap is not established, but it probably exists.", "software"),
            ("Software gap is not established and is probably large.", "software"),
            ("Software gap is not established; software is widely used.", "software"),
            ("Software gap is not established, it exists.", "software"),
            ("Software gap is not established, and they are probably large.", "software"),
            ("Software gap is not established; it is large.", "software"),
        ],
    )
    def test_an_asserted_continuation_stays_asserted(self, text: str, phrase: str) -> None:
        assert asserted(text, phrase)

    @pytest.mark.parametrize(
        "text",
        [
            "Software gap is not established, and it is not measured.",
            "Software gap is not established; it remains unknown.",
            "Software gap is not established, but this requires evidence.",
        ],
    )
    def test_a_continuation_that_denies_again_or_asks_for_evidence_keeps_the_denial(
        self, text: str
    ) -> None:
        assert not asserted(text, "software")

    @pytest.mark.parametrize(
        ("text", "phrase"),
        [
            ("Software gap is established.", "software"),
            ("Software gap is not large.", "software"),
            ("Software buyers have no budget.", "software"),
            ("Software buyers do not pay.", "software"),
            ("Software vendors are not responsive.", "software"),
            ("A software gap that buyers report is not established.", "software"),
            ("The software gap and the market are not established.", "software"),
            ("Evidence of software demand is not established.", "software"),
            ("Software market gap is not established.", "software"),
            ("Buyers say software gap is not established.", "software"),
            ("Software gap analysis shows nothing and is not established.", "software"),
        ],
    )
    def test_the_rule_reads_one_denied_subject_and_nothing_else(
        self, text: str, phrase: str
    ) -> None:
        """Not a later `not`: a subject that exists, two modifiers, a relative clause, a coordinated
        subject, a preposition or a clause before the subject leaves the reading as v1.2.0's."""
        assert asserted(text, phrase)

    def test_the_rule_only_moves_an_asserted_reading(self) -> None:
        text = "No software gap is established."
        before = [o.state for o in audit_v1_3.classify(text, "software")]
        after = [o.state for o in scope.classify(text, "software")]
        assert before == after == [OccurrenceState.DENIED]


# ============================================================================= the seam


class TestTheSeamIsTheV13Reading:
    CORPUS = (
        "Whether a need or software exists is unknown.",
        "Software gap is not established, but software demand probably exists.",
        "No evidence establishes software demand, and buyers are willing to pay.",
        "The notices show market activity, and buyers are willing to pay.",
        "Evidence of payments actually made would be required.",
        "Whether any authority publishes such notices again.",
        "Both rows are SCORABLE; no score exists.",
    )

    @pytest.mark.parametrize("text", CORPUS)
    @pytest.mark.parametrize("phrase", ["software", "buyers", "willing to pay", "score", "market"])
    @pytest.mark.parametrize("scoped_head", [False, True])
    def test_v1_2_0_functions_through_the_seam_are_v1_3_0_classify(
        self, text: str, phrase: str, scoped_head: bool
    ) -> None:
        seam = scope.read_occurrences(
            text,
            phrase,
            splitter=scope.clauses_v1_2,
            state_reader=scope.state_v1_2,
            scoped_head=scoped_head,
        )
        assert seam == audit_v1_3.classify(text, phrase, scoped_head=scoped_head)

    def test_verbatim_spans_are_honoured(self) -> None:
        text = "The packet supports nothing here."
        assert scope.classify(text, "supports", verbatim=True) == audit_v1_3.classify(
            text, "supports", verbatim=True
        )


# ============================================================================= re-binding


def _functions(path: pathlib.Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


class _Rename(ast.NodeTransformer):
    def __init__(self, names: dict[str, str]) -> None:
        self.names = names

    def visit_Name(self, node: ast.Name) -> ast.Name:
        node.id = self.names.get(node.id, node.id)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.name = self.names.get(node.name, node.name)
        self.generic_visit(node)
        return node


def _without_docstring(node: ast.FunctionDef) -> ast.FunctionDef:
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        node.body = body[1:]
    return node


class TestTheAuditIsReBoundNotRewritten:
    def test_every_rebound_function_is_v1_3_0_with_only_its_renames(self) -> None:
        old = _functions(PACKAGE / "assertion_audit_v1_3.py")
        new = _functions(PACKAGE / "assertion_audit_v1_5.py")
        assert list(new) == list(audit_v1_5.REBOUND_FUNCTIONS.values())
        for old_name, new_name in audit_v1_5.REBOUND_FUNCTIONS.items():
            renamed = _Rename(audit_v1_5.REBOUND_NAMES).visit(old[old_name])
            assert ast.dump(renamed) == ast.dump(new[new_name]), old_name

    def test_what_is_not_rebound_is_v1_3_0_s_own_object(self) -> None:
        for name in ("maskable_labels", "disjunctive_connectives", "_mask_identifiers", "_form"):
            assert getattr(audit_v1_5, name) is getattr(audit_v1_3, name), name

    def test_the_audit_reads_through_the_successor_scope(self) -> None:
        assert audit_v1_5.classify is scope.classify
        assert audit_v1_5.is_asserted is scope.is_asserted

    def test_the_gate_is_v1_3_0_s_evaluator_with_only_its_renames(self) -> None:
        old = _without_docstring(
            _functions(PACKAGE / "second_opportunity_gate_v1_3.py")[
                "evaluate_second_opportunity_output_v1_3"
            ]
        )
        new = _without_docstring(
            _functions(PACKAGE / "second_opportunity_gate_v1_5.py")[
                "evaluate_second_opportunity_output_v1_5"
            ]
        )
        renames = {
            "evaluate_second_opportunity_output_v1_3": "evaluate_second_opportunity_output_v1_5",
            "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1": (
                "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2"
            ),
            "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1": "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2",
            "evaluate_persistence_v1_3": "evaluate_persistence_v1_4",
            "SECOND_OPPORTUNITY_GATE_VERSION_V1_3": "SECOND_OPPORTUNITY_GATE_VERSION_V1_5",
        }
        assert ast.dump(_Rename(renames).visit(old)) == ast.dump(new)
        assert gate_v1_3.evaluate_second_opportunity_output_v1_3.__name__.endswith("v1_3")


# ============================================================================= identity


class TestIdentity:
    def test_a_new_gate_version_after_v1_4_0(self) -> None:
        assert SECOND_OPPORTUNITY_GATE_VERSION_V1_5 == "second-opportunity-output-gate@1.5.0"
        assert PREDECESSOR_GATE_VERSION == SECOND_OPPORTUNITY_GATE_VERSION_V1_4

    def test_components_move_exactly_along_the_assertion_scope_chain(self) -> None:
        moved = {
            k
            for k in set(COMPONENT_VERSIONS_V1_4) | set(COMPONENT_VERSIONS_V1_5)
            if COMPONENT_VERSIONS_V1_4.get(k) != COMPONENT_VERSIONS_V1_5.get(k)
        }
        assert moved == set(CHANGED_COMPONENTS)
        assert COMPONENT_VERSIONS_V1_5["output_schema"] == COMPONENT_VERSIONS_V1_4["output_schema"]
        assert COMPONENT_VERSIONS_V1_5["assertion_scope"] == scope.ASSERTION_SCOPE_POLICY_VERSION

    def test_the_decision_is_d1_and_d2_only(self) -> None:
        assert any(line.startswith("D1_") for line in OPERATOR_DECISION_V1_5)
        assert any(line.startswith("D2_") for line in OPERATOR_DECISION_V1_5)
        assert "D3_D4_D5_NOT_IMPLEMENTED" in OPERATOR_DECISION_V1_5


# ============================================================================= the gates


class TestTheGates:
    def test_the_fixture_answer_passes_both(self) -> None:
        old, new = verdicts("observed_need", FX.good_output()["observed_need"])
        assert old == new == ()

    @pytest.mark.parametrize(
        "text",
        [
            "Whether a need or software exists is unknown.",
            "Software gap is not established.",
        ],
    )
    def test_a_repaired_over_refusal_passes_v1_5_0_only(self, text: str) -> None:
        old, new = verdicts("observed_need", text)
        assert old and new == ()

    @pytest.mark.parametrize(
        "text",
        [
            "Buyers are willing to pay for software.",
            "No evidence establishes software demand, and buyers are willing to pay.",
            "Software gap is not established, but software demand probably exists.",
        ],
    )
    def test_a_genuine_assertion_fails_both_with_the_same_reasons(self, text: str) -> None:
        old, new = verdicts("observed_need", text)
        assert old and old == new

    def test_a_denied_subject_followed_by_an_asserted_continuation_still_fails_on_it(self) -> None:
        old, new = verdicts(
            "observed_need",
            "Software gap is not established, but the market clearly needs a solution.",
        )
        assert old and new
        assert "'software'" in old[0] and "'software'" not in new[0]
        assert "'market' appears in no source content statement" in new[0]

    def test_a_list_the_uncertainty_field_frames_keeps_its_frame(self) -> None:
        text = "Whether a need or dissatisfaction exists is unknown."
        old, new = verdicts("critical_uncertainties", [text])
        assert old and new == ()

    def test_the_market_word_is_still_refused_in_the_class(self) -> None:
        old, new = verdicts(
            "candidate_intervention_class", "An evidence-gathering or market-observation exercise."
        )
        assert old == new
        assert any("'market' appears in no source content statement" in r for r in new)
