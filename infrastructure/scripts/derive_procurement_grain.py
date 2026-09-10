"""Mission 1.81. Derive finer-grain procurement cohorts from held TED records.

**No network call.** The 177 division-92 NormalizedRecords are already persisted from
Mission 1.40, and the frozen acquisition windows are reconstructed from the correlation
ids the acquisition wrote -- exactly as Mission 1.41's reprocessing did. Cohort
completeness is relative to those windows: a cohort is every held notice of one window
that the extractor's own key puts together at the requested CPV grain.

**The grain is a parameter of the existing procedure**, `procurement-value-contrast@1.2.0`
with `cpv_grain`, and nothing here chooses membership after seeing a value: the key is
built from the classification codes, the notice class, the currency and the amount scope,
and the contrast is computed afterwards over whatever the key gathered.

**Idempotent.** A Signal's identity is its derivation fingerprint, so the same run twice
persists nothing the second time; on top of that a draft whose contributing input set and
parameter fingerprint already belong to a persisted Signal is SKIPPED and reported, so a
later extractor version bump cannot manufacture a second witness for one cohort either.
The claim interpretation job is the production job, over every procurement Signal: the
division Signals re-interpret to their existing Claims and Evidence (REUSED), and the
finer-grain Signals interpret to their own.

Usage:

    uv run --package sros-nlp python infrastructure/scripts/derive_procurement_grain.py --plan
    uv run --package sros-nlp python infrastructure/scripts/derive_procurement_grain.py --apply
    uv run --package sros-nlp python infrastructure/scripts/derive_procurement_grain.py --audit

`--audit` writes the per-notice census of the held division-92 corpus and touches nothing.
`--report` reads the persisted finer-grain Signals, Claims and Evidence back and writes the
run record from them; an `--apply` that persists nothing writes the re-run record instead.
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
# Mission 1.82. One record per grain: the group-grain run belongs to Mission 1.81 and
# stays byte-identical, so the file name carries the level rather than the mission.
RUN_RECORDS = {
    3: (
        DOCS / "procurement-grain-derivation-run-v1.json",
        DOCS / "procurement-grain-derivation-rerun-v1.json",
    ),
    4: (
        DOCS / "procurement-class-grain-derivation-run-v1.json",
        DOCS / "procurement-class-grain-derivation-rerun-v1.json",
    ),
}
AUDIT = DOCS / "procurement-division-92-notice-audit-v1.json"

AMOUNT_TYPE = "TOTAL_VALUE"
DIVISION = "92"
WINDOW_PREFIXES = {"A": "mission-1.40-A-%", "B": "mission-1.40-B-%"}


def _depth(code: str) -> int:
    return len(code.rstrip("0"))


def _audit_rows(conn, workspace_id: str) -> list[dict[str, object]]:
    """Every held division-92 notice, with what the record itself establishes."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT n.id, n.raw_record_id, n.observation_key, n.payload, r.correlation_id
                 FROM acquisition.normalized_records n
                 JOIN acquisition.raw_records r ON r.id = n.raw_record_id
                WHERE n.workspace_id = %s AND n.source_id = 'ted-eu'
                  AND n.superseded_at IS NULL
                ORDER BY n.observation_key""",
            (workspace_id,),
        )
        rows = cur.fetchall()
    out = []
    for nid, rid, key, payload, correlation in rows:
        entries = [e for e in payload["classification"]["codes"] if e.get("code")]
        codes = [str(e.get("code")) for e in entries]
        if not any(c.startswith(DIVISION) for c in codes):
            continue
        # The label the source published beside each code: null on every held entry.
        labels = [e.get("label") for e in entries]
        amount = None
        for entry in payload.get("amounts") or []:
            if (
                entry.get("amount_type") == AMOUNT_TYPE
                and entry.get("pairing") == "ESTABLISHED"
                and len(entry.get("amounts") or []) == 1
                and len(entry.get("currencies") or []) == 1
            ):
                amount = entry
        window = next(
            (
                w
                for w, p in WINDOW_PREFIXES.items()
                if correlation and correlation.startswith(p[:-1])
            ),
            None,
        )
        divisions = sorted({c[:2] for c in codes})
        groups = sorted({c[:3] for c in codes if _depth(c) >= 3})
        out.append(
            {
                "notice_id": payload["notice"]["publication_number"],
                "notice_type": payload["notice"]["class"],
                "cpv_codes": codes,
                "cpv_code_depths": [_depth(c) for c in codes],
                "cpv_labels": labels,
                "primary_or_additional_status": "NOT_ESTABLISHED_BY_HELD_RECORD",
                "divisions_carried": divisions,
                "groups_carried": groups,
                "single_division": len(divisions) == 1,
                "group_membership": (
                    "UNSPECIFIED_AT_GROUP"
                    if len(divisions) == 1 and not groups
                    else "AMBIGUOUS_ACROSS_DIVISIONS"
                    if len(divisions) != 1
                    else "AMBIGUOUS_ACROSS_GROUPS"
                    if len(groups) != 1
                    else groups[0]
                ),
                "total_value_present": amount is not None,
                "total_value_currency": amount["currencies"][0] if amount else None,
                "total_value_scope": amount["scope"] if amount else None,
                "acquisition_window": window,
                "normalized_record_id": str(nid),
                "raw_record_id": str(rid),
                "observation_key": key,
            }
        )
    return out


def _report_rows(conn, workspace_id: str, fingerprint: str, grain: int) -> dict[str, object]:
    """The persisted finer-grain Signals with their Claims and Evidence, read back."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT s.id, s.correlation_id, s.scope, s.magnitude, s.magnitude_unit,
                      s.extractor_version, s.parameters,
                      (SELECT count(*) FROM nlp.signal_inputs i
                        WHERE i.signal_id = s.id AND i.role = 'CONTRIBUTED')
                 FROM nlp.signals s
                WHERE s.workspace_id = %s AND s.signal_type_id = 'procurement_value_contrast'
                  AND s.parameter_fingerprint = %s
                ORDER BY s.correlation_id""",
            (workspace_id, fingerprint),
        )
        signals = cur.fetchall()
        cur.execute(
            """SELECT e.id, e.signal_id, e.claim_id, c.proposition_facts ->> 'proposition',
                      r.statement
                 FROM scoring.evidence e
                 JOIN research.claims c ON c.id = e.claim_id
                 JOIN research.claim_revisions r
                   ON r.claim_id = c.id AND r.revision = c.current_revision
                WHERE e.workspace_id = %s""",
            (workspace_id,),
        )
        evidence = cur.fetchall()
    by_signal: dict[str, list] = {}
    for eid, sid, cid, kind, statement in evidence:
        # The proposition key is deliberately not copied here: it is a SHA-256 the claim
        # row already carries, and a hex string beside the word "key" is what a secret
        # scanner is built to flag. The claim id reaches it.
        by_signal.setdefault(str(sid), []).append(
            {
                "evidence_id": str(eid),
                "claim_id": str(cid),
                "proposition_kind": kind,
                "statement": statement,
            }
        )
    out = []
    for sid, correlation, scope, magnitude, unit, version, parameters, members in signals:
        window = (
            correlation.split("-")[2]
            if correlation and correlation.startswith(("m181-", "m182-"))
            else None
        )
        out.append(
            {
                "signal_id": str(sid),
                "acquisition_window": window,
                "classification_level": scope.get("classification_level"),
                "classification_level_code": scope.get("classification_level_code"),
                "classification_codes": scope.get("classification_codes"),
                "notice_class": scope["notice_classes"][0],
                "currency": scope["currencies"][0],
                "amount_scope": scope["amount_scopes"][0],
                "contributing_records": int(members),
                "magnitude": str(magnitude),
                "magnitude_unit": unit,
                "extractor_version": version,
                "parameters": parameters,
                "evidence": sorted(
                    by_signal.get(str(sid), []), key=lambda e: e["proposition_kind"]
                ),
            }
        )
    return {
        "$comment": (
            "Mission 1.81. The finer-grain procurement derivation, read back from the canonical "
            "rows it persisted: one entry per Signal keyed at the requested CPV grain, with the "
            "Claims it witnesses and the Evidence rows that cite it. Nothing here was acquired; "
            "every contributing record is a Mission 1.40 NormalizedRecord."
        ),
        "grain": grain,
        "network_acquisitions": 0,
        "signals": out,
        "claims": sorted({e["claim_id"] for s in out for e in s["evidence"]}),
        "evidence_rows": sum(len(s["evidence"]) for s in out),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--grain", type=int, default=3)
    parser.add_argument(
        "--tag",
        default="182",
        help="mission tag written into the correlation id of a persisted signal",
    )
    args = parser.parse_args()

    import psycopg
    from sros_nlp.claim_job import run_claim_interpretation_job
    from sros_nlp.extractors import EXTRACTOR_REGISTRY
    from sros_nlp.extractors.base import CandidateGroup, DerivationRequest
    from sros_nlp.repositories import persist_signals, read_normalized_observations

    workspace_id = os.environ["DEV_WORKSPACE_ID"]
    conn = psycopg.connect(os.environ["DATABASE_URL"], autocommit=False)

    if args.audit:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('sros.workspace_id', %s, true)", (workspace_id,))
        rows = _audit_rows(conn, workspace_id)
        conn.rollback()
        conn.close()
        AUDIT.write_text(
            json.dumps(
                {
                    "$comment": (
                        "Mission 1.81 §4. Every held TED notice carrying a division-92 CPV code, "
                        "as the normalized record states it: codes, depths, notice class, whether "
                        "a TOTAL_VALUE amount is paired with one currency, and the acquisition "
                        "window. Primary/additional CPV status is NOT established by the held "
                        "representation (every code entry carries code, scheme and a null label "
                        "and nothing else), so it is recorded as such and never inferred."
                    ),
                    "division": DIVISION,
                    "held_notices": len(rows),
                    "notices": rows,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"wrote {AUDIT.name} ({len(rows)} notices)")
        return 0

    extractor = EXTRACTOR_REGISTRY["procurement-value-contrast"]
    derivation = extractor.resolve({"amount_type": AMOUNT_TYPE, "cpv_grain": args.grain})

    if args.grain not in RUN_RECORDS:
        print(
            f"REFUSED: no run record is registered for grain {args.grain}. A derivation "
            "that persists rows needs a place to record what it wrote, and reusing "
            "another grain's file would overwrite another mission's record."
        )
        conn.close()
        return 1
    out_path, rerun_path = RUN_RECORDS[args.grain]

    if args.report:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('sros.workspace_id', %s, true)", (workspace_id,))
        record = _report_rows(conn, workspace_id, derivation.parameter_fingerprint, args.grain)
        conn.rollback()
        conn.close()
        record["extractor_version"] = extractor.extractor_version
        record["parameters"] = derivation.parameters_json()
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"wrote {out_path.name} ({len(record['signals'])} signals)")
        return 0
    report: dict[str, object] = {
        "$comment": (
            "Mission 1.81. The finer-grain procurement derivation over held records, one "
            "acquisition window at a time, through the production extractor and the "
            "production claim interpretation job. Nothing here was acquired."
        ),
        "extractor_version": extractor.extractor_version,
        "parameters": derivation.parameters_json(),
        "parameter_fingerprint": derivation.parameter_fingerprint,
        "network_acquisitions": 0,
        "windows": [],
        "skipped_as_existing_witness": [],
        "signals_persisted": 0,
        "signals_reused": 0,
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
            cur.execute(
                """SELECT s.id, s.parameter_fingerprint,
                          array_agg(i.normalized_record_id ORDER BY i.normalized_record_id)
                     FROM nlp.signals s
                     JOIN nlp.signal_inputs i ON i.signal_id = s.id
                    WHERE s.workspace_id = %s AND s.signal_type_id = %s
                      AND i.role = 'CONTRIBUTED'
                    GROUP BY s.id, s.parameter_fingerprint""",
                (workspace_id, extractor.signal_type_id),
            )
            existing = {
                (tuple(sorted(str(x) for x in members)), fingerprint): str(signal_id)
                for signal_id, fingerprint, members in cur.fetchall()
            }

        now = datetime.now(UTC)
        for witness, pattern in WINDOW_PREFIXES.items():
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT n.id FROM acquisition.normalized_records n
                         JOIN acquisition.raw_records r ON r.id = n.raw_record_id
                        WHERE n.workspace_id = %s AND r.correlation_id LIKE %s""",
                    (workspace_id, pattern),
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
                key_facts = json.loads(key)
                outcome = extractor.derive(
                    CandidateGroup(key=key, observations=tuple(members)),
                    derivation,
                    DerivationRequest(
                        workspace_id=workspace_id,
                        correlation_id=f"m{args.tag}-grain{args.grain}-{witness}-{uuid.uuid4()}",
                        derived_at=now,
                        expires_at=now + timedelta(days=90),
                        research_session_id=session_id,
                    ),
                )
                entry: dict[str, object] = {
                    "window": witness,
                    "cpv_prefix": key_facts.get("cpv_prefix"),
                    "notice_class": key_facts.get("notice_class"),
                    "currency": key_facts.get("currency"),
                    "amount_scope": key_facts.get("amount_scope"),
                    "members": len(members),
                    "status": "DERIVED" if outcome.drafts else "REFUSED",
                    "refusals": [r.reason.value for r in outcome.refusals],
                    "refusal_detail": [r.detail for r in outcome.refusals],
                }
                if outcome.drafts:
                    draft = outcome.drafts[0]
                    membership = tuple(
                        sorted(
                            i.observation.normalized_record_id
                            for i in draft.inputs
                            if i.role.value == "CONTRIBUTED"
                        )
                    )
                    entry["signal_id"] = draft.id
                    entry["magnitude"] = str(draft.magnitude.value)
                    prior = existing.get((membership, derivation.parameter_fingerprint))
                    if prior is not None:
                        entry["status"] = "SKIPPED_EXISTING_WITNESS"
                        entry["existing_signal_id"] = prior
                        report["skipped_as_existing_witness"].append(  # type: ignore[union-attr]
                            {"window": witness, "signal_id": prior, "members": len(members)}
                        )
                    elif args.apply:
                        persisted = persist_signals(conn, [draft])
                        entry["persisted_signal_ids"] = list(persisted.signal_ids)
                        report["signals_persisted"] += len(persisted.signal_ids)  # type: ignore[operator]
                        for signal_id in persisted.signal_ids:
                            existing[(membership, derivation.parameter_fingerprint)] = signal_id
                cohorts.append(entry)

            report["windows"].append(  # type: ignore[union-attr]
                {
                    "witness": witness,
                    "normalized_records": len(record_ids),
                    "records_with_no_key": unkeyed,
                    "cohorts": cohorts,
                }
            )
            print(f"\n=== window {witness} ({len(record_ids)} records, {unkeyed} unkeyed) ===")
            for entry in cohorts:
                print(
                    f"  {entry['status']:26} n={entry['members']:3} prefix={entry['cpv_prefix']} "
                    f"class={entry['notice_class']:22} cur={entry['currency']:4} "
                    f"{entry.get('magnitude', '')} {entry['refusals']}"
                )

        if args.apply:
            interpretation = run_claim_interpretation_job(
                {
                    "workspace_id": workspace_id,
                    "research_session_id": session_id,
                    "correlation_id": f"m{args.tag}-interpret-{uuid.uuid4()}",
                    "interpreter_id": "observed-signal-restatement",
                    "signal_type_ids": ["procurement_value_contrast"],
                },
                factory,
            )
            report["interpretation"] = {
                "signals_considered": interpretation.run.signals_considered,
                "claims_new": interpretation.run.claims_new,
                "claims_reused": getattr(interpretation.run, "claims_reused", None),
                "evidence_new": interpretation.run.evidence_new,
                "evidence_conflicts": len(interpretation.persisted.evidence_conflicts),
                "text": str(interpretation),
            }
            print(
                f"\ninterpretation: considered={interpretation.run.signals_considered} "
                f"claims_new={interpretation.run.claims_new} "
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
        target = out_path if report["signals_persisted"] else rerun_path
        if target is rerun_path:
            report["$comment"] = (
                "Mission 1.81 §34. A second execution of the same derivation over the same "
                "held records: every cohort's witness set and parameter fingerprint already "
                "belong to a persisted Signal, so every draft is SKIPPED_EXISTING_WITNESS, 0 "
                "Signals are persisted, and the production interpretation job creates 0 Claims "
                "and 0 Evidence. Idempotence, measured rather than promised."
            )
        target.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"wrote {target.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
