"""Mission 1.36.1 §15. Diagnostic aggregation over the Docker Evidence, UNCALIBRATED.

**This is not an Opportunity Score and nothing here is persisted.** It runs the
real `aggregate()` with `allow_uncalibrated=True`, which the framework requires a
caller to say out loud, and writes one JSON artifact under `docs/data/`.

Two facts shape the output and neither is a limitation of this script.

**Eight Docker Evidence rows sit on EIGHT distinct Claims**, one row each, so
this is eight single-record aggregations rather than one eight-record
aggregation. Reliability resolving does not turn six observations of one article
into an aggregation, and a report that summed them would be inventing a claim
nobody made.

**The two Stack Exchange Claims are reported separately**, as §15 requires: they
have no applicable assessment, so their record is `NON_SCORABLE` and the
aggregation returns no score at all. That is the designed behaviour.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/report_docker_diagnostic_aggregation.py

Connects to a deployment, so `DATABASE_URL` must be set -- it lives in
`infrastructure/compose/.env` rather than in the shell -- and it runs through
`uv` because a bare `python` resolves `sros_contracts` from the path insert below
and cannot import `psycopg`.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "opportunity-engine" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "evidence-aggregation" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "evidence-reliability" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

DOCS = ROOT / "docs" / "data"
RESOLUTION = DOCS / "docker-reliability-resolution-v1.json"
OUT = DOCS / "docker-diagnostic-aggregation-v1.json"

BANNER = ("UNCALIBRATED", "DIAGNOSTIC ONLY", "NOT AN OPPORTUNITY SCORE")

EVIDENCE = """
    SELECT e.id, e.claim_id, e.direction, e.relevance, e.directness,
           e.extraction_confidence, e.observation_category, e.independence_state,
           e.independence_group_id, e.source_id, e.observed_at,
           c.temporality, c.claim_feature
      FROM scoring.evidence e
      JOIN research.claims c ON c.id = e.claim_id
     WHERE e.id = ANY(%s::uuid[])
     ORDER BY e.id
"""


def main() -> int:
    import psycopg
    from sros_contracts import (
        ClaimTemporality,
        EvidenceDirection,
        EvidenceIndependenceState,
        EvidenceObservationCategory,
    )
    from sros_evidence_aggregation import (
        REFERENCE_PROFILE_V1,
        EvidenceItem,
        aggregate,
    )

    resolution = json.loads(RESOLUTION.read_text(encoding="utf-8"))
    rows_by_id = {r["evidence_id"]: r for r in resolution["rows"]}

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(EVIDENCE, (list(rows_by_id),))
        columns = [d[0] for d in cur.description]
        evidence = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]

    results = []
    for row in evidence:
        resolved = rows_by_id[str(row["id"])]
        item = EvidenceItem(
            evidence_id=str(row["id"]),
            direction=EvidenceDirection(row["direction"]),
            relevance=row["relevance"],
            directness=row["directness"],
            # THE POINT OF THE WHOLE MISSION: the reliability comes from the
            # resolver's binding, never from the Evidence row, whose column is
            # still NULL. ADR-026 Decision 2.
            reliability=resolved["reliability"],
            extraction_confidence=row["extraction_confidence"],
            observation_category=EvidenceObservationCategory(row["observation_category"]),
            independence_state=EvidenceIndependenceState(row["independence_state"]),
            independence_group_id=(
                str(row["independence_group_id"]) if row["independence_group_id"] else None
            ),
            observed_at=row["observed_at"],
            source_id=row["source_id"],
        )
        result = aggregate(
            str(row["claim_id"]),
            [item],
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality(row["temporality"]),
            claim_feature=row["claim_feature"],
            allow_uncalibrated=True,
        )
        contribution = result.contributions[0]
        results.append(
            {
                "$banner": list(BANNER),
                "claim_id": str(row["claim_id"]),
                "evidence_id": str(row["id"]),
                "source_id": row["source_id"],
                "proposition_kind": resolved["scope"]["proposition_kind"],
                "reliability_resolution": {
                    "outcome": resolved["outcome"],
                    "reliability": resolved["reliability"],
                    "assessment_id": resolved["assessment_id"],
                    "assessment_version": resolved["assessment_version"],
                    "assessment_origin": resolved["assessment_origin"],
                    "reviewed_by": resolved["reviewed_by"],
                },
                "evidence_considered": result.raw_evidence_count,
                "scorable_evidence": result.scorable_evidence_count,
                "unavailable_evidence": result.non_scorable_evidence_count,
                "aggregation_status": result.status.value,
                "missing_requirements": list(result.missing_requirements),
                "support_strength": result.masses.support_strength,
                "contradiction_strength": result.masses.contradiction_strength,
                "supported_mass": result.masses.supported_mass,
                "contradicted_mass": result.masses.contradicted_mass,
                "conflict_mass": result.masses.conflict_mass,
                "uncertainty_mass": result.masses.uncertainty_mass,
                "evidence_level": result.level.to_json(),
                "q": contribution.q,
                "limiting_component": contribution.limiting_component,
                "components": contribution.components,
                # `NonScorableReason` is a str subclass, not an enum: the set is open by
                # design, because each missing component names itself.
                "non_scorable_reasons": [str(r) for r in contribution.non_scorable_reasons],
                "independence_state": row["independence_state"],
                "unknown_independence_count": result.unknown_independence_count,
                "independence_group_count": result.independence_group_count,
                "source_count": result.source_count,
                "profile_id": result.aggregation_profile_id,
                "profile_version": result.aggregation_profile_version,
                "profile_status": result.aggregation_profile_status,
                "calibrated": result.calibrated,
                "algorithm_version": result.algorithm_version,
            }
        )

    resolved_results = [r for r in results if r["scorable_evidence"] == 1]
    unavailable = [r for r in results if r["scorable_evidence"] == 0]

    document = {
        "$comment": (
            "Mission 1.36.1 §15. DIAGNOSTIC ONLY, over an UNCALIBRATED profile, and NOT an "
            "Opportunity Score. Nothing here is persisted: scoring.scores does not exist and "
            "this script writes one JSON artifact and no database row. Eight Docker Evidence "
            "rows sit on EIGHT distinct Claims, so these are eight SINGLE-RECORD "
            "aggregations -- reliability resolving does not turn six observations of one "
            "article into an aggregation. The reliability on every item came from the "
            "resolver's binding and never from scoring.evidence.reliability, which is still "
            "NULL on every row (ADR-026 Decision 2)."
        ),
        "$banner": list(BANNER),
        "artifact_version": "docker-diagnostic-aggregation@1.0.0",
        "generated_by": "mission-1.36.1",
        "profile": {
            "id": REFERENCE_PROFILE_V1.profile_id,
            "version": REFERENCE_PROFILE_V1.version,
            "status": REFERENCE_PROFILE_V1.status.value,
            "note": (
                "UNCALIBRATED. No parameter in this profile was fitted to labelled data, so "
                "every number below is a demonstration that the equations run and is not a "
                "measurement of anything. D-03 is not resolved."
            ),
        },
        "totals": {
            "claims_aggregated": len(results),
            "claims_with_scorable_evidence": len(resolved_results),
            "claims_with_unavailable_evidence": len(unavailable),
            "evidence_rows_per_claim": 1,
            "opportunity_scores_created": 0,
            "rows_persisted": 0,
        },
        "scorable": resolved_results,
        "unavailable": unavailable,
    }

    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(" | ".join(BANNER))
    print(
        f"profile: {REFERENCE_PROFILE_V1.profile_id}@{REFERENCE_PROFILE_V1.version} "
        f"{REFERENCE_PROFILE_V1.status.value}"
    )
    print(f"\n{len(results)} claims, one Evidence row each\n")
    print(f"  {'claim':10} {'source':20} {'status':22} {'q':>6} {'limiting':14} {'lvl':>3}")
    for r in results:
        q = "-" if r["q"] is None else f"{r['q']:.3f}"
        limiting = r["limiting_component"] or "-"
        level = r["evidence_level"]["evidence_level"]
        print(
            f"  {r['claim_id'][:8]:10} {r['source_id']:20} {r['aggregation_status']:22} "
            f"{q:>6} {limiting:14} {level:>3}"
        )
    print(
        f"\nscorable: {len(resolved_results)}   unavailable: {len(unavailable)}"
        f"   opportunity scores created: 0   rows persisted: 0"
    )
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
