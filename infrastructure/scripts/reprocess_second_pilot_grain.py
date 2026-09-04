"""Mission 1.41 §18-§23. Re-derive the frozen second-pilot windows under 1.1.0.

**No network call.** The 177 RawRecords and their NormalizedRecords are already
persisted from Mission 1.40, and §18 prefers reusing them: rerunning extraction
needs no new acquisition, and the frozen windows are reconstructed from the
correlation ids the acquisition wrote.

**§22 and §23 are enforced here, explicitly.** The extractor version moved
1.0.1 -> 1.1.0, so re-deriving a cohort whose members are unchanged produces a
NEW deterministic Signal id for the SAME witness. That is historical versioning,
not a second observation, and persisting it would manufacture witness
multiplicity -- the exact thing this mission exists to avoid creating by
accident. So a draft whose contributing input set already belongs to a persisted
Signal of this type is SKIPPED, and the skip is reported rather than silent.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/reprocess_second_pilot_grain.py --plan
    uv run --package sros-nlp python infrastructure/scripts/reprocess_second_pilot_grain.py --apply
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pathlib
import sys
import uuid
from datetime import UTC, datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "signal-model", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))
sys.path.insert(0, str(ROOT / "services" / "acquisition" / "python"))
sys.path.insert(0, str(ROOT / "services" / "nlp" / "python"))

DOCS = ROOT / "docs" / "data"
SELECTION = DOCS / "second-pilot-ted-category-selection-v1.json"
OUT = DOCS / "second-pilot-regrain-run-v1.json"

AMOUNT_TYPE = "TOTAL_VALUE"


def _cohort_facts(observations, extractor) -> dict[str, object]:
    """What a reader needs to see about a cohort, from the records themselves."""
    classes, scopes, currencies, divisions = set(), set(), set(), set()
    for observation in observations:
        notice = observation.section("notice")
        classes.add(notice.get("class"))
        # The extractor's own reading, rather than a second one here that could
        # disagree with the grouping this report is about.
        division = extractor._cpv_division(observation)
        if division is not None:
            divisions.add(division)
        for entry in observation.payload.get("amounts") or []:
            if isinstance(entry, dict) and entry.get("amount_type") == AMOUNT_TYPE:
                scopes.add(entry.get("scope"))
                for currency in entry.get("currencies") or []:
                    currencies.add(currency)
    return {
        "notice_classes": sorted(c for c in classes if c),
        "amount_scopes": sorted(s for s in scopes if s),
        "currencies": sorted(currencies),
        "cpv_divisions": sorted(divisions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()

    import psycopg
    from sros_nlp.claim_job import run_claim_interpretation_job
    from sros_nlp.extractors import EXTRACTOR_REGISTRY
    from sros_nlp.extractors.base import CandidateGroup, DerivationRequest
    from sros_nlp.repositories import persist_signals, read_normalized_observations

    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    windows = selection["acquisition_plan"]["windows"]
    extractor = EXTRACTOR_REGISTRY["procurement-value-contrast"]
    derivation = extractor.resolve({"amount_type": AMOUNT_TYPE})

    workspace_id = os.environ["DEV_WORKSPACE_ID"]
    conn = psycopg.connect(os.environ["DATABASE_URL"], autocommit=False)
    report: dict[str, object] = {
        "extractor_version": extractor.extractor_version,
        "network_acquisitions": 0,
        "windows": [],
        "skipped_as_existing_witness": [],
    }

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
            # Every persisted Signal of this type, by its contributing input set.
            cur.execute(
                """SELECT s.id, array_agg(i.normalized_record_id ORDER BY i.normalized_record_id)
                     FROM nlp.signals s
                     JOIN nlp.signal_inputs i ON i.signal_id = s.id
                    WHERE s.workspace_id = %s AND s.signal_type_id = %s
                    GROUP BY s.id""",
                (workspace_id, extractor.signal_type_id),
            )
            existing_witnesses = {
                tuple(sorted(str(x) for x in members)): str(signal_id)
                for signal_id, members in cur.fetchall()
            }

        now = datetime.now(UTC)
        for window in windows:
            witness = window["witness"]
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT n.id FROM acquisition.normalized_records n
                         JOIN acquisition.raw_records r ON r.id = n.raw_record_id
                        WHERE n.workspace_id = %s AND r.correlation_id LIKE %s""",
                    (workspace_id, f"mission-1.40-{witness}-%"),
                )
                record_ids = [str(r[0]) for r in cur.fetchall()]

            observations = read_normalized_observations(
                conn,
                workspace_id,
                record_kind_id=extractor.record_kind_id,
                record_ids=record_ids,
                limit=len(record_ids) or 1,
            )

            groups: dict[str, list] = {}
            unkeyed = 0
            for observation in observations:
                key = extractor.group_key(observation, derivation)
                if key is None:
                    unkeyed += 1
                    continue
                groups.setdefault(key, []).append(observation)

            cohorts = []
            for key in sorted(groups):
                members = groups[key]
                group = CandidateGroup(key=key, observations=tuple(members))
                outcome = extractor.derive(
                    group,
                    derivation,
                    DerivationRequest(
                        workspace_id=workspace_id,
                        correlation_id=f"m141-regrain-{witness}-{uuid.uuid4()}",
                        derived_at=now,
                        expires_at=now + timedelta(days=90),
                        research_session_id=session_id,
                    ),
                )
                entry = {
                    "window": witness,
                    "records": len(members),
                    **_cohort_facts(members, extractor),
                    "status": "DERIVED" if outcome.drafts else "REFUSED",
                    "refusals": [r.reason.value for r in outcome.refusals],
                    "refusal_detail": [r.detail for r in outcome.refusals],
                }
                if outcome.drafts and args.apply:
                    draft = outcome.drafts[0]
                    # CONTRIBUTED inputs only: an excluded input is recorded on
                    # the draft but is not part of what the Signal witnessed.
                    membership = tuple(
                        sorted(
                            i.observation.normalized_record_id
                            for i in draft.inputs
                            if i.role.value == "CONTRIBUTED"
                        )
                    )
                    existing = existing_witnesses.get(membership)
                    if existing is not None:
                        # §22, §23. Same witness, new procedure version. Not a
                        # second observation.
                        entry["status"] = "SKIPPED_EXISTING_WITNESS"
                        entry["existing_signal_id"] = existing
                        report["skipped_as_existing_witness"].append(
                            {"window": witness, "signal_id": existing, "records": len(members)}
                        )
                    else:
                        persisted = persist_signals(conn, [draft])
                        entry["persisted_signal_ids"] = list(persisted.signal_ids)
                        for signal_id in persisted.signal_ids:
                            existing_witnesses[membership] = signal_id
                cohorts.append(entry)

            report["windows"].append(
                {
                    "witness": witness,
                    "date_start": window["date_start"],
                    "date_end": window["date_end"],
                    "normalized_records": len(record_ids),
                    "records_with_no_key": unkeyed,
                    "cohorts": cohorts,
                }
            )
            print(f"\n=== window {witness} ({len(record_ids)} records, {unkeyed} unkeyed) ===")
            for entry in cohorts:
                print(
                    f"  {entry['status']:26} n={entry['records']:3} "
                    f"class={','.join(entry['notice_classes']):22} "
                    f"scope={','.join(entry['amount_scopes']):8} "
                    f"cur={','.join(entry['currencies']):6} "
                    f"div={','.join(entry['cpv_divisions'])}"
                )

        if args.apply:
            interpretation = run_claim_interpretation_job(
                {
                    "workspace_id": workspace_id,
                    "research_session_id": session_id,
                    "correlation_id": f"m141-interpret-{uuid.uuid4()}",
                    "interpreter_id": "observed-signal-restatement",
                    "signal_type_ids": ["procurement_value_contrast"],
                },
                factory,
            )
            report["interpretation"] = str(interpretation)
            print(
                f"\ninterpretation: claims_new={interpretation.run.claims_new} "
                f"evidence_new={interpretation.run.evidence_new} "
                f"conflicts={len(interpretation.persisted.evidence_conflicts)}"
            )
            conn.commit()
        else:
            conn.rollback()
            print("\n--plan only; nothing was persisted")
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"ROLLED BACK: {type(exc).__name__}: {exc}")
        return 1
    finally:
        conn.close()

    if args.apply:
        OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
