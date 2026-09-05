"""Render and validate the Mission 1.64 dispatch and residual-closure records.

Seven records, plus a manual dispatch packet generated from the FROZEN enquiry
rather than retyped, so the packet cannot drift from the document the operator
approved.

`validate()` enforces:

  - the approved enquiry's bytes still hash to the approved value, under a
    documented hashing boundary;
  - nothing is sent to an address nobody supplied, and no mailbox is inferred;
  - a dispatch is not an answer and an answer is not a PASS;
  - an ambiguous record lifecycle is not resolved in the direction that would
    qualify the last surviving candidate;
  - a configuration fact published for one data category is not transferred to
    another;
  - a field named as TRUNCATED is not called removed, and unnamed removed fields
    are not guessed in either direction;
  - fewer than two qualified apparatuses is not pair-ready, and no pair gate runs.

    uv run python infrastructure/scripts/render_enquiry_dispatch.py
    uv run python infrastructure/scripts/render_enquiry_dispatch.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.64-baseline-v1.json"
DISPATCH = DATA / "anchor-enquiry-dispatch-review-v1.json"
LIFECYCLE = DATA / "onyphe-datascan-record-lifecycle-v1.json"
PORTS = DATA / "onyphe-datascan-port-configuration-v1.json"
RETENTION = DATA / "onyphe-post-30d-field-retention-v1.json"
PACKAGE = DATA / "onyphe-package-final-recompute-v1.json"
READINESS = DATA / "apparatus-readiness-after-enquiry-dispatch-v1.json"

ENQUIRY_V1_JSON = DATA / "anchor-technical-lineage-enquiry-v1.json"
ENQUIRY_V1_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"
PACKET_MD = DATA / "anchor-enquiry-manual-dispatch-packet-v1.md"

APPROVED_SHA256 = "310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4"

ORDER = [BASELINE, DISPATCH, LIFECYCLE, PORTS, RETENTION, PACKAGE, READINESS]
RENDERED = {p: p.with_suffix(".md") for p in ORDER}

B_SLOTS = ("B1", "B2", "B3", "B4", "B5", "B6")
SLOT_STATES = ("PASS", "FAIL", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED", "NOT_APPLICABLE")

LIFECYCLE_STATES = (
    "OBSERVATION_EVENT_APPEND",
    "VERSIONED_OBSERVATION_HISTORY",
    "MAINTAINED_SERVICE_STATE_LAST_SEEN",
    "AMBIGUOUS",
    "UNKNOWN",
)

PORT_STATES = (
    "PORT_22_IN_DATASCAN_SET",
    "PORT_22_NOT_IN_DATASCAN_SET",
    "PORT_22_DATASCAN_STATUS_UNKNOWN",
)
CONFIG_TIME_STATES = ("CONFIGURATION_TIME_ADDRESSABLE", "CONFIGURATION_TIME_NOT_ADDRESSABLE")

RETENTION_STATES = {
    "ADDRESS": ("ADDRESS_SURVIVES", "ADDRESS_REMOVED", "ADDRESS_UNKNOWN"),
    "OBSERVATION_TIME": (
        "OBSERVATION_TIME_SURVIVES",
        "OBSERVATION_TIME_REMOVED",
        "OBSERVATION_TIME_UNKNOWN",
    ),
    "VANTAGE_FIELDS": (
        "VANTAGE_FIELDS_SURVIVE",
        "VANTAGE_FIELDS_REMOVED",
        "VANTAGE_FIELDS_UNKNOWN",
    ),
}

INDIVIDUAL_STATES = (
    "INDIVIDUALLY_QUALIFIED",
    "INDIVIDUALLY_NOT_QUALIFIED",
    "INDIVIDUALLY_UNRESOLVED",
)

APPARATUSES = ("LeakIX", "Netlas", "ONYPHE", "The Shadowserver Foundation")

PRIMARY_OUTCOMES = {
    "ANCHOR_ENQUIRY_DISPATCHED_ONYPHE_QUALIFIED",
    "ANCHOR_ENQUIRY_DISPATCHED_ONYPHE_UNRESOLVED",
    "ANCHOR_ENQUIRY_DISPATCHED_ONYPHE_NOT_QUALIFIED",
    "MANUAL_ANCHOR_ENQUIRY_DISPATCH_REQUIRED",
    "ANCHOR_CONTACT_CHANNEL_STILL_NOT_ESTABLISHED",
    "ONYPHE_TEMPORAL_OBJECT_NOT_ADDRESSABLE",
    "ONYPHE_DATASCAN_CONFIGURATION_GAP",
    "ONYPHE_LOCATION_FIELDS_RETENTION_GAP",
    "PREREGISTRATION_POSSIBILITY_COMPROMISED",
    "MISSION_1_63_NOT_MERGED",
    "MISSION_1_64_BASELINE_DRIFT",
    "MISSION_1_64_CANONICAL_MUTATION",
    "TARGETED_CONTACT_AND_ONYPHE_CLOSURE_BLOCKED",
}
DISPATCHED_OUTCOMES = {
    "ANCHOR_ENQUIRY_DISPATCHED_ONYPHE_QUALIFIED",
    "ANCHOR_ENQUIRY_DISPATCHED_ONYPHE_UNRESOLVED",
    "ANCHOR_ENQUIRY_DISPATCHED_ONYPHE_NOT_QUALIFIED",
}

OVERCLAIMS = (
    "installation",
    "customer",
    "subscription",
    "revenue",
    "market share",
    "adoption",
    "demand",
    "user base",
)

PREFERENCE_WORDS = (
    "best candidate",
    "preferred candidate",
    "strongest partner",
    "lead route",
    "front-runner",
    "front runner",
)

# A mailbox nobody published. Naming one in a record is fabricating a fact.
GUESSED_MAILBOXES = ("support@", "info@", "hello@", "security@", "contact@", "abuse@")


class ValidationError(Exception):
    """A Mission 1.64 record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _prose(node: object) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            out.extend(_prose(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_prose(item))
    elif isinstance(node, str):
        out.append(node)
    return out


def approved_digest() -> str:
    """The documented hashing boundary: the file's raw bytes as stored."""
    return hashlib.sha256(ENQUIRY_V1_MD.read_bytes()).hexdigest()


def validate() -> tuple[dict, ...]:
    records = tuple(_load(p) for p in ORDER)
    baseline, dispatch, lifecycle, ports, retention, package, readiness = records

    _validate_baseline(baseline)
    _validate_dispatch(dispatch)
    _validate_lifecycle(lifecycle)
    _validate_ports(ports)
    _validate_retention(retention)
    _validate_package(package, lifecycle, ports)
    _validate_readiness(readiness, dispatch, package)
    _validate_no_overclaims(records)
    _validate_no_preference(records)
    return records


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_63_merged") is not True:
        raise ValidationError("Mission 1.63 is not recorded as merged")
    if pre.get("verified_from_git_not_from_prompt") is not True:
        raise ValidationError(
            "the precondition must be verified from git rather than from a prompt"
        )

    check = baseline["approved_enquiry_hash_verification"]
    if check["approved_sha256"] != APPROVED_SHA256:
        raise ValidationError(
            "the recorded approved hash is not the operator's. The approval is immutable"
        )
    if check.get("verdict") != "HASH_VERIFIED":
        raise ValidationError("the approved enquiry did not verify")
    if not check.get("boundaries_tested"):
        raise ValidationError(
            "the hashing boundary must be documented. A hash whose boundary nobody wrote down is "
            "a hash two readers can disagree about"
        )
    for boundary in check["boundaries_tested"]:
        if boundary.get("digest") != APPROVED_SHA256 or boundary.get("matches") is not True:
            raise ValidationError(
                f"boundary {boundary.get('boundary')!r} does not match the approved hash"
            )
    live = approved_digest()
    if live != APPROVED_SHA256:
        raise ValidationError(
            f"§A1: the approved enquiry's bytes have changed. approved {APPROVED_SHA256}, "
            f"computed {live}. Do NOT send"
        )

    # The frozen enquiry's OWN state, not just its bytes. Mission 1.63's validator
    # checked this and this one dropped it; the probe found the gap by marking the
    # frozen document sent and watching nothing object. A hash guards the body and
    # says nothing about the delivery fields beside it.
    v1 = _load(ENQUIRY_V1_JSON)
    if v1.get("status") != "AWAITING_OPERATOR_APPROVAL":
        raise ValidationError(
            f"§A1: the frozen enquiry's status reads {v1.get('status')!r}. Marking it approved "
            "changes the document the approval names"
        )
    if v1["delivery"].get("sent") is not False:
        raise ValidationError(
            "§A5: the frozen enquiry records itself as sent, and this mission sent nothing"
        )
    if v1["delivery"].get("sent_at") is not None:
        raise ValidationError(
            "§A5: the frozen enquiry carries a send time. This repository may prepare a message "
            "and may never imply it was delivered"
        )
    for flag in (
        "bytes_changed",
        "renderer_rewrote_it",
        "subject_or_body_edited",
        "recipient_added_inside_hashed_body",
    ):
        if check.get(flag) is not False:
            raise ValidationError(f"§A1: {flag} must be false")

    acct = baseline["request_accounting"]
    for name in (
        "MEASUREMENT_QUERIES_EXECUTED",
        "TARGET_COUNTS_FETCHED",
        "HOST_RECORDS_FETCHED",
        "TARGET_BANNERS_FETCHED",
        "FACETS_FETCHED",
        "MEASUREMENT_DOWNLOADS",
        "TRIALS_STARTED",
        "PURCHASES",
        "OUTBOUND_ENQUIRIES_SENT",
    ):
        if acct.get(name) != 0:
            raise ValidationError(f"{name} must be 0 and reads {acct.get(name)!r}")
    if baseline["documentation_ledger"]["used"] != len(
        baseline["documentation_ledger"]["requests"]
    ):
        raise ValidationError("the ledger count and its entries disagree")

    for name, value in baseline["canonical_mutations"].items():
        if name.startswith("$"):
            continue
        if value not in (0, 0.0, False):
            raise ValidationError(f"canonical mutation {name} reads {value!r} and must be zero")


def _validate_dispatch(dispatch: dict) -> None:
    approval = dispatch["approval"]
    if approval["approved_sha256"] != APPROVED_SHA256:
        raise ValidationError("the dispatch record names a hash that is not the approved one")
    if approval.get("hash_verdict") != "HASH_VERIFIED":
        raise ValidationError("dispatch preparation requires a verified hash")

    a2 = dispatch["a2_the_approved_message_is_still_current"]
    if a2["answered_by_new_anchor_evidence"] and a2.get("superseded_before_send") is not True:
        raise ValidationError(
            "§A2: an anchor question became answered from new first-party evidence, so v1 must be "
            "SUPERSEDED_BEFORE_SEND and a new enquiry and hash required"
        )
    if (
        a2["still_unresolved"] + a2["answered_by_new_anchor_evidence"]
        != a2["questions_reassessed_against_mission_1_63_state"]
    ):
        raise ValidationError("the reassessment tally does not add up")

    recipient = dispatch["a3_recipient"]
    if (
        recipient.get("address_invented") is not False
        or recipient.get("address_inferred") is not False
    ):
        raise ValidationError("§A3: no contact address may be invented or inferred")
    blob = json.dumps(recipient) + json.dumps(dispatch.get("a5_dispatch", {}))
    for guess in GUESSED_MAILBOXES:
        if guess in blob:
            raise ValidationError(f"§A3: the record names a guessed mailbox form {guess!r}")

    sent = dispatch["a5_dispatch"]
    established = (
        bool(recipient.get("exact_address")) and recipient.get("supplied_by_operator") is True
    )
    if sent.get("sent") is True and not established:
        raise ValidationError(
            "an enquiry was sent without an operator-supplied first-party address. The exact string "
            "must come from the operator viewing the first-party page"
        )
    if sent.get("dispatch_count", 0) > 1:
        raise ValidationError("§A5: exactly one dispatch. No automatic follow-up, no mailing list")
    if sent.get("sent") is False and sent.get("sent_at") is not None:
        raise ValidationError("an unsent enquiry may not carry a send time")

    a7 = dispatch["a7_sending_would_not_have_answered_anything"]
    if a7.get("anchor_gate_changed_this_mission") is not False:
        raise ValidationError(
            "§A7: a dispatched enquiry is not an answered question, and no anchor gate may move "
            "without a received and reviewed response"
        )
    if a7["anchor_a8_before"] != a7["anchor_a8_after"]:
        raise ValidationError("§A7: A8 changed without a provider response")

    intake = dispatch["provider_response_intake_boundary"]
    if intake.get("response_received") is True:
        raise ValidationError(
            "a response is recorded as received. It must be frozen and reviewed in a separate step "
            "before any gate moves, which this mission did not perform"
        )
    if intake["if_a_response_arrives"].get("automatic_promotion_to_PASS") != "forbidden":
        raise ValidationError("an answer may not be promoted to PASS without review")


def _validate_lifecycle(lifecycle: dict) -> None:
    verdict = lifecycle["verdict"]
    if verdict["record_lifecycle"] not in LIFECYCLE_STATES:
        raise ValidationError(
            f"record lifecycle {verdict['record_lifecycle']!r} is not in the vocabulary"
        )
    if verdict["b2_result"] not in SLOT_STATES:
        raise ValidationError(f"B2 result {verdict['b2_result']!r} is not in the vocabulary")

    if verdict["b2_result"] == "PASS" and verdict["record_lifecycle"] not in (
        "OBSERVATION_EVENT_APPEND",
        "VERSIONED_OBSERVATION_HISTORY",
    ):
        raise ValidationError(
            "§B2: B2 passes only where a future observation generated in a window can be selected "
            "before retrieval. An ambiguous or maintained-state lifecycle cannot pass"
        )
    if verdict["record_lifecycle"] == "AMBIGUOUS" and verdict["b2_result"] == "PASS":
        raise ValidationError(
            "§B2: never choose the favourable interpretation. An ambiguous lifecycle leaves B2 PARTIAL"
        )
    if (
        verdict["record_lifecycle"] == "MAINTAINED_SERVICE_STATE_LAST_SEEN"
        and verdict["b2_result"] != "FAIL"
    ):
        raise ValidationError("§B2: a maintained last-seen lifecycle fails B2")
    if not verdict.get("the_interpretation_that_was_not_chosen", "").strip():
        raise ValidationError("the record must name the interpretation it declined")

    if not lifecycle["the_discriminating_case_that_is_still_unaddressed"].get("case", "").strip():
        raise ValidationError(
            "§B2: the record must name the case that separates the two lifecycles, or the residual "
            "cannot be asked as a question"
        )

    empirical = lifecycle["what_would_close_it"]["no_empirical_resolution_attempted"]
    for name in ("records_queried", "hosts_queried", "timestamps_compared"):
        if empirical.get(name) != 0:
            raise ValidationError(
                f"§B1: {name} reads {empirical.get(name)!r}. Documentation only; a sample query "
                "retrieves measurement and infers an architecture"
            )

    for item in lifecycle["new_first_party_evidence"]:
        if item.get("verbatim") and not item.get("why_it_is_not_decisive", "").strip():
            raise ValidationError(
                f"evidence from {item.get('source')!r} is quoted without saying what it does not "
                "settle. Converging evidence is not a statement"
            )


def _validate_ports(ports: dict) -> None:
    verdict = ports["verdict"]
    if verdict["membership"] not in PORT_STATES:
        raise ValidationError(f"port membership {verdict['membership']!r} is not in the vocabulary")
    if verdict["configuration_time_addressability"] not in CONFIG_TIME_STATES:
        raise ValidationError("configuration time addressability is not in the vocabulary")

    found = ports["what_was_found"]
    if (
        found.get("a_datascan_section_exists") is False
        and verdict["membership"] == "PORT_22_IN_DATASCAN_SET"
    ):
        raise ValidationError(
            "§B4: no datascan port section exists, so datascan membership cannot be established. "
            "The ctiscan list is not evidence for datascan"
        )
    transfer = ports["no_category_transfer_was_performed"]
    if transfer.get("used") is not False:
        raise ValidationError("§B4: a configuration fact was transferred between data categories")
    if not transfer.get("the_symmetric_refusal", "").strip():
        raise ValidationError(
            "§B4: the reverse inference must be refused too. Absence of a published list does not "
            "establish exclusion"
        )
    if (
        found.get("is_the_500_port_membership_published") is True
        and verdict["membership"] == "PORT_22_DATASCAN_STATUS_UNKNOWN"
    ):
        raise ValidationError("the membership is published and the verdict still reads unknown")


def _validate_retention(retention: dict) -> None:
    kept = retention["what_is_already_established_and_not_reopened"]
    if kept.get("the_raw_field_is_truncated_not_removed") is not True:
        raise ValidationError(
            "§B5: the raw field is TRUNCATED and not removed. Calling truncation removal reopens a "
            "gate on evidence that says the opposite"
        )
    if kept.get("b3_reopened") is not False:
        raise ValidationError("§B5: B3 is not reopened without contradictory evidence")
    if kept.get("contradictory_evidence_found") is not False:
        raise ValidationError("contradictory evidence is recorded and B3 was not reopened")

    verdict = retention["verdict"]
    for key, allowed in RETENTION_STATES.items():
        if verdict.get(key) not in allowed:
            raise ValidationError(
                f"{key} carries {verdict.get(key)!r}, which is not in the vocabulary"
            )
    if verdict.get("unnamed_removed_fields_inferred") is not False:
        raise ValidationError("§B6: unnamed removed fields may not be inferred")
    for key in ("why_not_inferred_present", "why_not_inferred_absent"):
        if not verdict.get(key, "").strip():
            raise ValidationError(f"§B6: the record must state {key}")

    found = retention["what_was_found"]
    if found.get("per_field_retention_annotations_exist") is False:
        for key in RETENTION_STATES:
            if not str(verdict[key]).endswith("UNKNOWN"):
                raise ValidationError(
                    f"§B6: no per-field retention annotation exists and {key} is recorded as "
                    f"{verdict[key]!r}. That is a guess"
                )

    bound = retention["full_fidelity_bound"]
    if not bound.get("MAX_FULL_FIDELITY_RETRIEVAL_DELAY", "").strip():
        raise ValidationError("§B7: the full-fidelity retrieval delay stays frozen")
    if bound.get("finite_retention_is_a_scheduling_constraint") is not True:
        raise ValidationError("§B7: finite retention is a scheduling constraint, not a failure")
    for flag in ("no_observation_dates_chosen", "no_records_fetched"):
        if bound.get(flag) is not True:
            raise ValidationError(f"§B7: {flag} must hold")


def _validate_package(package: dict, lifecycle: dict, ports: dict) -> None:
    pkg = package["package"]
    for slot in B_SLOTS:
        if slot not in pkg:
            raise ValidationError(
                f"§B8: slot {slot} was not recomputed. Report every mandatory gate"
            )
        entry = pkg[slot]
        for field in ("before", "after"):
            if entry[field] not in SLOT_STATES:
                raise ValidationError(f"{slot} carries {field} = {entry[field]!r}")
        if entry["changed"] != (entry["before"] != entry["after"]):
            raise ValidationError(f"{slot} disagrees with itself about whether it changed")
        if not entry.get("basis", "").strip():
            raise ValidationError(f"{slot} records no basis")
        if "binding_blocker" not in entry:
            raise ValidationError(f"{slot} does not say whether it is a binding blocker")

    if pkg["B2"]["after"] != lifecycle["verdict"]["b2_result"]:
        raise ValidationError("the package and the lifecycle review disagree about B2")
    if (
        ports["verdict"]["membership"] == "PORT_22_DATASCAN_STATUS_UNKNOWN"
        and pkg["B4"]["after"] == "PASS"
    ):
        raise ValidationError("B4 passes while datascan port-22 membership is unknown")
    if package["slots_changed"] != sum(1 for s in B_SLOTS if pkg[s]["changed"]):
        raise ValidationError("the changed-slot count disagrees with the slots")

    qual = package["individual_qualification"]
    if qual["verdict"] not in INDIVIDUAL_STATES:
        raise ValidationError(f"individual verdict {qual['verdict']!r} is not in the vocabulary")
    hard_fails = [s for s in B_SLOTS if pkg[s]["after"] == "FAIL"]
    all_pass = all(pkg[s]["after"] == "PASS" for s in B_SLOTS)
    if hard_fails and qual["verdict"] != "INDIVIDUALLY_NOT_QUALIFIED":
        raise ValidationError(f"a hard FAIL at {hard_fails} must give INDIVIDUALLY_NOT_QUALIFIED")
    if qual["verdict"] == "INDIVIDUALLY_QUALIFIED" and not all_pass:
        raise ValidationError("§B8: qualification is conjunctive. A partial is not a pass")
    if qual.get("not_ranked") is not True or qual.get("not_compared_to_the_anchor") is not True:
        raise ValidationError("§B8: the package is not ranked and not compared to the anchor")
    declared = [s for s in B_SLOTS if pkg[s].get("binding_blocker")]
    if sorted(qual.get("binding_blockers", [])) != sorted(declared):
        raise ValidationError("the declared binding blockers and the slots disagree")


def _validate_readiness(readiness: dict, dispatch: dict, package: dict) -> None:
    if readiness["primary_outcome"] not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {readiness['primary_outcome']!r}")
    if not readiness.get("primary_outcome_statement", "").strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")

    outcome = readiness["primary_outcome"]
    sent = dispatch["a5_dispatch"].get("sent") is True
    if outcome in DISPATCHED_OUTCOMES and not sent:
        raise ValidationError(
            f"§45: outcome {outcome} requires the enquiry to have been sent, and it was not"
        )
    if outcome == "ANCHOR_CONTACT_CHANNEL_STILL_NOT_ESTABLISHED" and dispatch["a3_recipient"].get(
        "exact_address"
    ):
        raise ValidationError("outcome E requires no exact address to have been supplied")
    if outcome == "MANUAL_ANCHOR_ENQUIRY_DISPATCH_REQUIRED" and not dispatch["a3_recipient"].get(
        "exact_address"
    ):
        raise ValidationError(
            "§45: outcome D requires the exact contact channel to be established. Without it "
            "the missing piece is upstream of the mechanism"
        )

    listed = {a["name"]: a for a in readiness["apparatuses"]}
    if set(listed) != set(APPARATUSES):
        raise ValidationError(f"readiness must cover exactly {APPARATUSES}")
    for name, entry in listed.items():
        if entry["individual_status"] not in INDIVIDUAL_STATES:
            raise ValidationError(f"{name} carries status {entry['individual_status']!r}")
    if listed["ONYPHE"]["individual_status"] != package["individual_qualification"]["verdict"]:
        raise ValidationError("the readiness record and the ONYPHE package disagree")
    if not sent and listed["Netlas"]["individual_status"] == "INDIVIDUALLY_QUALIFIED":
        raise ValidationError(
            "the anchor cannot qualify. A gate moves on a received and reviewed answer, never on a "
            "dispatch, and nothing was dispatched"
        )

    block = readiness["readiness"]
    counted = sum(1 for a in listed.values() if a["individual_status"] == "INDIVIDUALLY_QUALIFIED")
    if block["QUALIFIED_APPARATUS_COUNT"] != counted:
        raise ValidationError("the qualified count disagrees with the apparatus states")
    if block["PAIR_ANALYSIS_READY"] != (counted >= block["threshold_for_readiness"]):
        raise ValidationError("pair analysis is ready exactly when two apparatuses qualify")
    if block.get("this_is_a_status_not_a_selection") is not True:
        raise ValidationError("readiness is a status and never a selection")
    if readiness["secondary_outcomes"]["QUALIFIED_APPARATUS_COUNT"] != counted:
        raise ValidationError("the secondary outcomes and the readiness block disagree")

    pair = readiness["no_pair_work_was_performed"]
    for flag in (
        "same_frame_evaluated",
        "same_observation_window_evaluated",
        "vantage_compatibility_evaluated",
        "lineage_independence_evaluated",
        "shared_measurement_upstream_evaluated",
        "same_target_proposition_evaluated",
        "threshold_preregistrability_evaluated",
    ):
        if pair.get(flag) is not False:
            raise ValidationError(f"{flag} must be false. No pair gate may be evaluated")
    for counter in ("pairs_compared", "pairs_ranked", "pairs_selected"):
        if pair.get(counter) != 0:
            raise ValidationError(f"{counter} must be 0")

    controls = readiness["the_negative_controls_were_left_alone"]
    if controls.get("researched") != 0 or controls.get("rescue_attempted") != 0:
        raise ValidationError("the negative controls must be left alone")

    for name, value in readiness["stop_condition"].items():
        if name.startswith("$") or name == "awaiting":
            continue
        if value is not False:
            raise ValidationError(
                f"the stop condition {name} reads {value!r} and every one must be false"
            )


def _validate_no_overclaims(records: tuple[dict, ...]) -> None:
    for record in records:
        for sentence in _prose(record):
            tokens = re.findall(r"[a-z0-9]+", sentence.lower())
            for term in OVERCLAIMS:
                parts = term.split()
                if len(parts) == 1:
                    hit = parts[0] in tokens
                else:
                    hit = any(
                        tokens[i : i + len(parts)] == parts
                        for i in range(max(0, len(tokens) - len(parts) + 1))
                    )
                if hit:
                    raise ValidationError(
                        f"a record uses {term!r}. A count of addresses answering on a port is not a "
                        f"market statement. Offending sentence: {sentence[:110]!r}"
                    )


def _validate_no_preference(records: tuple[dict, ...]) -> None:
    for record in records:
        for sentence in _prose(record):
            lowered = sentence.lower()
            for word in PREFERENCE_WORDS:
                if word in lowered:
                    raise ValidationError(
                        f"a record uses {word!r}. This mission ranks nothing. Offending sentence: "
                        f"{sentence[:110]!r}"
                    )


# --------------------------------------------------------------------------- render


def render_packet(enquiry: dict, dispatch: dict) -> str:
    """The manual dispatch packet, generated from the FROZEN enquiry.

    Retyping the body would let the packet drift from the document the operator
    approved. Generating it means the two cannot disagree.
    """
    recipient = dispatch["a3_recipient"]
    address = recipient.get("exact_address") or "__TO_BE_SUPPLIED_BY_OPERATOR__"
    lines = [
        "# Anchor technical enquiry — manual dispatch packet",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        "The body below is generated from the frozen enquiry record, not retyped, so this packet",
        "cannot drift from the document the operator approved.",
        "",
        _row(["field", "value"]),
        _row(["---", "---"]),
        _row(["approved document", "`docs/data/anchor-technical-lineage-enquiry-v1.md`"]),
        _row(["approved sha256", f"`{APPROVED_SHA256}`"]),
        _row(["hashing boundary", "the file's raw bytes as stored"]),
        _row(["operator approval", f"`{dispatch['approval']['operator_approval_string']}`"]),
        _row(["status", f"`{dispatch['a5_dispatch']['status']}`"]),
        "",
        "## TO",
        "",
        f"    {address}",
        "",
    ]
    if address.startswith("__"):
        lines += [
            f"The address is **not established**. {recipient['why']}",
            "",
            f"To supply it: {recipient['the_operator_action_that_resolves_it']}",
            "",
            "**Do not substitute a guessed mailbox.** No address was inferred and none may be.",
            "",
        ]
    lines += [
        "## SUBJECT",
        "",
        f"    {enquiry['subject']}",
        "",
        "## BODY",
        "",
        enquiry["preamble"],
        "",
    ]
    for q in enquiry["questions"]:
        lines += [f"**{q['n']}. {q['topic']}.** {q['question']}", ""]
    lines += [
        enquiry["closing"],
        "",
        "---",
        "",
        "## What sending this does and does not do",
        "",
        f"- {dispatch['a7_sending_would_not_have_answered_anything']['rule']}",
        "- Send exactly once. No automatic follow-up, no mailing list, no CC or BCC.",
        "- A reply is recorded as correspondence evidence and reviewed separately before any gate "
        "moves.",
        "",
    ]
    return "\n".join(lines)


def render_baseline(record: dict) -> str:
    pre = record["repository_precondition"]
    base = record["canonical_baseline"]
    check = record["approved_enquiry_hash_verification"]
    acct = record["request_accounting"]
    lines = [
        "# Mission 1.64 — baseline",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        f"**Mission:** {record['mission']}  ",
        f"**Recorded:** {record['recorded_at']}",
        "",
        "## Precondition",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["Mission 1.63 merged", str(pre["mission_1_63_merged"])]),
        _row(["merge commit", f"`{pre['merge_commit']}`"]),
        _row(["branch", f"`{pre['branch']}`"]),
        _row(["migration head", f"`{pre['migration_head']}`"]),
        _row(["drift", f"**{base['drift_from_mission_1_63']}**"]),
        "",
        "## Approved enquiry hash",
        "",
        f"    approved  {check['approved_sha256']}",
        "",
        _row(["hashing boundary", "digest matches"]),
        _row(["---", "---"]),
    ]
    for b in check["boundaries_tested"]:
        lines.append(_row([b["boundary"], "yes" if b["matches"] else "**no**"]))
    lines += [
        "",
        check["why_all_three_agree"],
        "",
        f"**Verdict: `{check['verdict']}`.** {check['the_recipient_is_outside_the_frozen_range']}",
        "",
        "## Documentation ledger",
        "",
        f"{record['documentation_ledger']['used']} retrievals, all on Part B.",
        "",
        _row(["#", "target", "sought"]),
        _row(["---", "---", "---"]),
    ]
    for e in record["documentation_ledger"]["requests"]:
        lines.append(_row([str(e["n"]), e["target"], e["sought"]]))
    lines += [
        "",
        "## What did not happen",
        "",
        "```",
        f"measurement queries   {acct['MEASUREMENT_QUERIES_EXECUTED']}"
        f"    trials      {acct['TRIALS_STARTED']}",
        f"target counts         {acct['TARGET_COUNTS_FETCHED']}    purchases   {acct['PURCHASES']}",
        f"host records          {acct['HOST_RECORDS_FETCHED']}"
        f"    facets      {acct['FACETS_FETCHED']}",
        f"banners               {acct['TARGET_BANNERS_FETCHED']}"
        f"    enquiries   {acct['OUTBOUND_ENQUIRIES_SENT']}",
        "```",
        "",
        acct["the_documentation_carried_examples"],
        "",
    ]
    return "\n".join(lines)


def render_dispatch(record: dict) -> str:
    recipient = record["a3_recipient"]
    method = record["a4_dispatch_method"]
    verdict = record["verdict"]
    lines = [
        "# Anchor enquiry — dispatch review",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        f"**`{verdict['result']}`** — the enquiry is {verdict['enquiry_state']}.",
        "",
        "## The approval",
        "",
        f"    {record['approval']['operator_approval_string']}",
        "",
        f"Hash re-verified this mission: **{record['approval']['hash_verdict']}**.",
        "",
        f"*Authorises:* {record['approval']['what_the_approval_authorises']}",
        "",
        "*Does not authorise:*",
        "",
    ]
    lines += [f"- {i}" for i in record["approval"]["what_it_does_not_authorise"]]
    a2 = record["a2_the_approved_message_is_still_current"]
    lines += [
        "",
        "## The message is still current",
        "",
        f"{a2['still_unresolved']} of {a2['questions_reassessed_against_mission_1_63_state']} "
        f"questions still unresolved, {a2['answered_by_new_anchor_evidence']} answered by new "
        f"anchor evidence. Verdict **`{a2['verdict']}`**.",
        "",
        a2["why_the_onyphe_work_does_not_touch_it"],
        "",
        "## The recipient",
        "",
        f"`{recipient['status']}`. A contact page exists: <{recipient['contact_page']}>.",
        "",
        recipient["why"],
        "",
        f"*Resolved by:* {recipient['the_operator_action_that_resolves_it']}",
        "",
        f"*On the obfuscation:* {recipient['why_not']}",
        "",
        "## Dispatch method",
        "",
        f"Authorised outbound mail mechanism in this repository: "
        f"**{method['authorised_outbound_mail_mechanism_in_this_repository']}**.",
        "",
        "A mail-capable connector exists in the environment and was not used:",
        "",
    ]
    lines += [f"- {i}" for i in method["why_not"]]
    lines += [
        "",
        f"**{method['conclusion']}**",
        "",
        "## Sending would not have answered anything",
        "",
        record["a7_sending_would_not_have_answered_anything"]["rule"],
        "",
        f"A8 before `{record['a7_sending_would_not_have_answered_anything']['anchor_a8_before']}`, "
        f"after `{record['a7_sending_would_not_have_answered_anything']['anchor_a8_after']}`.",
        "",
        "## Verdict",
        "",
        verdict["this_is_not_a_repository_defect"],
        "",
        verdict["why_the_mission_did_not_stop_here"],
        "",
    ]
    return "\n".join(lines)


def render_lifecycle(record: dict) -> str:
    verdict = record["verdict"]
    case = record["the_discriminating_case_that_is_still_unaddressed"]
    lines = [
        "# ONYPHE datascan — record lifecycle",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        f"**Lifecycle:** `{verdict['record_lifecycle']}`  ",
        f"**B2:** `{verdict['b2_result']}`",
        "",
        record["the_question"]["why_it_decides_b2"],
        "",
        "## New first-party evidence",
        "",
    ]
    for item in record["new_first_party_evidence"]:
        if item.get("verbatim"):
            lines += [f"> {item['verbatim']}", ""]
            lines += [f"*Supports:* {item['what_it_supports']}", ""]
            lines += [f"*Not decisive because:* {item['why_it_is_not_decisive']}", ""]
        else:
            lines += [f"**{item['finding']}**", ""]
            for key in ("what_it_supports", "why_it_is_not_decisive", "why_it_is_recorded"):
                if item.get(key):
                    lines += [f"*{key.replace('_', ' ')}:* {item[key]}", ""]
    lines += [
        "## The discriminating case",
        "",
        f"**{case['case']}**",
        "",
        f"- *append model* — {case['under_an_append_model']}",
        f"- *maintained model* — {case['under_a_maintained_model']}",
        f"- *which the documentation states* — **{case['which_one_the_documentation_states']}**",
        "",
        case["why_the_easier_case_does_not_help"],
        "",
        "## Verdict",
        "",
        f"*Why not UNKNOWN:* {verdict['why_not_UNKNOWN']}",
        "",
        f"*Why not an append model:* {verdict['why_not_OBSERVATION_EVENT_APPEND']}",
        "",
        f"**The interpretation that was not chosen.** "
        f"{verdict['the_interpretation_that_was_not_chosen']}",
        "",
        verdict["the_mission_1_63_lesson_applied"],
        "",
        "## What would close it",
        "",
        record["what_would_close_it"]["one_sentence"],
        "",
        record["what_would_close_it"][
            "why_this_is_now_an_enquiry_question_rather_than_a_reading_question"
        ],
        "",
    ]
    return "\n".join(lines)


def render_ports(record: dict) -> str:
    found = record["what_was_found"]
    verdict = record["verdict"]
    lines = [
        "# ONYPHE datascan — port configuration",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        f"**Membership:** `{verdict['membership']}`  ",
        f"**Configuration time:** `{verdict['configuration_time_addressability']}`",
        "",
        record["the_question"]["why_the_ctiscan_list_does_not_answer_it"],
        "",
        "## What was found",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["category sections on the page", str(found["category_sections_on_the_page"])]),
        _row(["the only section", f"`{found['the_only_section']}`"]),
        _row(["a datascan section exists", f"**{found['a_datascan_section_exists']}**"]),
        _row(
            [
                "datascan cycle as documented",
                found["what_the_refresh_documentation_says_about_datascan"],
            ]
        ),
        _row(["500-port membership published", str(found["is_the_500_port_membership_published"])]),
        "",
        f"**{found['conclusion']}**",
        "",
        "## No category transfer",
        "",
        f"*The forbidden inference:* {record['no_category_transfer_was_performed']['the_forbidden_inference']}",
        "",
        record["no_category_transfer_was_performed"]["why_it_is_forbidden"],
        "",
        record["no_category_transfer_was_performed"]["the_symmetric_refusal"],
        "",
        "## Verdict",
        "",
        verdict["what_did_move"],
        "",
        f"*Configuration time addressability:* {verdict['why']}",
        "",
        f"**Is this a configuration-gap outcome?** "
        f"{record['is_this_a_configuration_gap_outcome']['selected']}. "
        f"{record['is_this_a_configuration_gap_outcome']['why_not']}",
        "",
    ]
    return "\n".join(lines)


def render_retention(record: dict) -> str:
    kept = record["what_is_already_established_and_not_reopened"]
    verdict = record["verdict"]
    bound = record["full_fidelity_bound"]
    lines = [
        "# ONYPHE — fields after thirty days",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        "## Already established, not reopened",
        "",
        f"> {kept['verbatim_rule']}",
        "",
        kept["why_that_matters"],
        "",
        f"B3 reopened: **{kept['b3_reopened']}**.",
        "",
        "## What this mission asked",
        "",
        record["what_this_mission_asked"]["why_those_four"],
        "",
        "## What was found",
        "",
        f"Per-field retention annotations exist: "
        f"**{record['what_was_found']['per_field_retention_annotations_exist']}**.",
        "",
        record["what_was_found"]["finding"],
        "",
        "## Verdict",
        "",
        _row(["field group", "state"]),
        _row(["---", "---"]),
        _row(["address", f"`{verdict['ADDRESS']}`"]),
        _row(["observation time", f"`{verdict['OBSERVATION_TIME']}`"]),
        _row(["vantage fields", f"`{verdict['VANTAGE_FIELDS']}`"]),
        "",
        f"*Why not inferred present:* {verdict['why_not_inferred_present']}",
        "",
        f"*Why not inferred absent:* {verdict['why_not_inferred_absent']}",
        "",
        f"*What moved:* {verdict['what_did_move']}",
        "",
        "## Full-fidelity bound",
        "",
        _row(["contract", "value"]),
        _row(["---", "---"]),
        _row(["`MAX_FULL_FIDELITY_RETRIEVAL_DELAY`", bound["MAX_FULL_FIDELITY_RETRIEVAL_DELAY"]]),
        _row(
            [
                "`MAX_PREDICATE_SUFFICIENT_RETRIEVAL_DELAY`",
                bound["MAX_PREDICATE_SUFFICIENT_RETRIEVAL_DELAY"],
            ]
        ),
        "",
        bound["why"],
        "",
        f"*The conservative contract:* {bound['the_conservative_contract']}",
        "",
        f"**Is this a retention-gap outcome?** "
        f"{record['is_this_a_location_fields_retention_gap_outcome']['selected']}. "
        f"{record['is_this_a_location_fields_retention_gap_outcome']['why_not']}",
        "",
    ]
    return "\n".join(lines)


def render_package(record: dict) -> str:
    qual = record["individual_qualification"]
    lines = [
        "# ONYPHE package — final recompute",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        f"**`{qual['verdict']}`**, binding blockers **{qual['binding_blockers']}**.",
        "",
        f"`{record['slots_changed']}` slots changed, `{record['slots_better_evidenced']}` better "
        f"evidenced ({', '.join(record['which_better_evidenced'])}).",
        "",
        _row(["slot", "requirement", "before", "after", "blocker"]),
        _row(["---"] * 5),
    ]
    for slot in B_SLOTS:
        e = record["package"][slot]
        lines.append(
            _row(
                [
                    slot,
                    e["slot"],
                    f"`{e['before']}`",
                    f"`{e['after']}`",
                    "**yes**" if e["binding_blocker"] else "",
                ]
            )
        )
    lines += ["", "## Slot findings", ""]
    for slot in B_SLOTS:
        e = record["package"][slot]
        lines += [f"### {slot} {e['slot']} — `{e['after']}`", "", e["basis"], ""]
        for key in (
            "what_improved",
            "the_residual",
            "record_lifecycle",
            "classification",
            "lineage_level",
        ):
            if e.get(key):
                lines += [f"*{key.replace('_', ' ')}:* {e[key]}", ""]
        if e.get("missing_facts"):
            lines += ["*missing facts:* " + "; ".join(e["missing_facts"]), ""]
    lines += [
        "## Qualification",
        "",
        qual["reason"],
        "",
        qual["why_three_missions_have_not_moved_it"],
        "",
        f"**{qual['the_shape_this_produces']}**",
        "",
        "## The three residual questions",
        "",
    ]
    lines += [
        f"{i + 1}. {q}" for i, q in enumerate(record["the_three_residual_questions"]["questions"])
    ]
    lines += [
        "",
        record["the_three_residual_questions"]["why_not"],
        "",
    ]
    return "\n".join(lines)


def render_readiness(record: dict) -> str:
    block = record["readiness"]
    nxt = record["next_mission_recommendation"]
    lines = [
        "# Apparatus readiness after enquiry dispatch",
        "",
        "Generated by `infrastructure/scripts/render_enquiry_dispatch.py`. Do not edit.",
        "",
        f"**Outcome: `{record['primary_outcome']}`**",
        "",
        record["primary_outcome_statement"],
        "",
        "## Why this outcome and not another",
        "",
    ]
    for key, text in record["why_this_outcome_and_not_another"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += ["", "## Secondary outcomes", "", _row(["subject", "state"]), _row(["---", "---"])]
    for key, value in record["secondary_outcomes"].items():
        if key.startswith("$"):
            continue
        lines.append(_row([key.replace("_", " "), f"`{value}`"]))
    lines += [
        "",
        "## Apparatuses",
        "",
        _row(["apparatus", "status", "binding failure", "researched"]),
        _row(["---"] * 4),
    ]
    for a in record["apparatuses"]:
        lines.append(
            _row(
                [
                    a["name"],
                    f"`{a['individual_status']}`",
                    a["binding_failure"],
                    "yes" if a["researched_this_mission"] else "",
                ]
            )
        )
    lines += [
        "",
        f"**`{block['status_word']}`.** Qualified `{block['QUALIFIED_APPARATUS_COUNT']}` of a "
        f"threshold of `{block['threshold_for_readiness']}`.",
        "",
        block["sending_the_enquiry_would_not_have_changed_this"],
        "",
        "## The shape this mission leaves",
        "",
        record["the_shape_this_mission_leaves"]["observation"],
        "",
        record["the_shape_this_mission_leaves"]["consequence"],
        "",
        f"*What this is not:* {record['the_shape_this_mission_leaves']['what_this_is_not']}",
        "",
        "## Next",
        "",
        f"**`{nxt['checkpoint']}`.** The single blocking input is {nxt['the_single_blocking_input']}.",
        "",
        f"*How to supply it:* {nxt['how_the_operator_supplies_it']}",
        "",
        f"    {nxt['operative_approval_string']}",
        "",
        f"*And one decision beside it:* {nxt['and_one_decision_beside_it']}",
        "",
        "It should:",
        "",
    ]
    lines += [f"- {i}" for i in nxt["it_should"]]
    lines += ["", "It must not:", ""]
    lines += [f"- {i}" for i in nxt["it_must_not"]]
    lines += ["", f"Awaiting: **{record['stop_condition']['awaiting']}**.", ""]
    return "\n".join(lines)


RENDERERS = {
    BASELINE: render_baseline,
    DISPATCH: render_dispatch,
    LIFECYCLE: render_lifecycle,
    PORTS: render_ports,
    RETENTION: render_retention,
    PACKAGE: render_package,
    READINESS: render_readiness,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  enquiry dispatch: {error}")
        return 1

    rendered = {
        RENDERED[path]: RENDERERS[path](record) for path, record in zip(ORDER, records, strict=True)
    }
    rendered[PACKET_MD] = render_packet(_load(ENQUIRY_V1_JSON), records[1])

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(f"ok       {len(rendered)} dispatch documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    _, dispatch, lifecycle, ports, retention, package, readiness = records
    print(f"enquiry  {dispatch['verdict']['enquiry_state']}, sha256 verified")
    print(f"contact  {dispatch['a3_recipient']['status']}")
    print(
        f"onyphe   B2 {lifecycle['verdict']['b2_result']} "
        f"({lifecycle['verdict']['record_lifecycle']}), "
        f"port22 {ports['verdict']['membership']}, "
        f"retention {retention['verdict']['ADDRESS']}"
    )
    print(f"package  {package['individual_qualification']['verdict']}")
    print(
        f"ready    {readiness['readiness']['status_word']}, qualified "
        f"{readiness['readiness']['QUALIFIED_APPARATUS_COUNT']}"
    )
    print(f"outcome  {readiness['primary_outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
