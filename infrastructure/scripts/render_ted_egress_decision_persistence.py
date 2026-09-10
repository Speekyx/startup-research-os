"""Render and validate the TED egress operator decision and its persistence (Mission 1.83.1).

An approval is the one thing in this repository a machine may not produce, so the gate is built
around what would make a fabricated one look real. It refuses:

    AN APPROVAL THAT DOES NOT NAME THIS PACKET. The digest is recomputed from the packet's own
    bound fields and compared against BOTH the stated and the recorded value; a copied hash, a
    moved version, or a representation digest the review never measured is refused.

    AN APPROVAL WRITTEN INTO THE DOCUMENT IT APPROVES. The frozen packet stays byte-identical
    and its own `approval_recorded` stays false, because marking a frozen document approved
    changes the bytes that were approved.

    AN ACCEPTANCE NOBODY WROTE. The text is recorded verbatim with its own digest and must name
    the packet, the decision and the subject. A machine recorded as the reviewer, a verifier
    clearing a human condition, or an approval inferred from a mission having run is refused.

    A REVIEW EDITED RATHER THAN APPENDED. v3 keeps its content, the successor carries every
    condition forward verbatim, and exactly one assessment moves.

    A CONFIGURATION RE-POINTED WITHOUT THE RE-CHECK. A compliance configuration pinned to a new
    review version must record that the conditions it answers are unchanged, and that any
    condition the successor adds is one no configuration can answer.

    A PERMISSION THAT WIDENED. Training, fine-tuning, embeddings, redistribution, customer
    access, another packet, another purpose and the commercial profile each stay where they
    were, and the operator's own list of what is not authorised is carried rather than summarised.

    AN ACT MISTAKEN FOR A PERMISSION. AVAILABLE is a gate state. A record claiming bytes were
    transmitted, an Opportunity created, a model called or research data acquired is refused.

    uv run python infrastructure/scripts/render_ted_egress_decision_persistence.py
    uv run python infrastructure/scripts/render_ted_egress_decision_persistence.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

APPROVAL = DATA / "ted-egress-operator-decision-v1.json"
APPROVAL_MD = DATA / "ted-egress-operator-decision-v1.md"
PERSISTENCE = DATA / "ted-egress-decision-persistence-v1.json"
PERSISTENCE_MD = DATA / "ted-egress-decision-persistence-v1.md"
PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"
EGRESS_REVIEW = DATA / "ted-selected-candidate-egress-review-v1.json"
CATALOG = DATA / "source-catalog-v1.json"
COMPLIANCE = DATA / "source-compliance-v1.json"
EGRESS_GATE = ROOT / "infrastructure" / "scripts" / "render_ted_selected_candidate_egress.py"

SOURCE_ID = "ted-eu"
USE_PROFILE = "local-private-research-v1"
ACTIVITY = "external_model_transmission"
SUBJECT = "ted-eu:CPV-class:9261"

#: The required conditions are DERIVED from the catalog's current review, never hard-coded.
#: A gate that pinned the five this repository happens to carry would assert the state we are in
#: rather than the property that matters, and a successor adding none would be unrepresentable.
#: What is pinned is the rule: every condition v3 required survives, the record reports exactly
#: what the catalog carries, and a human condition is satisfied by a human.
CONDITION_KINDS = ("CAPABILITY", "HUMAN_CONFIRMATION")

#: Activities this decision may never widen, with the state each must keep.
UNWIDENED = {
    "model_training": "NOT_ASSESSED",
    "fine_tuning": "NOT_ASSESSED",
    "embeddings": "NOT_ASSESSED",
    "public_redistribution": "NOT_PERMITTED",
    "customer_facing_source_data": "NOT_PERMITTED",
}

#: Everything the operator's approval says it does not authorise, checked as a set.
NOT_AUTHORIZED = frozenset(
    {
        "model training",
        "fine-tuning",
        "embeddings",
        "public redistribution",
        "resale",
        "customer-facing TED source-data access",
        "another TED packet",
        "another processing purpose",
        "commercial-multi-tenant-research-v1",
        "transmission to a provider whose current reviewed posture is not APPROVED",
    }
)

#: A permission is not an act, and these counters say so.
ZERO_ACCOUNTING = (
    "MODEL_CALLS",
    "embeddings_created",
    "research_data_fetches",
    "ted_api_calls",
    "ted_bulk_downloads",
    "new_raw_records",
    "new_normalized_records",
    "documentation_fetches",
    "opportunities_created",
    "opportunity_revisions_created",
    "opportunity_links_created",
    "reliability_assessments_created",
    "independence_groups_created",
    "scores_persisted",
    "hypotheses_synthesized",
    "bytes_transmitted_to_any_external_model",
)


class ValidationError(Exception):
    """The record says something the evidence does not support."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _egress_gate():
    spec = importlib.util.spec_from_file_location("egress_gate", EGRESS_GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reviews(catalog: dict) -> dict[int, dict]:
    source = next(s for s in catalog["sources"] if s["source_id"] == SOURCE_ID)
    return {
        r["review_version"]: r
        for r in source["reviews"]
        if r["assessed_use_profile"] == USE_PROFILE
    }


def _check_the_approval(approval: dict, packet: dict) -> None:
    """The digest is recomputed, the packet is untouched, and the text is the operator's."""
    recomputed = _egress_gate().packet_digest(packet)
    if approval["DECISION_PACKET_SHA256_RECOMPUTED"] != recomputed:
        raise ValidationError(
            f"the approval records a recomputed digest of "
            f"{approval['DECISION_PACKET_SHA256_RECOMPUTED']} and the packet's own bound fields "
            f"hash to {recomputed}"
        )
    if approval["DECISION_PACKET_SHA256_STATED"] != recomputed:
        raise ValidationError(
            "the digest the operator cited is not the digest this packet has. Copying the quoted "
            "hash would make the approval name whatever the message said rather than whatever the "
            "packet is"
        )
    if not approval["DECISION_PACKET_DIGEST_MATCHES"]:
        raise ValidationError("the approval records its own digest check as failing")
    if approval["DECISION_PACKET_VERSION"] != packet["DECISION_PACKET_VERSION"]:
        raise ValidationError("the approval names a different packet version")
    if approval["DECISION_PACKET_FILE_SHA256"] != hashlib.sha256(PACKET.read_bytes()).hexdigest():
        raise ValidationError(
            "the frozen packet file has changed since the approval named it. An approval does not "
            "survive a change to the document it approves"
        )
    if approval["packet_edited_by_this_approval"] or packet["approval_recorded"]:
        raise ValidationError(
            "the approval was written into the document it approves, which changes the bytes that "
            "were approved"
        )
    if approval["DECISION"] != "PERMIT_WITH_EXACT_CONDITIONS":
        raise ValidationError(f"an unrecognised decision {approval['DECISION']!r}")
    if approval["decided_by_kind"] != "NAMED_LOCAL_OPERATOR":
        raise ValidationError("the decision is not attributed to a named local operator")

    text = approval["ACCEPTANCE_TEXT"]
    if not str(text).strip():
        raise ValidationError("an approval with no acceptance text; nothing may be inferred for it")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if approval["ACCEPTANCE_SHA256"] != digest:
        raise ValidationError("the acceptance text does not hash to its recorded digest")
    for needle in (
        packet["DECISION_PACKET_ID"],
        recomputed,
        "PERMIT_WITH_EXACT_CONDITIONS",
        SUBJECT,
        packet["REPRESENTATION_SHA256"],
    ):
        if needle not in text:
            raise ValidationError(f"the acceptance text does not name {needle}")

    if approval["CONDITIONS_ADOPTED"] != packet["CONDITIONS"]:
        raise ValidationError(
            "the adopted conditions are not the packet's conditions. A condition reworded on the "
            "way into the registry is a condition the operator did not adopt"
        )
    if set(approval["NOT_AUTHORIZED"]) != NOT_AUTHORIZED:
        raise ValidationError("the operator's list of what is not authorised was not carried whole")
    if approval["scope"]["representation_sha256"] != packet["REPRESENTATION_SHA256"]:
        raise ValidationError("the approval's scope names a representation the packet does not")
    if not approval["spent"]:
        raise ValidationError(
            "an approval that is not spent by its use is an approval a second packet could reuse"
        )


def _check_the_append(record: dict, catalog: dict, packet: dict) -> None:
    """v3 keeps its content, and exactly one assessment moves."""
    reviews = _reviews(catalog)
    if 4 not in reviews:
        raise ValidationError("review v4 does not exist in the catalog")
    v3, v4 = reviews[3], reviews[4]
    append = record["append_not_edit"]

    if append["v3_content_changed"]:
        raise ValidationError("the record admits editing review v3")
    if "external_model_transmission" in v3:
        raise ValidationError(
            "v3 declares the activity it left unasked; the before-state is an absence"
        )
    if v4.get("external_model_transmission") != "PERMITTED_WITH_CONDITIONS":
        raise ValidationError("v4 does not record the approved assessment")
    if append["external_model_transmission_after"] != v4["external_model_transmission"]:
        raise ValidationError("the record and the catalog disagree about the new assessment")

    moved = [
        field
        for field in v3
        if field
        not in (
            "review_version",
            "reviewed_by",
            "reviewed_at",
            "conditions",
            "required_conditions",
            "open_questions",
            "review_notes",
            "evidence",
        )
        and v3[field] != v4.get(field)
    ]
    if moved:
        raise ValidationError(
            f"assessments other than the reviewed activity moved: {moved}. An append that answers "
            "one question is not a re-review wearing a version bump"
        )
    if v3["conditions"] != v4["conditions"][: len(v3["conditions"])]:
        raise ValidationError("v4 does not carry v3's conditions forward verbatim")
    if v3["evidence"] != v4["evidence"]:
        raise ValidationError("the documentary basis moved without a new document")
    if append["evidence_rows_changed"]:
        raise ValidationError("the record claims the basis moved with no new document")

    v3_keys = {c["key"] for c in v3["required_conditions"]}
    v4_keys = {c["key"] for c in v4["required_conditions"]}
    if not v3_keys <= v4_keys:
        raise ValidationError(f"v4 dropped required conditions: {sorted(v3_keys - v4_keys)}")
    added = v4_keys - v3_keys
    declared = append["required_condition_added"]
    expected = {declared} if declared else set()
    if added != expected:
        raise ValidationError(
            f"the record says {declared!r} was added and the catalog added {sorted(added)}"
        )
    for condition in v4["required_conditions"]:
        if condition["verification"] not in CONDITION_KINDS:
            raise ValidationError(f"{condition['key']}: verification {condition['verification']!r}")
        if not str(condition["description"]).strip():
            raise ValidationError(f"{condition['key']}: a required condition with no description")

    # The eight adopted conditions must actually be in the successor, verbatim.
    joined = " ".join(v4["conditions"])
    for condition in packet["CONDITIONS"]:
        if condition not in joined:
            raise ValidationError(
                "an adopted condition is not carried verbatim into the review successor"
            )


def _check_the_reconciliation(record: dict, catalog: dict, compliance: dict) -> None:
    """A configuration is re-pointed by performing the re-check, never by bumping a number."""
    reconciliation = record["compliance_reconciliation"]
    entry = next(
        s
        for s in compliance["sources"]
        if s["source_id"] == SOURCE_ID and s["use_profile_id"] == USE_PROFILE
    )
    if entry["review_version"] != reconciliation["pinned_after"]:
        raise ValidationError("the configuration is not pinned to the version the record names")
    if not reconciliation["re_check_performed"]:
        raise ValidationError("the configuration was re-pointed without the re-check")
    if not reconciliation["capability_conditions_byte_identical"]:
        raise ValidationError(
            "the configuration was re-pointed past conditions whose meaning moved"
        )
    if reconciliation["required_conditions_removed"]:
        raise ValidationError("a required condition was dropped by the successor")
    if reconciliation["added_condition_verification_kind"] != "HUMAN_CONFIRMATION":
        raise ValidationError(
            "the successor added a CAPABILITY condition the existing configuration never answered, "
            "so re-pointing it would verify something else"
        )

    reviews = _reviews(catalog)
    v3_required = {c["key"]: c for c in reviews[3]["required_conditions"]}
    v4_required = {c["key"]: c for c in reviews[4]["required_conditions"]}
    for key in reconciliation["capability_conditions_compared"]:
        if json.dumps(v3_required[key], sort_keys=True) != json.dumps(
            v4_required[key], sort_keys=True
        ):
            raise ValidationError(f"{key} is not byte-identical between v3 and v4")


def _check_the_conditions(record: dict, catalog: dict) -> None:
    """Every condition the successor requires, and no machine answered a human one."""
    conditions = record["conditions_after_persistence"]
    v4 = _reviews(catalog)[4]
    kinds = {c["key"]: c["verification"] for c in v4["required_conditions"]}

    reported = {k for k in conditions if k in kinds or k.startswith("ted-")}
    if reported != set(kinds):
        raise ValidationError(
            f"the record reports {sorted(reported)} and the successor requires {sorted(kinds)}"
        )
    signed = []
    for key, kind in kinds.items():
        entry = conditions[key]
        if entry["verification"] != kind:
            raise ValidationError(f"{key}: recorded as {entry['verification']}, not {kind}")
        if entry["result"] != "SATISFIED":
            raise ValidationError(f"{key}: {entry['result']}, so eligibility cannot be restored")
        if kind == "HUMAN_CONFIRMATION":
            if entry["verifier"] != "local-operator":
                raise ValidationError(
                    f"{key}: a human condition satisfied by {entry['verifier']!r}"
                )
            version = str(entry.get("verifier_version", "")).strip()
            if not version:
                raise ValidationError(f"{key}: no identifier for WHICH TEXT was signed")
            signed.append(version)
    human = len(signed)
    if conditions["machine_recorded_a_human_condition"]:
        raise ValidationError("a machine recorded a human condition")
    if conditions["verifier_cleared_a_human_condition"]:
        raise ValidationError("a verifier cleared a human condition")
    if conditions["human_confirmations_recorded"] != human:
        raise ValidationError(
            f"the record re-recorded {conditions['human_confirmations_recorded']} human "
            f"confirmations and the successor requires {human}. Appending a review orphans every "
            "one of them, so every one has to be recorded again"
        )
    # The flag alone is not checkable, and the identifier for WHICH TEXT was signed is. One
    # statement carries one identifier; several statements carry several. A record claiming one
    # statement while pointing at two texts is refused, and so is the reverse.
    distinct = len(set(signed))
    if conditions["human_confirmations_rest_on_one_statement"]:
        if distinct != 1:
            raise ValidationError(
                f"the record says the human confirmations rest on ONE statement and they name "
                f"{distinct} different texts"
            )
    elif human > 1 and distinct != human:
        raise ValidationError(
            f"the record says {human} human confirmations rest on separate statements and they "
            f"name {distinct} texts. Two rows carrying one identifier are one act recorded twice"
        )


def _check_the_gates(record: dict) -> None:
    """A permission is not an act."""
    gates = record["gates_after"]
    if gates["source_transmission"] != "PERMITTED_WITH_CONDITIONS":
        raise ValidationError("the source gate does not record the approved assessment")
    if gates["provider_posture"] != "APPROVED":
        raise ValidationError("a provider whose posture is not APPROVED")
    if gates["eligibility_after"] != "ELIGIBLE":
        raise ValidationError("eligibility was not restored")
    if gates["packet_gate_after"] != "AVAILABLE":
        raise ValidationError("the packet gate does not report the permission")
    if gates["bytes_transmitted_to_any_external_model"] != 0:
        raise ValidationError(
            "bytes were transmitted. AVAILABLE is a gate state, and a permission is not an act"
        )
    if not str(gates["packet_gate_note"]).strip():
        raise ValidationError("no statement separating the permission from the act")


def _check_nothing_widened(record: dict, approval: dict) -> None:
    """The operator's list, carried rather than summarised."""
    scope = record["what_was_not_authorised"]
    if set(scope["items"]) != NOT_AUTHORIZED:
        raise ValidationError("the operator's list of what is not authorised was not carried whole")
    if set(scope["items"]) != set(approval["NOT_AUTHORIZED"]):
        raise ValidationError("the persistence record and the approval disagree about the limits")
    for activity, expected in UNWIDENED.items():
        if scope[activity] != expected:
            raise ValidationError(f"{activity} is {scope[activity]!r} and must stay {expected!r}")
    if scope["widened_by_this_mission"] != 0:
        raise ValidationError("an activity was widened by a persistence mission")
    if "REQUIRES_REVIEW" not in scope["commercial_profile_state"]:
        raise ValidationError("the commercial profile is not recorded as unchanged")


def _check_nothing_else_moved(record: dict) -> None:
    """Governance rows moved. Research rows did not."""
    state = record["canonical_state"]
    before, after = dict(state["before"]), dict(state["after"])
    if before.pop("source_reviews") + 1 != after.pop("source_reviews"):
        raise ValidationError("the review count did not move by exactly the one append")
    if before != after:
        raise ValidationError(
            f"canonical research state moved: {[k for k in before if before[k] != after[k]]}"
        )
    if state["CANONICAL_RESEARCH_MUTATION"] != 0:
        raise ValidationError("a canonical research mutation in a governance mission")
    written = state["governance_rows_written"]
    if written["source_policy_reviews"] != 1:
        raise ValidationError("more than one review was appended")
    reported = len([k for k in record["conditions_after_persistence"] if k.startswith("ted-")])
    if written["source_condition_verifications"] != reported:
        raise ValidationError(
            f"{written['source_condition_verifications']} verifications written for {reported} "
            "required conditions; appending a review orphans every one and each needs its own row"
        )

    accounting = record["mission_accounting"]
    for key in ZERO_ACCOUNTING:
        if accounting[key] != 0:
            raise ValidationError(f"{key} is {accounting[key]}, and a persistence mission does 0")

    candidate = record["selected_candidate_unchanged"]
    if candidate["SELECTED_SUBJECT"] != SUBJECT:
        raise ValidationError("the selected subject moved")
    if candidate["candidate_ranking_reopened"] or candidate["descended_to_category_grain"]:
        raise ValidationError("the candidate arc was reopened by a persistence mission")

    parked = record["parked_states_preserved"]
    if parked["changed_by_this_mission"]:
        raise ValidationError("a parked state changed")
    if parked["q1"]["CONSTRUCT_SELECTED"] or parked["q1"]["RUN_AUTHORIZED"]:
        raise ValidationError("Q1 moved")
    if (
        parked["globalping"]["PASS"],
        parked["globalping"]["PARTIAL"],
        parked["globalping"]["FAIL"],
    ) != (12, 0, 0):
        raise ValidationError("the Globalping tally moved")

    stale = record["known_consequence_not_repaired"]
    if not str(stale["why_not_regenerated"]).strip():
        raise ValidationError(
            "a known stale artifact with no stated reason for leaving it. Recording a consequence "
            "is the alternative to fixing it silently, and it needs the reason"
        )


def validate() -> tuple[dict, dict]:
    approval = _load(APPROVAL)
    record = _load(PERSISTENCE)
    packet = _load(PACKET)
    catalog = _load(CATALOG)
    compliance = _load(COMPLIANCE)

    if record["primary_outcome"] != "TED_EGRESS_PERMITTED_WITH_CONDITIONS_AND_ELIGIBILITY_RESTORED":
        raise ValidationError(f"outcome {record['primary_outcome']!r}")
    if not str(record["outcome_basis"]).strip():
        raise ValidationError("an outcome with no stated basis")

    _check_the_approval(approval, packet)
    _check_the_append(record, catalog, packet)
    _check_the_reconciliation(record, catalog, compliance)
    _check_the_conditions(record, catalog)
    _check_the_gates(record)
    _check_nothing_widened(record, approval)
    _check_nothing_else_moved(record)

    verification = record["verification_before_writing"]
    if (
        verification["DECISION_PACKET_SHA256_RECOMPUTED"]
        != approval["DECISION_PACKET_SHA256_RECOMPUTED"]
    ):
        raise ValidationError(
            "the persistence record and the approval recomputed different digests"
        )
    if not verification["REPRESENTATION_UNCHANGED"]:
        raise ValidationError(
            "the representation moved after the approval named it, so the approval names a payload "
            "this repository no longer produces"
        )
    if (
        verification["REPRESENTATION_SHA256_APPROVED"]
        != verification["REPRESENTATION_SHA256_REMEASURED"]
    ):
        raise ValidationError("the approved and the re-measured representation digests differ")
    egress = _load(EGRESS_REVIEW)
    if (
        verification["REPRESENTATION_SHA256_APPROVED"]
        != egress["representation"]["REPRESENTATION_SHA256"]
    ):
        raise ValidationError("the approved representation is not the one the review measured")
    return approval, record


def render_approval(approval: dict) -> str:
    lines = [
        f"# Operator decision on {approval['DECISION_PACKET_ID']}",
        "",
        "Generated from `ted-egress-operator-decision-v1.json`. Do not edit by hand.",
        "",
        f"**{approval['DECISION']}**, by {approval['decided_by']} "
        f"({approval['decided_by_kind']}), on {approval['recorded_at']}.",
        "",
        approval["$comment"],
        "",
        "## The packet this names",
        "",
        f"- id `{approval['DECISION_PACKET_ID']}`, version {approval['DECISION_PACKET_VERSION']}",
        f"- digest stated `{approval['DECISION_PACKET_SHA256_STATED']}`",
        f"- digest recomputed `{approval['DECISION_PACKET_SHA256_RECOMPUTED']}`",
        f"- they agree: **{str(approval['DECISION_PACKET_DIGEST_MATCHES']).lower()}**",
        "",
        approval["digest_note"] + ".",
        "",
        "## Scope",
        "",
    ]
    for key, value in approval["scope"].items():
        lines.append(f"- `{key}` = {value}")
    lines += ["", "## What it does not authorise", ""]
    for item in approval["NOT_AUTHORIZED"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## The acceptance, verbatim",
        "",
        approval["acceptance_note"] + ".",
        "",
        "```",
        approval["ACCEPTANCE_TEXT"].rstrip(),
        "```",
        "",
        f"Digest `{approval['ACCEPTANCE_SHA256']}`.",
        "",
        f"**Spent.** {approval['spent_note']}.",
        "",
    ]
    return "\n".join(lines)


def render(record: dict) -> str:
    append = record["append_not_edit"]
    gates = record["gates_after"]
    lines = [
        "# The TED egress decision, persisted",
        "",
        "Generated from `ted-egress-decision-persistence-v1.json`. Do not edit by hand.",
        "",
        f"**{record['primary_outcome']}**",
        "",
        record["outcome_basis"] + ".",
        "",
        "## The append",
        "",
        f"Review v{append['review_before']} to v{append['review_after']}, "
        f"{append['conditions_before']} conditions to {append['conditions_after']}, "
        f"{append['required_conditions_before']} required to {append['required_conditions_after']}.",
        "",
        append["v3_content_proof"] + ".",
        "",
        append["supersession_note"] + ".",
        "",
        f"**One assessment moved.** `external_model_transmission`, "
        f"{append['external_model_transmission_before']} to "
        f"{append['external_model_transmission_after']}. {append['before_note']}.",
        "",
        f"**The added condition is separate, not a widening.** "
        f"{append['required_condition_added_note']}.",
        "",
        "## The conditions",
        "",
        "| condition | kind | verifier | result |",
        "|---|---|---|---|",
    ]
    for key in sorted(k for k in record["conditions_after_persistence"] if k.startswith("ted-")):
        entry = record["conditions_after_persistence"][key]
        lines.append(
            f"| `{key}` | {entry['verification']} | {entry['verifier']} | **{entry['result']}** |"
        )
    lines += [
        "",
        record["conditions_after_persistence"]["one_statement_note"] + ".",
        "",
        "## The gates, after",
        "",
        "| gate | state |",
        "|---|---|",
        f"| source transmission | **{gates['source_transmission']}** |",
        f"| profile egress | {gates['profile_egress']} |",
        f"| provider posture | {gates['provider_posture']} |",
        f"| eligibility | {gates['eligibility_before']} to **{gates['eligibility_after']}** |",
        f"| the selected packet | {gates['packet_gate_before']} to **{gates['packet_gate_after']}** |",
        "",
        gates["packet_gate_note"] + ".",
        "",
        "## What did not move",
        "",
        record["canonical_state"]["governance_note"] + ".",
        "",
        f"Canonical research mutation {record['canonical_state']['CANONICAL_RESEARCH_MUTATION']}, "
        f"model calls {record['mission_accounting']['MODEL_CALLS']}, research-data fetches "
        f"{record['mission_accounting']['research_data_fetches']}, hypotheses synthesized "
        f"{record['mission_accounting']['hypotheses_synthesized']}.",
        "",
        "## A known consequence, recorded rather than repaired",
        "",
        record["known_consequence_not_repaired"]["what_is_now_stale"] + ".",
        "",
        record["known_consequence_not_repaired"]["why_not_regenerated"] + ".",
        "",
        f"**Next: {record['recommended_next_mission']['id']} "
        f"{record['recommended_next_mission']['title']}.** "
        f"{record['recommended_next_mission']['shape']}. "
        f"{record['recommended_next_mission']['note']}.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        approval, record = validate()
    except ValidationError as error:
        print(f"REFUSED  ted egress decision persistence: {error}")
        return 1
    pages = ((APPROVAL_MD, render_approval(approval)), (PERSISTENCE_MD, render(record)))
    if args.check:
        for path, text in pages:
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print("ok       the TED egress decision and its persistence match their records")
        return 0
    for path, text in pages:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(
        f"gates    transmission {record['gates_after']['source_transmission']}; "
        f"eligibility {record['gates_after']['eligibility_after']}; "
        f"packet {record['gates_after']['packet_gate_after']}"
    )
    print("sent     0 bytes; a permission is a gate state and not an act")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
