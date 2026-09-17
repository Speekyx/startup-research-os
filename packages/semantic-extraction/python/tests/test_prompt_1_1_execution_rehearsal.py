"""Mission 1.85.12. Pre-execution rehearsal of the packet v5 (prompt 1.1.0) run, before any approval exists.

It drives `run_semantic_extraction_evaluation.py --execute` end to end on the committed v5 packet's own bounds
(price, documented per-call maximum, $9 ceiling), with synthetic records and a scripted transport. Where a
network failure matters, the scripted transport hands the call to the REAL `UrllibTransport` with `urlopen`
replaced, so the reset wrapping and the whole-request deadline of PR #185 run as they will in the real run.

Nothing here reaches a provider or reads a key: the credential is a placeholder and the compose .env loader is
a no-op. It asserts the current semantics and changes none of them.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys
import time
import urllib.request
from types import SimpleNamespace

import pytest
from sros_llm_gateway import transport as transport_module
from sros_llm_gateway.transport import HttpResponse
from sros_semantic_extraction_contract import render_question_surface, surface_sha256

REPO = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "infrastructure" / "scripts"
V4_PACKET_SHA256 = "5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e"
V5_PACKET_SHA256 = "6b27bccbc22c7051be9d8f1df4dd22a4635d0f664d4b4fa05ede820e90a72a7e"
PLACEHOLDER_KEY = "rehearsal-placeholder-not-a-key"
QUOTE = "I tried reinstalling the package but it still fails."


def load_runner():
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "v5_rehearsal_run_semantic_extraction_evaluation",
        SCRIPTS / "run_semantic_extraction_evaluation.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ok(payload: dict | None, stop_reason: str = "tool_use") -> HttpResponse:
    content = (
        [{"type": "tool_use", "name": "emit_structured_output", "input": payload}]
        if payload is not None
        else []
    )
    body = {
        "content": content,
        "stop_reason": stop_reason,
        "usage": {"input_tokens": 900, "output_tokens": 60},
    }
    return HttpResponse(status=200, body=json.dumps(body).encode(), headers={"request-id": "req_r"})


ACCEPTED = {
    "extraction_state": "FINDINGS_PRESENT",
    "findings": [
        {
            "finding_type": "REPORTED_FAILED_ATTEMPT",
            "evidence_quote": QUOTE,
            "evidence_occurrence": 1,
            "subject_quote": None,
            "subject_occurrence": None,
        }
    ],
}


class Scripted:
    """Each entry is an HttpResponse, or 'RESET' / 'STALL', which hand the call to the real transport."""

    script: list = []
    urls: list[str] = []
    real_calls = 0

    def post_json(self, url, headers, body, timeout_seconds):
        assert headers.get("x-api-key") == PLACEHOLDER_KEY
        type(self).urls.append(url)
        step = type(self).script.pop(0)
        if isinstance(step, HttpResponse):
            return step
        type(self).real_calls += 1
        return REAL_TRANSPORT.post_json(url, headers, body, timeout_seconds)


REAL_TRANSPORT = transport_module.UrllibTransport()


def build(runner, tmp_path, monkeypatch, surfaces, script, *, approval_packet_sha=None):
    packet = json.loads(runner.PACKET.read_text("utf-8"))
    assert packet["packet_sha256"] == V5_PACKET_SHA256
    packet["selection"]["records"] = [
        {
            "normalized_record_id": rid,
            "surface_sha256": surface_sha256(text),
            "surface_length": len(text),
            "egress_state": "EGRESS_APPROVED",
        }
        for rid, text in surfaces.items()
    ]
    packet["selection"]["egress_approved_record_ids"] = list(surfaces)
    bounds = packet["execution_bounds"]
    bounds["per_record_conservative_input_tokens"] = {rid: 5000 for rid in surfaces}
    bounds["max_calls"] = 2 * len(surfaces)
    bounds["retry_worst_case_usd"] = "0.100000"
    bounds["timeout_seconds"] = 0.3
    approval = {
        "packet_id": packet["packet_id"],
        "packet_version": packet["packet_version"],
        "packet_sha256": approval_packet_sha or packet["packet_sha256"],
        "decision": runner.APPROVAL_DECISION,
        "approved_by": "rehearsal",
        "operator_statement": "synthetic rehearsal approval in a temporary directory",
        "accepts_hard_ceiling_usd": True,
        "accepts_retention_bound": True,
        "accepts_retry_interpretation": True,
        "accepted_hard_ceiling_usd": bounds["hard_ceiling_usd_approved"],
        "accepted_reference_strength": "SINGLE_HUMAN_REFERENCE",
        "approved_provider": "anthropic",
        "approved_model": "claude-sonnet-5",
        "approved_record_count": len(surfaces),
        "approval_scope": runner.APPROVAL_SCOPE,
    }
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(json.dumps(approval), encoding="utf-8")
    monkeypatch.setattr(runner, "APPROVAL", approval_path)
    monkeypatch.setattr(runner, "ATTEMPT", tmp_path / "attempt.json")
    monkeypatch.setattr(runner, "verify_packet", lambda: packet)
    monkeypatch.setattr(runner, "_load_compose_env", lambda: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", PLACEHOLDER_KEY)
    monkeypatch.setitem(
        sys.modules,
        "build_semantic_egress_eligibility",
        SimpleNamespace(development_surfaces=lambda: surfaces),
    )
    monkeypatch.setattr(transport_module, "UrllibTransport", Scripted)

    def fake_urlopen(request, timeout=None):
        step = FAILURES.pop(0)
        if step == "STALL":
            time.sleep(2.0)
        raise ConnectionResetError(10054, "rehearsal reset")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    FAILURES.clear()
    FAILURES.extend(s for s in script if isinstance(s, str))
    Scripted.script, Scripted.urls, Scripted.real_calls = list(script), [], 0
    return hashlib.sha256(approval_path.read_bytes()).hexdigest()


FAILURES: list[str] = []


def surface(title: str, body: str) -> str:
    return render_question_surface(title, f"<p>{body}</p>")


def test_network_and_provider_failures_cost_one_record_each_and_never_a_schema_retry(
    tmp_path, monkeypatch
) -> None:
    runner = load_runner()
    surfaces = {
        "r1-accepted": surface("Build fails", QUOTE),
        "r2-reset": surface("Two", "Some body text here."),
        "r3-stall": surface("Three", "More body text here."),
        "r4-schema-retry": surface("Four", QUOTE),
        "r5-http-529": surface("Five", "Last body text here."),
    }
    script = [
        ok(ACCEPTED),
        "RESET",
        "STALL",
        ok({"findings": []}),
        ok(ACCEPTED),
        HttpResponse(status=529, body=b'{"type":"error"}', headers={"request-id": "req_e"}),
    ]
    digest = build(runner, tmp_path, monkeypatch, surfaces, script)
    out = tmp_path / "out"
    started = time.monotonic()
    assert runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)]) == 0
    assert time.monotonic() - started < 10, "the stalled call outlived its whole-request deadline"
    run = json.loads(next(out.glob("run-*.json")).read_text("utf-8"))
    by_id = {r["normalized_record_id"]: r for r in run["records"]}
    outcomes = {rid: [a["outcome"] for a in r["attempts"]] for rid, r in by_id.items()}
    assert outcomes == {
        "r1-accepted": ["ACCEPTED"],
        "r2-reset": ["PROVIDER_ERROR"],
        "r3-stall": ["PROVIDER_ERROR"],
        "r4-schema-retry": ["SCHEMA_FAILURE", "ACCEPTED"],
        "r5-http-529": ["PROVIDER_ERROR"],
    }
    # The reset and the stall were classified by the gateway hierarchy, not stopped as unexpected.
    assert by_id["r2-reset"]["attempts"][0]["error"]["class"] == "ProviderTemporaryError"
    assert by_id["r3-stall"]["attempts"][0]["error"]["class"] == "ProviderTimeoutError"
    assert by_id["r2-reset"]["attempts"][0]["transport"][0]["transport_error"] == "TransportError"
    assert by_id["r3-stall"]["attempts"][0]["transport"][0]["transport_error"] == "TimeoutError"
    assert by_id["r3-stall"]["attempts"][0]["transport"][0]["elapsed_seconds"] < 2.0
    # A record-level failure spends nothing of another record's retry.
    assert [a["retry_number"] for a in by_id["r4-schema-retry"]["attempts"]] == [0, 1]
    assert run["calls"] == 6 and run["stopped"] is None and Scripted.real_calls == 2
    assert Scripted.script == [] and FAILURES == []
    # No fallback: one route, one model, one provider, and the failures cost the documented maximum each.
    assert set(Scripted.urls) == {"https://api.anthropic.com/v1/messages"}
    bases = [c["basis"] for c in run["cost"]["charges"]]
    assert bases.count("NO_REPORTED_USAGE_CHARGED_AT_DOCUMENTED_MAXIMUM") == 3
    assert bases.count("REPORTED_USAGE") == 3
    assert run["cost"]["accepted_hard_ceiling_usd"] == "9.000000"


def test_the_ceiling_stops_the_run_before_a_call_that_could_cross_it(tmp_path, monkeypatch) -> None:
    runner = load_runner()
    surfaces = {f"r{i}": surface(f"Title {i}", f"Body text number {i}.") for i in range(1, 6)}
    digest = build(runner, tmp_path, monkeypatch, surfaces, ["RESET"] * 4)
    out = tmp_path / "out"
    with pytest.raises(runner.Refused) as refused:
        runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)])
    assert refused.value.refusal == "COST_CEILING_WOULD_BE_CROSSED"
    run = json.loads(next(out.glob("run-*.json")).read_text("utf-8"))
    # 4 x 2.245056 = 8.980224 was allowed (<= 9); the 5th call would have crossed and was never sent.
    assert run["calls"] == 4 and len(Scripted.urls) == 4
    assert run["stopped"] == "COST_CEILING_WOULD_BE_CROSSED"
    assert run["cost"]["spent_usd"] == "8.980224"


def test_the_spent_v4_approval_and_a_spent_v5_approval_unlock_nothing(
    tmp_path, monkeypatch
) -> None:
    runner = load_runner()
    surfaces = {"r1": surface("Build fails", QUOTE)}
    digest = build(
        runner,
        tmp_path,
        monkeypatch,
        surfaces,
        [ok(ACCEPTED)],
        approval_packet_sha=V4_PACKET_SHA256,
    )
    out = tmp_path / "out"
    with pytest.raises(runner.Refused) as refused:
        runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)])
    assert refused.value.refusal == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"
    assert Scripted.urls == [] and not (tmp_path / "attempt.json").exists()

    digest = build(runner, tmp_path, monkeypatch, surfaces, [ok(ACCEPTED)])
    assert runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)]) == 0
    Scripted.urls = []
    with pytest.raises(runner.Refused) as refused:
        runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)])
    assert refused.value.refusal == "EVALUATION_APPROVAL_ALREADY_SPENT"
    assert Scripted.urls == []


def test_the_committed_v5_packet_is_what_the_rehearsal_rehearses() -> None:
    runner = load_runner()
    packet = runner.verify_packet()
    assert packet["packet_sha256"] == V5_PACKET_SHA256 == runner.EXPECTED_PACKET_SHA256
    assert packet["prompt"]["version"] == "1.1.0"
    assert packet["provider"]["fallback_provider"] is None
    assert packet["retry_policy"]["model_fallback"] is None
    assert packet["execution_bounds"]["transport_retries"] == 0
