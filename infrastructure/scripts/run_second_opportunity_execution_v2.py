"""Execute the second-Opportunity synthesis under execution packet V2. Prepared by Mission 1.84.6.

ONE provider request, under `SECOND-OPPORTUNITY-SYNTH-EXEC-V2` version 2, and only once an operator
approval naming this packet's digest is recorded BESIDE the packet.

    uv run python infrastructure/scripts/run_second_opportunity_execution_v2.py
    uv run python infrastructure/scripts/run_second_opportunity_execution_v2.py --execute

**Verification is the default and execution is the opt-in**, exactly as for V1. Mission 1.84.6
prepared this runner and ran only its verification: no approval exists, so `--execute` refuses
before a transport is built.

**What differs from V1, and nothing else.** The adapter is built with thinking DISABLED and
`max_tokens` 128000, the operator's execution envelope. The provider's completion signal is read
from the retained response BEFORE the structured output is parsed, validated or judged: an answer
that stopped at the limit is refused however well-formed the part that arrived looks. And there are
ten ordered stages rather than eight, the new one third.

**No retry, no continuation, no repair.** A stop at the output limit ends the execution with
`EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY`. There is no second request, no request to finish the
JSON, and no repair model anywhere in this file.

**Nothing is persisted.** An answer that passes every machine stage still stops at a human.

The credential is read from the environment by the provider adapter and is never read, printed,
logged or written here.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
from collections.abc import Callable, Mapping
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
SCRIPTS = ROOT / "infrastructure" / "scripts"
sys.path.insert(0, str(SCRIPTS))

PACKET_FILE = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
APPROVAL_FILE = DATA / "second-opportunity-synthesis-execution-approval-v2.json"
REGISTER = DATA / "model-provider-policy-v1.json"
RESPONSE_ARTIFACT = DATA / "second-opportunity-synthesis-response-v2.json"
CORRELATION_ID = "second-opportunity-synthesis-execution-v2"

SUBJECT = "ted-eu:CPV-class:9261"
SOURCE_ID = "ted-eu"
USE_PROFILE = "local-private-research-v1"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"

#: The packet as Mission 1.84.6 prepared it. Pinned here rather than read from the packet, because a
#: runner that took its expectations from the file it checks would check nothing. An operator
#: approval does not change these values: it names them.
EXPECTED: dict[str, object] = {
    "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V2",
    "EXECUTION_PACKET_VERSION": 2,
    "EXECUTION_PACKET_SHA256": "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e",
    "PROVIDER_ID": "anthropic",
    "MODEL_ID": "claude-sonnet-5",
    "SUBJECT_KEY": SUBJECT,
    "REPRESENTATION_SHA256": "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72",
    "PROMPT_VERSION": "1.1.0",
    "PROMPT_SHA256": "2f60c61f63cda410b9f60e3eafd9676f983e7ff0220245c03c88136511ac7e82",
    "OUTPUT_SCHEMA_VERSION": "second-opportunity-synthesis-output@1.1.0",
    "OUTPUT_SCHEMA_SHA256": "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988",
    "OUTPUT_GATE_VERSION": "second-opportunity-output-gate@1.1.0",
    "THINKING": "DISABLED",
    "MAX_OUTPUT_TOKENS": 128000,
    "MAX_MODEL_CALLS": 1,
    "MAX_RETRIES": 0,
    "REQUEST_TIMEOUT": 60.0,
    "EXECUTION_COST_CEILING": 1.303908,
    "WEB": False,
    "TOOLS": False,
    "EXTERNAL_RETRIEVAL": False,
    "TRAINING": False,
    "FINE_TUNING": False,
    "EMBEDDINGS": False,
}

#: The ten ordered stages. The third is the one V1 did not have: the provider's own statement of
#: whether the answer finished, read before anything tries to make sense of the answer.
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

ACCEPTED = "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
NO_HYPOTHESIS = "EXECUTION_COMPLETED_INSUFFICIENT_EVIDENCE_NO_OPPORTUNITY"


class RefusedError(RuntimeError):
    """A bound field moved, or the approval is absent. Nothing is sent."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RefusedError("RUNNER_DEPENDENCY_MISSING", f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def v1_runner() -> Any:
    """The V1 runner, for the consumed-approval guard and the repaired retention path."""
    return _module("second_opportunity_runner_v1", SCRIPTS / "run_second_opportunity_execution.py")


def packet_gate() -> Any:
    """One authority for what the V2 digest binds: Mission 1.84.6's own gate."""
    return _module(
        "execution_packet_v2_gate", SCRIPTS / "render_second_opportunity_execution_packet_v2.py"
    )


def schema_sha256(schema: Mapping[str, object]) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()


class _NoSend:
    """A transport for building a request body locally. Verification never sends."""

    def post_json(self, *args: object, **kwargs: object) -> Any:
        raise AssertionError("verification builds the request body and never sends it")


# --------------------------------------------------------------------- the call as it would be made


def build_provider(packet: Mapping[str, Any], transport: Any, api_key: str | None = None) -> Any:
    """The adapter with the packet's own parameters: thinking DISABLED, max_tokens 128000."""
    from sros_llm_gateway.providers.anthropic import AnthropicProvider, AnthropicThinking

    params = packet["ADAPTER_PARAMETERS"]
    try:
        thinking = AnthropicThinking[str(params["thinking"])]
    except KeyError as exc:
        raise RefusedError(
            "THINKING_CONTROL_NO_LONGER_VALID",
            f"the adapter has no thinking configuration named {params['thinking']!r}",
        ) from exc
    kwargs: dict[str, Any] = {
        "max_output_tokens": int(params["max_output_tokens"]),
        "thinking": thinking,
        "transport": transport,
    }
    if api_key is not None:
        kwargs["api_key"] = api_key
    return AnthropicProvider(**kwargs)


def build_request(parts: Any, packet: Mapping[str, Any]) -> Any:
    from sros_llm_gateway.prompts.rendering import RenderedPrompt, UntrustedText
    from sros_llm_gateway.types import LlmRequest, LlmTier
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        SECOND_OPPORTUNITY_PROMPT_ID,
        SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
    )

    prompt = RenderedPrompt(
        system_instructions=parts.system_instructions,
        trusted_context=parts.trusted_context,
        untrusted=tuple(UntrustedText(content=c, label=label) for c, label in parts.untrusted),
        task=parts.task,
        metadata=parts.metadata,
    )
    return LlmRequest(
        tier=LlmTier.STRONG_MODEL,
        task=SECOND_OPPORTUNITY_PROMPT_ID,
        prompt_template_id=SECOND_OPPORTUNITY_PROMPT_ID,
        prompt_template_version=SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
        response_schema=SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        prompt=prompt,
        workspace_id=os.environ.get("DEV_WORKSPACE_ID", "00000000-0000-4000-8000-000000000001"),
        correlation_id=CORRELATION_ID,
        timeout_seconds=float(packet["REQUEST_TIMEOUT"]),
        max_retries=int(packet["GENERATION_PARAMETERS"]["max_retries"]),
        requires_structured_output=True,
    )


def request_body(parts: Any, packet: Mapping[str, Any]) -> dict[str, Any]:
    """The exact body the adapter would send, built locally and never sent."""
    provider = build_provider(packet, _NoSend(), api_key="verification-not-a-credential")
    return provider.build_body(build_request(parts, packet), str(packet["MODEL_ID"]))


# --------------------------------------------------------------------- approval


def check_approval(packet_sha256: str) -> dict[str, Any]:
    """The operator's approval, beside the packet and never inside it.

    Creating V2 authorised nothing. An approval is a separate record naming this packet's id,
    version and digest, and a V1 approval, which is spent, names a different digest.
    """
    if not APPROVAL_FILE.exists():
        raise RefusedError(
            "OPERATOR_APPROVAL_NOT_RECORDED",
            f"no approval names execution packet {packet_sha256}. Preparing V2 authorised no "
            "request, and this runner sends nothing without one",
        )
    approval = _load(APPROVAL_FILE)
    required = {
        "EXECUTION_PACKET_ID": EXPECTED["EXECUTION_PACKET_ID"],
        "EXECUTION_PACKET_VERSION": EXPECTED["EXECUTION_PACKET_VERSION"],
        "EXECUTION_PACKET_SHA256": packet_sha256,
        "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
    }
    for key, value in required.items():
        if approval.get(key) != value:
            raise RefusedError(
                "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET",
                f"the approval records {key}={approval.get(key)!r}, and this execution needs "
                f"{value!r}",
            )
    for key in ("approved_by", "operator_statement"):
        if not str(approval.get(key) or "").strip():
            raise RefusedError("OPERATOR_APPROVAL_INCOMPLETE", f"the approval has no {key}")
    return approval


def refuse_if_consumed(packet_sha256: str) -> None:
    """V1's guard, reading the record beside V1. A spent approval names a spent digest."""
    v1 = v1_runner()
    try:
        v1.refuse_if_consumed(packet_sha256)
    except v1.RefusedError as exc:
        raise RefusedError("EXECUTION_APPROVAL_ALREADY_CONSUMED", str(exc)) from exc


# --------------------------------------------------------------------- verification


def verify(use_profile: str = USE_PROFILE) -> dict[str, Any]:
    """Every pre-execution check the packet binds. Any failure refuses before a socket exists."""
    from sros_llm_gateway.pricing import load_pricing_from_env
    from sros_opportunity import (
        ExternalSynthesisDecision,
        SynthesisAvailability,
        authorize_packet_for_external_synthesis,
        serialize_packet_for_model,
    )
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
        render_second_opportunity_prompt_v1_1,
        second_opportunity_prompt_hash_v1_1,
    )

    findings: dict[str, object] = {}
    packet = _load(PACKET_FILE)

    # 1. the digest, recomputed from the bound fields, is the one this runner was prepared for
    recomputed = packet_gate().packet_digest(packet)
    findings["01_EXECUTION_PACKET_SHA256"] = recomputed
    if recomputed != EXPECTED["EXECUTION_PACKET_SHA256"]:
        raise RefusedError(
            "EXECUTION_PACKET_DIGEST_MISMATCH",
            f"the packet's bound fields hash to {recomputed}, and this runner was prepared for "
            f"{EXPECTED['EXECUTION_PACKET_SHA256']}",
        )
    if packet.get("EXECUTION_PACKET_SHA256") != recomputed:
        raise RefusedError("EXECUTION_PACKET_DIGEST_MISMATCH", "the recorded digest is stale")

    # 2. identity, and no approval written into the frozen document
    for key in ("EXECUTION_PACKET_ID", "EXECUTION_PACKET_VERSION", "SUBJECT_KEY"):
        if packet.get(key) != EXPECTED[key]:
            raise RefusedError("EXECUTION_PACKET_IDENTITY_MOVED", f"{key} is {packet.get(key)!r}")
    if packet.get("OPERATOR_EXECUTION_APPROVAL_RECORDED") is not False:
        raise RefusedError(
            "APPROVAL_WRITTEN_INTO_THE_PACKET",
            "marking a frozen document approved changes the bytes that were approved",
        )

    # 3. V1 spent, V2 not
    try:
        refuse_if_consumed(V1_SHA256)
    except RefusedError:
        findings["03_V1_APPROVAL_CONSUMED"] = True
    else:
        raise RefusedError("V1_GUARD_INACTIVE", "the consumed-approval guard no longer refuses V1")
    refuse_if_consumed(recomputed)
    findings["03_V2_APPROVAL_CONSUMED"] = False

    # 4. the TED representation, rebuilt through production serialisation
    v1 = v1_runner()
    evidence_packet, statements, evidence_to_claim, standings = v1.rebuild(use_profile)
    measurement = ExternalSynthesisDecision(
        availability=SynthesisAvailability.AVAILABLE,
        packet_id=evidence_packet.packet_id,
        refusal_reasons=(),
        per_source=((SOURCE_ID, "RECOMPUTED_FOR_VERIFICATION"),),
    )
    serialized = serialize_packet_for_model(evidence_packet, measurement, statements)
    representation = _sha256(serialized)
    findings["04_REPRESENTATION_SHA256"] = representation
    findings["04_REPRESENTATION_CHARACTERS"] = len(serialized)
    if representation != EXPECTED["REPRESENTATION_SHA256"]:
        raise RefusedError(
            "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED",
            f"recomputed {representation}. The approval is never updated to match",
        )
    if evidence_packet.packet_id != packet["SELECTED_PACKET_ID"]:
        raise RefusedError("SELECTED_PACKET_MOVED", "the rebuilt packet is not the one V2 names")

    # 5. the rendered prompt, v1.1.0, unchanged
    parts = render_second_opportunity_prompt_v1_1(evidence_packet, statements, evidence_to_claim)
    prompt_hash = second_opportunity_prompt_hash_v1_1(parts)
    findings["05_PROMPT_SHA256"] = prompt_hash
    if prompt_hash != EXPECTED["PROMPT_SHA256"] or packet["PROMPT_SHA256"] != prompt_hash:
        raise RefusedError(
            "SECOND_OPPORTUNITY_PROMPT_CHANGED_REQUIRES_REVIEW",
            f"the rendered prompt hashes to {prompt_hash}",
        )
    if packet["PROMPT_VERSION"] != SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1:
        raise RefusedError("SECOND_OPPORTUNITY_PROMPT_CHANGED_REQUIRES_REVIEW", "prompt version")

    # 6. the output contract and gate, live
    live_schema = schema_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    findings["06_OUTPUT_SCHEMA_SHA256"] = live_schema
    contract = {
        "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        "OUTPUT_SCHEMA_SHA256": live_schema,
        "OUTPUT_GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    }
    for key, live in contract.items():
        if live != EXPECTED[key] or packet[key] != live:
            raise RefusedError("OUTPUT_CONTRACT_MOVED", f"{key} is {live!r} live")

    # 7. the provider route, from the live register
    register = _load(REGISTER)
    posture = next(
        (
            str(e["posture"])
            for e in register["providers"]
            if e["provider_id"] == EXPECTED["PROVIDER_ID"]
        ),
        "NOT_ASSESSED",
    )
    findings["07_PROVIDER_POSTURE"] = posture
    if posture != "APPROVED" or packet["PROVIDER_ID"] != EXPECTED["PROVIDER_ID"]:
        raise RefusedError("PROVIDER_ROUTE_NO_LONGER_APPROVED", f"posture {posture}")
    if packet["MODEL_ID"] != EXPECTED["MODEL_ID"]:
        raise RefusedError("MODEL_MOVED", f"the packet names {packet['MODEL_ID']!r}")

    # 8. TED egress, live
    standing = standings.get(SOURCE_ID)
    if standing is None or not standing.permits_external_model_transmission:
        raise RefusedError("TED_EGRESS_NO_LONGER_AVAILABLE", f"{SOURCE_ID} standing {standing}")
    findings["08_TED_EXTERNAL_MODEL_TRANSMISSION"] = str(standing.transmission_state)
    if "PERMITTED_WITH_CONDITIONS" not in str(standing.transmission_state):
        raise RefusedError(
            "TED_EGRESS_NO_LONGER_AVAILABLE",
            f"external_model_transmission is {standing.transmission_state}",
        )
    live_gate = authorize_packet_for_external_synthesis(
        evidence_packet,
        {sid: standings[sid] for sid in evidence_packet.source_ids if sid in standings},
        provider_configured=bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
        provider_posture=posture,
    )
    findings["08_LIVE_PACKET_GATE"] = live_gate.availability.value
    if live_gate.availability is not SynthesisAvailability.AVAILABLE:
        raise RefusedError("TED_EGRESS_NO_LONGER_AVAILABLE", f"{list(live_gate.refusal_reasons)}")

    # 9. thinking and the envelope, from the body the adapter would send
    body = request_body(parts, packet)
    findings["09_REQUEST_THINKING"] = body.get("thinking")
    findings["09_REQUEST_MAX_TOKENS"] = body.get("max_tokens")
    if body.get("thinking") != {"type": "disabled"}:
        raise RefusedError("THINKING_CONTROL_NO_LONGER_VALID", f"thinking {body.get('thinking')}")
    if body.get("max_tokens") != EXPECTED["MAX_OUTPUT_TOKENS"]:
        raise RefusedError("OUTPUT_CEILING_MOVED", f"max_tokens {body.get('max_tokens')}")
    wire = len(json.dumps(body))
    findings["09_REQUEST_BODY_CHARACTERS"] = wire
    if wire != packet["TOKEN_ESTIMATION_BASIS"]["wire_characters"]:
        raise RefusedError(
            "INPUT_ESTIMATE_BASIS_MOVED",
            f"the body is {wire} characters and the estimate was sized on "
            f"{packet['TOKEN_ESTIMATION_BASIS']['wire_characters']}",
        )

    # 10. one call, no retry
    if int(packet["MAX_MODEL_CALLS"]) != 1 or int(packet["MAX_RETRIES"]) != 0:
        raise RefusedError("CALL_LIMIT_MOVED", "V2 authorises one call and no retry")
    if int(packet["GENERATION_PARAMETERS"]["max_retries"]) != 0:
        raise RefusedError("CALL_LIMIT_MOVED", "the request would carry a retry")

    # 11. the cost ceiling, against the held price
    pricing = load_pricing_from_env()
    if pricing.version != packet["PRICING_VERSION"]:
        raise RefusedError(
            "MODEL_COST_BASIS_CHANGED",
            f"the configured pricing is {pricing.version!r} and V2 was priced on "
            f"{packet['PRICING_VERSION']!r}",
        )
    worst, priced = pricing.cost_for(
        str(packet["PROVIDER_ID"]),
        str(packet["MODEL_ID"]),
        int(packet["INPUT_TOKEN_ESTIMATE"]),
        int(packet["MAX_OUTPUT_TOKENS"]),
    )
    findings["11_WORST_CASE_CALL_COST"] = worst
    if not priced or worst > float(packet["EXECUTION_COST_CEILING"]):
        raise RefusedError(
            "EXECUTION_COST_CEILING_EXCEEDED",
            f"the worst case is {worst} against a ceiling of {packet['EXECUTION_COST_CEILING']}",
        )

    # 12. every remaining bound field
    for key in ("REQUEST_TIMEOUT", "EXECUTION_COST_CEILING", "THINKING", "MAX_OUTPUT_TOKENS"):
        if packet[key] != EXPECTED[key]:
            raise RefusedError("BOUND_PARAMETER_MOVED", f"{key} is {packet[key]!r}")
    for key in ("WEB", "TOOLS", "EXTERNAL_RETRIEVAL", "TRAINING", "FINE_TUNING", "EMBEDDINGS"):
        if packet[key] is not False:
            raise RefusedError("CAPABILITY_WIDENED", f"{key} is {packet[key]!r}")

    findings["12_ALL_BOUND_FIELDS_MATCH"] = True
    findings["VERIFIED_AT"] = dt.datetime.now(dt.UTC).isoformat()
    return {
        "findings": findings,
        "packet_file": packet,
        "packet": evidence_packet,
        "statements": statements,
        "evidence_to_claim": evidence_to_claim,
        "parts": parts,
        "prompt_hash": prompt_hash,
        "representation": representation,
    }


# --------------------------------------------------------------------- the single call


def execute(
    context: Mapping[str, Any],
    *,
    transport: Any = None,
    config: Any = None,
    pricing: Any = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """EXACTLY ONE provider request. No retry, no continuation, no repair.

    The approval and the consumed-approval guard are checked again here, because this function is
    callable directly. `transport`, `config`, `pricing` and `api_key` exist so the path can be
    exercised by synthetic fixtures; the real transport is built only when none was supplied.
    """
    from sros_llm_gateway.config import load_config_from_env
    from sros_llm_gateway.gateway import LlmGateway
    from sros_llm_gateway.pricing import load_pricing_from_env
    from sros_llm_gateway.transport import UrllibTransport

    packet = context["packet_file"]
    check_approval(str(packet["EXECUTION_PACKET_SHA256"]))
    refuse_if_consumed(str(packet["EXECUTION_PACKET_SHA256"]))

    v1 = v1_runner()
    recorder = v1.RecordingTransport(transport if transport is not None else UrllibTransport())
    telemetry: list = []
    gateway = LlmGateway(
        config=config if config is not None else load_config_from_env(),
        pricing=pricing if pricing is not None else load_pricing_from_env(),
        telemetry=telemetry.append,
    )
    gateway.register(build_provider(packet, recorder, api_key=api_key))
    request = build_request(context["parts"], packet)

    started = dt.datetime.now(dt.UTC)
    # ONE call. What arrived is captured and nothing is sent again: the only call site is this one.
    try:
        response = gateway.complete(request)
        failure = None
    except Exception as exc:  # noqa: BLE001 -- captured and recorded, never retried
        response = None
        failure = exc
    finished = dt.datetime.now(dt.UTC)

    return {
        "response": response,
        "failure": failure,
        "transport_responses": recorder.responses,
        "transport_errors": recorder.transport_errors,
        "telemetry": telemetry,
        "timing": {
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "elapsed_seconds": round((finished - started).total_seconds(), 3),
        },
    }


# --------------------------------------------------------------------- the ten stages


def _strings(value: object) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def response_payload(raw: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Stage 2. The provider's response shape: a JSON object with content and a stop reason."""
    try:
        payload = json.loads(str(raw["body"]))
    except ValueError as exc:
        return None, f"the response body is not JSON ({exc})"
    if not isinstance(payload, dict):
        return None, "the response body is not a JSON object"
    if not isinstance(payload.get("content"), list):
        return None, "`content` is not a list"
    if "stop_reason" not in payload:
        return None, "the response carries no `stop_reason`, so it cannot say whether it finished"
    return payload, None


def structured_output_of(payload: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Stage 4. Exactly one forced tool call carrying a JSON object."""
    from sros_llm_gateway.providers.anthropic import STRUCTURED_TOOL_NAME

    blocks = [
        b
        for b in payload.get("content") or []
        if isinstance(b, dict)
        and b.get("type") == "tool_use"
        and b.get("name") == STRUCTURED_TOOL_NAME
    ]
    if len(blocks) != 1:
        return None, f"{len(blocks)} structured tool calls, and exactly one is required"
    candidate = blocks[0].get("input")
    if not isinstance(candidate, dict):
        return None, "the structured tool call's input is not a JSON object"
    return candidate, None


def provenance_of(
    result: Mapping[str, Any], context: Mapping[str, Any], output: Mapping[str, Any]
) -> dict[str, object]:
    """Stage 8. What the first revision would have to carry, and whether this run has it."""
    raw = result["transport_responses"][0]
    packet = context["packet_file"]
    return {
        "execution_packet_sha256": packet.get("EXECUTION_PACKET_SHA256"),
        "selected_packet_id": packet.get("SELECTED_PACKET_ID"),
        "preparation_version": packet.get("PREPARATION_VERSION"),
        "representation_sha256": context.get("representation"),
        "prompt_sha256": context.get("prompt_hash"),
        "provider": packet.get("PROVIDER_ID"),
        "model": packet.get("MODEL_ID"),
        "raw_response_sha256": _sha256(str(raw["body"])),
        "provider_request_id": next(iter((raw.get("headers") or {}).values()), "NOT_EXPOSED"),
        "cited_evidence_ids": sorted(_strings(output.get("supporting_evidence_ids"))),
    }


def validate_execution(
    result: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    semantic_gate: Callable[[Mapping[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """The ten ordered stages. The first that fails decides, and no later stage runs.

    **The completion signal outranks the content.** Stage 3 reads `stop_reason` from the response
    this runner retained. The Gateway may already have parsed the tool input and even found every
    required key present -- a response cut at the limit can carry an object that looks whole -- and
    none of that is consulted when stage 3 refuses: stages 4 to 10 are recorded NOT_REACHED.
    """
    from sros_llm_gateway.providers.anthropic import (
        AnthropicCompletion,
        classify_forced_tool_completion,
    )
    from sros_opportunity.schema_validation import schema_violations
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        evaluate_second_opportunity_output_v1_1,
    )

    stages = {name: "NOT_REACHED" for name in STAGES}
    report: dict[str, Any] = {
        "stages": stages,
        "persist": False,
        "stop_reason": "NOT_AVAILABLE",
        "completion": "NOT_AVAILABLE",
        "failed_stage": None,
        "reasons": [],
    }

    def refuse(stage: str, outcome: str, reasons: list[str]) -> dict[str, Any]:
        stages[stage] = "FAILED"
        report.update(outcome=outcome, failed_stage=stage, reasons=reasons)
        return report

    responses = result.get("transport_responses") or []
    if not responses:
        failure = result.get("failure")
        name = type(failure).__name__ if failure is not None else "nothing recorded"
        outcome = (
            "EXECUTION_FAILED_TIMEOUT_NO_RETRY"
            if "Timeout" in name
            else "EXECUTION_FAILED_TRANSPORT_NO_RETRY"
        )
        return refuse(STAGES[0], outcome, [f"no response arrived ({name})"])
    raw = responses[0]
    if raw.get("status") != 200:
        return refuse(
            STAGES[0],
            "EXECUTION_FAILED_PROVIDER_ERROR_NO_RETRY",
            [f"the provider answered HTTP {raw.get('status')}"],
        )
    stages[STAGES[0]] = "PASSED"

    payload, error = response_payload(raw)
    if payload is None:
        return refuse(
            STAGES[1], "EXECUTION_OUTPUT_REJECTED_AT_RESPONSE_SHAPE_NO_RETRY", [str(error)]
        )
    stages[STAGES[1]] = "PASSED"

    stop_reason = payload.get("stop_reason")
    completion = classify_forced_tool_completion(stop_reason)
    report["stop_reason"] = stop_reason
    report["completion"] = completion.value
    if completion is not AnthropicCompletion.COMPLETE:
        outcome = {
            AnthropicCompletion.OUTPUT_LIMIT_REACHED: "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY",
            AnthropicCompletion.REFUSED: "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY",
            AnthropicCompletion.UNSUPPORTED_STOP_REASON: (
                "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
            ),
        }[completion]
        return refuse(
            STAGES[2],
            outcome,
            [
                f"stop_reason {stop_reason!r} is {completion.value}. The completion signal decides "
                "before any parse, and whatever arrived is not judged"
            ],
        )
    stages[STAGES[2]] = "PASSED"

    output, error = structured_output_of(payload)
    if output is None:
        return refuse(
            STAGES[3], "EXECUTION_OUTPUT_REJECTED_AT_STRUCTURED_PARSE_NO_RETRY", [str(error)]
        )
    stages[STAGES[3]] = "PASSED"

    violations = schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    if violations:
        return refuse(
            STAGES[4], "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY", list(violations)
        )
    stages[STAGES[4]] = "PASSED"

    gate = semantic_gate or (
        lambda out: evaluate_second_opportunity_output_v1_1(
            out, context["packet"], context["statements"], context["evidence_to_claim"]
        )
    )
    decision = gate(output)
    if str(output.get("decision") or "") == "INSUFFICIENT_EVIDENCE":
        stages[STAGES[5]] = "NO_HYPOTHESIS_FORMED"
        report.update(outcome=NO_HYPOTHESIS, reasons=list(decision.refusal_reasons))
        return report
    if not decision.persist:
        return refuse(
            STAGES[5],
            "EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY",
            list(decision.refusal_reasons),
        )
    stages[STAGES[5]] = "PASSED"

    # 7. Re-read, not re-implemented: the boundary is a set check, and no-distortion is the gate's
    # own audit, which must exist and must have no failed field.
    packet = context["packet"]
    stray = sorted(set(_strings(output.get("supporting_evidence_ids"))) - set(packet.evidence_ids))
    stray += sorted(set(_strings(output.get("supporting_claim_ids"))) - set(packet.claim_ids))
    audit = getattr(decision, "audit", None)
    failed_fields = [] if audit is None else [f.field_name for f in audit.failed]
    if stray or audit is None or failed_fields:
        reasons = [f"cited ids outside the packet: {stray}"] if stray else []
        if audit is None:
            reasons.append("the gate returned no audit, so no-distortion was not shown")
        reasons += [f"{name} audited as failed" for name in failed_fields]
        return refuse(STAGES[6], "EXECUTION_OUTPUT_REJECTED_AT_EVIDENCE_BOUNDARY_NO_RETRY", reasons)
    stages[STAGES[6]] = "PASSED"

    provenance = provenance_of(result, context, output)
    missing = [key for key, value in provenance.items() if value in (None, "", [])]
    if missing:
        return refuse(
            STAGES[7],
            "EXECUTION_OUTPUT_REJECTED_AT_ATTRIBUTION_NO_RETRY",
            [f"no {key}" for key in missing],
        )
    stages[STAGES[7]] = "PASSED"
    report["provenance"] = provenance

    stages[STAGES[8]] = "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"
    stages[STAGES[9]] = "REQUIRED_NOT_PERFORMED"
    report.update(outcome=ACCEPTED)
    return report


# --------------------------------------------------------------------- retention


def build_artifact(result: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    """Mission 1.84.2's repaired artifact, plus what V2 must keep that V1 did not.

    The raw body itself is kept (redacted, hidden reasoning stripped), not only its digest. The
    usage the provider reported is taken from the response as well as from the Gateway's
    telemetry, so a response the Gateway refused still says what it cost. The parsed tool input is
    kept wherever one exists, and whether any stage judged it is recorded beside it: a truncated
    object is evidence to keep and never an answer to accept.
    """
    v1 = v1_runner()
    responses = list(result.get("transport_responses") or [])
    payload = None
    structured = None
    if responses:
        try:
            parsed = json.loads(str(responses[0]["body"]))
            payload = parsed if isinstance(parsed, dict) else None
        except ValueError:
            payload = None
        if payload is not None:
            structured, _ = structured_output_of(payload)
    artifact = v1.build_execution_artifact(
        outcome=str(report["outcome"]),
        transport_responses=responses,
        transport_errors=list(result.get("transport_errors") or []),
        telemetry=list(result.get("telemetry") or []),
        structured=structured,
        failure=result.get("failure"),
        timing=dict(result.get("timing") or {}),
        validation=dict(report),
    )
    artifact["execution_packet_id"] = EXPECTED["EXECUTION_PACKET_ID"]
    artifact["execution_packet_sha256"] = EXPECTED["EXECUTION_PACKET_SHA256"]
    artifact["TERMINAL_OUTCOME"] = str(report["outcome"])
    artifact["STOP_REASON"] = report.get("stop_reason")
    artifact["PROVIDER_COMPLETION"] = report.get("completion")
    artifact["PARSED_OUTPUT_JUDGED"] = report["stages"][STAGES[3]] == "PASSED"
    if payload is not None:
        artifact["RAW_PROVIDER_RESPONSE_BODY"] = v1.strip_reasoning(payload)
        usage = payload.get("usage")
        artifact["USAGE_FROM_RESPONSE"] = usage if isinstance(usage, dict) else "NOT_REPORTED"
    elif responses:
        artifact["RAW_PROVIDER_RESPONSE_BODY"] = str(responses[0]["body"])
        artifact["USAGE_FROM_RESPONSE"] = "NOT_PARSEABLE"
    else:
        artifact["RAW_PROVIDER_RESPONSE_BODY"] = "NOT_AVAILABLE"
        artifact["USAGE_FROM_RESPONSE"] = "NOT_AVAILABLE"
    artifact["PERSISTED"] = "NOTHING"
    return artifact


# --------------------------------------------------------------------- entry point


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform the one approved request. Verification runs first regardless.",
    )
    parser.add_argument("--use-profile", default=USE_PROFILE)
    args = parser.parse_args(argv)

    print("=== pre-execution verification (execution packet V2)")
    try:
        context = verify(args.use_profile)
    except RefusedError as refusal:
        print(f"\nREFUSED  nothing was sent: {refusal}")
        return 1
    for key, value in context["findings"].items():
        print(f"    {key:38s} {value}")

    sha = str(context["packet_file"]["EXECUTION_PACKET_SHA256"])
    try:
        check_approval(sha)
        approval_state = "RECORDED"
    except RefusedError as refusal:
        approval_state = refusal.code
    print(f"    {'OPERATOR_APPROVAL':38s} {approval_state}")

    if not args.execute:
        print("\nverified. Nothing sent. An approval naming this digest is required to execute.")
        return 0

    try:
        check_approval(sha)
        refuse_if_consumed(sha)
        if RESPONSE_ARTIFACT.exists():
            raise RefusedError(
                "EXECUTION_ALREADY_PERFORMED", f"{RESPONSE_ARTIFACT.name} already exists"
            )
    except RefusedError as refusal:
        print(f"\nREFUSED  nothing was sent: {refusal}")
        return 1

    print("\n=== ONE provider request")
    result = execute(context)
    report = validate_execution(result, context)
    artifact = build_artifact(result, report)
    with RESPONSE_ARTIFACT.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
    print(f"    outcome        {report['outcome']}")
    print(f"    stop reason    {report['stop_reason']}")
    print(f"    wrote          {RESPONSE_ARTIFACT.name}")
    print("\n    NOTHING PERSISTED. HUMAN_OUTPUT_REVIEW_REQUIRED = true.")
    return 0 if report["outcome"] in (ACCEPTED, NO_HYPOTHESIS) else 2


if __name__ == "__main__":
    raise SystemExit(main())
