"""Mission 1.84.19. CI gate 92 over the provider-strict projection, and the refusals it must make.

The whole gate runs once. Every refusal hands one of its checks a copy with one thing changed, so
the committed record is never touched. Nothing here reaches a network.
"""

from __future__ import annotations

import copy
import dataclasses
import importlib.util
import json
import pathlib
from typing import Any

import pytest
from sros_opportunity.schema_validation import schema_violations

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "infrastructure" / "scripts"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_92_under_test", SCRIPTS / "render_second_opportunity_provider_strict_projection.py"
    )


@pytest.fixture(scope="module")
def record(gate) -> dict[str, Any]:
    return gate.validate()


@pytest.fixture(scope="module")
def schemas(gate, record) -> tuple[dict[str, Any], dict[str, Any]]:
    return gate.SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2, record["PROVIDER_STRICT_INPUT_SCHEMA"][
        "schema"
    ]


def _changed(value: dict[str, Any], change) -> dict[str, Any]:
    mutated = copy.deepcopy(value)
    change(mutated)
    return mutated


class TestTheCommittedRecord:
    def test_it_validates_and_the_page_is_its_rendering(self, gate, record):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(record)

    def test_every_constraint_is_accounted_for_with_no_blocker(self, record):
        block = record["CONSTRAINT_ACCOUNTING"]
        assert block["CANONICAL_CONSTRAINTS_ACCOUNTED_FOR"] == "100_PERCENT"
        assert sum(block["totals"].values()) == block["constraints"] == len(block["rows"])
        assert block["totals"]["UNSUPPORTED_ARCHITECTURE_BLOCKER"] == 0

    def test_it_is_frozen(self, gate, record):
        freeze = record["FREEZE"]
        assert "PENDING" not in json.dumps(freeze)
        assert (
            freeze["STRICT_PROJECTION_SHA256"] == record["PROVIDER_STRICT_INPUT_SCHEMA"]["sha256"]
        )
        assert freeze["PROJECTOR_IMPLEMENTATION_SHA256"] == gate.file_sha(gate.PROJECTOR_FILE)

    def test_the_contract_and_the_gate_did_not_move(self, record):
        assert record["UNCHANGED"]["OUTPUT_SCHEMA_CHANGED"] is False
        assert record["UNCHANGED"]["SEMANTIC_GATE_CHANGED"] is False
        assert record["TERMINOLOGY"]["FULL_CANONICAL_SCHEMA_COMPLIANCE"] == "LOCAL_STAGE_5_ONLY"

    def test_what_the_model_no_longer_sees_is_named_and_still_enforced(self, record):
        removed = record["REMOVED_AND_NOT_STATED_IN_THE_PROMPT"]
        assert removed["count"] == len(removed["rows"]) == 8
        assert {row["keyword"] for row in removed["rows"]} == {"maxItems", "maxLength", "pattern"}
        assert "MUST_BE_EXPLICIT_IN_PROMPT" not in {row["class"] for row in removed["rows"]}
        enforced = {
            (row["path"], row["keyword"])
            for row in record["CONSTRAINT_ACCOUNTING"]["rows"]
            if row["local_enforcement"] == "LOCAL_STAGE_5_ASSERTS"
        }
        assert all((row["path"], row["keyword"]) in enforced for row in removed["rows"])

    def test_what_the_documentation_says_is_recorded_as_it_says_it(self, record):
        findings = record["CAPABILITY_FINDINGS"]
        assert findings["STRICT_TOOL_USE_SUPPORTED"]["value"] is True
        assert findings["STRING_MAX_LENGTH_SUPPORTED"]["value"] is False
        assert findings["ARRAY_MAX_ITEMS_SUPPORTED"]["value"] is False
        assert findings["PATTERN_SUPPORTED"]["value"] == "PARTIAL_DOCUMENTED_REGEX_SUBSET"
        assert findings["STRICT_FLAG_LOCATION"]["value"] == "TOOL_DEFINITION_TOP_LEVEL"
        assert findings["BETA_HEADER_REQUIRED"]["value"] is False


class TestTheProjection:
    def test_the_root_carries_exactly_the_contracts_twenty_names(self, schemas):
        canonical, projected = schemas
        assert list(projected["properties"]) == list(canonical["properties"])
        assert len(projected["properties"]) == 20
        assert projected["required"] == canonical["required"]
        assert projected["additionalProperties"] is False

    def test_no_unsupported_keyword_is_sent(self, schemas):
        text = json.dumps(schemas[1])
        for keyword in ("maxLength", "minLength", "maxItems", "pattern"):
            assert f'"{keyword}"' not in text

    def test_the_provider_enforced_keywords_are_sent_unchanged(self, schemas):
        canonical, projected = schemas
        assert (
            projected["properties"]["decision"]["enum"]
            == canonical["properties"]["decision"]["enum"]
        )
        assert projected["properties"]["supporting_evidence_ids"]["items"]["format"] == "uuid"
        inner = projected["properties"]["statement_classifications"]["items"]
        assert inner["additionalProperties"] is False
        assert inner["required"] == ["statement", "classification"]

    def test_no_property_named_by_any_earlier_answer_and_no_strict_flag_inside(self, schemas):
        text = json.dumps(schemas[1])
        assert "parameter name" not in text
        assert '"strict"' not in text


class TestTheContractStaysStricter:
    def test_an_extra_root_key_fails_the_projection_and_stage_5(self, gate, schemas):
        canonical, projected = schemas
        answer = gate.synthetic_valid(canonical) | {"parameter name": "value"}
        assert any(
            "unknown field 'parameter name'" in v for v in schema_violations(answer, projected)
        )
        assert any(
            "unknown field 'parameter name'" in v for v in schema_violations(answer, canonical)
        )

    @pytest.mark.parametrize("length, stage_5_passes", [(1189, True), (1500, True), (1501, False)])
    def test_the_summary_bound_is_local(self, gate, schemas, length, stage_5_passes):
        canonical, projected = schemas
        answer = gate.synthetic_valid(canonical)
        answer["evidence_bound_reasoning_summary"] = "s" * length
        assert schema_violations(answer, projected) == []
        assert (schema_violations(answer, canonical) == []) is stage_5_passes

    def test_an_array_over_its_bound_is_local(self, gate, schemas):
        canonical, projected = schemas
        answer = gate.synthetic_valid(canonical)
        answer["statement_classifications"] = answer["statement_classifications"] * 25
        assert schema_violations(answer, projected) == []
        assert schema_violations(answer, canonical) != []


class TestRefusals:
    def test_a_constraint_without_a_disposition_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda r: r["CONSTRAINT_ACCOUNTING"].__setitem__(
                "CANONICAL_CONSTRAINTS_ACCOUNTED_FOR", "INCOMPLETE"
            ),
        )
        with pytest.raises(gate.ValidationError, match="disappeared"):
            gate._check_accounting(mutated)

    def test_a_length_claimed_as_provider_enforced_is_refused(self, gate, record):
        def claim(r):
            row = next(x for x in r["CONSTRAINT_ACCOUNTING"]["rows"] if x["keyword"] == "maxLength")
            row["disposition"] = "PROVIDER_ENFORCED"

        with pytest.raises(gate.ValidationError, match="provider-enforced"):
            gate._check_accounting(_changed(record, claim))

    def test_a_local_only_constraint_nobody_enforces_is_refused(self, gate, record):
        def drop(r):
            row = next(
                x for x in r["CONSTRAINT_ACCOUNTING"]["rows"] if x["disposition"] == "LOCAL_ONLY"
            )
            row["local_enforcement"] = "NOT_A_SCHEMA_ASSERTION_IN_EITHER_SCHEMA"

        with pytest.raises(gate.ValidationError, match="not enforced locally"):
            gate._check_accounting(_changed(record, drop))

    def test_a_composed_bound_neither_sent_nor_stated_is_refused(self, gate, record):
        def unstate(r):
            row = next(
                x
                for x in r["CONSTRAINT_ACCOUNTING"]["rows"]
                if x["keyword"] == "maxLength"
                and x["constraint_class"] == "MUST_BE_EXPLICIT_IN_PROMPT"
            )
            row["prompt_states_it"] = False

        with pytest.raises(gate.ValidationError, match="neither enforced"):
            gate._check_accounting(_changed(record, unstate))

    @pytest.mark.parametrize(
        "key",
        ["EVERY_OBJECT_SAME_REQUIRED", "EVERY_OBJECT_ADDITIONAL_PROPERTIES_FALSE", "SAME_ENUMS"],
    )
    def test_a_broken_invariant_is_refused(self, gate, record, key):
        mutated = _changed(record, lambda r: r["INVARIANTS"].__setitem__(key, False))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_invariants(mutated)

    def test_a_simulation_that_disagrees_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda r: r["SIMULATIONS"][1].__setitem__("projection_observed", "PASS")
        )
        with pytest.raises(gate.ValidationError, match="projection disagrees"):
            gate._check_simulations(mutated)

    def test_full_compliance_attributed_to_the_provider_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda r: r["TERMINOLOGY"].__setitem__("FULL_CANONICAL_SCHEMA_COMPLIANCE", "PROVIDER"),
        )
        with pytest.raises(gate.ValidationError, match="attributed"):
            gate._check_unchanged(mutated)

    def test_a_moved_freeze_pin_is_refused(self, gate, monkeypatch):
        monkeypatch.setattr(gate, "FROZEN_PROJECTOR_SHA256", "0" * 64)
        with pytest.raises(gate.ValidationError, match="PROJECTOR_IMPLEMENTATION_SHA256"):
            gate.validate()

    def test_an_open_contract_has_no_projection(self, gate, monkeypatch):
        opened = _changed(
            gate.SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
            lambda s: s.__setitem__("additionalProperties", True),
        )
        monkeypatch.setattr(gate, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2", opened)
        with pytest.raises(gate.ValidationError, match="ARCHITECTURE_DECISION"):
            gate.build_record()

    def test_a_profile_that_claims_length_enforcement_is_refused(self, gate, monkeypatch):
        profile = gate.ANTHROPIC_STRICT_TOOL_PROFILE_V1
        widened = dataclasses.replace(
            profile,
            enforced_keywords=profile.enforced_keywords | {"maxLength"},
            local_only_keywords=profile.local_only_keywords - {"maxLength"},
        )
        monkeypatch.setattr(gate, "ANTHROPIC_STRICT_TOOL_PROFILE_V1", widened)
        # The projector has no rule for sending a length, so the claim is refused before any
        # accounting exists: a profile cannot promote a keyword the projector does not implement.
        with pytest.raises(gate.ValidationError, match="ARCHITECTURE_DECISION.*no projection rule"):
            gate.build_record()

    @pytest.mark.parametrize(
        "name, change, broken",
        [
            (
                "a property added",
                lambda s: s["properties"].__setitem__("parameter name", {"type": "string"}),
                "ROOT_PROPERTY_SETS_EQUAL",
            ),
            (
                "a required name dropped",
                lambda s: s["required"].pop(),
                "EVERY_OBJECT_SAME_REQUIRED",
            ),
            (
                "an enum member changed",
                lambda s: s["properties"]["decision"]["enum"].append("MAYBE"),
                "SAME_ENUMS",
            ),
            (
                "a type widened",
                lambda s: s["properties"]["subject"].__setitem__("type", ["string", "null"]),
                "SAME_TYPES",
            ),
            (
                "an unsupported keyword sent",
                lambda s: s["properties"]["subject"].__setitem__("maxLength", 80),
                "NO_LOCAL_ONLY_KEYWORD_SENT",
            ),
            (
                "strict placed inside the schema",
                lambda s: s.__setitem__("strict", True),
                "STRICT_FLAG_NOT_INSIDE_THE_SCHEMA",
            ),
        ],
    )
    def test_a_projection_that_moved_is_caught(self, gate, schemas, name, change, broken):
        canonical, projected = schemas
        values = gate.invariants(canonical, _changed(projected, change))
        assert values[broken] is False, name
