"""Project the held content-request Signals onto their convergent proposition.

Mission 1.43 §20. **No acquisition, no derivation, no new Signal.** Every input
already exists: this re-runs the production claim interpretation path over
Signals collected and derived by earlier missions, so the new convergence
contract can produce the broader Claims those Signals also witness.

Re-interpretation is safe to repeat. The detailed Claims are found by
`proposition_key` and their Evidence is idempotent on
`(workspace_id, claim_id, signal_id)` since Mission 1.41, so a replay adds no
detailed row; what is new is the convergent projection, which had no contract
until now.

    uv run python infrastructure/scripts/project_content_request_convergence.py --plan
    uv run python infrastructure/scripts/project_content_request_convergence.py --apply
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pathlib
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "contracts", "signal-model", "evidence-aggregation"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))
sys.path.insert(0, str(ROOT / "services" / "nlp" / "python"))

DOCS = ROOT / "docs" / "data"
OUT = DOCS / "calibration-corpus-expansion-run-v1.json"
PLAN = DOCS / "calibration-corpus-expansion-plan-v1.json"

SIGNAL_TYPE = "content_request_change"
DETAILED_KIND = "platform_counted_content_request_change"
CONVERGENT_KIND = "platform_counted_content_request_change_witnessed"


def snapshot(cur) -> dict[str, int]:
    counts = {}
    for name, table in (
        ("raw_records", "acquisition.raw_records"),
        ("normalized_records", "acquisition.normalized_records"),
        ("signals", "nlp.signals"),
        ("claims", "research.claims"),
        ("claim_revisions", "research.claim_revisions"),
        ("evidence", "scoring.evidence"),
        ("reliability_assessments", "epistemic.reliability_assessments"),
        ("reliability_basis_rows", "epistemic.reliability_assessment_basis"),
        ("opportunities", "research.opportunities"),
    ):
        cur.execute(f"SELECT count(*) FROM {table}")  # noqa: S608
        counts[name] = cur.fetchone()[0]
    cur.execute(
        "SELECT count(DISTINCT independence_group_id) FROM scoring.evidence"
        " WHERE independence_group_id IS NOT NULL"
    )
    counts["independence_groups"] = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM scoring.evidence WHERE reliability IS NOT NULL")
    counts["evidence_reliability_written"] = cur.fetchone()[0]
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="commit the projection")
    parser.add_argument("--plan", action="store_true", help="run and roll back")
    args = parser.parse_args()
    if not (args.apply or args.plan):
        print("REFUSED: pass --plan to rehearse or --apply to commit")
        return 1

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("REFUSED: DATABASE_URL is not set. This writes to a deployment.")
        return 1
    workspace_id = os.environ.get("DEV_WORKSPACE_ID")
    if not workspace_id:
        print("REFUSED: DEV_WORKSPACE_ID is not set.")
        return 1

    import psycopg
    from sros_nlp.claim_job import run_claim_interpretation_job

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan["bounds"]["network_acquisition_required"] is not False:
        print("REFUSED: the frozen plan does not say this route is acquisition-free")
        return 1

    conn = psycopg.connect(url, autocommit=False)

    def factory(_workspace_id: str):
        @contextlib.contextmanager
        def same():
            yield conn

        return same()

    report: dict[str, object] = {
        "$comment": (
            "Mission 1.43. The RESULT of the frozen plan: what re-interpreting held "
            "Signals under the new convergence contract actually produced. No "
            "acquisition, no derivation, no new Signal, no reliability."
        ),
        "artifact_version": "calibration-corpus-expansion-run@1.0.0",
        "generated_by": "mission-1.43",
        "network_acquisitions": 0,
        "signals_derived": 0,
        "signal_type_reprocessed": SIGNAL_TYPE,
        "detailed_kind": DETAILED_KIND,
        "convergent_kind": CONVERGENT_KIND,
    }

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('sros.workspace_id', %s, true)", (workspace_id,))
            report["counters_before"] = snapshot(cur)

            cur.execute(
                "SELECT id FROM research.research_sessions WHERE workspace_id = %s LIMIT 1",
                (workspace_id,),
            )
            session_id = str(cur.fetchone()[0])

            cur.execute(
                "SELECT count(*) FROM nlp.signals WHERE workspace_id = %s AND signal_type_id = %s",
                (workspace_id, SIGNAL_TYPE),
            )
            report["held_signals_reprocessed"] = cur.fetchone()[0]

        interpretation = run_claim_interpretation_job(
            {
                "workspace_id": workspace_id,
                "research_session_id": session_id,
                "correlation_id": f"m143-project-{uuid.uuid4()}",
                "interpreter_id": "observed-signal-restatement",
                "signal_type_ids": [SIGNAL_TYPE],
            },
            factory,
        )
        report["interpretation"] = {
            "claims_new": interpretation.run.claims_new,
            "evidence_new": interpretation.run.evidence_new,
            "signals_considered": interpretation.run.signals_considered,
            "signals_refused": interpretation.run.signals_refused,
            "evidence_conflicts": len(interpretation.persisted.evidence_conflicts),
        }

        with conn.cursor() as cur:
            report["counters_after"] = snapshot(cur)
            cur.execute(
                """SELECT c.id, c.current_revision,
                          c.proposition_facts ->> 'content_id',
                          c.proposition_facts ->> 'direction',
                          c.proposition_facts ->> 'audience_class',
                          count(e.id)
                     FROM research.claims c
                     JOIN scoring.evidence e ON e.claim_id = c.id
                    WHERE c.proposition_facts ->> 'proposition' = %s
                    GROUP BY c.id, c.current_revision, 3, 4, 5
                    ORDER BY count(e.id) DESC, 3, 4""",
                (CONVERGENT_KIND,),
            )
            report["convergent_claims"] = [
                {
                    "claim_id": str(r[0]),
                    "revision": r[1],
                    "content_id": r[2],
                    "direction": r[3],
                    "audience_class": r[4],
                    "evidence_count": r[5],
                }
                for r in cur.fetchall()
            ]

        before = report["counters_before"]
        after = report["counters_after"]
        report["deltas"] = {
            name: after[name] - before[name] for name in before if after[name] != before[name]
        }

        forbidden = {
            "raw_records",
            "normalized_records",
            "signals",
            "reliability_assessments",
            "reliability_basis_rows",
            "opportunities",
            "independence_groups",
            "evidence_reliability_written",
        }
        moved = forbidden & set(report["deltas"])
        if moved:
            conn.rollback()
            print(f"ROLLED BACK: these counters must not move and did: {sorted(moved)}")
            return 1

        if args.apply:
            conn.commit()
            report["committed"] = True
        else:
            conn.rollback()
            report["committed"] = False
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"ROLLED BACK: {type(exc).__name__}: {exc}")
        return 1
    finally:
        conn.close()

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"held {SIGNAL_TYPE} signals reprocessed : {report['held_signals_reprocessed']}")
    print("network acquisitions                   : 0")
    print(
        f"new claims / evidence                  : "
        f"{report['interpretation']['claims_new']} / {report['interpretation']['evidence_new']}"
    )
    print(f"deltas                                 : {report['deltas']}")
    print(f"\nconvergent Claims ({len(report['convergent_claims'])}):")
    for entry in report["convergent_claims"]:
        print(
            f"  {entry['claim_id'][:8]}  {entry['content_id']:20} {entry['direction']:11}"
            f" witnesses={entry['evidence_count']}"
        )
    print(f"\n{'COMMITTED' if report.get('committed') else '--plan only; rolled back'}")
    print(f"wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
