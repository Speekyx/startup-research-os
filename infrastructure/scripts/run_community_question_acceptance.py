"""Derive the acceptance-state Signal, then interpret it, on real records.

Mission 1.32 §6 to §8. **No network, no model, no acquisition.** It reads
`community_question` records this deployment already holds and runs the existing
derivation and interpretation jobs over them.

    python infrastructure/scripts/run_community_question_acceptance.py --plan
    python infrastructure/scripts/run_community_question_acceptance.py --apply

`--plan` reports what would be derived and writes nothing. `--apply` runs both
jobs in the real workspace and persists Signal, Claim, ClaimRevision and
Evidence through the production path -- never by direct insert.

**The retrieval page size is READ FROM PROVENANCE, never assumed.** The extractor
needs it to establish that the retrieval did not truncate, and a script that
hard-coded 100 would be asserting the very thing the check exists to test. If the
contributing raw records disagree about the bound, this refuses.

**The acceptance breakdown is reported in `--plan` and derived from nothing.** It
exists so the operator sees the split -- questions with zero answers, questions
answered but not accepted -- before any record is written, because a single count
of the two conflates facts that mean different things.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pathlib
import sys
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]

WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"
CORRELATION_ID = "mission-1.32-acceptance-state"
TAG = "docker"
SOURCE_ID = "stack-exchange"


def _load_env() -> None:
    env_file = ROOT / "infrastructure" / "compose" / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _factory(commit: bool):
    """A tenant connection factory entering BOTH isolation layers.

    `SET LOCAL ROLE` so the row-level policies apply at all -- the migration
    role bypasses them -- and the transaction-local workspace so they resolve to
    this tenant.
    """
    role = os.environ.get("APP_DB_ROLE", "sros_app")

    @contextlib.contextmanager
    def make(workspace_id: str):
        import psycopg

        connection = psycopg.connect(os.environ["DATABASE_URL"])
        try:
            with connection.transaction(force_rollback=not commit):
                connection.execute(f"SET LOCAL ROLE {role}")
                connection.execute(
                    "SELECT set_config('app.workspace_id', %s, true)", (workspace_id,)
                )
                yield connection
        finally:
            connection.close()

    return make


def _inputs() -> tuple[list[str], int, int, dict[str, int]]:
    """The contributing records, and the page size their retrieval asked for.

    Returns the normalized record ids, the page size, and how many of them carry
    the tag -- the last only so `--plan` can report it. The extractor recomputes
    everything it decides on.
    """
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT n.id, n.payload, r.provenance
                 FROM acquisition.normalized_records n
                 JOIN acquisition.raw_records r ON r.id = n.raw_record_id
                WHERE n.record_kind_id = 'community_question'
                  AND n.source_id = %s
                  AND r.provenance->>'tagged' = %s
                ORDER BY n.id""",
            (SOURCE_ID, TAG),
        )
        rows = cur.fetchall()

    if not rows:
        raise SystemExit(f"no held records came from a tagged={TAG!r} retrieval")

    sizes = {int(p["page_size"]) for _, _, p in rows if isinstance(p.get("page_size"), int)}
    pages = {int(p["page"]) for _, _, p in rows if isinstance(p.get("page"), int)}
    if len(sizes) != 1 or len(pages) != 1:
        raise SystemExit(
            f"these records arrived across pages {sorted(pages)} with page size(s) "
            f"{sorted(sizes)}. Completeness is established from ONE short page, so the "
            "derivation is refused rather than run on an ambiguous bound"
        )

    ids = [str(record_id) for record_id, _, _ in rows]
    eligible = [payload for _, payload, _ in rows if TAG in (payload["tags"]["values"] or [])]

    # Reported, never derived from. A missing flag is counted separately and is
    # NEVER folded into `unaccepted`: an absent value withholds the fact, and the
    # extractor refuses rather than reading it as a negative (§3).
    breakdown = {"missing": 0, "accepted": 0, "answered_unaccepted": 0, "zero_answers": 0}
    for payload in eligible:
        answers = payload.get("answers") or {}
        flag = answers.get("has_accepted_answer")
        if not isinstance(flag, bool):
            breakdown["missing"] += 1
            continue
        if flag:
            breakdown["accepted"] += 1
        elif answers.get("count") == 0:
            breakdown["zero_answers"] += 1
        else:
            breakdown["answered_unaccepted"] += 1
    breakdown["unaccepted"] = breakdown["answered_unaccepted"] + breakdown["zero_answers"]

    return ids, next(iter(sizes)), len(eligible), breakdown


def _session() -> str:
    """The one research session in this workspace, or a refusal."""
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM research.research_sessions WHERE workspace_id = %s ORDER BY id",
            (WORKSPACE_ID,),
        )
        rows = [str(row[0]) for row in cur.fetchall()]
    if len(rows) != 1:
        raise SystemExit(
            f"expected exactly one research session in {WORKSPACE_ID}, found {len(rows)}. "
            "Choosing between them is a decision this script must not make silently"
        )
    return rows[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="persist; otherwise plan only")
    args = parser.parse_args(argv)

    _load_env()
    if "DATABASE_URL" not in os.environ:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    sys.path.insert(0, str(ROOT / "services" / "nlp" / "python"))
    from sros_nlp.claim_job import run_claim_interpretation_job
    from sros_nlp.job import run_signal_derivation_job

    ids, page_size, carrying, breakdown = _inputs()
    print(f"records from the tagged={TAG!r} retrieval : {len(ids)}")
    print(f"    of those, carrying the tag itself    : {carrying}")
    print(f"    page size the retrieval asked for    : {page_size}")
    print(f"    acceptance flag missing on           : {breakdown['missing']}")
    print(f"    accepted answer present              : {breakdown['accepted']}")
    print(f"    answered, none accepted              : {breakdown['answered_unaccepted']}")
    print(f"    zero answers received                : {breakdown['zero_answers']}")
    print(f"    -> NO accepted answer (the signal)   : {breakdown['unaccepted']}")
    print(
        f"    truncation excluded                  : "
        f"{'yes, the page came back short' if len(ids) < page_size else 'NO -- a full page'}"
    )

    if not args.apply:
        print("\n--plan: nothing written. Re-run with --apply to persist.")
        return 0

    # The EXISTING session, not a new one. A research session is LINEAGE and
    # never identity (Ontology V2 §12): every one of the 26 existing Signals was
    # derived under this session, and creating a second would make one corpus
    # look like two discoveries. If the workspace ever holds more than one, this
    # refuses rather than picking.
    session_id = _session()
    print(f"\nreusing research session {session_id} (lineage, never identity)")

    factory = _factory(commit=True)

    derivation = run_signal_derivation_job(
        {
            "workspace_id": WORKSPACE_ID,
            "research_session_id": session_id,
            "correlation_id": CORRELATION_ID,
            "extractor_id": "community-question-without-accepted-answer",
            "parameters": {"tag": TAG, "retrieval_page_size": page_size},
            "normalized_record_ids": ids,
            "source_id": SOURCE_ID,
        },
        factory,
    )
    print("\n--- derivation")
    print(json.dumps(derivation.to_json(), indent=2, default=str)[:1600])
    if not derivation.persisted.signal_ids:
        print("no Signal was created; stopping before interpretation", file=sys.stderr)
        return 1

    interpretation = run_claim_interpretation_job(
        {
            "workspace_id": WORKSPACE_ID,
            "research_session_id": session_id,
            "correlation_id": CORRELATION_ID,
            "interpreter_id": "observed-signal-restatement",
            "signal_ids": list(derivation.persisted.signal_ids),
        },
        factory,
    )
    print("\n--- interpretation")
    print(json.dumps(interpretation.to_json(), indent=2, default=str)[:1800])
    print(f"\nsession {session_id} at {datetime.now(UTC).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
