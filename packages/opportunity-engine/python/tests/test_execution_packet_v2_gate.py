"""Mission 1.84.6, CI gate 70: the two refusals the adversarial probe found missing, and a
cross-section of the rest, each driven through the whole `validate()` against temporary copies.

The probe's first run caught 258 violations and let two through. A route sentence naming the batch
beta "asynchronous" satisfied a test for the word "synchronous", and a loop around the runner's one
call site satisfied a count of call sites. Both are closed in the gate and pinned here, so neither
can reopen without a test failing.

The copies keep the shipped records untouched. Every edit is followed by the same repair the probe
makes: the decision's file digest re-bound into the packet and the packet digest recomputed, with
the runner's pinned digest following the copy, so the check that refuses is the one written for the
violation and not the digest guard in front of it.
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
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_execution_packet_v2.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("gate_70_under_test", GATE_PATH)
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


@pytest.fixture
def world(tmp_path, monkeypatch):
    """The decision and the packet copied aside, the runner's pin following the copy's digest."""
    for name in ("DECISION", "PACKET"):
        source = getattr(GATE, name)
        target = tmp_path / source.name
        shutil.copyfile(source, target)
        monkeypatch.setattr(GATE, name, target)
    monkeypatch.setattr(GATE, "APPROVAL", tmp_path / GATE.APPROVAL.name)

    def module_with_pin(name, path):
        module = ORIGINAL_MODULE(name, path)
        if path == GATE.RUNNER:
            digest = _read(GATE.PACKET)["EXECUTION_PACKET_SHA256"]
            module.EXPECTED = {**module.EXPECTED, "EXECUTION_PACKET_SHA256": digest}
        return module

    monkeypatch.setattr(GATE, "_module", module_with_pin)
    return tmp_path


def _rebind() -> None:
    packet = _read(GATE.PACKET)
    packet["EXECUTION_ENVELOPE_DECISION_SHA256"] = hashlib.sha256(
        GATE.DECISION.read_bytes()
    ).hexdigest()
    packet["EXECUTION_PACKET_SHA256"] = GATE.packet_digest(packet)
    _write(GATE.PACKET, packet)


def _edit(path: pathlib.Path, fn) -> None:
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


def _remove(key: str, value: str):
    return lambda doc: doc[key].remove(value)


def _approval(recorded_by: str | None, digest: str) -> None:
    doc: dict[str, object] = {"EXECUTION_PACKET_SHA256": digest, "approved_by": "an operator"}
    if recorded_by is not None:
        doc["recorded_by"] = recorded_by
    _write(GATE.APPROVAL, doc)


# ================================================================== the shipped state


def test_the_shipped_records_validate() -> None:
    GATE.validate()


def test_the_copies_validate_before_anything_is_edited(world) -> None:
    GATE.validate()


def test_the_shipped_route_is_the_pinned_sentence() -> None:
    assert _read(GATE.PACKET)["PROVIDER_ROUTE"] == GATE.PROVIDER_ROUTE_TEXT


# ================================================================== the first escape: the route


@pytest.mark.parametrize(
    "route",
    [
        "The Anthropic Message Batches beta, asynchronous, under the Commercial Terms of Service.",
        "The Anthropic API, asynchronous batch endpoint, under the Commercial Terms of Service.",
        "A Claude subscription, synchronous, under the Commercial Terms of Service.",
        "The Anthropic API, synchronous Messages endpoint, under the Commercial Terms of Service.",
    ],
)
def test_a_route_sentence_other_than_the_reviewed_one_is_refused(world, route) -> None:
    _edit(GATE.PACKET, _set("PROVIDER_ROUTE", route))
    with pytest.raises(GATE.ValidationError, match="as reviewed"):
        GATE.validate()


# ================================================================== the second escape: a retry


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
    "the call inside a comprehension": (
        CALL,
        "        response = [gateway.complete(request) for _ in range(2)][-1]\n",
    ),
    "a second call site": (CALL, CALL + CALL),
    "two call sites on one line": (
        "gateway.complete(request)",
        "gateway.complete(request) or gateway.complete(request)",
    ),
    "execute called twice": (ENTRY, ENTRY + ENTRY),
    "execute called in a loop": (
        ENTRY,
        "    for _attempt in range(2):\n        result = execute(context)\n",
    ),
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


def test_a_comment_in_the_runner_is_not_a_retry() -> None:
    GATE._check_single_call_site(_runner_with(CALL, "        # one call\n" + CALL))


# ================================================================== a cross-section of section 27


def _parse_first(doc) -> None:
    stages = list(doc["VALIDATION_STAGES"])
    stages[2], stages[4] = stages[4], stages[2]
    doc["VALIDATION_STAGES"] = stages


REFUSED = [
    (
        "full domain reachable",
        "packet",
        _set("CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL", True),
    ),
    (
        "envelope reachable",
        "decision",
        _set("ENVELOPE_MODEL", "CONTRACT_FULL_DOMAIN_REACHABLE", True),
    ),
    ("state an error", "decision", lambda d: d["ENVELOPE_MODEL"]["STATE_IS_NOT"].remove("ERROR")),
    (
        "schema v1.2.0",
        "packet",
        _set("OUTPUT_SCHEMA_VERSION", "second-opportunity-synthesis-output@1.2.0"),
    ),
    (
        "narrative bounds accepted",
        "decision",
        _remove("REJECTED_ALTERNATIVES", "BOUND_THE_NARRATIVE_FIELDS_FURTHER"),
    ),
    (
        "character class accepted",
        "decision",
        _remove("REJECTED_ALTERNATIVES", "RESTRICT_THE_NARRATIVE_CHARACTER_CLASS"),
    ),
    (
        "batch surface",
        "packet",
        _set("PROVIDER_ROUTE_SURFACE", "POST https://api.anthropic.com/v1/messages/batches"),
    ),
    ("beta header", "packet", _set("BETA_HEADERS", ["message-batches-2024-09-24"])),
    ("batch selected", "decision", _set("SELECTED_ROUTE", "MESSAGE_BATCHES_BETA")),
    ("two calls", "packet", _set("MAX_MODEL_CALLS", 2)),
    (
        "split accepted",
        "decision",
        _remove("REJECTED_ALTERNATIVES", "SPLIT_THE_SYNTHESIS_ACROSS_CALLS"),
    ),
    ("continuation", "packet", _set("CONTINUATION_REQUESTS", True)),
    ("a retry", "packet", _set("MAX_RETRIES", 1)),
    ("retry authorised", "decision", _set("RETRY_AUTHORISED", True)),
    ("parse before completion", "packet", _parse_first),
    (
        "limit not fail-closed",
        "packet",
        _set("PROVIDER_COMPLETION_POLICY", "PROVIDER_LIMIT_FAIL_CLOSED", False),
    ),
    (
        "max_tokens complete",
        "packet",
        _set("PROVIDER_COMPLETION_POLICY", "complete_values", ["max_tokens", "tool_use"]),
    ),
    ("adaptive thinking", "packet", _set("ADAPTER_PARAMETERS", "thinking", "ADAPTIVE")),
    ("thinking omitted", "packet", _set("ADAPTER_PARAMETERS", "thinking", "PROVIDER_DEFAULT")),
    ("max_tokens 64000", "packet", _set("MAX_OUTPUT_TOKENS", 64000)),
    ("4096 recorded as 128000", "packet", _set("ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS", 128000)),
    ("estimate exact", "packet", _set("ESTIMATE_EXACT", True)),
    ("exact output count", "packet", _set("EXACT_MAX_OUTPUT_TOKEN_COUNT", 231608)),
    (
        "estimate an output count",
        "decision",
        _remove("WHAT_THE_ESTIMATE_IS_NOT", "an output token count"),
    ),
    ("prompt moved", "packet", _set("PROMPT_SHA256", ZERO)),
    ("representation moved", "packet", _set("REPRESENTATION_SHA256", ZERO)),
    ("subscription", "packet", _set("PROVIDER_ID", "anthropic-claude-subscription")),
    ("V1 approval reusable", "packet", _set("PREVIOUS_APPROVAL_REUSABLE", True)),
    ("V1 unconsumed", "packet", _set("PREDECESSOR_APPROVAL_CONSUMED", False)),
    ("V2 approved inside", "packet", _set("OPERATOR_EXECUTION_APPROVAL_RECORDED", True)),
    ("a model call", "packet", _set("preparation_accounting", "MODEL_CALLS", 1)),
    ("a provider request", "packet", _set("preparation_accounting", "MESSAGES_API_REQUESTS", 1)),
    ("TED bytes", "packet", _set("preparation_accounting", "TED_BYTES_SENT", 3604)),
    ("an Opportunity", "packet", _set("CANONICAL_COUNTERS", "research.opportunities", 2)),
    ("decision derived", "decision", _set("MATHEMATICALLY_DERIVED", True)),
    ("ceiling doubled", "packet", _set("EXECUTION_COST_CEILING", 2.607816)),
    (
        "timeout covers 128000",
        "packet",
        _set("TIMEOUT", "TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS", False),
    ),
]


@pytest.mark.parametrize(("record", "fn"), [c[1:] for c in REFUSED], ids=[c[0] for c in REFUSED])
def test_a_violation_is_refused_through_the_whole_gate(world, record, fn) -> None:
    _edit(GATE.PACKET if record == "packet" else GATE.DECISION, fn)
    with pytest.raises(GATE.ValidationError):
        GATE.validate()


# ================================================================== approvals and controls


def test_an_approval_recorded_by_the_preparing_mission_is_refused(world) -> None:
    _approval("mission-1.84.6", _read(GATE.PACKET)["EXECUTION_PACKET_SHA256"])
    with pytest.raises(GATE.ValidationError, match="prepared it"):
        GATE.validate()


def test_an_approval_naming_v1s_digest_is_refused(world) -> None:
    _approval("mission-1.84.7", GATE.V1_SHA256)
    with pytest.raises(GATE.ValidationError, match="other than V2"):
        GATE.validate()


def test_a_later_missions_approval_naming_v2_is_accepted(world) -> None:
    _approval("mission-1.84.7", _read(GATE.PACKET)["EXECUTION_PACKET_SHA256"])
    GATE.validate()


def test_a_note_binds_nothing(world) -> None:
    packet = _read(GATE.PACKET)
    packet["estimate_note"] = "Reworded; a note explains a field and binds nothing"
    _write(GATE.PACKET, packet)
    GATE.validate()


def test_a_digest_the_runner_was_not_prepared_for_is_refused(world, monkeypatch) -> None:
    monkeypatch.setattr(GATE, "_module", ORIGINAL_MODULE)
    provenance = ["PERSISTENCE_POLICY", "provenance_the_first_revision_must_carry"]
    _edit(GATE.PACKET, lambda d: d[provenance[0]][provenance[1]].append("the probe's extra item"))
    with pytest.raises(GATE.ValidationError, match="another digest"):
        GATE.validate()
