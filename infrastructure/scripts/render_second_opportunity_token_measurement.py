"""Mission 1.84.5, CI gate 69. The provider-native token measurement, re-derived where it can be.

Three records are checked against each other and against live code:

* the RECEIPT the one-shot runner wrote when it sent the one count request;
* the MEASUREMENT record, which carries the estimate, the documentation it rests on, and what it
  does and does not establish;
* the provider-model capability REGISTER, which keeps the model's documented maximum and this
  repository's adapter default side by side and never one in place of the other.

**What is re-derived rather than read.** The measured text is rebuilt from the live schema through
the Mission 1.84.4 builder, so a schema change fails here. The adapter's default budget, its thinking
configurations and its request bodies are read from the live provider. The headroom, the ratio and
the empirical cross-check are recomputed. The outcome is recomputed from the estimate and the
documented maximum, so a record that called an over-capacity estimate ready would fail.

**What cannot be re-derived, and is only checked for shape.** The documentation evidence: CI has no
network, and refetching would be a request this gate has no authority to make. Each entry carries
its final URL, retrieval instant, byte count and SHA-256, and each proposition cites fragments by
evidence id and line, so a later reader can refetch and compare.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import re
from collections.abc import Iterator
from typing import Any

from sros_llm_gateway.prompts.rendering import RenderedPrompt
from sros_llm_gateway.providers.anthropic import (
    COUNT_TOKENS_ENDPOINT,
    AnthropicProvider,
    AnthropicThinking,
)
from sros_llm_gateway.types import LlmRequest, LlmTier

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

MEASUREMENT = DATA / "second-opportunity-provider-token-measurement-v1.json"
MEASUREMENT_MD = DATA / "second-opportunity-provider-token-measurement-v1.md"
REGISTER = DATA / "provider-model-capability-register-v1.json"
REGISTER_MD = DATA / "provider-model-capability-register-v1.md"
RECEIPT = DATA / "second-opportunity-token-measurement-receipt-v1.json"

EXECUTION_RECORD_V1 = DATA / "second-opportunity-synthesis-execution-record-v1.json"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"


#: Mission 1.84.6. This mission recorded that IT created no execution packet V2. A V2 that a later
#: mission prepared does not make that false, so the check reads the packet's author instead of
#: requiring the file to be absent: a check pinned to an absence pins the repository's future to
#: one mission's verdict.
THIS_MISSION = (1, 84, 5)


def _v2_prepared_by_a_later_mission() -> bool:
    try:
        prepared_by = json.loads(PACKET_V2.read_text(encoding="utf-8")).get("prepared_by")
    except (OSError, ValueError, AttributeError):
        return False
    if not isinstance(prepared_by, str) or not prepared_by.startswith("mission-"):
        return False
    try:
        return tuple(int(part) for part in prepared_by.removeprefix("mission-").split(".")) > (
            THIS_MISSION
        )
    except ValueError:
        return False


CAPACITY_V2 = DATA / "second-opportunity-output-capacity-analysis-v2.json"
PROMPT_V2 = DATA / "second-opportunity-synthesis-prompt-v2.json"

MODEL = "claude-sonnet-5"
MODEL_MAX_OUTPUT_TOKENS = 128000
BATCH_BETA_MAX_OUTPUT_TOKENS = 300000
HELD_RATIO = 2.1565
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
ROOT_CAUSE_1_84_2 = "NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS"
DOCS_PREFIX = "https://platform.claude.com/docs/en/"

ACCEPTABLE_OUTCOMES = (
    "PROVIDER_NATIVE_TOKEN_ESTIMATE_READY_OPERATOR_HEADROOM_DECISION_REQUIRED",
    "BOUNDED_SCHEMA_EXCEEDS_OR_APPROACHES_MODEL_CAPABILITY",
    "SECOND_OPPORTUNITY_EXECUTION_PACKET_V2_READY_FOR_OPERATOR_APPROVAL",
    "TOKEN_MEASUREMENT_FAILED_NO_RETRY",
    "THINKING_CONTROL_REQUIRES_ARCHITECTURE_DECISION",
    "BOUNDED_OUTPUT_MAX_INSTANCE_CHANGED",
)
EXCEEDS = "BOUNDED_SCHEMA_EXCEEDS_OR_APPROACHES_MODEL_CAPABILITY"

PROPOSITIONS = (
    "A_MODEL_ID",
    "B_MAX_OUTPUT",
    "C_TOKENIZER",
    "D_TOKEN_COUNT_BEHAVIOUR",
    "E_TOKENIZER_USED_BY_THE_COUNT",
    "F_COUNT_IS_NOT_MESSAGE_CREATION",
    "G_BILLING",
    "H_SEPARATE_RATE_LIMITS",
    "I_ESTIMATE_NOT_EXACT",
    "J_ADAPTIVE_THINKING_DEFAULT",
    "K_THINKING_CAN_BE_DISABLED",
    "L_MAX_TOKENS_COVERS_THINKING_AND_ANSWER",
    "M_STRUCTURED_OUTPUT_AND_FORCED_TOOL_USE",
)
CLASSIFICATIONS = ("DOCUMENTED", "DOCUMENTED_AS_NOT_MESSAGE_CREATION")

ACCOUNTING = {
    "TOKEN_COUNT_API_REQUESTS": 1,
    "RETRIES": 0,
    "MESSAGES_API_REQUESTS": 0,
    "MODEL_INFERENCE_REQUESTS": 0,
    "TED_BYTES_SENT": 0,
    "RESEARCH_BYTES_SENT": 0,
}

#: Mission 1.84.4's thirteen counters. Nothing in Mission 1.84.5 writes to the database.
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

#: The adapter's fields. A new field would be a new request parameter nobody reviewed here, and a
#: generic parameter bag is exactly what Section 7 forbids.
ADAPTER_FIELDS = frozenset(
    {
        "name",
        "api_key",
        "endpoint",
        "count_tokens_endpoint",
        "transport",
        "max_output_tokens",
        "thinking",
        "supported_tiers",
    }
)

_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ValidationError(RuntimeError):
    """A record disagrees with live code, with a sibling record, or with itself."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _live_text_facts() -> dict[str, Any]:
    runner = _module(
        "token_measurement_runner", SCRIPTS / "run_second_opportunity_token_measurement.py"
    )
    _, facts = runner.measurement_text(runner.bounded_contract_gate())
    return dict(facts)


def _probe_request(schema: dict[str, Any] | None) -> LlmRequest:
    return LlmRequest(
        tier=LlmTier.STRONG_MODEL,
        task="gate.probe",
        prompt_template_id="gate-probe",
        prompt_template_version="1.0.0",
        workspace_id="00000000-0000-4000-8000-000000000001",
        prompt=RenderedPrompt(
            system_instructions="probe", trusted_context="", task="probe", untrusted=()
        ),
        response_schema=schema,
    )


def _adapter_default_budget() -> int:
    for field in dataclasses.fields(AnthropicProvider):
        if field.name == "max_output_tokens":
            return int(field.default)  # type: ignore[arg-type]
    raise ValidationError("AnthropicProvider no longer has a max_output_tokens field")


# --------------------------------------------------------------------------- the receipt


def _check_receipt(receipt: dict[str, Any], live: dict[str, Any]) -> None:
    if receipt.get("OUTCOME") != "MEASURED":
        raise ValidationError(f"the receipt outcome is {receipt.get('OUTCOME')!r}, not MEASURED")
    if receipt["MODEL"] != MODEL or receipt["endpoint"] != COUNT_TOKENS_ENDPOINT:
        raise ValidationError("the receipt names another model or another endpoint")
    if receipt["MEASUREMENT_SURFACE"] != "POST /v1/messages/count_tokens":
        raise ValidationError("the receipt names another measurement surface")
    shape = receipt["request_shape"]
    expected_shape = {
        "url": COUNT_TOKENS_ENDPOINT,
        "header_names": ["anthropic-version", "x-api-key"],
        "body_keys": ["messages", "model"],
        "model": MODEL,
        "message_count": 1,
        "message_role": "user",
        "content_type": "string",
        "system_sent": False,
        "tools_sent": False,
        "thinking_sent": False,
        "max_tokens_sent": False,
    }
    for key, value in expected_shape.items():
        if shape.get(key) != value:
            raise ValidationError(
                f"request_shape.{key} is {shape.get(key)!r}; the smallest valid request carries "
                f"{value!r}"
            )
    if receipt.get("credential_value_recorded") is not False:
        raise ValidationError("the receipt does not say that no credential value was recorded")
    if receipt.get("ACCOUNTING") != ACCOUNTING:
        raise ValidationError(f"the receipt accounting is {receipt.get('ACCOUNTING')}")
    tokens = receipt.get("INPUT_TOKENS")
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens <= 0:
        raise ValidationError("INPUT_TOKENS is not a positive integer")
    response = receipt.get("response") or {}
    if response.get("status") != 200:
        raise ValidationError("the recorded response is not a 200")
    if json.loads(response.get("body") or "null") != {"input_tokens": tokens}:
        raise ValidationError("the recorded response body does not carry the recorded estimate")
    if receipt.get("failure") is not None or receipt.get("transport_error") is not None:
        raise ValidationError("a MEASURED receipt carries a failure")
    for key, value in live.items():
        if receipt.get(key) != value:
            raise ValidationError(
                f"{key} is {receipt.get(key)!r} and the live rebuild gives {value!r}. The text "
                "that was counted is no longer the contract's maximum"
            )
    text = RECEIPT.read_text(encoding="utf-8")
    patterns = _module(
        "second_opportunity_runner", SCRIPTS / "run_second_opportunity_execution.py"
    ).SECRET_PATTERNS
    for pattern in patterns:
        if pattern.search(text):
            raise ValidationError("a credential-shaped string is present in the receipt")


# --------------------------------------------------------------------------- the documentation


def _check_documentation(record: dict[str, Any]) -> None:
    evidence = record["DOCUMENTATION_EVIDENCE"]
    ids = [e["id"] for e in evidence]
    if ids != [f"E{i:02d}" for i in range(1, len(ids) + 1)]:
        raise ValidationError(f"evidence ids are not a contiguous E01..: {ids}")
    used = set()
    for entry in evidence:
        eid = entry["id"]
        for field in ("requested_url", "final_url"):
            if not str(entry[field]).startswith(DOCS_PREFIX):
                raise ValidationError(f"{eid}.{field} is not a first-party documentation URL")
        if entry["first_party"] is not True:
            raise ValidationError(f"{eid} is not recorded as first-party")
        if entry["redirected"] != (entry["requested_url"] != entry["final_url"]):
            raise ValidationError(f"{eid}.redirected disagrees with its own URLs")
        if not _ISO_Z.match(str(entry["retrieved_at"])):
            raise ValidationError(f"{eid}.retrieved_at is not an instant")
        if not _HEX64.match(str(entry["sha256"])) or int(entry["bytes"]) <= 0:
            raise ValidationError(f"{eid} has no usable digest or size")
        if entry["used"] != (entry["http_status"] == 200):
            raise ValidationError(f"{eid} is used although it did not answer 200, or vice versa")
        if entry["used"]:
            used.add(eid)

    fetches = record["DOCUMENTATION_FETCHES"]
    failed = [e["id"] for e in evidence if e["http_status"] != 200]
    if fetches["attempted"] != len(evidence) or fetches["succeeded"] != len(used):
        raise ValidationError("DOCUMENTATION_FETCHES does not count the evidence list")
    if fetches["failed"] != failed:
        raise ValidationError("DOCUMENTATION_FETCHES.failed is not the non-200 entries")
    if fetches["third_party_sources"] != 0:
        raise ValidationError("a third-party source was used")

    propositions = record["DOCUMENTED_PROPOSITIONS"]
    if tuple(propositions) != PROPOSITIONS:
        raise ValidationError(f"the propositions are not A to M in order: {list(propositions)}")
    for pid, proposition in propositions.items():
        if not str(proposition.get("established", "")).strip():
            raise ValidationError(f"{pid} establishes nothing")
        if proposition.get("classification") not in CLASSIFICATIONS:
            raise ValidationError(f"{pid} has classification {proposition.get('classification')!r}")
        fragments = list(proposition.get("fragments") or []) + list(
            proposition.get("residual_fragments") or []
        )
        if not proposition.get("fragments"):
            raise ValidationError(f"{pid} cites no fragment")
        for fragment in fragments:
            _check_fragment(pid, fragment, used)
    if propositions["F_COUNT_IS_NOT_MESSAGE_CREATION"]["classification"] != (
        "DOCUMENTED_AS_NOT_MESSAGE_CREATION"
    ):
        raise ValidationError("F claims more than the pages say: they never say inference")

    expectations = record["BRIEF_EXPECTATIONS_RE_ESTABLISHED"]
    if len(expectations) != 7:
        raise ValidationError("the brief's seven expected values were not each re-established")
    for item in expectations:
        if item["proposition"] not in propositions or item["agrees"] is not True:
            raise ValidationError(f"expectation {item['expected_by_the_brief']!r} is unsupported")


def _check_fragment(pid: str, fragment: dict[str, Any], used: set[str]) -> None:
    if fragment.get("evidence") not in used:
        raise ValidationError(
            f"{pid} cites {fragment.get('evidence')!r}, which is not used evidence"
        )
    if not isinstance(fragment.get("line"), int) or fragment["line"] <= 0:
        raise ValidationError(f"{pid} cites a fragment with no line")
    verbatim = fragment.get("verbatim")
    row = fragment.get("verbatim_row_whitespace_collapsed")
    if (verbatim is None) == (row is None):
        raise ValidationError(
            f"{pid} has a fragment that is not exactly one of a quotation or a table row"
        )
    if verbatim is not None and not (0 < len(str(verbatim).split()) <= 25):
        raise ValidationError(f"{pid} quotes nothing, or more than a short fragment")
    if row is not None and not str(row).startswith("|"):
        raise ValidationError(f"{pid} records a table row that is not a table row")


# --------------------------------------------------------------------------- the measurement


def _check_measurement(record: dict[str, Any], receipt: dict[str, Any]) -> None:
    outcome = record["PRIMARY_OUTCOME"]
    if outcome not in ACCEPTABLE_OUTCOMES:
        raise ValidationError(f"PRIMARY_OUTCOME {outcome!r} is not one Section 27 accepts")
    if "EXACT_MAX_OUTPUT_TOKEN_COUNT" in set(_keys(record)):
        raise ValidationError("an exact output token count is recorded; the count is an estimate")
    if not re.fullmatch(r"[0-9a-f]{40}", str(record["START_COMMIT"])):
        raise ValidationError("START_COMMIT is not a commit id")

    measured = record["MEASUREMENT"]
    estimate = measured["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"]
    if estimate != receipt["INPUT_TOKENS"]:
        raise ValidationError("the recorded estimate is not the receipt's")
    for key in (
        "MEASUREMENT_SURFACE",
        "MODEL",
        "MEASUREMENT_SCHEMA_ID",
        "MEASUREMENT_SCHEMA_SHA256",
        "MEASUREMENT_TEXT_SHA256",
        "MEASUREMENT_TEXT_CHARACTERS",
        "MEASUREMENT_TEXT_UTF8_BYTES",
    ):
        if measured[key] != receipt[key]:
            raise ValidationError(f"MEASUREMENT.{key} disagrees with the receipt")
    if measured["receipt_sha256"] != hashlib.sha256(RECEIPT.read_bytes()).hexdigest():
        raise ValidationError("the receipt changed after the measurement record named it")
    if measured["request_id"] != receipt["response"]["request_id"]:
        raise ValidationError("the recorded request id is not the receipt's")
    required = {
        "ESTIMATE_NOT_EXACT": True,
        "SAME_MODEL_TOKENIZER_MEASUREMENT": True,
        "INPUT_TO_OUTPUT_TOKENIZATION_EQUIVALENCE": "NOT_ESTABLISHED",
        "DOCUMENTED_TOKEN_COUNT_MARGIN": "NONE",
        "SYSTEM_ADDED_TOKENS_MAY_BE_INCLUDED": True,
    }
    for key, value in required.items():
        if measured.get(key) != value:
            raise ValidationError(f"MEASUREMENT.{key} must be {value!r}")

    capacity = record["CAPACITY_COMPARISON"]
    if capacity["MODEL_MAX_OUTPUT_TOKENS"] != MODEL_MAX_OUTPUT_TOKENS:
        raise ValidationError("the documented maximum is not 128000")
    default = _adapter_default_budget()
    if capacity["ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS"] != default:
        raise ValidationError("the recorded adapter default is not the live adapter's")
    if default == capacity["MODEL_MAX_OUTPUT_TOKENS"]:
        raise ValidationError("the adapter default was made equal to the model's maximum")
    if capacity["HEADROOM_TO_PROVIDER_MAX"] != MODEL_MAX_OUTPUT_TOKENS - estimate:
        raise ValidationError("HEADROOM_TO_PROVIDER_MAX is not recomputable")
    if capacity["ESTIMATE_OVER_PROVIDER_MAX"] != round(estimate / MODEL_MAX_OUTPUT_TOKENS, 4):
        raise ValidationError("ESTIMATE_OVER_PROVIDER_MAX is not recomputable")
    exceeds = estimate > MODEL_MAX_OUTPUT_TOKENS
    if capacity["EXCEEDS_PROVIDER_MAX"] is not exceeds:
        raise ValidationError("EXCEEDS_PROVIDER_MAX disagrees with the arithmetic")
    if capacity["BATCH_API_BETA_MAX_OUTPUT_TOKENS"] != BATCH_BETA_MAX_OUTPUT_TOKENS:
        raise ValidationError("the batch beta ceiling is not the documented 300k")
    if capacity["HEADROOM_TO_BATCH_BETA_MAX"] != BATCH_BETA_MAX_OUTPUT_TOKENS - estimate:
        raise ValidationError("HEADROOM_TO_BATCH_BETA_MAX is not recomputable")
    if capacity["batch_route_adopted"] is not False:
        raise ValidationError("the batch route was adopted by arithmetic")

    if exceeds and outcome != EXCEEDS:
        raise ValidationError(
            f"the estimate {estimate} exceeds the documented maximum and the outcome is "
            f"{outcome!r}. Section 21 requires {EXCEEDS}"
        )
    ceiling = record["CEILING"]
    if ceiling["SELECTED_MAX_OUTPUT_TOKENS"] != "NONE":  # noqa: S105 - an output-token budget
        raise ValidationError("a ceiling was selected")
    if ceiling["OPERATOR_HEADROOM_POLICY"] != "NONE_HELD":
        raise ValidationError("a headroom policy is claimed and none was approved")
    if record["EXECUTION_PACKET_V2_CREATED"] is not False:
        raise ValidationError("the record claims an execution packet V2")
    if PACKET_V2.exists() and not _v2_prepared_by_a_later_mission():
        raise ValidationError("an execution packet V2 exists that no later mission prepared")
    if record["SCHEMA_REDUCED"] is not False:
        raise ValidationError("the schema was reduced")
    if record["OPTIONS_IMPLEMENTED"] != [] or record["OPTION_RECOMMENDED"] != "NONE":
        raise ValidationError("an operator option was implemented or recommended")
    for option in record["OPERATOR_OPTIONS"]:
        if not all(str(option.get(k, "")).strip() for k in ("option", "effect", "cost")):
            raise ValidationError(f"option {option.get('option')!r} is missing its effect or cost")

    cross = record["EMPIRICAL_RATIO_CROSS_CHECK"]
    characters = measured["MEASUREMENT_TEXT_CHARACTERS"]
    predicted = round(characters / HELD_RATIO)
    if cross["held_ratio_characters_per_token"] != HELD_RATIO:
        raise ValidationError("the held ratio is not Mission 1.84's")
    if cross["predicted_tokens_from_held_ratio"] != predicted:
        raise ValidationError("the predicted count is not recomputable")
    if cross["held_ratio_underestimates_by_tokens"] != estimate - predicted:
        raise ValidationError("the underestimate is not recomputable")
    if cross["held_ratio_underestimates_by_fraction"] != round(
        (estimate - predicted) / estimate, 4
    ):
        raise ValidationError("the underestimate fraction is not recomputable")
    if cross["measured_characters_per_token"] != round(characters / estimate, 4):
        raise ValidationError("the measured ratio is not recomputable")

    cost = record["COST"]
    if (
        cost["TOKEN_COUNT_API_COST"] != 0
        or cost["token_count_cost_basis"] != "proposition G_BILLING"  # noqa: S105 - a citation
    ):
        raise ValidationError("the counting cost is not zero on the documented basis")
    if cost["FUTURE_INFERENCE_COST"] != "NOT_COMPUTED":
        raise ValidationError("an inference cost was computed with no ceiling selected")

    accounting = record["ACCOUNTING"]
    expected_accounting = {
        **ACCOUNTING,
        "DOCUMENTATION_FETCHES": len(record["DOCUMENTATION_EVIDENCE"]),
        "CANONICAL_MUTATIONS": 0,
    }
    if accounting != expected_accounting:
        raise ValidationError(f"the mission accounting is {accounting}")
    if record["CANONICAL_COUNTERS"] != CANONICAL_COUNTERS:
        raise ValidationError("a canonical counter moved")


def _check_preconditions(record: dict[str, Any]) -> None:
    pre = record["PRECONDITIONS_1_84_4"]
    capacity = _load(CAPACITY_V2)
    maximum = capacity["MAXIMUM_VALID_INSTANCE"]
    pairs = {
        "SCHEMA_ID": capacity["schema_id"],
        "SCHEMA_SHA256": capacity["schema_sha256"],
        "FINITE_BOUND": capacity["FINITE_BOUND"],
        "UNBOUNDED_PATHS": capacity["unbounded_path_count"],
        "MAX_VALID_OUTPUT_CHARACTERS": maximum["MAX_VALID_OUTPUT_CHARACTERS"],
        "MAX_VALID_OUTPUT_UTF8_BYTES": maximum["MAX_VALID_OUTPUT_UTF8_BYTES"],
        "MAX_VALID_OUTPUT_SHA256": maximum["MAX_VALID_OUTPUT_SHA256"],
        "PROMPT_SHA256": _load(PROMPT_V2)["PROMPT_SHA256"],
        "TED_REPRESENTATION_SHA256": capacity["TED_REPRESENTATION_SHA256"],
        "V1_EXECUTION_APPROVAL_CONSUMED": capacity["V1_STATE"]["EXECUTION_APPROVAL_CONSUMED"],
    }
    for key, value in pairs.items():
        if pre[key] != value:
            raise ValidationError(f"PRECONDITIONS_1_84_4.{key} is not what Mission 1.84.4 recorded")
    if capacity["PROVIDER_MODEL_CAPABILITY"]["CONFIGURED_OUTPUT_TOKEN_CAPABILITY"] != (
        "NOT_ESTABLISHED"  # noqa: S105 - a state name, not a credential
    ):
        raise ValidationError("Mission 1.84.4's capability block was rewritten; it has a successor")


def _check_thinking_and_v1(record: dict[str, Any]) -> None:
    thinking = record["THINKING"]
    fixed = {
        "CLAUDE_SONNET_5_THINKING_POLICY": "DISABLED",
        "MODEL_DEFAULT": "ADAPTIVE_ON_BY_DEFAULT",
        "THINKING_DISABLE_SUPPORTED": "DOCUMENTED",
        "THINKING_CONTROL_REQUIRES_ARCHITECTURE_DECISION": False,
        "FUTURE_V2_THINKING": "DISABLED",
        "THINKING_TOKENS_SHARE_V2_MAX_TOKENS": False,
        "FORCED_TOOL_USE_WITH_THINKING_DISABLED": "NOT_RESTRICTED_BY_DOCUMENTATION",
    }
    for key, value in fixed.items():
        if thinking.get(key) != value:
            raise ValidationError(f"THINKING.{key} must be {value!r}")
    capability = thinking["ADAPTER_CAPABILITY"]
    if capability["members"] != [m.value for m in AnthropicThinking]:
        raise ValidationError("the recorded thinking configurations are not the adapter's")
    fields = {f.name: f for f in dataclasses.fields(AnthropicProvider)}
    if set(fields) != ADAPTER_FIELDS:
        raise ValidationError(
            f"the adapter's fields changed to {sorted(fields)}. A new field is a request "
            "parameter nobody reviewed here"
        )
    if capability["default"] != fields["thinking"].default:
        raise ValidationError("the recorded default thinking is not the adapter's")
    if capability["generic_parameter_collection"] is not False:
        raise ValidationError("a generic parameter collection is claimed")
    probe = AnthropicProvider(api_key="gate-probe-not-a-credential")
    structured = probe.build_body(_probe_request({"type": "object"}), MODEL)
    if "thinking" in structured:
        raise ValidationError("the default body carries a thinking field; the old body changed")
    disabled = AnthropicProvider(
        api_key="gate-probe-not-a-credential", thinking=AnthropicThinking.DISABLED
    ).build_body(_probe_request({"type": "object"}), MODEL)
    documented = {"type": "disabled"}
    if disabled.get("thinking") != documented or capability["disabled_request_field"] != documented:
        raise ValidationError("the DISABLED body does not carry the documented object")
    if disabled["tool_choice"] != {"type": "tool", "name": "emit_structured_output"}:
        raise ValidationError("DISABLED changed how structured output is forced")

    structured_output = record["STRUCTURED_OUTPUT"]
    if "output_config" in structured or "strict" in structured["tools"][0]:
        raise ValidationError("the adapter sends a native structured-output field")
    if (
        structured_output["NATIVE_PROVIDER_STRUCTURED_OUTPUT"] is not False
        or structured_output["MIGRATED"] is not False
        or structured_output["LOCAL_VALIDATOR_AUTHORITATIVE"] is not True
    ):
        raise ValidationError("the structured-output record claims a migration")

    v1 = record["V1_THINKING_FINDING"]
    packet = _load(PACKET_V1)
    if packet.get("EXECUTION_PACKET_SHA256") != V1_SHA256:
        raise ValidationError("the V1 packet digest moved")
    if v1["V1_MAX_OUTPUT_TOKENS"] != packet["MAX_OUTPUT_TOKENS"]:
        raise ValidationError("V1_MAX_OUTPUT_TOKENS is not the frozen packet's")
    execution = _load(EXECUTION_RECORD_V1)
    if execution["ROOT_CAUSE"] != ROOT_CAUSE_1_84_2 or v1["V1_ROOT_CAUSE"] != ROOT_CAUSE_1_84_2:
        raise ValidationError("Mission 1.84.2's root cause was rewritten")
    fixed_v1 = {
        "V1_THINKING_FIELD_SENT": False,
        "V1_EFFECTIVE_THINKING_CONFIGURATION": "ADAPTIVE_BY_MODEL_DEFAULT",
        "V1_OUTPUT_BUDGET_SHARED_WITH_ADAPTIVE_THINKING": True,
        "V1_THINKING_TOKENS_CONSUMED": "NOT_ESTABLISHED",
        "ROOT_CAUSE_REWRITTEN": False,
        "status": "CONTRIBUTING_FACTOR_POSSIBILITY",
    }
    for key, value in fixed_v1.items():
        if v1.get(key) != value:
            raise ValidationError(f"V1_THINKING_FINDING.{key} must be {value!r}")


# --------------------------------------------------------------------------- the register


def _check_register(register: dict[str, Any], record: dict[str, Any]) -> None:
    if register["provider"] != "anthropic" or set(register["MODELS"]) != {MODEL}:
        raise ValidationError("the register names another provider or model")
    model = register["MODELS"][MODEL]
    fixed = {
        "DOCUMENTED_MAX_OUTPUT_TOKENS": MODEL_MAX_OUTPUT_TOKENS,
        "BATCH_API_BETA_MAX_OUTPUT_TOKENS": BATCH_BETA_MAX_OUTPUT_TOKENS,
        "CONTEXT_WINDOW_TOKENS": 1000000,
        "THINKING_DEFAULT": "ADAPTIVE_ON_BY_DEFAULT",
        "THINKING_DISABLE_SUPPORTED": True,
        "MAX_TOKENS_COVERS": "THINKING_AND_RESPONSE",
        "NATIVE_STRUCTURED_OUTPUTS_SUPPORTED": True,
    }
    for key, value in fixed.items():
        if model.get(key) != value:
            raise ValidationError(f"register {MODEL}.{key} must be {value!r}")
    if (
        model["DOCUMENTED_MAX_OUTPUT_TOKENS"]
        != record["CAPACITY_COMPARISON"]["MODEL_MAX_OUTPUT_TOKENS"]
    ):
        raise ValidationError("the register and the measurement disagree on the maximum")
    for pid in model["propositions"]:
        if pid not in record["DOCUMENTED_PROPOSITIONS"]:
            raise ValidationError(f"the register cites {pid}, which the measurement does not hold")
    used = {e["id"] for e in record["DOCUMENTATION_EVIDENCE"] if e["used"]}
    _check_fragment("register price", model["price_fragment"], used)

    adapter = register["ADAPTER"]
    if adapter["ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS"] != _adapter_default_budget():
        raise ValidationError("the register's adapter default is not the live adapter's")
    if adapter["THINKING_CONFIGURATIONS"] != [m.value for m in AnthropicThinking]:
        raise ValidationError("the register's thinking configurations are not the adapter's")
    if adapter["DEFAULT_THINKING"] != AnthropicThinking.PROVIDER_DEFAULT.value:
        raise ValidationError("the register's default thinking is not the adapter's")
    if adapter["NATIVE_STRUCTURED_OUTPUT_USED"] is not False:
        raise ValidationError("the register claims native structured output is used")
    if adapter["COUNT_TOKENS_ENDPOINT"] != COUNT_TOKENS_ENDPOINT:
        raise ValidationError("the register's count endpoint is not the adapter's")
    if register["DOCUMENTED_MAX_AND_ADAPTER_DEFAULT_DISTINCT"] is not True or (
        adapter["ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS"] == model["DOCUMENTED_MAX_OUTPUT_TOKENS"]
    ):
        raise ValidationError("the documented maximum and the adapter default were merged")


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = _load(RECEIPT)
    record = _load(MEASUREMENT)
    register = _load(REGISTER)
    _check_receipt(receipt, _live_text_facts())
    _check_documentation(record)
    _check_measurement(record, receipt)
    _check_preconditions(record)
    _check_thinking_and_v1(record)
    _check_register(register, record)
    return record, register


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_token_measurement.py "
    "from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _fragment_line(fragment: dict[str, Any]) -> str:
    text = fragment.get("verbatim") or fragment.get("verbatim_row_whitespace_collapsed")
    return f"  - {fragment['evidence']} line {fragment['line']}: `` {text} ``"


def render_measurement(record: dict[str, Any]) -> str:
    m = record["MEASUREMENT"]
    c = record["CAPACITY_COMPARISON"]
    x = record["EMPIRICAL_RATIO_CROSS_CHECK"]
    t = record["THINKING"]
    v = record["V1_THINKING_FINDING"]
    lines = [
        HEADER.format(source=MEASUREMENT.name),
        "# Second opportunity: provider-native token measurement v1",
        "",
        f"Mission {record['mission']}, recorded {record['recorded_at']}. "
        f"Start commit `{record['START_COMMIT']}`.",
        "",
        f"**Outcome: `{record['PRIMARY_OUTCOME']}`.** {record['outcome_basis']}",
        "",
        "## The measurement",
        "",
        "```",
        f"estimate (input tokens)   {m['PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE']}",
        f"surface                   {m['MEASUREMENT_SURFACE']}",
        f"model                     {m['MODEL']}",
        f"text                      {m['MEASUREMENT_TEXT_CHARACTERS']} characters, "
        f"{m['MEASUREMENT_TEXT_UTF8_BYTES']} UTF-8 bytes",
        f"text sha256               {m['MEASUREMENT_TEXT_SHA256']}",
        f"schema                    {m['MEASUREMENT_SCHEMA_ID']}",
        f"request id                {m['request_id']}",
        "```",
        "",
        f"- `ESTIMATE_NOT_EXACT = {str(m['ESTIMATE_NOT_EXACT']).lower()}`. {m['margin_note']}",
        f"- `SAME_MODEL_TOKENIZER_MEASUREMENT = "
        f"{str(m['SAME_MODEL_TOKENIZER_MEASUREMENT']).lower()}`: {m['same_model_basis']}.",
        f"- `INPUT_TO_OUTPUT_TOKENIZATION_EQUIVALENCE = "
        f"{m['INPUT_TO_OUTPUT_TOKENIZATION_EQUIVALENCE']}`. "
        f"{m['why_input_to_output_is_not_established']}",
        f"- `DOCUMENTED_TOKEN_COUNT_MARGIN = {m['DOCUMENTED_TOKEN_COUNT_MARGIN']}`.",
        f"- Serialization measured: {m['measured_serialization']}",
        "",
        "## Against the model's documented maximum",
        "",
        "```",
        f"documented maximum output   {c['MODEL_MAX_OUTPUT_TOKENS']}  ({c['documented_form']})",
        f"adapter default             {c['ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS']}  (ours, not a capability)",
        f"headroom to the maximum     {c['HEADROOM_TO_PROVIDER_MAX']}",
        f"estimate over maximum       {c['ESTIMATE_OVER_PROVIDER_MAX']}",
        f"exceeds                     {str(c['EXCEEDS_PROVIDER_MAX']).lower()}",
        f"batch beta ceiling          {c['BATCH_API_BETA_MAX_OUTPUT_TOKENS']}  "
        f"(headroom {c['HEADROOM_TO_BATCH_BETA_MAX']}, not adopted)",
        "```",
        "",
        f"- {c['integer_reading']}",
        f"- {c['arithmetic_is_not_proof']}",
        f"- {c['provider_max_is_not_an_execution_budget']}",
        f"- {c['why_the_batch_route_is_not_adopted']}",
        "",
        "## The held ratio would have underestimated it",
        "",
        f"Mission 1.84's ratio of {x['held_ratio_characters_per_token']} characters per token "
        f"predicts {x['predicted_tokens_from_held_ratio']} tokens for this text; the provider "
        f"estimates {x['provider_native_estimate']}, so the held ratio is short by "
        f"{x['held_ratio_underestimates_by_tokens']} tokens "
        f"({x['held_ratio_underestimates_by_fraction']} of the estimate). This text measures "
        f"{x['measured_characters_per_token']} characters per token. {x['note']}",
        "",
        "## Thinking",
        "",
        f"- Operator policy for this synthesis: `{t['CLAUDE_SONNET_5_THINKING_POLICY']}`. "
        f"Model default: `{t['MODEL_DEFAULT']}`. Disabling: `{t['THINKING_DISABLE_SUPPORTED']}`.",
        f"- Adapter capability: `{t['ADAPTER_CAPABILITY']['type']}` with members "
        f"{', '.join('`' + x_ + '`' for x_ in t['ADAPTER_CAPABILITY']['members'])}; default "
        f"`{t['ADAPTER_CAPABILITY']['default']}` leaves the old request body unchanged.",
        f"- `FUTURE_V2_THINKING = {t['FUTURE_V2_THINKING']}`, "
        f"`THINKING_TOKENS_SHARE_V2_MAX_TOKENS = "
        f"{str(t['THINKING_TOKENS_SHARE_V2_MAX_TOKENS']).lower()}`. {t['thinking_tokens_basis']}",
        f"- Forced tool use with thinking disabled: `{t['FORCED_TOOL_USE_WITH_THINKING_DISABLED']}`."
        f" {t['forced_tool_use_note']}",
        "",
        "## What this says about V1",
        "",
        f"`V1_OUTPUT_BUDGET_SHARED_WITH_ADAPTIVE_THINKING = "
        f"{str(v['V1_OUTPUT_BUDGET_SHARED_WITH_ADAPTIVE_THINKING']).lower()}`. {v['basis']} "
        f"`V1_THINKING_TOKENS_CONSUMED = {v['V1_THINKING_TOKENS_CONSUMED']}`: "
        f"{v['why_not_established']} The root cause stays `{v['V1_ROOT_CAUSE']}`; this is a "
        f"`{v['status']}`, not a rewrite.",
        "",
        "## Ceiling, packet, cost",
        "",
        f"`SELECTED_MAX_OUTPUT_TOKENS = {record['CEILING']['SELECTED_MAX_OUTPUT_TOKENS']}`, "
        f"`OPERATOR_HEADROOM_POLICY = {record['CEILING']['OPERATOR_HEADROOM_POLICY']}`. "
        f"{record['CEILING']['why_none']} `EXECUTION_PACKET_V2_CREATED = "
        f"{str(record['EXECUTION_PACKET_V2_CREATED']).lower()}`. `TOKEN_COUNT_API_COST = "
        f"{record['COST']['TOKEN_COUNT_API_COST']}` (free to use), `FUTURE_INFERENCE_COST = "
        f"{record['COST']['FUTURE_INFERENCE_COST']}`.",
        "",
        "## Operator options (none implemented, none recommended)",
        "",
    ]
    for option in record["OPERATOR_OPTIONS"]:
        lines.append(f"- **`{option['option']}`**: {option['effect']}. Cost: {option['cost']}.")
    lines += ["", "## Documentation propositions", ""]
    for pid, proposition in record["DOCUMENTED_PROPOSITIONS"].items():
        lines.append(f"- **{pid}** ({proposition['classification']}): {proposition['established']}")
        for fragment in proposition["fragments"]:
            lines.append(_fragment_line(fragment))
    lines += [
        "",
        "## Documentation fetched",
        "",
        "| id | status | final URL | retrieved | bytes | sha256 |",
        "|---|---|---|---|---|---|",
    ]
    for e in record["DOCUMENTATION_EVIDENCE"]:
        lines.append(
            f"| {e['id']} | {e['http_status']} | {e['final_url']} | {e['retrieved_at']} | "
            f"{e['bytes']} | `{e['sha256'][:16]}` |"
        )
    lines += [
        "",
        "## Accounting",
        "",
        "```",
        *(f"{k.lower():28s} {v_}" for k, v_ in record["ACCOUNTING"].items()),
        "```",
        "",
        "Canonical counters, unchanged: "
        + " / ".join(str(v_) for v_ in record["CANONICAL_COUNTERS"].values())
        + ".",
        "",
        f"**Next: `{record['NEXT_REQUIRED_ACTION']}`.**",
        "",
    ]
    return "\n".join(lines)


def render_register(register: dict[str, Any]) -> str:
    model = register["MODELS"][MODEL]
    adapter = register["ADAPTER"]
    forced = model["FORCED_TOOL_USE"]
    return "\n".join(
        [
            HEADER.format(source=REGISTER.name),
            "# Provider-model capability register v1",
            "",
            f"Mission {register['mission']}, recorded {register['recorded_at']}. "
            f"Provider `{register['provider']}`, route: {register['route']}. Evidence: "
            f"`{register['evidence_record']}`.",
            "",
            f"## `{MODEL}`, as documented",
            "",
            "```",
            f"max output (synchronous)     {model['DOCUMENTED_MAX_OUTPUT_TOKENS']}  "
            f"({model['max_output_documented_form']})",
            f"max output (batches, beta)   {model['BATCH_API_BETA_MAX_OUTPUT_TOKENS']}  "
            f"({model['batch_documented_form']})",
            f"context window               {model['CONTEXT_WINDOW_TOKENS']}  "
            f"({model['context_documented_form']})",
            f"thinking default             {model['THINKING_DEFAULT']}",
            f"thinking can be disabled     {str(model['THINKING_DISABLE_SUPPORTED']).lower()}",
            f"max_tokens covers            {model['MAX_TOKENS_COVERS']}",
            f"tokenizer                    {model['TOKENIZER']}",
            f"forced tool use, adaptive    {forced['WITH_ADAPTIVE_THINKING']}",
            f"forced tool use, manual      {forced['WITH_MANUAL_EXTENDED_THINKING']}",
            f"forced tool use, disabled    {forced['WITH_THINKING_DISABLED']}",
            f"native structured outputs    {str(model['NATIVE_STRUCTURED_OUTPUTS_SUPPORTED']).lower()}",
            f"tool-use system prompt       {model['TOOL_USE_SYSTEM_PROMPT_TOKENS']['auto_or_none']} "
            f"(auto/none), {model['TOOL_USE_SYSTEM_PROMPT_TOKENS']['any_or_tool']} (any/tool)",
            f"price, USD per MTok          {model['DOCUMENTED_PRICE_USD_PER_MTOK']['input']} in, "
            f"{model['DOCUMENTED_PRICE_USD_PER_MTOK']['output']} out",
            "```",
            "",
            "Propositions: " + ", ".join(f"`{p}`" for p in model["propositions"]) + ".",
            "",
            "## This repository's adapter, beside it and not in place of it",
            "",
            "```",
            f"class                        {adapter['class']}",
            f"default max_output_tokens    {adapter['ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS']}",
            f"thinking configurations      {', '.join(adapter['THINKING_CONFIGURATIONS'])}",
            f"default thinking             {adapter['DEFAULT_THINKING']}",
            f"native structured output     {str(adapter['NATIVE_STRUCTURED_OUTPUT_USED']).lower()}",
            f"count endpoint               {adapter['COUNT_TOKENS_ENDPOINT']}",
            "```",
            "",
            f"{adapter['adapter_default_is_not_a_capability']}",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        record, register = validate()
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL     {type(exc).__name__}: {exc}")
        return 1
    rendered = {MEASUREMENT_MD: render_measurement(record), REGISTER_MD: render_register(register)}
    if args.write:
        for path, text in rendered.items():
            path.write_text(text, encoding="utf-8", newline="\n")
        print("wrote    " + ", ".join(p.name for p in rendered))
        return 0
    for path, text in rendered.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            print(f"FAIL     {path.name} is not the rendering of its record")
            return 1
    print("ok       the token measurement matches its receipt, the live contract and the adapter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
