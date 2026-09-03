"""Mission 1.36.1 §9, §12. What the resolver actually returns for the 8 Docker rows.

**Read-only, and it states what the code says rather than what a report expects.**
It builds each row's exact five-part scope, loads the current (non-superseded)
assessments from the database, and runs `resolve_reliability` -- the real
resolver, with no nearest-match and no partial-key behaviour of its own.

It also runs the NEGATIVE checks §10 asks for: the assessments that exist must
not resolve for scopes they were not reviewed for.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/report_docker_reliability_resolution.py

Connects to a deployment, so `DATABASE_URL` must be set -- it lives in
`infrastructure/compose/.env` rather than in the shell -- and it runs through
`uv` because a bare `python` resolves `sros_contracts` from the path insert above
and cannot import `psycopg`.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "opportunity-engine" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "evidence-reliability" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

DOCS = ROOT / "docs" / "data"
OUT = DOCS / "docker-reliability-resolution-v1.json"

ROWS = """
    SELECT e.id AS evidence_id, e.source_id, e.reliability AS supplied,
           c.claim_type, c.proposition_facts,
           s.id AS signal_id, s.signal_type_id, s.scope AS signal_scope,
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
     ORDER BY e.id
"""

ASSESSMENTS = """
    SELECT id, version, source_id, resource_id, record_kind_id, claim_type,
           proposition_kind, reliability, origin, reviewed_by, rationale,
           stated_limitation, calibration_dataset_ref
      FROM epistemic.reliability_assessments
     WHERE superseded_at IS NULL
     ORDER BY source_id
"""

BASIS = """
    SELECT basis_type, document_title, summarized_finding, document_url,
           section_reference, retrieved_at
      FROM epistemic.reliability_assessment_basis
     WHERE assessment_id = %s
"""


def main() -> int:
    import psycopg
    from sros_contracts import ClaimType, ReliabilityAssessmentOrigin, ReliabilityBasisType
    from sros_evidence_reliability import (
        ReliabilityAssessment,
        ReliabilityBasis,
        ReliabilityScope,
        resolve_reliability,
    )
    from sros_opportunity import (
        load_scope_rules,
        load_subject_registry,
        resolve_observation_scope,
    )

    registry = load_subject_registry(DOCS / "canonical-subject-registry-v1.json")
    rules = load_scope_rules(DOCS / "observation-scope-rules-v1.json")

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(ROWS)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]
        cur.execute(ASSESSMENTS)
        assessment_cols = [d[0] for d in cur.description]
        raw_assessments = [dict(zip(assessment_cols, r, strict=True)) for r in cur.fetchall()]
        for a in raw_assessments:
            cur.execute(BASIS, (a["id"],))
            a["_basis"] = cur.fetchall()

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
            # The real rows: the model refuses an assessment resting on none,
            # and a fabricated basis here would make the resolver's answer a
            # property of this script rather than of the database.
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

    per_row = []
    by_scope: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        observation = resolve_observation_scope(
            row["source_id"], row["signal_type_id"], row["signal_scope"], registry, rules
        )
        if observation.scope_id != "subject:docker":
            continue
        facts = row["proposition_facts"] or {}
        scope = ReliabilityScope(
            source_id=row["source_id"],
            resource_id=row["resource_id"],
            record_kind_id=row["record_kind_id"],
            claim_type=ClaimType(row["claim_type"]),
            proposition_kind=facts.get("proposition", ""),
        )
        resolution = resolve_reliability(
            scope=scope,
            candidates=assessments,
            supplied=float(row["supplied"]) if row["supplied"] is not None else None,
        )
        record = {
            "evidence_id": str(row["evidence_id"]),
            "scope": {
                "source_id": scope.source_id,
                "resource_id": scope.resource_id,
                "record_kind_id": scope.record_kind_id,
                "claim_type": scope.claim_type.value,
                "proposition_kind": scope.proposition_kind,
            },
            "outcome": resolution.outcome.value,
            "scorable": resolution.scorable,
            "reliability": resolution.reliability,
            "assessment_id": (resolution.binding.assessment_id if resolution.binding else None),
            "assessment_version": (
                resolution.binding.assessment_version if resolution.binding else None
            ),
            "detail": resolution.detail,
            "evidence_row_reliability_column": row["supplied"],
        }
        per_row.append(record)
        by_scope[
            (scope.source_id, scope.resource_id, scope.record_kind_id, scope.proposition_kind)
        ].append(record)

    # --- §10: the negative checks -----------------------------------------
    negatives = []
    for assessment in assessments:
        for key in sorted(by_scope, key=str):
            source, resource, kind, proposition = key
            matches = (
                assessment.scope.source_id == source
                and assessment.scope.resource_id == resource
                and assessment.scope.record_kind_id == kind
                and assessment.scope.proposition_kind == proposition
            )
            resolution = resolve_reliability(
                scope=ReliabilityScope(
                    source_id=source,
                    resource_id=resource,
                    record_kind_id=kind,
                    claim_type=ClaimType("OBSERVED"),
                    proposition_kind=proposition,
                ),
                candidates=[assessment],
            )
            negatives.append(
                {
                    "assessment_id": assessment.id,
                    "assessment_scope_source": assessment.scope.source_id,
                    "assessment_scope_proposition": assessment.scope.proposition_kind,
                    "tested_against_source": source,
                    "tested_against_proposition": proposition,
                    "scopes_are_identical": matches,
                    "outcome": resolution.outcome.value,
                    "resolved": resolution.reliability is not None,
                }
            )

    statuses = defaultdict(int)
    for record in per_row:
        statuses[record["outcome"]] += 1

    document = {
        "$comment": (
            "Mission 1.36.1 §9, §12, §10. What the REAL resolver returns for the eight "
            "Docker Evidence rows, and the negative checks proving no assessment reaches "
            "a scope it was not reviewed for. Read-only: nothing here writes, and the "
            "numbers are the code's answers rather than a report's expectations."
        ),
        "artifact_version": "docker-reliability-resolution@1.0.0",
        "generated_by": "mission-1.36.1",
        "current_assessments": [
            {
                "id": str(a["id"]),
                "version": a["version"],
                "source_id": a["source_id"],
                "proposition_kind": a["proposition_kind"],
                "origin": a["origin"],
                "reviewed_by": a["reviewed_by"],
            }
            for a in raw_assessments
        ],
        "totals": {
            "docker_evidence_rows": len(per_row),
            "resolved": statuses.get("RESOLVED", 0),
            "no_applicable_assessment": statuses.get("NO_APPLICABLE_ASSESSMENT", 0),
            "evidence_rows_with_non_null_reliability_column": sum(
                1 for r in per_row if r["evidence_row_reliability_column"] is not None
            ),
        },
        "by_scope": [
            {
                "source_id": key[0],
                "resource_id": key[1],
                "record_kind_id": key[2],
                "proposition_kind": key[3],
                "evidence_count": len(records),
                "outcomes": sorted({r["outcome"] for r in records}),
                "reliability": sorted({str(r["reliability"]) for r in records}),
                "assessment_ids": sorted({str(r["assessment_id"]) for r in records}),
            }
            for key, records in sorted(by_scope.items(), key=str)
        ],
        "rows": per_row,
        "negative_checks": negatives,
    }

    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"docker evidence rows : {len(per_row)}")
    print(f"  RESOLVED                    : {statuses.get('RESOLVED', 0)}")
    print(f"  NO_APPLICABLE_ASSESSMENT    : {statuses.get('NO_APPLICABLE_ASSESSMENT', 0)}")
    print(
        f"  evidence.reliability non-NULL: {document['totals']['evidence_rows_with_non_null_reliability_column']}"
    )
    print()
    for entry in document["by_scope"]:
        print(
            f"  {entry['source_id']:20} {entry['proposition_kind'][:48]:50} "
            f"rows={entry['evidence_count']} {entry['outcomes']} rel={entry['reliability']}"
        )
    print()
    leaks = [n for n in negatives if n["resolved"] and not n["scopes_are_identical"]]
    print(f"negative checks: {len(negatives)} run, {len(leaks)} leak(s)")
    for leak in leaks:
        print("  LEAK:", leak)
    print(f"\nwrote {OUT.name}")
    return 1 if leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
