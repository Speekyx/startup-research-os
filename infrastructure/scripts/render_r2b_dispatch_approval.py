"""Render and validate the GP-R2-B-Q1 dispatch approval.

An approval says an action MAY be performed. Nothing has been performed, and the danger
in this record is that every field an execution needs is already known from the approval
-- which is exactly what makes a fictional one easy to write.

Four things this gate holds:

    A QUOTED DIGEST IS RECOMPUTED, NOT COPIED.
    A RESTATED BODY IS COMPARED, NOT ASSUMED.
    THE THREAD IS BOUND, BECAUSE NO ADDRESS EXISTS TO BIND.
    AN APPROVAL TO ASK IS NOT AN ANSWER.

The instruction carried both a digest and the full body. Copying either would make the
approval name whatever the instruction said rather than whatever the packet is, so both
are recomputed and compared -- and this arc has already found a supplied quotation
differing from stored bytes by a trailing space.

The recipient is not bound and that is not an omission. A reply inside a thread inherits
its recipient, the sender of the message being answered is still NOT_ESTABLISHED, and
binding a sentinel would make the digest read as though an address had been pinned. The
thread is bound instead, by three digests.

`validate()` refuses: a digest or body that does not match the packet as stored; an
approval written into the packet; a recipient that is an address; a hash covering the
recipient or excluding nothing it should; an execution that records a send, an attestation
or a provider contact while pending; `BYTE_VERIFIED` on a channel that cannot reach it;
more than one outward reply; any item on the operator's not-authorised list flipped true;
a residual or the qualification moved; and any outward action at all.

    uv run python infrastructure/scripts/render_r2b_dispatch_approval.py
    uv run python infrastructure/scripts/render_r2b_dispatch_approval.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

APPROVAL = DATA / "globalping-r2b-dispatch-approval-v1.json"
PACKET = DATA / "globalping-r2b-enquiry-packet-v1.json"
V1_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
V2_APPROVAL = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v2.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"
FROZEN_REPLY = DATA / "globalping-r2-provider-reply-v1.json"

RENDERED = DATA / "globalping-r2b-dispatch-approval-v1.md"

RECIPIENT_SENTINEL = "DETERMINED_BY_THE_THREAD_NOT_SUPPLIED"

EXECUTION_STATUSES = (
    "PENDING_MANUAL_OPERATOR_ACTION",
    "SENT",
    "DISPATCH_ATTEMPTED_DELIVERY_FAILED",
    "SUPERSEDED",
    "WITHDRAWN",
)

# The operator's own exclusion list. Every one of them must stay false.
NOT_AUTHORISED = (
    "a_new_standalone_email",
    "a_different_thread",
    "a_modified_body",
    "a_second_send",
    "any_gmail_connector_action",
    "any_mailbox_read",
    "any_globalping_measurement",
    "any_other_provider_contact",
)

HARD_ZERO = (
    "EMAILS_SENT",
    "OUTWARD_REPLIES_MADE",
    "MAIL_CONNECTOR_EXECUTIONS",
    "MAILBOX_READS",
    "GITHUB_WRITES",
    "PUBLIC_POSTS",
    "PROVIDER_CONTACTS",
    "GLOBALPING_API_EXECUTIONS",
    "GLOBALPING_MEASUREMENTS_CREATED",
    "TARGET_HTTP_REQUESTS",
    "RESEARCH_API_CALLS",
    "MODEL_CALLS",
    "EMBEDDINGS",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "SCORES",
    "SOURCES_REGISTERED",
    "SOURCE_GOVERNANCE_MUTATIONS",
    "CANONICAL_MUTATIONS",
    "MIGRATIONS",
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
    """A quoted digest is recomputed, and a restated body is compared."""
    block = approval["approval"]
    if not block["approval_given"] or not str(block["approved_by"]).strip():
        raise ValidationError("this record exists to carry an approval and carries none")

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
    if block["hash_as_stated_by_the_operator"] != recomputed:
        raise ValidationError(
            "the digest the approval quotes and the digest the packet has disagree"
        )
    if not block["recomputed_hash_matches_the_stated_one"]:
        raise ValidationError("the record denies a match its own fields show")

    # The instruction restated the body in full, and a restatement is a claim.
    if block["approved_body_sha256"] != hashlib.sha256(packet["body"].encode("utf-8")).hexdigest():
        raise ValidationError(
            "the approved body digest is not the frozen body's; a restated body that was "
            "not compared is a body nobody checked"
        )
    if not block["approved_body_is_byte_identical_to_the_frozen_body"]:
        raise ValidationError("the record denies a body match its own digests show")
    for field in (
        "why_it_was_recomputed_rather_than_copied",
        "why_the_body_was_compared_and_not_assumed",
    ):
        if not str(block[field]).strip():
            raise ValidationError(f"the record does not state {field}")

    if block["packet_file_sha256"] != hashlib.sha256(PACKET.read_bytes()).hexdigest():
        raise ValidationError("the packet file changed after the approval was recorded")
    if block["packet_edited_by_this_mission"] or block["packet_content_sha256_changed"]:
        raise ValidationError("the approval records an edit to the document it approves")


def _check_the_approval_stayed_out_of_the_packet(approval: dict, packet: dict) -> None:
    block = approval["approval"]
    if not block["approval_recorded_in_this_document_rather_than_in_the_packet"]:
        raise ValidationError(
            "the record says the approval lives in the packet; it does not, and an approval "
            "written there would change the bytes the operator approved"
        )
    if not str(block["why"]).strip():
        raise ValidationError("the record does not say why the approval sits beside the packet")
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
    covered = approval["hash_covers"]
    if _digest(action, covered) != action["approval_sha256"]:
        raise ValidationError("the approved action does not answer to its recorded hash")
    for excluded in ("approval_sha256", "execution", "recorded_at", "recipient"):
        if excluded in covered:
            raise ValidationError(f"the approval hashes {excluded}")
        if excluded not in approval["hash_excludes"]:
            raise ValidationError(f"the approval does not declare {excluded} excluded")
    for required in (
        "approves",
        "approved_content_sha256",
        "mechanism",
        "thread_binding",
        "approved_subject",
    ):
        if required not in covered:
            raise ValidationError(f"{required} is not bound by the approval hash")

    if action["mechanism"] != "OPERATOR_MANUAL_REPLY_IN_EXISTING_EMAIL_THREAD":
        raise ValidationError(
            f"the mechanism is {action['mechanism']!r}; another mechanism is another action "
            "and needs its own approval"
        )
    if action["approves"] != packet["question_id"]:
        raise ValidationError("the approval names a different enquiry than the packet it cites")
    if action["packet_version"] != packet["packet_version"]:
        raise ValidationError("the approval names a different packet version")
    if action["approved_subject"] != packet["subject"]:
        raise ValidationError("the approved subject is not the packet's subject")
    if action["thread_binding"] != packet["thread_binding"]:
        raise ValidationError("the approved thread is not the packet's thread")
    if action["maximum_outward_replies"] != 1:
        raise ValidationError("one approval authorises exactly one outward reply")

    # No address is bound, for the same reason the packet binds none.
    if approval["recipient"] != RECIPIENT_SENTINEL:
        raise ValidationError(
            f"the recipient is {approval['recipient']!r}. The sender of the message being "
            "answered is NOT_ESTABLISHED, so any address here is invented"
        )
    if "@" in approval["recipient"]:
        raise ValidationError("an address was written into the recipient sentinel")
    if approval["recipient_is_bound_by_the_hash"]:
        raise ValidationError("the record claims the recipient is bound, and it is not")
    if not str(approval["why_the_recipient_is_not_bound"]).strip():
        raise ValidationError("the approval states no reason the recipient is unbound")


def _check_the_exclusions_hold(approval: dict) -> None:
    excluded = approval["explicitly_not_authorised"]
    for item in NOT_AUTHORISED:
        if item not in excluded:
            raise ValidationError(f"the approval does not record {item} as excluded")
        if excluded[item] is not False:
            raise ValidationError(
                f"{item} is recorded as authorised; the operator excluded it by name, and a "
                "later reading may not widen this approval by forgetting the list"
            )
    lifts = approval["what_this_approval_does_not_lift"]
    for field in (
        "the_mailbox_read_that_would_establish_the_earlier_sender",
        "the_attribution_of_whatever_comes_back",
    ):
        if not str(lifts[field]).strip():
            raise ValidationError(f"the approval does not say it leaves {field} where it was")


def _check_execution(approval: dict) -> None:
    execution = approval["execution"]
    if execution["status"] not in EXECUTION_STATUSES:
        raise ValidationError(f"the execution status {execution['status']!r} is undefined")
    if execution["outward_replies_made"] > approval["approved_action"]["maximum_outward_replies"]:
        raise ValidationError("more replies were made than the approval authorises")
    if execution["emails_sent_by_this_repository"] != 0:
        raise ValidationError("this repository sent mail on the operator's behalf")
    if execution["mail_connector_used"]:
        raise ValidationError("a mail connector was used, and the operator excluded that")
    if execution["mailbox_read"]:
        raise ValidationError("a mailbox was read, and the operator excluded that")

    if execution["byte_verification_is_possible_for_this_channel"]:
        raise ValidationError(
            "the record claims a manual reply can be byte-verified; the ceiling belongs to "
            "the medium and a mail client's outbox is unobservable from here"
        )
    if execution["attestation_levels_reachable_for_this_channel"] != ["OPERATOR_ATTESTED"]:
        raise ValidationError("this channel reaches OPERATOR_ATTESTED and nothing above it")
    level = execution["attestation_level"]
    if level is not None and level != "OPERATOR_ATTESTED":
        raise ValidationError(f"the attestation level {level!r} is not reachable here")

    if execution["status"] == "PENDING_MANUAL_OPERATOR_ACTION":
        for counter in ("outward_replies_made", "send_attempts", "deliveries_confirmed"):
            if execution[counter] != 0:
                raise ValidationError(f"the execution is pending and records {counter}")
        if execution["operator_attestation_recorded"] or level is not None:
            raise ValidationError("the execution is pending and records an attestation")
        if execution["provider_contacted"] or execution["provider_replied"]:
            raise ValidationError("the execution is pending and records a provider contact")

    for field in (
        "why_byte_verification_is_unreachable_here",
        "upgrade_path",
        "reachable_only_through",
    ):
        if not str(execution[field]).strip():
            raise ValidationError(f"the execution states no {field}")

    checks = approval["integrity_checks_frozen_before_any_send"]
    for flag, value in checks.items():
        if flag.startswith("$"):
            continue
        if value is not True:
            raise ValidationError(f"the integrity rule {flag} was weakened")


def _check_it_is_a_third_approval(approval: dict, packet: dict) -> None:
    link = approval["relationship_to_the_spent_approvals"]
    if not link["this_is_a_third_approval_not_a_renewal"]:
        raise ValidationError("this approval is recorded as a renewal of a spent one")
    for entry in link["prior_approvals"]:
        if entry["reused"]:
            raise ValidationError(f"{entry['record']} is recorded as reused")

    for path in (V1_APPROVAL, V2_APPROVAL):
        prior = _load(path)
        action = prior["approved_action"]
        if _digest(action, action["hash_covers"]) != action["approval_sha256"]:
            raise ValidationError(f"{path.name} no longer answers to its own hash")
        if action["approved_content_sha256"] == packet["content_sha256"]:
            raise ValidationError(f"{path.name} names this packet's digest")
        if action["approves"] == packet["question_id"]:
            raise ValidationError(f"{path.name} names this question id")
        if action["approval_sha256"] == approval["approved_action"]["approval_sha256"]:
            raise ValidationError(f"{path.name} shares a digest with this approval")


def _check_nothing_moved(approval: dict) -> None:
    scope = approval["scope"]
    if scope["approved_enquiries"] != ["GP-R2-B-Q1 v1"]:
        raise ValidationError("the approved set is not exactly this packet")
    for flag in ("r1_touched", "r2_a_touched", "qualification_recomputed"):
        if scope[flag]:
            raise ValidationError(f"{flag} is true, and this mission may not do it")
    if scope["residuals_closed_by_this_mission"] != 0:
        raise ValidationError("an approval to ask closed a residual")
    if not scope["an_approval_to_ask_is_not_an_answer"]:
        raise ValidationError("the record treats an approval to ask as an answer")

    if _load(THIRD_PARTY)["verdict"] != scope["r2_b_verdict_unchanged"]:
        raise ValidationError("R2-B moved, and approving a question resolves nothing")
    closure = _load(CLOSURE)
    if closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"] != "UNRESOLVED":
        raise ValidationError("the closure record moved R2-B")
    qualification = _load(QUALIFICATION)
    gates = {g["dimension"]: g["status"] for g in qualification["gates"]}
    if gates["C9_RIGHTS_FEASIBILITY"] != "PARTIAL":
        raise ValidationError("C9 moved")
    if qualification["verdict"] != "COUNTERPART_UNRESOLVED":
        raise ValidationError("the counterpart verdict moved")
    reply = _load(FROZEN_REPLY)
    if reply["attribution"]["sufficient_for_provider_authority"]:
        raise ValidationError(
            "the earlier reply now claims provider authority; approving a follow-up "
            "establishes nobody"
        )

    accounting = approval["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")

    action = approval["recommended_next_action"]
    if action["performed_by"] != "OPERATOR":
        raise ValidationError("the next action is not assigned to the operator")
    if not action["this_repository_may_not_perform_it"]:
        raise ValidationError("the record permits this repository to perform the reply")


def validate() -> dict:
    approval = _load(APPROVAL)
    packet = _load(PACKET)
    try:
        _check_it_names_the_packet(approval, packet)
        _check_the_approval_stayed_out_of_the_packet(approval, packet)
        _check_the_action_is_bound(approval, packet)
        _check_the_exclusions_hold(approval)
        _check_execution(approval)
        _check_it_is_a_third_approval(approval, packet)
        _check_nothing_moved(approval)
    except (KeyError, TypeError, IndexError) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return approval


def render(approval: dict) -> str:
    action = approval["approved_action"]
    execution = approval["execution"]
    block = approval["approval"]
    lines = [
        "# GP-R2-B-Q1 — approved, and not sent",
        "",
        f"Generated from `{APPROVAL.name}`. Do not edit by hand.",
        "",
        f"**Execution status: `{execution['status']}`.** An approval says an action MAY be "
        "performed. Nothing has been.",
        "",
        "## What was approved",
        "",
        "| | |",
        "|---|---|",
        f"| enquiry | `{action['approves']}` v{action['packet_version']} |",
        f"| mechanism | `{action['mechanism']}` |",
        f"| subject | {action['approved_subject']} |",
        f"| recipient | `{approval['recipient']}` |",
        f"| maximum outward replies | **{action['maximum_outward_replies']}** |",
        f"| approved content hash | `{action['approved_content_sha256'][:16]}…` |",
        f"| approval hash | `{action['approval_sha256'][:16]}…` |",
        "",
        "## The digest was recomputed and the body compared",
        "",
        block["why_it_was_recomputed_rather_than_copied"],
        "",
        block["why_the_body_was_compared_and_not_assumed"],
        "",
        f"Body byte-identical to the frozen packet: "
        f"**{block['approved_body_is_byte_identical_to_the_frozen_body']}**.",
        "",
        "## The thread is bound, not an address",
        "",
        approval["why_the_recipient_is_not_bound"],
        "",
        "| bound | value |",
        "|---|---|",
        f"| thread subject | {action['thread_binding']['thread_subject']} |",
        f"| prior enquiry digest | `{action['thread_binding']['prior_enquiry_packet_content_sha256'][:16]}…` |",
        f"| prior reply digest | `{action['thread_binding']['prior_reply_body_sha256'][:16]}…` |",
        "",
        "## What this approval does not authorise",
        "",
        "| | |",
        "|---|---|",
    ]
    for item in NOT_AUTHORISED:
        lines.append(f"| {item.replace('_', ' ')} | **no** |")
    lines += [
        "",
        "### And what it does not lift",
        "",
        f"- {approval['what_this_approval_does_not_lift']['the_mailbox_read_that_would_establish_the_earlier_sender']}",
        f"- {approval['what_this_approval_does_not_lift']['the_attribution_of_whatever_comes_back']}",
        "",
        "## Nothing has been performed",
        "",
        "| | |",
        "|---|---|",
        f"| outward replies made | {execution['outward_replies_made']} |",
        f"| send attempts | {execution['send_attempts']} |",
        f"| provider contacted | {execution['provider_contacted']} |",
        f"| provider replied | {execution['provider_replied']} |",
        f"| operator attestation | {execution['operator_attestation_recorded']} |",
        f"| attestation level | {execution['attestation_level']} |",
        f"| mail connector used | {execution['mail_connector_used']} |",
        f"| mailbox read | {execution['mailbox_read']} |",
        f"| emails sent by this repository | {execution['emails_sent_by_this_repository']} |",
        "",
        execution["why_byte_verification_is_unreachable_here"],
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
        print(f"REFUSED  R2-B dispatch approval: {error}")
        return 1

    text = render(approval)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the R2-B dispatch approval matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"approval {approval['approved_action']['approval_sha256'][:16]}…")
    print(f"status   {approval['execution']['status']}")
    print(f"replies  {approval['execution']['outward_replies_made']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
