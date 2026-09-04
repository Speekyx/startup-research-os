"""What the Wikimedia convergent reliability decision produced (Mission 1.44.1).

Runs the REAL resolver over the affected Evidence, the REAL leak checks over
every proposition kind in the corpus, and the REAL aggregator over the six
multi-Evidence Claims -- which is the first time `max(members)` receives groups
of three and four real canonical items.

**UNCALIBRATED, DIAGNOSTIC ONLY, NOT AN OPPORTUNITY SCORE, NOT A PROBABILITY.**
No score is persisted and no parameter is fitted.

    uv run python infrastructure/scripts/report_wikimedia_convergent_reliability_resolution.py
    uv run python infrastructure/scripts/report_wikimedia_convergent_reliability_resolution.py --link-review
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
OUT = DOCS / "wikimedia-convergent-reliability-resolution-v1.json"
REVIEW = DOCS / "wikimedia-convergent-operator-reliability-review-v1.json"

CONVERGENT_KIND = "platform_counted_content_request_change_witnessed"
DETAILED_KIND = "platform_counted_content_request_change"
SCOPE_FIELDS = ("source_id", "resource_id", "record_kind_id", "claim_type", "proposition_kind")

BANNER = ("UNCALIBRATED", "DIAGNOSTIC ONLY", "NOT AN OPPORTUNITY SCORE", "NOT A PROBABILITY")

ALL_KINDS = (
    "source_reported_procurement_value_contrast",
    "source_published_classification_value_contrast_witnessed",
    "platform_counted_content_request_change",
    "platform_counted_content_request_change_witnessed",
    "community_site_published_questions_carrying_tag",
    "community_site_questions_without_accepted_answer",
    "source_reported_metric_period_change",
    "source_reported_term_frequency_change",
    "source_reported_term_frequency_contrast",
)

ROWS = """
    SELECT e.id AS evidence_id, e.claim_id, e.signal_id, e.source_id, e.direction,
           e.relevance, e.directness, e.extraction_confidence, e.observation_category,
           e.independence_state, e.independence_group_id, e.reliability AS supplied,
           e.observed_at,
           c.claim_type, c.proposition_facts, c.current_revision, c.temporality,
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
           stated_limitation, review_rubric_id, review_rubric_version, created_at
      FROM epistemic.reliability_assessments
     WHERE superseded_at IS NULL
     ORDER BY created_at
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--link-review",
        action="store_true",
        help="write the persisted assessment back into the review artifact",
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
            cur.execute(
                "SELECT basis_type, document_title, summarized_finding, document_url,"
                " section_reference, retrieved_at"
                " FROM epistemic.reliability_assessment_basis WHERE assessment_id = %s",
                (entry["id"],),
            )
            bcols = [d[0] for d in cur.description]
            entry["_basis"] = [dict(zip(bcols, b, strict=True)) for b in cur.fetchall()]

        cur.execute("SELECT count(*) FROM scoring.evidence WHERE reliability IS NOT NULL")
        reliability_written = cur.fetchone()[0]
        cur.execute(
            "SELECT count(DISTINCT independence_group_id) FROM scoring.evidence"
            " WHERE independence_group_id IS NOT NULL"
        )
        independence_groups = cur.fetchone()[0]

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

    # ------------------------------------------------------------- §7 bindings
    bindings = []
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
        binding = resolution.binding
        row["_reliability"] = resolution.reliability
        bindings.append(
            {
                "evidence_id": str(row["evidence_id"]),
                "claim_id": str(row["claim_id"]),
                "content_id": facts.get("content_id"),
                "direction_fact": facts.get("direction"),
                "outcome": resolution.outcome.value,
                "reliability": resolution.reliability,
                "assessment_id": binding.assessment_id if binding else None,
                "assessment_version": binding.version if binding else None,
                "origin": binding.origin.value if binding else None,
                "reviewed_by": binding.reviewed_by if binding else None,
                "review_rubric_id": binding.review_rubric_id if binding else None,
                "review_rubric_version": binding.review_rubric_version if binding else None,
                "evidence_reliability_column": row["supplied"],
            }
        )

    # ---------------------------------------------------------- §8 leak checks
    leak_checks = []
    for assessment in live:
        for kind in ALL_KINDS:
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

    # ----------------------------------------------- §9-§14 the real aggregator
    by_claim: dict[str, list[dict]] = {}
    for row in rows:
        by_claim.setdefault(str(row["claim_id"]), []).append(row)

    claims = []
    for claim_id, members in sorted(by_claim.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        facts = members[0]["proposition_facts"] or {}
        items = [
            EvidenceItem(
                evidence_id=str(m["evidence_id"]),
                direction=EvidenceDirection(m["direction"]),
                relevance=m["relevance"],
                directness=m["directness"],
                reliability=m["_reliability"],
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
        claims.append(
            {
                "claim_id": claim_id,
                "content_id": facts.get("content_id"),
                "direction_fact": facts.get("direction"),
                "audience_class": facts.get("audience_class"),
                "temporality": members[0]["temporality"],
                "claim_feature": None,
                "raw_evidence_count": len(members),
                "scorable_evidence_count": result.scorable_evidence_count,
                "aggregation_status": result.status.value,
                "contributions": [
                    {
                        "evidence_id": c.evidence_id,
                        # The components live in a mapping, not as attributes.
                        **{name: value for name, value in c.components.items()},
                        "scorable": c.scorable,
                        "q": c.q,
                        "limiting_component": c.limiting_component,
                    }
                    for c in result.contributions
                ],
                "support_group_count": result.support_group_count,
                "contradiction_group_count": result.contradiction_group_count,
                "max_members_received": max(
                    (len(g.member_evidence_ids) for g in result.groups.support), default=0
                ),
                "collapsed_member_count": sum(
                    g.collapsed_member_count for g in result.groups.support
                ),
                "support_groups": [g.to_json() for g in result.groups.support],
                "established_independence_groups": sum(
                    1 for g in result.groups.support if g.kind.value == "INDEPENDENT"
                ),
                "unknown_independence_count": sum(
                    1 for m in members if m["independence_state"] == "UNKNOWN"
                ),
                "independence_groups_created": 0,
                "masses": result.masses.to_json(),
                "evidence_score": (
                    100.0 * result.masses.supported_mass
                    if result.status.value == "COMPLETE"
                    else None
                ),
                "evidence_level": result.level.to_json(),
                "limiting_components": sorted(
                    {c.limiting_component for c in result.contributions if c.limiting_component}
                ),
                "reliability_pass_through_baseline": pass_through,
                "versus_reliability_pass_through": (
                    "DIFFERS_FROM_RELIABILITY_PASS_THROUGH"
                    if differs
                    else "IDENTICAL_TO_RELIABILITY_PASS_THROUGH"
                ),
                "multi_evidence_verdict": (
                    "MULTI_EVIDENCE_PROCESSING_OCCURRED / NO_INDEPENDENT_CORROBORATION"
                    if result.scorable_evidence_count > 1 and result.support_group_count == 1
                    else None
                ),
                "contradiction_case": (
                    "NO_REAL_CONTRADICTION_CASE_YET"
                    if result.contradiction_group_count == 0
                    else "CONTRADICTION_PRESENT"
                ),
                "profile_status": REFERENCE_PROFILE_V1.status.value,
                "calibrated": False,
            }
        )

    new = [a for a in raw if a["proposition_kind"] == CONVERGENT_KIND]
    document = {
        "$comment": (
            "Mission 1.44.1. What the operator's decision produced, measured through the "
            "REAL resolver and the REAL aggregator. UNCALIBRATED, DIAGNOSTIC ONLY, NOT AN "
            "OPPORTUNITY SCORE, NOT A PROBABILITY. No score is persisted, no parameter is "
            "fitted, and no independence group is created."
        ),
        "$banner": list(BANNER),
        "artifact_version": "wikimedia-convergent-reliability-resolution@1.0.0",
        "generated_by": "mission-1.44.1",
        "persisted_assessment": (
            {
                "id": str(new[0]["id"]),
                "version": new[0]["version"],
                "reliability": float(new[0]["reliability"]),
                "origin": new[0]["origin"],
                "reviewed_by": new[0]["reviewed_by"],
                "review_rubric_id": new[0]["review_rubric_id"],
                "review_rubric_version": new[0]["review_rubric_version"],
                "recorded_at": new[0]["created_at"].isoformat(),
                "basis_rows": len(new[0]["_basis"]),
            }
            if new
            else None
        ),
        "resolution": {
            "evidence_rows": len(rows),
            "resolved": sum(1 for b in bindings if b["outcome"] == "RESOLVED"),
            "evidence_reliability_column_non_null": reliability_written,
            "bindings": bindings,
        },
        "leak_checks": {
            "run": len(leak_checks),
            "leaks_found": len(leaks),
            "checks": leak_checks,
        },
        "current_assessments": [
            {
                "assessment_id": str(a["id"]),
                "version": a["version"],
                "scope": {field: a[field] for field in SCOPE_FIELDS},
                "reliability": float(a["reliability"]),
                "reviewed_by": a["reviewed_by"],
                "review_rubric": (
                    f"{a['review_rubric_id']}@{a['review_rubric_version']}"
                    if a["review_rubric_id"]
                    else None
                ),
                "is_the_scope_under_review": a["proposition_kind"] == CONVERGENT_KIND,
            }
            for a in raw
        ],
        "aggregation_diagnostic": {
            "$note": (
                "The first time `max(members)` receives groups of THREE and FOUR real "
                "canonical items. It is not corroboration: every witness of a Claim sits in "
                "ONE unknown-provenance group, because independence is UNKNOWN."
            ),
            "independence_groups_in_deployment": independence_groups,
            "claims": claims,
        },
    }

    OUT.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )

    if args.link_review and new:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        review["persisted_assessment"] = {
            "id": str(new[0]["id"]),
            "version": new[0]["version"],
            "recorded_at": new[0]["created_at"].isoformat(),
        }
        REVIEW.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"linked review artifact -> assessment {new[0]['id']} v{new[0]['version']}")

    print(" | ".join(BANNER))
    print()
    print(f"convergent Evidence rows : {len(rows)} across {len(by_claim)} Claims")
    print(f"resolved                 : {document['resolution']['resolved']}/{len(rows)}")
    print(f"evidence.reliability set : {reliability_written} (expected 0, late binding)")
    print(f"leak checks              : {len(leak_checks)} run, {len(leaks)} leak(s)")
    print(f"independence groups      : {independence_groups}")
    print()
    for claim in claims:
        print(
            f"  {claim['claim_id'][:8]} {str(claim['content_id'])[:18]:20}"
            f" {str(claim['direction_fact']):11}"
            f" raw={claim['raw_evidence_count']} scorable={claim['scorable_evidence_count']}"
            f" groups={claim['support_group_count']} max_members={claim['max_members_received']}"
            f" q={claim['contributions'][0]['q']} {claim['aggregation_status']}"
        )
    print()
    print(f"wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
