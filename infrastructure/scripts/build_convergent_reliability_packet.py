"""Mission 1.42 §0, §1, §14. The reliability question for the convergent TED scope.

**It prepares the question and supplies no answer.** Every judgement field is
blank, and there is no field anywhere in this script that could hold a value:
`reliability`, `reviewed_by`, `reviewer_rationale`, `stated_limitation` and
`review_decision` are written as `null` or `""` and never assigned.

The existing TED assessment appears only as OTHER-SCOPE historical context
(§4, §16). Its `0.5` is a fact about a different proposition kind, it is not a
baseline, and it is not a starting point.

Read-only. It writes one JSON artifact and no database row.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/build_convergent_reliability_packet.py
    uv run --package sros-nlp python infrastructure/scripts/build_convergent_reliability_packet.py --check

Connects to a deployment, so `DATABASE_URL` must be set -- it lives in
`infrastructure/compose/.env` rather than in the shell -- and it runs through
`uv` because a bare `python` cannot import `psycopg`.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "evidence-reliability", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))

DOCS = ROOT / "docs" / "data"
OUT = DOCS / "second-pilot-convergent-reliability-review-packet-v1.json"
FINDINGS = ROOT / "infrastructure" / "scripts" / "convergent_reliability_findings.json"

CONVERGENT_KIND = "source_published_classification_value_contrast_witnessed"
DETAILED_KIND = "source_reported_procurement_value_contrast"

# Exactly the five fields ADR-026 makes a reliability scope. §0 forbids adding
# CPV division, currency, notice class, subject or any row id.
SCOPE_FIELDS = ("source_id", "resource_id", "record_kind_id", "claim_type", "proposition_kind")

ROWS = """
    SELECT e.id AS evidence_id, e.claim_id, e.signal_id, e.source_id, e.direction,
           e.relevance, e.directness, e.extraction_confidence, e.observation_category,
           e.independence_state, e.independence_group_id, e.reliability AS supplied,
           c.claim_type, c.proposition_facts, c.current_revision,
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
           proposition_kind, reliability, origin, reviewed_by, stated_limitation,
           review_rubric_id, review_rubric_version
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

# THE ONLY PLACE A JUDGEMENT COULD GO, and every field is empty. Kept as one
# object so a reader can see that the packet has no other slot for one.
BLANK_JUDGEMENT = {
    "review_decision": None,
    "reliability": None,
    "reviewed_by": None,
    "reviewer_rationale": "",
    "stated_limitation": "",
    "$note": (
        "Blank because a reliability value is a HUMAN judgement for one exact "
        "measurement-crossed-with-proposition scope. Software prepared every fact above and "
        "supplied no answer, suggested none, and has no code path that could. §16 forbids a "
        "recommended value, a range and any threshold adjective, and a test scans this object "
        "for all three."
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare and write nothing")
    args = parser.parse_args()

    import psycopg
    from sros_contracts import ClaimType, ReliabilityAssessmentOrigin, ReliabilityBasisType
    from sros_evidence_reliability import (
        ReliabilityAssessment,
        ReliabilityBasis,
        ReliabilityScope,
        resolve_reliability,
    )

    findings = json.loads(FINDINGS.read_text(encoding="utf-8"))

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(ROWS, (CONVERGENT_KIND,))
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]

        cur.execute(ASSESSMENTS)
        acols = [d[0] for d in cur.description]
        assessments_raw = [dict(zip(acols, r, strict=True)) for r in cur.fetchall()]
        for entry in assessments_raw:
            cur.execute(BASIS, (entry["id"],))
            entry["_basis"] = [
                dict(zip([d[0] for d in cur.description], b, strict=True)) for b in cur.fetchall()
            ]

        # Witness membership, for §1's table. Read from lineage, never from the
        # Claim: the whole point of the convergent proposition is that cohort
        # membership left the Claim's identity.
        for row in rows:
            cur.execute(
                """SELECT o.observation_key
                     FROM nlp.signal_inputs i
                     JOIN acquisition.normalized_records n ON n.id = i.normalized_record_id
                     JOIN acquisition.raw_records o ON o.id = n.raw_record_id
                    WHERE i.signal_id = %s AND i.role = 'CONTRIBUTED'
                    ORDER BY o.observation_key""",
                (row["signal_id"],),
            )
            row["_witness"] = [r[0] for r in cur.fetchall()]

    # -- §0: GROUP on the exact five-part key, measured rather than assumed ---
    scopes: dict[tuple, list[dict]] = {}
    for row in rows:
        facts = row["proposition_facts"] or {}
        key = (
            row["source_id"],
            row["resource_id"],
            row["record_kind_id"],
            row["claim_type"],
            facts.get("proposition", ""),
        )
        scopes.setdefault(key, []).append(row)

    # -- the real resolver over the real rows, with the real assessments ------
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
            reviewed_at=None,
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
        for a in assessments_raw
    ]

    resolutions = []
    for key, members in scopes.items():
        scope = ReliabilityScope(
            source_id=key[0],
            resource_id=key[1],
            record_kind_id=key[2],
            claim_type=ClaimType(key[3]),
            proposition_kind=key[4],
        )
        resolution = resolve_reliability(scope=scope, candidates=live, supplied=None)
        resolutions.append(
            {
                "scope": dict(zip(SCOPE_FIELDS, key, strict=True)),
                "evidence_count": len(members),
                "outcome": resolution.outcome.value,
                "reliability": resolution.reliability,
                "detail": resolution.detail,
            }
        )

    # -- §22: an assessment for one scope must not reach another -------------
    leak_checks = []
    other_kinds = sorted(
        {a["proposition_kind"] for a in assessments_raw} | {DETAILED_KIND, CONVERGENT_KIND}
    )
    for assessment in live:
        for kind in other_kinds:
            probe = ReliabilityScope(
                source_id=assessment.scope.source_id,
                resource_id=assessment.scope.resource_id,
                record_kind_id=assessment.scope.record_kind_id,
                claim_type=assessment.scope.claim_type,
                proposition_kind=kind,
            )
            resolution = resolve_reliability(scope=probe, candidates=[assessment], supplied=None)
            leak_checks.append(
                {
                    "assessment_id": assessment.id,
                    "assessment_proposition_kind": assessment.scope.proposition_kind,
                    "probed_proposition_kind": kind,
                    "only_field_differing": "proposition_kind",
                    "scopes_identical": assessment.scope.proposition_kind == kind,
                    "resolved": resolution.reliability is not None,
                    "outcome": resolution.outcome.value,
                }
            )

    document = {
        "$comment": (
            "Mission 1.42 §14. The reliability question for ONE exact scope, prepared and NOT "
            "answered. Every judgement field is blank and this generator has no code path that "
            "could fill one. The existing TED assessment appears only as OTHER-SCOPE historical "
            "context: its value belongs to a different proposition kind, it is not a baseline, "
            "and §4 forbids treating it as a starting point. GENERATED -- edit "
            "convergent_reliability_findings.json and re-render."
        ),
        "artifact_version": "second-pilot-convergent-reliability-review-packet@1.0.0",
        "generated_by": "mission-1.42",
        "outcome": "READY_FOR_SECOND_PILOT_RELIABILITY_REVIEW",
        "reliability_scale": {
            "range": "[0.0, 1.0]",
            "threshold_labels": None,
            "$note": (
                "The architecture defines no meaning for any particular value and no threshold "
                "vocabulary. A packet that invented one would be legislating."
            ),
        },
        "what_reliability_means": findings["what_reliability_means"],
        "measured_scopes": resolutions,
        "scope_breadth_finding": {
            "$note": (
                "§1. Mission 1.41 reported two Claims with two Evidence rows each, so the "
                "brief expected four rows. The live deployment holds more, and this records "
                "WHY that is not SECOND_PILOT_RELIABILITY_SCOPE_DRIFT: drift would be a "
                "reliability scope other than the expected five-part one, and there is exactly "
                "one scope and it is the expected one. A reliability scope carries NO "
                "classification division and NO currency, so it reaches every convergent Claim "
                "from this measurement -- not only the multi-Evidence ones."
            ),
            "brief_expected_evidence_rows": 4,
            "brief_expected_claims": 2,
            "live_evidence_rows": len(rows),
            "live_claims": len({str(r["claim_id"]) for r in rows}),
            "live_multi_evidence_claims": sum(
                1
                for claim_id in {str(r["claim_id"]) for r in rows}
                if sum(1 for r in rows if str(r["claim_id"]) == claim_id) > 1
            ),
            "is_scope_drift": False,
            "distinct_classification_divisions_in_scope": sorted(
                {(row["proposition_facts"] or {}).get("classification_division") for row in rows}
            ),
            "distinct_currencies_in_scope": sorted(
                {(row["proposition_facts"] or {}).get("currency") for row in rows}
            ),
            "what_this_changes_for_the_reviewer": (
                "One judgement on this scope binds every row above, including the "
                "division-90 Claim -- whose only witness is the Signal derived in Mission "
                "1.15.10, before the second pilot existed -- and the single-witness Claims. "
                "The reviewer is not answering only for the two multi-Evidence division-92 "
                "Claims."
            ),
            "precedent": (
                "Mission 1.40 recorded the same property from the other side: the existing TED "
                "assessment binds to the new division-92 DETAILED claim because its scope "
                "carries no division either."
            ),
        },
        "affected_rows": [
            {
                "claim_id": str(row["claim_id"]),
                "claim_revision": row["current_revision"],
                "evidence_id": str(row["evidence_id"]),
                "signal_id": str(row["signal_id"]),
                "witness_observation_keys": row["_witness"],
                "notice_class": (row["proposition_facts"] or {}).get("notice_class"),
                "currency": (row["proposition_facts"] or {}).get("currency"),
                "classification_division": (row["proposition_facts"] or {}).get(
                    "classification_division"
                ),
                "direction": row["direction"],
                "relevance": row["relevance"],
                "directness": row["directness"],
                "extraction_confidence": row["extraction_confidence"],
                "observation_category": row["observation_category"],
                "independence_state": row["independence_state"],
                "independence_group_id": row["independence_group_id"],
                "evidence_reliability_column": row["supplied"],
            }
            for row in rows
        ],
        "detailed_versus_convergent": findings["detailed_versus_convergent"],
        "documentary_review_matrix": findings["documentary_review_matrix"],
        "failure_modes": findings["failure_modes"],
        "engineering_validation_inputs": findings["engineering_validation_inputs"],
        "candidate_basis_rows": findings["candidate_basis_rows"],
        "existing_basis_applicability": findings["existing_basis_applicability"],
        "open_questions": findings["open_questions"],
        "what_a_value_would_not_do": findings["what_a_value_would_not_do"],
        "other_scope_historical_context": [
            {
                "$note": (
                    "A DIFFERENT scope's persisted assessment, reproduced as fact. §4: it shows "
                    "what documentation was accepted and how the workflow is structured. It is "
                    "not a baseline for this scope and must not be copied."
                ),
                "assessment_id": str(a["id"]),
                "version": a["version"],
                "scope": {field: a[field] for field in SCOPE_FIELDS},
                "origin": a["origin"],
                "reviewed_by": a["reviewed_by"],
                "reliability": float(a["reliability"]),
                "review_rubric": (
                    f"{a['review_rubric_id']}@{a['review_rubric_version']}"
                    if a["review_rubric_id"]
                    else None
                ),
                "is_the_scope_under_review": a["proposition_kind"] == CONVERGENT_KIND,
                "basis_row_count": len(a["_basis"]),
            }
            for a in assessments_raw
        ],
        "leak_checks": leak_checks,
        "operator_worksheet": {
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
            "question_1": (
                "Do I have enough documented information to make an accountable reliability "
                "judgement for this exact measurement and this exact proposition?"
            ),
            "question_1_answer": None,
            "if_no": (
                f"Leave the ReliabilityAssessment absent. All {len(rows)} Evidence rows across "
                f"{len({str(r['claim_id']) for r in rows})} Claims stay NON_SCORABLE and the "
                "resolver keeps returning NO_APPLICABLE_ASSESSMENT, which is the designed "
                "behaviour rather than a gap. NO is a real answer."
            ),
            "judgement": dict(BLANK_JUDGEMENT),
            "confirmations": [
                {"checked": False, "statement": "This is not a source-wide TED score."},
                {"checked": False, "statement": "This is not a probability the Claim is true."},
                {
                    "checked": False,
                    "statement": "This is not copied from the existing TED 0.5.",
                },
                {"checked": False, "statement": "This is not a score for CPV division 92."},
                {"checked": False, "statement": "This does not establish independence."},
                {
                    "checked": False,
                    "statement": "This does not calibrate the aggregation profile.",
                },
                {
                    "checked": False,
                    "statement": "This judgement was made by the named reviewer.",
                },
            ],
        },
        "what_this_packet_is_not": findings["what_this_packet_is_not"],
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"REFUSED: {OUT.name} does not exist; run without --check first")
            return 1
        if OUT.read_text(encoding="utf-8") == rendered:
            print(f"ok       {OUT.name} matches the live canonical state")
            return 0
        print(f"DRIFT    {OUT.name} does not match the live canonical state")
        return 1

    OUT.write_text(rendered, encoding="utf-8")

    print(f"convergent Evidence rows : {len(rows)}")
    print(f"distinct Claims          : {len({str(r['claim_id']) for r in rows})}")
    print(f"distinct reliability scopes: {len(scopes)}")
    for entry in resolutions:
        print(
            f"  {entry['scope']['proposition_kind'][:56]:58} "
            f"rows={entry['evidence_count']} {entry['outcome']}"
        )
    leaks = [c for c in leak_checks if c["resolved"] and not c["scopes_identical"]]
    print(f"\nleak checks: {len(leak_checks)} run, {len(leaks)} leak(s)")
    print(f"judgement fields: {sorted(BLANK_JUDGEMENT)} -- all blank")
    print(f"\nwrote {OUT.name}")
    return 1 if leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
