"""Mission 1.84.7. The V2 runner keeps what arrived even when judging it fails.

Mission 1.84.2 lost its only provider response on an exception path, and the 1.84.6 runner still
judged and rendered the response BEFORE writing anything: an exception in a stage, or a value the
JSON encoder refused, would have lost the bytes of a spent call again. `settle` writes the recording
transport's capture whatever breaks after the call. Synthetic results only: nothing here reaches a
transport, let alone a network.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
RUNNER_PATH = REPO_ROOT / "infrastructure" / "scripts" / "run_second_opportunity_execution_v2.py"
SECRET_MARKER = "sk-ant-SYNTHETIC-MARKER-0000000000"  # a fixture, not a credential


@pytest.fixture(scope="module")
def runner():
    spec = importlib.util.spec_from_file_location("runner_v2_failsafe_under_test", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result(body: dict | str | None = None) -> dict:
    if body is None:
        body = {
            "id": "msg_synthetic",
            "content": [{"type": "text", "text": "synthetic"}],
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 11, "output_tokens": 22},
        }
    text = body if isinstance(body, str) else json.dumps(body)
    return {
        "response": None,
        "failure": None,
        "transport_responses": [
            {"status": 200, "body": text, "headers": {"request-id": "req_synthetic_failsafe"}}
        ],
        "transport_errors": [],
        "telemetry": [],
        "timing": {"started_at": "t0", "finished_at": "t1", "elapsed_seconds": 1.0},
    }


def _boom(*_args, **_kwargs):
    raise RuntimeError(f"a stage crashed while holding {SECRET_MARKER}")


def test_a_crash_while_judging_still_keeps_the_bytes(runner, monkeypatch) -> None:
    monkeypatch.setattr(runner, "validate_execution", _boom)
    report, text = runner.settle(_result(), {})
    artifact = json.loads(text)
    assert report["outcome"] == runner.POST_CALL_FAILURE
    assert artifact["TERMINAL_OUTCOME"] == runner.POST_CALL_FAILURE
    assert artifact["POST_CALL_HANDLING_FAILED"] is True
    assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
    kept = artifact["transport_responses"][0]
    assert kept["body"]["usage"] == {"input_tokens": 11, "output_tokens": 22}
    assert kept["headers"] == {"request-id": "req_synthetic_failsafe"}
    assert artifact["PROVIDER_REQUESTS_MADE"] == 1
    assert artifact["RETRIES"] == 0
    assert artifact["PERSISTED"] == "NOTHING"


def test_the_fallback_redacts_a_credential_shape(runner, monkeypatch) -> None:
    monkeypatch.setattr(runner, "validate_execution", _boom)
    body = {"content": [], "stop_reason": "tool_use", "echo": SECRET_MARKER}
    _, text = runner.settle(_result(body), {})
    assert SECRET_MARKER not in text
    assert "[REDACTED]" in text


def test_the_fallback_strips_a_volunteered_reasoning_block(runner, monkeypatch) -> None:
    monkeypatch.setattr(runner, "validate_execution", _boom)
    body = {
        "content": [{"type": "thinking", "thinking": "hidden"}],
        "stop_reason": "tool_use",
        "reasoning": "hidden",
    }
    _, text = runner.settle(_result(body), {})
    assert "hidden" not in text
    assert json.loads(text)["HIDDEN_REASONING_RETAINED"] is False


def test_an_unparseable_body_is_kept_as_text(runner, monkeypatch) -> None:
    monkeypatch.setattr(runner, "validate_execution", _boom)
    _, text = runner.settle(_result("not json at all"), {})
    assert json.loads(text)["transport_responses"][0]["body"] == "not json at all"


def test_a_render_failure_keeps_the_validation_outcome(runner, monkeypatch) -> None:
    judged = {"outcome": runner.ACCEPTED, "stop_reason": "tool_use", "stages": {}}
    monkeypatch.setattr(runner, "validate_execution", lambda result, context: judged)
    monkeypatch.setattr(runner, "build_artifact", lambda result, report: {"x": object()})
    report, text = runner.settle(_result(), {})
    artifact = json.loads(text)
    assert report is judged
    assert artifact["TERMINAL_OUTCOME"] == runner.ACCEPTED
    assert artifact["POST_CALL_HANDLING_FAILED"] is True
    assert artifact["validation"]["outcome"] == runner.ACCEPTED


def test_the_normal_path_is_unchanged(runner, monkeypatch) -> None:
    judged = {"outcome": runner.ACCEPTED, "stop_reason": "tool_use", "stages": {}}
    monkeypatch.setattr(runner, "validate_execution", lambda result, context: judged)
    monkeypatch.setattr(runner, "build_artifact", lambda result, report: {"TERMINAL_OUTCOME": "X"})
    report, text = runner.settle(_result(), {})
    assert report is judged
    assert json.loads(text) == {"TERMINAL_OUTCOME": "X"}


@pytest.fixture
def wired(runner, tmp_path, monkeypatch):
    """main() with every external step replaced, and a counter on the one call."""
    calls: list[int] = []
    monkeypatch.setattr(
        runner,
        "verify",
        lambda profile: {"findings": {}, "packet_file": {"EXECUTION_PACKET_SHA256": "b" * 64}},
    )
    monkeypatch.setattr(runner, "check_approval", lambda sha: {})
    monkeypatch.setattr(runner, "refuse_if_consumed", lambda sha: None)

    def one_call(context):
        calls.append(1)
        return _result()

    monkeypatch.setattr(runner, "execute", one_call)
    monkeypatch.setattr(runner, "RESPONSE_ARTIFACT", tmp_path / "response-v2.json")
    return calls


def test_main_writes_the_bytes_when_a_stage_crashes(runner, wired, monkeypatch) -> None:
    monkeypatch.setattr(runner, "validate_execution", _boom)
    assert runner.main(["--execute"]) == 2
    assert wired == [1]
    artifact = json.loads(runner.RESPONSE_ARTIFACT.read_text(encoding="utf-8"))
    assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
    assert artifact["TERMINAL_OUTCOME"] == runner.POST_CALL_FAILURE


def test_main_refuses_before_the_call_when_an_artifact_exists(runner, wired) -> None:
    runner.RESPONSE_ARTIFACT.write_text("{}", encoding="utf-8")
    assert runner.main(["--execute"]) == 1
    assert wired == []
