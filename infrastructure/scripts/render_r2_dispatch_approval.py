"""Render and validate the GP-R2-Q1 dispatch approval.

The second of two approvals, and its rules INVERT against Mission 1.74.1's. That is
the whole reason it is a separate gate rather than the same one pointed at another
file:

    R1  public GitHub issue   every field pinned      BYTE_VERIFIED reachable
    R2  manual email          sender NOT pinned       BYTE_VERIFIED unreachable

Both differences are properties of the CHANNEL. A public repository and a GitHub
identity are determined before the act; a mail client's sender is not, and a mail
client's outbox is something no guard here can observe. So this gate REFUSES
`BYTE_VERIFIED` outright, where R1's gate requires that it be possible -- and a gate
that accepted the same evidence for both would be asserting something false about
one of them.

`validate()` refuses: an approval that no longer names the packet as stored; an
approval written into the packet it approves; a packet edited to say it was approved
or sent; a digest that does not recompute, or that hashes its own value, the
execution status, the date or the sender; a changed mechanism, recipient or subject
under an unchanged hash; a sender other than the placeholder; `BYTE_VERIFIED`
claimed for a channel that cannot produce it; a send with no operator attestation;
more sends than the one authorised; any mail sent, connector executed or mailbox
searched by this repository; and any edit to Mission 1.74's records or to the R1
approval's binding fields.

    uv run python infrastructure/scripts/render_r2_dispatch_approval.py
    uv run python infrastructure/scripts/render_r2_dispatch_approval.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
R2_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
R1_PACKET = DATA / "globalping-r1-enquiry-packet-v1.json"
R1_APPROVAL = DATA / "globalping-r1-dispatch-approval-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v1.json"

RENDERED = DATA / "mission-1.74.2-r2-dispatch-approval-v1.md"

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
    "MAIL_CONNECTOR_EXECUTIONS",
    "MAILBOX_SEARCHES",
    "PUBLIC_POSTS",
    "GITHUB_ISSUES_CREATED",
    "GH_INVOCATIONS",
    "PROVIDER_CONTACTS",
    "ENQUIRIES_SENT",
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
    if block["packet_file_sha256"] != hashlib.sha256(R2_PACKET.read_bytes()).hexdigest():
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

    for field in ("mechanism", "recipient", "approved_subject"):
        if not str(action[field]).strip():
            raise ValidationError(f"the approved action has no {field}")
        if field not in action["hash_covers"]:
            raise ValidationError(f"{field} is not bound by the approval hash")

    if action["mechanism"] != "OPERATOR_MANUAL_EMAIL":
        raise ValidationError(
            f"the mechanism is {action['mechanism']!r}; this gate governs the manual mail "
            "channel, and another mechanism is another action needing its own approval"
        )
    if action["approved_subject"] != packet["subject"]:
        raise ValidationError("the approved subject is not the packet's subject")
    if action["recipient"] != packet["recipient"]:
        raise ValidationError("the approved recipient is not the packet's recipient")
    if action["approves"] != packet["question_id"]:
        raise ValidationError("the approval names a different enquiry than the packet it cites")
    if action["channel"] != packet["channel"]:
        raise ValidationError("the approved channel is not the packet's channel")
    if not action["channel_matches_the_packet"]:
        raise ValidationError("the approved mechanism does not match the packet's channel")
    if action["maximum_sends"] != 1:
        raise ValidationError("one approval authorises exactly one send")

    # Mission 1.65. The sender is a placeholder, it is NOT bound, and the record says so.
    if action["sender"] != PLACEHOLDER_SENDER:
        raise ValidationError(
            "the sender is not the placeholder; a real mailbox pinned here would be a "
            "different approval that supersedes this one"
        )
    if action["sender_is_bound_by_the_hash"]:
        raise ValidationError("the record claims the sender is bound, and it is not")
    if action["every_binding_field_is_pinned"]:
        raise ValidationError(
            "the record claims every field is pinned; three of four are, and the cost of "
            "the fourth is what Mission 1.65 stated in advance"
        )
    for field in ("why_the_sender_is_not_pinned", "why_that_differs_from_mission_1_74_1"):
        if not str(action[field]).strip():
            raise ValidationError(f"the approval states no {field}")


def _check_execution(approval: dict) -> None:
    execution = approval["execution"]
    if execution["status"] not in EXECUTION_STATUSES:
        raise ValidationError(f"the execution status {execution['status']!r} is undefined")

    sends = execution["sends_made"]
    if sends > approval["approved_action"]["maximum_sends"]:
        raise ValidationError(
            f"{sends} sends were made and the approval authorises "
            f"{approval['approved_action']['maximum_sends']}"
        )

    if execution["emails_sent_by_this_repository"] != 0:
        raise ValidationError("this repository sent mail on the operator's behalf")
    if execution["mail_connector_used"]:
        raise ValidationError(
            "a mail connector was used; a connector present in the runtime is not channel "
            "authorisation, and an automated send is a different action"
        )
    if execution["mailbox_searched"]:
        raise ValidationError("a mailbox was searched, and nobody asked for that access")

    # The inversion against Mission 1.74.1, and the reason this is a separate gate.
    if execution["byte_verification_is_possible_for_this_channel"]:
        raise ValidationError(
            "the record claims a manual mail send can be byte-verified; Mission 1.66 "
            "established it cannot, because the send happens where no guard can observe it"
        )
    if execution["attestation_levels_reachable_for_this_channel"] != ["OPERATOR_ATTESTED"]:
        raise ValidationError("this channel reaches OPERATOR_ATTESTED and nothing above it")

    level = execution["attestation_level"]
    if level is not None and level != "OPERATOR_ATTESTED":
        raise ValidationError(f"the attestation level {level!r} is not reachable for this channel")

    if execution["status"] == "PENDING_MANUAL_OPERATOR_ACTION":
        if sends != 0:
            raise ValidationError("the execution is pending and records a send")
        if execution["operator_attestation_recorded"] or level is not None:
            raise ValidationError("the execution is pending and records an attestation")

    # Mission 1.74.4. An attempt that bounced is not a send and is not a contact.
    if execution["status"] == "DISPATCH_ATTEMPTED_DELIVERY_FAILED":
        if execution.get("send_attempts", 0) < 1:
            raise ValidationError("a failed dispatch records no attempt")
        if sends != 0 or execution.get("deliveries_confirmed", 0) != 0:
            raise ValidationError(
                "a failed dispatch records a delivery; nothing arrived, so nothing was sent"
            )
        if execution.get("provider_contacted"):
            raise ValidationError(
                "a bounced message is recorded as having contacted the provider; nobody "
                "received it, and a contact that never arrived is not a contact"
            )
        if execution["attestation_level"] is not None:
            raise ValidationError(
                "a failed dispatch carries an attestation level; the levels grade evidence "
                "that a message WAS delivered, and none was"
            )
        if not execution.get("attestation_is_of_a_failure_not_of_a_send"):
            raise ValidationError(
                "the record does not distinguish an attestation of a failure from one of a send"
            )
        if not execution.get("approval_exhausted"):
            raise ValidationError(
                "a one-send approval survived its attempt; the attempt consumed it"
            )
        if execution.get("retry_to_the_same_recipient_authorised"):
            raise ValidationError("a retry is treated as authorised by the spent approval")
        if not execution.get("replacement_requires_a_new_operator_approval"):
            raise ValidationError(
                "a replacement is treated as covered by the approval that was exhausted"
            )
        if execution.get("bounce_artifact_imported"):
            raise ValidationError(
                "a non-delivery report was imported from the operator's mailbox; that "
                "replaces an attestation with an inference"
            )
        for field in (
            "why_provider_contacted_is_false",
            "why_no_attestation_level",
            "why_the_approval_is_exhausted",
        ):
            if not str(execution.get(field) or "").strip():
                raise ValidationError(f"the failed dispatch states no {field}")

    if execution["status"] == "SENT":
        if not execution["operator_attestation_recorded"]:
            raise ValidationError(
                "SENT with no operator attestation; this repository cannot observe the send"
            )
        if sends < 1:
            raise ValidationError("SENT with no send recorded")
        if level != "OPERATOR_ATTESTED":
            raise ValidationError("SENT without the one attestation level this channel has")

    for field in (
        "why_byte_verification_is_unreachable_here",
        "upgrade_path",
        "reachable_only_through",
        "mail_connector_note",
    ):
        if not str(execution[field]).strip():
            raise ValidationError(f"the execution states no {field}")


def _check_integrity_rules(approval: dict) -> None:
    checks = approval["integrity_checks_frozen_before_any_send"]
    for flag, value in checks.items():
        if flag.startswith("$"):
            continue
        if value is not True:
            raise ValidationError(f"the integrity rule {flag} was weakened")


def _check_scope(approval: dict) -> None:
    scope = approval["scope"]
    if scope["approved_enquiries"] != ["GP-R2-Q1"]:
        raise ValidationError("the approved set is not exactly GP-R2-Q1")
    if scope["r1_approval_edited"]:
        raise ValidationError("the R1 approval's own fields were edited")

    # The R1 approval keeps its binding fields, and its digest still recomputes. A
    # forward pointer appended beside them does not move it, which is the point.
    r1 = _load(R1_APPROVAL)
    r1_action = r1["approved_action"]
    if _digest(r1_action, r1_action["hash_covers"]) != r1_action["approval_sha256"]:
        raise ValidationError("the R1 approval no longer answers to its own hash")
    # DEFECT CORRECTED IN MISSION 1.74.3. These two checks compared the R1 execution
    # state LIVE against a snapshot this record took when it was written, so they refused
    # the very transition the R1 approval was designed to make: the first legitimate
    # operator attestation turned this gate red. What this gate is entitled to assert is
    # that MISSION 1.74.2 did not move it -- history, recorded in the snapshot below --
    # plus that the R1 approval's BINDING fields are untouched, which is checked above and
    # is the property that actually matters. The snapshot is no longer compared to the
    # living record.
    if scope["r1_execution_state_when_this_was_written"] != "PENDING_MANUAL_OPERATOR_ACTION":
        raise ValidationError(
            "the recorded snapshot of the R1 execution state was rewritten; it is what "
            "Mission 1.74.2 observed, and a later transition does not change it"
        )
    if r1["execution"]["public_posts_made"] > r1["approved_action"]["maximum_public_posts"]:
        raise ValidationError("the R1 execution records more posts than R1 authorised")

    if not scope["both_enquiries_now_approved_separately"]:
        raise ValidationError("the record does not say both are approved separately")
    if not str(scope["and_that_is_not_one_approval_covering_both"]).strip():
        raise ValidationError("the record does not say why two approvals are not one")

    if scope["residuals_closed_by_this_mission"] != 0:
        raise ValidationError("an approval to ask closed a residual")
    if not scope["an_approval_to_ask_is_not_an_answer"]:
        raise ValidationError("the record treats an approval to ask as an answer")
    if scope["qualification_recomputed"]:
        raise ValidationError("the qualification was recomputed by an approval mission")

    closure = _load(CLOSURE)
    if closure["enquiries"]["enquiries_sent"] != 0:
        raise ValidationError("Mission 1.74's closure record now reports a send")
    if closure["residuals_remaining"] != 2:
        raise ValidationError("Mission 1.74's residual count was edited")
    r1_packet = _load(R1_PACKET)
    if r1_packet["send_status"] != "NOT_AUTHORIZED" or r1_packet["sent"]:
        raise ValidationError("the R1 packet was edited by this mission")


def _check_accounting(approval: dict) -> None:
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
    for flag in (
        "onyphe_mailbox_searched",
        "netlas_enquiry_sent",
        "scanner_arc_reopened",
        "adr_039_weakened",
        "mission_1_74_records_edited",
        "mission_1_74_1_approval_fields_edited",
    ):
        if parallel[flag] is not False:
            raise ValidationError(f"{flag} is true, and this mission may not do it")

    action = approval["recommended_next_action"]
    if action["performed_by"] != "OPERATOR":
        raise ValidationError("the next action is not assigned to the operator")
    if not action["this_repository_may_not_perform_it"]:
        raise ValidationError("the record permits this repository to perform the send")
    if not action["attestation_is_the_only_evidence_this_channel_can_produce"]:
        raise ValidationError("the record implies evidence this channel cannot produce")


def validate() -> dict:
    approval = _load(APPROVAL)
    packet = _load(R2_PACKET)

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
        _check_scope(approval)
        _check_accounting(approval)
    except (KeyError, TypeError) as error:
        raise ValidationError(f"the record does not carry {error!r}") from error
    return approval


def render(approval: dict) -> str:
    packet = _load(R2_PACKET)
    action = approval["approved_action"]
    execution = approval["execution"]

    lines = [
        "# Mission 1.74.2 — The second enquiry approved, and the ceiling that comes with it",
        "",
        "Generated from `globalping-r2-dispatch-approval-v1.json`. Do not edit by hand.",
        "",
        f"**Execution status: `{execution['status']}`**",
        "",
        "## What was approved",
        "",
        "| | |",
        "|---|---|",
        f"| enquiry | `{action['approves']}` |",
        f"| mechanism | `{action['mechanism']}` |",
        f"| channel | `{action['channel']}` |",
        f"| recipient | `{action['recipient']}` |",
        f"| subject | {action['approved_subject']} |",
        f"| sender | `{action['sender']}` |",
        f"| maximum sends | **{action['maximum_sends']}** |",
        f"| approved content hash | `{action['approved_content_sha256'][:16]}…` |",
        f"| approval hash | `{action['approval_sha256'][:16]}…` |",
        "",
        "The approval hash binds "
        + ", ".join(f"`{f}`" for f in action["hash_covers"])
        + ", and excludes "
        + ", ".join(f"`{f}`" for f in action["hash_excludes"])
        + ".",
        "",
        "## Three fields of four, and the cost was stated in advance",
        "",
        action["why_the_sender_is_not_pinned"],
        "",
        action["why_that_differs_from_mission_1_74_1"],
        "",
        "## The ceiling inverts against Mission 1.74.1",
        "",
        f"- byte verification possible: "
        f"**{execution['byte_verification_is_possible_for_this_channel']}**",
        f"- levels reachable: "
        f"{', '.join(f'`{lvl}`' for lvl in execution['attestation_levels_reachable_for_this_channel'])}",
        "",
        execution["why_byte_verification_is_unreachable_here"],
        "",
        f"**Upgrade path.** {execution['upgrade_path']}",
        "",
        "## An approval is not an execution",
        "",
        "| | |",
        "|---|---|",
        f"| sends made | {execution['sends_made']} |",
        f"| emails sent by this repository | {execution['emails_sent_by_this_repository']} |",
        f"| mail connector used | {execution['mail_connector_used']} |",
        f"| mailbox searched | {execution['mailbox_searched']} |",
        f"| operator attestation recorded | {execution['operator_attestation_recorded']} |",
        f"| attestation level | {execution['attestation_level']} |",
        "",
        execution["mail_connector_note"],
        "",
        "## Two approvals, and they are not one",
        "",
        f"- R1 is approved separately in `{approval['scope']['r1_approval_record']}`, "
        f"edited by this mission: **{approval['scope']['r1_approval_edited']}**.",
        f"- {approval['scope']['and_that_is_not_one_approval_covering_both']}",
        f"- Residuals closed by this mission: "
        f"**{approval['scope']['residuals_closed_by_this_mission']}**. "
        "An approval to ask is not an answer.",
        "",
        f"The packet still reads `send_status: {packet['send_status']}`, unchanged.",
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    for counter in (
        "EMAILS_SENT",
        "MAIL_CONNECTOR_EXECUTIONS",
        "MAILBOX_SEARCHES",
        "PROVIDER_CONTACTS",
        "ENQUIRIES_SENT",
        "PUBLIC_POSTS",
        "GLOBALPING_API_EXECUTIONS",
        "CANONICAL_MUTATIONS",
        "MODEL_CALLS",
    ):
        lines.append(f"| {counter} | {approval['mission_accounting'][counter]} |")
    lines += [
        "",
        f"**Next: {approval['recommended_next_action']['action']}.** "
        f"Performed by {approval['recommended_next_action']['performed_by']}; "
        "this repository may not perform it.",
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
        print(f"REFUSED  R2 dispatch approval: {error}")
        return 1

    text = render(approval)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the R2 dispatch approval matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"approval {approval['approved_action']['approval_sha256'][:16]}…")
    print(f"status   {approval['execution']['status']}")
    print(f"sends    {approval['execution']['sends_made']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
