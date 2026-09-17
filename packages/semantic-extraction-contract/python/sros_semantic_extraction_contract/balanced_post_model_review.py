"""Mission 1.85.13 (N08-B-PILOT). Balanced post-model operator review of the prompt 1.1.0 disagreements.

Mission 1.85.10 reviewed one side only: records the model called PRESENT and the blind reference called ABSENT.
Prompt 1.1.0 lost true positives as well, so a review of over-reads alone would ask the operator about half the
problem and read as though the other half did not exist. This module defines a review with two sides:

    NEW_FALSE_PRESENT  reference ABSENT, model PRESENT, and never reviewed before
    FALSE_NEGATIVE     reference PRESENT, model ABSENT

Each side has its own choices, because "the model over-read" and "the model under-read" are different
judgements and a shared vocabulary would let one be recorded as the other.

Everything here is a POST_MODEL_OPERATOR_REVIEW: the operator has seen the model's answer, so it is NOT a blind
annotation, it never replaces or edits the blind reference, and the preregistered Mission 1.85.12 readings stay
exactly as they were.

A record already reviewed at record level in Mission 1.85.10 is NOT re-reviewed here. Its judgement is reused
as `PRIOR_REVIEW_REUSED_RECORD_LEVEL_JUDGEMENT` and is never duplicated as a new human decision.

This module decides nothing. Pure functions: no file, database, network or model access.
"""

from __future__ import annotations

from typing import Any

from .post_model_review import (
    BLIND_ATTESTATION_KEYS,
    MAX_NOTE,
    PROVENANCE,
    ReviewRefusedError,
    _timezone_aware,
    canonical_sha256,
)

__all__ = [
    "AMBIGUOUS",
    "CHOICES_BY_SIDE",
    "FALSE_NEGATIVE",
    "LABEL",
    "NEW_FALSE_PRESENT",
    "NOTE_REQUIRED",
    "OVERREAD",
    "PRIOR_REVIEW_REUSE",
    "PROVENANCE",
    "RECOMMENDATION_RULE",
    "REVIEW_ID",
    "REVISION_TO_ABSENT",
    "REVISION_TO_PRESENT",
    "SIDES",
    "THIS_MISSION_REVIEW",
    "UNDERREAD",
    "UNRESOLVED",
    "ReviewRefusedError",
    "analyse",
    "blank_working_file",
    "canonical_sha256",
    "make_decision",
    "model_output_digest",
    "review_status",
    "validate_working",
]

REVIEW_ID = "semantic-extraction-balanced-post-model-review-development"
LABEL = "REPORTED_FAILED_ATTEMPT"
NEW_FALSE_PRESENT = "NEW_FALSE_PRESENT"
FALSE_NEGATIVE = "FALSE_NEGATIVE"
SIDES = (NEW_FALSE_PRESENT, FALSE_NEGATIVE)

OVERREAD = "HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD"
REVISION_TO_PRESENT = "POST_MODEL_HUMAN_REVISION_TO_PRESENT"
UNDERREAD = "HUMAN_REFERENCE_CONFIRMED_MODEL_UNDERREAD"
REVISION_TO_ABSENT = "POST_MODEL_HUMAN_REVISION_TO_ABSENT"
AMBIGUOUS = "LABEL_DEFINITION_AMBIGUOUS"
UNRESOLVED = "UNRESOLVED"

CHOICES_BY_SIDE = {
    NEW_FALSE_PRESENT: (OVERREAD, REVISION_TO_PRESENT, AMBIGUOUS, UNRESOLVED),
    FALSE_NEGATIVE: (UNDERREAD, REVISION_TO_ABSENT, AMBIGUOUS, UNRESOLVED),
}
NOTE_REQUIRED = frozenset({REVISION_TO_PRESENT, REVISION_TO_ABSENT, AMBIGUOUS})
CONFIRMED_BY_SIDE = {NEW_FALSE_PRESENT: OVERREAD, FALSE_NEGATIVE: UNDERREAD}
REVISION_BY_SIDE = {NEW_FALSE_PRESENT: REVISION_TO_PRESENT, FALSE_NEGATIVE: REVISION_TO_ABSENT}
EXPECTED_STATES = {
    NEW_FALSE_PRESENT: ("ABSENT", "PRESENT"),
    FALSE_NEGATIVE: ("PRESENT", "ABSENT"),
}

PRIOR_REVIEW_REUSE = "PRIOR_REVIEW_REUSED_RECORD_LEVEL_JUDGEMENT"
THIS_MISSION_REVIEW = "MISSION_1_85_13_NEW_REVIEW"

# Frozen before any decision exists (Mission 1.85.13). Every rule reads the RESOLVED decisions of a side,
# which are the decisions that are not UNRESOLVED:
#   DOMINANT   at least half the resolved decisions of that side, and at least one;
#   STRONG     at least two thirds of them, and at least two;
#   SUBSTANTIAL at least a third of every reviewed record.
# Several recommendations may apply, and none of them is acted on.
PRECISION_PROBLEM = "RFA_PRECISION_REMAINS_MODEL_OR_EXTRACTION_CONTRACT_PROBLEM"
OVERCONSTRAINS = "RFA_PROMPT_1_1_OVERCONSTRAINS_TRUE_POSITIVES"
STRUCTURED_CONTRACT = "PROMPT_ONLY_REVISION_INSUFFICIENT_CONSIDER_STRUCTURED_EXTRACTION_CONTRACT"
REFERENCE_ADJUDICATION = "REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED"
LABEL_DECISION = "LABEL_DEFINITION_DECISION_REQUIRED"
RECOMMENDATION_RULE = (
    "dominant = at least half the resolved decisions of that side and at least 1; strong = at least two "
    "thirds of them and at least 2; substantial = at least a third of every reviewed record. Confirmed "
    "over-reads dominant -> RFA_PRECISION_REMAINS_MODEL_OR_EXTRACTION_CONTRACT_PROBLEM; confirmed under-reads "
    "dominant -> RFA_PROMPT_1_1_OVERCONSTRAINS_TRUE_POSITIVES; both strong -> "
    "PROMPT_ONLY_REVISION_INSUFFICIENT_CONSIDER_STRUCTURED_EXTRACTION_CONTRACT; revisions substantial -> "
    "REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED; ambiguity substantial -> LABEL_DEFINITION_DECISION_REQUIRED. "
    "Derived only when the review is COMPLETE; nothing is revised automatically."
)


def model_output_digest(extraction: dict[str, Any]) -> str:
    """The accepted model output a decision is bound to: its state and every finding, not only this label's.

    A record on the FALSE_NEGATIVE side has no REPORTED_FAILED_ATTEMPT finding at all, so binding to this
    label's findings alone would bind it to an empty list and let a changed answer pass unnoticed.
    """
    return canonical_sha256(
        {
            "extraction_state": extraction["extraction_state"],
            "findings": sorted(
                (
                    {
                        k: f[k]
                        for k in (
                            "finding_id",
                            "finding_type",
                            "evidence_start",
                            "evidence_end",
                            "evidence_sha256",
                        )
                    }
                    for f in extraction["findings"]
                ),
                key=lambda f: (f["evidence_start"], f["finding_id"]),
            ),
        }
    )


def blank_working_file(
    operator_id: str, bindings: dict[str, str], records: list[dict[str, str]]
) -> dict[str, Any]:
    if not operator_id.strip() or not operator_id.replace("-", "").isalnum():
        raise ReviewRefusedError("OPERATOR_ID_INVALID", operator_id)
    listed = []
    for record in records:
        side = record["side"]
        if side not in SIDES:
            raise ReviewRefusedError("UNKNOWN_REVIEW_SIDE", side)
        blind, model = EXPECTED_STATES[side]
        if (record["original_blind_state"], record["model_state"]) != (blind, model):
            raise ReviewRefusedError(
                "RECORD_DOES_NOT_BELONG_TO_ITS_SIDE", record["normalized_record_id"]
            )
        listed.append(
            {
                k: record[k]
                for k in (
                    "normalized_record_id",
                    "side",
                    "surface_sha256",
                    "original_blind_state",
                    "model_state",
                    "model_output_sha256",
                )
            }
        )
    ids = [r["normalized_record_id"] for r in listed]
    if len(set(ids)) != len(ids):
        raise ReviewRefusedError("RECORD_ON_BOTH_SIDES", "a record may be reviewed once only")
    return {
        "$comment": "BALANCED POST-MODEL OPERATOR REVIEW working file. The operator has seen the model's answer: this is not a blind annotation and never replaces the original reference.",
        "review_id": REVIEW_ID,
        "provenance": PROVENANCE,
        "label": LABEL,
        "operator_id": operator_id,
        "bindings": dict(bindings),
        "records": listed,
        "decisions": [],
    }


def make_decision(
    working: dict[str, Any],
    record_id: str,
    *,
    surface_sha256: str,
    model_output_sha256: str,
    choice: str,
    note: str,
    decided_at: str,
) -> dict[str, Any]:
    """One explicit operator choice, bound to the side and to what the operator was shown."""
    record = next((r for r in working["records"] if r["normalized_record_id"] == record_id), None)
    if record is None:
        raise ReviewRefusedError("RECORD_NOT_UNDER_REVIEW", record_id)
    side = record["side"]
    if choice not in CHOICES_BY_SIDE[side]:
        raise ReviewRefusedError("CHOICE_NOT_AVAILABLE_ON_THIS_SIDE", f"{choice} on {side}")
    if surface_sha256 != record["surface_sha256"]:
        raise ReviewRefusedError("SURFACE_DIGEST_MISMATCH", record_id)
    if model_output_sha256 != record["model_output_sha256"]:
        raise ReviewRefusedError("MODEL_OUTPUT_DIGEST_MISMATCH", record_id)
    note = note.strip()
    if choice in NOTE_REQUIRED and not note:
        raise ReviewRefusedError("NOTE_REQUIRED", choice)
    if len(note) > MAX_NOTE:
        raise ReviewRefusedError("NOTE_TOO_LONG", str(len(note)))
    if not _timezone_aware(decided_at):
        raise ReviewRefusedError("DECIDED_AT_NOT_TIMEZONE_AWARE", decided_at)
    return {
        "normalized_record_id": record_id,
        "side": side,
        "surface_sha256": surface_sha256,
        "model_output_sha256": model_output_sha256,
        "original_blind_state": record["original_blind_state"],
        "model_state": record["model_state"],
        "decision": choice,
        "operator_note": note or None,
        "decided_by": working["operator_id"],
        "decided_at": decided_at,
        "provenance": PROVENANCE,
        "review_origin": THIS_MISSION_REVIEW,
        "blind": False,
    }


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
    if working.get("review_id") != REVIEW_ID:
        problems.append(("REVIEW_ID_INVALID", str(working.get("review_id"))))
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
        if rid in expected and any(record.get(k) != expected[rid][k] for k in record):
            problems.append(("STALE_RECORD", rid))
    seen: set[str] = set()
    for decision in working.get("decisions", []):
        rid = str(decision.get("normalized_record_id"))
        if rid in seen:
            problems.append(("DUPLICATE_DECISION", rid))
        seen.add(rid)
        if rid not in expected:
            problems.append(("DECISION_FOR_A_RECORD_NOT_UNDER_REVIEW", rid))
            continue
        if decision.get("review_origin") != THIS_MISSION_REVIEW:
            problems.append(("DECISION_REVIEW_ORIGIN_INVALID", rid))
            continue
        try:
            rebuilt = make_decision(
                working,
                rid,
                surface_sha256=str(decision.get("surface_sha256")),
                model_output_sha256=str(decision.get("model_output_sha256")),
                choice=str(decision.get("decision")),
                note=str(decision.get("operator_note") or ""),
                decided_at=str(decision.get("decided_at")),
            )
        except ReviewRefusedError as exc:
            problems.append((exc.code, rid))
            continue
        if rebuilt != decision:
            problems.append(("DECISION_NOT_AS_RECORDED", rid))
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


def _side_counts(working: dict[str, Any], side: str) -> dict[str, int]:
    counts = {choice: 0 for choice in CHOICES_BY_SIDE[side]}
    for decision in working["decisions"]:
        if decision["side"] == side:
            counts[decision["decision"]] += 1
    return counts


def analyse(working: dict[str, Any], status: str) -> dict[str, Any]:
    reviewed = len(working["records"])
    sides: dict[str, Any] = {}
    for side in SIDES:
        counts = _side_counts(working, side)
        listed = sum(1 for r in working["records"] if r["side"] == side)
        resolved = sum(n for choice, n in counts.items() if choice != UNRESOLVED)
        sides[side] = {
            "records": listed,
            "counts": counts,
            "decided": sum(counts.values()),
            "undecided": listed - sum(counts.values()),
            "resolved": resolved,
        }
    revisions = sum(sides[s]["counts"][REVISION_BY_SIDE[s]] for s in SIDES)
    ambiguous = sum(sides[s]["counts"][AMBIGUOUS] for s in SIDES)
    unresolved = sum(sides[s]["counts"][UNRESOLVED] for s in SIDES)
    undecided = sum(sides[s]["undecided"] for s in SIDES)

    def share(side: str, choice: str) -> tuple[bool, bool]:
        resolved, count = sides[side]["resolved"], sides[side]["counts"][choice]
        dominant = count >= 1 and 2 * count >= resolved
        strong = count >= 2 and 3 * count >= 2 * resolved
        return dominant, strong

    recommendations: list[str] = []
    if status == "COMPLETE":
        fp_dominant, fp_strong = share(NEW_FALSE_PRESENT, OVERREAD)
        fn_dominant, fn_strong = share(FALSE_NEGATIVE, UNDERREAD)
        if fp_dominant:
            recommendations.append(PRECISION_PROBLEM)
        if fn_dominant:
            recommendations.append(OVERCONSTRAINS)
        if fp_strong and fn_strong:
            recommendations.append(STRUCTURED_CONTRACT)
        if 3 * revisions >= reviewed and revisions >= 1:
            recommendations.append(REFERENCE_ADJUDICATION)
        if 3 * ambiguous >= reviewed and ambiguous >= 1:
            recommendations.append(LABEL_DECISION)
    return {
        "status": status,
        "records_reviewed": reviewed,
        "sides": sides,
        "post_model_human_revisions": revisions,
        "label_definition_ambiguous": ambiguous,
        "unresolved": unresolved,
        "undecided": undecided,
        "unresolved_or_undecided": unresolved + undecided,
        "development_recommendations": recommendations,
        "recommendation_rule": RECOMMENDATION_RULE,
    }
