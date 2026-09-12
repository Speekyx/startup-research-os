"""Mission 1.84.7, CI gate 71: the V2 execution record against what the one execution kept.

Each case edits a temporary copy of the record, the approval or the response artifact and drives the
whole `validate()`. After every edit the record's pins on the approval and the artifact follow the
copies, so the check that refuses is the one written for the violation and not the file digest in
front of it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import shutil

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_execution_record_v2.py"
)
SECRET_MARKER = "sk-ant-SYNTHETIC-MARKER-0000000000"  # a fixture, not a credential


def _load():
    spec = importlib.util.spec_from_file_location("gate_71_under_test", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _load()
ORIGINAL_MODULE = GATE._module


def _read(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: pathlib.Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def world(tmp_path, monkeypatch):
    for name in ("RECORD", "APPROVAL", "RESPONSE"):
        source = getattr(GATE, name)
        target = tmp_path / source.name
        shutil.copyfile(source, target)
        monkeypatch.setattr(GATE, name, target)
    return tmp_path


def _rebind() -> None:
    record = _read(GATE.RECORD)
    record["OPERATOR_APPROVAL"]["file_sha256"] = _sha(GATE.APPROVAL)
    record["RESPONSE_ARTIFACT"]["file_sha256"] = _sha(GATE.RESPONSE)
    _write(GATE.RECORD, record)


def _edit(which: str, fn) -> None:
    path = {"record": GATE.RECORD, "approval": GATE.APPROVAL, "response": GATE.RESPONSE}[which]
    doc = _read(path)
    fn(doc)
    _write(path, doc)
    _rebind()


def _set(*keys_and_value):
    *keys, value = keys_and_value

    def apply(doc):
        node = doc
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value

    return apply


def _truncate_summary(doc) -> None:
    doc["parsed_output"]["evidence_bound_reasoning_summary"] = doc["parsed_output"][
        "evidence_bound_reasoning_summary"
    ][:900]


# ================================================================== the shipped state


def test_the_shipped_record_validates() -> None:
    GATE.validate()


def test_the_copies_validate_before_anything_is_edited(world) -> None:
    GATE.validate()


def test_the_rendered_page_is_current() -> None:
    assert GATE.main(["--check"]) == 0


def test_the_outcome_is_the_briefs_factual_name_for_a_schema_rejection() -> None:
    record = _read(GATE.RECORD)
    assert record["PRIMARY_OUTCOME"] == "EXECUTION_SCHEMA_REJECTED_NO_RETRY"
    assert GATE.FACTUAL[record["RUNNER_OUTCOME"]] == record["PRIMARY_OUTCOME"]


# ================================================================== refusals


REFUSED = [
    ("two requests", "record", _set("actual_provider_requests", 2)),
    ("a retry", "record", _set("retries", 1)),
    ("a fallback", "record", _set("fallbacks", 1)),
    ("a continuation", "record", _set("continuation_requests", 1)),
    ("a repair call", "record", _set("repair_calls", 1)),
    ("further calls authorised", "record", _set("FURTHER_CALLS_AUTHORIZED_BY_V2", True)),
    ("the approval unspent", "record", _set("EXECUTION_APPROVAL_CONSUMED", False)),
    ("an Opportunity persisted", "record", _set("OPPORTUNITY_PERSISTED", True)),
    ("a canonical mutation", "record", _set("CANONICAL_MUTATIONS", 1)),
    ("a counter moved", "record", _set("CANONICAL_COUNTERS_AFTER", "research.opportunities", 2)),
    (
        "success claimed",
        "record",
        _set("PRIMARY_OUTCOME", "SECOND_OPPORTUNITY_SYNTHESIS_V2_READY_FOR_HUMAN_REVIEW"),
    ),
    ("a review packet for a rejected answer", "record", _set("HUMAN_REVIEW_PACKET", "PRODUCED")),
    ("no human review required", "record", _set("HUMAN_OUTPUT_REVIEW_REQUIRED", False)),
    (
        "stage 6 passed",
        "record",
        _set("VALIDATION_STAGES", "6_semantic_output_gate_v1_1_0", "PASSED"),
    ),
    ("a NOT_REACHED counted", "record", _set("STAGES_PASSED", 5)),
    ("another failed stage", "record", _set("FAILED_STAGE", "6_semantic_output_gate_v1_1_0")),
    ("the violation dropped", "record", _set("SCHEMA_VIOLATIONS", [])),
    ("a limit stop claimed", "record", _set("STOP_REASON", "max_tokens")),
    ("an incomplete completion", "record", _set("PROVIDER_COMPLETION", "OUTPUT_LIMIT_REACHED")),
    ("output understated", "record", _set("ACTUAL_USAGE", "output_tokens", 3000)),
    ("a total that is not the sum", "record", _set("ACTUAL_USAGE", "total_tokens", 12000)),
    ("cost rounded", "record", _set("ACTUAL_COST", "cost_units", 0.057)),
    ("the ceiling as the cost", "record", _set("ACTUAL_COST", "cost_units", 1.303908)),
    ("thinking tokens", "record", _set("THINKING_TOKENS_REPORTED", 12)),
    ("a timeout claimed", "record", _set("TIMED_OUT", True)),
    (
        "the batch route",
        "record",
        _set("ROUTE", "POST https://api.anthropic.com/v1/messages/batches"),
    ),
    ("another model", "record", _set("MODEL", "claude-opus-5")),
    ("adaptive thinking", "record", _set("THINKING_POLICY", "ADAPTIVE")),
    ("no TED bytes", "record", _set("TED_BYTES_SENT", 0)),
    ("a credential recorded", "record", _set("CREDENTIAL_VALUES_RECORDED", True)),
    ("V1 record rewritten", "record", _set("V1_EXECUTION_RECORD_SHA256", "0" * 64)),
    ("another request id", "record", _set("PROVIDER_REQUEST_ID", "req_other")),
    ("a credential shape in a note", "record", _set("human_review_note", SECRET_MARKER)),
    ("a fail-safe claimed", "record", _set("POST_CALL_FALLBACK_USED", True)),
    (
        "the approval names V1",
        "approval",
        _set(
            "EXECUTION_PACKET_SHA256",
            "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92",
        ),
    ),
    ("the approval recorded by 1.84.6", "approval", _set("recorded_by", "mission-1.84.6")),
    (
        "the operator's words edited",
        "approval",
        lambda d: d["operator_statement_lines"].__setitem__(0, "I APPROVE ANYTHING."),
    ),
    (
        "a second request allowed",
        "approval",
        lambda d: d["NOT_AUTHORISED"].remove("any second provider request"),
    ),
    ("persistence authorised", "approval", _set("OPPORTUNITY_PERSISTENCE_AUTHORISED", True)),
    ("two executions authorised", "approval", _set("EXECUTIONS_AUTHORISED", 2)),
    (
        "another approved ceiling",
        "approval",
        _set("APPROVED_EXECUTION", "EXECUTION_COST_CEILING", 2.0),
    ),
    (
        "usage altered in the body",
        "response",
        _set("RAW_PROVIDER_RESPONSE_BODY", "usage", "output_tokens", 3000),
    ),
    ("a second request in the artifact", "response", _set("PROVIDER_REQUESTS_MADE", 2)),
    ("the answer shortened to pass", "response", _truncate_summary),
    (
        "a reasoning block kept",
        "response",
        lambda d: d["RAW_PROVIDER_RESPONSE_BODY"]["content"].append(
            {"type": "thinking", "thinking": "x"}
        ),
    ),
    ("the artifact says persisted", "response", _set("PERSISTED", "OPPORTUNITY")),
]


@pytest.mark.parametrize(("which", "fn"), [c[1:] for c in REFUSED], ids=[c[0] for c in REFUSED])
def test_a_violation_is_refused_through_the_whole_gate(world, which, fn) -> None:
    _edit(which, fn)
    with pytest.raises(GATE.ValidationError):
        GATE.validate()


def test_an_edit_with_no_rebinding_is_refused_by_the_pin(world) -> None:
    doc = _read(GATE.RESPONSE)
    doc["timing"]["elapsed_seconds"] = 1.0
    _write(GATE.RESPONSE, doc)
    with pytest.raises(GATE.ValidationError, match="changed after"):
        GATE.validate()


def test_a_runner_blind_to_v2s_record_is_refused(world, tmp_path, monkeypatch) -> None:
    def blind(name, path):
        module = ORIGINAL_MODULE(name, path)
        if path == GATE.RUNNER:
            module.EXECUTION_RECORD_V2 = tmp_path / "absent.json"
        return module

    monkeypatch.setattr(GATE, "_module", blind)
    with pytest.raises(GATE.ValidationError, match="execute V2 again"):
        GATE.validate()


def test_a_note_reworded_binds_nothing(world) -> None:
    _edit("record", _set("cost_note", "Reworded; a note explains a field and binds nothing"))
    GATE.validate()


@pytest.mark.parametrize("key", ["ACTUAL_USAGE", "ACTUAL_COST"])
def test_not_established_is_refused_by_rule_when_the_response_reports_it(world, key) -> None:
    """The probe's first run: this was caught by a crash, which fails CI and states no reason."""
    _edit("record", _set(key, "NOT_ESTABLISHED"))
    with pytest.raises(GATE.ValidationError, match="genuinely unavailable"):
        GATE.validate()
