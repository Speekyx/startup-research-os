"""Mission 1.84.8, CI gate 73. Execution packet V3: V2's call, with the prompt aligned to the schema.

V3 changes one thing about the call V2 made, and gate 72 is where that thing is checked: the prompt
is v1.2.0, whose output-contract block is derived from the unchanged v1.1.0 schema. Everything else
is V2's, and this gate checks that it still is, against V2's packet and the live code rather than
against a copy of either:

* the route, the model, thinking DISABLED and `max_tokens` 128000, built into a request body by the
  live adapter and read back;
* the provider completion policy, through the adapter's own classifier, read before any parse;
* one call, no retry, no continuation, no repair, and a timeout that did not move;
* the ten ordered stages, the persistence policy and the retention policy;
* the cost, recomputed from the new request body at the held price.

**What CI cannot re-derive, and checks for agreement instead.** The TED representation, the rendered
v1.2.0 prompt digest and the request body length are rebuilt from the research database by the
runner's verification. The packet records what the preparing machine found; the body length is also
checked against arithmetic CI can do: V2's body plus the difference between the two system regions.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import importlib.util
import json
import math
import pathlib
from collections.abc import Iterator
from typing import Any

from sros_llm_gateway.pricing import ModelPrice
from sros_llm_gateway.prompts.rendering import RenderedPrompt
from sros_llm_gateway.providers.anthropic import (
    DEFAULT_ENDPOINT,
    FORCED_TOOL_COMPLETE_STOP_REASON,
    OUTPUT_LIMIT_STOP_REASONS,
    REFUSAL_STOP_REASON,
    STRUCTURED_TOOL_NAME,
    AnthropicCompletion,
    AnthropicProvider,
    AnthropicThinking,
    classify_forced_tool_completion,
)
from sros_llm_gateway.types import LlmRequest, LlmTier
from sros_opportunity.output_constraints import OUTPUT_CONSTRAINT_RENDERER_VERSION
from sros_opportunity.second_opportunity import (
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_ID,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
    SECOND_OPPORTUNITY_SYSTEM_V1_1,
    SECOND_OPPORTUNITY_SYSTEM_V1_2,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

PACKET = DATA / "second-opportunity-synthesis-execution-packet-v3.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v3.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v3.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v3.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v3.py"
)

PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
RECORD_V1 = DATA / "second-opportunity-synthesis-execution-record-v1.json"
RECORD_V2 = DATA / "second-opportunity-synthesis-execution-record-v2.json"
DECISION = DATA / "second-opportunity-execution-envelope-decision-v1.json"
ALIGNMENT = DATA / "second-opportunity-output-constraint-alignment-v1.json"
PROMPT_V3 = DATA / "second-opportunity-synthesis-prompt-v3.json"
MEASUREMENT = DATA / "second-opportunity-provider-token-measurement-v1.json"
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
PROVIDER_REGISTER = DATA / "model-provider-policy-v1.json"
PREPARATION_V5 = DATA / "opportunity-preparation-v5.json"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V3"
PACKET_VERSION = 3
PREPARED_BY = "mission-1.84.8"
THIS_MISSION = (1, 84, 8)
V1_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V1"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
V2_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V2"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
SUBJECT = "ted-eu:CPV-class:9261"
MODEL = "claude-sonnet-5"
REPRESENTATION_CHARACTERS = 3604

ENVELOPE_DECISION = "RUN_AT_THE_PROVIDER_MAXIMUM_ACCEPTING_AN_UNREACHABLE_WORST_CASE"
ALIGNMENT_DECISIONS = (
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_OUTPUT_GATE_V1_1_0_UNCHANGED",
    "DO_NOT_RAISE_EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH",
    "CORRECT_PROMPT_SCHEMA_CONSTRAINT_ALIGNMENT",
)
ROUTES_NOT_USED = ["MESSAGE_BATCHES_BETA", "anthropic-claude-subscription"]
#: The route as reviewed, pinned whole, as gate 70 pins it: a test for a word is passed by a word
#: containing it, and a pinned sentence cannot be reworded into another route.
PROVIDER_ROUTE_TEXT = (
    "The Anthropic API, synchronous Messages endpoint, accessed with an API key under the "
    "Commercial Terms of Service. Not the Message Batches beta, and not a consumer subscription."
)
DOCUMENTED_SYNCHRONOUS_MAXIMUM = 128000
MAX_OUTPUT_TOKENS_BASIS = "OPERATOR_SELECTED_DOCUMENTED_PROVIDER_MAXIMUM"
OUTPUT_TOKEN_CEILING_BASIS = "OPERATOR_SELECTED_PROVIDER_MAXIMUM"  # noqa: S105 -- an output-token basis, not a credential
#: V2's three, and a fourth this mission adds: the 3914 tokens V2 used are one sample, and an
#: envelope sized to one sample is an envelope optimised around it.
NOT_BASED_ON = (
    "SCHEMA_DERIVED_MAXIMUM",
    "PROVIDER_NATIVE_TOKEN_ESTIMATE",
    "EMPIRICAL_CHARS_PER_TOKEN",
    "V2_OBSERVED_OUTPUT_TOKENS",
)
CHARS_PER_TOKEN = 2.1565
CONSERVATIVE_MULTIPLIER = 1.25

STAGES = (
    "1_transport_success",
    "2_provider_response_shape",
    "3_provider_completion",
    "4_structured_output_parse",
    "5_schema_validation_v1_1_0",
    "6_semantic_output_gate_v1_1_0",
    "7_evidence_boundary_and_no_distortion",
    "8_attribution_and_provenance",
    "9_persistence_eligibility",
    "10_human_review",
)
READY = "SECOND_OPPORTUNITY_EXECUTION_PACKET_V3_READY_FOR_OPERATOR_APPROVAL"

CAPABILITY_NEGATIVES = (
    "TRAINING",
    "FINE_TUNING",
    "EMBEDDINGS",
    "WEB",
    "TOOLS",
    "EXTERNAL_RETRIEVAL",
    "HIDDEN_REASONING_RETENTION",
)
CALL_NEGATIVES = (
    "FALLBACK_MODEL",
    "FALLBACK_PROVIDER",
    "FALLBACK_ROUTE",
    "CONTINUATION_REQUESTS",
    "REPAIR_MODEL",
)
POST_PROCESSING = (
    "TRUNCATION",
    "ITEM_DROPPING",
    "REWRITING",
    "AUTO_SUMMARY",
    "STATEMENT_SPLITTING",
    "SEMANTIC_NORMALISATION",
)
PREPARATION_ZERO = (
    "MODEL_CALLS",
    "MESSAGES_API_REQUESTS",
    "PROVIDER_INFERENCE_REQUESTS",
    "TOKEN_COUNT_API_REQUESTS",
    "REMOTE_TEST_CALLS",
    "TED_BYTES_SENT",
    "DOCUMENTATION_FETCHES",
    "CANONICAL_MUTATIONS",
    "OPPORTUNITIES_CREATED",
    "CREDENTIAL_VALUES_READ_OR_LOGGED",
)
#: The ten terminal paths the brief names, each exercised by a synthetic transport.
RETENTION_PATHS = (
    "success",
    "provider_output_limit",
    "timeout",
    "provider_refusal",
    "unsupported_stop_reason",
    "parse_failure",
    "schema_failure",
    "semantic_failure",
    "provenance_failure",
    "human_review_ready_success",
)
RETENTION_PROPERTIES = (
    "usage_retained",
    "request_id_retained",
    "digests_retained",
    "terminal_outcome_retained",
    "hidden_reasoning_not_retained",
    "secrets_redacted",
    "no_network",
    "post_call_fail_safe",
)

CANONICAL_COUNTERS = {
    "acquisition.raw_records": 325,
    "acquisition.normalized_records": 325,
    "nlp.signals": 60,
    "research.claims": 91,
    "research.claim_revisions": 92,
    "scoring.evidence": 112,
    "epistemic.reliability_assessments": 4,
    "scoring.evidence_independence_groups": 0,
    "research.opportunities": 1,
    "research.opportunity_hypothesis_revisions": 2,
    "research.opportunity_hypothesis_evidence": 14,
    "nlp.embedding_provenance": 0,
    "registry.source_policy_reviews": 71,
}

COMPLETION_PROBES: tuple[object, ...] = ("end_turn", "pause_turn", "stop_sequence", "", None)

LLM_REQUEST_FIELDS = frozenset(f.name for f in dataclasses.fields(LlmRequest))
ADAPTER_FIELDS = frozenset(f.name for f in dataclasses.fields(AnthropicProvider))

#: The fields the V3 digest binds. Kept here rather than read from the record, because a digest over
#: whichever fields the record nominates is a digest the record can shrink.
DIGEST_FIELDS = (
    "EXECUTION_PACKET_ID",
    "EXECUTION_PACKET_VERSION",
    "PREDECESSOR_EXECUTION_PACKET_ID",
    "PREDECESSOR_EXECUTION_PACKET_SHA256",
    "PREDECESSOR_EXECUTION_OUTCOME",
    "PREDECESSOR_APPROVAL_CONSUMED",
    "CONSUMED_EXECUTION_PACKETS",
    "EXECUTION_ENVELOPE_DECISION",
    "EXECUTION_ENVELOPE_DECISION_SHA256",
    "PROMPT_ALIGNMENT_DECISION",
    "PROMPT_ALIGNMENT_RECORD_SHA256",
    "SOURCE_DECISION_PACKET_ID",
    "SOURCE_DECISION_PACKET_VERSION",
    "SOURCE_DECISION_PACKET_SHA256",
    "SUBJECT_KEY",
    "SELECTED_PACKET_ID",
    "PREPARATION_VERSION",
    "PROCESSING_PURPOSE",
    "REPRESENTATION_SCHEMA",
    "REPRESENTATION_SHA256",
    "PROVIDER_ID",
    "PROVIDER_ROUTE",
    "PROVIDER_ROUTE_SURFACE",
    "BETA_HEADERS",
    "ROUTES_NOT_USED",
    "PROVIDER_POSTURE",
    "MODEL_ID",
    "MODEL_TIER",
    "THINKING",
    "THINKING_REQUEST_FIELD",
    "ADAPTER_PARAMETERS",
    "PROMPT_ID",
    "PROMPT_VERSION",
    "PROMPT_SHA256",
    "PROMPT_CHANGED",
    "OUTPUT_CONSTRAINT_RENDERER",
    "OUTPUT_SCHEMA_VERSION",
    "OUTPUT_SCHEMA_SHA256",
    "OUTPUT_GATE_VERSION",
    "SCHEMA_CHANGED",
    "GATE_CHANGED",
    "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL",
    "CONTRACT_THEORETICAL_MAX_EXCEEDS_EXECUTION_ENVELOPE",
    "PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE",
    "ESTIMATE_EXACT",
    "GENERATION_PARAMETERS",
    "MAX_OUTPUT_TOKENS",
    "OUTPUT_TOKEN_CEILING",
    "MAX_OUTPUT_TOKENS_BASIS",
    "OUTPUT_TOKEN_CEILING_BASIS",
    "MAX_OUTPUT_TOKENS_NOT_BASED_ON",
    "INPUT_TOKEN_ESTIMATE",
    "TOTAL_TOKEN_CEILING",
    "PRICING_VERSION",
    "PRICE_PER_1K",
    "INPUT_WORST_CASE_COST",
    "OUTPUT_WORST_CASE_COST",
    "WORST_CASE_CALL_COST",
    "EXECUTION_COST_CEILING",
    "HEADROOM_POLICY",
    "MAX_MODEL_CALLS",
    "MAX_RETRIES",
    "FALLBACK_MODEL",
    "FALLBACK_PROVIDER",
    "FALLBACK_ROUTE",
    "CONTINUATION_REQUESTS",
    "REPAIR_MODEL",
    "REQUEST_TIMEOUT",
    "PROVIDER_COMPLETION_POLICY",
    "VALIDATION_STAGES",
    "PERSISTENCE_POLICY",
    "STRUCTURED_OUTPUT_MECHANISM",
    "NATIVE_PROVIDER_STRUCTURED_OUTPUT",
    "LOCAL_SCHEMA_VALIDATOR_MANDATORY",
    "OUTPUT_POST_PROCESSING",
    "TRAINING",
    "FINE_TUNING",
    "EMBEDDINGS",
    "WEB",
    "TOOLS",
    "EXTERNAL_RETRIEVAL",
    "HIDDEN_REASONING_RETENTION",
    "RETENTION_ON_EXECUTION",
    "failure_outcome",
    "output_limit_outcome",
)


class ValidationError(RuntimeError):
    """The packet disagrees with V2, with the alignment record, or with live code."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _keys(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, sub in value.items():
            yield str(key)
            yield from _keys(sub)
    elif isinstance(value, list):
        for sub in value:
            yield from _keys(sub)


def _mission_key(value: object) -> tuple[int, ...] | None:
    if not isinstance(value, str) or not value.startswith("mission-"):
        return None
    try:
        return tuple(int(part) for part in value.removeprefix("mission-").split("."))
    except ValueError:
        return None


def _bindable(value: object) -> object:
    """Notes and cited documentation explain a field and do not bind it."""
    if isinstance(value, dict):
        return {
            k: _bindable(v)
            for k, v in value.items()
            if k != "$comment" and not k.endswith("note") and k != "documentation"
        }
    if isinstance(value, list):
        return [_bindable(v) for v in value]
    return value


def packet_digest(packet: dict[str, Any]) -> str:
    """Recompute the V3 execution digest from the packet's own bound fields."""
    bound: dict[str, object] = {}
    for key in DIGEST_FIELDS:
        if key not in packet:
            raise ValidationError(f"the execution packet has no {key!r} to bind")
        bound[key] = _bindable(packet[key])
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return _sha256(payload)


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


def system_region_delta() -> int:
    """How much longer the v1.2.0 system region is than v1.1.0's, as the transport serialises it."""
    return len(json.dumps(SECOND_OPPORTUNITY_SYSTEM_V1_2)) - len(
        json.dumps(SECOND_OPPORTUNITY_SYSTEM_V1_1)
    )


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
            "EXECUTION_ENVELOPE_DECISION": ENVELOPE_DECISION,
        },
        "packet",
    )
    recomputed = packet_digest(packet)
    if packet["EXECUTION_PACKET_SHA256"] != recomputed:
        raise ValidationError(
            f"the packet records {packet['EXECUTION_PACKET_SHA256']} and its bound fields hash "
            f"to {recomputed}"
        )
    if recomputed in (V1_SHA256, V2_SHA256):
        raise ValidationError("V3 carries a spent predecessor's digest")
    note = str(packet["approval_note"])
    for word in ("egress", "V2", "beside", "prompt"):
        if word not in note:
            raise ValidationError(
                "the approval note does not keep this approval apart from V1's and V2's, from the "
                "prompt decision and from TED egress"
            )
    if packet["EXECUTION_ENVELOPE_DECISION_SHA256"] != _file_sha(DECISION):
        raise ValidationError("the envelope decision record changed after the packet bound it")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = _mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V3 recorded by the mission that prepared it. Preparing a packet "
                "authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V3's")
    return recomputed


def _check_predecessors(packet: dict[str, Any]) -> None:
    v1, v2 = _load(PACKET_V1), _load(PACKET_V2)
    record_v1, record_v2 = _load(RECORD_V1), _load(RECORD_V2)
    if v1["EXECUTION_PACKET_SHA256"] != V1_SHA256 or v2["EXECUTION_PACKET_SHA256"] != V2_SHA256:
        raise ValidationError("a spent predecessor's packet digest moved")
    for name, frozen in (("V1", v1), ("V2", v2)):
        if frozen["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
            raise ValidationError(f"the frozen {name} packet was edited to record an approval")
    if record_v1["EXECUTION_APPROVAL_CONSUMED"] is not True:
        raise ValidationError("V1's consumption was reset")
    if record_v2["EXECUTION_APPROVAL_CONSUMED"] is not True:
        raise ValidationError("V2's consumption was reset")
    if record_v2["FURTHER_CALLS_AUTHORIZED_BY_V2"] is not False:
        raise ValidationError("V2 now authorises further calls")
    if record_v2["execution_packet_sha256"] != V2_SHA256:
        raise ValidationError("V2's record names another digest")
    if (
        record_v2["HUMAN_REVIEW_PACKET"] != "NOT_PRODUCED"
        or record_v2["OPPORTUNITY_PERSISTED"] is not False
        or record_v2["CANONICAL_PERSISTENCE"] is not False
    ):
        raise ValidationError(
            "V2's record now treats its rejected answer as a candidate. V3 is a new call with a new "
            "prompt, never a second chance for V2's answer"
        )
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V2_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V2_SHA256,
            "PREDECESSOR_EXECUTION_OUTCOME": record_v2["PRIMARY_OUTCOME"],
            "PREDECESSOR_APPROVAL_CONSUMED": True,
            "CONSUMED_EXECUTION_PACKETS": [
                {"id": V1_ID, "sha256": V1_SHA256, "outcome": record_v1["PRIMARY_OUTCOME"]},
                {"id": V2_ID, "sha256": V2_SHA256, "outcome": record_v2["PRIMARY_OUTCOME"]},
            ],
        },
        "packet",
    )
    if record_v2["PRIMARY_OUTCOME"] != "EXECUTION_SCHEMA_REJECTED_NO_RETRY":
        raise ValidationError("V2's outcome is recorded as something other than its schema refusal")


# --------------------------------------------------------------------------- the one change


def _check_alignment_and_prompt(packet: dict[str, Any]) -> None:
    alignment = _load(ALIGNMENT)
    prompt = _load(PROMPT_V3)
    v2 = _load(PACKET_V2)
    _fixed(
        packet,
        {
            "PROMPT_ALIGNMENT_DECISION": list(ALIGNMENT_DECISIONS),
            "PROMPT_ALIGNMENT_RECORD_SHA256": _file_sha(ALIGNMENT),
            "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
            "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
            "PROMPT_SHA256": prompt["PROMPT_SHA256"],
            "PROMPT_CHANGED": True,
            "OUTPUT_CONSTRAINT_RENDERER": OUTPUT_CONSTRAINT_RENDERER_VERSION,
        },
        "packet",
    )
    if alignment["OPERATOR_DECISION"]["DECISIONS"] != list(ALIGNMENT_DECISIONS):
        raise ValidationError("the alignment record names a decision the packet does not")
    if alignment["PROMPT"]["SUCCESSOR_SHA256"] != packet["PROMPT_SHA256"]:
        raise ValidationError("the alignment record and the packet name different prompts")
    if prompt["PROMPT_VERSION"] != SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2:
        raise ValidationError("the prompt document is not v1.2.0")
    if prompt["SYSTEM_INSTRUCTION"] != SECOND_OPPORTUNITY_SYSTEM_V1_2:
        raise ValidationError("the prompt document's system region is not the live v1.2.0 one")
    if packet["PROMPT_SHA256"] in (v2["PROMPT_SHA256"], _load(PACKET_V1)["PROMPT_SHA256"]):
        raise ValidationError("V3 binds a prompt a spent packet already sent")
    if alignment["UNSTATED_IN_V1_2_0"]:
        raise ValidationError(
            "the aligned prompt still leaves a generation-relevant bound unstated"
        )


def _check_contract(packet: dict[str, Any]) -> None:
    live = hashlib.sha256(
        json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, sort_keys=True).encode("utf-8")
    ).hexdigest()
    _fixed(
        packet,
        {
            "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
            "OUTPUT_SCHEMA_SHA256": live,
            "OUTPUT_GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
            "SCHEMA_CHANGED": False,
            "GATE_CHANGED": False,
            "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL": False,
            "ESTIMATE_EXACT": False,
            "LOCAL_SCHEMA_VALIDATOR_MANDATORY": True,
        },
        "packet",
    )
    v2 = _load(PACKET_V2)
    for key in ("OUTPUT_SCHEMA_VERSION", "OUTPUT_SCHEMA_SHA256", "OUTPUT_GATE_VERSION"):
        if packet[key] != v2[key]:
            raise ValidationError(f"{key} moved from V2, and the operator kept the contract")
    measured = _load(MEASUREMENT)["MEASUREMENT"]["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"]
    if packet["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"] != measured:
        raise ValidationError("the theoretical-maximum estimate is not Mission 1.84.5's")
    if "EXACT_MAX_OUTPUT_TOKEN_COUNT" in set(_keys(packet)):
        raise ValidationError("an exact output token count is recorded; 231608 is an estimate")
    exceeds = packet["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"] > packet["MAX_OUTPUT_TOKENS"]
    if packet["CONTRACT_THEORETICAL_MAX_EXCEEDS_EXECUTION_ENVELOPE"] is not exceeds or not exceeds:
        raise ValidationError(
            "CONTRACT_THEORETICAL_MAX_EXCEEDS_EXECUTION_ENVELOPE disagrees with the arithmetic"
        )
    post = packet["OUTPUT_POST_PROCESSING"]
    if set(post) != set(POST_PROCESSING) or any(post[key] is not False for key in POST_PROCESSING):
        raise ValidationError(
            "an answer may be changed to fit a bound. Truncation, dropping, rewriting, summarising, "
            "splitting and normalising are all refused, and a 901-character summary stays invalid"
        )


def _check_representation(packet: dict[str, Any]) -> None:
    v2 = _load(PACKET_V2)
    for key in (
        "SOURCE_DECISION_PACKET_ID",
        "SOURCE_DECISION_PACKET_VERSION",
        "SOURCE_DECISION_PACKET_SHA256",
        "SUBJECT_KEY",
        "SELECTED_PACKET_ID",
        "PREPARATION_VERSION",
        "PROCESSING_PURPOSE",
        "REPRESENTATION_SCHEMA",
    ):
        if packet[key] != v2[key]:
            raise ValidationError(f"{key} is not what the approved egress rests on")
    if packet["REPRESENTATION_SHA256"] != v2["REPRESENTATION_SHA256"]:
        raise ValidationError(
            "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED: the representation digest is not the "
            "approved one"
        )
    if packet["REPRESENTATION_CHARACTER_COUNT"] != REPRESENTATION_CHARACTERS:
        raise ValidationError("the representation is not 3604 characters")

    verified = packet["PREPARATION_VERIFICATION"]
    _fixed(
        verified,
        {
            "representation_sha256": packet["REPRESENTATION_SHA256"],
            "representation_characters": REPRESENTATION_CHARACTERS,
            "prompt_sha256": packet["PROMPT_SHA256"],
            "v1_1_prompt_sha256_recomputed": v2["PROMPT_SHA256"],
            "selected_packet_id": packet["SELECTED_PACKET_ID"],
            "provider_posture": "APPROVED",
            "subscription_route_posture": "NOT_APPROVED",
            "ted_external_model_transmission": "PERMITTED_WITH_CONDITIONS",
            "ted_eligibility": "ELIGIBLE",
            "live_packet_gate": "AVAILABLE",
            "live_gate_refusals": [],
            "request_thinking": {"type": "disabled"},
            "request_max_tokens": packet["MAX_OUTPUT_TOKENS"],
            "request_body_characters": packet["TOKEN_ESTIMATION_BASIS"]["wire_characters"],
            "v2_request_body_characters_recomputed": v2["TOKEN_ESTIMATION_BASIS"][
                "wire_characters"
            ],
            "unstated_generation_constraints": 0,
            "pricing_version": packet["PRICING_VERSION"],
            "worst_case_from_the_configured_table": packet["WORST_CASE_CALL_COST"],
            "v1_guard_refuses_v1": True,
            "v2_guard_refuses_v2": True,
            "guard_permits_an_unseen_digest": True,
        },
        "PREPARATION_VERIFICATION",
    )

    preparation = _load(PREPARATION_V5)
    if packet["PREPARATION_VERSION"] != preparation["artifact_version"]:
        raise ValidationError("the packet names a preparation that is not the current one")
    selected = next((p for p in preparation["packets"] if p.get("subject") == SUBJECT), None)
    if selected is None or selected["packet_id"] != packet["SELECTED_PACKET_ID"]:
        raise ValidationError("the current preparation does not carry the selected packet")
    if selected["external_synthesis"]["availability"] != "AVAILABLE":
        raise ValidationError("TED_EGRESS_NO_LONGER_AVAILABLE in the current preparation")


# --------------------------------------------------------------------------- V2's call, unchanged


def _check_route(packet: dict[str, Any]) -> None:
    register = _load(PROVIDER_REGISTER)
    approved = sorted(
        str(e["provider_id"]) for e in register["providers"] if e.get("posture") == "APPROVED"
    )
    if approved != ["anthropic"]:
        raise ValidationError(
            f"PROVIDER_ROUTE_NO_LONGER_APPROVED: the register approves {approved}"
        )
    _fixed(
        packet,
        {
            "PROVIDER_ID": "anthropic",
            "PROVIDER_POSTURE": "APPROVED",
            "PROVIDER_ROUTE_SURFACE": f"POST {DEFAULT_ENDPOINT}",
            "BETA_HEADERS": [],
            "ROUTES_NOT_USED": ROUTES_NOT_USED,
            "MODEL_ID": MODEL,
            "MODEL_TIER": "STRONG_MODEL",
            "MAX_OUTPUT_TOKENS_BASIS": MAX_OUTPUT_TOKENS_BASIS,
            "OUTPUT_TOKEN_CEILING_BASIS": OUTPUT_TOKEN_CEILING_BASIS,
        },
        "packet",
    )
    if packet["PROVIDER_ROUTE"] != PROVIDER_ROUTE_TEXT:
        raise ValidationError(
            "the route is not the synchronous Messages API under Commercial Terms, as reviewed"
        )
    if tuple(packet["MAX_OUTPUT_TOKENS_NOT_BASED_ON"]) != NOT_BASED_ON:
        raise ValidationError(
            "the ceiling's basis no longer excludes what it must exclude, V2's 3914 tokens included"
        )
    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if capability["DOCUMENTED_MAX_OUTPUT_TOKENS"] != DOCUMENTED_SYNCHRONOUS_MAXIMUM:
        raise ValidationError("MODEL_CAPABILITY_REQUIRES_REFRESH: the held maximum moved")
    if packet["MAX_OUTPUT_TOKENS"] != capability["DOCUMENTED_MAX_OUTPUT_TOKENS"]:
        raise ValidationError(
            f"max_tokens is {packet['MAX_OUTPUT_TOKENS']}; the operator selected the documented "
            f"synchronous maximum, {capability['DOCUMENTED_MAX_OUTPUT_TOKENS']}"
        )
    if packet["MAX_OUTPUT_TOKENS"] != _load(PACKET_V2)["MAX_OUTPUT_TOKENS"]:
        raise ValidationError("max_tokens moved from V2")
    if packet["OUTPUT_TOKEN_CEILING"] != packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError("the output token ceiling and max_tokens disagree")
    default = next(
        f.default for f in dataclasses.fields(AnthropicProvider) if f.name == "max_output_tokens"
    )
    if packet["ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS"] != default:
        raise ValidationError("the recorded adapter default is not the live adapter's")
    if default == packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError("the adapter default was confused with the documented capability")


class _NoTransport:
    def post_json(self, *args: object, **kwargs: object) -> Any:
        raise AssertionError("the gate builds a request body and never sends it")


def _live_body(packet: dict[str, Any]) -> dict[str, Any]:
    params = packet["ADAPTER_PARAMETERS"]
    if set(params) != {"max_output_tokens", "thinking"} or not set(params) <= ADAPTER_FIELDS:
        raise ValidationError(f"adapter parameters {sorted(params)}; V3 binds exactly two")
    try:
        thinking = AnthropicThinking[str(params["thinking"])]
    except KeyError as exc:
        raise ValidationError(
            f"THINKING_CONTROL_NO_LONGER_VALID: no thinking configuration {params['thinking']!r}"
        ) from exc
    provider = AnthropicProvider(
        api_key="gate-probe-not-a-credential",
        max_output_tokens=int(params["max_output_tokens"]),
        thinking=thinking,
        transport=_NoTransport(),
    )
    request = LlmRequest(
        tier=LlmTier.STRONG_MODEL,
        task="gate.probe",
        prompt_template_id="gate-probe",
        prompt_template_version="1.0.0",
        workspace_id="00000000-0000-4000-8000-000000000001",
        prompt=RenderedPrompt(
            system_instructions="probe", trusted_context="", task="probe", untrusted=()
        ),
        response_schema=SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    )
    return provider.build_body(request, MODEL)


def _check_thinking_and_envelope(packet: dict[str, Any]) -> None:
    _fixed(
        packet,
        {
            "THINKING": "DISABLED",
            "THINKING_REQUEST_FIELD": {"type": "disabled"},
            "THINKING_POLICY_EXPLICIT": True,
            "ADAPTIVE_THINKING_USED": False,
            "THINKING_TOKENS_SHARE_OUTPUT_BUDGET": False,
            "STRUCTURED_OUTPUT_MECHANISM": "FORCED_TOOL_USE",
            "NATIVE_PROVIDER_STRUCTURED_OUTPUT": False,
        },
        "packet",
    )
    if packet["ADAPTER_PARAMETERS"].get("thinking") != "DISABLED":
        raise ValidationError("the adapter would be built with adaptive thinking")
    if packet["ADAPTER_PARAMETERS"].get("max_output_tokens") != packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError("the adapter would be built with another max_tokens")
    body = _live_body(packet)
    if body.get("thinking") != {"type": "disabled"}:
        raise ValidationError(
            f"THINKING_CONTROL_NO_LONGER_VALID: the adapter sends {body.get('thinking')!r}"
        )
    if body.get("max_tokens") != packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError(f"the adapter sends max_tokens {body.get('max_tokens')}")
    if body.get("tool_choice") != {"type": "tool", "name": STRUCTURED_TOOL_NAME}:
        raise ValidationError("the structured output is no longer forced into its tool")
    if "output_config" in body or "strict" in body["tools"][0]:
        raise ValidationError("a structured-output migration rode along with the prompt change")
    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if capability["THINKING_DISABLE_SUPPORTED"] is not True:
        raise ValidationError("THINKING_CONTROL_NO_LONGER_VALID: disabling is not documented")


def _check_completion_policy(packet: dict[str, Any]) -> None:
    policy = packet["PROVIDER_COMPLETION_POLICY"]
    if policy != _load(PACKET_V2)["PROVIDER_COMPLETION_POLICY"]:
        raise ValidationError(
            "the provider completion policy moved from V2. A prompt change may not weaken it"
        )
    _fixed(
        policy,
        {
            "signal_field": "stop_reason",
            "complete_values": [FORCED_TOOL_COMPLETE_STOP_REASON],
            "output_limit_values": sorted(OUTPUT_LIMIT_STOP_REASONS),
            "refusal_values": [REFUSAL_STOP_REASON],
            "any_other_value": "FAIL_CLOSED",
            "PROVIDER_LIMIT_FAIL_CLOSED": True,
            "COMPLETION_SIGNAL_PRECEDES_PARSE": True,
            "on_output_limit": "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY",
            "on_refusal": "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY",
            "on_any_other_value": "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY",
        },
        "PROVIDER_COMPLETION_POLICY",
    )
    for value in policy["complete_values"]:
        if classify_forced_tool_completion(value) is not AnthropicCompletion.COMPLETE:
            raise ValidationError(f"PROVIDER_LIMIT_SIGNAL_NOT_FAIL_CLOSED: {value!r}")
    for value in policy["output_limit_values"]:
        if classify_forced_tool_completion(value) is not AnthropicCompletion.OUTPUT_LIMIT_REACHED:
            raise ValidationError(f"PROVIDER_LIMIT_SIGNAL_NOT_FAIL_CLOSED: {value!r}")
    for value in policy["refusal_values"]:
        if classify_forced_tool_completion(value) is not AnthropicCompletion.REFUSED:
            raise ValidationError(f"the adapter does not read {value!r} as a refusal")
    for probe in COMPLETION_PROBES:
        if (
            classify_forced_tool_completion(probe)
            is not AnthropicCompletion.UNSUPPORTED_STOP_REASON
        ):
            raise ValidationError(
                f"PROVIDER_LIMIT_SIGNAL_NOT_FAIL_CLOSED: {probe!r} is read as something known"
            )
    if packet["output_limit_outcome"] != policy["on_output_limit"]:
        raise ValidationError("the packet's output-limit outcome is not the policy's")
    if packet["failure_outcome"] != "EXECUTION_FAILED_NO_RETRY":
        raise ValidationError("a failure outcome that is not a stop")
    if tuple(packet["VALIDATION_STAGES"]) != STAGES:
        raise ValidationError(
            "the validation stages are not the ten, in order, with provider completion third and "
            "the schema before the semantic gate"
        )


def _check_calls_and_timeout(packet: dict[str, Any]) -> None:
    params = packet["GENERATION_PARAMETERS"]
    supplied = {k: v for k, v in params.items() if k != "$comment" and not k.endswith("note")}
    for key, value in supplied.items():
        if value is None:
            if key in LLM_REQUEST_FIELDS:
                raise ValidationError(f"{key!r} is carried by the Gateway and frozen as absent")
            continue
        if key not in LLM_REQUEST_FIELDS:
            raise ValidationError(f"{key!r} is frozen with a value nothing reads")
    if supplied.get("max_retries") != 0 or packet["MAX_RETRIES"] != 0:
        raise ValidationError("a retry is a second call, and V3 authorises one")
    if packet["MAX_MODEL_CALLS"] != 1:
        raise ValidationError(f"MAX_MODEL_CALLS is {packet['MAX_MODEL_CALLS']}")
    for key in CALL_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if supplied.get("response_schema") != packet["OUTPUT_SCHEMA_VERSION"]:
        raise ValidationError("the request would carry another output schema")
    if not supplied.get("requires_structured_output"):
        raise ValidationError("a schema-bound task that does not require structured output")
    if supplied.get("timeout_seconds") != packet["REQUEST_TIMEOUT"]:
        raise ValidationError("the packet's timeout and its frozen parameter disagree")

    block = packet["TIMEOUT"]
    if packet["REQUEST_TIMEOUT"] != _load(PACKET_V2)["REQUEST_TIMEOUT"]:
        raise ValidationError(
            "the timeout moved from V2. One completed call is not a basis for a timeout policy"
        )
    elapsed = _load(RECORD_V2)["timing"]["elapsed_seconds"]
    _fixed(
        block,
        {
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "TIMEOUT_CHANGED_BY_THIS_MISSION": False,
            "V2_OBSERVED_ELAPSED_SECONDS": elapsed,
            "V2_OBSERVATION_USED_TO_CHANGE_THE_TIMEOUT": False,
            "STREAMING": False,
            "GENERATION_RATE_DOCUMENTED": False,
            "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
            "TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS": True,
            "ON_TIMEOUT": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
        },
        "TIMEOUT",
    )


def _check_cost(packet: dict[str, Any]) -> None:
    v2 = _load(PACKET_V2)
    record_v2 = _load(RECORD_V2)
    if packet["PRICING_VERSION"] != v2["PRICING_VERSION"]:
        raise ValidationError(
            "MODEL_COST_BASIS_REQUIRES_REFRESH: a pricing version this repository does not hold"
        )
    documented = _load(CAPABILITY)["MODELS"][MODEL]["DOCUMENTED_PRICE_USD_PER_MTOK"]
    price = packet["PRICE_PER_1K"]
    if not (
        math.isclose(float(price["input"]) * 1000, float(documented["input"]))
        and math.isclose(float(price["output"]) * 1000, float(documented["output"]))
    ):
        raise ValidationError("the held price disagrees with the documented price")
    held = ModelPrice(input_per_1k=float(price["input"]), output_per_1k=float(price["output"]))

    basis = packet["TOKEN_ESTIMATION_BASIS"]
    v2_wire = int(v2["TOKEN_ESTIMATION_BASIS"]["wire_characters"])
    delta = system_region_delta()
    _fixed(
        basis,
        {
            "exact_tokenizer_available": False,
            "no_test_request_was_sent": True,
            "chars_per_token": CHARS_PER_TOKEN,
            "conservative_multiplier": CONSERVATIVE_MULTIPLIER,
            "v2_wire_characters": v2_wire,
            "system_region_delta_characters": delta,
        },
        "TOKEN_ESTIMATION_BASIS",
    )
    wire = int(basis["wire_characters"])
    if wire != v2_wire + delta:
        raise ValidationError(
            f"the V3 body is {wire} characters, and V2's {v2_wire} plus the {delta} the system "
            f"region grew by gives {v2_wire + delta}: something other than the prompt moved"
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
    inputs = int(packet["INPUT_TOKEN_ESTIMATE"])
    if packet["TOTAL_TOKEN_CEILING"] != inputs + output:
        raise ValidationError("the total token ceiling is not the sum of its parts")
    if packet["INPUT_WORST_CASE_COST"] != held.cost_for(inputs, 0):
        raise ValidationError("the input worst case is not recomputable")
    if packet["OUTPUT_WORST_CASE_COST"] != held.cost_for(0, output):
        raise ValidationError("the output worst case is not recomputable")
    total = held.cost_for(inputs, output)
    if packet["WORST_CASE_CALL_COST"] != total:
        raise ValidationError("the worst-case call cost is not recomputable")
    if packet["EXECUTION_COST_CEILING"] != total or packet["HEADROOM_POLICY"] != "NONE_HELD":
        raise ValidationError(
            "a ceiling other than the worst case itself, and no general headroom policy exists "
            "to justify one"
        )
    if packet["COST_NOT_EXPECTED_ACTUAL"] is not True:
        raise ValidationError("the worst case is presented as an expected cost")
    previous = float(v2["EXECUTION_COST_CEILING"])
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
    usage = record_v2["ACTUAL_USAGE"]
    _fixed(
        packet["V2_OBSERVATION"],
        {
            "V2_INPUT_TOKEN_ESTIMATE": v2["INPUT_TOKEN_ESTIMATE"],
            "V2_ACTUAL_INPUT_TOKENS": usage["input_tokens"],
            "V2_ESTIMATE_COVERED_THE_ACTUAL": v2["INPUT_TOKEN_ESTIMATE"] >= usage["input_tokens"],
            "V2_ACTUAL_OUTPUT_TOKENS": usage["output_tokens"],
            "USED_TO_CHANGE_THE_ESTIMATION_METHOD": False,
            "USED_TO_REDUCE_MAX_OUTPUT_TOKENS": False,
        },
        "V2_OBSERVATION",
    )


def _check_boundaries(packet: dict[str, Any]) -> None:
    for key in CAPABILITY_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if packet["RETENTION_ON_EXECUTION"] != _load(PACKET_V2)["RETENTION_ON_EXECUTION"]:
        raise ValidationError("the retention policy moved from V2's repaired one")
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
                raise ValidationError(f"{path} names {test!r}, which no V3 runner test defines")

    policy = packet["PERSISTENCE_POLICY"]
    _fixed(
        policy,
        {
            "persist_if_gate_accepts": False,
            "human_review_required_before_persistence": True,
            "canonical_persistence": (
                "ONLY_AFTER_DETERMINISTIC_ACCEPTANCE_AND_SEPARATE_HUMAN_APPROVAL"
            ),
            "opportunity_created_by_this_packet": 0,
            "score_persisted": False,
            "independence_group_created": False,
        },
        "PERSISTENCE_POLICY",
    )
    if not policy["provenance_the_first_revision_must_carry"]:
        raise ValidationError("a persistence policy naming no provenance")


def _check_accounting(packet: dict[str, Any]) -> None:
    accounting = packet["preparation_accounting"]
    for key in PREPARATION_ZERO:
        if accounting.get(key) != 0:
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V3 does 0")
    if packet["CANONICAL_COUNTERS"] != CANONICAL_COUNTERS:
        raise ValidationError("a canonical counter moved")


_LOOPS = (
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


def _check_single_call_site(source: str) -> None:
    """One model call site, reached once: in no loop, in a function called once and never re-entered."""
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def enclosing(node: ast.AST) -> Iterator[ast.AST]:
        while node in parents:
            node = parents[node]
            yield node

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "complete"
    ]
    if len(calls) != 1:
        raise ValidationError(
            f"the V3 runner has {len(calls)} model call sites, and V3 authorises one call"
        )
    holder: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in enclosing(calls[0]):
        if isinstance(node, _LOOPS):
            raise ValidationError(
                "the V3 runner's one call site sits inside a loop, which is a retry by another name"
            )
        if holder is None and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            holder = node
    if holder is None:
        raise ValidationError("the V3 runner's call site is not inside a function")
    callers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == holder.name
    ]
    if len(callers) > 1:
        raise ValidationError(f"{holder.name}() is called {len(callers)} times, and V3 is one call")
    for caller in callers:
        chain = list(enclosing(caller))
        if holder in chain:
            raise ValidationError(f"{holder.name}() calls itself, which is a retry by another name")
        if any(isinstance(node, _LOOPS) for node in chain):
            raise ValidationError(
                f"{holder.name}() is called from inside a loop, which is a retry by another name"
            )


#: What the stage function may call on the parsed answer: reads, and nothing that changes it.
_READ_ONLY_METHODS = frozenset({"get", "items", "keys", "values"})


def _rooted_at_output(node: ast.AST) -> bool:
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return isinstance(node, ast.Name) and node.id == "output"


def _check_no_post_processing(source: str) -> None:
    """The answer is judged as it arrived: nothing slices a value, nothing reassigns or edits it.

    Section 15 is recorded in the packet as six prohibitions, and a record is a promise. This reads
    the runner: no slice anywhere in it, because a slice is how a string gets trimmed to a bound;
    the parsed answer bound exactly once in the stage function; nothing written into it or deleted
    from it; and no method called on it or on any part of it except a read. The behavioural half is
    in the runner's own tests: a 901-character summary is refused, which no trimming could allow.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Slice):
            raise ValidationError(
                f"the V3 runner slices a value on line {node.lineno}. An answer over a bound is "
                "refused, never trimmed to fit"
            )
    judge = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "validate_execution"
        ),
        None,
    )
    if judge is None:
        raise ValidationError("the V3 runner has no stage function to read")
    bindings = 0
    for node in ast.walk(judge):
        if isinstance(node, ast.Delete) and any(_rooted_at_output(t) for t in node.targets):
            raise ValidationError(
                f"the V3 runner deletes from the parsed answer on line {node.lineno}. A dropped "
                "item or field is post-processing, and the answer is judged as it arrived"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and _rooted_at_output(node.func.value)
            and node.func.attr not in _READ_ONLY_METHODS
        ):
            raise ValidationError(
                f"the V3 runner calls {node.func.attr} on the parsed answer on line "
                f"{node.lineno}. Only reads are allowed before the answer is judged"
            )
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        for target in targets:
            names = target.elts if isinstance(target, ast.Tuple) else [target]
            for name in names:
                if isinstance(name, ast.Name) and name.id == "output":
                    bindings += 1
                elif _rooted_at_output(name):
                    raise ValidationError(
                        "the V3 runner writes into the parsed answer before judging it. The "
                        "answer is judged exactly as it arrived"
                    )
    if bindings != 1:
        raise ValidationError(
            f"the V3 runner binds the parsed answer {bindings} times. A second binding is where "
            "a rewritten, summarised or truncated answer would replace the one that arrived"
        )


def _check_runner(packet: dict[str, Any]) -> None:
    _check_single_call_site(RUNNER.read_text(encoding="utf-8"))
    _check_no_post_processing(RUNNER.read_text(encoding="utf-8"))
    runner = _module("execution_runner_v3_for_gate", RUNNER)
    if runner.EXPECTED["EXECUTION_PACKET_SHA256"] != packet["EXECUTION_PACKET_SHA256"]:
        raise ValidationError("the runner was prepared for another digest")
    for key, value in runner.EXPECTED.items():
        if key in packet and packet[key] != value:
            raise ValidationError(
                f"the runner expects {key}={value!r} and V3 binds {packet[key]!r}"
            )
    if tuple(runner.STAGES) != STAGES:
        raise ValidationError("the runner's stages are not the gate's")
    if runner.APPROVAL_FILE.name != APPROVAL.name:
        raise ValidationError("the runner reads its approval from somewhere else")
    if runner.PROMPT_DOCUMENT.name != PROMPT_V3.name:
        raise ValidationError("the runner checks its prompt against another document")
    for label, digest in (("V1", V1_SHA256), ("V2", V2_SHA256)):
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
        raise ValidationError(
            "the runner refuses an unseen digest, so a genuinely new packet would be blocked "
            "merely because V1 and V2 are spent"
        ) from exc
    if runner.unstated_constraints(SECOND_OPPORTUNITY_SYSTEM_V1_2):
        raise ValidationError("the runner finds the v1.2.0 prompt leaving a bound unstated")
    if not runner.unstated_constraints(SECOND_OPPORTUNITY_SYSTEM_V1_1):
        raise ValidationError(
            "the runner's drift check would pass V2's prompt, so it checks nothing"
        )


def validate() -> dict[str, Any]:
    packet = _load(PACKET)
    _check_identity_and_approval(packet)
    _check_predecessors(packet)
    _check_alignment_and_prompt(packet)
    _check_contract(packet)
    _check_representation(packet)
    _check_route(packet)
    _check_thinking_and_envelope(packet)
    _check_completion_policy(packet)
    _check_calls_and_timeout(packet)
    _check_cost(packet)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet)
    return packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v3.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _sentence(text: object) -> str:
    value = str(text).strip()
    return value if value.endswith((".", "!", "?")) else value + "."


def _cost(value: object) -> str:
    """Six places, exact at these prices: a whole token costs a multiple of 0.000001."""
    return f"{float(str(value)):.6f}".rstrip("0").rstrip(".")


def render_packet(packet: dict[str, Any]) -> str:
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    timeout = packet["TIMEOUT"]
    policy = packet["PROVIDER_COMPLETION_POLICY"]
    observed = packet["V2_OBSERVATION"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v3",
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
                f"{packet['PREDECESSOR_EXECUTION_PACKET_SHA256'][:12]}..., "
                f"{packet['PREDECESSOR_EXECUTION_OUTCOME']}, consumed",
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
                f"gate                                {packet['OUTPUT_GATE_VERSION']}",
                f"prompt                              {packet['PROMPT_ID']}@{packet['PROMPT_VERSION']}",
                f"prompt sha256                       {packet['PROMPT_SHA256']}",
                f"representation sha256               {packet['REPRESENTATION_SHA256']}",
                "",
                f"MAX_OUTPUT_TOKENS                   {packet['MAX_OUTPUT_TOKENS']} "
                f"({packet['MAX_OUTPUT_TOKENS_BASIS']})",
                f"MAX_MODEL_CALLS                     {packet['MAX_MODEL_CALLS']}",
                f"MAX_RETRIES                         {packet['MAX_RETRIES']}",
                f"timeout                             {packet['REQUEST_TIMEOUT']} s",
                "",
                f"WORST_CASE_CALL_COST                {_cost(packet['WORST_CASE_CALL_COST'])}",
                f"EXECUTION_COST_CEILING              {_cost(packet['EXECUTION_COST_CEILING'])}",
                "",
                "contract_full_domain_reachable      "
                f"{str(packet['CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL']).lower()}",
                "provider_limit_fail_closed          "
                f"{str(policy['PROVIDER_LIMIT_FAIL_CLOSED']).lower()}",
                "retention_repair_verified           "
                f"{str(packet['RETENTION_REPAIR_VERIFIED']).lower()}",
                "human_review_required               "
                f"{str(packet['PERSISTENCE_POLICY']['human_review_required_before_persistence']).lower()}",
                f"canonical_persistence               {packet['PERSISTENCE_POLICY']['canonical_persistence']}",
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{str(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']).lower()}",
            ]
        ),
        "## The one change: the prompt",
        "",
        f"Prompt v{packet['PROMPT_VERSION']}, rendered by `{packet['OUTPUT_CONSTRAINT_RENDERER']}` "
        "from the unchanged schema, under the operator's decision "
        + ", ".join(f"`{d}`" for d in packet["PROMPT_ALIGNMENT_DECISION"])
        + f". {_sentence(packet['prompt_note'])}",
        "",
        "Schema changed `false`, gate changed `false`. No answer is changed to fit a bound: "
        + ", ".join(f"`{k}`" for k in packet["OUTPUT_POST_PROCESSING"])
        + " are all `false`.",
        "",
        "## Everything else is V2's",
        "",
        f"Signal: `{policy['signal_field']}`. Complete: "
        f"{', '.join(f'`{v}`' for v in policy['complete_values'])}. Output limit: "
        f"{', '.join(f'`{v}`' for v in policy['output_limit_values'])} → "
        f"`{policy['on_output_limit']}`. Refusal: "
        f"{', '.join(f'`{v}`' for v in policy['refusal_values'])} → `{policy['on_refusal']}`. "
        f"Anything else → `{policy['on_any_other_value']}`. Read before any parse.",
        "",
        "Validation stages, in order: "
        + ", ".join(f"`{s}`" for s in packet["VALIDATION_STAGES"])
        + ".",
        "",
        f"`max_tokens = {packet['MAX_OUTPUT_TOKENS']}`, not based on "
        f"{', '.join(f'`{b}`' for b in packet['MAX_OUTPUT_TOKENS_NOT_BASED_ON'])}.",
        "",
        f"Timeout {timeout['REQUEST_TIMEOUT_SECONDS']} s, changed `false`. V2 finished in "
        f"{timeout['V2_OBSERVED_ELAPSED_SECONDS']} s and that one observation changed nothing. "
        f"{_sentence(timeout['note'])}",
        "",
        "## Cost, recomputed from the new request body",
        "",
        *_code(
            [
                f"request body             {basis['wire_characters']} characters  "
                f"(V2 {basis['v2_wire_characters']} + system region "
                f"{basis['system_region_delta_characters']})",
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
                f"previous ceiling (V2)    {_cost(packet['PREVIOUS_EXECUTION_COST_CEILING'])}  "
                f"(+{_cost(packet['CEILING_DELTA_OVER_PREVIOUS'])}, "
                f"x{packet['CEILING_OVER_PREVIOUS_CEILING']})",
            ]
        ),
        f"V2 estimated {observed['V2_INPUT_TOKEN_ESTIMATE']} input tokens and used "
        f"{observed['V2_ACTUAL_INPUT_TOKENS']}; it used {observed['V2_ACTUAL_OUTPUT_TOKENS']} output "
        f"tokens. {_sentence(observed['note'])}",
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
        PACKET_MD.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {PACKET_MD.name}")
    if PACKET_MD.read_text(encoding="utf-8") != text:
        print(f"FAIL     {PACKET_MD.name} is not the rendering of its record")
        return 1
    print("ok       packet V3 is V2's call with the aligned prompt, and matches the live code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
