"""Render and validate the GP-R2-Q1 v2 dispatch approval.

The second approval for the second question, after the first was exhausted by an
attempt that bounced. Three things this gate exists to hold:

    A QUOTED DIGEST IS RECOMPUTED, NOT COPIED.
    A SECOND APPROVAL IS NOT A RENEWAL OF A SPENT ONE.
    THE CEILING BELONGS TO THE MEDIUM, NOT TO THE ADDRESS.

The approval arrived carrying a content hash. Copying it would make the approval
name whatever the instruction said rather than whatever the packet is, so the record
stores both the stated and the recomputed digest and this gate refuses them
disagreeing -- which turns a quoted string into a check.

The recipient changed, so this authorises a different action rather than extending
the exhausted one. The earlier approval stays exhausted, its attempt stays a
failure, and its `provider_contacted` stays false; this gate asserts all three, so a
later edit that quietly rehabilitated the bounce would fail here.

And the address changed while the medium did not, so Mission 1.66's ceiling is
unmoved: `BYTE_VERIFIED` stays unreachable, because a mail client's outbox is
something no guard here can observe.

    uv run python infrastructure/scripts/render_r2_v2_dispatch_approval.py
    uv run python infrastructure/scripts/render_r2_v2_dispatch_approval.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

APPROVAL = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
V2_PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
V1_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"

RENDERED = DATA / "mission-1.74.5-r2-v2-dispatch-approval-v1.md"

EXECUTION_STATUSES = (
    "PENDING_MANUAL_OPERATOR_ACTION",
    "SENT",
    "DISPATCH_ATTEMPTED_DELIVERY_FAILED",
    "SUPERSEDED",
    "WITHDRAWN",
)
PLACEHOLDER_SENDER = "PLACEHOLDER_PERMITTED_FOR_MANUAL_SEND_ONLY"

HARD_ZERO = (
    "EMAILS_SENT",
    "EMAILS_DELIVERED",
    "MAIL_CONNECTOR_EXECUTIONS",
    "MAILBOX_SEARCHES",
    "PUBLIC_POSTS",
    "GITHUB_ISSUES_CREATED",
    "PROVIDER_CONTACTS",
    "ENQUIRIES_DELIVERED",
    "GLOBALPING_API_EXECUTIONS",
    "GLOBALPING_MEASUREMENTS_CREATED",
    "TARGET_HTTP_REQUESTS",
    "SROS_FETCHER_RUNS",
    "ACCOUNTS_CREATED",
    "TOKENS_CREATED",
    "CREDENTIAL_READS",
    "FIRST_PARTY_DOCUMENT_REQUESTS",
    "SOURCES_REGISTERED",
    "SOURCE_GOVERNANCE_MUTATIONS",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "RELIABILITY_VALUES_ASSIGNED",
    "SCORES",
    "OPPORTUNITY_MUTATIONS",
    "MODEL_CALLS",
    "EMBEDDINGS",
    "MIGRATIONS",
    "CONSTRUCTS_SELECTED",
    "QUANTITY_CLASSES_SELECTED",
    "CANONICAL_MUTATIONS",
)


class ValidationError(RuntimeError):
    """The approval record says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _digest(mapping: dict, keys) -> str:
    binding = {key: mapping[key] for key in keys}
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _check_it_names_the_packet(approval: dict, packet: dict) -> None:
    """A quoted digest is recomputed, not copied."""
    block = approval["approval"]
    recomputed = _digest(packet, packet["hash_covers"])
    if recomputed != packet["content_sha256"]:
        raise ValidationError("the packet no longer answers to its own recorded hash")
    if approval["approved_action"]["approved_content_sha256"] != recomputed:
        raise ValidationError(
            "the approval names a hash the packet does not have, so it approves a document "
            "that is not this one"
        )
    if not block["hash_recomputed_from_the_packet_as_stored"]:
        raise ValidationError("the approval asserts a hash rather than recomputing it")

    stated = block["hash_as_stated_by_the_operator"]
    if stated != recomputed:
        raise ValidationError(
            "the digest the approval quotes and the digest the packet has disagree; the "
            "approval names a document that is not this one"
        )
    if not block["recomputed_hash_matches_the_stated_one"]:
        raise ValidationError("the record denies a match its own fields show")
    if not str(block["why_it_was_recomputed_rather_than_copied"]).strip():
        raise ValidationError("the record does not say why the digest was recomputed")

    if block["packet_file_sha256"] != hashlib.sha256(V2_PACKET.read_bytes()).hexdigest():
        raise ValidationError("the packet file changed after the approval was recorded")
    if block["packet_edited_by_this_mission"] or block["packet_content_sha256_changed"]:
        raise ValidationError("the approval records an edit to the document it approves")
    if block["approved_body_sha256"] != hashlib.sha256(packet["body"].encode("utf-8")).hexdigest():
        raise ValidationError("the approved body digest does not match the packet body")


def _check_the_approval_stayed_out_of_the_packet(packet: dict) -> None:
    if packet["operator_approval_recorded"]:
        raise ValidationError(
            "the packet now records an approval; the approval belongs beside it, not inside it"
        )
    if packet["sent"] or packet["execution_record_created"]:
        raise ValidationError("the packet was edited to claim it was sent")
    if packet["send_status"] != "NOT_AUTHORIZED":
        raise ValidationError(
            "the packet's own send status was edited; it means THIS DOCUMENT RECORDS NO "
            "AUTHORIZATION and is not where an approval is recorded"
        )


def _check_the_action_is_bound(approval: dict, packet: dict) -> None:
    action = approval["approved_action"]
    if _digest(action, action["hash_covers"]) != action["approval_sha256"]:
        raise ValidationError("the approved action does not answer to its recorded hash")

    for excluded in ("approval_sha256", "execution", "recorded_at", "sender"):
        if excluded in action["hash_covers"]:
            raise ValidationError(f"the approval hashes {excluded}")
        if excluded not in action["hash_excludes"]:
            raise ValidationError(f"the approval does not declare {excluded} excluded")

    for field in ("mechanism", "recipient", "channel", "approved_subject"):
        if not str(action[field]).strip():
            raise ValidationError(f"the approved action has no {field}")
        if field not in action["hash_covers"]:
            raise ValidationError(f"{field} is not bound by the approval hash")

    if action["mechanism"] != "OPERATOR_MANUAL_EMAIL":
        raise ValidationError(
            f"the mechanism is {action['mechanism']!r}; this gate governs the manual mail "
            "channel, and another mechanism is another action needing its own approval"
        )
    if action["approves"] != packet["question_id"]:
        raise ValidationError("the approval names a different enquiry than the packet it cites")
    if action["packet_version"] != packet["packet_version"]:
        raise ValidationError(
            "the approval names a different packet version; the two packets share a question "
            "id, and the version is part of what tells them apart"
        )
    if action["recipient"] != packet["recipient"]:
        raise ValidationError("the approved recipient is not the packet's recipient")
    if action["channel"] != packet["channel"]:
        raise ValidationError("the approved channel is not the packet's channel")
    if action["approved_subject"] != packet["subject"]:
        raise ValidationError("the approved subject is not the packet's subject")
    if not action["channel_matches_the_packet"]:
        raise ValidationError("the approved mechanism does not match the packet's channel")
    if action["maximum_sends"] != 1:
        raise ValidationError("one approval authorises exactly one send")

    if action["sender"] != PLACEHOLDER_SENDER:
        raise ValidationError(
            "the sender is not the placeholder; a real mailbox pinned here would be a "
            "different approval that supersedes this one"
        )
    if action["sender_is_bound_by_the_hash"]:
        raise ValidationError("the record claims the sender is bound, and it is not")
    if action["every_binding_field_is_pinned"]:
        raise ValidationError("the record claims every field is pinned, and the sender is not")
    if not action["sender_left_open_at_the_operators_explicit_instruction"]:
        raise ValidationError(
            "the sender is unpinned and the record does not attribute that to the operator"
        )
    if not str(action["why_the_sender_is_not_pinned"]).strip():
        raise ValidationError("the approval states no reason the sender is unpinned")


def _check_execution(approval: dict) -> None:
    execution = approval["execution"]
    if execution["status"] not in EXECUTION_STATUSES:
        raise ValidationError(f"the execution status {execution['status']!r} is undefined")

    sends = execution["sends_made"]
    if sends > approval["approved_action"]["maximum_sends"]:
        raise ValidationError("more sends were made than the approval authorises")
    if execution["emails_sent_by_this_repository"] != 0:
        raise ValidationError("this repository sent mail on the operator's behalf")
    if execution["mail_connector_used"]:
        raise ValidationError("a mail connector was used; that is a different action")
    if execution["mailbox_searched"]:
        raise ValidationError("a mailbox was searched, and nobody asked for that access")

    # The address changed and the medium did not, so the ceiling did not move.
    if execution["byte_verification_is_possible_for_this_channel"]:
        raise ValidationError(
            "the record claims a manual mail send can be byte-verified; the ceiling belongs "
            "to the medium rather than to the address, and the medium is unchanged"
        )
    if execution["attestation_levels_reachable_for_this_channel"] != ["OPERATOR_ATTESTED"]:
        raise ValidationError("this channel reaches OPERATOR_ATTESTED and nothing above it")
    level = execution["attestation_level"]
    if level is not None and level != "OPERATOR_ATTESTED":
        raise ValidationError(f"the attestation level {level!r} is not reachable here")

    if execution["status"] == "PENDING_MANUAL_OPERATOR_ACTION":
        if execution["send_attempts"] != 0 or sends != 0:
            raise ValidationError("the execution is pending and records an attempt")
        if execution["deliveries_confirmed"] != 0:
            raise ValidationError("the execution is pending and records a delivery")
        if execution["operator_attestation_recorded"] or level is not None:
            raise ValidationError("the execution is pending and records an attestation")
        if execution["provider_contacted"]:
            raise ValidationError("the execution is pending and records a provider contact")

    if execution["status"] == "SENT":
        if not execution["operator_attestation_recorded"]:
            raise ValidationError(
                "SENT with no operator attestation; this repository cannot observe the send"
            )
        if sends < 1:
            raise ValidationError("SENT with no send recorded")
        if level != "OPERATOR_ATTESTED":
            raise ValidationError("SENT without the one attestation level this channel has")

    if execution["status"] == "DISPATCH_ATTEMPTED_DELIVERY_FAILED":
        if execution["send_attempts"] < 1:
            raise ValidationError("a failed dispatch records no attempt")
        if sends != 0 or execution["deliveries_confirmed"] != 0:
            raise ValidationError("a failed dispatch records a delivery")
        if execution["provider_contacted"]:
            raise ValidationError("a bounced message is recorded as a provider contact")
        if level is not None:
            raise ValidationError("a failed dispatch carries an attestation level")

    for field in (
        "why_byte_verification_is_unreachable_here",
        "upgrade_path",
        "reachable_only_through",
    ):
        if not str(execution[field]).strip():
            raise ValidationError(f"the execution states no {field}")


def _check_the_relationship_to_the_spent_approval(approval: dict, packet: dict) -> None:
    """A second approval is not a renewal, and the first one's record stands."""
    link = approval["relationship_to_the_exhausted_approval"]
    if link["prior_approval_reused"]:
        raise ValidationError("the exhausted approval is recorded as reused")
    if link["prior_approval_edited_by_this_mission"]:
        raise ValidationError("the exhausted approval's own fields were edited")
    if link["prior_attempt_reinterpreted_as_delivered"]:
        raise ValidationError("the bounced attempt was reinterpreted as delivered")
    if not link["this_is_a_second_approval_not_a_renewal"]:
        raise ValidationError("this approval is recorded as a renewal of a spent one")

    prior = _load(V1_APPROVAL)
    execution = prior["execution"]
    if execution["status"] != link["prior_execution_state_expected"]:
        raise ValidationError(
            "the earlier approval's execution state moved; it recorded a failed attempt and "
            "a later mission may not rehabilitate it"
        )
    if execution["status"] != "DISPATCH_ATTEMPTED_DELIVERY_FAILED":
        raise ValidationError("the earlier attempt is no longer recorded as a failure")
    if execution["provider_contacted"] is not link["prior_provider_contacted_expected"]:
        raise ValidationError("the earlier bounce is now recorded as a provider contact")
    if execution["provider_contacted"]:
        raise ValidationError("a bounced message contacted nobody")
    if not execution.get("approval_exhausted"):
        raise ValidationError("the earlier approval is no longer recorded as exhausted")

    prior_action = prior["approved_action"]
    if _digest(prior_action, prior_action["hash_covers"]) != prior_action["approval_sha256"]:
        raise ValidationError("the earlier approval no longer answers to its own hash")
    if prior_action["approved_content_sha256"] == packet["content_sha256"]:
        raise ValidationError(
            "the exhausted approval names this packet's digest, so it would authorise a "
            "send it never approved"
        )
    if prior_action["recipient"] == packet["recipient"]:
        raise ValidationError("the exhausted approval already names this recipient")
    if approval["approved_action"]["approval_sha256"] == prior_action["approval_sha256"]:
        raise ValidationError("the two approvals share a digest, so they are one approval")


def _check_scope_and_accounting(approval: dict) -> None:
    scope = approval["scope"]
    if scope["approved_enquiries"] != ["GP-R2-Q1 v2"]:
        raise ValidationError("the approved set is not exactly the v2 packet")
    if scope["r1_touched"]:
        raise ValidationError("R1 was touched by an R2 approval")
    if scope["residuals_closed_by_this_mission"] != 0:
        raise ValidationError("an approval to ask closed a residual")
    if not scope["an_approval_to_ask_is_not_an_answer"]:
        raise ValidationError("the record treats an approval to ask as an answer")
    if scope["qualification_recomputed"]:
        raise ValidationError("the qualification was recomputed by an approval mission")

    accounting = approval["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")

    parallel = approval["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    if parallel["netlas_contact_state"] != "STILL_PENDING":
        raise ValidationError("the Netlas contact state moved")
    for flag in ("scanner_arc_reopened", "adr_039_weakened", "mission_1_74_records_edited"):
        if parallel[flag] is not False:
            raise ValidationError(f"{flag} is true, and this mission may not do it")

    action = approval["recommended_next_action"]
    if action["performed_by"] != "OPERATOR":
        raise ValidationError("the next action is not assigned to the operator")
    if not action["this_repository_may_not_perform_it"]:
        raise ValidationError("the record permits this repository to perform the send")
    if not action["attestation_is_the_only_evidence_this_channel_can_produce"]:
        raise ValidationError("the record implies evidence this channel cannot produce")


def _check_integrity_rules(approval: dict) -> None:
    checks = approval["integrity_checks_frozen_before_any_send"]
    for flag, value in checks.items():
        if flag.startswith("$"):
            continue
        if value is not True:
            raise ValidationError(f"the integrity rule {flag} was weakened")


def validate() -> dict:
    approval = _load(APPROVAL)
    packet = _load(V2_PACKET)

    if not approval["approval"]["approval_given"]:
        raise ValidationError("this record exists to carry an approval and carries none")
    if not str(approval["approval"]["approved_by"]).strip():
        raise ValidationError("the approval names no approver")

    try:
        _check_it_names_the_packet(approval, packet)
        _check_the_approval_stayed_out_of_the_packet(packet)
        _check_the_action_is_bound(approval, packet)
        _check_execution(approval)
        _check_integrity_rules(approval)
        _check_the_relationship_to_the_spent_approval(approval, packet)
        _check_scope_and_accounting(approval)
    except (KeyError, TypeError) as error:
        raise ValidationError(f"the record does not carry {error!r}") from error
    return approval


def render(approval: dict) -> str:
    packet = _load(V2_PACKET)
    prior = _load(V1_APPROVAL)
    action = approval["approved_action"]
    execution = approval["execution"]
    link = approval["relationship_to_the_exhausted_approval"]

    lines = [
        "# Mission 1.74.5 — The second approval, and the first one stays spent",
        "",
        "Generated from `globalping-r2-v2-dispatch-approval-v1.json`. Do not edit by hand.",
        "",
        f"**Execution status: `{execution['status']}`**",
        "",
        "## What was approved",
        "",
        "| | |",
        "|---|---|",
        f"| enquiry | `{action['approves']}` v{action['packet_version']} |",
        f"| mechanism | `{action['mechanism']}` |",
        f"| recipient | `{action['recipient']}` |",
        f"| channel | `{action['channel']}` |",
        f"| subject | {action['approved_subject']} |",
        f"| sender | `{action['sender']}` |",
        f"| maximum sends | **{action['maximum_sends']}** |",
        f"| approved content hash | `{action['approved_content_sha256'][:16]}…` |",
        f"| approval hash | `{action['approval_sha256'][:16]}…` |",
        "",
        "## The quoted digest was recomputed, not copied",
        "",
        approval["approval"]["why_it_was_recomputed_rather_than_copied"],
        "",
        f"Stated `{approval['approval']['hash_as_stated_by_the_operator'][:16]}…`, "
        f"recomputed `{action['approved_content_sha256'][:16]}…`, and the gate refuses them "
        "disagreeing.",
        "",
        "## The sender stays open, at the operator's instruction",
        "",
        action["why_the_sender_is_not_pinned"],
        "",
        "## A second approval, not a renewal",
        "",
        "| | first | second |",
        "|---|---|---|",
        f"| recipient | `{prior['approved_action']['recipient']}` | `{action['recipient']}` |",
        f"| execution | `{prior['execution']['status']}` | `{execution['status']}` |",
        f"| provider contacted | {prior['execution']['provider_contacted']} "
        f"| {execution['provider_contacted']} |",
        f"| approval hash | `{prior['approved_action']['approval_sha256'][:16]}…` "
        f"| `{action['approval_sha256'][:16]}…` |",
        "",
        link["why"],
        "",
        f"The earlier approval was reused: **{link['prior_approval_reused']}**. Its attempt "
        f"reinterpreted as delivered: **{link['prior_attempt_reinterpreted_as_delivered']}**.",
        "",
        "## The ceiling belongs to the medium",
        "",
        execution["why_byte_verification_is_unreachable_here"],
        "",
        f"Reachable: "
        f"{', '.join(f'`{lvl}`' for lvl in execution['attestation_levels_reachable_for_this_channel'])}. "
        f"Upgrade path: {execution['upgrade_path']}",
        "",
        "## Nothing has been performed",
        "",
        "| | |",
        "|---|---|",
        f"| send attempts | {execution['send_attempts']} |",
        f"| sends made | {execution['sends_made']} |",
        f"| deliveries confirmed | {execution['deliveries_confirmed']} |",
        f"| provider contacted | {execution['provider_contacted']} |",
        f"| emails sent by this repository | {execution['emails_sent_by_this_repository']} |",
        f"| mail connector used | {execution['mail_connector_used']} |",
        f"| mailbox searched | {execution['mailbox_searched']} |",
        f"| operator attestation | {execution['operator_attestation_recorded']} |",
        f"| attestation level | {execution['attestation_level']} |",
        "",
        f"The packet still reads `send_status: {packet['send_status']}`, unchanged, and "
        "records no approval of its own.",
        "",
        f"**Next: {approval['recommended_next_action']['action']}.** Performed by "
        f"{approval['recommended_next_action']['performed_by']}; this repository may not "
        "perform it.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        approval = validate()
    except ValidationError as error:
        print(f"REFUSED  R2 v2 dispatch approval: {error}")
        return 1

    text = render(approval)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the R2 v2 dispatch approval matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"approval {approval['approved_action']['approval_sha256'][:16]}…")
    print(f"status   {approval['execution']['status']}")
    print(f"sends    {approval['execution']['sends_made']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
