"""Which operator decisions and provider facts still block a DEVELOPMENT pilot run (Mission 1.85.7).

Reads the rendered decision package, the operator-owned decisions file and the provider verification,
and returns blockers. It decides nothing: a blank decision is a blocker, a REVISE is a blocker until the
package is re-rendered with the revision, and a REJECT of the retry reading or the ceiling is a blocker
because the run as bound cannot proceed. An authorised or rejected pilot threshold is a made decision.

No default exists for a missing price, a missing model state or a missing decision.
"""

from __future__ import annotations

from typing import Any

__all__ = ["accepted_ceiling", "operator_decision_blockers", "provider_blockers"]

AUTHORISE = "AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT"
REVISE_THRESHOLD = "REVISE_BEFORE_THE_PILOT_RUN"
REJECT_THRESHOLD = "REJECT_FOR_THE_PILOT"
THRESHOLD_CHOICES = {AUTHORISE, REVISE_THRESHOLD, REJECT_THRESHOLD}
REPEATABILITY_CHOICES = {
    "DEFER_TO_A_LATER_REPEATABILITY_RUN",
    "AUTHORISE_A_SEPARATELY_APPROVED_SECOND_RUN_LATER",
    "REJECT_FOR_THIS_FIRST_PILOT",
}


def provider_blockers(verification: dict[str, Any] | None, packet_model: str) -> list[str]:
    if not verification or verification.get("status") != "VERIFIED":
        return [
            "PROVIDER_VERIFICATION_NOT_ESTABLISHED: no verified provider documentation is bound"
        ]
    blockers = []
    model = verification.get("model") or {}
    if (
        model.get("documented_api_id") != packet_model
        or model.get("bound_by_packet") != packet_model
    ):
        blockers.append(
            f"CONFIGURED_MODEL_NOT_VERIFIED: the packet binds {packet_model!r}; no substitution is made"
        )
    if model.get("documented_state") != "ACTIVE":
        blockers.append(
            f"CONFIGURED_MODEL_NOT_AVAILABLE: {packet_model!r} is documented as {model.get('documented_state')!r}"
        )
    pricing = verification.get("pricing") or {}
    for key in ("input_usd_per_mtok", "output_usd_per_mtok", "us_only_inference_multiplier"):
        if pricing.get(key) in (None, "", "NOT_ESTABLISHED"):
            blockers.append(f"PROVIDER_PRICING_NOT_ESTABLISHED: {key}")
    return blockers


def operator_decision_blockers(package: dict[str, Any], decisions: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    items = {i["item_id"]: i for i in package["A_pilot_thresholds"]}
    made = {d.get("item_id"): d for d in decisions.get("A_pilot_thresholds", [])}
    unmade, revising, bad, dispositions = [], [], [], []
    for item_id, item in items.items():
        decision = made.get(item_id) or {}
        choice = decision.get("operator_decision")
        if choice is None:
            unmade.append(item_id)
        elif choice not in THRESHOLD_CHOICES:
            bad.append(item_id)
        elif choice == REVISE_THRESHOLD:
            revising.append(item_id)
        elif (
            choice == AUTHORISE
            and "repeatability_choices" in item
            and decision.get("repeatability_disposition") not in REPEATABILITY_CHOICES
        ):
            dispositions.append(item_id)
    if set(made) - set(items):
        bad.extend(sorted(str(k) for k in set(made) - set(items)))
    if unmade:
        blockers.append(
            f"THRESHOLDS_NOT_AUTHORISED: {len(unmade)} of {len(items)} single-human pilot threshold decisions unmade"
        )
    if revising:
        blockers.append(f"THRESHOLD_REVISION_PENDING: {', '.join(sorted(revising))}")
    if dispositions:
        blockers.append(f"REPEATABILITY_DISPOSITION_MISSING: {', '.join(sorted(dispositions))}")
    if bad:
        blockers.append(f"THRESHOLD_DECISION_INVALID: {', '.join(sorted(bad))}")

    retry = (decisions.get("B_retry") or {}).get("operator_decision")
    if retry is None:
        blockers.append("RETRY_INTERPRETATION_NOT_RATIFIED: the retry decision is blank")
    elif retry in ("REVISE", "REJECT"):
        blockers.append(f"RETRY_POLICY_CHANGE_REQUIRED: the operator chose {retry}")
    elif retry != "RATIFY":
        blockers.append(f"RETRY_DECISION_INVALID: {retry!r}")

    ceiling = decisions.get("C_hard_ceiling") or {}
    choice = ceiling.get("operator_decision")
    proposed = package["C_hard_ceiling"]["proposed_hard_ceiling_usd"]
    if choice is None:
        blockers.append("COST_CEILING_NOT_ACCEPTED: the ceiling decision is blank")
    elif choice == "REVISE":
        blockers.append(
            "COST_CEILING_REVISION_PENDING: re-render the package with the revised ceiling"
        )
    elif choice == "REJECT":
        blockers.append("COST_CEILING_REJECTED")
    elif choice != "ACCEPT":
        blockers.append(f"COST_CEILING_DECISION_INVALID: {choice!r}")
    elif str(ceiling.get("accepted_hard_ceiling_usd")) != proposed:
        blockers.append(
            f"COST_CEILING_ACCEPTANCE_MISMATCH: accepted {ceiling.get('accepted_hard_ceiling_usd')!r}, proposed {proposed}"
        )
    if (choice is not None or retry is not None or len(unmade) < len(items)) and not str(
        decisions.get("decided_by") or ""
    ).strip():
        blockers.append(
            "OPERATOR_DECISIONS_UNATTRIBUTED: decided_by is required once any decision is made"
        )
    return blockers


def accepted_ceiling(package: dict[str, Any], decisions: dict[str, Any]) -> str | None:
    ceiling = decisions.get("C_hard_ceiling") or {}
    if (
        ceiling.get("operator_decision") == "ACCEPT"
        and str(ceiling.get("accepted_hard_ceiling_usd"))
        == package["C_hard_ceiling"]["proposed_hard_ceiling_usd"]
    ):
        return str(package["C_hard_ceiling"]["proposed_hard_ceiling_usd"])
    return None
