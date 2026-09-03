"""Mission 1.37 §26. Can the CURRENT canonical corpus support empirical calibration?

**Read-only, and it measures rather than quoting an earlier report.** §26 says so
explicitly: counts from old reports are not evidence about the live database.

It walks every Claim in the deployment, resolves each Evidence row's reliability
through the real resolver, runs the real `aggregate()` under
`allow_uncalibrated=True`, and then reports the coverage dimensions §11 asks a
calibration dataset to span. It writes one JSON artifact and no database row.

The interesting output is the empty cells, not the full ones.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/audit_calibration_feasibility.py
    uv run --package sros-nlp python infrastructure/scripts/audit_calibration_feasibility.py --check

`--check` regenerates into memory and compares with the committed artifact,
exiting non-zero on any difference. §37: an artifact generated without a check
step drifts, and Mission 1.36.1 found one that had.

**It is an operator gate and NOT a CI step, and the distinction is real.** The
four `--check` steps CI already runs render repository files into other
repository files, so an empty database changes nothing about them. This artifact
MEASURES A DEPLOYMENT. CI's integration job applies migrations to an empty
database and seeds it, so the corpus this audit describes does not exist there --
a check step in that job would compare an empty measurement against a committed
full one and be permanently red, or be loosened until it verified nothing. Run it
locally before committing a change that could move the corpus.

The same constraint applies to `build_reliability_review_packet.py`, whose
missing check step Mission 1.36.1 recorded; it reads the database too, and that
backlog item needs this decision made before it can be closed.

Connects to a deployment, so `DATABASE_URL` must be set -- it lives in
`infrastructure/compose/.env` rather than in the shell -- and it runs through
`uv` because a bare `python` resolves `sros_contracts` from the path insert below
and cannot import `psycopg`.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "opportunity-engine" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "evidence-aggregation" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "evidence-reliability" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

DOCS = ROOT / "docs" / "data"
OUT = DOCS / "calibration-feasibility-audit-v1.json"

EVIDENCE = """
    SELECT e.id, e.claim_id, e.direction, e.relevance, e.directness,
           e.extraction_confidence, e.observation_category, e.independence_state,
           e.independence_group_id, e.source_id, e.observed_at,
           e.reliability AS supplied,
           c.claim_type, c.temporality, c.claim_feature, c.proposition_facts,
           s.signal_type_id, s.scope AS signal_scope,
           (SELECT DISTINCT si.record_kind_id FROM nlp.signal_inputs si
             WHERE si.signal_id = s.id LIMIT 1) AS record_kind_id,
           (SELECT DISTINCT r.provenance ->> 'resource_id'
              FROM nlp.signal_inputs si
              JOIN acquisition.normalized_records n ON n.id = si.normalized_record_id
              JOIN acquisition.raw_records r ON r.id = n.raw_record_id
             WHERE si.signal_id = s.id LIMIT 1) AS resource_id
      FROM scoring.evidence e
      JOIN research.claims c ON c.id = e.claim_id
      LEFT JOIN nlp.signals s ON s.id = e.signal_id
     ORDER BY e.claim_id, e.id
"""

ASSESSMENTS = """
    SELECT id, version, source_id, resource_id, record_kind_id, claim_type,
           proposition_kind, reliability, origin, reviewed_by, rationale,
           stated_limitation, calibration_dataset_ref
      FROM epistemic.reliability_assessments
     WHERE superseded_at IS NULL
"""

BASIS = """
    SELECT basis_type, document_title, summarized_finding, document_url,
           section_reference, retrieved_at
      FROM epistemic.reliability_assessment_basis
     WHERE assessment_id = %s
"""

# Tables that would hold an accountable reference target if one existed. Listed
# by name so the audit reports "absent" rather than silently finding nothing.
REFERENCE_TABLE_CANDIDATES = (
    ("calibration", "reference_labels"),
    ("calibration", "datasets"),
    ("scoring", "scores"),
    ("scoring", "calibration_reference"),
    ("research", "claim_outcomes"),
    ("research", "claim_resolutions"),
)


def build(conn) -> dict:
    from sros_contracts import (
        ClaimTemporality,
        ClaimType,
        EvidenceDirection,
        EvidenceIndependenceState,
        EvidenceObservationCategory,
        ReliabilityAssessmentOrigin,
        ReliabilityBasisType,
    )
    from sros_evidence_aggregation import (
        REFERENCE_PROFILE_V1,
        EvidenceItem,
        aggregate,
    )
    from sros_evidence_reliability import (
        ReliabilityAssessment,
        ReliabilityBasis,
        ReliabilityScope,
        resolve_reliability,
    )

    with conn.cursor() as cur:
        cur.execute(EVIDENCE)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]
        cur.execute(ASSESSMENTS)
        acols = [d[0] for d in cur.description]
        raw_assessments = [dict(zip(acols, r, strict=True)) for r in cur.fetchall()]
        for a in raw_assessments:
            cur.execute(BASIS, (a["id"],))
            a["_basis"] = cur.fetchall()

        present_reference_tables = []
        for schema, table in REFERENCE_TABLE_CANDIDATES:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = %s AND table_name = %s",
                (schema, table),
            )
            if cur.fetchone():
                present_reference_tables.append(f"{schema}.{table}")

    assessments = [
        ReliabilityAssessment(
            id=str(a["id"]),
            scope=ReliabilityScope(
                source_id=a["source_id"],
                resource_id=a["resource_id"],
                record_kind_id=a["record_kind_id"],
                claim_type=ClaimType(a["claim_type"]),
                proposition_kind=a["proposition_kind"],
            ),
            version=int(a["version"]),
            reliability=float(a["reliability"]),
            origin=ReliabilityAssessmentOrigin(a["origin"]),
            rationale=a["rationale"],
            stated_limitation=a["stated_limitation"],
            reviewed_by=a["reviewed_by"],
            reviewed_at=None,
            basis=tuple(
                ReliabilityBasis(
                    basis_type=ReliabilityBasisType(bt),
                    document_title=title,
                    summarized_finding=finding,
                    document_url=url,
                    section_reference=section,
                    retrieved_at=retrieved,
                )
                for bt, title, finding, url, section, retrieved in a["_basis"]
            ),
            calibration_dataset_ref=a["calibration_dataset_ref"],
        )
        for a in raw_assessments
    ]

    by_claim: dict[str, list[dict]] = {}
    for row in rows:
        by_claim.setdefault(str(row["claim_id"]), []).append(row)

    units = []
    for claim_id, claim_rows in sorted(by_claim.items()):
        first = claim_rows[0]
        items = []
        resolutions = []
        for row in claim_rows:
            facts = row["proposition_facts"] or {}
            resolution = resolve_reliability(
                scope=ReliabilityScope(
                    source_id=row["source_id"],
                    resource_id=row["resource_id"],
                    record_kind_id=row["record_kind_id"],
                    claim_type=ClaimType(row["claim_type"]),
                    proposition_kind=facts.get("proposition", ""),
                ),
                candidates=assessments,
                supplied=float(row["supplied"]) if row["supplied"] is not None else None,
            )
            resolutions.append(resolution)
            items.append(
                EvidenceItem(
                    evidence_id=str(row["id"]),
                    direction=EvidenceDirection(row["direction"]),
                    relevance=row["relevance"],
                    directness=row["directness"],
                    reliability=resolution.reliability,
                    extraction_confidence=row["extraction_confidence"],
                    observation_category=EvidenceObservationCategory(row["observation_category"]),
                    independence_state=EvidenceIndependenceState(row["independence_state"]),
                    independence_group_id=(
                        str(row["independence_group_id"]) if row["independence_group_id"] else None
                    ),
                    observed_at=row["observed_at"],
                    source_id=row["source_id"],
                )
            )

        result = aggregate(
            claim_id,
            items,
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality(first["temporality"]),
            claim_feature=first["claim_feature"],
            allow_uncalibrated=True,
        )
        directions = {r["direction"] for r in claim_rows}
        limiting = {
            c.limiting_component for c in result.contributions if c.limiting_component is not None
        }
        units.append(
            {
                "claim_id": claim_id,
                "evidence_count": len(claim_rows),
                "proposition_kind": (first["proposition_facts"] or {}).get("proposition", ""),
                "temporality": first["temporality"],
                "claim_feature": first["claim_feature"],
                "source_ids": sorted({r["source_id"] for r in claim_rows}),
                "signal_type_ids": sorted(
                    {r["signal_type_id"] for r in claim_rows if r["signal_type_id"]}
                ),
                "observation_categories": sorted({r["observation_category"] for r in claim_rows}),
                "independence_states": sorted({r["independence_state"] for r in claim_rows}),
                "directions": sorted(directions),
                "reliability_outcomes": sorted({r.outcome.value for r in resolutions}),
                "aggregation_status": result.status.value,
                "scorable_evidence": result.scorable_evidence_count,
                "non_scorable_evidence": result.non_scorable_evidence_count,
                "support_strength": result.masses.support_strength,
                "contradiction_strength": result.masses.contradiction_strength,
                "supported_mass": result.masses.supported_mass,
                "conflict_mass": result.masses.conflict_mass,
                "uncertainty_mass": result.masses.uncertainty_mass,
                "evidence_level": result.level.level,
                "limiting_components": sorted(limiting),
                "independent_support_groups": sum(
                    1 for g in result.groups.support if g.kind.value != "UNKNOWN"
                ),
            }
        )

    scorable = [u for u in units if u["scorable_evidence"] > 0]

    # -- §11's coverage dimensions, counted rather than asserted ------------
    coverage = {
        "support_only": sum(1 for u in scorable if u["directions"] == ["SUPPORTS"]),
        "contradiction_present": sum(1 for u in scorable if "CONTRADICTS" in u["directions"]),
        "mixed_support_and_contradiction": sum(
            1 for u in scorable if {"SUPPORTS", "CONTRADICTS"} <= set(u["directions"])
        ),
        "neutral_present": sum(1 for u in units if "NEUTRAL" in u["directions"]),
        "conflict_mass_non_zero": sum(1 for u in scorable if u["conflict_mass"] > 0.0),
        "single_source_claims": sum(1 for u in scorable if len(u["source_ids"]) == 1),
        "multi_source_claims": sum(1 for u in scorable if len(u["source_ids"]) > 1),
        "multi_evidence_claims": sum(1 for u in scorable if u["evidence_count"] > 1),
        "independence_established_claims": sum(
            1 for u in scorable if u["independent_support_groups"] > 0
        ),
        "independence_unknown_claims": sum(
            1 for u in scorable if u["independence_states"] == ["UNKNOWN"]
        ),
        "evergreen_claims": sum(1 for u in scorable if u["temporality"] == "EVERGREEN"),
        "temporally_sensitive_claims": sum(1 for u in scorable if u["temporality"] != "EVERGREEN"),
        "claims_with_a_claim_feature": sum(1 for u in scorable if u["claim_feature"]),
        "distinct_proposition_kinds": len({u["proposition_kind"] for u in scorable}),
        "distinct_source_ids": len({s for u in scorable for s in u["source_ids"]}),
        "distinct_observation_categories": len(
            {c for u in scorable for c in u["observation_categories"]}
        ),
        "categorised_market_or_validation": sum(
            1
            for u in scorable
            if {"MARKET_ACTIVITY", "DIRECT_VALIDATION"} & set(u["observation_categories"])
        ),
    }

    limiting_counter = Counter(c for u in scorable for c in u["limiting_components"])
    strength_counter = Counter(round(u["support_strength"], 6) for u in scorable)
    level_counter = Counter(u["evidence_level"] for u in units)
    status_counter = Counter(u["aggregation_status"] for u in units)

    return {
        "$comment": (
            "Mission 1.37 §26. Measured against the LIVE database, never quoted from an "
            "earlier report. Read-only: it writes one JSON artifact and no database row, "
            "and every aggregation runs under allow_uncalibrated=True. The empty cells "
            "are the finding -- a coverage dimension with zero cases cannot be fitted or "
            "validated, and a dimension with one distinct target value cannot be either."
        ),
        "artifact_version": "calibration-feasibility-audit@1.0.0",
        "generated_by": "mission-1.37",
        "profile": {
            "profile_id": REFERENCE_PROFILE_V1.profile_id,
            "version": REFERENCE_PROFILE_V1.version,
            "status": REFERENCE_PROFILE_V1.status.value,
            "algorithm_version": REFERENCE_PROFILE_V1.algorithm_version,
            "half_life_days": dict(REFERENCE_PROFILE_V1.half_life_days),
            "level_thresholds": REFERENCE_PROFILE_V1.level_thresholds.to_json(),
        },
        "totals": {
            "claims": len(units),
            "evidence_rows": len(rows),
            "claims_with_scorable_evidence": len(scorable),
            "claims_unavailable": sum(1 for u in units if u["aggregation_status"] == "UNAVAILABLE"),
            "current_reliability_assessments": len(assessments),
            "aggregation_status": dict(sorted(status_counter.items())),
            "evidence_level": {str(k): v for k, v in sorted(level_counter.items())},
        },
        "coverage": coverage,
        "limiting_component_counts": dict(sorted(limiting_counter.items())),
        "distinct_support_strengths": {str(k): v for k, v in sorted(strength_counter.items())},
        "reference_target_tables_present": present_reference_tables,
        "units": units,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and compare with the committed artifact; write nothing",
    )
    args = parser.parse_args()

    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        document = build(conn)

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"REFUSED: {OUT.name} does not exist; run without --check first")
            return 1
        if OUT.read_text(encoding="utf-8") == rendered:
            print(f"ok       {OUT.name} matches the live canonical state")
            return 0
        print(f"DRIFT    {OUT.name} does not match the live canonical state")
        print("         regenerate it, and read the diff before committing: a change here")
        print("         means the corpus moved, which is a fact about the deployment")
        return 1

    OUT.write_text(rendered, encoding="utf-8")

    totals = document["totals"]
    coverage = document["coverage"]
    print(f"claims                       : {totals['claims']}")
    print(f"  with scorable evidence     : {totals['claims_with_scorable_evidence']}")
    print(f"  UNAVAILABLE                : {totals['claims_unavailable']}")
    print(f"evidence rows                : {totals['evidence_rows']}")
    print(f"current reliability assessments: {totals['current_reliability_assessments']}")
    print("\ncoverage dimensions (§11):")
    for name, value in coverage.items():
        flag = "   <-- EMPTY" if value == 0 else ""
        print(f"  {name:36} {value}{flag}")
    print(f"\nlimiting components: {document['limiting_component_counts']}")
    print(f"distinct support strengths: {document['distinct_support_strengths']}")
    print(
        f"reference target tables present: {document['reference_target_tables_present'] or 'NONE'}"
    )
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
