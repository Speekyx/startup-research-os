"""Mission 1.84.7. V2's approval is spent, and the runner refuses its digest by name.

V1's guard reads only the record beside V1, so after the one execution under V2 it could not see
that V2's approval was spent; the runner's `--execute` was stopped only by the response artifact
already existing. The runner now reads V2's execution record too. These tests hold both halves: the
spent digest is refused, and a digest the record does not name is not.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
RUNNER_PATH = REPO_ROOT / "infrastructure" / "scripts" / "run_second_opportunity_execution_v2.py"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"


@pytest.fixture(scope="module")
def runner():
    spec = importlib.util.spec_from_file_location("runner_v2_consumed_under_test", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_spent_v2_digest_is_refused_by_name(runner) -> None:
    with pytest.raises(runner.RefusedError) as caught:
        runner.refuse_if_consumed(V2_SHA256)
    assert caught.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"


def test_an_unseen_digest_is_still_permitted(runner) -> None:
    runner.refuse_if_consumed("c" * 64)


def test_the_guard_reads_the_record_rather_than_refusing_v2_unconditionally(
    runner, tmp_path, monkeypatch
) -> None:
    record = tmp_path / "record-v2.json"
    record.write_text(
        json.dumps({"EXECUTION_APPROVAL_CONSUMED": True, "execution_packet_sha256": "d" * 64}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "EXECUTION_RECORD_V2", record)
    runner.refuse_if_consumed(V2_SHA256)
    with pytest.raises(runner.RefusedError):
        runner.refuse_if_consumed("d" * 64)


def test_a_record_not_marked_consumed_spends_nothing(runner, tmp_path, monkeypatch) -> None:
    record = tmp_path / "record-v2.json"
    record.write_text(
        json.dumps({"EXECUTION_APPROVAL_CONSUMED": False, "execution_packet_sha256": V2_SHA256}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "EXECUTION_RECORD_V2", record)
    runner.refuse_if_consumed(V2_SHA256)


def test_execute_now_refuses_v2_before_any_call(runner, tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        runner,
        "verify",
        lambda profile: {"findings": {}, "packet_file": {"EXECUTION_PACKET_SHA256": V2_SHA256}},
    )
    monkeypatch.setattr(runner, "check_approval", lambda sha: {})
    monkeypatch.setattr(runner, "RESPONSE_ARTIFACT", tmp_path / "absent-response.json")

    def tripwire(context):  # pragma: no cover - must never run
        raise AssertionError("a second execution under a spent approval")

    monkeypatch.setattr(runner, "execute", tripwire)
    assert runner.main(["--execute"]) == 1
    assert "EXECUTION_APPROVAL_ALREADY_CONSUMED" in capsys.readouterr().out
