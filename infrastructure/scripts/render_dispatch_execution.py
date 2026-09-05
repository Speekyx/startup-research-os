"""Render and validate the Mission 1.66 approved-dispatch execution record.

Three records, and one rule underneath all of them:

    AN APPROVAL IS NOT AN EXECUTION.

An approval says an action may be performed. Only a performance says it was.
Once an approval exists, every field an execution record needs is already known
-- recipient, subject, body, channel -- so a record could fill itself in
completely and be entirely fictional. `validate()` is what stops that:

  - both frozen hashes are recomputed from the artifacts as stored, so an
    approval that names bytes which have since moved is refused;
  - the frozen envelope and enquiry may not be edited after approval, and the
    approval may not be written into the document it approves;
  - `SENT` requires an explicit operator confirmation and an actual sender, and
    an approval on its own can never produce it;
  - a reported execution must match the approved recipient, channel and subject,
    because the hash binds the ACTION and not merely the message;
  - one approval authorises one send, and a duplicate is reported rather than
    tidied away;
  - `BYTE_VERIFIED` requires a body hash, so an attestation cannot be promoted
    into proof;
  - a dispatch moves no apparatus gate, and a provider reply is frozen rather
    than interpreted.

    uv run python infrastructure/scripts/render_dispatch_execution.py
    uv run python infrastructure/scripts/render_dispatch_execution.py --check

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

BASELINE = DATA / "mission-1.66-baseline-v1.json"
EXECUTION = DATA / "onyphe-enquiry-dispatch-execution-v1.json"
VERDICT = DATA / "approved-dispatch-execution-v1.json"

ONYPHE_ENVELOPE = DATA / "onyphe-dispatch-envelope-v1.json"
ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
NETLAS_ENVELOPE = DATA / "netlas-dispatch-envelope-v1.json"
NETLAS_ENQUIRY_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"

APPROVED_ENVELOPE_SHA256 = "12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2"
APPROVED_CONTENT_SHA256 = "0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f"
NETLAS_APPROVED_SHA256 = "310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4"
APPROVAL_STRING = f"APPROVE MISSION 1.65 DISPATCH {APPROVED_ENVELOPE_SHA256}"

APPROVED_RECIPIENT = "contact@onyphe.io"
APPROVED_CHANNEL = "OPERATOR_MANUAL_SEND"
APPROVED_SUBJECT = "Three questions about datascan record semantics and scan configuration"

# Restated from the Mission 1.65 contract. The digest binds the ACTION.
BINDING_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "outbound_channel",
    "sender_identity",
    "subject",
    "content_version",
)

ORDER = [BASELINE, EXECUTION, VERDICT]
RENDERED = {p: p.with_suffix(".md") for p in ORDER}

EXECUTION_STATES = (
    "APPROVED_AWAITING_MANUAL_EXECUTION",
    "SENT",
    "EXECUTION_DIVERGED",
    "DUPLICATE_DISPATCH_OCCURRED",
)
BODY_VERIFICATION_STATES = (
    "NOT_APPLICABLE_NOTHING_SENT",
    "OPERATOR_ATTESTED",
    "BYTE_VERIFIED",
    "NOT_AVAILABLE",
)
MESSAGE_ID_STATES = (
    "NOT_APPLICABLE_NOTHING_SENT",
    "NOT_AVAILABLE",
    "RECORDED",
)
PRIMARY_OUTCOMES = {
    "ONYPHE_APPROVED_DISPATCH_RECORDED",
    "ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION",
    "EXECUTION_DIVERGED_FROM_APPROVED_DISPATCH",
    "DUPLICATE_DISPATCH_OCCURRED",
    "PROVIDER_RESPONSE_RECEIVED_BEFORE_EXECUTION_RECORD",
    "APPROVED_DISPATCH_ENVELOPE_HASH_MISMATCH",
    "MISSION_1_65_NOT_MERGED",
    "MISSION_1_66_BASELINE_DRIFT",
    "MISSION_1_66_CANONICAL_MUTATION",
    "APPROVED_DISPATCH_EXECUTION_BLOCKED",
}

OVERCLAIMS = ("installation", "customer", "subscription", "revenue", "adoption", "demand")


class ValidationError(Exception):
    """A Mission 1.66 record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        # A record that is not an object is a broken record, and it is refused
        # by name rather than left to fail as an attribute error three frames
        # down where the message says nothing about which file was wrong.
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


def content_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def envelope_digest(envelope: dict, content_sha: str) -> str:
    binding = {f: envelope.get(f) for f in BINDING_FIELDS}
    binding["enquiry_content_sha256"] = content_sha
    blob = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate() -> tuple[dict, ...]:
    records = tuple(_load(p) for p in ORDER)
    baseline, execution, verdict = records

    _validate_frozen_artifacts()
    _validate_baseline(baseline)
    _validate_execution(execution)
    _validate_verdict(verdict, execution)
    _validate_no_overclaims(records)
    return records


def _validate_frozen_artifacts() -> None:
    """The approval names a hash. Recompute it, or it names nothing."""
    content = content_digest(ONYPHE_ENQUIRY_MD)
    if content != APPROVED_CONTENT_SHA256:
        raise ValidationError(
            f"outcome F: the approved ONYPHE enquiry body has changed. approved "
            f"{APPROVED_CONTENT_SHA256}, computed {content}. Hard stop"
        )

    envelope = _load(ONYPHE_ENVELOPE)
    digest = envelope_digest(envelope, content)
    if digest != APPROVED_ENVELOPE_SHA256:
        raise ValidationError(
            f"outcome F: the envelope no longer binds the approved action. approved "
            f"{APPROVED_ENVELOPE_SHA256}, computed {digest}"
        )
    if envelope.get("envelope_sha256") != APPROVED_ENVELOPE_SHA256:
        raise ValidationError("the envelope records a hash that is not the approved one")
    if envelope.get("approval_string") != APPROVAL_STRING:
        raise ValidationError("the envelope's approval string is not the one that was approved")

    # §5. The frozen envelope is not edited after approval, and the approval is
    # not written into the document it approves.
    if envelope.get("sender_identity_is_a_placeholder") is not True:
        raise ValidationError(
            "§4: the envelope's sender placeholder was replaced. The actual sender belongs to "
            "execution provenance, and the envelope records what was APPROVED"
        )
    if envelope.get("approval_recorded") is not False:
        raise ValidationError(
            "§5: the approval was written into the envelope. Marking a frozen document approved "
            "changes the bytes that were approved, so the approval lives in the execution record"
        )
    if envelope.get("sent") is not False or envelope.get("sent_at") is not None:
        raise ValidationError(
            "§5: the frozen envelope records a send. It records an approval target"
        )
    if envelope.get("dispatch_count") != 0:
        raise ValidationError("§5: the frozen envelope counts a dispatch")

    # §14. Netlas is untouched.
    netlas = _load(NETLAS_ENVELOPE)
    if content_digest(NETLAS_ENQUIRY_MD) != NETLAS_APPROVED_SHA256:
        raise ValidationError("§14: the approved Netlas enquiry body has changed")
    if netlas.get("recipient_address") is not None:
        raise ValidationError(
            "§14: a Netlas recipient appeared. No address may be guessed or decoded"
        )
    if netlas.get("envelope_sha256") is not None:
        raise ValidationError("§14: a Netlas envelope hash was created for an incomplete action")
    if netlas.get("approvable") is not False:
        raise ValidationError("§14: the Netlas envelope became approvable without a recipient")


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_65_merged") is not True:
        raise ValidationError("outcome G: Mission 1.65 is not recorded as merged")
    if pre.get("verified_from_git_not_from_prompt") is not True:
        raise ValidationError(
            "the precondition must be verified from git rather than from a prompt"
        )
    if pre.get("operator_report_agrees_with_git") is not True:
        raise ValidationError(
            "the brief's reported commit disagrees with git, and git is the authority"
        )
    if pre.get("working_tree_clean") is not True:
        raise ValidationError("the working tree was not clean at the precondition check")

    rec = baseline["approved_dispatch_recomputation"]
    for flag in ("enquiry_content_matches", "envelope_matches"):
        if rec.get(flag) is not True:
            raise ValidationError(f"outcome F: {flag} is false")
    if rec.get("envelope_sha256_supplied_by_operator") != APPROVED_ENVELOPE_SHA256:
        raise ValidationError("the operator-supplied hash is not the one recorded")

    if baseline["canonical_baseline"].get("drift_from_mission_1_65") != "none":
        raise ValidationError("outcome H: the canonical baseline drifted")

    acct = baseline["request_accounting"]
    for name in (
        "RESEARCH_DATA_REQUESTS",
        "MEASUREMENT_QUERIES",
        "COUNTS_FETCHED",
        "HOST_RECORDS_FETCHED",
        "BANNERS_FETCHED",
        "FACETS_FETCHED",
        "DOWNLOADS",
        "TRIALS",
        "PURCHASES",
        "MODEL_CALLS",
        "EMBEDDINGS",
        "CONNECTOR_EXECUTIONS",
        "OUTBOUND_ENQUIRIES_SENT",
    ):
        if acct.get(name) != 0:
            raise ValidationError(f"{name} must be 0 and reads {acct.get(name)!r}")

    for name, value in baseline["canonical_mutations"].items():
        if name.startswith("$"):
            continue
        if value not in (0, 0.0, False):
            raise ValidationError(
                f"outcome I: canonical mutation {name} reads {value!r} and must be zero"
            )


def _validate_execution(execution: dict) -> None:
    status = execution.get("execution_status")
    if status not in EXECUTION_STATES:
        raise ValidationError(f"execution status {status!r} is not in the vocabulary")

    approved = execution["the_action_that_was_approved"]
    if approved.get("dispatch_envelope_sha256") != APPROVED_ENVELOPE_SHA256:
        raise ValidationError("the execution record names an envelope hash that was not approved")
    if approved.get("enquiry_content_sha256") != APPROVED_CONTENT_SHA256:
        raise ValidationError("the execution record names a content hash that was not approved")
    if approved.get("approved_recipient") != APPROVED_RECIPIENT:
        raise ValidationError("the execution record restates the approved recipient wrongly")
    if approved.get("approved_channel") != APPROVED_CHANNEL:
        raise ValidationError("the execution record restates the approved channel wrongly")
    if approved.get("approved_subject") != APPROVED_SUBJECT:
        raise ValidationError("the execution record restates the approved subject wrongly")

    approval = execution["operator_approval"]
    if approval.get("exact_string") != APPROVAL_STRING:
        raise ValidationError("the recorded approval string is not the one the operator gave")
    if approval.get("names_envelope_sha256") != APPROVED_ENVELOPE_SHA256:
        raise ValidationError("the recorded approval names a different envelope")
    if approval.get("hash_recomputed_and_matches") is not True:
        raise ValidationError("an approval may not be recorded without recomputing what it names")
    if not str(approval.get("operator", "")).strip():
        raise ValidationError("an approval must name who gave it")
    if approval.get("source") != "OPERATOR_INTERACTION":
        raise ValidationError("an approval's source must be the operator")
    if not str(approval.get("approval_is_not_execution", "")).strip():
        raise ValidationError(
            "§13: the record must state that an approval is not dispatch evidence, because that is "
            "the one confusion this record exists to prevent"
        )

    ex = execution["execution"]
    confirmation = execution["operator_confirmation"]
    confirmed = confirmation.get("CONFIRMATION_GIVEN") is True

    # An approval can never produce a send.
    if ex.get("SENT") is True and not confirmed:
        raise ValidationError(
            "§3: SENT recorded with no explicit operator confirmation. An approval says an action "
            "MAY be performed; only a performance says it WAS"
        )
    if ex.get("SENT") is True and status == "APPROVED_AWAITING_MANUAL_EXECUTION":
        raise ValidationError("a record cannot be awaiting execution and sent at once")

    if status == "APPROVED_AWAITING_MANUAL_EXECUTION":
        if ex.get("SENT") is not False:
            raise ValidationError("an awaiting record may not be marked sent")
        for f in (
            "actual_recipient",
            "actual_channel",
            "actual_sender",
            "actual_subject",
            "sent_at",
            "message_id",
        ):
            if ex.get(f) is not None:
                raise ValidationError(
                    f"§3: {f} is populated on a record that reports no send. Filling execution "
                    "fields from the approval is describing a send that was only permitted"
                )
        if ex.get("send_count") != 0:
            raise ValidationError("an awaiting record counts a send")
        if ex.get("body_post_send_verification") != "NOT_APPLICABLE_NOTHING_SENT":
            raise ValidationError("nothing was sent, so no body was verified after sending")
        if confirmed:
            raise ValidationError(
                "the record reports an operator confirmation and still says nothing was sent"
            )
        if not confirmation.get("what_would_satisfy_it"):
            raise ValidationError(
                "a record awaiting a confirmation must say what would satisfy it, so the operator "
                "is not left guessing what to report"
            )

    if status in ("SENT", "DUPLICATE_DISPATCH_OCCURRED", "EXECUTION_DIVERGED"):
        if not confirmed:
            raise ValidationError(
                "§2: an execution may not be recorded without operator confirmation"
            )
        if not str(ex.get("actual_sender") or "").strip():
            raise ValidationError(
                "§2: a recorded execution must name the exact sender mailbox used. The envelope's "
                "placeholder is what was approved, not what was used"
            )
        if not ex.get("sent_at") and ex.get("message_id_status") not in MESSAGE_ID_STATES:
            raise ValidationError("a recorded execution must classify its message id")

    if status == "SENT":
        if ex.get("SENT") is not True:
            raise ValidationError("a SENT record must record the send")
        if ex.get("actual_recipient") != APPROVED_RECIPIENT:
            raise ValidationError(
                "§10: the actual recipient is not the approved one. The approved action was not "
                "executed as approved, and the envelope is not repaired to match"
            )
        if ex.get("actual_channel") != APPROVED_CHANNEL:
            raise ValidationError(
                "§11: the actual channel is not the approved one. A matching body and recipient do "
                "not make an automated send the approved action, because the channel is bound"
            )
        if ex.get("actual_subject") != APPROVED_SUBJECT:
            raise ValidationError("§9: the subject was changed, so this is not the approved action")
        if ex.get("send_count") != 1:
            raise ValidationError("§12: one approval authorises exactly one send")
        if ex.get("duplicate_send_count") != 0:
            raise ValidationError("§12: a duplicate is reported as DUPLICATE_DISPATCH_OCCURRED")

    verification = ex.get("body_post_send_verification")
    if verification not in BODY_VERIFICATION_STATES:
        raise ValidationError(f"body verification state {verification!r} is not in the vocabulary")
    if verification == "BYTE_VERIFIED" and ex.get("actual_body_sha256") != APPROVED_CONTENT_SHA256:
        raise ValidationError(
            "§8: BYTE_VERIFIED without a body hash equal to the approved content hash. An "
            "attestation is not proof and may not be promoted into one"
        )
    if ex.get("message_id_status") not in MESSAGE_ID_STATES:
        raise ValidationError("the message id status is not in the vocabulary")
    if ex.get("message_id_status") == "RECORDED" and not str(ex.get("message_id") or "").strip():
        raise ValidationError("a RECORDED message id must be present")

    frozen = execution["the_frozen_envelope_was_not_mutated"]
    for flag in (
        "envelope_edited",
        "binding_fields_edited",
        "sender_placeholder_replaced_in_envelope",
        "approval_written_into_the_envelope",
        "enquiry_content_edited",
    ):
        if frozen.get(flag) is not False:
            raise ValidationError(f"§5: {flag} must be false")

    connector = execution["no_connector_was_used"]
    if connector.get("connector_executions") != 0:
        raise ValidationError(
            "§19: the connector was invoked, and the envelope binds a manual send"
        )

    reply = execution["provider_response"]
    if reply.get("response_interpreted") is not False:
        raise ValidationError(
            "§16: a provider reply was interpreted. Freezing is this mission's job and reviewing is "
            "Mission 1.67's"
        )
    if reply.get("follow_up_sent") is not False:
        raise ValidationError("§18: a follow-up is a new outbound action needing its own approval")
    if reply.get("response_received") is True and reply.get("response_frozen") is not True:
        raise ValidationError("§17: a received reply must be preserved verbatim")
    if reply.get("response_received") is False and reply.get("response_frozen") is True:
        raise ValidationError("a reply cannot be frozen without having been received")
    if (
        reply.get("operator_mailbox_searched") is not False
        and reply.get("response_received") is False
    ):
        raise ValidationError(
            "a mailbox search that found nothing establishes more than this record claims; say so"
        )

    apparatus = execution["apparatus_state_unchanged"]
    for name in ("ONYPHE", "Netlas", "LeakIX", "The Shadowserver Foundation"):
        if apparatus[name].get("changed") is not False:
            raise ValidationError(
                f"§15: {name} is recorded as changed, and a dispatch moves no gate"
            )
    if apparatus["ONYPHE"].get("B2") != "PARTIAL":
        raise ValidationError("§15: ONYPHE B2 stays PARTIAL until a reviewed first-party response")
    if apparatus.get("qualified_count") != 0:
        raise ValidationError("§15: no apparatus qualifies")
    if apparatus.get("pair_analysis_ready") is not False:
        raise ValidationError("§15: pair analysis is not ready with zero qualified apparatuses")


def _validate_verdict(verdict: dict, execution: dict) -> None:
    outcome = verdict.get("primary_outcome")
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {outcome!r}")
    if not str(verdict.get("primary_outcome_statement", "")).strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")

    status = execution["execution_status"]
    if outcome == "ONYPHE_APPROVED_DISPATCH_RECORDED" and status != "SENT":
        raise ValidationError(
            "outcome A claims the approved action was performed while the execution record does "
            "not. Do not force A"
        )
    if outcome == "ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION" and status != (
        "APPROVED_AWAITING_MANUAL_EXECUTION"
    ):
        raise ValidationError("outcome B requires the execution record to be awaiting execution")
    if outcome == "DUPLICATE_DISPATCH_OCCURRED" and status != "DUPLICATE_DISPATCH_OCCURRED":
        raise ValidationError("outcome D requires the execution record to report a duplicate")

    integrity = verdict["integrity_of_the_approved_artifacts"]
    for flag in ("enquiry_content_matches", "envelope_matches", "operator_supplied_hash_matches"):
        if integrity.get(flag) is not True:
            raise ValidationError(f"{flag} is false and the outcome is not F")
    for flag in (
        "envelope_edited_since_approval",
        "enquiry_edited_since_approval",
        "netlas_enquiry_edited",
    ):
        if integrity.get(flag) is not False:
            raise ValidationError(f"§5: {flag} must be false")

    netlas = verdict["netlas_untouched"]
    if netlas.get("sent") is not False:
        raise ValidationError("§20: the Netlas enquiry is recorded as sent")
    if netlas.get("recipient") != "NOT_ESTABLISHED":
        raise ValidationError("§14: a Netlas recipient appeared without an operator supplying one")
    for flag in ("address_guessed", "obfuscation_decoded", "onyphe_approval_reused_for_netlas"):
        if netlas.get(flag) is not False:
            raise ValidationError(f"§14: {flag} must be false")

    counters = verdict["counters"]
    for name in (
        "outbound_enquiries_sent",
        "connector_executions",
        "follow_ups_sent",
        "netlas_enquiries_sent",
        "duplicate_sends",
        "provider_replies_interpreted",
        "research_data_requests",
        "measurement_queries",
        "counts_fetched",
        "host_records_fetched",
        "banners_fetched",
        "facets_fetched",
        "downloads",
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

    # An unsent enquiry cannot have produced a reply. Collapsed by hand rather
    # than mechanically: Mission 1.63 found a mechanical collapse that folded a
    # sibling check inside a `raise`, leaving something that looked like a guard
    # and could never fire.
    if (
        outcome == "ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION"
        and counters.get("provider_replies_frozen") != 0
    ):
        raise ValidationError("a reply cannot answer a dispatch that has not happened")

    states = verdict["apparatus_states_unchanged"]
    for name in ("Netlas", "ONYPHE", "LeakIX", "The Shadowserver Foundation"):
        if name not in states:
            raise ValidationError(f"§15: the verdict omits {name}")
        if states[name].get("changed") is not False:
            raise ValidationError(f"§15: {name} is recorded as changed")
    if states.get("qualified_count") != 0:
        raise ValidationError("no apparatus qualifies")
    if states.get("pair_analysis_ready") is not False:
        raise ValidationError("pair analysis is not ready")

    pair = verdict["no_pair_work_was_performed"]
    for flag in (
        "same_frame_evaluated",
        "vantage_compatibility_evaluated",
        "lineage_independence_evaluated",
        "shared_measurement_upstream_evaluated",
        "same_target_proposition_evaluated",
        "threshold_preregistrability_evaluated",
    ):
        if pair.get(flag) is not False:
            raise ValidationError(f"{flag} must be false")
    for counter in ("pairs_compared", "pairs_ranked", "pairs_selected"):
        if pair.get(counter) != 0:
            raise ValidationError(f"{counter} must be 0")

    for name, value in verdict["stop_condition"].items():
        if name.startswith("$") or name == "awaiting":
            continue
        if value is not False:
            raise ValidationError(f"the stop condition {name} reads {value!r} and must be false")


def _validate_no_overclaims(records: tuple[dict, ...]) -> None:
    for record in records:
        for sentence in _prose(record):
            tokens = re.findall(r"[a-z0-9]+", sentence.lower())
            for term in OVERCLAIMS:
                if term in tokens:
                    raise ValidationError(
                        f"a record uses {term!r}. Offending sentence: {sentence[:110]!r}"
                    )


# --------------------------------------------------------------------------- render


def render_baseline(record: dict) -> str:
    pre = record["repository_precondition"]
    rec = record["approved_dispatch_recomputation"]
    base = record["canonical_baseline"]
    acct = record["request_accounting"]
    lines = [
        "# Mission 1.66 — baseline",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_execution.py`. Do not edit.",
        "",
        f"**Mission:** {record['mission']}  ",
        f"**Recorded:** {record['recorded_at']}",
        "",
        "## Precondition",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["Mission 1.65 merged", str(pre["mission_1_65_merged"])]),
        _row(["pull request", f"#{pre['pull_request']} {pre['pull_request_state']}"]),
        _row(["merge commit", f"`{pre['merge_commit_short']}`"]),
        _row(["operator report agrees with git", str(pre["operator_report_agrees_with_git"])]),
        _row(["working tree clean", str(pre["working_tree_clean"])]),
        _row(["migration head", f"`{pre['migration_head']}`"]),
        _row(["drift", f"**{base['drift_from_mission_1_65']}**"]),
        "",
        pre["$note"],
        "",
        "## The approved action, recomputed",
        "",
        _row(["hash", "recomputed", "matches"]),
        _row(["---", "---", "---"]),
        _row(
            [
                "enquiry content",
                f"`{rec['enquiry_content_sha256_recomputed']}`",
                str(rec["enquiry_content_matches"]),
            ]
        ),
        _row(
            [
                "dispatch envelope",
                f"`{rec['envelope_sha256_recomputed']}`",
                str(rec["envelope_matches"]),
            ]
        ),
        "",
        f"`{rec['verdict']}` over {rec['hashing_boundary']}.",
        "",
        rec["why_recomputed_rather_than_read"],
        "",
        "## What this mission may and may not do",
        "",
    ]
    lines += [f"- **may** — {i}" for i in record["what_this_mission_may_and_may_not_do"]["may"]]
    lines += [
        f"- **may not** — {i}" for i in record["what_this_mission_may_and_may_not_do"]["may_not"]
    ]
    lines += [
        "",
        "## What did not happen",
        "",
        "```",
        f"measurement queries {acct['MEASUREMENT_QUERIES']}"
        f"    counts {acct['COUNTS_FETCHED']}"
        f"    hosts {acct['HOST_RECORDS_FETCHED']}",
        f"trials {acct['TRIALS']}"
        f"    purchases {acct['PURCHASES']}"
        f"    enquiries sent {acct['OUTBOUND_ENQUIRIES_SENT']}"
        f"    connector executions {acct['CONNECTOR_EXECUTIONS']}",
        "```",
        "",
        f"*No mailbox was searched.* {acct['why_no_mailbox_search']}",
        "",
    ]
    return "\n".join(lines)


def render_execution(record: dict) -> str:
    approved = record["the_action_that_was_approved"]
    approval = record["operator_approval"]
    ex = record["execution"]
    confirmation = record["operator_confirmation"]
    cannot = record["the_repository_cannot_verify_a_manual_send"]
    checks = record["integrity_checks_that_will_apply_when_a_send_is_reported"]
    frozen = record["the_frozen_envelope_was_not_mutated"]
    lines = [
        "# ONYPHE enquiry — dispatch execution record",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_execution.py`. Do not edit.",
        "",
        f"**Execution status: `{record['execution_status']}`.** Sent: **{ex['SENT']}**.",
        "",
    ]
    # A later mission may append a forward pointer. It never edits what this
    # record says; it says which record continues it, so a reader cannot take a
    # historical state for the current one.
    superseded = record.get("superseded_by")
    if superseded:
        lines += [
            f"> **Superseded by `{superseded['record']}`**, which records "
            f"*{superseded['state_it_records']}*. "
            f"{superseded['what_this_record_still_says']}",
            "",
        ]
    lines += [
        "## The action that was approved",
        "",
        _row(["field", "value"]),
        _row(["---", "---"]),
        _row(["envelope", f"`{approved['dispatch_envelope']}`"]),
        _row(["envelope sha256", f"`{approved['dispatch_envelope_sha256']}`"]),
        _row(["content sha256", f"`{approved['enquiry_content_sha256']}`"]),
        _row(["recipient", f"`{approved['approved_recipient']}`"]),
        _row(["channel", f"`{approved['approved_channel']}`"]),
        _row(["sender", f"`{approved['approved_sender']}`"]),
        _row(["subject", approved["approved_subject"]]),
        "",
        "## The approval",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["given", f"**{approval['APPROVAL_GIVEN']}**"]),
        _row(["operator", f"`{approval['operator']}`"]),
        _row(["source", f"`{approval['source']}`"]),
        _row(["hash recomputed and matches", str(approval["hash_recomputed_and_matches"])]),
        _row(["approval time", f"`{approval['approval_time']}`"]),
        _row(["not before", f"`{approval['approval_time_lower_bound']}`"]),
        "",
        f"    {approval['exact_string']}",
        "",
        f"*Why no exact time.* {approval['why_the_exact_time_is_not_recorded']}",
        "",
        f"**{approval['approval_is_not_execution']}**",
        "",
        "**It does not authorise:** " + "; ".join(approval["what_it_does_not_authorise"]) + ".",
        "",
        "## The execution",
        "",
        _row(["field", "value"]),
        _row(["---", "---"]),
        _row(["SENT", f"**{ex['SENT']}**"]),
        _row(["actual recipient", str(ex["actual_recipient"])]),
        _row(["actual channel", str(ex["actual_channel"])]),
        _row(["actual sender", str(ex["actual_sender"])]),
        _row(["sent at", str(ex["sent_at"])]),
        _row(["message id", f"`{ex['message_id_status']}`"]),
        _row(["send count", str(ex["send_count"])]),
        _row(["body verification", f"`{ex['body_post_send_verification']}`"]),
        "",
        ex["why_every_field_is_null"],
        "",
        "## What would satisfy the confirmation",
        "",
    ]
    lines += [f"- {i}" for i in confirmation["what_would_satisfy_it"]]
    lines += [
        "",
        "Optional, and optional deliberately: "
        + ", ".join(confirmation["optional_and_not_required"])
        + f". {confirmation['why_optional_stays_optional']}",
        "",
        "## The repository cannot verify a manual send",
        "",
        cannot["observation"],
        "",
        cannot["consequence"],
        "",
        f"*Which is why:* {cannot['which_is_why']}",
        "",
        f"*The shape it shares with earlier missions:* {cannot['the_shape_it_shares_with_earlier_missions']}",
        "",
        "## Integrity checks, frozen before any send",
        "",
        _row(["field", "must equal", "divergence code"]),
        _row(["---", "---", "---"]),
        _row(
            [
                "recipient",
                f"`{checks['recipient_must_equal']}`",
                f"`{checks['recipient_divergence_code']}`",
            ]
        ),
        _row(
            [
                "channel",
                f"`{checks['channel_must_equal']}`",
                f"`{checks['channel_divergence_code']}`",
            ]
        ),
        _row(["subject", checks["subject_must_equal"], f"`{checks['subject_divergence_code']}`"]),
        _row(["send count", "1", f"`{checks['duplicate_code']}`"]),
        "",
        checks["why_a_matching_body_does_not_rescue_a_wrong_channel"],
        "",
        f"*On divergence:* {checks['on_divergence']} {checks['no_automatic_cleanup_exists']}",
        "",
        "## The frozen envelope was not mutated",
        "",
        frozen["why_the_approval_is_not_written_into_the_envelope"],
        "",
        f"**A guard that now does a second job.** {frozen['a_guard_that_now_does_a_second_job']}",
        "",
        f"*Where the actual sender will go:* {frozen['where_the_actual_sender_will_go']}",
        "",
        "## The connector that was not used",
        "",
        record["no_connector_was_used"]["the_temptation_named"],
        "",
        f"*Who may close this:* {record['no_connector_was_used']['who_may_close_this']}",
        "",
        "## Provider response",
        "",
        f"Received **{record['provider_response']['response_received']}**, "
        f"basis `{record['provider_response']['basis']}`.",
        "",
        record["provider_response"]["why_that_distinction_is_kept"],
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
        record["apparatus_state_unchanged"]["rule"],
        "",
    ]
    return "\n".join(lines)


def render_verdict(record: dict) -> str:
    two = record["the_two_facts_this_mission_keeps_apart"]
    refused = record["what_would_have_completed_the_action_and_was_refused"]
    nxt = record["next_action"]
    lines = [
        "# Approved dispatch execution",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_execution.py`. Do not edit.",
        "",
        f"**Outcome: `{record['primary_outcome']}`**",
        "",
        record["primary_outcome_statement"],
        "",
        f"**This is not a failure.** {record['this_is_not_a_failure']}",
        "",
        "## The two facts this mission keeps apart",
        "",
        _row(["fact", "means"]),
        _row(["---", "---"]),
        _row(["approval", two["approval"]]),
        _row(["execution", two["execution"]]),
        "",
        two["why_they_are_easy_to_merge"],
        "",
        f"**{two['the_general_rule']}**",
        "",
        f"*And the new half:* {two['and_the_new_half']}",
        "",
        "Earlier instances:",
        "",
    ]
    lines += [f"- {i}" for i in two["earlier_instances"]]
    lines += [
        "",
        "## What would have completed the action, and was refused",
        "",
        f"**The available route.** {refused['the_available_route']}",
        "",
        f"**Why it was refused.** {refused['why_it_was_refused']}",
        "",
        f"**What it would have looked like.** {refused['what_it_would_have_looked_like']}",
        "",
        f"**How it could be authorised.** {refused['how_it_could_be_authorised']}",
        "",
        "## Why this outcome and not another",
        "",
    ]
    for key, text in record["why_this_outcome_and_not_another"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        "## Netlas, untouched",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["content approval", f"`{record['netlas_untouched']['content_approval']}`"]),
        _row(["recipient", f"`{record['netlas_untouched']['recipient']}`"]),
        _row(["envelope state", f"`{record['netlas_untouched']['envelope_state']}`"]),
        _row(["sent", str(record["netlas_untouched"]["sent"])]),
        "",
        record["netlas_untouched"]["the_rule"],
        "",
        "## Apparatus states, unchanged",
        "",
        _row(["apparatus", "status", "changed"]),
        _row(["---", "---", "---"]),
    ]
    for name in ("LeakIX", "Netlas", "ONYPHE", "The Shadowserver Foundation"):
        s = record["apparatus_states_unchanged"][name]
        lines.append(_row([name, f"`{s['individual']}`", str(s["changed"])]))
    lines += [
        "",
        f"Qualified `{record['apparatus_states_unchanged']['qualified_count']}`, pair analysis "
        f"ready **{record['apparatus_states_unchanged']['pair_analysis_ready']}**.",
        "",
        record["apparatus_states_unchanged"]["rule"],
        "",
        "## Next",
        "",
        f"**`{nxt['checkpoint']}`.** The next action is outside this repository: "
        f"{nxt['who_acts_next']} {nxt['what_they_do']}.",
        "",
        f"Packet: `{nxt['packet']}`",
        "",
        "What to report back:",
        "",
    ]
    lines += [f"- {i}" for i in nxt["what_to_report_back"]]
    lines += [
        "",
        f"Then: {nxt['then']}",
        "",
        f"*Do not poll.* {nxt['do_not_poll']}",
        "",
        f"*Netlas is independent.* {nxt['netlas_is_independent']}",
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
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  dispatch execution: {error}")
        return 1

    baseline, execution, verdict = records
    rendered = {
        RENDERED[BASELINE]: render_baseline(baseline),
        RENDERED[EXECUTION]: render_execution(execution),
        RENDERED[VERDICT]: render_verdict(verdict),
    }

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(f"ok       {len(rendered)} execution documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    print(f"outcome  {verdict['primary_outcome']}")
    print(f"status   {execution['execution_status']}")
    print(f"approval verified against {APPROVED_ENVELOPE_SHA256}")
    print(
        f"sent     {execution['execution']['SENT']}, send_count {execution['execution']['send_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
