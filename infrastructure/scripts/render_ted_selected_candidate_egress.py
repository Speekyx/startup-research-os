"""Render and validate the TED selected-candidate egress review (Mission 1.83).

An egress review is a source-governance decision that this repository prepares and does not
take. The gate holds the record and its frozen decision packet to that, and refuses:

    A REVIEW THAT WIDENED ITS OWN SCOPE. One source, one use profile, one activity, one
    processing purpose, one selected subject. A record naming a second profile as covered, a
    second purpose, or an activity other than the one under review is refused, and so is one
    that quietly covers the commercial profile.

    A PERMISSION MANUFACTURED FROM AN ADJACENT RIGHT. Commercial reuse is not external-model
    permission; automated processing is not external-model permission; retrieval-method
    neutrality answers acquisition. Each is recorded as an argument that is not sufficient
    alone, and a record that promotes one to sufficient is refused.

    A GATE COLLAPSED INTO ANOTHER. ADR-033 keeps four questions apart. A source review may
    not name a vendor, a provider posture may not stand in for a source permission, and a
    source permission may not stand in for a provider approval.

    A REPRESENTATION THAT MOVED. The payload is allowlisted, carries no raw notice, no notice
    body, no API response and no personal data, and was not trimmed into validity. A digest
    that does not cover the payload the packet names is refused.

    AN APPROVAL NOBODY GAVE. No source review appended, no reviewer recorded, no option
    defaulted, no approval inferred from the mission having been launched. The decision
    packet's digest is recomputed here rather than trusted.

    AN ACTIVITY WIDENED IN PASSING. Training, fine-tuning and embeddings stay exactly as
    unassessed as they are, whatever is decided about inference.

    ANYTHING ELSE MOVED. Canonical research state, the selected candidate, the Evidence
    semantics and the parked arc are all unchanged, and the mission called no model.

    uv run python infrastructure/scripts/render_ted_selected_candidate_egress.py
    uv run python infrastructure/scripts/render_ted_selected_candidate_egress.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

REVIEW = DATA / "ted-selected-candidate-egress-review-v1.json"
REVIEW_MD = DATA / "ted-selected-candidate-egress-review-v1.md"
PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"
PACKET_MD = DATA / "ted-selected-candidate-egress-decision-packet-v1.md"
PREPARATION = DATA / "opportunity-preparation-v4.json"
SEMANTICS = DATA / "procurement-subject-semantics-class-grain-v1.json"
PROVIDER_POLICY = DATA / "model-provider-policy-v1.json"
CATALOG = DATA / "source-catalog-v1.json"

SOURCE_ID = "ted-eu"
USE_PROFILE = "local-private-research-v1"
ACTIVITY = "external_model_transmission"
SUBJECT = "ted-eu:CPV-class:9261"
LABEL = "Sports facilities operation services"

#: The seven outcomes Mission 1.83 §33 admits, and nothing else.
ACCEPTABLE_OUTCOMES = frozenset(
    {
        "TED_EGRESS_REVIEW_READY_FOR_OPERATOR_DECISION",
        "TED_EGRESS_ALREADY_COVERED_BY_CURRENT_REVIEW",
        "TED_EGRESS_AUTHORITY_INSUFFICIENT_FOR_DECISION",
        "TED_EXTERNAL_MODEL_TRANSMISSION_NOT_PERMITTED",
        "TED_EGRESS_PACKET_CONTAINS_UNEXPECTED_PERSONAL_DATA",
        "TED_EGRESS_REPRESENTATION_CONTRACT_VIOLATION",
        "TED_EGRESS_REVIEW_ARCHITECTURE_GAP",
    }
)

#: Every activity §10 requires to be assessed separately.
REQUIRED_ACTIVITIES = (
    "LOCAL_STORAGE",
    "DERIVED_ANALYTICS",
    "COMMERCIAL_PURPOSE",
    "EXTRACTION_CLASSIFICATION",
    "EXTERNAL_MODEL_TRANSMISSION",
    "MODEL_INFERENCE",
    "MODEL_TRAINING",
    "FINE_TUNING",
    "EMBEDDINGS",
    "PUBLIC_REDISTRIBUTION",
    "CUSTOMER_FACING_SOURCE_DATA",
)

#: The activities an inference decision may never widen (§11).
UNWIDENED_ACTIVITIES = ("MODEL_TRAINING", "FINE_TUNING", "EMBEDDINGS")

#: The four questions ADR-033 keeps apart.
FOUR_GATES = (
    "may_a_model_read_this_material",
    "may_it_leave_this_deployment",
    "what_does_the_processor_do_with_it",
    "does_this_deployment_permit_that_class_of_egress",
)

#: A source review states the PROPERTY a provider must have. A condition naming a vendor puts
#: provider governance inside the source registry, which ADR-033 separates on purpose.
VENDOR_NAMES = ("anthropic", "openai", "google", "gemini", "mistral", "cohere", "azure", "claude")

#: Personal-data classes §6 requires to be scanned for and reported.
PERSONAL_DATA_CLASSES = (
    "natural_person_name",
    "email",
    "telephone",
    "postal_address",
    "individual_contact_details",
    "supplier_contact_person",
    "buyer_contact_person",
    "free_text_notice_content",
    "other_personal_identifiers",
)

#: Everything the decision packet's digest binds (§20).
DIGEST_FIELDS = (
    "DECISION_PACKET_ID",
    "DECISION_PACKET_VERSION",
    "SOURCE_ID",
    "USE_PROFILE",
    "ACTIVITY",
    "PROCESSING_PURPOSE",
    "SUBJECT",
    "PACKET_ID",
    "REPRESENTATION_SCHEMA",
    "REPRESENTATION_SHA256",
    "REPRESENTATION_BOUNDARY",
    "RAW_TED_PAYLOAD_INCLUDED",
    "PERSONAL_DATA_INCLUDED",
    "NOTICE_BODY_INCLUDED",
    "TRAINING",
    "FINE_TUNING",
    "EMBEDDINGS",
    "PUBLIC_REDISTRIBUTION",
    "CUSTOMER_SOURCE_DATA_ACCESS",
    "CONDITIONS",
    "HELD_AUTHORITY",
    "OPEN_QUESTIONS",
    "PROPOSED_DECISION_OPTIONS",
)

#: The three options a decision packet offers, and none of them is a default.
DECISION_OPTIONS = ("PERMIT_WITH_EXACT_CONDITIONS", "DEFER", "REFUSE")


class ValidationError(Exception):
    """The record says something the evidence does not support."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def packet_digest(packet: dict) -> str:
    """Recompute the decision packet's digest from its own load-bearing fields.

    Option PROSE is excluded and option NAMES are bound: re-wording an explanation must not
    pass as a re-hash of the same decision, and it must not silently change one either.
    """
    bound: dict[str, object] = {}
    for field in DIGEST_FIELDS:
        if field not in packet:
            raise ValidationError(f"the decision packet is missing the bound field {field}")
        if field == "PROPOSED_DECISION_OPTIONS":
            bound[field] = [option["option"] for option in packet[field]]
        else:
            bound[field] = packet[field]
    payload = json.dumps(bound, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _check_the_scope(record: dict) -> None:
    """§2. One source, one profile, one activity, one purpose, one subject."""
    scope = record["scope"]
    if scope["source_id"] != SOURCE_ID:
        raise ValidationError(f"the review is scoped to {scope['source_id']!r}")
    if scope["use_profile_id"] != USE_PROFILE:
        raise ValidationError(f"the review is scoped to profile {scope['use_profile_id']!r}")
    if scope["activity"] != ACTIVITY:
        raise ValidationError(f"the review is scoped to activity {scope['activity']!r}")
    if scope["selected_subject"] != SUBJECT or scope["selected_label"] != LABEL:
        raise ValidationError("the review is scoped to a subject other than the selected one")
    if not str(scope["processing_purpose"]).strip():
        raise ValidationError("a review with no stated processing purpose")
    if not str(scope["purpose_basis"]).strip():
        raise ValidationError("a processing purpose with no stated basis in the vocabulary")
    outside = {item.lower() for item in scope["explicitly_out_of_scope"]}
    for required in (
        "commercial-multi-tenant-research-v1",
        "public redistribution",
        "resale",
        "model training",
        "fine-tuning",
        "embeddings",
    ):
        if required not in outside:
            raise ValidationError(f"{required!r} is not recorded as out of scope")


def _check_the_four_gates(record: dict) -> None:
    """§3. Four questions, kept apart, with the provider one reported separately."""
    gates = record["four_gates"]
    for gate in FOUR_GATES:
        if gate not in gates:
            raise ValidationError(f"the four-gate table omits {gate}")
        if not str(gates[gate]["state"]).strip():
            raise ValidationError(f"{gate}: no state")
        if not str(gates[gate]["where"]).strip():
            raise ValidationError(f"{gate}: no location for the field that decides it")
    if gates["may_it_leave_this_deployment"]["field"] != ACTIVITY:
        raise ValidationError("the egress gate does not name external_model_transmission")
    if gates["what_does_the_processor_do_with_it"]["where"].split(",")[0].strip() != (
        "docs/data/model-provider-policy-v1.json"
    ):
        raise ValidationError("the provider gate is not answered by the provider register")
    if not gates["source_and_provider_are_not_collapsed"]:
        raise ValidationError("the record admits collapsing the source and provider gates")
    if not gates["no_provider_named_in_the_source_review"]:
        raise ValidationError("the record admits naming a provider in the source review")
    open_gates = sum(
        1
        for gate in FOUR_GATES
        if gates[gate]["state"] not in ("NOT_ASSESSED", "NOT_ADDRESSED", "UNCLEAR", "NOT_APPROVED")
    )
    if gates["gates_open"] != open_gates:
        raise ValidationError(
            f"the record counts {gates['gates_open']} open gates, the states say {open_gates}"
        )
    if gates["gates_refusing"] != len(FOUR_GATES) - open_gates:
        raise ValidationError("the refusing-gate count does not follow from the states")


def _check_the_representation(record: dict, preparation: dict) -> None:
    """§4, §5 and §33. The exact payload, allowlisted, untrimmed, and hashed.

    A representation that fails its contract is REPRESENTABLE and carries its own outcome. A
    gate that could only express a clean payload would force a future violation to be recorded
    as something it is not, so what is refused is a violation beside an outcome that claims
    none, and a violation outcome with nothing wrong.
    """
    rep = record["representation"]
    violated = record["primary_outcome"] == "TED_EGRESS_REPRESENTATION_CONTRACT_VIOLATION"
    if rep["REPRESENTATION_SCHEMA"] != "opportunity-transmission-representation@1.0.0":
        raise ValidationError(
            f"an unreviewed representation schema {rep['REPRESENTATION_SCHEMA']!r}"
        )
    clean = rep["ALLOWLIST_VALID"] and rep["REPRESENTATION_VIOLATIONS"] == 0
    if violated and clean:
        raise ValidationError(
            "a representation-contract-violation outcome over a payload that satisfies the contract"
        )
    if not violated and not clean:
        raise ValidationError(
            "the representation does not satisfy its own contract, and the outcome does not say so"
        )
    if rep["trimmed_to_pass"]:
        raise ValidationError("the payload was trimmed into validity rather than refused")
    permitted = {
        "packet_id",
        "subject",
        "procedures",
        "source_families",
        "dimensions",
        "dimension_bounds",
        "independence",
        "claims",
        "evidence_ids",
    }
    keys = set(rep["TOP_LEVEL_KEYS"])
    if not keys <= permitted and not violated:
        raise ValidationError(f"payload keys outside the allowlist: {sorted(keys - permitted)}")
    if len(rep["REPRESENTATION_SHA256"]) != 64:
        raise ValidationError("the representation digest is not a sha256")
    if rep["SERIALIZED_CHARACTER_COUNT"] <= 0 or rep["CLAIM_COUNT"] <= 0:
        raise ValidationError("an empty representation")
    if rep["REAL_GATE_AVAILABILITY"] == "AVAILABLE":
        raise ValidationError(
            "the record claims the live gate authorises this packet; the activity it turns on is "
            "the one this review exists to put to a person"
        )
    if not rep["REAL_GATE_REFUSAL_REASONS"]:
        raise ValidationError("an unavailable gate with no stated reason")
    if rep["SUBJECT_LABEL_IN_PAYLOAD"] is not None:
        raise ValidationError("the retrieved label is in the payload; the code is the identity")

    packets = {p["subject"]: p for p in preparation["packets"]}
    if SUBJECT not in packets:
        raise ValidationError(f"{SUBJECT} has no packet in the current preparation")
    live = packets[SUBJECT]
    if rep["PACKET_ID"] != live["packet_id"]:
        raise ValidationError("the reviewed packet is not the current preparation's packet")
    if rep["EVIDENCE_COUNT"] != live["size"]:
        raise ValidationError("the reviewed packet's size is not the preparation's")

    # §4 required a recomputation rather than a carried-forward figure, so a record that
    # merely restates the earlier number without saying it recomputed is refused.
    recomputed = rep["mission_1_82_diagnostic_recomputed"]
    if recomputed["characters_now"] != rep["SERIALIZED_CHARACTER_COUNT"]:
        raise ValidationError("the recomputation block disagrees with the measured payload")
    if (
        recomputed["characters_now"] != recomputed["characters_then"]
        and not str(recomputed["why_the_character_count_differs"]).strip()
    ):
        raise ValidationError("a changed character count with no stated reason")
    if recomputed["mission_1_82_record_corrected"]:
        raise ValidationError("an earlier mission's record was rewritten rather than pointed at")


def _check_personal_data(record: dict) -> None:
    """§6 and §33. Measured over the payload, and a finding is representable.

    Unexpected personal data STOPS the mission with its own outcome, so a record must be able
    to say so. What is refused is personal data beside an outcome that claims none, and the
    silent repair: stripping a field rather than refusing the packet.
    """
    scan = record["personal_data"]
    found = record["primary_outcome"] == "TED_EGRESS_PACKET_CONTAINS_UNEXPECTED_PERSONAL_DATA"
    counts = [
        scan[field]
        for field in (
            "PERSONAL_DATA_FIELDS",
            "RAW_SOURCE_PAYLOAD_FIELDS",
            "NOTICE_BODY_FIELDS",
            "SOURCE_API_PAYLOAD_FIELDS",
        )
    ]
    for cls in PERSONAL_DATA_CLASSES:
        if cls not in scan:
            raise ValidationError(f"the personal-data scan does not report {cls}")
        counts.append(scan[cls])
    if found and not any(counts):
        raise ValidationError(
            "an unexpected-personal-data outcome over a payload the scan found nothing in"
        )
    if not found and any(counts):
        raise ValidationError(
            "the payload carries personal data, raw source payload, a notice body or an API "
            "payload, and the outcome does not say so. That packet is not the packet any "
            "decision here describes"
        )
    if scan["stripping_performed"]:
        raise ValidationError("personal data was stripped rather than the packet refused")
    if not str(scan["organisation_is_not_a_natural_person"]).strip():
        raise ValidationError("the organisation-versus-person distinction is not addressed")


def _check_the_authority(record: dict) -> None:
    """§7, §8 and §16. What the held material establishes, and what it does not."""
    held = record["held_authority"]
    if held["IS_THE_CURRENT_QUESTION_ALREADY_ANSWERED_BY_HELD_AUTHORITY"] not in (
        "YES",
        "NO",
        "PARTIAL",
    ):
        raise ValidationError("the held-authority verdict is not one of YES, NO, PARTIAL")
    if held["RESEARCH_DATA_FETCHES"] != 0:
        raise ValidationError("research data was acquired by a governance review")
    if held["HELD_AUTHORITY_COUNT"] != len(held["documents"]):
        raise ValidationError("the held-authority count is not the number of documents listed")
    for document in held["documents"]:
        if document["bears_on_this_question"] not in ("YES", "NO", "PARTIAL"):
            raise ValidationError(f"{document['title']}: bearing is not YES, NO or PARTIAL")
        if not str(document["what_it_does_not_establish"]).strip():
            raise ValidationError(
                f"{document['title']}: a document cited with no statement of what it does NOT "
                "establish, which is where an adjacent right becomes a permission"
            )
    if held["NEW_DOCUMENTATION_FETCHES"] and not str(held["why_no_new_fetch"]).strip():
        raise ValidationError("documentation was fetched with no stated residual")

    scan = held["mechanical_scan_of_the_held_decision_text"]
    for term in ("processor", "transmit", "transfer", "automated"):
        if scan[term] != 0:
            raise ValidationError(
                f"the held instrument is recorded as containing {term!r}; if it does, the act is "
                "addressed and the review owes a reading of that text rather than a judgement call"
            )


def _check_the_arguments(record: dict) -> None:
    """§8 and §22. An adjacent right is an argument, and silence is not permission."""
    arguments = record["arguments_toward_permission"]
    if not arguments:
        raise ValidationError("no argument toward permission is recorded, in either direction")
    for argument in arguments:
        if argument["sufficient_alone"]:
            raise ValidationError(
                f"{argument['id']}: an argument recorded as sufficient alone. Commercial reuse, "
                "automated processing, a bounded representation and a non-public counterparty are "
                "each an argument and none of them is the permission"
            )
        if not str(argument["why_not"]).strip():
            raise ValidationError(f"{argument['id']}: insufficient, with no stated reason")
        if not str(argument["authority"]).strip():
            raise ValidationError(f"{argument['id']}: an argument resting on no named authority")
    # §17 and §33, in both directions. A record that says the authority settles the question
    # MECHANICALLY has no residual to name, and demanding one would make that finding
    # unrepresentable. A record that names one while also saying no judgement is required is
    # saying two things at once.
    defeats = record["what_defeats_mechanical_closure"]
    requires_judgement = record["human_judgement"]["HUMAN_JUDGEMENT_REQUIRED"]
    if requires_judgement and not defeats:
        raise ValidationError(
            "nothing is recorded as defeating mechanical closure, yet the record asks a person"
        )
    if not requires_judgement and defeats:
        raise ValidationError(
            "the record names a residual that defeats mechanical closure and also records that no "
            "accountable judgement is required"
        )
    for item in defeats:
        if not str(item["closeable_by"]).strip():
            raise ValidationError(f"{item['id']}: a residual with no route to closing it")


def _check_the_activity_matrix(record: dict) -> None:
    """§10 and §11. Each activity separately, and an inference decision widens nothing."""
    matrix = record["activity_matrix"]
    for activity in REQUIRED_ACTIVITIES:
        if activity not in matrix:
            raise ValidationError(f"the activity matrix omits {activity}")
        entry = matrix[activity]
        if entry["changed"]:
            raise ValidationError(
                f"{activity}: the record marks an activity as CHANGED by a review that appends "
                "nothing. A state changes when a review is written, not when one is prepared"
            )
    for activity in UNWIDENED_ACTIVITIES:
        entry = matrix[activity]
        if entry["current"] != entry["proposed"]:
            raise ValidationError(f"{activity}: widened by a decision about inference")
        if entry["proposed"] in ("PERMITTED", "PERMITTED_WITH_CONDITIONS"):
            raise ValidationError(f"{activity}: proposed as permitted by an inference review")
    for activity in ("PUBLIC_REDISTRIBUTION", "CUSTOMER_FACING_SOURCE_DATA"):
        if matrix[activity]["proposed"] != "NOT_PERMITTED":
            raise ValidationError(f"{activity}: a local inference review does not grant it")
    reviewed = matrix["EXTERNAL_MODEL_TRANSMISSION"]
    covered = record["already_covered_check"]["TED_EGRESS_ALREADY_COVERED_BY_CURRENT_REVIEW"]
    if reviewed["current"] != "NOT_ASSESSED" and not covered:
        raise ValidationError(
            "the record states a current transmission state other than NOT_ASSESSED, which "
            "contradicts the measured registry state"
        )
    # §17 and §33. A permission is expressible where the authority MECHANICALLY settles the
    # activity, and only there. A gate that could only ever say "ask a person" would force a
    # future mechanical finding to be recorded as something it is not.
    if reviewed["proposed"] in ("PERMITTED", "PERMITTED_WITH_CONDITIONS"):
        if record["human_judgement"]["HUMAN_JUDGEMENT_REQUIRED"]:
            raise ValidationError(
                "the review proposes a permission for an activity it also records as requiring "
                "accountable human judgement"
            )
        answered = record["held_authority"][
            "IS_THE_CURRENT_QUESTION_ALREADY_ANSWERED_BY_HELD_AUTHORITY"
        ]
        if answered != "YES":
            raise ValidationError(
                "a proposed permission resting on held authority that does not answer the question"
            )
        if not str(reviewed.get("mechanical_basis", "")).strip():
            raise ValidationError(
                "a proposed permission with no stated mechanical basis; moving from documents to a "
                "permission by judgement is what the operator decision packet is for"
            )

    boundary = record["inference_is_not_training"]
    if boundary["MODEL_INFERENCE_and_MODEL_TRAINING_are_the_same_activity"]:
        raise ValidationError("inference and training recorded as one activity")
    for field in (
        "an_inference_approval_would_widen_training",
        "an_inference_approval_would_widen_fine_tuning",
        "an_inference_approval_would_widen_embeddings",
    ):
        if boundary[field]:
            raise ValidationError(f"{field} is true; §11 keeps the four apart")


def _check_purpose_and_attribution(record: dict) -> None:
    """§12 and §13. Purpose-bound, and an obligation neither injected nor dropped."""
    limit = record["purpose_limit"]
    if limit["source"] != SOURCE_ID or limit["use_profile"] != USE_PROFILE:
        raise ValidationError("the purpose limit names a different source or profile")
    if limit["activity"] != ACTIVITY:
        raise ValidationError("the purpose limit names a different activity")
    if limit["processing_purpose"] != record["scope"]["processing_purpose"]:
        raise ValidationError("the purpose limit and the scope name different purposes")
    if not str(limit["what_it_must_not_become"]).strip():
        raise ValidationError("a purpose limit that does not say what it must not become")

    attribution = record["attribution"]
    if attribution["ATTRIBUTION_REQUIRED"] and not str(attribution["obligation"]).strip():
        raise ValidationError("attribution required, with no stated obligation")
    if attribution["injected_into_the_packet_by_this_mission"]:
        raise ValidationError(
            "attribution was injected into the model packet, which changes the bytes an approval "
            "would name"
        )
    if attribution["dropped_because_the_use_is_internal"]:
        raise ValidationError("an attribution obligation dropped because the use is internal")
    if (
        attribution["ATTRIBUTION_REQUIRED"]
        and not attribution["already_satisfied_by_the_payload"]
        and not attribution["where_the_obligation_also_lives"]
    ):
        raise ValidationError("an unmet attribution obligation with nowhere recorded to meet it")


def _check_derived_output(record: dict) -> None:
    """§14. Neither unrestricted nor called redistribution without basis."""
    derived = record["derived_output"]
    if not str(derived["DERIVED_OUTPUT_STATUS"]).strip():
        raise ValidationError("no derived-output status")
    if not derived["DERIVED_OUTPUT_CONDITIONS"]:
        raise ValidationError(
            "derived output with no conditions; the reuse conditions travel with it unless the "
            "authority says otherwise, and no held document says otherwise"
        )
    if derived["is_it_unrestricted"]:
        raise ValidationError("derived output recorded as unrestricted with no authority saying so")
    if derived["is_it_redistribution_of_a_ted_database"] and not str(derived["why_not"]).strip():
        raise ValidationError("derived output labelled redistribution with no basis")


def _check_no_approval(record: dict, packet: dict) -> None:
    """§17, §18 and §19. The mission investigated; it did not grant."""
    judgement = record["human_judgement"]
    if judgement["impersonated_the_reviewer"]:
        raise ValidationError("the record admits impersonating the human reviewer")
    if judgement["claude_recorded_as_reviewer"]:
        raise ValidationError("a machine recorded as the human reviewer")
    if judgement["SOURCE_REVIEW_APPENDED"]:
        raise ValidationError(
            "a source review was appended by a mission that holds no explicit operator "
            "authorization for this packet"
        )
    if judgement["HUMAN_JUDGEMENT_REQUIRED"] and not judgement["OPERATOR_DECISION_PACKET_CREATED"]:
        raise ValidationError("judgement required and no decision packet was frozen")
    if not str(judgement["why_no_review_was_appended"]).strip():
        raise ValidationError("no review appended, and no reason recorded")

    if packet["approval_recorded"]:
        raise ValidationError(
            "the frozen packet records an approval. An approval is recorded BESIDE a frozen "
            "document, never inside it, so the bytes the operator read do not move when they answer"
        )
    if packet["default_option"] is not None:
        raise ValidationError("the decision packet defaults an option")
    offered = [option["option"] for option in packet["PROPOSED_DECISION_OPTIONS"]]
    if sorted(offered) != sorted(DECISION_OPTIONS):
        raise ValidationError(f"the decision packet offers {offered}, not the three §19 options")
    for option in packet["PROPOSED_DECISION_OPTIONS"]:
        if not str(option["cost"]).strip():
            raise ValidationError(f"{option['option']}: an option offered with no stated cost")


def _check_the_packet(record: dict, packet: dict) -> None:
    """§19 and §20. The frozen question, and a digest that could have failed."""
    if packet["SOURCE_ID"] != SOURCE_ID or packet["USE_PROFILE"] != USE_PROFILE:
        raise ValidationError("the decision packet names a different source or profile")
    if packet["ACTIVITY"] != ACTIVITY:
        raise ValidationError("the decision packet names a different activity")
    if packet["SUBJECT"] != SUBJECT:
        raise ValidationError("the decision packet names a different subject")
    if packet["PROCESSING_PURPOSE"] != record["scope"]["processing_purpose"]:
        raise ValidationError("the decision packet and the review name different purposes")
    if packet["REPRESENTATION_SHA256"] != record["representation"]["REPRESENTATION_SHA256"]:
        raise ValidationError(
            "the decision packet names a representation the review did not measure"
        )
    if packet["PACKET_ID"] != record["representation"]["PACKET_ID"]:
        raise ValidationError("the decision packet names a different Opportunity packet")
    for field in (
        "RAW_TED_PAYLOAD_INCLUDED",
        "PERSONAL_DATA_INCLUDED",
        "NOTICE_BODY_INCLUDED",
        "TRAINING",
        "FINE_TUNING",
        "EMBEDDINGS",
        "PUBLIC_REDISTRIBUTION",
        "CUSTOMER_SOURCE_DATA_ACCESS",
    ):
        if packet[field]:
            raise ValidationError(f"{field} is true in a packet that describes none of it")
    if not packet["CONDITIONS"]:
        raise ValidationError("a decision packet with no conditions")
    if not packet["OPEN_QUESTIONS"]:
        raise ValidationError(
            "a decision packet with no open questions, put to a person because questions remain"
        )
    if not packet["HELD_AUTHORITY"]:
        raise ValidationError("a decision packet resting on no held authority")
    blob = " ".join(packet["CONDITIONS"]).lower()
    for vendor in VENDOR_NAMES:
        if vendor in blob:
            raise ValidationError(
                f"a condition names the vendor {vendor!r}. A source review states the PROPERTY a "
                "provider must have; the provider register decides which providers have it"
            )
    recomputed = packet_digest(packet)
    if packet["DECISION_PACKET_SHA256"] != recomputed:
        raise ValidationError(
            f"the packet's digest is {packet['DECISION_PACKET_SHA256']} and its own bound fields "
            f"hash to {recomputed}"
        )
    named = record["decision_packet"]
    if named["DECISION_PACKET_SHA256"] != recomputed:
        raise ValidationError("the review names a digest the packet does not have")
    if named["DECISION_PACKET_ID"] != packet["DECISION_PACKET_ID"]:
        raise ValidationError("the review names a different decision packet")
    if named["approval_recorded"]:
        raise ValidationError("the review records an approval nobody gave")


def _check_already_covered(record: dict) -> None:
    """§24. Asked rather than assumed, and not forced."""
    covered = record["already_covered_check"]
    if covered["TED_EGRESS_ALREADY_COVERED_BY_CURRENT_REVIEW"]:
        if covered["external_model_transmission_on_that_row"] == "NOT_ASSESSED":
            raise ValidationError(
                "the record claims the question is already covered by a review whose own field "
                "reads NOT_ASSESSED"
            )
        if not any(
            covered[reason]
            for reason in (
                "stale_preparation",
                "wrong_review_version_read",
                "activity_resolution_defect",
                "purpose_resolution_defect",
            )
        ):
            raise ValidationError(
                "an already-covered finding contradicts the measured state and names no defect "
                "that would explain it"
            )
    if covered["current_profile"] != USE_PROFILE:
        raise ValidationError("the covered-check read a review under a different profile")


def _check_nothing_else_moved(record: dict, semantics: dict) -> None:
    """§25 to §30. The mission read; it did not write."""
    state = record["canonical_state"]
    if state["before"] != state["after"]:
        raise ValidationError("canonical state moved in a review mission")
    if state["CANONICAL_RESEARCH_MUTATION"] != 0:
        raise ValidationError("a canonical research mutation in a review mission")
    if state["source_review_rows_written"] or state["condition_verification_rows_written"]:
        raise ValidationError("registry rows were written by a mission that grants nothing")

    accounting = record["mission_accounting"]
    for key in (
        "MODEL_CALLS",
        "embeddings_created",
        "RESEARCH_DATA_FETCHES",
        "ted_api_calls",
        "ted_bulk_downloads",
        "new_raw_records",
        "new_normalized_records",
        "OPPORTUNITY_CREATED",
        "opportunity_revisions_created",
        "opportunity_links_created",
        "reliability_assessments_created",
        "independence_groups_created",
        "scores_persisted",
        "bytes_transmitted_to_any_external_model",
    ):
        if accounting[key] != 0:
            raise ValidationError(f"{key} is {accounting[key]}, and §28 to §30 require 0")

    candidate = record["selected_candidate_unchanged"]
    if candidate["SELECTED_SUBJECT"] != semantics["selection"]["SELECTED_SUBJECT"]:
        raise ValidationError("the selected subject moved")
    if candidate["SELECTED_LABEL"] != semantics["selection"]["SELECTED_LABEL"]:
        raise ValidationError("the selected label moved")
    for field in (
        "candidate_ranking_reopened",
        "descended_to_category_grain",
        "another_candidate_selected",
    ):
        if candidate[field]:
            raise ValidationError(f"{field} is true; this mission concerns a transmission gate")

    semantics_block = record["evidence_semantics_unchanged"]
    if semantics_block["claims_widened_by_this_mission"] != 0:
        raise ValidationError("Evidence semantics widened by an egress review")
    for forbidden in ("willingness to pay", "market size", "demand", "realised expenditure"):
        if forbidden not in semantics_block["does_not_establish"]:
            raise ValidationError(
                f"{forbidden!r} is not recorded among what the Evidence cannot say"
            )

    parked = record["parked_states_preserved"]
    if parked["changed_by_this_mission"]:
        raise ValidationError("a parked state changed")
    if parked["q1"]["CONSTRUCT_SELECTED"] or parked["q1"]["RUN_AUTHORIZED"]:
        raise ValidationError("Q1 moved")
    if (
        parked["globalping"]["PASS"],
        parked["globalping"]["PARTIAL"],
        parked["globalping"]["FAIL"],
    ) != (
        12,
        0,
        0,
    ):
        raise ValidationError("the Globalping tally moved")


def validate() -> tuple[dict, dict]:
    record = _load(REVIEW)
    packet = _load(PACKET)
    preparation = _load(PREPARATION)
    semantics = _load(SEMANTICS)

    if record["primary_outcome"] not in ACCEPTABLE_OUTCOMES:
        raise ValidationError(f"outcome {record['primary_outcome']!r} is not one of the seven")
    if not str(record["outcome_basis"]).strip():
        raise ValidationError("an outcome with no stated basis")

    _check_the_scope(record)
    _check_the_four_gates(record)
    _check_the_representation(record, preparation)
    _check_personal_data(record)
    _check_the_authority(record)
    _check_the_arguments(record)
    _check_the_activity_matrix(record)
    _check_purpose_and_attribution(record)
    _check_derived_output(record)
    _check_no_approval(record, packet)
    _check_the_packet(record, packet)
    _check_already_covered(record)
    _check_nothing_else_moved(record, semantics)

    if (
        record["primary_outcome"] == "TED_EGRESS_REVIEW_READY_FOR_OPERATOR_DECISION"
        and not record["human_judgement"]["OPERATOR_DECISION_PACKET_CREATED"]
    ):
        raise ValidationError("the ready-for-decision outcome with no frozen packet")
    if record["primary_outcome"] == "TED_EXTERNAL_MODEL_TRANSMISSION_NOT_PERMITTED":
        prohibition = record.get("explicit_prohibition")
        if not prohibition or not str(prohibition.get("source", "")).strip():
            raise ValidationError(
                "a not-permitted outcome must name the source and scope of the prohibition, and an "
                "operator may not turn an explicit prohibition into permission"
            )
    if (
        record["primary_outcome"] == "TED_EGRESS_AUTHORITY_INSUFFICIENT_FOR_DECISION"
        and not record["what_defeats_mechanical_closure"]
    ):
        raise ValidationError("an insufficient-authority outcome that states no residual")
    return record, packet


def render(record: dict) -> str:
    rep = record["representation"]
    gates = record["four_gates"]
    lines = [
        "# May the selected procurement candidate leave the deployment?",
        "",
        "Generated from `ted-selected-candidate-egress-review-v1.json`. Do not edit by hand.",
        "",
        f"**{record['primary_outcome']}** — `{record['scope']['selected_subject']}`, "
        f'"{record["scope"]["selected_label"]}"; decision packet '
        f"`{record['decision_packet']['DECISION_PACKET_ID']}` frozen and unapproved.",
        "",
        record["outcome_basis"],
        "",
        "## The four gates",
        "",
        "| question | field | where | state |",
        "|---|---|---|---|",
    ]
    questions = {
        "may_a_model_read_this_material": "may a model READ this material?",
        "may_it_leave_this_deployment": "may it LEAVE this deployment?",
        "what_does_the_processor_do_with_it": "what does the processor DO with it?",
        "does_this_deployment_permit_that_class_of_egress": "does this deployment permit that egress?",
    }
    for gate, question in questions.items():
        entry = gates[gate]
        lines.append(
            f"| {question} | `{entry['field']}` | {entry['where']} | **{entry['state']}** |"
        )
    lines += [
        "",
        f"{gates['gates_open']} of {len(FOUR_GATES)} are open and {gates['gates_refusing']} refuses. "
        "The one that refuses was never asked.",
        "",
        "## What would leave",
        "",
        f"Packet `{rep['PACKET_ID'][:16]}…`, {rep['CLAIM_COUNT']} claims over "
        f"{rep['EVIDENCE_COUNT']} Evidence rows, {rep['SERIALIZED_CHARACTER_COUNT']} characters, "
        f"digest `{rep['REPRESENTATION_SHA256'][:16]}…`, "
        f"{rep['REPRESENTATION_VIOLATIONS']} representation violations.",
        "",
        record["personal_data"]["what_the_payload_actually_carries"],
        "",
        f"Live gate: **{rep['REAL_GATE_AVAILABILITY']}**.",
        "",
        rep["mission_1_82_diagnostic_recomputed"]["why_the_character_count_differs"],
        "",
        "## Arguments toward permission, and why none is sufficient alone",
        "",
    ]
    for argument in record["arguments_toward_permission"]:
        lines.append(f"- **{argument['id']}.** {argument['statement']} *{argument['why_not']}*")
    lines += ["", "## What defeats mechanical closure", ""]
    for item in record["what_defeats_mechanical_closure"]:
        lines.append(f"- **{item['id']} ({item['kind']}).** {item['statement']}")
    lines += [
        "",
        "## Activities",
        "",
        "| activity | current | proposed |",
        "|---|---|---|",
    ]
    for activity in REQUIRED_ACTIVITIES:
        entry = record["activity_matrix"][activity]
        lines.append(f"| `{activity}` | {entry['current']} | {entry['proposed']} |")
    lines += [
        "",
        record["inference_is_not_training"]["why"],
        "",
        "## Attribution and derived output",
        "",
        record["attribution"]["obligation"],
        "",
        record["attribution"]["how"],
        "",
        f"**{record['derived_output']['DERIVED_OUTPUT_STATUS']}.** "
        f"{record['derived_output']['what_the_output_would_be']}",
        "",
        "## What this mission did not do",
        "",
        record["human_judgement"]["why_no_review_was_appended"],
        "",
        f"Canonical research mutation {record['canonical_state']['CANONICAL_RESEARCH_MUTATION']}, "
        f"model calls {record['mission_accounting']['MODEL_CALLS']}, research-data fetches "
        f"{record['mission_accounting']['RESEARCH_DATA_FETCHES']}, bytes transmitted to any "
        f"external model {record['mission_accounting']['bytes_transmitted_to_any_external_model']}.",
        "",
        f"**Next: {record['recommended_next_action']['id']}.** "
        f"{record['recommended_next_action']['shape']}",
        "",
    ]
    return "\n".join(lines)


def render_packet(packet: dict) -> str:
    lines = [
        f"# Decision packet {packet['DECISION_PACKET_ID']}",
        "",
        "Generated from `ted-selected-candidate-egress-decision-packet-v1.json`. "
        "Do not edit by hand.",
        "",
        f"**Version {packet['DECISION_PACKET_VERSION']}**, digest "
        f"`{packet['DECISION_PACKET_SHA256']}`.",
        "",
        packet["approval_note"],
        "",
        "## The question",
        "",
        f"- source `{packet['SOURCE_ID']}`",
        f"- use profile `{packet['USE_PROFILE']}`",
        f"- activity `{packet['ACTIVITY']}`",
        f"- processing purpose: {packet['PROCESSING_PURPOSE']}",
        f'- subject `{packet["SUBJECT"]}`, "{packet["SUBJECT_LABEL"]}"',
        f"- representation `{packet['REPRESENTATION_SCHEMA']}`, "
        f"{packet['REPRESENTATION_CLAIM_COUNT']} claims, "
        f"{packet['REPRESENTATION_CHARACTER_COUNT']} characters, digest "
        f"`{packet['REPRESENTATION_SHA256']}`",
        "",
        "## What is not in it",
        "",
    ]
    for field in (
        "RAW_TED_PAYLOAD_INCLUDED",
        "PERSONAL_DATA_INCLUDED",
        "NOTICE_BODY_INCLUDED",
        "TRAINING",
        "FINE_TUNING",
        "EMBEDDINGS",
        "PUBLIC_REDISTRIBUTION",
        "CUSTOMER_SOURCE_DATA_ACCESS",
    ):
        lines.append(f"- `{field}` = {str(packet[field]).lower()}")
    lines += ["", "## Held authority", ""]
    for item in packet["HELD_AUTHORITY"]:
        lines.append(f"- {item}")
    lines += ["", "## Finding", "", packet["REVIEW_FINDING"], "", "## Conditions", ""]
    for index, condition in enumerate(packet["CONDITIONS"], 1):
        lines.append(f"{index}. {condition}")
    lines += ["", "## Open questions", ""]
    for question in packet["OPEN_QUESTIONS"]:
        lines.append(f"- {question}")
    lines += ["", "## Options", "", "| option | means | cost |", "|---|---|---|"]
    for option in packet["PROPOSED_DECISION_OPTIONS"]:
        lines.append(f"| **{option['option']}** | {option['means']} | {option['cost']} |")
    lines += [
        "",
        "No option is defaulted. " + packet["default_note"] + ".",
        "",
        packet["digest_covers"] + ".",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        record, packet = validate()
    except ValidationError as error:
        print(f"REFUSED  ted selected-candidate egress review: {error}")
        return 1
    pages = ((REVIEW_MD, render(record)), (PACKET_MD, render_packet(packet)))
    if args.check:
        for path, text in pages:
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print("ok       the TED egress review matches its records")
        return 0
    for path, text in pages:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(
        f"packet   {packet['DECISION_PACKET_ID']} v{packet['DECISION_PACKET_VERSION']} "
        f"{packet['DECISION_PACKET_SHA256']}"
    )
    print("approval NOT RECORDED; this mission investigated and did not grant")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
