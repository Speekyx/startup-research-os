"""Mission 1.84.15, CI gate 85. The one execution under packet V5, checked against what it kept.

The execution record says what happened; this gate re-derives it from what was retained. The raw
response digest is recomputed from the retained body and compared with the digest pinned here when
the record was written, the stop reason is read through the adapter's own classifier, the schema
verdict is recomputed by running the live v1.1.0 validator over the retained tool input, each length
violation is measured again and looked up in the prompt v1.4.0 system region, the cost is recomputed
from the reported usage at the held price, and the stage table is derived from those facts rather
than read.

The generation targets are measured too, for every composed text, and for diagnosis only: the gate
requires that the fields over a hard maximum are exactly the fields the schema refused, so a text over
its target and within its hard maximum can never have been the reason for a refusal, and a text over
its hard maximum always is.

The operator's approval is checked against the words it was given in, the digest it names, the
headroom policy it accepted and the prohibitions and residual-risk acceptance it carries. V1's to
V4's records are checked untouched, no human-review packet may exist for an answer a machine stage
refused, and the runner is asked whether it would execute V5 again.

    uv run python infrastructure/scripts/render_second_opportunity_execution_record_v5.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
from fractions import Fraction
from typing import Any

from sros_llm_gateway.pricing import ModelPrice
from sros_llm_gateway.providers.anthropic import (
    DEFAULT_ENDPOINT,
    STRUCTURED_TOOL_NAME,
    AnthropicCompletion,
    classify_forced_tool_completion,
)
from sros_opportunity.generation_headroom import (
    ARRAY_HEADROOM_POLICY,
    FIELD_ROLES,
    GENERATION_HEADROOM_POLICY,
    GENERATION_TARGET_RATIO,
    headroom_table,
    unstated_headroom,
)
from sros_opportunity.output_constraints import constraint_inventory, is_explicit
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
from sros_opportunity.second_opportunity_prompt_v1_3 import SECOND_OPPORTUNITY_SYSTEM_V1_3
from sros_opportunity.second_opportunity_prompt_v1_4 import SECOND_OPPORTUNITY_SYSTEM_V1_4

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

RECORD = DATA / "second-opportunity-synthesis-execution-record-v5.json"
RECORD_MD = DATA / "second-opportunity-synthesis-execution-record-v5.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v5.json"
RESPONSE = DATA / "second-opportunity-synthesis-response-v5.json"
REVIEW_PACKET = DATA / "second-opportunity-human-review-packet-v5.json"
PACKET_V5 = DATA / "second-opportunity-synthesis-execution-packet-v5.json"
RECORD_V1 = DATA / "second-opportunity-synthesis-execution-record-v1.json"
RECORD_V2 = DATA / "second-opportunity-synthesis-execution-record-v2.json"
RECORD_V3 = DATA / "second-opportunity-synthesis-execution-record-v3.json"
RECORD_V4 = DATA / "second-opportunity-synthesis-execution-record-v4.json"
RESPONSE_V3 = DATA / "second-opportunity-synthesis-response-v3.json"
RESPONSE_V4 = DATA / "second-opportunity-synthesis-response-v4.json"
APPROVAL_V4 = DATA / "second-opportunity-synthesis-execution-approval-v4.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v5.py"
PACKET_GATE = SCRIPTS / "render_second_opportunity_execution_packet_v5.py"

MISSION = "mission-1.84.15"
#: The merged main the mission started from, and the brief's 38 checks, all passed before the socket.
START_COMMIT = "dca098939fabd4b9ddc21ce69f4fad8a019e79ed"
BRANCH = "sprint-1/mission-1.84.15"
PRE_NETWORK_CHECKS: dict[str, object] = {"required": 38, "passed": 38, "problems": []}
V5_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V5"
V5_SHA256 = "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a"
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
#: V1's to V4's execution records, byte for byte as Missions 1.84.2, 1.84.7, 1.84.9 and 1.84.13 left
#: them, and V4's response and approval, which V5's record compares itself with.
V1_RECORD_SHA256 = "b769ddeb6ea4d4e773640c3ed83caeff52c52c857fd9125325140de4ab38c799"
V2_RECORD_SHA256 = "3fb8d5bae0cb2c64e165961518d9dfd3b1de98eef5244600ea0e5efc289001a7"
V3_RECORD_SHA256 = "abb093389664405f80878d2a1963beabfa4c271ed559437384146a92ccfb00a3"
V4_RECORD_SHA256 = "3e61c2d92df1184aac53f66e5c6e57fc9aeacb4aae4ebe9eb1c68bf774b10e1b"
V4_RESPONSE_SHA256 = "76ff8155062c44f727afc530e5a8d435d2bd70720bee524baeed0ee5f6e40205"
V4_APPROVAL_SHA256 = "c5cb608e4cf5aac6698ebec005658184e173518bb0ea719ba7e25185d5a73957"
#: What arrived and what authorised it, pinned when the record was written. An answer rewritten to
#: pass, with every digest recomputed to match, is still not the answer that arrived.
RAW_RESPONSE_SHA256 = "cd9ddf674a140bb0a6060e184209ab7d24a19efcc6c87a4b0cd73bc260e0e765"
PARSED_OUTPUT_SHA256 = "fc303141b2eb325c52a51466c3ad764fc541e0b4b7d05ba1c5a0f27ac019b177"
APPROVAL_FILE_SHA256 = "df2efd342c4962b1da2acebf6e9c3f4433677c8645112a83ebdb597d6b355873"
OPERATOR_STATEMENT_SHA256 = "60beeb267a28cd4dfa59880448a138efc5cfce108b9e2026f6be8b173551c082"
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
READY_FOR_HUMAN_REVIEW = "SECOND_OPPORTUNITY_SYNTHESIS_V5_READY_FOR_HUMAN_REVIEW"

#: The V5 runner's outcome codes, and the factual outcome the Mission 1.84.15 brief names for each.
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

#: What the operator's approval must still carry, verbatim, with a wrapped bullet joined by a space.
#: A refused answer is where each of these gets tempting.
REQUIRED_NOT_AUTHORISED = (
    "a second V5 provider request;",
    "any retry;",
    "retry after timeout;",
    "retry after provider refusal;",
    "retry after max_tokens;",
    "retry after parse failure;",
    "retry after schema failure;",
    "retry after semantic failure;",
    "retry after stage 7 failure;",
    "retry after stage 8 failure;",
    "retry after stage 9 failure;",
    "continuation;",
    '"finish the JSON";',
    "repair model;",
    "alternate Anthropic model;",
    "alternate provider;",
    "Message Batches;",
    "Claude subscription routing;",
    "adaptive thinking;",
    "web retrieval;",
    "external retrieval;",
    "new research acquisition;",
    "embeddings;",
    "scoring;",
    "ranking.",
)
REQUIRED_NO_REUSE = (
    "V1 re-execution;",
    "V2 re-execution;",
    "V3 re-execution;",
    "V4 re-execution;",
    "reuse of V1, V2, V3 or V4 approvals;",
    "restoration of any consumed approval.",
)
REQUIRED_UNCHANGED = (
    "schema v1.1.0;",
    "any maxLength;",
    "any maxItems;",
    "semantic gate v1.3.0;",
    "prompt v1.4.0 after execution begins;",
    "generation target ratio 4/5;",
    "array headroom NONE;",
    "TED representation;",
    "source-metadata evidence boundary;",
    "observed-statement atomicity;",
    "observed-disjunction policy;",
    "provider;",
    "route;",
    "model;",
    "thinking policy;",
    "max_tokens;",
    "timeout;",
    "cost ceiling.",
)
REQUIRED_SPECIFICALLY = (
    "raising maxLength 300 because V4 returned 316;",
    "raising maxLength 900 because V4 returned 1078;",
    "lowering information quality to hit a soft target;",
    "truncating output;",
    "rewriting output;",
    "summarizing output after generation;",
    "dropping fields;",
    "dropping statements;",
    "splitting statements after generation;",
    "changing classifications after generation.",
)
REQUIRED_RISK_EXCLUSIONS = (
    "treating source metadata as factual evidence;",
    "weakening ADR-040;",
    "weakening the source-metadata evidence-boundary decision;",
    "bypassing semantic validation;",
    "bypassing stage 9;",
    "skipping human review;",
    "automatic persistence.",
)
REQUIRED_UNDERSTOOD = (
    "the 4/5 target is prompt guidance only;",
    "it is not part of the output schema;",
    "it is not a validation bound;",
    "it is not a provider guarantee;",
    "it is not derived from V4's 316 or 1078 character outputs;",
    "a value above the generation target but at or below the hard schema maximum remains valid;",
    "a value above the hard schema maximum remains invalid.",
)
EXPIRY = "This acceptance expires with this one V5 inference attempt."

#: The canonical state before and after. Mission 1.84.15 may not move any of it.
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
    """The record disagrees with its approval, its retained response, V1 to V4, or the runner."""


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


# --------------------------------------------------------------------------- targets and bounds


def target_diagnostics(parsed: dict[str, Any]) -> list[dict[str, object]]:
    """Every composed text against its generation target and its hard maximum. Diagnostic only."""
    unstated = set(
        unstated_headroom(SECOND_OPPORTUNITY_SYSTEM_V1_4, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    )
    out: list[dict[str, object]] = []
    for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1):
        field, marker, rest = row.path.partition("[]")
        child = rest.lstrip(".")
        value = parsed.get(field)
        if marker:
            if not isinstance(value, list):
                raise ValidationError(f"{field} is not an array in the retained answer")
            texts = [item.get(child) if child else item for item in value]
        else:
            texts = [value]
        if not all(isinstance(text, str) for text in texts):
            raise ValidationError(f"{row.path} holds a value that is not text")
        lengths = [len(str(text)) for text in texts]
        out.append(
            {
                "field": row.path,
                "generation_target": row.generation_target,
                "hard_maximum": row.hard_maximum,
                "elements": len(lengths) if marker else None,
                "characters": lengths if marker else lengths[0],
                "longest": max(lengths, default=0),
                "over_target": sum(1 for n in lengths if n > row.generation_target),
                "over_hard_maximum": sum(1 for n in lengths if n > row.hard_maximum),
                "within_target": all(n <= row.generation_target for n in lengths),
                "within_hard_maximum": all(n <= row.hard_maximum for n in lengths),
                "target_stated_in_prompt_v1_4_0": row.path not in unstated,
            }
        )
    return out


def _max_length_constraint(field: str) -> Any:
    for constraint in constraint_inventory(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1):
        if constraint.path == field and constraint.keyword == "maxLength":
            return constraint
    raise ValidationError(f"the schema has no maxLength for {field!r}")


def violation_details(parsed: dict[str, Any], violations: list[str]) -> list[dict[str, object]]:
    """Each length violation measured again, beside its target and V4's and V3's lengths."""
    v4 = _load(RESPONSE_V4)["parsed_output"]
    v3 = _load(RESPONSE_V3)["parsed_output"]
    targets = {
        row.path: row.generation_target
        for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    }
    details: list[dict[str, object]] = []
    for violation in violations:
        match = _LENGTH_VIOLATION.match(violation)
        if match is None:
            raise ValidationError(
                f"this record describes an answer refused on a length bound, and the validator "
                f"reports {violation!r}"
            )
        field, length, bound = match.group(1), int(match.group(2)), int(match.group(3))
        text = parsed.get(field)
        if not isinstance(text, str) or len(text) != length:
            raise ValidationError(f"{field} is not {length} characters in the retained answer")
        if SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][field].get("maxLength") != bound:
            raise ValidationError(f"the live schema does not bound {field} at {bound}")
        if field not in targets:
            raise ValidationError(f"{field} has no generation target, and a composed text has one")
        constraint = _max_length_constraint(field)
        details.append(
            {
                "field": field,
                "characters": length,
                "maxLength": bound,
                "over_by": length - bound,
                "generation_target": targets[field],
                "over_target_by": length - targets[field],
                "stated_in_prompt_v1_4_0": is_explicit(constraint, SECOND_OPPORTUNITY_SYSTEM_V1_4),
                "stated_in_prompt_v1_3_0": is_explicit(constraint, SECOND_OPPORTUNITY_SYSTEM_V1_3),
                "target_stated_in_prompt_v1_4_0": field
                not in unstated_headroom(
                    SECOND_OPPORTUNITY_SYSTEM_V1_4, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
                ),
                "v4_characters": len(str(v4.get(field) or "")),
                "v3_characters": len(str(v3.get(field) or "")),
            }
        )
    return details


def _check_targets_never_decide(
    diagnostics: list[dict[str, object]], details: list[dict[str, object]]
) -> None:
    """The fields over a hard maximum are exactly the fields refused; a target decides nothing."""
    over_hard = {str(d["field"]) for d in diagnostics if not d["within_hard_maximum"]}
    refused = {str(d["field"]) for d in details}
    if over_hard != refused:
        raise ValidationError(
            f"the texts over a hard maximum are {sorted(over_hard)} and the schema refused "
            f"{sorted(refused)}: the hard schema, and nothing else, decides stage 5"
        )


# --------------------------------------------------------------------------- the packet


def _check_packet(record: dict[str, Any]) -> dict[str, Any]:
    packet = _load(PACKET_V5)
    digest = _module("packet_v5_gate_for_gate_85", PACKET_GATE).packet_digest(packet)
    if digest != V5_SHA256 or packet["EXECUTION_PACKET_SHA256"] != digest:
        raise ValidationError("the executed packet moved after it was approved")
    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
        raise ValidationError("the frozen packet was edited to record its own approval")
    if (
        Fraction(4, 5) != GENERATION_TARGET_RATIO
        or packet["GENERATION_TARGET_RATIO"] != GENERATION_HEADROOM_POLICY.ratio_text
        or packet["GENERATION_HEADROOM_POLICY"] != GENERATION_HEADROOM_POLICY.name
        or packet["ARRAY_HEADROOM_POLICY"] != ARRAY_HEADROOM_POLICY
    ):
        raise ValidationError("the headroom policy moved after V5 was approved")
    _fixed(
        record,
        {
            "execution_packet_id": V5_ID,
            "execution_packet_version": 5,
            "execution_packet_sha256": V5_SHA256,
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
            "START_COMMIT": START_COMMIT,
            "BRANCH": BRANCH,
            "EXECUTION_APPROVAL_CONSUMED": True,
            "FURTHER_CALLS_AUTHORIZED_BY_V5": False,
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
            "GENERATION_HEADROOM_POLICY": packet["GENERATION_HEADROOM_POLICY"],
            "GENERATION_TARGET_RATIO": packet["GENERATION_TARGET_RATIO"],
            "ARRAY_HEADROOM_POLICY": packet["ARRAY_HEADROOM_POLICY"],
            "GENERATION_HEADROOM_POLICY_DIGEST": packet["GENERATION_HEADROOM_POLICY_DIGEST"],
            "GENERATION_TARGETS_ALTER_VERDICT": False,
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
    _fixed(record["PRE_NETWORK_CHECKS"], PRE_NETWORK_CHECKS, "record.PRE_NETWORK_CHECKS")
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
        raise ValidationError("a canonical counter moved, and Mission 1.84.15 may move none")


# --------------------------------------------------------------------------- the approval


def _statement_bullets(lines: list[str]) -> set[str]:
    """The statement's bullets, a wrapped bullet joined back by a single space."""
    joined = "\n".join(lines).replace("\n  ", " ")
    return {line[2:] for line in joined.split("\n") if line.startswith("- ")}


def _check_approval(record: dict[str, Any], packet: dict[str, Any]) -> None:
    approval = _load(APPROVAL)
    block = record["OPERATOR_APPROVAL"]
    if _sha_file(APPROVAL) != APPROVAL_FILE_SHA256 or block["file_sha256"] != APPROVAL_FILE_SHA256:
        raise ValidationError("the approval changed after the execution record bound it")
    _fixed(
        approval,
        {
            "EXECUTION_PACKET_ID": V5_ID,
            "EXECUTION_PACKET_VERSION": 5,
            "EXECUTION_PACKET_SHA256": V5_SHA256,
            "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
            "recorded_by": MISSION,
            "EXECUTIONS_AUTHORISED": 1,
            "V1_APPROVAL_REUSED": False,
            "V2_APPROVAL_REUSED": False,
            "V3_APPROVAL_REUSED": False,
            "V4_APPROVAL_REUSED": False,
            "PACKET_V5_MODIFIED": False,
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
        V5_SHA256,
        "APPROVE_EXACTLY_ONE_EXECUTION",
        GENERATION_HEADROOM_POLICY.name,
        GENERATION_HEADROOM_POLICY.ratio_text,
        EXPIRY,
    ):
        if line not in lines:
            raise ValidationError(f"the recorded words no longer say {line!r}")
    stated = _statement_bullets(lines)
    headroom = approval["GENERATION_HEADROOM_POLICY_ACCEPTED"]
    risk = approval["RESIDUAL_RISK_ACCEPTED"]
    for name, required, present in (
        ("forbids", REQUIRED_NOT_AUTHORISED, approval["NOT_AUTHORISED"]),
        ("refuses to reuse", REQUIRED_NO_REUSE, approval["NO_PREVIOUS_EXECUTION_REUSED"]),
        ("withholds a change to", REQUIRED_UNCHANGED, approval["NO_CHANGE_APPROVED_TO"]),
        ("specifically forbids", REQUIRED_SPECIFICALLY, approval["SPECIFICALLY_NOT_AUTHORISED"]),
        ("keeps outside the residual risk", REQUIRED_RISK_EXCLUSIONS, risk["DOES_NOT_AUTHORISE"]),
        ("accepts about the target", REQUIRED_UNDERSTOOD, headroom["UNDERSTOOD_AND_ACCEPTED"]),
    ):
        missing = [item for item in required if item not in set(present) or item not in stated]
        if missing:
            raise ValidationError(f"the approval no longer {name} {missing}")
    if (
        risk["for"] != "this one V5 inference attempt"
        or risk["EXPIRES_WITH_THIS_ATTEMPT"] is not True
    ):
        raise ValidationError(
            "the residual-risk acceptance is no longer bounded to this one attempt"
        )
    roles = {role.field: role.intent for role in FIELD_ROLES}
    _fixed(
        headroom,
        {
            "policy": GENERATION_HEADROOM_POLICY.name,
            "ratio": GENERATION_HEADROOM_POLICY.ratio_text,
            "FIELD_ROLES_APPROVED": roles,
            "AUTHORISES_REMOVING_NECESSARY_INFORMATION": False,
        },
        "approval.GENERATION_HEADROOM_POLICY_ACCEPTED",
    )
    for field, intent in roles.items():
        if f"{field} =" not in lines or lines[lines.index(f"{field} =") + 1] != intent:
            raise ValidationError(f"the operator's words no longer approve {intent} for {field}")
    if not str(approval.get("approved_by") or "").strip():
        raise ValidationError("the approval names no approver")
    _fixed(
        block,
        {
            "decision": approval["decision"],
            "approved_by": approval["approved_by"],
            "recorded_by": MISSION,
            "RESIDUAL_RISK_ACCEPTED_FOR_THIS_EXECUTION": True,
            "RESIDUAL_RISK_ACCEPTANCE_EXPIRED": True,
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
            "generation_headroom_policy": packet["GENERATION_HEADROOM_POLICY"],
            "generation_target_ratio": packet["GENERATION_TARGET_RATIO"],
            "array_headroom_policy": packet["ARRAY_HEADROOM_POLICY"],
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
            "execution_packet_id": V5_ID,
            "execution_packet_sha256": V5_SHA256,
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
    details = violation_details(parsed, violations)
    if details != record["SCHEMA_VIOLATION_DETAILS"]:
        raise ValidationError("the recorded violation details are not what the answer measures")
    diagnostics = target_diagnostics(parsed)
    if diagnostics != record["GENERATION_TARGET_DIAGNOSTICS"]:
        raise ValidationError(
            "the recorded generation-target diagnostics are not what the answer measures"
        )
    _check_targets_never_decide(diagnostics, details)
    if record["HARD_SCHEMA_VERDICT"] != ("FAILED" if violations else "PASSED"):
        raise ValidationError("the recorded hard-schema verdict is not the validator's")
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
        ("V4", RECORD_V4, V4_RECORD_SHA256, "V4_EXECUTION_RECORD_SHA256", V4_SHA256),
    ):
        if _sha_file(path) != pinned or record[key] != pinned:
            raise ValidationError(f"{label}'s historical execution record was edited")
        historical = _load(path)
        if historical.get("EXECUTION_APPROVAL_CONSUMED") is not True:
            raise ValidationError(f"{label}'s consumption was reset")
        if historical.get("execution_packet_sha256") != digest:
            raise ValidationError(f"{label}'s record names another digest")
    for label, path, pinned in (
        ("V4's response", RESPONSE_V4, V4_RESPONSE_SHA256),
        ("V4's approval", APPROVAL_V4, V4_APPROVAL_SHA256),
    ):
        if _sha_file(path) != pinned:
            raise ValidationError(f"{label} was edited")


def _check_runner() -> None:
    runner = _module("execution_runner_v5_for_gate_85", RUNNER)
    for label, digest in (
        ("V5", V5_SHA256),
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
    if runner.EXECUTION_RECORD_V5.name != RECORD.name or runner.RESPONSE_ARTIFACT.name != (
        RESPONSE.name
    ):
        raise ValidationError("the runner reads V5's consumption or response from somewhere else")


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
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_record_v5.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _sentence(text: object) -> str:
    value = str(text).strip()
    return value if value.endswith((".", "!", "?")) else value + "."


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _yes(value: object) -> str:
    return "yes" if value else "no"


def _returned(row: dict[str, Any]) -> str:
    if row["elements"] is None:
        return str(row["characters"])
    lengths = ", ".join(str(n) for n in row["characters"])
    return f"{lengths} ({row['elements']} elements)"


def render(record: dict[str, Any]) -> str:
    usage = record["ACTUAL_USAGE"]
    cost = record["ACTUAL_COST"]
    approval = record["OPERATOR_APPROVAL"]
    kept = record["RESPONSE_ARTIFACT"]
    timing = record["timing"]
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: synthesis execution record v5",
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
                f"headroom policy        {record['GENERATION_HEADROOM_POLICY']}, ratio "
                f"{record['GENERATION_TARGET_RATIO']}, arrays {record['ARRAY_HEADROOM_POLICY']}",
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
        "## The bound that refused it",
        "",
        "| field | characters | hard maximum | over by | target | over target by | V4 | V3 |",
        "|---|---|---|---|---|---|---|---|",
        *[
            f"| `{d['field']}` | {d['characters']} | {d['maxLength']} | {d['over_by']} | "
            f"{d['generation_target']} | {d['over_target_by']} | {d['v4_characters']} | "
            f"{d['v3_characters']} |"
            for d in record["SCHEMA_VIOLATION_DETAILS"]
        ],
        "",
        _sentence(record["schema_note"]),
        "",
        "## Generation targets, for diagnosis only",
        "",
        "| composed text | target | hard maximum | returned characters | within target | "
        "within hard maximum |",
        "|---|---|---|---|---|---|",
        *[
            f"| `{row['field']}` | {row['generation_target']} | {row['hard_maximum']} | "
            f"{_returned(row)} | {_yes(row['within_target'])} | "
            f"{_yes(row['within_hard_maximum'])} |"
            for row in record["GENERATION_TARGET_DIAGNOSTICS"]
        ],
        "",
        _sentence(record["generation_target_note"]),
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
        "**The approval is spent**, and with it the residual-risk acceptance, which expired with "
        "this one attempt. A further call needs a new operator approval naming a new packet digest, "
        "and the runner refuses V1's, V2's, V3's, V4's and V5's by name.",
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
        "ok       the V5 execution record matches its approval, its retained response and the runner"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
