"""Mission 1.85.10 (N08-B-PILOT). Post-model operator review of pilot disagreements.

A POST_MODEL_OPERATOR_REVIEW is a different kind of record from the blind human annotation, and it must never
be mistaken for one:

- the operator has seen the model's disagreement before choosing;
- it is NOT a blind annotation and never carries a blind attestation;
- it does not replace, edit or supersede the original reference;
- it may inform a later prompt, contract or label-definition decision;
- the preregistered Mission 1.85.9 readings stay exactly as they were.

This module decides nothing. It defines the four choices, checks that a recorded choice is bound to the exact
inputs it was made on, and derives counts and development recommendations mechanically from the operator's
choices. Pure functions: no file, database, network or model access.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

__all__ = [
    "AMBIGUOUS",
    "CHOICES",
    "LABEL",
    "NOTE_REQUIRED",
    "OVERREAD",
    "PROVENANCE",
    "RECOMMENDATIONS",
    "REVIEW_ID",
    "REVISION",
    "UNRESOLVED",
    "ReviewRefusedError",
    "analyse",
    "blank_working_file",
    "canonical_sha256",
    "findings_digest",
    "make_decision",
    "review_status",
    "validate_working",
]

REVIEW_ID = "semantic-extraction-post-model-review-development"
PROVENANCE = "POST_MODEL_OPERATOR_REVIEW"
LABEL = "REPORTED_FAILED_ATTEMPT"
OVERREAD = "HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD"
REVISION = "POST_MODEL_HUMAN_REVISION"
AMBIGUOUS = "LABEL_DEFINITION_AMBIGUOUS"
UNRESOLVED = "UNRESOLVED"
CHOICES = (OVERREAD, REVISION, AMBIGUOUS, UNRESOLVED)
NOTE_REQUIRED = frozenset({REVISION, AMBIGUOUS})
MAX_NOTE = 600
# Frozen before any decision exists (Mission 1.85.10):
# - a choice DOMINATES when its count is the largest of the three resolved choices and at least 1; ties give
#   every tied choice;
# - ambiguity is SUBSTANTIAL when at least a third of the reviewed records are LABEL_DEFINITION_AMBIGUOUS.
RECOMMENDATIONS = {
    OVERREAD: "PROMPT_OR_EXTRACTION_CONTRACT_PRECISION_REVISION_REQUIRED",
    REVISION: "REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED",
    AMBIGUOUS: "LABEL_DEFINITION_DECISION_REQUIRED",
}
BLIND_ATTESTATION_KEYS = (
    "no_model_output_seen",
    "no_model_assistance_used",
    "attestation",
    "reference_origin",
)


class ReviewRefusedError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}{': ' + detail if detail else ''}")
        self.code = code


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def findings_digest(findings: list[dict[str, Any]]) -> str:
    """The model output a decision is bound to: the accepted findings of LABEL, ids, offsets and digests."""
    return canonical_sha256(
        sorted(
            (
                {
                    k: f[k]
                    for k in ("finding_id", "evidence_start", "evidence_end", "evidence_sha256")
                }
                for f in findings
                if f["finding_type"] == LABEL
            ),
            key=lambda f: (f["evidence_start"], f["finding_id"]),
        )
    )


def blank_working_file(
    operator_id: str, bindings: dict[str, str], records: list[dict[str, str]]
) -> dict[str, Any]:
    if not operator_id.strip() or not operator_id.replace("-", "").isalnum():
        raise ReviewRefusedError("OPERATOR_ID_INVALID", operator_id)
    return {
        "$comment": "POST-MODEL OPERATOR REVIEW working file. The operator has seen the model's disagreement: this is not a blind annotation and never replaces the original reference.",
        "review_id": REVIEW_ID,
        "provenance": PROVENANCE,
        "label": LABEL,
        "operator_id": operator_id,
        "bindings": dict(bindings),
        "records": [
            {
                k: r[k]
                for k in (
                    "normalized_record_id",
                    "surface_sha256",
                    "original_blind_state",
                    "model_state",
                    "model_findings_sha256",
                )
            }
            for r in records
        ],
        "decisions": [],
    }


def make_decision(
    working: dict[str, Any],
    record_id: str,
    *,
    surface_sha256: str,
    model_findings_sha256: str,
    choice: str,
    note: str,
    decided_at: str,
) -> dict[str, Any]:
    """One explicit operator choice, bound to what the operator was shown. Refuses rather than repairs."""
    record = next((r for r in working["records"] if r["normalized_record_id"] == record_id), None)
    if record is None:
        raise ReviewRefusedError("RECORD_NOT_UNDER_REVIEW", record_id)
    if choice not in CHOICES:
        raise ReviewRefusedError("UNSUPPORTED_CHOICE", choice)
    if surface_sha256 != record["surface_sha256"]:
        raise ReviewRefusedError("SURFACE_DIGEST_MISMATCH", record_id)
    if model_findings_sha256 != record["model_findings_sha256"]:
        raise ReviewRefusedError("MODEL_FINDINGS_DIGEST_MISMATCH", record_id)
    note = note.strip()
    if choice in NOTE_REQUIRED and not note:
        raise ReviewRefusedError("NOTE_REQUIRED", choice)
    if len(note) > MAX_NOTE:
        raise ReviewRefusedError("NOTE_TOO_LONG", str(len(note)))
    if not _timezone_aware(decided_at):
        raise ReviewRefusedError("DECIDED_AT_NOT_TIMEZONE_AWARE", decided_at)
    return {
        "normalized_record_id": record_id,
        "surface_sha256": surface_sha256,
        "model_findings_sha256": model_findings_sha256,
        "original_blind_state": record["original_blind_state"],
        "model_state": record["model_state"],
        "decision": choice,
        "operator_note": note or None,
        "decided_by": working["operator_id"],
        "decided_at": decided_at,
        "provenance": PROVENANCE,
        "blind": False,
    }


def _timezone_aware(value: Any) -> bool:
    try:
        return isinstance(value, str) and datetime.fromisoformat(value).utcoffset() is not None
    except ValueError:
        return False


def validate_working(
    working: dict[str, Any],
    *,
    expected_bindings: dict[str, str],
    expected_records: list[dict[str, str]],
) -> list[tuple[str, str]]:
    """Every problem with a working or committed review against freshly computed inputs."""
    problems: list[tuple[str, str]] = []
    if working.get("provenance") != PROVENANCE or working.get("label") != LABEL:
        problems.append(("PROVENANCE_OR_LABEL_INVALID", str(working.get("provenance"))))
    for key in BLIND_ATTESTATION_KEYS:
        if key in working:
            problems.append(("BLIND_ATTESTATION_NOT_PERMITTED", key))
    for name, value in expected_bindings.items():
        if (working.get("bindings") or {}).get(name) != value:
            problems.append(("STALE_BINDING", name))
    expected = {r["normalized_record_id"]: r for r in expected_records}
    listed = {r["normalized_record_id"]: r for r in working.get("records", [])}
    if set(listed) != set(expected) or len(working.get("records", [])) != len(expected):
        problems.append(("RECORD_SET_MISMATCH", f"{len(listed)} listed, {len(expected)} expected"))
    for rid, record in listed.items():
        if rid in expected and any(record.get(k) != expected[rid][k] for k in expected[rid]):
            problems.append(("STALE_RECORD", rid))
    seen: set[str] = set()
    for decision in working.get("decisions", []):
        rid = decision.get("normalized_record_id")
        if rid in seen:
            problems.append(("DUPLICATE_DECISION", str(rid)))
        seen.add(str(rid))
        if rid not in expected:
            problems.append(("DECISION_FOR_A_RECORD_NOT_UNDER_REVIEW", str(rid)))
            continue
        try:
            rebuilt = make_decision(
                working,
                rid,
                surface_sha256=str(decision.get("surface_sha256")),
                model_findings_sha256=str(decision.get("model_findings_sha256")),
                choice=str(decision.get("decision")),
                note=str(decision.get("operator_note") or ""),
                decided_at=str(decision.get("decided_at")),
            )
        except ReviewRefusedError as exc:
            problems.append((exc.code, str(rid)))
            continue
        if rebuilt != decision:
            problems.append(("DECISION_NOT_AS_RECORDED", str(rid)))
    return problems


def review_status(working: dict[str, Any], problems: list[tuple[str, str]]) -> str:
    if any(code.startswith("STALE") for code, _ in problems):
        return "STALE"
    if problems:
        return "INVALID"
    decided = {d["normalized_record_id"]: d["decision"] for d in working["decisions"]}
    if len(decided) < len(working["records"]) or UNRESOLVED in decided.values():
        return "INCOMPLETE"
    return "COMPLETE"


def analyse(working: dict[str, Any], status: str) -> dict[str, Any]:
    counts = {choice: 0 for choice in CHOICES}
    for decision in working["decisions"]:
        counts[decision["decision"]] += 1
    undecided = len(working["records"]) - len(working["decisions"])
    resolved = {c: counts[c] for c in (OVERREAD, REVISION, AMBIGUOUS)}
    top = max(resolved.values())
    recommendations: list[str] = []
    if status == "COMPLETE":
        recommendations = [RECOMMENDATIONS[c] for c, n in resolved.items() if n == top and n >= 1]
        ambiguous_substantial = 3 * resolved[AMBIGUOUS] >= len(working["records"])
        if ambiguous_substantial and RECOMMENDATIONS[AMBIGUOUS] not in recommendations:
            recommendations.append(RECOMMENDATIONS[AMBIGUOUS])
    return {
        "status": status,
        "counts": counts,
        "undecided": undecided,
        "unresolved_or_undecided": counts[UNRESOLVED] + undecided,
        "development_recommendations": recommendations,
        "recommendation_rule": "dominant = the largest of the three resolved counts (ties give each); ambiguity substantial at >= 1/3 of reviewed records; derived only when COMPLETE; nothing is revised automatically",
    }
