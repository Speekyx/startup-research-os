"""Mission 1.84.13, CI gate 82. The one execution under packet V4, checked against what it kept.

The execution record says what happened; this gate re-derives it from what was retained. The raw
response digest is recomputed from the retained body and compared with the digest pinned here when
the record was written, the stop reason is read through the adapter's own classifier, the schema
verdict is recomputed by running the live v1.1.0 validator over the retained tool input, each length
violation is measured again and looked up in the prompt v1.3.0 system region, the cost is recomputed
from the reported usage at the held price, and the stage table is derived from those facts rather
than read.

The operator's approval is checked against the words it was given in, the digest it names and the
prohibitions and residual-risk acceptance it carries. V1's, V2's and V3's records are checked
untouched, no human-review packet may exist for an answer a machine stage refused, and the runner is
asked whether it would execute V4 again.

    uv run python infrastructure/scripts/render_second_opportunity_execution_record_v4.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
from typing import Any

from sros_llm_gateway.pricing import ModelPrice
from sros_llm_gateway.providers.anthropic import (
    DEFAULT_ENDPOINT,
    STRUCTURED_TOOL_NAME,
    AnthropicCompletion,
    classify_forced_tool_completion,
)
from sros_opportunity.output_constraints import constraint_inventory, is_explicit
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_SYSTEM_V1_2,
)
from sros_opportunity.second_opportunity_prompt_v1_3 import SECOND_OPPORTUNITY_SYSTEM_V1_3

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

RECORD = DATA / "second-opportunity-synthesis-execution-record-v4.json"
RECORD_MD = DATA / "second-opportunity-synthesis-execution-record-v4.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v4.json"
RESPONSE = DATA / "second-opportunity-synthesis-response-v4.json"
REVIEW_PACKET = DATA / "second-opportunity-human-review-packet-v4.json"
PACKET_V4 = DATA / "second-opportunity-synthesis-execution-packet-v4.json"
RECORD_V1 = DATA / "second-opportunity-synthesis-execution-record-v1.json"
RECORD_V2 = DATA / "second-opportunity-synthesis-execution-record-v2.json"
RECORD_V3 = DATA / "second-opportunity-synthesis-execution-record-v3.json"
RESPONSE_V3 = DATA / "second-opportunity-synthesis-response-v3.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v4.py"
PACKET_GATE = SCRIPTS / "render_second_opportunity_execution_packet_v4.py"

MISSION = "mission-1.84.13"
V4_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V4"
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
#: V1's, V2's and V3's execution records, byte for byte as Missions 1.84.2, 1.84.7 and 1.84.9 left them.
V1_RECORD_SHA256 = "b769ddeb6ea4d4e773640c3ed83caeff52c52c857fd9125325140de4ab38c799"
V2_RECORD_SHA256 = "3fb8d5bae0cb2c64e165961518d9dfd3b1de98eef5244600ea0e5efc289001a7"
V3_RECORD_SHA256 = "abb093389664405f80878d2a1963beabfa4c271ed559437384146a92ccfb00a3"
#: What arrived and what authorised it, pinned when the record was written. An answer rewritten to
#: pass, with every digest recomputed to match, is still not the answer that arrived.
RAW_RESPONSE_SHA256 = "b526c5402efa10daf99eccf93e8a0a26f16f5c710f80adfb45ae088a062aab46"
PARSED_OUTPUT_SHA256 = "2c30d7ebe9e7ba8f66c46c83c3d7cfe885bb3f6c81e818f6f30bae1bde809c9d"
APPROVAL_FILE_SHA256 = "c5cb608e4cf5aac6698ebec005658184e173518bb0ea719ba7e25185d5a73957"
OPERATOR_STATEMENT_SHA256 = "064b87fce76a5fbbc29ca7b77dc68e0ce13cc661928b2a8f99a94be231488c92"
TED_REPRESENTATION_BYTES = 3604
PRICE = ModelPrice(input_per_1k=0.002, output_per_1k=0.01)
SECRET = re.compile(r"sk-ant-[A-Za-z0-9_\-]{6,}|sk-[A-Za-z0-9]{16,}")

STAGES = (
    "1_transport_success",
    "2_provider_response_shape",
    "3_provider_completion",
    "4_structured_output_parse",
    "5_schema_validation_v1_1_0",
    "6_semantic_output_gate_v1_3_0",
    "7_evidence_boundary_and_no_distortion",
    "8_attribution_and_provenance",
    "9_persistence_eligibility",
    "10_human_review",
)

ACCEPTED = "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
READY_FOR_HUMAN_REVIEW = "SECOND_OPPORTUNITY_SYNTHESIS_V4_READY_FOR_HUMAN_REVIEW"

#: The V4 runner's outcome codes, and the factual outcome the Mission 1.84.13 brief names for each.
FACTUAL = {
    "EXECUTION_FAILED_TIMEOUT_NO_RETRY": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
    "EXECUTION_FAILED_TRANSPORT_NO_RETRY": "EXECUTION_FAILED_TRANSPORT_NO_RETRY",
    "EXECUTION_FAILED_PROVIDER_ERROR_NO_RETRY": "EXECUTION_FAILED_PROVIDER_ERROR_NO_RETRY",
    "EXECUTION_OUTPUT_REJECTED_AT_RESPONSE_SHAPE_NO_RETRY": (
        "EXECUTION_PROVIDER_SHAPE_REJECTED_NO_RETRY"
    ),
    "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY": "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY",
    "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY": "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY",
    "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY": "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY",
    "EXECUTION_OUTPUT_REJECTED_AT_STRUCTURED_PARSE_NO_RETRY": "EXECUTION_PARSE_REJECTED_NO_RETRY",
    "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY": "EXECUTION_SCHEMA_REJECTED_NO_RETRY",
    "EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY": (
        "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY"
    ),
    "EXECUTION_OUTPUT_REJECTED_AT_EVIDENCE_BOUNDARY_NO_RETRY": (
        "EXECUTION_EVIDENCE_BOUNDARY_REJECTED_NO_RETRY"
    ),
    "EXECUTION_OUTPUT_REJECTED_AT_ATTRIBUTION_NO_RETRY": "EXECUTION_PROVENANCE_REJECTED_NO_RETRY",
    "EXECUTION_OUTPUT_REJECTED_AT_PERSISTENCE_ELIGIBILITY_NO_RETRY": (
        "EXECUTION_PERSISTENCE_ELIGIBILITY_REJECTED_NO_RETRY"
    ),
    "EXECUTION_COMPLETED_INSUFFICIENT_EVIDENCE_NO_OPPORTUNITY": (
        "EXECUTION_COMPLETED_INSUFFICIENT_EVIDENCE_NO_OPPORTUNITY"
    ),
    "EXECUTION_POST_CALL_HANDLING_FAILED_NO_RETRY": "EXECUTION_POST_CALL_HANDLING_FAILED_NO_RETRY",
    ACCEPTED: READY_FOR_HUMAN_REVIEW,
}

#: Prohibitions the operator's approval must still carry, verbatim. A refused answer is where each
#: of these gets tempting.
REQUIRED_PROHIBITIONS = (
    "re-execution of V1;",
    "re-execution of V2;",
    "re-execution of V3;",
    "reuse of any previous approval;",
    "any second provider request;",
    "any retry;",
    "retry after timeout;",
    "retry after max_tokens;",
    "retry after schema failure;",
    "retry after semantic failure;",
    "retry after evidence-boundary failure;",
    "retry after provenance failure;",
    "retry after persistence-eligibility failure;",
    "continuation requests;",
    '"finish the JSON" requests;',
    "repair-model calls;",
    "post-processing to rescue output;",
    "truncation;",
    "rewriting;",
    "statement splitting;",
    "dropping unsupported statements;",
    "reclassification after generation;",
    "automatic creation of Opportunity #2.",
)
#: What the operator approved no change to, verbatim.
REQUIRED_UNCHANGED = (
    "output schema v1.1.0;",
    "semantic gate v1.3.0;",
    "prompt v1.3.0;",
    "TED representation;",
    "source-metadata evidence boundary;",
    "observed-statement atomicity rule;",
    "observed-disjunction policy;",
    "model;",
    "route;",
    "thinking policy;",
    "max_tokens;",
    "timeout;",
    "cost ceiling.",
)
#: What the residual-risk acceptance does not authorise, verbatim.
REQUIRED_RISK_EXCLUSIONS = (
    "treating source metadata as factual evidence;",
    "weakening ADR-040;",
    "changing the source-metadata decision;",
    "automatic persistence;",
    "skipping human review.",
)

#: The canonical state before and after. Mission 1.84.13 may not move any of it.
CANONICAL_COUNTERS: dict[str, object] = {
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
    "scoring.scores": "ABSENT",
}

_LENGTH_VIOLATION = re.compile(r"^([a-z_]+): (\d+) characters exceeds maxLength (\d+)$")


class ValidationError(RuntimeError):
    """The record disagrees with its approval, its retained response, V1 to V3, or the runner."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    if not isinstance(block, dict):
        raise ValidationError(f"{where} is {block!r}; the record must carry the block itself")
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


# --------------------------------------------------------------------------- the schema refusal


def _max_length_constraint(field: str) -> Any:
    for constraint in constraint_inventory(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1):
        if constraint.path == field and constraint.keyword == "maxLength":
            return constraint
    raise ValidationError(f"the schema has no maxLength for {field!r}")


def violation_details(parsed: dict[str, Any], violations: list[str]) -> list[dict[str, object]]:
    """Each length violation measured again, and whether each prompt stated the bound in words."""
    v3 = _load(RESPONSE_V3)["parsed_output"]
    details: list[dict[str, object]] = []
    for violation in violations:
        match = _LENGTH_VIOLATION.match(violation)
        if match is None:
            raise ValidationError(
                f"this record describes an answer refused on length bounds, and the validator "
                f"reports {violation!r}"
            )
        field, length, bound = match.group(1), int(match.group(2)), int(match.group(3))
        text = parsed.get(field)
        if not isinstance(text, str) or len(text) != length:
            raise ValidationError(f"{field} is not {length} characters in the retained answer")
        if SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field].get("maxLength") != bound:
            raise ValidationError(f"the live schema does not bound {field} at {bound}")
        constraint = _max_length_constraint(field)
        details.append(
            {
                "field": field,
                "characters": length,
                "maxLength": bound,
                "over_by": length - bound,
                "stated_in_prompt_v1_3_0": is_explicit(constraint, SECOND_OPPORTUNITY_SYSTEM_V1_3),
                "stated_in_prompt_v1_2_0": is_explicit(constraint, SECOND_OPPORTUNITY_SYSTEM_V1_2),
                "v3_characters": len(str(v3.get(field) or "")),
            }
        )
    return details


# --------------------------------------------------------------------------- the packet


def _check_packet(record: dict[str, Any]) -> dict[str, Any]:
    packet = _load(PACKET_V4)
    digest = _module("packet_v4_gate_for_gate_82", PACKET_GATE).packet_digest(packet)
    if digest != V4_SHA256 or packet["EXECUTION_PACKET_SHA256"] != digest:
        raise ValidationError("the executed packet moved after it was approved")
    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
        raise ValidationError("the frozen packet was edited to record its own approval")
    _fixed(
        record,
        {
            "execution_packet_id": V4_ID,
            "execution_packet_version": 4,
            "execution_packet_sha256": V4_SHA256,
        },
        "record",
    )
    return packet


# --------------------------------------------------------------------------- the record


def _check_record(record: dict[str, Any], packet: dict[str, Any]) -> None:
    _fixed(
        record,
        {
            "recorded_by": MISSION,
            "EXECUTION_APPROVAL_CONSUMED": True,
            "FURTHER_CALLS_AUTHORIZED_BY_V4": False,
            "actual_provider_requests": 1,
            "actual_model_calls": 1,
            "retries": 0,
            "fallbacks": 0,
            "continuation_requests": 0,
            "repair_calls": 0,
            "PROVIDER": packet["PROVIDER_ID"],
            "ROUTE": f"POST {DEFAULT_ENDPOINT}",
            "ROUTE_KIND": "SYNCHRONOUS_MESSAGES_API",
            "BETA_HEADERS": [],
            "MODEL": packet["MODEL_ID"],
            "THINKING_POLICY": "DISABLED",
            "THINKING_REQUEST_VALUE": {"type": "disabled"},
            "MAX_TOKENS": packet["MAX_OUTPUT_TOKENS"],
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "PROMPT_VERSION": packet["PROMPT_VERSION"],
            "PROMPT_SHA256": packet["PROMPT_SHA256"],
            "OUTPUT_SCHEMA_VERSION": packet["OUTPUT_SCHEMA_VERSION"],
            "OUTPUT_SCHEMA_SHA256": packet["OUTPUT_SCHEMA_SHA256"],
            "OUTPUT_GATE_VERSION": packet["OUTPUT_GATE_VERSION"],
            "SEMANTIC_GATE_IMPLEMENTATION_SHA256": packet["SEMANTIC_GATE_IMPLEMENTATION_SHA256"],
            "HUMAN_OUTPUT_REVIEW_REQUIRED": True,
            "CANONICAL_PERSISTENCE": False,
            "OPPORTUNITY_PERSISTED": False,
            "CANONICAL_MUTATIONS": 0,
            "NOT_REACHED_IS_NOT_PASSED": True,
            "CREDENTIAL_VALUES_RECORDED": False,
            "TED_BYTES_SENT": TED_REPRESENTATION_BYTES,
            "TED_REPRESENTATION_CHARACTERS": packet["REPRESENTATION_CHARACTER_COUNT"],
            "TED_REPRESENTATION_SHA256": packet["REPRESENTATION_SHA256"],
            "REQUEST_BODY_CHARACTERS": packet["TOKEN_ESTIMATION_BASIS"]["wire_characters"],
            "INPUT_TOKEN_ESTIMATE": packet["INPUT_TOKEN_ESTIMATE"],
            "WORST_CASE_CALL_COST": packet["WORST_CASE_CALL_COST"],
            "EXECUTION_COST_CEILING": packet["EXECUTION_COST_CEILING"],
        },
        "record",
    )
    ready = record["PRIMARY_OUTCOME"] == READY_FOR_HUMAN_REVIEW
    if record["HUMAN_REVIEW_PACKET"] != ("PRODUCED" if ready else "NOT_PRODUCED"):
        raise ValidationError(
            "a human-review packet is produced for an answer every machine stage accepted, and "
            "for nothing else"
        )
    if REVIEW_PACKET.exists() is not ready:
        raise ValidationError(
            f"{REVIEW_PACKET.name} {'is missing' if ready else 'exists'}, and a human-review packet "
            "exists exactly when stages 1 to 9 passed"
        )
    if record["CANONICAL_COUNTERS_BEFORE"] != CANONICAL_COUNTERS:
        raise ValidationError("the canonical state before the call is not the one the brief fixed")
    if record["CANONICAL_COUNTERS_AFTER"] != CANONICAL_COUNTERS:
        raise ValidationError("a canonical counter moved, and Mission 1.84.13 may move none")


# --------------------------------------------------------------------------- the approval


def _check_approval(record: dict[str, Any], packet: dict[str, Any]) -> None:
    approval = _load(APPROVAL)
    block = record["OPERATOR_APPROVAL"]
    if _sha_file(APPROVAL) != APPROVAL_FILE_SHA256 or block["file_sha256"] != APPROVAL_FILE_SHA256:
        raise ValidationError("the approval changed after the execution record bound it")
    _fixed(
        approval,
        {
            "EXECUTION_PACKET_ID": V4_ID,
            "EXECUTION_PACKET_VERSION": 4,
            "EXECUTION_PACKET_SHA256": V4_SHA256,
            "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
            "recorded_by": MISSION,
            "EXECUTIONS_AUTHORISED": 1,
            "V1_APPROVAL_REUSED": False,
            "V2_APPROVAL_REUSED": False,
            "V3_APPROVAL_REUSED": False,
            "PACKET_V4_MODIFIED": False,
            "OPPORTUNITY_PERSISTENCE_AUTHORISED": False,
        },
        "approval",
    )
    lines = approval["operator_statement_lines"]
    if not lines or not all(isinstance(line, str) and line.strip() for line in lines):
        raise ValidationError("the operator's statement is empty or has an empty line")
    joined = "\n".join(lines)
    if approval["operator_statement"] != joined:
        raise ValidationError("the operator's statement and its lines disagree")
    digest = _sha_text(joined)
    if not (
        digest
        == approval["operator_statement_sha256"]
        == block["operator_statement_sha256"]
        == OPERATOR_STATEMENT_SHA256
    ):
        raise ValidationError("the operator's words changed after their digest was recorded")
    for line in (
        "I APPROVE THE FOLLOWING EXECUTION EXACTLY AS FROZEN.",
        V4_SHA256,
        "APPROVE_EXACTLY_ONE_EXECUTION",
    ):
        if line not in lines:
            raise ValidationError(f"the recorded words no longer say {line!r}")
    for name, required, present in (
        ("forbids", REQUIRED_PROHIBITIONS, approval["NOT_AUTHORISED"]),
        ("withholds a change to", REQUIRED_UNCHANGED, approval["NO_CHANGE_APPROVED_TO"]),
        (
            "keeps outside the residual risk",
            REQUIRED_RISK_EXCLUSIONS,
            approval["RESIDUAL_RISK_ACCEPTED"]["DOES_NOT_AUTHORISE"],
        ),
    ):
        missing = [
            item for item in required if item not in set(present) or f"- {item}" not in lines
        ]
        if missing:
            raise ValidationError(f"the approval no longer {name} {missing}")
    if approval["RESIDUAL_RISK_ACCEPTED"]["for"] != "this ONE execution":
        raise ValidationError("the residual-risk acceptance is no longer bounded to one execution")
    if not str(approval.get("approved_by") or "").strip():
        raise ValidationError("the approval names no approver")
    _fixed(
        block,
        {
            "decision": approval["decision"],
            "approved_by": approval["approved_by"],
            "recorded_by": MISSION,
        },
        "record.OPERATOR_APPROVAL",
    )
    executed = approval["APPROVED_EXECUTION"]
    if not str(executed.get("route", "")).startswith(packet["PROVIDER_ROUTE_SURFACE"] + ", "):
        raise ValidationError("the approved route is not the packet's")
    _fixed(
        executed,
        {
            "provider": packet["PROVIDER_ID"],
            "model": packet["MODEL_ID"],
            "thinking": packet["THINKING"],
            "thinking_request_value": packet["THINKING_REQUEST_FIELD"],
            "subject": packet["SUBJECT_KEY"],
            "output_schema": packet["OUTPUT_SCHEMA_VERSION"],
            "output_schema_sha256": packet["OUTPUT_SCHEMA_SHA256"],
            "semantic_gate": packet["OUTPUT_GATE_VERSION"],
            "semantic_gate_implementation_sha256": packet["SEMANTIC_GATE_IMPLEMENTATION_SHA256"],
            "prompt": f"{packet['PROMPT_ID']}@{packet['PROMPT_VERSION']}",
            "prompt_sha256": packet["PROMPT_SHA256"],
            "representation_sha256": packet["REPRESENTATION_SHA256"],
            "representation_characters": packet["REPRESENTATION_CHARACTER_COUNT"],
            "MAX_OUTPUT_TOKENS": packet["MAX_OUTPUT_TOKENS"],
            "MAX_MODEL_CALLS": packet["MAX_MODEL_CALLS"],
            "MAX_RETRIES": packet["MAX_RETRIES"],
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "REQUEST_BODY_CHARACTERS_PREPARED": packet["TOKEN_ESTIMATION_BASIS"]["wire_characters"],
            "INPUT_TOKEN_ESTIMATE": packet["INPUT_TOKEN_ESTIMATE"],
            "WORST_CASE_INPUT_COST": packet["INPUT_WORST_CASE_COST"],
            "WORST_CASE_OUTPUT_COST": packet["OUTPUT_WORST_CASE_COST"],
            "WORST_CASE_CALL_COST": packet["WORST_CASE_CALL_COST"],
            "EXECUTION_COST_CEILING": packet["EXECUTION_COST_CEILING"],
            "HUMAN_OUTPUT_REVIEW_REQUIRED": True,
            "CANONICAL_PERSISTENCE_AUTOMATICALLY_AUTHORIZED": False,
        },
        "approval.APPROVED_EXECUTION",
    )


# --------------------------------------------------------------------------- the response


def _derived_stages(
    completion: AnthropicCompletion, blocks: list[dict[str, Any]], violations: list[str]
) -> tuple[dict[str, str], str | None]:
    """The stage table these facts imply. Transport and shape were checked before this is called."""
    stages = dict.fromkeys(STAGES, "NOT_REACHED")
    stages[STAGES[0]] = stages[STAGES[1]] = "PASSED"
    if completion is not AnthropicCompletion.COMPLETE:
        stages[STAGES[2]] = "FAILED"
        return stages, STAGES[2]
    stages[STAGES[2]] = "PASSED"
    if len(blocks) != 1:
        stages[STAGES[3]] = "FAILED"
        return stages, STAGES[3]
    stages[STAGES[3]] = "PASSED"
    if violations:
        stages[STAGES[4]] = "FAILED"
        return stages, STAGES[4]
    raise ValidationError(
        "the retained answer passes the v1.1.0 schema, so its later stages need the evidence packet "
        "and the frozen gate; this record describes an answer refused at stage 5"
    )


def _check_response(record: dict[str, Any], packet: dict[str, Any]) -> None:
    artifact = _load(RESPONSE)
    kept = record["RESPONSE_ARTIFACT"]
    if _sha_file(RESPONSE) != kept["file_sha256"]:
        raise ValidationError("the response artifact changed after the execution record bound it")
    _fixed(
        artifact,
        {
            "PROVIDER_REQUESTS_MADE": 1,
            "RETRIES": 0,
            "transport_errors": [],
            "RAW_PROVIDER_RESPONSE_STATUS": 200,
            "RAW_PROVIDER_RESPONSE_RETAINED": True,
            "USAGE_RETAINED": True,
            "PARSED_OUTPUT_RETAINED": True,
            "HIDDEN_REASONING_REQUESTED": False,
            "HIDDEN_REASONING_RETAINED": False,
            "PERSISTED": "NOTHING",
            "execution_packet_id": V4_ID,
            "execution_packet_sha256": V4_SHA256,
        },
        "response",
    )
    if record["POST_CALL_FALLBACK_USED"] is not ("POST_CALL_HANDLING_FAILED" in artifact):
        raise ValidationError("the record misstates whether the post-call fail-safe was used")

    body = artifact["RAW_PROVIDER_RESPONSE_BODY"]
    if not isinstance(body, dict) or not isinstance(body.get("content"), list):
        raise ValidationError("the retained response is not the provider's message object")
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    digest = _sha_text(raw)
    if not (
        digest
        == artifact["RAW_PROVIDER_RESPONSE_SHA256"]
        == kept["raw_response_sha256"]
        == RAW_RESPONSE_SHA256
    ):
        raise ValidationError("the retained body is not the one that arrived")
    if (
        len(raw) != artifact["RAW_PROVIDER_RESPONSE_CHARACTERS"]
        or len(raw) != kept["raw_response_characters"]
    ):
        raise ValidationError("the retained body is not as long as what arrived")
    _fixed(
        kept,
        {
            "RAW_PROVIDER_RESPONSE_RETAINED": True,
            "raw_digest_recomputable_from_retained_body": True,
            "PARSED_OUTPUT_RETAINED": True,
            "USAGE_RETAINED": True,
            "HIDDEN_REASONING_RETAINED": False,
        },
        "record.RESPONSE_ARTIFACT",
    )
    _fixed(
        record,
        {
            "HTTP_STATUS": 200,
            "PROVIDER_REQUEST_ID": artifact["PROVIDER_REQUEST_ID"],
            "PROVIDER_MESSAGE_ID": body.get("id"),
            "RESPONSE_MODEL": body.get("model"),
            "STOP_REASON": body.get("stop_reason"),
        },
        "record",
    )
    if body.get("model") != packet["MODEL_ID"]:
        raise ValidationError(f"the response came from {body.get('model')!r}")
    if any(
        isinstance(block, dict) and block.get("type") in ("thinking", "redacted_thinking")
        for block in body["content"]
    ):
        raise ValidationError("a reasoning block was retained")

    if artifact["STOP_REASON"] != body.get("stop_reason"):
        raise ValidationError("the artifact's stop reason is not the response's own")
    completion = classify_forced_tool_completion(body.get("stop_reason"))
    if (
        record["PROVIDER_COMPLETION"] != completion.value
        or artifact["PROVIDER_COMPLETION"] != completion.value
    ):
        raise ValidationError("the recorded completion is not the adapter's reading of stop_reason")

    usage = body["usage"]
    tokens_in, tokens_out = int(usage["input_tokens"]), int(usage["output_tokens"])
    thinking = (usage.get("output_tokens_details") or {}).get("thinking_tokens")
    for key in ("ACTUAL_USAGE", "ACTUAL_COST"):
        if not isinstance(record[key], dict):
            raise ValidationError(
                f"the record gives {key} as {record[key]!r}, and the retained response reports "
                "the usage it rests on: NOT_ESTABLISHED is for a figure that was genuinely unavailable"
            )
    _fixed(
        record["ACTUAL_USAGE"],
        {
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": tokens_in + tokens_out,
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "thinking_tokens": thinking,
        },
        "record.ACTUAL_USAGE",
    )
    if thinking != 0 or record["THINKING_TOKENS_REPORTED"] != 0:
        raise ValidationError("thinking tokens were reported under a DISABLED policy")
    if artifact["USAGE_FROM_RESPONSE"] != usage:
        raise ValidationError("the artifact's usage is not the response's own usage block")
    telemetry = artifact["usage"]
    if len(telemetry) != 1 or (telemetry[0]["input_tokens"], telemetry[0]["output_tokens"]) != (
        tokens_in,
        tokens_out,
    ):
        raise ValidationError("the Gateway's telemetry and the response disagree about usage")

    cost = round(PRICE.cost_for(tokens_in, tokens_out), 6)
    _fixed(
        record["ACTUAL_COST"],
        {
            "cost_units": cost,
            "input_cost_units": round(PRICE.cost_for(tokens_in, 0), 6),
            "output_cost_units": round(PRICE.cost_for(0, tokens_out), 6),
            "pricing_version": packet["PRICING_VERSION"],
            "priced": True,
        },
        "record.ACTUAL_COST",
    )
    if telemetry[0]["cost_units"] != cost or telemetry[0]["priced"] is not True:
        raise ValidationError("the Gateway's telemetry and the recomputed cost disagree")
    if cost > packet["EXECUTION_COST_CEILING"] or record["ACTUAL_COST_WITHIN_CEILING"] is not True:
        raise ValidationError("the call cost more than its ceiling, or the record says otherwise")
    if record["INPUT_ESTIMATE_COVERED_THE_ACTUAL"] is not (
        tokens_in <= packet["INPUT_TOKEN_ESTIMATE"]
    ):
        raise ValidationError("the record misstates whether the input estimate covered the call")

    timing = artifact["timing"]
    if record["timing"] != timing:
        raise ValidationError("the recorded timing is not the artifact's")
    timed_out = float(timing["elapsed_seconds"]) >= float(packet["REQUEST_TIMEOUT"])
    if record["TIMED_OUT"] is not timed_out:
        raise ValidationError("the record misstates whether the call timed out")

    blocks = [
        block
        for block in body["content"]
        if isinstance(block, dict)
        and block.get("type") == "tool_use"
        and block.get("name") == STRUCTURED_TOOL_NAME
    ]
    parsed = artifact["parsed_output"]
    if len(blocks) != 1 or blocks[0].get("input") != parsed:
        raise ValidationError("the retained parsed output is not the tool call that arrived")
    parsed_digest = _sha_text(json.dumps(parsed, sort_keys=True))
    if not (
        parsed_digest
        == artifact["PARSED_OUTPUT_SHA256"]
        == kept["parsed_output_sha256"]
        == PARSED_OUTPUT_SHA256
    ):
        raise ValidationError("the parsed output is not the one that arrived")

    violations = list(schema_violations(dict(parsed), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
    if violations != record["SCHEMA_VIOLATIONS"]:
        raise ValidationError(
            "the recorded schema violations are not what the live v1.1.0 validator finds in the "
            f"retained answer: {violations}"
        )
    if violation_details(parsed, violations) != record["SCHEMA_VIOLATION_DETAILS"]:
        raise ValidationError("the recorded violation details are not what the answer measures")
    validation = artifact["validation"]
    if list(validation["reasons"]) != violations:
        raise ValidationError("the runner's retained reasons are not the schema's violations")
    if record["SEMANTIC_GATE_REFUSAL_REASONS"] != [] or record["SEMANTIC_GATE_VERDICT"] != (
        "NOT_REACHED"
    ):
        raise ValidationError("a semantic verdict is recorded for an answer the schema refused")
    stages, failed = _derived_stages(completion, blocks, violations)
    if record["VALIDATION_STAGES"] != stages or validation["stages"] != stages:
        raise ValidationError("the stage table is not the one these facts imply")
    if record["FAILED_STAGE"] != failed or validation["failed_stage"] != failed:
        raise ValidationError("the failed stage is not the one these facts imply")
    if record["STAGES_PASSED"] != sum(1 for verdict in stages.values() if verdict == "PASSED"):
        raise ValidationError("a stage that was not reached is counted as passed")

    runner_outcome = artifact["TERMINAL_OUTCOME"]
    if not (
        runner_outcome == artifact["OUTCOME"] == validation["outcome"] == record["RUNNER_OUTCOME"]
    ):
        raise ValidationError("the runner's outcome is not recorded consistently")
    if FACTUAL.get(runner_outcome) != record["PRIMARY_OUTCOME"]:
        raise ValidationError(
            f"{record['PRIMARY_OUTCOME']} does not follow from the runner's {runner_outcome}"
        )


# --------------------------------------------------------------------------- history, runner, secrets


def _check_history(record: dict[str, Any]) -> None:
    for label, path, pinned, key, digest in (
        ("V1", RECORD_V1, V1_RECORD_SHA256, "V1_EXECUTION_RECORD_SHA256", V1_SHA256),
        ("V2", RECORD_V2, V2_RECORD_SHA256, "V2_EXECUTION_RECORD_SHA256", V2_SHA256),
        ("V3", RECORD_V3, V3_RECORD_SHA256, "V3_EXECUTION_RECORD_SHA256", V3_SHA256),
    ):
        if _sha_file(path) != pinned or record[key] != pinned:
            raise ValidationError(f"{label}'s historical execution record was edited")
        historical = _load(path)
        if historical.get("EXECUTION_APPROVAL_CONSUMED") is not True:
            raise ValidationError(f"{label}'s consumption was reset")
        if historical.get("execution_packet_sha256") != digest:
            raise ValidationError(f"{label}'s record names another digest")


def _check_runner() -> None:
    runner = _module("execution_runner_v4_for_gate_82", RUNNER)
    for label, digest in (
        ("V4", V4_SHA256),
        ("V3", V3_SHA256),
        ("V2", V2_SHA256),
        ("V1", V1_SHA256),
    ):
        try:
            runner.refuse_if_consumed(digest)
        except runner.RefusedError as exc:
            if exc.code != "EXECUTION_APPROVAL_ALREADY_CONSUMED":
                raise ValidationError(
                    f"the runner refuses {label} for the wrong reason: {exc.code}"
                ) from exc
        else:
            raise ValidationError(
                f"the runner would execute {label} again: its guard does not see {label} spent"
            )
    try:
        runner.refuse_if_consumed("0" * 64)
    except runner.RefusedError as exc:
        raise ValidationError(
            "the runner's guard refuses every digest, not only spent ones"
        ) from exc
    if runner.EXECUTION_RECORD_V4.name != RECORD.name or runner.RESPONSE_ARTIFACT.name != (
        RESPONSE.name
    ):
        raise ValidationError("the runner reads V4's consumption or response from somewhere else")


def _check_no_credentials() -> None:
    for path in (RECORD, APPROVAL, RESPONSE, *([REVIEW_PACKET] if REVIEW_PACKET.exists() else [])):
        if SECRET.search(path.read_text(encoding="utf-8")):
            raise ValidationError(f"{path.name} carries something shaped like a credential")


def validate() -> dict[str, Any]:
    record = _load(RECORD)
    packet = _check_packet(record)
    _check_record(record, packet)
    _check_approval(record, packet)
    _check_response(record, packet)
    _check_history(record)
    _check_runner()
    _check_no_credentials()
    return record


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_record_v4.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _sentence(text: object) -> str:
    value = str(text).strip()
    return value if value.endswith((".", "!", "?")) else value + "."


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def render(record: dict[str, Any]) -> str:
    usage = record["ACTUAL_USAGE"]
    cost = record["ACTUAL_COST"]
    approval = record["OPERATOR_APPROVAL"]
    kept = record["RESPONSE_ARTIFACT"]
    timing = record["timing"]
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: synthesis execution record v4",
        "",
        f"Recorded by {record['recorded_by']} on {record['recorded_on']}. "
        f"**{record['PRIMARY_OUTCOME']}.**",
        "",
        f"**One provider request was made under `{record['execution_packet_id']}` version "
        f"{record['execution_packet_version']}, and the operator's approval is spent. Nothing was "
        "persisted.**",
        "",
        _sentence(record["outcome_note"]),
        "",
        "## The request",
        "",
        *_code(
            [
                f"packet                 {record['execution_packet_sha256']}",
                f"approval               {approval['decision']}, by {approval['approved_by']}",
                f"approval statement     {approval['operator_statement_sha256']}",
                f"route                  {record['ROUTE']} ({record['ROUTE_KIND']})",
                f"model                  {record['MODEL']} (response: {record['RESPONSE_MODEL']})",
                f"thinking               {record['THINKING_POLICY']}, "
                f"{json.dumps(record['THINKING_REQUEST_VALUE'])}",
                f"max_tokens             {record['MAX_TOKENS']}",
                f"timeout                {record['REQUEST_TIMEOUT_SECONDS']} s",
                f"prompt                 {record['PROMPT_VERSION']} {record['PROMPT_SHA256']}",
                f"schema                 {record['OUTPUT_SCHEMA_VERSION']} "
                f"{record['OUTPUT_SCHEMA_SHA256']}",
                f"semantic gate          {record['OUTPUT_GATE_VERSION']} "
                f"{record['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}",
                f"representation         {record['TED_REPRESENTATION_SHA256']}",
                f"started / finished     {timing['started_at']} / {timing['finished_at']}",
                f"elapsed                {timing['elapsed_seconds']} s "
                f"(timed out: {str(record['TIMED_OUT']).lower()})",
                f"HTTP status            {record['HTTP_STATUS']}",
                f"request id             {record['PROVIDER_REQUEST_ID']}",
                f"message id             {record['PROVIDER_MESSAGE_ID']}",
            ]
        ),
        "## What came back",
        "",
        *_code(
            [
                f"stop_reason            {record['STOP_REASON']} -> {record['PROVIDER_COMPLETION']}",
                f"input tokens           {usage['input_tokens']} "
                f"(estimated {record['INPUT_TOKEN_ESTIMATE']})",
                f"output tokens          {usage['output_tokens']} (ceiling {record['MAX_TOKENS']})",
                f"total tokens           {usage['total_tokens']}",
                f"thinking tokens        {usage['thinking_tokens']}",
                f"cost                   {cost['cost_units']} "
                f"({cost['input_cost_units']} input + {cost['output_cost_units']} output, "
                f"{cost['pricing_version']})",
                f"ceiling                {record['EXECUTION_COST_CEILING']} "
                f"(within: {str(record['ACTUAL_COST_WITHIN_CEILING']).lower()})",
            ]
        ),
        _sentence(record["cost_note"]),
        "",
        "## The ten stages",
        "",
        "| stage | verdict |",
        "|---|---|",
        *[f"| `{stage}` | {verdict} |" for stage, verdict in record["VALIDATION_STAGES"].items()],
        "",
        f"Stages passed: {record['STAGES_PASSED']}. Failed: `{record['FAILED_STAGE']}`, because the "
        "live v1.1.0 validator reports:",
        "",
        *[f"- `{violation}`" for violation in record["SCHEMA_VIOLATIONS"]],
        "",
        "A stage that was not reached is not a stage that passed: the semantic gate, the evidence "
        "boundary, attribution and persistence eligibility never judged this answer.",
        "",
        "## The two bounds",
        "",
        "| field | characters | bound | over by | stated in prompt v1.3.0 | stated in v1.2.0 | V3 |",
        "|---|---|---|---|---|---|---|",
        *[
            f"| `{d['field']}` | {d['characters']} | {d['maxLength']} | {d['over_by']} | "
            f"{str(d['stated_in_prompt_v1_3_0']).lower()} | "
            f"{str(d['stated_in_prompt_v1_2_0']).lower()} | {d['v3_characters']} |"
            for d in record["SCHEMA_VIOLATION_DETAILS"]
        ],
        "",
        _sentence(record["schema_note"]),
        "",
        "## What was kept",
        "",
        *_code(
            [
                f"response artifact      {kept['file']}",
                f"raw response sha256    {kept['raw_response_sha256']} "
                f"({kept['raw_response_characters']} characters, recomputable from the kept body)",
                f"parsed output sha256   {kept['parsed_output_sha256']}",
                f"usage retained         {str(kept['USAGE_RETAINED']).lower()}",
                f"hidden reasoning       retained: {str(kept['HIDDEN_REASONING_RETAINED']).lower()}",
                f"post-call fail-safe    used: {str(record['POST_CALL_FALLBACK_USED']).lower()}",
            ]
        ),
        _sentence(record["retention_note"]),
        "",
        "## Accounting",
        "",
        *_code(
            [
                f"provider requests      {record['actual_provider_requests']}",
                f"model calls            {record['actual_model_calls']}",
                f"retries                {record['retries']}",
                f"fallbacks              {record['fallbacks']}",
                f"continuations          {record['continuation_requests']}",
                f"repair calls           {record['repair_calls']}",
                f"TED bytes sent         {record['TED_BYTES_SENT']}",
                f"canonical mutations    {record['CANONICAL_MUTATIONS']}",
                f"Opportunity persisted  {str(record['OPPORTUNITY_PERSISTED']).lower()}",
            ]
        ),
        _sentence(record["ted_note"]),
        "",
        "Canonical counters before and after: "
        + " / ".join(str(v) for v in record["CANONICAL_COUNTERS_AFTER"].values())
        + ".",
        "",
        "## Human review",
        "",
        f"`HUMAN_OUTPUT_REVIEW_REQUIRED = true`, `HUMAN_REVIEW_PACKET = "
        f"{record['HUMAN_REVIEW_PACKET']}`. {_sentence(record['human_review_note'])}",
        "",
        "**The approval is spent.** A further call needs a new operator approval naming a new "
        "packet digest, and the runner refuses V1's, V2's, V3's and V4's by name.",
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
        record = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    rendered = render(record)
    if args.write:
        RECORD_MD.write_bytes(rendered.encode("utf-8"))
        print(f"wrote    {RECORD_MD.name}")
        return 0
    if not RECORD_MD.exists() or RECORD_MD.read_text(encoding="utf-8") != rendered:
        print(f"FAIL     {RECORD_MD.name} is not the rendering of its record")
        return 1
    print(
        "ok       the V4 execution record matches its approval, its retained response and the runner"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
