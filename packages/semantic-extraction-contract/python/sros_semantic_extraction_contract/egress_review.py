"""Human egress review: working decisions, strict validation and import (Mission 1.85.6).

Policy REVIEW_OR_EXCLUDE_NO_REDACTION, unchanged: `egress.py` stays the only definition of what a
decision is and how eligibility is derived. This module adds the practical path from a person's review
to that decision file, and decides nothing itself:

- a WORKING decision file lives outside the repository, next to the exact surfaces;
- `make_decision` and `make_bulk_decision` only turn an explicit operator choice into the contract's
  structure, and refuse a choice the contract would not accept (an approving reason on an exclusion, a
  bulk approval of a triggered record, a secret-like approval by any reason but an individual
  TRIGGER_REVIEWED_NOT_PERSONAL). Nothing here produces a choice nobody made;
- `validate_working_decisions` re-checks the whole file against a freshly computed scan before import,
  and refuses rather than repairs;
- `committed_decisions` builds the canonical decision document from a valid, complete working file.

A trigger is a reason to look, never a finding. Zero triggers is not "safe": a zero-trigger record still
needs a human decision, individual or an explicitly confirmed bulk set.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from .annotation import _MODEL_LIKE_IDS
from .egress import (
    _APPROVING,
    DECISION_ORIGINS,
    SCAN_ID,
    SCAN_VERSION,
    DecisionReason,
    EgressDecisionError,
    EgressState,
    derive_egress_eligibility,
    load_decisions,
    pattern_table_sha256,
)
from .surface import SURFACE_ID, SURFACE_VERSION

__all__ = [
    "APPROVING_REASONS",
    "EXCLUDING_REASONS",
    "INDIVIDUAL_APPROVING_REASONS",
    "POLICY",
    "WORKING_FORMAT",
    "ChoiceRefusedError",
    "blank_working_file",
    "check_operator",
    "committed_decisions",
    "make_bulk_decision",
    "make_decision",
    "record_set_sha256",
    "reviewable_records",
    "unresolved_record_ids",
    "validate_working_decisions",
    "zero_trigger_unresolved_ids",
]

POLICY = "REVIEW_OR_EXCLUDE_NO_REDACTION"
WORKING_FORMAT = "semantic-egress-review-working@1"
HUMAN = DECISION_ORIGINS[0]
INDIVIDUAL_APPROVING_REASONS = (
    DecisionReason.TRIGGER_REVIEWED_NOT_PERSONAL.value,
    DecisionReason.TRIGGER_REVIEWED_PUBLIC_REFERENCE.value,
)
APPROVING_REASONS = tuple(sorted(r.value for r in _APPROVING))
EXCLUDING_REASONS = tuple(sorted(r.value for r in DecisionReason if r not in _APPROVING))
CONFIRMATION = "I reviewed exactly these {n} zero-trigger records and approve them"


class ChoiceRefusedError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}{': ' + detail if detail else ''}")
        self.code = code


def record_set_sha256(ids: list[str]) -> str:
    """The digest `egress.load_decisions` checks: sha256 of the sorted ids joined by newlines."""
    return hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _triggered(record: dict[str, Any]) -> dict[str, int]:
    return {k: v for k, v in record["trigger_counts"].items() if v}


def reviewable_records(
    scan_records: list[dict[str, Any]], committed_doc: dict[str, Any]
) -> list[dict[str, Any]]:
    """Scan rows whose derived state is EGRESS_REVIEW_REQUIRED against the committed decision file.

    A mechanically excluded record is never reviewable: the transport rule dominates any human choice.
    """
    decisions = load_decisions(
        committed_doc, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256()
    )
    derived = {
        row["normalized_record_id"]: row
        for row in derive_egress_eligibility(scan_records, decisions)
    }
    return [
        r
        for r in scan_records
        if derived[r["normalized_record_id"]]["state"] == EgressState.EGRESS_REVIEW_REQUIRED.value
    ]


def blank_working_file(
    operator_id: str, reviewable: list[dict[str, Any]], scan_sha256: str
) -> dict[str, Any]:
    return {
        "$comment": "WORKING egress decisions for ONE human operator, kept OUTSIDE the repository. Written only when the operator clicks a decision in the local review page. Never edit REVIEW_REQUIRED in: it is derived. Import with semantic_egress_review.py import.",
        "format": WORKING_FORMAT,
        "scan": f"{SCAN_ID}@{SCAN_VERSION}",
        "pattern_table_sha256": pattern_table_sha256(),
        "surface": f"{SURFACE_ID}@{SURFACE_VERSION}",
        "policy": POLICY,
        "split": "DEVELOPMENT",
        "operator_id": operator_id,
        "prepared_from_scan_sha256": scan_sha256,
        "reviewable_record_ids": sorted(r["normalized_record_id"] for r in reviewable),
        "decisions": [],
        "bulk_decisions": [],
    }


def check_operator(operator_id: str) -> None:
    lowered = str(operator_id or "").strip().lower()
    if not lowered:
        raise ChoiceRefusedError("OPERATOR_ID_MISSING")
    if lowered in {"unknown", "none", "n/a", "tbd", "operator"} or any(
        m in lowered for m in _MODEL_LIKE_IDS
    ):
        raise ChoiceRefusedError("OPERATOR_ID_NOT_ACCEPTED", "placeholder or model-like identifier")


def _bulk_ids(working: dict[str, Any]) -> set[str]:
    return {
        rid for b in working.get("bulk_decisions", []) for rid in b.get("normalized_record_ids", [])
    }


def make_decision(
    working: dict[str, Any],
    record: dict[str, Any],
    *,
    surface_sha256: str,
    decision: str,
    reason: str,
    decided_at: str | None = None,
) -> dict[str, Any]:
    """Turn ONE explicit operator choice into a contract decision. Refuses what the contract refuses."""
    check_operator(working["operator_id"])
    rid = record["normalized_record_id"]
    if rid not in set(working["reviewable_record_ids"]):
        raise ChoiceRefusedError("RECORD_NOT_REVIEWABLE", rid)
    if surface_sha256 != record["surface_sha256"]:
        raise ChoiceRefusedError("SURFACE_DIGEST_MISMATCH", rid)
    if rid in _bulk_ids(working):
        raise ChoiceRefusedError("RECORD_ALREADY_IN_A_BULK_DECISION", rid)
    if decision == EgressState.EGRESS_APPROVED.value:
        if reason not in INDIVIDUAL_APPROVING_REASONS:
            raise ChoiceRefusedError("REASON_DOES_NOT_SUPPORT_APPROVAL", reason)
        if "secret_like" in _triggered(record) and (
            reason != DecisionReason.TRIGGER_REVIEWED_NOT_PERSONAL.value
        ):
            raise ChoiceRefusedError(
                "SECRET_LIKE_APPROVAL_NEEDS_TRIGGER_REVIEWED_NOT_PERSONAL", rid
            )
    elif decision == EgressState.EGRESS_EXCLUDED.value:
        if reason not in EXCLUDING_REASONS:
            raise ChoiceRefusedError("REASON_DOES_NOT_SUPPORT_EXCLUSION", reason)
    else:
        raise ChoiceRefusedError("DECISION_NOT_RECORDABLE", str(decision))
    return {
        "normalized_record_id": rid,
        "surface_sha256": surface_sha256,
        "decision": decision,
        "reason": reason,
        "decision_origin": HUMAN,
        "decided_by": working["operator_id"],
        "decided_at": decided_at or _now(),
    }


def zero_trigger_unresolved_ids(
    working: dict[str, Any], records: dict[str, dict[str, Any]]
) -> list[str]:
    decided = {d["normalized_record_id"] for d in working.get("decisions", [])} | _bulk_ids(working)
    return sorted(
        rid
        for rid in working["reviewable_record_ids"]
        if rid not in decided and rid in records and not _triggered(records[rid])
    )


def make_bulk_decision(
    working: dict[str, Any],
    records: dict[str, dict[str, Any]],
    *,
    record_ids: list[str],
    surface_sha256: dict[str, str],
    record_set_digest: str,
    confirmation: str,
    decided_at: str | None = None,
) -> dict[str, Any]:
    """An explicitly confirmed approval of an EXACT zero-trigger set. Refused on any mismatch."""
    check_operator(working["operator_id"])
    ids = sorted(record_ids)
    if not ids:
        raise ChoiceRefusedError("BULK_SET_EMPTY")
    if confirmation != CONFIRMATION.format(n=len(ids)):
        raise ChoiceRefusedError(
            "BULK_CONFIRMATION_MISSING", "the exact confirmation sentence is required"
        )
    if record_set_digest != record_set_sha256(ids):
        raise ChoiceRefusedError("BULK_RECORD_SET_DIGEST_MISMATCH")
    triggered = [rid for rid in ids if rid not in records or _triggered(records[rid])]
    if triggered:
        raise ChoiceRefusedError(
            "BULK_SET_CONTAINS_A_TRIGGERED_OR_UNKNOWN_RECORD", ", ".join(triggered)
        )
    if ids != zero_trigger_unresolved_ids(working, records):
        raise ChoiceRefusedError(
            "BULK_SET_IS_NOT_THE_CURRENT_ZERO_TRIGGER_SET",
            "the set changed since it was shown; reload and review it again",
        )
    if set(surface_sha256) != set(ids) or any(
        surface_sha256[rid] != records[rid]["surface_sha256"] for rid in ids
    ):
        raise ChoiceRefusedError("BULK_SURFACE_DIGESTS_MISMATCH")
    at = decided_at or _now()
    return {
        "bulk_decision_id": f"bulk-zero-trigger-{record_set_digest[:12]}",
        "normalized_record_ids": ids,
        "surface_sha256": {rid: surface_sha256[rid] for rid in ids},
        "record_set_sha256": record_set_digest,
        "reason": DecisionReason.BULK_ZERO_TRIGGER_ACCEPTED.value,
        "decision_origin": HUMAN,
        "decided_by": working["operator_id"],
        "decided_at": at,
        "confirmation": confirmation,
    }


def unresolved_record_ids(working: dict[str, Any]) -> list[str]:
    decided = {d["normalized_record_id"] for d in working.get("decisions", [])} | _bulk_ids(working)
    return sorted(set(working.get("reviewable_record_ids", [])) - decided)


def _valid_timestamp(value: Any) -> bool:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_working_decisions(
    working: Any,
    *,
    scan_records: list[dict[str, Any]],
    committed_doc: dict[str, Any],
    holdout_record_ids: set[str],
    require_complete: bool,
) -> list[tuple[str, str]]:
    """Every problem, as (code, detail). Refuses; never repairs. An empty list means importable."""
    problems: list[tuple[str, str]] = []

    def refuse(code: str, detail: str = "") -> None:
        problems.append((code, detail))

    if not isinstance(working, dict):
        return [("NOT_AN_OBJECT", type(working).__name__)]
    if working.get("split") != "DEVELOPMENT":
        refuse("HOLDOUT_OR_UNKNOWN_SPLIT_REFUSED", repr(working.get("split")))
    if working.get("format") != WORKING_FORMAT:
        refuse("WORKING_FORMAT_MISMATCH", repr(working.get("format")))
    if working.get("scan") != f"{SCAN_ID}@{SCAN_VERSION}":
        refuse("SCAN_VERSION_MISMATCH", repr(working.get("scan")))
    if working.get("pattern_table_sha256") != pattern_table_sha256():
        refuse("PATTERN_TABLE_DIGEST_MISMATCH")
    if working.get("surface") != f"{SURFACE_ID}@{SURFACE_VERSION}":
        refuse("SURFACE_VERSION_MISMATCH", repr(working.get("surface")))
    if working.get("policy") != POLICY:
        refuse("POLICY_MISMATCH", repr(working.get("policy")))
    try:
        check_operator(str(working.get("operator_id") or ""))
    except ChoiceRefusedError as exc:
        refuse(exc.code)
    records = {r["normalized_record_id"]: r for r in scan_records}
    reviewable = {
        r["normalized_record_id"] for r in reviewable_records(scan_records, committed_doc)
    }
    mentioned = (
        set(working.get("reviewable_record_ids", []))
        | {str(d.get("normalized_record_id")) for d in working.get("decisions", [])}
        | _bulk_ids(working)
    )
    if mentioned & holdout_record_ids:
        refuse("HOLDOUT_RECORD_REFUSED", ", ".join(sorted(mentioned & holdout_record_ids)))
    if set(working.get("reviewable_record_ids", [])) != reviewable:
        refuse(
            "REVIEWABLE_SET_CHANGED",
            "the working file was prepared against a different scan or decision state; prepare again",
        )

    seen: dict[str, str] = {}
    for raw in working.get("decisions", []):
        rid = str(raw.get("normalized_record_id"))
        if raw.get("decision") == EgressState.EGRESS_REVIEW_REQUIRED.value:
            refuse("REVIEW_REQUIRED_PERSISTED", rid)
            continue
        if rid in seen:
            refuse("DUPLICATE_DECISION", rid)
        seen[rid] = "individual"
        if rid not in records:
            refuse("UNKNOWN_RECORD", rid)
            continue
        if rid not in reviewable:
            refuse(
                "RECORD_NOT_REVIEWABLE",
                f"{rid} (mechanically excluded or already decided in the repository)",
            )
        if raw.get("decision_origin") != HUMAN:
            refuse("ORIGIN_NOT_HUMAN_OPERATOR", rid)
        if (
            raw.get("decided_by") != working.get("operator_id")
            or not str(raw.get("decided_by") or "").strip()
        ):
            refuse("DECIDED_BY_IS_NOT_THE_OPERATOR", rid)
        if not _valid_timestamp(raw.get("decided_at")):
            refuse("TIMESTAMP_INVALID", rid)
        if raw.get("surface_sha256") != records[rid]["surface_sha256"]:
            refuse("SURFACE_DIGEST_STALE", rid)
        decision, reason = raw.get("decision"), raw.get("reason")
        if decision == EgressState.EGRESS_APPROVED.value:
            if reason not in INDIVIDUAL_APPROVING_REASONS:
                refuse("DECISION_REASON_INCOMPATIBLE", f"{rid}: {decision}/{reason}")
            elif "secret_like" in _triggered(records[rid]) and (
                reason != DecisionReason.TRIGGER_REVIEWED_NOT_PERSONAL.value
            ):
                refuse("SECRET_LIKE_APPROVAL_NEEDS_TRIGGER_REVIEWED_NOT_PERSONAL", rid)
        elif decision == EgressState.EGRESS_EXCLUDED.value:
            if reason not in EXCLUDING_REASONS:
                refuse("DECISION_REASON_INCOMPATIBLE", f"{rid}: {decision}/{reason}")
        else:
            refuse("DECISION_NOT_RECORDABLE", f"{rid}: {decision!r}")

    for bulk in working.get("bulk_decisions", []):
        ids = list(bulk.get("normalized_record_ids", []))
        where = str(bulk.get("bulk_decision_id"))
        if ids != sorted(ids):
            refuse("BULK_IDS_NOT_SORTED", where)
        if bulk.get("record_set_sha256") != record_set_sha256(ids):
            refuse("BULK_RECORD_SET_DIGEST_MISMATCH", where)
        if bulk.get("reason") != DecisionReason.BULK_ZERO_TRIGGER_ACCEPTED.value:
            refuse("BULK_REASON_NOT_ZERO_TRIGGER", where)
        if bulk.get("decision_origin") != HUMAN or bulk.get("decided_by") != working.get(
            "operator_id"
        ):
            refuse("BULK_NOT_A_HUMAN_OPERATOR_DECISION", where)
        if not _valid_timestamp(bulk.get("decided_at")):
            refuse("TIMESTAMP_INVALID", where)
        if bulk.get("confirmation") != CONFIRMATION.format(n=len(ids)):
            refuse("BULK_CONFIRMATION_MISSING", where)
        if set(bulk.get("surface_sha256", {})) != set(ids):
            refuse("BULK_SURFACE_DIGESTS_DO_NOT_COVER_ITS_IDS", where)
        for rid in ids:
            if rid in seen:
                refuse("DUPLICATE_INDIVIDUAL_AND_BULK_DECISION", rid)
            seen[rid] = "bulk"
            if rid not in records:
                refuse("UNKNOWN_RECORD", rid)
                continue
            if rid not in reviewable:
                refuse("RECORD_NOT_REVIEWABLE", rid)
            if _triggered(records[rid]):
                refuse("BULK_CONTAINS_A_TRIGGERED_RECORD", rid)
            if bulk.get("surface_sha256", {}).get(rid) != records[rid]["surface_sha256"]:
                refuse("SURFACE_DIGEST_STALE", rid)

    if require_complete:
        missing = sorted(reviewable - set(seen))
        if missing:
            refuse("REVIEW_INCOMPLETE", f"{len(missing)} record(s) have no human decision")
    return problems


def committed_decisions(working: dict[str, Any], committed_doc: dict[str, Any]) -> dict[str, Any]:
    """The canonical decision document: existing committed decisions plus the working file's.

    Called only after `validate_working_decisions` returned no problem. The result is re-parsed by
    `egress.load_decisions`, so a document the contract would refuse is never returned.
    """
    individual_keys = (
        "normalized_record_id",
        "surface_sha256",
        "decision",
        "reason",
        "decision_origin",
        "decided_by",
        "decided_at",
    )
    bulk_keys = (
        "bulk_decision_id",
        "normalized_record_ids",
        "surface_sha256",
        "record_set_sha256",
        "reason",
        "decision_origin",
        "decided_by",
        "decided_at",
    )
    doc = dict(committed_doc)
    doc["decisions"] = sorted(
        [
            *committed_doc.get("decisions", []),
            *({k: d[k] for k in individual_keys} for d in working["decisions"]),
        ],
        key=lambda d: d["normalized_record_id"],
    )
    doc["bulk_decisions"] = [
        *committed_doc.get("bulk_decisions", []),
        *({k: b[k] for k in bulk_keys} for b in working.get("bulk_decisions", [])),
    ]
    try:
        load_decisions(doc, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256())
    except EgressDecisionError as exc:  # pragma: no cover - validation runs first
        raise ChoiceRefusedError("CONTRACT_REFUSED_THE_MERGED_DOCUMENT", str(exc)) from exc
    return doc
