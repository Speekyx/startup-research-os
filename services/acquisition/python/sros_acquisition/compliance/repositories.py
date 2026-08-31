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

from sros_contracts import ConditionVerification, ConditionVerificationResult

from .verification import AWAITING_HUMAN_VERIFIER, ConditionVerificationRecord

__all__ = [
    "VerificationReport",
    "read_condition_states",
    "read_human_decisions",
    "record_verifications",
]

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
    # Human conditions a machine pass declined to answer. Reported rather than
    # counted as "unknown", because nothing was written for them and a reader
    # deserves to know the difference between "checked and could not tell" and
    # "deliberately not touched" (Mission 1.15.6.2).
    left_to_a_human: tuple[str, ...] = ()

    def describe(self) -> str:
        text = (
            f"{self.recorded} verification(s): {self.satisfied} satisfied, "
            f"{self.unsatisfied} unsatisfied, {self.unknown} unknown"
        )
        if self.left_to_a_human:
            text += (
                f"; {len(self.left_to_a_human)} human condition(s) left untouched "
                "(a machine pass does not answer them, and does not revoke them)"
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
    left_to_a_human: list[str] = []

    for record in records:
        # Mission 1.15.6.2. A machine pass that could not decide a human
        # condition writes NOTHING for it -- not a row, and above all not a
        # cleared boolean.
        #
        # Before this, `verify --apply` turned a recorded operator acceptance
        # into `satisfied = FALSE` because `verify_source` yields UNKNOWN for a
        # human condition and every non-SATISFIED result cleared the flag. The
        # operator had withdrawn nothing; a routine command revoked their
        # decision.
        #
        # The distinction §12 asks for lives here: ABSENCE of a human result is
        # not a negative human result. A person recording a withdrawal writes a
        # row under their own identifier, which is `is_human_decision`, which
        # passes straight through this branch and clears the flag as it should.
        if record.awaits_human_decision:
            left_to_a_human.append(record.condition_key)
            continue

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
        left_to_a_human=tuple(left_to_a_human),
    )


def read_human_decisions(
    conn: Any, source_id: str, use_profile_id: str, review_version: int
) -> tuple[ConditionVerificationRecord, ...]:
    """Every decision a PERSON recorded for one (source, profile, review).

    Mission 1.15.6.2. This is the persisted half of the effective verification
    state, and the only half that is read from the database rather than
    re-evaluated. `resolve_effective_verifications` composes it with the live
    machine results.

    Three filters, and each is the query doing what the resolver would otherwise
    have to trust:

    * `verification = 'HUMAN_CONFIRMATION'` -- machine results are re-run, never
      read back, so a stale capability row can never authorise anything;
    * `verifier <> AWAITING_HUMAN_VERIFIER` -- the placeholder is not a decision.
      No row with it should exist after Mission 1.15.6.2, and filtering rather
      than assuming keeps rows written before it harmless;
    * the exact review version -- an acceptance belongs to the review it was
      made about, and a superseded one stays as history without satisfying
      anything current.

    Ordered oldest to newest so a caller keeping the last wins; the resolver
    compares timestamps rather than relying on it.
    """
    rows = conn.execute(
        """SELECT v.condition_key, v.verifier, v.verifier_version, v.result, v.reason,
                  v.reference, v.verified_at, r.review_version
             FROM registry.source_condition_verifications v
             JOIN registry.source_review_conditions c ON c.id = v.condition_id
             JOIN registry.source_policy_reviews r ON r.id = c.review_id
            WHERE v.source_id = %s
              AND r.assessed_use_profile = %s
              AND r.review_version = %s
              AND c.verification = 'HUMAN_CONFIRMATION'
              AND v.verifier <> %s
            ORDER BY v.verified_at""",
        (source_id, use_profile_id, review_version, AWAITING_HUMAN_VERIFIER),
    ).fetchall()
    return tuple(
        ConditionVerificationRecord(
            source_id=source_id,
            review_version=row[7],
            condition_key=row[0],
            verification=ConditionVerification.HUMAN_CONFIRMATION,
            verifier=row[1],
            verifier_version=row[2],
            result=ConditionVerificationResult(row[3]),
            reason=row[4],
            reference=row[5],
            verified_at=row[6],
        )
        for row in rows
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
