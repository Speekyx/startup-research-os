"""Render and validate the GP-R2-Q1 v2 provider reply.

A reply arrived and R2 did not close. Two things this gate exists to hold, and either
alone would keep it open:

    A REPLY WITH NO ESTABLISHED SENDER IS NOT A PROVIDER STATEMENT.
    AN ANSWER TO THE CLOSED HALF DOES NOT CLOSE THE OPEN ONE.

The first is a provenance ceiling. R1's reply was a public GitHub comment whose author
could be established from the provider's own API; a private email has no public surface,
so its sender lives only in a mailbox. This mission attempted that read, under an explicit
operator authorisation, and the connector refused it for missing permissions. So the
sender, the address and the date are `null` -- and this gate refuses them being anything
else while the retrieval method says nothing was retrieved.

The second is sharper, because no permission grant would fix it. The enquiry asked four
things and the reply answers one: commercial use, which Mission 1.74 had ALREADY closed on
the provider's own FAQ. The discriminator frozen before the send required an answer
*stating* that the Terms do or do not cover third-party publicly reachable targets. The
reply contains no such statement. A prohibition on proxying arguably presupposes one --
and Mission 1.74 graded exactly that shape non-closing, because a presupposition is not a
statement.

`validate()` refuses: a sender or timestamp recorded while nothing was read; attribution
claimed without it; the reply promoted past OPERATOR_SUPPLIED; commercial use read as
unlimited use; any of the three stated limitations dropped; R2-B moved; the qualification
recomputed; and the frozen packet or the spent v1 dispatch touched.

    uv run python infrastructure/scripts/render_r2_provider_reply.py
    uv run python infrastructure/scripts/render_r2_provider_reply.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

FROZEN = DATA / "globalping-r2-provider-reply-v1.json"
REVIEW = DATA / "globalping-r2-reply-review-v1.json"
PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
V1_DISPATCH = DATA / "globalping-r2-dispatch-approval-v1.json"
V2_DISPATCH = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v2.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"

RENDERED = DATA / "globalping-r2-reply-evidence-v1.md"

ATTRIBUTION_LEVELS = ("OPERATOR_SUPPLIED", "RAW_MAILBOX_READ")

# The fields a fabricated record fills in most convincingly.
HEADER_FIELDS = (
    "sender_display_name",
    "sender_email_address",
    "sent_at",
    "message_id",
    "in_reply_to_header",
    "recipient_as_received",
    "return_path",
    "dkim_or_spf_result",
)

STATED_LIMITATIONS = ("no_abuse", "no_exploitation_of_infrastructure", "no_use_as_a_proxy")

HARD_ZERO = (
    "MAILBOX_READS",
    "MAILBOX_MESSAGES_RETRIEVED",
    "EMAILS_SENT",
    "PUBLIC_API_READS",
    "GLOBALPING_API_EXECUTIONS",
    "GLOBALPING_MEASUREMENTS_CREATED",
    "TARGET_HTTP_REQUESTS",
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
    """A record says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _check_the_reply_is_frozen_as_supplied(frozen: dict, packet: dict) -> None:
    if frozen["record_kind"] != "FROZEN_PROVIDER_REPLY_SOURCE":
        raise ValidationError("the frozen record does not declare itself a source")
    if frozen["contains_interpretation"]:
        raise ValidationError("the frozen record contains interpretation")

    reply = frozen["reply"]
    if reply["body_sha256"] != hashlib.sha256(reply["body"].encode("utf-8")).hexdigest():
        raise ValidationError("the frozen reply does not answer to its own hash")
    if reply["body_source"] != "OPERATOR_SUPPLIED_TEXT":
        raise ValidationError(
            f"the body source is {reply['body_source']!r}; nothing was retrieved, so "
            "operator-supplied text is what this record holds"
        )
    if reply["body_retrieved_from_the_mailbox"]:
        raise ValidationError("the record claims a mailbox retrieval that did not happen")

    # A sender address is the single field the whole attribution question turns on.
    missing = frozen["message_fields_not_established"]
    provenance = frozen["provenance"]
    if not provenance["mailbox_read"]:
        for field in HEADER_FIELDS:
            if missing[field] is not None:
                raise ValidationError(
                    f"{field} is recorded as {missing[field]!r} and nothing was read. A "
                    "header field with no retrieval behind it is invented provenance"
                )
    if provenance["retrieval_method"] != "NONE_OPERATOR_SUPPLIED_ONLY":
        raise ValidationError("the retrieval method claims a retrieval the record denies")
    if provenance["results_returned"] != 0:
        raise ValidationError("the search returned results and the record holds none of them")
    if provenance["unrelated_mailbox_content_accessed"]:
        raise ValidationError("unrelated mailbox content was accessed")
    if provenance["public_surface_exists"]:
        raise ValidationError(
            "the record claims a public surface for a private email; if one existed the "
            "sender could have been established from it"
        )

    link = frozen["relationship_to_gp_r2_q1_v2"]
    if link["packet_content_sha256"] != packet["content_sha256"]:
        raise ValidationError("the frozen reply names a packet digest the packet does not have")

    # RECOMPUTED, not trusted. The first version of this check read the booleans the
    # record carries, so editing the packet's body left them true and the edit passed.
    # A guard that asks a record whether it is correct is not a guard.
    quoted = frozen["as_reported_by_the_operator"]["question_quoted_by_the_operator"]
    paragraphs = packet["body"].split("\n\n")
    if link["subject_matches_the_frozen_subject"] is not (
        frozen["as_reported_by_the_operator"]["thread_subject"] == packet["subject"]
    ):
        raise ValidationError("the record's subject match disagrees with the packet")
    if not link["subject_matches_the_frozen_subject"]:
        raise ValidationError("the reported subject is not the frozen subject")
    if link["quoted_question_is_the_frozen_first_paragraph"] is not (quoted == paragraphs[0]):
        raise ValidationError(
            "the record's first-paragraph match disagrees with the packet as stored; either "
            "the packet was edited or the quotation was"
        )
    if not link["quoted_question_is_the_frozen_first_paragraph"]:
        raise ValidationError(
            "the quoted question is not the frozen packet's first paragraph, so the reply "
            "is attached to a question this repository did not send"
        )
    if link["quoted_question_is_the_whole_frozen_body"] is not (quoted == packet["body"]):
        raise ValidationError("the record's whole-body claim disagrees with the packet")
    if link["quoted_question_is_the_whole_frozen_body"]:
        raise ValidationError(
            "the record claims the quotation is the whole body; the packet has a second "
            "paragraph, and which part was quoted is part of what the reply answered"
        )

    attribution = frozen["attribution"]
    if attribution["sufficient_for_provider_authority"]:
        raise ValidationError("provider authority is claimed with no established sender")
    for field in ("attributable_to_globalping_or_jsdelivr", "first_party"):
        if attribution[field] != "NOT_ESTABLISHED":
            raise ValidationError(f"{field} is {attribution[field]!r} and nothing establishes it")


def _check_the_review_reads_it_honestly(review: dict, frozen: dict, packet: dict) -> None:
    if review["record_kind"] != "REVIEWED_INTERPRETATION":
        raise ValidationError("the review does not declare itself an interpretation")
    source = review["source"]
    if source["reply_restated_in_this_record"]:
        raise ValidationError("the interpretation restates the reply rather than citing it")
    if source["reply_body_sha256"] != frozen["reply"]["body_sha256"]:
        raise ValidationError("the interpretation names a reply the frozen record does not hold")
    if source["frozen_reply_file_sha256"] != hashlib.sha256(FROZEN.read_bytes()).hexdigest():
        raise ValidationError("the frozen reply file changed after the review read it")

    attribution = review["question_1_attribution"]
    if attribution["provider_authority_established"]:
        raise ValidationError("the review establishes an authority the source cannot support")
    if attribution["level_reached"] not in ATTRIBUTION_LEVELS:
        raise ValidationError(f"the level {attribution['level_reached']!r} is undefined")
    if attribution["level_reached"] != "OPERATOR_SUPPLIED":
        raise ValidationError(
            "the review claims a level above OPERATOR_SUPPLIED while nothing was retrieved"
        )
    if attribution["level_required_to_close_a_rights_residual"] == attribution["level_reached"]:
        raise ValidationError("the review lowers the bar to the level it happens to have reached")
    for field in ("sender_display_name", "sender_email_address", "sent_at"):
        if attribution[field] is not None:
            raise ValidationError(f"the review records {field} and no read produced one")

    responsiveness = review["question_2_responsiveness"]
    clauses = responsiveness["clauses_asked"]
    addressed = sum(1 for state in clauses.values() if state.startswith("ADDRESSED"))
    if addressed != responsiveness["how_many_of_four_addressed"]:
        raise ValidationError("the count of addressed clauses does not match the clause table")
    if clauses["publicly_reachable_third_party_websites"] != "NOT_ADDRESSED":
        raise ValidationError(
            "the review records the third-party clause as addressed; the reply names no "
            "target, and that is the half R2 has open"
        )
    if not str(responsiveness["the_strongest_argument_that_it_answers_more"]).strip():
        raise ValidationError(
            "the review does not state the strongest argument against its own conclusion"
        )
    if not str(responsiveness["why_that_argument_does_not_carry"]).strip():
        raise ValidationError("the review raises a counter-argument and does not answer it")

    permission = review["question_3_does_it_establish_permission"]
    if (
        permission["discriminator_frozen_before_the_send"]
        != packet["expected_answer_discriminator"]
    ):
        raise ValidationError("the review quotes a discriminator the packet does not carry")
    if permission["does_the_reply_contain_such_a_statement"]:
        raise ValidationError(
            "the review says the reply states third-party target coverage; it states "
            "permission for commercial use"
        )
    if permission["broadened_into_permission_for_arbitrary_traffic"]:
        raise ValidationError("the reply was broadened into permission for arbitrary traffic")
    if permission["commercial_use_read_as_unlimited_use"]:
        raise ValidationError("commercial use was read as unlimited use")

    limits = review["question_4_limitations_stated_by_the_provider"]
    for limitation in STATED_LIMITATIONS:
        if limits[limitation] != "CLAIMED":
            raise ValidationError(
                f"{limitation} is {limits[limitation]!r}; the speaker is not established, so "
                "the limitation is claimed rather than established -- and it may not be "
                "dropped either"
            )
    if limits["limitations_removed_by_this_review"] != 0:
        raise ValidationError("a stated limitation was removed")
    if not limits["abuse_is_not_defined_by_the_reply"]:
        raise ValidationError(
            "the review treats 'no abuse' as bounded; the reply defines no standard for it"
        )


def _check_nothing_moved(review: dict) -> None:
    closes = review["question_5_does_it_close_the_residual"]
    if closes["answer"] != "NO":
        raise ValidationError("the review closes R2 on a reply with no established sender")
    if len(closes["two_independent_reasons"]) < 2:
        raise ValidationError("the review gives fewer than two independent reasons")
    if not closes["either_alone_would_be_enough"]:
        raise ValidationError(
            "the review makes its reasons jointly necessary; either alone keeps R2 open, and "
            "saying so is what stops one being fixed and read as a closure"
        )

    third_party = _load(THIRD_PARTY)
    if (
        closes["r2_b_before"] != third_party["verdict"]
        or closes["r2_b_after"] != third_party["verdict"]
    ):
        raise ValidationError("the R2-B verdict recorded here disagrees with its own review")
    if third_party["verdict"] != "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED":
        raise ValidationError("the third-party target scope review was moved by this mission")

    closure = _load(CLOSURE)
    if closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"] != "UNRESOLVED":
        raise ValidationError("the closure record moved R2-B")
    if closure["residuals"][1]["closed"]:
        raise ValidationError("R2 is recorded as closed")

    qualification = _load(QUALIFICATION)
    gates = {g["dimension"]: g["status"] for g in qualification["gates"]}
    block = review["question_6_qualification"]
    if gates["C9_RIGHTS_FEASIBILITY"] != "PARTIAL":
        raise ValidationError("C9 moved and no reply established the rights half")
    if block["c9_after"] != gates["C9_RIGHTS_FEASIBILITY"]:
        raise ValidationError("the review disagrees with the qualification about C9")
    if block["tally_after"] != qualification["tally"]:
        raise ValidationError("the review states a tally the qualification does not have")
    if block["qualification_recomputed"]:
        raise ValidationError("the qualification was recomputed by a reply that changed nothing")
    if block["verdict_after"] != qualification["verdict"]:
        raise ValidationError("the review states a verdict the qualification does not have")

    bounded = review["bounded_to_r2"]
    if bounded["r1_examined"]:
        raise ValidationError("R1 was examined by an R2 review")
    for flag in (
        "quantity_class_selected",
        "construct_selected",
        "frozen_v2_packet_modified",
        "failed_v1_dispatch_record_modified",
    ):
        if bounded[flag]:
            raise ValidationError(f"{flag} is true, and this mission may not do it")
    for counter in (
        "globalping_measurements_run",
        "target_http_requests",
        "evidence_independence_groups_created",
        "canonical_research_mutations",
    ):
        if bounded[counter] != 0:
            raise ValidationError(f"{counter} is {bounded[counter]}, and it must be 0")

    # The spent v1 dispatch and the v2 packet stay exactly as they were.
    v1 = _load(V1_DISPATCH)["execution"]
    if v1["status"] != "DISPATCH_ATTEMPTED_DELIVERY_FAILED" or v1["provider_contacted"]:
        raise ValidationError("the failed v1 dispatch record was altered")
    v2 = _load(V2_DISPATCH)["execution"]
    if v2["status"] != "SENT":
        raise ValidationError("the v2 dispatch status moved")
    if v2["provider_replied"]:
        raise ValidationError(
            "the v2 dispatch record now claims a provider reply; a reply whose sender is "
            "not established is not a provider reply, and that record is not this mission's "
            "to move"
        )

    follow_up = review["what_would_close_r2_b"]
    if not follow_up["requires_a_new_operator_approval"]:
        raise ValidationError("a follow-up enquiry is described as needing no approval")


def _check_accounting(frozen: dict) -> None:
    accounting = frozen["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")
    # The one non-zero counter, and it is counted rather than rounded away.
    if accounting["MAIL_CONNECTOR_EXECUTIONS"] < 1:
        raise ValidationError(
            "the record reports no connector execution and the provenance block records an "
            "attempted read. An attempt that reached a connector is a different fact from "
            "never having tried"
        )
    if not str(frozen["mail_connector_execution_note"]).strip():
        raise ValidationError("the connector execution is counted with no note saying what it was")


def validate() -> tuple[dict, dict]:
    frozen = _load(FROZEN)
    review = _load(REVIEW)
    packet = _load(PACKET)
    try:
        _check_the_reply_is_frozen_as_supplied(frozen, packet)
        _check_the_review_reads_it_honestly(review, frozen, packet)
        _check_nothing_moved(review)
        _check_accounting(frozen)
    except (KeyError, TypeError, IndexError) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return frozen, review


def render(frozen: dict, review: dict) -> str:
    attribution = review["question_1_attribution"]
    responsiveness = review["question_2_responsiveness"]
    permission = review["question_3_does_it_establish_permission"]
    limits = review["question_4_limitations_stated_by_the_provider"]
    closes = review["question_5_does_it_close_the_residual"]
    follow_up = review["what_would_close_r2_b"]

    lines = [
        "# The R2 reply, and why R2 is still open",
        "",
        f"Generated from `{FROZEN.name}` and `{REVIEW.name}`. Do not edit by hand.",
        "",
        "**A reply arrived. R2 did not close, for two independent reasons.**",
        "",
        "## What was said",
        "",
        f"> {frozen['reply']['body'].replace(chr(10), chr(10) + '> ')}",
        "",
        f"Frozen at `{frozen['reply']['body_sha256'][:16]}…`, source "
        f"`{frozen['reply']['body_source']}`.",
        "",
        "## Reason one: nobody knows who said it",
        "",
        "| field | value |",
        "|---|---|",
    ]
    for field in HEADER_FIELDS:
        lines.append(f"| {field} | {frozen['message_fields_not_established'][field]} |")
    lines += [
        "",
        frozen["message_fields_not_established"]["why_none_of_these_are_recorded"],
        "",
        f"Level reached: **`{attribution['level_reached']}`**. Level a rights residual needs: "
        f"**`{attribution['level_required_to_close_a_rights_residual']}`**.",
        "",
        attribution["why_the_thread_is_not_enough"],
        "",
        f"**{attribution['why_a_rights_residual_needs_the_higher_level']}**",
        "",
        "## Reason two: it answers the half that was already closed",
        "",
        "| clause asked | state |",
        "|---|---|",
    ]
    for clause, state in responsiveness["clauses_asked"].items():
        lines.append(f"| {clause.replace('_', ' ')} | `{state}` |")
    lines += [
        "",
        f"**The discriminator frozen before the send required:** "
        f"{permission['what_the_discriminator_required']}.",
        "",
        f"Does the reply contain such a statement: "
        f"**{permission['does_the_reply_contain_such_a_statement']}**. It answers "
        f"**{permission['which_half_it_answers']}**, which was already "
        f"`{permission['r2_a_status_before_this_reply']}`.",
        "",
        "### The strongest argument the other way",
        "",
        responsiveness["the_strongest_argument_that_it_answers_more"],
        "",
        f"**Why it does not carry.** {responsiveness['why_that_argument_does_not_carry']}",
        "",
        f"**{permission['why_this_is_the_sharper_finding']}**",
        "",
        "## The limitations, recorded and not dropped",
        "",
        "| limitation | state |",
        "|---|---|",
    ]
    for limitation in STATED_LIMITATIONS:
        lines.append(f"| {limitation.replace('_', ' ')} | `{limits[limitation]}` |")
    lines += [
        "",
        limits["why_they_are_recorded_even_at_this_level"],
        "",
        f"`no_abuse` is undefined by the reply. {limits['what_that_means']}",
        "",
        "## What did not move",
        "",
        "| | before | after |",
        "|---|---|---|",
        f"| R2-B | `{closes['r2_b_before']}` | `{closes['r2_b_after']}` |",
        f"| C9 | `{review['question_6_qualification']['c9_before']}` "
        f"| `{review['question_6_qualification']['c9_after']}` |",
        f"| verdict | `{review['question_6_qualification']['verdict_before']}` "
        f"| `{review['question_6_qualification']['verdict_after']}` |",
        "",
        "Either reason alone would have been enough: "
        f"**{closes['either_alone_would_be_enough']}**. {closes['why_that_matters']}",
        "",
        "## What would close it",
        "",
        follow_up["shape_of_a_follow_up"],
        "",
        f"**{follow_up['why_the_last_enquiry_did_not_get_it']}**",
        "",
        f"Requires a new operator approval: **{follow_up['requires_a_new_operator_approval']}**. "
        f"{follow_up['why']} And first: {follow_up['and_first']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        frozen, review = validate()
    except ValidationError as error:
        print(f"REFUSED  R2 provider reply: {error}")
        return 1

    text = render(frozen, review)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its records")
            return 1
        print("ok       the R2 provider reply matches its records")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"level    {review['question_1_attribution']['level_reached']}")
    print(f"closes   {review['question_5_does_it_close_the_residual']['answer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
