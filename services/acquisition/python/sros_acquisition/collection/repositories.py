"""Persisting raw records: idempotent, revision-aware, tenant-scoped.

Mission 1.5 §21, §23, §24, §30, §44, §45.

Three outcomes per observation, and telling them apart is the whole job:

    UNCHANGED   the same observation with the same content. No new row; the
                existing one's `last_seen_at` moves, so "we checked and it had
                not changed" is still recorded
    REVISED     the same observation with different content. A new row, and the
                previous one is marked superseded rather than overwritten --
                economic data is revised, and both statements are true about
                when the source made them
    NEW         an observation not seen before

`UNCHANGED` is what makes duplicate Celery delivery safe (§30) without claiming
exactly-once: the second delivery finds the row and moves a timestamp.

**Writes go through a tenant transaction.** The explicit `workspace_id` filter
is layer one and RLS is layer two (ADR-012); neither replaces the other, and the
`INSERT ... WHERE workspace_id = %s` here is not redundant with the policy —
it is the layer that fails loudly rather than silently returning nothing.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .records import RawRecordDraft

__all__ = [
    "PersistenceOutcome",
    "collector_enabled",
    "PersistenceReport",
    "count_records",
    "persist_drafts",
    "read_observation_history",
]


class PersistenceOutcome(StrEnum):
    NEW = "NEW"
    UNCHANGED = "UNCHANGED"
    REVISED = "REVISED"


@dataclass(frozen=True)
class PersistenceReport:
    new: int = 0
    unchanged: int = 0
    revised: int = 0
    record_ids: tuple[str, ...] = field(default=())

    @property
    def total(self) -> int:
        return self.new + self.unchanged + self.revised

    def describe(self) -> str:
        return (
            f"{self.total} observation(s): {self.new} new, {self.unchanged} unchanged, "
            f"{self.revised} revised"
        )

    def to_json(self) -> dict[str, object]:
        return {
            "new": self.new,
            "unchanged": self.unchanged,
            "revised": self.revised,
            "total": self.total,
        }


def persist_drafts(conn: Any, drafts: Sequence[RawRecordDraft]) -> PersistenceReport:
    """Write a batch, and classify each observation.

    The caller owns the transaction. §44 requires that a rollback leaves no
    partial acquisition, and that is a property of the caller's transaction
    rather than of anything savepointed here: half a page of observations is not
    a smaller success, it is a page whose provenance is now wrong.
    """
    counts = dict.fromkeys(PersistenceOutcome, 0)
    ids: list[str] = []

    for draft in drafts:
        outcome = _persist_one(conn, draft)
        counts[outcome] += 1
        ids.append(str(draft.record_id))

    return PersistenceReport(
        new=counts[PersistenceOutcome.NEW],
        unchanged=counts[PersistenceOutcome.UNCHANGED],
        revised=counts[PersistenceOutcome.REVISED],
        record_ids=tuple(ids),
    )


def _persist_one(conn: Any, draft: RawRecordDraft) -> PersistenceOutcome:
    # Does this exact content already exist? The unique constraint is
    # (workspace_id, source_id, content_hash) and the fingerprint covers the
    # identifying facts as well as the value, so a hit here means "the same
    # observation, unchanged" and nothing else.
    existing = conn.execute(
        """SELECT id FROM acquisition.raw_records
            WHERE workspace_id = %s AND source_id = %s AND content_hash = %s""",
        (draft.workspace_id, draft.source_id, draft.content_hash),
    ).fetchone()
    if existing is not None:
        # A re-sighting, not a new record. §23: preserve the retrieval history
        # without growing the table once per poll.
        conn.execute(
            """UPDATE acquisition.raw_records
                  SET last_seen_at = GREATEST(last_seen_at, %s)
                WHERE workspace_id = %s AND id = %s""",
            (draft.collected_at, draft.workspace_id, existing[0]),
        )
        return PersistenceOutcome.UNCHANGED

    # Is there an earlier version of this same observation? If so this is an
    # upstream revision, and the previous row is superseded -- never updated in
    # place, because what the source said last year is still true about last
    # year (§24).
    superseded = conn.execute(
        """UPDATE acquisition.raw_records
              SET superseded_at = %s
            WHERE workspace_id = %s AND source_id = %s
              AND observation_key = %s AND superseded_at IS NULL
        RETURNING id""",
        (draft.collected_at, draft.workspace_id, draft.source_id, draft.observation_key),
    ).fetchall()

    conn.execute(
        """INSERT INTO acquisition.raw_records
               (id, workspace_id, research_session_id, source_id, source_reference,
                acquisition_method, content_hash, payload_ref, content_language,
                observation_key, last_seen_at, observed_at, provenance, review_version,
                correlation_id, collector_id, collector_version, payload,
                collected_at, expires_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            draft.record_id,
            draft.workspace_id,
            draft.research_session_id,
            draft.source_id,
            draft.source_reference,
            draft.acquisition_method,
            draft.content_hash,
            draft.payload_ref,
            draft.content_language,
            draft.observation_key,
            draft.collected_at,
            draft.observed_at,
            json.dumps(draft.provenance, sort_keys=True),
            draft.review_version,
            draft.correlation_id,
            draft.collector_id,
            draft.collector_version,
            json.dumps(draft.payload, sort_keys=True),
            draft.collected_at,
            draft.expires_at,
        ),
    )
    return PersistenceOutcome.REVISED if superseded else PersistenceOutcome.NEW


def read_observation_history(
    conn: Any, workspace_id: str, observation_key: str
) -> list[dict[str, object]]:
    """Everything this source has said about one observation, newest first.

    The query §24 exists to make possible. Without `observation_key` a revision
    was an unrelated row and this could not be written at all.
    """
    rows = conn.execute(
        """SELECT id, content_hash, collected_at, last_seen_at, superseded_at,
                  observed_at, payload, collector_version
             FROM acquisition.raw_records
            WHERE workspace_id = %s AND observation_key = %s
            ORDER BY collected_at DESC""",
        (workspace_id, observation_key),
    ).fetchall()
    return [
        {
            "id": str(r[0]),
            "content_hash": r[1],
            "collected_at": r[2],
            "last_seen_at": r[3],
            "superseded_at": r[4],
            "observed_at": r[5],
            "payload": r[6],
            "collector_version": r[7],
            "current": r[4] is None,
        }
        for r in rows
    ]


def count_records(conn: Any, workspace_id: str, source_id: str | None = None) -> int:
    return int(
        conn.execute(
            """SELECT count(*) FROM acquisition.raw_records
                WHERE workspace_id = %s AND (%s::text IS NULL OR source_id = %s::text)""",
            (workspace_id, source_id, source_id),
        ).fetchone()[0]
    )


def collector_enabled(conn: Any, source_id: str) -> bool:
    """Whether the operational switch is on for this source.

    A separate question from eligibility, and deliberately read from the
    DATABASE rather than from the catalog: the catalog loader writes
    `collector_enabled = FALSE` unconditionally, so a catalog can never turn a
    collector on. What is on is a property of the deployment, set by an operator
    through `sros-source enable`, which the database itself refuses for an
    ineligible source.

    `registry.sources` is global and readable by the runtime role, so this works
    inside a tenant transaction without any tenant meaning attaching to it.
    """
    row = conn.execute(
        "SELECT collector_enabled FROM registry.sources WHERE id = %s", (source_id,)
    ).fetchone()
    return bool(row and row[0])
