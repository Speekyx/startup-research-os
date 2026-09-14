"""Mission 1.84.20, CI gate 95: execution packet V8, V7's request with a proven cost ceiling, frozen
and unapproved.

V7 was superseded before it was approved or executed: the figure it called its cost ceiling was a
body-based estimate plus the output maximum, while the provider adds a system prompt of undocumented
size under strict tool use. CI gate 94 proved a hard ceiling from documented bounds and recorded V7's
supersession. V8 is V7's request, byte for byte, with that ceiling, the estimate kept apart as a
planning figure, and both disclosed risks left for the operator to decide. This gate re-derives it:

    uv run python infrastructure/scripts/render_second_opportunity_execution_packet_v8.py --check

It refuses: bound fields that do not hash to the digest, a spent or superseded digest, an unreviewed
or missing field, an approval recorded by the preparing mission, or either risk accepted by it; V1 to
V6 edited or their consumption reset, V7 described as anything but superseded before execution, its
supersession or gate 94's record moved; a contract, gate, prompt, strict projection, freeze, route,
model, thinking, max_tokens, timeout, retention or persistence policy that moved; a request body that
is not V7's bytes; a cost figure that is not gate 94's, an estimate standing where the ceiling must,
or V7's cost field names back in the packet; a synthetic answer that does not stop where it must; a
runner with more than one call site, post-processing, a stage 5 other than the full contract, a guard
that renames V7's refusal, an approval check that does not demand both risk decisions, or one that
would execute V1 to V7; and any preparation call, TED byte or canonical counter that moved.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import inspect
import json
import pathlib
import sys
import tempfile
from collections.abc import Callable
from decimal import Decimal
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

from sros_llm_gateway.providers.anthropic import (  # noqa: E402
    STRUCTURED_TOOL_NAME,
    AnthropicProvider,
)
from sros_llm_gateway.providers.anthropic_strict import AnthropicStrictToolProvider  # noqa: E402
from sros_llm_gateway.types import ProviderInvalidRequestError  # noqa: E402

PACKET = DATA / "second-opportunity-synthesis-execution-packet-v8.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v8.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v8.json"
PACKET_V7 = DATA / "second-opportunity-synthesis-execution-packet-v7.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v8.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v8.py"
)
GATE_93 = SCRIPTS / "render_second_opportunity_execution_packet_v7.py"
GATE_94 = SCRIPTS / "render_second_opportunity_execution_cost_ceiling.py"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V8"
PACKET_VERSION = 8
PREPARED_BY = "mission-1.84.20"
THIS_MISSION = (1, 84, 20)
READY = "SECOND_OPPORTUNITY_EXECUTION_PACKET_V8_READY_FOR_OPERATOR_APPROVAL"
DOCUMENTATION_FETCHES = 12
SUPERSEDED = "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
CONSUMED = "EXECUTION_APPROVAL_ALREADY_CONSUMED"
RISK_FLAGS = (
    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8",
    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8",
)
#: The cost fields V7 carried under names that called an estimate a bound. None may return.
V7_COST_FIELDS = (
    "INPUT_TOKEN_ESTIMATE",
    "TOTAL_TOKEN_CEILING",
    "INPUT_WORST_CASE_COST",
    "OUTPUT_WORST_CASE_COST",
    "WORST_CASE_CALL_COST",
    "EXECUTION_COST_CEILING",
    "HEADROOM_POLICY",
    "TOKEN_ESTIMATION_BASIS",
)
#: The cost fields V8 takes from gate 94's record, each under the record's own name.
COST_FROM_RECORD = {
    "PLANNING_INPUT_TOKEN_ESTIMATE": "BODY_BASED_INPUT_TOKEN_ESTIMATE",
    "PLANNING_INPUT_COST_ESTIMATE": "PLANNING_INPUT_COST_ESTIMATE",
    "PLANNING_COST_ESTIMATE": "PLANNING_COST_ESTIMATE",
    "PLANNING_COST_ESTIMATE_CLASSIFICATION": "PLANNING_COST_ESTIMATE_CLASSIFICATION",
    "MAX_BILLABLE_INPUT_TOKENS": "MAX_BILLABLE_INPUT_TOKENS",
    "MAX_BILLABLE_INPUT_TOKENS_BASIS": "MAX_BILLABLE_INPUT_TOKENS_BASIS",
    "DATA_RESIDENCY_MULTIPLIER": "DATA_RESIDENCY_MULTIPLIER",
    "HARD_INPUT_COST_CEILING": "HARD_INPUT_COST_CEILING",
    "HARD_OUTPUT_COST_CEILING": "HARD_OUTPUT_COST_CEILING",
    "HARD_EXECUTION_COST_CEILING": "HARD_EXECUTION_COST_CEILING",
    "HARD_EXECUTION_COST_CEILING_PROVEN": "HARD_EXECUTION_COST_CEILING_PROVEN",
    "UNKNOWN_COST_CATEGORIES": "UNKNOWN_COST_CATEGORIES",
    "REQUEST_BODY_CHARACTERS": "REQUEST_BODY_CHARACTERS",
    "PRICING_VERSION": "PRICING_VERSION",
    "PRICE_PER_1K": "PRICE_PER_1K",
}


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Gate 93, V7's gate, whose checks of what did not move V8 reuses rather than copies; gate 94, the
#: authority on cost and on V7's supersession; gate 81, whose frozen helpers every packet reuses.
G93 = _module("gate_93_for_packet_v8", GATE_93)
G94 = _module("gate_94_for_packet_v8", GATE_94)
G81 = G93.G81

V7_ID, V7_SHA256 = G94.V7_ID, G94.V7_SHA256
SHAS, IDS = G93.SHAS, G93.IDS
V6_ID, V6_SHA256, V6_OUTCOME, V6_VIOLATIONS = (
    G93.V6_ID,
    G93.V6_SHA256,
    G93.V6_OUTCOME,
    G93.V6_VIOLATIONS,
)
STAGES = G93.STAGES
PREPARATION_ZERO = G93.PREPARATION_ZERO
RETENTION_PATHS = G93.RETENTION_PATHS
RETENTION_PROPERTIES = G93.RETENTION_PROPERTIES
CANONICAL_COUNTERS = G93.CANONICAL_COUNTERS
CAPABILITY_NEGATIVES = G93.CAPABILITY_NEGATIVES

#: What the V8 digest binds: V7's fields without its cost figures, its predecessor fields and its
#: residual-risk flag; with V7 as the superseded predecessor and V6 as the last one executed, V7's
#: supersession, the request body's identity, gate 94's cost figures and both risk flags.
DIGEST_FIELDS: tuple[str, ...] = (
    *(
        f
        for f in G93.DIGEST_FIELDS
        if f
        not in (
            *V7_COST_FIELDS,
            "PREDECESSOR_EXECUTION_OUTCOME",
            "PREDECESSOR_SCHEMA_VIOLATION",
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7",
        )
    ),
    "PREDECESSOR_STATUS",
    "PREDECESSOR_EXECUTED",
    "PREDECESSOR_APPROVED",
    "LAST_EXECUTED_PREDECESSOR_ID",
    "LAST_EXECUTED_PREDECESSOR_SHA256",
    "LAST_EXECUTED_PREDECESSOR_OUTCOME",
    "LAST_EXECUTED_PREDECESSOR_SCHEMA_VIOLATION",
    "SUPERSEDED_EXECUTION_PACKETS",
    "V7_SUPERSESSION_RECORD_SHA256",
    "REQUEST_BODY_SHA256",
    *COST_FROM_RECORD,
    "COST_CEILING_RECORD_SHA256",
    *RISK_FLAGS,
)
#: Everything else the packet may carry. Closed, as V7's was.
UNBOUND_FIELDS: tuple[str, ...] = (
    *(
        f
        for f in G93.UNBOUND_FIELDS
        if f
        not in (
            "TOKEN_ESTIMATION_BASIS",
            "cost_ceiling_basis",
            "COST_NOT_EXPECTED_ACTUAL",
            "cost_note",
            "PREVIOUS_EXECUTION_COST_CEILING",
            "CEILING_DELTA_OVER_PREVIOUS",
            "CEILING_OVER_PREVIOUS_CEILING",
            "LARGER_THAN_PREVIOUS_CEILING",
            "ceiling_delta_note",
            "V6_OBSERVATION",
            "V7_PREFLIGHT",
        )
    ),
    "PLANNING_ESTIMATION_BASIS",
    "cost_note",
    "V7_RECONFIRMATION",
    "V8_PREFLIGHT",
    "OBSERVED_USAGE_NOT_USED",
    "supersession_note",
    "risk_note",
)


class ValidationError(RuntimeError):
    """The packet disagrees with V7, with gate 94, or with live code."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def text_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _through(check: Callable[..., Any], *args: Any) -> Any:
    """Run one of gate 93's or gate 94's checks, and report its refusal as this gate's."""
    try:
        return check(*args)
    except (G93.ValidationError, G94.ValidationError, G81.ValidationError) as exc:
        raise ValidationError(str(exc)) from exc


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


def packet_digest(packet: dict[str, Any]) -> str:
    """Recompute the V8 execution digest from the packet's own bound fields."""
    bound: dict[str, object] = {}
    for key in DIGEST_FIELDS:
        if key not in packet:
            raise ValidationError(f"the execution packet has no {key!r} to bind")
        bound[key] = G81._bindable(packet[key])
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_gate() -> Any:
    """Gate 87, the one authority on gate v1.4.0's implementation digest."""
    return G93.freeze_gate()


def snapshot() -> tuple[Any, Any, Any]:
    """Gate 81's authenticated snapshot, and prompts v1.5.0 and v1.4.0 rendered over it."""
    return _through(G93.snapshot)


def runner() -> Any:
    return _module("execution_runner_v8_for_gate", RUNNER)


def cost_record() -> tuple[dict[str, Any], dict[str, Any]]:
    """Gate 94's validated cost record and V7's supersession."""
    return _through(G94.validate)


# --------------------------------------------------------------------------- derived blocks


def request_bodies(parts: Any, packet: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """V7's body, through V7's runner and packet, and V8's, through V8's: both built, never sent."""
    module = runner()
    try:
        v8 = module.request_body(parts, packet)
    except (ProviderInvalidRequestError, module.RefusedError) as exc:
        raise ValidationError(
            f"STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE: V8's request cannot be built: {exc}"
        ) from exc
    return G93.runner().request_body(parts, _load(PACKET_V7)), v8


def request_differential(parts: Any, packet: dict[str, Any]) -> dict[str, object]:
    """V7's body against V8's: byte for byte, and structurally wherever they differ."""
    v7, v8 = request_bodies(parts, packet)
    wire7, wire8 = json.dumps(v7), json.dumps(v8)
    differences = [
        f"{key}: {'added' if key not in v7 else 'removed' if key not in v8 else 'changed'}"
        for key in sorted(set(v7) | set(v8))
        if v7.get(key) != v8.get(key)
    ]
    if wire7 != wire8 and not differences:
        differences = ["serialised bytes differ with no structural difference"]
    return {
        "v7_body_characters": len(wire7),
        "v8_body_characters": len(wire8),
        "v7_body_sha256": hashlib.sha256(wire7.encode("utf-8")).hexdigest(),
        "v8_body_sha256": hashlib.sha256(wire8.encode("utf-8")).hexdigest(),
        "byte_identical": wire7 == wire8,
        "differences": differences,
        "REQUEST_BODY_DIFFERENCES_V7_TO_V8": len(differences),
        "unapproved_drift": list(differences),
        "tool_choice": v8.get("tool_choice"),
    }


def preflight_results() -> list[dict[str, object]]:
    """Gate 89's synthetic answers, and one extra root key, through V8's own stages."""
    module = runner()
    fx = _module("fixtures_for_packet_v8", G93.FIXTURES)
    g89 = _module("gate_89_fixtures_for_packet_v8", G93.GATE_89)
    gate_76 = _module("gate_76_for_packet_v8", G93.GATE_76)
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
            **dict.fromkeys(RISK_FLAGS, False),
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
    if recomputed in (*SHAS, V7_SHA256):
        raise ValidationError("V8 carries a spent or superseded predecessor's digest")
    note = str(packet["approval_note"])
    for word in ("egress", "V6", "V7", "superseded", "beside", "residual", "timeout"):
        if word not in note:
            raise ValidationError(
                "the approval note does not keep this approval apart from V1's to V6's spent "
                "approvals, from V7, which never had one, from both risk decisions and from TED "
                "egress"
            )
    if (
        packet["EXECUTION_ENVELOPE_DECISION_SHA256"]
        != _load(PACKET_V7)["EXECUTION_ENVELOPE_DECISION_SHA256"]
    ):
        raise ValidationError("the envelope decision moved from V7")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = G81._mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V8 recorded by the mission that prepared it. Preparing a packet "
                "authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V8's")
    return recomputed


def _check_predecessors(packet: dict[str, Any]) -> None:
    packets = [_load(p) for p in G93.PACKETS]
    records = [_load(p) for p in G93.RECORDS]
    for index, (frozen, digest) in enumerate(zip(packets, SHAS, strict=True)):
        if frozen["EXECUTION_PACKET_SHA256"] != digest:
            raise ValidationError(f"V{index + 1}'s packet digest moved")
        if frozen["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
            raise ValidationError(
                f"the frozen V{index + 1} packet was edited to record an approval"
            )
    if G93.G90.packet_digest(packets[5]) != V6_SHA256:
        raise ValidationError("V6's bound fields no longer hash to its digest")
    for index, record in enumerate(records):
        if record["EXECUTION_APPROVAL_CONSUMED"] is not True:
            raise ValidationError(f"V{index + 1}'s consumption was reset")
    _fixed(
        records[5],
        {
            "execution_packet_sha256": V6_SHA256,
            "PRIMARY_OUTCOME": V6_OUTCOME,
            "CANONICAL_PERSISTENCE": False,
            "SCHEMA_VIOLATIONS": V6_VIOLATIONS,
            "FAILED_STAGE": "5_schema_validation_v1_2_0",
        },
        "V6's record",
    )
    _through(G93._validates, G93.GATE_91, "91")
    _, supersession = cost_record()
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V7_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V7_SHA256,
            "PREDECESSOR_STATUS": "SUPERSEDED_BEFORE_EXECUTION",
            "PREDECESSOR_EXECUTED": False,
            "PREDECESSOR_APPROVED": False,
            "PREDECESSOR_APPROVAL_CONSUMED": False,
            "LAST_EXECUTED_PREDECESSOR_ID": V6_ID,
            "LAST_EXECUTED_PREDECESSOR_SHA256": V6_SHA256,
            "LAST_EXECUTED_PREDECESSOR_OUTCOME": V6_OUTCOME,
            "LAST_EXECUTED_PREDECESSOR_SCHEMA_VIOLATION": "UNKNOWN_ROOT_PROPERTY",
            "CONSUMED_EXECUTION_PACKETS": [
                {"id": ident, "sha256": digest, "outcome": record["PRIMARY_OUTCOME"]}
                for ident, digest, record in zip(IDS, SHAS, records, strict=True)
            ],
            "SUPERSEDED_EXECUTION_PACKETS": [
                {
                    "id": V7_ID,
                    "sha256": V7_SHA256,
                    "status": supersession["STATUS"],
                    "reason": supersession["REASON"],
                }
            ],
            "V7_SUPERSESSION_RECORD_SHA256": text_sha(G94.SUPERSESSION),
        },
        "packet",
    )


def _check_v7_reconfirmation(packet: dict[str, Any]) -> None:
    record, _ = cost_record()
    if packet["V7_RECONFIRMATION"] != record["V7_COST_RECONFIRMATION"]:
        raise ValidationError("V7_RECONFIRMATION is not what gate 94 re-derives from V7")


# --------------------------------------------------------------------------- what did not move


def _check_request(packet: dict[str, Any], parts: Any) -> None:
    """The body V8 would send: V7's, byte for byte."""
    module = runner()
    _v7_body, body = request_bodies(parts, packet)
    differential = request_differential(parts, packet)
    if (
        not differential["byte_identical"]
        or differential["differences"]
        or differential["REQUEST_BODY_DIFFERENCES_V7_TO_V8"] != 0
    ):
        raise ValidationError(
            f"V8_REQUEST_BODY_HAS_UNAPPROVED_DRIFT: {differential['differences'] or 'bytes moved'}"
        )
    if differential["v8_body_sha256"] != G94.V7_REQUEST_BODY_SHA256:
        raise ValidationError("V8_REQUEST_BODY_HAS_UNAPPROVED_DRIFT: V7's body itself moved")
    if packet["REQUEST_BODY_DIFFERENTIAL"] != differential:
        raise ValidationError("REQUEST_BODY_DIFFERENTIAL is not the rebuilt comparison")
    _fixed(
        packet,
        {
            "REQUEST_BODY_SHA256": differential["v8_body_sha256"],
            "REQUEST_BODY_CHARACTERS": differential["v8_body_characters"],
        },
        "packet",
    )
    if body.get("thinking") != {"type": "disabled"}:
        raise ValidationError(f"THINKING_CONTROL_NO_LONGER_VALID: {body.get('thinking')!r}")
    if body.get("max_tokens") != packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError(f"the adapter sends max_tokens {body.get('max_tokens')}")
    if body.get("tool_choice") != {"type": "tool", "name": STRUCTURED_TOOL_NAME}:
        raise ValidationError(
            "STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE: the tool is not forced"
        )
    problems = module.strict_tool_problems(body)
    if problems:
        raise ValidationError(
            f"STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE: {problems}"
        )
    selectors = G94.billing_selectors(body)
    for key, required in G94.SELECTORS_REQUIRED.items():
        if selectors[key] != required:
            raise ValidationError(
                f"the body carries {key}={selectors[key]!r}, and the ceiling was proven for "
                f"{required!r}"
            )
    provider = module.build_provider(
        packet, module._NoSend(), api_key="gate-probe-not-a-credential"
    )
    if type(provider) is not AnthropicStrictToolProvider:
        raise ValidationError("the runner's adapter is not the strict one")
    plain = AnthropicProvider(api_key="gate-probe-not-a-credential", transport=module._NoSend())
    if provider._headers() != plain._headers():
        raise ValidationError("the strict adapter sends a header the plain one does not")


def _check_calls_and_timeout(packet: dict[str, Any]) -> None:
    _through(G93._check_calls_and_timeout, packet)
    v7 = _load(PACKET_V7)
    if packet["REQUEST_TIMEOUT"] != v7["REQUEST_TIMEOUT"] or packet["REQUEST_TIMEOUT"] != 60.0:
        raise ValidationError("the timeout moved, and this mission changes no timeout")
    _fixed(
        packet["TIMEOUT"],
        {
            "TIMEOUT_CHANGED_BY_THIS_MISSION": False,
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8": False,
        },
        "TIMEOUT",
    )


def _check_cost(packet: dict[str, Any]) -> None:
    record, _ = cost_record()
    block = record["COST_RECORD"]
    for key in V7_COST_FIELDS:
        if key in packet:
            raise ValidationError(f"ESTIMATE_CALLED_HARD_CEILING: V7's field {key} is back")
    for key, source in COST_FROM_RECORD.items():
        if packet[key] != block[source]:
            raise ValidationError(f"{key} is {packet[key]!r}; gate 94 derives {block[source]!r}")
    if packet["COST_CEILING_RECORD_SHA256"] != text_sha(G94.RECORD):
        raise ValidationError("the packet was prepared on another cost-ceiling record")
    if (
        packet["HARD_EXECUTION_COST_CEILING_PROVEN"] is not True
        or packet["UNKNOWN_COST_CATEGORIES"]
    ):
        raise ValidationError("TRUE_EXECUTION_COST_CEILING_NOT_ESTABLISHED")
    if Decimal(str(packet["PLANNING_COST_ESTIMATE"])) >= Decimal(
        str(packet["HARD_EXECUTION_COST_CEILING"])
    ):
        raise ValidationError("ESTIMATE_CALLED_HARD_CEILING: the estimate is not below the ceiling")
    if packet["PLANNING_COST_ESTIMATE_CLASSIFICATION"] != "PLANNING_ESTIMATE":
        raise ValidationError(
            "ESTIMATE_CALLED_HARD_CEILING: the planning figure is labelled a bound"
        )
    for key in ("PRICING_VERSION", "PRICE_PER_1K"):
        if packet[key] != _load(PACKET_V7)[key]:
            raise ValidationError(f"{key} moved from V7")
    _fixed(
        packet["PLANNING_ESTIMATION_BASIS"],
        {
            "classification": "PLANNING_ESTIMATE",
            "chars_per_token": G93.CHARS_PER_TOKEN,
            "conservative_multiplier": G93.CONSERVATIVE_MULTIPLIER,
            "wire_characters": packet["REQUEST_BODY_CHARACTERS"],
            "strict_format_prompt_tokens": "NOT_ESTABLISHED",
            "covers_the_strict_format_prompt": False,
            "is_a_bound": False,
        },
        "PLANNING_ESTIMATION_BASIS",
    )
    _fixed(
        packet["OBSERVED_USAGE_NOT_USED"],
        {"USED_FOR_THE_HARD_CEILING": False, "USED_FOR_THE_PLANNING_ESTIMATE": False},
        "OBSERVED_USAGE_NOT_USED",
    )


def _check_verification(packet: dict[str, Any]) -> None:
    """What verification found on the preparing machine, checked for agreement with CI's facts."""
    _fixed(
        packet["PREPARATION_VERIFICATION"],
        {
            "representation_sha256": G93.REPRESENTATION_SHA256,
            "representation_characters": G93.REPRESENTATION_CHARACTERS,
            "prompt_sha256": G93.PROMPT_SHA256,
            "selected_packet_id": packet["SELECTED_PACKET_ID"],
            "approved_evidence_rows": len(packet["APPROVED_EVIDENCE_IDS"]),
            "provider_posture": "APPROVED",
            "ted_external_model_transmission": "PERMITTED_WITH_CONDITIONS",
            "live_packet_gate": "AVAILABLE",
            "request_thinking": {"type": "disabled"},
            "request_max_tokens": packet["MAX_OUTPUT_TOKENS"],
            "request_strict_tool": "FROZEN_PROJECTION_STRICT_FORCED",
            "request_body_characters": packet["REQUEST_BODY_CHARACTERS"],
            "request_body_sha256": packet["REQUEST_BODY_SHA256"],
            "unstated_generation_constraints": 0,
            "unstated_generation_relevant_semantic_rules": 0,
            "unstated_generation_targets": 0,
            "output_schema_sha256": G93.CANONICAL_SCHEMA_SHA256,
            "provider_strict_schema_sha256": packet["PROVIDER_STRICT_SCHEMA_SHA256"],
            "semantic_gate_implementation_sha256": packet["SEMANTIC_GATE_IMPLEMENTATION_SHA256"],
            "reasoning_summary_hard_max_and_target": [1500, 1200],
            "pricing_version": packet["PRICING_VERSION"],
            "hard_execution_cost_ceiling": packet["HARD_EXECUTION_COST_CEILING"],
            "planning_cost_estimate": packet["PLANNING_COST_ESTIMATE"],
            "source_metadata_context_sha256": packet["SOURCE_METADATA_CONTEXT_SHA256"],
            "trusted_context_sha256": packet["TRUSTED_CONTEXT_SHA256"],
            "stages_6_to_9_ready": True,
            "v1_to_v6_guards_refuse_their_digests": True,
            "v7_refused_as_superseded": True,
            "guard_permits_an_unseen_digest": True,
            "operator_approval": "OPERATOR_APPROVAL_NOT_RECORDED",
        },
        "PREPARATION_VERIFICATION",
    )
    preparation = _load(G93.PREPARATION)
    if packet["PREPARATION_VERSION"] != preparation["artifact_version"]:
        raise ValidationError("the packet names a preparation that is not the current one")
    selected = next(
        (p for p in preparation["packets"] if p.get("subject") == packet["SUBJECT_KEY"]), None
    )
    if selected is None or selected["packet_id"] != packet["SELECTED_PACKET_ID"]:
        raise ValidationError("the current preparation does not carry the selected packet")
    if selected["external_synthesis"]["availability"] != "AVAILABLE":
        raise ValidationError("TED_EGRESS_NO_LONGER_AVAILABLE in the current preparation")


def _check_preflight(packet: dict[str, Any]) -> None:
    record = _through(G93._validates, G93.GATE_89, "89")
    if record["OUTCOME"] != "DETERMINISTIC_STAGE_6_TO_9_PATH_READY":
        raise ValidationError("DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY")
    live = preflight_results()
    if packet["V8_PREFLIGHT"] != live:
        raise ValidationError("V8_PREFLIGHT is not what V8's stages give over the fixtures")
    for row in live:
        if row["stopped_at"] != row["must_stop_at"]:
            raise ValidationError(
                f"DETERMINISTIC_STAGE_5_TO_9_PATH_NOT_READY: {row['fixture']} stopped at "
                f"{row['stopped_at']} and must stop at {row['must_stop_at']}"
            )
    by_id = {row["fixture"]: row for row in live}
    if by_id["F_LONG_SUMMARY_POSITIVE"]["summary_characters"] != 1189:
        raise ValidationError("the long positive summary is not 1189 characters")
    if by_id["H_SUMMARY_AT_THE_NEW_BOUND"]["summary_characters"] != 1500:
        raise ValidationError("the summary at the bound is not 1500 characters")
    if by_id["I_SUMMARY_ONE_OVER_THE_NEW_BOUND"]["stopped_at"] != "5_schema_validation_v1_2_0":
        raise ValidationError("a 1501-character summary no longer stops at stage 5")
    if by_id["J_EXTRA_ROOT_PROPERTY_REFUSED_AT_LOCAL_STAGE_5"]["reasons"] != V6_VIOLATIONS:
        raise ValidationError(
            "an extra root key is no longer refused by the full contract at stage 5"
        )


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
                raise ValidationError(
                    f"RETENTION_PATH_NOT_READY_FOR_NEXT_EXECUTION: {path} names {test!r}, which no "
                    "V8 runner test defines"
                )
    if packet["PERSISTENCE_POLICY"] != _load(PACKET_V7)["PERSISTENCE_POLICY"]:
        raise ValidationError("the persistence policy moved from V7")


def _check_accounting(packet: dict[str, Any]) -> None:
    accounting = packet["preparation_accounting"]
    for key in PREPARATION_ZERO:
        if accounting.get(key) != 0:
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V8 does 0")
    if accounting.get("DOCUMENTATION_FETCHES") != DOCUMENTATION_FETCHES:
        raise ValidationError("the documentation reads are not the ones gate 94 records")
    if packet["CANONICAL_COUNTERS"] != CANONICAL_COUNTERS:
        raise ValidationError("a canonical counter moved")


def _check_approval_behaviour(module: Any, packet: dict[str, Any]) -> None:
    """The runner's approval check, exercised on synthetic approvals written to a temporary
    directory and never beside the packet: both risks decided, and both accepted, or nothing."""
    base = {
        "EXECUTION_PACKET_ID": PACKET_ID,
        "EXECUTION_PACKET_VERSION": PACKET_VERSION,
        "EXECUTION_PACKET_SHA256": packet["EXECUTION_PACKET_SHA256"],
        "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
        "approved_by": "gate 95",
        "operator_statement": "a synthetic approval, never written beside the packet",
    }
    residual, timeout = RISK_FLAGS
    cases: list[tuple[dict[str, object], str | None]] = [
        ({}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ({residual: True}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ({timeout: True}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ({residual: "yes", timeout: True}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ({residual: False, timeout: True}, "RESIDUAL_SEMANTIC_LIMITATION_NOT_ACCEPTED"),
        ({residual: True, timeout: False}, "STRICT_FIRST_REQUEST_TIMEOUT_RISK_NOT_ACCEPTED"),
        ({residual: True, timeout: True}, None),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / APPROVAL.name
        module.APPROVAL_FILE = path
        for extra, code in cases:
            path.write_text(json.dumps({**base, **extra}), encoding="utf-8")
            try:
                module.check_approval(str(packet["EXECUTION_PACKET_SHA256"]))
            except module.RefusedError as exc:
                if exc.code != code:
                    raise ValidationError(
                        f"the runner's approval check refuses {extra} as {exc.code}, and it must "
                        f"say {code}"
                    ) from exc
            else:
                if code is not None:
                    raise ValidationError(
                        "the runner's approval check accepts an approval that does not decide and "
                        f"accept both risks: {extra}"
                    )


def _check_runner(packet: dict[str, Any], parts: Any, parts_v1_4: Any) -> None:
    source = RUNNER.read_text(encoding="utf-8")
    _through(G81._check_single_call_site, source)
    _through(G81._check_no_post_processing, source)
    if G93._stage_5_schema(source) != "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2":
        raise ValidationError("the runner's stage 5 is not the full output schema v1.2.0")
    if "parameter name" in source:
        raise ValidationError("the runner names a key an earlier answer carried")
    module = runner()
    if module.EXPECTED["EXECUTION_PACKET_SHA256"] != packet["EXECUTION_PACKET_SHA256"]:
        raise ValidationError("the runner was prepared for another digest")
    for key, value in module.EXPECTED.items():
        if key in packet and packet[key] != value:
            raise ValidationError(
                f"the runner expects {key}={value!r} and V8 binds {packet[key]!r}"
            )
    if tuple(module.STAGES) != STAGES:
        raise ValidationError("the runner's stages are not the gate's")
    if list(inspect.signature(module.validate_execution).parameters) != ["result", "context"]:
        raise ValidationError("the runner's semantic gate can be injected")
    if module.APPROVAL_FILE.name != APPROVAL.name or module.PROMPT_DOCUMENT.name != (
        G93.PROMPT_V6.name
    ):
        raise ValidationError("the runner reads its approval or its prompt from somewhere else")
    if tuple(module.RISK_DECISIONS) != RISK_FLAGS:
        raise ValidationError("the runner's approval does not demand both risk decisions")
    if module.COST_SELECTORS_REQUIRED != G94.SELECTORS_REQUIRED:
        raise ValidationError("the runner checks the body against other cost selectors")
    _check_approval_behaviour(runner(), packet)
    for index, digest in enumerate(SHAS):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != CONSUMED:
                raise ValidationError(f"the runner refuses V{index + 1} as {exc.code}") from exc
        else:
            raise ValidationError(f"the runner would execute V{index + 1}'s spent digest")
    try:
        module.refuse_if_consumed(V7_SHA256)
    except module.RefusedError as exc:
        if exc.code != SUPERSEDED:
            raise ValidationError(
                f"the runner refuses V7 as {exc.code}, not as superseded"
            ) from exc
    else:
        raise ValidationError("V7_STILL_EXECUTABLE: the V8 runner's guard lets V7's digest through")
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
    _check_v7_reconfirmation(packet)
    _through(G93._check_v6_reconfirmation, packet)
    _through(G93._check_contract_and_gate, packet)
    _through(G93._check_strict, packet)
    _through(G93._check_prompt, packet, parts)
    _through(G93._check_route, packet)
    _through(G93._check_representation, packet, snap)
    _check_request(packet, parts)
    _check_calls_and_timeout(packet)
    _check_cost(packet)
    _check_verification(packet)
    _check_preflight(packet)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet, parts, parts_v1_4)
    return packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v8.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _sentence(text: object) -> str:
    value = str(text).strip()
    value = value[:1].upper() + value[1:]
    return value if value.endswith((".", "!", "?")) else value + "."


def _flag(value: object) -> str:
    return str(value).lower()


def render_packet(packet: dict[str, Any]) -> str:
    v7 = packet["V7_RECONFIRMATION"]
    diff = packet["REQUEST_BODY_DIFFERENTIAL"]
    timeout = packet["TIMEOUT"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v8",
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
                f"immediate predecessor               {packet['PREDECESSOR_EXECUTION_PACKET_ID']} "
                f"{packet['PREDECESSOR_EXECUTION_PACKET_SHA256']}",
                f"its status                          {packet['PREDECESSOR_STATUS']} "
                f"(executed {_flag(packet['PREDECESSOR_EXECUTED'])}, approved "
                f"{_flag(packet['PREDECESSOR_APPROVED'])}, consumed "
                f"{_flag(packet['PREDECESSOR_APPROVAL_CONSUMED'])})",
                f"last executed predecessor           {packet['LAST_EXECUTED_PREDECESSOR_ID']} "
                f"{packet['LAST_EXECUTED_PREDECESSOR_SHA256']}",
                f"its outcome                         {packet['LAST_EXECUTED_PREDECESSOR_OUTCOME']}"
                f", {packet['LAST_EXECUTED_PREDECESSOR_SCHEMA_VIOLATION']}",
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
                f"provider strict mode                {_flag(packet['PROVIDER_STRICT_MODE'])}",
                f"structured output mechanism         {packet['STRUCTURED_OUTPUT_MECHANISM']}",
                f"provider strict schema              {packet['PROVIDER_STRICT_SCHEMA_ID']}",
                f"provider strict schema sha256       {packet['PROVIDER_STRICT_SCHEMA_SHA256']}",
                f"capability profile                  {packet['STRICT_CAPABILITY_PROFILE_ID']}",
                f"capability profile sha256           {packet['STRICT_CAPABILITY_PROFILE_SHA256']}",
                f"projection freeze commit            {packet['STRICT_PROJECTION_FREEZE_COMMIT']}",
                "",
                f"request body                        {packet['REQUEST_BODY_CHARACTERS']} characters, "
                f"sha256 {packet['REQUEST_BODY_SHA256']}",
                f"MAX_OUTPUT_TOKENS                   {packet['MAX_OUTPUT_TOKENS']}",
                f"MAX_MODEL_CALLS                     {packet['MAX_MODEL_CALLS']}",
                f"MAX_RETRIES                         {packet['MAX_RETRIES']}",
                f"timeout                             {packet['REQUEST_TIMEOUT']} s",
                "",
                f"PLANNING_INPUT_TOKEN_ESTIMATE       {packet['PLANNING_INPUT_TOKEN_ESTIMATE']}",
                f"PLANNING_COST_ESTIMATE              {packet['PLANNING_COST_ESTIMATE']}  "
                f"({packet['PLANNING_COST_ESTIMATE_CLASSIFICATION']})",
                f"MAX_BILLABLE_INPUT_TOKENS           {packet['MAX_BILLABLE_INPUT_TOKENS']}  "
                f"({packet['MAX_BILLABLE_INPUT_TOKENS_BASIS']})",
                f"DATA_RESIDENCY_MULTIPLIER           {packet['DATA_RESIDENCY_MULTIPLIER']}",
                f"HARD_INPUT_COST_CEILING             {packet['HARD_INPUT_COST_CEILING']}",
                f"HARD_OUTPUT_COST_CEILING            {packet['HARD_OUTPUT_COST_CEILING']}",
                f"HARD_EXECUTION_COST_CEILING         {packet['HARD_EXECUTION_COST_CEILING']}",
                "HARD_EXECUTION_COST_CEILING_PROVEN  "
                f"{_flag(packet['HARD_EXECUTION_COST_CEILING_PROVEN'])}",
                "",
                f"human_review_required               {_flag(packet['HUMAN_REVIEW_REQUIRED'])}",
                "canonical_persistence               "
                f"{packet['PERSISTENCE_POLICY']['canonical_persistence']}",
                "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8      "
                f"{_flag(packet['RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8'])}",
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8 "
                f"{_flag(packet['STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8'])}",
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{_flag(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED'])}",
                f"NEW_APPROVAL_REQUIRED               {_flag(packet['NEW_APPROVAL_REQUIRED'])}",
                "PREVIOUS_APPROVAL_REUSABLE          "
                f"{_flag(packet['PREVIOUS_APPROVAL_REUSABLE'])}",
            ]
        ),
        "## What changed from V7",
        "",
        f"{_sentence(packet['supersession_note'])}",
        "",
        "The request body, rebuilt through V7's runner and V8's over the same snapshot, is "
        f"{'byte-identical' if diff['byte_identical'] else 'NOT identical'}: "
        f"{diff['v8_body_characters']} characters, sha256 `{diff['v8_body_sha256']}`, "
        f"{diff['REQUEST_BODY_DIFFERENCES_V7_TO_V8']} differences.",
        "",
        "## Cost: an estimate, and a ceiling",
        "",
        f"{_sentence(packet['cost_note'])}",
        "",
        *_code(
            [
                f"request body                 {packet['REQUEST_BODY_CHARACTERS']} characters",
                f"planning input estimate      {packet['PLANNING_INPUT_TOKEN_ESTIMATE']} tokens, "
                f"{packet['PLANNING_INPUT_COST_ESTIMATE']}",
                f"planning cost estimate       {packet['PLANNING_COST_ESTIMATE']}  (not a bound)",
                f"max billable input           {packet['MAX_BILLABLE_INPUT_TOKENS']} tokens",
                f"hard input cost ceiling      {packet['HARD_INPUT_COST_CEILING']}",
                f"hard output cost ceiling     {packet['HARD_OUTPUT_COST_CEILING']}",
                f"hard execution cost ceiling  {packet['HARD_EXECUTION_COST_CEILING']}",
                f"unknown cost categories      {packet['UNKNOWN_COST_CATEGORIES']}",
                f"pricing                      {packet['PRICING_VERSION']}",
            ]
        ),
        "## V7, reconfirmed and superseded",
        "",
        *_code(
            [
                f"packet                       {v7['EXECUTION_PACKET_ID']} v"
                f"{v7['EXECUTION_PACKET_VERSION']} {v7['EXECUTION_PACKET_SHA256_RECOMPUTED']}",
                f"approval recorded            {_flag(v7['approval_recorded'])}",
                f"its EXECUTION_COST_CEILING   {v7['packet_execution_cost_ceiling']}  "
                "(ESTIMATE_NOT_PROVEN_HARD_CEILING)",
                f"strict prompt tokens         {v7['strict_mode_injected_system_prompt_tokens']}",
                f"status                       {packet['PREDECESSOR_STATUS']}",
            ]
        ),
        "## Two risks for the approval to decide",
        "",
        f"{_sentence(packet['risk_note'])}",
        "",
        *_code(
            [
                f"request timeout                    {timeout['REQUEST_TIMEOUT_SECONDS']} s, "
                f"changed {_flag(timeout['TIMEOUT_CHANGED_BY_THIS_MISSION'])}",
                "first grammar compilation latency  "
                f"{timeout['FIRST_REQUEST_GRAMMAR_COMPILATION_LATENCY']}",
                f"provider compilation timeout       {timeout['PROVIDER_COMPILATION_TIMEOUT_SECONDS']} s",
                "retries                            0",
            ]
        ),
        "## Synthetic answers through V8's stages",
        "",
        "| fixture | summary characters | must stop at | stopped at |",
        "|---|---|---|---|",
        *[
            f"| {row['fixture']} | {row['summary_characters']} | {row['must_stop_at'] or 'stage 9'} "
            f"| {row['stopped_at'] or 'stage 9 (' + str(row['outcome']) + ')'} |"
            for row in packet["V8_PREFLIGHT"]
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
    text = render_packet(copy.deepcopy(packet))
    if args.write:
        PACKET_MD.write_bytes(text.encode("utf-8"))
        print(f"wrote    {PACKET_MD.name}")
    if not PACKET_MD.exists() or PACKET_MD.read_text(encoding="utf-8") != text:
        print(f"FAIL     {PACKET_MD.name} is not the rendering of its record")
        return 1
    print("ok       packet V8 is V7's request, byte for byte, with a proven cost ceiling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
