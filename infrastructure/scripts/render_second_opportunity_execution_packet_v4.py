"""Gate 81: execution packet V4, V3's call with prompt v1.3.0 and gate v1.3.0, frozen and unapproved.

Mission 1.84.12. The operator decided to align the prompt with the generation-relevant rules of the
unchanged semantic gate v1.3.0, under the unchanged schema v1.1.0, and to prepare exactly one more
call only if every deterministic stage from 6 to 9 is ready. This gate re-derives the packet:

    uv run python infrastructure/scripts/render_second_opportunity_execution_packet_v4.py --check

It refuses: bound fields that do not hash to the digest, a spent digest, or an approval recorded by
the mission that prepared the packet; V1, V2 or V3 edited, their consumption reset, or V3 treated as a
candidate; a prompt that is not v1.3.0 or that leaves a class-A semantic rule or a schema bound
unstated; a semantic-alignment or preflight record that moved or no longer validates; gate v1.3.0,
the schema or the TED representation moved; an approved evidence boundary that is not the snapshot's;
a route, model, thinking configuration, max_tokens, completion policy, timeout, retention or
persistence policy that moved from V3; stages that are not the ten with gate v1.3.0 at stage 6; a
request body that is not the one the snapshot rebuilds; a cost ceiling that is not the recomputed
worst case; a retention path no V4 runner test defines; a runner with more than one call site, that
slices, rewrites, drops or summarises the answer before judging it, whose semantic gate can be
injected, that expects another digest, that would execute V1's, V2's or V3's spent digest, or that
refuses an unseen one; and any preparation call, TED byte or canonical counter that moved.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import importlib.util
import inspect
import json
import math
import pathlib
import sys
from collections.abc import Iterator
from typing import Any, NamedTuple

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

from sros_llm_gateway.pricing import ModelPrice  # noqa: E402
from sros_llm_gateway.prompts.rendering import RenderedPrompt  # noqa: E402
from sros_llm_gateway.providers.anthropic import (  # noqa: E402
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
from sros_llm_gateway.types import LlmRequest, LlmTier  # noqa: E402
from sros_opportunity.output_constraints import OUTPUT_CONSTRAINT_RENDERER_VERSION  # noqa: E402
from sros_opportunity.second_opportunity import (  # noqa: E402
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_ID,
    render_second_opportunity_prompt_v1_2,
)
from sros_opportunity.second_opportunity_gate_v1_2 import build_trusted_context  # noqa: E402
from sros_opportunity.second_opportunity_gate_v1_3 import (  # noqa: E402
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
    build_source_metadata_context,
)
from sros_opportunity.second_opportunity_prompt_v1_3 import (  # noqa: E402
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_3,
    SECOND_OPPORTUNITY_SYSTEM_V1_3,
    render_second_opportunity_prompt_v1_3,
    second_opportunity_prompt_hash_v1_3,
)
from sros_opportunity.semantic_generation_rules import (  # noqa: E402
    OPERATOR_DECISION_SEMANTIC_PROMPT_ALIGNMENT,
    SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
    SEMANTIC_RULE_CENSUS_VERSION,
    SOURCE_LABEL_BLOCK_RENDERER_VERSION,
    policy_digest,
)

PACKET = DATA / "second-opportunity-synthesis-execution-packet-v4.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v4.md"
APPROVAL = DATA / "second-opportunity-synthesis-execution-approval-v4.json"
RUNNER = SCRIPTS / "run_second_opportunity_execution_v4.py"
RUNNER_V3 = SCRIPTS / "run_second_opportunity_execution_v3.py"
RUNNER_TESTS = (
    ROOT
    / "packages"
    / "opportunity-engine"
    / "python"
    / "tests"
    / "test_second_opportunity_execution_v4.py"
)
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
PACKET_V3 = DATA / "second-opportunity-synthesis-execution-packet-v3.json"
RECORD_V1 = DATA / "second-opportunity-synthesis-execution-record-v1.json"
RECORD_V2 = DATA / "second-opportunity-synthesis-execution-record-v2.json"
RECORD_V3 = DATA / "second-opportunity-synthesis-execution-record-v3.json"
REPLAY_V1_3 = DATA / "second-opportunity-v3-diagnostic-replay-gate-v1.3-v1.json"
SNAPSHOT_RECORD = DATA / "second-opportunity-v3-diagnostic-replay-v1.json"
PROMPT_V4 = DATA / "second-opportunity-synthesis-prompt-v4.json"
ALIGNMENT = DATA / "second-opportunity-semantic-prompt-alignment-v1.json"
PREFLIGHT = DATA / "second-opportunity-stage-6-9-preflight-v1.json"
DECISION = DATA / "second-opportunity-execution-envelope-decision-v1.json"
PREPARATION_V5 = DATA / "opportunity-preparation-v5.json"
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
PROVIDER_REGISTER = DATA / "model-provider-policy-v1.json"
GATE_76 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
GATE_77 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_3.py"
GATE_78 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay_v1_3.py"
GATE_79 = SCRIPTS / "render_second_opportunity_semantic_prompt_alignment.py"
GATE_80 = SCRIPTS / "render_second_opportunity_stage_6_9_preflight.py"

PACKET_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V4"
PACKET_VERSION = 4
PREPARED_BY = "mission-1.84.12"
THIS_MISSION = (1, 84, 12)
V1_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V1"
V2_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V2"
V3_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V3"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
SUBJECT = "ted-eu:CPV-class:9261"
MODEL = "claude-sonnet-5"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
PROMPT_V1_2_SHA256 = "1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d"
GATE_IMPLEMENTATION_SHA256 = "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3"
CHARS_PER_TOKEN = 2.1565
CONSERVATIVE_MULTIPLIER = 1.25
V3_WIRE_CHARACTERS = 22124

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

STAGE_CONDITIONS = {
    "6_semantic_output_gate_v1_3_0": (
        "gate v1.3.0 over the answer as it arrived, with the trusted context and the registry's "
        "source-metadata channel; fixed in the runner and never injectable"
    ),
    "7_evidence_boundary_and_no_distortion": (
        "every cited Evidence and Claim id inside the approved boundary this packet binds, each "
        "Evidence cited with its approved Claim, and gate v1.3.0's own v1.4.0 audit with no failed "
        "field"
    ),
    "8_attribution_and_provenance": (
        "every provenance field the first revision must carry is present, the request id read by "
        "its header name"
    ),
    "9_persistence_eligibility": (
        "the canonical OpportunityHypothesis (opportunity-hypothesis@1.0.0) constructs from the "
        "answer in memory; nothing is persisted, and an answer it refuses is not eligible for review"
    ),
    "10_human_review": "REQUIRED_NOT_PERFORMED: no machine stage stands in for the human review",
}

READY = "SECOND_OPPORTUNITY_EXECUTION_PACKET_V4_READY_FOR_OPERATOR_APPROVAL"

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
    "persistence_eligibility_failure",
    "human_review_ready_success",
)
RETENTION_PROPERTIES = (
    "usage_retained",
    "request_id_retained",
    "digests_retained",
    "cost_retained",
    "stages_retained",
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

LLM_REQUEST_FIELDS = frozenset(f.name for f in dataclasses.fields(LlmRequest))
ADAPTER_FIELDS = frozenset(f.name for f in dataclasses.fields(AnthropicProvider))

#: What the V4 digest binds. V3's fields, the gate that moved at stage 6, the prompt and the records
#: that justify it, and the approved evidence boundary stage 7 reads.
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
    "SEMANTIC_PROMPT_ALIGNMENT_DECISION",
    "SEMANTIC_PROMPT_ALIGNMENT_RECORD_SHA256",
    "STAGE_6_TO_9_PREFLIGHT_RECORD_SHA256",
    "SOURCE_DECISION_PACKET_ID",
    "SOURCE_DECISION_PACKET_VERSION",
    "SOURCE_DECISION_PACKET_SHA256",
    "SUBJECT_KEY",
    "SELECTED_PACKET_ID",
    "PREPARATION_VERSION",
    "PROCESSING_PURPOSE",
    "REPRESENTATION_SCHEMA",
    "REPRESENTATION_SHA256",
    "APPROVED_EVIDENCE_IDS",
    "APPROVED_CLAIM_IDS",
    "APPROVED_EVIDENCE_TO_CLAIM",
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
    "SEMANTIC_GENERATION_RULES_RENDERER",
    "SEMANTIC_RULE_CENSUS",
    "SOURCE_LABEL_BLOCK_RENDERER",
    "SEMANTIC_GENERATION_POLICY_DIGEST",
    "OUTPUT_SCHEMA_VERSION",
    "OUTPUT_SCHEMA_SHA256",
    "OUTPUT_GATE_VERSION",
    "SEMANTIC_GATE_IMPLEMENTATION_SHA256",
    "SCHEMA_CHANGED",
    "SEMANTIC_GATE_CHANGED_BY_THIS_MISSION",
    "OUTPUT_GATE_CHANGED_FROM_PREDECESSOR",
    "SOURCE_METADATA_CONTEXT_SHA256",
    "TRUSTED_CONTEXT_SHA256",
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
    "STAGE_CONDITIONS",
    "PERSISTENCE_POLICY",
    "HUMAN_REVIEW_REQUIRED",
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

#: Everything the packet carries beyond the digest-bound fields and the digest itself: its identity
#: and approval flags, the notes and cited bases, the figures derived from bound ones, V3's
#: observation, what verification found and the accounting. The set is closed, so a field nobody
#: reviewed (an "approved" flag, say) cannot ride along unbound and unchecked.
UNBOUND_FIELDS = (
    "$comment",
    "record_version",
    "prepared_by",
    "prepared_at",
    "PRIMARY_OUTCOME",
    "OPERATOR_EXECUTION_APPROVAL_RECORDED",
    "NEW_APPROVAL_REQUIRED",
    "PREVIOUS_APPROVAL_REUSABLE",
    "approval_note",
    "SUBJECT_LABEL",
    "REPRESENTATION_CHARACTER_COUNT",
    "boundary_note",
    "PROVIDER_SELECTION_BASIS",
    "MODEL_SELECTION_BASIS",
    "THINKING_POLICY_EXPLICIT",
    "ADAPTIVE_THINKING_USED",
    "THINKING_TOKENS_SHARE_OUTPUT_BUDGET",
    "thinking_note",
    "ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS",
    "adapter_default_note",
    "prompt_note",
    "gate_note",
    "estimate_note",
    "TOKEN_ESTIMATION_BASIS",
    "V3_OBSERVATION",
    "INPUT_PRICE_BASIS",
    "OUTPUT_PRICE_BASIS",
    "price_corroboration_note",
    "COST_UNIT_NOTE",
    "cost_ceiling_basis",
    "COST_NOT_EXPECTED_ACTUAL",
    "cost_note",
    "PREVIOUS_EXECUTION_COST_CEILING",
    "CEILING_DELTA_OVER_PREVIOUS",
    "CEILING_OVER_PREVIOUS_CEILING",
    "LARGER_THAN_PREVIOUS_CEILING",
    "ceiling_delta_note",
    "TIMEOUT",
    "validation_note",
    "structured_output_note",
    "tools_note",
    "RETENTION_REPAIR_VERIFIED",
    "RETENTION_VERIFIED_PATHS",
    "RETENTION_VERIFIED_PROPERTIES",
    "PREPARATION_VERIFICATION",
    "preparation_accounting",
    "CANONICAL_COUNTERS",
    "digest_covers",
)


class ValidationError(RuntimeError):
    """The packet disagrees with V3, with the records that justify it, or with live code."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def text_sha(path: pathlib.Path) -> str:
    """A record's digest over its text with LF line ends, whatever the checkout wrote."""
    return _sha256(path.read_text(encoding="utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze_gate() -> Any:
    """Gate 77, the one authority on gate v1.3.0's implementation digest."""
    return _module("gate_77_for_packet_v4", GATE_77)


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
    """Recompute the V4 execution digest from the packet's own bound fields."""
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


# --------------------------------------------------------------------------- the snapshot


class Snapshot(NamedTuple):
    """The authenticated packet and everything the prompt and the body are rebuilt from.

    A named tuple rather than a dataclass, because the V4 runner and the packet builder load this
    gate by path, without registering it as a module, and a dataclass resolves its annotations
    through the module registry."""

    packet: Any
    statements: dict[str, str]
    pairs: dict[str, str]
    metadata: Any
    trusted: Any
    parts_v1_2: Any
    parts_v1_3: Any
    representation_sha256: str


def snapshot() -> Snapshot:
    from sros_opportunity import (
        ExternalSynthesisDecision,
        SynthesisAvailability,
        serialize_packet_for_model,
    )

    gate_76 = _module("gate_76_for_packet_v4", GATE_76)
    packet, statements, pairs = gate_76.packet_from_snapshot(
        _load(SNAPSHOT_RECORD)["PACKET_SNAPSHOT"]
    )
    gate_76.authenticate(packet, statements, pairs)
    metadata = build_source_metadata_context(
        _module("gate_78_for_packet_v4", GATE_78).registry_entries(list(packet.source_ids))
    )
    measurement = ExternalSynthesisDecision(
        availability=SynthesisAvailability.AVAILABLE,
        packet_id=packet.packet_id,
        refusal_reasons=(),
        per_source=(("ted-eu", "RECOMPUTED_FOR_PACKET_V4"),),
    )
    representation = serialize_packet_for_model(packet, measurement, statements)
    if len(representation) != REPRESENTATION_CHARACTERS:
        raise ValidationError("the representation is not 3604 characters")
    return Snapshot(
        packet=packet,
        statements=statements,
        pairs=pairs,
        metadata=metadata,
        trusted=build_trusted_context(packet),
        parts_v1_2=render_second_opportunity_prompt_v1_2(packet, statements, pairs),
        parts_v1_3=render_second_opportunity_prompt_v1_3(
            packet, statements, pairs, source_metadata=metadata
        ),
        representation_sha256=_sha256(representation),
    )


class _NoTransport:
    def post_json(self, *args: object, **kwargs: object) -> Any:
        raise AssertionError("the gate builds a request body and never sends it")


def body_characters(parts: Any, packet: dict[str, Any], version: str) -> int:
    """len(json.dumps(body)) for these regions, built by the live adapter and never sent."""
    from sros_llm_gateway.prompts.rendering import UntrustedText

    params = packet["ADAPTER_PARAMETERS"]
    provider = AnthropicProvider(
        api_key="gate-probe-not-a-credential",
        max_output_tokens=int(params["max_output_tokens"]),
        thinking=AnthropicThinking[str(params["thinking"])],
        transport=_NoTransport(),
    )
    request = LlmRequest(
        tier=LlmTier.STRONG_MODEL,
        task=SECOND_OPPORTUNITY_PROMPT_ID,
        prompt_template_id=SECOND_OPPORTUNITY_PROMPT_ID,
        prompt_template_version=version,
        response_schema=SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        prompt=RenderedPrompt(
            system_instructions=parts.system_instructions,
            trusted_context=parts.trusted_context,
            untrusted=tuple(UntrustedText(content=c, label=label) for c, label in parts.untrusted),
            task=parts.task,
            metadata=parts.metadata,
        ),
        workspace_id="00000000-0000-4000-8000-000000000001",
        correlation_id="second-opportunity-synthesis-execution-v4",
        timeout_seconds=float(packet["REQUEST_TIMEOUT"]),
        max_retries=int(packet["GENERATION_PARAMETERS"]["max_retries"]),
        requires_structured_output=True,
    )
    return len(json.dumps(provider.build_body(request, MODEL)))


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
    if recomputed in (V1_SHA256, V2_SHA256, V3_SHA256):
        raise ValidationError("V4 carries a spent predecessor's digest")
    note = str(packet["approval_note"])
    for word in ("egress", "V3", "beside", "prompt", "gate"):
        if word not in note:
            raise ValidationError(
                "the approval note does not keep this approval apart from V1's, V2's and V3's, "
                "from the prompt and gate decisions and from TED egress"
            )
    if (
        packet["EXECUTION_ENVELOPE_DECISION_SHA256"]
        != _load(PACKET_V3)["EXECUTION_ENVELOPE_DECISION_SHA256"]
    ):
        raise ValidationError("the envelope decision moved from V3")
    if APPROVAL.exists():
        approval = _load(APPROVAL)
        author = _mission_key(approval.get("recorded_by"))
        if author is None or author <= THIS_MISSION:
            raise ValidationError(
                "an approval of V4 recorded by the mission that prepared it. Preparing a packet "
                "authorises nothing, and the operator approves it separately"
            )
        if approval.get("EXECUTION_PACKET_SHA256") != recomputed:
            raise ValidationError("an approval on disk names a digest other than V4's")
    return recomputed


def _check_predecessors(packet: dict[str, Any]) -> None:
    v1, v2, v3 = _load(PACKET_V1), _load(PACKET_V2), _load(PACKET_V3)
    record_v1, record_v2, record_v3 = _load(RECORD_V1), _load(RECORD_V2), _load(RECORD_V3)
    for name, frozen, digest in (
        ("V1", v1, V1_SHA256),
        ("V2", v2, V2_SHA256),
        ("V3", v3, V3_SHA256),
    ):
        if frozen["EXECUTION_PACKET_SHA256"] != digest:
            raise ValidationError(f"{name}'s packet digest moved")
        if frozen["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is not False:
            raise ValidationError(f"the frozen {name} packet was edited to record an approval")
    for name, record in (("V1", record_v1), ("V2", record_v2), ("V3", record_v3)):
        if record["EXECUTION_APPROVAL_CONSUMED"] is not True:
            raise ValidationError(f"{name}'s consumption was reset")
    if record_v3["FURTHER_CALLS_AUTHORIZED_BY_V3"] is not False:
        raise ValidationError("V3 now authorises further calls")
    if record_v3["execution_packet_sha256"] != V3_SHA256:
        raise ValidationError("V3's record names another digest")
    if (
        record_v3["HUMAN_REVIEW_PACKET"] != "NOT_PRODUCED"
        or record_v3["OPPORTUNITY_PERSISTED"] is not False
        or record_v3["CANONICAL_PERSISTENCE"] is not False
    ):
        raise ValidationError(
            "V3's record now treats its refused answer as a candidate. V4 is a new call with a new "
            "prompt, never a second chance for V3's answer"
        )
    replay = _load(REPLAY_V1_3)
    _fixed(
        replay,
        {
            "V3_CANDIDATE": False,
            "V3_PERSISTABLE": False,
            "V3_HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
            "V3_APPROVAL_CONSUMED": True,
            "EXECUTION_PACKET_V4": "NOT_CREATED",
        },
        "the v1.3.0 diagnostic replay record",
    )
    _fixed(
        packet,
        {
            "PREDECESSOR_EXECUTION_PACKET_ID": V3_ID,
            "PREDECESSOR_EXECUTION_PACKET_SHA256": V3_SHA256,
            "PREDECESSOR_EXECUTION_OUTCOME": record_v3["PRIMARY_OUTCOME"],
            "PREDECESSOR_APPROVAL_CONSUMED": True,
            "CONSUMED_EXECUTION_PACKETS": [
                {"id": V1_ID, "sha256": V1_SHA256, "outcome": record_v1["PRIMARY_OUTCOME"]},
                {"id": V2_ID, "sha256": V2_SHA256, "outcome": record_v2["PRIMARY_OUTCOME"]},
                {"id": V3_ID, "sha256": V3_SHA256, "outcome": record_v3["PRIMARY_OUTCOME"]},
            ],
        },
        "packet",
    )
    if record_v3["PRIMARY_OUTCOME"] != "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY":
        raise ValidationError("V3's outcome is recorded as something other than its gate refusal")


# --------------------------------------------------------------------------- what changed


def _check_prompt(packet: dict[str, Any], snap: Snapshot) -> None:
    prompt = _load(PROMPT_V4)
    alignment = _load(ALIGNMENT)
    v3 = _load(PACKET_V3)
    live = second_opportunity_prompt_hash_v1_3(snap.parts_v1_3)
    _fixed(
        packet,
        {
            "PROMPT_ALIGNMENT_DECISION": v3["PROMPT_ALIGNMENT_DECISION"],
            "PROMPT_ALIGNMENT_RECORD_SHA256": v3["PROMPT_ALIGNMENT_RECORD_SHA256"],
            "SEMANTIC_PROMPT_ALIGNMENT_DECISION": list(OPERATOR_DECISION_SEMANTIC_PROMPT_ALIGNMENT),
            "SEMANTIC_PROMPT_ALIGNMENT_RECORD_SHA256": text_sha(ALIGNMENT),
            "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
            "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_3,
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
    if prompt["PROMPT_SHA256"] != live or prompt["PROMPT_VERSION"] != "1.3.0":
        raise ValidationError("the prompt document is not the live v1.3.0 prompt")
    if prompt["SYSTEM_INSTRUCTION"] != SECOND_OPPORTUNITY_SYSTEM_V1_3:
        raise ValidationError("the prompt document's system region is not the live v1.3.0 one")
    spent = {_load(p)["PROMPT_SHA256"] for p in (PACKET_V1, PACKET_V2, PACKET_V3)}
    if live in spent or prompt["PREDECESSOR_PROMPT_SHA256"] != PROMPT_V1_2_SHA256:
        raise ValidationError(
            "V4 binds a prompt a spent packet already sent, or a wrong predecessor"
        )
    if alignment["UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES"] != 0:
        raise ValidationError("the aligned prompt still leaves a class-A semantic rule unstated")
    if alignment["PROMPT_V1_3_SHA256"] != live:
        raise ValidationError("the alignment record names another prompt")
    gate_79 = _module("gate_79_for_packet_v4", GATE_79)
    try:
        gate_79.validate()
    except gate_79.ValidationError as exc:
        raise ValidationError(f"gate 79 no longer validates: {exc}") from exc


def _check_preflight(packet: dict[str, Any]) -> None:
    gate_80 = _module("gate_80_for_packet_v4", GATE_80)
    try:
        record = gate_80.validate()
    except gate_80.ValidationError as exc:
        raise ValidationError(f"DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY: {exc}") from exc
    if record["OUTCOME"] != gate_80.READY or record["VALID_FIXTURE_REACHES_STAGE_9"] is not True:
        raise ValidationError("DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY")
    if packet["STAGE_6_TO_9_PREFLIGHT_RECORD_SHA256"] != text_sha(PREFLIGHT):
        raise ValidationError("the preflight record changed after the packet bound it")


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
            "OUTPUT_GATE_CHANGED_FROM_PREDECESSOR": True,
            "CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL": False,
            "ESTIMATE_EXACT": False,
            "LOCAL_SCHEMA_VALIDATOR_MANDATORY": True,
        },
        "packet",
    )
    v3 = _load(PACKET_V3)
    for key in ("OUTPUT_SCHEMA_VERSION", "OUTPUT_SCHEMA_SHA256"):
        if packet[key] != v3[key]:
            raise ValidationError(f"{key} moved from V3, and the operator kept the schema")
    if v3["OUTPUT_GATE_VERSION"] == packet["OUTPUT_GATE_VERSION"]:
        raise ValidationError("V4 binds V3's gate, v1.1.0, which refused the answer V3 received")
    if (
        packet["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"]
        != v3["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"]
    ):
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
            "an answer may be changed to fit a bound or a rule. Truncation, dropping, rewriting, "
            "summarising, splitting and normalising are all refused"
        )


def _check_representation(packet: dict[str, Any], snap: Snapshot) -> None:
    v3 = _load(PACKET_V3)
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
    ):
        if packet[key] != v3[key]:
            raise ValidationError(f"{key} is not what the approved egress rests on")
    if (
        packet["REPRESENTATION_SHA256"] != REPRESENTATION_SHA256
        or snap.representation_sha256 != REPRESENTATION_SHA256
    ):
        raise ValidationError(
            "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED: the representation is not the approved one"
        )
    if snap.packet.packet_id != packet["SELECTED_PACKET_ID"]:
        raise ValidationError("the snapshot is not the selected packet")
    _fixed(
        packet,
        {
            "APPROVED_EVIDENCE_IDS": list(snap.packet.evidence_ids),
            "APPROVED_CLAIM_IDS": list(snap.packet.claim_ids),
            "APPROVED_EVIDENCE_TO_CLAIM": {
                e: snap.pairs[e] for e in snap.packet.evidence_ids if e in snap.pairs
            },
            "SOURCE_METADATA_CONTEXT_SHA256": snap.metadata.digest(),
            "TRUSTED_CONTEXT_SHA256": snap.trusted.digest(),
        },
        "packet",
    )
    verified = packet["PREPARATION_VERIFICATION"]
    _fixed(
        verified,
        {
            "representation_sha256": REPRESENTATION_SHA256,
            "representation_characters": REPRESENTATION_CHARACTERS,
            "prompt_sha256": packet["PROMPT_SHA256"],
            "v1_2_prompt_sha256_recomputed": PROMPT_V1_2_SHA256,
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
            "v3_request_body_characters_recomputed": V3_WIRE_CHARACTERS,
            "unstated_generation_constraints": 0,
            "unstated_generation_relevant_semantic_rules": 0,
            "pricing_version": packet["PRICING_VERSION"],
            "worst_case_from_the_configured_table": packet["WORST_CASE_CALL_COST"],
            "source_metadata_context_sha256": packet["SOURCE_METADATA_CONTEXT_SHA256"],
            "trusted_context_sha256": packet["TRUSTED_CONTEXT_SHA256"],
            "semantic_gate_implementation_sha256": GATE_IMPLEMENTATION_SHA256,
            "v1_guard_refuses_v1": True,
            "v2_guard_refuses_v2": True,
            "v3_guard_refuses_v3": True,
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


# --------------------------------------------------------------------------- V3's call, unchanged


def _check_route(packet: dict[str, Any]) -> None:
    register = _load(PROVIDER_REGISTER)
    approved = sorted(
        str(e["provider_id"]) for e in register["providers"] if e.get("posture") == "APPROVED"
    )
    if approved != ["anthropic"]:
        raise ValidationError(
            f"PROVIDER_ROUTE_NO_LONGER_APPROVED: the register approves {approved}"
        )
    v3 = _load(PACKET_V3)
    for key in (
        "PROVIDER_ID",
        "PROVIDER_POSTURE",
        "PROVIDER_ROUTE",
        "PROVIDER_ROUTE_SURFACE",
        "BETA_HEADERS",
        "ROUTES_NOT_USED",
        "MODEL_ID",
        "MODEL_TIER",
        "MAX_OUTPUT_TOKENS",
        "OUTPUT_TOKEN_CEILING",
        "MAX_OUTPUT_TOKENS_BASIS",
        "OUTPUT_TOKEN_CEILING_BASIS",
        "ADAPTER_PARAMETERS",
        "ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS",
    ):
        if packet[key] != v3[key]:
            raise ValidationError(f"{key} moved from V3")
    if (
        packet["PROVIDER_ROUTE_SURFACE"] != f"POST {DEFAULT_ENDPOINT}"
        or packet["MODEL_ID"] != MODEL
    ):
        raise ValidationError("the route or the model is not the reviewed one")
    if tuple(packet["MAX_OUTPUT_TOKENS_NOT_BASED_ON"]) != (
        *v3["MAX_OUTPUT_TOKENS_NOT_BASED_ON"],
        "V3_OBSERVED_OUTPUT_TOKENS",
    ):
        raise ValidationError("the ceiling's basis no longer excludes V3's observed output")
    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if packet["MAX_OUTPUT_TOKENS"] != capability["DOCUMENTED_MAX_OUTPUT_TOKENS"]:
        raise ValidationError("max_tokens is not the documented synchronous maximum")


def _check_thinking_and_envelope(packet: dict[str, Any], snap: Snapshot) -> None:
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
    params = packet["ADAPTER_PARAMETERS"]
    if set(params) != {"max_output_tokens", "thinking"} or not set(params) <= ADAPTER_FIELDS:
        raise ValidationError(f"adapter parameters {sorted(params)}; V4 binds exactly two")
    provider = AnthropicProvider(
        api_key="gate-probe-not-a-credential",
        max_output_tokens=int(params["max_output_tokens"]),
        thinking=AnthropicThinking[str(params["thinking"])],
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
    body = provider.build_body(request, MODEL)
    if body.get("thinking") != {"type": "disabled"}:
        raise ValidationError(f"THINKING_CONTROL_NO_LONGER_VALID: {body.get('thinking')!r}")
    if body.get("max_tokens") != packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError(f"the adapter sends max_tokens {body.get('max_tokens')}")
    if body.get("tool_choice") != {"type": "tool", "name": STRUCTURED_TOOL_NAME}:
        raise ValidationError("the structured output is no longer forced into its tool")
    if "output_config" in body or "strict" in body["tools"][0]:
        raise ValidationError("a structured-output migration rode along with the prompt change")


def _check_completion_policy(packet: dict[str, Any]) -> None:
    policy = packet["PROVIDER_COMPLETION_POLICY"]
    if policy != _load(PACKET_V3)["PROVIDER_COMPLETION_POLICY"]:
        raise ValidationError("the provider completion policy moved from V3")
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
        },
        "PROVIDER_COMPLETION_POLICY",
    )
    for value in policy["output_limit_values"]:
        if classify_forced_tool_completion(value) is not AnthropicCompletion.OUTPUT_LIMIT_REACHED:
            raise ValidationError(f"PROVIDER_LIMIT_SIGNAL_NOT_FAIL_CLOSED: {value!r}")
    for probe in ("end_turn", "pause_turn", "stop_sequence", None, "a_value_added_later"):
        if (
            classify_forced_tool_completion(probe)
            is not AnthropicCompletion.UNSUPPORTED_STOP_REASON
        ):
            raise ValidationError(f"PROVIDER_LIMIT_SIGNAL_NOT_FAIL_CLOSED: {probe!r} is known")
    if tuple(packet["VALIDATION_STAGES"]) != STAGES:
        raise ValidationError(
            "the validation stages are not the ten, in order, with gate v1.3.0 at stage 6"
        )
    if packet["STAGE_CONDITIONS"] != STAGE_CONDITIONS:
        raise ValidationError("the stage conditions are not the ones the V4 runner implements")
    if packet["output_limit_outcome"] != policy["on_output_limit"]:
        raise ValidationError("the packet's output-limit outcome is not the policy's")
    if packet["failure_outcome"] != "EXECUTION_FAILED_NO_RETRY":
        raise ValidationError("a failure outcome that is not a stop")


def _check_calls_and_timeout(packet: dict[str, Any]) -> None:
    params = packet["GENERATION_PARAMETERS"]
    if params != _load(PACKET_V3)["GENERATION_PARAMETERS"]:
        raise ValidationError("the generation parameters moved from V3")
    supplied = {k: v for k, v in params.items() if k != "$comment" and not k.endswith("note")}
    for key, value in supplied.items():
        if value is not None and key not in LLM_REQUEST_FIELDS:
            raise ValidationError(f"{key!r} is frozen with a value nothing reads")
    if supplied.get("max_retries") != 0 or packet["MAX_RETRIES"] != 0:
        raise ValidationError("a retry is a second call, and V4 authorises one")
    if packet["MAX_MODEL_CALLS"] != 1:
        raise ValidationError(f"MAX_MODEL_CALLS is {packet['MAX_MODEL_CALLS']}")
    for key in CALL_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if packet["REQUEST_TIMEOUT"] != _load(PACKET_V3)["REQUEST_TIMEOUT"]:
        raise ValidationError("the timeout moved from V3")
    elapsed = _load(RECORD_V3)["timing"]["elapsed_seconds"]
    _fixed(
        packet["TIMEOUT"],
        {
            "REQUEST_TIMEOUT_SECONDS": packet["REQUEST_TIMEOUT"],
            "TIMEOUT_CHANGED_BY_THIS_MISSION": False,
            "V3_OBSERVED_ELAPSED_SECONDS": elapsed,
            "V3_OBSERVATION_USED_TO_CHANGE_THE_TIMEOUT": False,
            "STREAMING": False,
            "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
            "TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS": True,
            "ON_TIMEOUT": "EXECUTION_FAILED_TIMEOUT_NO_RETRY",
        },
        "TIMEOUT",
    )


def _check_cost(packet: dict[str, Any], snap: Snapshot) -> None:
    v3 = _load(PACKET_V3)
    record_v3 = _load(RECORD_V3)
    if (
        packet["PRICING_VERSION"] != v3["PRICING_VERSION"]
        or packet["PRICE_PER_1K"] != v3["PRICE_PER_1K"]
    ):
        raise ValidationError("MODEL_COST_BASIS_REQUIRES_REFRESH: the price moved from V3")
    price = packet["PRICE_PER_1K"]
    held = ModelPrice(input_per_1k=float(price["input"]), output_per_1k=float(price["output"]))
    v3_wire = body_characters(snap.parts_v1_2, packet, "1.2.0")
    if v3_wire != V3_WIRE_CHARACTERS:
        raise ValidationError(
            f"V3's body rebuilds to {v3_wire} characters, not the {V3_WIRE_CHARACTERS} it sent: the "
            "method no longer reproduces the call it is compared with"
        )
    wire = body_characters(snap.parts_v1_3, packet, SECOND_OPPORTUNITY_PROMPT_VERSION_V1_3)
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
            "v3_wire_characters": V3_WIRE_CHARACTERS,
            "prompt_delta_characters": wire - V3_WIRE_CHARACTERS,
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
    if packet["TOTAL_TOKEN_CEILING"] != expected + output:
        raise ValidationError("the total token ceiling is not the sum of its parts")
    if packet["INPUT_WORST_CASE_COST"] != held.cost_for(expected, 0):
        raise ValidationError("the input worst case is not recomputable")
    if packet["OUTPUT_WORST_CASE_COST"] != held.cost_for(0, output):
        raise ValidationError("the output worst case is not recomputable")
    total = held.cost_for(expected, output)
    if packet["WORST_CASE_CALL_COST"] != total:
        raise ValidationError("the worst-case call cost is not recomputable")
    if packet["EXECUTION_COST_CEILING"] != total or packet["HEADROOM_POLICY"] != "NONE_HELD":
        raise ValidationError("a ceiling other than the worst case itself")
    if packet["COST_NOT_EXPECTED_ACTUAL"] is not True:
        raise ValidationError("the worst case is presented as an expected cost")
    previous = float(v3["EXECUTION_COST_CEILING"])
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
    usage = record_v3["ACTUAL_USAGE"]
    _fixed(
        packet["V3_OBSERVATION"],
        {
            "V3_INPUT_TOKEN_ESTIMATE": v3["INPUT_TOKEN_ESTIMATE"],
            "V3_ACTUAL_INPUT_TOKENS": usage["input_tokens"],
            "V3_ESTIMATE_COVERED_THE_ACTUAL": v3["INPUT_TOKEN_ESTIMATE"] >= usage["input_tokens"],
            "V3_ACTUAL_OUTPUT_TOKENS": usage["output_tokens"],
            "USED_TO_CHANGE_THE_ESTIMATION_METHOD": False,
            "USED_TO_REDUCE_MAX_OUTPUT_TOKENS": False,
        },
        "V3_OBSERVATION",
    )


def _check_boundaries(packet: dict[str, Any]) -> None:
    v3 = _load(PACKET_V3)
    for key in CAPABILITY_NEGATIVES:
        if packet[key] is not False:
            raise ValidationError(f"{key} is {packet[key]!r}")
    if packet["RETENTION_ON_EXECUTION"] != v3["RETENTION_ON_EXECUTION"]:
        raise ValidationError("the retention policy moved from V3's repaired one")
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
                raise ValidationError(f"{path} names {test!r}, which no V4 runner test defines")
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
            raise ValidationError(f"{key} is {accounting.get(key)}, and preparing V4 does 0")
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
            f"the V4 runner has {len(calls)} model call sites, and V4 is one call"
        )
    holder: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in enclosing(calls[0]):
        if isinstance(node, _LOOPS):
            raise ValidationError("the V4 runner's one call site sits inside a loop")
        if holder is None and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            holder = node
    if holder is None:
        raise ValidationError("the V4 runner's call site is not inside a function")
    callers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == holder.name
    ]
    if len(callers) > 1:
        raise ValidationError(f"{holder.name}() is called {len(callers)} times, and V4 is one call")
    for caller in callers:
        chain = list(enclosing(caller))
        if holder in chain or any(isinstance(node, _LOOPS) for node in chain):
            raise ValidationError(
                f"{holder.name}() is re-entered, which is a retry by another name"
            )


_READ_ONLY_METHODS = frozenset({"get", "items", "keys", "values"})


def _rooted_at_output(node: ast.AST) -> bool:
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return isinstance(node, ast.Name) and node.id == "output"


def _check_no_post_processing(source: str) -> None:
    """The answer is judged as it arrived: nothing slices a value, nothing reassigns or edits it."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Slice):
            raise ValidationError(
                f"the V4 runner slices a value on line {node.lineno}. An answer over a bound is "
                "refused, never trimmed to fit"
            )
    judges = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in ("validate_execution", "dry_hypothesis")
    ]
    if len(judges) != 2:
        raise ValidationError("the V4 runner has no stage function or no stage-9 construction")
    for judge in judges:
        bindings = 0
        for node in ast.walk(judge):
            if isinstance(node, ast.Delete) and any(_rooted_at_output(t) for t in node.targets):
                raise ValidationError(f"{judge.name} deletes from the parsed answer")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and _rooted_at_output(node.func.value)
                and node.func.attr not in _READ_ONLY_METHODS
            ):
                raise ValidationError(
                    f"{judge.name} calls {node.func.attr} on the parsed answer on line "
                    f"{node.lineno}. Only reads are allowed"
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
                        raise ValidationError(f"{judge.name} writes into the parsed answer")
        expected = 1 if judge.name == "validate_execution" else 0
        if bindings != expected:
            raise ValidationError(
                f"{judge.name} binds the parsed answer {bindings} times; a second binding is where "
                "a rewritten answer would replace the one that arrived"
            )


def _check_runner(packet: dict[str, Any], snap: Snapshot) -> None:
    source = RUNNER.read_text(encoding="utf-8")
    _check_single_call_site(source)
    _check_no_post_processing(source)
    runner = _module("execution_runner_v4_for_gate", RUNNER)
    if runner.EXPECTED["EXECUTION_PACKET_SHA256"] != packet["EXECUTION_PACKET_SHA256"]:
        raise ValidationError("the runner was prepared for another digest")
    for key, value in runner.EXPECTED.items():
        if key in packet and packet[key] != value:
            raise ValidationError(
                f"the runner expects {key}={value!r} and V4 binds {packet[key]!r}"
            )
    if tuple(runner.STAGES) != STAGES:
        raise ValidationError("the runner's stages are not the gate's")
    if list(inspect.signature(runner.validate_execution).parameters) != ["result", "context"]:
        raise ValidationError("the runner's semantic gate can be injected")
    if runner.APPROVAL_FILE.name != APPROVAL.name or runner.PROMPT_DOCUMENT.name != PROMPT_V4.name:
        raise ValidationError("the runner reads its approval or its prompt from somewhere else")
    for label, digest in (("V1", V1_SHA256), ("V2", V2_SHA256), ("V3", V3_SHA256)):
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
    if runner.unstated_semantic_rules(snap.parts_v1_3) or runner.unstated_constraints(
        snap.parts_v1_3.system_instructions
    ):
        raise ValidationError("the runner finds prompt v1.3.0 leaving a rule or a bound unstated")
    if not runner.unstated_semantic_rules(snap.parts_v1_2):
        raise ValidationError("the runner's semantic drift check would pass prompt v1.2.0")


def validate() -> dict[str, Any]:
    packet = _load(PACKET)
    snap = snapshot()
    _check_identity_and_approval(packet)
    _check_predecessors(packet)
    _check_prompt(packet, snap)
    _check_preflight(packet)
    _check_contract(packet)
    _check_representation(packet, snap)
    _check_route(packet)
    _check_thinking_and_envelope(packet, snap)
    _check_completion_policy(packet)
    _check_calls_and_timeout(packet)
    _check_cost(packet, snap)
    _check_boundaries(packet)
    _check_accounting(packet)
    _check_runner(packet, snap)
    return packet


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_execution_packet_v4.py "
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
    policy = packet["PROVIDER_COMPLETION_POLICY"]
    observed = packet["V3_OBSERVATION"]
    out = [
        HEADER.format(source=PACKET.name),
        "# Second opportunity: synthesis execution packet v4",
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
                f"representation sha256               {packet['REPRESENTATION_SHA256']}",
                f"representation characters           {packet['REPRESENTATION_CHARACTER_COUNT']}",
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
                "human_review_required               "
                f"{str(packet['HUMAN_REVIEW_REQUIRED']).lower()}",
                f"canonical_persistence               {packet['PERSISTENCE_POLICY']['canonical_persistence']}",
                "OPERATOR_EXECUTION_APPROVAL_RECORDED "
                f"{str(packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']).lower()}",
                "NEW_APPROVAL_REQUIRED               "
                f"{str(packet['NEW_APPROVAL_REQUIRED']).lower()}",
                "PREVIOUS_APPROVAL_REUSABLE          "
                f"{str(packet['PREVIOUS_APPROVAL_REUSABLE']).lower()}",
            ]
        ),
        "## What changed from V3",
        "",
        f"Prompt v{packet['PROMPT_VERSION']}: {_sentence(packet['prompt_note'])} The semantic gate "
        f"at stage 6 is `{packet['OUTPUT_GATE_VERSION']}`, unchanged by this mission. Under the "
        "operator's decision "
        + ", ".join(f"`{d}`" for d in packet["SEMANTIC_PROMPT_ALIGNMENT_DECISION"])
        + ".",
        "",
        "| stage | condition |",
        "|---|---|",
        *[f"| `{stage}` | {text} |" for stage, text in packet["STAGE_CONDITIONS"].items()],
        "",
        "## Everything else is V3's",
        "",
        f"Signal: `{policy['signal_field']}`. Complete: "
        f"{', '.join(f'`{v}`' for v in policy['complete_values'])}. Output limit: "
        f"{', '.join(f'`{v}`' for v in policy['output_limit_values'])}. Refusal: "
        f"{', '.join(f'`{v}`' for v in policy['refusal_values'])}. Anything else fails closed. "
        "Read before any parse.",
        "",
        "## Cost, recomputed from the new request body",
        "",
        *_code(
            [
                f"request body             {basis['wire_characters']} characters  "
                f"(V3 {basis['v3_wire_characters']} + prompt {basis['prompt_delta_characters']})",
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
                f"previous ceiling (V3)    {_cost(packet['PREVIOUS_EXECUTION_COST_CEILING'])}  "
                f"(+{_cost(packet['CEILING_DELTA_OVER_PREVIOUS'])}, "
                f"x{packet['CEILING_OVER_PREVIOUS_CEILING']})",
            ]
        ),
        f"V3 estimated {observed['V3_INPUT_TOKEN_ESTIMATE']} input tokens and used "
        f"{observed['V3_ACTUAL_INPUT_TOKENS']}; it used {observed['V3_ACTUAL_OUTPUT_TOKENS']} "
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
    print(
        "ok       packet V4 is V3's call with prompt v1.3.0 and gate v1.3.0, and matches live code"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
