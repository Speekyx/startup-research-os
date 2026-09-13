"""Mission 1.84.17, CI gate 90: execution packet V6, V5's call over schema v1.2.0, gate v1.4.0 and prompt
v1.5.0, frozen and unapproved.

The operator moved the reasoning summary's hard maximum in Mission 1.84.16 and, in 1.84.17, decided that
schema v1.2.0 is the V6 execution contract, judged by a successor gate bound to it. Gate v1.4.0 was
frozen by CI gate 87 and committed before this packet existed; prompt v1.5.0 (gate 88) states the new
bound; the V6 runner's stages 5 to 9 and every retention path were proved on synthetic answers (gate
89). This gate re-derives the packet:

    uv run python infrastructure/scripts/render_second_opportunity_execution_packet_v6.py --check

It reuses gate 81's frozen helpers and gate 84's digest fields, and compares everything with V5.

It refuses: bound fields that do not hash to the digest, a spent digest, an unreviewed or missing field,
or an approval recorded by the mission that prepared the packet; V1 to V5 edited, their consumption
reset, V5 made a candidate or its violation rewritten; a schema other than v1.2.0, a summary bound or
target other than the schema's and the policy's, or the operator's decision records moved; a gate
other than the frozen v1.4.0, its freeze record, test digest or commit moved, or gate 86, 87, 88 or 89
no longer validating; a prompt that is not v1.5.0 or leaves a bound, rule or target unstated; a
headroom policy other than V5's; the representation moved; a route, model, thinking configuration,
max_tokens, completion policy, timeout, retention or persistence policy that moved from V5; a request
body the snapshot does not rebuild through the V6 runner; a cost ceiling that is not the recomputed
worst case; a residual-risk acceptance carried over; a retention path no V6 runner test defines; a
runner with more than one call site, that edits the answer, whose gate can be injected, that expects
another digest, that would execute V1 to V5 again or refuses an unseen digest; and any preparation
call, TED byte or canonical counter that moved.
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
    generation_target,
    headroom_policy_digest,
    headroom_table,
)
from sros_opportunity.output_constraints import OUTPUT_CONSTRAINT_RENDERER_VERSION  # noqa: E402
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_PROMPT_ID  # noqa: E402
from sros_opportunity.second_opportunity_gate_v1_4 import (  # noqa: E402
    OPERATOR_DECISION_V1_4,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
)
from sros_opportunity.second_opportunity_prompt_v1_4 import (  # noqa: E402
    render_second_opportunity_prompt_v1_4,
)
from sros_opportunity.second_opportunity_prompt_v1_5 import (  # noqa: E402
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5,
    SECOND_OPPORTUNITY_SYSTEM_V1_5,
    render_second_opportunity_prompt_v1_5,
    second_opportunity_prompt_hash_v1_5,
)
from sros_opportunity.second_opportunity_schema_v1_2 import (  # noqa: E402
    REASONING_SUMMARY_DECISION_BASIS,
    REASONING_SUMMARY_FIELD,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
    output_schema_sha256,
)
from sros_opportunity.semantic_generation_rules import (  # noqa: E402
    SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
    SEMANTIC_RULE_CENSUS_VERSION,
    SOURCE_LABEL_BLOCK_RENDERER_VERSION,
    policy_digest,
)

PACKET = DATA / "second-opportunity-synthesis-execution-packet-v6.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v6.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v6.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v6.py"
RUNNER_V5 = SCRIPTS / "run_second_opportunity_execution_v5.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v6.py"
)
PACKETS = tuple(
    DATA / f"second-opportunity-synthesis-execution-packet-v{n}.json" for n in range(1, 6)
)
RECORDS = tuple(
    DATA / f"second-opportunity-synthesis-execution-record-v{n}.json" for n in range(1, 6)
)
PACKET_V5 = PACKETS[4]
RECORD_V5 = RECORDS[4]
PROMPT_V6 = DATA / "second-opportunity-synthesis-prompt-v6.json"
CAPACITY_V3 = DATA / "second-opportunity-output-capacity-analysis-v3.json"
PREFLIGHT_V2 = DATA / "second-opportunity-stage-6-9-preflight-v2.json"
FREEZE_V1_4 = DATA / "second-opportunity-output-gate-v1.4-freeze-v1.json"
CONTRACT_DECISION = DATA / "second-opportunity-reasoning-summary-contract-decision-v1.json"
CONTRACT_RECORD = DATA / "second-opportunity-reasoning-summary-contract-v1.json"
HEADROOM = DATA / "second-opportunity-generation-headroom-policy-v1.json"
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
PROVIDER_REGISTER = DATA / "model-provider-policy-v1.json"
PREPARATION = DATA / "opportunity-preparation-v5.json"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_76 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
GATE_81 = SCRIPTS / "render_second_opportunity_execution_packet_v4.py"
GATE_84 = SCRIPTS / "render_second_opportunity_execution_packet_v5.py"
GATE_86 = SCRIPTS / "render_second_opportunity_reasoning_summary_contract.py"
GATE_87 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"
GATE_88 = SCRIPTS / "render_second_opportunity_prompt_v1_5.py"
GATE_89 = SCRIPTS / "render_second_opportunity_stage_6_9_preflight_v2.py"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V6"
PACKET_VERSION = 6
PREPARED_BY = "mission-1.84.17"
THIS_MISSION = (1, 84, 17)
IDS = tuple(f"SECOND-OPPORTUNITY-SYNTH-EXEC-V{n}" for n in range(1, 6))
SHAS = (
    "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92",
    "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e",
    "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2",
    "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b",
    "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a",
)
V5_ID, V5_SHA256 = IDS[4], SHAS[4]
MODEL = "claude-sonnet-5"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
PROMPT_V1_4_SHA256 = "960955f44a7ac0b95c995941aeac6ca772e196f4e6cb309b44ecfaa741bd6f46"
GATE_IMPLEMENTATION_SHA256 = "eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb"
GATE_TEST_SHA256 = "73796544b550a70f09b230b278e45280daebee6385f44d833d05dfb06998c4ab"
#: The commit that froze gate v1.4.0, made before prompt v1.5.0 was rendered or this packet existed.
GATE_FREEZE_COMMIT = "402a698f695241801d9cd61fd9f5d444ebb16221"
CONTRACT_DECISION_SHA256 = "f8aa8b525b87cf561b7a8eb181d6fb68ffe50da10a62cd153af37137ecee0886"
CONTRACT_RECORD_SHA256 = "b6a620fa64eb438140b4dcbb417e97aa6961870d0f334e7a91938e8188793516"
CHARS_PER_TOKEN = 2.1565
CONSERVATIVE_MULTIPLIER = 1.25
V5_WIRE_CHARACTERS = 31963
V5_OUTCOME = "EXECUTION_SCHEMA_REJECTED_NO_RETRY"
V5_HISTORICAL_VIOLATIONS = [
    "evidence_bound_reasoning_summary: 1031 characters exceeds maxLength 900",
]
READY = "SECOND_OPPORTUNITY_EXECUTION_PACKET_V6_READY_FOR_OPERATOR_APPROVAL"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Gate 81, whose frozen helpers V6 reuses rather than copies, and gate 84, whose digest fields it extends.
G81 = _module("gate_81_for_packet_v6", GATE_81)
G84 = _module("gate_84_for_packet_v6", GATE_84)

#: Stages 5 and 6 are named for what judges there, and both moved: schema v1.2.0 and gate v1.4.0.
STAGE_RENAMES = {
    "5_schema_validation_v1_1_0": "5_schema_validation_v1_2_0",
    "6_semantic_output_gate_v1_3_0": "6_semantic_output_gate_v1_4_0",
}
STAGES = tuple(STAGE_RENAMES.get(stage, stage) for stage in G81.STAGES)
STAGE_CONDITIONS = {
    "6_semantic_output_gate_v1_4_0": (
        "gate v1.4.0 over the answer as it arrived, with the trusted context and the registry's "
        "source-metadata channel; gate v1.3.0 called once, its structural reasons read against "
        "schema v1.2.0; fixed in the runner and never injectable"
    ),
    "7_evidence_boundary_and_no_distortion": (
        "every cited Evidence and Claim id inside the approved boundary this packet binds, each "
        "Evidence cited with its approved Claim, and the v1.4.0 audit gate v1.4.0 returns, which is "
        "gate v1.3.0's own, with no failed field"
    ),
    **{k: v for k, v in G81.STAGE_CONDITIONS.items() if k[0] in "89" or k.startswith("10_")},
}
POST_PROCESSING = G81.POST_PROCESSING
PREPARATION_ZERO = G81.PREPARATION_ZERO
RETENTION_PATHS = G81.RETENTION_PATHS
RETENTION_PROPERTIES = G81.RETENTION_PROPERTIES
CANONICAL_COUNTERS = G81.CANONICAL_COUNTERS
CAPABILITY_NEGATIVES = G81.CAPABILITY_NEGATIVES
CALL_NEGATIVES = G81.CALL_NEGATIVES
LLM_REQUEST_FIELDS = G81.LLM_REQUEST_FIELDS

#: What the V6 digest binds: V5's fields, and the operator's contract, the frozen successor gate, the
#: capacity and prompt records and the residual-risk acceptance, which V6 does not carry.
DIGEST_FIELDS: tuple[str, ...] = (
    *G84.DIGEST_FIELDS,
    "REASONING_SUMMARY_CONTRACT_DECISION_SHA256",
    "REASONING_SUMMARY_CONTRACT_RECORD_SHA256",
    "REASONING_SUMMARY_DECISION_BASIS",
    "REASONING_SUMMARY_HARD_MAX",
    "REASONING_SUMMARY_GENERATION_TARGET",
    "SEMANTIC_GATE_SUCCESSOR_DECISION",
    "SEMANTIC_GATE_FREEZE_RECORD_SHA256",
    "SEMANTIC_GATE_FROZEN_TEST_SHA256",
    "SEMANTIC_GATE_FREEZE_COMMIT",
    "OUTPUT_CAPACITY_RECORD_SHA256",
    "PROMPT_RECORD_SHA256",
    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6",
)
#: Everything else the packet may carry. Closed, as V5's was.
UNBOUND_FIELDS: tuple[str, ...] = (
    *(field for field in G84.UNBOUND_FIELDS if field != "V4_OBSERVATION"),
    "V5_OBSERVATION",
    "contract_note",
)


class ValidationError(RuntimeError):
    """The packet disagrees with V5, with the records that justify it, or with live code."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def text_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def file_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _through(check: Callable[..., Any], *args: Any) -> Any:
    """Run one of gate 81's frozen checks, and report its refusal as this gate's."""
    try:
        return check(*args)
    except G81.ValidationError as exc:
        raise ValidationError(str(exc)) from exc


def packet_digest(packet: dict[str, Any]) -> str:
    """Recompute the V6 execution digest from the packet's own bound fields."""
    bound: dict[str, object] = {}
    for key in DIGEST_FIELDS:
        if key not in packet:
            raise ValidationError(f"the execution packet has no {key!r} to bind")
        bound[key] = G81._bindable(packet[key])
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_gate() -> Any:
    """Gate 87, the one authority on gate v1.4.0's implementation digest."""
    return _module("gate_87_for_packet_v6", GATE_87)


def snapshot() -> tuple[Any, Any, Any]:
    """Gate 81's authenticated snapshot, and prompts v1.5.0 and v1.4.0 rendered over it."""
    snap = _through(G81.snapshot)
    arguments = (snap.packet, snap.statements, snap.pairs)
    return (
        snap,
        render_second_opportunity_prompt_v1_5(*arguments, source_metadata=snap.metadata),
        render_second_opportunity_prompt_v1_4(*arguments, source_metadata=snap.metadata),
    )


def runner() -> Any:
    return _module("execution_runner_v6_for_gate", RUNNER)


def wire_characters(module: Any, parts: Any, packet: dict[str, Any]) -> int:
    """len(json.dumps(body)) for these regions, built by the runner's own adapter and never sent."""
    return len(json.dumps(module.request_body(parts, packet)))


def summary_bound() -> tuple[int, int]:
    hard = int(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["properties"][REASONING_SUMMARY_FIELD]["maxLength"]
    )
    return hard, generation_target(hard)


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


def _validates(path: pathlib.Path, name: str) -> Any:
    gate = _module(f"gate_{name}_for_packet_v6", path)
    try:
        return gate.validate()
    except gate.ValidationError as exc:
        raise ValidationError(f"gate {name} no longer validates: {exc}") from exc


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
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6": False,
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
        raise ValidationError("V6 carries a spent predecessor's digest")
    note = str(packet["approval_note"])
    for word in ("egress", "V5", "beside", "gate", "schema", "residual"):
        if word not in note:
            raise ValidationError(
                "the approval note does not keep this approval apart from V1's to V5's, from the "
                "schema and gate decisions, from the residual-risk acceptance and from TED egress"
            )
    if (
        packet["EXECUTION_ENVELOPE_DECISION_SHA256"]
        != _load(PACKET_V5)["EXECUTION_ENVELOPE_DECISION_SHA256"]
    ):
        raise ValidationError("the envelope decision moved from V5")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = G81._mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V6 recorded by the mission that prepared it. Preparing a packet "
                "authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V6's")
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
    if G84.packet_digest(packets[4]) != V5_SHA256:
        raise ValidationError("V5's bound fields no longer hash to its digest")
    for index, record in enumerate(records):
        if record["EXECUTION_APPROVAL_CONSUMED"] is not True:
            raise ValidationError(f"V{index + 1}'s consumption was reset")
    _fixed(
        records[4],
        {
            "execution_packet_sha256": V5_SHA256,
            "PRIMARY_OUTCOME": V5_OUTCOME,
            "HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
            "OPPORTUNITY_PERSISTED": False,
            "CANONICAL_PERSISTENCE": False,
            "SCHEMA_VIOLATIONS": V5_HISTORICAL_VIOLATIONS,
            "FAILED_STAGE": "5_schema_validation_v1_1_0",
        },
        "V5's record",
    )
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V5_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V5_SHA256,
            "PREDECESSOR_EXECUTION_OUTCOME": V5_OUTCOME,
            "PREDECESSOR_APPROVAL_CONSUMED": True,
            "CONSUMED_EXECUTION_PACKETS": [
                {"id": ident, "sha256": digest, "outcome": record["PRIMARY_OUTCOME"]}
                for ident, digest, record in zip(IDS, SHAS, records, strict=True)
            ],
        },
        "packet",
    )


# --------------------------------------------------------------------------- what changed


def _check_contract_and_gate(packet: dict[str, Any]) -> None:
    """The operator's contract, schema v1.2.0, and the frozen gate v1.4.0 bound to it."""
    hard, target = summary_bound()
    freeze = freeze_gate()
    implementation = freeze.implementation_sha256()
    if implementation != GATE_IMPLEMENTATION_SHA256 or freeze.FROZEN_IMPLEMENTATION_SHA256 != (
        GATE_IMPLEMENTATION_SHA256
    ):
        raise ValidationError("SEMANTIC_GATE_V1_4_NOT_FROZEN: the implementation moved")
    if (
        freeze.file_sha(freeze.TEST_FILE) != GATE_TEST_SHA256
        or freeze.FROZEN_TEST_SHA256 != GATE_TEST_SHA256
    ):
        raise ValidationError("gate v1.4.0's frozen test file moved")
    record = _load(FREEZE_V1_4)
    if not (
        record["GATE_V1_4_FROZEN"] is True
        and record["SEMANTIC_GATE_V1_4_IMPLEMENTATION_SHA256"] == implementation
        and record["NON_STRUCTURAL_SEMANTIC_DIVERGENCES"] == 0
        and record["COMMON_DOMAIN_SEMANTIC_DIVERGENCES"] == 0
    ):
        raise ValidationError("gate v1.4.0's freeze record does not stand behind it")
    if file_sha(CONTRACT_DECISION) != CONTRACT_DECISION_SHA256 or file_sha(CONTRACT_RECORD) != (
        CONTRACT_RECORD_SHA256
    ):
        raise ValidationError("the operator's reasoning-summary decision or its record moved")
    _fixed(
        packet,
        {
            "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
            "OUTPUT_SCHEMA_SHA256": output_schema_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2),
            "OUTPUT_GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
            "SEMANTIC_GATE_IMPLEMENTATION_SHA256": implementation,
            "SEMANTIC_GATE_FROZEN_TEST_SHA256": GATE_TEST_SHA256,
            "SEMANTIC_GATE_FREEZE_RECORD_SHA256": text_sha(FREEZE_V1_4),
            "SEMANTIC_GATE_FREEZE_COMMIT": GATE_FREEZE_COMMIT,
            "SEMANTIC_GATE_SUCCESSOR_DECISION": list(OPERATOR_DECISION_V1_4),
            "REASONING_SUMMARY_CONTRACT_DECISION_SHA256": CONTRACT_DECISION_SHA256,
            "REASONING_SUMMARY_CONTRACT_RECORD_SHA256": CONTRACT_RECORD_SHA256,
            "REASONING_SUMMARY_DECISION_BASIS": REASONING_SUMMARY_DECISION_BASIS,
            "REASONING_SUMMARY_HARD_MAX": hard,
            "REASONING_SUMMARY_GENERATION_TARGET": target,
            "OUTPUT_CAPACITY_RECORD_SHA256": text_sha(CAPACITY_V3),
            "SCHEMA_CHANGED": True,
            "SEMANTIC_GATE_CHANGED_BY_THIS_MISSION": True,
            "OUTPUT_GATE_CHANGED_FROM_PREDECESSOR": True,
            "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL": False,
            "CONTRACT_THEORETICAL_MAX_EXCEEDS_EXECUTION_ENVELOPE": True,
            "ESTIMATE_EXACT": False,
            "LOCAL_SCHEMA_VALIDATOR_MANDATORY": True,
        },
        "packet",
    )
    capacity = _load(CAPACITY_V3)
    if (
        capacity["REACHABILITY"]["CONTRACT_FULL_DOMAIN_REACHABLE"] is not False
        or capacity["PERSISTENCE"]["PERSISTENCE_COMPATIBILITY"] != "COMPATIBLE"
        or capacity["HEADROOM"]["OTHER_HEADROOM_ROW_DRIFT"] != 0
        or capacity["HEADROOM"]["REASONING_SUMMARY"]["v1_2_0"] != [hard, target]
    ):
        raise ValidationError("the capacity record does not stand behind schema v1.2.0")
    v5 = _load(PACKET_V5)
    for key in (
        "SOURCE_METADATA_CONTEXT_SHA256",
        "TRUSTED_CONTEXT_SHA256",
        "PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE",
    ):
        if packet[key] != v5[key]:
            raise ValidationError(f"{key} moved from V5")
    post = packet["OUTPUT_POST_PROCESSING"]
    if set(post) != set(POST_PROCESSING) or any(post[key] is not False for key in POST_PROCESSING):
        raise ValidationError(
            "an answer may be changed to fit a bound. Truncation, dropping, rewriting, summarising, "
            "splitting and normalising are all refused, and a target is never a reason to"
        )
    for path, name in ((GATE_86, "86"),):
        _validates(path, name)


def _check_prompt(packet: dict[str, Any], parts: Any) -> None:
    v5 = _load(PACKET_V5)
    prompt = _load(PROMPT_V6)
    live = second_opportunity_prompt_hash_v1_5(parts)
    same_as_v5 = (
        "PROMPT_ALIGNMENT_DECISION",
        "PROMPT_ALIGNMENT_RECORD_SHA256",
        "SEMANTIC_PROMPT_ALIGNMENT_DECISION",
        "SEMANTIC_PROMPT_ALIGNMENT_RECORD_SHA256",
        "GENERATION_HEADROOM_DECISION",
        "GENERATION_HEADROOM_RECORD_SHA256",
        "GENERATION_HEADROOM_POLICY",
        "GENERATION_TARGET_RATIO",
        "ARRAY_HEADROOM_POLICY",
        "GENERATION_HEADROOM_RENDERER",
        "FIELD_ROLE_POLICY",
        "GENERATION_HEADROOM_POLICY_DIGEST",
        "NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT",
        "OUTPUT_CONSTRAINT_RENDERER",
        "SEMANTIC_GENERATION_RULES_RENDERER",
        "SEMANTIC_RULE_CENSUS",
        "SOURCE_LABEL_BLOCK_RENDERER",
        "SEMANTIC_GENERATION_POLICY_DIGEST",
    )
    for key in same_as_v5:
        if packet[key] != v5[key]:
            raise ValidationError(f"{key} moved from V5")
    _fixed(
        packet,
        {
            "STAGE_6_TO_9_PREFLIGHT_RECORD_SHA256": text_sha(PREFLIGHT_V2),
            "GENERATION_HEADROOM_DECISION": list(OPERATOR_DECISION_GENERATION_HEADROOM),
            "GENERATION_HEADROOM_RECORD_SHA256": text_sha(HEADROOM),
            "GENERATION_HEADROOM_POLICY": GENERATION_HEADROOM_POLICY.name,
            "GENERATION_TARGET_RATIO": GENERATION_HEADROOM_POLICY.ratio_text,
            "ARRAY_HEADROOM_POLICY": ARRAY_HEADROOM_POLICY,
            "GENERATION_HEADROOM_RENDERER": GENERATION_HEADROOM_RENDERER_VERSION,
            "FIELD_ROLE_POLICY": FIELD_ROLE_POLICY_VERSION,
            "GENERATION_HEADROOM_POLICY_DIGEST": headroom_policy_digest(),
            "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
            "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5,
            "PROMPT_SHA256": live,
            "PROMPT_RECORD_SHA256": text_sha(PROMPT_V6),
            "PROMPT_CHANGED": True,
            "OUTPUT_CONSTRAINT_RENDERER": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "SEMANTIC_GENERATION_RULES_RENDERER": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
            "SEMANTIC_RULE_CENSUS": SEMANTIC_RULE_CENSUS_VERSION,
            "SOURCE_LABEL_BLOCK_RENDERER": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
            "SEMANTIC_GENERATION_POLICY_DIGEST": policy_digest(),
        },
        "packet",
    )
    if (
        prompt["PROMPT_SHA256"] != live
        or prompt["PROMPT_VERSION"] != SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5
        or prompt["SYSTEM_INSTRUCTION"] != SECOND_OPPORTUNITY_SYSTEM_V1_5
        or prompt["PREDECESSOR_PROMPT_SHA256"] != PROMPT_V1_4_SHA256
        or prompt["SEMANTIC_GATE"]["implementation_sha256"] != GATE_IMPLEMENTATION_SHA256
    ):
        raise ValidationError("the prompt document is not the live v1.5.0 prompt over v1.4.0")
    spent = {_load(p)["PROMPT_SHA256"] for p in PACKETS}
    if live in spent:
        raise ValidationError("V6 binds a prompt a spent packet already sent")
    checks = prompt["CHECKS"]
    if (
        checks["UNSTATED_GENERATION_CONSTRAINTS"]
        or checks["UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES"]
        or checks["UNSTATED_GENERATION_TARGETS"]
        or checks["PROMPT_DRIFT"]
    ):
        raise ValidationError("the prompt record does not stand behind prompt v1.5.0")
    _validates(GATE_88, "88")


def _check_preflight(packet: dict[str, Any]) -> None:
    record = _validates(GATE_89, "89")
    if record["OUTCOME"] != "DETERMINISTIC_STAGE_6_TO_9_PATH_READY":
        raise ValidationError("DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY")
    if record["RETENTION_OUTCOME"] != "RETENTION_PATH_READY_FOR_NEXT_EXECUTION":
        raise ValidationError("RETENTION_PATH_NOT_READY_FOR_NEXT_EXECUTION")
    module = runner()
    fx = _module("fixtures_for_packet_v6", FIXTURES)
    gate_76 = _module("gate_76_for_packet_v6", GATE_76)
    # A target is guidance, never a bound: through the V6 runner's own stages, one character over a
    # target passes stage 5 and one character over the hard maximum fails it.
    rows = {row.path: row for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)}
    with gate_76.no_transport():
        for field in ("candidate_intervention_class", REASONING_SUMMARY_FIELD):
            row = rows[field]
            for length, refused in (
                (row.generation_target + 1, False),
                (row.hard_maximum + 1, True),
            ):
                answer = fx.good_output(**{field: "x" * length})
                report = module.validate_execution(fx.recorded_result(answer), fx.runner_context())
                at_stage_5 = report["failed_stage"] == "5_schema_validation_v1_2_0"
                if at_stage_5 is not refused:
                    raise ValidationError(
                        f"the V6 runner {'passes' if not at_stage_5 else 'refuses'} {field} at "
                        f"{length} characters: a generation target is enforced, or a hard maximum "
                        "is not"
                    )


def _check_representation(packet: dict[str, Any], snap: Any, parts: Any, wire: int) -> None:
    v5 = _load(PACKET_V5)
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
        if packet[key] != v5[key]:
            raise ValidationError(f"{key} is not what V5 and the approved egress rest on")
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
    hard, target = summary_bound()
    _fixed(
        packet["PREPARATION_VERIFICATION"],
        {
            "representation_sha256": REPRESENTATION_SHA256,
            "representation_characters": REPRESENTATION_CHARACTERS,
            "prompt_sha256": packet["PROMPT_SHA256"],
            "v1_4_prompt_sha256_recomputed": PROMPT_V1_4_SHA256,
            "selected_packet_id": packet["SELECTED_PACKET_ID"],
            "approved_evidence_rows": len(packet["APPROVED_EVIDENCE_IDS"]),
            "provider_posture": "APPROVED",
            "ted_external_model_transmission": "PERMITTED_WITH_CONDITIONS",
            "live_packet_gate": "AVAILABLE",
            "request_thinking": {"type": "disabled"},
            "request_max_tokens": packet["MAX_OUTPUT_TOKENS"],
            "request_body_characters": wire,
            "v5_request_body_characters_recomputed": V5_WIRE_CHARACTERS,
            "unstated_generation_constraints": 0,
            "unstated_generation_relevant_semantic_rules": 0,
            "unstated_generation_targets": 0,
            "output_schema_sha256": packet["OUTPUT_SCHEMA_SHA256"],
            "semantic_gate_implementation_sha256": GATE_IMPLEMENTATION_SHA256,
            "reasoning_summary_hard_max_and_target": [hard, target],
            "pricing_version": packet["PRICING_VERSION"],
            "worst_case_from_the_configured_table": packet["WORST_CASE_CALL_COST"],
            "source_metadata_context_sha256": packet["SOURCE_METADATA_CONTEXT_SHA256"],
            "trusted_context_sha256": packet["TRUSTED_CONTEXT_SHA256"],
            "stages_6_to_9_ready": True,
            "v1_guard_refuses_v1": True,
            "v2_guard_refuses_v2": True,
            "v3_guard_refuses_v3": True,
            "v4_guard_refuses_v4": True,
            "v5_guard_refuses_v5": True,
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


# --------------------------------------------------------------------------- V5's call, unchanged


def _check_route(packet: dict[str, Any]) -> None:
    register = _load(PROVIDER_REGISTER)
    approved = sorted(
        str(e["provider_id"]) for e in register["providers"] if e.get("posture") == "APPROVED"
    )
    if approved != ["anthropic"]:
        raise ValidationError(
            f"PROVIDER_ROUTE_NO_LONGER_APPROVED: the register approves {approved}"
        )
    v5 = _load(PACKET_V5)
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
        "STRUCTURED_OUTPUT_MECHANISM",
        "NATIVE_PROVIDER_STRUCTURED_OUTPUT",
        "RETENTION_ON_EXECUTION",
        "failure_outcome",
        "output_limit_outcome",
    ):
        if packet[key] != v5[key]:
            raise ValidationError(f"{key} moved from V5")
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
    if tuple(packet["MAX_OUTPUT_TOKENS_NOT_BASED_ON"]) != (
        *v5["MAX_OUTPUT_TOKENS_NOT_BASED_ON"],
        "V5_OBSERVED_OUTPUT_TOKENS",
    ):
        raise ValidationError("the ceiling's basis no longer excludes V5's observed output")
    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if packet["MAX_OUTPUT_TOKENS"] != capability["DOCUMENTED_MAX_OUTPUT_TOKENS"]:
        raise ValidationError("max_tokens is not the documented synchronous maximum")


def _check_calls_and_timeout(packet: dict[str, Any]) -> None:
    v5 = _load(PACKET_V5)
    params = packet["GENERATION_PARAMETERS"]
    if params != {
        **v5["GENERATION_PARAMETERS"],
        "response_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
    }:
        raise ValidationError("the generation parameters moved from V5 beyond the response schema")
    supplied = {k: v for k, v in params.items() if k != "$comment" and not k.endswith("note")}
    for key, value in supplied.items():
        if value is not None and key not in LLM_REQUEST_FIELDS:
            raise ValidationError(f"{key!r} is frozen with a value nothing reads")
    if supplied.get("max_retries") != 0 or packet["MAX_RETRIES"] != 0:
        raise ValidationError("a retry is a second call, and V6 authorises one")
    if packet["MAX_MODEL_CALLS"] != 1:
        raise ValidationError(f"MAX_MODEL_CALLS is {packet['MAX_MODEL_CALLS']}")
    for key in CALL_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if packet["REQUEST_TIMEOUT"] != v5["REQUEST_TIMEOUT"]:
        raise ValidationError("the timeout moved from V5")
    elapsed = _load(RECORD_V5)["timing"]["elapsed_seconds"]
    _fixed(
        packet["TIMEOUT"],
        {
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "TIMEOUT_CHANGED_BY_THIS_MISSION": False,
            "V5_OBSERVED_ELAPSED_SECONDS": elapsed,
            "V5_OBSERVATION_USED_TO_CHANGE_THE_TIMEOUT": False,
            "STREAMING": False,
            "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
            "TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS": True,
            "ON_TIMEOUT": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
        },
        "TIMEOUT",
    )


def _check_cost(packet: dict[str, Any], snap: Any, parts: Any, parts_v1_4: Any) -> int:
    v5 = _load(PACKET_V5)
    record_v5 = _load(RECORD_V5)
    if (
        packet["PRICING_VERSION"] != v5["PRICING_VERSION"]
        or packet["PRICE_PER_1K"] != v5["PRICE_PER_1K"]
    ):
        raise ValidationError("MODEL_COST_BASIS_REQUIRES_REFRESH: the price moved from V5")
    price = packet["PRICE_PER_1K"]
    held = ModelPrice(input_per_1k=float(price["input"]), output_per_1k=float(price["output"]))
    v5_wire = wire_characters(_module("runner_v5_for_packet_v6", RUNNER_V5), parts_v1_4, v5)
    if v5_wire != V5_WIRE_CHARACTERS:
        raise ValidationError(
            f"V5's body rebuilds to {v5_wire} characters, not the {V5_WIRE_CHARACTERS} it sent"
        )
    wire = wire_characters(runner(), parts, packet)
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
            "v5_wire_characters": V5_WIRE_CHARACTERS,
            "delta_characters_over_v5": wire - V5_WIRE_CHARACTERS,
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
    previous = float(v5["EXECUTION_COST_CEILING"])
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
    usage = record_v5["ACTUAL_USAGE"]
    _fixed(
        packet["V5_OBSERVATION"],
        {
            "V5_INPUT_TOKEN_ESTIMATE": v5["INPUT_TOKEN_ESTIMATE"],
            "V5_ACTUAL_INPUT_TOKENS": usage["input_tokens"],
            "V5_ESTIMATE_COVERED_THE_ACTUAL": v5["INPUT_TOKEN_ESTIMATE"] >= usage["input_tokens"],
            "V5_ACTUAL_OUTPUT_TOKENS": usage["output_tokens"],
            "USED_TO_CHANGE_THE_ESTIMATION_METHOD": False,
            "USED_TO_REDUCE_MAX_OUTPUT_TOKENS": False,
            "USED_TO_SET_THE_SUMMARY_BOUND": False,
        },
        "V5_OBSERVATION",
    )
    return wire


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
                raise ValidationError(f"{path} names {test!r}, which no V6 runner test defines")
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
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V6 does 0")
    if packet["CANONICAL_COUNTERS"] != CANONICAL_COUNTERS:
        raise ValidationError("a canonical counter moved")


def _check_runner(packet: dict[str, Any], parts: Any, parts_v1_4: Any) -> None:
    source = RUNNER.read_text(encoding="utf-8")
    _through(G81._check_single_call_site, source)
    _through(G81._check_no_post_processing, source)
    module = runner()
    if module.EXPECTED["EXECUTION_PACKET_SHA256"] != packet["EXECUTION_PACKET_SHA256"]:
        raise ValidationError("the runner was prepared for another digest")
    for key, value in module.EXPECTED.items():
        if key in packet and packet[key] != value:
            raise ValidationError(
                f"the runner expects {key}={value!r} and V6 binds {packet[key]!r}"
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
    if module.unstated_targets(parts_v1_4) != [REASONING_SUMMARY_FIELD]:
        raise ValidationError("the runner's headroom check would pass prompt v1.4.0 under v1.2.0")


def validate() -> dict[str, Any]:
    packet = _load(PACKET)
    snap, parts, parts_v1_4 = snapshot()
    _check_identity_and_approval(packet)
    _check_predecessors(packet)
    _check_contract_and_gate(packet)
    _check_prompt(packet, parts)
    _check_preflight(packet)
    _check_route(packet)
    _through(G81._check_thinking_and_envelope, packet, snap)
    _check_calls_and_timeout(packet)
    wire = _check_cost(packet, snap, parts, parts_v1_4)
    _check_representation(packet, snap, parts, wire)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet, parts, parts_v1_4)
    return packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v6.py "
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
    observed = packet["V5_OBSERVATION"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v6",
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
                f"reasoning summary                   hard maximum "
                f"{packet['REASONING_SUMMARY_HARD_MAX']}, generation target "
                f"{packet['REASONING_SUMMARY_GENERATION_TARGET']} "
                f"({packet['REASONING_SUMMARY_DECISION_BASIS']})",
                f"semantic gate                       {packet['OUTPUT_GATE_VERSION']}",
                f"gate implementation                 {packet['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}",
                f"gate frozen tests                   {packet['SEMANTIC_GATE_FROZEN_TEST_SHA256']}",
                f"gate freeze commit                  {packet['SEMANTIC_GATE_FREEZE_COMMIT']}",
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
                "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6 "
                f"{str(packet['RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6']).lower()}",
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{str(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']).lower()}",
                "NEW_APPROVAL_REQUIRED               "
                f"{str(packet['NEW_APPROVAL_REQUIRED']).lower()}",
                "PREVIOUS_APPROVAL_REUSABLE          "
                f"{str(packet['PREVIOUS_APPROVAL_REUSABLE']).lower()}",
            ]
        ),
        "## What changed from V5",
        "",
        f"{_sentence(packet['contract_note'])} {_sentence(packet['gate_note'])} Prompt "
        f"v{packet['PROMPT_VERSION']}: {_sentence(packet['prompt_note'])}",
        "",
        "## Cost, recomputed from the new request body",
        "",
        *_code(
            [
                f"request body             {basis['wire_characters']} characters  "
                f"(V5 {basis['v5_wire_characters']} + {basis['delta_characters_over_v5']})",
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
                f"previous ceiling (V5)    {_cost(packet['PREVIOUS_EXECUTION_COST_CEILING'])}  "
                f"(+{_cost(packet['CEILING_DELTA_OVER_PREVIOUS'])}, "
                f"x{packet['CEILING_OVER_PREVIOUS_CEILING']})",
            ]
        ),
        f"V5 estimated {observed['V5_INPUT_TOKEN_ESTIMATE']} input tokens and used "
        f"{observed['V5_ACTUAL_INPUT_TOKENS']}; it used {observed['V5_ACTUAL_OUTPUT_TOKENS']} "
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
    print("ok       packet V6 is V5's call over schema v1.2.0, gate v1.4.0 and prompt v1.5.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
