"""Mission 1.84.3. The schema has no maximum, so no ceiling can be derived from it.

Four things this file defends.

BOUNDEDNESS IS RE-DERIVED, NOT READ. The walk runs against the executable schema. Tests that took
`FINITE_BOUND` from the artifact would be checking that somebody typed a boolean.

THE EIGHT UNBOUNDED PATHS ARE MISSION 1.31's, BYTE-IDENTICALLY. The three fields Mission 1.84
added are the only properly bounded ones in the schema, which corrects Mission 1.84.2's
attribution without excusing 1.84's failure to derive anything.

A FLOOR IS NOT A MAXIMUM. The bounded subset alone already exceeds the frozen cap, with the
unbounded arrays held empty and worst-case JSON escaping applied. It is a lower bound on a
maximum that does not exist.

NO NUMBER WAS INVENTED. No ceiling, no exact token count, no provider limit standing in for a
schema bound, and no schema edit to make the arithmetic come out.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest
from sros_opportunity import (
    SECOND_OPPORTUNITY_GATE_VERSION,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
    SYNTHESIS_OUTPUT_SCHEMA,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / ("render_second_opportunity_output_capacity.py")
)
ANALYSIS = DATA / "second-opportunity-output-capacity-analysis-v1.json"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"

EXPECTED_UNBOUNDED = {
    "supported_dimensions[]",
    "unsupported_dimensions[]",
    "supporting_evidence_ids[]",
    "supporting_claim_ids[]",
    "source_families[]",
    "critical_uncertainties[]",
    "commercial_claims_supported[]",
    "commercial_claims_not_supported[]",
}


def _gate():
    spec = importlib.util.spec_from_file_location("output_capacity_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _gate()


@pytest.fixture(scope="module")
def record() -> dict:
    return json.loads(ANALYSIS.read_text(encoding="utf-8"))


class TestTheSchemaIsUnbounded:
    def test_the_walk_finds_exactly_the_eight_paths(self, gate) -> None:
        found = set(gate.unbounded_paths(SECOND_OPPORTUNITY_OUTPUT_SCHEMA))
        assert found == EXPECTED_UNBOUNDED

    def test_each_one_is_a_string_with_no_enum_and_no_maxlength(self) -> None:
        for path in EXPECTED_UNBOUNDED:
            field = path.removesuffix("[]")
            items = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"][field]["items"]
            assert items["type"] == "string"
            assert "enum" not in items
            assert items.get("maxLength") is None

    def test_every_one_is_required(self) -> None:
        """An optional unbounded path would still be reachable, but these are not even optional."""
        required = set(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"])
        for path in EXPECTED_UNBOUNDED:
            assert path.removesuffix("[]") in required

    def test_the_record_agrees_with_the_walk(self, record, gate) -> None:
        assert record["FINITE_BOUND"] is False
        assert sorted(i["path"] for i in record["unbounded_paths"]) == sorted(
            gate.unbounded_paths(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)
        )

    def test_a_bounded_variant_would_be_finite(self, gate) -> None:
        """The walk is discriminating: bound the item strings and it reports finite."""
        import copy

        variant = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)
        for path in EXPECTED_UNBOUNDED:
            variant["properties"][path.removesuffix("[]")]["items"]["maxLength"] = 120
        assert gate.unbounded_paths(variant) == []

    def test_a_missing_maxitems_is_also_caught(self, gate) -> None:
        import copy

        variant = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)
        for path in EXPECTED_UNBOUNDED:
            variant["properties"][path.removesuffix("[]")]["items"]["maxLength"] = 120
        del variant["properties"]["recommended_next_evidence"]["maxItems"]
        assert "recommended_next_evidence" in gate.unbounded_paths(variant)

    def test_open_additional_properties_is_caught(self, gate) -> None:
        """§12. An open object destroys a finite bound however small its declared fields are."""
        import copy

        variant = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)
        for path in EXPECTED_UNBOUNDED:
            variant["properties"][path.removesuffix("[]")]["items"]["maxLength"] = 120
        variant["properties"]["statement_classifications"]["items"]["additionalProperties"] = True
        assert "statement_classifications[]" in gate.unbounded_paths(variant)


class TestTheProvenanceIsMission131s:
    def test_all_eight_come_from_the_base_schema(self) -> None:
        base = set(SYNTHESIS_OUTPUT_SCHEMA["required"])
        for path in EXPECTED_UNBOUNDED:
            assert path.removesuffix("[]") in base

    def test_they_are_byte_identical_to_the_base(self) -> None:
        for path in EXPECTED_UNBOUNDED:
            field = path.removesuffix("[]")
            assert (
                SYNTHESIS_OUTPUT_SCHEMA["properties"][field]
                == SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"][field]
            )

    def test_the_three_fields_1_84_added_are_all_bounded(self, gate) -> None:
        """The correction to Mission 1.84.2's attribution, checked rather than asserted."""
        base = set(SYNTHESIS_OUTPUT_SCHEMA["required"])
        added = set(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]) - base
        assert added == {
            "recommended_next_evidence",
            "confidence_classification",
            "statement_classifications",
        }
        unbounded_fields = {p.removesuffix("[]") for p in EXPECTED_UNBOUNDED}
        assert added & unbounded_fields == set()

    def test_the_record_attributes_each_path_correctly(self, record) -> None:
        base = set(SYNTHESIS_OUTPUT_SCHEMA["required"])
        for item in record["unbounded_paths"]:
            field = item["path"].removesuffix("[]")
            expected = "MISSION_1_31_BASE_SCHEMA" if field in base else "MISSION_1_84"
            assert item["introduced_by"] == expected


class TestTheFloorIsAFloor:
    def test_it_is_not_called_a_maximum(self, record) -> None:
        assert record["SCHEMA_MAX_SERIALIZED_SIZE"] == "UNBOUNDED"
        assert "NOT the schema maximum" in record["BOUNDED_SUBSET_FLOOR"]["$comment"]

    def test_it_holds_the_unbounded_arrays_empty(self, record) -> None:
        assert "empty" in record["BOUNDED_SUBSET_FLOOR"]["method"]

    def test_it_exceeds_the_frozen_cap(self, record) -> None:
        floor = record["BOUNDED_SUBSET_FLOOR"]
        assert floor["floor_exceeds_frozen_cap"] is True
        assert floor["frozen_cap_it_is_compared_against"] == 3000
        assert floor["FLOOR_SERIALIZED_CHARACTERS"] > 3000

    def test_worst_case_escaping_is_applied(self, record) -> None:
        """A quotation mark serialises to two characters; ignoring that understates the floor."""
        assert record["BOUNDED_SUBSET_FLOOR"]["worst_case_escaping_applied"] is True

    def test_escaping_really_does_increase_the_serialized_size(self) -> None:
        plain = json.dumps({"s": "a" * 300})
        escaped = json.dumps({"s": '"' * 300})
        assert len(escaped) > len(plain)
        assert len(escaped) - len(plain) == 300

    def test_a_larger_legal_maxitems_would_increase_the_floor(self) -> None:
        """A positive control on the arithmetic, computed without touching the real schema."""
        item = {"statement": '"' * 300, "classification": "OBSERVED_OR_EVIDENCE_SUPPORTED"}
        small = len(json.dumps([item] * 24, sort_keys=True))
        large = len(json.dumps([item] * 48, sort_keys=True))
        assert large > small

    def test_a_longer_legal_maxlength_would_increase_the_floor(self) -> None:
        assert len(json.dumps('"' * 600)) > len(json.dumps('"' * 300))

    def test_statement_classifications_dominates(self, record) -> None:
        top = record["DOMINANT_FIELDS_BY_SERIALIZED_SIZE"][0]
        assert top["field"] == "statement_classifications"
        assert top["bounded"] is True


class TestNoNumberWasInvented:
    def test_no_ceiling_was_selected(self, record) -> None:
        assert record["SELECTED_MAX_OUTPUT_TOKENS"] == "NONE"
        assert record["DERIVED_MIN_OUTPUT_TOKEN_CAPACITY"] == "NOT_DERIVABLE"

    def test_no_exact_token_count(self, record) -> None:
        tokens = record["TOKENIZATION"]
        assert tokens["EXACT_MAX_OUTPUT_TOKEN_COUNT"] == "NOT_ESTABLISHED"
        assert tokens["exact_tokenizer_available"] is False
        assert tokens["no_ceiling_derived"] is True

    def test_the_empirical_ratio_carries_its_direction_warning(self, record) -> None:
        """§16. Too high a ratio divides by too much and underestimates tokens."""
        warning = record["TOKENIZATION"]["empirical_ratio_direction_warning"]
        assert "UNDERESTIMATES" in warning.upper()
        assert record["TOKENIZATION"]["empirical_ratio_classification"] == (
            "EMPIRICAL_LOWER_INFORMATION_BOUND"
        )

    def test_no_provider_limit_stands_in_for_a_schema_bound(self, record) -> None:
        assert record["PROVIDER_OUTPUT_TOKEN_LIMIT"] in ("NOT_READ", "NOT_ESTABLISHED")

    def test_3000_was_not_carried_forward(self, record) -> None:
        assert record["SELECTED_MAX_OUTPUT_TOKENS"] != 3000
        assert record["THINGS_NOT_DONE"]["copied_3000"] is False

    def test_no_dependency_was_installed_for_a_convenient_number(self, record) -> None:
        assert record["ACCOUNTING"]["DEPENDENCIES_INSTALLED"] == 0


class TestTheSchemaWasNotEditedToRescueCapacity:
    def test_twenty_required_fields_remain(self) -> None:
        assert len(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]) == 20

    def test_the_two_fields_the_failed_response_omitted_are_still_required(self) -> None:
        required = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]
        assert "confidence_classification" in required
        assert "statement_classifications" in required

    def test_the_dominant_field_was_not_shrunk(self) -> None:
        sc = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"]["statement_classifications"]
        assert sc["maxItems"] == 24
        assert sc["items"]["properties"]["statement"]["maxLength"] == 300

    def test_the_versions_are_the_code_s(self, record) -> None:
        assert record["schema_id"] == SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION
        assert record["output_gate"] == SECOND_OPPORTUNITY_GATE_VERSION
        assert record["schema_changed_by_this_mission"] is False

    def test_every_not_done_flag_is_false(self, record) -> None:
        for key, value in record["THINGS_NOT_DONE"].items():
            if key.startswith("$") or key == "note":
                continue
            assert value is False, key


class TestNoV2AndV1Untouched:
    def test_no_v2_packet_exists(self, record) -> None:
        assert record["EXECUTION_PACKET_V2_CREATED"] is False
        if PACKET_V2.exists():  # Mission 1.84.6: a later mission's V2, never this one's
            prepared_by = json.loads(PACKET_V2.read_text(encoding="utf-8"))["prepared_by"]
            later = tuple(int(p) for p in prepared_by.removeprefix("mission-").split("."))
            assert later > (1, 84, 3), prepared_by

    def test_v1_is_byte_identical_and_still_capped_at_3000(self) -> None:
        packet = json.loads(PACKET_V1.read_text(encoding="utf-8"))
        assert packet["EXECUTION_PACKET_SHA256"] == V1_SHA256
        assert packet["MAX_OUTPUT_TOKENS"] == 3000
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False

    def test_the_consumed_approval_was_not_reset(self, record) -> None:
        state = record["V1_STATE"]
        assert state["EXECUTION_APPROVAL_CONSUMED"] is True
        assert state["FURTHER_CALLS_AUTHORIZED_BY_V1"] is False
        assert state["guard_still_refuses_v1"] is True

    def test_the_guard_still_permits_a_genuinely_new_digest(self, record) -> None:
        assert record["V1_STATE"]["guard_permits_a_new_digest"] is True


class TestOptionsAreOfferedAndNotTaken:
    def test_none_implemented_and_none_recommended(self, record) -> None:
        options = record["OPTIONS_FOR_THE_OPERATOR"]
        assert options["implemented_here"] == "NONE"
        assert options["recommended_here"] == "NONE"

    def test_each_option_says_whether_it_makes_the_schema_finite(self, record) -> None:
        """The only property that decides whether a ceiling becomes derivable."""
        for option in record["OPTIONS_FOR_THE_OPERATOR"]["options"]:
            assert isinstance(option["makes_the_schema_finite"], bool)
            assert option["cost"].strip()

    def test_exactly_one_option_makes_the_schema_finite(self, record) -> None:
        finite = [
            o for o in record["OPTIONS_FOR_THE_OPERATOR"]["options"] if o["makes_the_schema_finite"]
        ]
        assert len(finite) == 1
        assert finite[0]["id"] == "BOUND_THE_EIGHT_ITEM_STRINGS"


class TestNothingElseMovedAndNothingWasCalled:
    def test_the_payload_digests_are_the_approved_ones(self, record) -> None:
        revalidation = record["REVALIDATION"]
        packet = json.loads(PACKET_V1.read_text(encoding="utf-8"))
        assert revalidation["representation_sha256_recomputed"] == packet["REPRESENTATION_SHA256"]
        assert revalidation["prompt_sha256_recomputed"] == packet["PROMPT_SHA256"]

    def test_provider_model_and_pricing_are_unchanged(self, record) -> None:
        revalidation = record["REVALIDATION"]
        assert revalidation["provider_posture"] == "APPROVED"
        assert revalidation["model_selection_changed"] is False
        assert revalidation["pricing_changed"] is False
        assert revalidation["subscription_route_used"] is False

    def test_the_retention_repair_is_verified(self, record) -> None:
        assert record["RETENTION_REPAIR_VERIFIED"] is True
        assert record["retention_repair_evidence"].strip()

    def test_every_accounting_counter_is_zero(self, record) -> None:
        for key, value in record["ACCOUNTING"].items():
            assert value == 0, key

    def test_the_gate_is_wired_into_ci(self) -> None:
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "render_second_opportunity_output_capacity.py --check" in ci
