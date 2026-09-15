"""Mission 1.84.23, CI gate 100: execution packet V10, V9's request with prompt v1.6.0, frozen and
unapproved.

V9 was executed once, and gate v1.4.0 refused its answer at stage 6: one concept in an asserted field
that no supplied statement supports, and six requests for evidence written as instructions. The
operator kept the schema, the gate, the strict architecture, the timeout, the ceiling and the headroom,
and asked for a prompt successor that states the bounded surface forms the gate already reads. CI gate
99 re-derives prompt v1.6.0, frozen and pushed at ed0ce1a before any V10 artifact existed. V10 is V9
with that prompt and nothing else: the provider body is V9's bytes with the v1.6.0 system region in
place of v1.5.0's, the hard ceiling is gate 94's, the planning estimate is recomputed from V10's own
body, and both risks are left for the operator to decide. This gate re-derives it:

    uv run python infrastructure/scripts/render_second_opportunity_execution_packet_v10.py --check

It refuses: bound fields that do not hash to the digest, a spent or superseded digest, an unreviewed or
missing field, an approval recorded by the preparing mission, or either risk accepted by it; V1 to V6
or V9 edited or their consumption reset, V7 or V8 described as anything but superseded before
execution, V9's record not what gate 98 validates, or its refusals classified otherwise than gate 99
records; a prompt other than the frozen v1.6.0, or a freeze commit or push other than the one verified
before V10; a contract, gate, strict projection, route, model, thinking, max_tokens, timeout,
retention or persistence policy that moved; a body that differs from V9's anywhere but the system
region; a hard ceiling that moved, or a planning estimate not recomputed from the body; a synthetic
answer that does not stop where it must; a runner whose guard renames a refusal, whose approval check
does not demand both risk decisions, or that would execute V1 to V9; and any preparation call, TED
byte or canonical counter that moved.
"""

from __future__ import annotations

import argparse
import copy
import functools
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

PACKET = DATA / "second-opportunity-synthesis-execution-packet-v10.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v10.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v10.json"
PACKET_V9 = DATA / "second-opportunity-synthesis-execution-packet-v9.json"
PROMPT_V7 = DATA / "second-opportunity-synthesis-prompt-v7.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v10.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v10.py"
)
GATE_97 = SCRIPTS / "render_second_opportunity_execution_packet_v9.py"
GATE_98 = SCRIPTS / "render_second_opportunity_execution_record_v9.py"
GATE_99 = SCRIPTS / "render_second_opportunity_prompt_v1_6.py"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V10"
PACKET_VERSION = 10
PREPARED_BY = "mission-1.84.23"
THIS_MISSION = (1, 84, 23)
READY = "SECOND_OPPORTUNITY_EXECUTION_PACKET_V10_READY_FOR_OPERATOR_APPROVAL"
DOCUMENTATION_FETCHES = 0
SUPERSEDED = "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
CONSUMED = "EXECUTION_APPROVAL_ALREADY_CONSUMED"
RISK_FLAGS = (
    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10",
    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10",
)
V9_RISK_FLAGS = (
    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9",
    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9",
)
PROMPT_V1_6_SHA256 = "a89960ceb62794c42a84fe7110da6397045c2f57933a721f19cd543e4c221ed5"
V9_OUTCOME = "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY"
V9_FAILED_STAGE = "6_semantic_output_gate_v1_4_0"
FAMILIES = {
    "GENUINE_OUTPUT_SUPPORT_FAILURE_UNDER_CURRENT_POLICY": 1,
    "GENERATION_SURFACE_FORM_MISALIGNMENT": 6,
}
#: The prompt v1.6.0 freeze: the commit that carries the policy, the prompt, their tests and gate 99,
#: and the remote check that found it on origin before any V10 artifact was written.
FREEZE_COMMIT = "ed0ce1aa1f170e9e3cdd5c1c3c0e922497218237"
FREEZE_PUSH = {
    "commit": FREEZE_COMMIT,
    "branch": "sprint-1/mission-1.84.23",
    "remote_ref_sha": FREEZE_COMMIT,
    "verified_with": "git ls-remote origin refs/heads/sprint-1/mission-1.84.23",
    "verified_at": "2026-09-14T19:32:00Z",
    "PROMPT_V1_6_FREEZE_PUSH_VERIFIED_BEFORE_V10": True,
}
#: The one structural difference V10's body may show against V9's: the system region.
APPROVED_DIFFERENCES = ["system: changed"]


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Gate 97, V9's gate, and through it gates 93 to 96; gate 98, the authority on V9's execution; gate
#: 99, the authority on prompt v1.6.0 and on V9's refusals as it classifies them.
G97 = _module("gate_97_for_packet_v10", GATE_97)
G98 = _module("gate_98_for_packet_v10", GATE_98)
G99 = _module("gate_99_for_packet_v10", GATE_99)
G96, G95, G94, G93, G81 = G97.G96, G97.G95, G97.G94, G97.G93, G97.G81

V7_ID, V7_SHA256 = G97.V7_ID, G97.V7_SHA256
V8_ID, V8_SHA256 = G97.V8_ID, G97.V8_SHA256
V9_ID, V9_SHA256 = G97.PACKET_ID, G98.V9_SHA256
SHAS, IDS = G93.SHAS, G93.IDS
V6_ID, V6_SHA256, V6_VIOLATIONS = G93.V6_ID, G93.V6_SHA256, G93.V6_VIOLATIONS
STAGES = G93.STAGES
PREPARATION_ZERO = G93.PREPARATION_ZERO
RETENTION_PATHS = G93.RETENTION_PATHS
RETENTION_PROPERTIES = G93.RETENTION_PROPERTIES
CANONICAL_COUNTERS = G93.CANONICAL_COUNTERS
CAPABILITY_NEGATIVES = G93.CAPABILITY_NEGATIVES
CALL_NEGATIVES = G93.CALL_NEGATIVES
LLM_REQUEST_FIELDS = G93.LLM_REQUEST_FIELDS
V10_TIMEOUT = G96.V9_TIMEOUT

#: What the V10 digest binds: V9's fields without V9's risk flags and V6's schema violation, with V9 as
#: the consumed predecessor whose failed stage is bound instead, V9's record and refusal families, the
#: surface policy, its block and the freeze commit, and V10's own risk flags. PROMPT_VERSION,
#: PROMPT_SHA256, PROMPT_RECORD_SHA256 and the request body and planning figures were bound already.
DIGEST_FIELDS: tuple[str, ...] = (
    *(
        f
        for f in G97.DIGEST_FIELDS
        if f not in (*V9_RISK_FLAGS, "LAST_EXECUTED_PREDECESSOR_SCHEMA_VIOLATION")
    ),
    "PREDECESSOR_OUTCOME",
    "LAST_EXECUTED_PREDECESSOR_FAILED_STAGE",
    "V9_EXECUTION_RECORD_SHA256",
    "V9_REFUSAL_FAMILIES",
    "GENERATION_SURFACE_POLICY",
    "GENERATION_SURFACE_RENDERER",
    "GENERATION_SURFACE_BLOCK_SHA256",
    "PROMPT_V1_6_FREEZE_COMMIT",
    *RISK_FLAGS,
)
#: Everything else the packet may carry. Closed, as V9's was.
UNBOUND_FIELDS: tuple[str, ...] = (
    *(
        f
        for f in G97.UNBOUND_FIELDS
        if f
        not in (
            "V6_RECONFIRMATION",
            "V7_RECONFIRMATION",
            "V8_RECONFIRMATION",
            "V9_PREFLIGHT",
            "OPERATOR_STATED_INTENTIONS",
        )
    ),
    "V9_RECONFIRMATION",
    "V10_PREFLIGHT",
    "PROMPT_V1_6_FREEZE_PUSH",
    "surface_note",
)

#: The TIMEOUT block: V9's, unchanged by this mission, with V10's risk flag.
TIMEOUT_FIXED: dict[str, object] = {
    **{
        k: v
        for k, v in G97.TIMEOUT_FIXED.items()
        if k != "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9"
    },
    "TIMEOUT_CHANGED_BY_THIS_MISSION": False,
    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10": False,
}

#: The synthetic answers V10 adds to V9's, drawn from gate 99's conformance cases by name.
EXTRA_PREFLIGHT: tuple[tuple[str, str, str | None], ...] = (
    ("K_SUPPORTED_CLASS_REACHES_STAGE_9", "SUPPORTED_CLASS_PASSES", None),
    (
        "L_UNSUPPORTED_CLASS_REFUSED_AT_STAGE_6",
        "UNSUPPORTED_CLASS_CONCEPT_FAILS",
        "6_semantic_output_gate_v1_4_0",
    ),
    ("M_NOUN_PHRASE_REQUEST_REACHES_STAGE_9", "EVIDENCE_OF_IS_A_REQUEST", None),
    (
        "N_IMPERATIVE_REQUEST_REFUSED_AT_STAGE_6",
        "IMPERATIVE_FAILS",
        "6_semantic_output_gate_v1_4_0",
    ),
    (
        "O_PRESUPPOSED_CONFIRMATION_REFUSED_AT_STAGE_6",
        "PRESUPPOSED_CONFIRMATION_FAILS",
        "6_semantic_output_gate_v1_4_0",
    ),
    (
        "P_DECLARATIVE_FINDING_REFUSED_AT_STAGE_6",
        "DECLARATIVE_FINDING_FAILS",
        "6_semantic_output_gate_v1_4_0",
    ),
)


class ValidationError(RuntimeError):
    """The packet disagrees with V9, with gates 94, 96, 98 and 99, or with live code."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def text_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _through(check: Callable[..., Any], *args: Any) -> Any:
    """Run one of gates 81 and 93 to 99's checks, and report its refusal as this gate's."""
    try:
        return check(*args)
    except (
        G81.ValidationError,
        G93.ValidationError,
        G94.ValidationError,
        G95.ValidationError,
        G96.ValidationError,
        G97.ValidationError,
        G98.ValidationError,
        G99.ValidationError,
    ) as exc:
        raise ValidationError(str(exc)) from exc


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


def packet_digest(packet: dict[str, Any]) -> str:
    """Recompute the V10 execution digest from the packet's own bound fields."""
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
    """The authenticated snapshot, prompt v1.5.0 over it (V9's) and prompt v1.6.0 over it (V10's)."""
    from sros_opportunity.second_opportunity_prompt_v1_6 import (
        render_second_opportunity_prompt_v1_6,
    )

    snap, parts_v1_5, _parts_v1_4 = _through(G93.snapshot)
    parts_v1_6 = render_second_opportunity_prompt_v1_6(
        snap.packet, snap.statements, snap.pairs, source_metadata=snap.metadata
    )
    return snap, parts_v1_5, parts_v1_6


def runner() -> Any:
    return _module("execution_runner_v10_for_gate", RUNNER)


def timeout_record() -> tuple[dict[str, Any], dict[str, Any]]:
    """Gate 96's validated timeout decision and V8's supersession."""
    return _through(G96.validate)


def cost_record() -> tuple[dict[str, Any], dict[str, Any]]:
    """Gate 94's validated cost record and V7's supersession."""
    return _through(G94.validate)


@functools.lru_cache(maxsize=1)
def prompt_record() -> dict[str, Any]:
    """Gate 99's validated prompt v1.6.0 record, with V9's refusals reproduced and classified."""
    return dict(_through(G99.validate))


@functools.lru_cache(maxsize=1)
def v9_record() -> dict[str, Any]:
    """Gate 98's validated V9 execution record."""
    return dict(_through(G98.validate))


# --------------------------------------------------------------------------- derived blocks


def request_bodies(
    parts_v1_5: Any, parts_v1_6: Any, packet: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """V9's body, through V9's runner and packet, and V10's, through V10's: both built, never sent."""
    module = runner()
    try:
        v10 = module.request_body(parts_v1_6, packet)
    except (ProviderInvalidRequestError, module.RefusedError) as exc:
        raise ValidationError(
            f"STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE: V10's request cannot be built: {exc}"
        ) from exc
    return G97.runner().request_body(parts_v1_5, _load(PACKET_V9)), v10


def _escaped(text: str) -> str:
    """A text as it sits inside a JSON string, the way the transport serialises the body."""
    return json.dumps(text)[1:-1]


def request_differential(
    parts_v1_5: Any, parts_v1_6: Any, packet: dict[str, Any]
) -> dict[str, object]:
    """V9's body against V10's: they differ in the system region and nowhere else."""
    v9, v10 = request_bodies(parts_v1_5, parts_v1_6, packet)
    wire9, wire10 = json.dumps(v9), json.dumps(v10)
    old = _escaped(str(parts_v1_5.system_instructions))
    new = _escaped(str(parts_v1_6.system_instructions))
    occurrences = wire9.count(old)
    substituted = wire9.replace(old, new) if occurrences == 1 else None
    differences = [
        f"{key}: {'added' if key not in v9 else 'removed' if key not in v10 else 'changed'}"
        for key in sorted(set(v9) | set(v10))
        if v9.get(key) != v10.get(key)
    ]
    drift = [d for d in differences if d not in APPROVED_DIFFERENCES]
    if substituted != wire10:
        drift.append("the body moved outside the system region")
    return {
        "v9_body_characters": len(wire9),
        "v10_body_characters": len(wire10),
        "v9_body_sha256": _sha(wire9),
        "v10_body_sha256": _sha(wire10),
        "byte_identical": wire9 == wire10,
        "differences": differences,
        "REQUEST_BODY_DIFFERENCES_V9_TO_V10": len(differences),
        "v1_5_system_region_occurrences_in_v9_body": occurrences,
        "v10_body_is_v9_body_with_the_v1_6_system_region": substituted == wire10,
        "added_characters": len(wire10) - len(wire9),
        "unapproved_drift": drift,
        "timeout_in_the_provider_body": any("timeout" in key.lower() for key in G96.body_keys(v10)),
        "tool_choice": v10.get("tool_choice"),
    }


def preflight_results() -> list[dict[str, object]]:
    """Gate 89's synthetic answers, the extra root key, and gate 99's cases, through V10's stages."""
    module = runner()
    fx = _module("fixtures_for_packet_v10", G93.FIXTURES)
    g89 = _module("gate_89_fixtures_for_packet_v10", G93.GATE_89)
    gate_76 = _module("gate_76_for_packet_v10", G93.GATE_76)
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
    conformance = {case["case"]: case for case in G99.CONFORMANCE_CASES}
    for fixture_id, name, stage in EXTRA_PREFLIGHT:
        case = conformance[name]
        answer = fx.good_output(**{case["field"]: case["value"]})
        cases.append((fixture_id, stage, fx.recorded_result(answer), fx.runner_context()))
    reported = ("I_", "J_", "L_", "N_", "O_", "P_")
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
                    "reasons": list(report["reasons"]) if fixture_id.startswith(reported) else [],
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
    if recomputed in (*SHAS, V7_SHA256, V8_SHA256, V9_SHA256):
        raise ValidationError("V10 carries a spent or superseded predecessor's digest")
    note = str(packet["approval_note"])
    for word in (
        "egress",
        "V9",
        "V7",
        "V8",
        "superseded",
        "spent",
        "beside",
        "residual",
        "timeout",
    ):
        if word not in note:
            raise ValidationError(
                "the approval note does not keep this approval apart from V1's to V6's and V9's "
                "spent approvals, from V7 and V8, which never had one, from both risk decisions and "
                "from TED egress"
            )
    if (
        packet["EXECUTION_ENVELOPE_DECISION_SHA256"]
        != _load(PACKET_V9)["EXECUTION_ENVELOPE_DECISION_SHA256"]
    ):
        raise ValidationError("the envelope decision moved from V9")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = G81._mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V10 recorded by the mission that prepared it, or before it. "
                "Preparing a packet authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V10's")
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
    _through(G93._validates, G93.GATE_91, "91")
    v9_packet = _load(PACKET_V9)
    if (
        v9_packet["EXECUTION_PACKET_SHA256"] != V9_SHA256
        or _through(G97.packet_digest, v9_packet) != V9_SHA256
    ):
        raise ValidationError("V9's packet no longer hashes to the digest that was executed")
    if v9_packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
        raise ValidationError("the frozen V9 packet was edited to record an approval")
    record = v9_record()
    if (
        record["EXECUTION_APPROVAL_CONSUMED"] is not True
        or record["execution_packet_sha256"] != V9_SHA256
        or record["PRIMARY_OUTCOME"] != V9_OUTCOME
        or record["FAILED_STAGE"] != V9_FAILED_STAGE
    ):
        raise ValidationError("V9's record no longer says V9 was executed, refused at 6 and spent")
    if text_sha(G98.RECORD) != G98.RECORD_FILE_SHA256:
        raise ValidationError("V9's execution record is not the one gate 98 pins")
    _, v7_supersession = cost_record()
    _, v8_supersession = timeout_record()
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V9_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V9_SHA256,
            "PREDECESSOR_STATUS": "CONSUMED",
            "PREDECESSOR_EXECUTED": True,
            "PREDECESSOR_APPROVED": True,
            "PREDECESSOR_APPROVAL_CONSUMED": True,
            "PREDECESSOR_OUTCOME": V9_OUTCOME,
            "PREVIOUS_PREDECESSOR_ID": V8_ID,
            "PREVIOUS_PREDECESSOR_SHA256": V8_SHA256,
            "PREVIOUS_PREDECESSOR_STATUS": "SUPERSEDED_BEFORE_EXECUTION",
            "LAST_EXECUTED_PREDECESSOR_ID": V9_ID,
            "LAST_EXECUTED_PREDECESSOR_SHA256": V9_SHA256,
            "LAST_EXECUTED_PREDECESSOR_OUTCOME": V9_OUTCOME,
            "LAST_EXECUTED_PREDECESSOR_FAILED_STAGE": V9_FAILED_STAGE,
            "CONSUMED_EXECUTION_PACKETS": [
                *(
                    {"id": ident, "sha256": digest, "outcome": frozen["PRIMARY_OUTCOME"]}
                    for ident, digest, frozen in zip(IDS, SHAS, records, strict=True)
                ),
                {"id": V9_ID, "sha256": V9_SHA256, "outcome": record["PRIMARY_OUTCOME"]},
            ],
            "SUPERSEDED_EXECUTION_PACKETS": [
                {
                    "id": doc["SUPERSEDED_EXECUTION_PACKET_ID"],
                    "sha256": doc["SUPERSEDED_EXECUTION_PACKET_SHA256"],
                    "status": doc["STATUS"],
                    "reason": doc["REASON"],
                }
                for doc in (v7_supersession, v8_supersession)
            ],
            "V7_SUPERSESSION_RECORD_SHA256": text_sha(G94.SUPERSESSION),
            "V8_SUPERSESSION_RECORD_SHA256": text_sha(G96.SUPERSESSION),
            "TIMEOUT_DECISION_RECORD_SHA256": text_sha(G96.RECORD),
            "V9_EXECUTION_RECORD_SHA256": text_sha(G98.RECORD),
        },
        "packet",
    )


def _check_v9_reconfirmation(packet: dict[str, Any]) -> None:
    record = prompt_record()
    if packet["V9_RECONFIRMATION"] != record["V9_RECONFIRMATION"]:
        raise ValidationError("V9_RECONFIRMATION is not what gate 99 re-derives from V9")
    families = {
        name: block["refusals"] for name, block in record["V9_RECONFIRMATION"]["FAMILIES"].items()
    }
    if packet["V9_REFUSAL_FAMILIES"] != families or families != FAMILIES:
        raise ValidationError(
            f"V9_REFUSAL_FAMILIES is {packet['V9_REFUSAL_FAMILIES']!r}, and gate 99 classifies "
            f"V9's seven refusals as {families!r}"
        )


# --------------------------------------------------------------------------- the prompt and freeze


def _check_prompt(packet: dict[str, Any], parts_v1_6: Any) -> None:
    from sros_opportunity.generation_surface_policy import (
        GENERATION_SURFACE_POLICY_VERSION,
        GENERATION_SURFACE_RENDERER_VERSION,
    )
    from sros_opportunity.second_opportunity_prompt_v1_6 import (
        SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6,
        second_opportunity_prompt_hash_v1_6,
    )

    record = prompt_record()
    v9 = _load(PACKET_V9)
    live = second_opportunity_prompt_hash_v1_6(parts_v1_6)
    if live != PROMPT_V1_6_SHA256 or record["PROMPT_SHA256"] != live:
        raise ValidationError(
            f"the prompt rendered over the snapshot hashes to {live}, not the frozen v1.6.0"
        )
    _fixed(
        packet,
        {
            "PROMPT_ID": v9["PROMPT_ID"],
            "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6,
            "PROMPT_SHA256": live,
            "PROMPT_CHANGED": True,
            "PROMPT_RECORD_SHA256": text_sha(PROMPT_V7),
            "GENERATION_SURFACE_POLICY": GENERATION_SURFACE_POLICY_VERSION,
            "GENERATION_SURFACE_RENDERER": GENERATION_SURFACE_RENDERER_VERSION,
            "GENERATION_SURFACE_BLOCK_SHA256": record["GENERATION_SURFACE_BLOCK_SHA256"],
            "PROMPT_V1_6_FREEZE_COMMIT": FREEZE_COMMIT,
            "PROMPT_V1_6_FREEZE_PUSH": FREEZE_PUSH,
        },
        "packet",
    )
    for key in (
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
        if packet[key] != v9[key]:
            raise ValidationError(f"{key} moved from V9")
    if (
        record["DIFFERENTIAL"]["PROMPT_V1_6_HAS_UNAPPROVED_DRIFT"] is not False
        or record["CONFORMANCE"]["GATE_BEHAVIOR_CHANGED"] is not False
        or record["CENSUS"]["UNSTATED_GENERATION_SURFACE_RULES"] != 0
    ):
        raise ValidationError("gate 99's record no longer shows prompt v1.6.0 as frozen and clean")
    _fixed(
        packet["PROMPT_DECISION"],
        {
            "PROMPT_VERSION": "1.6.0",
            "PROMPT_TEXT_CHANGED": True,
            "V1_5_0_SYSTEM_REGION_KEPT_AS_A_BYTE_IDENTICAL_PREFIX": True,
            "ONLY_THE_GENERATION_SURFACE_BLOCK_ADDED": True,
            "SEMANTIC_GATE_RULES_CHANGED": False,
            "REQUEST_PARSER_EXPANDED": False,
            "SUPPORTED_ASSERTION_POLICY_WEAKENED": False,
            "EXECUTION_BINDING_CHANGED": True,
        },
        "PROMPT_DECISION",
    )
    for relative, digest in record["FREEZE_FILES"].items():
        if G99.file_sha(relative) != digest:
            raise ValidationError(f"PROMPT_V1_6_FREEZE_FILE_MOVED: {relative}")


# --------------------------------------------------------------------------- what did not move


def _check_request(packet: dict[str, Any], parts_v1_5: Any, parts_v1_6: Any) -> None:
    """The body V10 would send: V9's, byte for byte, with the v1.6.0 system region in its place."""
    module = runner()
    _v9_body, body = request_bodies(parts_v1_5, parts_v1_6, packet)
    differential = request_differential(parts_v1_5, parts_v1_6, packet)
    if (
        differential["byte_identical"]
        or differential["differences"] != APPROVED_DIFFERENCES
        or differential["unapproved_drift"]
        or differential["v1_5_system_region_occurrences_in_v9_body"] != 1
        or not differential["v10_body_is_v9_body_with_the_v1_6_system_region"]
        or differential["timeout_in_the_provider_body"]
    ):
        raise ValidationError(
            "V10_REQUEST_BODY_HAS_UNAPPROVED_DRIFT: "
            f"{differential['unapproved_drift'] or differential['differences']}"
        )
    if differential["v9_body_sha256"] != G96.V8_REQUEST_BODY_SHA256:
        raise ValidationError("V10_REQUEST_BODY_HAS_UNAPPROVED_DRIFT: V9's body itself moved")
    if packet["REQUEST_BODY_DIFFERENTIAL"] != differential:
        raise ValidationError("REQUEST_BODY_DIFFERENTIAL is not the rebuilt comparison")
    _fixed(
        packet,
        {
            "REQUEST_BODY_SHA256": differential["v10_body_sha256"],
            "REQUEST_BODY_CHARACTERS": differential["v10_body_characters"],
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
    v9 = _load(PACKET_V9)
    if packet["REQUEST_TIMEOUT"] != V10_TIMEOUT:
        raise ValidationError(
            f"TIMEOUT_POLICY_REQUIRES_ARCHITECTURE_DECISION: REQUEST_TIMEOUT is "
            f"{packet['REQUEST_TIMEOUT']!r}, and the operator decided {V10_TIMEOUT}"
        )
    if packet["GENERATION_PARAMETERS"] != v9["GENERATION_PARAMETERS"]:
        raise ValidationError("the generation parameters moved from V9")
    supplied = {
        k: v
        for k, v in packet["GENERATION_PARAMETERS"].items()
        if k != "$comment" and not k.endswith("note")
    }
    for key, value in supplied.items():
        if value is not None and key not in LLM_REQUEST_FIELDS:
            raise ValidationError(f"{key!r} is frozen with a value nothing reads")
    if supplied.get("max_retries") != 0 or packet["MAX_RETRIES"] != 0:
        raise ValidationError(
            "a retry is a second call, V10 authorises one, and no retry offsets the timeout risk"
        )
    if packet["MAX_MODEL_CALLS"] != 1:
        raise ValidationError(f"MAX_MODEL_CALLS is {packet['MAX_MODEL_CALLS']}")
    for key in CALL_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    _fixed(packet["TIMEOUT"], TIMEOUT_FIXED, "TIMEOUT")
    if packet["TIMEOUT_DECISION_BASIS"] != "OPERATOR_AVAILABILITY_BUDGET":
        raise ValidationError("TIMEOUT_DECISION_BASIS is not the operator's availability budget")
    timeout, _ = timeout_record()
    if timeout["TIMEOUT_DECISION"]["REQUEST_TIMEOUT_V9_SECONDS"] != packet["REQUEST_TIMEOUT"]:
        raise ValidationError("the packet's timeout is not the one gate 96 records")


def planning_block(wire: int) -> dict[str, object]:
    """Gate 94's derivation over V10's body: the planning figures move, and the ceiling does not."""
    return dict(G94.cost_block(_load(PACKET_V9), {"body_characters": wire}))


def _check_cost(packet: dict[str, Any]) -> None:
    record, _ = cost_record()
    block = record["COST_RECORD"]
    for key in (
        "MAX_BILLABLE_INPUT_TOKENS",
        "MAX_BILLABLE_INPUT_TOKENS_BASIS",
        "DATA_RESIDENCY_MULTIPLIER",
        "HARD_INPUT_COST_CEILING",
        "HARD_OUTPUT_COST_CEILING",
        "HARD_EXECUTION_COST_CEILING",
        "HARD_EXECUTION_COST_CEILING_PROVEN",
        "UNKNOWN_COST_CATEGORIES",
        "PLANNING_COST_ESTIMATE_CLASSIFICATION",
        "PRICING_VERSION",
        "PRICE_PER_1K",
    ):
        if packet[key] != block[key]:
            raise ValidationError(
                f"HARD_COST_CEILING_CHANGED: {key} is {packet[key]!r}; gate 94 derives {block[key]!r}"
            )
    live = planning_block(int(packet["REQUEST_BODY_CHARACTERS"]))
    for key, source in (
        ("PLANNING_INPUT_TOKEN_ESTIMATE", "BODY_BASED_INPUT_TOKEN_ESTIMATE"),
        ("PLANNING_INPUT_COST_ESTIMATE", "PLANNING_INPUT_COST_ESTIMATE"),
        ("PLANNING_COST_ESTIMATE", "PLANNING_COST_ESTIMATE"),
    ):
        if packet[key] != live[source]:
            raise ValidationError(
                f"{key} is {packet[key]!r}, and gate 94's derivation over V10's "
                f"{packet['REQUEST_BODY_CHARACTERS']}-character body gives {live[source]!r}"
            )
    if live["HARD_EXECUTION_COST_CEILING"] != packet["HARD_EXECUTION_COST_CEILING"]:
        raise ValidationError("HARD_COST_CEILING_CHANGED: the derivation over V10 moved it")
    if packet["COST_CEILING_RECORD_SHA256"] != text_sha(G94.RECORD) or (
        packet["COST_CEILING_RECORD_SHA256"] != _load(PACKET_V9)["COST_CEILING_RECORD_SHA256"]
    ):
        raise ValidationError("the packet was prepared on another cost-ceiling record")
    if Decimal(str(packet["PLANNING_COST_ESTIMATE"])) >= Decimal(
        str(packet["HARD_EXECUTION_COST_CEILING"])
    ):
        raise ValidationError("ESTIMATE_CALLED_HARD_CEILING: the estimate is not below the ceiling")
    _fixed(
        packet["PLANNING_ESTIMATION_BASIS"],
        {
            "classification": "PLANNING_ESTIMATE",
            "is_a_bound": False,
            "exact_tokenizer_available": False,
            "no_test_request_was_sent": True,
            "chars_per_token": G93.CHARS_PER_TOKEN,
            "conservative_multiplier": G93.CONSERVATIVE_MULTIPLIER,
            "wire_characters": packet["REQUEST_BODY_CHARACTERS"],
            "raw_estimate": round(packet["REQUEST_BODY_CHARACTERS"] / G93.CHARS_PER_TOKEN, 1),
            "strict_format_prompt_tokens": "NOT_ESTABLISHED",
            "covers_the_strict_format_prompt": False,
        },
        "PLANNING_ESTIMATION_BASIS",
    )


def _check_verification(packet: dict[str, Any]) -> None:
    _fixed(
        packet["PREPARATION_VERIFICATION"],
        {
            "representation_sha256": G93.REPRESENTATION_SHA256,
            "representation_characters": G93.REPRESENTATION_CHARACTERS,
            "prompt_sha256": PROMPT_V1_6_SHA256,
            "selected_packet_id": packet["SELECTED_PACKET_ID"],
            "approved_evidence_rows": len(packet["APPROVED_EVIDENCE_IDS"]),
            "provider_posture": "APPROVED",
            "ted_external_model_transmission": "PERMITTED_WITH_CONDITIONS",
            "request_thinking": {"type": "disabled"},
            "request_max_tokens": packet["MAX_OUTPUT_TOKENS"],
            "request_strict_tool": "FROZEN_PROJECTION_STRICT_FORCED",
            "request_body_characters": packet["REQUEST_BODY_CHARACTERS"],
            "request_body_sha256": packet["REQUEST_BODY_SHA256"],
            "request_timeout_seconds": V10_TIMEOUT,
            "unstated_generation_constraints": 0,
            "unstated_generation_relevant_semantic_rules": 0,
            "unstated_generation_targets": 0,
            "unstated_generation_surface_rules": 0,
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
            "v9_refused_as_consumed": True,
            "v7_refused_as_superseded": True,
            "v8_refused_as_superseded": True,
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
    if packet["V10_PREFLIGHT"] != live:
        raise ValidationError("V10_PREFLIGHT is not what V10's stages give over the fixtures")
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
    for fixture_id, _name, stage in EXTRA_PREFLIGHT:
        row = by_id[fixture_id]
        if stage is None and row["outcome"] != "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW":
            raise ValidationError(f"{fixture_id} does not reach stage 9")
        if stage is not None and not row["reasons"]:
            raise ValidationError(f"{fixture_id} is refused with no reason recorded")


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
                    "V10 runner test defines"
                )
    v9 = _load(PACKET_V9)
    for key in ("PROVIDER_COMPLETION_POLICY", "RETENTION_ON_EXECUTION"):
        if packet[key] != v9[key]:
            raise ValidationError(f"{key} moved from V9")
    policy = copy.deepcopy(v9["PERSISTENCE_POLICY"])
    policy["provenance_the_first_revision_must_carry"] = [
        *policy["provenance_the_first_revision_must_carry"],
        "the prompt v1.6.0 record and its freeze commit",
        "the V9 execution record",
    ]
    if packet["PERSISTENCE_POLICY"] != policy:
        raise ValidationError(
            "PERSISTENCE_POLICY moved from V9 beyond naming prompt v1.6.0's record and V9's"
        )


def _check_accounting(packet: dict[str, Any]) -> None:
    accounting = packet["preparation_accounting"]
    for key in PREPARATION_ZERO:
        if accounting.get(key) != 0:
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V10 does 0")
    if accounting.get("DOCUMENTATION_FETCHES") != DOCUMENTATION_FETCHES:
        raise ValidationError("documentation reads recorded, and preparing V10 read none")
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
        "approved_by": "gate 100",
        "operator_statement": "a synthetic approval, never written beside the packet",
    }
    residual, timeout = RISK_FLAGS
    cases: list[tuple[dict[str, object], str | None]] = [
        ({}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ({residual: True}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ({timeout: True}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ({residual: "yes", timeout: True}, "OPERATOR_APPROVAL_INCOMPLETE"),
        (dict.fromkeys(V9_RISK_FLAGS, True), "OPERATOR_APPROVAL_INCOMPLETE"),
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
                        f"accept both of V10's risks: {extra}"
                    )


def _check_runner(packet: dict[str, Any], parts_v1_5: Any, parts_v1_6: Any) -> None:
    from sros_opportunity.generation_surface_policy import SURFACE_RULE_IDS

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
                f"the runner expects {key}={value!r} and V10 binds {packet[key]!r}"
            )
    if module.EXPECTED["REQUEST_TIMEOUT"] != V10_TIMEOUT:
        raise ValidationError("the runner does not wait the operator's 240.0 seconds")
    built = module.build_request(parts_v1_6, packet)
    if built.max_retries != 0:
        raise ValidationError(
            f"the runner's request would retry {built.max_retries} time(s); V10 authorises one call, "
            "and no retry offsets the timeout risk"
        )
    if built.timeout_seconds != V10_TIMEOUT:
        raise ValidationError(
            f"the runner's request would wait {built.timeout_seconds} s, not {V10_TIMEOUT}"
        )
    if built.prompt_template_version != "1.6.0":
        raise ValidationError("the runner's request names a prompt other than v1.6.0")
    authority = module.packet_gate()
    for name in ("packet_digest", "freeze_gate"):
        if not callable(getattr(authority, name, None)):
            raise ValidationError(
                f"the runner's packet authority has no {name}(), and its verification would "
                "stop on it"
            )
    if tuple(module.STAGES) != STAGES:
        raise ValidationError("the runner's stages are not the gate's")
    if list(inspect.signature(module.validate_execution).parameters) != ["result", "context"]:
        raise ValidationError("the runner's semantic gate can be injected")
    if module.APPROVAL_FILE.name != APPROVAL.name or module.PROMPT_DOCUMENT.name != PROMPT_V7.name:
        raise ValidationError("the runner reads its approval or its prompt from somewhere else")
    if tuple(module.RISK_DECISIONS) != RISK_FLAGS:
        raise ValidationError("the runner's approval does not demand both of V10's risk decisions")
    if module.COST_SELECTORS_REQUIRED != G94.SELECTORS_REQUIRED:
        raise ValidationError("the runner checks the body against other cost selectors")
    _check_approval_behaviour(runner(), packet)
    for label, digest in (*((f"V{i + 1}", sha) for i, sha in enumerate(SHAS)), ("V9", V9_SHA256)):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != CONSUMED:
                raise ValidationError(f"the runner refuses {label} as {exc.code}") from exc
        else:
            raise ValidationError(f"the runner would execute {label}'s spent digest")
    for label, digest in (("V7", V7_SHA256), ("V8", V8_SHA256)):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != SUPERSEDED:
                raise ValidationError(
                    f"the runner refuses {label} as {exc.code}, not as superseded"
                ) from exc
        else:
            raise ValidationError(
                f"{label}_STILL_EXECUTABLE: the V10 runner's guard lets {label}'s digest through"
            )
    try:
        module.refuse_if_consumed("0" * 64)
    except module.RefusedError as exc:
        raise ValidationError("the runner refuses an unseen digest") from exc
    if (
        module.unstated_semantic_rules(parts_v1_6)
        or module.unstated_constraints(parts_v1_6.system_instructions)
        or module.unstated_targets(parts_v1_6)
        or module.unstated_surface(parts_v1_6)
    ):
        raise ValidationError(
            "the runner finds prompt v1.6.0 leaving a rule, bound, target or surface form unstated"
        )
    if module.unstated_surface(parts_v1_5) != list(SURFACE_RULE_IDS):
        raise ValidationError("the runner's surface check would pass prompt v1.5.0")


def validate() -> dict[str, Any]:
    packet = _load(PACKET)
    snap, parts_v1_5, parts_v1_6 = snapshot()
    _check_identity_and_approval(packet)
    _check_predecessors(packet)
    _check_v9_reconfirmation(packet)
    _through(G93._check_contract_and_gate, packet)
    _through(G93._check_strict, packet)
    _check_prompt(packet, parts_v1_6)
    _through(G93._check_route, packet)
    _through(G93._check_representation, packet, snap)
    _check_request(packet, parts_v1_5, parts_v1_6)
    _check_calls_and_timeout(packet)
    _check_cost(packet)
    _check_verification(packet)
    _check_preflight(packet)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet, parts_v1_5, parts_v1_6)
    return packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v10.py "
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
    diff = packet["REQUEST_BODY_DIFFERENTIAL"]
    v9 = packet["V9_RECONFIRMATION"]
    freeze = packet["PROMPT_V1_6_FREEZE_PUSH"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v10",
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
                f"its outcome                         {packet['PREDECESSOR_OUTCOME']}",
                f"previous predecessor                {packet['PREVIOUS_PREDECESSOR_ID']} "
                f"{packet['PREVIOUS_PREDECESSOR_SHA256']}",
                f"its status                          {packet['PREVIOUS_PREDECESSOR_STATUS']}",
                f"subject                             {packet['SUBJECT_KEY']}",
                "",
                f"provider                            {packet['PROVIDER_ID']}",
                f"route                               {packet['PROVIDER_ROUTE_SURFACE']} "
                "(synchronous, Commercial Terms)",
                f"model                               {packet['MODEL_ID']}",
                f"thinking                            {packet['THINKING']}",
                "",
                f"output schema                       {packet['OUTPUT_SCHEMA_VERSION']}",
                f"full canonical stage 5              {packet['FULL_CANONICAL_STAGE_5_VALIDATION']}",
                f"semantic gate                       {packet['OUTPUT_GATE_VERSION']} "
                f"({packet['SEMANTIC_GATE_IMPLEMENTATION_SHA256']})",
                f"prompt                              {packet['PROMPT_ID']}@{packet['PROMPT_VERSION']}",
                f"prompt sha256                       {packet['PROMPT_SHA256']}",
                f"generation surface policy           {packet['GENERATION_SURFACE_POLICY']}",
                f"prompt v1.6.0 freeze commit         {packet['PROMPT_V1_6_FREEZE_COMMIT']}",
                "freeze push verified before V10     "
                f"{_flag(freeze['PROMPT_V1_6_FREEZE_PUSH_VERIFIED_BEFORE_V10'])}",
                f"reasoning summary                   hard maximum "
                f"{packet['REASONING_SUMMARY_HARD_MAX']}, generation target "
                f"{packet['REASONING_SUMMARY_GENERATION_TARGET']}",
                f"generation target ratio             {packet['GENERATION_TARGET_RATIO']}",
                f"representation sha256               {packet['REPRESENTATION_SHA256']}",
                "",
                f"provider strict mode                {_flag(packet['PROVIDER_STRICT_MODE'])}",
                f"provider strict schema sha256       {packet['PROVIDER_STRICT_SCHEMA_SHA256']}",
                f"projection freeze commit            {packet['STRICT_PROJECTION_FREEZE_COMMIT']}",
                "",
                f"request body                        {packet['REQUEST_BODY_CHARACTERS']} characters, "
                f"sha256 {packet['REQUEST_BODY_SHA256']}",
                f"MAX_OUTPUT_TOKENS                   {packet['MAX_OUTPUT_TOKENS']}",
                f"MAX_MODEL_CALLS                     {packet['MAX_MODEL_CALLS']}",
                f"MAX_RETRIES                         {packet['MAX_RETRIES']}",
                f"REQUEST_TIMEOUT                     {packet['REQUEST_TIMEOUT']} s "
                f"({packet['TIMEOUT_DECISION_BASIS']})",
                "",
                f"PLANNING_INPUT_TOKEN_ESTIMATE       {packet['PLANNING_INPUT_TOKEN_ESTIMATE']}",
                f"PLANNING_INPUT_COST_ESTIMATE        {packet['PLANNING_INPUT_COST_ESTIMATE']}",
                f"PLANNING_COST_ESTIMATE              {packet['PLANNING_COST_ESTIMATE']}",
                f"HARD_EXECUTION_COST_CEILING         {packet['HARD_EXECUTION_COST_CEILING']}",
                "HARD_EXECUTION_COST_CEILING_PROVEN  "
                f"{_flag(packet['HARD_EXECUTION_COST_CEILING_PROVEN'])}",
                "",
                f"human_review_required               {_flag(packet['HUMAN_REVIEW_REQUIRED'])}",
                "canonical_persistence               "
                f"{packet['PERSISTENCE_POLICY']['canonical_persistence']}",
                "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10      "
                f"{_flag(packet['RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10'])}",
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10 "
                f"{_flag(packet['STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10'])}",
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{_flag(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED'])}",
                f"NEW_APPROVAL_REQUIRED               {_flag(packet['NEW_APPROVAL_REQUIRED'])}",
                "PREVIOUS_APPROVAL_REUSABLE          "
                f"{_flag(packet['PREVIOUS_APPROVAL_REUSABLE'])}",
            ]
        ),
        "## What changed from V9: the prompt, and nothing else",
        "",
        f"{_sentence(packet['surface_note'])}",
        "",
        "The request body, rebuilt through V9's runner with prompt v1.5.0 and through V10's with "
        "prompt v1.6.0 over the same snapshot, is V9's body with the v1.6.0 system region in place "
        f"of v1.5.0's: {diff['v9_body_characters']} -> {diff['v10_body_characters']} characters "
        f"(+{diff['added_characters']}), sha256 `{diff['v10_body_sha256']}`, differences "
        f"{diff['differences']}, and no timeout in it.",
        "",
        "## V9, re-derived",
        "",
        *_code(
            [
                f"packet                  {v9['EXECUTION_PACKET_ID']} {v9['EXECUTION_PACKET_SHA256']}",
                f"outcome                 {v9['PRIMARY_OUTCOME']}",
                f"request                 {v9['PROVIDER_REQUESTS']}, HTTP {v9['HTTP_STATUS']}, "
                f"{v9['ELAPSED_SECONDS']} s, {v9['STOP_REASON']}",
                f"usage                   {v9['USAGE']['input_tokens']} in / "
                f"{v9['USAGE']['output_tokens']} out / {v9['USAGE']['thinking_tokens']} thinking / "
                f"{v9['USAGE']['total_tokens']} total, cost {v9['ACTUAL_COST']}",
                f"root keys               {v9['ROOT_KEYS_RETURNED']}, unknown "
                f"{v9['UNKNOWN_ROOT_PROPERTIES_RETURNED']}",
                *(
                    f"{name:<52}{block['refusals']} refusal(s)"
                    for name, block in v9["FAMILIES"].items()
                ),
            ]
        ),
        "## Synthetic answers through V10's stages",
        "",
        "| fixture | summary characters | must stop at | stopped at |",
        "|---|---|---|---|",
        *[
            f"| {row['fixture']} | {row['summary_characters']} | {row['must_stop_at'] or 'stage 9'} "
            f"| {row['stopped_at'] or 'stage 9 (' + str(row['outcome']) + ')'} |"
            for row in packet["V10_PREFLIGHT"]
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
    print("ok       packet V10 is V9's request with prompt v1.6.0, frozen and unapproved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
