"""Mission 1.40 §8, §9. The bounded second-pilot acquisition, held to the frozen plan.

**Every parameter comes from the frozen selection artifact**, never from an
argument. A script that took a category or a window on the command line would let
the plan be edited after the results were seen, which §37 forbids by name.

Two disjoint publication windows over CPV division 92, each its own acquisition,
each its own cohort. It runs the real collection job and the real normalization,
signal-derivation and claim-interpretation jobs, in the caller's transaction, and
writes into the LIVE research corpus -- which is the point: Mission 1.39 proved
the mechanics on fixtures, and only real rows can change calibration feasibility.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/run_second_pilot_acquisition.py --plan
    uv run --package sros-nlp python infrastructure/scripts/run_second_pilot_acquisition.py --apply

`--plan` prints what would be requested and contacts nothing.
"""

from __future__ import annotations

import argparse
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
OUT = DOCS / "second-pilot-acquisition-run-v1.json"

USE_PROFILE = "local-private-research-v1"


def plan() -> dict:
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    acquisition = selection["acquisition_plan"]
    return {
        "cpv_division": acquisition["cpv_division"],
        "windows": acquisition["windows"],
        "bounds": acquisition["bounds"],
        "source_id": acquisition["source_id"],
        "resource_id": acquisition["resource_id"],
        "frozen_selection_sha256": selection["frozen_selection_sha256"],
        "official_label": selection["selected"]["official_label"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually contact TED and persist")
    parser.add_argument("--plan", action="store_true", help="print the frozen plan and stop")
    args = parser.parse_args()

    frozen = plan()
    print("FROZEN PLAN")
    print(f"  selection hash : {frozen['frozen_selection_sha256']}")
    print(f"  CPV division   : {frozen['cpv_division']}  {frozen['official_label']}")
    print(f"  source         : {frozen['source_id']} / {frozen['resource_id']}")
    for window in frozen["windows"]:
        print(
            f"  window {window['witness']}       : {window['date_start']} .. {window['date_end']}"
        )
    print(f"  bounds         : {frozen['bounds']}")

    if not args.apply:
        print("\n--plan only; nothing was contacted and nothing was written")
        return 0

    import psycopg
    from sros_acquisition.collection.job import run_ted_search_job

    url = os.environ["DATABASE_URL"]
    workspace_id = os.environ["DEV_WORKSPACE_ID"]

    conn = psycopg.connect(url, autocommit=False)
    runs = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('sros.workspace_id', %s, true)", (workspace_id,))
            cur.execute(
                "SELECT id FROM research.research_sessions WHERE workspace_id = %s LIMIT 1",
                (workspace_id,),
            )
            row = cur.fetchone()
        if row is None:
            print("REFUSED: no research session exists in this workspace to attribute the run to")
            return 1
        session_id = str(row[0])

        def factory(_workspace_id: str):
            import contextlib

            @contextlib.contextmanager
            def same():
                yield conn

            return same()

        for window in frozen["windows"]:
            payload = {
                "workspace_id": workspace_id,
                "research_session_id": session_id,
                "correlation_id": f"mission-1.40-{window['witness']}-{uuid.uuid4()}",
                "date_start": window["date_start"],
                "date_end": window["date_end"],
                "cpv_division": frozen["cpv_division"],
                **frozen["bounds"],
            }
            print(f"\n=== window {window['witness']} ===")
            result = run_ted_search_job(payload, factory, use_profile=USE_PROFILE)
            runs.append(
                {
                    "witness": window["witness"],
                    "date_start": window["date_start"],
                    "date_end": window["date_end"],
                    "result": str(result),
                }
            )
            print(f"  {result}")

        conn.commit()
    except Exception as exc:  # noqa: BLE001 - reported, then re-raised context-free
        conn.rollback()
        print(f"\nROLLED BACK: {type(exc).__name__}: {exc}")
        return 1
    finally:
        conn.close()

    OUT.write_text(
        json.dumps({"frozen": frozen, "runs": runs}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
