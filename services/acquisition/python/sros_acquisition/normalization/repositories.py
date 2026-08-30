"""Reading raw records and persisting normalized ones.

Mission 1.6 §22–§24, §29–§31, §35.

Four outcomes per raw record, and telling them apart is the whole job:

    NEW          the first normalized representation of this observation under
                 this (schema, normalizer) lineage
    REVISED      a LATER raw version of an observation already normalized under
                 this lineage. A new row; the previous one is marked superseded
                 rather than overwritten -- economic data is revised, and both
                 statements are true about when the source made them
    UNCHANGED    this exact identity is already stored with this exact content.
                 Nothing is written. That is what makes duplicate Celery
                 delivery safe (§35) without claiming exactly-once
    CONFLICT     this exact identity is already stored with DIFFERENT content.
                 Nothing is written, and it is reported

`CONFLICT` deserves its own paragraph, because "just overwrite" is the tempting
answer and it is wrong. The identity says *this is the same representation*: the
same raw record, the same schema version, the same normalizer version. If the
content differs, either the normalizer is not deterministic or a reviewed input
it reads changed without the version being bumped. Overwriting would destroy the
stored representation, which §24 forbids; inserting would need an identity that
distinguishes them, which is exactly what a version bump is. So the row stands,
the mismatch is reported, and **bumping the normalizer version is the mechanism
by which output is allowed to change**.

**Writes go through a tenant transaction.** The explicit `workspace_id` filter
is layer one and RLS is layer two (ADR-012); the composite foreign key added in
migration 0009 is layer three, and none replaces another.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from .model import NormalizedRecordDraft as Draft
from .model import RawRecordView

__all__ = [
    "NormalizationOutcome",
    "PersistenceReport",
    "count_normalized",
    "persist_normalized",
    "read_normalized_history",
    "read_raw_records",
]


class NormalizationOutcome(StrEnum):
    NEW = "NEW"
    REVISED = "REVISED"
    UNCHANGED = "UNCHANGED"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class PersistenceReport:
    new: int = 0
    revised: int = 0
    unchanged: int = 0
    conflicted: int = 0
    record_ids: tuple[str, ...] = field(default=())
    conflicts: tuple[str, ...] = field(default=())

    @property
    def total(self) -> int:
        return self.new + self.revised + self.unchanged + self.conflicted

    def describe(self) -> str:
        return (
            f"{self.total} record(s): {self.new} new, {self.revised} revised, "
            f"{self.unchanged} unchanged, {self.conflicted} conflicted"
        )

    def to_json(self) -> dict[str, object]:
        return {
            "new": self.new,
            "revised": self.revised,
            "unchanged": self.unchanged,
            "conflicted": self.conflicted,
            "total": self.total,
            "conflicts": list(self.conflicts),
        }


# ------------------------------------------------------------------- reading


_RAW_COLUMNS = """
    r.id, r.workspace_id, r.research_session_id, r.source_id, r.observation_key,
    r.content_hash, r.acquisition_method, r.payload::text, r.provenance::text,
    r.review_version, r.collector_id, r.collector_version, r.correlation_id,
    r.collected_at, r.observed_at, r.expires_at
"""


def _view(row: Sequence[Any]) -> RawRecordView:
    # §13. The payload is parsed from its JSON **text** with
    # `parse_float=Decimal`, never from an already-parsed float. A value that
    # has been through IEEE-754 once may already differ from what the source
    # sent, and re-reading it would bake the difference in rather than avoid it.
    payload = json.loads(row[7], parse_float=Decimal) if row[7] else {}
    provenance = json.loads(row[8]) if row[8] else {}
    return RawRecordView(
        record_id=str(row[0]),
        workspace_id=str(row[1]),
        research_session_id=str(row[2]) if row[2] else None,
        source_id=row[3],
        observation_key=row[4],
        content_hash=row[5],
        acquisition_method=row[6],
        payload=payload,
        provenance=provenance,
        review_version=int(row[9]),
        collector_id=row[10],
        collector_version=row[11],
        correlation_id=row[12],
        collected_at=row[13],
        observed_at=row[14],
        expires_at=row[15],
    )


def read_raw_records(
    conn: Any,
    workspace_id: str,
    *,
    record_ids: Sequence[str] | None = None,
    research_session_id: str | None = None,
    source_id: str | None = None,
    only_unnormalized: bool = False,
    normalizer_id: str | None = None,
    normalizer_version: str | None = None,
    schema_version: int | None = None,
    limit: int = 500,
) -> list[RawRecordView]:
    """The raw records a normalization pass will read.

    `only_unnormalized` is scoped to ONE lineage on purpose. "Already
    normalized" is not a property of a raw record -- it is a property of a raw
    record *under a given normalizer and schema version*. A global flag would
    make a re-normalization under a new version find nothing to do, which is the
    opposite of what §24 asks for.

    `limit` is our own bound (§34) and is always applied. "The caller will pass
    one" is not a bound; the default is.
    """
    clauses = ["r.workspace_id = %s"]
    params: list[Any] = [workspace_id]

    if record_ids:
        clauses.append("r.id = ANY(%s::uuid[])")
        params.append(list(record_ids))
    if research_session_id:
        clauses.append("r.research_session_id = %s")
        params.append(research_session_id)
    if source_id:
        clauses.append("r.source_id = %s")
        params.append(source_id)
    if only_unnormalized:
        clauses.append(
            """NOT EXISTS (
                   SELECT 1 FROM acquisition.normalized_records n
                    WHERE n.workspace_id = r.workspace_id
                      AND n.raw_record_id = r.id
                      AND n.normalizer_id = %s
                      AND n.normalizer_version = %s
                      AND n.normalization_schema_version = %s)"""
        )
        params.extend([normalizer_id, normalizer_version, schema_version])

    params.append(limit)
    # The interpolated parts are the column list and the clause TEMPLATES, both
    # literals in this module. Every caller-supplied value goes through `params`
    # as a bound parameter -- there is no path by which a workspace id, a record
    # id or a source id reaches the string.
    rows = conn.execute(
        f"SELECT {_RAW_COLUMNS} FROM acquisition.raw_records r "  # noqa: S608
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY r.collected_at, r.observation_key LIMIT %s",
        tuple(params),
    ).fetchall()
    return [_view(row) for row in rows]


# ------------------------------------------------------------------- writing


def persist_normalized(conn: Any, drafts: Sequence[Draft]) -> PersistenceReport:
    """Write a batch, and classify each record.

    The caller owns the transaction. §29 requires that a rollback leave no
    partial normalization, and that is a property of the caller's transaction
    rather than of anything savepointed here: half a batch is not a smaller
    success, it is a batch whose lineage is now incomplete.
    """
    counts = dict.fromkeys(NormalizationOutcome, 0)
    ids: list[str] = []
    conflicts: list[str] = []

    for draft in drafts:
        outcome = _persist_one(conn, draft)
        counts[outcome] += 1
        if outcome is NormalizationOutcome.CONFLICT:
            conflicts.append(draft.raw_record_id)
        else:
            ids.append(str(draft.record_id))

    return PersistenceReport(
        new=counts[NormalizationOutcome.NEW],
        revised=counts[NormalizationOutcome.REVISED],
        unchanged=counts[NormalizationOutcome.UNCHANGED],
        conflicted=counts[NormalizationOutcome.CONFLICT],
        record_ids=tuple(ids),
        conflicts=tuple(conflicts),
    )


def _persist_one(conn: Any, draft: Draft) -> NormalizationOutcome:
    # 1. Is this exact representation already stored? The identity is the
    #    unique constraint from migration 0009: raw record plus both versions.
    existing = conn.execute(
        """SELECT id, content_hash FROM acquisition.normalized_records
            WHERE workspace_id = %s AND raw_record_id = %s
              AND normalization_schema_version = %s
              AND normalizer_id = %s AND normalizer_version = %s""",
        (
            draft.workspace_id,
            draft.raw_record_id,
            draft.normalization_schema_version,
            draft.normalizer_id,
            draft.normalizer_version,
        ),
    ).fetchone()
    if existing is not None:
        # §23. A redelivery writes NOTHING. Idempotency without a claim of
        # exactly-once delivery, which Celery does not provide (ADR-004).
        if existing[1] == draft.content_hash:
            return NormalizationOutcome.UNCHANGED
        # See the module docstring. The stored representation stands.
        return NormalizationOutcome.CONFLICT

    # 2. Supersede STRICTLY EARLIER siblings in the SAME lineage.
    #
    #    Same lineage, because writing schema 2 must not retire schema 1 -- that
    #    would be the "which version should downstream use" policy §49 forbids
    #    inventing (D-08).
    #
    #    Strictly earlier, because a batch may reach an older raw version after
    #    a newer one. Without the bound, normalizing out of order would retire
    #    the newer representation and leave the older one current.
    superseded = conn.execute(
        """UPDATE acquisition.normalized_records
              SET superseded_at = %s
            WHERE workspace_id = %s AND source_id = %s AND observation_key = %s
              AND normalization_schema_version = %s
              AND normalizer_id = %s AND normalizer_version = %s
              AND superseded_at IS NULL
              AND collected_at < %s
        RETURNING id""",
        (
            draft.collected_at,
            draft.workspace_id,
            draft.source_id,
            draft.observation_key,
            draft.normalization_schema_version,
            draft.normalizer_id,
            draft.normalizer_version,
            draft.collected_at,
        ),
    ).fetchall()

    # 3. Is there a LATER sibling already? Then this row arrives superseded, so
    #    "the current representation of this observation" stays answerable
    #    whatever order a batch happened to run in (§48).
    later = conn.execute(
        """SELECT min(collected_at) FROM acquisition.normalized_records
            WHERE workspace_id = %s AND source_id = %s AND observation_key = %s
              AND normalization_schema_version = %s
              AND normalizer_id = %s AND normalizer_version = %s
              AND collected_at > %s""",
        (
            draft.workspace_id,
            draft.source_id,
            draft.observation_key,
            draft.normalization_schema_version,
            draft.normalizer_id,
            draft.normalizer_version,
            draft.collected_at,
        ),
    ).fetchone()
    superseded_at: datetime | None = later[0] if later else None

    conn.execute(
        """INSERT INTO acquisition.normalized_records
               (id, workspace_id, raw_record_id, research_session_id, source_id,
                extraction_method, normalizer_id, normalizer_version,
                normalization_schema_id, normalization_schema_version,
                record_kind_registry, record_kind_id, payload, content_hash,
                content_language, observation_key, superseded_at, provenance,
                quality, quality_reasons, correlation_id, collector_id,
                collector_version, review_version,
                observed_at, collected_at, normalized_at, expires_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                   %s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            draft.record_id,
            draft.workspace_id,
            draft.raw_record_id,
            draft.research_session_id,
            draft.source_id,
            draft.extraction_method,
            draft.normalizer_id,
            draft.normalizer_version,
            draft.normalization_schema_id,
            draft.normalization_schema_version,
            draft.record_kind_registry,
            draft.record_kind_id,
            json.dumps(draft.payload, sort_keys=True),
            draft.content_hash,
            draft.content_language,
            draft.observation_key,
            superseded_at,
            json.dumps(draft.provenance, sort_keys=True),
            draft.quality.value,
            json.dumps([r.to_json() for r in draft.quality_reasons], sort_keys=True),
            draft.correlation_id,
            draft.collector_id,
            draft.collector_version,
            draft.review_version,
            draft.observed_at,
            draft.collected_at,
            draft.normalized_at,
            draft.expires_at,
        ),
    )
    return NormalizationOutcome.REVISED if superseded else NormalizationOutcome.NEW


# ------------------------------------------------------------------- queries


def read_normalized_history(
    conn: Any, workspace_id: str, observation_key: str
) -> list[dict[str, object]]:
    """Every normalized representation of one observation, newest first.

    The query §48 and §49 exist to make possible. Deliberately NOT filtered to
    one lineage: the point is that several normalizer and schema versions
    coexist and can all be seen. Which one a consumer should read is D-08, open,
    and this function takes no position on it.
    """
    rows = conn.execute(
        """SELECT id, raw_record_id, content_hash, quality, normalizer_id,
                  normalizer_version, normalization_schema_version,
                  observed_at, collected_at, normalized_at, superseded_at, payload
             FROM acquisition.normalized_records
            WHERE workspace_id = %s AND observation_key = %s
            ORDER BY normalized_at DESC, collected_at DESC""",
        (workspace_id, observation_key),
    ).fetchall()
    return [
        {
            "id": str(r[0]),
            "raw_record_id": str(r[1]),
            "content_hash": r[2],
            "quality": r[3],
            "normalizer": f"{r[4]}@{r[5]}",
            "schema_version": r[6],
            "observed_at": r[7],
            "collected_at": r[8],
            "normalized_at": r[9],
            "superseded_at": r[10],
            "current": r[10] is None,
            "payload": r[11],
        }
        for r in rows
    ]


def count_normalized(conn: Any, workspace_id: str, source_id: str | None = None) -> int:
    return int(
        conn.execute(
            """SELECT count(*) FROM acquisition.normalized_records
                WHERE workspace_id = %s AND (%s::text IS NULL OR source_id = %s::text)""",
            (workspace_id, source_id, source_id),
        ).fetchone()[0]
    )
