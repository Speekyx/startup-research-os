"""Mission 1.84.6, CI gate 70. The execution-envelope decision and execution packet V2.

Two records, checked against each other, against the frozen records they rest on, and against live
code:

* the operator's execution-envelope DECISION: the bounded acceptance contract may be larger than
  what the selected route can emit in one synchronous run, and that is a first-class state rather
  than an error;
* execution PACKET V2: the exact call that decision makes preparable, frozen and unapproved.

**What is re-derived rather than read.** The packet digest, from its bound fields. The output
schema's digest and version, from the live contract. The request body, from the live adapter built
with the packet's own adapter parameters, so a packet saying DISABLED over an adapter that no longer
sends the documented object fails. The completion policy, from the adapter's own constants and its
classifier. Every cost figure, from the held price. The input estimate, from the recorded body
length and the held ratio.

**What CI cannot re-derive, and checks for agreement instead.** The TED representation and the
rendered prompt digest are rebuilt from the research database by the runner's verification, which
CI has no data for. The packet records what that verification found on the preparing machine, and
those values must equal the approved digests the frozen records already carry.
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
from sros_opportunity.second_opportunity import (
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_ID,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

DECISION = DATA / "second-opportunity-execution-envelope-decision-v1.json"
DECISION_MD = DATA / "second-opportunity-execution-envelope-decision-v1.md"
PACKET = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v2.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v2.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v2.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v2.py"
)

PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
EXECUTION_RECORD_V1 = DATA / "second-opportunity-synthesis-execution-record-v1.json"
CAPACITY_V2 = DATA / "second-opportunity-output-capacity-analysis-v2.json"
PROMPT_V2 = DATA / "second-opportunity-synthesis-prompt-v2.json"
MEASUREMENT = DATA / "second-opportunity-provider-token-measurement-v1.json"
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
PROVIDER_REGISTER = DATA / "model-provider-policy-v1.json"
PREPARATION_V5 = DATA / "opportunity-preparation-v5.json"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V2"
PACKET_VERSION = 2
PREPARED_BY = "mission-1.84.6"
THIS_MISSION = (1, 84, 6)
V1_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V1"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
SUBJECT = "ted-eu:CPV-class:9261"
MODEL = "claude-sonnet-5"
REPRESENTATION_CHARACTERS = 3604

DECISION_VALUE = "RUN_AT_THE_PROVIDER_MAXIMUM_ACCEPTING_AN_UNREACHABLE_WORST_CASE"
REJECTED_ALTERNATIVES = (
    "BOUND_THE_NARRATIVE_FIELDS_FURTHER",
    "RESTRICT_THE_NARRATIVE_CHARACTER_CLASS",
    "CHANGE_THE_ROUTE_TO_THE_BATCHES_300K_BETA",
    "SPLIT_THE_SYNTHESIS_ACROSS_CALLS",
)
ROUTES_NOT_USED = ["MESSAGE_BATCHES_BETA", "anthropic-claude-subscription"]
#: The route as reviewed, pinned whole. The first probe run found that a test for the word
#: "synchronous" is passed by "asynchronous", so a sentence naming the batch beta as the route got
#: through; a pinned sentence cannot be reworded into another route.
PROVIDER_ROUTE_TEXT = (
    "The Anthropic API, synchronous Messages endpoint, accessed with an API key under the "
    "Commercial Terms of Service. Not the Message Batches beta, and not a consumer subscription."
)
DOCUMENTED_SYNCHRONOUS_MAXIMUM = 128000
MAX_OUTPUT_TOKENS_BASIS = "OPERATOR_SELECTED_DOCUMENTED_PROVIDER_MAXIMUM"
OUTPUT_TOKEN_CEILING_BASIS = "OPERATOR_SELECTED_PROVIDER_MAXIMUM"  # noqa: S105 -- an output-token basis, not a credential
NOT_BASED_ON = (
    "SCHEMA_DERIVED_MAXIMUM",
    "PROVIDER_NATIVE_TOKEN_ESTIMATE",
    "EMPIRICAL_CHARS_PER_TOKEN",
)
CHARS_PER_TOKEN = 2.1565
CONSERVATIVE_MULTIPLIER = 1.25

#: The ten ordered stages. The runner carries the same tuple and the gate compares them.
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

OUTCOMES = (
    "SECOND_OPPORTUNITY_EXECUTION_PACKET_V2_READY_FOR_OPERATOR_APPROVAL",
    "MODEL_COST_BASIS_REQUIRES_REFRESH",
    "THINKING_CONTROL_NO_LONGER_VALID",
    "PROVIDER_LIMIT_SIGNAL_NOT_FAIL_CLOSED",
    "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED",
    "SECOND_OPPORTUNITY_PROMPT_CHANGED_REQUIRES_REVIEW",
    "PROVIDER_ROUTE_NO_LONGER_APPROVED",
    "TED_EGRESS_NO_LONGER_AVAILABLE",
    "RETENTION_PATH_NOT_READY_FOR_SECOND_EXECUTION",
)
READY = OUTCOMES[0]

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
RETENTION_PATHS = (
    "raw_response_on_success",
    "raw_response_on_schema_failure",
    "raw_response_on_provider_limit",
    "usage_retained",
    "request_id_retained",
    "digests_retained",
    "terminal_outcome_retained",
    "hidden_reasoning_not_retained",
    "secrets_redacted",
    "no_network",
)

#: Mission 1.84.5's thirteen counters. Nothing in Mission 1.84.6 writes to the database.
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

#: Values the adapter must NOT read as a completion. Anything unforeseen fails closed.
COMPLETION_PROBES: tuple[object, ...] = ("end_turn", "pause_turn", "stop_sequence", "", None)

LLM_REQUEST_FIELDS = frozenset(f.name for f in dataclasses.fields(LlmRequest))
ADAPTER_FIELDS = frozenset(f.name for f in dataclasses.fields(AnthropicProvider))

#: The fields the V2 digest binds. Kept here rather than read from the record, because a digest over
#: whichever fields the record nominates is a digest the record can shrink.
DIGEST_FIELDS = (
    "EXECUTION_PACKET_ID",
    "EXECUTION_PACKET_VERSION",
    "PREDECESSOR_EXECUTION_PACKET_ID",
    "PREDECESSOR_EXECUTION_PACKET_SHA256",
    "PREDECESSOR_EXECUTION_OUTCOME",
    "PREDECESSOR_APPROVAL_CONSUMED",
    "EXECUTION_ENVELOPE_DECISION",
    "EXECUTION_ENVELOPE_DECISION_SHA256",
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
    "OUTPUT_SCHEMA_VERSION",
    "OUTPUT_SCHEMA_SHA256",
    "OUTPUT_GATE_VERSION",
    "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL",
    "CONTRACT_THEORETICAL_MAX_EXCEEDS_EXECUTION_ENVELOPE",
    "PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE",
    "ESTIMATE_EXACT",
    "GENERATION_PARAMETERS",
    "MAX_OUTPUT_TOKENS",
    "OUTPUT_TOKEN_CEILING",
    "MAX_OUTPUT_TOKENS_BASIS",
    "OUTPUT_TOKEN_CEILING_BASIS",
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
    """The records disagree with each other, with the frozen records, or with live code."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    """Recompute the V2 execution digest from the packet's own bound fields."""
    bound: dict[str, object] = {}
    for key in DIGEST_FIELDS:
        if key not in packet:
            raise ValidationError(f"the execution packet has no {key!r} to bind")
        bound[key] = _bindable(packet[key])
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return _sha256(payload)


def statement_digest(decision: dict[str, Any]) -> str:
    return _sha256("\n".join(str(line) for line in decision["OPERATOR_STATEMENT"]))


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


# --------------------------------------------------------------------------- the decision


def _check_decision(decision: dict[str, Any]) -> None:
    _fixed(
        decision,
        {
            "DECISION": DECISION_VALUE,
            "DECISION_OWNER": "OPERATOR",
            "DECISION_KIND": "ARCHITECTURE",
            "MATHEMATICALLY_DERIVED": False,
            "DECISION_REQUEST": (
                "OPERATOR_DECISION_ON_A_BOUNDED_CONTRACT_LARGER_THAN_THE_MODEL_CAN_EMIT"
            ),
            "DECISION_REQUESTED_BY": "mission-1.84.5",
            "OUTPUT_CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL": False,
            "NOT_A_SCHEMA_DEFECT": True,
            "EXECUTION_ENVELOPE_IS_A_STRICT_SUBSET_OF_THE_CONTRACT": True,
            "MAX_OUTPUT_TOKENS_SELECTED": DOCUMENTED_SYNCHRONOUS_MAXIMUM,
            "MAX_OUTPUT_TOKENS_BASIS": MAX_OUTPUT_TOKENS_BASIS,
            "OUTPUT_TOKEN_CEILING_BASIS": OUTPUT_TOKEN_CEILING_BASIS,
            "THINKING": "DISABLED",
            "SELECTED_ROUTE": "SYNCHRONOUS_MESSAGES_API",
            "ROUTES_NOT_USED": ROUTES_NOT_USED,
            "FAIL_CLOSED_ON_PROVIDER_LIMIT": True,
            "RETRY_AUTHORISED": False,
            "CONTINUATION_AUTHORISED": False,
            "REPAIR_MODEL_AUTHORISED": False,
            "SCHEMA_CHANGED": False,
            "SCHEMA_V1_2_0_CREATED": False,
            "PROMPT_CHANGED": False,
            "NATIVE_STRUCTURED_OUTPUT_MIGRATION": False,
            "AUTHORISES_A_REQUEST": False,
            "recorded_by": PREPARED_BY,
        },
        "decision",
    )
    if tuple(decision["REJECTED_ALTERNATIVES"]) != REJECTED_ALTERNATIVES:
        raise ValidationError(
            f"the rejected alternatives are {decision['REJECTED_ALTERNATIVES']}; the operator "
            f"rejected exactly {list(REJECTED_ALTERNATIVES)}"
        )
    if tuple(decision["MAX_OUTPUT_TOKENS_NOT_BASED_ON"]) != NOT_BASED_ON:
        raise ValidationError("the ceiling's basis no longer excludes what it must exclude")
    for key in ("reason", "accepted_consequence", "safety_consequence"):
        if not str(decision.get(key) or "").strip():
            raise ValidationError(f"the decision states no {key}")
    if "rejected" not in decision["safety_consequence"]:
        raise ValidationError("the safety consequence does not say a limit stop is rejected")

    statement = decision["OPERATOR_STATEMENT"]
    if not statement or not all(isinstance(line, str) and line.strip() for line in statement):
        raise ValidationError("the operator's statement is empty or has an empty line")
    if DECISION_VALUE not in statement or "No retry is authorised." not in statement:
        raise ValidationError("the recorded statement is not the operator's decision")
    if decision["OPERATOR_STATEMENT_SHA256"] != statement_digest(decision):
        raise ValidationError("the operator's words changed after their digest was recorded")

    envelope = decision["ENVELOPE_MODEL"]
    _fixed(
        envelope,
        {
            "CONTRACT_MAXIMUM": "FINITE_BUT_LARGER_THAN_THE_EXECUTION_ENVELOPE",
            "CONTRACT_MAXIMUM_TOKEN_ESTIMATE_EXACT": False,
            "EXECUTION_ROUTE": "SYNCHRONOUS_MESSAGES_API",
            "EXECUTION_MAXIMUM_OUTPUT_TOKENS": DOCUMENTED_SYNCHRONOUS_MAXIMUM,
            "CONTRACT_FULL_DOMAIN_REACHABLE": False,
            "STATE": "CONTRACT_LARGER_THAN_EXECUTION_ENVELOPE",
        },
        "decision.ENVELOPE_MODEL",
    )
    if set(envelope["STATE_IS_NOT"]) != {"ERROR", "UNKNOWN", "SCHEMA_INVALID"}:
        raise ValidationError("the envelope state is not kept apart from an error")
    questions = (envelope["CONTRACT_QUESTION"], envelope["ENVELOPE_QUESTION"])
    if not all(str(q).strip() for q in questions) or questions[0] == questions[1]:
        raise ValidationError("the contract and the envelope must answer two different questions")

    measurement = _load(MEASUREMENT)
    capacity = _load(CAPACITY_V2)
    estimate = measurement["MEASUREMENT"]["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"]
    rests = decision["RESTS_ON"]
    if envelope["CONTRACT_MAXIMUM_TOKEN_ESTIMATE"] != estimate:
        raise ValidationError("the envelope's estimate is not Mission 1.84.5's")
    if rests["mission_1_84_5"]["MAX_INSTANCE_TOKEN_ESTIMATE"] != estimate:
        raise ValidationError("the decision cites an estimate Mission 1.84.5 did not record")
    if not estimate > envelope["EXECUTION_MAXIMUM_OUTPUT_TOKENS"]:
        raise ValidationError(
            "the decision describes a contract larger than the envelope, and the estimate does "
            "not exceed the envelope"
        )
    if measurement["MEASUREMENT"]["ESTIMATE_NOT_EXACT"] is not True:
        raise ValidationError("Mission 1.84.5's estimate is no longer recorded as an estimate")
    maximum = capacity["MAXIMUM_VALID_INSTANCE"]["MAX_VALID_OUTPUT_CHARACTERS"]
    if envelope["CONTRACT_MAXIMUM_CHARACTERS"] != maximum:
        raise ValidationError("the envelope's character maximum is not Mission 1.84.4's")
    if capacity["FINITE_BOUND"] is not True or capacity["unbounded_path_count"] != 0:
        raise ValidationError("the contract is no longer finite")
    if set(decision["WHAT_THE_ESTIMATE_IS_NOT"]) != {
        "an exact count",
        "an output token count",
        "a required execution limit",
    }:
        raise ValidationError("the estimate is read as more than it is")


# --------------------------------------------------------------------------- the packet


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
            "EXECUTION_ENVELOPE_DECISION": DECISION_VALUE,
        },
        "packet",
    )
    recomputed = packet_digest(packet)
    if packet["EXECUTION_PACKET_SHA256"] != recomputed:
        raise ValidationError(
            f"the packet records {packet['EXECUTION_PACKET_SHA256']} and its bound fields hash "
            f"to {recomputed}"
        )
    if recomputed == V1_SHA256:
        raise ValidationError("V2 carries V1's digest")
    note = str(packet["approval_note"])
    if "egress" not in note.lower() or "V1" not in note or "beside" not in note:
        raise ValidationError(
            "the approval note does not keep this approval apart from V1's and from TED egress"
        )
    decision_bytes = hashlib.sha256(DECISION.read_bytes()).hexdigest()
    if packet["EXECUTION_ENVELOPE_DECISION_SHA256"] != decision_bytes:
        raise ValidationError("the decision record changed after the packet bound it")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = _mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V2 recorded by the mission that prepared it. Preparing a packet "
                "authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V2's")
    return recomputed


def _check_v1(packet: dict[str, Any]) -> None:
    v1 = _load(PACKET_V1)
    if v1["EXECUTION_PACKET_SHA256"] != V1_SHA256:
        raise ValidationError("the V1 packet digest moved")
    if v1["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
        raise ValidationError("the frozen V1 packet was edited to record an approval")
    record = _load(EXECUTION_RECORD_V1)
    if record["EXECUTION_APPROVAL_CONSUMED"] is not True:
        raise ValidationError("V1's consumption was reset")
    if record["FURTHER_CALLS_AUTHORIZED_BY_V1"] is not False:
        raise ValidationError("V1 now authorises further calls")
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V1_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V1_SHA256,
            "PREDECESSOR_EXECUTION_OUTCOME": record["PRIMARY_OUTCOME"],
            "PREDECESSOR_APPROVAL_CONSUMED": True,
        },
        "packet",
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
            "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL": False,
            "ESTIMATE_EXACT": False,
            "LOCAL_SCHEMA_VALIDATOR_MANDATORY": True,
        },
        "packet",
    )
    if _load(CAPACITY_V2)["schema_sha256"] != live:
        raise ValidationError("the schema moved after Mission 1.84.4 measured its maximum")
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


def _check_prompt_and_representation(packet: dict[str, Any]) -> None:
    prompt = _load(PROMPT_V2)
    if packet["PROMPT_ID"] != SECOND_OPPORTUNITY_PROMPT_ID:
        raise ValidationError("the prompt id is not the procedure's")
    if packet["PROMPT_VERSION"] != SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1:
        raise ValidationError("SECOND_OPPORTUNITY_PROMPT_CHANGED_REQUIRES_REVIEW: prompt version")
    if packet["PROMPT_SHA256"] != prompt["PROMPT_SHA256"] or packet["PROMPT_UNCHANGED"] is not True:
        raise ValidationError(
            "SECOND_OPPORTUNITY_PROMPT_CHANGED_REQUIRES_REVIEW: the packet's prompt digest is not "
            "the v1.1.0 digest Mission 1.84.4 recorded"
        )
    v1 = _load(PACKET_V1)
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
        if packet[key] != v1[key]:
            raise ValidationError(f"{key} is not what the approved egress rests on")
    if packet["REPRESENTATION_SHA256"] != v1["REPRESENTATION_SHA256"]:
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
            "pricing_version": packet["PRICING_VERSION"],
            "worst_case_from_the_configured_table": packet["WORST_CASE_CALL_COST"],
            "v1_guard_refuses_v1": True,
            "v1_guard_permits_an_unseen_digest": True,
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
        raise ValidationError("the ceiling's basis no longer excludes what it must exclude")

    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if capability["DOCUMENTED_MAX_OUTPUT_TOKENS"] != DOCUMENTED_SYNCHRONOUS_MAXIMUM:
        raise ValidationError("MODEL_CAPABILITY_REQUIRES_REFRESH: the held maximum moved")
    if packet["MAX_OUTPUT_TOKENS"] != capability["DOCUMENTED_MAX_OUTPUT_TOKENS"]:
        raise ValidationError(
            f"max_tokens is {packet['MAX_OUTPUT_TOKENS']}; the operator selected the documented "
            f"synchronous maximum, {capability['DOCUMENTED_MAX_OUTPUT_TOKENS']}"
        )
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
        raise ValidationError(f"adapter parameters {sorted(params)}; V2 binds exactly two")
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
        raise ValidationError("a structured-output migration rode along with the envelope")
    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if capability["THINKING_DISABLE_SUPPORTED"] is not True:
        raise ValidationError("THINKING_CONTROL_NO_LONGER_VALID: disabling is not documented")
    if capability["FORCED_TOOL_USE"]["WITH_THINKING_DISABLED"] != "NOT_RESTRICTED_BY_DOCUMENTATION":
        raise ValidationError("forced tool use with thinking disabled is restricted")


def _check_completion_policy(packet: dict[str, Any]) -> None:
    policy = packet["PROVIDER_COMPLETION_POLICY"]
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
            raise ValidationError(
                f"PROVIDER_LIMIT_SIGNAL_NOT_FAIL_CLOSED: the adapter does not read {value!r} as "
                "the output limit"
            )
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
            "the validation stages are not the ten, in order, with provider completion third"
        )

    evidence = {e["id"]: e for e in _load(MEASUREMENT)["DOCUMENTATION_EVIDENCE"]}
    named: set[str] = set()
    for fragment in policy["documentation"]:
        entry = evidence.get(fragment.get("evidence"))
        if entry is None or entry["used"] is not True:
            raise ValidationError(
                f"a fragment cites {fragment.get('evidence')!r}, not held evidence"
            )
        if not isinstance(fragment.get("line"), int) or fragment["line"] <= 0:
            raise ValidationError("a completion fragment has no line")
        verbatim = str(fragment.get("verbatim") or "")
        if not 0 < len(verbatim.split()) <= 25:
            raise ValidationError("a completion fragment quotes nothing, or more than a fragment")
        documented = (
            FORCED_TOOL_COMPLETE_STOP_REASON,
            REFUSAL_STOP_REASON,
            *OUTPUT_LIMIT_STOP_REASONS,
        )
        named.update(value for value in documented if f'"{value}"' in verbatim)
    missing = {FORCED_TOOL_COMPLETE_STOP_REASON, REFUSAL_STOP_REASON, *OUTPUT_LIMIT_STOP_REASONS}
    missing -= named
    if missing:
        raise ValidationError(f"no documentation fragment names {sorted(missing)}")


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
        raise ValidationError("a retry is a second call, and V2 authorises one")
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
    v1_timeout = _load(PACKET_V1)["REQUEST_TIMEOUT"]
    if packet["REQUEST_TIMEOUT"] != v1_timeout:
        if (
            block["TIMEOUT_CHANGED_BY_THIS_MISSION"] is not True
            or not str(block.get("change_review") or "").strip()
        ):
            raise ValidationError("a timeout moved from the reviewed bound with no review")
    elif block["TIMEOUT_CHANGED_BY_THIS_MISSION"] is not False:
        raise ValidationError("the timeout is recorded as changed and it is not")
    _fixed(
        block,
        {
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "STREAMING": False,
            "GENERATION_RATE_DOCUMENTED": False,
            "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
            "TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS": True,
            "ON_TIMEOUT": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
        },
        "TIMEOUT",
    )


def _check_cost(packet: dict[str, Any]) -> None:
    v1 = _load(PACKET_V1)
    if packet["PRICING_VERSION"] != v1["PRICING_VERSION"]:
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
    _fixed(
        basis,
        {
            "exact_tokenizer_available": False,
            "no_test_request_was_sent": True,
            "chars_per_token": CHARS_PER_TOKEN,
            "conservative_multiplier": CONSERVATIVE_MULTIPLIER,
            "v1_definition_recovered": False,
            "v1_recorded_wire_characters": v1["TOKEN_ESTIMATION_BASIS"]["wire_characters"],
        },
        "TOKEN_ESTIMATION_BASIS",
    )
    wire = int(basis["wire_characters"])
    expected = math.ceil(wire / CHARS_PER_TOKEN * CONSERVATIVE_MULTIPLIER)
    if packet["INPUT_TOKEN_ESTIMATE"] != expected:
        raise ValidationError(
            f"INPUT_TOKEN_ESTIMATE is {packet['INPUT_TOKEN_ESTIMATE']}; {wire} characters give "
            f"{expected} under the held ratio and multiplier"
        )
    if not basis["v1_body_wire_characters"] > basis["v1_recorded_wire_characters"]:
        raise ValidationError("the body definition is not the conservative one on V1")
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
    previous = float(v1["EXECUTION_COST_CEILING"])
    if packet["PREVIOUS_EXECUTION_COST_CEILING"] != previous:
        raise ValidationError("the previous ceiling is not V1's")
    if packet["CEILING_OVER_PREVIOUS_CEILING"] != round(total / previous, 2):
        raise ValidationError("the ratio to the previous ceiling is not recomputable")
    if packet["MATERIALLY_LARGER_THAN_PREVIOUS_APPROVAL"] is not (total > previous):
        raise ValidationError("the ceiling's size against V1's approval is misstated")


def _check_boundaries(packet: dict[str, Any]) -> None:
    for key in CAPABILITY_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    retention = packet["RETENTION_ON_EXECUTION"]
    for key in (
        "raw_provider_response",
        "raw_provider_response_digest",
        "provider_stop_reason",
        "parsed_output_digest",
        "provider_request_id",
        "usage_metadata",
        "terminal_outcome",
    ):
        if "RETAINED" not in str(retention.get(key)):
            raise ValidationError(f"retention of {key} is not recorded as RETAINED")
    if not str(retention["hidden_reasoning"]).startswith("NOT RETAINED"):
        raise ValidationError("hidden reasoning is retained")
    if packet["RETENTION_REPAIR_VERIFIED"] is not True:
        raise ValidationError("RETENTION_PATH_NOT_READY_FOR_SECOND_EXECUTION")
    paths = packet["RETENTION_VERIFIED_PATHS"]
    if tuple(paths) != RETENTION_PATHS:
        raise ValidationError(f"the verified retention paths are {list(paths)}")
    tests = RUNNER_TESTS.read_text(encoding="utf-8")
    for path, test in paths.items():
        if f"def {test}(" not in tests:
            raise ValidationError(f"{path} names {test!r}, which no runner test defines")

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
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V2 does 0")
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
    """One model call site, reached once: in no loop, in a function called once and never re-entered.

    Counting the text `gateway.complete(` finds a second call site and misses a retry, because a
    loop around the one call site is a second request with no second call site. The first probe
    run showed exactly that, so the runner is read as a syntax tree.
    """
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
            f"the V2 runner has {len(calls)} model call sites, and V2 authorises one call"
        )
    holder: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in enclosing(calls[0]):
        if isinstance(node, _LOOPS):
            raise ValidationError(
                "the V2 runner's one call site sits inside a loop, which is a retry by another name"
            )
        if holder is None and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            holder = node
    if holder is None:
        raise ValidationError("the V2 runner's call site is not inside a function")
    callers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == holder.name
    ]
    if len(callers) > 1:
        raise ValidationError(f"{holder.name}() is called {len(callers)} times, and V2 is one call")
    for caller in callers:
        chain = list(enclosing(caller))
        if holder in chain:
            raise ValidationError(f"{holder.name}() calls itself, which is a retry by another name")
        if any(isinstance(node, _LOOPS) for node in chain):
            raise ValidationError(
                f"{holder.name}() is called from inside a loop, which is a retry by another name"
            )


def _check_runner(packet: dict[str, Any]) -> None:
    _check_single_call_site(RUNNER.read_text(encoding="utf-8"))
    runner = _module("execution_runner_v2_for_gate", RUNNER)
    if runner.EXPECTED["EXECUTION_PACKET_SHA256"] != packet["EXECUTION_PACKET_SHA256"]:
        raise ValidationError("the runner was prepared for another digest")
    for key, value in runner.EXPECTED.items():
        if key in packet and packet[key] != value:
            raise ValidationError(
                f"the runner expects {key}={value!r} and V2 binds {packet[key]!r}"
            )
    if tuple(runner.STAGES) != STAGES:
        raise ValidationError("the runner's stages are not the gate's")
    if runner.APPROVAL_FILE.name != APPROVAL.name:
        raise ValidationError("the runner reads its approval from somewhere else")


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    decision = _load(DECISION)
    packet = _load(PACKET)
    _check_decision(decision)
    _check_identity_and_approval(packet)
    _check_v1(packet)
    _check_contract(packet)
    _check_prompt_and_representation(packet)
    _check_route(packet)
    _check_thinking_and_envelope(packet)
    _check_completion_policy(packet)
    _check_calls_and_timeout(packet)
    _check_cost(packet)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet)
    return decision, packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v2.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _sentence(text: object) -> str:
    """A recorded note ends where its writer stopped; the page ends it with a full stop."""
    value = str(text).strip()
    return value if value.endswith((".", "!", "?")) else value + "."


def _capitalised(text: object) -> str:
    value = str(text).strip()
    return value[:1].upper() + value[1:]


def _cost(value: object) -> str:
    """Six places, exact at these prices: a whole token costs a multiple of 0.000001."""
    return f"{float(str(value)):.6f}".rstrip("0").rstrip(".")


def render_decision(decision: dict[str, Any]) -> str:
    envelope = decision["ENVELOPE_MODEL"]
    out = [
        HEADER.format(source=DECISION.name),
        "# Second opportunity: execution envelope decision v1",
        "",
        f"Mission {decision['mission']}, recorded {decision['recorded_at']}. The answer to "
        f"`{decision['DECISION_REQUEST']}`, which {decision['DECISION_REQUESTED_BY']} requested.",
        "",
        f"**Decision: `{decision['DECISION']}`.** An {decision['DECISION_KIND'].lower()} decision "
        f"owned by the {decision['DECISION_OWNER'].lower()}; mathematically derived: "
        f"`{str(decision['MATHEMATICALLY_DERIVED']).lower()}`.",
        "",
        "## The operator's words",
        "",
        *[f"> {line}" for line in decision["OPERATOR_STATEMENT"]],
        "",
        f"SHA-256 of the statement: `{decision['OPERATOR_STATEMENT_SHA256']}`.",
        "",
        "## Two questions, kept apart",
        "",
        f"- The contract answers: *{envelope['CONTRACT_QUESTION']}*",
        f"- The execution envelope answers: *{envelope['ENVELOPE_QUESTION']}*",
        "",
        *_code(
            [
                f"contract maximum            {envelope['CONTRACT_MAXIMUM']}",
                f"contract maximum characters {envelope['CONTRACT_MAXIMUM_CHARACTERS']}",
                f"contract maximum estimate   {envelope['CONTRACT_MAXIMUM_TOKEN_ESTIMATE']} "
                f"(exact: {str(envelope['CONTRACT_MAXIMUM_TOKEN_ESTIMATE_EXACT']).lower()})",
                f"execution route             {envelope['EXECUTION_ROUTE']}",
                f"execution maximum           {envelope['EXECUTION_MAXIMUM_OUTPUT_TOKENS']} "
                "output tokens",
                f"full domain reachable       {str(envelope['CONTRACT_FULL_DOMAIN_REACHABLE']).lower()}",
                f"state                       {envelope['STATE']}",
            ]
        ),
        f"The state is not {', '.join(f'`{s}`' for s in envelope['STATE_IS_NOT'])}. "
        f"{_sentence(envelope['state_note'])}",
        "",
        "## What the operator accepted, and what it costs",
        "",
        f"- Reason: {_sentence(decision['reason'])}",
        f"- Accepted consequence: {_sentence(decision['accepted_consequence'])}",
        f"- Safety consequence: {_sentence(decision['safety_consequence'])}",
        "- Not a schema defect; the execution envelope is a strict subset of the contract.",
        f"- Rejected: {', '.join(f'`{a}`' for a in decision['REJECTED_ALTERNATIVES'])}.",
        f"- max_tokens {decision['MAX_OUTPUT_TOKENS_SELECTED']}, basis "
        f"`{decision['MAX_OUTPUT_TOKENS_BASIS']}`; not based on "
        f"{', '.join(f'`{b}`' for b in decision['MAX_OUTPUT_TOKENS_NOT_BASED_ON'])}.",
        f"- Thinking `{decision['THINKING']}`. Route `{decision['SELECTED_ROUTE']}`; not used: "
        f"{', '.join(f'`{r}`' for r in decision['ROUTES_NOT_USED'])}.",
        "- No retry, no continuation, no repair model. The schema, the prompt and the "
        "structured-output mechanism are unchanged.",
        "",
        f"The estimate is {decision['WHAT_THE_ESTIMATE_IS']}. It is not "
        f"{', '.join(decision['WHAT_THE_ESTIMATE_IS_NOT'])}.",
        "",
        f"**{_sentence(decision['authorisation_note'])}**",
        "",
    ]
    return "\n".join(out)


def render_packet(packet: dict[str, Any]) -> str:
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    timeout = packet["TIMEOUT"]
    policy = packet["PROVIDER_COMPLETION_POLICY"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v2",
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
                f"provider                            {packet['PROVIDER_ID']}",
                f"route                               {packet['PROVIDER_ROUTE_SURFACE']} "
                "(synchronous, Commercial Terms)",
                f"model                               {packet['MODEL_ID']}",
                f"thinking                            {packet['THINKING']}",
                "",
                f"schema / gate                       {packet['OUTPUT_SCHEMA_VERSION']} / "
                f"{packet['OUTPUT_GATE_VERSION']}",
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
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{str(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']).lower()}",
            ]
        ),
        "## The envelope",
        "",
        f"The contract's theoretical maximum is estimated at "
        f"{packet['PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE']} tokens (an estimate, not exact), "
        f"above the {packet['MAX_OUTPUT_TOKENS']} a synchronous request may ask for, so "
        "`CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL = false`. "
        f"The estimate is {_sentence(packet['estimate_note'])}",
        "",
        f"`max_tokens = {packet['MAX_OUTPUT_TOKENS']}`, basis `{packet['MAX_OUTPUT_TOKENS_BASIS']}`, "
        f"not {', '.join(f'`{b}`' for b in packet['MAX_OUTPUT_TOKENS_NOT_BASED_ON'])}. The adapter's "
        f"own default is {packet['ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS']}: "
        f"{packet['adapter_default_note']}.",
        "",
        "## When the answer does not finish",
        "",
        f"Signal: `{policy['signal_field']}`. Complete: "
        f"{', '.join(f'`{v}`' for v in policy['complete_values'])}. Output limit: "
        f"{', '.join(f'`{v}`' for v in policy['output_limit_values'])} → "
        f"`{policy['on_output_limit']}`. Refusal: "
        f"{', '.join(f'`{v}`' for v in policy['refusal_values'])} → `{policy['on_refusal']}`. "
        f"Anything else → `{policy['on_any_other_value']}`.",
        "",
        _sentence(policy["precedence_note"]),
        "",
        *[
            f"- {f['evidence']} line {f['line']}: `` {f['verbatim']} ``"
            for f in policy["documentation"]
        ],
        "",
        "Validation stages, in order: "
        + ", ".join(f"`{s}`" for s in packet["VALIDATION_STAGES"])
        + ".",
        "",
        "## The timeout",
        "",
        f"{timeout['REQUEST_TIMEOUT_SECONDS']} s, {timeout['TIMEOUT_BASIS']}; changed by this "
        f"mission: `{str(timeout['TIMEOUT_CHANGED_BY_THIS_MISSION']).lower()}`. "
        f"{_sentence(timeout['note'])}",
        "",
        "## Cost",
        "",
        *_code(
            [
                f"input token estimate     {packet['INPUT_TOKEN_ESTIMATE']}  "
                f"({basis['wire_characters']} body characters / {basis['chars_per_token']} "
                f"x {basis['conservative_multiplier']})",
                f"output token ceiling     {packet['OUTPUT_TOKEN_CEILING']}",
                f"total token ceiling      {packet['TOTAL_TOKEN_CEILING']}",
                f"pricing                  {packet['PRICING_VERSION']}  "
                f"({packet['PRICE_PER_1K']['input']} / {packet['PRICE_PER_1K']['output']} per 1k)",
                f"input worst case         {_cost(packet['INPUT_WORST_CASE_COST'])}",
                f"output worst case        {_cost(packet['OUTPUT_WORST_CASE_COST'])}",
                f"total worst case         {_cost(packet['WORST_CASE_CALL_COST'])}",
                f"execution cost ceiling   {_cost(packet['EXECUTION_COST_CEILING'])}  "
                f"(headroom policy: {packet['HEADROOM_POLICY']})",
                f"previous ceiling (V1)    {_cost(packet['PREVIOUS_EXECUTION_COST_CEILING'])}  "
                f"(x{packet['CEILING_OVER_PREVIOUS_CEILING']})",
            ]
        ),
        "Costs are shown to six decimal places, which is exact at these prices; the record keeps "
        "the float the pricing function returned.",
        "",
        f"{_sentence(basis['v1_definition_note'])} "
        f"{_sentence(_capitalised(packet['cost_ceiling_basis']))} "
        f"That is {_sentence(packet['materially_larger_note'])}",
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
        f"Predecessor: {packet['PREDECESSOR_EXECUTION_PACKET_ID']} "
        f"`{packet['PREDECESSOR_EXECUTION_PACKET_SHA256']}`, "
        f"{packet['PREDECESSOR_EXECUTION_OUTCOME']}, approval consumed.",
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
        decision, packet = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    rendered = {DECISION_MD: render_decision(decision), PACKET_MD: render_packet(packet)}
    if args.write:
        for path, text in rendered.items():
            path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {', '.join(p.name for p in rendered)}")
    stale = [p for p, text in rendered.items() if p.read_text(encoding="utf-8") != text]
    for path in stale:
        print(f"FAIL     {path.name} is not the rendering of its record")
    if stale:
        return 1
    print("ok       the execution envelope and packet V2 match their records and the live code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
