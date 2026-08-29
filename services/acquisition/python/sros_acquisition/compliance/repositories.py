"""Persisting verification results, and syncing the boolean the gate reads.

Mission 1.4 §18. Two writes per verification, in this order and for a reason:

    1. INSERT the verification record -- who checked, at which version, when,
       what the answer was, why, and what was looked at;
    2. UPDATE `registry.source_review_conditions.satisfied` from it.

The order is enforced by the database. Migration 0007 installs a trigger that
refuses to set `satisfied = TRUE` with no `SATISFIED` verification record for
that condition, so the boolean cannot get ahead of its evidence -- and cannot be
set by hand at all.

**Only SATISFIED clears a condition.** `UNSATISFIED`, `UNKNOWN` and
`NOT_APPLICABLE` all write `satisfied = FALSE` and clear the provenance columns.
That includes the case where a condition was satisfied yesterday and is not
today: re-verification can take a source back out of eligibility, which is the
point of running it again.

**The registry is administered, not served.** These functions run as the
migration role through the CLI, like every other registry write. `registry.*` is
SELECT-only for the runtime role, so no HTTP request can reach them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sros_contracts import ConditionVerificationResult

from .verification import ConditionVerificationRecord

__all__ = ["VerificationReport", "read_condition_states", "record_verifications"]

# The same namespace the registry loader uses, so ids from the two are drawn
# from one space and cannot collide by coincidence.
_NAMESPACE = uuid.UUID("2f1b6d84-5a3e-5c17-9d20-7e4a1f8c3b60")


@dataclass(frozen=True)
class VerificationReport:
    recorded: int
    satisfied: int
    unsatisfied: int
    unknown: int
    missing_conditions: tuple[str, ...] = ()

    def describe(self) -> str:
        text = (
            f"{self.recorded} verification(s): {self.satisfied} satisfied, "
            f"{self.unsatisfied} unsatisfied, {self.unknown} unknown"
        )
        if self.missing_conditions:
            text += f"; {len(self.missing_conditions)} condition(s) not found in the registry"
        return text


def record_verifications(
    conn: Any, records: tuple[ConditionVerificationRecord, ...] | list[ConditionVerificationRecord]
) -> VerificationReport:
    """Write an append-only verification log entry per record, then sync the gate.

    A record whose condition is not in the registry is reported rather than
    inserted. It means the catalog was not loaded, or was loaded at a different
    review version -- and inventing the row would create a condition nobody
    reviewed.
    """
    recorded = 0
    counts = dict.fromkeys(("satisfied", "unsatisfied", "unknown"), 0)
    missing: list[str] = []

    for record in records:
        row = conn.execute(
            """SELECT c.id
                 FROM registry.source_review_conditions c
                 JOIN registry.source_policy_reviews r ON r.id = c.review_id
                WHERE c.source_id = %s
                  AND r.review_version = %s
                  AND c.condition_key = %s""",
            (record.source_id, record.review_version, record.condition_key),
        ).fetchone()
        if row is None:
            missing.append(f"{record.source_id}/{record.review_version}/{record.condition_key}")
            continue
        condition_id = row[0]

        # Append-only: the id includes the moment, so a re-run adds an entry
        # instead of rewriting the previous answer. The history of a condition
        # is part of what makes its current state trustworthy.
        verification_id = uuid.uuid5(
            _NAMESPACE,
            "|".join(
                (
                    "verification",
                    str(condition_id),
                    record.verifier,
                    record.verifier_version,
                    record.verified_at.isoformat(),
                )
            ),
        )
        conn.execute(
            """INSERT INTO registry.source_condition_verifications
                   (id, condition_id, source_id, condition_key, verifier, verifier_version,
                    result, reason, reference, verified_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (id) DO NOTHING""",
            (
                verification_id,
                condition_id,
                record.source_id,
                record.condition_key,
                record.verifier,
                record.verifier_version,
                record.result.value,
                record.reason,
                record.reference,
                record.verified_at,
            ),
        )
        recorded += 1

        if record.result is ConditionVerificationResult.SATISFIED:
            conn.execute(
                """UPDATE registry.source_review_conditions
                      SET satisfied = TRUE,
                          satisfied_at = %s,
                          satisfied_by = %s,
                          satisfaction_reference = %s
                    WHERE id = %s""",
                (record.verified_at, record.verifier, str(verification_id), condition_id),
            )
            counts["satisfied"] += 1
        else:
            # Cleared, not left alone. A condition that stops holding must stop
            # clearing the gate on the next run, and leaving the old TRUE in
            # place would make eligibility a statement about the past.
            conn.execute(
                """UPDATE registry.source_review_conditions
                      SET satisfied = FALSE,
                          satisfied_at = NULL,
                          satisfied_by = NULL,
                          satisfaction_reference = NULL
                    WHERE id = %s""",
                (condition_id,),
            )
            if record.result is ConditionVerificationResult.UNSATISFIED:
                counts["unsatisfied"] += 1
            else:
                counts["unknown"] += 1

    return VerificationReport(
        recorded=recorded,
        satisfied=counts["satisfied"],
        unsatisfied=counts["unsatisfied"],
        unknown=counts["unknown"],
        missing_conditions=tuple(missing),
    )


def read_condition_states(conn: Any, source_id: str) -> list[dict[str, Any]]:
    """Every condition on the current review, with its latest verification.

    A LATERAL join rather than a window function so a condition with no
    verification still appears: "never checked" is a state a reader has to be
    able to see, and an inner join would hide it.
    """
    rows = conn.execute(
        """SELECT c.condition_key, c.description, c.verification, c.verification_detail,
                  c.satisfied, c.satisfied_at, c.satisfied_by,
                  v.verifier, v.verifier_version, v.result, v.reason, v.verified_at
             FROM registry.source_review_conditions c
             JOIN registry.source_policy_reviews r ON r.id = c.review_id
             LEFT JOIN LATERAL (
                 SELECT verifier, verifier_version, result, reason, verified_at
                   FROM registry.source_condition_verifications
                  WHERE condition_id = c.id
                  ORDER BY verified_at DESC, created_at DESC
                  LIMIT 1
             ) v ON TRUE
            WHERE c.source_id = %s AND r.superseded_at IS NULL
            ORDER BY c.condition_key""",
        (source_id,),
    ).fetchall()
    return [
        {
            "condition_key": r[0],
            "description": r[1],
            "verification": r[2],
            "verification_detail": r[3],
            "satisfied": r[4],
            "satisfied_at": r[5],
            "satisfied_by": r[6],
            "latest_verification": (
                {
                    "verifier": r[7],
                    "verifier_version": r[8],
                    "result": r[9],
                    "reason": r[10],
                    "verified_at": r[11],
                }
                if r[7] is not None
                else None
            ),
        }
        for r in rows
    ]
