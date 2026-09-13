"""Mission 1.84.14: generation headroom, derived from the live schema and the operator's exact ratio.

What these tests defend:

THE RATIO IS EXACTLY 4/5 AND EVERY TARGET IS floor(hard * 4/5), by one function in integer arithmetic.
THE TARGET IS NOT VALIDATION: target, target + 1 and the hard maximum pass the schema; hard + 1 fails.
ONLY COMPOSED TEXT GETS A TARGET: no copied id, closed choice, identity copy or element count does.
THE TABLE IS DERIVED, NEVER MAINTAINED: a mutated bound or ratio moves exactly the targets it should.
PROMPT v1.4.0 IS v1.3.0 PLUS ONE BLOCK, and it states every target beside its hard maximum.
"""

from __future__ import annotations

import copy
import importlib.util
import math
import pathlib
from fractions import Fraction

import pytest
from sros_opportunity.generation_headroom import (
    ARRAY_HEADROOM_POLICY,
    FIELD_ROLES,
    GENERATION_HEADROOM_POLICY,
    GENERATION_TARGET_RATIO,
    GenerationHeadroomPolicy,
    generation_target,
    headroom_table,
    render_generation_headroom_block,
    unstated_headroom,
    untargeted_bounds,
)
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1 as SCHEMA
from sros_opportunity.second_opportunity_prompt_v1_3 import (
    SECOND_OPPORTUNITY_SYSTEM_V1_3,
    render_second_opportunity_prompt_v1_3,
)
from sros_opportunity.second_opportunity_prompt_v1_4 import (
    GENERATION_HEADROOM_BLOCK_V1_4,
    SECOND_OPPORTUNITY_SYSTEM_V1_4,
    render_second_opportunity_prompt_v1_4,
    second_opportunity_prompt_hash_v1_4,
    unstated_headroom_in,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
FIXTURES = REPO_ROOT / "infrastructure" / "scripts" / "second_opportunity_synthetic_fixtures.py"
CANDIDATE = "candidate_intervention_class"
SUMMARY = "evidence_bound_reasoning_summary"


@pytest.fixture(scope="module")
def fx():
    spec = importlib.util.spec_from_file_location("fixtures_for_headroom_tests", FIXTURES)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rows() -> dict:
    return {row.path: row for row in headroom_table(SCHEMA)}


#: The block with line breaks folded, so a phrase is found wherever wrapping broke it.
FLAT = " ".join(GENERATION_HEADROOM_BLOCK_V1_4.split())


class TestTheRatioIsExact:
    def test_the_ratio_is_four_fifths(self):
        assert Fraction(4, 5) == GENERATION_TARGET_RATIO
        assert GENERATION_HEADROOM_POLICY.ratio_text == "4/5"
        assert float(GENERATION_TARGET_RATIO) == 0.8

    def test_a_float_ratio_is_refused(self):
        with pytest.raises(TypeError):
            GenerationHeadroomPolicy(
                version="x",
                name="x",
                ratio=0.8,  # type: ignore[arg-type]
                applies_to_keyword="maxLength",
                applies_to_rule="composed_length",
                identity_rules=(),
                array_headroom=ARRAY_HEADROOM_POLICY,
            )

    def test_the_target_is_the_integer_floor(self):
        for hard in range(1, 5001):
            assert generation_target(hard) == math.floor(Fraction(hard) * Fraction(4, 5))

    def test_no_binary_rounding_can_move_a_target(self):
        exact = [generation_target(h) for h in range(1, 5001)]
        assert exact == [(h * 4) // 5 for h in range(1, 5001)]

    @pytest.mark.parametrize("bad", [0, -1, 300.0, True, "300"])
    def test_a_hard_maximum_is_a_positive_integer(self, bad):
        with pytest.raises(ValueError):
            generation_target(bad)


class TestTheTargetsDeriveFromTheLiveSchema:
    def test_the_candidate_class_targets_240_below_300(self):
        row = _rows()[CANDIDATE]
        assert (row.hard_maximum, row.generation_target) == (300, 240)
        assert row.hard_maximum == SCHEMA["properties"][CANDIDATE]["maxLength"]

    def test_the_summary_targets_720_below_900(self):
        row = _rows()[SUMMARY]
        assert (row.hard_maximum, row.generation_target) == (900, 720)
        assert row.hard_maximum == SCHEMA["properties"][SUMMARY]["maxLength"]

    def test_every_row_is_the_one_function_of_its_hard_bound(self):
        for row in headroom_table(SCHEMA):
            assert row.generation_target == generation_target(row.hard_maximum)
            assert row.constraint_rule == "composed_length"

    def test_twelve_composed_texts_get_a_target(self):
        assert len(headroom_table(SCHEMA)) == 12


class TestOnlyComposedTextGetsATarget:
    @pytest.mark.parametrize(
        "path", ["supporting_evidence_ids[]", "supporting_claim_ids[]", "source_families[]"]
    )
    def test_copied_values_get_none(self, path):
        assert path not in _rows()
        reasons = {e["field"]: e["reason"] for e in untargeted_bounds(SCHEMA)}
        assert reasons[path].startswith("copied_length")

    def test_the_subject_identity_gets_none(self):
        assert "subject" not in _rows()
        reasons = {e["field"]: e["reason"] for e in untargeted_bounds(SCHEMA)}
        assert "SUBJECT_IS_THE_PACKET_IDENTITY" in reasons["subject"]

    def test_closed_choices_get_none(self):
        for name in ("decision", "confidence_classification"):
            assert name not in _rows()

    def test_no_element_count_gets_a_target(self):
        counts = [e for e in untargeted_bounds(SCHEMA) if e["keyword"] == "maxItems"]
        assert counts and all("ARRAY_HEADROOM_POLICY = NONE" in e["reason"] for e in counts)
        assert all(not row.path.endswith("maxItems") for row in headroom_table(SCHEMA))


class TestTheTargetIsNotValidation:
    @pytest.mark.parametrize("field", [CANDIDATE, SUMMARY])
    def test_target_target_plus_one_and_hard_pass_and_hard_plus_one_fails(self, fx, field):
        row = _rows()[field]
        for length, valid in (
            (row.generation_target, True),
            (row.generation_target + 1, True),
            (row.hard_maximum, True),
            (row.hard_maximum + 1, False),
        ):
            output = fx.good_output(**{field: "x" * length})
            assert (not schema_violations(output, SCHEMA)) is valid, (field, length)


class TestTheTableIsDerivedNeverMaintained:
    def test_a_mutated_hard_bound_moves_its_target(self):
        mutated = copy.deepcopy(SCHEMA)
        mutated["properties"][CANDIDATE]["maxLength"] = 350
        rows = {row.path: row for row in headroom_table(mutated)}
        assert (rows[CANDIDATE].hard_maximum, rows[CANDIDATE].generation_target) == (350, 280)
        assert rows[SUMMARY].generation_target == 720

    def test_a_mutated_ratio_moves_every_target(self):
        policy = GenerationHeadroomPolicy(
            version="mutated",
            name="mutated",
            ratio=Fraction(3, 4),
            applies_to_keyword="maxLength",
            applies_to_rule="composed_length",
            identity_rules=GENERATION_HEADROOM_POLICY.identity_rules,
            array_headroom=ARRAY_HEADROOM_POLICY,
        )
        for base, moved in zip(headroom_table(SCHEMA), headroom_table(SCHEMA, policy), strict=True):
            assert moved.generation_target == (base.hard_maximum * 3) // 4
        assert render_generation_headroom_block(SCHEMA, policy) != GENERATION_HEADROOM_BLOCK_V1_4

    def test_a_mutated_copied_bound_creates_no_target(self):
        mutated = copy.deepcopy(SCHEMA)
        mutated["properties"]["supporting_evidence_ids"]["items"]["maxLength"] = 40
        assert headroom_table(mutated) == headroom_table(SCHEMA)
        assert render_generation_headroom_block(mutated) == GENERATION_HEADROOM_BLOCK_V1_4

    def test_a_mutated_element_count_creates_no_target(self):
        mutated = copy.deepcopy(SCHEMA)
        mutated["properties"]["critical_uncertainties"]["maxItems"] = 13
        assert headroom_table(mutated) == headroom_table(SCHEMA)
        assert render_generation_headroom_block(mutated) == GENERATION_HEADROOM_BLOCK_V1_4


class TestPromptV140:
    def test_v1_3_is_a_byte_identical_prefix(self):
        assert SECOND_OPPORTUNITY_SYSTEM_V1_4.startswith(SECOND_OPPORTUNITY_SYSTEM_V1_3)
        added = SECOND_OPPORTUNITY_SYSTEM_V1_4[len(SECOND_OPPORTUNITY_SYSTEM_V1_3) :]
        assert added == "\n" + GENERATION_HEADROOM_BLOCK_V1_4 + "\n"

    def test_the_other_regions_are_v1_3s(self, fx):
        args = (fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM)
        v13 = render_second_opportunity_prompt_v1_3(*args, source_metadata=fx.metadata())
        v14 = render_second_opportunity_prompt_v1_4(*args, source_metadata=fx.metadata())
        assert (v14.trusted_context, v14.untrusted, v14.task) == (
            v13.trusted_context,
            v13.untrusted,
            v13.task,
        )
        assert second_opportunity_prompt_hash_v1_4(v14) != second_opportunity_prompt_hash_v1_4(v13)

    def test_every_target_is_stated_beside_its_hard_maximum(self, fx):
        parts = render_second_opportunity_prompt_v1_4(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
        )
        assert unstated_headroom_in(parts) == []
        assert unstated_headroom(SECOND_OPPORTUNITY_SYSTEM_V1_3, SCHEMA)
        line = "  candidate_intervention_class: generation target 240 characters; hard maximum 300"
        assert line + " characters" in SECOND_OPPORTUNITY_SYSTEM_V1_4.split("\n")

    def test_the_target_is_never_called_a_limit(self):
        assert "never a limit of the contract" in FLAT
        assert "still valid and is not refused" in FLAT

    def test_the_roles_are_stated(self):
        for role in FIELD_ROLES:
            assert f"  {role.field}" in GENERATION_HEADROOM_BLOCK_V1_4.split("\n")
            for line in role.lines:
                assert " ".join(line.split()) in FLAT
        assert "and only the class" in FLAT
        assert "a synthesis, not a ledger" in FLAT

    def test_concision_never_costs_information(self):
        for item in ("an uncertainty", "an unsupported claim", "a relevant limitation"):
            assert item in FLAT
        assert "more confident than the evidence allows, or harder to audit" in FLAT
        assert "it may exceed the target, and it still stays within its hard maximum" in FLAT

    def test_no_scratchpad_is_requested(self):
        assert "write no count, draft or working anywhere in it" in FLAT

    @pytest.mark.parametrize("historical", ["316", "1078", "224", "868", "V4", "tender"])
    def test_no_historical_answer_reaches_the_block(self, historical):
        assert historical not in GENERATION_HEADROOM_BLOCK_V1_4
