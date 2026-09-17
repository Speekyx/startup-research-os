"""Mission 1.85.7. The final operator decision package, the measured cost model and ceiling enforcement.

No test here reaches a provider. Gateways are scripted. Since Mission 1.85.8 the committed decisions file holds
the operator's own recorded decisions; every other decision set below (blank, filled or malformed) is a
synthetic copy made inside a test and never written to the repository, and no test creates an approval file
in the repository.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import pathlib
import sys
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sros_llm_gateway.types import SchemaValidationError
from sros_semantic_extraction.cost import (
    CeilingRefusalError,
    CostLedger,
    CostModel,
    Prices,
    call_cost,
    proposed_hard_ceiling,
)
from sros_semantic_extraction.decisions import (
    decision_record_problems,
    operator_decision_blockers,
    provider_blockers,
)
from sros_semantic_extraction_contract import render_question_surface, surface_sha256

REPO = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO / "docs" / "data"
SCRIPTS = REPO / "infrastructure" / "scripts"


def load_json(name: str):
    return json.loads((DATA / name).read_text("utf-8"))


PACKAGE = load_json("semantic-extraction-operator-decision-package-development-v1.json")
DECISIONS = load_json("semantic-extraction-operator-decisions-development-v1.json")
VERIFICATION = load_json("anthropic-claude-sonnet-5-pilot-verification-v1.json")
SIZES = load_json("semantic-extraction-request-size-development-v1.json")
ELIGIBILITY = load_json("stack-overflow-semantic-egress-eligibility-development-v1.json")
PACKET = load_json("semantic-extraction-evaluation-packet-development-v1.json")
PRICES = Prices(Decimal(2), Decimal(10), Decimal("1.1"))


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"n08b_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runner():
    return load_script("run_semantic_extraction_evaluation")


def filled_decisions() -> dict:
    """A synthetic, complete operator decision set. Never written anywhere."""
    decisions = copy.deepcopy(DECISIONS)
    decisions["decided_by"] = "synthetic-test-operator"
    decisions["decided_at"] = "2026-09-17T12:00:00+00:00"
    for item in decisions["A_pilot_thresholds"]:
        item["operator_decision"] = "AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT"
        if "repeatability_disposition" in item:
            item["repeatability_disposition"] = "DEFER_TO_A_LATER_REPEATABILITY_RUN"
    decisions["B_retry"]["operator_decision"] = "RATIFY"
    decisions["C_hard_ceiling"]["operator_decision"] = "ACCEPT"
    decisions["C_hard_ceiling"]["accepted_hard_ceiling_usd"] = PACKAGE["C_hard_ceiling"][
        "proposed_hard_ceiling_usd"
    ]
    return decisions


def blank_decisions() -> dict:
    """The blank decision set the renderer creates, rebuilt in memory. Never written anywhere."""
    renderer = load_script("render_semantic_extraction_decision_package")
    return renderer.blank_decisions(PACKAGE["A_pilot_thresholds"])


def codes(blockers: list[str]) -> set[str]:
    return {b.split(":")[0] for b in blockers}


class TestCostModel:
    def test_cost_is_derived_from_the_exact_approved_set_only(self) -> None:
        approved = set(ELIGIBILITY["approved_record_ids"])
        excluded = {r["normalized_record_id"] for r in ELIGIBILITY["records"]} - approved
        assert len(approved) == 46 and len(excluded) == 4
        measured = {r["normalized_record_id"] for r in SIZES["records"]}
        bounded = set(PACKAGE["C_hard_ceiling"]["per_record_conservative_input_tokens"])
        assert measured == approved == bounded
        assert not (bounded & excluded)
        assert set(PACKET["execution_bounds"]["per_record_conservative_input_tokens"]) == approved

    def test_expected_calls_and_the_retry_maximum_are_distinct(self) -> None:
        ceiling = PACKAGE["C_hard_ceiling"]
        assert ceiling["EXPECTED_CALLS"] == 46
        assert ceiling["MAX_CALLS_WITH_RETRY"] == 92
        assert PACKET["execution_bounds"]["max_calls"] == 92
        assert Decimal(ceiling["retry_worst_case_usd"]) == 2 * Decimal(
            ceiling["conservative_bound_usd"]
        )
        assert Decimal(ceiling["planning_estimate_usd"]) < Decimal(
            ceiling["conservative_bound_usd"]
        )

    def test_the_package_recomputes_from_the_measured_bytes(self) -> None:
        model = CostModel(PRICES, 1_000_000, 4096, 474, 1)
        run = model.run(
            (r["normalized_record_id"], r["request_body_utf8_bytes"]) for r in SIZES["records"]
        )
        ceiling = PACKAGE["C_hard_ceiling"]
        assert (
            str(run.retry_worst_case_usd.quantize(Decimal("0.000001")))
            == ceiling["retry_worst_case_usd"]
        )
        assert str(proposed_hard_ceiling(run)) + ".000000" == ceiling["proposed_hard_ceiling_usd"]
        assert run.per_call_documented_maximum_usd == call_cost(PRICES, 1_000_000, 4096)

    def test_the_old_full_context_bound_is_not_reused(self) -> None:
        ceiling = PACKAGE["C_hard_ceiling"]
        assert ceiling["old_bound_reused"] is False
        proposed = Decimal(ceiling["proposed_hard_ceiling_usd"])
        old = Decimal(ceiling["old_full_context_window_bound_usd"])
        assert proposed != old and proposed < old / 10
        assert (
            Decimal(ceiling["retry_worst_case_usd"])
            + Decimal(ceiling["per_call_documented_maximum_usd"])
            <= proposed
        )
        assert "206.5452" not in json.dumps(PACKET["execution_bounds"])

    def test_the_pricing_source_is_versioned_and_digested(self) -> None:
        pricing = PACKAGE["C_hard_ceiling"]["pricing"]
        path = REPO / pricing["source"]
        assert pricing["source_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert VERIFICATION["version"] == "1.0.0" and VERIFICATION["provider_calls"] == 0
        assert all(
            len(e["sha256"]) == 64 and e["verified_quotes"] for e in VERIFICATION["evidence"]
        )
        assert PACKET["provider"]["verification"]["sha256"] == pricing["source_sha256"]

    def test_unknown_prices_have_no_default(self) -> None:
        with pytest.raises(ValueError):
            Prices(Decimal(0), Decimal(10), Decimal(1))
        with pytest.raises(ValueError):
            Prices(2, Decimal(10), Decimal(1))  # type: ignore[arg-type]


class TestReadinessGates:
    def test_unknown_pricing_blocks_readiness(self) -> None:
        broken = copy.deepcopy(VERIFICATION)
        broken["pricing"]["input_usd_per_mtok"] = None
        assert "PROVIDER_PRICING_NOT_ESTABLISHED" in codes(
            provider_blockers(broken, "claude-sonnet-5")
        )
        assert codes(provider_blockers(None, "claude-sonnet-5")) == {
            "PROVIDER_VERIFICATION_NOT_ESTABLISHED"
        }

    def test_an_unavailable_configured_model_blocks_readiness_and_nothing_is_substituted(
        self,
    ) -> None:
        assert provider_blockers(VERIFICATION, "claude-sonnet-5") == []
        retired = copy.deepcopy(VERIFICATION)
        retired["model"]["documented_state"] = "RETIRED"
        assert "CONFIGURED_MODEL_NOT_AVAILABLE" in codes(
            provider_blockers(retired, "claude-sonnet-5")
        )
        assert "CONFIGURED_MODEL_NOT_VERIFIED" in codes(
            provider_blockers(VERIFICATION, "claude-opus-5")
        )
        renderer = load_script("render_semantic_extraction_packet")
        assert renderer.MODEL == "claude-sonnet-5" == PACKET["provider"]["model"]

    def test_unresolved_decisions_keep_the_packet_blocked(self, tmp_path, monkeypatch) -> None:
        blank = blank_decisions()
        assert codes(operator_decision_blockers(PACKAGE, blank)) == {
            "THRESHOLDS_NOT_AUTHORISED",
            "RETRY_INTERPRETATION_NOT_RATIFIED",
            "COST_CEILING_NOT_ACCEPTED",
        }
        renderer = load_script("render_semantic_extraction_packet")
        path = tmp_path / "blank-decisions.json"
        path.write_text(json.dumps(blank), encoding="utf-8")
        monkeypatch.setattr(renderer, "DECISIONS", path)
        packet = renderer.build()
        assert packet["status"] == "BLOCKED_OPERATOR_DECISIONS"
        assert codes(packet["blockers"]) == codes(operator_decision_blockers(PACKAGE, blank))
        assert packet["execution_bounds"]["hard_ceiling_usd_approved"] is None
        assert operator_decision_blockers(PACKAGE, filled_decisions()) == []

    def test_each_decision_blocks_on_its_own(self) -> None:
        one_threshold = filled_decisions()
        one_threshold["A_pilot_thresholds"][0]["operator_decision"] = None
        assert codes(operator_decision_blockers(PACKAGE, one_threshold)) == {
            "THRESHOLDS_NOT_AUTHORISED"
        }
        retry = filled_decisions()
        retry["B_retry"]["operator_decision"] = None
        assert codes(operator_decision_blockers(PACKAGE, retry)) == {
            "RETRY_INTERPRETATION_NOT_RATIFIED"
        }
        ceiling = filled_decisions()
        ceiling["C_hard_ceiling"]["operator_decision"] = None
        assert codes(operator_decision_blockers(PACKAGE, ceiling)) == {"COST_CEILING_NOT_ACCEPTED"}
        cases = {
            "THRESHOLD_REVISION_PENDING": ("A", "REVISE_BEFORE_THE_PILOT_RUN"),
            "RETRY_POLICY_CHANGE_REQUIRED": ("B", "REJECT"),
            "COST_CEILING_REJECTED": ("C", "REJECT"),
            "COST_CEILING_REVISION_PENDING": ("C", "REVISE"),
        }
        for code, (section, value) in cases.items():
            decisions = filled_decisions()
            if section == "A":
                decisions["A_pilot_thresholds"][1]["operator_decision"] = value
            elif section == "B":
                decisions["B_retry"]["operator_decision"] = value
            else:
                decisions["C_hard_ceiling"]["operator_decision"] = value
            assert code in codes(operator_decision_blockers(PACKAGE, decisions)), code
        mismatch = filled_decisions()
        mismatch["C_hard_ceiling"]["accepted_hard_ceiling_usd"] = "206.5452"
        assert "COST_CEILING_ACCEPTANCE_MISMATCH" in codes(
            operator_decision_blockers(PACKAGE, mismatch)
        )
        unattributed = filled_decisions()
        unattributed["decided_by"] = None
        assert "OPERATOR_DECISIONS_UNATTRIBUTED" in codes(
            operator_decision_blockers(PACKAGE, unattributed)
        )
        rejected = filled_decisions()
        rejected["A_pilot_thresholds"][2]["operator_decision"] = "REJECT_FOR_THE_PILOT"
        assert operator_decision_blockers(PACKAGE, rejected) == []

    def test_the_flip_rate_needs_a_repeatability_disposition_and_the_budget_is_not_doubled(
        self,
    ) -> None:
        item = next(
            i for i in PACKAGE["A_pilot_thresholds"] if i["metric"] == "run_to_run_label_flip_rate"
        )
        assert set(item["repeatability_choices"]) == {
            "DEFER_TO_A_LATER_REPEATABILITY_RUN",
            "AUTHORISE_A_SEPARATELY_APPROVED_SECOND_RUN_LATER",
            "REJECT_FOR_THIS_FIRST_PILOT",
        }
        decisions = filled_decisions()
        for d in decisions["A_pilot_thresholds"]:
            if "repeatability_disposition" in d:
                d["repeatability_disposition"] = None
        assert "REPEATABILITY_DISPOSITION_MISSING" in codes(
            operator_decision_blockers(PACKAGE, decisions)
        )
        assert PACKAGE["C_hard_ceiling"]["MAX_CALLS_WITH_RETRY"] == 92

    def test_the_committed_decisions_are_exactly_the_operators(self) -> None:
        # Mission 1.85.8: the operator's explicit decisions, recorded as given.
        by_id = {d["item_id"]: d for d in DECISIONS["A_pilot_thresholds"]}
        flip = by_id.pop("run_to_run_label_flip_rate::each extractable label")
        assert len(by_id) == 9
        assert all(
            d["operator_decision"] == "AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT" for d in by_id.values()
        )
        assert all(d["revised_value"] is None for d in DECISIONS["A_pilot_thresholds"])
        assert flip["operator_decision"] == "REJECT_FOR_THE_PILOT"
        assert flip["repeatability_disposition"] == "REJECT_FOR_THIS_FIRST_PILOT"
        assert "Do not run additional model calls" in flip["operator_note"]
        assert DECISIONS["B_retry"] == {
            "operator_decision": "RATIFY",
            "revised_reading": None,
            "operator_note": DECISIONS["B_retry"]["operator_note"],
        }
        assert DECISIONS["C_hard_ceiling"]["operator_decision"] == "ACCEPT"
        assert DECISIONS["C_hard_ceiling"]["accepted_hard_ceiling_usd"] == "9.000000"
        assert DECISIONS["C_hard_ceiling"]["revised_hard_ceiling_usd"] is None
        assert DECISIONS["decided_by"] == "operator-a"
        assert datetime.fromisoformat(DECISIONS["decided_at"]).utcoffset() is not None
        assert decision_record_problems(PACKAGE, DECISIONS) == []
        assert operator_decision_blockers(PACKAGE, DECISIONS) == []
        assert PACKET["execution_bounds"]["hard_ceiling_usd_approved"] == "9.000000"
        assert (
            PACKAGE["decision_state"]["decisions_sha256"]
            == PACKET["operator_decisions"]["decisions_sha256"]
        )
        composition = PACKAGE["reference_composition_on_approved_records"]
        assert composition["NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"]["PRESENT"] == 0
        assert composition["REPORTED_FAILED_ATTEMPT"] == {
            "PRESENT": 15,
            "ABSENT": 29,
            "UNCERTAIN": 2,
        }


class TestLedger:
    def test_preflight_refuses_a_ceiling_below_the_bounded_run(self) -> None:
        maximum = call_cost(PRICES, 1_000_000, 4096)
        with pytest.raises(CeilingRefusalError) as refused:
            CostLedger(PRICES, Decimal(2), maximum).preflight(Decimal("0.1"))
        assert refused.value.code == "CEILING_BELOW_ONE_DOCUMENTED_MAXIMUM_CALL"
        with pytest.raises(CeilingRefusalError) as refused:
            CostLedger(PRICES, Decimal(8), maximum).preflight(Decimal("6.065972"))
        assert refused.value.code == "CEILING_BELOW_BOUNDED_RUN_COST"
        CostLedger(PRICES, Decimal(9), maximum).preflight(Decimal("6.065972"))

    def test_no_call_starts_if_it_could_cross_the_ceiling(self) -> None:
        maximum = call_cost(PRICES, 1_000_000, 4096)
        ledger = CostLedger(PRICES, Decimal(5), maximum)
        ledger.authorise_next_call()
        ledger.charge_unknown()
        ledger.authorise_next_call()
        ledger.charge_usage(10_000, 4096)
        ledger.authorise_next_call()
        ledger.charge_unknown()
        with pytest.raises(CeilingRefusalError) as refused:
            ledger.authorise_next_call()
        assert refused.value.code == "COST_CEILING_WOULD_BE_CROSSED"
        assert ledger.spent_usd <= Decimal(5)
        assert [c["basis"] for c in ledger.charges] == [
            "NO_REPORTED_USAGE_CHARGED_AT_DOCUMENTED_MAXIMUM",
            "REPORTED_USAGE",
            "NO_REPORTED_USAGE_CHARGED_AT_DOCUMENTED_MAXIMUM",
        ]


class UsageGateway:
    """Scripted gateway recording what a transport would: stop_reason, and usage when a 200 carries it."""

    def __init__(self, recorder, script):
        self.recorder, self.script, self.calls = recorder, list(script), 0

    def complete(self, request):
        self.calls += 1
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        entry = {"status": 200, "request_id": "req", "body_sha256": "x", "stop_reason": "tool_use"}
        if "usage" in item:
            entry["usage"] = item["usage"]
        self.recorder.responses.append(entry)
        return SimpleNamespace(structured=item.get("payload"))


NO_FINDING = {"extraction_state": "NO_FINDING_ESTABLISHED", "findings": []}


class TestRunnerEnforcement:
    def _packet(self, runner, surfaces: dict[str, str], ceiling: str, retry_worst: str = "0.1"):
        packet = json.loads(runner.PACKET.read_text("utf-8"))
        packet["status"] = runner.READY
        packet["selection"]["records"] = [
            {
                "normalized_record_id": rid,
                "surface_sha256": surface_sha256(surface),
                "surface_length": len(surface),
                "egress_state": "EGRESS_APPROVED",
            }
            for rid, surface in surfaces.items()
        ]
        packet["selection"]["egress_approved_record_ids"] = list(surfaces)
        bounds = packet["execution_bounds"]
        bounds["hard_ceiling_usd_approved"] = ceiling
        bounds["retry_worst_case_usd"] = retry_worst
        bounds["per_record_conservative_input_tokens"] = {rid: 5000 for rid in surfaces}
        bounds["max_calls"] = 2 * len(surfaces)
        return packet

    def surfaces(self, n: int) -> dict[str, str]:
        return {
            f"r-{i}": render_question_surface(f"Question {i}", f"<p>Body number {i} here.</p>")
            for i in range(n)
        }

    def test_the_committed_packet_has_no_accepted_ceiling_and_cannot_run(
        self, runner, tmp_path
    ) -> None:
        packet = self._packet(runner, self.surfaces(1), None)  # type: ignore[arg-type]
        with pytest.raises(runner.Refused) as refused:
            runner.execute(
                packet,
                self.surfaces(1),
                UsageGateway(None, []),
                runner.RecordingTransport(None),
                tmp_path / "o",
                workspace_id="w",
            )
        assert refused.value.refusal == "COST_CEILING_NOT_ACCEPTED"

    def test_preflight_refuses_before_any_call(self, runner, tmp_path) -> None:
        surfaces = self.surfaces(1)
        packet = self._packet(runner, surfaces, "8.000000", retry_worst="6.065972")
        recorder = runner.RecordingTransport(inner=None)
        gateway = UsageGateway(recorder, [])
        with pytest.raises(runner.Refused) as refused:
            runner.execute(packet, surfaces, gateway, recorder, tmp_path / "o", workspace_id="w")
        assert refused.value.refusal == "CEILING_BELOW_BOUNDED_RUN_COST"
        assert gateway.calls == 0

    def test_the_run_stops_before_a_call_that_could_cross_the_ceiling(
        self, runner, tmp_path
    ) -> None:
        surfaces = self.surfaces(2)
        packet = self._packet(runner, surfaces, "5.000000")
        recorder = runner.RecordingTransport(inner=None)
        gateway = UsageGateway(
            recorder,
            [SchemaValidationError("a"), SchemaValidationError("b"), {"payload": NO_FINDING}],
        )
        with pytest.raises(runner.Refused) as refused:
            runner.execute(packet, surfaces, gateway, recorder, tmp_path / "o", workspace_id="w")
        assert refused.value.refusal == "COST_CEILING_WOULD_BE_CROSSED"
        assert gateway.calls == 2
        [written] = list((tmp_path / "o").glob("run-*.json"))
        run = json.loads(written.read_text("utf-8"))
        assert run["stopped"] == "COST_CEILING_WOULD_BE_CROSSED"
        assert Decimal(run["cost"]["spent_usd"]) <= Decimal("5")

    def test_reported_usage_is_charged_and_a_run_within_bounds_completes(
        self, runner, tmp_path
    ) -> None:
        surfaces = self.surfaces(2)
        packet = self._packet(runner, surfaces, "9.000000")
        recorder = runner.RecordingTransport(inner=None)
        usage = {"input_tokens": 1500, "output_tokens": 200}
        gateway = UsageGateway(
            recorder,
            [{"payload": NO_FINDING, "usage": usage}, {"payload": NO_FINDING, "usage": usage}],
        )
        run = runner.execute(packet, surfaces, gateway, recorder, tmp_path / "o", workspace_id="w")
        assert run["stopped"] is None and gateway.calls == 2
        assert Decimal(run["cost"]["spent_usd"]) == 2 * call_cost(PRICES, 1500, 200)

    def test_input_above_the_conservative_bound_stops_the_run(self, runner, tmp_path) -> None:
        surfaces = self.surfaces(2)
        packet = self._packet(runner, surfaces, "9.000000")
        recorder = runner.RecordingTransport(inner=None)
        gateway = UsageGateway(
            recorder,
            [
                {"payload": NO_FINDING, "usage": {"input_tokens": 50_000, "output_tokens": 10}},
                {"payload": NO_FINDING},
            ],
        )
        with pytest.raises(runner.Refused) as refused:
            runner.execute(packet, surfaces, gateway, recorder, tmp_path / "o", workspace_id="w")
        assert refused.value.refusal == "CONSERVATIVE_INPUT_BOUND_EXCEEDED"
        assert gateway.calls == 1

    def test_provider_verification_expires(self, runner) -> None:
        runner.check_provider_verification(PACKET, date(2026, 9, 17))
        with pytest.raises(runner.Refused) as refused:
            runner.check_provider_verification(PACKET, date(2027, 6, 1))
        assert refused.value.refusal == "PROVIDER_VERIFICATION_EXPIRED"

    def test_the_committed_packet_cannot_execute_and_no_approval_exists(
        self, runner, monkeypatch
    ) -> None:
        import os

        from sros_llm_gateway import transport

        class KeyTripwire(dict):
            def get(self, key, default=None):
                assert key != "ANTHROPIC_API_KEY", "the runner read the API key"
                return super().get(key, default)

            def __getitem__(self, key):
                assert key != "ANTHROPIC_API_KEY", "the runner read the API key"
                return super().__getitem__(key)

        def no_transport(*args, **kwargs):
            raise AssertionError("a transport was built")

        monkeypatch.setattr(os, "environ", KeyTripwire(os.environ))
        monkeypatch.setattr(transport.UrllibTransport, "__init__", no_transport)
        assert runner.verify_packet()["status"] == runner.READY
        assert not runner.APPROVAL.exists() and not runner.ATTEMPT.exists()
        with pytest.raises(runner.Refused) as refused:
            runner.main(["--execute"])
        assert refused.value.refusal == "APPROVAL_SHA256_NOT_SUPPLIED"
        with pytest.raises(runner.Refused) as refused:
            runner.main(["--execute", "--approval-sha256", "0" * 64])
        assert refused.value.refusal == "OPERATOR_APPROVAL_NOT_RECORDED"
        assert not runner.APPROVAL.exists() and not runner.ATTEMPT.exists()


class TestNoProviderCallAndNoApproval:
    NEW = (
        "measure_semantic_extraction_request_sizes.py",
        "render_semantic_extraction_decision_package.py",
        "render_semantic_extraction_packet.py",
    )

    def test_the_new_scripts_build_no_transport_and_count_no_tokens(self) -> None:
        for name in self.NEW:
            source = (SCRIPTS / name).read_text("utf-8")
            tree = ast.parse(source)
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            imported = {
                a.name
                for n in ast.walk(tree)
                if isinstance(n, ast.ImportFrom | ast.Import)
                for a in n.names
            }
            assert "UrllibTransport" not in names | imported, name
            assert "count_tokens" not in source, name
            if (
                name != "render_semantic_extraction_packet.py"
            ):  # the packet names the file it requires
                assert "semantic-extraction-evaluation-approval" not in source, name

    def test_the_decision_package_is_current_and_never_rewrites_decisions(self) -> None:
        renderer = load_script("render_semantic_extraction_decision_package")
        before = renderer.DECISIONS.read_bytes()
        package, created = renderer.build()
        assert created is None
        assert renderer.dump(package) == renderer.PACKAGE.read_bytes()
        assert renderer.DECISIONS.read_bytes() == before


PREVIOUS_PACKET_SHA256 = "63c7302d64d52aa49e56060de1a2d92ffdb8e2030e9c19ba550acba0cc357993"


def approval_for(packet: dict, **overrides) -> dict:
    approval = {
        "packet_id": packet["packet_id"],
        "packet_version": packet["packet_version"],
        "packet_sha256": packet["packet_sha256"],
        "decision": "APPROVE_EXACTLY_ONE_EVALUATION_RUN",
        "approved_by": "synthetic-test-operator",
        "operator_statement": "synthetic approval inside a test, never written to the repository",
        "accepts_hard_ceiling_usd": True,
        "accepts_retention_bound": True,
        "accepts_retry_interpretation": True,
        "accepted_hard_ceiling_usd": packet["execution_bounds"]["hard_ceiling_usd_approved"],
        "accepted_reference_strength": packet["reference"]["REFERENCE_STRENGTH"],
    }
    approval.update(overrides)
    return approval


def _item(decisions: dict, metric: str) -> dict:
    return next(d for d in decisions["A_pilot_thresholds"] if d["item_id"].startswith(metric))


def _set_item(metric: str, key: str, value):
    def change(decisions: dict) -> None:
        _item(decisions, metric)[key] = value

    return change


def _set(section: str | None, key: str, value):
    def change(decisions: dict) -> None:
        (decisions[section] if section else decisions)[key] = value

    return change


class TestRecordedDecisionsAndFrozenPacket:
    """Mission 1.85.8. The recorded decisions are validated strictly, the packet is READY only because every
    gate is satisfied, and only an approval naming the exact new digest could pass the approval gate."""

    def test_a_malformed_decision_record_is_refused_not_repaired(self) -> None:
        flip = "run_to_run_label_flip_rate"
        cases = {
            "REVISE_WITHOUT_REVISED_VALUE": _set_item(
                "validator_acceptance_rate", "operator_decision", "REVISE_BEFORE_THE_PILOT_RUN"
            ),
            "REVISED_VALUE_WITHOUT_REVISE": _set_item(
                "validator_acceptance_rate", "revised_value", 0.9
            ),
            "UNSUPPORTED_THRESHOLD_DECISION": _set_item("recall", "operator_decision", "APPROVE"),
            "REPEATABILITY_DISPOSITION_CONTRADICTS_REJECT": _set_item(
                flip, "repeatability_disposition", "DEFER_TO_A_LATER_REPEATABILITY_RUN"
            ),
            "REPEATABILITY_DISPOSITION_MISSING": _set_item(flip, "repeatability_disposition", None),
            "REPEATABILITY_DISPOSITION_ON_ANOTHER_ITEM": _set_item(
                "recall", "repeatability_disposition", "REJECT_FOR_THIS_FIRST_PILOT"
            ),
            "DECIDED_AT_NOT_TIMEZONE_AWARE": _set(None, "decided_at", "2026-09-17T15:37:35"),
            "DECIDED_BY_MISSING": _set(None, "decided_by", " "),
            "CEILING_ACCEPTANCE_IS_NOT_THE_PROPOSED_CEILING": _set(
                "C_hard_ceiling", "accepted_hard_ceiling_usd", 9.0
            ),
            "RETRY_REVISE_WITHOUT_REVISED_READING": _set("B_retry", "operator_decision", "REVISE"),
            "UNSUPPORTED_RETRY_DECISION": _set("B_retry", "operator_decision", "OK"),
        }
        for code, change in cases.items():
            decisions = copy.deepcopy(DECISIONS)
            change(decisions)
            assert code in codes(decision_record_problems(PACKAGE, decisions)), code
            assert "OPERATOR_DECISIONS_INVALID" in codes(
                operator_decision_blockers(PACKAGE, decisions)
            ), code
        old = copy.deepcopy(DECISIONS)
        old["C_hard_ceiling"]["accepted_hard_ceiling_usd"] = "206.5452"
        assert "CEILING_ACCEPTANCE_IS_NOT_THE_PROPOSED_CEILING" in codes(
            decision_record_problems(PACKAGE, old)
        )

    def test_nine_thresholds_authorised_and_the_flip_rate_needs_no_other_run(self) -> None:
        decisions = PACKET["operator_decisions"]
        assert len(decisions["thresholds_authorised"]) == 9
        assert decisions["thresholds_rejected_for_the_pilot"] == [
            "run_to_run_label_flip_rate::each extractable label"
        ]
        assert decisions["additional_repeatability_runs_authorised"] == 0
        bounds = PACKET["execution_bounds"]
        assert bounds["EXPECTED_CALLS"] == 46 and bounds["MAX_CALLS_WITH_RETRY"] == 92
        assert bounds["max_calls"] == 92
        assert len(PACKET["selection"]["egress_approved_record_ids"]) == 46
        assert len(PACKET["selection"]["egress_excluded_record_ids"]) == 4

    def test_the_retry_policy_is_ratified_and_bound_by_digest(self) -> None:
        renderer = load_script("render_semantic_extraction_packet")
        policy = PACKET["retry_policy"]
        assert policy["operator_decision"] == "RATIFY"
        assert policy["max_schema_retries_per_record"] == 1
        assert policy["provider_fallback"] is None and policy["model_fallback"] is None
        rule = {
            k: policy[k]
            for k in (
                "max_schema_retries_per_record",
                "reading",
                "inside_the_retry_class",
                "outside_the_retry_class",
                "implemented_as",
            )
        }
        assert policy["rule_sha256"] == renderer.canonical_sha(rule)
        assert (
            policy["implementation_sha256"]
            == hashlib.sha256(renderer.RETRY_IMPLEMENTATION.read_bytes()).hexdigest()
        )
        assert PACKET["operator_decisions"]["threshold_decisions_sha256"] == renderer.canonical_sha(
            PACKET["operator_decisions"]["threshold_decisions"]
        )

    def test_ready_only_when_every_other_gate_is_satisfied(self, tmp_path, monkeypatch) -> None:
        assert PACKET["status"] == "READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL"
        assert PACKET["blockers"] == []
        renderer = load_script("render_semantic_extraction_packet")
        unpriced = copy.deepcopy(VERIFICATION)
        unpriced["pricing"]["output_usd_per_mtok"] = None
        path = tmp_path / "verification.json"
        path.write_text(json.dumps(unpriced), encoding="utf-8")
        monkeypatch.setattr(renderer, "VERIFICATION", path)
        packet = renderer.build()
        assert packet["status"] == "BLOCKED_OPERATOR_DECISIONS"
        assert "PROVIDER_PRICING_NOT_ESTABLISHED" in codes(packet["blockers"])

    def test_any_bound_artifact_change_changes_the_digest(self, tmp_path, monkeypatch) -> None:
        renderer = load_script("render_semantic_extraction_packet")
        assert renderer.build()["packet_sha256"] == PACKET["packet_sha256"]
        changed = copy.deepcopy(DECISIONS)
        changed["decided_at"] = "2026-09-17T15:37:36+04:00"
        path = tmp_path / "decisions.json"
        path.write_text(json.dumps(changed), encoding="utf-8")
        monkeypatch.setattr(renderer, "DECISIONS", path)
        assert renderer.build()["packet_sha256"] != PACKET["packet_sha256"]
        monkeypatch.undo()
        implementation = tmp_path / "request.py"
        implementation.write_bytes(renderer.RETRY_IMPLEMENTATION.read_bytes() + b"\n")
        monkeypatch.setattr(renderer, "RETRY_IMPLEMENTATION", implementation)
        assert renderer.build()["packet_sha256"] != PACKET["packet_sha256"]

    def test_an_approval_for_the_previous_digest_is_invalid(self, runner, tmp_path) -> None:
        packet = runner.verify_packet()
        assert packet["packet_sha256"] != PREVIOUS_PACKET_SHA256
        assert packet["packet_sha256"] == runner.EXPECTED_PACKET_SHA256
        for stale in (
            approval_for(packet, packet_sha256=PREVIOUS_PACKET_SHA256, packet_version=3),
            approval_for(packet, packet_sha256=PREVIOUS_PACKET_SHA256),
            approval_for(packet, packet_version=3),
        ):
            path = tmp_path / "stale-approval.json"
            path.write_text(json.dumps(stale), encoding="utf-8")
            with pytest.raises(runner.Refused) as refused:
                runner.check_approval(packet, path, hashlib.sha256(path.read_bytes()).hexdigest())
            assert refused.value.refusal == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"

    def test_only_an_approval_naming_the_exact_ready_digest_passes_the_gate(
        self, runner, tmp_path
    ) -> None:
        packet = runner.verify_packet()
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(approval_for(packet)), encoding="utf-8")
        approval = runner.check_approval(
            packet, path, hashlib.sha256(path.read_bytes()).hexdigest()
        )
        assert approval["packet_sha256"] == packet["packet_sha256"]
        wrong = tmp_path / "wrong-ceiling.json"
        wrong.write_text(
            json.dumps(approval_for(packet, accepted_hard_ceiling_usd="206.5452")), encoding="utf-8"
        )
        with pytest.raises(runner.Refused) as refused:
            runner.check_approval(packet, wrong, hashlib.sha256(wrong.read_bytes()).hexdigest())
        assert refused.value.refusal == "OPERATOR_APPROVAL_INCOMPLETE"
        assert not runner.APPROVAL.exists() and not runner.ATTEMPT.exists()

    def test_merging_grants_no_execution_authority(self, runner) -> None:
        packet = runner.verify_packet()
        assert packet["operator_approval_recorded"] is False
        assert packet["approval_requirements"]["merge_is_not_approval"] is True
        assert "packet_sha256" in packet["approval_requirements"]["must_name"]
        assert not runner.APPROVAL.exists() and not runner.ATTEMPT.exists()
        assert not any(DATA.glob("semantic-extraction-evaluation-approval*"))
