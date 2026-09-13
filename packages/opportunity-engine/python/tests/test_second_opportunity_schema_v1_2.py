"""Mission 1.84.16: output schema v1.2.0 is v1.1.0 with one bound moved, and nothing else.

Every length check here runs on synthetic text over the synthetic fixture's answer. No historical
answer is revalidated under v1.2.0: V5 stays judged against v1.1.0.
"""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib

import pytest
from sros_opportunity.generation_headroom import generation_target, headroom_table
from sros_opportunity.output_constraints import constraint_inventory
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
from sros_opportunity.second_opportunity_schema_v1_2 import (
    EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX,
    MISSING,
    REASONING_SUMMARY_DECISION_BASIS,
    REASONING_SUMMARY_FIELD,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
    output_schema_sha256,
    semantic_schema_diff,
)

V1_1_SHA256 = "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
V1_2_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
SUMMARY_PATH = f"properties.{REASONING_SUMMARY_FIELD}.maxLength"


def _synthetic_answer() -> dict:
    import importlib.util

    root = pathlib.Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location(
        "fixtures_for_schema_v1_2",
        root / "infrastructure" / "scripts" / "second_opportunity_synthetic_fixtures.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.good_output()


def _with_summary(length: int) -> dict:
    answer = _synthetic_answer()
    answer[REASONING_SUMMARY_FIELD] = "y" * length
    return answer


class TestTheIdentities:
    def test_the_version(self):
        assert (
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2
            == "second-opportunity-synthesis-output@1.2.0"
        )

    def test_v1_1_is_untouched(self):
        assert output_schema_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == V1_1_SHA256
        assert (
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][REASONING_SUMMARY_FIELD][
                "maxLength"
            ]
            == 900
        )

    def test_the_v1_2_digest(self):
        assert output_schema_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2) == V1_2_SHA256

    def test_the_digest_is_the_repository_convention(self):
        schema = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
        expected = hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()
        assert output_schema_sha256(schema) == expected

    def test_the_bound_is_the_operators(self):
        assert EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX == 1500
        assert REASONING_SUMMARY_DECISION_BASIS == "OPERATOR_SEMANTIC_BUDGET"


class TestExactlyOneSemanticChange:
    def test_the_diff_is_one_leaf(self):
        diff = semantic_schema_diff(
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
        )
        assert diff == [(SUMMARY_PATH, 900, 1500)]

    def test_every_other_constraint_is_identical(self):
        old = {
            (c.path, c.keyword): c.value
            for c in constraint_inventory(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
        }
        new = {
            (c.path, c.keyword): c.value
            for c in constraint_inventory(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
        }
        assert set(old) == set(new)
        moved = {key for key in old if old[key] != new[key]}
        assert moved == {(REASONING_SUMMARY_FIELD, "maxLength")}

    def test_the_diff_sees_a_second_change(self):
        schema = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
        schema["properties"]["candidate_intervention_class"]["maxLength"] = 301
        assert len(semantic_schema_diff(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, schema)) == 2

    def test_the_diff_sees_a_reworded_description(self):
        schema = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
        schema["properties"][REASONING_SUMMARY_FIELD]["description"] = "reworded"
        assert len(semantic_schema_diff(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, schema)) >= 2

    def test_the_diff_sees_an_added_and_a_removed_key(self):
        schema = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
        schema["properties"]["extra"] = {"type": "string"}
        del schema["properties"]["subject"]
        diff = semantic_schema_diff(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, schema)
        assert ("properties.extra", MISSING, {"type": "string"}) in diff
        assert any(path == "properties.subject" and new == MISSING for path, _old, new in diff)

    def test_the_diff_compares_types(self):
        assert semantic_schema_diff({"a": 1}, {"a": True}) == [("a", 1, True)]


class TestTheHeadroomFollowsTheBound:
    def test_the_summary_target_is_derived(self):
        rows = {row.path: row for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)}
        row = rows[REASONING_SUMMARY_FIELD]
        assert row.hard_maximum == EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX
        assert row.generation_target == generation_target(EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX)
        assert row.generation_target == 1200

    def test_only_the_summary_row_moves(self):
        def table(schema: dict) -> dict:
            return {
                row.path: (
                    row.hard_maximum,
                    row.generation_target,
                    row.constraint_rule,
                    row.constraint_class,
                )
                for row in headroom_table(schema)
            }

        old, new = (
            table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1),
            table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2),
        )
        assert set(old) == set(new) and len(new) == 12
        assert {path for path in old if old[path] != new[path]} == {REASONING_SUMMARY_FIELD}


class TestTheBoundaries:
    @pytest.mark.parametrize("length", [1199, 1200, 1201, 1499, 1500])
    def test_within_the_new_bound_passes(self, length):
        assert schema_violations(_with_summary(length), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2) == []

    def test_one_over_the_new_bound_fails(self):
        violations = schema_violations(_with_summary(1501), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
        assert violations == [f"{REASONING_SUMMARY_FIELD}: 1501 characters exceeds maxLength 1500"]

    @pytest.mark.parametrize("length", [901, 1031, 1500])
    def test_v1_1_still_refuses_over_its_own_bound(self, length):
        violations = schema_violations(_with_summary(length), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
        assert violations == [
            f"{REASONING_SUMMARY_FIELD}: {length} characters exceeds maxLength 900"
        ]

    def test_the_synthetic_answer_passes_both(self):
        answer = _synthetic_answer()
        assert schema_violations(answer, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []
        assert schema_violations(answer, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2) == []

    @pytest.mark.parametrize(
        "field",
        [
            "candidate_intervention_class",
            "observed_need",
            "hypothesis_statement",
            "target_actor_if_supported",
        ],
    )
    def test_every_other_composed_bound_is_where_it_was(self, field):
        bound = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field]["maxLength"]
        for schema in (
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
        ):
            answer = _synthetic_answer()
            answer[field] = "y" * bound
            assert schema_violations(answer, schema) == []
            answer[field] = "y" * (bound + 1)
            assert schema_violations(answer, schema) == [
                f"{field}: {bound + 1} characters exceeds maxLength {bound}"
            ]
