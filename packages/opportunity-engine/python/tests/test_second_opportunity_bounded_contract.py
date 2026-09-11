"""Mission 1.84.4. The eight unbounded item types are bounded, and the contract is finite.

Five things this file defends.

THE SUCCESSOR IS FINITE AND THE PREDECESSOR IS NOT. Both are walked with the executable schema.
A test that read `FINITE_BOUND` from the artifact would be checking that somebody typed a boolean,
and a test that only checked the successor would not notice v1.0.0 being "fixed" in place -- which
would make the historical execution stop resolving against the contract it actually used.

EACH BOUND MATCHES ITS FIELD. A dimension is refused when it is UNKNOWN rather than when it is
long; an id is refused when it is not an id rather than when it is over 36 characters; a source
family is a registry slug and not an enum; three of the eight are prose and only those three got a
length.

THE MAXIMUM IS REBUILT AND REVALIDATED. Not read from the record. Worst-case JSON escaping means a
non-BMP character, twelve serialized characters for one character of budget -- five times the
quotation mark Mission 1.84.3's floor used, and understating it is the unsafe direction.

NO CEILING WAS INVENTED. No exact token count without a tokenizer, no safe conversion asserted
without a contract that establishes one, no adapter default promoted to a provider capability, and
no round number anywhere.

NOTHING HISTORICAL MOVED. v1.0.0 readable, its prompt digest unchanged, the TED representation
unchanged, V1 consumed and still refused, and no V2.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import uuid

import pytest
from sros_contracts.ids import ClaimId, EvidenceId
from sros_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA
from sros_opportunity.dimensions import EvidenceDimension
from sros_opportunity.schema_validation import schema_violations, unsupported_keywords
from sros_opportunity.second_opportunity import (
    BOUNDED_ITEM_TYPES,
    CANONICAL_UUID_PATTERN,
    COMMERCIAL_CLAIM_MAX_LENGTH,
    CRITICAL_UNCERTAINTY_MAX_LENGTH,
    REGISTRY_SLUG_MAX_LENGTH,
    REGISTRY_SLUG_PATTERN,
    SECOND_OPPORTUNITY_GATE_VERSION,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_VERSION,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
    SECOND_OPPORTUNITY_SYSTEM,
    SECOND_OPPORTUNITY_SYSTEM_V1_1,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_bounded_contract.py"
)
DECISION = DATA / "second-opportunity-output-boundedness-decision-v1.json"
CAPACITY = DATA / "second-opportunity-output-capacity-analysis-v2.json"
CAPACITY_V1 = DATA / "second-opportunity-output-capacity-analysis-v1.json"
PROMPT = DATA / "second-opportunity-synthesis-prompt-v2.json"
PROMPT_V1 = DATA / "second-opportunity-synthesis-prompt-v1.json"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
RUN_SCRIPT = REPO_ROOT / "infrastructure" / "scripts" / "run_second_opportunity_execution.py"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
PROMPT_V1_SHA256 = "af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080"

THE_EIGHT = tuple(field for field, _ in BOUNDED_ITEM_TYPES)
EXPECTED_UNBOUNDED = {f"{field}[]" for field in THE_EIGHT}


def _gate():
    spec = importlib.util.spec_from_file_location("bounded_contract_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _gate()


@pytest.fixture(scope="module")
def decision():
    return json.loads(DECISION.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def capacity():
    return json.loads(CAPACITY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def prompt_doc():
    return json.loads(PROMPT.read_text(encoding="utf-8"))


# --------------------------------------------------------------- boundedness, both directions


class TestBoundedness:
    def test_the_successor_has_no_unbounded_path(self, gate):
        assert gate.unbounded_paths(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []

    def test_the_predecessor_still_has_its_eight(self, gate):
        """v1.0.0 keeps the defect, because the historical execution used it."""
        assert set(gate.unbounded_paths(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)) == EXPECTED_UNBOUNDED

    def test_the_record_agrees_with_the_walker(self, capacity):
        assert capacity["FINITE_BOUND"] is True
        assert capacity["unbounded_path_count"] == 0
        assert capacity["predecessor_unbounded_path_count"] == 8

    def test_capacity_declared_finite_while_a_path_is_unbounded_is_refused(self, gate, capacity):
        broken = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
        broken["properties"]["critical_uncertainties"]["items"].pop("maxLength")
        assert gate.unbounded_paths(broken) == ["critical_uncertainties[]"]

    def test_the_validator_understands_every_keyword_the_schemas_use(self):
        assert unsupported_keywords(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []
        assert unsupported_keywords(SECOND_OPPORTUNITY_OUTPUT_SCHEMA) == []


# --------------------------------------------------------------- each bound matches its field


class TestSemanticBounds:
    def test_every_one_of_the_eight_is_classified(self):
        methods = dict(BOUNDED_ITEM_TYPES)
        assert set(methods) == set(THE_EIGHT)
        assert set(methods.values()) == {
            "CLOSED_VOCABULARY",
            "CANONICAL_IDENTIFIER",
            "BOUNDED_IDENTIFIER",
            "BOUNDED_NARRATIVE",
        }

    def test_one_number_was_not_applied_to_all_eight(self):
        """Section 5. Four different instruments, because the fields differ in kind."""
        items = {
            field: SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field]["items"]
            for field in THE_EIGHT
        }
        lengths = {i.get("maxLength") for i in items.values()}
        assert len(lengths) > 1
        assert {i.get("enum") is not None for i in items.values()} == {True, False}
        assert {i.get("pattern") is not None for i in items.values()} == {True, False}

    def test_dimensions_are_the_canonical_vocabulary(self):
        expected = [d.value for d in EvidenceDimension]
        for field in ("supported_dimensions", "unsupported_dimensions"):
            items = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field]["items"]
            assert items["enum"] == expected

    def test_an_unknown_dimension_is_refused_however_short(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["supported_dimensions"]
        for bad in ("X", "MARKET_DEMAND", "market activity", "MARKET_ACTIVIT"):
            assert schema_violations([bad], field), bad

    def test_a_dimension_as_arbitrary_prose_is_refused(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["unsupported_dimensions"]
        prose = "the packet establishes nothing about willingness to pay"
        assert schema_violations([prose], field)

    def test_dimensions_carry_no_maxlength_beside_their_enum(self):
        for field in ("supported_dimensions", "unsupported_dimensions"):
            items = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field]["items"]
            assert "maxLength" not in items

    def test_evidence_and_claim_ids_use_the_canonical_identity_grammar(self):
        for field in ("supporting_evidence_ids", "supporting_claim_ids"):
            items = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field]["items"]
            assert items["pattern"] == CANONICAL_UUID_PATTERN
            assert items["maxLength"] == 36

    def test_the_pattern_accepts_what_the_identity_classes_produce(self):
        pattern = re.compile(CANONICAL_UUID_PATTERN)
        for identity in (ClaimId, EvidenceId):
            assert pattern.match(str(identity.generate()))

    def test_a_malformed_evidence_id_is_refused(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["supporting_evidence_ids"]
        for bad in (
            "the first evidence row",
            "0b407e80336a4b718a5909f0464bf43f",
            str(uuid.uuid4()).upper(),
            "{0b407e80-336a-4b71-8a59-09f0464bf43f}",
            "0b407e80-336a-4b71-8a59-09f0464bf43",
        ):
            assert schema_violations([bad], field), bad

    def test_a_malformed_claim_id_is_refused(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["supporting_claim_ids"]
        for bad in ("claim 1", "d25bd256-49a1-494f-b6f8", "x" * 36):
            assert schema_violations([bad], field), bad

    def test_source_families_is_a_registry_not_an_enum(self):
        """Section 9. `domain.v1.json` lists it under registries, so an enum would freeze it."""
        items = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["source_families"]["items"]
        assert "enum" not in items
        assert items["pattern"] == REGISTRY_SLUG_PATTERN
        assert items["maxLength"] == REGISTRY_SLUG_MAX_LENGTH
        spec = json.loads(
            (REPO_ROOT / "packages" / "contracts" / "schema" / "domain.v1.json").read_text(
                encoding="utf-8"
            )
        )
        assert "source_family" in {r["name"] for r in spec["registries"]}
        assert "source_family" not in {e["name"] for e in spec["closed_enums"]}

    def test_the_slug_grammar_is_the_one_the_database_enforces(self):
        sql = (
            REPO_ROOT / "infrastructure" / "db" / "migrations" / "0001_foundation.sql"
        ).read_text(encoding="utf-8")
        match = re.search(r"registry_entries_id_slug_check\s*\n\s*CHECK \(id ~ '([^']+)'\)", sql)
        assert match is not None
        assert match.group(1) == REGISTRY_SLUG_PATTERN

    def test_source_family_bound_to_the_wrong_vocabulary_is_refused(self):
        """A catalog `source_family` and a packet `source_family` are not the same string set."""
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["source_families"]
        assert schema_violations(["public_procurement"], field) == []
        for wrong in ("PUBLIC_PROCUREMENT", "public procurement", "UNREGISTERED", "-leading"):
            assert schema_violations([wrong], field), wrong

    def test_critical_uncertainties_carries_the_operator_length(self):
        items = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["critical_uncertainties"][
            "items"
        ]
        assert items["maxLength"] == CRITICAL_UNCERTAINTY_MAX_LENGTH == 500
        assert items["minLength"] == 1
        assert "enum" not in items

    def test_critical_uncertainties_maxitems_was_not_reduced(self):
        assert (
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["critical_uncertainties"][
                "maxItems"
            ]
            == 12
        )

    def test_commercial_claims_are_narrative_with_the_operator_length(self):
        for field in ("commercial_claims_supported", "commercial_claims_not_supported"):
            items = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field]["items"]
            assert items["maxLength"] == COMMERCIAL_CLAIM_MAX_LENGTH == 300
            assert "enum" not in items

    def test_the_narrative_branch_is_justified_by_the_historical_output(self):
        """Section 11 required inspection rather than assumption, and this is the evidence."""
        run = json.loads((DATA / "opportunity-synthesis-run-v1.1.json").read_text(encoding="utf-8"))
        claims = run["model_output"]["commercial_claims_not_supported"]
        assert claims
        names = {d.value for d in EvidenceDimension}
        assert not (set(claims) & names)
        assert all(" " in claim for claim in claims)


# --------------------------------------------------------------- lengths, both sides of the line


class TestLengths:
    def test_the_maximum_legal_narrative_length_is_accepted(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["critical_uncertainties"]
        assert schema_violations(["u" * 500], field) == []
        commercial = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][
            "commercial_claims_supported"
        ]
        assert schema_violations(["c" * 300], commercial) == []

    def test_one_over_the_maximum_is_refused(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["critical_uncertainties"]
        assert schema_violations(["u" * 501], field)
        commercial = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][
            "commercial_claims_supported"
        ]
        assert schema_violations(["c" * 301], commercial)
        other = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][
            "commercial_claims_not_supported"
        ]
        assert schema_violations(["c" * 301], other)

    def test_an_empty_uncertainty_is_refused(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["critical_uncertainties"]
        assert schema_violations([""], field)

    def test_an_array_over_its_maxitems_is_refused(self):
        field = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["source_families"]
        assert schema_violations(["a"] * 10, field) == []
        assert schema_violations(["a"] * 11, field)


# --------------------------------------------------------------- nothing was reduced or reordered


class TestNothingReduced:
    def test_maxitems_is_identical_across_the_version_bump(self):
        old = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"]
        new = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]
        for name, node in old.items():
            assert node.get("maxItems") == new[name].get("maxItems"), name

    def test_the_required_list_is_identical_and_in_order(self):
        assert list(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]) == list(
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["required"]
        )

    def test_only_the_eight_items_changed(self):
        old = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"]
        new = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]
        changed = {
            name
            for name in old
            if json.dumps(old[name], sort_keys=True) != json.dumps(new[name], sort_keys=True)
        }
        assert changed == set(THE_EIGHT)

    def test_the_failed_response_shaped_nothing(self, decision):
        """Section 12. The 18/20 answer was missing fields 19 and 20 and neither was touched."""
        assert decision["THINGS_NOT_DONE"]["failed_18_of_20_response_used_as_design_evidence"] is (
            False
        )
        for field in ("confidence_classification", "statement_classifications"):
            assert field in SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["required"]
            assert json.dumps(
                SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"][field], sort_keys=True
            ) == json.dumps(
                SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field], sort_keys=True
            )


# --------------------------------------------------------------- the maximum instance


class TestMaximumInstance:
    def test_the_maximum_instance_validates(self, gate, capacity):
        instance = gate.maximum_instance(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, gate.WORST_FILL)
        assert schema_violations(instance, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []
        assert capacity["MAXIMUM_VALID_INSTANCE"]["MAX_INSTANCE_SCHEMA_VALID"] is True

    def test_the_recorded_numbers_are_the_rebuilt_ones(self, gate, capacity):
        instance = gate.maximum_instance(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, gate.WORST_FILL)
        text = json.dumps(instance, sort_keys=True)
        block = capacity["MAXIMUM_VALID_INSTANCE"]
        assert block["MAX_VALID_OUTPUT_CHARACTERS"] == len(text)
        assert block["MAX_VALID_OUTPUT_UTF8_BYTES"] == len(text.encode("utf-8"))

    def test_the_worst_case_escaping_is_worse_than_a_quotation_mark(self, gate, capacity):
        """Understating the maximum is the unsafe direction, so the fill is the worst one."""
        block = capacity["MAXIMUM_VALID_INSTANCE"]
        assert block["ASCII_FILL_MAXIMUM_CHARACTERS"] < block["MAX_VALID_OUTPUT_CHARACTERS"]
        assert json.dumps(gate.WORST_FILL)[1:-1] != gate.WORST_FILL

    def test_every_field_has_a_contribution(self, capacity):
        fields = {row["field"] for row in capacity["FIELD_CONTRIBUTIONS"]}
        assert fields == set(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"])

    def test_the_formerly_unbounded_paths_are_no_longer_dominant(self, capacity):
        """Section 20's actual finding, asserted so a later reader cannot miss it."""
        rows = {row["field"]: row["percentage_of_total"] for row in capacity["FIELD_CONTRIBUTIONS"]}
        identifiers = ("supporting_evidence_ids", "supporting_claim_ids", "source_families")
        assert sum(rows[f] for f in identifiers) < 1.0
        assert rows["statement_classifications"] > 20.0


# --------------------------------------------------------------- no ceiling was invented


class TestNoCeilingInvented:
    def test_no_exact_token_count_without_a_tokenizer(self, capacity):
        tokens = capacity["TOKENIZATION"]
        assert tokens["EXACT_TOKENIZER_AVAILABLE"] is False
        assert tokens["EXACT_MAX_OUTPUT_TOKEN_COUNT"] == "NOT_ESTABLISHED"

    def test_no_tokenizer_is_installed(self):
        """The claim above is checked rather than asserted."""
        import importlib.util as util

        for module in ("tokenizers", "tiktoken", "transformers", "sentencepiece", "anthropic"):
            assert util.find_spec(module) is None, module

    def test_the_empirical_ratio_is_not_called_exact(self, capacity):
        tokens = capacity["TOKENIZATION"]
        assert tokens["empirical_ratio_classification"] == "EMPIRICAL_LOWER_INFORMATION_BOUND"
        assert tokens["empirical_ratio_use_here"] == "NONE"
        assert "UNDERESTIMATES" in tokens["empirical_ratio_direction_warning"]

    def test_no_unsafe_conversion_was_assumed(self, capacity):
        assert capacity["TOKENIZATION"]["SAFE_TOKEN_BOUND_AVAILABLE"] is False
        assert capacity["DERIVED_MIN_OUTPUT_TOKEN_CAPACITY"] == "NOT_DERIVABLE"
        assert capacity["SELECTED_MAX_OUTPUT_TOKENS"] == "NONE"

    def test_no_round_number_was_chosen(self, capacity):
        text = json.dumps(capacity)
        for arbitrary in ("4096", "8192", "16384", "32768"):
            assert f'"SELECTED_MAX_OUTPUT_TOKENS": {arbitrary}' not in text

    def test_the_provider_limit_is_not_a_schema_proof(self, capacity):
        capability = capacity["PROVIDER_MODEL_CAPABILITY"]
        assert capability["CONFIGURED_OUTPUT_TOKEN_CAPABILITY"] == "NOT_ESTABLISHED"
        assert "adapter default" in capability["why_that_is_not_the_capability"]

    def test_the_adapter_default_is_ours_and_is_named_as_such(self, capacity):
        from sros_llm_gateway.providers.anthropic import AnthropicProvider

        assert AnthropicProvider.max_output_tokens == 4096
        assert "4096" in capacity["PROVIDER_MODEL_CAPABILITY"]["what_is_held"]


# --------------------------------------------------------------- history did not move


class TestHistoryUnchanged:
    def test_v1_0_0_is_still_readable(self):
        """Section 17. A historical output resolves against the contract it was produced under."""
        assert SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION.endswith("@1.0.0")
        assert len(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]) == 20
        assert SECOND_OPPORTUNITY_OUTPUT_SCHEMA is not SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

    def test_a_historical_output_is_not_valid_under_v1_1_0(self):
        """They are different contracts, which is the whole point of versioning one."""
        historical = json.loads(
            (DATA / "opportunity-synthesis-run-v1.1.json").read_text(encoding="utf-8")
        )["model_output"]
        assert schema_violations(historical, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)

    def test_the_versions_differ_everywhere_they_should(self):
        assert SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1.endswith("@1.1.0")
        assert SECOND_OPPORTUNITY_GATE_VERSION_V1_1 != SECOND_OPPORTUNITY_GATE_VERSION
        assert SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1 != SECOND_OPPORTUNITY_PROMPT_VERSION

    def test_the_frozen_prompt_document_was_not_edited(self, prompt_doc):
        frozen = json.loads(PROMPT_V1.read_text(encoding="utf-8"))
        assert frozen["PROMPT_SHA256"] == PROMPT_V1_SHA256
        assert frozen["PROMPT_VERSION"] == "1.0.0"
        assert prompt_doc["PROMPT_SHA256"] != PROMPT_V1_SHA256

    def test_the_system_region_extends_its_predecessor_verbatim(self):
        assert SECOND_OPPORTUNITY_SYSTEM_V1_1.startswith(SECOND_OPPORTUNITY_SYSTEM)
        assert len(SECOND_OPPORTUNITY_SYSTEM_V1_1) > len(SECOND_OPPORTUNITY_SYSTEM)

    def test_the_semantic_evidence_boundaries_were_not_weakened(self):
        """Section 16. Every refusal v1.0.0 could state, v1.1.0 still states."""
        for phrase in (
            "willingness to pay",
            "market demand",
            "product-market fit",
            "INSUFFICIENT_EVIDENCE",
        ):
            assert phrase in SECOND_OPPORTUNITY_SYSTEM_V1_1

    def test_the_ted_representation_did_not_move(self, decision, capacity, prompt_doc):
        for record in (decision, capacity, prompt_doc):
            assert record["TED_REPRESENTATION_SHA256"] == REPRESENTATION_SHA256

    def test_capacity_analysis_v1_was_not_rewritten(self):
        v1 = json.loads(CAPACITY_V1.read_text(encoding="utf-8"))
        assert v1["FINITE_BOUND"] is False
        assert v1["unbounded_path_count"] == 8
        assert v1["PRIMARY_OUTCOME"] == "OUTPUT_SCHEMA_HAS_UNBOUNDED_SERIALIZED_SIZE"


# --------------------------------------------------------------- V1, V2 and the accounting


class TestExecutionState:
    def test_no_v2_packet_exists(self, capacity):
        assert capacity["EXECUTION_PACKET_V2_CREATED"] is False
        assert not PACKET_V2.exists()

    def test_v1_is_consumed_and_its_approval_is_not_reusable(self, capacity):
        v1 = capacity["V1_STATE"]
        assert v1["execution_packet_sha256"] == V1_SHA256
        assert v1["EXECUTION_APPROVAL_CONSUMED"] is True
        assert v1["PREVIOUS_APPROVAL_REUSABLE"] is False
        assert v1["NEW_APPROVAL_REQUIRED_FOR_ANY_FUTURE_EXECUTION"] is True

    def test_the_consumption_record_was_not_reset(self, capacity):
        assert capacity["V1_STATE"]["consumption_record_reset"] is False
        record = json.loads(
            (DATA / "second-opportunity-synthesis-execution-record-v1.json").read_text(
                encoding="utf-8"
            )
        )
        assert record["EXECUTION_APPROVAL_CONSUMED"] is True

    def test_the_frozen_packet_records_no_approval_inside_itself(self):
        packet = json.loads(PACKET_V1.read_text(encoding="utf-8"))
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False
        assert packet["EXECUTION_PACKET_SHA256"] == V1_SHA256

    def test_the_accounting_is_zero(self, capacity):
        assert set(capacity["ACCOUNTING"].values()) == {0}

    def test_this_mission_added_no_dependency(self, capacity):
        assert capacity["ACCOUNTING"]["DEPENDENCIES_INSTALLED"] == 0

    def test_no_module_here_can_reach_a_provider(self):
        """The bounded contract lives in a package that still cannot call a model."""
        import sros_opportunity.schema_validation as module

        source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("sros_llm_gateway", "urllib", "requests", "httpx", "socket"):
            assert forbidden not in source


# --------------------------------------------------------------- the gate refuses


class TestGateRefusals:
    def _mutate(self, gate, record, path, value):
        import copy

        broken = copy.deepcopy(record)
        node = broken
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        return broken

    def test_the_gate_accepts_the_shipped_records(self, gate):
        gate.validate()

    def test_a_finite_claim_over_an_unbounded_schema_is_refused(self, gate, capacity, monkeypatch):
        broken = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
        broken["properties"]["commercial_claims_supported"]["items"].pop("maxLength")
        monkeypatch.setattr(gate, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1", broken)
        with pytest.raises(gate.ValidationError, match="REMAINS_UNBOUNDED"):
            gate._check_the_successor_is_finite(capacity)

    def test_v1_0_0_repaired_in_place_is_refused(self, gate, monkeypatch):
        repaired = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
        monkeypatch.setattr(gate, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA", repaired)
        with pytest.raises(gate.ValidationError, match="edited in place"):
            gate._check_v1_0_0_was_not_edited()

    def test_a_reduced_maxitems_is_refused(self, gate, monkeypatch):
        shrunk = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
        shrunk["properties"]["statement_classifications"]["maxItems"] = 8
        monkeypatch.setattr(gate, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1", shrunk)
        with pytest.raises(gate.ValidationError, match="maxItems moved"):
            gate._check_nothing_was_reduced()

    def test_a_dimension_bound_by_length_is_refused(self, gate, decision, monkeypatch):
        wrong = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
        wrong["properties"]["supported_dimensions"]["items"] = {
            "type": "string",
            "maxLength": 40,
        }
        monkeypatch.setattr(gate, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1", wrong)
        with pytest.raises(gate.ValidationError, match="canonical EvidenceDimension"):
            gate._check_each_bound_matches_its_semantics(decision)

    def test_source_families_frozen_into_an_enum_is_refused(self, gate, decision, monkeypatch):
        wrong = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
        wrong["properties"]["source_families"]["items"] = {
            "type": "string",
            "enum": ["public_procurement"],
            "maxLength": 128,
            "pattern": REGISTRY_SLUG_PATTERN,
        }
        monkeypatch.setattr(gate, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1", wrong)
        with pytest.raises(gate.ValidationError, match="REGISTRY"):
            gate._check_each_bound_matches_its_semantics(decision)

    def test_a_wrong_maximum_is_refused(self, gate, capacity):
        broken = self._mutate(
            gate, capacity, ["MAXIMUM_VALID_INSTANCE", "MAX_VALID_OUTPUT_CHARACTERS"], 1234
        )
        with pytest.raises(gate.ValidationError, match="MAX_VALID_OUTPUT_CHARACTERS"):
            gate._check_the_maximum(broken)

    def test_an_ascii_diagnostic_presented_as_the_maximum_is_refused(self, gate, capacity):
        block = capacity["MAXIMUM_VALID_INSTANCE"]
        broken = self._mutate(
            gate,
            capacity,
            ["MAXIMUM_VALID_INSTANCE", "ASCII_FILL_MAXIMUM_CHARACTERS"],
            block["MAX_VALID_OUTPUT_CHARACTERS"],
        )
        with pytest.raises(gate.ValidationError):
            gate._check_the_maximum(broken)

    def test_a_selected_ceiling_without_a_conversion_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["SELECTED_MAX_OUTPUT_TOKENS"], 8192)
        with pytest.raises(gate.ValidationError, match="cannot be derived"):
            gate._check_no_ceiling_was_invented(broken)

    def test_a_derived_capacity_without_a_conversion_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["DERIVED_MIN_OUTPUT_TOKEN_CAPACITY"], 143000)
        with pytest.raises(gate.ValidationError, match="cannot be derived"):
            gate._check_no_ceiling_was_invented(broken)

    def test_an_exact_count_without_a_tokenizer_is_refused(self, gate, capacity):
        broken = self._mutate(
            gate, capacity, ["TOKENIZATION", "EXACT_MAX_OUTPUT_TOKEN_COUNT"], 77000
        )
        with pytest.raises(gate.ValidationError, match="no exact tokenizer"):
            gate._check_no_ceiling_was_invented(broken)

    def test_using_the_empirical_ratio_is_refused(self, gate, capacity):
        broken = self._mutate(
            gate, capacity, ["TOKENIZATION", "empirical_ratio_use_here"], "DIVIDED_THE_MAXIMUM"
        )
        with pytest.raises(gate.ValidationError, match="unsafe direction"):
            gate._check_no_ceiling_was_invented(broken)

    def test_an_adapter_default_recorded_as_a_capability_is_refused(self, gate, capacity):
        broken = self._mutate(
            gate,
            capacity,
            ["PROVIDER_MODEL_CAPABILITY", "CONFIGURED_OUTPUT_TOKEN_CAPABILITY"],
            4096,
        )
        with pytest.raises(gate.ValidationError, match="capability ceiling"):
            gate._check_no_ceiling_was_invented(broken)

    def test_a_v2_claimed_without_a_ceiling_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["EXECUTION_PACKET_V2_CREATED"], True)
        with pytest.raises(gate.ValidationError, match="V2"):
            gate._check_no_v2(broken)

    def test_a_reset_consumption_record_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["V1_STATE", "consumption_record_reset"], True)
        with pytest.raises(gate.ValidationError, match="reset"):
            gate._check_no_v2(broken)

    def test_a_reused_v1_approval_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["V1_STATE", "PREVIOUS_APPROVAL_REUSABLE"], True)
        with pytest.raises(gate.ValidationError, match="reused"):
            gate._check_no_v2(broken)

    def test_a_guard_that_refuses_every_digest_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["V1_STATE", "guard_permits_a_new_digest"], False)
        with pytest.raises(gate.ValidationError, match="unseen digest"):
            gate._check_no_v2(broken)

    def test_an_unchanged_prompt_digest_is_refused(self, gate, capacity, prompt_doc, decision):
        broken = self._mutate(gate, prompt_doc, ["PROMPT_SHA256"], PROMPT_V1_SHA256)
        with pytest.raises(gate.ValidationError, match="predecessor's digest"):
            gate._check_the_prompt(capacity, broken, decision)

    def test_a_moved_ted_representation_is_refused(self, gate, capacity, prompt_doc, decision):
        broken = self._mutate(gate, capacity, ["TED_REPRESENTATION_SHA256"], "0" * 64)
        with pytest.raises(gate.ValidationError, match="REPRESENTATION_CHANGED"):
            gate._check_the_prompt(broken, prompt_doc, decision)

    def test_a_prompt_recorded_as_sent_is_refused(self, gate, capacity, prompt_doc, decision):
        broken = self._mutate(gate, prompt_doc, ["SENT"], True)
        with pytest.raises(gate.ValidationError, match="transmission"):
            gate._check_the_prompt(capacity, broken, decision)

    def test_changed_research_semantics_are_refused(self, gate, capacity, prompt_doc, decision):
        broken = self._mutate(
            gate, prompt_doc, ["SEMANTIC_DIFF", "research_semantics_changed"], True
        )
        with pytest.raises(gate.ValidationError, match="output-contract"):
            gate._check_the_prompt(capacity, broken, decision)

    def test_an_unversioned_gate_is_refused(self, gate, decision):
        broken = self._mutate(gate, decision, ["SUCCESSOR_GATE"], SECOND_OPPORTUNITY_GATE_VERSION)
        with pytest.raises(gate.ValidationError):
            gate._check_the_decision(broken)

    def test_a_mutated_v1_0_0_admitted_in_the_record_is_refused(self, gate, decision):
        broken = self._mutate(gate, decision, ["V1_0_0_MUTATED_IN_PLACE"], True)
        with pytest.raises(gate.ValidationError, match="mutated in place"):
            gate._check_the_decision(broken)

    def test_revalidating_history_under_v1_1_0_is_refused(self, gate, decision):
        broken = self._mutate(gate, decision, ["HISTORICAL_OUTPUTS_REVALIDATED_UNDER_V1_1_0"], True)
        with pytest.raises(gate.ValidationError, match="section 17"):
            gate._check_the_decision(broken)

    def test_the_failed_response_as_design_evidence_is_refused(self, gate, decision):
        broken = self._mutate(
            gate,
            decision,
            ["THINGS_NOT_DONE", "failed_18_of_20_response_used_as_design_evidence"],
            True,
        )
        with pytest.raises(gate.ValidationError, match="THINGS_NOT_DONE"):
            gate._check_the_decision(broken)

    def test_a_nonzero_accounting_is_refused(self, gate, capacity):
        for key in (
            "MODEL_CALLS",
            "PROVIDER_REQUESTS",
            "NETWORK_REQUESTS",
            "TED_BYTES_TRANSMITTED",
        ):
            broken = self._mutate(gate, capacity, ["ACCOUNTING", key], 1)
            with pytest.raises(gate.ValidationError, match=key):
                gate._check_the_accounting(broken)

    def test_an_unverified_retention_repair_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["RETENTION_REPAIR_VERIFIED"], False)
        with pytest.raises(gate.ValidationError, match="RETENTION_PATH_NOT_READY"):
            gate._check_the_accounting(broken)

    def test_an_unlisted_outcome_is_refused(self, gate, capacity):
        broken = self._mutate(gate, capacity, ["PRIMARY_OUTCOME"], "EVERYTHING_IS_FINE")
        with pytest.raises(gate.ValidationError, match="not an acceptable outcome"):
            gate._check_the_accounting(broken)


# --------------------------------------------------------------- the execution path is untouched


class TestExecutionPathUntouched:
    def test_the_runner_still_makes_exactly_one_gateway_call(self):
        text = RUN_SCRIPT.read_text(encoding="utf-8")
        assert text.count("gateway.complete(") == 1

    def test_the_runner_was_not_repointed_at_v1_1_0(self):
        """Nothing here authorises an execution, so the runner still names the consumed contract."""
        text = RUN_SCRIPT.read_text(encoding="utf-8")
        assert "second_opportunity_prompt_hash_v1_1" not in text
        assert "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1" not in text
