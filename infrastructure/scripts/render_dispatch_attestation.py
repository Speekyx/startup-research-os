"""Render and validate the Mission 1.66.1 manual-dispatch attestation.

The operator performed the already-approved action and attested to it afterwards.
This records that later event, and `validate()` enforces what recording it may
and may not mean:

  - both frozen hashes are recomputed, so an attestation about bytes that have
    since moved is refused;
  - the approved envelope is untouched, its sender placeholder is not replaced
    and it is not marked sent -- it records what was APPROVED;
  - Mission 1.66's execution record keeps its original statement and gains only
    a forward pointer, because rewriting it would make that mission's report
    describe a moment it did not observe;
  - the attested execution must match the approved recipient, channel, subject
    and send count, and the sender is admitted only because the envelope bound a
    placeholder rather than a mailbox;
  - `OPERATOR_ATTESTED` may not be reported as `BYTE_VERIFIED` while no sent
    message has been imported and hashed;
  - one approval authorises one send;
  - the mailbox was not searched, so the reply status is NOT_CHECKED and never
    NO_RESPONSE_EXISTS;
  - a sent question is not an answer, so no apparatus gate moves.

    uv run python infrastructure/scripts/render_dispatch_attestation.py
    uv run python infrastructure/scripts/render_dispatch_attestation.py --check

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

ATTESTATION = DATA / "onyphe-manual-dispatch-attestation-v1.json"
RENDERED = ATTESTATION.with_suffix(".md")

ONYPHE_ENVELOPE = DATA / "onyphe-dispatch-envelope-v1.json"
ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
MISSION_1_66_EXECUTION = DATA / "onyphe-enquiry-dispatch-execution-v1.json"
MISSION_1_66_VERDICT = DATA / "approved-dispatch-execution-v1.json"
NETLAS_ENVELOPE = DATA / "netlas-dispatch-envelope-v1.json"

APPROVED_ENVELOPE_SHA256 = "12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2"
APPROVED_CONTENT_SHA256 = "0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f"
APPROVED_RECIPIENT = "contact@onyphe.io"
APPROVED_CHANNEL = "OPERATOR_MANUAL_SEND"
APPROVED_SUBJECT = "Three questions about datascan record semantics and scan configuration"
APPROVED_SENDER_PLACEHOLDER = "OPERATOR_CHOSEN_MAILBOX_AT_SEND_TIME"

APPROVAL_LOWER_BOUND_UTC = "2026-09-05T17:09:39Z"
MISSION_1_66_MERGED_UTC = "2026-09-05T17:50:04Z"

BINDING_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "outbound_channel",
    "sender_identity",
    "subject",
    "content_version",
)

EXECUTION_STATES = ("SENT", "EXECUTION_DIVERGED", "DUPLICATE_DISPATCH_OCCURRED")
EVIDENCE_LEVELS = ("OPERATOR_ATTESTED", "BYTE_VERIFIED")
MESSAGE_ID_STATES = ("NOT_AVAILABLE", "RECORDED")
RESPONSE_STATES = (
    "NOT_CHECKED_AFTER_DISPATCH",
    "RECEIVED_PENDING_REVIEW",
    "CHECKED_NONE_FOUND",
)
PRIMARY_OUTCOMES = {
    "ONYPHE_MANUAL_DISPATCH_ATTESTED",
    "EXECUTION_DIVERGED_FROM_APPROVED_DISPATCH",
    "DUPLICATE_DISPATCH_OCCURRED",
    "MISSION_1_66_NOT_MERGED",
    "MISSION_1_66_1_BASELINE_DRIFT",
    "MISSION_1_66_1_CANONICAL_MUTATION",
}

OVERCLAIMS = ("installation", "customer", "subscription", "revenue", "adoption", "demand")


class ValidationError(Exception):
    """A Mission 1.66.1 record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


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


def envelope_digest(envelope: dict, content_sha: str) -> str:
    binding = {f: envelope.get(f) for f in BINDING_FIELDS}
    binding["enquiry_content_sha256"] = content_sha
    blob = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate() -> dict:
    record = _load(ATTESTATION)
    _validate_frozen_artifacts()
    _validate_mission_1_66_untouched(record)
    _validate_attestation(record)
    _validate_matching(record)
    _validate_boundaries(record)
    _validate_no_overclaims(record)
    return record


def _validate_frozen_artifacts() -> None:
    content = hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest()
    if content != APPROVED_CONTENT_SHA256:
        raise ValidationError(
            f"the approved enquiry body has changed. approved {APPROVED_CONTENT_SHA256}, "
            f"computed {content}. An attestation about bytes that moved attests to nothing"
        )

    envelope = _load(ONYPHE_ENVELOPE)
    digest = envelope_digest(envelope, content)
    if digest != APPROVED_ENVELOPE_SHA256:
        raise ValidationError(
            f"the envelope no longer binds the approved action. approved "
            f"{APPROVED_ENVELOPE_SHA256}, computed {digest}"
        )
    if envelope.get("sender_identity") != APPROVED_SENDER_PLACEHOLDER:
        raise ValidationError(
            "the frozen envelope's sender placeholder was replaced with an actual mailbox. The "
            "placeholder describes what was APPROVED; the actual sender is execution provenance"
        )
    if envelope.get("sender_identity_is_a_placeholder") is not True:
        raise ValidationError("the frozen envelope no longer declares its sender a placeholder")
    if envelope.get("sent") is not False or envelope.get("sent_at") is not None:
        raise ValidationError(
            "the frozen envelope was marked sent. It records the permission, not the event"
        )
    if envelope.get("dispatch_count") != 0:
        raise ValidationError("the frozen envelope counts a dispatch")
    if envelope.get("approval_recorded") is not False:
        raise ValidationError("the approval was written into the document it approves")

    netlas = _load(NETLAS_ENVELOPE)
    if netlas.get("recipient_address") is not None:
        raise ValidationError("a Netlas recipient appeared. No address may be guessed or decoded")
    if netlas.get("envelope_sha256") is not None:
        raise ValidationError("a Netlas envelope hash was created for an incomplete action")


def _validate_mission_1_66_untouched(record: dict) -> None:
    """Mission 1.66 recorded a moment. A later event does not rewrite it."""
    execution = _load(MISSION_1_66_EXECUTION)
    if execution.get("execution_status") != "APPROVED_AWAITING_MANUAL_EXECUTION":
        raise ValidationError(
            "Mission 1.66's execution record was rewritten. It recorded that nothing had been "
            "established as sent AT THAT TIME, which is still true of that moment"
        )
    if execution["execution"].get("SENT") is not False:
        raise ValidationError("Mission 1.66's execution record was edited to read sent")
    if execution["operator_confirmation"].get("CONFIRMATION_GIVEN") is not False:
        raise ValidationError(
            "Mission 1.66's record was edited to carry a confirmation it did not receive"
        )

    pointer = execution.get("superseded_by")
    if not pointer:
        raise ValidationError(
            "Mission 1.66's execution record carries no forward pointer, so a reader meeting it "
            "alone would take a historical state for the current one"
        )
    if pointer.get("record") != "onyphe-manual-dispatch-attestation-v1":
        raise ValidationError("the forward pointer names the wrong record")

    verdict = _load(MISSION_1_66_VERDICT)
    if verdict.get("primary_outcome") != "ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION":
        raise ValidationError(
            "Mission 1.66's verdict was rewritten. Its outcome was correct when it ran, and a "
            "mission report may not be edited to describe a moment it did not observe"
        )

    history = record["the_history_this_appends_to"]
    if len(history.get("chain", [])) < 4:
        raise ValidationError("the history chain must show every state, not only the current one")
    if history["chain"][-1].get("state") != "OPERATOR_ATTESTED_SENT":
        raise ValidationError("the chain's last state must be the one this record establishes")
    for field in ("mission_1_66_was_correct_when_it_ran", "so_mission_1_66_is_not_rewritten"):
        if not str(history.get(field, "")).strip():
            raise ValidationError(f"the record must state {field}")


def _validate_attestation(record: dict) -> None:
    status = record.get("execution_status")
    if status not in EXECUTION_STATES:
        raise ValidationError(f"execution status {status!r} is not in the vocabulary")

    level = record.get("verification_basis")
    if level not in EVIDENCE_LEVELS:
        raise ValidationError(f"verification basis {level!r} is not in the vocabulary")

    evidence = record["evidence_level_and_why_it_is_not_higher"]
    if evidence.get("level") != level:
        raise ValidationError("the record states two different evidence levels")
    if level == "BYTE_VERIFIED":
        if evidence.get("sent_message_artifact_imported") is not True:
            raise ValidationError(
                "BYTE_VERIFIED without an imported sent-message artifact. An attestation is not "
                "proof and may not be promoted into one by relabelling"
            )
        if record["the_attestation"].get("actual_body_sha256") != APPROVED_CONTENT_SHA256:
            raise ValidationError("BYTE_VERIFIED without a body hash equal to the approved content")
    if level == "OPERATOR_ATTESTED":
        if evidence.get("repository_observed_the_send") is not False:
            raise ValidationError(
                "an attestation records what the repository did NOT observe; claiming it did "
                "would make the level meaningless"
            )
        if not str(evidence.get("what_would_be_required_for_byte_verification", "")).strip():
            raise ValidationError(
                "the record must say what stronger evidence would take, so the weaker level is a "
                "stated position rather than a shrug"
            )

    attest = record["the_attestation"]
    if not str(attest.get("actual_sender") or "").strip():
        raise ValidationError("an attested send must name the exact sender mailbox used")
    if not str(attest.get("attested_by") or "").strip():
        raise ValidationError("an attestation must name who made it")
    if attest.get("attestation_source") != "OPERATOR_STATEMENT":
        raise ValidationError(
            "an attestation's source is the operator's statement and nothing else"
        )
    if attest.get("message_id_status") not in MESSAGE_ID_STATES:
        raise ValidationError("the message id status is not in the vocabulary")
    if attest.get("message_id_status") == "NOT_AVAILABLE" and attest.get("message_id") is not None:
        raise ValidationError("a message id is recorded while its status says none is available")
    if (
        attest.get("message_id_status") == "RECORDED"
        and not str(attest.get("message_id") or "").strip()
    ):
        raise ValidationError("a RECORDED message id must be present")
    if not str(attest.get("why_no_message_id", "")).strip() and attest.get("message_id") is None:
        raise ValidationError(
            "an absent message id must say why, so it is not read as an oversight"
        )

    once = record["exactly_once"]
    if once.get("send_count") != 1:
        raise ValidationError("one approval authorises exactly one send")
    if once.get("duplicate_send_count") != 0:
        raise ValidationError("a duplicate is reported as DUPLICATE_DISPATCH_OCCURRED")
    if attest.get("send_count") != once.get("send_count"):
        raise ValidationError("the attestation and the exactly-once section disagree on the count")
    for flag in ("resent_during_this_mission", "follow_up_sent"):
        if once.get(flag) is not False:
            raise ValidationError(f"{flag} must be false. A later message is a NEW outbound action")

    timing = record["timing_consistency"]
    if timing.get("approval_not_before") != APPROVAL_LOWER_BOUND_UTC:
        raise ValidationError("the approval's lower bound is not the one that was established")
    if timing.get("mission_1_66_merged_at") != MISSION_1_66_MERGED_UTC:
        raise ValidationError("the recorded Mission 1.66 merge time is not the one git reports")
    if attest.get("sent_at_utc") != timing.get("attested_send_utc"):
        raise ValidationError("the attestation and the timing check disagree on the send time")
    if timing.get("attested_send_utc", "") <= APPROVAL_LOWER_BOUND_UTC:
        raise ValidationError("the attested send precedes the approval it claims to execute")
    for flag in ("send_after_approval", "send_after_mission_1_66_reported_awaiting", "consistent"):
        if timing.get(flag) is not True:
            raise ValidationError(f"timing check {flag} is false")
    if not str(timing.get("what_this_does_not_establish", "")).strip():
        raise ValidationError(
            "a possible time is not a time that happened, and the record must say so rather than "
            "letting a consistency check read as confirmation"
        )


def _validate_matching(record: dict) -> None:
    m = record["execution_matching"]
    for field, approved in (
        ("recipient", APPROVED_RECIPIENT),
        ("channel", APPROVED_CHANNEL),
        ("subject", APPROVED_SUBJECT),
    ):
        if m[field].get("approved") != approved:
            raise ValidationError(f"the record restates the approved {field} wrongly")
        if m[field].get("actual") != approved:
            raise ValidationError(
                f"the attested {field} is not the approved one. The approved action was not "
                f"executed as approved, and the envelope is not repaired to match"
            )
        if m[field].get("verdict") != "MATCH":
            raise ValidationError(f"{field} does not match and the outcome is not divergence")
    if m["send_count"].get("actual") != 1:
        raise ValidationError("the matched send count is not one")

    sender = m["sender"]
    if sender.get("approved") != APPROVED_SENDER_PLACEHOLDER:
        raise ValidationError("the record restates the approved sender placeholder wrongly")
    if sender.get("verdict") != "ALLOWED_BY_APPROVED_PLACEHOLDER":
        raise ValidationError(
            "the sender is admitted only because the envelope bound a placeholder rather than a "
            "mailbox, and the record must say which"
        )
    if not str(sender.get("why_this_is_not_a_divergence", "")).strip():
        raise ValidationError("the record must say why a named sender is not a divergence")
    if sender.get("actual") != record["the_attestation"].get("actual_sender"):
        raise ValidationError("the matching section and the attestation disagree on the sender")

    if m.get("verdict") != "EXECUTION_MATCHES_APPROVED_DISPATCH":
        raise ValidationError("every field matches and the overall verdict says otherwise")

    cost = record["the_stated_cost_that_was_actually_paid"]
    for field in ("what_was_stated", "what_that_means_now", "why_it_is_worth_recording"):
        if not str(cost.get(field, "")).strip():
            raise ValidationError(f"the record must state {field}")


def _validate_boundaries(record: dict) -> None:
    frozen = record["the_frozen_envelope_is_untouched"]
    for flag in (
        "envelope_edited",
        "binding_fields_edited",
        "sender_placeholder_replaced",
        "approval_written_into_the_envelope",
        "enquiry_content_edited",
        "envelope_marked_sent",
    ):
        if frozen.get(flag) is not False:
            raise ValidationError(f"{flag} must be false")

    reply = record["provider_response"]
    if reply.get("status") not in RESPONSE_STATES:
        raise ValidationError("the provider response status is not in the vocabulary")
    if reply.get("mailbox_searched") is not False:
        raise ValidationError("the mailbox was not to be searched during this mission")
    # A claim about what is IN a mailbox requires having looked in it. Without
    # this, a record could report CHECKED_NONE_FOUND -- materially stronger than
    # NOT_CHECKED -- while recording that no search happened.
    if reply.get("status") in ("CHECKED_NONE_FOUND", "RECEIVED_PENDING_REVIEW") and not reply.get(
        "mailbox_searched"
    ):
        raise ValidationError(
            f"status {reply.get('status')!r} asserts what is in the mailbox while the record says "
            "it was never searched. Not checked and nothing there are different facts"
        )
    if reply.get("status") == "NOT_CHECKED_AFTER_DISPATCH" and reply.get("is_not") != (
        "NO_RESPONSE_EXISTS"
    ):
        raise ValidationError(
            "an unchecked mailbox establishes NOT_CHECKED and never NO_RESPONSE_EXISTS, and the "
            "record must name the claim it is declining to make"
        )
    for flag in ("response_frozen", "response_interpreted"):
        if reply.get(flag) is not False:
            raise ValidationError(f"{flag} must be false. Reviewing a reply is a separate mission")

    apparatus = record["apparatus_state_unchanged"]
    for name in ("ONYPHE", "Netlas", "LeakIX", "The Shadowserver Foundation"):
        if apparatus[name].get("changed") is not False:
            raise ValidationError(
                f"{name} is recorded as changed, and a SENT question is not an answer"
            )
    if apparatus["ONYPHE"].get("B2") != "PARTIAL":
        raise ValidationError("ONYPHE B2 stays PARTIAL until a reviewed first-party response")
    if apparatus["ONYPHE"].get("port_22_membership") != "UNKNOWN":
        raise ValidationError("the datascan port membership stays UNKNOWN")
    if apparatus.get("qualified_count") != 0:
        raise ValidationError("no apparatus qualifies")
    if apparatus.get("pair_analysis_ready") is not False:
        raise ValidationError("pair analysis is not ready with zero qualified apparatuses")

    netlas = record["netlas_untouched"]
    if netlas.get("sent") is not False:
        raise ValidationError("the Netlas enquiry is recorded as sent")
    if netlas.get("recipient") != "NOT_ESTABLISHED":
        raise ValidationError("a Netlas recipient appeared without an operator supplying one")
    for flag in ("address_guessed", "obfuscation_decoded", "onyphe_approval_reused_for_netlas"):
        if netlas.get(flag) is not False:
            raise ValidationError(f"{flag} must be false")

    counters = record["counters"]
    for name in (
        "emails_sent_by_this_repository",
        "connector_executions",
        "mailbox_searches",
        "follow_ups_sent",
        "netlas_enquiries_sent",
        "provider_replies_frozen",
        "provider_replies_interpreted",
        "research_data_requests",
        "measurement_queries",
        "counts_fetched",
        "host_records_fetched",
        "banners_fetched",
        "trials",
        "purchases",
        "model_calls",
        "embeddings",
        "canonical_mutations",
        "sources_registered",
        "governance_reviews_created",
        "reliability_values_assigned",
        "independence_groups_created",
        "apparatus_gates_changed",
        "pairs_compared",
        "migrations_created",
    ):
        if counters.get(name) != 0:
            raise ValidationError(f"counter {name} reads {counters.get(name)!r} and must be 0")
    if counters.get("reference_profile") != "UNCALIBRATED":
        raise ValidationError("the reference profile is not calibrated by a dispatch")
    if counters.get("problem_family") != "PARKED":
        raise ValidationError("Problem-Family stays PARKED")

    base = record["canonical_baseline_unchanged"]
    for name, expected in (
        ("raw_records", 325),
        ("normalized_records", 325),
        ("signals", 33),
        ("claims", 44),
        ("claim_revisions", 45),
        ("evidence", 58),
        ("inferred_claims", 1),
        ("threshold_registrations", 1),
        ("claim_derivations", 1),
        ("proposition_evaluation_refusals", 0),
        ("reliability_assessments", 4),
        ("evidence_independence_groups", 0),
        ("registered_sources", 29),
    ):
        if base.get(name) != expected:
            raise ValidationError(
                f"baseline {name} reads {base.get(name)!r} and Mission 1.66 left {expected}"
            )
    if base.get("drift") != "none":
        raise ValidationError("the canonical baseline drifted")

    outcome = record.get("primary_outcome")
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {outcome!r}")
    if not str(record.get("primary_outcome_statement", "")).strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")
    if outcome == "ONYPHE_MANUAL_DISPATCH_ATTESTED" and record["execution_status"] != "SENT":
        raise ValidationError("outcome A claims an attested send and the status says otherwise")
    if outcome == "DUPLICATE_DISPATCH_OCCURRED" and record["exactly_once"]["send_count"] == 1:
        raise ValidationError("outcome C claims a duplicate and the count is one")

    for name, value in record["stop_condition"].items():
        if name.startswith("$") or name == "awaiting":
            continue
        if value is not False:
            raise ValidationError(f"the stop condition {name} reads {value!r} and must be false")


def _validate_no_overclaims(record: dict) -> None:
    for sentence in _prose(record):
        tokens = re.findall(r"[a-z0-9]+", sentence.lower())
        for term in OVERCLAIMS:
            if term in tokens:
                raise ValidationError(f"the record uses {term!r}: {sentence[:110]!r}")


# --------------------------------------------------------------------------- render


def render(record: dict) -> str:
    history = record["the_history_this_appends_to"]
    approved = record["the_action_that_was_approved"]
    attest = record["the_attestation"]
    evidence = record["evidence_level_and_why_it_is_not_higher"]
    matching = record["execution_matching"]
    cost = record["the_stated_cost_that_was_actually_paid"]
    timing = record["timing_consistency"]
    once = record["exactly_once"]
    reply = record["provider_response"]
    first = record["what_this_is_the_first_of"]

    lines = [
        "# ONYPHE enquiry — manual dispatch attestation",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_attestation.py`. Do not edit.",
        "",
        f"**Status: `{record['execution_status']}`.** Evidence: "
        f"**`{record['verification_basis']}`**.",
        "",
        record["primary_outcome_statement"],
        "",
        "## The history this appends to",
        "",
        _row(["state", "established by", "record"]),
        _row(["---", "---", "---"]),
    ]
    for step in history["chain"]:
        lines.append(_row([f"`{step['state']}`", step["established_by"], f"`{step['record']}`"]))
    lines += [
        "",
        history["mission_1_66_was_correct_when_it_ran"],
        "",
        history["so_mission_1_66_is_not_rewritten"],
        "",
        f"*The stale-record hazard:* {history['how_the_stale_record_is_handled']}",
        "",
        "## The attestation",
        "",
        _row(["field", "approved", "attested"]),
        _row(["---", "---", "---"]),
        _row(
            ["recipient", f"`{approved['approved_recipient']}`", f"`{attest['actual_recipient']}`"]
        ),
        _row(["channel", f"`{approved['approved_channel']}`", f"`{attest['actual_channel']}`"]),
        _row(["sender", f"`{approved['approved_sender']}`", f"`{attest['actual_sender']}`"]),
        _row(["subject", approved["approved_subject"], attest["actual_subject"]]),
        _row(["send count", str(approved["approved_send_count"]), str(attest["send_count"])]),
        _row(["sent at", "—", f"`{attest['sent_at']}`"]),
        _row(["message id", "—", f"`{attest['message_id_status']}`"]),
        "",
        f"Attested by `{attest['attested_by']}`, source `{attest['attestation_source']}`.",
        "",
        f"*On the message id:* {attest['why_no_message_id']}",
        "",
        f"**Verdict: `{matching['verdict']}`.**",
        "",
        f"*On the sender:* {matching['sender']['why_this_is_not_a_divergence']}",
        "",
        "## Why the evidence level is not higher",
        "",
        f"`{evidence['level']}`, and deliberately not `{evidence['is_not']}`.",
        "",
        f"**What byte verification would take.** {evidence['what_would_be_required_for_byte_verification']}. "
        f"Artifact imported: **{evidence['sent_message_artifact_imported']}**. Repository observed "
        f"the send: **{evidence['repository_observed_the_send']}**.",
        "",
        evidence["why_the_repository_could_not_observe_it"],
        "",
        f"**{evidence['the_asymmetry_worth_naming']}**",
        "",
        "## The stated cost that was actually paid",
        "",
        f"*Stated in Mission 1.65:* {cost['what_was_stated']}.",
        "",
        cost["what_that_means_now"],
        "",
        cost["why_it_is_worth_recording"],
        "",
        "## Timing",
        "",
        _row(["moment", "time"]),
        _row(["---", "---"]),
        _row(["approval not before", f"`{timing['approval_not_before']}`"]),
        _row(["Mission 1.66 merged", f"`{timing['mission_1_66_merged_at']}`"]),
        _row(["attested send", f"`{timing['attested_send_utc']}`"]),
        "",
        f"Consistent: **{timing['consistent']}**. {timing['what_this_does_not_establish']}",
        "",
        "## Exactly once",
        "",
        f"Send count **{once['send_count']}**, duplicates **{once['duplicate_send_count']}**.",
        "",
        once["the_rule"],
        "",
        f"*If another send is discovered:* {once['if_another_send_is_discovered']}",
        "",
        "## Provider response",
        "",
        f"Status `{reply['status']}`, which is **not** `{reply['is_not']}`.",
        "",
        reply["why_not_checked"],
        "",
        f"*When a reply arrives:* {reply['what_happens_when_a_reply_arrives']}",
        "",
        "## Apparatus state",
        "",
        _row(["apparatus", "status", "changed"]),
        _row(["---", "---", "---"]),
    ]
    for name in ("LeakIX", "Netlas", "ONYPHE", "The Shadowserver Foundation"):
        s = record["apparatus_state_unchanged"][name]
        lines.append(_row([name, f"`{s['individual']}`", str(s["changed"])]))
    lines += [
        "",
        f"Qualified `{record['apparatus_state_unchanged']['qualified_count']}`, pair analysis ready "
        f"**{record['apparatus_state_unchanged']['pair_analysis_ready']}**.",
        "",
        record["apparatus_state_unchanged"]["rule"],
        "",
        "## A first, and whose",
        "",
        first["observation"],
        "",
        f"**{first['and_it_was_not_completed_by_this_repository']}** Elapsed: {first['elapsed']}.",
        "",
        f"Awaiting: **{record['stop_condition']['awaiting']}**.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        record = validate()
    except ValidationError as error:
        print(f"REFUSED  dispatch attestation: {error}")
        return 1

    text = render(record)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the attestation matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"status   {record['execution_status']}, evidence {record['verification_basis']}")
    print(f"sender   {record['the_attestation']['actual_sender']}")
    print(f"matching {record['execution_matching']['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
