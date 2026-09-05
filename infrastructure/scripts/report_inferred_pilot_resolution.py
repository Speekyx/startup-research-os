"""What the Mission 1.56 pilot rows mean downstream. READ-ONLY.

    uv run python infrastructure/scripts/report_inferred_pilot_resolution.py

`run_inferred_pilot.py` records what was WRITTEN. This records what the written
rows RESOLVE TO, which is a different question and the one a later mission will
ask: does the new INFERRED scope reach any reviewed reliability, and can the
aggregator produce a number for a Claim whose only Evidence contradicts it.

Every value comes from the REAL resolver and the REAL aggregator over the REAL
rows. Nothing is persisted -- opening a write transaction here would make a
diagnostic capable of changing what it is diagnosing.

The interesting result is a negative one, and it is what the manifest predicted:
the reviewed Wikimedia `0.65` shares source, resource and record kind with the
new scope and differs on `claim_type` AND `proposition_kind`, so it does not
reach it. The Evidence is NON_SCORABLE, which is correct rather than a gap.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
EXECUTION = DATA / "first-deterministic-inferred-pilot-v1.json"
RESOLUTION = DATA / "first-deterministic-inferred-pilot-resolution-v1.json"

DEFAULT_DATABASE_URL = "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros"

# The scope the new rows sit in. `resource_id` is not on `scoring.evidence`, so
# it is read back through the Signal's contributing records the same way the
# pilot runner read it.
SCOPE_QUERY = """
SELECT e.source_id,
       min(nr.provenance -> 'acquisition' ->> 'resource_id'),
       min(nr.record_kind_id),
       cl.claim_type,
       cl.proposition_facts ->> 'proposition'
  FROM scoring.evidence e
  JOIN research.claims cl ON cl.id = e.claim_id
  JOIN nlp.signal_inputs si ON si.signal_id = e.signal_id
  JOIN acquisition.normalized_records nr ON nr.id = si.normalized_record_id
 WHERE cl.id = %s
 GROUP BY e.source_id, cl.claim_type, cl.proposition_facts ->> 'proposition'
"""


def _connect(url: str):
    import psycopg

    conn = psycopg.connect(url)
    workspace = conn.execute("SELECT id::text FROM core.workspaces WHERE slug = 'dev'").fetchone()[
        0
    ]
    conn.execute("SELECT set_config('app.workspace_id', %s, false)", (workspace,))
    return conn


def _assessments(conn: Any) -> list[Any]:
    """Every CURRENT assessment, with its real basis rows. A superseded one is
    excluded because the resolver excludes it, not because it is inconvenient."""
    from sros_contracts import ClaimType
    from sros_evidence_reliability.model import (
        ReliabilityAssessment,
        ReliabilityAssessmentOrigin,
        ReliabilityBasis,
        ReliabilityBasisType,
        ReliabilityScope,
    )

    basis: dict[str, list[Any]] = {}
    for row in conn.execute(
        """SELECT assessment_id::text, basis_type, document_title, document_url,
                  section_reference, summarized_finding, excerpt, retrieved_at
             FROM epistemic.reliability_assessment_basis"""
    ).fetchall():
        basis.setdefault(row[0], []).append(
            ReliabilityBasis(
                basis_type=ReliabilityBasisType(row[1]),
                document_title=row[2],
                document_url=row[3],
                section_reference=row[4],
                summarized_finding=row[5],
                excerpt=row[6],
                retrieved_at=row[7],
            )
        )

    return [
        ReliabilityAssessment(
            id=row[0],
            scope=ReliabilityScope(row[1], row[2], row[3], ClaimType(row[4]), row[5]),
            version=row[7],
            reliability=float(row[6]),
            origin=ReliabilityAssessmentOrigin(row[8]),
            rationale=row[9],
            stated_limitation=row[10],
            reviewed_by=row[11],
            reviewed_at=row[12],
            basis=tuple(basis.get(row[0], ())),
        )
        for row in conn.execute(
            """SELECT id::text, source_id, resource_id, record_kind_id, claim_type,
                      proposition_kind, reliability, version, origin, rationale,
                      stated_limitation, reviewed_by, reviewed_at
                 FROM epistemic.reliability_assessments
                WHERE superseded_at IS NULL
                ORDER BY source_id, proposition_kind"""
        ).fetchall()
    ]


def main() -> int:
    from sros_contracts import (
        ClaimTemporality,
        ClaimType,
        EvidenceDirection,
        EvidenceIndependenceState,
        EvidenceObservationCategory,
    )
    from sros_evidence_aggregation import REFERENCE_PROFILE_V1, EvidenceItem, aggregate
    from sros_evidence_reliability.model import ReliabilityScope, resolve_reliability

    execution = json.loads(EXECUTION.read_text(encoding="utf-8"))
    claim_id = execution["persistence"]["claim_id"]
    if claim_id is None:
        print("REFUSED  the pilot took the refusal path, so there is no Claim to resolve")
        return 1

    conn = _connect(DEFAULT_DATABASE_URL)
    try:
        source_id, resource_id, record_kind_id, claim_type, proposition_kind = conn.execute(
            SCOPE_QUERY, (claim_id,)
        ).fetchone()
        scope = ReliabilityScope(
            source_id=source_id,
            resource_id=resource_id,
            record_kind_id=record_kind_id,
            claim_type=ClaimType(claim_type),
            proposition_kind=proposition_kind,
        )
        candidates = _assessments(conn)
        resolution = resolve_reliability(scope=scope, candidates=candidates)

        rows = conn.execute(
            """SELECT id::text, direction, relevance, directness, extraction_confidence,
                      reliability, observation_category, independence_state, source_id
                 FROM scoring.evidence WHERE claim_id = %s ORDER BY id""",
            (claim_id,),
        ).fetchall()
        census = dict(
            conn.execute(
                "SELECT direction, count(*) FROM scoring.evidence GROUP BY direction ORDER BY 1"
            ).fetchall()
        )
        claims_with_contradiction = int(
            conn.execute(
                """SELECT count(DISTINCT claim_id) FROM scoring.evidence
                    WHERE direction = 'CONTRADICTS'"""
            ).fetchone()[0]
        )
        claims_with_both = int(
            conn.execute(
                """SELECT count(*) FROM (
                       SELECT claim_id FROM scoring.evidence
                        GROUP BY claim_id
                       HAVING count(*) FILTER (WHERE direction = 'SUPPORTS') > 0
                          AND count(*) FILTER (WHERE direction = 'CONTRADICTS') > 0
                   ) mixed"""
            ).fetchone()[0]
        )
    finally:
        conn.close()

    items = [
        EvidenceItem(
            evidence_id=row[0],
            direction=EvidenceDirection(row[1]),
            relevance=row[2],
            directness=row[3],
            extraction_confidence=row[4],
            # The RESOLVED value, which is None. Passing anything else here
            # would be the invented reliability the whole contract exists to
            # keep out of the arithmetic.
            reliability=resolution.reliability,
            observation_category=EvidenceObservationCategory(row[6]),
            independence_state=EvidenceIndependenceState(row[7]),
            source_id=row[8],
        )
        for row in rows
    ]
    result = aggregate(
        claim_id,
        items,
        REFERENCE_PROFILE_V1,
        temporality=ClaimTemporality.EVERGREEN,
        allow_uncalibrated=True,
    )

    near = [
        {
            "assessment_id": a.id,
            "reliability": a.reliability,
            "fields_shared": sum(
                getattr(a.scope, f) == getattr(scope, f)
                for f in (
                    "source_id",
                    "resource_id",
                    "record_kind_id",
                    "claim_type",
                    "proposition_kind",
                )
            ),
            "differs_on": [
                f
                for f in (
                    "source_id",
                    "resource_id",
                    "record_kind_id",
                    "claim_type",
                    "proposition_kind",
                )
                if getattr(a.scope, f) != getattr(scope, f)
            ],
        }
        for a in candidates
    ]

    record = {
        "mission": execution["mission"],
        "artifact": "pilot downstream resolution",
        "recorded_at": execution["recorded_at"],
        "read_only": True,
        "rows_written": 0,
        "claim_id": claim_id,
        "scope": {
            "source_id": scope.source_id,
            "resource_id": scope.resource_id,
            "record_kind_id": scope.record_kind_id,
            "claim_type": scope.claim_type.value,
            "proposition_kind": scope.proposition_kind,
        },
        "reliability": {
            "candidates_offered": len(candidates),
            "outcome": resolution.outcome.value,
            "reliability": resolution.reliability,
            "nothing_leaked": near,
            "why_it_matters": (
                "The reviewed Wikimedia 0.65 shares source, resource and record kind with "
                "this scope. It differs on claim_type AND proposition_kind, and both halves "
                "are real: a threshold proposition is a different question from a restatement "
                "of the count, and an INFERRED derivation is a different question from an "
                "OBSERVED one. Reaching for the nearest number would have answered neither."
            ),
        },
        "aggregation": {
            "profile": REFERENCE_PROFILE_V1.profile_id,
            "calibration_state": REFERENCE_PROFILE_V1.status.value,
            "raw_evidence_count": result.raw_evidence_count,
            "scorable_evidence_count": result.scorable_evidence_count,
            "status": result.status.value,
            "missing_requirements": list(result.missing_requirements),
            "non_scorable_evidence_count": result.non_scorable_evidence_count,
            "support_group_count": result.support_group_count,
            "contradiction_group_count": result.contradiction_group_count,
            "evidence_level": result.level.level,
            "evidence_score": result.evidence_score,
            "masses": result.masses.to_json() if result.masses is not None else None,
        },
        "the_direction_that_had_never_existed": {
            "evidence_by_direction": {k: int(v) for k, v in census.items()},
            "claims_carrying_a_contradiction": claims_with_contradiction,
            "claims_carrying_both_directions": claims_with_both,
            "what_this_settles": (
                "Mission 1.48 measured 57 Evidence rows and found every one of them SUPPORTS, "
                "then established why: `direction` is proposition identity at the OBSERVED "
                "layer, so an interpreter there cannot emit a contradicting row about a Claim "
                "it already restated. The INFERRED layer removes direction from identity, and "
                "this is the first CONTRADICTS row in the repository."
            ),
            "what_this_does_NOT_settle": (
                "The CONTRADICTION CASE is still unreached. Contradiction enters the "
                "arithmetic when one Claim carries evidence in both directions, and this "
                "Claim carries one row. `claims_carrying_both_directions` is the counter to "
                "watch, and it is still 0. A second witness disagreeing about the SAME "
                "threshold proposition is what would move it, and this proposition can never "
                "have one -- only Wikimedia's logs can measure requests to a Wikipedia "
                "article, which is the SOURCE_INDEPENDENCE_IS_PARTIAL limitation the operator "
                "was asked to weigh before approving."
            ),
        },
        "why_no_score_is_the_right_answer": (
            "Reliability is purpose-relative and resolved late from a reviewed assessment. "
            "None applies to this new scope, so the Evidence is NON_SCORABLE and the "
            "aggregation is UNAVAILABLE. That is the designed behaviour: the system stays "
            "capable of producing no score, which is what makes a score mean something when "
            "one appears."
        ),
    }
    RESOLUTION.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"scope            {scope.source_id} | {scope.claim_type.value} | {scope.proposition_kind}"
    )
    print(f"reliability      {resolution.outcome.value}, value {resolution.reliability}")
    print(
        f"aggregation      {result.status.value}, raw {result.raw_evidence_count}, "
        f"scorable {result.scorable_evidence_count}"
    )
    print(f"directions       {dict(census)}")
    print(f"claims with both {claims_with_both}")
    print(f"wrote            {RESOLUTION.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
