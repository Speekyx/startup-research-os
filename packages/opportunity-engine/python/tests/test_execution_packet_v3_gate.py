"""Mission 1.84.8, CI gate 73: execution packet V3 against V2, the alignment record and live code.

Each case edits a temporary copy of the packet, recomputes its digest so the check that refuses is
the one written for the violation and not the digest guard in front of it, and lets the runner's
pinned digest follow the copy. The runner cases edit the runner's source in memory or wrap the
loaded runner, because a runner that would execute a spent digest, or refuse an unseen one, is a
defect of the runner and not of the packet.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_execution_packet_v3.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("gate_73_under_test", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _load()
ORIGINAL_MODULE = GATE._module
RUNNER_SOURCE = GATE.RUNNER.read_text(encoding="utf-8")
ZERO = "0" * 64


def _read(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: pathlib.Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _pinned(wrap=None):
    def module_with_pin(name, path):
        module = ORIGINAL_MODULE(name, path)
        if path == GATE.RUNNER:
            digest = _read(GATE.PACKET)["EXECUTION_PACKET_SHA256"]
            module.EXPECTED = {**module.EXPECTED, "EXECUTION_PACKET_SHA256": digest}
            if wrap is not None:
                wrap(module)
        return module

    return module_with_pin


@pytest.fixture
def world(tmp_path, monkeypatch):
    """The packet copied aside, the runner's pin following the copy's digest."""
    target = tmp_path / GATE.PACKET.name
    shutil.copyfile(GATE.PACKET, target)
    monkeypatch.setattr(GATE, "PACKET", target)
    monkeypatch.setattr(GATE, "APPROVAL", tmp_path / GATE.APPROVAL.name)
    monkeypatch.setattr(GATE, "_module", _pinned())
    return tmp_path


def _edit(fn) -> None:
    packet = _read(GATE.PACKET)
    fn(packet)
    packet["EXECUTION_PACKET_SHA256"] = GATE.packet_digest(packet)
    _write(GATE.PACKET, packet)


def _set(*keys_and_value):
    *keys, value = keys_and_value

    def apply(doc):
        node = doc
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value

    return apply


def _swap(first: int, second: int):
    def apply(doc):
        stages = list(doc["VALIDATION_STAGES"])
        stages[first], stages[second] = stages[second], stages[first]
        doc["VALIDATION_STAGES"] = stages

    return apply


def _approval(recorded_by: str, digest: str) -> None:
    _write(GATE.APPROVAL, {"EXECUTION_PACKET_SHA256": digest, "recorded_by": recorded_by})


# ================================================================== the shipped state


def test_the_shipped_packet_validates() -> None:
    GATE.validate()


def test_the_rendered_page_is_current() -> None:
    assert GATE.main(["--check"]) == 0


def test_the_copies_validate_before_anything_is_edited(world) -> None:
    GATE.validate()


def test_the_body_grew_by_exactly_the_system_region() -> None:
    packet = _read(GATE.PACKET)
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    assert basis["wire_characters"] == basis["v2_wire_characters"] + GATE.system_region_delta()


# ================================================================== refusals


REFUSED = [
    ("schema changed", _set("SCHEMA_CHANGED", True)),
    ("gate changed", _set("GATE_CHANGED", True)),
    ("schema v1.2.0", _set("OUTPUT_SCHEMA_VERSION", "second-opportunity-synthesis-output@1.2.0")),
    ("the V2 prompt", _set("PROMPT_VERSION", "1.1.0")),
    (
        "V2's prompt digest",
        _set("PROMPT_SHA256", "2f60c61f63cda410b9f60e3eafd9676f983e7ff0220245c03c88136511ac7e82"),
    ),
    ("the prompt recorded as unchanged", _set("PROMPT_CHANGED", False)),
    ("another model", _set("MODEL_ID", "claude-opus-5")),
    (
        "the batch route",
        _set("PROVIDER_ROUTE_SURFACE", "POST https://api.anthropic.com/v1/messages/batches"),
    ),
    ("a beta header", _set("BETA_HEADERS", ["message-batches-2024-09-24"])),
    ("the subscription route", _set("PROVIDER_ID", "anthropic-claude-subscription")),
    ("thinking enabled", _set("ADAPTER_PARAMETERS", "thinking", "ADAPTIVE")),
    ("max_tokens 64000", _set("MAX_OUTPUT_TOKENS", 64000)),
    ("max_tokens sized to V2's 3914", _set("MAX_OUTPUT_TOKENS", 3914)),
    (
        "V2's output tokens allowed to size the envelope",
        lambda d: d["MAX_OUTPUT_TOKENS_NOT_BASED_ON"].remove("V2_OBSERVED_OUTPUT_TOKENS"),
    ),
    ("a retry", _set("MAX_RETRIES", 1)),
    ("a retry in the request", _set("GENERATION_PARAMETERS", "max_retries", 2)),
    ("a continuation", _set("CONTINUATION_REQUESTS", True)),
    ("two calls", _set("MAX_MODEL_CALLS", 2)),
    ("a repair model", _set("REPAIR_MODEL", True)),
    ("the representation moved", _set("REPRESENTATION_SHA256", ZERO)),
    ("V2 unconsumed", _set("PREDECESSOR_APPROVAL_CONSUMED", False)),
    ("V2's approval reusable", _set("PREVIOUS_APPROVAL_REUSABLE", True)),
    ("V3 marked approved", _set("OPERATOR_EXECUTION_APPROVAL_RECORDED", True)),
    (
        "V2's outcome rewritten",
        _set(
            "PREDECESSOR_EXECUTION_OUTCOME",
            "SECOND_OPPORTUNITY_SYNTHESIS_V2_READY_FOR_HUMAN_REVIEW",
        ),
    ),
    ("V2 dropped from the spent list", lambda d: d["CONSUMED_EXECUTION_PACKETS"].pop()),
    ("truncation permitted", _set("OUTPUT_POST_PROCESSING", "TRUNCATION", True)),
    ("rewriting permitted", _set("OUTPUT_POST_PROCESSING", "REWRITING", True)),
    ("the timeout raised", _set("REQUEST_TIMEOUT", 120.0)),
    ("V2's elapsed time used", _set("TIMEOUT", "V2_OBSERVATION_USED_TO_CHANGE_THE_TIMEOUT", True)),
    ("the ceiling doubled", _set("EXECUTION_COST_CEILING", 2.6113)),
    ("V2's ceiling copied", _set("EXECUTION_COST_CEILING", 1.303908)),
    ("the input estimate", _set("INPUT_TOKEN_ESTIMATE", 11954)),
    (
        "V2's usage reduced the envelope",
        _set("V2_OBSERVATION", "USED_TO_REDUCE_MAX_OUTPUT_TOKENS", True),
    ),
    (
        "the limit not fail-closed",
        _set("PROVIDER_COMPLETION_POLICY", "PROVIDER_LIMIT_FAIL_CLOSED", False),
    ),
    (
        "max_tokens read as complete",
        _set("PROVIDER_COMPLETION_POLICY", "complete_values", ["max_tokens", "tool_use"]),
    ),
    ("parse before completion", _swap(2, 3)),
    ("semantic before schema", _swap(4, 5)),
    ("a model call", _set("preparation_accounting", "MODEL_CALLS", 1)),
    ("a provider request", _set("preparation_accounting", "MESSAGES_API_REQUESTS", 1)),
    ("TED bytes", _set("preparation_accounting", "TED_BYTES_SENT", 3604)),
    ("an Opportunity", _set("CANONICAL_COUNTERS", "research.opportunities", 2)),
    (
        "a retention path no test defines",
        _set("RETENTION_VERIFIED_PATHS", "timeout", "test_nothing"),
    ),
    (
        "human review dropped",
        _set("PERSISTENCE_POLICY", "human_review_required_before_persistence", False),
    ),
    ("automatic persistence", _set("PERSISTENCE_POLICY", "persist_if_gate_accepts", True)),
]


@pytest.mark.parametrize("fn", [c[1] for c in REFUSED], ids=[c[0] for c in REFUSED])
def test_a_violation_is_refused_through_the_whole_gate(world, fn) -> None:
    _edit(fn)
    with pytest.raises(GATE.ValidationError):
        GATE.validate()


# ================================================================== approvals and controls


def test_an_approval_recorded_by_the_preparing_mission_is_refused(world) -> None:
    _approval("mission-1.84.8", _read(GATE.PACKET)["EXECUTION_PACKET_SHA256"])
    with pytest.raises(GATE.ValidationError, match="prepared it"):
        GATE.validate()


def test_an_approval_naming_v2s_digest_is_refused(world) -> None:
    _approval("mission-1.84.9", GATE.V2_SHA256)
    with pytest.raises(GATE.ValidationError, match="other than V3"):
        GATE.validate()


def test_a_later_missions_approval_naming_v3_is_accepted(world) -> None:
    _approval("mission-1.84.9", _read(GATE.PACKET)["EXECUTION_PACKET_SHA256"])
    GATE.validate()


def test_a_note_binds_nothing(world) -> None:
    packet = _read(GATE.PACKET)
    packet["prompt_note"] = "Reworded; a note explains a field and binds nothing"
    _write(GATE.PACKET, packet)
    GATE.validate()


# ================================================================== the runner


def _runner_with(old: str, new: str) -> str:
    assert RUNNER_SOURCE.count(old) == 1, old
    return RUNNER_SOURCE.replace(old, new, 1)


CALL = "        response = gateway.complete(request)\n"
TRY_BLOCK = (
    "    try:\n"
    "        response = gateway.complete(request)\n"
    "        failure = None\n"
    "    except Exception as exc:  # noqa: BLE001 -- captured and recorded, never retried\n"
    "        response = None\n"
    "        failure = exc\n"
)
ENTRY = "    result = execute(context)\n"

RETRIES = {
    "a for loop around the call": (
        TRY_BLOCK,
        "    for _attempt in range(2):\n"
        "        try:\n"
        "            response = gateway.complete(request)\n"
        "            failure = None\n"
        "            break\n"
        "        except Exception as exc:  # noqa: BLE001\n"
        "            response = None\n"
        "            failure = exc\n",
    ),
    "a while loop around the call": (
        CALL,
        "        while response is None:\n            response = gateway.complete(request)\n",
    ),
    "a second call site": (CALL, CALL + CALL),
    "execute called twice": (ENTRY, ENTRY + ENTRY),
    "execute calling itself on failure": (
        TRY_BLOCK,
        TRY_BLOCK + "    if failure is not None:\n        return execute(context)\n",
    ),
}


def test_the_real_runner_has_one_call_site_reached_once() -> None:
    GATE._check_single_call_site(RUNNER_SOURCE)


@pytest.mark.parametrize("case", sorted(RETRIES))
def test_a_retry_by_any_shape_is_refused(case) -> None:
    old, new = RETRIES[case]
    with pytest.raises(GATE.ValidationError):
        GATE._check_single_call_site(_runner_with(old, new))


@pytest.mark.parametrize(
    "fn",
    [
        _set("HUMAN_REVIEW_PACKET", "PRODUCED"),
        _set("OPPORTUNITY_PERSISTED", True),
        _set("CANONICAL_PERSISTENCE", True),
    ],
    ids=["a human-review packet", "an Opportunity persisted", "canonical persistence"],
)
def test_v2s_rejected_answer_is_never_a_candidate(world, monkeypatch, fn) -> None:
    record = _read(GATE.RECORD_V2)
    fn(record)
    target = world / GATE.RECORD_V2.name
    _write(target, record)
    monkeypatch.setattr(GATE, "RECORD_V2", target)
    with pytest.raises(GATE.ValidationError, match="second chance"):
        GATE.validate()


AFTER_PARSE = '    stages[STAGES[3]] = "PASSED"\n'
SUMMARY_FIELD = "evidence_bound_reasoning_summary"

#: Every shape section 15 forbids, written where it would matter: after the parse, before the schema.
POST_PROCESSING = {
    "the summary truncated to its bound": (
        f'    output["{SUMMARY_FIELD}"] = output["{SUMMARY_FIELD}"][:900]\n'
    ),
    "every string trimmed in a comprehension": (
        "    output = {k: v[:1] if isinstance(v, str) else v for k, v in output.items()}\n"
    ),
    "the answer replaced by a rewritten one": f'    output = dict(output, {SUMMARY_FIELD}="short")\n',
    "the answer merged in place": f'    output |= {{"{SUMMARY_FIELD}": "short"}}\n',
    "a field written into the answer": '    output["critical_uncertainties"] = []\n',
    "an item dropped in place": '    output["critical_uncertainties"].pop()\n',
    "a field deleted": '    del output["recommended_next_evidence"]\n',
    "a field summarised through update": f'    output.update({SUMMARY_FIELD}="short")\n',
    "a statement split into more": '    output["statement_classifications"].extend([])\n',
}


def test_the_real_runner_judges_the_answer_as_it_arrived() -> None:
    GATE._check_no_post_processing(RUNNER_SOURCE)


@pytest.mark.parametrize("case", sorted(POST_PROCESSING))
def test_post_processing_of_any_shape_is_refused(case) -> None:
    source = _runner_with(AFTER_PARSE, AFTER_PARSE + POST_PROCESSING[case])
    with pytest.raises(GATE.ValidationError, match="answer"):
        GATE._check_no_post_processing(source)


def test_a_slice_anywhere_in_the_runner_is_refused() -> None:
    source = _runner_with(ENTRY, "    result = execute(context)\n    report = str(result)[:80]\n")
    with pytest.raises(GATE.ValidationError, match="slices"):
        GATE._check_no_post_processing(source)


def test_a_runner_blind_to_v2s_spent_approval_is_refused(world, monkeypatch, tmp_path) -> None:
    def blind(module):
        original = module.v2_runner

        def v2_without_its_record():
            v2 = original()
            v2.EXECUTION_RECORD_V2 = tmp_path / "absent.json"
            return v2

        module.v2_runner = v2_without_its_record

    monkeypatch.setattr(GATE, "_module", _pinned(blind))
    with pytest.raises(GATE.ValidationError, match="V2's spent digest"):
        GATE.validate()


def test_a_runner_refusing_every_digest_is_refused(world, monkeypatch) -> None:
    def refuses_everything(module):
        def refuse(_digest):
            raise module.RefusedError("EXECUTION_APPROVAL_ALREADY_CONSUMED", "refuses everything")

        module.refuse_if_consumed = refuse

    monkeypatch.setattr(GATE, "_module", _pinned(refuses_everything))
    with pytest.raises(GATE.ValidationError, match="unseen digest"):
        GATE.validate()


def test_a_runner_whose_drift_check_passes_v2s_prompt_is_refused(world, monkeypatch) -> None:
    def blind_drift(module):
        module.unstated_constraints = lambda _text: []

    monkeypatch.setattr(GATE, "_module", _pinned(blind_drift))
    with pytest.raises(GATE.ValidationError, match="checks nothing"):
        GATE.validate()
