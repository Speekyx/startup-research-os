"""Render and validate the Mission 1.65 dual-enquiry dispatch preparation.

Six records, one frozen enquiry, and one dispatch packet generated from that
enquiry rather than retyped.

`validate()` enforces the rule this mission freezes:

    CONTENT_APPROVAL_IS_NOT_DISPATCH_APPROVAL

and the three gates that stay separate — content, recipient, channel — plus:

  - the Netlas approved body still hashes to the approved value;
  - no recipient is guessed, and the check is on PROVENANCE rather than on the
    spelling of the address, because a correctly retrieved mailbox may happen to
    look conventional while a guessed one may not;
  - an envelope with no recipient carries no hash, because a hash is an approval
    handle for an action;
  - an envelope hash binds content, recipient, channel and sender;
  - a connector being present in the runtime is not channel authorisation;
  - the ONYPHE enquiry asks nothing already answered and requests no data,
    access, trial or price;
  - nothing is marked sent.

    uv run python infrastructure/scripts/render_dispatch_envelope.py
    uv run python infrastructure/scripts/render_dispatch_envelope.py --check

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

BASELINE = DATA / "mission-1.65-baseline-v1.json"
ENQUIRY = DATA / "onyphe-technical-methodology-enquiry-v1.json"
CONTRACT = DATA / "outbound-dispatch-envelope-contract-v1.json"
NETLAS_ENV = DATA / "netlas-dispatch-envelope-v1.json"
ONYPHE_ENV = DATA / "onyphe-dispatch-envelope-v1.json"
READINESS = DATA / "dual-enquiry-readiness-v1.json"

NETLAS_ENQUIRY_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"
ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
ONYPHE_PACKET_MD = DATA / "onyphe-enquiry-dispatch-packet-v1.md"

NETLAS_APPROVED_SHA256 = "310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4"

ORDER = [BASELINE, ENQUIRY, CONTRACT, NETLAS_ENV, ONYPHE_ENV, READINESS]
RENDERED = {p: p.with_suffix(".md") for p in ORDER}

ENVELOPE_STATES = (
    "INCOMPLETE_RECIPIENT",
    "INCOMPLETE_CHANNEL",
    "READY_FOR_OPERATOR_APPROVAL",
    "APPROVED_NOT_SENT",
    "SENT",
    "SUPERSEDED",
)
CHANNEL_STATES = (
    "NOT_EVALUATED",
    "AVAILABLE_NOT_AUTHORIZED",
    "OPERATOR_MANUAL_SEND",
    "AUTHORIZED_CONNECTOR",
    "BLOCKED",
)
BINDING_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "outbound_channel",
    "sender_identity",
    "subject",
    "content_version",
)
REQUIRED_ENVELOPE_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "recipient_provenance",
    "sender_identity",
    "outbound_channel",
    "channel_authorization_basis",
    "subject",
    "content_version",
)

PRIMARY_OUTCOMES = {
    "DUAL_ENQUIRIES_FROZEN_DISPATCH_ENVELOPES_READY",
    "NETLAS_RECIPIENT_PENDING_ONYPHE_ENQUIRY_FROZEN",
    "ONYPHE_CONTACT_PENDING_NETLAS_ENVELOPE_READY",
    "DUAL_CONTACT_CHANNELS_PENDING_ENQUIRIES_FROZEN",
    "OUTBOUND_CHANNEL_AUTHORIZATION_NOT_ESTABLISHED",
    "APPROVED_ENQUIRY_HASH_MISMATCH",
    "ONYPHE_ENQUIRY_SEMANTIC_SCOPE_CONFLICT",
    "MISSION_1_64_NOT_MERGED",
    "MISSION_1_65_BASELINE_DRIFT",
    "MISSION_1_65_CANONICAL_MUTATION",
    "DUAL_ENQUIRY_PREPARATION_BLOCKED",
}

# An enquiry may ask about method. It may not ask for the thing itself.
FORBIDDEN_ASKS = (
    "how many hosts",
    "send us a sample",
    "provide a count",
    "free trial",
    "trial account",
    "evaluation account",
    "pricing",
    "a quote",
    "api key",
    "give us access",
    "a demo",
)

OVERCLAIMS = ("installation", "customer", "subscription", "revenue", "adoption", "demand")


class ValidationError(Exception):
    """A Mission 1.65 record claims something the rules do not permit."""


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


def content_digest(path: pathlib.Path) -> str:
    """The documented boundary: the rendered file's raw bytes as stored."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def envelope_digest(envelope: dict, content_sha: str) -> str:
    """sha256 over canonical JSON of the binding fields.

    Binds the ACTION: content, recipient, channel, sender. Excludes when it was
    recorded and how it was established, which are provenance about the action
    rather than parts of it.
    """
    binding = {f: envelope.get(f) for f in BINDING_FIELDS}
    binding["enquiry_content_sha256"] = content_sha
    blob = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate() -> tuple[dict, ...]:
    records = tuple(_load(p) for p in ORDER)
    baseline, enquiry, contract, netlas, onyphe, readiness = records

    _validate_baseline(baseline)
    _validate_enquiry(enquiry)
    _validate_contract(contract)
    _validate_netlas_envelope(netlas)
    _validate_onyphe_envelope(onyphe, enquiry)
    _validate_readiness(readiness, netlas, onyphe)
    _validate_no_overclaims(records)
    return records


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_64_merged") is not True:
        raise ValidationError("Mission 1.64 is not recorded as merged")
    if pre.get("verified_from_git_not_from_prompt") is not True:
        raise ValidationError(
            "the precondition must be verified from git rather than from a prompt"
        )

    approved = baseline["netlas_approved_enquiry"]
    if approved["approved_sha256"] != NETLAS_APPROVED_SHA256:
        raise ValidationError("the recorded approved hash is not the operator's")
    live = content_digest(NETLAS_ENQUIRY_MD)
    if live != NETLAS_APPROVED_SHA256:
        raise ValidationError(
            f"§A1 / outcome F: the Netlas approved body has changed. approved "
            f"{NETLAS_APPROVED_SHA256}, computed {live}. Hard stop; do NOT send"
        )
    for flag in (
        "recipient_added",
        "sender_added",
        "channel_added",
        "wording_changed",
        "text_normalised",
        "approval_metadata_inserted_into_hashed_document",
    ):
        if approved.get(flag) is not False:
            raise ValidationError(f"§A1: {flag} must be false. The approved body is untouched")

    carried = baseline["content_approval_carried_forward"]
    if carried.get("CONTENT_APPROVED") is not True:
        raise ValidationError("the existing content approval is recorded as not granted")
    for name in ("RECIPIENT_APPROVED", "CHANNEL_APPROVED", "SEND_NOW"):
        if carried.get(name) is not False:
            raise ValidationError(
                f"§A2: content approval does not imply {name}. "
                "CONTENT_APPROVAL_IS_NOT_DISPATCH_APPROVAL"
            )

    acct = baseline["request_accounting"]
    for name in (
        "RESEARCH_DATA_REQUESTS",
        "MEASUREMENT_QUERIES",
        "COUNTS_FETCHED",
        "HOST_RECORDS_FETCHED",
        "BANNERS_FETCHED",
        "TRIALS",
        "PURCHASES",
        "OUTBOUND_ENQUIRIES_SENT",
    ):
        if acct.get(name) != 0:
            raise ValidationError(f"{name} must be 0 and reads {acct.get(name)!r}")

    for name, value in baseline["canonical_mutations"].items():
        if name.startswith("$"):
            continue
        if value not in (0, 0.0, False):
            raise ValidationError(f"canonical mutation {name} reads {value!r} and must be zero")


def _validate_enquiry(enquiry: dict) -> None:
    if enquiry.get("status") != "AWAITING_OPERATOR_DISPATCH_APPROVAL":
        raise ValidationError(f"the enquiry's status reads {enquiry.get('status')!r}")
    if enquiry["delivery"].get("sent") is not False:
        raise ValidationError("the enquiry records itself as sent, and nothing was sent")
    if enquiry["delivery"].get("sent_at") is not None:
        raise ValidationError(
            "this repository may prepare a message and may never imply it was delivered"
        )
    if enquiry["delivery"].get("recipient_is_recorded_outside_this_document") is not True:
        raise ValidationError(
            "§B6: a recipient inside the hashed body changes the bytes the hash is computed over"
        )

    prov = enquiry["provenance_of_the_three_questions"]
    if prov.get("question_count") != 3:
        raise ValidationError("§B5: exactly three core questions")
    if prov.get("questions_added_beyond_the_frozen_three") != 0:
        raise ValidationError("§B: no fourth question may be added to the frozen three")
    if len(enquiry["questions"]) != 3:
        raise ValidationError(f"the enquiry carries {len(enquiry['questions'])} questions")
    if [q["n"] for q in enquiry["questions"]] != [1, 2, 3]:
        raise ValidationError("the questions must be numbered 1 to 3")
    for q in enquiry["questions"]:
        for field in ("topic", "question", "why_we_ask", "unanswered_by", "gate"):
            if not q.get(field, "").strip():
                raise ValidationError(f"enquiry question {q['n']} states no {field}")

    # The sendable body may not ask for data, access, a trial or a price.
    sendable = [enquiry["subject"], enquiry["preamble"], enquiry["closing"]]
    for q in enquiry["questions"]:
        sendable += [q["topic"], q["question"], q["why_we_ask"]]
    body = " ".join(sendable).lower()
    for ask in FORBIDDEN_ASKS:
        if ask in body:
            raise ValidationError(
                f"§B4: the enquiry body contains {ask!r}. It asks about METHOD and never for the "
                "data, for access, for a trial or for a price"
            )

    # It must not ask a question the documentation already answered.
    proof = enquiry["no_data_request_proof"]
    if proof.get("already_answered_questions_repeated") != 0:
        raise ValidationError(
            "§B3: the enquiry repeats a question the public documentation already answers"
        )
    q3 = next(q for q in enquiry["questions"] if q["n"] == 3)
    if "truncat" not in q3["why_we_ask"].lower():
        raise ValidationError(
            "§B3: question 3 must state the already-known truncation as known, so the provider is "
            "not asked to restate its own documentation"
        )

    # It must not ask the provider to grade our gate.
    if not enquiry["what_this_enquiry_is_not"].get("does_not_ask_for_a_conclusion", "").strip():
        raise ValidationError(
            "§B1: the enquiry must ask what the system does, never whether it qualifies"
        )
    for phrase in ("observation-addressable", "does your api qualify"):
        if phrase in body:
            raise ValidationError(
                f"§B1: the body contains {phrase!r}, which asks the provider for our conclusion"
            )

    boundary = enquiry["content_boundary"]
    if boundary.get("hash_recorded_here") is not False:
        raise ValidationError(
            "§B6: the hash must live OUTSIDE the bytes it hashes. Writing it here changes them"
        )
    if not boundary.get("hash_recorded_in", "").strip():
        raise ValidationError("§B6: the record must say where its hash lives")


def _validate_contract(contract: dict) -> None:
    rule = contract["the_rule_this_freezes"]
    if rule.get("name") != "CONTENT_APPROVAL_IS_NOT_DISPATCH_APPROVAL":
        raise ValidationError("the contract must freeze the named rule")
    if rule.get("no_migration") is not True or rule.get("no_global_approval_subsystem") is not True:
        raise ValidationError("the contract creates no migration and no approval subsystem")
    if "registry" not in rule.get("why_not_the_registry", "").lower():
        raise ValidationError(
            "the contract must say why this rule is NOT an apparatus-requirements registry entry"
        )

    gates = contract["three_gates_that_stay_separate"]
    for name in ("CONTENT_APPROVAL", "RECIPIENT_ESTABLISHMENT", "CHANNEL_AUTHORIZATION"):
        if name not in gates:
            raise ValidationError(f"the contract omits the {name} gate")
    never = " ".join(gates["CHANNEL_AUTHORIZATION"]["never_granted_by"]).lower()
    if "connector" not in never:
        raise ValidationError(
            "the contract must state that a connector being present is not channel authorisation"
        )

    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in contract["envelope_required_fields"]:
            raise ValidationError(f"the contract omits required envelope field {field}")
    for state in CHANNEL_STATES:
        if state not in contract["channel_states"]:
            raise ValidationError(f"the contract omits channel state {state}")
    for state in ENVELOPE_STATES:
        if state not in contract["envelope_states"]:
            raise ValidationError(f"the contract omits envelope state {state}")

    h = contract["envelope_hash"]
    for field in (
        "enquiry_content_sha256",
        "recipient_address",
        "outbound_channel",
        "sender_identity",
    ):
        if field not in h["binding_fields"]:
            raise ValidationError(
                f"§D5: the envelope hash must bind {field}. A hash that omits it would let an "
                "approval cover a different action"
            )
    if "APPROVE MISSION 1.65 DISPATCH" not in h.get("approval_string_form", ""):
        raise ValidationError("§D5: the approval string form is fixed")

    if contract["no_envelope_without_a_recipient"].get("no_hash_is_computed_for_it") is not True:
        raise ValidationError("§D6: an envelope with no recipient carries no hash")


def _validate_netlas_envelope(env: dict) -> None:
    if env["state"] not in ENVELOPE_STATES:
        raise ValidationError(
            f"the Netlas envelope state {env['state']!r} is not in the vocabulary"
        )
    if env["enquiry_content_sha256"] != NETLAS_APPROVED_SHA256:
        raise ValidationError(
            "the Netlas envelope names a content hash that is not the approved one"
        )

    if env["state"] == "INCOMPLETE_RECIPIENT":
        if env.get("recipient_address") is not None:
            raise ValidationError("an INCOMPLETE_RECIPIENT envelope names a recipient")
        if env.get("envelope_sha256") is not None:
            raise ValidationError(
                "§D6: no approval hash for an incomplete action. A hash is an approval handle"
            )
        if env.get("approval_string") is not None:
            raise ValidationError("§D6: an incomplete envelope carries no approval string")
        if env.get("approvable") is not False:
            raise ValidationError("§D6: an incomplete envelope is not approvable")
        if env.get("packet_generated") is not False:
            raise ValidationError(
                "§E: a packet is produced only where recipient and channel are known"
            )

    for flag in ("address_invented", "address_inferred", "obfuscation_decoded"):
        if env.get(flag) is not False:
            raise ValidationError(f"§A3: {flag} must be false")
    if env.get("conventional_mailboxes_refused") is not True:
        raise ValidationError("§A3: conventional mailbox names are refused")

    approval = env["content_approval"]
    if approval.get("CONTENT_APPROVED") is not True:
        raise ValidationError("the Netlas content approval is recorded as not granted")

    apparatus = env["apparatus_state_unchanged"]
    if apparatus.get("changed_this_mission") is not False:
        raise ValidationError("Part G: no apparatus gate changes because a question exists")
    if apparatus.get("netlas_A8") != "PARTIAL":
        raise ValidationError("Part G: Netlas A8 stays PARTIAL")


def _validate_onyphe_envelope(env: dict, enquiry: dict) -> None:
    if env["state"] not in ENVELOPE_STATES:
        raise ValidationError(
            f"the ONYPHE envelope state {env['state']!r} is not in the vocabulary"
        )
    if env["outbound_channel"] not in CHANNEL_STATES:
        raise ValidationError(f"channel {env['outbound_channel']!r} is not in the vocabulary")
    if env.get("connector_state") not in CHANNEL_STATES:
        raise ValidationError("the connector state is not in the vocabulary")

    if env["state"] == "READY_FOR_OPERATOR_APPROVAL":
        for field in REQUIRED_ENVELOPE_FIELDS:
            if env.get(field) in (None, ""):
                raise ValidationError(
                    f"§D: a READY envelope must carry {field}. An envelope missing a required "
                    "field is not an action anybody can approve"
                )
        if not env.get("recipient_address"):
            raise ValidationError("§D6: a READY envelope must name a recipient")
        if env.get("approvable") is not True:
            raise ValidationError("a READY envelope is approvable")

    # Recipient provenance, not spelling. A retrieved mailbox may look conventional.
    prov = env["recipient_provenance"]
    if prov.get("how_established") != "RETRIEVED_FROM_FIRST_PARTY_PAGE":
        raise ValidationError(
            "§C: a recipient must be retrieved from a first-party page or supplied by the operator "
            "from one. No other provenance establishes one"
        )
    if not prov.get("pages"):
        raise ValidationError("the recipient provenance names no page it was read from")
    for page in prov["pages"]:
        if not page.get("url", "").strip() or not page.get("rendered_as", "").strip():
            raise ValidationError(
                "each provenance page must name its URL and how the address renders"
            )
    for flag in ("address_invented", "address_inferred", "obfuscation_decoded"):
        if prov.get(flag) is not False:
            raise ValidationError(f"§C: {flag} must be false")
    if not prov.get("the_distinction_that_matters_here", "").strip():
        raise ValidationError(
            "§C: where a retrieved address happens to look conventional, the record must say why "
            "provenance rather than spelling decides it"
        )
    if prov.get("what_it_is_not", "").strip() == "":
        raise ValidationError(
            "§C: the record must say what the route is NOT, so a general contact mailbox is not "
            "read as a dedicated technical channel"
        )

    # A demo or sales address must be excluded rather than silently unused.
    if not env.get("addresses_seen_and_excluded"):
        raise ValidationError(
            "§C: other published addresses were seen and the record does not say why they were "
            "not chosen"
        )
    for item in env["addresses_seen_and_excluded"]:
        if not item.get("excluded_because", "").strip():
            raise ValidationError("each excluded address must say why")

    # Sender identity.
    if env["outbound_channel"] == "AUTHORIZED_CONNECTOR":
        if env.get("sender_identity_is_a_placeholder") is True:
            raise ValidationError(
                "§D1: a connector envelope needs the specific operator-visible sender account. "
                "Naming only the connector does not say which mailbox the recipient will see"
            )
        if not env.get("channel_authorization_basis", "").strip():
            raise ValidationError(
                "§D4: a connector channel needs an explicit operator authorisation"
            )
    if env.get("sender_identity_is_a_placeholder") is True:
        if env["outbound_channel"] != "OPERATOR_MANUAL_SEND":
            raise ValidationError(
                "§D3: a placeholder sender is permitted only for OPERATOR_MANUAL_SEND"
            )
        if not env.get("its_cost_stated", "").strip():
            raise ValidationError(
                "§D3: a placeholder sender leaves the hash binding three of four fields, and the "
                "record must say so"
            )

    if env["outbound_channel"] == "OPERATOR_MANUAL_SEND" and env.get("connector_state") not in (
        "AVAILABLE_NOT_AUTHORIZED",
        "NOT_EVALUATED",
        "BLOCKED",
    ):
        raise ValidationError(
            "§D2: a connector present in the runtime starts at AVAILABLE_NOT_AUTHORIZED unless a "
            "prior explicit operator authorisation exists"
        )
    if not env.get("why_the_connector_was_not_selected", "").strip():
        raise ValidationError(
            "§D2: the record must say why the connector was not used, rather than leaving its "
            "presence unexplained"
        )

    if env["subject"] != enquiry["subject"]:
        raise ValidationError("the envelope subject and the frozen enquiry subject disagree")
    if env["enquiry_document_id"] != "onyphe-technical-methodology-enquiry-v1":
        raise ValidationError("the envelope names the wrong enquiry document")

    for flag in ("sent", "approval_recorded"):
        if env.get(flag) is not False:
            raise ValidationError(f"§F: {flag} must be false. Mission 1.65 stops before send")
    if env.get("sent_at") is not None:
        raise ValidationError("§F: an unsent envelope carries no send time")
    if env.get("dispatch_count") != 0:
        raise ValidationError("§F: nothing was dispatched")

    apparatus = env["apparatus_state_unchanged"]
    if apparatus.get("changed_this_mission") is not False:
        raise ValidationError("Part G: freezing questions changes no apparatus gate")


def _validate_readiness(readiness: dict, netlas: dict, onyphe: dict) -> None:
    if readiness["primary_outcome"] not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {readiness['primary_outcome']!r}")
    if not readiness.get("primary_outcome_statement", "").strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")

    outcome = readiness["primary_outcome"]
    netlas_ready = netlas["state"] == "READY_FOR_OPERATOR_APPROVAL"
    onyphe_ready = onyphe["state"] == "READY_FOR_OPERATOR_APPROVAL"
    if outcome == "DUAL_ENQUIRIES_FROZEN_DISPATCH_ENVELOPES_READY" and not (
        netlas_ready and onyphe_ready
    ):
        raise ValidationError("§outcomes: A requires both envelopes complete. Do not force A")
    if outcome == "NETLAS_RECIPIENT_PENDING_ONYPHE_ENQUIRY_FROZEN" and netlas.get(
        "recipient_address"
    ):
        raise ValidationError("outcome B requires the Netlas recipient to still be unsupplied")

    listed = {e["envelope"]: e for e in readiness["envelopes"]}
    for env, record in (
        ("netlas-dispatch-envelope-v1", netlas),
        ("onyphe-dispatch-envelope-v1", onyphe),
    ):
        if env not in listed:
            raise ValidationError(f"the readiness record omits {env}")
        if listed[env]["state"] != record["state"]:
            raise ValidationError(f"{env}: the readiness record and the envelope disagree on state")
        if listed[env]["recipient_known"] != bool(record.get("recipient_address")):
            raise ValidationError(f"{env}: the readiness record disagrees about the recipient")
        if listed[env]["hashed"] != (record.get("envelope_sha256") is not None):
            raise ValidationError(f"{env}: the readiness record disagrees about the hash")

    states = readiness["apparatus_states_unchanged"]
    for name in ("Netlas", "ONYPHE", "LeakIX", "The Shadowserver Foundation"):
        if name not in states:
            raise ValidationError(f"Part G: the readiness record omits {name}")
        if states[name].get("changed") is not False:
            raise ValidationError(f"Part G: {name} is recorded as changed, and no gate moved")
    if states.get("qualified_count") != 0:
        raise ValidationError("no apparatus qualifies")
    if states.get("pair_analysis_ready") is not False:
        raise ValidationError("pair analysis is not ready with zero qualified apparatuses")

    pair = readiness["no_pair_work_was_performed"]
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

    counters = readiness["counters"]
    for name in (
        "research_data_requests",
        "measurement_queries",
        "counts_fetched",
        "host_records_fetched",
        "banners_fetched",
        "trials",
        "purchases",
        "outbound_enquiries_sent",
        "model_calls",
        "embeddings",
        "canonical_mutations",
        "sources_registered",
        "governance_reviews_created",
        "apparatus_gates_changed",
    ):
        if counters.get(name) != 0:
            raise ValidationError(f"counter {name} reads {counters.get(name)!r} and must be 0")

    for name, value in readiness["stop_condition"].items():
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


def render_enquiry(record: dict) -> str:
    lines = [
        "# ONYPHE technical methodology enquiry — DRAFTED, NOT SENT",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_envelope.py`. Do not edit.",
        "",
        f"**Status:** `{record['status']}`  ",
        f"**Sent:** {record['delivery']['sent']}",
        "",
        record["delivery"]["why"],
        "",
        "## What this enquiry is not",
        "",
    ]
    for key, text in record["what_this_enquiry_is_not"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        "---",
        "",
        f"## Subject: {record['subject']}",
        "",
        record["preamble"],
        "",
    ]
    for q in record["questions"]:
        lines += [
            f"**{q['n']}. {q['topic']}.** {q['question']}",
            "",
            f"> *Why we ask:* {q['why_we_ask']}",
            "",
        ]
    lines += [
        record["closing"],
        "",
        "---",
        "",
        "## Provenance",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["questions frozen by", record["provenance_of_the_three_questions"]["frozen_by"]]),
        _row(["questions", str(record["provenance_of_the_three_questions"]["question_count"])]),
        _row(
            [
                "added beyond the frozen three",
                str(
                    record["provenance_of_the_three_questions"][
                        "questions_added_beyond_the_frozen_three"
                    ]
                ),
            ]
        ),
        _row(
            [
                "already-answered questions repeated",
                str(record["no_data_request_proof"]["already_answered_questions_repeated"]),
            ]
        ),
        _row(["hash recorded in", f"`{record['content_boundary']['hash_recorded_in']}`"]),
        "",
        record["content_boundary"]["why"],
        "",
    ]
    return "\n".join(lines)


def render_packet(enquiry: dict, env: dict, content_sha: str, env_sha: str) -> str:
    """The dispatch packet, generated from the frozen enquiry rather than retyped."""
    lines = [
        "# ONYPHE enquiry — dispatch packet",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_envelope.py`. Do not edit.",
        "",
        "The body below is generated from the frozen enquiry record, not retyped, so this packet",
        "cannot drift from the document the hash names.",
        "",
        _row(["field", "value"]),
        _row(["---", "---"]),
        _row(["**TO**", f"`{env['recipient_address']}`"]),
        _row(["**FROM / CHANNEL**", f"`{env['sender_identity']}` via `{env['outbound_channel']}`"]),
        _row(["**SUBJECT**", env["subject"]]),
        _row(["approved content hash", f"`{content_sha}`"]),
        _row(["dispatch envelope hash", f"`{env_sha}`"]),
        _row(["state", f"`{env['state']}`"]),
        _row(["sent", str(env["sent"])]),
        "",
        f"Approval string: `APPROVE MISSION 1.65 DISPATCH {env_sha}`",
        "",
        "*Recipient provenance:* read from "
        + " and ".join(f"<{p['url']}>" for p in env["recipient_provenance"]["pages"])
        + ", where it renders as a mailto link.",
        "",
        "---",
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
        "## What approving this does and does not do",
        "",
        f"- {env['what_approval_authorises']}",
    ]
    lines += [f"- **Not:** {i}" for i in env["what_approval_does_not_authorise"]]
    lines += [
        "",
        f"*On the sender:* {env['why_a_placeholder_is_permitted']} {env['its_cost_stated']}",
        "",
    ]
    return "\n".join(lines)


def render_baseline(record: dict) -> str:
    pre = record["repository_precondition"]
    base = record["canonical_baseline"]
    approved = record["netlas_approved_enquiry"]
    carried = record["content_approval_carried_forward"]
    acct = record["request_accounting"]
    lines = [
        "# Mission 1.65 — baseline",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_envelope.py`. Do not edit.",
        "",
        f"**Mission:** {record['mission']}  ",
        f"**Recorded:** {record['recorded_at']}",
        "",
        "## Precondition",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["Mission 1.64 merged", str(pre["mission_1_64_merged"])]),
        _row(["merge commit", f"`{pre['merge_commit']}`"]),
        _row(["branch", f"`{pre['branch']}`"]),
        _row(["migration head", f"`{pre['migration_head']}`"]),
        _row(["drift", f"**{base['drift_from_mission_1_64']}**"]),
        "",
        "## The approved Netlas enquiry",
        "",
        f"    {approved['approved_sha256']}",
        "",
        f"`{approved['verdict']}`, over {approved['hashing_boundary']}.",
        "",
        approved["why_none_of_that_was_done"],
        "",
        "## What the existing approval means",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["`CONTENT_APPROVED`", f"**{carried['CONTENT_APPROVED']}**"]),
        _row(["`RECIPIENT_APPROVED`", f"**{carried['RECIPIENT_APPROVED']}**"]),
        _row(["`CHANNEL_APPROVED`", f"**{carried['CHANNEL_APPROVED']}**"]),
        _row(["`SEND_NOW`", f"**{carried['SEND_NOW']}**"]),
        "",
        carried["why_these_are_four_separate_facts"],
        "",
        "## Retrievals",
        "",
        _row(["#", "subject", "sought"]),
        _row(["---", "---", "---"]),
    ]
    for e in record["documentation_ledger"]["requests"]:
        lines.append(_row([str(e["n"]), e["subject"], e["sought"]]))
    lines += [
        "",
        f"*The Netlas contact page was not re-fetched.* "
        f"{record['documentation_ledger']['why_not']}",
        "",
        "## What did not happen",
        "",
        "```",
        f"measurement queries {acct['MEASUREMENT_QUERIES']}"
        f"    counts {acct['COUNTS_FETCHED']}"
        f"    hosts {acct['HOST_RECORDS_FETCHED']}",
        f"banners {acct['BANNERS_FETCHED']}"
        f"    trials {acct['TRIALS']}"
        f"    purchases {acct['PURCHASES']}"
        f"    enquiries sent {acct['OUTBOUND_ENQUIRIES_SENT']}",
        "```",
        "",
        acct["a_demo_address_was_seen_and_not_used"],
        "",
    ]
    return "\n".join(lines)


def render_contract(record: dict) -> str:
    rule = record["the_rule_this_freezes"]
    lines = [
        "# Outbound dispatch envelope contract",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_envelope.py`. Do not edit.",
        "",
        f"**`{record['contract_id']}`**",
        "",
        f"## `{rule['name']}`",
        "",
        rule["rule"],
        "",
        rule["why_it_exists"],
        "",
        f"*Not a registry entry:* {rule['why_not_the_registry']}",
        "",
        "## Three gates that stay separate",
        "",
        _row(["gate", "asks", "granted by"]),
        _row(["---", "---", "---"]),
    ]
    for name, g in record["three_gates_that_stay_separate"].items():
        if name.startswith("$"):
            continue
        lines.append(_row([f"`{name}`", g["asks"], g["granted_by"]]))
    lines += [
        "",
        "**Never granted by:** "
        + "; ".join(
            record["three_gates_that_stay_separate"]["CHANNEL_AUTHORIZATION"]["never_granted_by"]
        ),
        "",
        "## Envelope states",
        "",
        _row(["state", "meaning"]),
        _row(["---", "---"]),
    ]
    for state in ENVELOPE_STATES:
        lines.append(_row([f"`{state}`", record["envelope_states"][state]]))
    lines += ["", "## Channel states", "", _row(["state", "meaning"]), _row(["---", "---"])]
    for state in CHANNEL_STATES:
        lines.append(_row([f"`{state}`", record["channel_states"][state]]))
    h = record["envelope_hash"]
    lines += [
        "",
        "## The envelope hash",
        "",
        f"Binds: {', '.join(f'`{f}`' for f in h['binding_fields'])}.",
        "",
        f"Excludes: {', '.join(f'`{f}`' for f in h['excluded_from_the_hash'])}. "
        f"{h['why_those_are_excluded']}",
        "",
        f"Approval string: `{h['approval_string_form']}`",
        "",
        f"*Means:* {h['what_that_approval_means']}. *Does not mean:* "
        + "; ".join(h["what_it_does_not_mean"])
        + ".",
        "",
        "## No envelope without a recipient",
        "",
        record["no_envelope_without_a_recipient"]["rule"],
        "",
        record["no_envelope_without_a_recipient"]["why"],
        "",
        "## Sender identity",
        "",
    ]
    for key, text in record["sender_identity_rules"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines.append("")
    return "\n".join(lines)


def render_netlas_envelope(record: dict) -> str:
    lines = [
        "# Netlas dispatch envelope — template",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_envelope.py`. Do not edit.",
        "",
        f"**State: `{record['state']}`.** Approvable: **{record['approvable']}**.",
        "",
        _row(["field", "value"]),
        _row(["---", "---"]),
        _row(["enquiry", f"`{record['enquiry_document_id']}`"]),
        _row(["content sha256", f"`{record['enquiry_content_sha256']}`"]),
        _row(["content approved", f"**{record['content_approval']['CONTENT_APPROVED']}**"]),
        _row(["recipient", "**not established**"]),
        _row(["channel", f"`{record['outbound_channel']}`"]),
        _row(["sender", "not bound"]),
        _row(["envelope hash", "**none**"]),
        "",
        f"**Why no hash.** {record['why_no_hash']}",
        "",
        f"**Why the recipient is unknown.** {record['why_the_recipient_is_unknown']}",
        "",
        f"**Resolved by:** {record['the_operator_action_that_resolves_it']}",
        "",
        f"**Why the channel is not evaluated.** {record['why_the_channel_is_not_evaluated']}",
        "",
        "## What would complete it",
        "",
    ]
    lines += [f"- {i}" for i in record["what_would_complete_this_envelope"]]
    lines += [
        "",
        "## Apparatus state",
        "",
        f"A7 `{record['apparatus_state_unchanged']['netlas_A7']}`, "
        f"A8 `{record['apparatus_state_unchanged']['netlas_A8']}`, changed "
        f"**{record['apparatus_state_unchanged']['changed_this_mission']}**.",
        "",
        record["apparatus_state_unchanged"]["rule"],
        "",
    ]
    return "\n".join(lines)


def render_onyphe_envelope(record: dict, content_sha: str, env_sha: str) -> str:
    prov = record["recipient_provenance"]
    lines = [
        "# ONYPHE dispatch envelope",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_envelope.py`. Do not edit.",
        "",
        f"**State: `{record['state']}`.** Sent: **{record['sent']}**.",
        "",
        _row(["field", "value"]),
        _row(["---", "---"]),
        _row(["enquiry", f"`{record['enquiry_document_id']}`"]),
        _row(["content sha256", f"`{content_sha}`"]),
        _row(["recipient", f"`{record['recipient_address']}`"]),
        _row(["channel", f"`{record['outbound_channel']}`"]),
        _row(["sender", f"`{record['sender_identity']}`"]),
        _row(["connector state", f"`{record['connector_state']}`"]),
        _row(["envelope sha256", f"`{env_sha}`"]),
        "",
        f"Approval string: `APPROVE MISSION 1.65 DISPATCH {env_sha}`",
        "",
        "## Recipient provenance",
        "",
        f"`{prov['how_established']}`, confirmed independently on "
        f"{len(prov['pages'])} first-party pages:",
        "",
    ]
    for p in prov["pages"]:
        lines.append(f"- <{p['url']}> — {p['rendered_as']}, labelled *{p['label_as_printed']}*")
    lines += [
        "",
        f"**{prov['the_distinction_that_matters_here']}**",
        "",
        f"*What it is:* {prov['what_it_is']}. *What it is not:* {prov['what_it_is_not']}",
        "",
        "## Addresses seen and excluded",
        "",
        _row(["purpose as printed", "excluded because"]),
        _row(["---", "---"]),
    ]
    for item in record["addresses_seen_and_excluded"]:
        lines.append(_row([item["purpose_as_printed"], item["excluded_because"]]))
    lines += [
        "",
        "## Channel and sender",
        "",
        record["why_the_connector_was_not_selected"],
        "",
        f"*On the placeholder sender:* {record['why_a_placeholder_is_permitted']}",
        "",
        f"*Its cost:* {record['its_cost_stated']} {record['how_to_pin_the_fourth']}",
        "",
        "## What approval does and does not authorise",
        "",
        f"- {record['what_approval_authorises']}",
    ]
    lines += [f"- **Not:** {i}" for i in record["what_approval_does_not_authorise"]]
    lines += [
        "",
        "## Apparatus state",
        "",
        f"B2 `{record['apparatus_state_unchanged']['onyphe_B2']}`, "
        f"B4 `{record['apparatus_state_unchanged']['onyphe_B4']}`, "
        f"`{record['apparatus_state_unchanged']['onyphe_individual_status']}`, changed "
        f"**{record['apparatus_state_unchanged']['changed_this_mission']}**.",
        "",
        record["apparatus_state_unchanged"]["rule"],
        "",
    ]
    return "\n".join(lines)


def render_readiness(record: dict) -> str:
    nxt = record["next_mission_recommendation"]
    lines = [
        "# Dual enquiry readiness",
        "",
        "Generated by `infrastructure/scripts/render_dispatch_envelope.py`. Do not edit.",
        "",
        f"**Outcome: `{record['primary_outcome']}`**",
        "",
        record["primary_outcome_statement"],
        "",
        "## Envelopes",
        "",
        _row(["envelope", "state", "recipient", "channel", "hashed", "approvable"]),
        _row(["---"] * 6),
    ]
    for e in record["envelopes"]:
        lines.append(
            _row(
                [
                    f"`{e['envelope']}`",
                    f"`{e['state']}`",
                    "yes" if e["recipient_known"] else "**no**",
                    "yes" if e["channel_bound"] else "**no**",
                    "yes" if e["hashed"] else "**no**",
                    "yes" if e["approvable"] else "**no**",
                ]
            )
        )
    lines += ["", "## Why this outcome and not another", ""]
    for key, text in record["why_this_outcome_and_not_another"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        "## The asymmetry, and why it is not a preference",
        "",
        record["the_asymmetry_and_why_it_is_not_a_preference"]["observation"],
        "",
        record["the_asymmetry_and_why_it_is_not_a_preference"]["not_a_ranking"],
        "",
        f"*{record['the_asymmetry_and_why_it_is_not_a_preference']['the_temptation_declined']}*",
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
        f"**`{nxt['checkpoint']}`.**",
        "",
        f"*One approval is available now:* {nxt['one_approval_is_available_now']['what_it_authorises']}",
        "",
        f"*One input is still missing:* the {nxt['one_input_is_still_missing']['field']} for "
        f"`{nxt['one_input_is_still_missing']['envelope']}`. "
        f"{nxt['one_input_is_still_missing']['how_the_operator_supplies_it']}",
        "",
        f"**{nxt['name']}** should:",
        "",
    ]
    lines += [f"- {i}" for i in nxt["it_should"]]
    lines += ["", "It must not:", ""]
    lines += [f"- {i}" for i in nxt["it_must_not"]]
    lines += ["", f"Awaiting: **{record['stop_condition']['awaiting']}**.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  dispatch envelope: {error}")
        return 1

    baseline, enquiry, contract, netlas, onyphe, readiness = records

    enquiry_md = render_enquiry(enquiry)
    # The content hash is over the RENDERED enquiry, so it is computed from the
    # text about to be written rather than from whatever is on disk.
    content_sha = hashlib.sha256(enquiry_md.encode("utf-8")).hexdigest()
    env_sha = envelope_digest(onyphe, content_sha)

    rendered = {
        RENDERED[BASELINE]: render_baseline(baseline),
        RENDERED[ENQUIRY]: enquiry_md,
        RENDERED[CONTRACT]: render_contract(contract),
        RENDERED[NETLAS_ENV]: render_netlas_envelope(netlas),
        RENDERED[ONYPHE_ENV]: render_onyphe_envelope(onyphe, content_sha, env_sha),
        RENDERED[READINESS]: render_readiness(readiness),
        ONYPHE_PACKET_MD: render_packet(enquiry, onyphe, content_sha, env_sha),
    }

    recorded_content = onyphe.get("enquiry_content_sha256")
    recorded_env = onyphe.get("envelope_sha256")
    placeholder = "PLACEHOLDER_COMPUTED_BY_RENDERER"
    if recorded_content != placeholder and recorded_content != content_sha:
        print(
            f"DRIFT    the recorded enquiry content hash is {recorded_content} and the rendered "
            f"enquiry hashes to {content_sha}"
        )
        return 1
    if recorded_env != placeholder and recorded_env != env_sha:
        print(
            f"DRIFT    the recorded envelope hash is {recorded_env} and the envelope canonicalises "
            f"to {env_sha}"
        )
        return 1

    if args.check:
        if placeholder in (recorded_content, recorded_env):
            print("DRIFT    the ONYPHE envelope still carries a placeholder hash")
            return 1
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

    print(f"outcome  {readiness['primary_outcome']}")
    print(f"netlas   {netlas['state']}, recipient {netlas['recipient_address']}, no hash")
    print(f"onyphe   {onyphe['state']}, recipient {onyphe['recipient_address']}")
    print(f"content  {content_sha}")
    print(f"envelope {env_sha}")
    print(f"approve  APPROVE MISSION 1.65 DISPATCH {env_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
