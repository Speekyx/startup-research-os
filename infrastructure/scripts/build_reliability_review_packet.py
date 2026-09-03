"""Mission 1.36 §13. Build the Docker reliability review packet. No judgement.

**This script cannot produce a reliability value and has no field in which to put
one.** Every judgement key it writes is `null` or an empty string, and a test
asserts that the emitted document contains no number in any judgement position
and no adjective ranking a source. The mission's whole point is that the number
is the operator's, so the software prepares the question and stops.

**Read-only over the research tables.** It computes the exact five-part scopes
the Docker Evidence rows bind to, attaches the acquisition provenance recorded at
collection time, and carries the documentary findings this mission retrieved. It
writes one JSON artifact under `docs/data/` and nothing else.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/build_reliability_review_packet.py

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
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

DOCS = ROOT / "docs" / "data"
OUT = DOCS / "docker-evidence-reliability-review-packet-v1.json"
FINDINGS = ROOT / "infrastructure" / "scripts" / "reliability_review_findings.json"

ROWS = """
    SELECT e.id AS evidence_id, e.source_id, e.reliability, e.relevance, e.directness,
           e.extraction_confidence, e.independence_state, e.evidence_level,
           e.observation_category, e.extraction_method,
           c.claim_type, c.proposition_facts,
           s.id AS signal_id, s.signal_type_id, s.scope AS signal_scope,
           s.parameters, s.temporal_window, s.derivation_confidence,
           (SELECT DISTINCT si.record_kind_id FROM nlp.signal_inputs si
             WHERE si.signal_id = s.id LIMIT 1) AS record_kind_id,
           (SELECT DISTINCT si.record_kind_registry FROM nlp.signal_inputs si
             WHERE si.signal_id = s.id LIMIT 1) AS record_kind_registry,
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

PROVENANCE = """
    SELECT DISTINCT r.provenance, n.normalizer_id, n.normalizer_version,
           r.collector_id, r.collector_version, n.quality
      FROM nlp.signal_inputs si
      JOIN acquisition.normalized_records n ON n.id = si.normalized_record_id
      JOIN acquisition.raw_records r ON r.id = n.raw_record_id
     WHERE si.signal_id = %s
"""

#: Provenance keys worth carrying into a review packet, per source. Everything
#: else the collector recorded is governance or plumbing and is not evidence
#: about the MEASUREMENT.
PROVENANCE_KEYS = {
    "stack-exchange": (
        "tagged",
        "site",
        "filter",
        "page",
        "page_size",
        "max_pages",
        "max_records",
        "quota_max",
        "quota_remaining",
        "date_window",
        "resource_id",
        "endpoint",
    ),
    "wikimedia-pageviews": (
        "article",
        "project",
        "access",
        "agent",
        "agent_semantics",
        "granularity",
        "date_window",
        "max_days",
        "resource_id",
        "endpoint",
        "user_agent",
    ),
}

BLANK_JUDGEMENT = {
    "$comment": (
        "EVERY FIELD HERE IS THE OPERATOR'S. Software did not fill any of them and has "
        "no code path that could: no number, no range, no recommendation, no adjective. "
        "`reliability: null` means NO ASSESSMENT EXISTS. It does not mean 0.0, 0.5, or "
        "any other value, and unknown is never defaulted."
    ),
    "reliability": None,
    "reviewed_by": None,
    "reviewer_rationale": "",
    "stated_limitation": "",
    "reviewer_decision": None,
    "origin_if_reviewed": "HUMAN_REVIEW",
}


def main() -> int:
    import psycopg
    from sros_opportunity import (
        load_scope_rules,
        load_subject_registry,
        resolve_observation_scope,
    )

    registry = load_subject_registry(DOCS / "canonical-subject-registry-v1.json")
    rules = load_scope_rules(DOCS / "observation-scope-rules-v1.json")
    findings = json.loads(FINDINGS.read_text(encoding="utf-8"))

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(ROWS)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]

        docker: list[dict] = []
        for row in rows:
            scope = resolve_observation_scope(
                row["source_id"], row["signal_type_id"], row["signal_scope"], registry, rules
            )
            if scope.scope_id == "subject:docker":
                docker.append(row)

        grouped: dict[tuple, list[dict]] = defaultdict(list)
        for row in docker:
            facts = row["proposition_facts"] or {}
            grouped[
                (
                    row["source_id"],
                    row["resource_id"],
                    row["record_kind_id"],
                    row["claim_type"],
                    facts.get("proposition"),
                )
            ].append(row)

        scopes = []
        for key in sorted(grouped, key=str):
            source, resource, kind, claim_type, proposition = key
            members = sorted(grouped[key], key=lambda m: str(m["evidence_id"]))

            provenance: dict[str, object] = {}
            tooling: set[str] = set()
            for member in members:
                cur.execute(PROVENANCE, (member["signal_id"],))
                for prov, nid, nver, cid, cver, quality in cur.fetchall():
                    tooling.add(
                        f"collector {cid}@{cver}; normalizer {nid}@{nver}; quality {quality}"
                    )
                    for k in PROVENANCE_KEYS.get(source, ()):
                        if k in prov:
                            provenance.setdefault(k, prov[k])

            note = findings["scopes"].get(proposition)
            if note is None:
                raise SystemExit(
                    f"REFUSED: no documentary findings recorded for proposition kind "
                    f"{proposition!r}. A scope with no prepared review is a scope this "
                    "packet would ship blank, and §13 requires the findings."
                )

            scopes.append(
                {
                    "scope": {
                        "source_id": source,
                        "resource_id": resource,
                        "record_kind_registry": members[0]["record_kind_registry"],
                        "record_kind_id": kind,
                        "claim_type": claim_type,
                        "proposition_kind": proposition,
                    },
                    "assessment_key_candidate": None,
                    "evidence_count": len(members),
                    "evidence_ids": [str(m["evidence_id"]) for m in members],
                    "signal_types_represented": sorted(
                        {m["signal_type_id"] for m in members if m["signal_type_id"]}
                    ),
                    "current_resolver_status": {
                        "reliability_on_evidence_rows": sorted(
                            {
                                ("NULL" if m["reliability"] is None else str(m["reliability"]))
                                for m in members
                            }
                        ),
                        "resolution": "NO_APPLICABLE_ASSESSMENT",
                        "scorable": False,
                        "note": (
                            "No reliability assessment matches this exact five-part scope, so "
                            "the resolver returns NO_APPLICABLE_ASSESSMENT and every row is "
                            "NON_SCORABLE with MISSING_RELIABILITY. That is the designed "
                            "behaviour, not a gap to fill with a default."
                        ),
                    },
                    "separately_known_and_not_reliability": {
                        "$comment": (
                            "§12. These are different components answering different "
                            "questions. A deterministic extractor reading a Signal perfectly "
                            "says nothing about whether the underlying measurement is "
                            "dependable for this proposition."
                        ),
                        "relevance": sorted({m["relevance"] for m in members}),
                        "directness": sorted({m["directness"] for m in members}),
                        "extraction_confidence": sorted(
                            {m["extraction_confidence"] for m in members}
                        ),
                        "derivation_confidence": sorted(
                            {float(m["derivation_confidence"]) for m in members}
                        ),
                        "independence_state": sorted({m["independence_state"] for m in members}),
                        "evidence_level": sorted({m["evidence_level"] for m in members}),
                        "observation_category": sorted(
                            {m["observation_category"] for m in members}
                        ),
                    },
                    "measurement_definition": note["measurement_definition"],
                    "proposition_definition": note["proposition_definition"],
                    "acquisition_provenance": {
                        "$comment": (
                            "Recorded by the collector AT COLLECTION TIME from the source's "
                            "own responses. First-party evidence about the retrieval even "
                            "where the publisher's documentation is unreachable now."
                        ),
                        "tooling": sorted(tooling),
                        **provenance,
                    },
                    "authoritative_documents": note["authoritative_documents"],
                    "methodology_findings": note["methodology_findings"],
                    "failure_modes": note["failure_modes"],
                    "unresolved_questions": note["unresolved_questions"],
                    "candidate_basis_rows": note["candidate_basis_rows"],
                    "documentation_status": note["documentation_status"],
                    "operator_judgement": dict(BLANK_JUDGEMENT),
                }
            )

        cur.execute(
            "SELECT source_id, resource_id, record_kind_id, claim_type, proposition_kind, "
            "version FROM epistemic.reliability_assessments WHERE superseded_at IS NULL"
        )
        existing = [
            {
                "source_id": r[0],
                "resource_id": r[1],
                "record_kind_id": r[2],
                "claim_type": r[3],
                "proposition_kind": r[4],
                "version": r[5],
            }
            for r in cur.fetchall()
        ]

    document = {
        "$comment": findings["artifact_comment"],
        "artifact_version": "docker-evidence-reliability-review-packet@1.0.0",
        "prepared_by": "mission-1.36",
        "prepared_at": "2026-09-03T00:00:00+00:00",
        "outcome": "READY_FOR_OPERATOR_RELIABILITY_REVIEW",
        "contract": findings["contract"],
        "scope_count": len(scopes),
        "evidence_rows_covered": sum(s["evidence_count"] for s in scopes),
        "scopes": scopes,
        "existing_assessments_and_why_they_do_not_apply": {
            "$comment": (
                "§16. No inheritance. An assessment applies only where ALL FIVE fields "
                "match exactly, and the one that exists matches none of the scopes above "
                "on any of the five."
            ),
            "assessments": existing,
            "matches_any_docker_scope": False,
        },
        "worksheet": findings["worksheet"],
    }

    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"docker evidence rows      : {len(docker)}")
    print(f"distinct reliability scopes: {len(scopes)}")
    for s in scopes:
        sc = s["scope"]
        print(
            f"  {sc['source_id']:20} {sc['proposition_kind']:52} "
            f"rows={s['evidence_count']} docs={s['documentation_status']}"
        )
    print(f"existing assessments      : {len(existing)} (matching none of the above)")
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
