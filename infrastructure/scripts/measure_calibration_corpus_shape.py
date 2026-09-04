"""The calibration shape of the live corpus (Mission 1.43 §0, §27).

Measures what the corpus IS, per Claim, across every dimension that decides
whether calibration is possible: which aggregation mechanism each Claim
exercises, whether anything contradicts, whether any provenance is established,
and whether the full aggregator has any reason to differ from the Mission 1.37
B-2 reliability pass-through baseline.

**Measured, never inferred.** It runs the real resolver and the real aggregator
over the real rows; nothing here reads a previous report.

    uv run python infrastructure/scripts/measure_calibration_corpus_shape.py
    uv run python infrastructure/scripts/measure_calibration_corpus_shape.py --out <path>
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "evidence-reliability", "evidence-aggregation", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))

DOCS = ROOT / "docs" / "data"
DEFAULT_OUT = DOCS / "calibration-corpus-baseline-v1.json"

BANNER = ("UNCALIBRATED", "DIAGNOSTIC ONLY", "NOT AN OPPORTUNITY SCORE", "NOT A PROBABILITY")

ROWS = """
    SELECT e.id AS evidence_id, e.claim_id, e.signal_id, e.source_id, e.direction,
           e.relevance, e.directness, e.extraction_confidence, e.observation_category,
           e.independence_state, e.independence_group_id, e.reliability AS supplied,
           e.observed_at,
           c.claim_type, c.proposition_facts, c.current_revision, c.temporality,
           c.claim_feature,
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
"""

FAMILIES = {
    "ted-eu": "public_procurement",
    "wikimedia-pageviews": "encyclopedia_readership",
    "world-bank": "official_statistics",
    "gdelt": "news_corpus",
    "stack-exchange": "community_qa",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
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
        EvidenceIndependenceState,
        EvidenceObservationCategory,
        ReliabilityAssessmentOrigin,
        ReliabilityBasisType,
    )
    from sros_evidence_aggregation import REFERENCE_PROFILE_V1, EvidenceItem, aggregate
    from sros_evidence_reliability import (
        ReliabilityAssessment,
        ReliabilityBasis,
        ReliabilityScope,
        resolve_reliability,
    )

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(ROWS)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]
        cur.execute(ASSESSMENTS)
        acols = [d[0] for d in cur.description]
        raw = [dict(zip(acols, r, strict=True)) for r in cur.fetchall()]
        for entry in raw:
            cur.execute(
                "SELECT basis_type, document_title, summarized_finding, document_url,"
                " section_reference, retrieved_at"
                " FROM epistemic.reliability_assessment_basis WHERE assessment_id = %s",
                (entry["id"],),
            )
            bcols = [d[0] for d in cur.description]
            entry["_basis"] = [dict(zip(bcols, b, strict=True)) for b in cur.fetchall()]

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
                for b in a["_basis"]
            ),
            calibration_dataset_ref=None,
            review_rubric_id=a["review_rubric_id"],
            review_rubric_version=a["review_rubric_version"],
        )
        for a in raw
    ]

    by_claim: dict[str, list[dict]] = {}
    for row in rows:
        by_claim.setdefault(str(row["claim_id"]), []).append(row)

    units = []
    for claim_id, members in sorted(by_claim.items()):
        facts = members[0]["proposition_facts"] or {}
        kind = facts.get("proposition", "")

        resolved: dict[str, float | None] = {}
        scopes = set()
        for member in members:
            scope = ReliabilityScope(
                source_id=member["source_id"],
                resource_id=member["resource_id"],
                record_kind_id=member["record_kind_id"],
                claim_type=ClaimType(member["claim_type"]),
                proposition_kind=kind,
            )
            scopes.add(scope.key)
            resolution = resolve_reliability(
                scope=scope, candidates=live, supplied=member["supplied"]
            )
            resolved[str(member["evidence_id"])] = resolution.reliability

        items = [
            EvidenceItem(
                evidence_id=str(m["evidence_id"]),
                direction=EvidenceDirection(m["direction"]),
                relevance=m["relevance"],
                directness=m["directness"],
                reliability=resolved[str(m["evidence_id"])],
                extraction_confidence=m["extraction_confidence"],
                observation_category=EvidenceObservationCategory(m["observation_category"]),
                independence_state=EvidenceIndependenceState(m["independence_state"]),
                independence_group_id=(
                    str(m["independence_group_id"]) if m["independence_group_id"] else None
                ),
                observed_at=m["observed_at"],
                source_id=m["source_id"],
            )
            for m in members
        ]
        result = aggregate(
            claim_id,
            items,
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality(members[0]["temporality"]),
            allow_uncalibrated=True,
        )

        qs = [c.q for c in result.contributions if c.q is not None]
        pass_through = max(qs) if qs else None
        differs = (
            pass_through is not None and abs(result.masses.support_strength - pass_through) > 1e-9
        )

        units.append(
            {
                "claim_id": claim_id,
                "source_id": members[0]["source_id"],
                "source_family": FAMILIES.get(members[0]["source_id"], "UNREGISTERED"),
                "proposition_kind": kind,
                "claim_type": members[0]["claim_type"],
                "temporality": members[0]["temporality"],
                "claim_feature": members[0]["claim_feature"],
                "evidence_count": len(members),
                "support_count": sum(1 for m in members if m["direction"] == "SUPPORTS"),
                "contradiction_count": sum(1 for m in members if m["direction"] == "CONTRADICTS"),
                "reliability_scopes": sorted(scopes),
                "distinct_reliability_values": sorted(
                    {v for v in resolved.values() if v is not None}
                ),
                "independence_states": sorted({m["independence_state"] for m in members}),
                "observation_categories": sorted({m["observation_category"] for m in members}),
                "runtime_support_groups": result.support_group_count,
                "runtime_contradiction_groups": result.contradiction_group_count,
                "max_group_members": max(
                    (len(g.member_evidence_ids) for g in result.groups.support), default=0
                ),
                "established_independence_groups": sum(
                    1 for g in result.groups.support if g.kind.value == "INDEPENDENT"
                ),
                "aggregation_status": result.status.value,
                "scorable_evidence_count": result.scorable_evidence_count,
                "support_strength": result.masses.support_strength,
                "limiting_components": sorted(
                    {c.limiting_component for c in result.contributions if c.limiting_component}
                ),
                "evidence_level": result.level.level,
                "reliability_pass_through": pass_through,
                "aggregator_differs_from_pass_through": differs,
            }
        )

    scorable = [u for u in units if u["aggregation_status"] == "COMPLETE"]

    def tally(field: str) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for unit in units:
            value = unit[field]
            if isinstance(value, list):
                for item in value:
                    counter[str(item)] += 1
            else:
                counter[str(value)] += 1
        return dict(sorted(counter.items()))

    document = {
        "$comment": (
            "Mission 1.43 §0. The calibration shape of the live corpus, measured through "
            "the REAL resolver and the REAL aggregator. UNCALIBRATED, DIAGNOSTIC ONLY, "
            "NOT AN OPPORTUNITY SCORE. Nothing is persisted and no parameter is fitted."
        ),
        "$banner": list(BANNER),
        "artifact_version": "calibration-corpus-baseline@1.0.0",
        "generated_by": "mission-1.43",
        "totals": {
            "claims": len(units),
            "evidence_rows": len(rows),
            "scorable_claims": len(scorable),
            "multi_evidence_claims": sum(1 for u in units if u["evidence_count"] > 1),
            "scorable_multi_evidence_claims": sum(1 for u in scorable if u["evidence_count"] > 1),
            "max_evidence_per_claim": max((u["evidence_count"] for u in units), default=0),
            "current_reliability_assessments": len(live),
        },
        "mechanisms_exercised": {
            "$note": (
                "Which aggregation mechanism any real Claim has actually put to work. "
                "A mechanism no Claim exercises cannot be calibrated, however many rows "
                "the corpus holds."
            ),
            "claims_with_more_than_one_scorable_item": sum(
                1 for u in units if u["scorable_evidence_count"] > 1
            ),
            "claims_with_more_than_one_support_group": sum(
                1 for u in units if u["runtime_support_groups"] > 1
            ),
            "claims_with_established_independence": sum(
                1 for u in units if u["established_independence_groups"] > 0
            ),
            "claims_with_contradiction": sum(1 for u in units if u["contradiction_count"] > 0),
            "claims_temporally_sensitive": sum(1 for u in units if u["temporality"] != "EVERGREEN"),
            "claims_with_claim_feature": sum(1 for u in units if u["claim_feature"]),
            "claims_where_aggregator_differs_from_pass_through": sum(
                1 for u in units if u["aggregator_differs_from_pass_through"]
            ),
        },
        "diversity": {
            "source_ids": tally("source_id"),
            "source_families": tally("source_family"),
            "proposition_kinds": tally("proposition_kind"),
            "claim_types": tally("claim_type"),
            "temporalities": tally("temporality"),
            "observation_categories": tally("observation_categories"),
            "independence_states": tally("independence_states"),
            "limiting_components": tally("limiting_components"),
            "distinct_reliability_values": tally("distinct_reliability_values"),
            "evidence_counts": tally("evidence_count"),
        },
        "units": units,
    }

    out = pathlib.Path(args.out)
    out.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(" | ".join(BANNER))
    totals = document["totals"]
    print(
        f"\nclaims {totals['claims']}  evidence {totals['evidence_rows']}  "
        f"scorable {totals['scorable_claims']}  "
        f"multi-Evidence {totals['multi_evidence_claims']} "
        f"(scorable {totals['scorable_multi_evidence_claims']})"
    )
    print("\nmechanisms exercised by at least one real Claim:")
    for name, count in document["mechanisms_exercised"].items():
        if name.startswith("$"):
            continue
        flag = "" if count else "   <-- NEVER"
        print(f"  {name:52} {count}{flag}")
    print("\ndiversity:")
    for name in (
        "source_families",
        "proposition_kinds",
        "limiting_components",
        "distinct_reliability_values",
        "evidence_counts",
    ):
        print(f"  {name:28} {document['diversity'][name]}")
    print(f"\nwrote {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
