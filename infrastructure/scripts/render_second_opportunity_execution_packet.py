"""Render and validate the second-Opportunity synthesis execution packet (Mission 1.84).

An execution packet describes a call nobody has made. What makes it worth anything is that it
cannot quietly become a different call, so the gate refuses:

    A PACKET WHOSE PAYLOAD IS NOT THE APPROVED ONE. The representation digest is compared
    against the digest the operator's approval names, and a mismatch is the hard stop
    APPROVED_TED_EGRESS_REPRESENTATION_CHANGED. It is never repaired by reserialising, by
    updating the approval, or by arguing that the meaning is unchanged.

    A PACKET WHOSE SCOPE IS WIDER THAN THE APPROVAL. Source, profile, activity, purpose,
    subject and representation schema are compared field for field against the approval, and
    every act the operator excluded stays excluded.

    A VENDOR CHOSEN RATHER THAN DERIVED. The eligible providers are recomputed from the current
    register, and a packet naming one the register does not currently approve is refused. A
    single-route claim is refused when the register approves more than one.

    A PARAMETER NOTHING READS. Every non-null generation parameter must be a field the Gateway's
    own request type carries, and every null one must NOT be, so a null records an unsupported
    parameter rather than a silently accepted default. `max_retries` is 0, because a retry is a
    second call and this packet authorises one.

    A COST BASIS NOBODY HELD. The worst case recomputes from the recorded token ceilings and the
    recorded prices, the pricing version is named, and the ceiling covers the worst case.

    AN APPROVAL INSIDE THE THING BEING APPROVED. `OPERATOR_EXECUTION_APPROVAL_RECORDED` is false,
    and the TED egress approval is recorded as a different act from approving this execution.

    A GATE THAT CLAIMS MORE THAN IT CHECKS. The output contract must state that lexical
    filtering is not semantic safety and must keep human review required.

    A PREPARATION THAT EXECUTED. Model calls, transmitted bytes, test requests, research
    acquisition and canonical mutation are all 0.

    uv run python infrastructure/scripts/render_second_opportunity_execution_packet.py
    uv run python infrastructure/scripts/render_second_opportunity_execution_packet.py --check

Deterministic from repository files and the installed packages, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import pathlib

from sros_llm_gateway.types import LlmRequest
from sros_opportunity import (
    ANTI_DISTORTION_RULES,
    CONFIDENCE_CLASSIFICATIONS,
    FORBIDDEN_TRANSFORMATIONS,
    PERSISTENCE_GATE_VERSION,
    SECOND_OPPORTUNITY_GATE_VERSION,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
    SECOND_OPPORTUNITY_PROCEDURE_VERSION,
    SECOND_OPPORTUNITY_PROMPT_ID,
    SECOND_OPPORTUNITY_PROMPT_VERSION,
    SECOND_OPPORTUNITY_SYSTEM,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

PROMPT = DATA / "second-opportunity-synthesis-prompt-v1.json"
PROMPT_MD = DATA / "second-opportunity-synthesis-prompt-v1.md"
CONTRACT = DATA / "second-opportunity-synthesis-output-contract-v1.json"
CONTRACT_MD = DATA / "second-opportunity-synthesis-output-contract-v1.md"
PACKET = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_MD = DATA / "second-opportunity-synthesis-execution-packet-v1.md"

APPROVAL = DATA / "ted-egress-operator-decision-v1.json"
DECISION_PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"
PROVIDER_REGISTER = DATA / "model-provider-policy-v1.json"
PREPARATION_V5 = DATA / "opportunity-preparation-v5.json"
PREPARATION_V4 = DATA / "opportunity-preparation-v4.json"

SUBJECT = "ted-eu:CPV-class:9261"
PURPOSE = "bounded external inference for Opportunity hypothesis synthesis"
REPRESENTATION_CHANGED = "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED"

#: §21. The Gateway is the authority on which generation parameters exist. A packet that froze a
#: temperature would freeze a value nothing reads, and a reader would take the absence of one as
#: a defaulted choice rather than as an unavailable knob.
LLM_REQUEST_FIELDS = frozenset(f.name for f in dataclasses.fields(LlmRequest))

#: §6. Every one of these is false, and a true one is not a configuration difference.
CAPABILITY_NEGATIVES = (
    "TRAINING",
    "FINE_TUNING",
    "EMBEDDINGS",
    "WEB",
    "TOOLS",
    "EXTERNAL_RETRIEVAL",
)

#: §35 to §37. What preparing a packet costs, which is nothing.
ZERO_PREPARATION = (
    "MODEL_CALLS",
    "BYTES_SENT_TO_ANY_EXTERNAL_MODEL",
    "TOKENS_SENT",
    "PROVIDER_REQUESTS",
    "TEST_REQUESTS",
    "research_data_fetches",
    "network_discovery_calls",
    "canonical_research_mutation",
    "opportunities_created",
    "opportunity_revisions_created",
    "claims_created",
    "evidence_created",
    "signals_created",
    "embeddings_created",
    "scores_persisted",
    "independence_groups_created",
    "credential_values_read_or_logged",
)

#: §27. The eight ordered stages, by their first distinguishing word.
VALIDATION_STAGES = (
    "transport",
    "provider response shape",
    "structured-output parse",
    "schema validation",
    "semantic output gate",
    "evidence-boundary gate",
    "attribution",
    "canonical persistence eligibility",
)

#: The fields the digest binds. Kept here rather than read from the record, because a digest
#: computed over whichever fields the record nominates is a digest the record can shrink.
DIGEST_FIELDS = (
    "EXECUTION_PACKET_ID",
    "EXECUTION_PACKET_VERSION",
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
    "PROVIDER_POSTURE",
    "MODEL_ID",
    "MODEL_TIER",
    "PROMPT_ID",
    "PROMPT_VERSION",
    "PROMPT_SHA256",
    "GENERATION_PARAMETERS",
    "INPUT_TOKEN_ESTIMATE",
    "MAX_OUTPUT_TOKENS",
    "TOTAL_TOKEN_CEILING",
    "PRICING_VERSION",
    "WORST_CASE_CALL_COST",
    "EXECUTION_COST_CEILING",
    "MAX_MODEL_CALLS",
    "REQUEST_TIMEOUT",
    "OUTPUT_SCHEMA_VERSION",
    "OUTPUT_GATE_VERSION",
    "PERSISTENCE_POLICY",
    "TRAINING",
    "FINE_TUNING",
    "EMBEDDINGS",
    "WEB",
    "TOOLS",
    "EXTERNAL_RETRIEVAL",
    "failure_outcome",
)


class ValidationError(RuntimeError):
    """The records disagree with each other, with the code, or with the approval."""


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def packet_digest(packet: dict) -> str:
    """Recompute the execution digest from the packet's own bound fields."""
    bound: dict[str, object] = {}
    for key in DIGEST_FIELDS:
        if key not in packet:
            raise ValidationError(f"the execution packet has no {key!r} to bind")
        value = packet[key]
        if key == "GENERATION_PARAMETERS":
            value = {k: v for k, v in value.items() if not k.endswith("note") and k != "$comment"}
        if key == "PERSISTENCE_POLICY":
            value = {k: v for k, v in value.items() if k != "note"}
        bound[key] = value
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return _sha256(payload)


def approved_providers(register: dict) -> list[str]:
    """The provider ids the CURRENT register approves. Derived, never listed here."""
    return sorted(
        str(entry["provider_id"])
        for entry in register["providers"]
        if str(entry.get("posture")) == "APPROVED"
    )


# --------------------------------------------------------------------------- the prompt


def _check_the_prompt(prompt: dict) -> None:
    if prompt["PROMPT_ID"] != SECOND_OPPORTUNITY_PROMPT_ID:
        raise ValidationError("the frozen prompt id is not the one the procedure carries")
    if prompt["PROMPT_VERSION"] != SECOND_OPPORTUNITY_PROMPT_VERSION:
        raise ValidationError("the frozen prompt version is not the one the procedure carries")
    if prompt["PROCEDURE"] != SECOND_OPPORTUNITY_PROCEDURE_VERSION:
        raise ValidationError("the frozen procedure version is not the one the code carries")

    system = prompt["SYSTEM_INSTRUCTION"]
    if system != SECOND_OPPORTUNITY_SYSTEM:
        raise ValidationError(
            "the recorded system instruction is not the one the code renders, so the artifact "
            "and the executable prompt have drifted into two texts"
        )
    if _sha256(system) != prompt["SYSTEM_SHA256"]:
        raise ValidationError("SYSTEM_SHA256 does not hash the recorded system instruction")
    if _sha256(prompt["USER_INSTRUCTION"]) != prompt["TASK_SHA256"]:
        raise ValidationError("TASK_SHA256 does not hash the recorded user instruction")

    schema_digest = _sha256(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA, sort_keys=True))
    if prompt["OUTPUT_SCHEMA_SHA256"] != schema_digest:
        raise ValidationError("the recorded schema digest is not the live schema's")

    placeholder = prompt["INPUT_PLACEHOLDER"]
    if placeholder["region"] != "untrusted":
        raise ValidationError(
            "source-derived statements outside the untrusted region. §41 makes them data, and a "
            "region is what enforces it"
        )
    labels = placeholder["labels"]
    if len(labels) != int(placeholder["count"]):
        raise ValidationError("the placeholder count does not match its labels")
    for label in labels:
        if not (str(label).startswith("evidence=") and " claim=" in str(label)):
            raise ValidationError(f"a supplied statement label naming no lineage: {label!r}")
    if "statements" in placeholder or "text" in placeholder:
        raise ValidationError(
            "the prompt artifact carries the statement text as well as the representation, so "
            "two copies of one text can drift apart"
        )

    boundaries = prompt["SEMANTIC_BOUNDARIES"]
    if boundaries["anti_distortion_rules"] != ANTI_DISTORTION_RULES:
        raise ValidationError("the recorded anti-distortion rules are not the code's")
    named = [name for name, _, _ in FORBIDDEN_TRANSFORMATIONS]
    if list(boundaries["forbidden_transformations"]) != named:
        raise ValidationError("the frozen forbidden transformations are not the code's")
    if list(boundaries["classification_required"]) != [
        "OBSERVED_OR_EVIDENCE_SUPPORTED",
        "HYPOTHESIS_TO_VALIDATE",
        "UNKNOWN_REQUIRES_EVIDENCE",
    ]:
        raise ValidationError("§18's three classifications are not the ones frozen")
    if not str(boundaries["attribution"]).strip():
        raise ValidationError("§20 attribution recorded as a heading with no rule under it")

    if not any("INSUFFICIENT_EVIDENCE" in rule for rule in prompt["REFUSAL_RULES"]):
        raise ValidationError(
            "no refusal rule names INSUFFICIENT_EVIDENCE, so the model is not told that "
            "answering nothing is permitted"
        )
    if not any(
        "no numeric confidence" in rule or "no probability" in rule
        for rule in prompt["REFUSAL_RULES"]
    ):
        raise ValidationError("§17 forbids a numeric confidence and the prompt does not say so")
    if prompt["inherits_byte_identically"] != "sros_opportunity.synthesis.SYNTHESIS_SYSTEM":
        raise ValidationError("the prompt does not say which frozen text it inherits")


# --------------------------------------------------------------------------- the contract


def _check_the_contract(contract: dict) -> None:
    if contract["OUTPUT_SCHEMA_VERSION"] != SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION:
        raise ValidationError("the contract's schema version is not the code's")
    if contract["OUTPUT_GATE_VERSION"] != SECOND_OPPORTUNITY_GATE_VERSION:
        raise ValidationError("the contract's gate version is not the code's")
    if contract["BASE_GATE_VERSION"] != PERSISTENCE_GATE_VERSION:
        raise ValidationError(
            f"the contract names base gate {contract['BASE_GATE_VERSION']!r} and the code carries "
            f"{PERSISTENCE_GATE_VERSION!r}"
        )
    live_required = list(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"])
    if list(contract["required_fields"]) != live_required:
        raise ValidationError("the contract's required fields are not the live schema's")
    for field in live_required:
        if "score" in field or "probability" in field:
            raise ValidationError(f"§31: a required output field named {field!r}")

    if list(contract["confidence_classifications"]) != list(CONFIDENCE_CLASSIFICATIONS):
        raise ValidationError("the contract's confidence classifications are not the code's")
    if contract["numeric_confidence_requested"]:
        raise ValidationError("§17: a numeric confidence is requested")
    if not str(contract["numeric_confidence_note"]).strip():
        raise ValidationError("a refusal to request a number with no reason recorded")

    order = [str(stage) for stage in contract["validation_order"]]
    if len(order) != len(VALIDATION_STAGES):
        raise ValidationError(f"§27 asks for {len(VALIDATION_STAGES)} stages, found {len(order)}")
    for expected, actual in zip(VALIDATION_STAGES, order, strict=True):
        if expected not in actual:
            raise ValidationError(f"validation stage {actual!r} is not {expected!r} in order")
    if not str(contract["failure_policy"]).strip():
        raise ValidationError("a validation order with no stated failure policy")
    if "second model call" not in contract["failure_policy"]:
        raise ValidationError(
            "the failure policy does not refuse repair by a second call, which is the repair a "
            "failing gate invites"
        )

    recorded = {entry["name"]: entry for entry in contract["forbidden_transformations"]}
    for name, establishes, never in FORBIDDEN_TRANSFORMATIONS:
        if name not in recorded:
            raise ValidationError(f"§19 transformation {name} is not in the contract")
        entry = recorded[name]
        if not str(entry["establishes"]).strip() or not str(entry["is_not"]).strip():
            raise ValidationError(f"{name} recorded with only one half of the distinction")
        if entry["establishes"] == entry["is_not"]:
            raise ValidationError(f"{name} establishes exactly what it is not")
        del establishes, never
    if len(recorded) != len(FORBIDDEN_TRANSFORMATIONS):
        raise ValidationError("the contract carries a transformation the code does not")

    stale = contract["two_stale_checks_generalised"]
    if stale["weakened"]:
        raise ValidationError(
            "a frozen check recorded as weakened. Generalising a stale assertion is repair; "
            "weakening one to admit this packet is not"
        )
    if stale["base_gate_version_after"] != PERSISTENCE_GATE_VERSION:
        raise ValidationError("the recorded post-generalisation gate version is not the code's")
    if stale["base_gate_version_before"] == stale["base_gate_version_after"]:
        raise ValidationError("a frozen gate changed and its version did not")

    if not contract["lexical_filtering_is_not_semantic_safety"]:
        raise ValidationError("§28: a contract claiming lexical filtering proves semantic safety")
    review = contract["human_review"]
    if not review["HUMAN_OUTPUT_REVIEW_REQUIRED"]:
        raise ValidationError("§29: human output review is not required")
    if not str(review["why"]).strip() or not str(review["who"]).strip():
        raise ValidationError("human review required with no stated reason or reviewer")
    if review["weakened_to_create_opportunity_two"]:
        raise ValidationError("human review weakened so an Opportunity could be created")
    if "UNKNOWN" not in contract["independence_rule"]:
        raise ValidationError("§32: the independence rule does not keep independence UNKNOWN")


# --------------------------------------------------------------------------- the packet


def _check_the_payload(packet: dict, approval: dict, decision: dict) -> None:
    """§4 and §5. The reconstructed payload is the approved one, or nothing proceeds."""
    scope = approval["scope"]
    if packet["REPRESENTATION_SHA256"] != scope["representation_sha256"]:
        raise ValidationError(
            f"{REPRESENTATION_CHANGED}: the packet names representation "
            f"{packet['REPRESENTATION_SHA256']} and the approval names "
            f"{scope['representation_sha256']}. The approval is never updated to match, the "
            "payload is never reserialised to recover the digest, and no argument that the "
            "meaning is unchanged substitutes for the bytes"
        )
    if packet["REPRESENTATION_SCHEMA"] != scope["representation_schema"]:
        raise ValidationError("the representation schema is not the approved one")
    if packet["SUBJECT_KEY"] != scope["subject"] or packet["SUBJECT_KEY"] != SUBJECT:
        raise ValidationError("the subject is not the approved one")
    if packet["PROCESSING_PURPOSE"] != scope["processing_purpose"] or (
        packet["PROCESSING_PURPOSE"] != PURPOSE
    ):
        raise ValidationError("§8: the processing purpose is not the approved one")
    if packet["SOURCE_DECISION_PACKET_ID"] != approval["DECISION_PACKET_ID"]:
        raise ValidationError("the execution packet cites a decision packet nobody approved")
    if packet["SOURCE_DECISION_PACKET_VERSION"] != approval["DECISION_PACKET_VERSION"]:
        raise ValidationError("the cited decision packet version is not the approved one")
    if packet["SOURCE_DECISION_PACKET_SHA256"] != approval["DECISION_PACKET_SHA256_RECOMPUTED"]:
        raise ValidationError("the cited decision digest is not the recomputed approved one")
    if decision["DECISION_PACKET_ID"] != approval["DECISION_PACKET_ID"]:
        raise ValidationError("the approval and the frozen packet disagree about the packet id")
    if int(packet["REPRESENTATION_CLAIM_COUNT"]) < 1:
        raise ValidationError("a payload with no claims")
    if int(packet["REPRESENTATION_CHARACTER_COUNT"]) < 1:
        raise ValidationError("a payload of no characters")


def _check_the_route(packet: dict, register: dict) -> None:
    """§9 to §12. The provider is derived from the register and the model from held config."""
    eligible = approved_providers(register)
    if not eligible:
        raise ValidationError(
            "no provider in the current register is APPROVED, so no route is eligible and this "
            "packet names one"
        )
    if packet["PROVIDER_ID"] not in eligible:
        raise ValidationError(
            f"provider {packet['PROVIDER_ID']!r} is not APPROVED in the current register "
            f"(approved: {eligible})"
        )
    if packet["PROVIDER_POSTURE"] != "APPROVED":
        raise ValidationError("a packet naming a provider whose recorded posture is not APPROVED")
    basis = str(packet["PROVIDER_SELECTION_BASIS"])
    if not basis.strip():
        raise ValidationError("a provider with no stated selection basis")
    if "deterministic" in basis and len(eligible) != 1:
        raise ValidationError(
            f"the basis claims exactly one eligible route and the register approves {eligible}. "
            "MODEL_PROVIDER_SELECTION_REQUIRES_OPERATOR_DECISION"
        )
    if not str(packet["PROVIDER_ROUTE"]).strip():
        raise ValidationError(
            "§38: a provider with no named route, so a different route of the "
            "same vendor would inherit an assessment nobody made"
        )
    if not str(packet["MODEL_ID"]).strip():
        raise ValidationError("a packet with no model")
    if not str(packet["MODEL_SELECTION_BASIS"]).strip():
        raise ValidationError("a model with no stated selection basis")


def _check_the_parameters(packet: dict) -> None:
    """§21 and §24. Only what the Gateway supports, and exactly one call."""
    params = packet["GENERATION_PARAMETERS"]
    supplied = {
        key: value
        for key, value in params.items()
        if key != "$comment" and not key.endswith("note")
    }
    for key, value in supplied.items():
        if value is None:
            if key in LLM_REQUEST_FIELDS:
                raise ValidationError(
                    f"{key!r} is recorded as unsupported and the Gateway carries it, so a real "
                    "parameter is frozen as absent"
                )
            continue
        if key not in LLM_REQUEST_FIELDS:
            raise ValidationError(
                f"§21: {key!r} is frozen with a value and the Gateway's request type has no such "
                "field, so the packet freezes a parameter nothing reads"
            )
    if "unsupported_parameters_note" not in params:
        raise ValidationError(
            "null parameters with no note saying null means unavailable rather than defaulted"
        )
    if supplied.get("max_retries") != 0:
        raise ValidationError(
            f"§24: max_retries is {supplied.get('max_retries')!r}. A retry is a second call and "
            "this packet authorises one"
        )
    timeout = supplied.get("timeout_seconds")
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValidationError("§25: a call with no bounded timeout")
    if packet["REQUEST_TIMEOUT"] != timeout:
        raise ValidationError("the packet's timeout and its frozen parameter disagree")
    if int(packet["MAX_MODEL_CALLS"]) != 1:
        raise ValidationError(f"§24: MAX_MODEL_CALLS is {packet['MAX_MODEL_CALLS']}")
    if packet["failure_outcome"] != "EXECUTION_FAILED_NO_RETRY":
        raise ValidationError("a failure outcome that is not a stop")
    if not supplied.get("requires_structured_output"):
        raise ValidationError("a schema-bound task that does not require structured output")


def _check_the_budget(packet: dict) -> None:
    """§22 and §23. The numbers recompute, and none of them was invented."""
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    if basis["exact_tokenizer_available"]:
        raise ValidationError(
            "an exact tokenizer is claimed; then the estimate must be exact rather than measured"
        )
    if not str(basis["why"]).strip() or not str(basis["measured_pair"]).strip():
        raise ValidationError("an estimate with no stated basis for its ratio")
    if float(basis["conservative_multiplier"]) < 1.0:
        raise ValidationError("a multiplier below 1.0, which is not conservative")
    if not basis["no_test_request_was_sent"]:
        raise ValidationError("§22: a test request was sent to size a budget")
    if not str(basis["limitation"]).strip():
        raise ValidationError("a measured ratio with no stated limitation")

    inputs = int(packet["INPUT_TOKEN_ESTIMATE"])
    output = int(packet["MAX_OUTPUT_TOKENS"])
    if inputs <= 0 or output <= 0:
        raise ValidationError("a token ceiling of zero")
    if int(packet["TOTAL_TOKEN_CEILING"]) != inputs + output:
        raise ValidationError("the total token ceiling is not the sum of its parts")

    if not str(packet["PRICING_VERSION"]).strip():
        raise ValidationError(
            "§23: no pricing version. MODEL_COST_BASIS_REQUIRES_REFRESH_OR_OPERATOR_CEILING"
        )
    for key in ("INPUT_PRICE_BASIS", "OUTPUT_PRICE_BASIS"):
        if not str(packet[key]).strip():
            raise ValidationError(f"{key} is empty, so a price was assumed rather than held")
    worst = float(packet["WORST_CASE_CALL_COST"])
    ceiling = float(packet["EXECUTION_COST_CEILING"])
    if worst <= 0:
        raise ValidationError("a worst case of zero, which no priced call has")
    if ceiling < worst:
        raise ValidationError(
            f"the ceiling {ceiling} is below the worst case {worst}, so the packet authorises a "
            "call it also forbids"
        )
    if not str(packet["cost_ceiling_basis"]).strip():
        raise ValidationError("a ceiling with no stated basis")
    if not str(packet["COST_UNIT_NOTE"]).strip():
        raise ValidationError(
            "a cost in units the record does not explain. ADR-006 makes them provider-agnostic"
        )


def _check_the_boundaries(packet: dict, approval: dict) -> None:
    """§6, §13, §26, §30 and §34."""
    for key in CAPABILITY_NEGATIVES:
        if packet[key]:
            raise ValidationError(f"§6/§13: {key} is true")
    if not str(packet["capability_note"]).strip():
        raise ValidationError("six negatives with no statement of what IS reachable")

    retention = packet["RETENTION_ON_EXECUTION"]
    hidden = str(retention["hidden_reasoning"])
    if not hidden.startswith("NOT RETAINED"):
        raise ValidationError(f"§26: hidden reasoning recorded as {hidden!r}")
    if "RETAINED" not in str(retention["raw_provider_response"]):
        raise ValidationError(
            "the raw response is not retained, so a gate verdict about it would be unverifiable"
        )

    policy = packet["PERSISTENCE_POLICY"]
    if policy["persist_if_gate_accepts"]:
        raise ValidationError("§30: persistence on a gate verdict alone")
    if not policy["human_review_required_before_persistence"]:
        raise ValidationError("§29: persistence with no human review in front of it")
    if int(policy["opportunity_created_by_this_packet"]) != 0:
        raise ValidationError("a preparation that created an Opportunity")
    if policy["score_persisted"] or policy["independence_group_created"]:
        raise ValidationError("§31/§32: a score or an independence group")
    if not policy["provenance_the_first_revision_must_carry"]:
        raise ValidationError("a persistence policy naming no provenance")

    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"]:
        raise ValidationError(
            "§34: the frozen packet records an approval of itself. An approval lives beside it, "
            "because marking a frozen document approved changes the bytes that were approved"
        )
    if not str(packet["approval_note"]).strip():
        raise ValidationError("no note keeping the egress approval apart from an execution one")
    if "egress" not in packet["approval_note"].lower():
        raise ValidationError(
            "§34: the packet does not say that the TED egress approval is a different act from "
            "approving this execution"
        )

    excluded = {item.lower() for item in approval["NOT_AUTHORIZED"]}
    if "model training" in excluded and packet["TRAINING"]:
        raise ValidationError("training, which the operator excluded by name")
    if "fine-tuning" in excluded and packet["FINE_TUNING"]:
        raise ValidationError("fine-tuning, which the operator excluded by name")
    if "embeddings" in excluded and packet["EMBEDDINGS"]:
        raise ValidationError("embeddings, which the operator excluded by name")


def _check_the_preparation(packet: dict, preparation: dict) -> None:
    """§2, §3, §35 to §40."""
    if packet["PREPARATION_VERSION"] != preparation["artifact_version"]:
        raise ValidationError(
            f"the packet names preparation {packet['PREPARATION_VERSION']!r} and the current "
            f"artifact is {preparation['artifact_version']!r}"
        )
    accounting = packet["preparation_accounting"]
    for key in ZERO_PREPARATION:
        if accounting[key] != 0:
            raise ValidationError(f"{key} is {accounting[key]}, and preparing a packet does 0")
    guards = packet["regression_guards"]
    for key in (
        "ted_egress_permission_unchanged",
        "first_opportunity_untouched",
        "q1_globalping_arc_unchanged",
        "candidate_selection_unchanged",
        "preparation_v4_unchanged",
    ):
        if not guards[key]:
            raise ValidationError(f"§39/§40: {key} is false")
    if not PREPARATION_V4.exists():
        raise ValidationError(
            "§2: preparation v4 is gone. A historical preparation is never rewritten and never "
            "removed, because a later mission's record points at it"
        )


def _check_the_live_governance(packet: dict, preparation: dict) -> None:
    """§3. v5 reads the live governance, and the selected packet's egress is AVAILABLE."""
    selected = None
    for entry in preparation["packets"]:
        if entry.get("subject") == SUBJECT:
            selected = entry
            break
    if selected is None:
        raise ValidationError(f"preparation {preparation['artifact_version']} has no {SUBJECT}")
    if selected["packet_id"] != packet["SELECTED_PACKET_ID"]:
        raise ValidationError(
            "the execution packet names a selected packet the current preparation does not carry"
        )
    egress = selected["external_synthesis"]
    if egress["availability"] != "AVAILABLE":
        raise ValidationError(
            f"§3: the live egress gate reports {egress['availability']} for {SUBJECT} "
            f"({egress['refusal_reasons']}), so this packet describes a call the deployment "
            "refuses"
        )
    if egress["refusal_reasons"]:
        raise ValidationError("an AVAILABLE gate carrying refusal reasons")


def validate() -> tuple[dict, dict, dict]:
    prompt = _load(PROMPT)
    contract = _load(CONTRACT)
    packet = _load(PACKET)
    approval = _load(APPROVAL)
    decision = _load(DECISION_PACKET)
    register = _load(PROVIDER_REGISTER)
    preparation = _load(PREPARATION_V5)

    _check_the_prompt(prompt)
    _check_the_contract(contract)
    _check_the_payload(packet, approval, decision)
    _check_the_route(packet, register)
    _check_the_parameters(packet)
    _check_the_budget(packet)
    _check_the_boundaries(packet, approval)
    _check_the_preparation(packet, preparation)
    _check_the_live_governance(packet, preparation)

    if packet["PROMPT_SHA256"] != prompt["PROMPT_SHA256"]:
        raise ValidationError("the execution packet and the frozen prompt name different digests")
    if packet["PROMPT_ID"] != prompt["PROMPT_ID"]:
        raise ValidationError("the execution packet cites a prompt the frozen record does not")
    if packet["OUTPUT_SCHEMA_VERSION"] != contract["OUTPUT_SCHEMA_VERSION"]:
        raise ValidationError("the packet and the contract name different output schemas")
    if packet["OUTPUT_GATE_VERSION"] != contract["OUTPUT_GATE_VERSION"]:
        raise ValidationError("the packet and the contract name different output gates")

    recomputed = packet_digest(packet)
    if packet["EXECUTION_PACKET_SHA256"] != recomputed:
        raise ValidationError(
            f"§33: the packet records {packet['EXECUTION_PACKET_SHA256']} and its bound fields "
            f"hash to {recomputed}, so an approval citing the recorded value would name a call "
            "this packet no longer describes"
        )
    if not str(packet["digest_covers"]).strip():
        raise ValidationError("a digest with no statement of what it binds")
    return prompt, contract, packet


# --------------------------------------------------------------------------- rendering


def render_prompt(prompt: dict) -> str:
    placeholder = prompt["INPUT_PLACEHOLDER"]
    lines = [
        f"# {prompt['PROMPT_ID']} v{prompt['PROMPT_VERSION']}",
        "",
        "Generated from `second-opportunity-synthesis-prompt-v1.json`. Do not edit by hand.",
        "",
        prompt["$comment"],
        "",
        f"- procedure `{prompt['PROCEDURE']}`",
        f"- subject `{prompt['SUBJECT']}`, packet `{prompt['PACKET_ID']}`",
        f"- **PROMPT_SHA256** `{prompt['PROMPT_SHA256']}`",
        f"- system region `{prompt['SYSTEM_SHA256']}`",
        f"- task region `{prompt['TASK_SHA256']}`",
        f"- output schema `{prompt['OUTPUT_SCHEMA_VERSION']}` `{prompt['OUTPUT_SCHEMA_SHA256']}`",
        "",
        prompt["prompt_hash_covers"] + ".",
        "",
        "## What the base prompt inherits",
        "",
        f"Byte-identical from `{prompt['inherits_byte_identically']}`, at base version "
        f"{prompt['base_prompt_version']}.",
        "",
        prompt["base_prompt_version_note"] + ".",
        "",
        "## The input region",
        "",
        f"{placeholder['count']} supplied statements, in the `{placeholder['region']}` region, "
        f"shaped as {placeholder['shape']}.",
        "",
    ]
    lines.extend(f"- `{label}`" for label in placeholder["labels"])
    lines += [
        "",
        placeholder["note"] + ".",
        "",
        "## Refusal rules",
        "",
    ]
    lines.extend(f"- {rule}." for rule in prompt["REFUSAL_RULES"])
    boundaries = prompt["SEMANTIC_BOUNDARIES"]
    lines += [
        "",
        "## Semantic boundaries",
        "",
        "Forbidden transformations: "
        + ", ".join(f"`{name}`" for name in boundaries["forbidden_transformations"])
        + ".",
        "",
        "Every substantive statement is classified "
        + ", ".join(f"`{name}`" for name in boundaries["classification_required"])
        + ".",
        "",
        boundaries["attribution"] + ".",
        "",
        "```text",
        boundaries["anti_distortion_rules"],
        "```",
        "",
        "## The frozen system instruction",
        "",
        "```text",
        prompt["SYSTEM_INSTRUCTION"].strip(),
        "```",
        "",
        "## The frozen task instruction",
        "",
        "```text",
        prompt["USER_INSTRUCTION"].strip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def render_contract(contract: dict) -> str:
    review = contract["human_review"]
    stale = contract["two_stale_checks_generalised"]
    lines = [
        f"# {contract['OUTPUT_SCHEMA_VERSION']}",
        "",
        "Generated from `second-opportunity-synthesis-output-contract-v1.json`. "
        "Do not edit by hand.",
        "",
        contract["$comment"],
        "",
        f"- schema `{contract['OUTPUT_SCHEMA_VERSION']}` `{contract['OUTPUT_SCHEMA_SHA256']}`",
        f"- gate `{contract['OUTPUT_GATE_VERSION']}`",
        f"- base gate `{contract['BASE_GATE_VERSION']}`, base audit "
        f"`{contract['BASE_AUDIT_VERSION']}`",
        f"- {len(contract['required_fields'])} required fields",
        "",
        "## Required fields",
        "",
    ]
    lines.extend(f"- `{field}`" for field in contract["required_fields"])
    lines += [
        "",
        "Added by this contract: "
        + ", ".join(f"`{name}`" for name in contract["added_by_this_contract"])
        + ".",
        "",
        "## The mission's field names against this repository's vocabulary",
        "",
        "| asked for | carried by |",
        "|---|---|",
    ]
    for asked, carried in contract["field_mapping"].items():
        if asked.startswith("$"):
            continue
        lines.append(f"| `{asked}` | {carried} |")
    lines += [
        "",
        "## Confidence",
        "",
        "Classifications: "
        + ", ".join(f"`{name}`" for name in contract["confidence_classifications"])
        + ".",
        "",
        contract["numeric_confidence_note"] + ".",
        "",
        "## Validation order",
        "",
    ]
    lines.extend(f"{i}. {stage}" for i, stage in enumerate(contract["validation_order"], 1))
    lines += [
        "",
        contract["failure_policy"] + ".",
        "",
        "## Two stale checks, generalised rather than weakened",
        "",
        stale["reliability_assertion"] + ".",
        "",
        stale["external_knowledge_markers"] + ".",
        "",
        f"Base gate {stale['base_gate_version_before']} to "
        f"**{stale['base_gate_version_after']}**. Weakened: {stale['weakened']}.",
        "",
        "## Forbidden transformations",
        "",
        "| name | the packet establishes | it is NOT |",
        "|---|---|---|",
    ]
    for entry in contract["forbidden_transformations"]:
        lines.append(f"| `{entry['name']}` | {entry['establishes']} | {entry['is_not']} |")
    lines += [
        "",
        "## Independence",
        "",
        contract["independence_rule"] + ".",
        "",
        "## Human review",
        "",
        f"**HUMAN_OUTPUT_REVIEW_REQUIRED = {review['HUMAN_OUTPUT_REVIEW_REQUIRED']}**, by "
        f"{review['who']}, {review['when']}.",
        "",
        review["why"] + ".",
        "",
        f"Lexical filtering is not semantic safety: "
        f"{contract['lexical_filtering_is_not_semantic_safety']}.",
        "",
    ]
    return "\n".join(lines)


def render_packet(packet: dict) -> str:
    params = packet["GENERATION_PARAMETERS"]
    policy = packet["PERSISTENCE_POLICY"]
    basis = packet["TOKEN_ESTIMATION_BASIS"]
    lines = [
        f"# {packet['EXECUTION_PACKET_ID']} v{packet['EXECUTION_PACKET_VERSION']}",
        "",
        "Generated from `second-opportunity-synthesis-execution-packet-v1.json`. "
        "Do not edit by hand.",
        "",
        packet["$comment"],
        "",
        f"**EXECUTION_PACKET_SHA256** `{packet['EXECUTION_PACKET_SHA256']}`",
        "",
        f"**OPERATOR_EXECUTION_APPROVAL_RECORDED = "
        f"{packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']}**",
        "",
        packet["approval_note"] + ".",
        "",
        "## The egress decision this rests on",
        "",
        f"- `{packet['SOURCE_DECISION_PACKET_ID']}` v{packet['SOURCE_DECISION_PACKET_VERSION']}",
        f"- `{packet['SOURCE_DECISION_PACKET_SHA256']}`",
        "",
        "## The payload",
        "",
        f"- subject `{packet['SUBJECT_KEY']}` ({packet['SUBJECT_LABEL']})",
        f"- selected packet `{packet['SELECTED_PACKET_ID']}`",
        f"- preparation `{packet['PREPARATION_VERSION']}`",
        f"- purpose {packet['PROCESSING_PURPOSE']}",
        f"- representation `{packet['REPRESENTATION_SCHEMA']}`",
        f"- **REPRESENTATION_SHA256** `{packet['REPRESENTATION_SHA256']}`",
        f"- {packet['REPRESENTATION_CLAIM_COUNT']} claims, "
        f"{packet['REPRESENTATION_CHARACTER_COUNT']} characters",
        "",
        "## The route",
        "",
        f"- provider `{packet['PROVIDER_ID']}`, posture **{packet['PROVIDER_POSTURE']}**",
        f"- route {packet['PROVIDER_ROUTE']}",
        f"- model `{packet['MODEL_ID']}` on tier `{packet['MODEL_TIER']}`",
        "",
        packet["PROVIDER_SELECTION_BASIS"] + ".",
        "",
        packet["MODEL_SELECTION_BASIS"] + ".",
        "",
        "## The prompt",
        "",
        f"- `{packet['PROMPT_ID']}` v{packet['PROMPT_VERSION']}",
        f"- **PROMPT_SHA256** `{packet['PROMPT_SHA256']}`",
        "",
        "## Generation parameters",
        "",
        "| parameter | value |",
        "|---|---|",
    ]
    for key, value in params.items():
        if key == "$comment" or key.endswith("note"):
            continue
        lines.append(f"| `{key}` | `{value}` |")
    lines += [
        "",
        params["unsupported_parameters_note"] + ".",
        "",
        params["max_retries_note"] + ".",
        "",
        "## Budget",
        "",
        f"- input estimate {packet['INPUT_TOKEN_ESTIMATE']} tokens, max output "
        f"{packet['MAX_OUTPUT_TOKENS']}, ceiling {packet['TOTAL_TOKEN_CEILING']}",
        f"- pricing version `{packet['PRICING_VERSION']}`",
        f"- {packet['INPUT_PRICE_BASIS']}",
        f"- {packet['OUTPUT_PRICE_BASIS']}",
        f"- **WORST_CASE_CALL_COST {packet['WORST_CASE_CALL_COST']}** cost units",
        f"- **EXECUTION_COST_CEILING {packet['EXECUTION_COST_CEILING']}** cost units",
        f"- MAX_MODEL_CALLS {packet['MAX_MODEL_CALLS']}, timeout {packet['REQUEST_TIMEOUT']}s",
        "",
        packet["cost_ceiling_basis"] + ".",
        "",
        packet["COST_UNIT_NOTE"] + ".",
        "",
        f"Exact tokenizer available: {basis['exact_tokenizer_available']}. {basis['why']}. "
        f"{basis['measured_pair']}, giving a raw estimate of {basis['raw_estimate']} tokens over "
        f"{basis['wire_characters']} wire characters, multiplied by "
        f"{basis['conservative_multiplier']}.",
        "",
        basis["limitation"] + ".",
        "",
        f"No test request was sent: {basis['no_test_request_was_sent']}.",
        "",
        "## What the call cannot reach",
        "",
        "| capability | state |",
        "|---|---|",
    ]
    for key in CAPABILITY_NEGATIVES:
        lines.append(f"| {key} | {packet[key]} |")
    lines += [
        "",
        packet["capability_note"] + ".",
        "",
        "## Retention, if it runs",
        "",
        "| what | kept |",
        "|---|---|",
    ]
    for key, value in packet["RETENTION_ON_EXECUTION"].items():
        if key == "note":
            continue
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        packet["RETENTION_ON_EXECUTION"]["note"] + ".",
        "",
        "## Persistence",
        "",
        f"- persist on a gate verdict alone: {policy['persist_if_gate_accepts']}",
        f"- human review before persistence: {policy['human_review_required_before_persistence']}",
        f"- Opportunities created by this packet: {policy['opportunity_created_by_this_packet']}",
        f"- score persisted: {policy['score_persisted']}, independence group: "
        f"{policy['independence_group_created']}",
        "",
        "The first revision must carry: "
        + ", ".join(policy["provenance_the_first_revision_must_carry"])
        + ".",
        "",
        policy["note"] + ".",
        "",
        "## Failure",
        "",
        f"**{packet['failure_outcome']}**. {packet['failure_note']}.",
        "",
        f"{packet['timeout_note']}.",
        "",
        "## What preparing this cost",
        "",
        "| counter | value |",
        "|---|---|",
    ]
    for key in ZERO_PREPARATION:
        lines.append(f"| {key} | {packet['preparation_accounting'][key]} |")
    lines += [
        "",
        packet["preparation_accounting"]["note"] + ".",
        "",
        "## What the digest binds",
        "",
        packet["digest_covers"] + ".",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        prompt, contract, packet = validate()
    except ValidationError as error:
        print(f"REFUSED  second opportunity execution packet: {error}")
        return 1
    pages = (
        (PROMPT_MD, render_prompt(prompt)),
        (CONTRACT_MD, render_contract(contract)),
        (PACKET_MD, render_packet(packet)),
    )
    if args.check:
        for path, text in pages:
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print("ok       the second-opportunity execution packet matches its records")
        return 0
    for path, text in pages:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"packet   {packet['EXECUTION_PACKET_ID']} {packet['EXECUTION_PACKET_SHA256']}")
    print(
        f"approval OPERATOR_EXECUTION_APPROVAL_RECORDED = "
        f"{packet['OPERATOR_EXECUTION_APPROVAL_RECORDED']}"
    )
    print(
        f"calls    0 made; MAX_MODEL_CALLS {packet['MAX_MODEL_CALLS']}, "
        f"ceiling {packet['EXECUTION_COST_CEILING']} cost units"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
