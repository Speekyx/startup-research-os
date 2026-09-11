"""Execute the operator-approved second-Opportunity synthesis. Mission 1.84.2.

ONE provider request, under the frozen packet `SECOND-OPPORTUNITY-SYNTH-EXEC-V1` version 1.

    uv run python infrastructure/scripts/run_second_opportunity_execution.py
    uv run python infrastructure/scripts/run_second_opportunity_execution.py --execute

**Verification is the default and execution is the opt-in.** The eight pre-execution checks the
operator's approval enumerates run first, every time, and a single mismatch on any bound field
refuses before a socket exists. A runner whose default did the outward thing would make the safe
path the one somebody has to remember.

**No retry, under any circumstance.** `max_retries` is 0 on the request, so the Gateway's own
retry branch cannot be entered, and there is no `except` here that calls the provider again.
Mission 1.31.1 retried once on a schema failure; that mission's approval permitted it and this
one's does not.

**Nothing is persisted.** No Opportunity, no revision, no link, no score. Even a clean pass through
all eight validation stages stops at a human-review packet, because the frozen output contract
records HUMAN_OUTPUT_REVIEW_REQUIRED and the approval repeats it.

The credential is read from the environment by the provider adapter and is never read, printed,
logged or written here.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
SCRIPTS = ROOT / "infrastructure" / "scripts"
sys.path.insert(0, str(SCRIPTS))

PACKET_FILE = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
REGISTER = DATA / "model-provider-policy-v1.json"
RESPONSE_ARTIFACT = DATA / "second-opportunity-synthesis-response-v1.json"
EXECUTION_RECORD = DATA / "second-opportunity-synthesis-execution-record-v1.json"
CORRELATION_ID = "mission-1.84.2-second-opportunity-synthesis"

SUBJECT = "ted-eu:CPV-class:9261"
SOURCE_ID = "ted-eu"
USE_PROFILE = "local-private-research-v1"

#: The operator's approval, transcribed. Every one of these is compared rather than trusted, and
#: a mismatch refuses. They are pinned here rather than read from the packet, because a runner
#: that read its expectations from the file it is checking would check nothing.
APPROVED = {
    "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V1",
    "EXECUTION_PACKET_VERSION": 1,
    "EXECUTION_PACKET_SHA256": ("570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"),
    "PROVIDER_ID": "anthropic",
    "MODEL_ID": "claude-sonnet-5",
    "SUBJECT_KEY": SUBJECT,
    "REPRESENTATION_SHA256": ("2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"),
    "PROMPT_SHA256": "af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080",
    "MAX_MODEL_CALLS": 1,
    "MAX_RETRIES": 0,
    "REQUEST_TIMEOUT": 60.0,
    "EXECUTION_COST_CEILING": 0.10,
    "MAX_OUTPUT_TOKENS": 3000,
    "WEB": False,
    "TOOLS": False,
    "EXTERNAL_RETRIEVAL": False,
    "TRAINING": False,
    "FINE_TUNING": False,
    "EMBEDDINGS": False,
}


class RefusedError(RuntimeError):
    """A bound field moved. Nothing is sent."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _import_packet_digest():
    """One authority for what the execution digest binds: Mission 1.84's own gate."""
    import importlib.util

    path = SCRIPTS / "render_second_opportunity_execution_packet.py"
    spec = importlib.util.spec_from_file_location("execution_packet_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------- the eight checks


def rebuild(use_profile: str) -> tuple[object, dict, dict, dict]:
    """Rebuild the selected packet through the CURRENT deterministic preparation path."""
    import psycopg
    from run_opportunity_preparation import (
        SUBJECT_REGISTRY,
        _families,
        _load_env,
        _resolve_late,
        _rows,
        _standings,
    )
    from sros_opportunity import (
        EvidenceFacets,
        IndependenceState,
        PacketEligibility,
        assess_eligibility,
        build_packet,
        group_by_subject,
        load_subject_registry,
        map_signal_type,
    )

    _load_env()
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros"
    )
    standings = _standings(use_profile)
    families = _families(use_profile)
    rows, live = _rows(use_profile)

    assessed = []
    evidence_to_claim: dict[str, str] = {}
    for row in rows:
        mapping = map_signal_type(row["signal_type_id"])
        reliability, status, _ = _resolve_late(row, live)
        facets = EvidenceFacets(
            evidence_id=str(row["id"]),
            claim_id=str(row["claim_id"]),
            source_id=str(row["source_id"] or ""),
            source_family=families.get(str(row["source_id"]), "UNREGISTERED"),
            use_profile_id=use_profile,
            extraction_method=row["extraction_method"],
            claim_type=str(row["claim_type"]),
            claim_lifecycle=str(row["lifecycle"]),
            claim_temporality=str(row["temporality"]),
            claim_origin=str(row["origin"]),
            direction=str(row["direction"]),
            observation_category=str(row["observation_category"]),
            evidence_level=int(row["evidence_level"]),
            relevance=row["relevance"],
            directness=row["directness"],
            extraction_confidence=row["extraction_confidence"],
            reliability=reliability,
            reliability_status=status,
            independence_state=IndependenceState(str(row["independence_state"])),
            independence_group_id=(
                str(row["independence_group_id"]) if row["independence_group_id"] else None
            ),
            observed_at=(row["observed_at"].isoformat() if row["observed_at"] else None),
            signal_type_id=row["signal_type_id"],
            dimensions=mapping.dimensions if mapping else frozenset(),
            dimension_bound=mapping.bound if mapping else "",
        )
        decision = assess_eligibility(facets, standings.get(facets.source_id))
        assessed.append((facets, decision.eligibility, row["scope"]))
        evidence_to_claim[facets.evidence_id] = facets.claim_id

    admissible = [
        (f, e, s)
        for f, e, s in assessed
        if e in (PacketEligibility.ELIGIBLE_CONTEXT, PacketEligibility.ELIGIBLE_SCORING)
    ]
    registry = load_subject_registry(SUBJECT_REGISTRY)
    groups = group_by_subject([(f, s) for f, _, s in admissible], registry=registry)
    eligibility_by_id = {f.evidence_id: e for f, e, _ in admissible}

    packet = None
    for group in groups:
        if str(group.label) != SUBJECT:
            continue
        packet = build_packet(
            group.key,
            group.label,
            tuple((f, eligibility_by_id[f.evidence_id]) for f in group.facets),
        )
    if packet is None:
        raise RefusedError(f"the current preparation path produces no packet for {SUBJECT}")

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, r.statement FROM research.claims c
              JOIN research.claim_revisions r ON r.claim_id = c.id
             WHERE c.id = ANY(%s)
               AND r.revision = (SELECT max(revision) FROM research.claim_revisions r2
                                  WHERE r2.claim_id = c.id)
            """,
            (sorted(packet.claim_ids),),
        )
        statements = {str(cid): stmt for cid, stmt in cur.fetchall()}
    return packet, statements, evidence_to_claim, standings


def verify(use_profile: str) -> dict:
    """The operator's eight pre-execution checks. Any failure refuses before a socket exists."""
    from sros_opportunity import (
        ExternalSynthesisDecision,
        SynthesisAvailability,
        authorize_packet_for_external_synthesis,
        render_second_opportunity_prompt,
        second_opportunity_prompt_hash,
        serialize_packet_for_model,
    )

    findings: dict[str, object] = {}
    packet_file = _load(PACKET_FILE)

    # 1. recompute the execution packet digest and match the approval
    gate = _import_packet_digest()
    recomputed = gate.packet_digest(packet_file)
    findings["1_EXECUTION_PACKET_SHA256_RECOMPUTED"] = recomputed
    if recomputed != APPROVED["EXECUTION_PACKET_SHA256"]:
        raise RefusedError(
            f"the packet's bound fields hash to {recomputed}, and the approval names "
            f"{APPROVED['EXECUTION_PACKET_SHA256']}"
        )
    if packet_file["EXECUTION_PACKET_SHA256"] != recomputed:
        raise RefusedError("the packet's recorded digest is not its recomputed one")

    # 2. version 1 unchanged
    if packet_file["EXECUTION_PACKET_ID"] != APPROVED["EXECUTION_PACKET_ID"]:
        raise RefusedError("the packet id is not the approved one")
    if packet_file["EXECUTION_PACKET_VERSION"] != APPROVED["EXECUTION_PACKET_VERSION"]:
        raise RefusedError("the packet version moved")
    if packet_file["OPERATOR_EXECUTION_APPROVAL_RECORDED"]:
        raise RefusedError(
            "the frozen packet has been edited to record an approval inside itself, so its bytes "
            "are no longer the bytes that were approved"
        )
    findings["2_VERSION_UNCHANGED"] = True

    # 3. recompute the representation digest
    packet, statements, evidence_to_claim, standings = rebuild(use_profile)
    measurement_only = ExternalSynthesisDecision(
        availability=SynthesisAvailability.AVAILABLE,
        packet_id=packet.packet_id,
        refusal_reasons=(),
        per_source=((SOURCE_ID, "RECOMPUTED_FOR_VERIFICATION"),),
    )
    serialized = serialize_packet_for_model(packet, measurement_only, statements)
    representation = _sha256(serialized)
    findings["3_REPRESENTATION_SHA256_RECOMPUTED"] = representation
    findings["3_REPRESENTATION_CHARACTERS"] = len(serialized)
    if representation != APPROVED["REPRESENTATION_SHA256"]:
        raise RefusedError(
            f"APPROVED_TED_EGRESS_REPRESENTATION_CHANGED: recomputed {representation}, approved "
            f"{APPROVED['REPRESENTATION_SHA256']}. The approval is never updated to match and the "
            "payload is never reserialised to recover the digest"
        )
    if packet.packet_id != packet_file["SELECTED_PACKET_ID"]:
        raise RefusedError("the rebuilt packet is not the one the execution packet names")

    # 4. recompute the rendered prompt digest
    parts = render_second_opportunity_prompt(packet, statements, evidence_to_claim)
    prompt_hash = second_opportunity_prompt_hash(parts)
    findings["4_PROMPT_SHA256_RECOMPUTED"] = prompt_hash
    if prompt_hash != APPROVED["PROMPT_SHA256"]:
        raise RefusedError(
            f"the rendered prompt hashes to {prompt_hash}, and the approval names "
            f"{APPROVED['PROMPT_SHA256']}. A changed prompt is a different execution"
        )

    # 5. provider posture still APPROVED
    register = _load(REGISTER)
    posture = next(
        (
            str(e["posture"])
            for e in register["providers"]
            if e["provider_id"] == APPROVED["PROVIDER_ID"]
        ),
        "NOT_ASSESSED",
    )
    findings["5_PROVIDER_POSTURE"] = posture
    if posture != "APPROVED":
        raise RefusedError(f"provider {APPROVED['PROVIDER_ID']} posture is {posture}")
    if packet_file["PROVIDER_ID"] != APPROVED["PROVIDER_ID"]:
        raise RefusedError("the packet names a provider the approval does not")
    if packet_file["MODEL_ID"] != APPROVED["MODEL_ID"]:
        raise RefusedError("the packet names a model the approval does not")

    # 6. TED source egress still PERMITTED_WITH_CONDITIONS
    standing = standings.get(SOURCE_ID)
    if standing is None:
        raise RefusedError(f"{SOURCE_ID} has no standing under {use_profile}")
    transmission = standing.transmission_state
    findings["6_TED_EXTERNAL_MODEL_TRANSMISSION"] = str(transmission)
    findings["6_TED_PERMITS_TRANSMISSION"] = standing.permits_external_model_transmission
    if not standing.permits_external_model_transmission:
        raise RefusedError(f"{SOURCE_ID} does not permit external model transmission")
    if "PERMITTED_WITH_CONDITIONS" not in str(transmission):
        raise RefusedError(
            f"TED external_model_transmission is {transmission}, and the approval rests on "
            "PERMITTED_WITH_CONDITIONS"
        )
    live_gate = authorize_packet_for_external_synthesis(
        packet,
        {sid: standings[sid] for sid in packet.source_ids if sid in standings},
        provider_configured=bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
        provider_posture=posture,
    )
    findings["6_LIVE_PACKET_GATE"] = live_gate.availability.value
    findings["6_LIVE_GATE_REFUSALS"] = list(live_gate.refusal_reasons)
    if live_gate.availability is not SynthesisAvailability.AVAILABLE:
        raise RefusedError(
            f"the live egress gate reports {live_gate.availability.value}: "
            f"{list(live_gate.refusal_reasons)}"
        )

    # 7. every execution parameter still matches the frozen packet
    params = packet_file["GENERATION_PARAMETERS"]
    checks = {
        "MAX_MODEL_CALLS": packet_file["MAX_MODEL_CALLS"],
        "MAX_RETRIES": params["max_retries"],
        "REQUEST_TIMEOUT": float(packet_file["REQUEST_TIMEOUT"]),
        "EXECUTION_COST_CEILING": float(packet_file["EXECUTION_COST_CEILING"]),
        "MAX_OUTPUT_TOKENS": packet_file["MAX_OUTPUT_TOKENS"],
        "WEB": packet_file["WEB"],
        "TOOLS": packet_file["TOOLS"],
        "EXTERNAL_RETRIEVAL": packet_file["EXTERNAL_RETRIEVAL"],
        "TRAINING": packet_file["TRAINING"],
        "FINE_TUNING": packet_file["FINE_TUNING"],
        "EMBEDDINGS": packet_file["EMBEDDINGS"],
        "SUBJECT_KEY": packet_file["SUBJECT_KEY"],
    }
    mismatched = {k: v for k, v in checks.items() if APPROVED.get(k, v) != v}
    findings["7_PARAMETERS"] = checks
    if mismatched:
        raise RefusedError(f"bound parameters differ from the approval: {mismatched}")
    for key in ("temperature", "top_p", "seed", "reasoning_effort"):
        if params[key] is not None:
            raise RefusedError(f"{key} is frozen with a value the Gateway does not carry")
    if not str(packet_file["RETENTION_ON_EXECUTION"]["hidden_reasoning"]).startswith(
        "NOT RETAINED"
    ):
        raise RefusedError("the retention policy no longer refuses hidden reasoning")

    # 8. nothing left to refuse
    findings["8_ALL_BOUND_FIELDS_MATCH"] = True
    findings["VERIFIED_AT"] = dt.datetime.now(dt.UTC).isoformat()
    return {
        "findings": findings,
        "packet": packet,
        "packet_file": packet_file,
        "statements": statements,
        "evidence_to_claim": evidence_to_claim,
        "parts": parts,
        "prompt_hash": prompt_hash,
        "representation": representation,
        "serialized_characters": len(serialized),
        "live_gate": live_gate,
    }


# --------------------------------------------------------------------- consumed authority


def consumed_approvals() -> list[dict]:
    """Approvals already spent, read from the record that lives BESIDE the frozen packet.

    Section 13. The frozen packet is never edited to say it has been used -- that would change
    the bytes that were approved -- so the fact lives here, and the guard reads it rather than
    relying on anybody remembering.
    """
    if not EXECUTION_RECORD.exists():
        return []
    record = _load(EXECUTION_RECORD)
    entries = record.get("CONSUMED_APPROVALS")
    if isinstance(entries, list):
        return [e for e in entries if isinstance(e, dict)]
    # A single-execution record is one consumed approval.
    if record.get("EXECUTION_APPROVAL_CONSUMED"):
        return [
            {
                "execution_packet_sha256": record.get("execution_packet_sha256"),
                "execution_packet_version": record.get("execution_packet_version"),
                "provider_requests": record.get("actual_provider_requests"),
            }
        ]
    return []


def refuse_if_consumed(packet_sha256: str) -> None:
    """A failed call spends an approval exactly as a successful one does."""
    for entry in consumed_approvals():
        if entry.get("execution_packet_sha256") != packet_sha256:
            continue
        raise RefusedError(
            "EXECUTION_APPROVAL_ALREADY_CONSUMED: the approval for execution packet "
            f"{packet_sha256} records {entry.get('provider_requests')} provider request(s) "
            "already made. An approval authorising exactly one execution is spent by the "
            "execution, whatever the output turned out to be. A further call needs a new "
            "operator approval naming a new packet digest."
        )


# --------------------------------------------------------------------- retention


#: Section 11 E. Shapes a credential takes. Redacted before anything is written, so a provider
#: error that echoes a header cannot land in a committed artifact.
SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{6,}"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"\bey[JI][A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{8,}"),
)

#: Section 11 D. Keys a provider may use for hidden reasoning. None is requested, and none is
#: kept even if one arrives: the frozen retention policy says NOT RETAINED.
REASONING_KEYS = ("thinking", "reasoning", "reasoning_content", "chain_of_thought")


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def strip_reasoning(value):
    """Drop any hidden-reasoning block a provider volunteered, at any depth."""
    if isinstance(value, dict):
        return {k: strip_reasoning(v) for k, v in value.items() if k.lower() not in REASONING_KEYS}
    if isinstance(value, list):
        return [strip_reasoning(v) for v in value]
    return value


class RecordingTransport:
    """Keeps the bytes that arrived, so a failure still has a response to point at.

    Mission 1.84.2 learned this the expensive way. The frozen retention policy says the raw
    provider response is RETAINED because *a gate verdict over a response nobody kept is
    unverifiable* -- and on the consumed call the bytes were discarded by the exception path,
    which is precisely when they were worth most. The Gateway builds its result locally, so
    nothing downstream of it can recover them; the transport seam is where they arrive, and a
    mission that must keep them keeps them here. It is not in the Gateway because what to retain
    is a per-mission decision, not a property every caller should inherit.
    """

    def __init__(self, inner) -> None:
        self.inner = inner
        self.responses: list[dict[str, object]] = []
        self.transport_errors: list[str] = []

    def post_json(self, *args, **kwargs):
        try:
            response = self.inner.post_json(*args, **kwargs)
        except Exception as exc:
            # A transport failure has no body, and recording that it had none is itself a fact.
            self.transport_errors.append(f"{type(exc).__name__}: {redact(str(exc))}")
            raise
        body = getattr(response, "body", b"")
        text = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
        self.responses.append(
            {
                "status": getattr(response, "status", None),
                "body": redact(text),
                "headers": {
                    k: v
                    for k, v in (getattr(response, "headers", {}) or {}).items()
                    if k.lower() in ("request-id", "x-request-id", "anthropic-request-id")
                },
            }
        )
        return response


def build_execution_artifact(
    *,
    outcome: str,
    transport_responses: list[dict[str, object]],
    transport_errors: list[str],
    telemetry: list,
    structured: dict | None,
    failure: BaseException | None,
    timing: dict,
    validation: dict | None = None,
) -> dict:
    """One artifact shape for every terminal path. Section 11 C.

    A path that produced no bytes says so with an explicit status rather than by omitting a key,
    because a missing key and a measured absence read the same to whoever comes next.
    """
    raw = transport_responses[0] if transport_responses else None
    usage = [
        {
            "input_tokens": u.input_tokens,
            "output_tokens": u.output_tokens,
            "cost_units": round(u.cost_units, 6),
            "priced": bool(getattr(u, "priced", False)),
            "outcome": getattr(u.outcome, "value", str(u.outcome)),
            "error_category": getattr(u.error_category, "value", str(u.error_category)),
        }
        for u in telemetry
    ]
    artifact: dict[str, object] = {
        "$comment": (
            "Mission 1.84.2's repaired retention path. Written on every terminal outcome, so a "
            "rejected response is as recoverable as an accepted one."
        ),
        "OUTCOME": outcome,
        "PROVIDER_REQUESTS_MADE": len(transport_responses) + len(transport_errors),
        "RETRIES": 0,
        "timing": timing,
        "RAW_PROVIDER_RESPONSE_RETAINED": raw is not None,
        "RAW_PROVIDER_RESPONSE_SHA256": (
            _sha256(str(raw["body"])) if raw is not None else "NOT_AVAILABLE"
        ),
        "RAW_PROVIDER_RESPONSE_CHARACTERS": len(str(raw["body"])) if raw is not None else 0,
        "RAW_PROVIDER_RESPONSE_STATUS": raw["status"] if raw is not None else "NOT_AVAILABLE",
        "PROVIDER_REQUEST_ID": (
            next(iter(raw["headers"].values()), "NOT_EXPOSED")
            if raw is not None
            else "NOT_AVAILABLE"
        ),
        "transport_errors": list(transport_errors),
        "USAGE_RETAINED": bool(usage),
        "usage": usage if usage else "NOT_ESTABLISHED",
        "HIDDEN_REASONING_REQUESTED": False,
        "HIDDEN_REASONING_RETAINED": False,
    }
    if structured is not None:
        cleaned = strip_reasoning(structured)
        artifact["PARSED_OUTPUT_RETAINED"] = True
        artifact["PARSED_OUTPUT_SHA256"] = _sha256(json.dumps(cleaned, sort_keys=True))
        artifact["parsed_output"] = cleaned
    else:
        artifact["PARSED_OUTPUT_RETAINED"] = False
        artifact["PARSED_OUTPUT_SHA256"] = "NOT_AVAILABLE"
    if failure is not None:
        artifact["failure"] = {
            "type": type(failure).__name__,
            "message": redact(str(failure)),
        }
    if validation is not None:
        artifact["validation"] = validation
    artifact["PERSISTED"] = "NOTHING"
    return artifact


# --------------------------------------------------------------------- the single call


def execute(context: dict, *, transport=None, gateway=None) -> dict:
    """EXACTLY ONE provider request. No retry, no fallback, no second attempt.

    `transport` and `gateway` exist so the retention path can be exercised by synthetic
    fixtures. A fixture reaches no network by construction, and the default builds the real
    transport only when nothing was supplied.
    """
    from sros_llm_gateway.config import load_config_from_env
    from sros_llm_gateway.gateway import LlmGateway
    from sros_llm_gateway.pricing import load_pricing_from_env
    from sros_llm_gateway.prompts.rendering import RenderedPrompt, UntrustedText
    from sros_llm_gateway.providers.anthropic import AnthropicProvider
    from sros_llm_gateway.transport import UrllibTransport
    from sros_llm_gateway.types import LlmRequest, LlmTier
    from sros_opportunity import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
        SECOND_OPPORTUNITY_PROMPT_ID,
        SECOND_OPPORTUNITY_PROMPT_VERSION,
    )

    packet_file = context["packet_file"]
    parts = context["parts"]

    refuse_if_consumed(packet_file["EXECUTION_PACKET_SHA256"])

    recorder = RecordingTransport(transport if transport is not None else UrllibTransport())
    telemetry: list = []
    if gateway is None:
        gateway = LlmGateway(
            config=load_config_from_env(),
            pricing=load_pricing_from_env(),
            telemetry=telemetry.append,
        )
        gateway.register(
            AnthropicProvider(
                max_output_tokens=packet_file["MAX_OUTPUT_TOKENS"], transport=recorder
            )
        )

    prompt = RenderedPrompt(
        system_instructions=parts.system_instructions,
        trusted_context=parts.trusted_context,
        untrusted=tuple(UntrustedText(content=c, label=label) for c, label in parts.untrusted),
        task=parts.task,
        metadata=parts.metadata,
    )
    request = LlmRequest(
        tier=LlmTier.STRONG_MODEL,
        task=SECOND_OPPORTUNITY_PROMPT_ID,
        prompt_template_id=SECOND_OPPORTUNITY_PROMPT_ID,
        prompt_template_version=SECOND_OPPORTUNITY_PROMPT_VERSION,
        response_schema=SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
        prompt=prompt,
        workspace_id=os.environ.get("DEV_WORKSPACE_ID", "00000000-0000-4000-8000-000000000001"),
        correlation_id=CORRELATION_ID,
        timeout_seconds=float(packet_file["REQUEST_TIMEOUT"]),
        max_retries=int(packet_file["GENERATION_PARAMETERS"]["max_retries"]),
        requires_structured_output=True,
    )

    started = dt.datetime.now(dt.UTC)
    # ONE call. The except captures what arrived and re-raises nothing to a retry: there is no
    # second `gateway.complete` anywhere in this function, and the approval authorises one.
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


def terminal_outcome(result: dict) -> str:
    """Name the terminal state from what actually happened."""
    failure = result["failure"]
    if failure is None:
        return "RESPONSE_RECEIVED_AWAITING_VALIDATION"
    name = type(failure).__name__
    if result["transport_errors"] and not result["transport_responses"]:
        return "EXECUTION_FAILED_TRANSPORT_NO_RETRY"
    if "Timeout" in name:
        return "EXECUTION_FAILED_TIMEOUT_NO_RETRY"
    if "Schema" in name:
        return "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY"
    return "EXECUTION_FAILED_NO_RETRY"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform the one approved provider request. Verification runs first regardless.",
    )
    parser.add_argument("--use-profile", default=USE_PROFILE)
    args = parser.parse_args(argv)

    print("=== pre-execution verification (the operator's eight checks)")
    try:
        context = verify(args.use_profile)
    except RefusedError as refusal:
        print(f"\nREFUSED  nothing was sent: {refusal}")
        return 1
    for key, value in context["findings"].items():
        shown = value if not isinstance(value, dict) else json.dumps(value, sort_keys=True)
        print(f"    {key:38s} {shown}")

    spent = consumed_approvals()
    print(f"    CONSUMED_APPROVALS                     {len(spent)}")

    if not args.execute:
        print("\nverified. Nothing sent. Pass --execute to perform the one approved request.")
        return 0

    try:
        refuse_if_consumed(context["packet_file"]["EXECUTION_PACKET_SHA256"])
    except RefusedError as refusal:
        print(f"\nREFUSED  {refusal}")
        return 1

    print("\n=== ONE provider request")
    result = execute(context)
    outcome = terminal_outcome(result)
    response = result["response"]
    artifact = build_execution_artifact(
        outcome=outcome,
        transport_responses=result["transport_responses"],
        transport_errors=result["transport_errors"],
        telemetry=result["telemetry"],
        structured=(response.structured if response is not None else None),
        failure=result["failure"],
        timing=result["timing"],
    )
    RESPONSE_ARTIFACT.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"    outcome        {outcome}")
    print(f"    raw retained   {artifact['RAW_PROVIDER_RESPONSE_RETAINED']}")
    print(f"    usage retained {artifact['USAGE_RETAINED']}")
    print(f"    wrote          {RESPONSE_ARTIFACT.name}")
    print("\n    NOTHING PERSISTED. HUMAN_OUTPUT_REVIEW_REQUIRED = true.")
    return 0 if result["failure"] is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
