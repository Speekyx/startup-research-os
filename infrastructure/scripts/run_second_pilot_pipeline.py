"""Mission 1.40 §11-§13. Normalize, derive and interpret the second-pilot records.

**Derivation runs ONCE PER FROZEN WINDOW, and that is the preregistered cohort
partition.** The extractor's cohort key groups by (source, record kind, resource,
notice class, CPV division) and carries no period, so a single derivation over
both windows would produce ONE cohort. Scoping each run to one window's records
is what makes the two witnesses two.

The windows were fixed in `second-pilot-ted-category-selection-v1.json` before any
notice was retrieved and before any amount was seen, so this is a partition by a
rule rather than by the result (§16).

Usage:

    uv run --package sros-nlp python infrastructure/scripts/run_second_pilot_pipeline.py
"""

from __future__ import annotations

import contextlib
import json
import os
import pathlib
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "signal-model", "contracts", "evidence-reliability"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))
sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
sys.path.insert(0, str(ROOT / "services" / "nlp" / "python"))

DOCS = ROOT / "docs" / "data"
SELECTION = DOCS / "second-pilot-ted-category-selection-v1.json"
OUT = DOCS / "second-pilot-pipeline-run-v1.json"

EXTRACTOR = "procurement-value-contrast"
INTERPRETER = "observed-signal-restatement"


def main() -> int:
    import psycopg
    from sros_acquisition.normalization.job import run_normalization_job
    from sros_nlp.claim_job import run_claim_interpretation_job
    from sros_nlp.job import run_signal_derivation_job

    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    windows = selection["acquisition_plan"]["windows"]

    workspace_id = os.environ["DEV_WORKSPACE_ID"]
    conn = psycopg.connect(os.environ["DATABASE_URL"], autocommit=False)
    report: dict[str, object] = {"windows": [], "interpretation": None}

    def factory(_workspace_id: str):
        @contextlib.contextmanager
        def same():
            yield conn

        return same()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('sros.workspace_id', %s, true)", (workspace_id,))
            cur.execute(
                "SELECT id FROM research.research_sessions WHERE workspace_id = %s LIMIT 1",
                (workspace_id,),
            )
            session_id = str(cur.fetchone()[0])

        signal_ids: list[str] = []
        for window in windows:
            witness = window["witness"]
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id FROM acquisition.raw_records
                        WHERE workspace_id = %s AND correlation_id LIKE %s""",
                    (workspace_id, f"mission-1.40-{witness}-%"),
                )
                raw_ids = [str(r[0]) for r in cur.fetchall()]

            normalization = run_normalization_job(
                {
                    "workspace_id": workspace_id,
                    "research_session_id": session_id,
                    "correlation_id": f"m140-norm-{witness}-{uuid.uuid4()}",
                    "raw_record_ids": raw_ids,
                    "max_records": len(raw_ids),
                },
                factory,
            )

            with conn.cursor() as cur:
                cur.execute(
                    """SELECT n.id FROM acquisition.normalized_records n
                        WHERE n.workspace_id = %s AND n.raw_record_id = ANY(%s::uuid[])""",
                    (workspace_id, raw_ids),
                )
                normalized_ids = [str(r[0]) for r in cur.fetchall()]

            # THE PARTITION. Scoped to this window's records, so this window's
            # notices form their own cohort.
            derivation = run_signal_derivation_job(
                {
                    "workspace_id": workspace_id,
                    "research_session_id": session_id,
                    "correlation_id": f"m140-derive-{witness}-{uuid.uuid4()}",
                    "extractor_id": EXTRACTOR,
                    "parameters": {"amount_type": "TOTAL_VALUE"},
                    "normalized_record_ids": normalized_ids,
                    "max_records": len(normalized_ids) or 1,
                },
                factory,
            )
            signal_ids.extend(getattr(derivation, "signal_ids", ()) or ())

            entry = {
                "witness": witness,
                "date_start": window["date_start"],
                "date_end": window["date_end"],
                "raw_records": len(raw_ids),
                "normalized_records": len(normalized_ids),
                "normalization": str(normalization),
                "derivation": str(derivation),
            }
            report["windows"].append(entry)
            print(
                f"window {witness}: raw={len(raw_ids)} normalized={len(normalized_ids)} "
                f"| {derivation}"
            )

        interpretation = run_claim_interpretation_job(
            {
                "workspace_id": workspace_id,
                "research_session_id": session_id,
                "correlation_id": f"m140-interpret-{uuid.uuid4()}",
                "interpreter_id": INTERPRETER,
                "signal_type_ids": ["procurement_value_contrast"],
            },
            factory,
        )
        report["interpretation"] = str(interpretation)
        print(f"\ninterpretation: {interpretation}")

        conn.commit()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"ROLLED BACK: {type(exc).__name__}: {exc}")
        return 1
    finally:
        conn.close()

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
