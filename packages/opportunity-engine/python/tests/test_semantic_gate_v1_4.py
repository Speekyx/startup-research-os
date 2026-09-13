"""Mission 1.84.17. The semantic output gate v1.4.0: gate v1.3.0's semantics, structure read against v1.2.0.

Every case here is synthetic: the Mission 1.84.12 fixture packet, its statements and its registry
names, the census fixtures CI gate 79 proves, and summaries built from the fixture's own words or
from one repeated letter. No historical answer is read, replayed or quoted. What these pin:

* identity: a new gate version whose components are v1.3.0's with the gate and the output schema
  moved, and nothing else (brief section 7);
* gate v1.3.0 untouched, still its own freeze (section 6);
* the common domain: wherever the summary is within v1.1.0's bound, the two verdicts are equal (8);
* the band: v1.3.0 refuses only on the old bound, v1.4.0 does not produce it, and a semantic
  violation still fails there (9);
* above: v1.4.0 fails naming schema v1.2.0 and its bound (10);
* the matrix: gate v1.3.0's own frozen test file, replayed through both gates, diverges nowhere (11);
* fail closed: a predecessor that stops writing its structural reasons first is refused, not stripped.

An evaluation costs most of a second, so the corpus is evaluated once, by the gate's own function,
and every test below reads that one evaluation.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import pathlib
from typing import Any

import pytest
from sros_opportunity import second_opportunity_gate_v1_4 as successor_module
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
from sros_opportunity.second_opportunity_gate_v1_3 import (
    COMPONENT_VERSIONS_V1_3,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
)
from sros_opportunity.second_opportunity_gate_v1_4 import (
    COMPONENT_VERSIONS_V1_4,
    OPERATOR_DECISION_V1_4,
    PREDECESSOR_GATE_VERSION,
    PREDECESSOR_STRUCTURAL_REASON_PREFIX,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
    STRUCTURAL_REASON_PREFIX,
    PredecessorShapeError,
    evaluate_second_opportunity_output_v1_4,
)
from sros_opportunity.second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
)
from sros_opportunity.validation import PersistenceDecision

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"
SUITE = REPO_ROOT / "packages" / "opportunity-engine" / "python"
SUMMARY = "evidence_bound_reasoning_summary"
V1_3_TESTS = SUITE / "tests" / "test_semantic_gate_v1_3.py"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _module(
    "gate_87_for_v1_4_tests", SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"
)
FX = GATE.fixtures()
DIFF = GATE.differential()
OLD, NEW = DIFF.bounds()
CASE_IDS = [case[0] for case in GATE.corpus(FX)]
BASE = str(FX.good_output()[SUMMARY])
#: A sentence the semantic gate refuses whatever the summary's length: no statement supplies it.
VIOLATION = " Buyers are willing to pay."


def both(output: dict[str, Any]) -> tuple[Any, Any]:
    return GATE.verdicts(FX, output, {})


def repeated(times: int) -> str:
    return " ".join([BASE] * times)


BAND_REPETITIONS = [k for k in range(1, 20) if OLD < len(repeated(k)) <= NEW]


@pytest.fixture(scope="module")
def evaluated() -> dict[str, tuple[Any, dict[str, Any], Any, Any]]:
    return {row[0][0]: row for row in GATE.evaluate_corpus(FX)}


class TestIdentity:
    def test_a_new_gate_version_beside_the_old_one(self) -> None:
        assert SECOND_OPPORTUNITY_GATE_VERSION_V1_4 == "second-opportunity-output-gate@1.4.0"
        assert PREDECESSOR_GATE_VERSION == SECOND_OPPORTUNITY_GATE_VERSION_V1_3
        assert SECOND_OPPORTUNITY_GATE_VERSION_V1_4 != SECOND_OPPORTUNITY_GATE_VERSION_V1_3

    def test_only_the_gate_and_the_output_schema_move(self) -> None:
        moved = {
            k
            for k in COMPONENT_VERSIONS_V1_3.keys() | COMPONENT_VERSIONS_V1_4.keys()
            if COMPONENT_VERSIONS_V1_3.get(k) != COMPONENT_VERSIONS_V1_4.get(k)
        }
        assert moved == {"gate", "output_schema"}
        assert COMPONENT_VERSIONS_V1_4["gate"] == SECOND_OPPORTUNITY_GATE_VERSION_V1_4
        schema = COMPONENT_VERSIONS_V1_4["output_schema"]
        assert schema == SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2

    def test_the_operator_decision_is_carried_as_given(self) -> None:
        assert tuple(OPERATOR_DECISION_V1_4) == GATE.REQUIRED_DECISION
        assert "DO_NOT_REVERT_TO_OUTPUT_SCHEMA_V1_1_0" in OPERATOR_DECISION_V1_4

    def test_the_two_bounds_are_the_schemas_own(self) -> None:
        assert SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][SUMMARY]["maxLength"] == OLD
        assert SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["properties"][SUMMARY]["maxLength"] == NEW
        assert OLD < NEW

    def test_the_structural_prefixes_name_the_two_schemas(self) -> None:
        assert f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2}: " == STRUCTURAL_REASON_PREFIX
        old = "second-opportunity-synthesis-output@1.1.0"
        assert PREDECESSOR_STRUCTURAL_REASON_PREFIX.startswith(old)

    def test_both_channels_stay_required_with_no_default(self) -> None:
        parameters = inspect.signature(evaluate_second_opportunity_output_v1_4).parameters
        for name in ("trusted_context", "source_metadata"):
            assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            assert parameters[name].default is inspect.Parameter.empty

    def test_the_module_carries_no_length_of_its_own(self) -> None:
        tree = ast.parse(inspect.getsource(successor_module))
        numbers = [
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, int)
            and not isinstance(n.value, bool)
        ]
        assert numbers == []

    def test_it_calls_gate_v1_3_once_and_reimplements_nothing(self) -> None:
        tree = ast.parse(inspect.getsource(successor_module))
        calls = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and getattr(n.func, "id", None) == "evaluate_second_opportunity_output_v1_3"
        ]
        functions = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        assert len(calls) == 1
        assert functions == ["evaluate_second_opportunity_output_v1_4"]


class TestGateV13IsUntouched:
    def test_its_freeze_still_validates_with_the_same_digest(self) -> None:
        block = GATE.predecessor_block()
        assert block["implementation_sha256"] == GATE.PREDECESSOR_IMPLEMENTATION_SHA256
        assert block["test_sha256"] == GATE.PREDECESSOR_TEST_SHA256
        assert block["still_validates"] is True


class TestTheCorpus:
    @pytest.mark.parametrize("case_id", CASE_IDS)
    def test_no_case_diverges(self, case_id: str, evaluated: dict[str, Any]) -> None:
        _case, record, _old, _new = evaluated[case_id]
        assert not DIFF.divergent(record), record

    def test_it_reaches_all_three_domains(self, evaluated: dict[str, Any]) -> None:
        domains = {row[1]["domain"] for row in evaluated.values()}
        assert {"COMMON", "BAND", "ABOVE"} <= domains

    def test_every_census_fixture_is_in_it(self) -> None:
        census = [c for c in CASE_IDS if c.startswith("census:")]
        assert len(census) == len(GATE.gate_79().corpus(FX))

    def test_within_the_old_bound_the_verdicts_are_equal_to_the_letter(
        self, evaluated: dict[str, Any]
    ) -> None:
        for _case, record, old, new in evaluated.values():
            if record["domain"] != "COMMON":
                continue
            before = [
                r.removeprefix(PREDECESSOR_STRUCTURAL_REASON_PREFIX) for r in old.refusal_reasons
            ]
            after = [r.removeprefix(STRUCTURAL_REASON_PREFIX) for r in new.refusal_reasons]
            assert after == before
            assert new.persist is old.persist

    def test_no_v1_4_verdict_carries_the_old_bound_or_the_old_schema(
        self, evaluated: dict[str, Any]
    ) -> None:
        for _case, _record, _old, new in evaluated.values():
            for reason in new.refusal_reasons:
                assert not reason.startswith(PREDECESSOR_STRUCTURAL_REASON_PREFIX)
                assert not (SUMMARY in reason and reason.endswith(f"maxLength {OLD}"))


class TestBand:
    @pytest.mark.parametrize("length", [OLD + 1, (OLD + NEW) // 2, NEW])
    def test_a_long_summary_within_the_new_bound_passes_v1_4_only(self, length: int) -> None:
        old, new = both(FX.good_output(**{SUMMARY: "y" * length}))
        assert list(old.refusal_reasons) == [
            f"{PREDECESSOR_STRUCTURAL_REASON_PREFIX}{SUMMARY}: {length} characters exceeds "
            f"maxLength {OLD}"
        ]
        assert new.persist is True and new.refusal_reasons == ()

    @pytest.mark.parametrize("times", BAND_REPETITIONS)
    def test_the_fixtures_own_words_repeated_pass_v1_4(self, times: int) -> None:
        old, new = both(FX.good_output(**{SUMMARY: repeated(times)}))
        assert len(old.refusal_reasons) == 1 and old.persist is False
        assert new.persist is True

    @pytest.mark.parametrize("times", BAND_REPETITIONS)
    def test_a_semantic_violation_in_the_band_still_fails(self, times: int) -> None:
        old, new = both(FX.good_output(**{SUMMARY: repeated(times) + VIOLATION}))
        assert new.persist is False and new.refusal_reasons
        assert not any(r.startswith(STRUCTURAL_REASON_PREFIX) for r in new.refusal_reasons)
        assert list(new.refusal_reasons) == list(old.refusal_reasons[1:])
        assert "WILLINGNESS_TO_PAY" in " ".join(new.refusal_reasons)

    def test_another_structural_violation_in_the_band_is_still_reported(self) -> None:
        output = FX.good_output(
            **{SUMMARY: repeated(BAND_REPETITIONS[0]), "confidence_classification": "HIGH"}
        )
        _old, new = both(output)
        structural = [r for r in new.refusal_reasons if r.startswith(STRUCTURAL_REASON_PREFIX)]
        assert any("confidence_classification" in r for r in structural)
        assert not any(SUMMARY in r for r in structural)

    def test_the_band_is_not_empty(self) -> None:
        assert BAND_REPETITIONS


class TestAbove:
    def test_one_over_the_new_bound_fails_naming_schema_v1_2(self) -> None:
        _old, new = both(FX.good_output(**{SUMMARY: "y" * (NEW + 1)}))
        assert list(new.refusal_reasons) == [
            f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2}: {SUMMARY}: {NEW + 1} characters "
            f"exceeds maxLength {NEW}"
        ]
        assert new.persist is False

    def test_above_the_bound_a_semantic_violation_is_reported_too(self) -> None:
        times = next(k for k in range(1, 40) if len(repeated(k)) > NEW)
        old, new = both(FX.good_output(**{SUMMARY: repeated(times) + VIOLATION}))
        assert new.refusal_reasons[0].startswith(STRUCTURAL_REASON_PREFIX)
        assert new.refusal_reasons[0].endswith(f"maxLength {NEW}")
        assert list(new.refusal_reasons[1:]) == list(old.refusal_reasons[1:])


class TestFailClosed:
    def test_a_predecessor_that_reorders_its_reasons_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real = successor_module.evaluate_second_opportunity_output_v1_3

        def reordered(*args: Any, **kwargs: Any) -> PersistenceDecision:
            decision = real(*args, **kwargs)
            return PersistenceDecision(
                persist=decision.persist,
                gate_version=decision.gate_version,
                refusal_reasons=tuple(reversed(decision.refusal_reasons)),
                audit=decision.audit,
                notes=decision.notes,
            )

        monkeypatch.setattr(successor_module, "evaluate_second_opportunity_output_v1_3", reordered)
        output = FX.good_output(**{SUMMARY: "y" * (NEW + 1), "confidence_classification": "HIGH"})
        args, kwargs = GATE._arguments(FX, output, {})
        with pytest.raises(PredecessorShapeError):
            evaluate_second_opportunity_output_v1_4(*args, **kwargs)


@pytest.fixture(scope="module")
def replay() -> dict[str, Any]:
    return DIFF.replay_matrix(V1_3_TESTS, SUITE)


class TestTheV13MatrixThroughBothGates:
    def test_every_v1_3_test_still_passes(self, replay: dict[str, Any]) -> None:
        assert replay["returncode"] == 0 and replay["exitstatus"] == 0
        assert replay["tests"]["failed"] == 0 and replay["tests"]["passed"] > 0

    def test_the_spy_replaced_every_reference(self, replay: dict[str, Any]) -> None:
        assert "tests.test_semantic_gate_v1_3" in replay["patched_modules"]
        assert "sros_opportunity.second_opportunity_gate_v1_3" in replay["patched_modules"]

    def test_the_two_gates_diverge_nowhere(self, replay: dict[str, Any]) -> None:
        summary = replay["summary"]
        assert summary["EVALUATOR_CALLS"] > 0
        assert replay["tests_reaching_the_evaluator"] > 0
        assert summary["DIVERGENCES"] == 0
        assert summary["NON_STRUCTURAL_SEMANTIC_DIVERGENCES"] == 0
        assert summary["COMMON_DOMAIN_SEMANTIC_DIVERGENCES"] == 0
