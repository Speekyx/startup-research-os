"""What the operator's reliability decision actually did (Mission 1.42.1 §10-§22).

Runs AFTER the assessment is persisted, against the live deployment:

    §10  the real resolver over all six convergent Evidence rows, with bindings
    §11  leak checks, bidirectional, varying only `proposition_kind`
    §13  the real Evidence Aggregator over both real multi-Evidence Claims
    §16  whether `max(members)` finally received two real items
    §20  the Mission 1.37 B-2 reliability-pass-through baseline, for comparison

**Nothing is persisted by this script** except the outcome pointer written back
onto the operator review artifact, and `scoring.evidence.reliability` is never
written: reliability binds late (ADR-026 Decision 2), so a score names the
assessment and version it used rather than carrying a stale copy.

Before the assessment exists this reports honestly that nothing resolves, which
is the same thing it will report if the operator answers NO.

    uv run python infrastructure/scripts/report_convergent_reliability_resolution.py
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "evidence-reliability", "evidence-aggregation", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))

DOCS = ROOT / "docs" / "data"
OUT = DOCS / "second-pilot-convergent-reliability-resolution-v1.json"
REVIEW = DOCS / "second-pilot-convergent-operator-reliability-review-v1.json"

CONVERGENT_KIND = "source_published_classification_value_contrast_witnessed"
DETAILED_KIND = "source_reported_procurement_value_contrast"
SCOPE_FIELDS = ("source_id", "resource_id", "record_kind_id", "claim_type", "proposition_kind")

BANNER = (
    "UNCALIBRATED",
    "DIAGNOSTIC ONLY",
    "NOT AN OPPORTUNITY SCORE",
    "NOT A PROBABILITY",
)

ROWS = """
    SELECT e.id AS evidence_id, e.claim_id, e.signal_id, e.source_id, e.direction,
           e.relevance, e.directness, e.extraction_confidence, e.observation_category,
           e.independence_state, e.independence_group_id, e.reliability AS supplied,
           e.observed_at, c.claim_type, c.proposition_facts, c.current_revision,
           c.temporality,
           (SELECT DISTINCT si.record_kind_id FROM nlp.signal_inputs si
             WHERE si.signal_id = e.signal_id LIMIT 1) AS record_kind_id,
           (SELECT DISTINCT r.provenance ->> 'resource_id'
              FROM nlp.signal_inputs si
              JOIN acquisition.normalized_records n ON n.id = si.normalized_record_id
              JOIN acquisition.raw_records r ON r.id = n.raw_record_id
             WHERE si.signal_id = e.signal_id LIMIT 1) AS resource_id
      FROM scoring.evidence e
      JOIN research.claims c ON c.id = e.claim_id
     WHERE c.proposition_facts ->> 'proposition' = %s
     ORDER BY e.claim_id, e.id
"""

ASSESSMENTS = """
    SELECT id, version, source_id, resource_id, record_kind_id, claim_type,
           proposition_kind, reliability, origin, reviewed_by, reviewed_at,
           stated_limitation, review_rubric_id, review_rubric_version
      FROM epistemic.reliability_assessments
     WHERE superseded_at IS NULL
     ORDER BY source_id, proposition_kind
"""

BASIS = """
    SELECT basis_type, document_title, summarized_finding, document_url,
           section_reference, retrieved_at
      FROM epistemic.reliability_assessment_basis
     WHERE assessment_id = %s
     ORDER BY basis_type, document_title
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--link-review",
        action="store_true",
        help="write the persisted assessment id back onto the operator review artifact",
    )
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
        cur.execute(ROWS, (CONVERGENT_KIND,))
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]

        cur.execute(ASSESSMENTS)
        acols = [d[0] for d in cur.description]
        raw = [dict(zip(acols, r, strict=True)) for r in cur.fetchall()]
        for entry in raw:
            cur.execute(BASIS, (entry["id"],))
            entry["_basis"] = [
                dict(zip([d[0] for d in cur.description], b, strict=True)) for b in cur.fetchall()
            ]

        cur.execute("SELECT count(*) FROM scoring.evidence WHERE reliability IS NOT NULL")
        supplied_count = cur.fetchone()[0]

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

    # -- §10: the REAL resolver, per row, and the binding it produces ---------
    bindings = []
    resolved: dict[str, float | None] = {}
    for row in rows:
        scope = ReliabilityScope(
            source_id=row["source_id"],
            resource_id=row["resource_id"],
            record_kind_id=row["record_kind_id"],
            claim_type=ClaimType(row["claim_type"]),
            proposition_kind=CONVERGENT_KIND,
        )
        resolution = resolve_reliability(scope=scope, candidates=live, supplied=row["supplied"])
        resolved[str(row["evidence_id"])] = resolution.reliability
        binding = resolution.binding
        bindings.append(
            {
                "evidence_id": str(row["evidence_id"]),
                "claim_id": str(row["claim_id"]),
                "outcome": resolution.outcome.value,
                "reliability": resolution.reliability,
                "assessment_id": binding.assessment_id if binding else None,
                "assessment_version": binding.version if binding else None,
                "origin": binding.origin.value if binding else None,
                "reviewed_by": binding.reviewed_by if binding else None,
                "review_rubric": (
                    f"{binding.review_rubric_id}@{binding.review_rubric_version}"
                    if binding and binding.review_rubric_id
                    else None
                ),
                "evidence_reliability_column": row["supplied"],
            }
        )

    # -- §11: an assessment for one scope must not reach another --------------
    leak_checks = []
    kinds = sorted({a["proposition_kind"] for a in raw} | {DETAILED_KIND, CONVERGENT_KIND})
    for assessment in live:
        for kind in kinds:
            probe = ReliabilityScope(
                source_id=assessment.scope.source_id,
                resource_id=assessment.scope.resource_id,
                record_kind_id=assessment.scope.record_kind_id,
                claim_type=assessment.scope.claim_type,
                proposition_kind=kind,
            )
            outcome = resolve_reliability(scope=probe, candidates=[assessment], supplied=None)
            leak_checks.append(
                {
                    "assessment_id": assessment.id,
                    "assessment_proposition_kind": assessment.scope.proposition_kind,
                    "probed_proposition_kind": kind,
                    "only_field_differing": "proposition_kind",
                    "scopes_identical": assessment.scope.proposition_kind == kind,
                    "resolved": outcome.reliability is not None,
                    "outcome": outcome.outcome.value,
                }
            )
    leaks = [c for c in leak_checks if c["resolved"] and not c["scopes_identical"]]

    # -- §13-§20: the REAL aggregator, with the RESOLVED reliability ----------
    by_claim: dict[str, list[dict]] = {}
    for row in rows:
        by_claim.setdefault(str(row["claim_id"]), []).append(row)

    diagnostics = []
    for claim_id, members in sorted(by_claim.items()):
        items = [
            EvidenceItem(
                evidence_id=str(m["evidence_id"]),
                direction=EvidenceDirection(m["direction"]),
                relevance=m["relevance"],
                directness=m["directness"],
                # Resolved LATE, from the assessment. Never read from the column,
                # which stays NULL on every row by design.
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

        # §20. B-2 from the Mission 1.37 strategy: report the reliability-limited
        # strongest item and ignore every other mechanism. If the full aggregator
        # matches it, the grouping logic ran and added nothing measurable -- which
        # is a finding, not a failure.
        qs = [c.q for c in result.contributions if c.q is not None]
        pass_through = max(qs) if qs else None
        facts = members[0]["proposition_facts"] or {}

        diagnostics.append(
            {
                "$banner": list(BANNER),
                "claim_id": claim_id,
                "claim_revision": members[0]["current_revision"],
                "notice_class": facts.get("notice_class"),
                "currency": facts.get("currency"),
                "classification_division": facts.get("classification_division"),
                "raw_evidence_count": result.raw_evidence_count,
                "scorable_evidence_count": result.scorable_evidence_count,
                "non_scorable_evidence_count": result.non_scorable_evidence_count,
                "aggregation_status": result.status.value,
                "missing_requirements": list(result.missing_requirements),
                "contributions": [c.to_json() for c in result.contributions],
                "support_group_count": result.support_group_count,
                "support_groups": [g.to_json() for g in result.groups.support],
                "max_members_received": max(
                    (len(g.members) for g in result.groups.support), default=0
                ),
                "contradiction_group_count": result.contradiction_group_count,
                "unknown_independence_count": result.unknown_independence_count,
                "independence_groups_created": 0,
                "masses": result.masses.to_json(),
                "evidence_level": result.level.to_json(),
                "limiting_components": sorted(
                    {c.limiting_component for c in result.contributions if c.limiting_component}
                ),
                "reliability_pass_through_baseline": pass_through,
                "profile_id": result.aggregation_profile_id,
                "profile_version": result.aggregation_profile_version,
                "profile_status": result.aggregation_profile_status,
                "calibrated": result.calibrated,
            }
        )

    multi = [d for d in diagnostics if d["raw_evidence_count"] > 1]
    scorable_multi = [d for d in multi if d["scorable_evidence_count"] > 1]

    document = {
        "$comment": (
            "Mission 1.42.1 §10-§22. What the operator's reliability decision did, measured "
            "against the live deployment. UNCALIBRATED, DIAGNOSTIC ONLY, NOT AN OPPORTUNITY "
            "SCORE. No score is persisted, no independence is manufactured, and "
            "scoring.evidence.reliability stays NULL on every row because reliability binds "
            "late. Two witnesses of UNKNOWN provenance collapse into ONE conservative group: "
            "that is correct, and it is not corroboration."
        ),
        "$banner": list(BANNER),
        "artifact_version": "second-pilot-convergent-reliability-resolution@1.0.0",
        "generated_by": "mission-1.42.1",
        "scope": dict(
            zip(
                SCOPE_FIELDS,
                (
                    "ted-eu",
                    "notices/eforms-contract-and-award",
                    "procurement_notice",
                    "OBSERVED",
                    CONVERGENT_KIND,
                ),
                strict=True,
            )
        ),
        "current_assessments": [
            {
                "assessment_id": a.id,
                "proposition_kind": a.scope.proposition_kind,
                "version": a.version,
                "reliability": a.reliability,
                "origin": a.origin.value,
                "reviewed_by": a.reviewed_by,
                "review_rubric": (
                    f"{a.review_rubric_id}@{a.review_rubric_version}"
                    if a.review_rubric_id
                    else None
                ),
                "is_the_scope_under_review": a.scope.proposition_kind == CONVERGENT_KIND,
            }
            for a in live
        ],
        "resolution": {
            "evidence_rows": len(rows),
            "claims": len(by_claim),
            "resolved_rows": sum(1 for b in bindings if b["reliability"] is not None),
            "bindings": bindings,
            "evidence_reliability_column_non_null": supplied_count,
            "$note": (
                "ADR-026 Decision 2. Every binding is produced at resolve time and no "
                "reliability is written onto scoring.evidence."
            ),
        },
        "leak_checks": {
            "run": len(leak_checks),
            "leaks_found": len(leaks),
            "checks": leak_checks,
        },
        "aggregation_diagnostic": {
            "$note": (
                "The real aggregator, allow_uncalibrated=True, nothing persisted. "
                "`max_members_received` is the size of the largest support group, which is "
                "what `max(members)` actually saw."
            ),
            "multi_evidence_claims": len(multi),
            "scorable_multi_evidence_claims": len(scorable_multi),
            "claims": diagnostics,
        },
    }
    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.link_review:
        current = [a for a in live if a.scope.proposition_kind == CONVERGENT_KIND]
        if len(current) != 1:
            print(f"REFUSED: expected exactly one assessment for the scope, found {len(current)}")
            return 1
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        review["persisted_assessment"] = {
            "id": current[0].id,
            "version": current[0].version,
            "recorded_at": current[0].reviewed_at.isoformat(),
        }
        REVIEW.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"linked review artifact -> assessment {current[0].id} v{current[0].version}")

    print(" | ".join(BANNER))
    print(f"\nconvergent Evidence rows : {len(rows)} across {len(by_claim)} Claims")
    print(f"resolved                 : {document['resolution']['resolved_rows']}/{len(rows)}")
    print(f"evidence.reliability set : {supplied_count} (expected 0, late binding)")
    print(f"leak checks              : {len(leak_checks)} run, {len(leaks)} leak(s)")
    print(f"multi-Evidence Claims    : {len(multi)}, scorable: {len(scorable_multi)}")
    for entry in diagnostics:
        print(
            f"  claim {entry['claim_id'][:8]}  raw={entry['raw_evidence_count']} "
            f"scorable={entry['scorable_evidence_count']} "
            f"groups={entry['support_group_count']} "
            f"max_members={entry['max_members_received']} "
            f"status={entry['aggregation_status']}"
        )
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
