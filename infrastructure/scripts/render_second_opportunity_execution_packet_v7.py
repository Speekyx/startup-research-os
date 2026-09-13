"""Mission 1.84.19, CI gate 93: execution packet V7, V6's call with a strict tool over the frozen
projection of schema v1.2.0, frozen and unapproved.

V6 was refused at stage 5 on one key its closed contract does not declare. The operator kept the
contract, gate v1.4.0, prompt v1.5.0 and the headroom policy, and asked for the provider's strict tool
use over a deterministic projection of the contract, with the full contract still deciding stage 5.
CI gate 92 froze that projection, and its freeze commit was pushed and found on the remote before any
V7 artifact existed. This gate re-derives the packet:

    uv run python infrastructure/scripts/render_second_opportunity_execution_packet_v7.py --check

It refuses: bound fields that do not hash to the digest, a spent digest, an unreviewed or missing
field, or an approval recorded by the mission that prepared the packet; V1 to V6 edited or their
consumption reset, or V6's historical refusal re-derived as anything but its one undeclared field; a
contract, gate or prompt that moved from V6; strict fields that are not gate 92's frozen ones, or a
freeze commit or push record that moved; a request body whose difference from V6's is anything but
the strict flag and the projected tool schema; a route, model, thinking, max_tokens, completion,
timeout, retention or persistence policy that moved from V6; a cost ceiling that is not the worst case
recomputed from the new body; a residual-risk acceptance carried over; a synthetic answer that does not
stop where it must, including an extra root key, which local stage 5 still refuses; a runner with more
than one call site, post-processing, an injectable gate, a stage 5 other than the full contract, a
provider that is not the strict one, another digest, or one that would execute V1 to V6 again; and any
preparation call, TED byte or canonical counter that moved.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import inspect
import json
import math
import pathlib
import sys
from collections.abc import Callable
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

from sros_llm_gateway.pricing import ModelPrice  # noqa: E402
from sros_llm_gateway.providers.anthropic import (  # noqa: E402
    DEFAULT_ENDPOINT,
    STRUCTURED_TOOL_NAME,
    AnthropicProvider,
)
from sros_llm_gateway.providers.anthropic_strict import (  # noqa: E402
    STRICT_TOOL_FLAG,
    AnthropicStrictToolProvider,
    canonical_json_sha256,
)
from sros_llm_gateway.types import ProviderInvalidRequestError  # noqa: E402
from sros_opportunity.schema_validation import schema_violations  # noqa: E402
from sros_opportunity.second_opportunity_prompt_v1_5 import (  # noqa: E402
    second_opportunity_prompt_hash_v1_5,
)
from sros_opportunity.second_opportunity_schema_v1_2 import (  # noqa: E402
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
)

PACKET = DATA / "second-opportunity-synthesis-execution-packet-v7.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v7.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v7.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v7.py"
RUNNER_V6 = SCRIPTS / "run_second_opportunity_execution_v6.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v7.py"
)
PACKETS = tuple(
    DATA / f"second-opportunity-synthesis-execution-packet-v{n}.json" for n in range(1, 7)
)
RECORDS = tuple(
    DATA / f"second-opportunity-synthesis-execution-record-v{n}.json" for n in range(1, 7)
)
PACKET_V6 = PACKETS[5]
RECORD_V6 = RECORDS[5]
RESPONSE_V6 = DATA / "second-opportunity-synthesis-response-v6.json"
PROMPT_V6 = DATA / "second-opportunity-synthesis-prompt-v6.json"
STRICT_RECORD = DATA / "second-opportunity-provider-strict-projection-v1.json"
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
PROVIDER_REGISTER = DATA / "model-provider-policy-v1.json"
PREPARATION = DATA / "opportunity-preparation-v5.json"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_76 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
GATE_81 = SCRIPTS / "render_second_opportunity_execution_packet_v4.py"
GATE_88 = SCRIPTS / "render_second_opportunity_prompt_v1_5.py"
GATE_89 = SCRIPTS / "render_second_opportunity_stage_6_9_preflight_v2.py"
GATE_90 = SCRIPTS / "render_second_opportunity_execution_packet_v6.py"
GATE_91 = SCRIPTS / "render_second_opportunity_execution_record_v6.py"
GATE_92 = SCRIPTS / "render_second_opportunity_provider_strict_projection.py"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V7"
PACKET_VERSION = 7
PREPARED_BY = "mission-1.84.19"
THIS_MISSION = (1, 84, 19)
IDS = tuple(f"SECOND-OPPORTUNITY-SYNTH-EXEC-V{n}" for n in range(1, 7))
SHAS = (
    "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92",
    "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e",
    "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2",
    "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b",
    "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a",
    "969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9",
)
V6_ID, V6_SHA256 = IDS[5], SHAS[5]
MODEL = "claude-sonnet-5"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
CANONICAL_SCHEMA_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
PROMPT_SHA256 = "0713eb8053e83627e1156324cc9003031fff1f8e81289efe5cc89f182f542abb"
CHARS_PER_TOKEN = 2.1565
CONSERVATIVE_MULTIPLIER = 1.25
V6_WIRE_CHARACTERS = 31967
V6_OUTCOME = "EXECUTION_SCHEMA_REJECTED_NO_RETRY"
V6_VIOLATIONS = ["<root>: unknown field 'parameter name'; additionalProperties is false"]
#: The strict-projection freeze, committed and pushed before any V7 artifact existed, and the
#: remote check that found it there: `git ls-remote` printed this SHA for the branch.
FREEZE_COMMIT = "57154affb934516650b84480c2438a75c9b9a5a5"
FREEZE_PUSH = {
    "commit": FREEZE_COMMIT,
    "branch": "sprint-1/mission-1.84.19",
    "remote_ref_sha": FREEZE_COMMIT,
    "verified_with": "git ls-remote origin refs/heads/sprint-1/mission-1.84.19",
    "verified_at": "2026-09-13T20:30:52Z",
    "STRICT_PROJECTION_FREEZE_PUSH_VERIFIED_BEFORE_V7": True,
}
PROJECTION_ID = "second-opportunity-provider-strict-input-schema@1.0.0"
READY = "SECOND_OPPORTUNITY_EXECUTION_PACKET_V7_READY_FOR_OPERATOR_APPROVAL"
#: The only two ways V7's body may differ from V6's.
APPROVED_DIFFERENCES = ["tools[0].input_schema: changed", f"tools[0].{STRICT_TOOL_FLAG}: added"]
DOCUMENTATION_FETCHES = 8


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Gate 81, whose frozen helpers every packet since V4 reuses, and gate 90, V6's own gate.
G81 = _module("gate_81_for_packet_v7", GATE_81)
G90 = _module("gate_90_for_packet_v7", GATE_90)

STAGES = G90.STAGES
STAGE_CONDITIONS = G90.STAGE_CONDITIONS
POST_PROCESSING = G81.POST_PROCESSING
#: Preparing V7 read eight documentation pages, which gate 92 records, and did nothing else.
PREPARATION_ZERO = tuple(k for k in G81.PREPARATION_ZERO if k != "DOCUMENTATION_FETCHES")
RETENTION_PATHS = G81.RETENTION_PATHS
RETENTION_PROPERTIES = G81.RETENTION_PROPERTIES
CANONICAL_COUNTERS = G81.CANONICAL_COUNTERS
CAPABILITY_NEGATIVES = G81.CAPABILITY_NEGATIVES
CALL_NEGATIVES = G81.CALL_NEGATIVES
LLM_REQUEST_FIELDS = G81.LLM_REQUEST_FIELDS

#: What the V7 digest binds: V6's fields without V6's residual-risk flag, and the strict mechanism,
#: its frozen projection and its freeze commit, the predecessor's violation, the full-contract stage
#: 5 requirement, the request-body differential and V7's own residual-risk flag.
DIGEST_FIELDS: tuple[str, ...] = (
    *(f for f in G90.DIGEST_FIELDS if f != "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6"),
    "PREDECESSOR_SCHEMA_VIOLATION",
    "PROVIDER_STRICT_MODE",
    "PROVIDER_STRICT_SCHEMA_ID",
    "PROVIDER_STRICT_SCHEMA_SHA256",
    "STRICT_CAPABILITY_PROFILE_ID",
    "STRICT_CAPABILITY_PROFILE_SHA256",
    "STRICT_PROJECTOR_IMPLEMENTATION_SHA256",
    "STRICT_PROJECTION_TEST_SHA256",
    "STRICT_PROJECTION_RECORD_SHA256",
    "STRICT_PROJECTION_FREEZE_COMMIT",
    "FULL_CANONICAL_STAGE_5_VALIDATION",
    "REQUEST_BODY_DIFFERENTIAL",
    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7",
)
#: Everything else the packet may carry. Closed, as V6's was.
UNBOUND_FIELDS: tuple[str, ...] = (
    *(field for field in G90.UNBOUND_FIELDS if field != "V5_OBSERVATION"),
    "V6_OBSERVATION",
    "V6_RECONFIRMATION",
    "V7_PREFLIGHT",
    "STRICT_PROJECTION_FREEZE_PUSH",
    "PROMPT_DECISION",
    "strict_note",
)


class ValidationError(RuntimeError):
    """The packet disagrees with V6, with the frozen projection, or with live code."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def text_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _through(check: Callable[..., Any], *args: Any) -> Any:
    """Run one of gate 81's frozen checks, and report its refusal as this gate's."""
    try:
        return check(*args)
    except G81.ValidationError as exc:
        raise ValidationError(str(exc)) from exc


def packet_digest(packet: dict[str, Any]) -> str:
    """Recompute the V7 execution digest from the packet's own bound fields."""
    bound: dict[str, object] = {}
    for key in DIGEST_FIELDS:
        if key not in packet:
            raise ValidationError(f"the execution packet has no {key!r} to bind")
        bound[key] = G81._bindable(packet[key])
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_gate() -> Any:
    """Gate 87, the one authority on gate v1.4.0's implementation digest."""
    return G90.freeze_gate()


def snapshot() -> tuple[Any, Any, Any]:
    """Gate 81's authenticated snapshot, and prompts v1.5.0 and v1.4.0 rendered over it."""
    try:
        return G90.snapshot()
    except G90.ValidationError as exc:
        raise ValidationError(str(exc)) from exc


def runner() -> Any:
    return _module("execution_runner_v7_for_gate", RUNNER)


def runner_v6() -> Any:
    return _module("execution_runner_v6_for_gate_93", RUNNER_V6)


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


def _validates(path: pathlib.Path, name: str) -> Any:
    gate = _module(f"gate_{name}_for_packet_v7", path)
    try:
        return gate.validate()
    except gate.ValidationError as exc:
        raise ValidationError(f"gate {name} no longer validates: {exc}") from exc


# --------------------------------------------------------------------------- derived blocks


def v6_reconfirmation() -> dict[str, object]:
    """V6's outcome, re-derived from its committed record and its retained answer."""
    record = _load(RECORD_V6)
    parsed = _load(RESPONSE_V6)["parsed_output"]
    declared = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["properties"]
    required = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["required"]
    usage = record["ACTUAL_USAGE"]
    summary = record["REASONING_SUMMARY"]
    undeclared = [key for key in parsed if key not in declared]
    return {
        "provider_requests": record["actual_provider_requests"],
        "model_calls": record["actual_model_calls"],
        "retries": record["retries"],
        "fallbacks": record["fallbacks"],
        "continuations": record["continuation_requests"],
        "repair_calls": record["repair_calls"],
        "stop_reason": record["STOP_REASON"],
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "thinking_tokens": usage["thinking_tokens"],
        "total_tokens": usage["total_tokens"],
        "actual_cost": record["ACTUAL_COST"]["cost_units"],
        "stages": record["VALIDATION_STAGES"],
        "response_root_keys": len(parsed),
        "declared_required_keys_present": sum(1 for key in required if key in parsed),
        "declared_required_keys": len(required),
        "undeclared_root_keys": undeclared,
        "undeclared_values": {key: parsed[key] for key in undeclared},
        "summary_characters": summary["characters"],
        "summary_generation_target": summary["generation_target"],
        "summary_hard_maximum": summary["hard_maximum"],
        "all_composed_strings_within_hard_maximum": all(
            row["within_hard_maximum"] for row in record["GENERATION_TARGET_DIAGNOSTICS"]
        ),
        "canonical_persistence": record["CANONICAL_PERSISTENCE"],
        "approval_consumed": record["EXECUTION_APPROVAL_CONSUMED"],
        "live_v1_2_0_violations": schema_violations(
            dict(parsed), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
        ),
        "OBSERVED_UNKNOWN_PROPERTY_EVENTS_V6": len(undeclared),
        "PROVIDER_UNKNOWN_PROPERTY_RATE": "NOT_ESTABLISHED",
        "REPLAYED_THROUGH_THE_STRICT_PROJECTION": False,
    }


def request_bodies(parts: Any, packet: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """V6's body, through V6's runner and packet, and V7's, through V7's: both built, never sent.

    The strict adapter refuses to build a body from a schema outside the reviewed subset, and the V7
    runner refuses a projection or profile that is not the frozen one. Either refusal is this gate's,
    named, rather than an exception nobody reads.
    """
    module = runner()
    try:
        v7 = module.request_body(parts, packet)
    except (ProviderInvalidRequestError, module.RefusedError) as exc:
        raise ValidationError(
            f"STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE: V7's request cannot be built: {exc}"
        ) from exc
    return runner_v6().request_body(parts, _load(PACKET_V6)), v7


def request_differential(parts: Any, packet: dict[str, Any]) -> dict[str, object]:
    """Every path where V7's body differs from V6's, structurally."""
    v6, v7 = request_bodies(parts, packet)
    differences: list[str] = []
    for key in sorted(set(v6) | set(v7)):
        if key == "tools":
            continue
        if v6.get(key) != v7.get(key):
            differences.append(f"{key}: {'added' if key not in v6 else 'changed'}")
    tools6, tools7 = v6.get("tools") or [], v7.get("tools") or []
    if len(tools6) != 1 or len(tools7) != 1:
        differences.append(f"tools: {len(tools6)} before and {len(tools7)} after")
    else:
        for key in sorted(set(tools6[0]) | set(tools7[0])):
            if key not in tools6[0]:
                differences.append(f"tools[0].{key}: added")
            elif key not in tools7[0]:
                differences.append(f"tools[0].{key}: removed")
            elif tools6[0][key] != tools7[0][key]:
                differences.append(f"tools[0].{key}: changed")
    return {
        "v6_body_characters": len(json.dumps(v6)),
        "v7_body_characters": len(json.dumps(v7)),
        "delta_characters": len(json.dumps(v7)) - len(json.dumps(v6)),
        "differences": differences,
        "approved_differences": list(APPROVED_DIFFERENCES),
        "unapproved_drift": [d for d in differences if d not in APPROVED_DIFFERENCES],
        "v6_tool_input_schema_sha256": canonical_json_sha256(tools6[0]["input_schema"]),
        "v7_tool_input_schema_sha256": canonical_json_sha256(tools7[0]["input_schema"]),
        "unchanged": [
            key
            for key in ("model", "max_tokens", "system", "messages", "thinking", "tool_choice")
            if v6.get(key) == v7.get(key)
        ]
        + [
            f"tools[0].{key}" for key in ("name", "description") if tools6[0][key] == tools7[0][key]
        ],
        "tool_choice": v7.get("tool_choice"),
    }


def cost_fields(wire: int) -> dict[str, object]:
    """The input estimate, the worst case and the ceiling for a body of `wire` characters."""
    v6 = _load(PACKET_V6)
    price = v6["PRICE_PER_1K"]
    held = ModelPrice(input_per_1k=float(price["input"]), output_per_1k=float(price["output"]))
    estimate = math.ceil(wire / CHARS_PER_TOKEN * CONSERVATIVE_MULTIPLIER)
    output = int(v6["MAX_OUTPUT_TOKENS"])
    total = held.cost_for(estimate, output)
    previous = float(v6["EXECUTION_COST_CEILING"])
    return {
        "INPUT_TOKEN_ESTIMATE": estimate,
        "TOTAL_TOKEN_CEILING": estimate + output,
        "INPUT_WORST_CASE_COST": held.cost_for(estimate, 0),
        "OUTPUT_WORST_CASE_COST": held.cost_for(0, output),
        "WORST_CASE_CALL_COST": total,
        "EXECUTION_COST_CEILING": total,
        "PREVIOUS_EXECUTION_COST_CEILING": previous,
        "CEILING_DELTA_OVER_PREVIOUS": round(total - previous, 6),
        "CEILING_OVER_PREVIOUS_CEILING": round(total / previous, 4),
        "LARGER_THAN_PREVIOUS_CEILING": total > previous,
    }


def preflight_results() -> list[dict[str, object]]:
    """Gate 89's synthetic answers, and one extra root key, through V7's own stages."""
    module = runner()
    fx = _module("fixtures_for_packet_v7", FIXTURES)
    g89 = _module("gate_89_fixtures_for_packet_v7", GATE_89)
    gate_76 = _module("gate_76_for_packet_v7", GATE_76)
    cases = [
        (fixture_id, stage, result, context)
        for fixture_id, _what, stage, result, context in g89.fixtures(fx)
    ]
    extra = fx.good_output()
    extra["parameter name"] = "value"
    cases.append(
        (
            "J_EXTRA_ROOT_PROPERTY_REFUSED_AT_LOCAL_STAGE_5",
            "5_schema_validation_v1_2_0",
            fx.recorded_result(extra),
            fx.runner_context(),
        )
    )
    out: list[dict[str, object]] = []
    with gate_76.no_transport():
        for fixture_id, stage, result, context in cases:
            report = module.validate_execution(result, context)
            body = json.loads(result["transport_responses"][0]["body"])
            answer = next((b["input"] for b in body["content"] if b.get("type") == "tool_use"), {})
            out.append(
                {
                    "fixture": fixture_id,
                    "summary_characters": len(
                        str(answer.get("evidence_bound_reasoning_summary", ""))
                    ),
                    "must_stop_at": stage,
                    "stopped_at": report["failed_stage"],
                    "outcome": report["outcome"],
                    "reasons": list(report["reasons"])
                    if fixture_id.startswith(("I_", "J_"))
                    else [],
                }
            )
    return out


# --------------------------------------------------------------------------- identity


def _check_identity_and_approval(packet: dict[str, Any]) -> str:
    _fixed(
        packet,
        {
            "EXECUTION_PACKET_ID": PACKET_ID,
            "EXECUTION_PACKET_VERSION": PACKET_VERSION,
            "prepared_by": PREPARED_BY,
            "PRIMARY_OUTCOME": READY,
            "OPERATOR_EXECUTION_APPROVAL_RECORDED": False,
            "NEW_APPROVAL_REQUIRED": True,
            "PREVIOUS_APPROVAL_REUSABLE": False,
            "HUMAN_REVIEW_REQUIRED": True,
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7": False,
        },
        "packet",
    )
    known = {*DIGEST_FIELDS, *UNBOUND_FIELDS, "EXECUTION_PACKET_SHA256"}
    extra, missing = sorted(set(packet) - known), sorted(known - set(packet))
    if extra or missing:
        raise ValidationError(
            f"the packet carries fields nothing reviews ({extra}) or lacks fields ({missing})"
        )
    recomputed = packet_digest(packet)
    if packet["EXECUTION_PACKET_SHA256"] != recomputed:
        raise ValidationError(
            f"the packet records {packet['EXECUTION_PACKET_SHA256']} and its bound fields hash "
            f"to {recomputed}"
        )
    if recomputed in SHAS:
        raise ValidationError("V7 carries a spent predecessor's digest")
    note = str(packet["approval_note"])
    for word in ("egress", "V6", "beside", "strict", "residual", "process"):
        if word not in note:
            raise ValidationError(
                "the approval note does not keep this approval apart from V1's to V6's, from the "
                "strict-tool decision, from the residual-risk and process-deviation acceptances "
                "V6 spent, and from TED egress"
            )
    if (
        packet["EXECUTION_ENVELOPE_DECISION_SHA256"]
        != _load(PACKET_V6)["EXECUTION_ENVELOPE_DECISION_SHA256"]
    ):
        raise ValidationError("the envelope decision moved from V6")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = G81._mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V7 recorded by the mission that prepared it. Preparing a packet "
                "authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V7's")
    return recomputed


def _check_predecessors(packet: dict[str, Any]) -> None:
    packets = [_load(p) for p in PACKETS]
    records = [_load(p) for p in RECORDS]
    for index, (frozen, digest) in enumerate(zip(packets, SHAS, strict=True)):
        if frozen["EXECUTION_PACKET_SHA256"] != digest:
            raise ValidationError(f"V{index + 1}'s packet digest moved")
        if frozen["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
            raise ValidationError(
                f"the frozen V{index + 1} packet was edited to record an approval"
            )
    if G90.packet_digest(packets[5]) != V6_SHA256:
        raise ValidationError("V6's bound fields no longer hash to its digest")
    for index, record in enumerate(records):
        if record["EXECUTION_APPROVAL_CONSUMED"] is not True:
            raise ValidationError(f"V{index + 1}'s consumption was reset")
    _fixed(
        records[5],
        {
            "execution_packet_sha256": V6_SHA256,
            "PRIMARY_OUTCOME": V6_OUTCOME,
            "HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
            "OPPORTUNITY_PERSISTED": False,
            "CANONICAL_PERSISTENCE": False,
            "SCHEMA_VIOLATIONS": V6_VIOLATIONS,
            "FAILED_STAGE": "5_schema_validation_v1_2_0",
        },
        "V6's record",
    )
    _validates(GATE_91, "91")
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V6_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V6_SHA256,
            "PREDECESSOR_EXECUTION_OUTCOME": V6_OUTCOME,
            "PREDECESSOR_APPROVAL_CONSUMED": True,
            "PREDECESSOR_SCHEMA_VIOLATION": "UNKNOWN_ROOT_PROPERTY",
            "CONSUMED_EXECUTION_PACKETS": [
                {"id": ident, "sha256": digest, "outcome": record["PRIMARY_OUTCOME"]}
                for ident, digest, record in zip(IDS, SHAS, records, strict=True)
            ],
        },
        "packet",
    )


def _check_v6_reconfirmation(packet: dict[str, Any]) -> None:
    derived = v6_reconfirmation()
    if packet["V6_RECONFIRMATION"] != derived:
        raise ValidationError("V6_RECONFIRMATION is not what V6's record and retained answer give")
    _fixed(
        derived,
        {
            "provider_requests": 1,
            "model_calls": 1,
            "retries": 0,
            "fallbacks": 0,
            "continuations": 0,
            "repair_calls": 0,
            "stop_reason": "tool_use",
            "input_tokens": 12903,
            "output_tokens": 3637,
            "thinking_tokens": 0,
            "total_tokens": 16540,
            "actual_cost": 0.062176,
            "response_root_keys": 21,
            "declared_required_keys_present": 20,
            "undeclared_root_keys": ["parameter name"],
            "undeclared_values": {"parameter name": "value"},
            "summary_characters": 1169,
            "summary_generation_target": 1200,
            "summary_hard_maximum": 1500,
            "all_composed_strings_within_hard_maximum": True,
            "canonical_persistence": False,
            "approval_consumed": True,
            "live_v1_2_0_violations": V6_VIOLATIONS,
            "OBSERVED_UNKNOWN_PROPERTY_EVENTS_V6": 1,
        },
        "V6_RECONFIRMATION",
    )
    stages = derived["stages"]
    if list(stages.values())[:5] != ["PASSED"] * 4 + ["FAILED"] or any(
        value != "NOT_REACHED" for value in list(stages.values())[5:]
    ):
        raise ValidationError(
            "V6's stage table is not 1 to 4 passed, 5 failed, 6 to 10 not reached"
        )


# --------------------------------------------------------------------------- what did not move


def _check_contract_and_gate(packet: dict[str, Any]) -> None:
    v6 = _load(PACKET_V6)
    implementation = freeze_gate().implementation_sha256()
    if implementation != v6["SEMANTIC_GATE_IMPLEMENTATION_SHA256"]:
        raise ValidationError("SEMANTIC_GATE_CHANGED: gate v1.4.0's implementation moved")
    for key in (
        "OUTPUT_SCHEMA_VERSION",
        "OUTPUT_SCHEMA_SHA256",
        "OUTPUT_GATE_VERSION",
        "SEMANTIC_GATE_IMPLEMENTATION_SHA256",
        "SEMANTIC_GATE_FROZEN_TEST_SHA256",
        "SEMANTIC_GATE_FREEZE_RECORD_SHA256",
        "SEMANTIC_GATE_FREEZE_COMMIT",
        "SEMANTIC_GATE_SUCCESSOR_DECISION",
        "REASONING_SUMMARY_CONTRACT_DECISION_SHA256",
        "REASONING_SUMMARY_CONTRACT_RECORD_SHA256",
        "REASONING_SUMMARY_DECISION_BASIS",
        "REASONING_SUMMARY_HARD_MAX",
        "REASONING_SUMMARY_GENERATION_TARGET",
        "OUTPUT_CAPACITY_RECORD_SHA256",
        "SOURCE_METADATA_CONTEXT_SHA256",
        "TRUSTED_CONTEXT_SHA256",
        "PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE",
        "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL",
        "CONTRACT_THEORETICAL_MAX_EXCEEDS_EXECUTION_ENVELOPE",
        "ESTIMATE_EXACT",
        "LOCAL_SCHEMA_VALIDATOR_MANDATORY",
        "OUTPUT_POST_PROCESSING",
        "GENERATION_HEADROOM_DECISION",
        "GENERATION_HEADROOM_RECORD_SHA256",
        "GENERATION_HEADROOM_POLICY",
        "GENERATION_TARGET_RATIO",
        "ARRAY_HEADROOM_POLICY",
        "GENERATION_HEADROOM_RENDERER",
        "FIELD_ROLE_POLICY",
        "GENERATION_HEADROOM_POLICY_DIGEST",
        "NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT",
    ):
        if packet[key] != v6[key]:
            raise ValidationError(f"{key} moved from V6")
    if packet["OUTPUT_SCHEMA_SHA256"] != canonical_json_sha256(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
    ):
        raise ValidationError("OUTPUT_SCHEMA_CHANGED: the live contract is not the bound one")
    if packet["OUTPUT_SCHEMA_SHA256"] != CANONICAL_SCHEMA_SHA256:
        raise ValidationError("OUTPUT_SCHEMA_CHANGED")
    post = packet["OUTPUT_POST_PROCESSING"]
    if set(post) != set(POST_PROCESSING) or any(post[key] is not False for key in POST_PROCESSING):
        raise ValidationError("an answer may be changed to fit, or an unknown key filtered away")
    _fixed(
        packet,
        {
            "SCHEMA_CHANGED": False,
            "SEMANTIC_GATE_CHANGED_BY_THIS_MISSION": False,
            "OUTPUT_GATE_CHANGED_FROM_PREDECESSOR": False,
            "NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT": "NOT_HELD",
        },
        "packet",
    )


def _check_strict(packet: dict[str, Any]) -> None:
    record = _validates(GATE_92, "92")
    freeze = record["FREEZE"]
    _fixed(
        packet,
        {
            "PROVIDER_STRICT_MODE": True,
            "STRUCTURED_OUTPUT_MECHANISM": "FORCED_STRICT_TOOL_USE",
            "NATIVE_PROVIDER_STRUCTURED_OUTPUT": False,
            "PROVIDER_STRICT_SCHEMA_ID": record["PROVIDER_STRICT_INPUT_SCHEMA"]["id"],
            "PROVIDER_STRICT_SCHEMA_SHA256": freeze["STRICT_PROJECTION_SHA256"],
            "STRICT_CAPABILITY_PROFILE_ID": record["CAPABILITY_PROFILE_ID"],
            "STRICT_CAPABILITY_PROFILE_SHA256": freeze["CAPABILITY_PROFILE_SHA256"],
            "STRICT_PROJECTOR_IMPLEMENTATION_SHA256": freeze["PROJECTOR_IMPLEMENTATION_SHA256"],
            "STRICT_PROJECTION_TEST_SHA256": freeze["TEST_SHA256"],
            "STRICT_PROJECTION_RECORD_SHA256": text_sha(STRICT_RECORD),
            "STRICT_PROJECTION_FREEZE_COMMIT": FREEZE_COMMIT,
            "STRICT_PROJECTION_FREEZE_PUSH": FREEZE_PUSH,
            "FULL_CANONICAL_STAGE_5_VALIDATION": "REQUIRED_OUTPUT_SCHEMA_V1_2_0_LOCAL",
        },
        "packet",
    )
    if packet["PROVIDER_STRICT_SCHEMA_ID"] != PROJECTION_ID:
        raise ValidationError("the provider projection is named as something other than itself")
    if record["TERMINOLOGY"]["FULL_CANONICAL_SCHEMA_COMPLIANCE"] != "LOCAL_STAGE_5_ONLY":
        raise ValidationError("full canonical compliance is attributed to strict mode")


def _check_prompt(packet: dict[str, Any], parts: Any) -> None:
    v6 = _load(PACKET_V6)
    live = second_opportunity_prompt_hash_v1_5(parts)
    for key in (
        "PROMPT_ID",
        "PROMPT_VERSION",
        "PROMPT_SHA256",
        "PROMPT_RECORD_SHA256",
        "PROMPT_ALIGNMENT_DECISION",
        "PROMPT_ALIGNMENT_RECORD_SHA256",
        "SEMANTIC_PROMPT_ALIGNMENT_DECISION",
        "SEMANTIC_PROMPT_ALIGNMENT_RECORD_SHA256",
        "OUTPUT_CONSTRAINT_RENDERER",
        "SEMANTIC_GENERATION_RULES_RENDERER",
        "SEMANTIC_RULE_CENSUS",
        "SOURCE_LABEL_BLOCK_RENDERER",
        "SEMANTIC_GENERATION_POLICY_DIGEST",
        "STAGE_6_TO_9_PREFLIGHT_RECORD_SHA256",
    ):
        if packet[key] != v6[key]:
            raise ValidationError(f"{key} moved from V6")
    if live != PROMPT_SHA256 or packet["PROMPT_SHA256"] != live:
        raise ValidationError("the prompt rendered over the snapshot is not V6's v1.5.0")
    _fixed(packet, {"PROMPT_CHANGED": False}, "packet")
    _fixed(
        packet["PROMPT_DECISION"],
        {
            "PROMPT_VERSION": "1.5.0",
            "PROMPT_TEXT_CHANGED": False,
            "PROMPT_SEMANTICS_CHANGED": False,
            "EXECUTION_BINDING_CHANGED": True,
            "EXTRA_PROPERTY_WARNING_ADDED": False,
        },
        "PROMPT_DECISION",
    )
    _validates(GATE_88, "88")


def _check_preflight(packet: dict[str, Any]) -> None:
    record = _validates(GATE_89, "89")
    if record["OUTCOME"] != "DETERMINISTIC_STAGE_6_TO_9_PATH_READY":
        raise ValidationError("DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY")
    live = preflight_results()
    if packet["V7_PREFLIGHT"] != live:
        raise ValidationError("V7_PREFLIGHT is not what V7's stages give over the fixtures")
    for row in live:
        if row["stopped_at"] != row["must_stop_at"]:
            raise ValidationError(
                f"DETERMINISTIC_STAGE_5_TO_9_PATH_NOT_READY: {row['fixture']} stopped at "
                f"{row['stopped_at']} and must stop at {row['must_stop_at']}"
            )
    by_id = {row["fixture"]: row for row in live}
    if by_id["F_LONG_SUMMARY_POSITIVE"]["summary_characters"] != 1189:
        raise ValidationError("the long positive summary is not 1189 characters")
    if by_id["J_EXTRA_ROOT_PROPERTY_REFUSED_AT_LOCAL_STAGE_5"]["reasons"] != V6_VIOLATIONS:
        raise ValidationError(
            "an extra root key is no longer refused by the full contract at stage 5"
        )


def _check_route(packet: dict[str, Any]) -> None:
    register = _load(PROVIDER_REGISTER)
    approved = sorted(
        str(e["provider_id"]) for e in register["providers"] if e.get("posture") == "APPROVED"
    )
    if approved != ["anthropic"]:
        raise ValidationError(
            f"PROVIDER_ROUTE_NO_LONGER_APPROVED: the register approves {approved}"
        )
    v6 = _load(PACKET_V6)
    for key in (
        "PROVIDER_ID",
        "PROVIDER_POSTURE",
        "PROVIDER_ROUTE",
        "PROVIDER_ROUTE_SURFACE",
        "BETA_HEADERS",
        "ROUTES_NOT_USED",
        "MODEL_ID",
        "MODEL_TIER",
        "THINKING",
        "THINKING_REQUEST_FIELD",
        "THINKING_POLICY_EXPLICIT",
        "ADAPTIVE_THINKING_USED",
        "THINKING_TOKENS_SHARE_OUTPUT_BUDGET",
        "MAX_OUTPUT_TOKENS",
        "OUTPUT_TOKEN_CEILING",
        "MAX_OUTPUT_TOKENS_BASIS",
        "OUTPUT_TOKEN_CEILING_BASIS",
        "ADAPTER_PARAMETERS",
        "ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS",
        "PROVIDER_COMPLETION_POLICY",
        "RETENTION_ON_EXECUTION",
        "failure_outcome",
        "output_limit_outcome",
        "SUBJECT_KEY",
        "SELECTED_PACKET_ID",
        "PREPARATION_VERSION",
        "PROCESSING_PURPOSE",
        "REPRESENTATION_SCHEMA",
        "REPRESENTATION_SHA256",
        "REPRESENTATION_CHARACTER_COUNT",
        "APPROVED_EVIDENCE_IDS",
        "APPROVED_CLAIM_IDS",
        "APPROVED_EVIDENCE_TO_CLAIM",
        "SOURCE_DECISION_PACKET_ID",
        "SOURCE_DECISION_PACKET_VERSION",
        "SOURCE_DECISION_PACKET_SHA256",
        "PRICING_VERSION",
        "PRICE_PER_1K",
        "EXECUTION_ENVELOPE_DECISION",
    ):
        if packet[key] != v6[key]:
            raise ValidationError(f"{key} moved from V6")
    _fixed(
        packet,
        {"VALIDATION_STAGES": list(STAGES), "STAGE_CONDITIONS": STAGE_CONDITIONS},
        "packet",
    )
    if (
        packet["PROVIDER_ROUTE_SURFACE"] != f"POST {DEFAULT_ENDPOINT}"
        or packet["MODEL_ID"] != MODEL
    ):
        raise ValidationError("the route or the model is not the reviewed one")
    if packet["BETA_HEADERS"] != []:
        raise ValidationError("a beta header rode along with strict mode")
    if tuple(packet["MAX_OUTPUT_TOKENS_NOT_BASED_ON"]) != (
        *v6["MAX_OUTPUT_TOKENS_NOT_BASED_ON"],
        "V6_OBSERVED_OUTPUT_TOKENS",
    ):
        raise ValidationError("the ceiling's basis no longer excludes V6's observed output")
    if packet["REPRESENTATION_SHA256"] != REPRESENTATION_SHA256:
        raise ValidationError("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")


def _check_request(packet: dict[str, Any], parts: Any) -> int:
    """The body V7 would send: V6's, with the strict flag and the projected schema, and nothing else."""
    module = runner()
    v6_body, body = request_bodies(parts, packet)
    if len(json.dumps(v6_body)) != V6_WIRE_CHARACTERS:
        raise ValidationError("V6's body no longer rebuilds to the 31967 characters it sent")
    if body.get("thinking") != {"type": "disabled"}:
        raise ValidationError(f"THINKING_CONTROL_NO_LONGER_VALID: {body.get('thinking')!r}")
    if body.get("max_tokens") != packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError(f"the adapter sends max_tokens {body.get('max_tokens')}")
    if body.get("tool_choice") != {"type": "tool", "name": STRUCTURED_TOOL_NAME}:
        raise ValidationError(
            "STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE: the synthesis tool is no "
            "longer forced"
        )
    if "output_config" in body:
        raise ValidationError("a JSON-output format rode along with strict tool use")
    problems = module.strict_tool_problems(body)
    if problems:
        raise ValidationError(
            f"STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE: {problems}"
        )
    differential = request_differential(parts, packet)
    if differential["unapproved_drift"] or sorted(differential["differences"]) != sorted(
        APPROVED_DIFFERENCES
    ):
        raise ValidationError(
            f"STRICT_REQUEST_BODY_HAS_UNAPPROVED_DRIFT: {differential['differences']}"
        )
    if differential["v6_tool_input_schema_sha256"] != CANONICAL_SCHEMA_SHA256:
        raise ValidationError("V6's body did not carry the full contract")
    if differential["v7_tool_input_schema_sha256"] != packet["PROVIDER_STRICT_SCHEMA_SHA256"]:
        raise ValidationError("V7's body does not carry the frozen projection")
    if packet["REQUEST_BODY_DIFFERENTIAL"] != differential:
        raise ValidationError("REQUEST_BODY_DIFFERENTIAL is not the rebuilt difference")
    provider = module.build_provider(
        packet, module._NoSend(), api_key="gate-probe-not-a-credential"
    )
    if type(provider) is not AnthropicStrictToolProvider:
        raise ValidationError("the runner's adapter is not the strict one")
    plain = AnthropicProvider(api_key="gate-probe-not-a-credential", transport=module._NoSend())
    if provider._headers() != plain._headers():
        raise ValidationError("the strict adapter sends a header the plain one does not")
    return len(json.dumps(body))


def _check_calls_and_timeout(packet: dict[str, Any]) -> None:
    v6 = _load(PACKET_V6)
    params = packet["GENERATION_PARAMETERS"]
    expected = {
        **v6["GENERATION_PARAMETERS"],
        "response_schema": PROJECTION_ID,
        "response_schema_note": (
            "the tool carries the provider-strict projection; stage 5 validates the answer "
            "against the full output schema v1.2.0, which the projection is not"
        ),
    }
    if params != expected:
        raise ValidationError("the generation parameters moved from V6 beyond the tool schema")
    supplied = {k: v for k, v in params.items() if k != "$comment" and not k.endswith("note")}
    for key, value in supplied.items():
        if value is not None and key not in LLM_REQUEST_FIELDS:
            raise ValidationError(f"{key!r} is frozen with a value nothing reads")
    if supplied.get("max_retries") != 0 or packet["MAX_RETRIES"] != 0:
        raise ValidationError("a retry is a second call, and V7 authorises one")
    if packet["MAX_MODEL_CALLS"] != 1:
        raise ValidationError(f"MAX_MODEL_CALLS is {packet['MAX_MODEL_CALLS']}")
    for key in CALL_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if packet["REQUEST_TIMEOUT"] != v6["REQUEST_TIMEOUT"]:
        raise ValidationError("the timeout moved from V6")
    _fixed(
        packet["TIMEOUT"],
        {
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "TIMEOUT_CHANGED_BY_THIS_MISSION": False,
            "V6_OBSERVED_ELAPSED_SECONDS": _load(RECORD_V6)["timing"]["elapsed_seconds"],
            "V6_OBSERVATION_USED_TO_CHANGE_THE_TIMEOUT": False,
            "STREAMING": False,
            "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
            "TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS": True,
            "FIRST_REQUEST_GRAMMAR_COMPILATION_LATENCY": "NOT_ESTABLISHED",
            "PROVIDER_COMPILATION_TIMEOUT_SECONDS": 180,
            "TIMEOUT_MAY_END_THE_CALL_DURING_GRAMMAR_COMPILATION": True,
            "ON_TIMEOUT": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
        },
        "TIMEOUT",
    )


def _check_cost(packet: dict[str, Any], wire: int) -> None:
    v6 = _load(PACKET_V6)
    record = _load(RECORD_V6)
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    _fixed(
        basis,
        {
            "exact_tokenizer_available": False,
            "no_test_request_was_sent": True,
            "chars_per_token": CHARS_PER_TOKEN,
            "conservative_multiplier": CONSERVATIVE_MULTIPLIER,
            "wire_characters": wire,
            "raw_estimate": round(wire / CHARS_PER_TOKEN, 1),
            "v6_wire_characters": V6_WIRE_CHARACTERS,
            "delta_characters_over_v6": wire - V6_WIRE_CHARACTERS,
            "strict_format_prompt_tokens": "NOT_ESTABLISHED",
        },
        "TOKEN_ESTIMATION_BASIS",
    )
    fields = cost_fields(wire)
    _fixed(packet, fields, "packet")
    tool_overhead = _load(CAPABILITY)["MODELS"][MODEL]["TOOL_USE_SYSTEM_PROMPT_TOKENS"][
        "any_or_tool"
    ]
    if basis["documented_tool_use_overhead_tokens"] != tool_overhead:
        raise ValidationError("the tool-use overhead is not the documented one")
    estimate = int(str(fields["INPUT_TOKEN_ESTIMATE"]))
    if estimate - wire / CHARS_PER_TOKEN < tool_overhead:
        raise ValidationError("the multiplier's margin does not cover the documented tool overhead")
    _fixed(
        packet,
        {"HEADROOM_POLICY": "NONE_HELD", "COST_NOT_EXPECTED_ACTUAL": True},
        "packet",
    )
    usage = record["ACTUAL_USAGE"]
    _fixed(
        packet["V6_OBSERVATION"],
        {
            "V6_INPUT_TOKEN_ESTIMATE": v6["INPUT_TOKEN_ESTIMATE"],
            "V6_ACTUAL_INPUT_TOKENS": usage["input_tokens"],
            "V6_ESTIMATE_COVERED_THE_ACTUAL": v6["INPUT_TOKEN_ESTIMATE"] >= usage["input_tokens"],
            "V6_ACTUAL_OUTPUT_TOKENS": usage["output_tokens"],
            "USED_TO_CHANGE_THE_ESTIMATION_METHOD": False,
            "USED_TO_REDUCE_MAX_OUTPUT_TOKENS": False,
            "USED_TO_CHOOSE_THE_PROJECTION": False,
        },
        "V6_OBSERVATION",
    )


def _check_representation(packet: dict[str, Any], snap: Any) -> None:
    """The TED representation and the boundary, V6's exactly, re-derived from the snapshot."""
    if (
        packet["REPRESENTATION_SHA256"] != REPRESENTATION_SHA256
        or snap.representation_sha256 != REPRESENTATION_SHA256
    ):
        raise ValidationError(
            "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED: the representation is not the approved one"
        )
    _fixed(
        packet,
        {
            "REPRESENTATION_CHARACTER_COUNT": REPRESENTATION_CHARACTERS,
            "APPROVED_EVIDENCE_IDS": list(snap.packet.evidence_ids),
            "APPROVED_CLAIM_IDS": list(snap.packet.claim_ids),
            "SOURCE_METADATA_CONTEXT_SHA256": snap.metadata.digest(),
            "TRUSTED_CONTEXT_SHA256": snap.trusted.digest(),
        },
        "packet",
    )


def _check_verification(packet: dict[str, Any], wire: int) -> None:
    """What verification found on the preparing machine, checked for agreement with CI's facts."""
    _fixed(
        packet["PREPARATION_VERIFICATION"],
        {
            "representation_sha256": REPRESENTATION_SHA256,
            "representation_characters": REPRESENTATION_CHARACTERS,
            "prompt_sha256": PROMPT_SHA256,
            "selected_packet_id": packet["SELECTED_PACKET_ID"],
            "approved_evidence_rows": len(packet["APPROVED_EVIDENCE_IDS"]),
            "provider_posture": "APPROVED",
            "ted_external_model_transmission": "PERMITTED_WITH_CONDITIONS",
            "live_packet_gate": "AVAILABLE",
            "request_thinking": {"type": "disabled"},
            "request_max_tokens": packet["MAX_OUTPUT_TOKENS"],
            "request_strict_tool": "FROZEN_PROJECTION_STRICT_FORCED",
            "request_body_characters": wire,
            "v6_request_body_characters_recomputed": V6_WIRE_CHARACTERS,
            "unstated_generation_constraints": 0,
            "unstated_generation_relevant_semantic_rules": 0,
            "unstated_generation_targets": 0,
            "output_schema_sha256": CANONICAL_SCHEMA_SHA256,
            "provider_strict_schema_sha256": packet["PROVIDER_STRICT_SCHEMA_SHA256"],
            "semantic_gate_implementation_sha256": packet["SEMANTIC_GATE_IMPLEMENTATION_SHA256"],
            "reasoning_summary_hard_max_and_target": [1500, 1200],
            "pricing_version": packet["PRICING_VERSION"],
            "worst_case_from_the_configured_table": packet["WORST_CASE_CALL_COST"],
            "source_metadata_context_sha256": packet["SOURCE_METADATA_CONTEXT_SHA256"],
            "trusted_context_sha256": packet["TRUSTED_CONTEXT_SHA256"],
            "stages_6_to_9_ready": True,
            "v1_to_v6_guards_refuse_their_digests": True,
            "guard_permits_an_unseen_digest": True,
            "operator_approval": "OPERATOR_APPROVAL_NOT_RECORDED",
        },
        "PREPARATION_VERIFICATION",
    )
    preparation = _load(PREPARATION)
    if packet["PREPARATION_VERSION"] != preparation["artifact_version"]:
        raise ValidationError("the packet names a preparation that is not the current one")
    selected = next(
        (p for p in preparation["packets"] if p.get("subject") == packet["SUBJECT_KEY"]), None
    )
    if selected is None or selected["packet_id"] != packet["SELECTED_PACKET_ID"]:
        raise ValidationError("the current preparation does not carry the selected packet")
    if selected["external_synthesis"]["availability"] != "AVAILABLE":
        raise ValidationError("TED_EGRESS_NO_LONGER_AVAILABLE in the current preparation")


def _check_boundaries(packet: dict[str, Any]) -> None:
    for key in CAPABILITY_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if packet["RETENTION_REPAIR_VERIFIED"] is not True:
        raise ValidationError("RETENTION_PATH_NOT_READY_FOR_NEXT_EXECUTION")
    tests = RUNNER_TESTS.read_text(encoding="utf-8") if RUNNER_TESTS.exists() else ""
    for name, expected in (
        ("RETENTION_VERIFIED_PATHS", RETENTION_PATHS),
        ("RETENTION_VERIFIED_PROPERTIES", RETENTION_PROPERTIES),
    ):
        block = packet[name]
        if tuple(block) != expected:
            raise ValidationError(f"{name} is {list(block)}; it must be {list(expected)}")
        for path, test in block.items():
            if f"def {test}(" not in tests:
                raise ValidationError(f"{path} names {test!r}, which no V7 runner test defines")
    policy = packet["PERSISTENCE_POLICY"]
    _fixed(
        policy,
        {
            "persist_if_gate_accepts": False,
            "human_review_required_before_persistence": True,
            "canonical_persistence": (
                "ONLY_AFTER_DETERMINISTIC_STAGES_1_TO_9_AND_SEPARATE_HUMAN_APPROVAL"
            ),
            "opportunity_created_by_this_packet": 0,
            "score_persisted": False,
            "independence_group_created": False,
            "stage_9_constructs_in_memory_only": True,
        },
        "PERSISTENCE_POLICY",
    )
    provenance = policy["provenance_the_first_revision_must_carry"]
    for item in ("the provider-strict projection record and its freeze commit",):
        if item not in provenance:
            raise ValidationError(f"the persistence policy does not name {item}")


def _check_accounting(packet: dict[str, Any]) -> None:
    accounting = packet["preparation_accounting"]
    for key in PREPARATION_ZERO:
        if accounting.get(key) != 0:
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V7 does 0")
    if accounting.get("DOCUMENTATION_FETCHES") != DOCUMENTATION_FETCHES:
        raise ValidationError("the documentation reads are not the ones gate 92 records")
    if packet["CANONICAL_COUNTERS"] != CANONICAL_COUNTERS:
        raise ValidationError("a canonical counter moved")


def _stage_5_schema(source: str) -> str | None:
    """The name stage 5 validates against, read from the syntax of the stage function."""
    tree = ast.parse(source)
    judge = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_execution"),
        None,
    )
    if judge is None:
        return None
    for node in ast.walk(judge):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "schema_violations"
            and len(node.args) == 2
        ):
            return getattr(node.args[1], "id", None)
    return None


def _check_runner(packet: dict[str, Any], parts: Any, parts_v1_4: Any) -> None:
    source = RUNNER.read_text(encoding="utf-8")
    _through(G81._check_single_call_site, source)
    _through(G81._check_no_post_processing, source)
    if _stage_5_schema(source) != "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2":
        raise ValidationError("the runner's stage 5 is not the full output schema v1.2.0")
    if "parameter name" in source:
        raise ValidationError("the runner names a key an earlier answer carried")
    module = runner()
    if module.EXPECTED["EXECUTION_PACKET_SHA256"] != packet["EXECUTION_PACKET_SHA256"]:
        raise ValidationError("the runner was prepared for another digest")
    for key, value in module.EXPECTED.items():
        if key in packet and packet[key] != value:
            raise ValidationError(
                f"the runner expects {key}={value!r} and V7 binds {packet[key]!r}"
            )
    if tuple(module.STAGES) != STAGES:
        raise ValidationError("the runner's stages are not the gate's")
    if list(inspect.signature(module.validate_execution).parameters) != ["result", "context"]:
        raise ValidationError("the runner's semantic gate can be injected")
    if module.APPROVAL_FILE.name != APPROVAL.name or module.PROMPT_DOCUMENT.name != PROMPT_V6.name:
        raise ValidationError("the runner reads its approval or its prompt from somewhere else")
    for index, digest in enumerate(SHAS):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != "EXECUTION_APPROVAL_ALREADY_CONSUMED":
                raise ValidationError(
                    f"the runner refuses V{index + 1} for the wrong reason"
                ) from exc
        else:
            raise ValidationError(f"the runner would execute V{index + 1}'s spent digest")
    try:
        module.refuse_if_consumed("0" * 64)
    except module.RefusedError as exc:
        raise ValidationError("the runner refuses an unseen digest") from exc
    if (
        module.unstated_semantic_rules(parts)
        or module.unstated_constraints(parts.system_instructions)
        or module.unstated_targets(parts)
    ):
        raise ValidationError(
            "the runner finds prompt v1.5.0 leaving a rule, bound or target unstated"
        )
    if module.unstated_targets(parts_v1_4) != ["evidence_bound_reasoning_summary"]:
        raise ValidationError("the runner's headroom check would pass prompt v1.4.0 under v1.2.0")


def validate() -> dict[str, Any]:
    packet = _load(PACKET)
    snap, parts, parts_v1_4 = snapshot()
    _check_identity_and_approval(packet)
    _check_predecessors(packet)
    _check_v6_reconfirmation(packet)
    _check_contract_and_gate(packet)
    _check_strict(packet)
    _check_prompt(packet, parts)
    _check_route(packet)
    _check_representation(packet, snap)
    wire = _check_request(packet, parts)
    _check_calls_and_timeout(packet)
    _check_cost(packet, wire)
    _check_verification(packet, wire)
    _check_preflight(packet)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet, parts, parts_v1_4)
    return packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v7.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _sentence(text: object) -> str:
    value = str(text).strip()
    value = value[:1].upper() + value[1:]
    return value if value.endswith((".", "!", "?")) else value + "."


def _cost(value: object) -> str:
    return f"{float(str(value)):.6f}".rstrip("0").rstrip(".")


def render_packet(packet: dict[str, Any]) -> str:
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    observed = packet["V6_OBSERVATION"]
    diff = packet["REQUEST_BODY_DIFFERENTIAL"]
    v6 = packet["V6_RECONFIRMATION"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v7",
        "",
        f"Prepared by {packet['prepared_by']} on {packet['prepared_at']}. "
        f"**{packet['PRIMARY_OUTCOME']}.**",
        "",
        f"**{_sentence(packet['approval_note'])}**",
        "",
        "## The approval surface",
        "",
        *_code(
            [
                f"EXECUTION_PACKET_ID                 {packet['EXECUTION_PACKET_ID']}",
                f"VERSION                             {packet['EXECUTION_PACKET_VERSION']}",
                f"SHA256                              {packet['EXECUTION_PACKET_SHA256']}",
                "",
                f"predecessor                         {packet['PREDECESSOR_EXECUTION_PACKET_ID']} "
                f"{packet['PREDECESSOR_EXECUTION_PACKET_SHA256']}",
                f"predecessor outcome                 {packet['PREDECESSOR_EXECUTION_OUTCOME']}, "
                "consumed",
                f"predecessor schema violation        {packet['PREDECESSOR_SCHEMA_VIOLATION']}",
                f"subject                             {packet['SUBJECT_KEY']}",
                "",
                f"provider                            {packet['PROVIDER_ID']}",
                f"route                               {packet['PROVIDER_ROUTE_SURFACE']} "
                "(synchronous, Commercial Terms)",
                f"model                               {packet['MODEL_ID']}",
                f"thinking                            {packet['THINKING']}",
                "",
                f"output schema                       {packet['OUTPUT_SCHEMA_VERSION']}",
                f"output schema sha256                {packet['OUTPUT_SCHEMA_SHA256']}",
                f"full canonical stage 5              {packet['FULL_CANONICAL_STAGE_5_VALIDATION']}",
                f"semantic gate                       {packet['OUTPUT_GATE_VERSION']}",
                f"gate implementation                 {packet['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}",
                f"prompt                              {packet['PROMPT_ID']}@{packet['PROMPT_VERSION']}",
                f"prompt sha256                       {packet['PROMPT_SHA256']}",
                f"reasoning summary                   hard maximum "
                f"{packet['REASONING_SUMMARY_HARD_MAX']}, generation target "
                f"{packet['REASONING_SUMMARY_GENERATION_TARGET']}",
                f"generation target ratio             {packet['GENERATION_TARGET_RATIO']}",
                f"representation sha256               {packet['REPRESENTATION_SHA256']}",
                "",
                f"provider strict mode                {str(packet['PROVIDER_STRICT_MODE']).lower()}",
                f"structured output mechanism         {packet['STRUCTURED_OUTPUT_MECHANISM']}",
                f"provider strict schema              {packet['PROVIDER_STRICT_SCHEMA_ID']}",
                f"provider strict schema sha256       {packet['PROVIDER_STRICT_SCHEMA_SHA256']}",
                f"capability profile                  {packet['STRICT_CAPABILITY_PROFILE_ID']}",
                f"capability profile sha256           {packet['STRICT_CAPABILITY_PROFILE_SHA256']}",
                f"projector sha256                    {packet['STRICT_PROJECTOR_IMPLEMENTATION_SHA256']}",
                f"projection tests sha256             {packet['STRICT_PROJECTION_TEST_SHA256']}",
                f"projection freeze commit            {packet['STRICT_PROJECTION_FREEZE_COMMIT']}",
                "",
                f"MAX_OUTPUT_TOKENS                   {packet['MAX_OUTPUT_TOKENS']}",
                f"MAX_MODEL_CALLS                     {packet['MAX_MODEL_CALLS']}",
                f"MAX_RETRIES                         {packet['MAX_RETRIES']}",
                f"timeout                             {packet['REQUEST_TIMEOUT']} s",
                "",
                f"WORST_CASE_CALL_COST                {_cost(packet['WORST_CASE_CALL_COST'])}",
                f"EXECUTION_COST_CEILING              {_cost(packet['EXECUTION_COST_CEILING'])}",
                "",
                "human_review_required               "
                f"{str(packet['HUMAN_REVIEW_REQUIRED']).lower()}",
                "canonical_persistence               "
                f"{packet['PERSISTENCE_POLICY']['canonical_persistence']}",
                "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7 "
                f"{str(packet['RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7']).lower()}",
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{str(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']).lower()}",
                "NEW_APPROVAL_REQUIRED               "
                f"{str(packet['NEW_APPROVAL_REQUIRED']).lower()}",
                "PREVIOUS_APPROVAL_REUSABLE          "
                f"{str(packet['PREVIOUS_APPROVAL_REUSABLE']).lower()}",
            ]
        ),
        "## What changed from V6",
        "",
        f"{_sentence(packet['strict_note'])} {_sentence(packet['structured_output_note'])}",
        "",
        "The request body, rebuilt through both runners over the same snapshot, differs from V6's "
        "in exactly these places: " + "; ".join(f"`{d}`" for d in diff["differences"]) + ". "
        f"V6's body: {diff['v6_body_characters']} characters; V7's: {diff['v7_body_characters']} "
        f"({diff['delta_characters']:+d}). Unchanged: "
        + ", ".join(f"`{u}`" for u in diff["unchanged"])
        + ".",
        "",
        "## V6, reconfirmed from what it kept",
        "",
        *_code(
            [
                f"stop reason              {v6['stop_reason']}",
                f"tokens                   {v6['input_tokens']} in, {v6['output_tokens']} out, "
                f"{v6['thinking_tokens']} thinking, {v6['total_tokens']} total",
                f"actual cost              {_cost(v6['actual_cost'])}",
                f"root keys                {v6['response_root_keys']} "
                f"({v6['declared_required_keys_present']} of {v6['declared_required_keys']} declared)",
                f"undeclared               {v6['undeclared_values']}",
                f"summary                  {v6['summary_characters']} "
                f"(target {v6['summary_generation_target']}, hard maximum "
                f"{v6['summary_hard_maximum']})",
                f"live v1.2.0 violations   {v6['live_v1_2_0_violations']}",
                f"unknown-property events  {v6['OBSERVED_UNKNOWN_PROPERTY_EVENTS_V6']}; rate "
                f"{v6['PROVIDER_UNKNOWN_PROPERTY_RATE']}",
            ]
        ),
        "## Cost, recomputed from the new request body",
        "",
        *_code(
            [
                f"request body             {basis['wire_characters']} characters  "
                f"(V6 {basis['v6_wire_characters']} {basis['delta_characters_over_v6']:+d})",
                f"input token estimate     {packet['INPUT_TOKEN_ESTIMATE']}  "
                f"({basis['wire_characters']} / {basis['chars_per_token']} x "
                f"{basis['conservative_multiplier']})",
                f"output token ceiling     {packet['OUTPUT_TOKEN_CEILING']}",
                f"total token ceiling      {packet['TOTAL_TOKEN_CEILING']}",
                f"input worst case         {_cost(packet['INPUT_WORST_CASE_COST'])}",
                f"output worst case        {_cost(packet['OUTPUT_WORST_CASE_COST'])}",
                f"total worst case         {_cost(packet['WORST_CASE_CALL_COST'])}",
                f"execution cost ceiling   {_cost(packet['EXECUTION_COST_CEILING'])}  "
                f"(headroom policy: {packet['HEADROOM_POLICY']})",
                f"previous ceiling (V6)    {_cost(packet['PREVIOUS_EXECUTION_COST_CEILING'])}  "
                f"({_cost(packet['CEILING_DELTA_OVER_PREVIOUS'])})",
            ]
        ),
        f"V6 estimated {observed['V6_INPUT_TOKEN_ESTIMATE']} input tokens and used "
        f"{observed['V6_ACTUAL_INPUT_TOKENS']}. {_sentence(basis['strict_note'])}",
        "",
        "## Synthetic answers through V7's stages",
        "",
        "| fixture | summary characters | must stop at | stopped at |",
        "|---|---|---|---|",
        *[
            f"| {row['fixture']} | {row['summary_characters']} | {row['must_stop_at'] or 'stage 9'} "
            f"| {row['stopped_at'] or 'stage 9 (' + str(row['outcome']) + ')'} |"
            for row in packet["V7_PREFLIGHT"]
        ],
        "",
        "## Accounting",
        "",
        *_code(
            [
                f"{key.lower():34s} {value}"
                for key, value in packet["preparation_accounting"].items()
                if key != "$comment"
            ]
        ),
        "Canonical counters, unchanged: "
        + " / ".join(str(v) for v in packet["CANONICAL_COUNTERS"].values())
        + ".",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        packet = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    text = render_packet(packet)
    if args.write:
        PACKET_MD.write_bytes(text.encode("utf-8"))
        print(f"wrote    {PACKET_MD.name}")
    if PACKET_MD.read_text(encoding="utf-8") != text:
        print(f"FAIL     {PACKET_MD.name} is not the rendering of its record")
        return 1
    print(
        "ok       packet V7 is V6's call with a strict tool over the frozen projection of schema v1.2.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
