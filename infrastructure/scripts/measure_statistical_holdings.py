"""What statistical evidence this deployment actually holds (Mission 1.46 §0).

Measured from the live deployment before any candidate was considered, because
§0 requires the holdings to be known before selection rather than after: a
candidate chosen first and then justified against whatever happens to be held is
a rationalisation.

Reads only. Writes `docs/data/statistical-holdings-baseline-v1.json`.

    uv run python infrastructure/scripts/measure_statistical_holdings.py
    uv run python infrastructure/scripts/measure_statistical_holdings.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "data" / "statistical-holdings-baseline-v1.json"

STATISTICAL_SOURCES = ("world-bank", "eurostat", "fred")

HOLDINGS = """
    SELECT r.source_id,
           count(DISTINCT r.id)                                   AS raw_records,
           count(DISTINCT n.id)                                   AS normalized_records,
           count(DISTINCT n.payload ->> 'record_kind')            AS record_kinds,
           count(DISTINCT n.payload -> 'metric' ->> 'id')         AS metrics,
           count(DISTINCT n.payload -> 'geography' ->> 'source_code') AS geographies,
           count(DISTINCT n.payload -> 'period' ->> 'label')      AS periods
      FROM acquisition.raw_records r
      LEFT JOIN acquisition.normalized_records n ON n.raw_record_id = r.id
     WHERE r.source_id = ANY(%s)
     GROUP BY r.source_id
"""

OBSERVATIONS = """
    SELECT n.payload -> 'metric' ->> 'id'              AS metric_id,
           n.payload -> 'metric' ->> 'scheme'          AS metric_scheme,
           n.payload -> 'series' ->> 'resource_id'     AS resource_id,
           n.payload -> 'series' ->> 'dataset'         AS dataset,
           n.payload -> 'series' ->> 'frequency'       AS frequency,
           n.payload -> 'geography' ->> 'source_code'  AS geography_source_code,
           n.payload -> 'geography' ->> 'canonical_code' AS geography_canonical,
           n.payload -> 'geography' ->> 'kind'         AS geography_kind,
           n.payload -> 'period' ->> 'type'            AS period_type,
           n.payload -> 'period' ->> 'label'           AS period_label,
           n.payload -> 'period' ->> 'timezone_state'  AS period_timezone_state,
           n.payload -> 'observation' ->> 'unit'       AS unit,
           n.payload -> 'observation' ->> 'unit_state' AS unit_state,
           n.payload -> 'observation' ->> 'value_state' AS value_state,
           n.payload ->> 'record_kind'                 AS record_kind
      FROM acquisition.normalized_records n
      JOIN acquisition.raw_records r ON r.id = n.raw_record_id
     WHERE r.source_id = %s
     ORDER BY geography_source_code, period_label
"""

SIGNALS = """
    SELECT s.signal_type_id, s.quantity_family, s.extractor_id, s.extractor_version,
           s.magnitude, s.unit, s.direction, s.temporal_basis, count(*) OVER () AS total
      FROM nlp.signals s
     WHERE s.signal_type_id = %s
     ORDER BY s.created_at
"""

CLAIMS = """
    SELECT c.id::text, c.claim_type, c.temporality, c.proposition_facts,
           v.statement, c.current_revision
      FROM research.claims c
      JOIN research.claim_revisions v
        ON v.claim_id = c.id AND v.revision = c.current_revision
     WHERE c.proposition_facts ->> 'source_id' = %s
     ORDER BY c.id
"""

EVIDENCE = """
    SELECT e.id::text, e.claim_id::text, e.direction, e.relevance, e.directness,
           e.extraction_confidence, e.reliability, e.independence_state,
           e.independence_group_id::text, e.observation_category
      FROM scoring.evidence e
     WHERE e.source_id = %s
     ORDER BY e.id
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare and write nothing")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("REFUSED: DATABASE_URL is not set. This measures a deployment, not the tree.")
        return 1

    import psycopg

    document: dict = {
        "$comment": (
            "Mission 1.46 §0. What statistical evidence this deployment holds, measured "
            "BEFORE any candidate pair was considered. A candidate chosen first and then "
            "justified against whatever is held is a rationalisation, so the order is the "
            "point. Reads only: no RawRecord, Signal, Claim or Evidence was created."
        ),
        "artifact_version": "statistical-holdings-baseline@1.0.0",
        "generated_by": "mission-1.46",
        "statistical_sources_examined": list(STATISTICAL_SOURCES),
        "holdings": {},
        "observations": {},
        "signals": {},
        "claims": {},
        "evidence": {},
    }

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(HOLDINGS, (list(STATISTICAL_SOURCES),))
        columns = [d.name for d in cur.description]
        found = {row[0]: dict(zip(columns, row, strict=True)) for row in cur.fetchall()}
        for source_id in STATISTICAL_SOURCES:
            document["holdings"][source_id] = found.get(
                source_id,
                {
                    "source_id": source_id,
                    "raw_records": 0,
                    "normalized_records": 0,
                    "record_kinds": 0,
                    "metrics": 0,
                    "geographies": 0,
                    "periods": 0,
                },
            )

        for source_id in STATISTICAL_SOURCES:
            cur.execute(OBSERVATIONS, (source_id,))
            names = [d.name for d in cur.description]
            document["observations"][source_id] = [
                dict(zip(names, row, strict=True)) for row in cur.fetchall()
            ]

            cur.execute(CLAIMS, (source_id,))
            names = [d.name for d in cur.description]
            document["claims"][source_id] = [
                dict(zip(names, row, strict=True)) for row in cur.fetchall()
            ]

            cur.execute(EVIDENCE, (source_id,))
            names = [d.name for d in cur.description]
            rows = [dict(zip(names, row, strict=True)) for row in cur.fetchall()]
            for row in rows:
                row["reliability"] = float(row["reliability"]) if row["reliability"] else None
            document["evidence"][source_id] = rows

        cur.execute("SELECT signal_type_id, count(*) FROM nlp.signals GROUP BY 1 ORDER BY 1")
        document["signals"] = {row[0]: row[1] for row in cur.fetchall()}

    text = json.dumps(document, indent=2, ensure_ascii=False, default=str) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"REFUSED: {OUT.name} does not exist; run without --check first")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {OUT.name} does not match the live deployment")
            return 1
        print(f"ok       {OUT.name} matches the live statistical holdings")
        return 0

    OUT.write_text(text, encoding="utf-8")
    for source_id in STATISTICAL_SOURCES:
        holding = document["holdings"][source_id]
        print(
            f"{source_id:14} raw={holding['raw_records']:>4} "
            f"normalized={holding['normalized_records']:>4} "
            f"metrics={holding['metrics']} "
            f"claims={len(document['claims'][source_id])} "
            f"evidence={len(document['evidence'][source_id])}"
        )
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
