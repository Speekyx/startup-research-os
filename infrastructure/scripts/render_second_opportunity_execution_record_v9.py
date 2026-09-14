"""Mission 1.84.22, CI gate 98. The one execution under packet V9, checked against what it kept.

The execution record says what happened; this gate re-derives it from what was retained. The raw
response digest is recomputed from the retained body and compared with the digest pinned here when the
record was written, the stop reason is read through the adapter's own classifier, the full v1.2.0
validator runs again over the retained tool input, the cost is recomputed from the usage the provider
reported at the held price and checked against the hard ceiling, and every billed category the usage
reports is checked against the assumptions the ceiling was proven under.

Stages 6 to 10 judge the answer against the evidence packet, and CI holds no database. They are re-run
from Mission 1.84.10's authenticated snapshot: the snapshot must rebuild V9's representation, rendered
prompt, trusted context and source-metadata channel, digest for digest, before the V9 runner's own
`validate_execution` judges the retained answer again under a transport tripwire, and its verdict must
be the one the execution retained, reason for reason. Each semantic refusal is then measured against
the answer: a term refused as unsupported must be in the refused text and in no supplied statement, and
an item refused as not request-shaped must not be request-shaped.

The operator's approval is checked against the words it was given in, the digest it names, both of V9's
risk acceptances and the prohibitions it lists. V1 to V6 are held to gate 91, V7 and V8 to their
supersession records, no human-review packet may exist for an answer a machine stage refused, and the
runner is asked whether it would execute V9 again: its guard must refuse the digest as spent, and
`--execute` must stop before any transport. The record file itself is pinned last.

    uv run python infrastructure/scripts/render_second_opportunity_execution_record_v9.py --check
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import sys
from decimal import Decimal
from typing import Any

from sros_llm_gateway.pricing import ModelPrice
from sros_llm_gateway.providers.anthropic import (
    DEFAULT_ENDPOINT,
    STRUCTURED_TOOL_NAME,
    AnthropicCompletion,
    classify_forced_tool_completion,
)
from sros_opportunity.assertion_context import is_request_shaped
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity_prompt_v1_5 import SECOND_OPPORTUNITY_SYSTEM_V1_5
from sros_opportunity.second_opportunity_schema_v1_2 import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-synthesis-execution-record-v9.json"
RECORD_MD = DATA / "second-opportunity-synthesis-execution-record-v9.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v9.json"
RESPONSE = DATA / "second-opportunity-synthesis-response-v9.json"
REVIEW_PACKET = DATA / "second-opportunity-human-review-packet-v9.json"
PACKET_V9 = DATA / "second-opportunity-synthesis-execution-packet-v9.json"
#: Mission 1.84.10's snapshot of the selected packet, which rebuilds V9's inputs with no database.
SNAPSHOT_RECORD = DATA / "second-opportunity-v3-diagnostic-replay-v1.json"
SUPERSESSION = {
    "V7": DATA / "second-opportunity-synthesis-execution-supersession-v7.json",
    "V8": DATA / "second-opportunity-synthesis-execution-supersession-v8.json",
}
#: What V7 or V8 would have left behind had either been approved or run. Neither may exist.
NEVER_RUN = {
    label: [
        DATA / f"second-opportunity-synthesis-execution-approval-{label.lower()}.json",
        DATA / f"second-opportunity-synthesis-execution-record-{label.lower()}.json",
        DATA / f"second-opportunity-synthesis-response-{label.lower()}.json",
    ]
    for label in ("V7", "V8")
}
RUNNER = SCRIPTS / "run_second_opportunity_execution_v9.py"
PACKET_GATE = SCRIPTS / "render_second_opportunity_execution_packet_v9.py"
RECORD_GATE_V6 = SCRIPTS / "render_second_opportunity_execution_record_v6.py"
REPLAY_GATE = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"

MISSION = "mission-1.84.22"
#: The merged main the mission started from, and the operator's 58 checks, all passed before the socket.
START_COMMIT = "5426643d50449a323d416d666486d6cf599a151a"
BRANCH = "sprint-1/mission-1.84.22"
PRE_NETWORK_CHECKS: dict[str, object] = {"required": 58, "passed": 58, "problems": []}
V9_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V9"
V9_SHA256 = "ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d"
V8_SHA256 = "583946460c6cf68c1be5519916f92d268e36ed65924aeb24901731439586c399"
V7_SHA256 = "51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8"
V6_SHA256 = "969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9"
SPENT = {
    "V1": "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92",
    "V2": "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e",
    "V3": "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2",
    "V4": "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b",
    "V5": "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a",
    "V6": V6_SHA256,
}
CONSUMED = "EXECUTION_APPROVAL_ALREADY_CONSUMED"
SUPERSEDED = "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
#: What arrived and what authorised it, pinned when the record was written. An answer rewritten to
#: pass, with every digest recomputed to match, is still not the answer that arrived.
RAW_RESPONSE_SHA256 = "4fe8da9662636e4ffbbf11d41a528968215ba9cbd97bbb0a3727425628be10ac"
PARSED_OUTPUT_SHA256 = "f6ce54b2bd942f6a0eddd10805244ccaf6aa51cffd8870bcdfbe8c3e655ec2c2"
RESPONSE_FILE_SHA256 = "f129e8edba6bbf0bb8c4d182888a9ecdc7f34f4f4ca9dce09a3377cfdc4b6bdd"
APPROVAL_FILE_SHA256 = "86f73a61ca8178be3a43708c5e775789c5ffc5a7bb32187f032c8f188ab59854"
OPERATOR_STATEMENT_SHA256 = "de5ee683f0e6a1c64bdc20e04be78a681609e03e8267a1b7754539b4b226c17b"
OPERATOR_MESSAGE_SHA256 = "5eade97cac43eea9ecb8d5258dd1796668d9e5f29ed61ee70d3d8f071999e51c"
SNAPSHOT_RECORD_SHA256 = "43ec43831229bd7afc91910bbe371c275f4c1f3a1f4663332b49d90d50f8fb15"
#: The record itself, pinned once it was written. Checked last, so every rule speaks first.
RECORD_FILE_SHA256 = "6b2eeba732df1f5ecf7ed52032625d3ab0204cee2f1ee935663fa25bfcf3ea61"
TED_REPRESENTATION_BYTES = 3604
PRICE = ModelPrice(input_per_1k=0.002, output_per_1k=0.01)
SECRET = re.compile(r"sk-ant-[A-Za-z0-9_\-]{6,}|sk-[A-Za-z0-9]{16,}")
#: The residency values the provider documents (CI gate 94, D12 line 307). The ceiling already carries
#: the 1.1 multiplier `us` incurs, so either is within it, and any other value is a category it never
#: priced.
INFERENCE_GEOS = ("us", "global")

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
READY_FOR_HUMAN_REVIEW = "SECOND_OPPORTUNITY_SYNTHESIS_V9_READY_FOR_HUMAN_REVIEW"

#: The V9 runner's outcome codes, and the terminal outcome the Mission 1.84.22 brief names for each.
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

#: Lines the operator's approval must still carry, verbatim.
REQUIRED_LINES = (
    "I APPROVE THE FOLLOWING EXECUTION EXACTLY AS FROZEN.",
    V9_SHA256,
    "APPROVE_EXACTLY_ONE_EXECUTION",
    "No second inference is authorized.",
    "V7 and V8 were never approved, executed or consumed.",
    "Do not execute V7 or V8.",
    "Do not reuse any previous approval.",
    "For THIS V9 execution only:",
    "This acceptance expires after the one V9 inference attempt.",
    "It does NOT authorize persistence.",
    "I explicitly accept that the one authorized V9 attempt may still time out.",
    "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
    "and the approval is consumed.",
    "No second request is authorized.",
    "is an estimate only and is NOT the ceiling.",
    "for actual cost.",
    "Do not modify packet V9.",
)
REQUIRED_RISK_BECAUSE = (
    "provider strict mode addresses structural shape, not semantic truth;",
    "canonical schema v1.2.0 remains mandatory at stage 5;",
    "semantic gate v1.4.0 remains mandatory at stage 6;",
    "evidence-boundary validation remains mandatory at stage 7;",
    "attribution/provenance remains mandatory at stage 8;",
    "canonical persistence eligibility remains mandatory at stage 9;",
    "human review remains mandatory;",
    "no automatic persistence is authorized.",
)
REQUIRED_TIMEOUT_IS_NOT = (
    "a provider-guaranteed response-time bound;",
    "a guarantee that compilation plus generation completes in time;",
    "a statistical latency estimate;",
    "a reason to retry.",
)
REQUIRED_NOT_AUTHORISED = (
    "retry",
    "fallback",
    "continuation",
    "repair request",
    "alternate provider",
    "alternate model",
    "alternate route",
    "schema change",
    "semantic-gate change",
    "prompt change",
    "strict-projection change",
    "timeout change",
    "post-processing",
    "automatic persistence",
)

#: What prompt v1.5.0 tells the model, in its own words, about the rules gate v1.4.0 applied here.
PROMPT_RULES = {
    "prior_knowledge_unavailable": (
        "Your prior knowledge about the subject is UNAVAILABLE as factual support"
    ),
    "next_evidence_names_what_would_be_observed": (
        "`recommended_next_evidence` names what would have to be OBSERVED"
    ),
    "each_request_states_no_finding": (
        "each item names the evidence or observation that would have to be obtained, and states "
        "no finding"
    ),
    "no_wording_of_confirmation": (
        "no adverb of certainty and no wording of confirmation turns one into a conclusion"
    ),
}

#: The canonical state before and after. Mission 1.84.22 may not move any of it.
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

_AUDITED = re.compile(r"^([a-z_]+)(?:\[(\d+)\])? audited ([A-Z_]+): (.*)$", re.S)
_UNSUPPORTED_TERM = re.compile(r"^'([^']+)' appears in no source content statement")
_NOT_REQUEST_SHAPED = "it is not request-shaped, so it is read as the assertion it has become"
_PROMOTED = re.compile(r"\[([^\]]*)\] promote a FUTURE_EVIDENCE_REQUEST to a conclusion")


class ValidationError(RuntimeError):
    """The record disagrees with its approval, its response, the replay, V1 to V8, or the runner."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


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


def _fixed(block: Any, expected: dict[str, object], where: str) -> None:
    if not isinstance(block, dict):
        raise ValidationError(f"{where} is {block!r}; the record must carry the block itself")
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


#: Gate 91 holds V1 to V6; gate 97 recomputes V9's digest; gate 76 carries the snapshot machinery.
G91 = _module("gate_91_for_gate_98", RECORD_GATE_V6)
G97 = _module("gate_97_for_gate_98", PACKET_GATE)
G76 = _module("gate_76_for_gate_98", REPLAY_GATE)


def runner() -> Any:
    return _module("execution_runner_v9_for_gate_98", RUNNER)


# --------------------------------------------------------------------------- measured facts


def target_diagnostics(parsed: dict[str, Any]) -> list[dict[str, object]]:
    """Every composed text against its generation target and hard maximum, as gate 91 measures it."""
    try:
        diagnostics: list[dict[str, object]] = G91.target_diagnostics(parsed)
    except G91.ValidationError as exc:
        raise ValidationError(str(exc)) from exc
    return diagnostics


def reasoning_summary(parsed: dict[str, Any]) -> dict[str, object]:
    try:
        summary: dict[str, object] = G91.reasoning_summary(parsed)
    except G91.ValidationError as exc:
        raise ValidationError(str(exc)) from exc
    return summary


def usage_facts(usage: dict[str, Any]) -> dict[str, object]:
    """The usage block's figures, as the provider reported them."""
    tokens_in, tokens_out = int(usage["input_tokens"]), int(usage["output_tokens"])
    return {
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "total_tokens": tokens_in + tokens_out,
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "thinking_tokens": (usage.get("output_tokens_details") or {}).get("thinking_tokens"),
        "service_tier": usage.get("service_tier"),
        "inference_geo": usage.get("inference_geo"),
    }


def billed_categories(usage: dict[str, Any]) -> dict[str, object]:
    """Every billed category the usage block reports, beside the one multiplier it can trigger."""
    return {
        "service_tier": usage.get("service_tier"),
        "inference_geo": usage.get("inference_geo"),
        "us_only_multiplier_applies": usage.get("inference_geo") == "us",
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "cache_creation": usage.get("cache_creation"),
        "thinking_tokens": (usage.get("output_tokens_details") or {}).get("thinking_tokens"),
    }


def billing_contradictions(usage: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    """Each observed billed category the proven ceiling does not assume. Any one fails closed."""
    found: list[str] = []
    if usage.get("service_tier") != "standard":
        found.append(
            f"service_tier {usage.get('service_tier')!r}: the ceiling prices the standard tier, "
            "and claude-sonnet-5 is documented outside Priority Tier"
        )
    if usage.get("inference_geo") not in INFERENCE_GEOS:
        found.append(
            f"inference_geo {usage.get('inference_geo')!r}: the provider documents only "
            f"{' and '.join(INFERENCE_GEOS)}, and the ceiling carries the multiplier for both"
        )
    for key in ("cache_creation_input_tokens", "cache_read_input_tokens"):
        if usage.get(key) not in (0, None):
            found.append(
                f"{key} {usage.get(key)}: the request sets no cache_control, and the ceiling "
                "prices no cache write or read"
            )
    creation = usage.get("cache_creation")
    if isinstance(creation, dict):
        found += [
            f"cache_creation.{key} {value}: the ceiling prices no cache write"
            for key, value in creation.items()
            if value not in (0, None)
        ]
    thinking = (usage.get("output_tokens_details") or {}).get("thinking_tokens")
    if thinking not in (0, None):
        found.append(f"thinking_tokens {thinking}: thinking is disabled, and none is priced")
    if int(usage["input_tokens"]) > int(packet["MAX_BILLABLE_INPUT_TOKENS"]):
        found.append("input tokens over the documented context window the ceiling bounds them by")
    if int(usage["output_tokens"]) > int(packet["MAX_OUTPUT_TOKENS"]):
        found.append("output tokens over the max_tokens the ceiling bounds them by")
    return found


def _decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def actual_cost(usage: dict[str, Any], packet: dict[str, Any]) -> dict[str, object]:
    """The cost the reported usage implies at the held price, exact, with residency applied."""
    price = packet["PRICE_PER_1K"]
    geo_us = usage.get("inference_geo") == "us"
    multiplier = Decimal(str(packet["DATA_RESIDENCY_MULTIPLIER"])) if geo_us else Decimal(1)
    thousand = Decimal(1000)
    cost_in = Decimal(int(usage["input_tokens"])) * Decimal(str(price["input"])) / thousand
    cost_out = Decimal(int(usage["output_tokens"])) * Decimal(str(price["output"])) / thousand
    return {
        "cost_units": _decimal((cost_in + cost_out) * multiplier),
        "input_cost_units": _decimal(cost_in * multiplier),
        "output_cost_units": _decimal(cost_out * multiplier),
        "residency_multiplier": _decimal(multiplier),
        "pricing_version": packet["PRICING_VERSION"],
        "priced": True,
        "source": "the provider's usage block in the retained response, at the held price",
    }


def prompt_statements() -> dict[str, bool]:
    """Whether prompt v1.5.0 states each rule in words, its lines wrapped or not."""
    flat = " ".join(SECOND_OPPORTUNITY_SYSTEM_V1_5.split())
    return {key: " ".join(text.split()) in flat for key, text in PROMPT_RULES.items()}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _text_at(parsed: dict[str, Any], field: str, index: int | None) -> str:
    value = parsed.get(field)
    if index is None:
        if not isinstance(value, str):
            raise ValidationError(f"{field} is not text in the retained answer")
        return value
    if not isinstance(value, list) or index >= len(value) or not isinstance(value[index], str):
        raise ValidationError(f"{field}[{index}] is not text in the retained answer")
    return str(value[index])


def semantic_details(
    parsed: dict[str, Any], statements: dict[str, str], reasons: list[str]
) -> list[dict[str, object]]:
    """Each stage 6 refusal, measured again against the answer that arrived and the statements."""
    details: list[dict[str, object]] = []
    for reason in reasons:
        match = _AUDITED.match(reason)
        if match is None:
            raise ValidationError(
                f"a semantic refusal of a kind this record does not describe: {reason!r}"
            )
        field, index, verdict, rest = match.groups()
        position = int(index) if index is not None else None
        text = _text_at(parsed, field, position)
        path = f"{field}[{position}]" if position is not None else field
        unsupported = _UNSUPPORTED_TERM.match(rest)
        if verdict == "UNSUPPORTED" and unsupported is not None:
            term = unsupported.group(1)
            if term.lower() not in _words(text):
                raise ValidationError(f"{path} does not carry the word {term!r} it was refused on")
            if any(term.lower() in _words(statement) for statement in statements.values()):
                raise ValidationError(
                    f"{term!r} is in a supplied statement, so it was not unsupported"
                )
            details.append(
                {
                    "field": path,
                    "verdict": verdict,
                    "kind": "UNSUPPORTED_TERM",
                    "term": term,
                    "text": text,
                    "characters": len(text),
                    "term_in_the_refused_text": True,
                    "term_in_any_supplied_statement": False,
                }
            )
        elif verdict == "BOUND_EXCEEDED" and rest.startswith(_NOT_REQUEST_SHAPED):
            if is_request_shaped(text):
                raise ValidationError(f"{path} is request-shaped, and it was refused as not")
            promoted = _PROMOTED.search(rest)
            words = (
                [w.strip(" '\"") for w in promoted.group(1).split(",")]
                if promoted is not None
                else []
            )
            absent = [w for w in words if w.lower() not in _words(text)]
            if absent:
                raise ValidationError(f"{path} does not carry {absent}, which it was refused on")
            details.append(
                {
                    "field": path,
                    "verdict": verdict,
                    "kind": "NOT_REQUEST_SHAPED",
                    "text": text,
                    "characters": len(text),
                    "first_word": text.split()[0] if text.split() else "",
                    "request_shaped": False,
                    "confirmation_words": words,
                }
            )
        else:
            raise ValidationError(
                f"a semantic refusal of a kind this record does not describe: {reason!r}"
            )
    return details


# --------------------------------------------------------------------------- the replay


def snapshot_packet() -> tuple[Any, dict[str, str], dict[str, str]]:
    """The selected packet, its statements and its boundary, from the authenticated snapshot."""
    if _sha_file(SNAPSHOT_RECORD) != SNAPSHOT_RECORD_SHA256:
        raise ValidationError("the snapshot Mission 1.84.10 authenticated was edited")
    snapshot = _load(SNAPSHOT_RECORD)["PACKET_SNAPSHOT"]
    packet, statements, evidence_to_claim = G76.packet_from_snapshot(snapshot)
    return packet, statements, evidence_to_claim


def replay(
    response: dict[str, Any], packet_file: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, str], dict[str, object]]:
    """Stages 1 to 10 over the retained answer, re-run by the V9 runner with no database."""
    from sros_opportunity import (
        ExternalSynthesisDecision,
        SynthesisAvailability,
        serialize_packet_for_model,
    )
    from sros_opportunity.second_opportunity_gate_v1_2 import build_trusted_context
    from sros_opportunity.second_opportunity_prompt_v1_5 import (
        render_second_opportunity_prompt_v1_5,
        second_opportunity_prompt_hash_v1_5,
    )

    packet, statements, evidence_to_claim = snapshot_packet()
    module = runner()
    measurement = ExternalSynthesisDecision(
        availability=SynthesisAvailability.AVAILABLE,
        packet_id=packet.packet_id,
        refusal_reasons=(),
        per_source=(("ted-eu", "RECOMPUTED_FOR_THE_V9_RECORD"),),
    )
    representation = _sha_text(serialize_packet_for_model(packet, measurement, statements))
    metadata = module.source_metadata_for(list(packet.source_ids))
    parts = render_second_opportunity_prompt_v1_5(
        packet, statements, evidence_to_claim, source_metadata=metadata
    )
    trusted = build_trusted_context(packet)
    found: dict[str, object] = {
        "representation_sha256": representation,
        "prompt_sha256": second_opportunity_prompt_hash_v1_5(parts),
        "trusted_context_sha256": trusted.digest(),
        "source_metadata_sha256": metadata.digest(),
    }
    bound = {
        "representation_sha256": packet_file["REPRESENTATION_SHA256"],
        "prompt_sha256": packet_file["PROMPT_SHA256"],
        "trusted_context_sha256": packet_file["TRUSTED_CONTEXT_SHA256"],
        "source_metadata_sha256": packet_file["SOURCE_METADATA_CONTEXT_SHA256"],
    }
    for key, value in bound.items():
        if found[key] != value:
            raise ValidationError(
                f"the snapshot rebuilds {key} {found[key]}, not V9's {value}: it is not the packet "
                "V9 sent"
            )
    boundary = {
        eid: evidence_to_claim[eid] for eid in packet.evidence_ids if eid in evidence_to_claim
    }
    if (
        packet.packet_id != packet_file["SELECTED_PACKET_ID"]
        or list(packet.evidence_ids) != packet_file["APPROVED_EVIDENCE_IDS"]
        or list(packet.claim_ids) != packet_file["APPROVED_CLAIM_IDS"]
        or boundary != packet_file["APPROVED_EVIDENCE_TO_CLAIM"]
    ):
        raise ValidationError("the snapshot's evidence boundary is not the one V9 approved")
    context = {
        "packet_file": packet_file,
        "packet": packet,
        "statements": statements,
        "evidence_to_claim": evidence_to_claim,
        "trusted_context": trusted,
        "source_metadata": metadata,
        "representation": representation,
        "prompt_hash": found["prompt_sha256"],
    }
    with G76.no_transport():
        report: dict[str, Any] = module.validate_execution(
            G76.reconstructed_result(response), context
        )
    return report, statements, found


def _derived_stages(
    completion: AnthropicCompletion,
    blocks: list[dict[str, Any]],
    violations: list[str],
    report: dict[str, Any],
) -> tuple[dict[str, str], str | None]:
    """The stage table: stages 1 to 5 from the facts, and from 6 the replay, which must agree."""
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
    stages[STAGES[4]] = "PASSED"
    replayed = report["stages"]
    if any(replayed.get(name) != stages[name] for name in STAGES[:5]):
        raise ValidationError("the replay disagrees with the retained facts about stages 1 to 5")
    for name in STAGES[5:]:
        stages[name] = replayed[name]
    return stages, report.get("failed_stage")


def _no_pass_after_failure(stages: dict[str, str]) -> None:
    failed = False
    for name in STAGES:
        verdict = stages[name]
        if failed and verdict != "NOT_REACHED":
            raise ValidationError(
                f"{name} is {verdict} after an earlier stage failed; a stage that was not reached is "
                "NOT_REACHED, never passed"
            )
        failed = failed or verdict == "FAILED"


# --------------------------------------------------------------------------- the packet and record


def _check_packet(record: dict[str, Any]) -> dict[str, Any]:
    packet = _load(PACKET_V9)
    try:
        digest = G97.packet_digest(packet)
    except G97.ValidationError as exc:
        raise ValidationError(str(exc)) from exc
    if digest != V9_SHA256 or packet["EXECUTION_PACKET_SHA256"] != digest:
        raise ValidationError("the executed packet moved after it was approved")
    for key in (
        "OPERATOR_EXECUTION_APPROVAL_RECORDED",
        "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9",
        "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9",
    ):
        if packet[key] is not False:
            raise ValidationError(f"the frozen packet was edited to record {key}")
    if packet["PROVIDER_ROUTE_SURFACE"] != f"POST {DEFAULT_ENDPOINT}":
        raise ValidationError("the packet's route is not the synchronous Messages API")
    _fixed(
        record,
        {
            "execution_packet_id": V9_ID,
            "execution_packet_version": 9,
            "execution_packet_sha256": V9_SHA256,
        },
        "record",
    )
    return packet


def _check_record(record: dict[str, Any], packet: dict[str, Any]) -> None:
    _fixed(
        record,
        {
            "recorded_by": MISSION,
            "START_COMMIT": START_COMMIT,
            "BRANCH": BRANCH,
            "EXECUTION_APPROVAL_CONSUMED": True,
            "FURTHER_CALLS_AUTHORIZED_BY_V9": False,
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
            "PROVIDER_STRICT_MODE": True,
            "STRUCTURED_OUTPUT_MECHANISM": packet["STRUCTURED_OUTPUT_MECHANISM"],
            "PROVIDER_STRICT_SCHEMA_ID": packet["PROVIDER_STRICT_SCHEMA_ID"],
            "PROVIDER_STRICT_SCHEMA_SHA256": packet["PROVIDER_STRICT_SCHEMA_SHA256"],
            "STRICT_CAPABILITY_PROFILE_ID": packet["STRICT_CAPABILITY_PROFILE_ID"],
            "STRICT_CAPABILITY_PROFILE_SHA256": packet["STRICT_CAPABILITY_PROFILE_SHA256"],
            "STRICT_PROJECTION_FREEZE_COMMIT": packet["STRICT_PROJECTION_FREEZE_COMMIT"],
            "MAX_TOKENS": packet["MAX_OUTPUT_TOKENS"],
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "REQUEST_BODY_CHARACTERS": packet["REQUEST_BODY_CHARACTERS"],
            "REQUEST_BODY_SHA256": packet["REQUEST_BODY_SHA256"],
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
            "PLANNING_COST_ESTIMATE": packet["PLANNING_COST_ESTIMATE"],
            "PLANNING_INPUT_TOKEN_ESTIMATE": packet["PLANNING_INPUT_TOKEN_ESTIMATE"],
            "HARD_EXECUTION_COST_CEILING": packet["HARD_EXECUTION_COST_CEILING"],
            "HARD_EXECUTION_COST_CEILING_PROVEN": True,
            "HUMAN_OUTPUT_REVIEW_REQUIRED": True,
            "CANONICAL_PERSISTENCE": False,
            "OPPORTUNITY_PERSISTED": False,
            "CANONICAL_MUTATIONS": 0,
            "NOT_REACHED_IS_NOT_PASSED": True,
            "CREDENTIAL_VALUES_RECORDED": False,
            "TED_BYTES_SENT": TED_REPRESENTATION_BYTES,
            "TED_REPRESENTATION_CHARACTERS": packet["REPRESENTATION_CHARACTER_COUNT"],
            "TED_REPRESENTATION_SHA256": packet["REPRESENTATION_SHA256"],
        },
        "record",
    )
    if packet["HARD_EXECUTION_COST_CEILING_PROVEN"] is not True:
        raise ValidationError("the packet no longer records its hard ceiling as proven")
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
        raise ValidationError("a canonical counter moved, and Mission 1.84.22 may move none")


# --------------------------------------------------------------------------- the approval


def _check_approval(record: dict[str, Any], packet: dict[str, Any]) -> None:
    approval = _load(APPROVAL)
    block = record["OPERATOR_APPROVAL"]
    if (
        _sha_file(APPROVAL) != APPROVAL_FILE_SHA256
        or block.get("file_sha256") != APPROVAL_FILE_SHA256
    ):
        raise ValidationError("the approval changed after the execution record bound it")
    _fixed(
        approval,
        {
            "EXECUTION_PACKET_ID": V9_ID,
            "EXECUTION_PACKET_VERSION": 9,
            "EXECUTION_PACKET_SHA256": V9_SHA256,
            "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
            "recorded_by": MISSION,
            "EXECUTIONS_AUTHORISED": 1,
            "EXACT_BOUND_ARTIFACTS_ONLY": True,
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9": True,
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9": True,
            "V9_ONLY": True,
            "INHERITABLE_BY_FUTURE_PACKET": False,
            **{f"{label}_APPROVAL_REUSED": False for label in SPENT},
            "V7_EXECUTED": False,
            "V8_EXECUTED": False,
            "PACKET_V9_MODIFIED": False,
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
    if not (
        _sha_text(joined)
        == approval["operator_statement_sha256"]
        == block.get("operator_statement_sha256")
        == OPERATOR_STATEMENT_SHA256
    ):
        raise ValidationError("the operator's words changed after their digest was recorded")
    if not (
        approval["OPERATOR_MESSAGE"]["sha256"]
        == block.get("operator_message_sha256")
        == OPERATOR_MESSAGE_SHA256
    ):
        raise ValidationError("the operator's message is not the one the approval was drawn from")
    for line in REQUIRED_LINES:
        if line not in lines:
            raise ValidationError(f"the recorded words no longer say {line!r}")
    stated = {line[2:] for line in lines if line.startswith("- ")}
    risk = approval["RESIDUAL_RISK_ACCEPTANCE"]
    timeout = approval["TIMEOUT_RISK_ACCEPTANCE"]
    for name, required, present in (
        (
            "accepts the residual risk only because",
            REQUIRED_RISK_BECAUSE,
            risk["ACCEPTED_ONLY_BECAUSE"],
        ),
        (
            "says the 240 seconds are not",
            REQUIRED_TIMEOUT_IS_NOT,
            timeout["THE_240_SECONDS_ARE_NOT"],
        ),
    ):
        missing = [item for item in required if item not in set(present) or item not in stated]
        if missing:
            raise ValidationError(f"the approval no longer {name} {missing}")
    missing = [item for item in REQUIRED_NOT_AUTHORISED if item not in approval["NOT_AUTHORISED"]]
    if missing or approval["NOT_AUTHORISED_STATEMENT"] not in " ".join(lines):
        raise ValidationError(
            f"the approval no longer forbids {missing or 'what its words forbid'}"
        )
    _fixed(
        risk,
        {
            "for": "this one V9 inference attempt",
            "PRE_AUTHORISES_PERSISTENCE": False,
            "EXPIRES_WITH_THIS_ATTEMPT": True,
            "V9_ONLY": True,
            "INHERITABLE_BY_FUTURE_PACKET": False,
        },
        "approval.RESIDUAL_RISK_ACCEPTANCE",
    )
    _fixed(
        timeout,
        {
            "for": "this one V9 inference attempt",
            "MAY_STILL_TIME_OUT_ACCEPTED": True,
            "ON_TIMEOUT": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
            "APPROVAL_CONSUMED_ON_TIMEOUT": True,
            "SECOND_REQUEST_AUTHORISED": False,
            "V9_ONLY": True,
            "INHERITABLE_BY_FUTURE_PACKET": False,
        },
        "approval.TIMEOUT_RISK_ACCEPTANCE",
    )
    _fixed(
        timeout["ACKNOWLEDGED"],
        {
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "PROVIDER_GRAMMAR_COMPILATION_TIMEOUT_SECONDS": packet["TIMEOUT"][
                "PROVIDER_COMPILATION_TIMEOUT_SECONDS"
            ],
            "STRICT_GRAMMAR_COMPILATION_LATENCY": "NOT_ESTABLISHED",
            "END_TO_END_LATENCY_BOUND": "NOT_ESTABLISHED",
            "TIMEOUT_RISK_ELIMINATED": False,
            "MAX_RETRIES": 0,
        },
        "approval.TIMEOUT_RISK_ACCEPTANCE.ACKNOWLEDGED",
    )
    _fixed(
        approval["COST_RISK_ACCEPTANCE"],
        {
            "HARD_EXECUTION_COST_CEILING": packet["HARD_EXECUTION_COST_CEILING"],
            "PLANNING_COST_ESTIMATE": packet["PLANNING_COST_ESTIMATE"],
            "PLANNING_ESTIMATE_IS_THE_CEILING": False,
            "ACTUAL_USAGE_AND_COST_MUST_BE_RETAINED": True,
            "CEILING_EVER_SUBSTITUTED_FOR_ACTUAL_COST": False,
            "UNAVAILABLE_FIGURE_REPORTED_AS": "NOT_ESTABLISHED",
        },
        "approval.COST_RISK_ACCEPTANCE",
    )
    if not str(approval.get("approved_by") or "").strip():
        raise ValidationError("the approval names no approver")
    _fixed(
        block,
        {
            "decision": approval["decision"],
            "approved_by": approval["approved_by"],
            "recorded_by": MISSION,
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9": True,
            "RESIDUAL_RISK_ACCEPTANCE_EXPIRED": True,
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9": True,
            "TIMEOUT_RISK_ACCEPTANCE_EXPIRED": True,
            "V9_ONLY": True,
            "INHERITABLE_BY_FUTURE_PACKET": False,
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
            "provider_strict_mode": packet["PROVIDER_STRICT_MODE"],
            "provider_strict_mechanism": packet["STRUCTURED_OUTPUT_MECHANISM"],
            "provider_strict_projection": packet["PROVIDER_STRICT_SCHEMA_ID"],
            "provider_strict_projection_sha256": packet["PROVIDER_STRICT_SCHEMA_SHA256"],
            "capability_profile": packet["STRICT_CAPABILITY_PROFILE_ID"],
            "capability_profile_sha256": packet["STRICT_CAPABILITY_PROFILE_SHA256"],
            "strict_projection_freeze_commit": packet["STRICT_PROJECTION_FREEZE_COMMIT"],
            "output_schema": packet["OUTPUT_SCHEMA_VERSION"],
            "output_schema_sha256": packet["OUTPUT_SCHEMA_SHA256"],
            "semantic_gate": packet["OUTPUT_GATE_VERSION"],
            "semantic_gate_implementation_sha256": packet["SEMANTIC_GATE_IMPLEMENTATION_SHA256"],
            "prompt": f"{packet['PROMPT_ID']}@{packet['PROMPT_VERSION']}",
            "prompt_sha256": packet["PROMPT_SHA256"],
            "representation_sha256": packet["REPRESENTATION_SHA256"],
            "representation_characters": packet["REPRESENTATION_CHARACTER_COUNT"],
            "reasoning_summary_hard_max": packet["REASONING_SUMMARY_HARD_MAX"],
            "reasoning_summary_generation_target": packet["REASONING_SUMMARY_GENERATION_TARGET"],
            "generation_target_ratio": packet["GENERATION_TARGET_RATIO"],
            "MAX_OUTPUT_TOKENS": packet["MAX_OUTPUT_TOKENS"],
            "MAX_MODEL_CALLS": packet["MAX_MODEL_CALLS"],
            "MAX_RETRIES": packet["MAX_RETRIES"],
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "REQUEST_BODY_CHARACTERS": packet["REQUEST_BODY_CHARACTERS"],
            "REQUEST_BODY_SHA256": packet["REQUEST_BODY_SHA256"],
            "PLANNING_COST_ESTIMATE": packet["PLANNING_COST_ESTIMATE"],
            "HARD_EXECUTION_COST_CEILING": packet["HARD_EXECUTION_COST_CEILING"],
            "HARD_EXECUTION_COST_CEILING_PROVEN": packet["HARD_EXECUTION_COST_CEILING_PROVEN"],
            "HUMAN_OUTPUT_REVIEW_REQUIRED": True,
            "CANONICAL_PERSISTENCE_AUTOMATICALLY_AUTHORIZED": False,
        },
        "approval.APPROVED_EXECUTION",
    )


# --------------------------------------------------------------------------- the response


def _check_response(record: dict[str, Any], packet: dict[str, Any]) -> None:
    artifact = _load(RESPONSE)
    kept = record["RESPONSE_ARTIFACT"]
    if (
        _sha_file(RESPONSE) != kept.get("file_sha256")
        or kept.get("file_sha256") != RESPONSE_FILE_SHA256
    ):
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
            "execution_packet_id": V9_ID,
            "execution_packet_sha256": V9_SHA256,
            "PROVIDER_STRICT_MODE": True,
            "PROVIDER_STRICT_SCHEMA_SHA256": packet["PROVIDER_STRICT_SCHEMA_SHA256"],
        },
        "response",
    )
    if record["POST_CALL_FALLBACK_USED"] is not ("POST_CALL_HANDLING_FAILED" in artifact):
        raise ValidationError("the record misstates whether the post-call fail-safe was used")

    body = artifact["RAW_PROVIDER_RESPONSE_BODY"]
    if not isinstance(body, dict) or not isinstance(body.get("content"), list):
        raise ValidationError("the retained response is not the provider's message object")
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    if not (
        _sha_text(raw)
        == artifact["RAW_PROVIDER_RESPONSE_SHA256"]
        == kept.get("raw_response_sha256")
        == RAW_RESPONSE_SHA256
    ):
        raise ValidationError("the retained body is not the one that arrived")
    if len(raw) != artifact["RAW_PROVIDER_RESPONSE_CHARACTERS"] or len(raw) != kept.get(
        "raw_response_characters"
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
    for key in ("ACTUAL_USAGE", "ACTUAL_COST"):
        if not isinstance(record[key], dict):
            raise ValidationError(
                f"the record gives {key} as {record[key]!r}, and the retained response reports "
                "the usage it rests on: NOT_ESTABLISHED is for a figure that was genuinely unavailable"
            )
    _fixed(record["ACTUAL_USAGE"], usage_facts(usage), "record.ACTUAL_USAGE")
    thinking = (usage.get("output_tokens_details") or {}).get("thinking_tokens")
    if thinking != 0 or record["THINKING_TOKENS_REPORTED"] != 0:
        raise ValidationError("thinking tokens were reported under a DISABLED policy")
    if artifact["USAGE_FROM_RESPONSE"] != usage:
        raise ValidationError("the artifact's usage is not the response's own usage block")
    telemetry = artifact["usage"]
    if len(telemetry) != 1 or (telemetry[0]["input_tokens"], telemetry[0]["output_tokens"]) != (
        int(usage["input_tokens"]),
        int(usage["output_tokens"]),
    ):
        raise ValidationError("the Gateway's telemetry and the response disagree about usage")

    _fixed(
        record["BILLED_CATEGORIES_OBSERVED"], billed_categories(usage), "record.BILLED_CATEGORIES"
    )
    contradictions = billing_contradictions(usage, packet)
    if record["BILLED_CATEGORY_CONTRADICTIONS"] != contradictions:
        raise ValidationError("the recorded billing contradictions are not what the usage shows")
    if contradictions:
        raise ValidationError(
            "an observed billed category contradicts the proven ceiling's assumptions, and the "
            "record fails closed: " + "; ".join(contradictions)
        )
    cost = actual_cost(usage, packet)
    _fixed(record["ACTUAL_COST"], cost, "record.ACTUAL_COST")
    held = round(PRICE.cost_for(int(usage["input_tokens"]), int(usage["output_tokens"])), 6)
    base = Decimal(str(cost["cost_units"])) / Decimal(str(cost["residency_multiplier"]))
    if Decimal(str(held)) != base or (
        telemetry[0]["cost_units"] != held or telemetry[0]["priced"] is not True
    ):
        raise ValidationError("the Gateway's telemetry and the recomputed cost disagree")
    ceiling = Decimal(str(packet["HARD_EXECUTION_COST_CEILING"]))
    within = Decimal(str(cost["cost_units"])) <= ceiling
    if not within or record["ACTUAL_COST_WITHIN_HARD_CEILING"] is not True:
        raise ValidationError(
            "the call cost more than its hard ceiling, or the record says otherwise"
        )
    if record["INPUT_ESTIMATE_COVERED_THE_ACTUAL"] is not (
        int(usage["input_tokens"]) <= int(packet["PLANNING_INPUT_TOKEN_ESTIMATE"])
    ):
        raise ValidationError(
            "the record misstates whether the planning estimate covered the input"
        )

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
    if not (
        _sha_text(json.dumps(parsed, sort_keys=True))
        == artifact["PARSED_OUTPUT_SHA256"]
        == kept.get("parsed_output_sha256")
        == PARSED_OUTPUT_SHA256
    ):
        raise ValidationError("the parsed output is not the one that arrived")

    violations = list(schema_violations(dict(parsed), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2))
    if violations != record["SCHEMA_VIOLATIONS"]:
        raise ValidationError(
            "the recorded schema violations are not what the live v1.2.0 validator finds in the "
            f"retained answer: {violations}"
        )
    if record["HARD_SCHEMA_VERDICT"] != ("FAILED" if violations else "PASSED"):
        raise ValidationError("the recorded hard-schema verdict is not the validator's")
    properties = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["properties"]
    unknown = sorted(key for key in parsed if key not in properties)
    if record["UNKNOWN_ROOT_PROPERTIES_RETURNED"] != unknown or record["ROOT_KEYS_RETURNED"] != len(
        parsed
    ):
        raise ValidationError("the recorded root keys are not the ones the answer carries")
    if target_diagnostics(parsed) != record["GENERATION_TARGET_DIAGNOSTICS"]:
        raise ValidationError(
            "the recorded generation-target diagnostics are not what the answer measures"
        )
    if reasoning_summary(parsed) != record["REASONING_SUMMARY"]:
        raise ValidationError(
            "the recorded reasoning-summary lengths are not what the answer measures"
        )

    report, statements, found = replay(artifact, packet)
    validation = artifact["validation"]
    for key in (
        "stages",
        "failed_stage",
        "reasons",
        "outcome",
        "stop_reason",
        "completion",
        "persist",
    ):
        if report.get(key) != validation.get(key):
            raise ValidationError(f"the replay's {key} is not the one the execution retained")
    _fixed(
        record["STAGE_REPLAY"],
        {
            **found,
            "snapshot": f"docs/data/{SNAPSHOT_RECORD.name}",
            "snapshot_sha256": SNAPSHOT_RECORD_SHA256,
            "database_used": False,
            "transport_constructed": False,
            "reproduced": True,
        },
        "record.STAGE_REPLAY",
    )
    stages, failed = _derived_stages(completion, blocks, violations, report)
    _no_pass_after_failure(stages)
    if record["VALIDATION_STAGES"] != stages or validation["stages"] != stages:
        raise ValidationError("the stage table is not the one these facts imply")
    if record["FAILED_STAGE"] != failed or validation["failed_stage"] != failed:
        raise ValidationError("the failed stage is not the one these facts imply")
    if record["STAGES_PASSED"] != sum(1 for verdict in stages.values() if verdict == "PASSED"):
        raise ValidationError("a stage that was not reached is counted as passed")
    if record["SEMANTIC_GATE_VERDICT"] != stages[STAGES[5]]:
        raise ValidationError("the recorded semantic verdict is not the stage table's")
    semantic_reasons = list(validation["reasons"]) if failed == STAGES[5] else []
    if record["SEMANTIC_GATE_REFUSAL_REASONS"] != semantic_reasons:
        raise ValidationError("the recorded semantic refusal reasons are not the gate's")
    details = semantic_details(parsed, statements, semantic_reasons)
    if record["SEMANTIC_REFUSAL_DETAILS"] != details:
        raise ValidationError(
            "the recorded semantic refusal details are not what the answer measures"
        )
    _fixed(record["PROMPT_STATED_RULES"], prompt_statements(), "record.PROMPT_STATED_RULES")

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


def spent_record_shas() -> dict[str, str]:
    """V1's to V5's execution records by gate 87's pins, as gate 91 holds them, and V6's by gate 91's."""
    out: dict[str, str] = {}
    for label in ("V1", "V2", "V3", "V4", "V5"):
        name = f"second-opportunity-synthesis-execution-record-{label.lower()}.json"
        path = next((p for p in G91.HISTORY if p.name == name), None)
        if path is None:
            raise ValidationError(f"gate 91 no longer pins {name}")
        out[label] = str(G91.HISTORY[path])
    out["V6"] = str(G91.RECORD_FILE_SHA256)
    return out


def _check_history(record: dict[str, Any]) -> None:
    try:
        v6 = G91.validate()
    except G91.ValidationError as exc:
        raise ValidationError(f"V1 to V6 no longer stand as spent: gate 91 refuses: {exc}") from exc
    if (
        v6.get("execution_packet_sha256") != V6_SHA256
        or v6.get("EXECUTION_APPROVAL_CONSUMED") is not True
    ):
        raise ValidationError("V6's record no longer names V6 spent")
    _fixed(
        record,
        {
            f"{label}_EXECUTION_RECORD_SHA256": digest
            for label, digest in spent_record_shas().items()
        },
        "record",
    )


def _check_supersessions(record: dict[str, Any], packet: dict[str, Any]) -> None:
    for label in ("V7", "V8"):
        path = SUPERSESSION[label]
        bound = packet[f"{label}_SUPERSESSION_RECORD_SHA256"]
        if _sha_text(path.read_text(encoding="utf-8")) != bound:
            raise ValidationError(f"{label}'s supersession record changed after V9 bound it")
        doc = _load(path)
        _fixed(
            doc,
            {
                "STATUS": "SUPERSEDED_BEFORE_EXECUTION",
                f"{label}_EXECUTED": False,
                f"{label}_APPROVED": False,
                f"{label}_APPROVAL_CONSUMED": False,
            },
            f"{label}'s supersession",
        )
        for trace in NEVER_RUN[label]:
            if trace.exists():
                raise ValidationError(
                    f"{trace.name} exists: {label} was superseded before execution, and never "
                    "approved or run"
                )
        _fixed(
            record,
            {
                f"{label}_STATUS": "SUPERSEDED_BEFORE_EXECUTION",
                f"{label}_SUPERSESSION_RECORD_SHA256": bound,
            },
            "record",
        )


def _check_runner() -> None:
    module = runner()
    for label, digest in (("V9", V9_SHA256), *SPENT.items()):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != CONSUMED:
                raise ValidationError(
                    f"the runner refuses {label} for the wrong reason: {exc.code}"
                ) from exc
        else:
            raise ValidationError(
                f"the runner would execute {label} again: its guard does not see {label} spent"
            )
    for label, digest in (("V7", V7_SHA256), ("V8", V8_SHA256)):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != SUPERSEDED:
                raise ValidationError(f"the runner refuses {label} as {exc.code}") from exc
        else:
            raise ValidationError(f"the runner would execute {label}, superseded before execution")
    try:
        module.refuse_if_consumed("0" * 64)
    except module.RefusedError as exc:
        raise ValidationError(
            "the runner's guard refuses every digest, not only spent ones"
        ) from exc
    if (
        module.EXECUTION_RECORD_V9.name != RECORD.name
        or module.RESPONSE_ARTIFACT.name != RESPONSE.name
        or module.APPROVAL_FILE.name != APPROVAL.name
    ):
        raise ValidationError("the runner reads V9's consumption, response or approval elsewhere")

    reached: list[bool] = []

    def refuse_execute(*args: object, **kwargs: object) -> None:
        reached.append(True)
        raise AssertionError("gate 98: execute() was reached")

    module.execute = refuse_execute
    out = io.StringIO()
    with G76.no_transport(), contextlib.redirect_stdout(out):
        code = module.main(["--execute"])
    if code != 1 or reached or CONSUMED not in out.getvalue():
        raise ValidationError(
            f"a second --execute of V9 is not refused before any network as {CONSUMED} "
            f"(exit {code}, execute reached: {bool(reached)})"
        )


def _check_no_credentials() -> None:
    for path in (RECORD, APPROVAL, RESPONSE, *([REVIEW_PACKET] if REVIEW_PACKET.exists() else [])):
        if SECRET.search(path.read_text(encoding="utf-8")):
            raise ValidationError(f"{path.name} carries something shaped like a credential")


def validate() -> dict[str, Any]:
    for path, why in (
        (RECORD, "without it the runner's guard cannot see V9 spent"),
        (APPROVAL, "the approval the one request spent belongs beside the packet"),
        (RESPONSE, "what the one request brought back is what the record rests on"),
    ):
        if not path.exists():
            raise ValidationError(f"{path.name} is missing: {why}")
    record = _load(RECORD)
    packet = _check_packet(record)
    _check_record(record, packet)
    _check_approval(record, packet)
    _check_response(record, packet)
    _check_history(record)
    _check_supersessions(record, packet)
    _check_runner()
    _check_no_credentials()
    if _sha_file(RECORD) != RECORD_FILE_SHA256:
        raise ValidationError("the execution record changed after it was written and pinned")
    return record


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_record_v9.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _sentence(text: object) -> str:
    value = str(text).strip()
    return value if value.endswith((".", "!", "?")) else value + "."


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _yes(value: object) -> str:
    return "yes" if value else "no"


def _flag(value: object) -> str:
    return str(value).lower()


def _returned(row: dict[str, Any]) -> str:
    if row["elements"] is None:
        return str(row["characters"])
    lengths = ", ".join(str(n) for n in row["characters"])
    return f"{lengths} ({row['elements']} elements)"


def _refusal(row: dict[str, Any]) -> str:
    text = str(row["text"]).replace("|", "\\|")
    if row["kind"] == "UNSUPPORTED_TERM":
        why = f"the word `{row['term']}` is in no supplied statement"
    else:
        confirmation = row["confirmation_words"]
        why = f"opens with `{row['first_word']}`, not a request"
        if confirmation:
            why += "; carries " + ", ".join(f"`{w}`" for w in confirmation)
    return f"| `{row['field']}` | {row['verdict']} | {why} | {text} |"


def render(record: dict[str, Any]) -> str:
    usage = record["ACTUAL_USAGE"]
    cost = record["ACTUAL_COST"]
    billed = record["BILLED_CATEGORIES_OBSERVED"]
    approval = record["OPERATOR_APPROVAL"]
    kept = record["RESPONSE_ARTIFACT"]
    timing = record["timing"]
    summary = record["REASONING_SUMMARY"]
    replayed = record["STAGE_REPLAY"]
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: synthesis execution record v9",
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
                f"approval file          {approval['file_sha256']}",
                f"approval statement     {approval['operator_statement_sha256']}",
                "residual semantic risk accepted for V9: "
                f"{_flag(approval['RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9'])}, expired: "
                f"{_flag(approval['RESIDUAL_RISK_ACCEPTANCE_EXPIRED'])}",
                "strict first-request timeout risk accepted for V9: "
                f"{_flag(approval['STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9'])}, expired: "
                f"{_flag(approval['TIMEOUT_RISK_ACCEPTANCE_EXPIRED'])}",
                f"route                  {record['ROUTE']} ({record['ROUTE_KIND']})",
                f"model                  {record['MODEL']} (response: {record['RESPONSE_MODEL']})",
                f"thinking               {record['THINKING_POLICY']}, "
                f"{json.dumps(record['THINKING_REQUEST_VALUE'])}",
                f"strict mode            {_flag(record['PROVIDER_STRICT_MODE'])}, "
                f"{record['STRUCTURED_OUTPUT_MECHANISM']}",
                f"strict projection      {record['PROVIDER_STRICT_SCHEMA_ID']} "
                f"{record['PROVIDER_STRICT_SCHEMA_SHA256']}",
                f"capability profile     {record['STRICT_CAPABILITY_PROFILE_ID']} "
                f"{record['STRICT_CAPABILITY_PROFILE_SHA256']}",
                f"strict freeze commit   {record['STRICT_PROJECTION_FREEZE_COMMIT']}",
                f"max_tokens             {record['MAX_TOKENS']}",
                f"timeout                {record['REQUEST_TIMEOUT_SECONDS']} s, no retry",
                f"request body           {record['REQUEST_BODY_CHARACTERS']} characters "
                f"{record['REQUEST_BODY_SHA256']}",
                f"prompt                 {record['PROMPT_VERSION']} {record['PROMPT_SHA256']}",
                f"schema                 {record['OUTPUT_SCHEMA_VERSION']} "
                f"{record['OUTPUT_SCHEMA_SHA256']}",
                f"summary bound/target   {record['REASONING_SUMMARY_HARD_MAX']} / "
                f"{record['REASONING_SUMMARY_GENERATION_TARGET']}",
                f"semantic gate          {record['OUTPUT_GATE_VERSION']} "
                f"{record['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}",
                f"representation         {record['TED_REPRESENTATION_SHA256']}",
                f"started / finished     {timing['started_at']} / {timing['finished_at']}",
                f"elapsed                {timing['elapsed_seconds']} s "
                f"(timed out: {_flag(record['TIMED_OUT'])})",
                f"HTTP status            {record['HTTP_STATUS']}",
                f"request id             {record['PROVIDER_REQUEST_ID']}",
                f"message id             {record['PROVIDER_MESSAGE_ID']}",
            ]
        ),
        _sentence(record["request_body_note"]),
        "",
        "## What came back",
        "",
        *_code(
            [
                f"stop_reason            {record['STOP_REASON']} -> {record['PROVIDER_COMPLETION']}",
                f"input tokens           {usage['input_tokens']} "
                f"(planning estimate {record['PLANNING_INPUT_TOKEN_ESTIMATE']})",
                f"output tokens          {usage['output_tokens']} (max_tokens {record['MAX_TOKENS']})",
                f"thinking tokens        {usage['thinking_tokens']}",
                f"total tokens           {usage['total_tokens']}",
                f"service tier           {billed['service_tier']}",
                f"inference geo          {billed['inference_geo']} "
                f"(US-only multiplier applies: {_yes(billed['us_only_multiplier_applies'])})",
                f"cache tokens           created {billed['cache_creation_input_tokens']}, "
                f"read {billed['cache_read_input_tokens']}",
                f"actual cost            {cost['cost_units']} ({cost['input_cost_units']} input + "
                f"{cost['output_cost_units']} output, x{cost['residency_multiplier']}, "
                f"{cost['pricing_version']})",
                f"planning estimate      {record['PLANNING_COST_ESTIMATE']} (not incurred)",
                f"hard ceiling           {record['HARD_EXECUTION_COST_CEILING']} (not incurred; "
                f"actual within it: {_flag(record['ACTUAL_COST_WITHIN_HARD_CEILING'])})",
                "billing contradictions "
                + (", ".join(record["BILLED_CATEGORY_CONTRADICTIONS"]) or "none"),
            ]
        ),
        _sentence(record["billing_note"]),
        "",
        _sentence(record["cost_note"]),
        "",
        "## The ten stages",
        "",
        "| stage | verdict |",
        "|---|---|",
        *[f"| `{stage}` | {verdict} |" for stage, verdict in record["VALIDATION_STAGES"].items()],
        "",
        f"Stages passed: {record['STAGES_PASSED']}. Failed: `{record['FAILED_STAGE']}`. A stage that "
        "was not reached is not a stage that passed.",
        "",
        "## Stage 5: the full schema, and strict mode",
        "",
        f"Schema v1.2.0 verdict: **{record['HARD_SCHEMA_VERDICT']}**, "
        f"{len(record['SCHEMA_VIOLATIONS'])} violation(s). Root keys returned: "
        f"{record['ROOT_KEYS_RETURNED']}; undeclared root keys: "
        f"{record['UNKNOWN_ROOT_PROPERTIES_RETURNED'] or 'none'}.",
        "",
        _sentence(record["strict_note"]),
        "",
        "## Stage 6: what refused it",
        "",
        "Gate v1.4.0's reasons, as the execution retained them and as the replay reproduces them:",
        "",
        *[f"- `{reason}`" for reason in record["SEMANTIC_GATE_REFUSAL_REASONS"]],
        "",
        "| field | verdict | measured again | returned text |",
        "|---|---|---|---|",
        *[_refusal(row) for row in record["SEMANTIC_REFUSAL_DETAILS"]],
        "",
        "What prompt v1.5.0 states in words about these rules:",
        "",
        *[
            f"- {key}: {_yes(value)} (`{PROMPT_RULES[key]}`)"
            for key, value in record["PROMPT_STATED_RULES"].items()
        ],
        "",
        _sentence(record["semantic_note"]),
        "",
        "## The replay, with no database",
        "",
        *_code(
            [
                f"snapshot               {replayed['snapshot']} {replayed['snapshot_sha256']}",
                f"representation         {replayed['representation_sha256']}",
                f"prompt                 {replayed['prompt_sha256']}",
                f"trusted context        {replayed['trusted_context_sha256']}",
                f"source metadata        {replayed['source_metadata_sha256']}",
                f"database used          {_flag(replayed['database_used'])}",
                f"transport constructed  {_flag(replayed['transport_constructed'])}",
                f"verdict reproduced     {_flag(replayed['reproduced'])}",
            ]
        ),
        "## The reasoning summary",
        "",
        *_code(
            [
                f"characters             {summary['characters']}",
                f"generation target      {summary['generation_target']} "
                f"(within: {_yes(summary['within_target'])})",
                f"hard maximum           {summary['hard_maximum']} "
                f"(within: {_yes(summary['within_hard_maximum'])})",
            ]
        ),
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
                f"response artifact      {kept['file']} {kept['file_sha256']}",
                f"raw response sha256    {kept['raw_response_sha256']} "
                f"({kept['raw_response_characters']} characters, recomputable from the kept body)",
                f"parsed output sha256   {kept['parsed_output_sha256']}",
                f"usage retained         {_flag(kept['USAGE_RETAINED'])}",
                f"hidden reasoning       retained: {_flag(kept['HIDDEN_REASONING_RETAINED'])}",
                f"post-call fail-safe    used: {_flag(record['POST_CALL_FALLBACK_USED'])}",
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
                f"Opportunity persisted  {_flag(record['OPPORTUNITY_PERSISTED'])}",
            ]
        ),
        _sentence(record["ted_note"]),
        "",
        "Canonical counters before and after: "
        + " / ".join(str(v) for v in record["CANONICAL_COUNTERS_AFTER"].values())
        + ".",
        "",
        "## V1 to V8",
        "",
        *_code(
            [
                *[
                    f"{label} execution record  {record[f'{label}_EXECUTION_RECORD_SHA256']} "
                    "(consumed)"
                    for label in SPENT
                ],
                *[
                    f"{label} supersession      {record[f'{label}_SUPERSESSION_RECORD_SHA256']} "
                    f"({record[f'{label}_STATUS']})"
                    for label in ("V7", "V8")
                ],
            ]
        ),
        "## Human review",
        "",
        f"`HUMAN_OUTPUT_REVIEW_REQUIRED = true`, `HUMAN_REVIEW_PACKET = "
        f"{record['HUMAN_REVIEW_PACKET']}`. {_sentence(record['human_review_note'])}",
        "",
        f"**The approval is spent.** {_sentence(record['consumption_note'])}",
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
        "ok       the V9 execution record matches its approval, its retained response, the replay "
        "and the runner; V9 cannot run again"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
