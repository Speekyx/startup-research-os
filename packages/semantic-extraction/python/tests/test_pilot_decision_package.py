"""Mission 1.85.7. The final operator decision package, the measured cost model and ceiling enforcement.

No test here reaches a provider. Gateways are scripted, and the committed decisions file is blank: every
filled decision below is a synthetic copy made inside a test and never written to the repository.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import pathlib
import sys
from datetime import date
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
from sros_semantic_extraction.decisions import operator_decision_blockers, provider_blockers
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

    def test_unresolved_decisions_keep_the_packet_blocked(self) -> None:
        assert codes(operator_decision_blockers(PACKAGE, DECISIONS)) == {
            "THRESHOLDS_NOT_AUTHORISED",
            "RETRY_INTERPRETATION_NOT_RATIFIED",
            "COST_CEILING_NOT_ACCEPTED",
        }
        assert PACKET["status"] == "BLOCKED_OPERATOR_DECISIONS"
        assert codes(PACKET["blockers"]) == codes(operator_decision_blockers(PACKAGE, DECISIONS))
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

    def test_the_committed_decisions_are_blank_and_nothing_decided_them(self) -> None:
        assert DECISIONS["decided_by"] is None and DECISIONS["decided_at"] is None
        assert all(d["operator_decision"] is None for d in DECISIONS["A_pilot_thresholds"])
        assert DECISIONS["B_retry"]["operator_decision"] is None
        assert DECISIONS["C_hard_ceiling"]["operator_decision"] is None
        assert DECISIONS["C_hard_ceiling"]["accepted_hard_ceiling_usd"] is None
        assert PACKET["execution_bounds"]["hard_ceiling_usd_approved"] is None
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

    def test_the_committed_packet_cannot_execute_and_no_approval_exists(self, runner) -> None:
        assert runner.verify_packet()["status"] != runner.READY
        assert not runner.APPROVAL.exists() and not runner.ATTEMPT.exists()
        with pytest.raises(runner.Refused) as refused:
            runner.main(["--execute", "--approval-sha256", "0" * 64])
        assert refused.value.refusal == "PACKET_NOT_READY_FOR_APPROVAL"


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
