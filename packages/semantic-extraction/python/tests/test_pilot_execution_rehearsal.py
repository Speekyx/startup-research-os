"""Mission 1.85.9. A dress rehearsal of `run_semantic_extraction_evaluation.py --execute` end to end.

Everything is real except three things: the packet is a synthetic READY copy with three synthetic records,
the approval and attempt files live in a pytest temporary directory, and the HTTP transport is scripted. The
real approval gate, provider verification, ceiling preflight, ADR-033 authorization, gateway, strict provider
adapter, validator and retry rule all run. No network is reached and no key is read: the credential is a
placeholder string set by the test, and the compose .env loader is replaced by a no-op.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys
from types import SimpleNamespace

import pytest
from sros_llm_gateway import transport as transport_module
from sros_llm_gateway.transport import HttpResponse
from sros_semantic_extraction_contract import render_question_surface, surface_sha256

REPO = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "infrastructure" / "scripts"


def load_runner():
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "rehearsal_run_semantic_extraction_evaluation",
        SCRIPTS / "run_semantic_extraction_evaluation.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tool_response(payload: dict | None, stop_reason: str = "tool_use") -> HttpResponse:
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
    return HttpResponse(
        status=200, body=json.dumps(body).encode("utf-8"), headers={"request-id": "req_rehearsal"}
    )


class ScriptedTransport:
    script: list[HttpResponse] = []
    bodies: list[dict] = []
    urls: list[str] = []

    def post_json(self, url, headers, body, timeout_seconds):
        type(self).urls.append(url)
        type(self).bodies.append(body)
        assert headers.get("x-api-key") == "rehearsal-placeholder-not-a-key"
        return type(self).script.pop(0)


@pytest.fixture
def rehearsal(tmp_path, monkeypatch):
    runner = load_runner()
    surfaces = {
        "rehearsal-accepts": render_question_surface(
            "Build fails", "<p>I tried reinstalling the package but it still fails.</p>"
        ),
        "rehearsal-truncated": render_question_surface("Other", "<p>Some body text here.</p>"),
        "rehearsal-retried": render_question_surface("Third", "<p>Short question body.</p>"),
    }
    packet = json.loads(runner.PACKET.read_text("utf-8"))
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
    approval = {
        "packet_id": packet["packet_id"],
        "packet_version": packet["packet_version"],
        "packet_sha256": packet["packet_sha256"],
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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "rehearsal-placeholder-not-a-key")
    monkeypatch.setitem(
        sys.modules,
        "build_semantic_egress_eligibility",
        SimpleNamespace(development_surfaces=lambda: surfaces),
    )
    monkeypatch.setattr(transport_module, "UrllibTransport", ScriptedTransport)
    ScriptedTransport.bodies, ScriptedTransport.urls = [], []
    ScriptedTransport.script = [
        tool_response(
            {
                "extraction_state": "FINDINGS_PRESENT",
                "findings": [
                    {
                        "finding_type": "REPORTED_FAILED_ATTEMPT",
                        "evidence_quote": "I tried reinstalling the package but it still fails.",
                        "evidence_occurrence": 1,
                        "subject_quote": None,
                        "subject_occurrence": None,
                    }
                ],
            }
        ),
        tool_response({"extraction_state": "NO_FINDING_ESTABLISHED"}, stop_reason="max_tokens"),
        tool_response({"findings": []}),
        tool_response({"extraction_state": "ABSTAINED_TEXT_INSUFFICIENT", "findings": []}),
    ]
    digest = hashlib.sha256(approval_path.read_bytes()).hexdigest()
    return runner, tmp_path, digest


def test_a_full_execution_rehearsal_runs_every_real_gate_once(rehearsal) -> None:
    runner, tmp_path, digest = rehearsal
    out = tmp_path / "out"
    assert runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)]) == 0
    assert (tmp_path / "attempt.json").exists()
    run = json.loads(next(out.glob("run-*.json")).read_text("utf-8"))
    assert run["approval_sha256"] == digest
    assert (run["provider"], run["model"]) == ("anthropic", "claude-sonnet-5")
    assert run["calls"] == 4 and run["stopped"] is None and run["canonical_writes"] == 0
    assert set(ScriptedTransport.urls) == {"https://api.anthropic.com/v1/messages"}
    assert all(b["model"] == "claude-sonnet-5" for b in ScriptedTransport.bodies)
    assert all(b["tools"][0].get("strict") is True for b in ScriptedTransport.bodies)
    by_id = {r["normalized_record_id"]: r for r in run["records"]}
    accepted = by_id["rehearsal-accepts"]
    assert accepted["accepted"] is True
    assert accepted["extraction"]["findings"][0]["finding_type"] == "REPORTED_FAILED_ATTEMPT"
    assert accepted["attempts"][0]["transport"][0]["elapsed_seconds"] >= 0
    truncated = by_id["rehearsal-truncated"]
    assert [a["outcome"] for a in truncated["attempts"]] == ["OUTPUT_LIMIT_REACHED"]
    retried = by_id["rehearsal-retried"]
    assert [a["outcome"] for a in retried["attempts"]] == ["SCHEMA_FAILURE", "ACCEPTED"]
    assert [a["retry_number"] for a in retried["attempts"]] == [0, 1]
    assert [a["call_number"] for a in retried["attempts"]] == [3, 4]
    assert len(run["cost"]["charges"]) == 4


def test_a_second_execution_is_refused_before_any_transport(rehearsal) -> None:
    runner, tmp_path, digest = rehearsal
    out = tmp_path / "out"
    assert runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)]) == 0
    ScriptedTransport.urls = []
    with pytest.raises(runner.Refused) as refused:
        runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(out)])
    assert refused.value.refusal == "EVALUATION_APPROVAL_ALREADY_SPENT"
    assert ScriptedTransport.urls == []


def test_an_output_directory_inside_the_repository_is_refused_before_the_credential(
    rehearsal, monkeypatch
) -> None:
    runner, tmp_path, digest = rehearsal
    loaded = []
    monkeypatch.setattr(runner, "_load_compose_env", lambda: loaded.append(True))
    with pytest.raises(runner.Refused) as refused:
        runner.main(["--execute", "--approval-sha256", digest, "--output-dir", str(REPO / "x")])
    assert refused.value.refusal == "OUTPUT_DIRECTORY_INSIDE_THE_REPOSITORY"
    assert loaded == [] and not (tmp_path / "attempt.json").exists()
