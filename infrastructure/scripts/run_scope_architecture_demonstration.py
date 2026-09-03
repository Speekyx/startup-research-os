"""Mission 1.34 §32. The scope architecture, exercised on the real corpus.

**No network, no model, no write.** It reads Evidence, Claims and Signal scopes
already held, resolves each row's observation scope through the reviewed
registries, and runs the §15 gate. Nothing is inserted, updated or deleted: the
only output is a JSON artifact under `docs/data/`.

Three things it must show, and the third is the point:

    A. Docker Evidence resolves to PRODUCT and is admitted as DIRECT.
    B. TED Evidence resolves to CATEGORY and stays there.
    C. Offering TED to the Docker Opportunity with no reviewed relation is
       REFUSED, deterministically, by name.

Usage:

    python infrastructure/scripts/run_scope_architecture_demonstration.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "opportunity-engine" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

DOCS = ROOT / "docs" / "data"
SUBJECT_REGISTRY = DOCS / "canonical-subject-registry-v1.json"
SCOPE_RULES = DOCS / "observation-scope-rules-v1.json"
SCOPE_RELATIONS = DOCS / "scope-relation-registry-v1.json"
OUT = DOCS / "scope-architecture-demonstration-v1.json"

QUERY = """
    SELECT e.id, e.claim_id, e.source_id, e.direction, e.observation_category,
           e.independence_state, e.independence_group_id, e.evidence_level,
           e.reliability, e.relevance, e.directness, e.extraction_confidence,
           e.extraction_method, e.observed_at,
           c.claim_type, c.lifecycle, c.temporality, c.origin,
           s.signal_type_id, s.scope
      FROM scoring.evidence e
      JOIN research.claims c ON c.id = e.claim_id
      LEFT JOIN nlp.signals s ON s.id = e.signal_id
     ORDER BY e.id
"""


def _rows() -> list[dict[str, object]]:
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(QUERY)
        columns = [d[0] for d in (cur.description or [])]
        return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def main() -> int:
    from sros_opportunity import (
        EvidenceFacets,
        IndependenceState,
        ReliabilityStatus,
        admit_evidence,
        build_scoped_packet,
        load_scope_relations,
        load_scope_rules,
        load_subject_registry,
        map_signal_type,
        opportunity_subject_scope,
        resolve_observation_scope,
    )

    registry = load_subject_registry(SUBJECT_REGISTRY)
    rules = load_scope_rules(SCOPE_RULES)
    relations = load_scope_relations(SCOPE_RELATIONS)

    rows = _rows()
    facets_by_id: dict[str, EvidenceFacets] = {}
    scopes: dict[str, object] = {}
    by_scope: dict[str, list[str]] = {}

    for row in rows:
        mapping = map_signal_type(row["signal_type_id"])  # type: ignore[arg-type]
        facets = EvidenceFacets(
            evidence_id=str(row["id"]),
            claim_id=str(row["claim_id"]),
            source_id=str(row["source_id"]),
            source_family="",
            use_profile_id="local-private-research-v1",
            extraction_method=row["extraction_method"],  # type: ignore[arg-type]
            claim_type=str(row["claim_type"]),
            claim_lifecycle=str(row["lifecycle"]),
            claim_temporality=str(row["temporality"]),
            claim_origin=str(row["origin"]),
            direction=str(row["direction"]),
            observation_category=str(row["observation_category"]),
            evidence_level=int(row["evidence_level"]),  # type: ignore[arg-type]
            relevance=row["relevance"],  # type: ignore[arg-type]
            directness=row["directness"],  # type: ignore[arg-type]
            extraction_confidence=row["extraction_confidence"],  # type: ignore[arg-type]
            reliability=row["reliability"],  # type: ignore[arg-type]
            reliability_status=(
                ReliabilityStatus.RESOLVED
                if row["reliability"] is not None
                else ReliabilityStatus.NO_APPLICABLE_ASSESSMENT
            ),
            independence_state=IndependenceState(str(row["independence_state"])),
            independence_group_id=(
                str(row["independence_group_id"]) if row["independence_group_id"] else None
            ),
            observed_at=str(row["observed_at"]) if row["observed_at"] else None,
            signal_type_id=row["signal_type_id"],  # type: ignore[arg-type]
            dimensions=mapping.dimensions if mapping else frozenset(),
            dimension_bound=mapping.rationale if mapping else "",
        )
        facets_by_id[facets.evidence_id] = facets
        scope = resolve_observation_scope(
            facets.source_id,
            facets.signal_type_id,
            row["scope"],  # type: ignore[arg-type]
            registry,
            rules,
        )
        scopes[facets.evidence_id] = scope
        by_scope.setdefault(scope.scope_id, []).append(facets.evidence_id)

    docker_scope = opportunity_subject_scope("docker", registry)

    # --- A + C: every row offered to the Docker Opportunity ------------------
    admitted, refusals = [], []
    for evidence_id, facets in sorted(facets_by_id.items()):
        scope = scopes[evidence_id]
        decision = admit_evidence(
            facets,
            scope,  # type: ignore[arg-type]
            docker_scope,
            relations,
            governance_permits_processing=True,
        )
        if decision.ok and decision.admitted is not None:
            admitted.append(decision.admitted)
        else:
            refusals.append((evidence_id, decision.refusal_reason or "", decision.detail))

    packet = build_scoped_packet(docker_scope, "subject:docker", tuple(admitted), tuple(refusals))

    # --- B: TED, described at its own scope, attached to nothing -------------
    ted_ids = [eid for eid, f in facets_by_id.items() if f.source_id == "ted-eu"]
    ted = [
        {
            "evidence_id": eid,
            "scope_id": scopes[eid].scope_id,  # type: ignore[union-attr]
            "scope_type": (
                scopes[eid].scope_type.value  # type: ignore[union-attr]
                if scopes[eid].scope_type  # type: ignore[union-attr]
                else None
            ),
            "origin": (
                scopes[eid].origin.value  # type: ignore[union-attr]
                if scopes[eid].origin  # type: ignore[union-attr]
                else None
            ),
            "dimensions": sorted(d.value for d in facets_by_id[eid].dimensions),
            "attached_to_docker": eid in packet.direct_evidence_ids
            or eid in packet.contextual_evidence_ids,
            "refused_because": next((reason for rid, reason, _ in refusals if rid == eid), None),
        }
        for eid in sorted(ted_ids)
    ]

    resolved = {
        scope_id: {
            "scope_type": (
                scopes[ids[0]].scope_type.value  # type: ignore[union-attr]
                if scopes[ids[0]].scope_type  # type: ignore[union-attr]
                else None
            ),
            "status": scopes[ids[0]].status.value,  # type: ignore[union-attr]
            "origin": (
                scopes[ids[0]].origin.value  # type: ignore[union-attr]
                if scopes[ids[0]].origin  # type: ignore[union-attr]
                else None
            ),
            "evidence_rows": len(ids),
        }
        for scope_id, ids in sorted(by_scope.items())
    }

    document = {
        "$comment": (
            "Mission 1.34 §32. The scope architecture exercised on the REAL corpus, "
            "with no network call, no model call and no write of any kind. It shows "
            "that Docker Evidence resolves to PRODUCT and is admitted as DIRECT, that "
            "TED Evidence resolves to CATEGORY and stays there, and that offering TED "
            "to the Docker Opportunity is REFUSED because no reviewed relation "
            "connects the two scopes. The refusal is the demonstration."
        ),
        "artifact_version": "scope-architecture-demonstration@1.0.0",
        "generated_by": "mission-1.34",
        "procedures": {
            **packet.procedures,
            "subject_registry": registry.registry_version,
            "scope_rules": rules.registry_version,
            "scope_relations": relations.registry_version,
        },
        "totals": {
            "evidence_rows_inspected": len(rows),
            "scopes_resolved": sum(
                1
                for s in scopes.values()
                if s.resolved  # type: ignore[union-attr]
            ),
            "scopes_undetermined": sum(
                1
                for s in scopes.values()
                if not s.resolved  # type: ignore[union-attr]
            ),
            "reviewed_scope_relations": len(relations.relations),
            "model_calls": 0,
            "network_calls": 0,
            "rows_written": 0,
        },
        "scopes_by_id": resolved,
        "docker_packet": {
            "packet_id": packet.packet_id,
            "opportunity_scope_id": packet.opportunity_scope.scope_id,
            "opportunity_scope_type": (
                packet.opportunity_scope.scope_type.value
                if packet.opportunity_scope.scope_type
                else None
            ),
            "direct_evidence": len(packet.direct_evidence),
            "contextual_evidence": len(packet.contextual_evidence),
            "scope_relations_used": len(packet.scope_relations),
            "direct_dimensions": sorted(d.value for d in packet.direct_dimensions),
            "direct_counting_dimensions": sorted(
                d.value for d in packet.direct_counting_dimensions
            ),
            "contextual_dimensions_by_scope": {
                scope_id: sorted({s.dimension.value for s in scoped})
                for scope_id, scoped in packet.contextual_dimensions_by_scope.items()
            },
            "role_counts": packet.role_counts,
            "limitations": list(packet.limitations()),
        },
        "ted_evidence": ted,
        "refusal_counts": {
            reason: sum(1 for _, r, _ in refusals if r == reason)
            for reason in sorted({r for _, r, _ in refusals})
        },
        "refusals": [
            {"evidence_id": eid, "reason": reason, "detail": detail}
            for eid, reason, detail in sorted(refusals)
        ],
    }

    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"evidence rows inspected      : {len(rows)}")
    print(f"scopes resolved              : {document['totals']['scopes_resolved']}")
    print(f"scopes UNDETERMINED          : {document['totals']['scopes_undetermined']}")
    print(f"reviewed scope relations     : {len(relations.relations)}")
    print()
    for scope_id, info in resolved.items():
        print(f"  {info['scope_type'] or 'UNDETERMINED':13} {scope_id:52} {info['evidence_rows']}")
    print()
    print(f"docker packet direct rows    : {len(packet.direct_evidence)}")
    print(f"docker packet contextual rows: {len(packet.contextual_evidence)}")
    print(
        f"direct counting dimensions   : {sorted(d.value for d in packet.direct_counting_dimensions)}"
    )
    print(f"refusals                     : {document['refusal_counts']}")
    print()
    for row in ted:
        print(
            f"  TED {row['evidence_id'][:8]} scope={row['scope_type']} "
            f"attached_to_docker={row['attached_to_docker']} "
            f"refused={row['refused_because']}"
        )
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
