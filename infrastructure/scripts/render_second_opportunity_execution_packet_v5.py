"""Gate 84: execution packet V5, V4's call with prompt v1.4.0, frozen and unapproved.

Mission 1.84.14. The operator kept schema v1.1.0, gate v1.3.0 and the representation, and chose a
generation-headroom policy: a target at most 4/5 of each composed text's hard maximum, stated beside
it, and field roles. Prompt v1.4.0 carries it, and this packet prepares exactly one more call only if
the policy, the prompt and every deterministic stage are ready. This gate re-derives the packet:

    uv run python infrastructure/scripts/render_second_opportunity_execution_packet_v5.py --check

It reuses gate 81's frozen helpers (the snapshot, the body builder, the single-call-site and
no-post-processing checks, the stages and the retention paths) and compares everything with V4.

It refuses: bound fields that do not hash to the digest, a spent digest, an unreviewed or missing
field, or an approval recorded by the mission that prepared the packet; V1 to V4 edited, their
consumption reset, V4 made a candidate or its violations rewritten; a prompt that is not v1.4.0 or
leaves a schema bound, a class-A rule or a generation target unstated; a headroom policy, ratio,
array policy or record other than the operator's and gate 83's; gate 79, 80 or 83 no longer
validating, or the V5 runner's stages 6 to 9 not refusing at their own stages; the schema, gate
v1.3.0 or the representation moved; a route, model, thinking configuration, max_tokens, completion
policy, timeout, retention or persistence policy that moved from V4; a request body the snapshot does
not rebuild; a cost ceiling that is not the recomputed worst case; a retention path no V5 runner test
defines; a runner with more than one call site, that edits the answer, whose gate can be injected,
that expects another digest, that would execute V1 to V4 again or refuses an unseen digest; and any
preparation call, TED byte or canonical counter that moved.
"""

from __future__ import annotations

import argparse
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
from sros_llm_gateway.providers.anthropic import DEFAULT_ENDPOINT  # noqa: E402
from sros_opportunity.generation_headroom import (  # noqa: E402
    ARRAY_HEADROOM_POLICY,
    FIELD_ROLE_POLICY_VERSION,
    GENERATION_HEADROOM_POLICY,
    GENERATION_HEADROOM_RENDERER_VERSION,
    OPERATOR_DECISION_GENERATION_HEADROOM,
    headroom_policy_digest,
    headroom_table,
)
from sros_opportunity.output_constraints import OUTPUT_CONSTRAINT_RENDERER_VERSION  # noqa: E402
from sros_opportunity.second_opportunity import (  # noqa: E402
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_ID,
)
from sros_opportunity.second_opportunity_gate_v1_3 import (  # noqa: E402
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
)
from sros_opportunity.second_opportunity_prompt_v1_4 import (  # noqa: E402
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4,
    SECOND_OPPORTUNITY_SYSTEM_V1_4,
    render_second_opportunity_prompt_v1_4,
    second_opportunity_prompt_hash_v1_4,
)
from sros_opportunity.semantic_generation_rules import (  # noqa: E402
    SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
    SEMANTIC_RULE_CENSUS_VERSION,
    SOURCE_LABEL_BLOCK_RENDERER_VERSION,
    policy_digest,
)

PACKET = DATA / "second-opportunity-synthesis-execution-packet-v5.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v5.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v5.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v5.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v5.py"
)
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
PACKET_V3 = DATA / "second-opportunity-synthesis-execution-packet-v3.json"
PACKET_V4 = DATA / "second-opportunity-synthesis-execution-packet-v4.json"
RECORD_V1 = DATA / "second-opportunity-synthesis-execution-record-v1.json"
RECORD_V2 = DATA / "second-opportunity-synthesis-execution-record-v2.json"
RECORD_V3 = DATA / "second-opportunity-synthesis-execution-record-v3.json"
RECORD_V4 = DATA / "second-opportunity-synthesis-execution-record-v4.json"
PROMPT_V5 = DATA / "second-opportunity-synthesis-prompt-v5.json"
HEADROOM = DATA / "second-opportunity-generation-headroom-policy-v1.json"
PREFLIGHT = DATA / "second-opportunity-stage-6-9-preflight-v1.json"
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
PROVIDER_REGISTER = DATA / "model-provider-policy-v1.json"
PREPARATION = DATA / "opportunity-preparation-v5.json"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_76 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
GATE_79 = SCRIPTS / "render_second_opportunity_semantic_prompt_alignment.py"
GATE_80 = SCRIPTS / "render_second_opportunity_stage_6_9_preflight.py"
GATE_81 = SCRIPTS / "render_second_opportunity_execution_packet_v4.py"
GATE_83 = SCRIPTS / "render_second_opportunity_generation_headroom.py"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V5"
PACKET_VERSION = 5
PREPARED_BY = "mission-1.84.14"
THIS_MISSION = (1, 84, 14)
V1_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V1"
V2_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V2"
V3_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V3"
V4_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V4"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
MODEL = "claude-sonnet-5"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
PROMPT_V1_3_SHA256 = "a62fa218ab04e7da5b050ec40dcf2450c749dafd34262fe8c83e9fbc040acc5a"
GATE_IMPLEMENTATION_SHA256 = "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3"
CHARS_PER_TOKEN = 2.1565
CONSERVATIVE_MULTIPLIER = 1.25
V4_WIRE_CHARACTERS = 27946
V4_OUTCOME = "EXECUTION_SCHEMA_REJECTED_NO_RETRY"
V4_HISTORICAL_VIOLATIONS = [
    "candidate_intervention_class: 316 characters exceeds maxLength 300",
    "evidence_bound_reasoning_summary: 1078 characters exceeds maxLength 900",
]
READY = "SECOND_OPPORTUNITY_EXECUTION_PACKET_V5_READY_FOR_OPERATOR_APPROVAL"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Gate 81, whose frozen helpers V5 reuses rather than copies.
G81 = _module("gate_81_for_packet_v5", GATE_81)

STAGES = G81.STAGES
STAGE_CONDITIONS = G81.STAGE_CONDITIONS
POST_PROCESSING = G81.POST_PROCESSING
PREPARATION_ZERO = G81.PREPARATION_ZERO
RETENTION_PATHS = G81.RETENTION_PATHS
RETENTION_PROPERTIES = G81.RETENTION_PROPERTIES
CANONICAL_COUNTERS = G81.CANONICAL_COUNTERS
CAPABILITY_NEGATIVES = G81.CAPABILITY_NEGATIVES
CALL_NEGATIVES = G81.CALL_NEGATIVES
LLM_REQUEST_FIELDS = G81.LLM_REQUEST_FIELDS

#: What the V5 digest binds: V4's fields, and the headroom policy, its record and its renderer.
DIGEST_FIELDS: tuple[str, ...] = (
    *G81.DIGEST_FIELDS,
    "GENERATION_HEADROOM_DECISION",
    "GENERATION_HEADROOM_RECORD_SHA256",
    "GENERATION_HEADROOM_POLICY",
    "GENERATION_TARGET_RATIO",
    "ARRAY_HEADROOM_POLICY",
    "GENERATION_HEADROOM_RENDERER",
    "FIELD_ROLE_POLICY",
    "GENERATION_HEADROOM_POLICY_DIGEST",
    "NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT",
)
#: Everything else the packet may carry. Closed, as V4's was.
UNBOUND_FIELDS: tuple[str, ...] = (
    *(field for field in G81.UNBOUND_FIELDS if field != "V3_OBSERVATION"),
    "V4_OBSERVATION",
    "headroom_note",
)


class ValidationError(RuntimeError):
    """The packet disagrees with V4, with the records that justify it, or with live code."""


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
    """Recompute the V5 execution digest from the packet's own bound fields."""
    bound: dict[str, object] = {}
    for key in DIGEST_FIELDS:
        if key not in packet:
            raise ValidationError(f"the execution packet has no {key!r} to bind")
        bound[key] = G81._bindable(packet[key])
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_gate() -> Any:
    """Gate 77, the one authority on gate v1.3.0's implementation digest."""
    return G81.freeze_gate()


def snapshot() -> tuple[Any, Any]:
    """Gate 81's authenticated snapshot, and prompt v1.4.0 rendered over it."""
    snap = _through(G81.snapshot)
    parts = render_second_opportunity_prompt_v1_4(
        snap.packet, snap.statements, snap.pairs, source_metadata=snap.metadata
    )
    return snap, parts


def body_characters(parts: Any, packet: dict[str, Any], version: str) -> int:
    return int(G81.body_characters(parts, packet, version))


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


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
    if recomputed in (V1_SHA256, V2_SHA256, V3_SHA256, V4_SHA256):
        raise ValidationError("V5 carries a spent predecessor's digest")
    note = str(packet["approval_note"])
    for word in ("egress", "V4", "beside", "prompt", "headroom"):
        if word not in note:
            raise ValidationError(
                "the approval note does not keep this approval apart from V1's to V4's, from the "
                "prompt and headroom decisions and from TED egress"
            )
    if (
        packet["EXECUTION_ENVELOPE_DECISION_SHA256"]
        != _load(PACKET_V4)["EXECUTION_ENVELOPE_DECISION_SHA256"]
    ):
        raise ValidationError("the envelope decision moved from V4")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = G81._mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V5 recorded by the mission that prepared it. Preparing a packet "
                "authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V5's")
    return recomputed


def _check_predecessors(packet: dict[str, Any]) -> None:
    packets = [_load(p) for p in (PACKET_V1, PACKET_V2, PACKET_V3, PACKET_V4)]
    records = [_load(p) for p in (RECORD_V1, RECORD_V2, RECORD_V3, RECORD_V4)]
    digests = (V1_SHA256, V2_SHA256, V3_SHA256, V4_SHA256)
    for name, frozen, digest in zip(("V1", "V2", "V3", "V4"), packets, digests, strict=True):
        if frozen["EXECUTION_PACKET_SHA256"] != digest:
            raise ValidationError(f"{name}'s packet digest moved")
        if frozen["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
            raise ValidationError(f"the frozen {name} packet was edited to record an approval")
    if G81.packet_digest(packets[3]) != V4_SHA256:
        raise ValidationError("V4's bound fields no longer hash to its digest")
    for name, record in zip(("V1", "V2", "V3", "V4"), records, strict=True):
        if record["EXECUTION_APPROVAL_CONSUMED"] is not True:
            raise ValidationError(f"{name}'s consumption was reset")
    record_v4 = records[3]
    _fixed(
        record_v4,
        {
            "execution_packet_sha256": V4_SHA256,
            "PRIMARY_OUTCOME": V4_OUTCOME,
            "FURTHER_CALLS_AUTHORIZED_BY_V4": False,
            "HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
            "OPPORTUNITY_PERSISTED": False,
            "CANONICAL_PERSISTENCE": False,
            "SCHEMA_VIOLATIONS": V4_HISTORICAL_VIOLATIONS,
            "FAILED_STAGE": "5_schema_validation_v1_1_0",
        },
        "V4's record",
    )
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V4_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V4_SHA256,
            "PREDECESSOR_EXECUTION_OUTCOME": V4_OUTCOME,
            "PREDECESSOR_APPROVAL_CONSUMED": True,
            "CONSUMED_EXECUTION_PACKETS": [
                {"id": ident, "sha256": digest, "outcome": record["PRIMARY_OUTCOME"]}
                for ident, digest, record in zip(
                    (V1_ID, V2_ID, V3_ID, V4_ID), digests, records, strict=True
                )
            ],
        },
        "packet",
    )


# --------------------------------------------------------------------------- what changed


def _check_prompt(packet: dict[str, Any], parts: Any) -> None:
    v4 = _load(PACKET_V4)
    prompt = _load(PROMPT_V5)
    headroom = _load(HEADROOM)
    live = second_opportunity_prompt_hash_v1_4(parts)
    _fixed(
        packet,
        {
            "PROMPT_ALIGNMENT_DECISION": v4["PROMPT_ALIGNMENT_DECISION"],
            "PROMPT_ALIGNMENT_RECORD_SHA256": v4["PROMPT_ALIGNMENT_RECORD_SHA256"],
            "SEMANTIC_PROMPT_ALIGNMENT_DECISION": v4["SEMANTIC_PROMPT_ALIGNMENT_DECISION"],
            "SEMANTIC_PROMPT_ALIGNMENT_RECORD_SHA256": v4[
                "SEMANTIC_PROMPT_ALIGNMENT_RECORD_SHA256"
            ],
            "STAGE_6_TO_9_PREFLIGHT_RECORD_SHA256": text_sha(PREFLIGHT),
            "GENERATION_HEADROOM_DECISION": list(OPERATOR_DECISION_GENERATION_HEADROOM),
            "GENERATION_HEADROOM_RECORD_SHA256": text_sha(HEADROOM),
            "GENERATION_HEADROOM_POLICY": GENERATION_HEADROOM_POLICY.name,
            "GENERATION_TARGET_RATIO": GENERATION_HEADROOM_POLICY.ratio_text,
            "ARRAY_HEADROOM_POLICY": ARRAY_HEADROOM_POLICY,
            "GENERATION_HEADROOM_RENDERER": GENERATION_HEADROOM_RENDERER_VERSION,
            "FIELD_ROLE_POLICY": FIELD_ROLE_POLICY_VERSION,
            "GENERATION_HEADROOM_POLICY_DIGEST": headroom_policy_digest(),
            "NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT": headroom["NATIVE_STRUCTURED_OUTPUT"][
                "NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT"
            ],
            "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
            "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4,
            "PROMPT_SHA256": live,
            "PROMPT_CHANGED": True,
            "OUTPUT_CONSTRAINT_RENDERER": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "SEMANTIC_GENERATION_RULES_RENDERER": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
            "SEMANTIC_RULE_CENSUS": SEMANTIC_RULE_CENSUS_VERSION,
            "SOURCE_LABEL_BLOCK_RENDERER": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
            "SEMANTIC_GENERATION_POLICY_DIGEST": policy_digest(),
        },
        "packet",
    )
    if packet["STAGE_6_TO_9_PREFLIGHT_RECORD_SHA256"] != v4["STAGE_6_TO_9_PREFLIGHT_RECORD_SHA256"]:
        raise ValidationError("the stage 6 to 9 preflight record moved since V4 bound it")
    if (
        prompt["PROMPT_SHA256"] != live
        or prompt["PROMPT_VERSION"] != "1.4.0"
        or prompt["SYSTEM_INSTRUCTION"] != SECOND_OPPORTUNITY_SYSTEM_V1_4
        or prompt["PREDECESSOR_PROMPT_SHA256"] != PROMPT_V1_3_SHA256
    ):
        raise ValidationError("the prompt document is not the live v1.4.0 prompt over v1.3.0")
    spent = {_load(p)["PROMPT_SHA256"] for p in (PACKET_V1, PACKET_V2, PACKET_V3, PACKET_V4)}
    if live in spent:
        raise ValidationError("V5 binds a prompt a spent packet already sent")
    checks = headroom["PROMPT"]
    if (
        headroom["PROMPT_V1_4_SHA256"] != live
        or checks["UNSTATED_GENERATION_CONSTRAINTS"] != 0
        or checks["UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES"] != 0
        or checks["UNSTATED_GENERATION_TARGETS"] != 0
        or headroom["DRIFT"]["HEADROOM_TARGET_DRIFT"] != 0
        or headroom["INDEPENDENCE"]["V4_VALUES_USED_TO_DERIVE_HEADROOM"] is not False
    ):
        raise ValidationError("the headroom record does not stand behind prompt v1.4.0")
    for path, name in ((GATE_79, "79"), (GATE_83, "83")):
        gate = _module(f"gate_{name}_for_packet_v5", path)
        try:
            gate.validate()
        except gate.ValidationError as exc:
            raise ValidationError(f"gate {name} no longer validates: {exc}") from exc


def _check_preflight() -> None:
    gate_80 = _module("gate_80_for_packet_v5", GATE_80)
    try:
        record = gate_80.validate()
    except gate_80.ValidationError as exc:
        raise ValidationError(f"DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY: {exc}") from exc
    if record["OUTCOME"] != gate_80.READY:
        raise ValidationError("DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY")
    runner = _module("runner_v5_for_preflight", RUNNER)
    fx = _module("fixtures_for_packet_v5", FIXTURES)
    gate_76 = _module("gate_76_for_packet_v5", GATE_76)
    with gate_76.no_transport():
        for fixture_id, _what, intended, result, context in gate_80.fixtures(fx):
            report = runner.validate_execution(result, context)
            if report["failed_stage"] != intended:
                raise ValidationError(
                    f"DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY: under the V5 runner {fixture_id} "
                    f"stopped at {report['failed_stage']}, not {intended}"
                )
        # A target is guidance, never a bound: through the V5 runner's own stages, one character
        # over a target passes stage 5 and one character over the hard maximum fails it.
        rows = {row.path: row for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)}
        for field in ("candidate_intervention_class", "evidence_bound_reasoning_summary"):
            row = rows[field]
            for length, refused in (
                (row.generation_target + 1, False),
                (row.hard_maximum + 1, True),
            ):
                answer = fx.good_output(**{field: "x" * length})
                report = runner.validate_execution(fx.recorded_result(answer), fx.runner_context())
                at_stage_5 = report["failed_stage"] == "5_schema_validation_v1_1_0"
                if at_stage_5 is not refused:
                    raise ValidationError(
                        f"the V5 runner {'passes' if not at_stage_5 else 'refuses'} {field} at "
                        f"{length} characters: a generation target is enforced, or a hard maximum "
                        "is not"
                    )


def _check_contract(packet: dict[str, Any]) -> None:
    live = hashlib.sha256(
        json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, sort_keys=True).encode("utf-8")
    ).hexdigest()
    implementation = freeze_gate().implementation_sha256()
    if implementation != GATE_IMPLEMENTATION_SHA256:
        raise ValidationError("SEMANTIC_GATE_CHANGED: gate v1.3.0's implementation moved")
    _fixed(
        packet,
        {
            "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
            "OUTPUT_SCHEMA_SHA256": live,
            "OUTPUT_GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
            "SEMANTIC_GATE_IMPLEMENTATION_SHA256": implementation,
            "SCHEMA_CHANGED": False,
            "SEMANTIC_GATE_CHANGED_BY_THIS_MISSION": False,
            "OUTPUT_GATE_CHANGED_FROM_PREDECESSOR": False,
            "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL": False,
            "ESTIMATE_EXACT": False,
            "LOCAL_SCHEMA_VALIDATOR_MANDATORY": True,
        },
        "packet",
    )
    v4 = _load(PACKET_V4)
    for key in (
        "OUTPUT_SCHEMA_VERSION",
        "OUTPUT_SCHEMA_SHA256",
        "OUTPUT_GATE_VERSION",
        "SEMANTIC_GATE_IMPLEMENTATION_SHA256",
        "SOURCE_METADATA_CONTEXT_SHA256",
        "TRUSTED_CONTEXT_SHA256",
        "PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE",
        "CONTRACT_THEORETICAL_MAX_EXCEEDS_EXECUTION_ENVELOPE",
    ):
        if packet[key] != v4[key]:
            raise ValidationError(f"{key} moved from V4")
    post = packet["OUTPUT_POST_PROCESSING"]
    if set(post) != set(POST_PROCESSING) or any(post[key] is not False for key in POST_PROCESSING):
        raise ValidationError(
            "an answer may be changed to fit a bound. Truncation, dropping, rewriting, summarising, "
            "splitting and normalising are all refused, and a target is never a reason to"
        )


def _check_representation(packet: dict[str, Any], snap: Any, parts: Any) -> None:
    v4 = _load(PACKET_V4)
    for key in (
        "SOURCE_DECISION_PACKET_ID",
        "SOURCE_DECISION_PACKET_VERSION",
        "SOURCE_DECISION_PACKET_SHA256",
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
    ):
        if packet[key] != v4[key]:
            raise ValidationError(f"{key} is not what V4 and the approved egress rest on")
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
            "APPROVED_EVIDENCE_IDS": list(snap.packet.evidence_ids),
            "APPROVED_CLAIM_IDS": list(snap.packet.claim_ids),
            "SOURCE_METADATA_CONTEXT_SHA256": snap.metadata.digest(),
            "TRUSTED_CONTEXT_SHA256": snap.trusted.digest(),
        },
        "packet",
    )
    _fixed(
        packet["PREPARATION_VERIFICATION"],
        {
            "representation_sha256": REPRESENTATION_SHA256,
            "representation_characters": REPRESENTATION_CHARACTERS,
            "prompt_sha256": packet["PROMPT_SHA256"],
            "v1_3_prompt_sha256_recomputed": PROMPT_V1_3_SHA256,
            "selected_packet_id": packet["SELECTED_PACKET_ID"],
            "approved_evidence_rows": len(packet["APPROVED_EVIDENCE_IDS"]),
            "provider_posture": "APPROVED",
            "subscription_route_posture": "NOT_APPROVED",
            "ted_external_model_transmission": "PERMITTED_WITH_CONDITIONS",
            "ted_eligibility": "ELIGIBLE",
            "live_packet_gate": "AVAILABLE",
            "live_gate_refusals": [],
            "request_thinking": {"type": "disabled"},
            "request_max_tokens": packet["MAX_OUTPUT_TOKENS"],
            "request_body_characters": packet["TOKEN_ESTIMATION_BASIS"]["wire_characters"],
            "v4_request_body_characters_recomputed": V4_WIRE_CHARACTERS,
            "unstated_generation_constraints": 0,
            "unstated_generation_relevant_semantic_rules": 0,
            "unstated_generation_targets": 0,
            "pricing_version": packet["PRICING_VERSION"],
            "worst_case_from_the_configured_table": packet["WORST_CASE_CALL_COST"],
            "source_metadata_context_sha256": packet["SOURCE_METADATA_CONTEXT_SHA256"],
            "trusted_context_sha256": packet["TRUSTED_CONTEXT_SHA256"],
            "semantic_gate_implementation_sha256": GATE_IMPLEMENTATION_SHA256,
            "v1_guard_refuses_v1": True,
            "v2_guard_refuses_v2": True,
            "v3_guard_refuses_v3": True,
            "v4_guard_refuses_v4": True,
            "guard_permits_an_unseen_digest": True,
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


# --------------------------------------------------------------------------- V4's call, unchanged


def _check_route(packet: dict[str, Any]) -> None:
    register = _load(PROVIDER_REGISTER)
    approved = sorted(
        str(e["provider_id"]) for e in register["providers"] if e.get("posture") == "APPROVED"
    )
    if approved != ["anthropic"]:
        raise ValidationError(
            f"PROVIDER_ROUTE_NO_LONGER_APPROVED: the register approves {approved}"
        )
    v4 = _load(PACKET_V4)
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
        "MAX_OUTPUT_TOKENS",
        "OUTPUT_TOKEN_CEILING",
        "MAX_OUTPUT_TOKENS_BASIS",
        "OUTPUT_TOKEN_CEILING_BASIS",
        "ADAPTER_PARAMETERS",
        "ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS",
        "PROVIDER_COMPLETION_POLICY",
        "VALIDATION_STAGES",
        "STAGE_CONDITIONS",
        "STRUCTURED_OUTPUT_MECHANISM",
        "NATIVE_PROVIDER_STRUCTURED_OUTPUT",
        "RETENTION_ON_EXECUTION",
        "failure_outcome",
        "output_limit_outcome",
    ):
        if packet[key] != v4[key]:
            raise ValidationError(f"{key} moved from V4")
    if (
        packet["PROVIDER_ROUTE_SURFACE"] != f"POST {DEFAULT_ENDPOINT}"
        or packet["MODEL_ID"] != MODEL
    ):
        raise ValidationError("the route or the model is not the reviewed one")
    if tuple(packet["MAX_OUTPUT_TOKENS_NOT_BASED_ON"]) != (
        *v4["MAX_OUTPUT_TOKENS_NOT_BASED_ON"],
        "V4_OBSERVED_OUTPUT_TOKENS",
    ):
        raise ValidationError("the ceiling's basis no longer excludes V4's observed output")
    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if packet["MAX_OUTPUT_TOKENS"] != capability["DOCUMENTED_MAX_OUTPUT_TOKENS"]:
        raise ValidationError("max_tokens is not the documented synchronous maximum")


def _check_calls_and_timeout(packet: dict[str, Any]) -> None:
    v4 = _load(PACKET_V4)
    params = packet["GENERATION_PARAMETERS"]
    if params != v4["GENERATION_PARAMETERS"]:
        raise ValidationError("the generation parameters moved from V4")
    supplied = {k: v for k, v in params.items() if k != "$comment" and not k.endswith("note")}
    for key, value in supplied.items():
        if value is not None and key not in LLM_REQUEST_FIELDS:
            raise ValidationError(f"{key!r} is frozen with a value nothing reads")
    if supplied.get("max_retries") != 0 or packet["MAX_RETRIES"] != 0:
        raise ValidationError("a retry is a second call, and V5 authorises one")
    if packet["MAX_MODEL_CALLS"] != 1:
        raise ValidationError(f"MAX_MODEL_CALLS is {packet['MAX_MODEL_CALLS']}")
    for key in CALL_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if packet["REQUEST_TIMEOUT"] != v4["REQUEST_TIMEOUT"]:
        raise ValidationError("the timeout moved from V4")
    elapsed = _load(RECORD_V4)["timing"]["elapsed_seconds"]
    _fixed(
        packet["TIMEOUT"],
        {
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "TIMEOUT_CHANGED_BY_THIS_MISSION": False,
            "V4_OBSERVED_ELAPSED_SECONDS": elapsed,
            "V4_OBSERVATION_USED_TO_CHANGE_THE_TIMEOUT": False,
            "STREAMING": False,
            "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
            "TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS": True,
            "ON_TIMEOUT": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
        },
        "TIMEOUT",
    )


def _check_cost(packet: dict[str, Any], snap: Any, parts: Any) -> None:
    v4 = _load(PACKET_V4)
    record_v4 = _load(RECORD_V4)
    if (
        packet["PRICING_VERSION"] != v4["PRICING_VERSION"]
        or packet["PRICE_PER_1K"] != v4["PRICE_PER_1K"]
    ):
        raise ValidationError("MODEL_COST_BASIS_REQUIRES_REFRESH: the price moved from V4")
    price = packet["PRICE_PER_1K"]
    held = ModelPrice(input_per_1k=float(price["input"]), output_per_1k=float(price["output"]))
    v4_wire = body_characters(snap.parts_v1_3, packet, "1.3.0")
    if v4_wire != V4_WIRE_CHARACTERS:
        raise ValidationError(
            f"V4's body rebuilds to {v4_wire} characters, not the {V4_WIRE_CHARACTERS} it sent"
        )
    wire = body_characters(parts, packet, SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4)
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
            "v4_wire_characters": V4_WIRE_CHARACTERS,
            "prompt_delta_characters": wire - V4_WIRE_CHARACTERS,
        },
        "TOKEN_ESTIMATION_BASIS",
    )
    expected = math.ceil(wire / CHARS_PER_TOKEN * CONSERVATIVE_MULTIPLIER)
    if packet["INPUT_TOKEN_ESTIMATE"] != expected:
        raise ValidationError(
            f"INPUT_TOKEN_ESTIMATE is {packet['INPUT_TOKEN_ESTIMATE']}; {wire} characters give "
            f"{expected} under the held ratio and multiplier"
        )
    tool_overhead = _load(CAPABILITY)["MODELS"][MODEL]["TOOL_USE_SYSTEM_PROMPT_TOKENS"][
        "any_or_tool"
    ]
    if basis["documented_tool_use_overhead_tokens"] != tool_overhead:
        raise ValidationError("the tool-use overhead is not the documented one")
    if expected - wire / CHARS_PER_TOKEN < tool_overhead:
        raise ValidationError("the multiplier's margin does not cover the documented tool overhead")
    output = int(packet["MAX_OUTPUT_TOKENS"])
    total = held.cost_for(expected, output)
    _fixed(
        packet,
        {
            "TOTAL_TOKEN_CEILING": expected + output,
            "INPUT_WORST_CASE_COST": held.cost_for(expected, 0),
            "OUTPUT_WORST_CASE_COST": held.cost_for(0, output),
            "WORST_CASE_CALL_COST": total,
            "EXECUTION_COST_CEILING": total,
            "HEADROOM_POLICY": "NONE_HELD",
            "COST_NOT_EXPECTED_ACTUAL": True,
        },
        "packet",
    )
    previous = float(v4["EXECUTION_COST_CEILING"])
    _fixed(
        packet,
        {
            "PREVIOUS_EXECUTION_COST_CEILING": previous,
            "CEILING_DELTA_OVER_PREVIOUS": round(total - previous, 6),
            "CEILING_OVER_PREVIOUS_CEILING": round(total / previous, 4),
            "LARGER_THAN_PREVIOUS_CEILING": total > previous,
        },
        "packet",
    )
    usage = record_v4["ACTUAL_USAGE"]
    _fixed(
        packet["V4_OBSERVATION"],
        {
            "V4_INPUT_TOKEN_ESTIMATE": v4["INPUT_TOKEN_ESTIMATE"],
            "V4_ACTUAL_INPUT_TOKENS": usage["input_tokens"],
            "V4_ESTIMATE_COVERED_THE_ACTUAL": v4["INPUT_TOKEN_ESTIMATE"] >= usage["input_tokens"],
            "V4_ACTUAL_OUTPUT_TOKENS": usage["output_tokens"],
            "USED_TO_CHANGE_THE_ESTIMATION_METHOD": False,
            "USED_TO_REDUCE_MAX_OUTPUT_TOKENS": False,
            "USED_TO_DERIVE_HEADROOM": False,
        },
        "V4_OBSERVATION",
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
                raise ValidationError(f"{path} names {test!r}, which no V5 runner test defines")
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
    if not policy["provenance_the_first_revision_must_carry"]:
        raise ValidationError("a persistence policy naming no provenance")


def _check_accounting(packet: dict[str, Any]) -> None:
    accounting = packet["preparation_accounting"]
    for key in PREPARATION_ZERO:
        if accounting.get(key) != 0:
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V5 does 0")
    if packet["CANONICAL_COUNTERS"] != CANONICAL_COUNTERS:
        raise ValidationError("a canonical counter moved")


def _check_runner(packet: dict[str, Any], snap: Any, parts: Any) -> None:
    source = RUNNER.read_text(encoding="utf-8")
    _through(G81._check_single_call_site, source)
    _through(G81._check_no_post_processing, source)
    runner = _module("execution_runner_v5_for_gate", RUNNER)
    if runner.EXPECTED["EXECUTION_PACKET_SHA256"] != packet["EXECUTION_PACKET_SHA256"]:
        raise ValidationError("the runner was prepared for another digest")
    for key, value in runner.EXPECTED.items():
        if key in packet and packet[key] != value:
            raise ValidationError(
                f"the runner expects {key}={value!r} and V5 binds {packet[key]!r}"
            )
    if tuple(runner.STAGES) != STAGES:
        raise ValidationError("the runner's stages are not the gate's")
    if list(inspect.signature(runner.validate_execution).parameters) != ["result", "context"]:
        raise ValidationError("the runner's semantic gate can be injected")
    if runner.APPROVAL_FILE.name != APPROVAL.name or runner.PROMPT_DOCUMENT.name != PROMPT_V5.name:
        raise ValidationError("the runner reads its approval or its prompt from somewhere else")
    for label, digest in (
        ("V1", V1_SHA256),
        ("V2", V2_SHA256),
        ("V3", V3_SHA256),
        ("V4", V4_SHA256),
    ):
        try:
            runner.refuse_if_consumed(digest)
        except runner.RefusedError as exc:
            if exc.code != "EXECUTION_APPROVAL_ALREADY_CONSUMED":
                raise ValidationError(f"the runner refuses {label} for the wrong reason") from exc
        else:
            raise ValidationError(f"the runner would execute {label}'s spent digest")
    try:
        runner.refuse_if_consumed("0" * 64)
    except runner.RefusedError as exc:
        raise ValidationError("the runner refuses an unseen digest") from exc
    if (
        runner.unstated_semantic_rules(parts)
        or runner.unstated_constraints(parts.system_instructions)
        or runner.unstated_targets(parts)
    ):
        raise ValidationError(
            "the runner finds prompt v1.4.0 leaving a rule, bound or target unstated"
        )
    if not runner.unstated_targets(snap.parts_v1_3):
        raise ValidationError("the runner's headroom check would pass prompt v1.3.0")


def validate() -> dict[str, Any]:
    packet = _load(PACKET)
    snap, parts = snapshot()
    _check_identity_and_approval(packet)
    _check_predecessors(packet)
    _check_prompt(packet, parts)
    _check_preflight()
    _check_contract(packet)
    _check_representation(packet, snap, parts)
    _check_route(packet)
    _through(G81._check_thinking_and_envelope, packet, snap)
    _check_calls_and_timeout(packet)
    _check_cost(packet, snap, parts)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet, snap, parts)
    return packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v5.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _sentence(text: object) -> str:
    value = str(text).strip()
    return value if value.endswith((".", "!", "?")) else value + "."


def _cost(value: object) -> str:
    return f"{float(str(value)):.6f}".rstrip("0").rstrip(".")


def render_packet(packet: dict[str, Any]) -> str:
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    observed = packet["V4_OBSERVATION"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v5",
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
                f"subject                             {packet['SUBJECT_KEY']}",
                "",
                f"provider                            {packet['PROVIDER_ID']}",
                f"route                               {packet['PROVIDER_ROUTE_SURFACE']} "
                "(synchronous, Commercial Terms)",
                f"model                               {packet['MODEL_ID']}",
                f"thinking                            {packet['THINKING']}",
                "",
                f"schema                              {packet['OUTPUT_SCHEMA_VERSION']}",
                f"schema sha256                       {packet['OUTPUT_SCHEMA_SHA256']}",
                f"semantic gate                       {packet['OUTPUT_GATE_VERSION']}",
                f"gate implementation                 {packet['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}",
                f"prompt                              {packet['PROMPT_ID']}@{packet['PROMPT_VERSION']}",
                f"prompt sha256                       {packet['PROMPT_SHA256']}",
                f"generation headroom                 {packet['GENERATION_HEADROOM_POLICY']}",
                f"generation target ratio             {packet['GENERATION_TARGET_RATIO']}",
                f"array headroom                      {packet['ARRAY_HEADROOM_POLICY']}",
                f"representation sha256               {packet['REPRESENTATION_SHA256']}",
                f"representation characters           {packet['REPRESENTATION_CHARACTER_COUNT']}",
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
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{str(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']).lower()}",
                "NEW_APPROVAL_REQUIRED               "
                f"{str(packet['NEW_APPROVAL_REQUIRED']).lower()}",
                "PREVIOUS_APPROVAL_REUSABLE          "
                f"{str(packet['PREVIOUS_APPROVAL_REUSABLE']).lower()}",
            ]
        ),
        "## What changed from V4",
        "",
        f"Prompt v{packet['PROMPT_VERSION']}: {_sentence(packet['prompt_note'])} "
        f"{_sentence(packet['headroom_note'])} Under the operator's decision "
        + ", ".join(f"`{d}`" for d in packet["GENERATION_HEADROOM_DECISION"])
        + ".",
        "",
        "## Cost, recomputed from the new request body",
        "",
        *_code(
            [
                f"request body             {basis['wire_characters']} characters  "
                f"(V4 {basis['v4_wire_characters']} + prompt {basis['prompt_delta_characters']})",
                f"input token estimate     {packet['INPUT_TOKEN_ESTIMATE']}  "
                f"({basis['wire_characters']} / {basis['chars_per_token']} x "
                f"{basis['conservative_multiplier']})",
                f"output token ceiling     {packet['OUTPUT_TOKEN_CEILING']}",
                f"total token ceiling      {packet['TOTAL_TOKEN_CEILING']}",
                f"pricing                  {packet['PRICING_VERSION']}  "
                f"({packet['PRICE_PER_1K']['input']} / {packet['PRICE_PER_1K']['output']} per 1k)",
                f"input worst case         {_cost(packet['INPUT_WORST_CASE_COST'])}",
                f"output worst case        {_cost(packet['OUTPUT_WORST_CASE_COST'])}",
                f"total worst case         {_cost(packet['WORST_CASE_CALL_COST'])}",
                f"execution cost ceiling   {_cost(packet['EXECUTION_COST_CEILING'])}  "
                f"(headroom policy: {packet['HEADROOM_POLICY']})",
                f"previous ceiling (V4)    {_cost(packet['PREVIOUS_EXECUTION_COST_CEILING'])}  "
                f"(+{_cost(packet['CEILING_DELTA_OVER_PREVIOUS'])}, "
                f"x{packet['CEILING_OVER_PREVIOUS_CEILING']})",
            ]
        ),
        f"V4 estimated {observed['V4_INPUT_TOKEN_ESTIMATE']} input tokens and used "
        f"{observed['V4_ACTUAL_INPUT_TOKENS']}; it used {observed['V4_ACTUAL_OUTPUT_TOKENS']} "
        f"output tokens. {_sentence(observed['note'])}",
        "",
        "## What was verified live, on the preparing machine",
        "",
        *[
            f"- `{key}`: {value if isinstance(value, str) else json.dumps(value)}"
            for key, value in packet["PREPARATION_VERIFICATION"].items()
            if key != "$comment"
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
    print("ok       packet V5 is V4's call with prompt v1.4.0, and matches live code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
