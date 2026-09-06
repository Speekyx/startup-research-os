"""Render and validate the GP-R2-B-Q1 follow-up enquiry packet.

One question, and it is the one that was not answered. Four things this gate holds:

    A NEW QUESTION IS A NEW ACTION, AND NO SPENT APPROVAL REACHES IT.
    THE THREAD IS WHAT IS BOUND, BECAUSE NO ADDRESS IS KNOWN.
    R2-B CLOSES ON A STATEMENT ABOUT TARGETS, OR IT DOES NOT CLOSE.
    RESPONSIVENESS AND AUTHORITY ARE SEPARATE GATES.

The last enquiry asked four things and came back with an answer to the one clause that
was already settled. So this packet asks nothing about commercial use, and the gate
refuses it doing so.

No address is bound, and that is not an omission. The sender of the reply being answered
is NOT_ESTABLISHED -- Mission 1.76.1 attempted the mailbox read and the connector refused
it -- so inventing a recipient would fabricate the field the exchange hangs on. The
mechanism does not need one: a reply inside a thread inherits its recipient. What the
digest binds is the THREAD, identified by its subject, the prior packet's digest and the
prior reply's digest, which pins the conversation rather than a mailbox.

`validate()` refuses: the packet reachable by either spent approval; a digest that does
not recompute; an address written into the recipient field; the body broadened past the
one question; commercial use asked again; a discriminator that would close R2-B on
silence, on generic commercial permission, on the proxy limitation or on a presupposition;
an approval or a send recorded in the packet; more than one outward reply; provider
authority claimed for the earlier reply; and any outward action at all.

    uv run python infrastructure/scripts/render_r2b_followup_packet.py
    uv run python infrastructure/scripts/render_r2b_followup_packet.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

PACKET = DATA / "globalping-r2b-enquiry-packet-v1.json"
V1_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
V2_PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
V1_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
V2_APPROVAL = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
FROZEN_REPLY = DATA / "globalping-r2-provider-reply-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v2.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"

RENDERED = DATA / "globalping-r2b-followup-packet-v1.md"

RECIPIENT_SENTINEL = "DETERMINED_BY_THE_THREAD_NOT_SUPPLIED"

RESOLVING_ANSWERS = ("PERMITTED", "NOT_PERMITTED", "CONDITIONALLY_PERMITTED")

# Every route to R2-B that this arc has already refused, named so it cannot be
# rediscovered as a novelty.
NON_CLOSING = (
    "silence",
    "a generic commercial-use permission",
    "'publicly reachable target' appearing only in technical API documentation",
    "product behaviour",
    "the proxy limitation alone",
    "absence from the prohibited-use list",
    "implication or presupposition",
)

# Words whose presence in the body would mean the question grew past the one asked.
BROADENING_TERMS = ("GET ", "scan", "proxy through", "unlimited", "any method", "crawl")

OUTWARD_COUNTERS = (
    "emails_sent",
    "gmail_reads",
    "gmail_writes",
    "mail_connector_calls",
    "github_writes",
    "globalping_api_executions",
    "globalping_measurements_created",
    "target_http_requests",
    "research_api_calls",
    "model_calls",
    "embeddings",
    "canonical_research_mutations",
)


class ValidationError(RuntimeError):
    """The packet says something this gate refuses."""


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


def _check_it_answers_to_its_own_hash(packet: dict) -> None:
    if _digest(packet, packet["hash_covers"]) != packet["content_sha256"]:
        raise ValidationError("the packet does not answer to its own recorded hash")
    for excluded in packet["hash_excludes"]:
        if excluded in packet["hash_covers"]:
            raise ValidationError(f"the packet both covers and excludes {excluded}")
    for required in ("body", "subject", "thread_binding", "question_id"):
        if required not in packet["hash_covers"]:
            raise ValidationError(f"{required} is not bound by the packet hash")
    if "recipient" in packet["hash_covers"]:
        raise ValidationError(
            "the recipient is hashed; it is a sentinel rather than a value, and binding it "
            "would make the digest read as though an address had been pinned"
        )


def _check_it_is_a_new_question(packet: dict) -> None:
    v1, v2 = _load(V1_PACKET), _load(V2_PACKET)
    for other, name in ((v1, V1_PACKET.name), (v2, V2_PACKET.name)):
        if packet["content_sha256"] == other["content_sha256"]:
            raise ValidationError(f"the packet shares a digest with {name}")
        if packet["question_id"] == other["question_id"]:
            raise ValidationError(
                f"the packet reuses the question id of {name}; a spent approval names that "
                "id and would reach this body"
            )
        if other["send_status"] != "NOT_AUTHORIZED" or other["operator_approval_recorded"]:
            raise ValidationError(f"{name} was edited by this mission")

    # Neither spent approval may name this packet.
    for approval_path in (V1_APPROVAL, V2_APPROVAL):
        approval = _load(approval_path)
        action = approval["approved_action"]
        if action["approved_content_sha256"] == packet["content_sha256"]:
            raise ValidationError(
                f"{approval_path.name} names this packet's digest, so a spent approval would "
                "authorise a send it never approved"
            )
        if action["approves"] == packet["question_id"]:
            raise ValidationError(f"{approval_path.name} names this question id")
        if _digest(action, action["hash_covers"]) != action["approval_sha256"]:
            raise ValidationError(f"{approval_path.name} no longer answers to its own hash")

    named = {entry["record"] for entry in packet["prior_approvals_that_cannot_authorise_this"]}
    for approval_path in (V1_APPROVAL, V2_APPROVAL):
        if f"docs/data/{approval_path.name}" not in named:
            raise ValidationError(
                f"the packet does not name {approval_path.name} as unable to authorise it"
            )
    if not packet["requires_a_new_explicit_operator_approval"]:
        raise ValidationError("the packet claims it needs no new approval")


def _check_the_thread_is_what_is_bound(packet: dict) -> None:
    if packet["recipient"] != RECIPIENT_SENTINEL:
        raise ValidationError(
            f"the recipient is {packet['recipient']!r}. The sender of the reply being "
            "answered is NOT_ESTABLISHED, so any address here is invented"
        )
    if packet["recipient_is_an_address"]:
        raise ValidationError("the packet claims its recipient is an address")
    if "@" in packet["recipient"]:
        raise ValidationError("an address was written into the recipient sentinel")
    if not str(packet["why_the_recipient_is_not_an_address"]).strip():
        raise ValidationError("the packet does not say why no address is bound")

    binding = packet["thread_binding"]
    v2, reply = _load(V2_PACKET), _load(FROZEN_REPLY)
    if binding["thread_subject"] != v2["subject"] or packet["subject"] != v2["subject"]:
        raise ValidationError("the bound thread is not the thread the enquiry was sent in")
    if binding["prior_enquiry_packet_content_sha256"] != v2["content_sha256"]:
        raise ValidationError("the thread binding names a packet digest v2 does not have")
    if binding["prior_reply_body_sha256"] != reply["reply"]["body_sha256"]:
        raise ValidationError("the thread binding names a reply the frozen record does not hold")


def _check_it_asks_one_question(packet: dict) -> None:
    body = packet["body"]
    if packet["asks_about_commercial_use"]:
        raise ValidationError(
            "the packet asks about commercial use again; R2-A closed in Mission 1.74 and "
            "asking a settled question is how the last enquiry got the easy clause answered"
        )
    if "commercial use" in body.lower().split("commercial-use point")[-1]:
        raise ValidationError(
            "the body asks about commercial use beyond acknowledging the answer already given"
        )
    if body.count("?") != 1:
        raise ValidationError(
            f"the body carries {body.count('?')} questions; a compound enquiry gets the "
            "easiest clause answered, which is how R2-B stayed open"
        )
    if packet["independent_policy_questions_combined"] != 1:
        raise ValidationError("the packet combines more than one independent policy question")
    for term in BROADENING_TERMS:
        if term.lower() in body.lower():
            raise ValidationError(
                f"the body mentions {term!r}, which broadens past the one question"
            )
    for required in ("HEAD", "third-party", "do not own or operate"):
        if required not in body:
            raise ValidationError(f"the body does not name {required!r}, which is the question")
    if packet["legal_interpretation_added"] or packet["examples_added"]:
        raise ValidationError("the packet adds legal interpretation or examples")

    # The wording is the operator's; only the wrapping is this repository's.
    if not packet["body_differs_from_the_supplied_text_only_by_line_wrapping"]:
        raise ValidationError("the record denies a rewrap-only difference it claims elsewhere")
    if " ".join(body.split()) != " ".join(packet["body_as_supplied_by_the_operator"].split()):
        raise ValidationError(
            "the frozen body differs from the supplied text by more than line wrapping"
        )


def _check_the_discriminator_is_frozen_and_strict(packet: dict) -> None:
    discriminator = packet["expected_answer_discriminator"]
    closing = discriminator["closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"]
    if tuple(closing) != RESOLVING_ANSWERS:
        raise ValidationError(
            f"the resolving answers are {tuple(closing)}, not {RESOLVING_ANSWERS}"
        )
    for answer, text in closing.items():
        if not str(text).strip():
            raise ValidationError(f"the {answer} branch is undefined")
    if not discriminator["the_answer_must_address_third_party_target_scope_explicitly"]:
        raise ValidationError(
            "the discriminator does not require the answer to address target scope; that "
            "requirement is the whole reason the last reply did not close R2-B"
        )
    missing = [route for route in NON_CLOSING if route not in discriminator["does_not_close_r2_b"]]
    if missing:
        raise ValidationError(f"the discriminator omits refused routes: {missing}")
    if not str(discriminator["why_presupposition_is_listed"]).strip():
        raise ValidationError(
            "the discriminator lists presupposition without saying why; the strongest "
            "argument for closing R2-B was a presupposition, and it will be found again"
        )


def _check_nothing_was_authorised_or_sent(packet: dict) -> None:
    if packet["send_status"] != "NOT_AUTHORIZED":
        raise ValidationError("the packet records an authorization; approvals live beside packets")
    if packet["operator_approval_recorded"]:
        raise ValidationError("the packet records an operator approval")
    if packet["sent"] or packet["execution_record_created"]:
        raise ValidationError("the packet claims it was sent")
    if packet["maximum_outward_replies"] != 1:
        raise ValidationError("the packet authorises other than exactly one outward reply")

    authority = packet["authority_of_the_prior_reply"]
    if authority["sender_identity"] != "NOT_ESTABLISHED":
        raise ValidationError("the packet establishes a sender Mission 1.76.1 could not")
    if authority["claimed_by_this_mission"]:
        raise ValidationError("this mission claims provider authority for the earlier reply")
    if authority["does_it_block_preparing_this_packet"]:
        raise ValidationError(
            "the packet treats the unestablished sender as blocking its own preparation; "
            "responsiveness and authority are separate gates"
        )
    if not authority["semantic_responsiveness_and_provider_authority_are_separate_gates"]:
        raise ValidationError("the packet merges responsiveness with authority")

    actions = packet["outward_actions_performed_by_this_mission"]
    for counter in OUTWARD_COUNTERS:
        if counter not in actions:
            raise ValidationError(f"the packet does not report {counter}")
        if actions[counter] != 0:
            raise ValidationError(f"{counter} is {actions[counter]}, and it must be 0")


def _check_nothing_downstream_moved() -> None:
    if _load(THIRD_PARTY)["verdict"] != "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED":
        raise ValidationError("R2-B moved, and preparing a question resolves nothing")
    closure = _load(CLOSURE)
    if closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"] != "UNRESOLVED":
        raise ValidationError("the closure record moved R2-B")
    if closure["residuals"][1]["closed"]:
        raise ValidationError("R2 is recorded as closed")
    qualification = _load(QUALIFICATION)
    gates = {g["dimension"]: g["status"] for g in qualification["gates"]}
    if gates["C9_RIGHTS_FEASIBILITY"] != "PARTIAL":
        raise ValidationError("C9 moved")
    if qualification["verdict"] != "COUNTERPART_UNRESOLVED":
        raise ValidationError("the counterpart verdict moved")
    reply = _load(FROZEN_REPLY)
    if reply["attribution"]["sufficient_for_provider_authority"]:
        raise ValidationError("the frozen reply now claims provider authority")
    if (
        reply["reply"]["body_sha256"]
        != hashlib.sha256(reply["reply"]["body"].encode("utf-8")).hexdigest()
    ):
        raise ValidationError("the frozen reply was altered")


def validate() -> dict:
    packet = _load(PACKET)
    try:
        _check_it_answers_to_its_own_hash(packet)
        _check_it_is_a_new_question(packet)
        _check_the_thread_is_what_is_bound(packet)
        _check_it_asks_one_question(packet)
        _check_the_discriminator_is_frozen_and_strict(packet)
        _check_nothing_was_authorised_or_sent(packet)
        _check_nothing_downstream_moved()
    except (KeyError, TypeError, IndexError) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return packet


def render(packet: dict) -> str:
    discriminator = packet["expected_answer_discriminator"]
    lines = [
        "# GP-R2-B-Q1 — one question, and it is the one that was not answered",
        "",
        f"Generated from `{PACKET.name}`. Do not edit by hand.",
        "",
        f"**`send_status: {packet['send_status']}`.** {packet['what_send_status_means']}",
        "",
        "## The packet",
        "",
        "| | |",
        "|---|---|",
        f"| question | `{packet['question_id']}` v{packet['packet_version']} |",
        f"| residual | `{packet['residual_id']}` |",
        f"| subject | {packet['subject']} |",
        f"| channel | `{packet['channel']}` |",
        f"| recipient | `{packet['recipient']}` |",
        f"| maximum outward replies | **{packet['maximum_outward_replies']}** |",
        f"| content hash | `{packet['content_sha256'][:16]}…` |",
        "",
        "### The frozen body",
        "",
        f"> {packet['body'].replace(chr(10), chr(10) + '> ')}",
        "",
        "## It asks one thing",
        "",
        packet["why_a_new_packet_rather_than_a_v3_of_the_old_one"],
        "",
        f"Asks about commercial use: **{packet['asks_about_commercial_use']}**. "
        f"{packet['why_not']}",
        "",
        "Deliberately not broadened to: "
        + ", ".join(f"`{item}`" for item in packet["scope_deliberately_not_broadened_to"])
        + ".",
        "",
        "## The thread is what is bound",
        "",
        packet["why_the_recipient_is_not_an_address"],
        "",
        "| bound | value |",
        "|---|---|",
        f"| thread subject | {packet['thread_binding']['thread_subject']} |",
        f"| prior enquiry digest | `{packet['thread_binding']['prior_enquiry_packet_content_sha256'][:16]}…` |",
        f"| prior reply digest | `{packet['thread_binding']['prior_reply_body_sha256'][:16]}…` |",
        "",
        "## The discriminator, frozen before dispatch",
        "",
        "R2-B closes only on a reply that explicitly establishes one of:",
        "",
    ]
    for answer, text in discriminator[
        "closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"
    ].items():
        lines.append(f"- **`{answer}`** — {text}")
    lines += ["", "It does **not** close on:", ""]
    lines += [f"- {route}" for route in discriminator["does_not_close_r2_b"]]
    lines += [
        "",
        f"**{discriminator['why_presupposition_is_listed']}**",
        "",
        "## No approval, and no spent one reaches it",
        "",
    ]
    for entry in packet["prior_approvals_that_cannot_authorise_this"]:
        lines.append(f"- `{entry['record']}` — {entry['why']}")
    lines += [
        "",
        "## Authority stays a separate question",
        "",
        f"Sender of the earlier reply: **`{packet['authority_of_the_prior_reply']['sender_identity']}`**. "
        f"{packet['authority_of_the_prior_reply']['what_it_affects']}",
        "",
        "## Nothing was performed",
        "",
        "| | |",
        "|---|---|",
    ]
    for counter in OUTWARD_COUNTERS:
        lines.append(
            f"| {counter} | {packet['outward_actions_performed_by_this_mission'][counter]} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        packet = validate()
    except ValidationError as error:
        print(f"REFUSED  R2-B follow-up packet: {error}")
        return 1

    text = render(packet)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the R2-B follow-up packet matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"packet   {packet['question_id']} v{packet['packet_version']}")
    print(f"hash     {packet['content_sha256'][:16]}…")
    print(f"status   {packet['send_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
