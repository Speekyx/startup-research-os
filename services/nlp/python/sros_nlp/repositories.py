"""Reading normalized records, and writing signals, lineage and run records.

`signal-derivation-runtime-v1.md` §5. Three outcomes per signal, mirroring the
normalization layer's four:

    NEW         the first time this derivation identity was stored
    UNCHANGED   this exact derivation fingerprint is already stored, byte for
                byte. Nothing is written -- what makes redelivery safe
    CONFLICT    the fingerprint is stored with DIFFERENT content. Nothing is
                written, and it is reported

`CONFLICT` means the extractor is not deterministic, or an input it read changed
without the version being bumped. The stored row stands, and **bumping the
extractor version is the mechanism by which output is allowed to change** --
exactly the rule `persist_normalized` follows one level down.

**A Signal never exists without its lineage.** The signal row, its
`signal_inputs` rows and the run record are written in the caller's transaction,
so a rollback leaves none of them rather than a signal citing nothing.

**Writes go through a tenant transaction.** The explicit `workspace_id` filter
is layer one and RLS is layer two (ADR-012); the composite foreign keys from
migration 0012 are layer three, and none replaces another.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from sros_contracts import NormalizationQualityReason, NormalizedRecordQuality
from sros_signal_model import SignalDraft, canonical_json

from .observations import NormalizedObservation

__all__ = [
    "DerivationRunRecord",
    "SignalOutcome",
    "SignalPersistenceReport",
    "count_signals",
    "persist_run",
    "persist_signals",
    "read_normalized_observations",
]

_OBSERVATION_COLUMNS = (
    "n.id, n.raw_record_id, n.source_id, n.observation_key, n.record_kind_id, "
    "n.quality, n.quality_reasons, n.payload"
)


class SignalOutcome(StrEnum):
    NEW = "NEW"
    UNCHANGED = "UNCHANGED"
    CONFLICT = "CONFLICT"


@dataclass
class SignalPersistenceReport:
    new: int = 0
    unchanged: int = 0
    conflicted: int = 0
    signal_ids: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        return {
            "new": self.new,
            "unchanged": self.unchanged,
            "conflicted": self.conflicted,
            "signal_ids": list(self.signal_ids),
            "conflicts": list(self.conflicts),
        }


@dataclass(frozen=True)
class DerivationRunRecord:
    """One extractor EXECUTION, not one logical job.

    Delivery is at-least-once (ADR-004), so a redelivery writes a second run row
    while writing zero new signals. That is the honest record of what happened:
    the SIGNALS are what is idempotent.
    """

    workspace_id: str
    extractor_id: str
    extractor_version: str
    signal_type_id: str
    parameter_fingerprint: str
    correlation_id: str
    started_at: datetime
    finished_at: datetime
    expires_at: datetime
    research_session_id: str | None = None
    groups_considered: int = 0
    groups_derived: int = 0
    groups_refused: int = 0
    signals_new: int = 0
    signals_unchanged: int = 0
    signals_conflicted: int = 0
    records_considered: int = 0
    records_contributed: int = 0
    records_excluded: int = 0
    refusals: tuple[dict[str, object], ...] = field(default=())
    truncated_by: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "extractor": f"{self.extractor_id}@{self.extractor_version}",
            "signal_type_id": self.signal_type_id,
            "parameter_fingerprint": self.parameter_fingerprint,
            "groups_considered": self.groups_considered,
            "groups_derived": self.groups_derived,
            "groups_refused": self.groups_refused,
            "signals_new": self.signals_new,
            "signals_unchanged": self.signals_unchanged,
            "signals_conflicted": self.signals_conflicted,
            "records_considered": self.records_considered,
            "records_contributed": self.records_contributed,
            "records_excluded": self.records_excluded,
            "refusals": [dict(r) for r in self.refusals],
            "truncated_by": self.truncated_by,
        }


# ------------------------------------------------------------------- reading


def read_normalized_observations(
    conn: Any,
    workspace_id: str,
    *,
    record_kind_id: str,
    record_ids: Sequence[str] | None = None,
    research_session_id: str | None = None,
    source_id: str | None = None,
    limit: int = 500,
) -> list[NormalizedObservation]:
    """The canonical observations a derivation pass will read.

    **Superseded rows are excluded.** A superseded row is an earlier raw version
    of an observation that has since been revised; reading both would put two
    rows for one `observation_key` in front of the extractor, which the model
    refuses as `AMBIGUOUS_OBSERVATION_LINEAGE`. Excluding the retired one is not
    a choice between lineages -- D-08 is about coexisting NORMALIZER versions,
    and those are both current, both read, and correctly refused.

    `limit` is our own bound and is always applied. "The caller will pass one"
    is not a bound; the default is.
    """
    clauses = ["n.workspace_id = %s", "n.record_kind_id = %s", "n.superseded_at IS NULL"]
    params: list[Any] = [workspace_id, record_kind_id]

    if record_ids:
        clauses.append("n.id = ANY(%s::uuid[])")
        params.append(list(record_ids))
    if research_session_id:
        clauses.append("n.research_session_id = %s")
        params.append(research_session_id)
    if source_id:
        clauses.append("n.source_id = %s")
        params.append(source_id)
    params.append(limit)

    # The interpolated parts are the column list and the clause TEMPLATES, both
    # literals in this module. Every caller-supplied value goes through `params`
    # as a bound parameter.
    rows = conn.execute(
        f"SELECT {_OBSERVATION_COLUMNS} "  # noqa: S608 - see above
        "FROM acquisition.normalized_records n "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY n.source_id, n.observation_key LIMIT %s",
        tuple(params),
    ).fetchall()
    return [_observation(row) for row in rows]


def _observation(row: Sequence[Any]) -> NormalizedObservation:
    reasons: set[NormalizationQualityReason] = set()
    for entry in row[6] or ():
        code = entry.get("code") if isinstance(entry, dict) else entry
        try:
            reasons.add(NormalizationQualityReason(code))
        except ValueError:
            # A reason this build does not know is DROPPED rather than guessed
            # at. The required-fact check then cannot see it, so the record is
            # treated as supplying the fact -- which is why an unknown reason is
            # a contract drift to fix rather than tolerate, and why
            # validate_schema compares the enum against the contract.
            continue
    return NormalizedObservation(
        normalized_record_id=str(row[0]),
        raw_record_id=str(row[1]),
        source_id=str(row[2]),
        observation_key=str(row[3]),
        record_kind_id=str(row[4]),
        quality=NormalizedRecordQuality(str(row[5])),
        quality_reasons=frozenset(reasons),
        payload=row[7] or {},
    )


def count_signals(conn: Any, workspace_id: str) -> int:
    row = conn.execute(
        "SELECT count(*) FROM nlp.signals WHERE workspace_id = %s", (workspace_id,)
    ).fetchone()
    return int(row[0]) if row else 0


# ------------------------------------------------------------------- writing


def persist_signals(conn: Any, drafts: Sequence[SignalDraft]) -> SignalPersistenceReport:
    """Write a batch of signals with their lineage, and classify each one."""
    report = SignalPersistenceReport()
    ids: list[str] = []
    conflicts: list[str] = []

    for draft in drafts:
        outcome = _persist_one(conn, draft)
        if outcome is SignalOutcome.NEW:
            report.new += 1
            ids.append(draft.id)
        elif outcome is SignalOutcome.UNCHANGED:
            report.unchanged += 1
            ids.append(draft.id)
        else:
            report.conflicted += 1
            conflicts.append(draft.derivation_fingerprint)

    report.signal_ids = tuple(ids)
    report.conflicts = tuple(conflicts)
    return report


def _persist_one(conn: Any, draft: SignalDraft) -> SignalOutcome:
    # 1. Is this exact derivation already stored? The identity is the unique
    #    constraint from migration 0012.
    existing = conn.execute(
        """SELECT id, magnitude, direction FROM nlp.signals
            WHERE workspace_id = %s AND derivation_fingerprint = %s""",
        (draft.workspace_id, draft.derivation_fingerprint),
    ).fetchone()
    if existing is not None:
        stored_magnitude, stored_direction = existing[1], existing[2]
        same = (
            stored_magnitude == draft.magnitude.value and stored_direction == draft.direction.value
        )
        # A redelivery writes NOTHING. Idempotent persistence without a claim of
        # exactly-once delivery, which Celery does not provide (ADR-004).
        return SignalOutcome.UNCHANGED if same else SignalOutcome.CONFLICT

    conn.execute(
        """INSERT INTO nlp.signals (
               id, workspace_id, research_session_id,
               quantity_family, signal_type_registry, signal_type_id,
               magnitude, magnitude_kind, magnitude_unit, magnitude_unit_state,
               direction, derivation_confidence,
               extractor_id, extractor_version, signal_schema_id, signal_schema_version,
               derivation_kind, model_version, prompt_version, extraction_method,
               parameters, parameter_fingerprint, derivation_fingerprint,
               scope, temporal_basis, temporal_window,
               correlation_id, observed_at, derived_at, expires_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                   %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            draft.id,
            draft.workspace_id,
            draft.research_session_id,
            draft.quantity_family.value,
            draft.signal_type_registry,
            draft.signal_type_id,
            draft.magnitude.value,
            draft.magnitude.kind.value,
            draft.magnitude.unit,
            draft.magnitude.unit_state.value,
            draft.direction.value,
            draft.derivation_confidence,
            draft.derivation.extractor_id,
            draft.derivation.extractor_version,
            _SCHEMA_ID,
            _SCHEMA_VERSION,
            draft.derivation.kind.value,
            draft.derivation.model_version,
            draft.derivation.prompt_version,
            f"{draft.derivation.extractor_id}@{draft.derivation.extractor_version}",
            json.dumps(draft.derivation.parameters_json(), sort_keys=True),
            draft.parameter_fingerprint,
            draft.derivation_fingerprint,
            json.dumps(draft.scope.to_json(), sort_keys=True),
            draft.window.basis.value,
            json.dumps(draft.window.to_json(), sort_keys=True),
            draft.correlation_id,
            draft.observed_at,
            draft.derived_at,
            draft.expires_at,
        ),
    )

    for position, assessed in enumerate(draft.inputs):
        observation = assessed.observation
        conn.execute(
            """INSERT INTO nlp.signal_inputs (
                   id, workspace_id, signal_id, normalized_record_id, raw_record_id,
                   source_id, observation_key, record_kind_registry, record_kind_id,
                   period_label, period_type, input_quality, input_quality_reasons,
                   role, refusal_reason, withheld_facts, input_position)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                str(uuid.uuid5(_INPUT_NAMESPACE, f"{draft.id}|{position}")),
                draft.workspace_id,
                draft.id,
                observation.normalized_record_id,
                observation.raw_record_id,
                observation.source_id,
                observation.observation_key,
                _RECORD_KIND_REGISTRY,
                observation.record_kind_id,
                observation.period_label,
                observation.period_type.value,
                observation.quality.value,
                json.dumps(sorted(r.value for r in observation.quality_reasons)),
                assessed.role.value,
                assessed.refusal_reason.value if assessed.refusal_reason else None,
                json.dumps(sorted(f.value for f in assessed.withheld)),
                position,
            ),
        )
    return SignalOutcome.NEW


def persist_run(conn: Any, run: DerivationRunRecord) -> str:
    """The run record, written in the same transaction as its signals.

    A random id, deliberately: this is an EVENT. Two executions of one logical
    job are two things that happened, and a deterministic id would silently
    overwrite the first with the second.
    """
    run_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO nlp.signal_derivation_runs (
               id, workspace_id, research_session_id,
               extractor_id, extractor_version, signal_type_registry, signal_type_id,
               parameter_fingerprint,
               groups_considered, groups_derived, groups_refused,
               signals_new, signals_unchanged, signals_conflicted,
               records_considered, records_contributed, records_excluded,
               refusals, truncated_by, correlation_id,
               started_at, finished_at, expires_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                   %s, %s, %s, %s, %s, %s)""",
        (
            run_id,
            run.workspace_id,
            run.research_session_id,
            run.extractor_id,
            run.extractor_version,
            _SIGNAL_TYPE_REGISTRY,
            run.signal_type_id,
            run.parameter_fingerprint,
            run.groups_considered,
            run.groups_derived,
            run.groups_refused,
            run.signals_new,
            run.signals_unchanged,
            run.signals_conflicted,
            run.records_considered,
            run.records_contributed,
            run.records_excluded,
            canonical_json([dict(r) for r in run.refusals]),
            run.truncated_by,
            run.correlation_id,
            run.started_at,
            run.finished_at,
            run.expires_at,
        ),
    )
    return run_id


_SCHEMA_ID = "sros.signal"
_SCHEMA_VERSION = 1
_RECORD_KIND_REGISTRY = "normalization_record_kind"
_SIGNAL_TYPE_REGISTRY = "signal_type"
# Deterministic input ids, so a re-insert of one signal's lineage converges
# rather than accumulating parallel rows.
_INPUT_NAMESPACE = uuid.UUID("2a7f4c98-51de-5b36-9c04-8e13a6d7f025")
