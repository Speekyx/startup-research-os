"""Which registered resource produced this measurement? (Mission 1.77)

The reliability scope is five facts -- source, resource, record kind, claim type and
proposition kind -- and it is matched in full or not at all. Four of the five are read
off the Claim and the Evidence row. The fifth, the RESOURCE, is not a proposition fact:
ADR-035 and ADR-036 keep it out of proposition identity for every kind that converges,
so a diagnostic reading `claims.proposition_facts` finds it absent for Wikimedia and
present for TED, and concludes that the lineage cannot say what it measured.

The lineage can. Every RawRecord carries `provenance.resource_id`, written at acquisition
from the AUTHORIZED dataset -- four gates before any socket -- and `nlp.signal_inputs`
names the RawRecords a Signal was derived from. So the resource a measurement came from
is a persisted historical fact reached by a join, and this script asks that join for
every Evidence row without naming any source.

    RULE  scope.resource_id = the ONE distinct raw_records.provenance.resource_id
          reachable through evidence -> signal -> signal_inputs -> raw_records;
          zero or more than one distinct value  ->  no scope, no resolution.

It runs the REAL resolver twice per row -- once the way Mission 1.76 read the corpus
(proposition facts) and once through lineage -- so the difference is measured rather than
argued. Then the REAL aggregator, read-only, over every Claim whose rows resolve.

**UNCALIBRATED. DIAGNOSTIC ONLY. NOT AN OPPORTUNITY SCORE.** Nothing is written to the
database: no reliability on an Evidence row, no assessment, no independence group, no
score, no Opportunity revision. The counters are measured before and after to prove it.

    uv run python infrastructure/scripts/report_reliability_resource_binding.py

Reads a deployment, so it is an OPERATOR gate and not a CI gate (Mission 1.37 §22).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in (
    "claim-model",
    "evidence-reliability",
    "evidence-aggregation",
    "opportunity-engine",
    "contracts",
):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))

OUT = ROOT / "docs" / "data" / "reliability-resource-binding-diagnostic-v1.json"

ARTIFACT_VERSION = "reliability-resource-binding-diagnostic@1.0.0"
BANNER = ("UNCALIBRATED", "DIAGNOSTIC_ONLY", "NOT_AN_OPPORTUNITY_SCORE")

# One row per Evidence. The resource comes from the RawRecords the Signal was derived
# from, and from nowhere else; `array_agg(DISTINCT ...)` keeps every distinct value so
# that ambiguity is visible rather than collapsed by a LIMIT 1.
ROWS = """
    SELECT e.id AS evidence_id, e.claim_id, e.signal_id, e.source_id, e.direction,
           e.relevance, e.directness, e.extraction_confidence, e.observation_category,
           e.independence_state, e.independence_group_id, e.reliability AS supplied,
           e.observed_at, e.extraction_method, e.evidence_level,
           c.claim_type, c.proposition_facts, c.temporality, c.lifecycle, c.origin,
           c.proposition_facts ->> 'resource_id' AS claim_facts_resource_id,
           s.signal_type_id,
           (SELECT array_agg(DISTINCT si.record_kind_id) FROM nlp.signal_inputs si
             WHERE si.signal_id = e.signal_id) AS record_kinds,
           (SELECT array_agg(DISTINCT r.provenance ->> 'resource_id')
              FROM nlp.signal_inputs si
              JOIN acquisition.raw_records r ON r.id = si.raw_record_id
             WHERE si.signal_id = e.signal_id) AS lineage_resources,
           (SELECT array_agg(DISTINCT r.source_id)
              FROM nlp.signal_inputs si
              JOIN acquisition.raw_records r ON r.id = si.raw_record_id
             WHERE si.signal_id = e.signal_id) AS lineage_sources,
           (SELECT array_agg(DISTINCT r.collector_id || '@' || r.collector_version)
              FROM nlp.signal_inputs si
              JOIN acquisition.raw_records r ON r.id = si.raw_record_id
             WHERE si.signal_id = e.signal_id) AS lineage_collectors,
           (SELECT count(*) FROM nlp.signal_inputs si
             WHERE si.signal_id = e.signal_id) AS input_rows,
           EXISTS (SELECT 1 FROM research.opportunity_hypothesis_evidence oe
                    WHERE oe.evidence_id = e.id) AS on_opportunity
      FROM scoring.evidence e
      JOIN research.claims c ON c.id = e.claim_id
      LEFT JOIN nlp.signals s ON s.id = e.signal_id
     ORDER BY e.source_id, c.proposition_facts ->> 'proposition', e.claim_id, e.id
"""

ASSESSMENTS = """
    SELECT id, version, source_id, resource_id, record_kind_id, claim_type,
           proposition_kind, reliability, origin, reviewed_by, reviewed_at,
           stated_limitation, review_rubric_id, review_rubric_version, created_at
      FROM epistemic.reliability_assessments
     WHERE superseded_at IS NULL
     ORDER BY created_at
"""

BASIS = """
    SELECT basis_type, document_title, summarized_finding, document_url,
           section_reference, retrieved_at
      FROM epistemic.reliability_assessment_basis
     WHERE assessment_id = %s
"""

# Per-layer identifier persistence, measured rather than described.
LAYERS = (
    (
        "scoring.evidence",
        "source_id",
        "SELECT count(*) FROM scoring.evidence WHERE source_id IS NOT NULL",
        "SELECT count(*) FROM scoring.evidence",
    ),
    (
        "research.claims",
        "proposition_facts.resource_id",
        "SELECT count(*) FROM research.claims WHERE proposition_facts ? 'resource_id'",
        "SELECT count(*) FROM research.claims",
    ),
    (
        "nlp.signals",
        "scope.resource_id",
        "SELECT count(*) FROM nlp.signals WHERE scope ? 'resource_id'",
        "SELECT count(*) FROM nlp.signals",
    ),
    (
        "nlp.signal_inputs",
        "record_kind_id",
        "SELECT count(*) FROM nlp.signal_inputs WHERE record_kind_id IS NOT NULL",
        "SELECT count(*) FROM nlp.signal_inputs",
    ),
    (
        "nlp.signal_inputs",
        "raw_record_id",
        "SELECT count(*) FROM nlp.signal_inputs WHERE raw_record_id IS NOT NULL",
        "SELECT count(*) FROM nlp.signal_inputs",
    ),
    (
        "acquisition.normalized_records",
        "provenance.resource_id",
        "SELECT count(*) FROM acquisition.normalized_records WHERE provenance ? 'resource_id'",
        "SELECT count(*) FROM acquisition.normalized_records",
    ),
    (
        "acquisition.normalized_records",
        "collector_id",
        "SELECT count(*) FROM acquisition.normalized_records WHERE collector_id IS NOT NULL",
        "SELECT count(*) FROM acquisition.normalized_records",
    ),
    (
        "acquisition.raw_records",
        "provenance.resource_id",
        "SELECT count(*) FROM acquisition.raw_records WHERE provenance ? 'resource_id'",
        "SELECT count(*) FROM acquisition.raw_records",
    ),
    (
        "acquisition.raw_records",
        "collector_id",
        "SELECT count(*) FROM acquisition.raw_records WHERE collector_id IS NOT NULL",
        "SELECT count(*) FROM acquisition.raw_records",
    ),
    (
        "acquisition.raw_records",
        "collector_version",
        "SELECT count(*) FROM acquisition.raw_records WHERE collector_version IS NOT NULL",
        "SELECT count(*) FROM acquisition.raw_records",
    ),
    (
        "acquisition.raw_records",
        "provenance.authorization_issued_at",
        "SELECT count(*) FROM acquisition.raw_records WHERE provenance ? 'authorization_issued_at'",
        "SELECT count(*) FROM acquisition.raw_records",
    ),
)

COUNTERS = {
    "raw_records": "SELECT count(*) FROM acquisition.raw_records",
    "normalized_records": "SELECT count(*) FROM acquisition.normalized_records",
    "signals": "SELECT count(*) FROM nlp.signals",
    "claims": "SELECT count(*) FROM research.claims",
    "claim_revisions": "SELECT count(*) FROM research.claim_revisions",
    "evidence": "SELECT count(*) FROM scoring.evidence",
    "evidence_reliability_written": "SELECT count(*) FROM scoring.evidence WHERE reliability IS NOT NULL",
    "reliability_assessments": "SELECT count(*) FROM epistemic.reliability_assessments",
    "reliability_assessment_basis_rows": "SELECT count(*) FROM epistemic.reliability_assessment_basis",
    "independence_groups": "SELECT count(DISTINCT independence_group_id) FROM scoring.evidence WHERE independence_group_id IS NOT NULL",
    "opportunities": "SELECT count(*) FROM research.opportunities",
    "opportunity_revisions": "SELECT count(*) FROM research.opportunity_hypothesis_revisions",
    "opportunity_evidence_links": "SELECT count(*) FROM research.opportunity_hypothesis_evidence",
    "threshold_registrations": "SELECT count(*) FROM research.threshold_registrations",
    "claim_derivations": "SELECT count(*) FROM research.claim_derivations",
    "proposition_evaluation_refusals": "SELECT count(*) FROM research.proposition_evaluation_refusals",
    "embeddings": "SELECT count(*) FROM nlp.embedding_provenance",
}


def _count_everything(cur) -> dict[str, object]:
    out: dict[str, object] = {}
    for name, query in COUNTERS.items():
        cur.execute(query)
        out[name] = cur.fetchone()[0]
    cur.execute("SELECT to_regclass('scoring.scores') IS NOT NULL")
    out["scores_table"] = "PRESENT" if cur.fetchone()[0] else "ABSENT"
    return out


def _fetch(cur, query, params=()):
    cur.execute(query, params)
    columns = [d[0] for d in cur.description]
    return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def _json(value):
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if hasattr(value, "hex"):  # UUID
        return str(value)
    return value


def _scope_from_lineage(row, scope_from_lineage, claim_type):
    """The one rule, stated once in `sros_evidence_reliability.lineage`."""
    built = scope_from_lineage(
        source_id=row["source_id"],
        claim_type=claim_type(row["claim_type"]),
        proposition_facts=row["proposition_facts"] or {},
        lineage_resource_ids=row["lineage_resources"] or [],
        lineage_record_kind_ids=row["record_kinds"] or [],
    )
    return built.scope, built.basis


def _scope_from_claim_facts(row, scope_type, claim_type):
    """How Mission 1.76 read the corpus: the resource is a proposition fact, or nothing."""
    resource = row["claim_facts_resource_id"]
    kinds = sorted(k for k in (row["record_kinds"] or []) if k)
    if not resource or len(kinds) != 1:
        return None
    facts = row["proposition_facts"] or {}
    return scope_type(
        source_id=row["source_id"],
        resource_id=resource,
        record_kind_id=kinds[0],
        claim_type=claim_type(row["claim_type"]),
        proposition_kind=facts.get("proposition", ""),
    )


def _resolution(scope, live, supplied, resolve_reliability):
    result = resolve_reliability(scope=scope, candidates=live, supplied=supplied)
    binding = result.binding
    entry = {
        "outcome": result.outcome.value,
        "reliability": result.reliability,
        "assessment_id": binding.assessment_id if binding else None,
        "assessment_version": binding.version if binding else None,
        "origin": binding.origin.value if binding else None,
    }
    if binding:
        matched = next(a for a in live if a.id == binding.assessment_id)
        entry["assessment_scope"] = {
            "source_id": matched.scope.source_id,
            "resource_id": matched.scope.resource_id,
            "record_kind_id": matched.scope.record_kind_id,
            "claim_type": matched.scope.claim_type.value,
            "proposition_kind": matched.scope.proposition_kind,
        }
    return result, entry


def main() -> int:
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
        BASIS_EXPLICIT,
        ReliabilityAssessment,
        ReliabilityBasis,
        ReliabilityScope,
        resolve_reliability,
        scope_from_lineage,
    )
    from sros_opportunity import EvidenceFacets, IndependenceState, ReliabilityStatus

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        before = _count_everything(cur)
        rows = _fetch(cur, ROWS)
        raw_assessments = _fetch(cur, ASSESSMENTS)
        for entry in raw_assessments:
            entry["_basis"] = _fetch(cur, BASIS, (entry["id"],))
        layers = []
        for table, identifier, present_query, total_query in LAYERS:
            cur.execute(present_query)
            present = cur.fetchone()[0]
            cur.execute(total_query)
            total = cur.fetchone()[0]
            layers.append(
                {
                    "table": table,
                    "identifier": identifier,
                    "rows_carrying_it": present,
                    "rows": total,
                }
            )
        cur.execute(
            "SELECT source_id, provenance ->> 'resource_id' AS resource_id, collector_id,"
            " collector_version, count(*) AS records"
            " FROM acquisition.raw_records GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4"
        )
        raw_resources = [
            dict(zip([d[0] for d in cur.description], r, strict=True)) for r in cur.fetchall()
        ]
        revisions = _fetch(
            cur,
            "SELECT id, opportunity_id, revision, created_at, epistemic_limitations"
            " FROM research.opportunity_hypothesis_revisions ORDER BY created_at",
        )
        after = _count_everything(cur)

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
        for a in raw_assessments
    ]

    # ------------------------------------------------------------ per Evidence row
    out_rows = []
    for row in rows:
        facts = row["proposition_facts"] or {}
        supplied = float(row["supplied"]) if row["supplied"] is not None else None
        claim_scope = _scope_from_claim_facts(row, ReliabilityScope, ClaimType)
        lineage_scope, basis = _scope_from_lineage(row, scope_from_lineage, ClaimType)
        _, via_claim = _resolution(claim_scope, live, supplied, resolve_reliability)
        lineage_result, via_lineage = _resolution(
            lineage_scope, live, supplied, resolve_reliability
        )
        row["_reliability"] = lineage_result.reliability

        # §15. The existing repository path decides scorability from the resolved value.
        facets = EvidenceFacets(
            evidence_id=str(row["evidence_id"]),
            claim_id=str(row["claim_id"]),
            source_id=row["source_id"],
            source_family="(not consulted)",
            use_profile_id="(not consulted)",
            extraction_method=row["extraction_method"],
            claim_type=row["claim_type"],
            claim_lifecycle=row["lifecycle"],
            claim_temporality=row["temporality"],
            claim_origin=row["origin"],
            direction=row["direction"],
            observation_category=row["observation_category"],
            evidence_level=int(row["evidence_level"]),
            relevance=row["relevance"],
            directness=row["directness"],
            extraction_confidence=row["extraction_confidence"],
            reliability=lineage_result.reliability,
            reliability_status=(
                ReliabilityStatus.RESOLVED
                if lineage_result.reliability is not None
                else ReliabilityStatus(lineage_result.outcome.value)
                if lineage_result.outcome.value in ReliabilityStatus.__members__
                else ReliabilityStatus.NO_APPLICABLE_ASSESSMENT
            ),
            independence_state=IndependenceState(row["independence_state"]),
            independence_group_id=(
                str(row["independence_group_id"]) if row["independence_group_id"] else None
            ),
            observed_at=row["observed_at"].isoformat() if row["observed_at"] else None,
            signal_type_id=row["signal_type_id"],
            dimensions=frozenset(),
            dimension_bound="",
        )
        out_rows.append(
            {
                "evidence_id": str(row["evidence_id"]),
                "claim_id": str(row["claim_id"]),
                "signal_id": str(row["signal_id"]),
                "source_id": row["source_id"],
                "on_opportunity": bool(row["on_opportunity"]),
                "claim_type": row["claim_type"],
                "proposition_kind": facts.get("proposition", ""),
                "evidence_reliability_column": supplied,
                "lineage": {
                    "signal_input_rows": int(row["input_rows"]),
                    "sources": sorted(row["lineage_sources"] or []),
                    "collectors": sorted(row["lineage_collectors"] or []),
                    "record_kinds": sorted(row["record_kinds"] or []),
                    "resources": sorted(r for r in (row["lineage_resources"] or []) if r),
                    "distinct_resource_count": len(
                        {r for r in (row["lineage_resources"] or []) if r}
                    ),
                },
                "claim_facts_resource_id": row["claim_facts_resource_id"],
                "resource_basis": basis,
                "scope": (
                    None
                    if lineage_scope is None
                    else {
                        "source_id": lineage_scope.source_id,
                        "resource_id": lineage_scope.resource_id,
                        "record_kind_id": lineage_scope.record_kind_id,
                        "claim_type": lineage_scope.claim_type.value,
                        "proposition_kind": lineage_scope.proposition_kind,
                    }
                ),
                "resolution_via_claim_facts": via_claim,
                "resolution_via_lineage": via_lineage,
                "scorable_via_lineage": facets.is_scorable,
                "missing_factors_via_lineage": list(facets.missing_factors),
            }
        )

    # ------------------------------------------------------- per scope, and totals
    by_scope: dict[tuple, dict] = {}
    for entry in out_rows:
        key = (entry["source_id"], entry["claim_type"], entry["proposition_kind"])
        bucket = by_scope.setdefault(
            key,
            {
                "source_id": key[0],
                "claim_type": key[1],
                "proposition_kind": key[2],
                "rows": 0,
                "on_opportunity_rows": 0,
                "resolved_via_claim_facts": 0,
                "resolved_via_lineage": 0,
                "reliability_via_lineage": set(),
                "assessment_ids_via_lineage": set(),
                "resource_bases": set(),
            },
        )
        bucket["rows"] += 1
        bucket["on_opportunity_rows"] += int(entry["on_opportunity"])
        bucket["resolved_via_claim_facts"] += int(
            entry["resolution_via_claim_facts"]["outcome"] == "RESOLVED"
        )
        bucket["resolved_via_lineage"] += int(
            entry["resolution_via_lineage"]["outcome"] == "RESOLVED"
        )
        if entry["resolution_via_lineage"]["reliability"] is not None:
            bucket["reliability_via_lineage"].add(entry["resolution_via_lineage"]["reliability"])
            bucket["assessment_ids_via_lineage"].add(
                entry["resolution_via_lineage"]["assessment_id"]
            )
        bucket["resource_bases"].add(entry["resource_basis"])
    scopes = []
    for bucket in by_scope.values():
        bucket["reliability_via_lineage"] = sorted(bucket["reliability_via_lineage"])
        bucket["assessment_ids_via_lineage"] = sorted(bucket["assessment_ids_via_lineage"])
        bucket["resource_bases"] = sorted(bucket["resource_bases"])
        scopes.append(bucket)

    def _n(predicate):
        return sum(1 for e in out_rows if predicate(e))

    measurements = {
        "evidence_rows": len(out_rows),
        "opportunity_linked_rows": _n(lambda e: e["on_opportunity"]),
        "rows_with_exactly_one_lineage_resource": _n(
            lambda e: e["lineage"]["distinct_resource_count"] == 1
        ),
        "rows_with_ambiguous_lineage_resource": _n(
            lambda e: e["lineage"]["distinct_resource_count"] > 1
        ),
        "rows_with_no_lineage_resource": _n(lambda e: e["lineage"]["distinct_resource_count"] == 0),
        "rows_with_scope": _n(lambda e: e["scope"] is not None),
        "resolved_via_claim_facts": _n(
            lambda e: e["resolution_via_claim_facts"]["outcome"] == "RESOLVED"
        ),
        "resolved_via_lineage": _n(lambda e: e["resolution_via_lineage"]["outcome"] == "RESOLVED"),
        "opportunity_linked_resolved_via_claim_facts": _n(
            lambda e: (
                e["on_opportunity"] and e["resolution_via_claim_facts"]["outcome"] == "RESOLVED"
            )
        ),
        "opportunity_linked_resolved_via_lineage": _n(
            lambda e: e["on_opportunity"] and e["resolution_via_lineage"]["outcome"] == "RESOLVED"
        ),
        "scorable_via_stored_column": _n(lambda e: e["evidence_reliability_column"] is not None),
        "scorable_via_lineage": _n(lambda e: e["scorable_via_lineage"]),
        "opportunity_linked_scorable_via_stored_column": _n(
            lambda e: e["on_opportunity"] and e["evidence_reliability_column"] is not None
        ),
        "opportunity_linked_scorable_via_lineage": _n(
            lambda e: e["on_opportunity"] and e["scorable_via_lineage"]
        ),
        "resolved_rows_whose_resource_basis_is_explicit": _n(
            lambda e: (
                e["resolution_via_lineage"]["outcome"] == "RESOLVED"
                and e["resource_basis"] == BASIS_EXPLICIT
            )
        ),
    }

    # -------------------------------------------------- the real aggregator, read-only
    by_claim: dict[str, list[dict]] = {}
    for row in rows:
        if row["_reliability"] is not None:
            by_claim.setdefault(str(row["claim_id"]), []).append(row)
    aggregation = []
    for claim_id, members in sorted(by_claim.items(), key=lambda kv: (-len(kv[1]), kv[0])):
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
        facts = members[0]["proposition_facts"] or {}
        aggregation.append(
            {
                "claim_id": claim_id,
                "source_id": members[0]["source_id"],
                "proposition_kind": facts.get("proposition", ""),
                "on_opportunity": any(bool(m["on_opportunity"]) for m in members),
                "raw_evidence_count": len(members),
                "scorable_evidence_count": result.scorable_evidence_count,
                "aggregation_status": result.status.value,
                "support_strength": result.masses.support_strength,
                "contradiction_strength": result.masses.contradiction_strength,
                "uncertainty_mass": result.masses.uncertainty_mass,
                "reliability_pass_through": pass_through,
                "identical_to_reliability_pass_through": (
                    pass_through is not None
                    and abs(result.masses.support_strength - pass_through) <= 1e-9
                ),
                "support_group_count": result.support_group_count,
                "contradiction_group_count": result.contradiction_group_count,
                "max_members_received": max(
                    (len(g.member_evidence_ids) for g in result.groups.support), default=0
                ),
                "established_independence_groups": sum(
                    1 for g in result.groups.support if g.kind.value == "INDEPENDENT"
                ),
                "limiting_components": sorted(
                    {c.limiting_component for c in result.contributions if c.limiting_component}
                ),
                "evidence_level": result.level.level,
            }
        )

    # -------------------------------------------- the canonical limitation, read only
    limitation = None
    if revisions:
        first = revisions[0]
        later = [
            {
                "assessment_id": str(a["id"]),
                "source_id": a["source_id"],
                "proposition_kind": a["proposition_kind"],
                "reliability": float(a["reliability"]),
                "created_at": a["created_at"].isoformat(),
            }
            for a in raw_assessments
            if a["created_at"] > first["created_at"]
        ]
        limitation = {
            "representation": "CANONICAL_ROW research.opportunity_hypothesis_revisions",
            "revision_id": str(first["id"]),
            "opportunity_id": str(first["opportunity_id"]),
            "revision": first["revision"],
            "created_at": first["created_at"].isoformat(),
            "limitation_text": (first["epistemic_limitations"] or [None])[0],
            "assessments_created_after_the_revision": later,
            "opportunity_linked_rows_resolving_via_lineage": measurements[
                "opportunity_linked_resolved_via_lineage"
            ],
            "revisions_before": before["opportunity_revisions"],
            "revisions_after": after["opportunity_revisions"],
        }

    report = {
        "$comment": (
            "Mission 1.77. Which registered resource produced each held measurement, read "
            "from the RawRecords a Signal was derived from, and the REAL resolver run over "
            "the resulting five-part scope. Nothing is written back."
        ),
        "$banner": list(BANNER),
        "artifact_version": ARTIFACT_VERSION,
        "generated_by": "mission-1.77",
        "measured_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "scope_construction": {
            "source_id": "scoring.evidence.source_id",
            "resource_id": (
                "the ONE distinct acquisition.raw_records.provenance.resource_id reachable "
                "through nlp.signal_inputs.raw_record_id for the Evidence row's Signal"
            ),
            "record_kind_id": "the ONE distinct nlp.signal_inputs.record_kind_id for the Signal",
            "claim_type": "research.claims.claim_type",
            "proposition_kind": "research.claims.proposition_facts.proposition",
            "ambiguity_rule": (
                "zero distinct resources -> NONE_LINEAGE_ABSENT; more than one distinct "
                "resource or record kind -> NONE_LINEAGE_AMBIGUOUS; either way no scope is "
                "built and the resolver reports that the row cannot state its scope"
            ),
            "reads_current_collector_or_registry_configuration": False,
            "source_specific_branches": 0,
            "resource_bases_admitted": [BASIS_EXPLICIT],
        },
        "lineage_audit": {
            "layers": layers,
            "raw_record_resources": raw_resources,
        },
        "current_assessments": [
            {
                "id": str(a["id"]),
                "version": int(a["version"]),
                "scope": {
                    "source_id": a["source_id"],
                    "resource_id": a["resource_id"],
                    "record_kind_id": a["record_kind_id"],
                    "claim_type": a["claim_type"],
                    "proposition_kind": a["proposition_kind"],
                },
                "reliability": float(a["reliability"]),
                "origin": a["origin"],
                "reviewed_by": a["reviewed_by"],
                "created_at": a["created_at"].isoformat(),
                "basis_rows": len(a["_basis"]),
            }
            for a in raw_assessments
        ],
        "measurements": measurements,
        "scopes": scopes,
        "rows": out_rows,
        "aggregation_diagnostic": {
            "$banner": list(BANNER),
            "profile": "REFERENCE_PROFILE_V1",
            "calibration": REFERENCE_PROFILE_V1.status.value,
            "claims": aggregation,
            "claims_where_full_aggregator_differs_from_pass_through": sum(
                1 for c in aggregation if not c["identical_to_reliability_pass_through"]
            ),
            "claims_with_established_independence": sum(
                1 for c in aggregation if c["established_independence_groups"] > 0
            ),
            "persisted": False,
        },
        "opportunity_limitation": limitation,
        "counters": {"before": before, "after": after},
    }

    OUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=_json) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote     {OUT.relative_to(ROOT)}")
    for key in (
        "evidence_rows",
        "resolved_via_claim_facts",
        "resolved_via_lineage",
        "opportunity_linked_resolved_via_lineage",
        "scorable_via_lineage",
    ):
        print(f"{key:48} {measurements[key]}")
    print(
        f"{'assessments before/after':48} {before['reliability_assessments']}/{after['reliability_assessments']}"
    )
    print(
        f"{'evidence.reliability written before/after':48} {before['evidence_reliability_written']}/{after['evidence_reliability_written']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
