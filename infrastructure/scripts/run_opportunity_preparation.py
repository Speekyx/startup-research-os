"""Run the deterministic Opportunity Engine preparation path over real Evidence.

Mission 1.28 §16.

    python infrastructure/scripts/run_opportunity_preparation.py
    python infrastructure/scripts/run_opportunity_preparation.py --check

**No model is called and none can be.** This script imports no provider and no
Gateway. It evaluates the §9 external-synthesis gate for every packet and reports
the decision; reaching a model would be a separate mission with its own cost
declaration.

**The use profile is DECLARED, never inferred** (ADR-027). `SROS_USE_PROFILE`, or
`local-private-research-v1` by default, which is what this deployment runs under.
The Evidence rows themselves do not record a use profile -- most were collected
before ADR-027 existed -- so this is the runtime's declaration about itself and is
reported as such rather than presented as a stored fact.

`--check` re-runs the whole path and fails if the committed report has drifted,
for the same reason every other generated document here is checked: two
hand-maintained copies of one fact drift, and the drift is found by whoever
trusted the wrong one.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "data"
CATALOG = DOCS / "source-catalog-v1.json"
SUBJECT_REGISTRY = DOCS / "canonical-subject-registry-v1.json"
OUTPUT = DOCS / "opportunity-preparation-v1.json"

DEFAULT_USE_PROFILE = "local-private-research-v1"


def _load_env() -> None:
    env_file = ROOT / "infrastructure" / "compose" / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _standings(use_profile: str) -> dict[str, object]:
    """Resolve each source's standing from the registry, outside the engine.

    The opportunity package does not import `sros_acquisition`, so this is where
    the registry is read and where a governance fact becomes a value object. An
    engine able to do this itself could decide its own authorization.
    """
    sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
    from sros_acquisition.registry.catalog import load_catalog
    from sros_opportunity import SourcePolicyStanding

    catalog = load_catalog(CATALOG)
    out: dict[str, object] = {}
    for source in catalog.sources:
        review = source.review_for(use_profile)
        if review is None:
            continue
        approval = getattr(review.approval_state, "value", str(review.approval_state))
        # `assessment` defaults to NOT_ASSESSED rather than raising, which is
        # exactly the distinction the opportunity gate needs: nobody looked is a
        # state, and it is not the same as somebody looked and said no.
        assessed = review.assessment("external_model_transmission")
        transmission = getattr(assessed, "value", str(assessed))
        permits_transmission: bool | None
        if transmission == "NOT_ASSESSED":
            permits_transmission = None
        elif transmission.startswith("PERMITTED"):
            permits_transmission = True
        else:
            permits_transmission = False
        out[source.source_id] = SourcePolicyStanding(
            source_id=source.source_id,
            use_profile_id=use_profile,
            permits_local_processing=approval.startswith("APPROVED"),
            permits_external_model_transmission=permits_transmission,
            transmission_state=transmission,
            basis=(
                f"{use_profile} review v{review.review_version}: {approval}; "
                f"external_model_transmission={transmission}"
            ),
        )
    return out


def _rows(use_profile: str) -> list[dict[str, object]]:
    import psycopg

    query = """
        SELECT e.id, e.claim_id, e.source_id, e.direction, e.observation_category,
               e.independence_state, e.independence_group_id, e.evidence_level,
               e.reliability, e.relevance, e.directness, e.extraction_confidence,
               e.extraction_method, e.observed_at,
               c.claim_type, c.lifecycle, c.temporality, c.origin,
               s.signal_type_id, s.scope
          FROM scoring.evidence e
          JOIN research.claims c ON c.id = e.claim_id
          LEFT JOIN nlp.signals s ON s.id = e.signal_id
         ORDER BY e.id
    """
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(query)
        columns = [d[0] for d in (cur.description or [])]
        return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def _families(use_profile: str) -> dict[str, str]:
    sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
    from sros_acquisition.registry.catalog import load_catalog

    catalog = load_catalog(CATALOG)
    return {s.source_id: s.source_family for s in catalog.sources}


def build_report(use_profile: str) -> dict[str, object]:
    from sros_opportunity import (
        DIMENSION_MAP_VERSION,
        DIMENSION_TAXONOMY_VERSION,
        EGRESS_PROCEDURE_VERSION,
        ELIGIBILITY_PROCEDURE_VERSION,
        GROUPING_PROCEDURE_VERSION,
        PACKET_PROCEDURE_VERSION,
        SUFFICIENCY_PROCEDURE_VERSION,
        SUFFICIENCY_V1,
        EvidenceFacets,
        IndependenceState,
        PacketEligibility,
        ReliabilityStatus,
        assess_eligibility,
        authorize_packet_for_external_synthesis,
        build_packet,
        evaluate,
        group_by_subject,
        load_subject_registry,
        map_signal_type,
    )

    standings = _standings(use_profile)
    families = _families(use_profile)
    rows = _rows(use_profile)

    assessed: list[tuple[object, PacketEligibility, dict[str, object] | None]] = []
    per_row: list[dict[str, object]] = []

    for row in rows:
        mapping = map_signal_type(row["signal_type_id"])  # type: ignore[arg-type]
        dimensions = mapping.dimensions if mapping else frozenset()
        bound = mapping.bound if mapping else ""
        facets = EvidenceFacets(
            evidence_id=str(row["id"]),
            claim_id=str(row["claim_id"]),
            source_id=str(row["source_id"] or ""),
            source_family=families.get(str(row["source_id"]), "UNREGISTERED"),
            use_profile_id=use_profile,
            extraction_method=row["extraction_method"],  # type: ignore[arg-type]
            claim_type=str(row["claim_type"]),
            claim_lifecycle=str(row["lifecycle"]),
            claim_temporality=str(row["temporality"]),
            claim_origin=str(row["origin"]),
            direction=str(row["direction"]),
            observation_category=str(row["observation_category"]),
            evidence_level=int(row["evidence_level"]),  # type: ignore[arg-type]
            relevance=row["relevance"],  # type: ignore[arg-type]
            directness=row["directness"],  # type: ignore[arg-type]
            extraction_confidence=row["extraction_confidence"],  # type: ignore[arg-type]
            reliability=row["reliability"],  # type: ignore[arg-type]
            reliability_status=(
                ReliabilityStatus.RESOLVED
                if row["reliability"] is not None
                else ReliabilityStatus.NO_APPLICABLE_ASSESSMENT
            ),
            independence_state=IndependenceState(str(row["independence_state"])),
            independence_group_id=(
                str(row["independence_group_id"]) if row["independence_group_id"] else None
            ),
            observed_at=(row["observed_at"].isoformat() if row["observed_at"] else None),  # type: ignore[union-attr]
            signal_type_id=row["signal_type_id"],  # type: ignore[arg-type]
            dimensions=dimensions,
            dimension_bound=bound,
        )
        decision = assess_eligibility(facets, standings.get(facets.source_id))  # type: ignore[arg-type]
        assessed.append((facets, decision.eligibility, row["scope"]))  # type: ignore[arg-type]
        per_row.append(
            {
                "evidence_id": facets.evidence_id,
                "source_id": facets.source_id,
                "source_family": facets.source_family,
                "signal_type_id": facets.signal_type_id,
                "dimensions": sorted(d.value for d in facets.dimensions),
                "eligibility": decision.eligibility.value,
                "reasons": list(decision.reasons),
                "independence_state": facets.independence_state.value,
                "scorable": facets.is_scorable,
                "missing_factors": list(facets.missing_factors),
            }
        )

    admissible = [
        (facets, eligibility, scope)
        for facets, eligibility, scope in assessed
        if eligibility in (PacketEligibility.ELIGIBLE_CONTEXT, PacketEligibility.ELIGIBLE_SCORING)
    ]
    excluded = len(assessed) - len(admissible)

    # Mission 1.30 §4. The reviewed registry, so evidence from two source
    # families that a person mapped to one subject lands in one packet. An
    # unmapped identifier keeps its own source-native key exactly as before.
    registry = load_subject_registry(SUBJECT_REGISTRY)
    groups = group_by_subject(
        [(f, s) for f, _, s in admissible],  # type: ignore[arg-type,misc]
        registry=registry,
    )
    eligibility_by_id = {f.evidence_id: e for f, e, _ in admissible}

    packets: list[dict[str, object]] = []
    formable = 0
    for group in groups:
        packet = build_packet(
            group.key,
            group.label,
            tuple((f, eligibility_by_id[f.evidence_id]) for f in group.facets),
        )
        result = evaluate(packet)
        gate = authorize_packet_for_external_synthesis(
            packet,
            {sid: standings[sid] for sid in packet.source_ids if sid in standings},  # type: ignore[misc]
            provider_configured=bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
            provider_posture="APPROVED",
        )
        if result.status.value == "HYPOTHESIS_FORMABLE":
            formable += 1
        packets.append(
            {
                "packet_id": packet.packet_id,
                "subject": packet.subject_label,
                "size": packet.size,
                "canonical_subject_id": group.canonical_subject_id,
                "source_ids": list(packet.source_ids),
                "source_families": list(packet.source_families),
                "signal_type_ids": list(packet.signal_type_ids),
                "dimensions": sorted(d.value for d in packet.dimensions),
                "counting_dimensions": sorted(d.value for d in packet.counting_dimensions),
                "eligibility_counts": packet.eligibility_counts,
                "independence": packet.independence_summary(),
                "scoring_eligible": packet.scoring_eligible_count,
                "sufficiency": {
                    "status": result.status.value,
                    "reasons": list(result.reasons),
                    "eligible_rows": result.eligible_rows,
                    "distinct_counting_dimensions": result.distinct_counting_dimensions,
                    "distinct_dimensions_literal": result.distinct_dimensions_literal,
                    "scoring_ready": result.scoring_ready,
                },
                "external_synthesis": {
                    "availability": gate.availability.value,
                    "refusal_reasons": list(gate.refusal_reasons),
                    "per_source": [list(p) for p in gate.per_source],
                },
            }
        )

    dimension_totals: dict[str, int] = {}
    for entry in per_row:
        for name in entry["dimensions"]:  # type: ignore[union-attr]
            dimension_totals[name] = dimension_totals.get(name, 0) + 1

    eligibility_totals: dict[str, int] = {}
    for entry in per_row:
        key = str(entry["eligibility"])
        eligibility_totals[key] = eligibility_totals.get(key, 0) + 1

    family_totals: dict[str, int] = {}
    for entry in per_row:
        key = str(entry["source_family"])
        family_totals[key] = family_totals.get(key, 0) + 1

    return {
        "mission": "1.28",
        "use_profile_id": use_profile,
        "use_profile_note": (
            "DECLARED by the runtime, never inferred (ADR-027). The Evidence rows do "
            "not themselves record a use profile: most were collected before ADR-027 "
            "existed."
        ),
        "procedures": {
            "subject_registry": registry.registry_version,
            "dimension_taxonomy": DIMENSION_TAXONOMY_VERSION,
            "dimension_map": DIMENSION_MAP_VERSION,
            "eligibility": ELIGIBILITY_PROCEDURE_VERSION,
            "grouping": GROUPING_PROCEDURE_VERSION,
            "packet": PACKET_PROCEDURE_VERSION,
            "sufficiency": SUFFICIENCY_PROCEDURE_VERSION,
            "external_synthesis_gate": EGRESS_PROCEDURE_VERSION,
        },
        "sufficiency_rule": SUFFICIENCY_V1.statement,
        "totals": {
            "evidence_rows_inspected": len(assessed),
            "eligible_context": eligibility_totals.get("ELIGIBLE_CONTEXT", 0),
            "eligible_scoring": eligibility_totals.get("ELIGIBLE_SCORING", 0),
            "requires_review": eligibility_totals.get("REQUIRES_REVIEW", 0),
            "ineligible": eligibility_totals.get("INELIGIBLE", 0),
            "excluded_from_packets": excluded,
            "packets_built": len(packets),
            "packets_formable": formable,
            "packets_insufficient": len(packets) - formable,
            "opportunity_hypotheses_generated": 0,
            "model_calls": 0,
            "cost_units": 0.0,
        },
        "evidence_dimension_distribution": dict(sorted(dimension_totals.items())),
        "source_family_composition": dict(sorted(family_totals.items())),
        "rows": per_row,
        "packets": packets,
        "epistemic_note": (
            "No Opportunity, Signal, Claim, Evidence, ReliabilityAssessment or Score "
            "was created by this run. Every packet is a gathering of references; "
            "nothing here asserts that an opportunity exists."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the report drifted")
    parser.add_argument("--use-profile", default=None)
    args = parser.parse_args(argv)

    _load_env()
    use_profile = args.use_profile or os.environ.get("SROS_USE_PROFILE") or DEFAULT_USE_PROFILE

    if "DATABASE_URL" not in os.environ:
        print("DATABASE_URL is not set; this script reads real Evidence.", file=sys.stderr)
        return 2

    report = build_report(use_profile)
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False) + "\n"

    if args.check:
        if not OUTPUT.exists():
            print(f"FAIL  {OUTPUT.relative_to(ROOT)} does not exist", file=sys.stderr)
            return 1
        if OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"FAIL  {OUTPUT.relative_to(ROOT)} is out of date", file=sys.stderr)
            return 1
        print(f"ok  {OUTPUT.relative_to(ROOT)} is current")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    totals = report["totals"]
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    for key, value in totals.items():  # type: ignore[union-attr]
        print(f"  {key:34s} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
