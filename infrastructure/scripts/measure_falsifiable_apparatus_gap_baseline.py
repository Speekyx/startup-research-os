"""The structural gap, re-established from live code and live data (Mission 1.48 §0).

§0 forbids relying on mission reports. Mission 1.43 asserted that with ONE
support group the full aggregator is algebraically the B-2 pass-through
baseline, and Missions 1.42.1 and 1.44.1 observed it; this script RE-DERIVES it
by running the REAL `aggregate()` over the REAL corpus, with reliability
resolved late through the REAL resolver, and comparing the result against B-2
computed independently.

B-2 is the reliability pass-through baseline of Mission 1.37: the strongest
scorable supporting item's `q`, ignoring every other mechanism. If the full
aggregator and B-2 agree on every Claim, the aggregation layer is empirically
unidentifiable from the corpus, which is the whole reason Mission 1.48 exists.

Reads only. Writes `docs/data/falsifiable-evidence-apparatus-gap-baseline-v1.json`.

**NOT WIRED INTO CI**, like every artifact that measures a deployment: CI's
integration job starts from an empty database, so the step would be permanently
red or loosened until it verified nothing (Mission 1.37). `--check` is an
OPERATOR gate.

    uv run python infrastructure/scripts/measure_falsifiable_apparatus_gap_baseline.py
    uv run python infrastructure/scripts/measure_falsifiable_apparatus_gap_baseline.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "data" / "falsifiable-evidence-apparatus-gap-baseline-v1.json"

COUNTERS = """
    SELECT (SELECT count(*) FROM acquisition.raw_records)                    AS raw_records,
           (SELECT count(*) FROM acquisition.normalized_records)             AS normalized_records,
           (SELECT count(*) FROM nlp.signals)                                AS signals,
           (SELECT count(*) FROM research.claims)                            AS claims,
           (SELECT count(*) FROM research.claim_revisions)                   AS claim_revisions,
           (SELECT count(*) FROM scoring.evidence)                           AS evidence,
           (SELECT count(*) FROM epistemic.reliability_assessments)          AS reliability_assessments,
           (SELECT count(*) FROM epistemic.reliability_assessment_basis)     AS reliability_basis_rows,
           (SELECT count(DISTINCT independence_group_id) FROM scoring.evidence
             WHERE independence_group_id IS NOT NULL)                        AS independence_groups,
           (SELECT count(*) FROM research.opportunities)                     AS opportunities,
           (SELECT count(*) FROM research.opportunity_hypothesis_revisions)  AS opportunity_revisions,
           (SELECT count(*) FROM research.opportunity_hypothesis_evidence)   AS opportunity_evidence_links,
           (SELECT count(*) FROM nlp.embedding_provenance)                   AS embeddings,
           (SELECT count(*) FROM registry.sources)                           AS registered_sources,
           (SELECT count(*) FROM scoring.evidence WHERE reliability IS NOT NULL)
                                                                             AS evidence_with_stored_reliability
"""

ROWS = """
    SELECT e.id AS evidence_id, e.claim_id, e.signal_id, e.source_id, e.direction,
           e.relevance, e.directness, e.extraction_confidence, e.observation_category,
           e.independence_state, e.independence_group_id, e.reliability AS supplied,
           e.observed_at,
           c.claim_type, c.proposition_facts, c.temporality, c.claim_feature,
           (SELECT DISTINCT si.record_kind_id FROM nlp.signal_inputs si
             WHERE si.signal_id = e.signal_id LIMIT 1) AS record_kind_id,
           (SELECT DISTINCT r.provenance ->> 'resource_id'
              FROM nlp.signal_inputs si
              JOIN acquisition.normalized_records n ON n.id = si.normalized_record_id
              JOIN acquisition.raw_records r ON r.id = n.raw_record_id
             WHERE si.signal_id = e.signal_id LIMIT 1) AS resource_id
      FROM scoring.evidence e
      JOIN research.claims c ON c.id = e.claim_id
     ORDER BY e.claim_id, e.id
"""

ASSESSMENTS = """
    SELECT id, version, source_id, resource_id, record_kind_id, claim_type,
           proposition_kind, reliability, origin, reviewed_by, reviewed_at,
           stated_limitation, review_rubric_id, review_rubric_version
      FROM epistemic.reliability_assessments
     WHERE superseded_at IS NULL
     ORDER BY id
"""

# The model refuses an assessment with no documentary basis, so the basis rows
# are fetched rather than stubbed. Reviewer reasoning is permitted alongside
# retrieved documents and never instead of them.
BASIS = """
    SELECT assessment_id, basis_type, document_title, document_url,
           section_reference, summarized_finding, retrieved_at
      FROM epistemic.reliability_assessment_basis
     ORDER BY assessment_id, id
"""


def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("REFUSED: DATABASE_URL is not set. This reads a deployment, not the tree.")
        return 1

    import psycopg
    from sros_contracts import (
        ClaimTemporality,
        ClaimType,
        EvidenceDirection,
        ReliabilityAssessmentOrigin,
        ReliabilityBasisType,
    )
    from sros_evidence_aggregation import REFERENCE_PROFILE_V1, aggregate, evidence_item_from_row
    from sros_evidence_aggregation.items import evaluate_item
    from sros_evidence_reliability import (
        ReliabilityAssessment,
        ReliabilityBasis,
        ReliabilityScope,
        resolve_reliability,
    )

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(COUNTERS)
        counters = dict(zip([d.name for d in cur.description], cur.fetchone(), strict=True))

        cur.execute("SELECT to_regclass('scoring.scores')")
        counters["scores_table"] = cur.fetchone()[0] or "ABSENT"

        cur.execute(ROWS)
        columns = [d.name for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]

        cur.execute(ASSESSMENTS)
        acols = [d.name for d in cur.description]
        raw_assessments = [dict(zip(acols, r, strict=True)) for r in cur.fetchall()]

        cur.execute(BASIS)
        bcols = [d.name for d in cur.description]
        basis_rows: dict[str, list[dict]] = {}
        for record in cur.fetchall():
            row = dict(zip(bcols, record, strict=True))
            basis_rows.setdefault(str(row["assessment_id"]), []).append(row)

    live = [
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
            rationale="(not reproduced here)",
            stated_limitation=a["stated_limitation"],
            reviewed_by=a["reviewed_by"],
            reviewed_at=a["reviewed_at"],
            basis=tuple(
                ReliabilityBasis(
                    basis_type=ReliabilityBasisType(b["basis_type"]),
                    document_title=b["document_title"],
                    summarized_finding=b["summarized_finding"],
                    document_url=b["document_url"],
                    section_reference=b["section_reference"],
                    retrieved_at=b["retrieved_at"],
                )
                for b in basis_rows.get(str(a["id"]), ())
            ),
            calibration_dataset_ref=None,
            review_rubric_id=a["review_rubric_id"],
            review_rubric_version=a["review_rubric_version"],
        )
        for a in raw_assessments
    ]

    # Reliability binds LATE (ADR-026 Decision 2): the column is NULL on every
    # row and the value is resolved at read time against the five-part scope.
    by_claim: dict[str, list[dict]] = {}
    for row in rows:
        facts = row["proposition_facts"] or {}
        scope = ReliabilityScope(
            source_id=row["source_id"],
            resource_id=row["resource_id"],
            record_kind_id=row["record_kind_id"],
            claim_type=ClaimType(row["claim_type"]),
            proposition_kind=facts.get("proposition", ""),
        )
        resolution = resolve_reliability(scope=scope, candidates=live, supplied=row["supplied"])
        row["reliability"] = resolution.reliability
        by_claim.setdefault(str(row["claim_id"]), []).append(row)

    # ------------------------------------------------- §0 A: aggregator vs B-2
    #
    # A FIXED reference moment, passed to both the aggregator and the
    # independent B-2 computation. Every Claim in this corpus is EVERGREEN so
    # freshness is 1.0 either way, but a wall clock would make the artifact
    # differ on every run and `--check` would report drift that is only the
    # passage of time.
    moment = datetime(2026, 9, 4, tzinfo=UTC)

    comparisons = []
    for claim_id, claim_rows in sorted(by_claim.items()):
        items = [evidence_item_from_row(r) for r in claim_rows]
        temporality = ClaimTemporality(claim_rows[0]["temporality"] or "EVERGREEN")
        claim_feature = claim_rows[0]["claim_feature"]
        result = aggregate(
            claim_id,
            items,
            REFERENCE_PROFILE_V1,
            temporality=temporality,
            claim_feature=claim_feature,
            now=moment,
            allow_uncalibrated=True,
        )

        # B-2, computed INDEPENDENTLY of the aggregator: the strongest scorable
        # supporting item's q, ignoring grouping, saturation and contradiction.
        half_life = REFERENCE_PROFILE_V1.half_life_for(claim_feature)
        supporting_q = [
            c.q
            for c in (
                evaluate_item(i, temporality=temporality, now=moment, half_life_days=half_life)
                for i in items
            )
            if c.scorable and c.direction is EvidenceDirection.SUPPORTS and c.q is not None
        ]
        b2 = max(supporting_q) if supporting_q else None
        full = result.masses.support_strength

        differs = b2 is not None and abs(float(full) - float(b2)) > 1e-12
        comparisons.append(
            {
                "claim_id": claim_id,
                "evidence_count": len(items),
                "scorable_supporting": len(supporting_q),
                "support_groups": result.support_group_count,
                "contradiction_groups": result.contradiction_group_count,
                "full_aggregator_support_strength": round(float(full), 12),
                "contradiction_strength": round(float(result.masses.contradiction_strength), 12),
                "conflict_mass": round(float(result.masses.conflict_mass), 12),
                "b2_pass_through": None if b2 is None else round(float(b2), 12),
                "differs_from_b2": differs,
                "status": result.status.value,
            }
        )

    differing = [c for c in comparisons if c["differs_from_b2"]]
    scorable = [c for c in comparisons if c["b2_pass_through"] is not None]
    multi = [c for c in scorable if c["evidence_count"] > 1]

    document = {
        "$comment": (
            "Mission 1.48 section 0. The structural gap re-derived from live code and "
            "live data rather than quoted from a mission report: the REAL aggregator "
            "run over the REAL corpus with reliability resolved through the REAL "
            "resolver, against a B-2 pass-through computed independently. Generated by "
            "infrastructure/scripts/measure_falsifiable_apparatus_gap_baseline.py. "
            "Deliberately not verified in CI, which starts from an empty database."
        ),
        "generated_by": "mission-1.48",
        "reference_moment": moment.isoformat(),
        "profile": REFERENCE_PROFILE_V1.profile_id,
        "profile_calibration_status": REFERENCE_PROFILE_V1.status.value,
        "counters": counters,
        "aggregation_shape": {
            "claims_with_evidence": len(comparisons),
            "scorable_claims": len(scorable),
            "scorable_multi_evidence_claims": len(multi),
            "max_evidence_per_claim": max((c["evidence_count"] for c in comparisons), default=0),
            "max_support_groups_on_one_claim": max(
                (c["support_groups"] for c in comparisons), default=0
            ),
            "claims_with_more_than_one_support_group": sum(
                1 for c in comparisons if c["support_groups"] > 1
            ),
            "claims_with_any_contradiction_group": sum(
                1 for c in comparisons if c["contradiction_groups"] > 0
            ),
            "aggregator_differs_from_b2_cases": len(differing),
        },
        "comparisons": comparisons,
        "structural_finding": (
            "Every scorable Claim resolves to exactly one support group, so saturation "
            "over one group is that group's strength, group strength is max() over its "
            "members, and B-2 reports the same maximum. The two are therefore equal by "
            "ALGEBRA rather than by coincidence, and no quantity of additional "
            "single-group Evidence can separate them. Only a second ESTABLISHED "
            "INDEPENDENT support group, or a real CONTRADICTION, can."
        ),
    }

    text = json.dumps(document, indent=2, ensure_ascii=False, default=str) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"REFUSED: {OUT.name} does not exist; run without --check first")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {OUT.name} does not match the live deployment")
            return 1
        print(f"ok       {OUT.name} matches the live canonical state")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    shape = document["aggregation_shape"]
    for key, value in shape.items():
        print(f"  {key:44} {value}")
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
