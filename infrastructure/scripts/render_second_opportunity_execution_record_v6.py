"""Mission 1.84.18, CI gate 91. The one execution under packet V6, checked against what it kept.

The execution record says what happened; this gate re-derives it from what was retained. The raw
response digest is recomputed from the retained body and compared with the digest pinned here when the
record was written, the stop reason is read through the adapter's own classifier, the schema verdict is
recomputed by running the live v1.2.0 validator over the retained tool input, each violation is
measured again (a length against its bound, an unknown field against the closed object), the cost is
recomputed from the reported usage at the held price, and the stage table is derived from those facts
rather than read.

The generation targets are measured too, for every composed text, and for diagnosis only: the gate
requires that the texts over a hard maximum are exactly the texts refused on a length, so a text over
its target and within its hard maximum can never have been the reason for a refusal.

The operator's approval is checked against the words it was given in, the digest it names, the
process-deviation acceptance and the residual-risk acceptance it carries, and the prohibitions it
lists. V1's to V5's artifacts are checked untouched against the digests gate 87 pins, no human-review
packet may exist for an answer a machine stage refused, and the runner is asked whether it would
execute V6 again. The record file itself is pinned last, after every rule has had its say.

    uv run python infrastructure/scripts/render_second_opportunity_execution_record_v6.py --check
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
    GENERATION_HEADROOM_POLICY,
    GENERATION_TARGET_RATIO,
    headroom_table,
    unstated_headroom,
)
from sros_opportunity.output_constraints import constraint_inventory, is_explicit
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
from sros_opportunity.second_opportunity_prompt_v1_5 import SECOND_OPPORTUNITY_SYSTEM_V1_5
from sros_opportunity.second_opportunity_schema_v1_2 import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

RECORD = DATA / "second-opportunity-synthesis-execution-record-v6.json"
RECORD_MD = DATA / "second-opportunity-synthesis-execution-record-v6.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v6.json"
RESPONSE = DATA / "second-opportunity-synthesis-response-v6.json"
REVIEW_PACKET = DATA / "second-opportunity-human-review-packet-v6.json"
PACKET_V6 = DATA / "second-opportunity-synthesis-execution-packet-v6.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v6.py"
PACKET_GATE = SCRIPTS / "render_second_opportunity_execution_packet_v6.py"
FREEZE_GATE = SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"

MISSION = "mission-1.84.18"
#: The merged main the mission started from, and the operator's 50 checks, all passed before the socket.
START_COMMIT = "24f12ff69c83c1ca59724dbab2859e330a5ade75"
BRANCH = "sprint-1/mission-1.84.18"
PRE_NETWORK_CHECKS: dict[str, object] = {"required": 50, "passed": 50, "problems": []}
V6_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V6"
V6_SHA256 = "969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9"
V5_SHA256 = "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a"
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
SPENT = {"V1": V1_SHA256, "V2": V2_SHA256, "V3": V3_SHA256, "V4": V4_SHA256, "V5": V5_SHA256}
#: What arrived and what authorised it, pinned when the record was written. An answer rewritten to
#: pass, with every digest recomputed to match, is still not the answer that arrived.
RAW_RESPONSE_SHA256 = "4c63becd5ff62436d30bf9d3f16406935fd8b63a69764835dbb746a67e6e940c"
PARSED_OUTPUT_SHA256 = "e8332db816337e94fd35c0b4ad39f073f4b2cf1372f5c47fbf6a132827e7b824"
RESPONSE_FILE_SHA256 = "e8a13d7da4be4167162f4e45a1dc5328bbd550493386fe5dd58069897d0879c4"
APPROVAL_FILE_SHA256 = "dfe8a9e69c7dfcbbcc8dcf6f849b3b22b1a93230db2f38e03f0f76eaf4701553"
OPERATOR_STATEMENT_SHA256 = "c6b6602c32815b2325c5dcc23733638567b64d2abb531ca4a5c17c23de775973"
#: The record itself, pinned once it was written. Checked last, so every rule speaks first.
RECORD_FILE_SHA256 = "77f4f27dc72d39a58175e61132b81178d85e7fefc85e7fd669c8bac438c1e6a4"
TED_REPRESENTATION_BYTES = 3604
PRICE = ModelPrice(input_per_1k=0.002, output_per_1k=0.01)
SECRET = re.compile(r"sk-ant-[A-Za-z0-9_\-]{6,}|sk-[A-Za-z0-9]{16,}")
SUMMARY = "evidence_bound_reasoning_summary"

STAGES = (
    "1_transport_success",
    "2_provider_response_shape",
    "3_provider_completion",
    "4_structured_output_parse",
    "5_schema_validation_v1_2_0",
    "6_semantic_output_gate_v1_4_0",
    "7_evidence_boundary_and_no_distortion",
    "8_attribution_and_provenance",
    "9_persistence_eligibility",
    "10_human_review",
)

ACCEPTED = "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
READY_FOR_HUMAN_REVIEW = "SECOND_OPPORTUNITY_SYNTHESIS_V6_READY_FOR_HUMAN_REVIEW"

#: The V6 runner's outcome codes, and the factual outcome the Mission 1.84.18 brief names for each.
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
    "any second V6 inference;",
    "any retry;",
    "any fallback;",
    "any continuation;",
    "any repair-model call;",
    '"finish the JSON";',
    "post-processing to rescue the output;",
    "truncation;",
    "summarization;",
    "string shortening after generation;",
    "statement deletion;",
    "statement splitting;",
    "classification rewriting;",
    "source-reference rewriting;",
    "schema changes;",
    "semantic-gate changes;",
    "prompt changes;",
    "headroom-policy changes;",
    "another provider;",
    "another Anthropic model;",
    "Message Batches;",
    "Claude subscription routing;",
    "adaptive thinking;",
    "web retrieval;",
    "external retrieval;",
    "additional research acquisition;",
    "training;",
    "fine-tuning;",
    "embeddings;",
    "scoring;",
    "ranking;",
    "re-execution of V1, V2, V3, V4 or V5;",
    "reuse of any previous approval;",
    "restoration of any consumed approval;",
    "revalidation of V5 as a candidate under schema v1.2.0;",
    "automatic persistence of Opportunity #2.",
)
REQUIRED_CONTRACT_UNDERSTOOD = (
    "1500 is an operator semantic-budget judgement;",
    "it was not mathematically derived;",
    "it was not statistically estimated from V3, V4 or V5;",
    "it is not claimed optimal;",
    "V1 through V5 remain historically tied to their original contracts;",
    "V5 MUST NOT be revalidated into a candidate under schema v1.2.0.",
)
REQUIRED_GATE_INTENT = (
    "use output schema v1.2.0 for structural validation;",
    "preserve every non-structural semantic behaviour of v1.3.0;",
    "preserve assertion-context semantics;",
    "preserve denial semantics;",
    "preserve source-origin semantics;",
    "preserve source-metadata policy;",
    "preserve lexical-inflection policy;",
    "preserve OBSERVED atomicity;",
    "preserve OBSERVED disjunction policy;",
    "preserve commercial-claim boundaries;",
    "preserve MARKET_ACTIVITY semantics;",
    "preserve BT-161 semantics;",
    "preserve trusted-context semantics.",
)
REQUIRED_DEVIATION_ACKNOWLEDGED = (
    "gate v1.4.0 reached final content before V6 preparation;",
    "its freeze commit 402a698f695241801d9cd61fd9f5d444ebb16221 was committed before the V6 "
    "artifacts;",
    "that commit contains no V6-path artifact;",
    "its initial push failed;",
    "the failure was initially misread;",
    "therefore the freeze commit did not exist on the remote before V6 artifacts were prepared;",
    "it reached the remote only with the mission's final push;",
    "a prompt-v1.5 draft also existed locally before the freeze pins were written;",
    "no frozen gate byte changed afterward;",
    "the V6 packet binds the freeze commit, freeze record and frozen-test digest.",
)
REQUIRED_DEVIATION_BECAUSE = (
    "the freeze commit is an ancestor of the dependent V6 artifacts;",
    "its tree contains no V6-path files;",
    "frozen gate content did not move;",
    "all dependencies and digests are now present on merged main;",
    "the packet cryptographically binds the frozen predecessor state.",
)
REQUIRED_RISK_BECAUSE = (
    "source metadata is explicitly not factual support;",
    "prompt v1.5 communicates that rule;",
    "stages 6 through 9 remain mandatory;",
    "OpportunityHypothesis construction is performed in memory at stage 9;",
    "stage 10 human review remains mandatory;",
    "canonical persistence is not automatically authorized.",
)
REQUIRED_LINES = (
    "I APPROVE THE FOLLOWING EXECUTION EXACTLY AS FROZEN.",
    V6_SHA256,
    "APPROVE_EXACTLY_ONE_EXECUTION",
    "PROCESS_DEVIATION_ACCEPTED_FOR_V6 = true",
    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6 = true",
    "This acceptance applies ONLY to V6.",
    "It is NOT a precedent.",
    "This acceptance expires after the one V6 inference attempt.",
    "It does NOT pre-authorize persistence.",
    "Do not edit packet V6 to record approval.",
)

#: The canonical state before and after. Mission 1.84.18 may not move any of it.
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
_UNKNOWN_FIELD = re.compile(r"^<root>: unknown field '(.+)'; additionalProperties is false$")


class ValidationError(RuntimeError):
    """The record disagrees with its approval, its retained response, V1 to V5, or the runner."""


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


def _history() -> dict[pathlib.Path, str]:
    """V1's to V5's packets, approvals, records and responses, by the digests gate 87 pins."""
    pins = _module("freeze_gate_for_gate_91", FREEZE_GATE).HISTORY_SHA256
    return {ROOT / relative: digest for relative, digest in pins.items()}


#: Resolved at load, and read through the module at check time so a test can point one at a copy.
HISTORY: dict[pathlib.Path, str] = _history()


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
        unstated_headroom(SECOND_OPPORTUNITY_SYSTEM_V1_5, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    )
    out: list[dict[str, object]] = []
    for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2):
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
                "target_stated_in_prompt_v1_5_0": row.path not in unstated,
            }
        )
    return out


def reasoning_summary(parsed: dict[str, Any]) -> dict[str, object]:
    """The summary against the operator's 1500 and its 1200 target, and against the historical 900."""
    text = parsed.get(SUMMARY)
    if not isinstance(text, str):
        raise ValidationError("the retained answer carries no reasoning summary text")
    hard = int(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["properties"][SUMMARY]["maxLength"])
    target = next(
        row.generation_target
        for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
        if row.path == SUMMARY
    )
    historical = int(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][SUMMARY]["maxLength"])
    return {
        "characters": len(text),
        "generation_target": target,
        "hard_maximum": hard,
        "within_target": len(text) <= target,
        "within_hard_maximum": len(text) <= hard,
        "v1_1_0_hard_maximum": historical,
        "over_the_v1_1_0_hard_maximum": len(text) > historical,
        "v1_1_0_verdict_applies": False,
    }


def historical_contract_diagnostic(parsed: dict[str, Any]) -> dict[str, object]:
    """The retained answer through schema v1.1.0, as a fact about the old contract, never a verdict."""
    return {
        "schema": "second-opportunity-synthesis-output@1.1.0",
        "violations": list(schema_violations(dict(parsed), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)),
        "IS_A_VERDICT": False,
    }


def _max_length_constraint(field: str) -> Any:
    for constraint in constraint_inventory(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2):
        if constraint.path == field and constraint.keyword == "maxLength":
            return constraint
    raise ValidationError(f"the schema has no maxLength for {field!r}")


def violation_details(parsed: dict[str, Any], violations: list[str]) -> list[dict[str, object]]:
    """Each violation measured again against the live v1.2.0 schema and the answer that arrived."""
    targets = {
        row.path: row.generation_target
        for row in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    }
    properties = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["properties"]
    details: list[dict[str, object]] = []
    for violation in violations:
        unknown = _UNKNOWN_FIELD.match(violation)
        length = _LENGTH_VIOLATION.match(violation)
        if unknown is not None:
            name = unknown.group(1)
            if name not in parsed:
                raise ValidationError(f"the retained answer carries no field {name!r}")
            if name in properties:
                raise ValidationError(f"{name!r} is a declared field of schema v1.2.0")
            if SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2.get("additionalProperties") is not False:
                raise ValidationError("schema v1.2.0 is no longer a closed object")
            details.append(
                {
                    "kind": "UNKNOWN_FIELD",
                    "path": "<root>",
                    "field": name,
                    "value": parsed[name],
                    "position_in_tool_input": list(parsed).index(name),
                    "declared_in_schema_v1_2_0": False,
                    "additional_properties_allowed": False,
                    "declared_fields_all_present": all(key in parsed for key in properties),
                }
            )
        elif length is not None:
            field, chars, bound = length.group(1), int(length.group(2)), int(length.group(3))
            text = parsed.get(field)
            if not isinstance(text, str) or len(text) != chars:
                raise ValidationError(f"{field} is not {chars} characters in the retained answer")
            if properties[field].get("maxLength") != bound:
                raise ValidationError(f"the live schema does not bound {field} at {bound}")
            if field not in targets:
                raise ValidationError(
                    f"{field} has no generation target, and a composed text has one"
                )
            details.append(
                {
                    "kind": "LENGTH",
                    "field": field,
                    "characters": chars,
                    "maxLength": bound,
                    "over_by": chars - bound,
                    "generation_target": targets[field],
                    "over_target_by": chars - targets[field],
                    "stated_in_prompt_v1_5_0": is_explicit(
                        _max_length_constraint(field), SECOND_OPPORTUNITY_SYSTEM_V1_5
                    ),
                }
            )
        else:
            raise ValidationError(
                f"a violation of a kind this record does not describe: {violation!r}"
            )
    return details


def _check_targets_never_decide(
    diagnostics: list[dict[str, object]], details: list[dict[str, object]]
) -> None:
    """The texts over a hard maximum are exactly the texts refused on a length; a target decides nothing."""
    over_hard = {str(d["field"]) for d in diagnostics if not d["within_hard_maximum"]}
    refused = {str(d["field"]) for d in details if d["kind"] == "LENGTH"}
    if over_hard != refused:
        raise ValidationError(
            f"the texts over a hard maximum are {sorted(over_hard)} and the schema refused "
            f"{sorted(refused)} on a length: the hard schema, and nothing else, decides stage 5"
        )


# --------------------------------------------------------------------------- the packet


def _check_packet(record: dict[str, Any]) -> dict[str, Any]:
    packet = _load(PACKET_V6)
    digest = _module("packet_v6_gate_for_gate_91", PACKET_GATE).packet_digest(packet)
    if digest != V6_SHA256 or packet["EXECUTION_PACKET_SHA256"] != digest:
        raise ValidationError("the executed packet moved after it was approved")
    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
        raise ValidationError("the frozen packet was edited to record its own approval")
    if (
        Fraction(4, 5) != GENERATION_TARGET_RATIO
        or packet["GENERATION_TARGET_RATIO"] != GENERATION_HEADROOM_POLICY.ratio_text
        or packet["GENERATION_HEADROOM_POLICY"] != GENERATION_HEADROOM_POLICY.name
        or packet["ARRAY_HEADROOM_POLICY"] != ARRAY_HEADROOM_POLICY
    ):
        raise ValidationError("the headroom policy moved after V6 was approved")
    _fixed(
        record,
        {
            "execution_packet_id": V6_ID,
            "execution_packet_version": 6,
            "execution_packet_sha256": V6_SHA256,
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
            "FURTHER_CALLS_AUTHORIZED_BY_V6": False,
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
            "REASONING_SUMMARY_HARD_MAX": packet["REASONING_SUMMARY_HARD_MAX"],
            "REASONING_SUMMARY_GENERATION_TARGET": packet["REASONING_SUMMARY_GENERATION_TARGET"],
            "OUTPUT_GATE_VERSION": packet["OUTPUT_GATE_VERSION"],
            "SEMANTIC_GATE_IMPLEMENTATION_SHA256": packet["SEMANTIC_GATE_IMPLEMENTATION_SHA256"],
            "SEMANTIC_GATE_FROZEN_TEST_SHA256": packet["SEMANTIC_GATE_FROZEN_TEST_SHA256"],
            "SEMANTIC_GATE_FREEZE_COMMIT": packet["SEMANTIC_GATE_FREEZE_COMMIT"],
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
        raise ValidationError("a canonical counter moved, and Mission 1.84.18 may move none")


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
            "EXECUTION_PACKET_ID": V6_ID,
            "EXECUTION_PACKET_VERSION": 6,
            "EXECUTION_PACKET_SHA256": V6_SHA256,
            "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
            "recorded_by": MISSION,
            "EXECUTIONS_AUTHORISED": 1,
            "EXACT_BOUND_ARTIFACTS_ONLY": True,
            "PROCESS_DEVIATION_ACCEPTED_FOR_V6": True,
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6": True,
            "V1_APPROVAL_REUSED": False,
            "V2_APPROVAL_REUSED": False,
            "V3_APPROVAL_REUSED": False,
            "V4_APPROVAL_REUSED": False,
            "V5_APPROVAL_REUSED": False,
            "PACKET_V6_MODIFIED": False,
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
    for line in REQUIRED_LINES:
        if line not in lines:
            raise ValidationError(f"the recorded words no longer say {line!r}")
    stated = _statement_bullets(lines)
    deviation = approval["PROCESS_DEVIATION_ACCEPTANCE"]
    risk = approval["RESIDUAL_RISK_ACCEPTANCE"]
    for name, required, present in (
        ("forbids", REQUIRED_NOT_AUTHORISED, approval["NOT_AUTHORISED"]),
        (
            "understands about the contract",
            REQUIRED_CONTRACT_UNDERSTOOD,
            approval["OUTPUT_CONTRACT_SUCCESSOR_APPROVED"]["UNDERSTOOD"],
        ),
        (
            "approves as the gate's intent",
            REQUIRED_GATE_INTENT,
            approval["SEMANTIC_GATE_V1_4_APPROVED"]["APPROVED_SEMANTIC_INTENT"],
        ),
        (
            "acknowledges about the deviation",
            REQUIRED_DEVIATION_ACKNOWLEDGED,
            deviation["ACKNOWLEDGED"],
        ),
        (
            "accepts the deviation because",
            REQUIRED_DEVIATION_BECAUSE,
            deviation["ACCEPTED_BECAUSE"],
        ),
        (
            "accepts the residual risk only because",
            REQUIRED_RISK_BECAUSE,
            risk["ACCEPTED_ONLY_BECAUSE"],
        ),
    ):
        missing = [item for item in required if item not in set(present) or item not in stated]
        if missing:
            raise ValidationError(f"the approval no longer {name} {missing}")
    _fixed(
        deviation,
        {
            "for": "execution packet V6 only",
            "PRECEDENT": False,
            "EXPIRES_WITH_V6_EXECUTION_AUTHORITY": True,
            "INHERITABLE_BY_A_FUTURE_PACKET": False,
        },
        "approval.PROCESS_DEVIATION_ACCEPTANCE",
    )
    _fixed(
        risk,
        {
            "for": "this one V6 inference attempt",
            "PRE_AUTHORISES_PERSISTENCE": False,
            "EXPIRES_WITH_THIS_ATTEMPT": True,
            "INHERITABLE_BY_A_FUTURE_PACKET": False,
        },
        "approval.RESIDUAL_RISK_ACCEPTANCE",
    )
    if (
        approval["SEMANTIC_GATE_V1_4_APPROVED"]["GATE_MODIFICATION_AFTER_APPROVAL_AUTHORISED"]
        is not False
    ):
        raise ValidationError("the approval is recorded as authorising a gate modification")
    if approval["OUTPUT_CONTRACT_SUCCESSOR_APPROVED"]["V5_REVALIDATED_UNDER_V1_2_0"] is not False:
        raise ValidationError("the approval is recorded as revalidating V5 under schema v1.2.0")
    if not str(approval.get("approved_by") or "").strip():
        raise ValidationError("the approval names no approver")
    _fixed(
        block,
        {
            "decision": approval["decision"],
            "approved_by": approval["approved_by"],
            "recorded_by": MISSION,
            "PROCESS_DEVIATION_ACCEPTED_FOR_V6": True,
            "PROCESS_DEVIATION_ACCEPTANCE_EXPIRED": True,
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
            "reasoning_summary_hard_max": packet["REASONING_SUMMARY_HARD_MAX"],
            "reasoning_summary_generation_target": packet["REASONING_SUMMARY_GENERATION_TARGET"],
            "generation_headroom_policy": packet["GENERATION_HEADROOM_POLICY"],
            "generation_target_ratio": packet["GENERATION_TARGET_RATIO"],
            "array_headroom_policy": packet["ARRAY_HEADROOM_POLICY"],
            "semantic_gate": packet["OUTPUT_GATE_VERSION"],
            "semantic_gate_implementation_sha256": packet["SEMANTIC_GATE_IMPLEMENTATION_SHA256"],
            "semantic_gate_frozen_test_sha256": packet["SEMANTIC_GATE_FROZEN_TEST_SHA256"],
            "semantic_gate_freeze_commit": packet["SEMANTIC_GATE_FREEZE_COMMIT"],
            "semantic_gate_freeze_record_sha256": packet["SEMANTIC_GATE_FREEZE_RECORD_SHA256"],
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
        "the retained answer passes the v1.2.0 schema, so its later stages need the evidence packet "
        "and the frozen gate; this record describes an answer refused at stage 5"
    )


def _check_response(record: dict[str, Any], packet: dict[str, Any]) -> None:
    artifact = _load(RESPONSE)
    kept = record["RESPONSE_ARTIFACT"]
    if _sha_file(RESPONSE) != kept["file_sha256"] or kept["file_sha256"] != RESPONSE_FILE_SHA256:
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
            "execution_packet_id": V6_ID,
            "execution_packet_sha256": V6_SHA256,
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

    violations = list(schema_violations(dict(parsed), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2))
    if violations != record["SCHEMA_VIOLATIONS"]:
        raise ValidationError(
            "the recorded schema violations are not what the live v1.2.0 validator finds in the "
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
    if reasoning_summary(parsed) != record["REASONING_SUMMARY"]:
        raise ValidationError(
            "the recorded reasoning-summary lengths are not what the answer measures"
        )
    if historical_contract_diagnostic(parsed) != record["HISTORICAL_CONTRACT_DIAGNOSTIC"]:
        raise ValidationError(
            "the recorded schema v1.1.0 diagnostic is not what the old validator finds, or it is "
            "recorded as a verdict"
        )
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
    history = HISTORY
    if len(history) != 18:
        raise ValidationError(f"gate 87 pins {len(history)} historical artifacts, not 18")
    for path, pinned in history.items():
        if _sha_file(path) != pinned:
            raise ValidationError(f"{path.name}, a V1 to V5 artifact, was edited")
    for label, digest in SPENT.items():
        key = f"{label}_EXECUTION_RECORD_SHA256"
        path = next(p for p in history if p.name.endswith(f"execution-record-{label.lower()}.json"))
        if record[key] != history[path]:
            raise ValidationError(f"the record does not bind {label}'s execution record as pinned")
        historical = _load(path)
        if historical.get("EXECUTION_APPROVAL_CONSUMED") is not True:
            raise ValidationError(f"{label}'s consumption was reset")
        if historical.get("execution_packet_sha256") != digest:
            raise ValidationError(f"{label}'s record names another digest")


def _check_runner() -> None:
    runner = _module("execution_runner_v6_for_gate_91", RUNNER)
    for label, digest in (("V6", V6_SHA256), *reversed(list(SPENT.items()))):
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
    if (
        runner.EXECUTION_RECORD_V6.name != RECORD.name
        or runner.RESPONSE_ARTIFACT.name != RESPONSE.name
        or runner.APPROVAL_FILE.name != APPROVAL.name
    ):
        raise ValidationError("the runner reads V6's consumption, response or approval elsewhere")


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
    if _sha_file(RECORD) != RECORD_FILE_SHA256:
        raise ValidationError("the execution record changed after it was written and pinned")
    return record


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_record_v6.py "
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


def _detail(row: dict[str, Any]) -> str:
    if row["kind"] == "UNKNOWN_FIELD":
        return (
            f"| unknown field | `{row['field']}` | `{json.dumps(row['value'])}` | position "
            f"{row['position_in_tool_input']} in the tool input; not declared by schema v1.2.0, "
            "which is a closed object |"
        )
    return (
        f"| length | `{row['field']}` | {row['characters']} characters | hard maximum "
        f"{row['maxLength']}, over by {row['over_by']} |"
    )


def render(record: dict[str, Any]) -> str:
    usage = record["ACTUAL_USAGE"]
    cost = record["ACTUAL_COST"]
    approval = record["OPERATOR_APPROVAL"]
    kept = record["RESPONSE_ARTIFACT"]
    timing = record["timing"]
    summary = record["REASONING_SUMMARY"]
    historical = record["HISTORICAL_CONTRACT_DIAGNOSTIC"]
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: synthesis execution record v6",
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
                f"process deviation      accepted for V6: "
                f"{str(approval['PROCESS_DEVIATION_ACCEPTED_FOR_V6']).lower()}, expired: "
                f"{str(approval['PROCESS_DEVIATION_ACCEPTANCE_EXPIRED']).lower()}",
                f"residual semantic risk accepted for this execution: "
                f"{str(approval['RESIDUAL_RISK_ACCEPTED_FOR_THIS_EXECUTION']).lower()}, expired: "
                f"{str(approval['RESIDUAL_RISK_ACCEPTANCE_EXPIRED']).lower()}",
                f"route                  {record['ROUTE']} ({record['ROUTE_KIND']})",
                f"model                  {record['MODEL']} (response: {record['RESPONSE_MODEL']})",
                f"thinking               {record['THINKING_POLICY']}, "
                f"{json.dumps(record['THINKING_REQUEST_VALUE'])}",
                f"max_tokens             {record['MAX_TOKENS']}",
                f"timeout                {record['REQUEST_TIMEOUT_SECONDS']} s",
                f"prompt                 {record['PROMPT_VERSION']} {record['PROMPT_SHA256']}",
                f"schema                 {record['OUTPUT_SCHEMA_VERSION']} "
                f"{record['OUTPUT_SCHEMA_SHA256']}",
                f"summary bound/target   {record['REASONING_SUMMARY_HARD_MAX']} / "
                f"{record['REASONING_SUMMARY_GENERATION_TARGET']}",
                f"semantic gate          {record['OUTPUT_GATE_VERSION']} "
                f"{record['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}",
                f"gate freeze commit     {record['SEMANTIC_GATE_FREEZE_COMMIT']}",
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
        "live v1.2.0 validator reports:",
        "",
        *[f"- `{violation}`" for violation in record["SCHEMA_VIOLATIONS"]],
        "",
        "A stage that was not reached is not a stage that passed: the semantic gate, the evidence "
        "boundary, attribution and persistence eligibility never judged this answer.",
        "",
        "## What refused it",
        "",
        "| kind | field | returned | against schema v1.2.0 |",
        "|---|---|---|---|",
        *[_detail(row) for row in record["SCHEMA_VIOLATION_DETAILS"]],
        "",
        _sentence(record["schema_note"]),
        "",
        "## The reasoning summary",
        "",
        *_code(
            [
                f"characters             {summary['characters']}",
                f"generation target      {summary['generation_target']} "
                f"(within: {_yes(summary['within_target'])})",
                f"hard maximum           {summary['hard_maximum']} "
                f"(within: {_yes(summary['within_hard_maximum'])})",
                f"schema v1.1.0 bound    {summary['v1_1_0_hard_maximum']} "
                f"(over it: {_yes(summary['over_the_v1_1_0_hard_maximum'])}; "
                "not the V6 contract)",
            ]
        ),
        _sentence(record["historical_note"]),
        "",
        "Through schema v1.1.0, for the record only: "
        + "; ".join(f"`{v}`" for v in historical["violations"])
        + ".",
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
        "**The approval is spent**, and with it the process-deviation acceptance and the residual-risk "
        "acceptance, which expired with this one attempt. A further call needs a new operator "
        "approval naming a new packet digest, and the runner refuses V1's to V6's by name.",
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
        "ok       the V6 execution record matches its approval, its retained response and the runner"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
