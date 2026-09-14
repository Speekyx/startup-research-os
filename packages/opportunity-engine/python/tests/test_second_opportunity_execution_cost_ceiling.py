"""Mission 1.84.20. CI gate 94: the execution cost ceiling and V7's supersession, and the refusals
they must make.

The record and the supersession are built once. Every refusal feeds one of the gate's checks a deep
copy with one field changed, so nothing committed is touched and each refusal is attributed to the
rule that makes it. The V7 runner's guard is exercised with its transport tripwired. Nothing here
reaches a network.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
from decimal import Decimal
from typing import Any

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "infrastructure" / "scripts"
V7_SHA256 = "51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8"
SUPERSEDED = "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
CONSUMED = "EXECUTION_APPROVAL_ALREADY_CONSUMED"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_94_under_test", SCRIPTS / "render_second_opportunity_execution_cost_ceiling.py"
    )


@pytest.fixture(scope="module")
def record(gate) -> dict[str, Any]:
    return json.loads(gate.RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def supersession(gate) -> dict[str, Any]:
    return json.loads(gate.SUPERSESSION.read_text(encoding="utf-8"))


def _changed(doc: dict[str, Any], change) -> dict[str, Any]:
    mutated = copy.deepcopy(doc)
    change(mutated)
    return mutated


def _row(doc: dict[str, Any], category: str) -> dict[str, Any]:
    return next(r for r in doc["COST_CATEGORIES"] if r["category"] == category)


class TestTheCommittedRecords:
    def test_the_records_validate(self, gate):
        record, supersession = gate.validate()
        assert record["PRIMARY_OUTCOME"] == gate.READY
        assert supersession["STATUS"] == "SUPERSEDED_BEFORE_EXECUTION"

    def test_the_page_is_the_rendering(self, gate, record, supersession):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(record, supersession)

    def test_the_hard_ceiling(self, record):
        block = record["COST_RECORD"]
        assert block["MAX_BILLABLE_INPUT_TOKENS"] == 1000000
        assert block["OUTPUT_TOKEN_HARD_MAXIMUM"] == 128000
        assert block["DATA_RESIDENCY_MULTIPLIER"] == "1.1"
        assert block["HARD_INPUT_COST_CEILING"] == "2.2"
        assert block["HARD_OUTPUT_COST_CEILING"] == "1.408"
        assert block["HARD_EXECUTION_COST_CEILING"] == "3.608"
        assert block["HARD_EXECUTION_COST_CEILING_PROVEN"] is True
        assert block["UNKNOWN_COST_CATEGORIES"] == []

    def test_the_estimate_is_kept_and_named_for_what_it_is(self, record):
        block = record["COST_RECORD"]
        assert block["REQUEST_BODY_CHARACTERS"] == 31326
        assert block["BODY_BASED_INPUT_TOKEN_ESTIMATE"] == 18158
        assert block["PLANNING_INPUT_COST_ESTIMATE"] == "0.036316"
        assert block["PLANNING_COST_ESTIMATE"] == "1.316316"
        assert block["PLANNING_COST_ESTIMATE_CLASSIFICATION"] == "PLANNING_ESTIMATE"
        assert block["PLANNING_COST_ESTIMATE_IS_NOT"] == ["WORST_CASE", "CEILING"]

    def test_the_provider_facts_the_brief_asks_for(self, record):
        facts = record["PROVIDER_FACTS"]
        assert facts["MODEL_CONTEXT_WINDOW_TOKENS"]["value"] == 1000000
        assert facts["MAX_BILLABLE_INPUT_TOKENS"]["value"] == 1000000
        assert facts["STRICT_INTERNAL_PROMPT_TOKENS"]["value"] == "NOT_ESTABLISHED"
        assert facts["STRICT_INTERNAL_PROMPT_INCLUDED_IN_CONTEXT_BOUND"]["value"] is True
        assert facts["STRICT_INTERNAL_PROMPT_INCLUDED_IN_BILLABLE_USAGE"]["value"] is True
        assert facts["CACHE_BILLING_APPLICABLE"]["value"] is False

    def test_v7_is_reclassified_and_superseded(self, record, supersession):
        assert record["V7_COST_NUMBER_CLASSIFICATION"] == "ESTIMATE_NOT_PROVEN_HARD_CEILING"
        assert record["V7_EXECUTION_COST_CEILING_PROVEN"] is False
        assert record["V7_APPROVAL_AUTHORISED"] is False
        for key in ("V7_EXECUTED", "V7_APPROVED", "V7_APPROVAL_CONSUMED"):
            assert supersession[key] is False
        assert supersession["REASON"] == "COST_CEILING_SEMANTICS_NOT_PROVEN"
        assert supersession["REFUSAL_OUTCOME"] == SUPERSEDED

    def test_twelve_first_party_pages_and_no_provider_request(self, record):
        assert len(record["DOCUMENTATION_EVIDENCE"]) == 12
        assert all(row["first_party"] for row in record["DOCUMENTATION_EVIDENCE"])
        accounting = record["ACCOUNTING"]
        assert accounting["DOCUMENTATION_REQUESTS"] == 12
        for key in (
            "MODEL_CALLS",
            "PROVIDER_REQUESTS",
            "TOKEN_COUNT_API_REQUESTS",
            "TED_BYTES_SENT",
        ):
            assert accounting[key] == 0

    def test_the_decimal_helpers(self, gate):
        assert gate.decimal_text(Decimal("2.2000")) == "2.2"
        assert gate.decimal_text(Decimal("1000")) == "1000"
        assert gate.tokens_from_form("1M tokens") == 1000000
        assert gate.tokens_from_form("128K tokens") == 128000


class TestTerminology:
    def test_the_estimate_called_the_ceiling_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["COST_RECORD"].__setitem__("HARD_EXECUTION_COST_CEILING", "1.316316"),
        )
        with pytest.raises(gate.ValidationError, match="ESTIMATE_CALLED_HARD_CEILING"):
            gate._check_terminology(mutated)

    def test_the_planning_figure_labelled_a_bound_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["COST_RECORD"].__setitem__(
                "PLANNING_COST_ESTIMATE_CLASSIFICATION", "CEILING"
            ),
        )
        with pytest.raises(gate.ValidationError, match="ESTIMATE_CALLED_HARD_CEILING"):
            gate._check_terminology(mutated)

    def test_a_terminology_that_stops_keeping_them_apart_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["TERMINOLOGY"].__setitem__("ESTIMATE_IS_NOT_A_CEILING", False)
        )
        with pytest.raises(gate.ValidationError, match="ESTIMATE_CALLED_HARD_CEILING"):
            gate._check_terminology(mutated)


class TestProviderFacts:
    def test_an_invented_context_window_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["PROVIDER_FACTS"]["MODEL_CONTEXT_WINDOW_TOKENS"].__setitem__(
                "value", 2000000
            ),
        )
        with pytest.raises(gate.ValidationError, match="CONTEXT_WINDOW_INVENTED"):
            gate._check_facts(mutated)

    def test_a_context_window_the_quotes_do_not_state_is_refused(self, gate, record):
        def invent(d):
            fact = d["PROVIDER_FACTS"]["MODEL_CONTEXT_WINDOW_TOKENS"]
            fact["documented_form"] = "2M tokens"
            fact["value"] = 2000000

        with pytest.raises(gate.ValidationError, match="CONTEXT_WINDOW_INVENTED"):
            gate._check_facts(_changed(record, invent))

    def test_a_fact_resting_on_nothing_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["PROVIDER_FACTS"]["MAX_BILLABLE_INPUT_TOKENS"].__setitem__("rests_on", []),
        )
        with pytest.raises(gate.ValidationError, match="rests on no quoted proposition"):
            gate._check_propositions(mutated)

    def test_a_page_that_is_not_first_party_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["DOCUMENTATION_EVIDENCE"][0].__setitem__("first_party", False)
        )
        with pytest.raises(gate.ValidationError, match="first-party"):
            gate._check_propositions(mutated)

    @pytest.mark.parametrize("value", [0, 474, "COVERED_BY_THE_ESTIMATE"])
    def test_unknown_strict_tokens_said_known_are_refused(self, gate, record, value):
        mutated = _changed(
            record,
            lambda d: d["PROVIDER_FACTS"]["STRICT_INTERNAL_PROMPT_TOKENS"].__setitem__(
                "value", value
            ),
        )
        with pytest.raises(gate.ValidationError, match="UNKNOWN_STRICT_TOKENS_SAID_COVERED"):
            gate._check_facts(mutated)

    def test_the_estimate_said_to_cover_the_strict_prompt_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["COST_RECORD"].__setitem__(
                "BODY_BASED_ESTIMATE_COVERS_THE_STRICT_PROMPT", True
            ),
        )
        with pytest.raises(gate.ValidationError, match="UNKNOWN_STRICT_TOKENS_SAID_COVERED"):
            gate._check_facts(mutated)

    def test_the_strict_prompt_placed_outside_the_bound_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["PROVIDER_FACTS"][
                "STRICT_INTERNAL_PROMPT_INCLUDED_IN_CONTEXT_BOUND"
            ].__setitem__("value", "NOT_ESTABLISHED"),
        )
        with pytest.raises(
            gate.ValidationError, match="STRICT_INTERNAL_PROMPT_INCLUDED_IN_CONTEXT_BOUND"
        ):
            gate._check_facts(mutated)

    def test_a_held_price_the_pages_do_not_state_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["COST_RECORD"]["PRICE_PER_1K"].__setitem__("input", 0.003)
        )
        with pytest.raises(gate.ValidationError, match="MODEL_COST_BASIS_CHANGED"):
            gate._check_facts(mutated)

    def test_the_timeout_risk_accepted_here_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["STRICT_FIRST_REQUEST_TIMEOUT"].__setitem__(
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8", True
            ),
        )
        with pytest.raises(gate.ValidationError, match="STRICT_FIRST_REQUEST_TIMEOUT_RISK"):
            gate._check_facts(mutated)


class TestEveryBillingCategory:
    @pytest.mark.parametrize(
        "category",
        ["DATA_RESIDENCY_US_ONLY", "PROMPT_CACHE_WRITE_1H", "STRICT_SCHEMA_COMPILATION_FEE"],
    )
    def test_a_category_dropped_is_refused(self, gate, record, category):
        mutated = _changed(
            record,
            lambda d: d.__setitem__(
                "COST_CATEGORIES", [r for r in d["COST_CATEGORIES"] if r["category"] != category]
            ),
        )
        with pytest.raises(gate.ValidationError, match="UNDOCUMENTED_BILLING_CATEGORY_IGNORED"):
            gate._check_categories(mutated)

    def test_a_cache_charge_ignored_while_caching_is_on_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["REQUEST_BODY_BILLING_SELECTORS"].__setitem__("cache_control", True)
        )
        with pytest.raises(gate.ValidationError, match="CACHE_OR_BILLING_CHARGE_IGNORED"):
            gate._check_categories(mutated)

    def test_the_residency_multiplier_called_inapplicable_is_refused(self, gate, record):
        def drop(d):
            row = _row(d, "DATA_RESIDENCY_US_ONLY")
            row["disposition"] = gate.NOT_APPLICABLE
            row.pop("request_selector")

        with pytest.raises(gate.ValidationError, match="UNDOCUMENTED_BILLING_CATEGORY_IGNORED"):
            gate._check_categories(_changed(record, drop))

    def test_the_residency_multiplier_dropped_from_the_arithmetic_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["COST_RECORD"].__setitem__("DATA_RESIDENCY_MULTIPLIER", "1")
        )
        with pytest.raises(gate.ValidationError, match="data-residency multiplier"):
            gate._check_categories(mutated)

    def test_an_unbounded_category_under_a_proven_ceiling_is_refused(self, gate, record):
        def unbound(d):
            _row(d, "STRICT_SCHEMA_COMPILATION_FEE")["disposition"] = gate.UNBOUNDED
            d["COST_RECORD"]["UNKNOWN_COST_CATEGORIES"] = ["STRICT_SCHEMA_COMPILATION_FEE"]

        with pytest.raises(
            gate.ValidationError, match="TRUE_EXECUTION_COST_CEILING_NOT_ESTABLISHED"
        ):
            gate._check_categories(_changed(record, unbound))

    def test_an_unknown_category_list_that_hides_one_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: _row(d, "STRICT_SCHEMA_COMPILATION_FEE").__setitem__(
                "disposition", gate.UNBOUNDED
            ),
        )
        with pytest.raises(gate.ValidationError, match="UNKNOWN_COST_CATEGORIES"):
            gate._check_categories(mutated)


class TestTheArithmetic:
    def test_the_body_based_estimate_as_the_input_bound_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["COST_RECORD"].__setitem__("MAX_BILLABLE_INPUT_TOKENS", 18158)
        )
        with pytest.raises(gate.ValidationError, match="body-based estimate"):
            gate._check_arithmetic(mutated)

    @pytest.mark.parametrize("tokens", [12903, 11599, 12899])
    def test_an_input_bound_taken_from_observed_usage_is_refused(self, gate, record, tokens):
        mutated = _changed(
            record, lambda d: d["COST_RECORD"].__setitem__("MAX_BILLABLE_INPUT_TOKENS", tokens)
        )
        with pytest.raises(gate.ValidationError, match="earlier call reported"):
            gate._check_arithmetic(mutated)

    def test_a_ceiling_replaced_by_an_incurred_cost_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["COST_RECORD"].__setitem__("HARD_EXECUTION_COST_CEILING", "0.062176"),
        )
        with pytest.raises(gate.ValidationError, match="earlier call incurred"):
            gate._check_arithmetic(mutated)

    def test_a_ceiling_the_derivation_does_not_give_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["COST_RECORD"].__setitem__("HARD_EXECUTION_COST_CEILING", "3.28")
        )
        with pytest.raises(gate.ValidationError, match="derivation gives 3.608"):
            gate._check_arithmetic(mutated)

    def test_observed_usage_used_for_the_ceiling_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["OBSERVED_USAGE_NOT_USED"].__setitem__("USED_FOR_THE_HARD_CEILING", True),
        )
        with pytest.raises(gate.ValidationError, match="earlier call reported"):
            gate._check_arithmetic(mutated)

    def test_a_ceiling_not_proven_is_refused(self, gate, record):
        mutated = _changed(
            record,
            lambda d: d["COST_RECORD"].__setitem__("HARD_EXECUTION_COST_CEILING_PROVEN", False),
        )
        with pytest.raises(
            gate.ValidationError, match="TRUE_EXECUTION_COST_CEILING_NOT_ESTABLISHED"
        ):
            gate._check_arithmetic(mutated)


class TestV7:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("approval_recorded", True),
            ("packet_execution_cost_ceiling", 3.608),
            ("strict_mode_injected_system_prompt_tokens", 0),
            ("request_body_characters", 31967),
        ],
    )
    def test_a_v7_reconfirmation_edited_is_refused(self, gate, record, key, value):
        mutated = _changed(record, lambda d: d["V7_COST_RECONFIRMATION"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_v7(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("V7_COST_NUMBER_CLASSIFICATION", "HARD_CEILING"),
            ("V7_EXECUTION_COST_CEILING_PROVEN", True),
            ("V7_APPROVAL_AUTHORISED", True),
        ],
    )
    def test_v7s_figure_called_a_proven_ceiling_is_refused(self, gate, record, key, value):
        mutated = _changed(record, lambda d: d.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match="ESTIMATE_CALLED_HARD_CEILING"):
            gate._check_v7(mutated)

    def test_a_provider_billing_error_is_not_the_defect(self, gate, record):
        mutated = _changed(
            record, lambda d: d["DEFECT"].__setitem__("not_a_provider_billing_error", False)
        )
        with pytest.raises(gate.ValidationError, match="accounting"):
            gate._check_v7(mutated)


class TestTheSupersession:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("STATUS", "CONSUMED"),
            ("STATUS", "FAILED"),
            ("STATUS", "REJECTED_BY_PROVIDER"),
            ("V7_EXECUTED", True),
            ("V7_APPROVED", True),
            ("V7_APPROVAL_CONSUMED", True),
            ("REFUSAL_OUTCOME", CONSUMED),
            ("REASON", "PROVIDER_REFUSED"),
            ("SUPERSEDED_EXECUTION_PACKET_SHA256", "0" * 64),
            ("COST_CEILING_RECORD_SHA256", "0" * 64),
        ],
    )
    def test_a_misrecorded_supersession_is_refused(self, gate, record, supersession, key, value):
        mutated = _changed(supersession, lambda d: d.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match="V7_SUPERSESSION_MISRECORDED"):
            gate._check_supersession(mutated, record)

    def test_an_approval_of_v7_is_refused(self, gate, tmp_path, monkeypatch):
        forged = tmp_path / "approval-v7.json"
        forged.write_text(json.dumps({"EXECUTION_PACKET_SHA256": V7_SHA256}), encoding="utf-8")
        monkeypatch.setattr(gate, "APPROVAL_V7", forged)
        with pytest.raises(gate.ValidationError, match="V7_APPROVAL_FABRICATED"):
            gate._check_live_v7()

    @pytest.mark.parametrize("name", ["RECORD_V7", "RESPONSE_V7"])
    def test_an_execution_of_v7_on_disk_is_refused(self, gate, tmp_path, monkeypatch, name):
        artifact = tmp_path / f"{name.lower()}.json"
        artifact.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(gate, name, artifact)
        with pytest.raises(gate.ValidationError, match="V7_EXECUTED"):
            gate._check_live_v7()

    def test_an_edited_v7_packet_is_refused(self, gate, tmp_path, monkeypatch):
        edited = tmp_path / "packet-v7.json"
        edited.write_bytes(gate.PACKET_V7.read_bytes().replace(b"1.316316", b"3.608000", 1))
        monkeypatch.setattr(gate, "PACKET_V7", edited)
        with pytest.raises(gate.ValidationError, match="packet V7 was edited"):
            gate._check_live_v7()


class TestTheV7Guard:
    @pytest.fixture
    def runner_v7(self, gate):
        return gate.runner_v7()

    def test_v7_is_refused_as_superseded(self, runner_v7):
        with pytest.raises(runner_v7.RefusedError) as refusal:
            runner_v7.refuse_if_consumed(V7_SHA256)
        assert refusal.value.code == SUPERSEDED

    def test_v1_to_v6_are_still_refused_as_consumed(self, gate, runner_v7):
        for digest in gate.SHAS:
            with pytest.raises(runner_v7.RefusedError) as refusal:
                runner_v7.refuse_if_consumed(digest)
            assert refusal.value.code == CONSUMED

    def test_an_unseen_digest_is_not_refused(self, runner_v7):
        runner_v7.refuse_if_consumed("0" * 64)

    def test_v7_is_refused_before_its_approval_and_any_transport(
        self, runner_v7, tmp_path, monkeypatch
    ):
        import sros_llm_gateway.transport as transport_module

        forged = tmp_path / "approval-v7.json"
        forged.write_text(
            json.dumps(
                {
                    "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V7",
                    "EXECUTION_PACKET_VERSION": 7,
                    "EXECUTION_PACKET_SHA256": V7_SHA256,
                    "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
                    "approved_by": "nobody",
                    "operator_statement": "forged, for a test",
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner_v7, "APPROVAL_FILE", forged)
        built: list[int] = []
        original = transport_module.UrllibTransport.__init__

        def tripwire(self, *a, **k):  # pragma: no cover - must never run
            built.append(1)
            return original(self, *a, **k)

        monkeypatch.setattr(transport_module.UrllibTransport, "__init__", tripwire)
        with pytest.raises(runner_v7.RefusedError) as refusal:
            runner_v7.execute(
                {"packet_file": {"EXECUTION_PACKET_SHA256": V7_SHA256}, "parts": None}
            )
        assert refusal.value.code == SUPERSEDED
        assert built == []

    def test_without_its_record_the_guard_would_let_v7_through(
        self, runner_v7, tmp_path, monkeypatch
    ):
        """Which is why gate 94 requires the record to exist and to be what it derives."""
        monkeypatch.setattr(runner_v7, "SUPERSESSION_RECORD", tmp_path / "absent.json")
        runner_v7.refuse_if_consumed(V7_SHA256)

    def test_a_removed_guard_is_refused(self, gate, monkeypatch):
        honest = gate.runner_v7

        def unguarded():
            module = honest()
            module.refuse_if_superseded = lambda digest: None
            return module

        monkeypatch.setattr(gate, "runner_v7", unguarded)
        with pytest.raises(gate.ValidationError, match="V7_STILL_EXECUTABLE"):
            gate._check_v7_guard()

    def test_a_guard_that_calls_v7_consumed_is_refused(self, gate, monkeypatch):
        honest = gate.runner_v7

        def renaming():
            module = honest()

            def renamed(digest):
                raise module.RefusedError(CONSUMED, "renamed")

            module.refuse_if_superseded = renamed
            return module

        monkeypatch.setattr(gate, "runner_v7", renaming)
        with pytest.raises(gate.ValidationError, match="never had an approval to spend"):
            gate._check_v7_guard()


class TestAccounting:
    @pytest.mark.parametrize(
        "key",
        ["MODEL_CALLS", "PROVIDER_REQUESTS", "MESSAGES_API_REQUESTS", "TOKEN_COUNT_API_REQUESTS"],
    )
    def test_a_provider_request_made_while_preparing_is_refused(self, gate, record, key):
        mutated = _changed(record, lambda d: d["ACCOUNTING"].__setitem__(key, 1))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_accounting(mutated)
