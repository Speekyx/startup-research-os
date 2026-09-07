"""Render and validate the GP-R2-B-Q1 provider reply, its review, and the closure it caused.

R2-B closed on twenty-two characters. That is not a reason to check it less.

Four things this gate holds:

    THE EVIDENCE AND THE CONCLUSION LIVE IN SEPARATE DOCUMENTS.
    THE DISCRIMINATOR IS READ LIVE, FROM THE PACKET, AND NOT RESTATED.
    THE PERMISSION IS EXACTLY AS WIDE AS THE QUESTION.
    A CLOSED RESIDUAL AUTHORISES NOTHING TO RUN.

The reply is anaphoric: "Yes it's not a problem" carries its scope only because the question
carries it. So the bound is the thing most easily lost, and the gate refuses a record that
drops a limitation, widens the activity, or reads the answer as unconditional.

The discriminator was frozen in Mission 1.76.2 and sent in 1.76.4. It is loaded from the
packet at validation time and compared, so an edit that softened it after the answer arrived
fails here rather than passing quietly.

`validate()` refuses: a frozen reply that does not answer to its own hash, or that carries a
verdict, an evidence level or a message id; a review whose chosen branch text is not the
packet's; a closure resting on one of the seven routes the discriminator excludes; a dropped
limitation; a widened activity; a superseded record edited rather than pointed forward; a
reopened passing dimension; and a qualification that authorises a run.

    uv run python infrastructure/scripts/render_r2b_reply_review.py
    uv run python infrastructure/scripts/render_r2b_reply_review.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

REPLY = DATA / "globalping-r2b-provider-reply-v1.json"
REVIEW = DATA / "globalping-r2b-reply-review-v1.json"
PACKET = DATA / "globalping-r2b-enquiry-packet-v1.json"
APPROVAL = DATA / "globalping-r2b-dispatch-approval-v1.json"
SCOPE_V1 = DATA / "globalping-third-party-target-scope-review-v1.json"
SCOPE_V2 = DATA / "globalping-third-party-target-scope-review-v2.json"
CLOSURE_V2 = DATA / "globalping-residual-closure-v2.json"
CLOSURE_V3 = DATA / "globalping-residual-closure-v3.json"
QUAL_V3 = DATA / "globalping-counterpart-qualification-v3.json"
QUAL_V4 = DATA / "globalping-counterpart-qualification-v4.json"
RECIPIENT = DATA / "globalping-r2-replacement-recipient-review-v1.json"

RENDERED = DATA / "globalping-r2b-reply-review-v1.md"

PROVIDER_ADDRESS = "d@globalping.io"

# The four limitations the question carried. A "yes" to a conditional proposition agrees to
# the conditional one, and dropping one of these widens it past the sentence it answers.
LIMITATIONS = (
    "compliance with Globalping's limits and other policies",
    "no abuse",
    "no exploitation of infrastructure",
    "no use as a proxy",
)

# Things this answer does not reach. The permission's width comes from the question, so a
# reader who loses the question loses the bound.
NOT_ESTABLISHED = (
    "GET or any method other than HEAD",
    "response body retrieval",
    "scanning or enumeration",
    "unbounded or unlimited volume",
    "use as a proxy",
)

GATES = (
    "THREAD_BINDING",
    "SENDER_IDENTITY_ESTABLISHED",
    "PROVIDER_AUTHORITY_ESTABLISHED",
    "REPLY_FROZEN",
    "SEMANTIC_RESPONSIVENESS",
    "THIRD_PARTY_TARGET_SCOPE",
    "BOUNDED_HEAD_SCOPE",
    "LIMITS_PRESERVED",
    "R2_B_RESIDUAL_CLOSED",
)

# Each condition and the field that must carry its basis. A condition asserted with no
# basis is a sentence, and Mission 1.74.7 defined this level as five checkable things.
LEVEL_CONDITIONS = (
    ("solicited", "solicited_basis"),
    ("responsive_to_the_exact_predicate", "responsive_basis"),
    ("attributable_to_the_provider", "attributable_basis"),
    ("retrieved_without_a_summarising_extraction", "retrieval_basis"),
    ("durably_re_examinable", "durability_basis"),
)

HARD_ZERO = (
    "EMAILS_SENT",
    "OUTWARD_REPLIES_MADE",
    "MAILBOX_READS",
    "GLOBALPING_API_EXECUTIONS",
    "GLOBALPING_MEASUREMENTS_CREATED",
    "TARGET_HTTP_REQUESTS",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "SCORES",
    "CANONICAL_MUTATIONS",
)


class ValidationError(RuntimeError):
    """The reply, the review or the closure says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _check_the_reply_is_frozen_and_says_nothing_about_itself(reply: dict, packet: dict) -> None:
    """A document holding both the evidence and the conclusion can adjust the first."""
    body = reply["reply"]
    if hashlib.sha256(body["body"].encode("utf-8")).hexdigest() != body["body_sha256"]:
        raise ValidationError("the frozen reply does not answer to its own recorded hash")
    if body["body_length_characters"] != len(body["body"]):
        raise ValidationError("the frozen reply misreports its own length")
    if not body["operator_statement_matches_the_extracted_bytes"]:
        raise ValidationError(
            "the operator's quotation and the extracted bytes disagree, and the record does "
            "not say which won"
        )
    if body["body_as_stated_by_the_operator"] != body["body"]:
        raise ValidationError("the record claims a quotation match its own fields refute")

    for banned in ("verdict", "evidence_level", "closes_r2_b", "r2_b_residual_closed", "gates"):
        if banned in reply:
            raise ValidationError(
                f"the frozen source carries {banned!r}; it states what was said and may not "
                "state what it means"
            )

    if reply["answers"]["packet_content_sha256"] != packet["content_sha256"]:
        raise ValidationError("the frozen reply answers a different enquiry than this packet")
    if reply["answers"]["thread_subject"] != packet["subject"]:
        raise ValidationError("the frozen reply names a different thread subject")

    headers = reply["headers_as_displayed"]
    if headers["sender_email"] != PROVIDER_ADDRESS:
        raise ValidationError(
            f"the reply is recorded as coming from {headers['sender_email']!r}, which is not "
            "the address the provider publishes"
        )
    for absent in ("message_id",):
        if headers[absent] is not None:
            raise ValidationError(f"the record carries a {absent} the export does not have")
    for absent in (
        "message_id_available",
        "received_chain_available",
        "dkim_or_spf_result_available",
    ):
        if headers[absent]:
            raise ValidationError(
                f"the record claims {absent}; a printed thread export renders what a reader "
                "sees and carries no transport headers"
            )
    if not headers["displayed_time_carries_no_offset"]:
        raise ValidationError(
            "the record claims an offset for a displayed time; the export states no zone and "
            "an invented one would be a fact about nothing"
        )

    provenance = reply["provenance"]
    if provenance["summarising_model_in_the_extraction_path"]:
        raise ValidationError("a summarising model is in the extraction path; 1.63 refuses that")
    if provenance["artifact_committed_to_this_repository"]:
        raise ValidationError(
            "the export is recorded as committed; it carries the operator's mailbox and a "
            "per-account key, and this repository is public"
        )
    if provenance["gmail_permalink_recorded"]:
        raise ValidationError("a Gmail permalink is recorded, and it embeds an account key")
    if len(provenance["artifact_sha256"]) != 64:
        raise ValidationError("the export fingerprint is not a sha256")

    discrepancy = reply["discrepancy_recorded_rather_than_resolved"]
    if discrepancy["resolved"]:
        raise ValidationError(
            "the send-time discrepancy is recorded as resolved; the export states no zone, so "
            "the two times cannot be subtracted without assuming one"
        )
    if discrepancy["does_it_bear_on_r2_b"]:
        raise ValidationError("a six-minute send-time difference is recorded as bearing on R2-B")


def _check_the_discriminator_was_not_softened(review: dict, packet: dict) -> None:
    """Frozen in 1.76.2, sent in 1.76.4, applied here without a word of it changing."""
    discriminator = packet["expected_answer_discriminator"]
    branches = discriminator["closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"]

    if not discriminator["the_answer_must_address_third_party_target_scope_explicitly"]:
        raise ValidationError("the discriminator's explicitness requirement was removed")
    for required in ("PERMITTED", "NOT_PERMITTED", "CONDITIONALLY_PERMITTED"):
        if required not in branches:
            raise ValidationError(f"the discriminator lost its {required} branch")

    scope = review["gates"]["THIRD_PARTY_TARGET_SCOPE"]
    branch = scope["which_discriminator_branch"]
    if branch not in branches:
        raise ValidationError(
            f"the review chose branch {branch!r}, which the packet does not define"
        )
    if scope["branch_text"] != branches[branch]:
        raise ValidationError(
            "the review's quoted branch text is not the packet's; a discriminator restated "
            "rather than read is a discriminator that can drift"
        )

    responsiveness = review["gates"]["SEMANTIC_RESPONSIVENESS"]
    if not responsiveness["the_referent_is_supplied_by_the_question_not_inferred"]:
        raise ValidationError(
            "the review records the referent as inferred, which is the presupposition route "
            "the discriminator excludes by name"
        )
    for field in (
        "why_this_is_not_the_presupposition_route_the_discriminator_refuses",
        "how_that_is_known",
        "unambiguity_test",
    ):
        if not str(responsiveness[field]).strip():
            raise ValidationError(f"the review does not state {field}")

    # None of the seven excluded routes may be what closed it.
    closed_by = str(review["gates"]["R2_B_RESIDUAL_CLOSED"]["closed_by"]).lower()
    for excluded in discriminator["does_not_close_r2_b"]:
        token = excluded.strip("'").lower()
        if (
            token in ("silence", "product behaviour", "implication or presupposition")
            and token in closed_by
        ):
            raise ValidationError(
                f"R2-B is recorded as closed by {excluded!r}, which the discriminator excludes"
            )


def _check_the_permission_is_as_wide_as_the_question(review: dict) -> None:
    """The answer is anaphoric, so the bound lives in the question and is easily lost."""
    limits = review["gates"]["LIMITS_PRESERVED"]
    if limits["status"] != "YES":
        raise ValidationError("the review does not preserve the stated limitations")
    if limits["dropped_by_this_review"] != 0:
        raise ValidationError("the review drops a limitation the question carried")
    for limitation in LIMITATIONS:
        if limitation not in limits["limitations"]:
            raise ValidationError(f"the limitation {limitation!r} was dropped")

    bounded = review["gates"]["BOUNDED_HEAD_SCOPE"]
    if not bounded["the_permission_is_exactly_as_wide_as_the_question"]:
        raise ValidationError("the review records the permission as wider than the question")
    for item in NOT_ESTABLISHED:
        if item not in bounded["not_established_by_this_answer"]:
            raise ValidationError(
                f"the review does not record {item!r} as outside what this answer establishes"
            )
    if "HEAD" not in bounded["what_was_asked"]:
        raise ValidationError("the recorded activity does not name the method that was asked about")

    scope = review["gates"]["THIRD_PARTY_TARGET_SCOPE"]
    if scope["status"] != "PERMITTED":
        raise ValidationError(f"the scope verdict {scope['status']!r} is not a closing one")
    if not str(scope["why_not_conditionally_permitted"]).strip():
        raise ValidationError("the review does not say why it chose PERMITTED over CONDITIONALLY")


def _check_authority_was_established_and_bounded(review: dict) -> None:
    identity = review["gates"]["SENDER_IDENTITY_ESTABLISHED"]
    if review["gates"]["SENDER_EMAIL"] != PROVIDER_ADDRESS:
        raise ValidationError("the review names a sender other than the provider's address")
    if not str(identity["basis"]).strip():
        raise ValidationError("the review states no basis for the sender identity")
    for absent in (
        "the legal identity of the person behind the display name",
        "their role or authority to bind the provider contractually",
    ):
        if absent not in identity["what_is_not_established"]:
            raise ValidationError(f"the review does not record {absent!r} as unestablished")

    authority = review["gates"]["PROVIDER_AUTHORITY_ESTABLISHED"]
    corroboration = authority["corroboration"]
    if corroboration["treated_as"] != "CORROBORATION_ONLY":
        raise ValidationError(
            "the GitHub username link is treated as a basis; identifying a display name with "
            "a username is an inference and 1.74.4 recorded such a thing as corroboration only"
        )
    if not str(corroboration["why_not_the_basis"]).strip():
        raise ValidationError(
            "the record does not say why the username link is corroboration rather than the "
            "basis; an unexplained demotion is one a later reader reverses"
        )
    weaker = authority["weaker_than_r1_and_the_record_says_so"]
    if not str(weaker["why_r1_is_stronger"]).strip():
        raise ValidationError("the review does not say why R1's basis is stronger than this one")

    # The address was established first-party, and that record still says what it said.
    recipient = _load(RECIPIENT)
    if not recipient["establishment"]["address_is_established_first_party"]:
        raise ValidationError("the address is no longer recorded as established first-party")
    if recipient["candidate_address"] != PROVIDER_ADDRESS:
        raise ValidationError("the recipient record names a different address")


def _check_the_evidence_level(review: dict) -> None:
    level = review["evidence_level"]
    conditions = level["conditions_all_of_which_must_hold"]
    for condition, basis in LEVEL_CONDITIONS:
        if not conditions[condition]:
            raise ValidationError(f"the evidence level condition {condition} does not hold")
        if not str(conditions.get(basis) or "").strip():
            raise ValidationError(
                f"the condition {condition} is asserted with no {basis}; an unbacked condition "
                "is a sentence rather than a check"
            )
    if not level["is_a_closing_level"]:
        raise ValidationError("the level is not closing and R2-B is recorded as closed")
    differs = level["the_condition_that_differs_from_r1"]
    if not differs["this_level_is_weaker_than_r1_and_the_record_says_so"]:
        raise ValidationError(
            "the record does not state that private correspondence is a weaker durability "
            "basis than a public permalinked comment"
        )
    if not str(differs["what_replaces_it"]).strip():
        raise ValidationError("the record does not say what replaces public citability")


def _check_the_closure_chain(review: dict) -> None:
    scope_v1, scope_v2 = _load(SCOPE_V1), _load(SCOPE_V2)
    if scope_v1["verdict"] != "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED":
        raise ValidationError("the superseded scope review was edited rather than pointed forward")
    if scope_v1["superseded_by"] != SCOPE_V2.name:
        raise ValidationError("the superseded scope review does not point at its successor")
    if scope_v2["supersedes"] != SCOPE_V1.name:
        raise ValidationError("the new scope review does not name what it supersedes")
    if not scope_v2["declared_not_documented"]["the_terms_still_read_as_they_did"]:
        raise ValidationError(
            "the record claims the Terms changed; no published document was amended, and a "
            "declaration is not an amendment"
        )
    if scope_v2["declared_not_documented"]["closed_on_documentation"]:
        raise ValidationError(
            "R2-B is recorded as closed on documentation; no published document was amended"
        )
    if (
        scope_v2["terms_silence_turned_favourable"]
        or scope_v2["terms_ambiguity_turned_into_prohibition"]
    ):
        raise ValidationError("the scope review turned a silence or an ambiguity into a verdict")

    closure_v2, closure_v3 = _load(CLOSURE_V2), _load(CLOSURE_V3)
    if closure_v2["residuals_remaining"] != 1 or closure_v2["superseded_by"] != CLOSURE_V3.name:
        raise ValidationError("the superseded closure record was edited or does not point forward")
    if closure_v3["residuals_remaining"] != 0:
        raise ValidationError("R2-B is closed and the closure record still counts a residual")
    if not closure_v3["r2_pass_requires_both"]["B_third_party_targets_within_permitted_use"]:
        raise ValidationError("R2 is recorded as passing with its second half unmet")
    for residual in closure_v3["residuals"]:
        if not residual["closed"]:
            raise ValidationError(f"{residual['id']} is not closed and the count says zero remain")
    for limitation in LIMITATIONS:
        if limitation not in closure_v3["limitations_carried_forward"]:
            raise ValidationError(f"the closure record drops {limitation!r}")
    if closure_v3["project_governance_classification"][
        "provider_terms_block_the_intended_activity"
    ]:
        raise ValidationError("the classification contradicts the closure")
    if not closure_v3["project_governance_classification"]["this_is_not_a_legal_conclusion"]:
        raise ValidationError("the record presents a governance classification as a legal one")

    qual_v3, qual_v4 = _load(QUAL_V3), _load(QUAL_V4)
    if qual_v3["tally"] != {"PASS": 11, "PARTIAL": 1, "FAIL": 0, "UNKNOWN": 0}:
        raise ValidationError("the superseded qualification was edited rather than pointed forward")
    if qual_v3["superseded_by"] != QUAL_V4.name:
        raise ValidationError("the superseded qualification does not point at its successor")

    before = {g["dimension"]: g["status"] for g in qual_v3["gates"]}
    after = {g["dimension"]: g["status"] for g in qual_v4["gates"]}
    if set(before) != set(after):
        raise ValidationError("the qualification's dimension set changed")
    for dimension, status in before.items():
        if status == "PASS" and after[dimension] != "PASS":
            raise ValidationError(
                f"{dimension} was reopened, and no contradicting evidence was found"
            )
        if dimension != "C9_RIGHTS_FEASIBILITY" and after[dimension] != status:
            raise ValidationError(f"{dimension} moved, and nothing in this mission bears on it")
    if after["C9_RIGHTS_FEASIBILITY"] != "PASS":
        raise ValidationError("R2-B closed and C9 did not move")

    tally = qual_v4["tally"]
    counted = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0}
    for status in after.values():
        counted[status] += 1
    if tally != counted:
        raise ValidationError(f"the tally {tally} does not count the gates {counted}")
    if qual_v4["verdict"] != "COUNTERPART_RESOLVED":
        raise ValidationError("every dimension passes and the verdict is not resolved")
    if qual_v4["passing_dimensions_reopened"] != 0:
        raise ValidationError("a passing dimension was reopened")

    c9 = next(g for g in qual_v4["gates"] if g["dimension"] == "C9_RIGHTS_FEASIBILITY")
    if not str(c9["stated_bound"]).strip():
        raise ValidationError("C9 passes with no stated bound on what the permission covers")
    if not c9["weaker_than_r1_evidence"]:
        raise ValidationError("C9 does not record that its basis is weaker than R1's")


def _check_nothing_was_authorised_to_run(review: dict) -> None:
    qual = _load(QUAL_V4)["what_qualification_does_not_authorise"]
    for flag in (
        "no_construct_is_selected",
        "no_quantity_class_is_selected",
        "no_corpus_is_frozen",
        "no_measurement_was_run",
        "no_independence_group_exists",
        "no_score_is_issued",
    ):
        if not qual[flag]:
            raise ValidationError(f"{flag} is false; a qualified counterpart is not a running one")
    if not qual["a_run_still_needs"]:
        raise ValidationError("the record does not say what a run would still need")
    if _load(DATA / "globalping-counterpart-qualification-v4.json")["no_score_issued"] is not True:
        raise ValidationError("a score was issued")

    for absent in ("selected-quantity-class-v1.json",):
        if (DATA / absent).exists():
            raise ValidationError(f"{absent} exists; no quantity class was selected here")

    for statement in review["what_this_review_does_not_do"]:
        if not str(statement).strip():
            raise ValidationError("the review's exclusion list carries an empty entry")
    for required in ("amend the provider's Terms, which still read as they did",):
        if required not in review["what_this_review_does_not_do"]:
            raise ValidationError(f"the review does not record that it does not {required}")


def _check_every_gate_is_answered(review: dict, reply: dict) -> None:
    for name in GATES:
        if name not in review["gates"]:
            raise ValidationError(f"the review does not answer {name}")
    if review["cites"]["reply_body_sha256"] != reply["reply"]["body_sha256"]:
        raise ValidationError("the review cites a different reply than the one that is frozen")
    if not review["cites"]["the_discriminator_was_frozen_before_dispatch"]:
        raise ValidationError("the review does not rest on a discriminator frozen before dispatch")
    if review["gates"]["REPLY_FROZEN"]["status"] != "YES":
        raise ValidationError("the review proceeds on a reply that was not frozen")
    if not review["gates"]["REPLY_FROZEN"]["frozen_before_it_was_read"]:
        raise ValidationError("the reply was read before it was frozen")

    execution = _load(APPROVAL)["execution"]
    if execution["reply_record"] != "docs/data/globalping-r2b-provider-reply-v1.json":
        raise ValidationError("the execution names a different frozen reply")
    if execution["delivery"]["evidence_sha256"] != reply["reply"]["body_sha256"]:
        raise ValidationError("the execution's delivery cites a different reply")


def validate() -> tuple[dict, dict]:
    reply = _load(REPLY)
    review = _load(REVIEW)
    packet = _load(PACKET)
    try:
        _check_the_reply_is_frozen_and_says_nothing_about_itself(reply, packet)
        _check_every_gate_is_answered(review, reply)
        _check_the_discriminator_was_not_softened(review, packet)
        _check_the_permission_is_as_wide_as_the_question(review)
        _check_authority_was_established_and_bounded(review)
        _check_the_evidence_level(review)
        _check_the_closure_chain(review)
        _check_nothing_was_authorised_to_run(review)
    except (KeyError, TypeError, IndexError, StopIteration) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return reply, review


def render(reply: dict, review: dict) -> str:
    gates = review["gates"]
    qual = _load(QUAL_V4)
    closure = _load(CLOSURE_V3)
    level = review["evidence_level"]

    lines = [
        "# R2-B — twenty-two characters, and the residual closes",
        "",
        f"Generated from `{REPLY.name}` and `{REVIEW.name}`. Do not edit by hand.",
        "",
        f"> {reply['reply']['body']}",
        "",
        f"`{reply['reply']['body_sha256'][:16]}…`, "
        f"{reply['reply']['body_length_characters']} characters, from "
        f"`{reply['headers_as_displayed']['sender_email']}` at "
        f"{reply['headers_as_displayed']['displayed_reply_time_normalised']} as displayed.",
        "",
        "## The gates, each answered separately",
        "",
        "| gate | |",
        "|---|---|",
    ]
    for name in GATES:
        value = gates[name]
        status = value if isinstance(value, str) else value["status"]
        lines.append(f"| {name} | `{status}` |")
    lines += [
        f"| SENDER_EMAIL | `{gates['SENDER_EMAIL']}` |",
        "",
        "## Why an anaphoric answer is not the presupposition route",
        "",
        gates["SEMANTIC_RESPONSIVENESS"][
            "why_this_is_not_the_presupposition_route_the_discriminator_refuses"
        ],
        "",
        gates["SEMANTIC_RESPONSIVENESS"]["how_that_is_known"],
        "",
        f"**{gates['SEMANTIC_RESPONSIVENESS']['unambiguity_test']}**",
        "",
        "## The permission is exactly as wide as the question",
        "",
        gates["BOUNDED_HEAD_SCOPE"]["what_was_asked"] + ".",
        "",
        "It does not establish:",
        "",
    ]
    lines += [f"- {item}" for item in gates["BOUNDED_HEAD_SCOPE"]["not_established_by_this_answer"]]
    lines += [
        "",
        gates["BOUNDED_HEAD_SCOPE"]["why_the_list_is_written_down"],
        "",
        "### Limitations preserved",
        "",
    ]
    lines += [f"- {item}" for item in gates["LIMITS_PRESERVED"]["limitations"]]
    lines += [
        "",
        gates["LIMITS_PRESERVED"]["why_they_survive_a_yes"],
        "",
        "## Authority, and what it is not",
        "",
        gates["PROVIDER_AUTHORITY_ESTABLISHED"]["basis"],
        "",
        f"Weaker than R1's: {gates['PROVIDER_AUTHORITY_ESTABLISHED']['weaker_than_r1_and_the_record_says_so']['why_r1_is_stronger']}",
        "",
        f"**Evidence level `{level['level']}`.** "
        f"{level['the_condition_that_differs_from_r1']['what_replaces_it']}",
        "",
        "## What moved",
        "",
        "| | before | after |",
        "|---|---|---|",
        f"| R2-B | UNRESOLVED | {closure['sub_results']['R2_B_THIRD_PARTY_TARGET_SCOPE']} |",
        "| C9 | PARTIAL | PASS |",
        f"| tally | 11 / 1 / 0 | "
        f"{qual['tally']['PASS']} / {qual['tally']['PARTIAL']} / {qual['tally']['FAIL']} |",
        f"| counterpart | {qual['verdict_before']} | **{qual['verdict']}** |",
        f"| residuals remaining | 1 | {closure['residuals_remaining']} |",
        "",
        "## A qualified counterpart is not a running one",
        "",
        "A run still needs:",
        "",
    ]
    lines += [
        f"- {item}" for item in qual["what_qualification_does_not_authorise"]["a_run_still_needs"]
    ]
    lines += [
        "",
        f"**{closure['project_governance_classification']['classification']}**, and it is a "
        "governance classification rather than a legal conclusion.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        reply, review = validate()
    except ValidationError as error:
        print(f"REFUSED  R2-B reply review: {error}")
        return 1

    text = render(reply, review)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its records")
            return 1
        print("ok       the R2-B reply review matches its records")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"reply    {reply['reply']['body_sha256'][:16]}…")
    print(f"scope    {review['gates']['THIRD_PARTY_TARGET_SCOPE']['status']}")
    print(f"closed   {review['gates']['R2_B_RESIDUAL_CLOSED']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
