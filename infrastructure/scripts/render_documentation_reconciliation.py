"""Render and validate the Mission 1.66.2 ONYPHE documentation reconciliation.

Ten records, and one discipline underneath all of them:

    A DOCUMENT SAYS WHAT IT SAYS, AND NOT WHAT IT WOULD BE CONVENIENT FOR IT
    TO SAY.

`validate()` enforces the readings this mission was most tempted to make and
did not:

  - historical retention, "data collected", a latest-first default sort and an
    older-result function are each compatible with BOTH storage models, so none
    of them may promote B2;
  - a port-set CARDINALITY is not a MEMBERSHIP, and a membership published for
    one category is not a fact about another;
  - a configuration documented as having CHANGED does not become
    time-addressable by being documented;
  - the retention sentence names the field it TRUNCATES and does not name the
    fields it REMOVES, so the unnamed ones stay UNKNOWN in both directions;
  - the User API is documented as showing an API key, so it is not executed to
    find out what its port list means;
  - a support address is established by citation, never by spelling;
  - Mission 1.65 is not rewritten because a later document was found;
  - and nothing was sent, executed, registered or measured.

    uv run python infrastructure/scripts/render_documentation_reconciliation.py
    uv run python infrastructure/scripts/render_documentation_reconciliation.py --check

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

BASELINE = DATA / "mission-1.66.2-baseline-v1.json"
RECONCILIATION = DATA / "onyphe-public-documentation-reconciliation-v1.json"
TEMPORAL = DATA / "onyphe-temporal-object-public-doc-review-v2.json"
PORTS = DATA / "onyphe-datascan-port-configuration-public-doc-review-v2.json"
USER_API = DATA / "onyphe-user-api-configuration-surface-review-v1.json"
RETENTION = DATA / "onyphe-retention-public-doc-review-v2.json"
CONTACT = DATA / "onyphe-contact-channel-reconciliation-v1.json"
REASSESSMENT = DATA / "onyphe-three-question-reassessment-v1.json"
PACKAGE = DATA / "onyphe-package-recomputed-v2.json"
READINESS = DATA / "qualified-apparatus-readiness-v3.json"

ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
ONYPHE_ENVELOPE = DATA / "onyphe-dispatch-envelope-v1.json"
NETLAS_ENVELOPE = DATA / "netlas-dispatch-envelope-v1.json"
NETLAS_ENQUIRY_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"
ATTESTATION = DATA / "onyphe-manual-dispatch-attestation-v1.json"

ONYPHE_CONTENT_SHA256 = "0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f"
ONYPHE_ENVELOPE_SHA256 = "12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2"
NETLAS_APPROVED_SHA256 = "310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4"

BINDING_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "outbound_channel",
    "sender_identity",
    "subject",
    "content_version",
)

ORDER = [
    BASELINE,
    RECONCILIATION,
    TEMPORAL,
    PORTS,
    USER_API,
    RETENTION,
    CONTACT,
    REASSESSMENT,
    PACKAGE,
    READINESS,
]
RENDERED = {p: p.with_suffix(".md") for p in ORDER}

GATE_STATES = ("PASS", "PARTIAL", "FAIL", "UNKNOWN")
INDIVIDUAL_STATES = (
    "INDIVIDUALLY_QUALIFIED",
    "INDIVIDUALLY_NOT_QUALIFIED",
    "INDIVIDUALLY_UNRESOLVED",
)
RETENTION_STATES = ("RETAINED", "REMOVED", "TRUNCATED", "UNKNOWN")
CLASSIFICATIONS = ("ANSWERED_BY_PUBLIC_DOCS", "PARTIALLY_CONSTRAINED", "STILL_UNRESOLVED")
USER_API_SAFETY = (
    "SAFE_PUBLIC_CONFIGURATION",
    "MIXED_METADATA_REQUIRES_OPERATOR_DECISION",
    "SECRET_BEARING_DO_NOT_EXECUTE",
    "UNKNOWN",
)
PRIMARY_OUTCOMES = {
    "ONYPHE_PUBLIC_DOCUMENTATION_CLOSES_ALL_RESIDUALS",
    "ONYPHE_PUBLIC_DOCUMENTATION_CLOSES_SOME_RESIDUALS",
    "ONYPHE_PUBLIC_DOCUMENTATION_RECONCILED_RESIDUALS_REMAIN",
    "ONYPHE_B2_CLOSED_BY_PUBLIC_DOCUMENTATION",
    "ONYPHE_CONFIGURATION_ROUTE_DOCUMENTED_BUT_NOT_SAFE_TO_EXECUTE",
    "ONYPHE_PUBLIC_DOCUMENTATION_CONTRADICTS_CURRENT_PACKAGE",
    "MISSION_1_66_1_NOT_MERGED",
    "MISSION_1_66_2_BASELINE_DRIFT",
    "MISSION_1_66_2_CANONICAL_MUTATION",
    "ONYPHE_DOCUMENTATION_RECONCILIATION_BLOCKED",
}

OVERCLAIMS = ("installation", "customer", "subscription", "revenue", "adoption", "demand")


class ValidationError(Exception):
    """A Mission 1.66.2 record claims something the documents do not support."""


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


def _envelope_digest(envelope: dict, content_sha: str) -> str:
    binding = {f: envelope.get(f) for f in BINDING_FIELDS}
    binding["enquiry_content_sha256"] = content_sha
    blob = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate() -> tuple[dict, ...]:
    records = tuple(_load(p) for p in ORDER)
    (
        baseline,
        reconciliation,
        temporal,
        ports,
        user_api,
        retention,
        contact,
        reassessment,
        package,
        readiness,
    ) = records

    _validate_frozen_history()
    _validate_baseline(baseline)
    _validate_temporal(temporal)
    _validate_ports(ports)
    _validate_user_api(user_api)
    _validate_retention(retention)
    _validate_contact(contact)
    _validate_reassessment(reassessment, temporal, ports, retention)
    _validate_package(package, temporal, ports, retention)
    _validate_readiness(readiness, package)
    _validate_reconciliation(reconciliation, package, readiness, user_api, contact)
    _validate_no_overclaims(records)
    return records


def _validate_frozen_history() -> None:
    """Later documents extend history. They do not rewrite it."""
    content = hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest()
    if content != ONYPHE_CONTENT_SHA256:
        raise ValidationError("the sent ONYPHE enquiry was edited. A sent document may not change")
    envelope = _load(ONYPHE_ENVELOPE)
    if _envelope_digest(envelope, content) != ONYPHE_ENVELOPE_SHA256:
        raise ValidationError("the approved ONYPHE dispatch envelope no longer binds its action")
    if hashlib.sha256(NETLAS_ENQUIRY_MD.read_bytes()).hexdigest() != NETLAS_APPROVED_SHA256:
        raise ValidationError("the approved Netlas enquiry body was edited")

    # Mission 1.65's record of what it established stays as written. Anchored to
    # the RECORD's own field and to the sentence whose deletion would BE the
    # rewrite, rather than to a phrase in the rendered prose: a scan aimed at
    # wording fires on a re-render that changed nothing, which is how a
    # structural check turns into noise and then gets loosened.
    provenance = _load(ONYPHE_ENVELOPE)["recipient_provenance"]
    if "No such channel is published" not in str(provenance.get("what_it_is_not", "")):
        raise ValidationError(
            "Mission 1.65's statement that no dedicated support channel was published has been "
            "rewritten. It accurately recorded the pages that mission inspected, and a document "
            "found later extends the evidence rather than falsifying the earlier reading"
        )

    netlas = _load(NETLAS_ENVELOPE)
    if netlas.get("recipient_address") is not None:
        raise ValidationError("a Netlas recipient appeared. No address may be guessed or decoded")

    attestation = _load(ATTESTATION)
    if attestation["exactly_once"].get("send_count") != 1:
        raise ValidationError("the ONYPHE enquiry send count moved. One approval, one send")
    if attestation["exactly_once"].get("follow_up_sent") is not False:
        raise ValidationError("a follow-up was sent. That is a new action needing its own approval")
    if attestation["provider_response"].get("status") != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError(
            "the provider response status moved. This mission is about public documentation and "
            "does not check a mailbox"
        )


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_66_1_merged") is not True:
        raise ValidationError("outcome G: Mission 1.66.1 is not recorded as merged")
    if pre.get("verified_from_git_not_from_prompt") is not True:
        raise ValidationError(
            "the precondition must be verified from git rather than from a prompt"
        )
    if baseline["canonical_baseline"].get("drift_from_mission_1_66_1") != "none":
        raise ValidationError("outcome H: the canonical baseline drifted")

    budget = baseline["documentation_budget"]
    if budget.get("used", 0) > budget.get("maximum", 0):
        raise ValidationError(
            f"§2: the budget is {budget.get('maximum')} first-party requests and "
            f"{budget.get('used')} were used"
        )
    if len(budget.get("requests", [])) != budget.get("used"):
        raise ValidationError("the ledger and the used count disagree")
    for entry in budget["requests"]:
        if not str(entry.get("url", "")).strip() or not str(entry.get("sought", "")).strip():
            raise ValidationError("every request must name its URL and what it sought")

    boundary = baseline["source_boundary"]
    if boundary.get("search_summary_used_as_evidence") is not False:
        raise ValidationError(
            "§1: a search or retrieval summary was used as evidence. Mission 1.63 established that "
            "a summary is not a document, after one reported a sentence a page did not contain"
        )
    if boundary.get("every_load_bearing_claim_requoted_from_the_page") is not True:
        raise ValidationError("§1: every load-bearing claim must be re-read against the page")

    acct = baseline["request_accounting"]
    for name in (
        "ONYPHE_DATA_API_EXECUTIONS",
        "USER_API_EXECUTIONS",
        "SEARCH_API_EXECUTIONS",
        "EXPORT_API_EXECUTIONS",
        "SUMMARY_API_EXECUTIONS",
        "SIMPLE_API_EXECUTIONS",
        "DISCOVERY_API_EXECUTIONS",
        "ONDEMAND_SCAN_EXECUTIONS",
        "MEASUREMENT_QUERIES",
        "COUNTS_FETCHED",
        "HOST_RECORDS_FETCHED",
        "BANNERS_FETCHED",
        "DOWNLOADS",
        "TRIALS",
        "PURCHASES",
        "MAILBOX_SEARCHES",
        "ENQUIRIES_SENT",
        "FOLLOWUPS_SENT",
        "CREDENTIALS_READ",
        "MODEL_CALLS",
        "EMBEDDINGS",
    ):
        if acct.get(name) != 0:
            raise ValidationError(f"§42/§43/§44: {name} must be 0 and reads {acct.get(name)!r}")

    for name, value in baseline["canonical_mutations"].items():
        if name.startswith("$"):
            continue
        if value not in (0, 0.0, False):
            raise ValidationError(f"outcome I: canonical mutation {name} reads {value!r}")


def _validate_temporal(temporal: dict) -> None:
    """§A3. Every available wording is compatible with both storage models."""
    disc = temporal["the_exact_discriminator"]
    for field in ("case", "if_yes", "if_no", "if_the_documentation_does_not_say"):
        if not str(disc.get(field, "")).strip():
            raise ValidationError(f"the discriminator must state {field}")
    if "again" not in disc["case"].lower() or "same" not in disc["case"].lower():
        raise ValidationError(
            "§A2: the discriminator must be the REPEATED observation of the SAME service. Any "
            "weaker question is one the documentation can answer without settling B2"
        )

    verdict = temporal["verdict"]
    if verdict.get("B2") not in GATE_STATES:
        raise ValidationError(f"B2 verdict {verdict.get('B2')!r} is not in the vocabulary")

    refused = temporal["inferences_that_were_available_and_refused"]
    for name in (
        "historical_data_exists",
        "data_collected_wording",
        "latest_first_default",
        "older_result_retrievable",
        "last_observed_wording",
    ):
        if not str(refused.get(name, "")).strip():
            raise ValidationError(
                f"§A3: the record must say why {name} does not close B2. Each is compatible with "
                "both storage models, and leaving one unaddressed is how it later reads as support"
            )

    # B2 may only PASS on the repeated-observation case being answered.
    if verdict.get("B2") == "PASS":
        if temporal["the_page_most_likely_to_answer_it_does_not"].get("finding"):
            raise ValidationError(
                "§A4: B2 records PASS while the record still says no page states the repeated-"
                "observation semantics. Historical support, collection wording and a latest-first "
                "sort do not close the gate"
            )
        if verdict.get("state") != "APPEND_OR_VERSIONED":
            raise ValidationError("§A4: a B2 PASS must name the storage model that was established")
    if verdict.get("B2") == "PARTIAL" and verdict.get("state") != "AMBIGUOUS":
        raise ValidationError("a PARTIAL B2 is the ambiguous state and must say so")


def _validate_ports(ports: dict) -> None:
    current = ports["current_documented_configuration"]
    if not str(current.get("cardinality_is_not_membership", "")).strip():
        raise ValidationError(
            "§B1: the record must state that a port COUNT is not a port SET. A page saying 500 "
            "ports says how many, never which"
        )

    tcp = ports["tcp_22_membership"]
    if tcp.get("verdict") not in (
        "DATASCAN_TCP22_PRESENT",
        "DATASCAN_TCP22_ABSENT",
        "DATASCAN_TCP22_UNKNOWN",
    ):
        raise ValidationError(f"TCP22 verdict {tcp.get('verdict')!r} is not in the vocabulary")
    if (
        tcp.get("verdict") == "DATASCAN_TCP22_PRESENT"
        and tcp.get("datascan_tcp_section_exists") is not True
    ):
        raise ValidationError(
            "§B3: TCP/22 recorded as present in datascan while no datascan TCP section is "
            "published. A membership published for ctiscan is not a fact about datascan"
        )
    if (
        tcp.get("port_22_appears_under")
        and "ctiscan" in str(tcp.get("port_22_appears_under"))
        and tcp.get("verdict") != "DATASCAN_TCP22_UNKNOWN"
    ):
        raise ValidationError(
            "§B3: port 22 appears under a ctiscan heading and the record draws a datascan "
            "conclusion from it. That is the category transfer Mission 1.63 refused"
        )
    if not str(tcp.get("absence_is_not_denial", "")).strip():
        raise ValidationError(
            "§D: the record must state that a missing section is not a statement that datascan "
            "scans no TCP ports"
        )

    drift = ports["historical_configuration_drift"]
    if drift.get("DATASCAN_CONFIGURATION_HISTORICALLY_MUTABLE") is True:
        if not drift.get("verbatim"):
            raise ValidationError("§B2: documented drift must be quoted, not asserted")
        if not str(drift.get("basis_page", "")).strip():
            raise ValidationError("§B2: documented drift must name the page it came from")

    addressable = ports["configuration_time_addressability"]
    if addressable.get("verdict") not in (
        "CONFIGURATION_TIME_ADDRESSABLE",
        "CONFIGURATION_TIME_NOT_ADDRESSABLE",
        "CONFIGURATION_TIME_UNKNOWN",
    ):
        raise ValidationError(
            "the configuration time-addressability verdict is not in the vocabulary"
        )
    if addressable.get("verdict") == "CONFIGURATION_TIME_ADDRESSABLE" and not (
        addressable.get("PORT_SET_VERSIONED")
        or addressable.get("PORT_SET_DATED")
        or addressable.get("PORT_SET_INVARIANT_FOR_RELEVANT_PERIOD")
    ):
        raise ValidationError(
            "§B4: a configuration is time-addressable only if the port set is versioned, dated or "
            "established invariant. Current membership is not historical membership"
        )
    if addressable.get("current_membership_is_not_historical_membership") is not True:
        raise ValidationError("§B4: the record must keep current and historical membership apart")
    if (
        drift.get("DATASCAN_CONFIGURATION_HISTORICALLY_MUTABLE") is True
        and addressable.get("verdict") == "CONFIGURATION_TIME_ADDRESSABLE"
    ):
        raise ValidationError(
            "a configuration documented as having CHANGED does not become addressable by being "
            "documented. Knowing it moved is not knowing where it was"
        )

    offered = ports["candidate_registry_requirement_offered_and_not_added"]
    if offered.get("REGISTRY_UNCHANGED") != 14:
        raise ValidationError("§40: the apparatus requirement registry stays at 14 this mission")
    for field in (
        "statement",
        "demonstrated_by",
        "why_it_is_not_already_represented",
        "why_it_was_not_added_here",
    ):
        if not str(offered.get(field, "")).strip():
            raise ValidationError(f"an offered requirement must state {field}")


def _validate_user_api(user_api: dict) -> None:
    endpoint = user_api["endpoint"]
    if endpoint.get("EXECUTED") is not False or endpoint.get("execution_attempts") != 0:
        raise ValidationError("§C1: the User API was executed. Documentation only")
    if endpoint.get("credentials_read") != 0:
        raise ValidationError("§43: a credential was read. Credentials are irrelevant here")

    verdict = user_api["verdict"]
    if verdict.get("ENDPOINT_EXECUTION_SAFETY") not in USER_API_SAFETY:
        raise ValidationError("the User API safety verdict is not in the vocabulary")
    if verdict.get("DATASCAN_CONFIGURATION_RELEVANCE") not in (
        "ESTABLISHED",
        "PARTIAL",
        "UNKNOWN",
        "NOT_APPLICABLE",
    ):
        raise ValidationError("the User API datascan relevance verdict is not in the vocabulary")

    exposes = user_api["what_the_documentation_says_it_exposes"]
    kinds = {c.get("kind") for c in exposes["categories"]}
    if (
        "LICENCE_AND_CREDENTIAL" in kinds
        and exposes.get("it_is_not_pure_configuration_metadata") is not True
    ):
        raise ValidationError(
            "§C2: the documentation places credential material on this surface and the record "
            "still calls it pure configuration metadata"
        )
    credential = user_api["the_credential_finding"]
    if (
        credential.get("documentation_names_an_api_key_among_what_the_endpoint_lets_you_view")
        is True
        and verdict.get("ENDPOINT_EXECUTION_SAFETY") != "SECRET_BEARING_DO_NOT_EXECUTE"
    ):
        raise ValidationError(
            "§C3: the documentation names an API key among what this endpoint shows, and the "
            "record does not classify it SECRET_BEARING_DO_NOT_EXECUTE. Avoiding measurement "
            "contamination does not justify credential exposure"
        )

    gap = user_api["the_configuration_semantic_gap"]
    if gap.get("USER_API_PORT_LIST_RESOURCE_MAPPING") not in ("ESTABLISHED", "PARTIAL", "UNKNOWN"):
        raise ValidationError("the port-list resource mapping verdict is not in the vocabulary")
    if (
        gap.get("USER_API_PORT_LIST_RESOURCE_MAPPING") == "ESTABLISHED"
        and gap.get("whether_the_list_is_datascan_specific") == "NOT_DOCUMENTED"
    ):
        raise ValidationError(
            "§C4: the port-list mapping is recorded as established while the documentation does "
            "not say which category it describes. A generic scanned-ports list is not the datascan "
            "set"
        )
    if not str(gap.get("the_inference_refused", "")).strip():
        raise ValidationError("§C4: the record must name the attribution it refused")


def _validate_retention(retention: dict) -> None:
    raw = retention["raw_response_field"]
    if raw.get("post_30_day_treatment") != "TRUNCATED to 4KB":
        raise ValidationError("the raw response field is documented as truncated")
    if raw.get("is_not") != "REMOVED":
        raise ValidationError(
            "§E2: truncation is not removal. The retention sentence names the field it truncates "
            "and does not name the fields it removes"
        )
    if raw.get("B3") != "PASS" or raw.get("reopened") is not False:
        raise ValidationError("§E2: B3 is not reopened without contradictory first-party evidence")

    fields = retention["location_fields"]
    for name in ("ip", "@timestamp", "node.id", "node.country", "node.physicalcountry"):
        if name not in fields:
            raise ValidationError(f"§E3: the record omits the field {name}")
        state = fields[name].get("post_30_day_state")
        if state not in RETENTION_STATES:
            raise ValidationError(f"{name} retention state {state!r} is not in the vocabulary")
        if state == "RETAINED" and "removed" not in str(fields[name].get("basis", "")).lower():
            raise ValidationError(
                f"§E3: {name} is recorded RETAINED. Silence is UNKNOWN, and neither an archive "
                "being useful without it nor historical querying existing is documentation"
            )

    refused = retention["arguments_available_and_refused"]
    for name in (
        "the_archive_would_be_useless_without_addresses",
        "historical_querying_proves_timestamps_survive",
    ):
        if not str(refused.get(name, "")).strip():
            raise ValidationError(f"§E3: the record must name and refuse the argument {name}")

    verdict = retention["verdict"]
    for name in ("ADDRESS_RETENTION", "OBSERVATION_TIME_RETENTION", "VANTAGE_FIELD_RETENTION"):
        if verdict.get(name) not in RETENTION_STATES:
            raise ValidationError(f"{name} is not in the vocabulary")
    if verdict.get("ADDRESS_RETENTION") != fields["ip"]["post_30_day_state"]:
        raise ValidationError("the address retention verdict and the ip field state disagree")
    if verdict.get("OBSERVATION_TIME_RETENTION") != fields["@timestamp"]["post_30_day_state"]:
        raise ValidationError(
            "the observation time verdict and the @timestamp field state disagree"
        )


def _validate_contact(contact: dict) -> None:
    if contact.get("append_only") is not True or contact.get("mission_1_65_rewritten") is not False:
        raise ValidationError("§F2: the reconciliation is append-only and Mission 1.65 stands")

    prior = contact["what_mission_1_65_recorded"]
    if prior.get("was_it_accurate") is not True:
        raise ValidationError(
            "§F2: Mission 1.65 accurately recorded the evidence available to it. A later document "
            "extends history rather than falsifying the earlier moment"
        )

    evidence = contact["the_new_first_party_evidence"]
    if evidence.get("how_established") != "RETRIEVED_FROM_FIRST_PARTY_PAGE":
        raise ValidationError("§F1: a contact channel is established from a first-party page")
    if evidence.get("inferred_from_spelling") is not False:
        raise ValidationError(
            "§F1: the address must be cited, never inferred from spelling. A conventional mailbox "
            "is exactly the kind a system could guess"
        )
    if not str(evidence.get("verbatim_instruction", "")).strip():
        raise ValidationError("§F1: the citation must quote the page")
    if not str(evidence.get("url", "")).startswith("https://"):
        raise ValidationError("§F1: the citation must name the page it came from")

    not_authorised = contact["what_this_does_not_authorise"]
    for flag in (
        "resend_to_support",
        "second_enquiry_created",
        "new_dispatch_envelope_created",
        "previous_manual_send_superseded",
        "reminder_or_follow_up",
    ):
        if not_authorised.get(flag) is not False:
            raise ValidationError(f"§F3: {flag} must be false")
    if not_authorised.get("one_send_stands") != 1:
        raise ValidationError("§F3: one approval authorises one send, and it has been used")

    if (
        contact["verdict"].get("apparatus_effect")
        != "none. A better contact route is not an answer to a methodological question, and no gate moves because a mailbox was found."
    ):
        raise ValidationError(
            "§F3: the record must state that finding a contact route moves no apparatus gate"
        )


def _validate_reassessment(
    reassessment: dict, temporal: dict, ports: dict, retention: dict
) -> None:
    if reassessment["the_enquiry_was_not_edited"].get("edited") is not False:
        raise ValidationError("a sent document may not be edited")

    questions = {q["n"]: q for q in reassessment["questions"]}
    if set(questions) != {1, 2, 3}:
        raise ValidationError("the reassessment must cover exactly the three sent questions")

    q1 = questions[1]
    if q1.get("classification") not in CLASSIFICATIONS:
        raise ValidationError("question 1 classification is not in the vocabulary")
    if q1["classification"] == "ANSWERED_BY_PUBLIC_DOCS" and temporal["verdict"]["B2"] != "PASS":
        raise ValidationError(
            "question 1 is recorded answered while B2 is not PASS. The question and the gate it "
            "decides may not disagree"
        )

    # §G: subparts stay apart.
    for n in (2, 3):
        subparts = questions[n].get("subparts")
        if not subparts or len(subparts) < 3:
            raise ValidationError(
                f"§G: question {n} must classify its subparts independently. Collapsing them lets "
                "one answered part stand for the whole"
            )
        for sub in subparts:
            if sub.get("classification") not in CLASSIFICATIONS:
                raise ValidationError(
                    f"question {n} subpart classification is not in the vocabulary"
                )

    tcp_sub = next(s for s in questions[2]["subparts"] if "TCP/22" in s["subpart"])
    if (
        tcp_sub["classification"] == "ANSWERED_BY_PUBLIC_DOCS"
        and ports["tcp_22_membership"]["verdict"] == "DATASCAN_TCP22_UNKNOWN"
    ):
        raise ValidationError("the TCP/22 subpart is answered while the port verdict is unknown")

    for sub in questions[3]["subparts"]:
        if sub["classification"] == "ANSWERED_BY_PUBLIC_DOCS":
            raise ValidationError(
                "§G: a retention field is recorded answered while the retention review leaves the "
                "removed fields unnamed"
            )
    if (
        retention["verdict"]["ADDRESS_RETENTION"] == "UNKNOWN"
        and questions[3]["overall"] == "ANSWERED_BY_PUBLIC_DOCS"
    ):
        raise ValidationError("question 3 is answered while address retention is unknown")

    summary = reassessment["summary"]
    answered = sum(
        1 for q in reassessment["questions"] if q.get("classification") == "ANSWERED_BY_PUBLIC_DOCS"
    )
    if summary.get("questions_answered_by_public_documentation") != answered:
        raise ValidationError("the summary and the per-question classifications disagree")


def _validate_package(package: dict, temporal: dict, ports: dict, retention: dict) -> None:
    for name, gate in package["gates"].items():
        if gate.get("verdict") not in GATE_STATES:
            raise ValidationError(
                f"gate {name} verdict {gate.get('verdict')!r} is not in the vocabulary"
            )
        if not str(gate.get("basis", "")).strip():
            raise ValidationError(f"gate {name} states no basis")

    if package["gates"]["B2"]["verdict"] != temporal["verdict"]["B2"]:
        raise ValidationError("the package and the temporal review disagree about B2")
    if package["gates"]["B3"]["verdict"] != retention["raw_response_field"]["B3"]:
        raise ValidationError("the package and the retention review disagree about B3")

    status = package["individual_status"]
    if status.get("verdict") not in INDIVIDUAL_STATES:
        raise ValidationError("the individual status is not in the vocabulary")
    blocking = [n for n, g in package["gates"].items() if g["verdict"] in ("PARTIAL", "UNKNOWN")]
    if status["verdict"] == "INDIVIDUALLY_QUALIFIED" and blocking:
        raise ValidationError(
            f"§I: qualification requires every mandatory gate to PASS, and {blocking} are not. "
            "PARTIAL cannot qualify and UNKNOWN cannot qualify"
        )
    if (
        status.get("PARTIAL_cannot_qualify") is not True
        or status.get("UNKNOWN_cannot_qualify") is not True
    ):
        raise ValidationError("§I: the record must state that PARTIAL and UNKNOWN cannot qualify")

    changed = sum(1 for g in package["gates"].values() if g.get("changed") is True)
    if package.get("gates_changed_this_mission") != changed:
        raise ValidationError("the recorded gate-change count and the gates disagree")
    if (
        changed
        and ports["tcp_22_membership"]["verdict"] == "DATASCAN_TCP22_UNKNOWN"
        and (package["gates"]["B4"]["verdict"] == "PASS")
    ):
        raise ValidationError("B4 moved to PASS while the port membership is unknown")


def _validate_readiness(readiness: dict, package: dict) -> None:
    names = {a["name"] for a in readiness["apparatuses"]}
    for expected in ("Netlas", "ONYPHE", "LeakIX", "The Shadowserver Foundation"):
        if expected not in names:
            raise ValidationError(f"the readiness record omits {expected}")
    for apparatus in readiness["apparatuses"]:
        if apparatus.get("individual") not in INDIVIDUAL_STATES:
            raise ValidationError(f"{apparatus['name']} status is not in the vocabulary")
        if apparatus.get("changed") is not False:
            raise ValidationError(f"{apparatus['name']} is recorded as changed, and no gate moved")
        if (
            apparatus["name"] == "ONYPHE"
            and apparatus["individual"] != package["individual_status"]["verdict"]
        ):
            raise ValidationError("the readiness record and the package disagree about ONYPHE")

    qualified = sum(
        1 for a in readiness["apparatuses"] if a["individual"] == "INDIVIDUALLY_QUALIFIED"
    )
    if readiness.get("qualified_apparatus_count") != qualified:
        raise ValidationError("the qualified count and the apparatus states disagree")
    if readiness.get("pair_analysis_ready") is not (
        qualified >= readiness.get("minimum_required", 2)
    ):
        raise ValidationError("§J: pair readiness requires at least two qualified apparatuses")

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

    construct = readiness["measurement_construct_unchanged"]
    if "SSH-" not in construct.get("quantity", ""):
        raise ValidationError(
            "§3: the construct is the literal prefix predicate and was not narrowed"
        )
    if construct.get("substituted_with_a_protocol_label") is not False:
        raise ValidationError("§3: protocol:ssh may not be substituted for the raw predicate")
    if construct.get("substituted_with_a_vendor_product") is not False:
        raise ValidationError("§3: a vendor product may not be substituted for the raw predicate")


def _validate_reconciliation(
    reconciliation: dict, package: dict, readiness: dict, user_api: dict, contact: dict
) -> None:
    outcome = reconciliation.get("primary_outcome")
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {outcome!r}")
    if not str(reconciliation.get("primary_outcome_statement", "")).strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")

    if (
        outcome == "ONYPHE_PUBLIC_DOCUMENTATION_CLOSES_ALL_RESIDUALS"
        and package["individual_status"]["verdict"] != "INDIVIDUALLY_QUALIFIED"
    ):
        raise ValidationError(
            "outcome A claims every residual closed while ONYPHE is not qualified"
        )

    secondary = reconciliation["secondary_outcomes"]
    if secondary.get("TOTAL_QUALIFIED_APPARATUSES") != readiness["qualified_apparatus_count"]:
        raise ValidationError("the reported qualified count disagrees with the readiness record")
    if (
        secondary.get("USER_API_SECRET_BEARING_DO_NOT_EXECUTE") is True
        and user_api["verdict"]["ENDPOINT_EXECUTION_SAFETY"] != "SECRET_BEARING_DO_NOT_EXECUTE"
    ):
        raise ValidationError("the reported User API outcome disagrees with the review")
    if (
        secondary.get("ONYPHE_SUPPORT_CONTACT_CHANNEL_ESTABLISHED") is True
        and contact["verdict"]["ONYPHE_SUPPORT_CONTACT_CHANNEL"] != "ESTABLISHED"
    ):
        raise ValidationError("the reported contact outcome disagrees with the reconciliation")

    boundaries = reconciliation["boundaries_held"]
    for name in (
        "api_executions_of_any_kind",
        "credentials_read",
        "enquiries_sent",
        "follow_ups_sent",
        "measurement_queries",
        "counts_fetched",
        "host_records_fetched",
        "banners_fetched",
        "trials",
        "purchases",
        "sources_registered",
        "governance_reviews",
        "thresholds_created",
        "claims_created",
        "evidence_created",
        "reliability_assigned",
        "independence_groups_created",
        "pairs_selected",
        "model_calls",
        "embeddings",
        "migrations_created",
        "canonical_mutations",
        "registry_additions",
    ):
        if boundaries.get(name) != 0:
            raise ValidationError(f"{name} reads {boundaries.get(name)!r} and must be 0")
    for name in (
        "user_api_executed",
        "mailbox_searched",
        "provider_reply_checked",
        "provider_reply_inferred",
        "resent_to_support",
        "netlas_sent",
        "netlas_address_guessed",
        "mission_1_65_rewritten",
        "frozen_enquiry_edited",
    ):
        if boundaries.get(name) is not False:
            raise ValidationError(f"{name} must be false")
    if boundaries.get("registry_count") != 14:
        raise ValidationError("§40: the registry stays at 14")
    if boundaries.get("reference_profile") != "UNCALIBRATED":
        raise ValidationError("nothing here calibrates a profile")
    if boundaries.get("problem_family") != "PARKED":
        raise ValidationError("Problem-Family stays PARKED")

    for name, value in reconciliation["stop_condition"].items():
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
                    raise ValidationError(f"a record uses {term!r}: {sentence[:110]!r}")


# --------------------------------------------------------------------------- render


def render_baseline(record: dict) -> str:
    pre = record["repository_precondition"]
    budget = record["documentation_budget"]
    boundary = record["source_boundary"]
    lines = [
        "# Mission 1.66.2 — baseline",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**Mission:** {record['mission']}  ",
        f"**Recorded:** {record['recorded_at']}",
        "",
        "## Precondition",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["Mission 1.66.1 merged", str(pre["mission_1_66_1_merged"])]),
        _row(["merge commit", f"`{pre['merge_commit_short']}`"]),
        _row(["operator report agrees with git", str(pre["operator_report_agrees_with_git"])]),
        _row(["working tree clean", str(pre["working_tree_clean"])]),
        _row(["migration head", f"`{pre['migration_head']}`"]),
        _row(["drift", f"**{record['canonical_baseline']['drift_from_mission_1_66_1']}**"]),
        "",
        "## Documentation budget",
        "",
        f"**{budget['used']} of {budget['maximum']} first-party document requests.**",
        "",
        _row(["#", "page", "sought", "outcome"]),
        _row(["---", "---", "---", "---"]),
    ]
    for entry in budget["requests"]:
        lines.append(
            _row([str(entry["n"]), f"`{entry['url']}`", entry["sought"], f"`{entry['outcome']}`"])
        )
    lines += [
        "",
        budget["one_path_was_wrong_and_that_cost_a_request"],
        "",
        budget["one_page_the_brief_expected_does_not_exist"],
        "",
        "## Source boundary",
        "",
        boundary["why_that_matters_here"],
        "",
    ]
    return "\n".join(lines)


def render_temporal(record: dict) -> str:
    disc = record["the_exact_discriminator"]
    says = record["what_the_pages_actually_say"]
    best = record["the_page_most_likely_to_answer_it_does_not"]
    verdict = record["verdict"]
    lines = [
        "# ONYPHE temporal object — public documentation review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**B2: `{verdict['B2']}`.** State: `{verdict['state']}`. Changed this mission: "
        f"**{verdict['changed_this_mission']}**.",
        "",
        "## The exact discriminator",
        "",
        disc["case"],
        "",
        _row(["if", "then"]),
        _row(["---", "---"]),
        _row(["yes", disc["if_yes"]]),
        _row(["no", disc["if_no"]]),
        _row(["the documentation does not say", disc["if_the_documentation_does_not_say"]]),
        "",
        disc["why_this_is_the_only_question_left"],
        "",
        "## What the pages actually say",
        "",
        _row(["function", "verbatim"]),
        _row(["---", "---"]),
    ]
    for fn in says["query_language_time_functions"]:
        lines.append(_row([f"`{fn['function']}`", f"*{fn['verbatim']}*"]))
    lines += [
        "",
        f"Default sort: *{says['default_sort']['verbatim']}*",
        "",
        f"Timestamp: *{says['timestamp_definition']['verbatim']}*",
        "",
        f"**{says['timestamp_definition']['why_it_does_not_settle_the_case']}**",
        "",
        "## The page most likely to answer it does not",
        "",
        f"**{best['page']}.** {best['why_it_was_the_best_candidate']}",
        "",
        best["finding"],
        "",
        f"*What that establishes:* {best['what_that_establishes']}",
        "",
        "## Inferences available and refused",
        "",
    ]
    for key, text in record["inferences_that_were_available_and_refused"].items():
        if key.startswith("$") or key == "the_rule":
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        f"**{record['inferences_that_were_available_and_refused']['the_rule']}**",
        "",
        f"*What would close it:* {record['what_would_close_it']['documentary']}. "
        f"{record['what_would_close_it']['empirical_route_refused']}",
        "",
        f"*Not promoted because:* {verdict['not_promoted_because']}",
        "",
    ]
    return "\n".join(lines)


def render_ports(record: dict) -> str:
    current = record["current_documented_configuration"]
    finding = record["the_finding_this_mission_adds"]
    drift = record["historical_configuration_drift"]
    tcp = record["tcp_22_membership"]
    addressable = record["configuration_time_addressability"]
    offered = record["candidate_registry_requirement_offered_and_not_added"]
    lines = [
        "# ONYPHE datascan port configuration — public documentation review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**TCP/22: `{tcp['verdict']}`.** Configuration time-addressability: "
        f"`{addressable['verdict']}`. Historically mutable: "
        f"**{drift['DATASCAN_CONFIGURATION_HISTORICALLY_MUTABLE']}**.",
        "",
        "## Current documented configuration",
        "",
        "*datascan, IP scanning:*",
        "",
    ]
    lines += [f"- *{i['verbatim']}*" for i in current["datascan_ip_scanning"]]
    lines += ["", "*ctiscan:*", ""]
    lines += [f"- *{i['verbatim']}*" for i in current["ctiscan"]]
    lines += [
        "",
        f"**{current['cardinality_is_not_membership']}**",
        "",
        f"## {finding['name']}",
        "",
        f"*Evidence:* {finding['evidence']}",
        "",
        finding["what_it_means"],
        "",
        f"**{finding['why_it_matters_for_the_construct']}**",
        "",
        f"*It is not a refutation:* {finding['it_is_not_a_refutation']}",
        "",
        "## Historical configuration drift",
        "",
        f"Basis: {drift['basis_page']}.",
        "",
    ]
    lines += [f"- *{v}*" for v in drift["verbatim"]]
    lines += [
        "",
        drift["the_sharpest_pair"]["reading"],
        "",
        f"*Not a contradiction:* {drift['the_sharpest_pair']['not_recorded_as_a_contradiction']}",
        "",
        f"**{drift['why_this_strengthens_rather_than_weakens_the_registry_rule']}**",
        "",
        "## TCP/22 membership",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["verdict", f"`{tcp['verdict']}`"]),
        _row(["sections printed", "; ".join(tcp["scanned_ports_page_sections_as_printed"])]),
        _row(["datascan TCP section exists", str(tcp["datascan_tcp_section_exists"])]),
        _row(["port 22 appears under", tcp["port_22_appears_under"]]),
        "",
        tcp["what_that_does_not_establish"],
        "",
        f"*Absence is not denial:* {tcp['absence_is_not_denial']}",
        "",
        "## Configuration time-addressability",
        "",
        addressable["why_not_addressable"],
        "",
        f"**{addressable['why_the_drift_makes_this_worse_rather_than_better']}**",
        "",
        f"## Offered and not added: `{offered['proposed_name']}`",
        "",
        offered["statement"],
        "",
        f"*Demonstrated by:* {offered['demonstrated_by']}",
        "",
        f"*Why it is not already represented:* {offered['why_it_is_not_already_represented']}",
        "",
        f"*Why it was not added here:* {offered['why_it_was_not_added_here']}",
        "",
        f"Registry unchanged at **{offered['REGISTRY_UNCHANGED']}**. Recommended adopter: "
        f"{offered['recommended_adopter']}.",
        "",
    ]
    return "\n".join(lines)


def render_user_api(record: dict) -> str:
    endpoint = record["endpoint"]
    exposes = record["what_the_documentation_says_it_exposes"]
    credential = record["the_credential_finding"]
    gap = record["the_configuration_semantic_gap"]
    verdict = record["verdict"]
    lines = [
        "# ONYPHE User API — configuration surface review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**`{verdict['ENDPOINT_EXECUTION_SAFETY']}`.** Datascan relevance: "
        f"`{verdict['DATASCAN_CONFIGURATION_RELEVANCE']}`. Executed: **{endpoint['EXECUTED']}**.",
        "",
        "## Why it was looked at at all",
        "",
        record["why_it_was_looked_at_at_all"]["the_appeal"],
        "",
        f"**{record['why_it_was_looked_at_at_all']['the_trap_in_that_appeal']}**",
        "",
        "## What the documentation says it exposes",
        "",
        _row(["kind", "what"]),
        _row(["---", "---"]),
    ]
    for c in exposes["categories"]:
        text = c.get("verbatim") or c.get("description", "")
        lines.append(_row([f"`{c['kind']}`", f"*{text}*" if c.get("verbatim") else text]))
    lines += [
        "",
        "## The credential finding",
        "",
        f"Exact wording: *{credential['exact_wording']}*",
        "",
        credential["what_is_established"],
        "",
        f"*What is not established:* {credential['what_is_not_established']}",
        "",
        f"**{credential['the_rule_this_rests_on']}**",
        "",
        f"*And it was not checked either:* {credential['no_credential_was_read_to_check']}",
        "",
        "## The configuration semantic gap",
        "",
        f"`USER_API_PORT_LIST_RESOURCE_MAPPING = {gap['USER_API_PORT_LIST_RESOURCE_MAPPING']}`",
        "",
        gap["why_the_gap_is_larger_than_it_looks"],
        "",
        f"*The inference refused:* {gap['the_inference_refused']}",
        "",
        f"**{verdict['both_reasons_are_independent']}**",
        "",
        f"*What a future mission may not do:* {verdict['what_a_future_mission_may_not_do']}",
        "",
    ]
    return "\n".join(lines)


def render_retention(record: dict) -> str:
    sentence = record["the_optimisation_sentence"]
    raw = record["raw_response_field"]
    fields = record["location_fields"]
    verdict = record["verdict"]
    lines = [
        "# ONYPHE retention — public documentation review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**Address `{verdict['ADDRESS_RETENTION']}`, observation time "
        f"`{verdict['OBSERVATION_TIME_RETENTION']}`, vantage "
        f"`{verdict['VANTAGE_FIELD_RETENTION']}`.**",
        "",
        "## Retention horizons",
        "",
        _row(["window", "categories"]),
        _row(["---", "---"]),
    ]
    for entry in record["retention_horizons"]["verbatim_categories"]:
        lines.append(_row([entry["window"], ", ".join(entry["categories"])]))
    lines += [
        "",
        record["retention_horizons"]["note_on_the_two_categories_this_arc_compares"],
        "",
        "## The optimisation sentence",
        "",
        f"> {sentence['verbatim']}",
        "",
        _row(["operation", "what"]),
        _row(["---", "---"]),
        _row(["REMOVED", sentence["two_operations_not_one"]["REMOVED"]]),
        _row(["TRUNCATED", sentence["two_operations_not_one"]["TRUNCATED"]]),
        "",
        f"**{sentence['two_operations_not_one']['why_the_distinction_holds']}**",
        "",
        f"*Effect on the construct:* {raw['effect_on_the_construct']} B3 stays `{raw['B3']}`.",
        "",
        f"*The temptation refused:* {raw['the_temptation_refused']}",
        "",
        "## Location fields",
        "",
        _row(["field", "post-30-day", "documented meaning"]),
        _row(["---", "---", "---"]),
    ]
    for name in ("ip", "@timestamp", "node.id", "node.country", "node.physicalcountry"):
        f = fields[name]
        lines.append(
            _row([f"`{name}`", f"**{f['post_30_day_state']}**", f"*{f['documented_definition']}*"])
        )
    lines += ["", "## Arguments available and refused", ""]
    for key, text in record["arguments_available_and_refused"].items():
        if key.startswith("$") or key == "the_rule":
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        f"**{record['arguments_available_and_refused']['the_rule']}**",
        "",
        f"*Why it is load-bearing:* {verdict['why_it_is_load_bearing']}",
        "",
    ]
    return "\n".join(lines)


def render_contact(record: dict) -> str:
    prior = record["what_mission_1_65_recorded"]
    evidence = record["the_new_first_party_evidence"]
    printed = record["on_the_printed_form"]
    lines = [
        "# ONYPHE contact channel — reconciliation",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**`{record['verdict']['ONYPHE_SUPPORT_CONTACT_CHANNEL']}`**, append-only. "
        f"Mission 1.65 rewritten: **{record['mission_1_65_rewritten']}**.",
        "",
        "## What Mission 1.65 recorded, and why it stands",
        "",
        f"> {prior['statement']}",
        "",
        prior["why_it_was_accurate"],
        "",
        f"**{prior['why_it_is_not_now_wrong']}**",
        "",
        f"*What would have been wrong:* {prior['what_would_have_been_wrong']}",
        "",
        "## The new first-party evidence",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["publication", evidence["publication"]]),
        _row(["url", f"`{evidence['url']}`"]),
        _row(["retrieved", evidence["retrieved_at"]]),
        _row(["as printed", f"`{evidence['address_as_printed']}`"]),
        _row(["occurrences", str(evidence["occurrences_on_the_page"])]),
        _row(["inferred from spelling", str(evidence["inferred_from_spelling"])]),
        "",
        f"> {evidence['verbatim_instruction']}",
        "",
        f"**{evidence['why_that_matters']}**",
        "",
        "## On the printed form",
        "",
        printed["how_this_differs_from_the_netlas_case"],
        "",
        f"*What a future mission must still do:* {printed['what_a_future_mission_must_still_do']}",
        "",
        "## What this does not authorise",
        "",
        record["what_this_does_not_authorise"]["the_existing_dispatch_remains_valid"],
        "",
        f"*Apparatus effect:* {record['verdict']['apparatus_effect']}",
        "",
    ]
    return "\n".join(lines)


def render_reassessment(record: dict) -> str:
    lines = [
        "# ONYPHE three-question reassessment",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**Answered by public documentation: "
        f"{record['summary']['questions_answered_by_public_documentation']} of 3.** The sent "
        f"enquiry was not edited.",
        "",
    ]
    for q in record["questions"]:
        lines += [
            f"## Q{q['n']} — {q['topic']}",
            "",
            f"Gate `{q['gate']}`. **`{q.get('classification') or q.get('overall')}`**",
            "",
        ]
        if q.get("subparts"):
            lines += [_row(["subpart", "classification"]), _row(["---", "---"])]
            # Question 2 subdivides into aspects of one question; question 3
            # subdivides into independent FIELDS. The keys differ because the
            # things differ, and forcing one name on both would flatten that.
            lines += [
                _row([s.get("subpart") or s["field"], f"`{s['classification']}`"])
                for s in q["subparts"]
            ]
            lines.append("")
        if q.get("what_the_public_documentation_added"):
            lines += [f"*Added:* {q['what_the_public_documentation_added']}", ""]
        if q.get("why_it_is_still_unresolved"):
            lines += [q["why_it_is_still_unresolved"], ""]
    lines += [
        "## The honest reading",
        "",
        record["summary"]["the_honest_reading"],
        "",
    ]
    return "\n".join(lines)


def render_package(record: dict) -> str:
    status = record["individual_status"]
    finding = record["the_finding_that_makes_B4_harder_rather_than_easier"]
    lines = [
        "# ONYPHE package — recomputed",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**`{status['verdict']}`.** Gates changed this mission: "
        f"**{record['gates_changed_this_mission']}**.",
        "",
        _row(["gate", "topic", "verdict", "changed"]),
        _row(["---", "---", "---", "---"]),
    ]
    for name, gate in record["gates"].items():
        lines.append(
            _row([f"`{name}`", gate["topic"], f"**{gate['verdict']}**", str(gate["changed"])])
        )
    lines += [
        "",
        "## What moved and what did not",
        "",
        f"Verdicts changed: **{record['what_moved_and_what_did_not']['verdicts_changed']}**. Evidence "
        "strengthened:",
        "",
    ]
    lines += [f"- {i}" for i in record["what_moved_and_what_did_not"]["evidence_strengthened"]]
    lines += [
        "",
        f"**{record['what_moved_and_what_did_not']['the_distinction_that_matters']}**",
        "",
        f"## {finding['name']}",
        "",
        f"*Basis:* {finding['basis']}",
        "",
        finding["effect"],
        "",
        f"*Recorded as a risk rather than a failure:* {finding['why_it_is_recorded_as_a_risk_rather_than_a_failure']}",
        "",
        "## Individual status",
        "",
        f"*Why not qualified:* {status['why_not_qualified']}",
        "",
        f"*Why not disqualified:* {status['why_not_not_qualified']}",
        "",
        f"**{status['the_temptation_named']}**",
        "",
    ]
    return "\n".join(lines)


def render_readiness(record: dict) -> str:
    arc = record["the_arc_position"]
    lines = [
        "# Qualified apparatus readiness",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**Qualified {record['qualified_apparatus_count']} of "
        f"{len(record['apparatuses'])}.** `{record['pair_analysis_state']}`.",
        "",
        _row(["apparatus", "status", "blocking", "researched here"]),
        _row(["---", "---", "---", "---"]),
    ]
    for a in record["apparatuses"]:
        lines.append(
            _row(
                [
                    a["name"],
                    f"`{a['individual']}`",
                    ", ".join(a["blocking"]),
                    str(a["researched_this_mission"]),
                ]
            )
        )
    lines += [
        "",
        "## Where the arc actually is",
        "",
        f"*Target:* {arc['target']}",
        "",
        f"*Distance:* {arc['distance_from_it']}",
        "",
        arc["what_has_actually_been_achieved"],
        "",
        "*What would move it:*",
        "",
    ]
    lines += [f"- {i}" for i in arc["what_would_move_it"]]
    lines += [
        "",
        f"*What would not:* {arc['what_would_not_move_it']}",
        "",
    ]
    return "\n".join(lines)


def render_reconciliation(record: dict) -> str:
    established = record["what_this_mission_actually_established"]
    reusable = record["the_reusable_observation"]
    nxt = record["next_mission_recommendation"]
    lines = [
        "# ONYPHE public documentation reconciliation",
        "",
        "Generated by `infrastructure/scripts/render_documentation_reconciliation.py`. Do not edit.",
        "",
        f"**Outcome: `{record['primary_outcome']}`**",
        "",
        record["primary_outcome_statement"],
        "",
        f"**This is a valid successful mission.** {record['this_is_a_valid_successful_mission']}",
        "",
        "## What this mission actually established",
        "",
    ]
    for key, item in established.items():
        if key.startswith("$"):
            continue
        lines += [
            f"**{key.split('_', 1)[1].replace('_', ' ')}** — {item['finding']}",
            "",
            f"*Status:* `{item['status']}`. *Consequence:* {item['consequence']}",
            "",
        ]
    lines += [
        "## The reusable observation",
        "",
        f"**{reusable['statement']}**",
        "",
        reusable["why_that_difference_is_operational"],
        "",
        f"*The earlier instance:* {reusable['the_earlier_instance']}",
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
        "## Next",
        "",
        f"**{nxt['name']}.** {nxt['why_now']}",
        "",
        "It should carry forward:",
        "",
    ]
    lines += [f"- {i}" for i in nxt["it_should_carry_forward"]]
    lines += ["", "It must not:", ""]
    lines += [f"- {i}" for i in nxt["it_must_not"]]
    lines += [
        "",
        f"*The parallel track:* {nxt['the_parallel_track']}",
        "",
        f"*Netlas:* {nxt['netlas_remains_independent']}",
        "",
        f"Awaiting: **{record['stop_condition']['awaiting']}**.",
        "",
    ]
    return "\n".join(lines)


RENDERERS = {
    BASELINE: render_baseline,
    RECONCILIATION: render_reconciliation,
    TEMPORAL: render_temporal,
    PORTS: render_ports,
    USER_API: render_user_api,
    RETENTION: render_retention,
    CONTACT: render_contact,
    REASSESSMENT: render_reassessment,
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
        print(f"REFUSED  documentation reconciliation: {error}")
        return 1

    rendered = {RENDERED[p]: RENDERERS[p](r) for p, r in zip(ORDER, records, strict=True)}

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(f"ok       {len(rendered)} reconciliation documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    reconciliation, package, readiness = records[1], records[8], records[9]
    print(f"outcome  {reconciliation['primary_outcome']}")
    print(
        f"onyphe   {package['individual_status']['verdict']}, gates changed {package['gates_changed_this_mission']}"
    )
    print(
        f"pairs    qualified {readiness['qualified_apparatus_count']}, {readiness['pair_analysis_state']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
