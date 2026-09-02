"""The first bounded Opportunity synthesis, on the real `docker` packet.

Mission 1.31 §9, §10, §12, §20, §21. **This spends real credits in `--apply`.**

    python infrastructure/scripts/run_opportunity_synthesis.py            # plan
    python infrastructure/scripts/run_opportunity_synthesis.py --apply    # one call

**Authorization resolves before serialization, not before the socket.** The
egress gate runs first, and `serialize_packet_for_model` refuses on an
unauthorised decision before it assembles any string — so a refused packet leaves
no text for a later bug to send.

**One logical call.** A single same-route retry is permitted for a schema
failure, is counted, and is reported. There is no cross-provider fallback:
ADR-006 forbids it and a schema failure is not a reason to ask somebody else.

**The persistence gate is frozen in `validation.py` and was written before this
ran.** Nothing here may weaken it, and the script has no flag that could.

**The prompt regions stay apart all the way to the provider.** Claim statements
are `UntrustedText`; the rubric and the packet facts are trusted regions. Source
material is never an instruction.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pathlib
import sys
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "data"
CATALOG = DOCS / "source-catalog-v1.json"
SUBJECT_REGISTRY = DOCS / "canonical-subject-registry-v1.json"
PROVIDER_POLICY = DOCS / "model-provider-policy-v1.json"
ARTIFACT = DOCS / "opportunity-synthesis-run-v1.json"

WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"
USE_PROFILE = "local-private-research-v1"
SUBJECT = "docker"
CORRELATION_ID = "mission-1.31-synthesis"

#: §10. Output is capped so the hard maximum is a real bound rather than the
#: adapter's 4096-token default -- the lesson Mission 1.27 paid for when its
#: first hard maximum came out above the ceiling.
#:
#: **1500 was too small and cost this mission two calls.** The schema's own
#: maxLengths admit about 5,200 characters before JSON overhead, which is
#: roughly 1,800 tokens, so the first attempt and its one permitted retry both
#: came back missing the last five required fields. Bounding the output is right;
#: bounding it below what the requested schema can serialise is a defect, and the
#: arithmetic is now done against the schema rather than guessed.
MAX_OUTPUT_TOKENS = 3000
COST_CEILING = 0.25


def _load_env() -> None:
    env_file = ROOT / "infrastructure" / "compose" / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _rows():
    """The docker packet's Evidence, Claims and Signal scopes, from the database."""
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.id, e.claim_id, e.source_id, e.direction, e.observation_category,
                   e.independence_state, e.independence_group_id, e.evidence_level,
                   e.reliability, e.relevance, e.directness, e.extraction_confidence,
                   e.extraction_method, e.observed_at,
                   c.claim_type, c.lifecycle, c.temporality, c.origin,
                   s.signal_type_id, s.scope, r.statement
              FROM scoring.evidence e
              JOIN research.claims c ON c.id = e.claim_id
              JOIN research.claim_revisions r
                ON r.claim_id = c.id AND r.revision = c.current_revision
              LEFT JOIN nlp.signals s ON s.id = e.signal_id
             ORDER BY e.id
            """
        )
        columns = [d[0] for d in (cur.description or [])]
        return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def _families() -> dict[str, str]:
    sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
    from sros_acquisition.registry.catalog import load_catalog

    return {s.source_id: s.source_family for s in load_catalog(CATALOG).sources}


def _standings():
    sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
    from sros_acquisition.registry.catalog import load_catalog
    from sros_opportunity import SourcePolicyStanding

    catalog = load_catalog(CATALOG)
    out = {}
    for source in catalog.sources:
        review = source.review_for(USE_PROFILE)
        if review is None:
            continue
        approval = getattr(review.approval_state, "value", str(review.approval_state))
        assessed = review.assessment("external_model_transmission")
        transmission = getattr(assessed, "value", str(assessed))
        permits: bool | None = (
            None if transmission == "NOT_ASSESSED" else transmission.startswith("PERMITTED")
        )
        out[source.source_id] = SourcePolicyStanding(
            source_id=source.source_id,
            use_profile_id=USE_PROFILE,
            permits_local_processing=approval.startswith("APPROVED"),
            permits_external_model_transmission=permits,
            transmission_state=transmission,
            basis=f"{USE_PROFILE} review v{review.review_version}: {approval}",
        )
    return out


def _build_packet():
    """Rebuild the docker packet by the same deterministic path as preparation."""
    from sros_opportunity import (
        EvidenceFacets,
        IndependenceState,
        ReliabilityStatus,
        assess_eligibility,
        build_packet,
        group_by_subject,
        load_subject_registry,
        map_signal_type,
    )

    families = _families()
    standings = _standings()
    admissible = []
    statements: dict[str, str] = {}
    evidence_to_claim: dict[str, str] = {}

    for row in _rows():
        mapping = map_signal_type(row["signal_type_id"])
        facets = EvidenceFacets(
            evidence_id=str(row["id"]),
            claim_id=str(row["claim_id"]),
            source_id=str(row["source_id"] or ""),
            source_family=families.get(str(row["source_id"]), "UNREGISTERED"),
            use_profile_id=USE_PROFILE,
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
            reliability=row["reliability"],
            reliability_status=(
                ReliabilityStatus.RESOLVED
                if row["reliability"] is not None
                else ReliabilityStatus.NO_APPLICABLE_ASSESSMENT
            ),
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
        if not decision.may_enter_packet:
            continue
        admissible.append((facets, decision.eligibility, row["scope"]))
        statements[facets.claim_id] = str(row["statement"])
        evidence_to_claim[facets.evidence_id] = facets.claim_id

    registry = load_subject_registry(SUBJECT_REGISTRY)
    groups = group_by_subject([(f, s) for f, _, s in admissible], registry=registry)
    eligibility = {f.evidence_id: e for f, e, _ in admissible}

    for group in groups:
        if group.canonical_subject_id != SUBJECT:
            continue
        packet = build_packet(
            group.key,
            group.label,
            tuple((f, eligibility[f.evidence_id]) for f in group.facets),
        )
        wanted = set(packet.claim_ids)
        return (
            packet,
            {cid: text for cid, text in statements.items() if cid in wanted},
            {eid: cid for eid, cid in evidence_to_claim.items() if eid in set(packet.evidence_ids)},
            standings,
        )
    raise SystemExit(f"no packet for canonical subject {SUBJECT!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="make the one real call")
    args = parser.parse_args(argv)

    _load_env()
    if "DATABASE_URL" not in os.environ:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    from sros_opportunity import (
        MANDATORY_UNSUPPORTED_REPORT,
        SYNTHESIS_OUTPUT_SCHEMA,
        SYNTHESIS_PROCEDURE_VERSION,
        SYNTHESIS_PROMPT_ID,
        SYNTHESIS_PROMPT_VERSION,
        authorize_packet_for_external_synthesis,
        evaluate,
        evaluate_persistence,
        render_synthesis_prompt,
        serialize_packet_for_model,
        synthesis_prompt_hash,
    )

    packet, statements, evidence_to_claim, standings = _build_packet()
    sufficiency = evaluate(packet)

    print(f"packet          {packet.packet_id[:24]}  subject {packet.subject_label}")
    print(f"sufficiency     {sufficiency.status.value}")
    print(f"rows            {packet.size}  scoring-eligible {packet.scoring_eligible_count}")
    print(f"families        {', '.join(packet.source_families)}")
    print(f"dimensions      {sorted(d.value for d in packet.counting_dimensions)}")

    if sufficiency.status.value != "HYPOTHESIS_FORMABLE":
        print("\nthe packet is not formable; synthesis is not attempted", file=sys.stderr)
        return 1

    # ---------------------------------------------- §9 authorization FIRST
    gate = authorize_packet_for_external_synthesis(
        packet,
        {sid: standings[sid] for sid in packet.source_ids if sid in standings},
        provider_configured=bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
        provider_posture="APPROVED",
    )
    print(f"\negress          {gate.availability.value}  {list(gate.per_source)}")
    if not gate.authorized:
        print("OPPORTUNITY_SYNTHESIS_EGRESS_BLOCKED", file=sys.stderr)
        for reason in gate.refusal_reasons:
            print(f"  {reason}", file=sys.stderr)
        return 1

    # The Mission 1.29 allowlist, unchanged and unbroadened. Building it here
    # also proves the representation bound holds for what this mission sends.
    payload = serialize_packet_for_model(packet, gate, statements)

    parts = render_synthesis_prompt(packet, statements, evidence_to_claim)
    prompt_hash = synthesis_prompt_hash()

    # ------------------------------------------------------- §10 cost, first
    approx_input_chars = (
        len(parts.system_instructions)
        + len(parts.trusted_context)
        + len(parts.task)
        + sum(len(c) + len(label) for c, label in parts.untrusted)
    )
    approx_input_tokens = approx_input_chars // 4 + 200
    provider = os.environ.get("LLM_TIER_STRONG_PROVIDER", "")
    model = os.environ.get("LLM_TIER_STRONG_MODEL", "")

    from sros_llm_gateway.pricing import load_pricing_from_env

    pricing = load_pricing_from_env()
    price = pricing.price_for(provider, model)

    def _cost(inp: int, out: int) -> float | None:
        """The table's own arithmetic. A price rests on a configured rate, and a
        script that computed one itself could disagree with what the Gateway
        will actually record."""
        if price is None:
            return None
        return price.cost_for(inp, out)

    expected = _cost(approx_input_tokens, 900)
    # Hard maximum: the one call plus the one permitted schema retry, both at
    # the capped output ceiling.
    hard_max = _cost(approx_input_tokens * 2, MAX_OUTPUT_TOKENS * 2)

    print("\n--- §10 predeclared before any call")
    print(f"    provider              {provider}")
    print(f"    model                 {model}")
    print("    logical calls         1 (one same-route schema retry permitted)")
    print(f"    approx input tokens   {approx_input_tokens}")
    print(f"    max output tokens     {MAX_OUTPUT_TOKENS}")
    print(f"    expected cost         {expected if expected is None else f'{expected:.4f}'} USD")
    print(f"    hard maximum cost     {hard_max if hard_max is None else f'{hard_max:.4f}'} USD")
    print(f"    mission ceiling       {COST_CEILING:.2f} USD")
    print(f"    transmitted payload   {len(payload)} chars, keys {sorted(json.loads(payload))}")
    print(f"    prompt sha256         {prompt_hash[:32]}...")

    if hard_max is None:
        print("\nno pricing is configured for this model; refusing to call blind", file=sys.stderr)
        return 1
    if hard_max > COST_CEILING:
        print(
            f"\nSTOP: hard maximum {hard_max:.4f} exceeds the {COST_CEILING:.2f} ceiling",
            file=sys.stderr,
        )
        return 1

    if not args.apply:
        print("\n--plan: nothing sent. Re-run with --apply to make the one call.")
        return 0

    # --------------------------------------------------------- §20 one call
    from sros_llm_gateway.config import load_config_from_env
    from sros_llm_gateway.gateway import LlmGateway
    from sros_llm_gateway.prompts.rendering import RenderedPrompt, UntrustedText
    from sros_llm_gateway.providers.anthropic import AnthropicProvider
    from sros_llm_gateway.types import LlmRequest, LlmTier, SchemaValidationError

    gateway = LlmGateway(config=load_config_from_env(), pricing=pricing)
    gateway.register(AnthropicProvider(max_output_tokens=MAX_OUTPUT_TOKENS))

    prompt = RenderedPrompt(
        system_instructions=parts.system_instructions,
        trusted_context=parts.trusted_context,
        untrusted=tuple(UntrustedText(content=c, label=label) for c, label in parts.untrusted),
        task=parts.task,
        metadata=parts.metadata,
    )
    request = LlmRequest(
        tier=LlmTier.STRONG_MODEL,
        task=SYNTHESIS_PROMPT_ID,
        prompt_template_id=SYNTHESIS_PROMPT_ID,
        prompt_template_version=SYNTHESIS_PROMPT_VERSION,
        response_schema=SYNTHESIS_OUTPUT_SCHEMA,
        prompt=prompt,
        workspace_id=WORKSPACE_ID,
        correlation_id=CORRELATION_ID,
        timeout_seconds=120,
        requires_structured_output=True,
    )

    # Attempts spent on the under-sized 1500-token cap, before it was raised.
    # Recorded rather than forgotten: they cost real money and they are part of
    # what this mission spent.
    abandoned_attempts = int(os.environ.get("SROS_SYNTHESIS_ABANDONED_ATTEMPTS", "0"))
    retries = 0
    try:
        response = gateway.complete(request)
    except SchemaValidationError:
        retries = 1
        print("    schema failure; one same-route retry (counted)")
        response = gateway.complete(request)

    output = response.structured or {}
    print("\n--- model output")
    print(json.dumps(output, indent=2, ensure_ascii=False)[:2600])

    # ------------------------------------- §12 and §21, frozen and applied
    decision = evaluate_persistence(
        output, packet, statements, evidence_to_claim, MANDATORY_UNSUPPORTED_REPORT
    )
    print("\n--- deterministic audit and frozen persistence gate")
    if decision.audit is not None:
        for entry in decision.audit.fields:
            print(f"    {entry.field_name:34s} {entry.verdict.value}")
            for finding in entry.findings:
                print(f"        - {finding[:170]}")
    print(f"    PERSIST: {decision.persist}")
    for reason in decision.refusal_reasons:
        print(f"        REFUSED: {reason[:200]}")
    for note in decision.notes:
        print(f"        note: {note[:200]}")

    artifact = {
        "mission": "1.31",
        "packet_id": packet.packet_id,
        "subject": packet.subject_label,
        "procedure": SYNTHESIS_PROCEDURE_VERSION,
        "prompt_version": SYNTHESIS_PROMPT_VERSION,
        "prompt_sha256": prompt_hash,
        "provider": provider,
        "model": model,
        "logical_calls": 1,
        "schema_retries": retries,
        "abandoned_attempts_before_output_cap_fix": abandoned_attempts,
        "abandoned_attempts_note": (
            "Attempts spent against a 1500-token output cap that was smaller than the "
            "requested schema can serialise. Both failed schema validation with the last "
            "five required fields missing, so no answer was produced and none was "
            "rejected. The cap was raised to 3000 and nothing about the task, prompt, "
            "schema or evidence changed."
        ),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cost_units": round(response.usage.cost_units, 6),
        "hard_maximum_cost_units": round(hard_max, 6),
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "authorization_resolved_before_serialization": True,
        "egress": {
            "availability": gate.availability.value,
            "per_source": [list(p) for p in gate.per_source],
        },
        "transmitted_payload_keys": sorted(json.loads(payload)),
        "evidence_ids": list(packet.evidence_ids),
        "claim_ids": list(packet.claim_ids),
        "model_output": output,
        "persistence": {
            "gate_version": decision.gate_version,
            "persist": decision.persist,
            "refusal_reasons": list(decision.refusal_reasons),
            "notes": list(decision.notes),
            "audit_version": decision.audit.audit_version if decision.audit else None,
            "audit": [
                {
                    "field": entry.field_name,
                    "verdict": entry.verdict.value,
                    "findings": list(entry.findings),
                }
                for entry in (decision.audit.fields if decision.audit else ())
            ],
        },
        "ran_at": datetime.now(UTC).isoformat(),
    }
    ARTIFACT.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {ARTIFACT.relative_to(ROOT)}")
    print(
        f"tokens {response.usage.input_tokens} in / {response.usage.output_tokens} out, "
        f"cost {response.usage.cost_units:.4f} USD, retries {retries}"
    )
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        raise SystemExit(main())
    raise SystemExit(130)
