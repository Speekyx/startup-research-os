"""Residual-identifier scan and egress eligibility, policy REVIEW_OR_EXCLUDE_NO_REDACTION (Mission 1.85.4).

The scan is a REVIEW TRIGGER and nothing more. A regular expression cannot decide that a string is
personal data, and it must not decide that a string is not: a record with no trigger is still waiting
for a human decision. So eligibility is derived, never stored, from three inputs:

    mechanical transmission rule  -> may only EXCLUDE (the transmitted bytes would differ from the surface)
    human decision (HUMAN_OPERATOR) bound to the surface and scan digests -> APPROVED or EXCLUDED
    otherwise                     -> EGRESS_REVIEW_REQUIRED

There is no redaction path. The stored question and the versioned surface are never altered, because a
modified surface would invalidate every quote and offset a finding cites.

The scan runs on the exact surface that would be transmitted. Mission 1.85.3's counts were taken on
title plus unescaped HTML, which is not that text, and are not reused.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .surface import SURFACE_ID, SURFACE_VERSION, surface_sha256

__all__ = [
    "DECISION_ORIGINS",
    "PATTERNS",
    "SCAN_ID",
    "SCAN_VERSION",
    "TRANSPORT_DELIMITER_TOKENS",
    "DecisionReason",
    "EgressDecisionError",
    "EgressState",
    "derive_egress_eligibility",
    "load_decisions",
    "pattern_table_sha256",
    "scan_surface",
    "transmission_integrity_problems",
]

SCAN_ID = "residual-identifier-scan"
SCAN_VERSION = "1.0.0"

# (name, pattern). Triggers, so false positives are accepted: a Python decorator matches at_handle and
# an image digest matches long_token_like, and a human looks at both.
PATTERNS: tuple[tuple[str, str], ...] = (
    ("url", r"(?:https?|ftp)://|\bwww\."),
    ("url_with_userinfo", r"://[^/\s:@]+:[^/\s@]+@"),
    ("email_like", r"[\w.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}"),
    ("ipv4_like", r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    ("ipv6_like", r"\b(?:[0-9A-Fa-f]{1,4}:){4,7}[0-9A-Fa-f]{1,4}\b"),
    ("user_home_path", r"(?:/home/|/Users/|/root\b|[A-Za-z]:[\\/]+Users[\\/]+)[\w.-]*"),
    ("at_handle", r"(?<![\w/@.])@[A-Za-z][\w-]{2,}"),
    ("long_token_like", r"\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{32,}\b"),
    (
        "secret_like",
        r"AKIA[0-9A-Z]{16}|eyJ[\w-]{8,}\.[\w-]{8,}\.|-----BEGIN [A-Z ]*PRIVATE KEY-----"
        r"|(?i:\b(?:password|passwd|secret|api[_-]?key|token|authorization)\b\s*[:=])|Bearer\s+\S{16,}",
    ),
)
_COMPILED = tuple((name, re.compile(pattern)) for name, pattern in PATTERNS)

# The gateway's untrusted region rewrites these, so a surface containing one would be transmitted as
# different bytes than the surface a quote is checked against.
TRANSPORT_DELIMITER_TOKENS = ("<<<", ">>>", "[[delimiter-neutralized]]")

DECISION_ORIGINS = ("HUMAN_OPERATOR",)


class EgressState(StrEnum):
    EGRESS_APPROVED = "EGRESS_APPROVED"
    EGRESS_EXCLUDED = "EGRESS_EXCLUDED"
    EGRESS_REVIEW_REQUIRED = "EGRESS_REVIEW_REQUIRED"


class DecisionReason(StrEnum):
    TRIGGER_REVIEWED_NOT_PERSONAL = "TRIGGER_REVIEWED_NOT_PERSONAL"
    TRIGGER_REVIEWED_PUBLIC_REFERENCE = "TRIGGER_REVIEWED_PUBLIC_REFERENCE"
    BULK_ZERO_TRIGGER_ACCEPTED = "BULK_ZERO_TRIGGER_ACCEPTED"
    CONTAINS_PERSONAL_IDENTIFIER = "CONTAINS_PERSONAL_IDENTIFIER"
    CONTAINS_SECRET_LIKE_VALUE = "CONTAINS_SECRET_LIKE_VALUE"  # noqa: S105 -- a reason code, not a secret
    OPERATOR_DISCRETION = "OPERATOR_DISCRETION"


_APPROVING = {
    DecisionReason.TRIGGER_REVIEWED_NOT_PERSONAL,
    DecisionReason.TRIGGER_REVIEWED_PUBLIC_REFERENCE,
    DecisionReason.BULK_ZERO_TRIGGER_ACCEPTED,
}


class EgressDecisionError(ValueError):
    """A decision file that cannot be trusted is refused whole, never partly applied."""


def pattern_table_sha256() -> str:
    canonical = json.dumps([list(p) for p in PATTERNS], separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def scan_surface(surface: str) -> dict[str, list[tuple[int, int]]]:
    """Offsets of every trigger, by pattern. Offsets never leave local review; counts may be committed."""
    return {
        name: [(m.start(), m.end()) for m in pattern.finditer(surface)]
        for name, pattern in _COMPILED
    }


def transmission_integrity_problems(surface: str) -> list[str]:
    return [
        f"SURFACE_CONTAINS_TRANSPORT_DELIMITER:{token}"
        for token in TRANSPORT_DELIMITER_TOKENS
        if token in surface
    ]


@dataclass(frozen=True)
class EgressDecision:
    normalized_record_id: str
    surface_sha256: str
    decision: EgressState
    reason: DecisionReason
    decided_by: str
    decision_origin: str
    decided_at: str


def load_decisions(
    doc: dict[str, Any], *, scan_id: str, pattern_digest: str
) -> dict[str, EgressDecision]:
    """Parse a human decision file. Every problem is collected; any problem refuses the whole file."""
    problems: list[str] = []
    if (
        doc.get("scan") != f"{scan_id}@{SCAN_VERSION}"
        or doc.get("pattern_table_sha256") != pattern_digest
    ):
        problems.append("decision file names a different scan version or pattern table")
    if doc.get("surface") != f"{SURFACE_ID}@{SURFACE_VERSION}":
        problems.append("decision file names a different surface version")
    decisions: dict[str, EgressDecision] = {}
    bulk_ids: set[str] = set()
    for bulk in doc.get("bulk_decisions", []):
        ids = sorted(bulk.get("normalized_record_ids", []))
        digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
        if bulk.get("record_set_sha256") != digest:
            problems.append(
                f"bulk decision {bulk.get('bulk_decision_id')!r}: record_set_sha256 does not match its ids"
            )
        if (
            bulk.get("decision_origin") not in DECISION_ORIGINS
            or not str(bulk.get("decided_by", "")).strip()
        ):
            problems.append(
                f"bulk decision {bulk.get('bulk_decision_id')!r}: not a recorded human decision"
            )
        if bulk.get("reason") != DecisionReason.BULK_ZERO_TRIGGER_ACCEPTED.value:
            problems.append(
                f"bulk decision {bulk.get('bulk_decision_id')!r}: a bulk decision may only accept zero-trigger records"
            )
        bulk_ids.update(ids)
    for raw in doc.get("decisions", []):
        rid = str(raw.get("normalized_record_id", ""))
        where = f"decision for {rid!r}"
        if raw.get("decision_origin") not in DECISION_ORIGINS:
            problems.append(
                f"{where}: origin {raw.get('decision_origin')!r} is not a human operator"
            )
        if not str(raw.get("decided_by", "")).strip() or not str(raw.get("decided_at", "")).strip():
            problems.append(f"{where}: decided_by and decided_at are required")
        try:
            state = EgressState(raw.get("decision"))
            reason = DecisionReason(raw.get("reason"))
        except ValueError:
            problems.append(f"{where}: unknown decision or reason")
            continue
        if state is EgressState.EGRESS_REVIEW_REQUIRED:
            problems.append(f"{where}: REVIEW_REQUIRED is derived, never recorded")
            continue
        if (state is EgressState.EGRESS_APPROVED) != (reason in _APPROVING):
            problems.append(f"{where}: reason {reason.value} does not support {state.value}")
        if rid in decisions:
            problems.append(f"{where}: duplicate")
        decisions[rid] = EgressDecision(
            rid,
            str(raw.get("surface_sha256", "")),
            state,
            reason,
            str(raw.get("decided_by", "")),
            str(raw.get("decision_origin", "")),
            str(raw.get("decided_at", "")),
        )
    for bulk in doc.get("bulk_decisions", []):
        for rid, surface_digest in bulk.get("surface_sha256", {}).items():
            if rid in decisions:
                problems.append(f"record {rid!r} has both an individual and a bulk decision")
                continue
            decisions[rid] = EgressDecision(
                rid,
                surface_digest,
                EgressState.EGRESS_APPROVED,
                DecisionReason.BULK_ZERO_TRIGGER_ACCEPTED,
                str(bulk.get("decided_by", "")),
                str(bulk.get("decision_origin", "")),
                str(bulk.get("decided_at", "")),
            )
        if set(bulk.get("surface_sha256", {})) != set(bulk.get("normalized_record_ids", [])):
            problems.append(
                f"bulk decision {bulk.get('bulk_decision_id')!r}: surface digests do not cover exactly its ids"
            )
    if problems:
        raise EgressDecisionError("; ".join(problems))
    return decisions


def derive_egress_eligibility(
    records: list[dict[str, Any]], decisions: dict[str, EgressDecision]
) -> list[dict[str, Any]]:
    """A pure function. `records` carry normalized_record_id, surface_sha256, trigger_counts and
    transmission_problems. The output order follows the input order."""
    out = []
    for record in records:
        rid = record["normalized_record_id"]
        triggers = {k: v for k, v in record["trigger_counts"].items() if v}
        decision = decisions.get(rid)
        if record["transmission_problems"]:
            state, basis, origin = (
                EgressState.EGRESS_EXCLUDED,
                record["transmission_problems"][0].split(":")[0],
                "DETERMINISTIC_RULE",
            )
        elif decision is None:
            state, basis, origin = EgressState.EGRESS_REVIEW_REQUIRED, "NO_HUMAN_DECISION", None
        elif decision.surface_sha256 != record["surface_sha256"]:
            state, basis, origin = (
                EgressState.EGRESS_REVIEW_REQUIRED,
                "DECISION_BOUND_TO_A_DIFFERENT_SURFACE",
                None,
            )
        elif decision.reason is DecisionReason.BULK_ZERO_TRIGGER_ACCEPTED and triggers:
            state, basis, origin = (
                EgressState.EGRESS_REVIEW_REQUIRED,
                "BULK_DECISION_DOES_NOT_COVER_A_TRIGGERED_RECORD",
                None,
            )
        elif (
            decision.decision is EgressState.EGRESS_APPROVED
            and "secret_like" in triggers
            and decision.reason is not DecisionReason.TRIGGER_REVIEWED_NOT_PERSONAL
        ):
            state, basis, origin = (
                EgressState.EGRESS_REVIEW_REQUIRED,
                "SECRET_LIKE_TRIGGER_NEEDS_AN_INDIVIDUAL_REVIEW",
                None,
            )
        else:
            state, basis, origin = (
                decision.decision,
                decision.reason.value,
                decision.decision_origin,
            )
        out.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": record["surface_sha256"],
                "triggers": triggers,
                "state": state.value,
                "basis": basis,
                "decision_origin": origin,
                "decided_by": decision.decided_by
                if decision and origin == "HUMAN_OPERATOR"
                else None,
            }
        )
    return out


def surface_matches(surface: str, expected: str) -> bool:
    return surface_sha256(surface) == expected
