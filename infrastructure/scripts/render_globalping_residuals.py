"""Render and validate the Mission 1.74 Globalping residual closure.

Twelve records, and one discipline underneath all of them:

    EVERYTHING POINTS THE SAME WAY AND NOTHING COMMITS THE PROVIDER TO IT.

`validate()` enforces the readings this mission was most tempted to make and did
not:

  - an implementation is not a contract, and a dependency default is not a
    provider commitment;
  - zero matches for a word mean the word is absent, not that the behaviour is;
  - a source-code test is not a public API guarantee, and none was found anyway;
  - a commercial-use FAQ answer that defers to the Terms does not widen them;
  - a consumer-scoped liability clause does not bind business users;
  - a schema accepting a publicly reachable target is technical validation, not
    permission;
  - product design is not a grant, silence is not permission, and ambiguity is
    not a prohibition either;
  - governance does not bend to make a provider pass;
  - and a prepared enquiry is not an authorised one.

    uv run python infrastructure/scripts/render_globalping_residuals.py
    uv run python infrastructure/scripts/render_globalping_residuals.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.74-baseline-v1.json"
LEDGER = DATA / "mission-1.74-documentation-ledger-v1.json"
REDIRECT = DATA / "globalping-redirect-contract-review-v1.json"
TERMS_SCOPE = DATA / "globalping-provider-terms-scope-review-v1.json"
COMMERCIAL = DATA / "globalping-commercial-purpose-review-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v2.json"
READINESS = DATA / "q1-two-route-readiness-v2.json"
DECISION = DATA / "quantity-class-selection-decision-v4.json"
R1_PACKET = DATA / "globalping-r1-enquiry-packet-v1.json"
R2_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"

QUALIFICATION_V1 = DATA / "independent-http-counterpart-qualification-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
GOVERNANCE_DECISION = DATA / "public-http-observation-governance-decision-v1.json"
MINIMIZATION_1_72 = DATA / "public-http-data-minimization-policy-v1.json"

ORDER = [
    BASELINE,
    LEDGER,
    REDIRECT,
    TERMS_SCOPE,
    COMMERCIAL,
    THIRD_PARTY,
    CLOSURE,
    QUALIFICATION,
    READINESS,
    DECISION,
    R1_PACKET,
    R2_PACKET,
]

RENDERED = {
    DECISION: DATA / "mission-1.74-globalping-residuals-v1.md",
    REDIRECT: DATA / "globalping-redirect-evidence-v1.md",
}

R1_VERDICTS = (
    "R1_PASS_DOCUMENTED_NO_REDIRECT",
    "R1_FAIL_DOCUMENTED_REDIRECT_FOLLOWING",
    "R1_PARTIAL_IMPLEMENTATION_ONLY",
    "R1_UNKNOWN_NO_PROVIDER_CONTRACT",
)

# §3. Only a normative provider contract may close R1.
R1_CLOSING_EVIDENCE_LEVELS = (
    "R1_A_NORMATIVE_PROVIDER_CONTRACT",
    "R1_B_PROVIDER_MAINTAINED_IMPLEMENTATION_CONTRACT",
)
R1_NON_CLOSING_EVIDENCE_LEVELS = (
    "R1_C_IMPLEMENTATION_OBSERVED",
    "R1_D_DEPENDENCY_DEFAULT",
    "PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL",
)

GATE_STATUSES = ("PASS", "PARTIAL", "FAIL", "UNKNOWN")

MANDATORY_DIMENSIONS = (
    "C1_DIRECTABLE_TARGET",
    "C2_OWN_MEASUREMENT_PRODUCTION",
    "C3_TERMINAL_SUBMISSION_ACCOUNTING",
    "C4_TRANSPORT_LEVEL_RESULT_SURFACE",
    "C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY",
    "C6_REQUEST_CONTRACT_RECONSTRUCTABILITY",
    "C7_VANTAGE_REVIEWABILITY",
    "C8_RESULT_MINIMIZATION",
    "C9_RIGHTS_FEASIBILITY",
    "C10_INDEPENDENCE_PLAUSIBILITY",
    "C11_BOUNDED_PILOT_FEASIBILITY",
    "C12_SAME_HTTP_WORLD_STATE_FAMILY",
)

PRIMARY_OUTCOMES = (
    "GLOBALPING_COUNTERPART_QUALIFIED_Q1_SELECTED",
    "GLOBALPING_COUNTERPART_QUALIFIED",
    "GLOBALPING_ONE_RESIDUAL_REMAINS_PROVIDER_CLARIFICATION_REQUIRED",
    "GLOBALPING_TWO_PROVIDER_CLARIFICATIONS_REQUIRED",
    "GLOBALPING_REDIRECT_CONTRACT_CLOSED_RIGHTS_SCOPE_REMAINS",
    "GLOBALPING_RIGHTS_SCOPE_CLOSED_REDIRECT_CONTRACT_REMAINS",
    "GLOBALPING_PROVIDER_TERMS_BLOCK_INTENDED_ACTIVITY",
    "GLOBALPING_REDIRECT_CONTRACT_INCOMPATIBLE",
)

# §18 and §25. A sub-result restates a review verdict and may not drift from it.
COMMERCIAL_SUB_RESULT = {
    "COMMERCIAL_USE_GENERAL_PERMITTED_WITHIN_TERMS": "PERMITTED_WITHIN_TERMS",
    "COMMERCIAL_USE_GENERAL_UNRESOLVED": "UNRESOLVED",
    "COMMERCIAL_USE_GENERAL_PROHIBITED": "PROHIBITED",
}
THIRD_PARTY_SUB_RESULT = {
    "THIRD_PARTY_TARGET_SCOPE_WITHIN_PERMITTED_USE": "WITHIN_PERMITTED_USE",
    "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED": "UNRESOLVED",
    "THIRD_PARTY_TARGET_SCOPE_OUTSIDE_PERMITTED_USE": "OUTSIDE_PERMITTED_USE",
}

# §50.
FORBIDDEN_VOCABULARY = ("LEGAL", "UNLAWFUL", "DEFINITIVELY_LEGALLY_PERMITTED", "LEGAL_ADVICE")

HARD_ZERO = (
    "GLOBALPING_MEASUREMENTS_CREATED",
    "GLOBALPING_MEASUREMENTS_READ",
    "GLOBALPING_API_EXECUTIONS",
    "GLOBALPING_PROBE_RUNS",
    "TARGET_HTTP_REQUESTS",
    "SROS_FETCHER_RUNS",
    "TARGET_VALUE_EXPOSURES",
    "ACCOUNTS_CREATED",
    "TOKENS_CREATED",
    "TRIALS",
    "PURCHASES",
    "CREDENTIAL_READS",
    "MAILBOX_SEARCHES",
    "ENQUIRIES_SENT",
    "PROVIDER_CONTACTS",
    "ALTERNATIVE_COUNTERPARTS_EVALUATED",
    "SOURCES_REGISTERED",
    "SOURCE_GOVERNANCE_MUTATIONS",
    "THRESHOLDS_REGISTERED",
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
)

CENSUS_BLOCKS = ("canonical_baseline", "canonical_mutation_boundary", "mission_accounting")


class ValidationError(RuntimeError):
    """A record says something this mission's rules refuse."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _walk_outside_census(node, key=None):
    if key in CENSUS_BLOCKS:
        return
    yield node
    if isinstance(node, dict):
        for child_key, value in node.items():
            yield from _walk_outside_census(value, child_key)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_outside_census(item, key)


def _at(record: dict, path: list[str], message: str):
    node = record
    for key in path:
        if not isinstance(node, dict) or key not in node:
            raise ValidationError(f"{'.'.join(path)} is not recorded, so {message} is unchecked")
        node = node[key]
    return node


def _false(record: dict, path: list[str], message: str) -> None:
    if _at(record, path, message) is not False:
        raise ValidationError(message)


def _true(record: dict, path: list[str], message: str) -> None:
    if _at(record, path, message) is not True:
        raise ValidationError(message)


def _check_preconditions(baseline: dict, ledger: dict) -> None:
    """§0, §1, §45, §53."""
    pre = baseline["repository_precondition"]
    _true(
        baseline,
        ["repository_precondition", "mission_1_73_merged"],
        "the baseline does not record Mission 1.73 as merged",
    )
    if pre["observed_main"] != pre["expected_main"]:
        raise ValidationError("the observed main does not match the expected commit")
    if pre["expected_main"] != "2c05b73":
        raise ValidationError("the expected main is not the Mission 1.73 merge commit")
    for flag in (
        "local_matches_origin",
        "working_tree_clean",
        "adr_039_present",
        "globalping_qualification_package_present",
        "selected_quantity_class_artifact_absent",
        "selected_construct_artifact_absent",
    ):
        _true(baseline, ["repository_precondition", flag], f"the precondition {flag} is not met")
    _false(
        baseline,
        ["repository_precondition", "sros_fetcher_implemented"],
        "the SROS fetcher is implemented",
    )
    if (
        pre["globalping_initial_pass"],
        pre["globalping_initial_partial"],
        pre["globalping_initial_fail"],
    ) != (10, 2, 0):
        raise ValidationError(
            "the recorded initial Globalping state is not 10 PASS / 2 PARTIAL / 0 FAIL"
        )
    previous = _load(QUALIFICATION_V1)["tally"]
    if (previous["PASS"], previous["PARTIAL"], previous["FAIL"]) != (10, 2, 0):
        raise ValidationError("Mission 1.73's qualification record no longer says 10 / 2 / 0")

    if baseline["canonical_baseline"]["drift_from_mission_1_73"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["canonical_baseline"]["migration_head"] != "0035_refusal_provenance":
        raise ValidationError("the migration head moved")

    scope = baseline["scope"]
    if scope["only_candidate"] != "GLOBALPING":
        raise ValidationError("the candidate is not Globalping")
    if scope["alternative_counterparts_evaluated"] != 0:
        raise ValidationError("an alternative counterpart was evaluated")
    for flag in (
        "counterpart_discovery_performed",
        "quantity_class_discovery_performed",
        "scanner_discovery_performed",
        "construct_selected",
        "predicate_selected",
    ):
        _false(baseline, ["scope", flag], f"the scope records {flag}")

    if ledger["used"] > ledger["maximum_requests"]:
        raise ValidationError("the documentation budget was exceeded")
    for name, cap in ledger["caps"].items():
        if ledger["split"][name] > cap:
            raise ValidationError(f"the {name} sub-budget was exceeded")
    if sum(ledger["split"].values()) != ledger["used"]:
        raise ValidationError("the ledger split does not sum to the requests used")
    if len(ledger["requests"]) != ledger["used"]:
        raise ValidationError("the recorded requests do not match the count used")
    _true(ledger, ["failed_counted_against_budget"], "failed retrievals were not counted")
    for counter in ("globalping_api_executions", "target_http_requests"):
        if ledger[counter] != 0:
            raise ValidationError(f"{counter} is not zero")


def _check_r1(redirect: dict) -> None:
    """§3 to §10. The evidence grading is the whole point."""
    if redirect["verdict"] not in R1_VERDICTS:
        raise ValidationError(f"the R1 verdict {redirect['verdict']!r} is not one of the four")
    if not redirect["exact_question"]["question"].strip():
        raise ValidationError("the R1 question is empty")
    _false(
        redirect,
        ["exact_question", "broadened_into_generic_redirect_support"],
        "R1 was broadened into generic redirect support",
    )

    if not redirect["surfaces_reviewed"]:
        raise ValidationError("no surface was reviewed for R1")
    if len(redirect["surfaces_reviewed"]) != redirect["surfaces_reviewed_count"]:
        raise ValidationError("the surface count does not match the list")

    # §7. Zero matches are an absence in a surface, never a behavioural fact.
    _false(
        redirect,
        ["zero_matches_proves_no_redirect"],
        "zero documentation matches were treated as proving no redirect",
    )
    if redirect["zero_matches_means"] != "NOT_DOCUMENTED_IN_REVIEWED_SURFACE":
        raise ValidationError("zero matches are given the wrong meaning")

    # §8. Implementation may never be promoted to a contract.
    implementation = redirect["implementation"]
    if implementation["IMPLEMENTATION_CONTRACT_STATUS"] != "NON_NORMATIVE":
        raise ValidationError("the implementation was promoted to a normative contract")
    _false(
        implementation, ["run_against_a_live_target"], "the implementation was run against a target"
    )
    _false(
        implementation,
        ["local_redirect_test_constructed_and_presented_as_provider_behaviour"],
        "a local test was presented as provider behaviour",
    )

    # §3 level R1-D.
    _false(
        redirect,
        ["dependency_default", "globalping_normatively_binds_to_it"],
        "the dependency default is treated as a provider commitment",
    )
    _false(
        redirect,
        ["dependency_default", "can_close_r1_by_itself"],
        "the dependency default is treated as closing R1",
    )

    # §9.
    _false(
        redirect,
        ["provider_tests", "treated_as_public_api_contract"],
        "a provider test was treated as a public API contract",
    )

    level = redirect["evidence_level"]
    if level not in R1_CLOSING_EVIDENCE_LEVELS + R1_NON_CLOSING_EVIDENCE_LEVELS:
        raise ValidationError(f"the R1 evidence level {level!r} is undefined")
    if redirect["verdict"] == "R1_PASS_DOCUMENTED_NO_REDIRECT" and (
        level not in R1_CLOSING_EVIDENCE_LEVELS
    ):
        raise ValidationError(
            "R1 passes on evidence that cannot close it: only a normative provider contract may"
        )
    if redirect["verdict"] == "R1_FAIL_DOCUMENTED_REDIRECT_FOLLOWING" and (
        level not in R1_CLOSING_EVIDENCE_LEVELS
    ):
        raise ValidationError("R1 fails on evidence that is not a provider contract")
    if level in R1_NON_CLOSING_EVIDENCE_LEVELS and redirect["verdict"] in {
        "R1_PASS_DOCUMENTED_NO_REDIRECT",
        "R1_FAIL_DOCUMENTED_REDIRECT_FOLLOWING",
    }:
        raise ValidationError("a non-closing evidence level produced a closing verdict")

    for statement in redirect["provider_statements_found"]:
        if not str(statement["what_it_does_not_establish"]).strip():
            raise ValidationError("a provider statement is recorded with no stated limit")
        if statement["evidence_level"] in R1_CLOSING_EVIDENCE_LEVELS:
            raise ValidationError(
                "an incidental maintainer statement was graded as a closing evidence level"
            )


def _check_r2(terms: dict, commercial: dict, third_party: dict) -> None:
    """§11 to §26. Three questions, kept apart."""
    # §48.
    version = terms["terms_version"]
    for field in ("document", "source", "effective_date", "retrieved_at"):
        if not str(version[field]).strip():
            raise ValidationError(f"the terms version does not record {field}")
    _false(terms, ["versions_silently_combined"], "terms versions were silently combined")
    _false(
        terms,
        ["website_shell_versus_repository_copy", "favourable_version_chosen"],
        "a favourable terms version was chosen",
    )

    # §13, §14.
    if terms["consumer_commercial_clause"]["heading_scope"] not in {
        "CONSUMER_ONLY",
        "ALL_USERS",
        "AMBIGUOUS_SCOPE",
        "NOT_FOUND_CURRENT_VERSION",
    }:
        raise ValidationError("the consumer clause scope is undefined")
    if terms["consumer_commercial_clause"]["heading_scope"] == "CONSUMER_ONLY":
        _false(
            terms,
            ["consumer_commercial_clause", "applied_globally"],
            "a consumer-scoped clause was applied globally",
        )
    _false(
        terms,
        ["structure", "mention_treated_as_a_grant"],
        "a business-user mention was treated as a grant",
    )

    # §19.
    reservation = terms["reservation_of_rights"]
    if reservation["scope"] not in {"SERVICE_AND_IP_RIGHTS", "USE_PURPOSE_RIGHTS", "AMBIGUOUS"}:
        raise ValidationError("the reservation clause scope is undefined")
    _false(
        reservation,
        ["read_as_everything_unmentioned_is_prohibited"],
        "the reservation clause was read as prohibiting everything unmentioned",
    )
    _false(reservation, ["ignored"], "the reservation clause was ignored")
    _false(
        reservation,
        ["copyright_licence_semantics_imported_without_textual_basis"],
        "copyright-licence semantics were imported into a service-use clause",
    )

    # §20.
    _false(
        terms,
        ["prohibited_use", "absence_creates_a_grant"],
        "an absence from prohibited use was turned into a grant",
    )

    # §49.
    _false(
        terms,
        ["authority_ranking", "faq_may_override_contradictory_terms"],
        "the FAQ may override contradictory Terms",
    )
    _false(
        terms,
        ["authority_ranking", "examples_may_override_terms"],
        "examples may override the Terms",
    )

    # §12, §18. R2-A closes and must not be allowed to close R2-B.
    if commercial["verdict"] not in COMMERCIAL_SUB_RESULT:
        raise ValidationError("the commercial-use verdict is undefined")
    _false(
        commercial,
        ["overstated_beyond_the_provider_text"],
        "the commercial-use finding was overstated beyond the provider text",
    )
    _false(
        commercial,
        ["what_the_answer_does_not_do", "resolves_third_party_target_scope"],
        "the commercial FAQ was treated as resolving third-party target scope",
    )
    _false(
        commercial,
        ["what_the_answer_does_not_do", "widens_the_terms"],
        "the commercial FAQ was treated as widening the Terms",
    )
    _false(
        commercial,
        ["access_recorded_separately", "establishes_r2"],
        "public access was treated as establishing R2",
    )

    # §15, §16, §17, §21, §23.
    activity = third_party["frozen_intended_activity"]
    if not str(activity["description"]).strip():
        raise ValidationError("the intended activity is not frozen")
    _false(
        activity,
        ["simplified_to_commercial_scraping"],
        "the intended activity was simplified to commercial scraping",
    )
    _false(
        activity,
        ["simplified_to_monitoring_our_infrastructure"],
        "the intended activity was simplified to monitoring our own infrastructure",
    )

    permitted = third_party["permitted_use_section"]
    if permitted["is_it_an_exclusive_purpose_limitation"] not in {"YES", "NO", "AMBIGUOUS"}:
        raise ValidationError("the Permitted Use limitation question is unanswered")
    if not str(permitted["exact_wording"]).strip():
        raise ValidationError("the Permitted Use wording is not recorded")

    api = third_party["api_target_definition"]
    if api["classification"] != "TECHNICAL_TARGET_VALIDATION_ONLY":
        raise ValidationError("the API target schema is not classified as technical validation")
    _false(
        api,
        ["is_an_express_permitted_use_grant"],
        "a technical target schema was treated as a permitted-use grant",
    )

    design = third_party["product_design_evidence"]
    _false(design, ["product_design_is_a_terms_grant"], "product design was treated as a grant")
    _false(
        design, ["provider_examples_override_terms"], "examples were treated as overriding Terms"
    )

    if third_party["verdict"] not in THIRD_PARTY_SUB_RESULT:
        raise ValidationError("the third-party target scope verdict is undefined")
    _false(third_party, ["terms_silence_turned_favourable"], "terms silence was turned favourable")
    _false(
        third_party,
        ["terms_ambiguity_turned_into_prohibition"],
        "terms ambiguity was turned into a prohibition",
    )


def _check_closure(closure: dict, redirect: dict, commercial: dict, third_party: dict) -> None:
    """§25, §26, §38, §39, §51."""
    residuals = {r["id"]: r for r in closure["residuals"]}
    if residuals["R1"]["verdict"] != redirect["verdict"]:
        raise ValidationError("the closure record and the R1 review disagree")

    # A sub-result is the review's verdict said again; it may not say anything else.
    if closure["sub_results"]["R2_A_COMMERCIAL_USE"] != COMMERCIAL_SUB_RESULT.get(
        commercial["verdict"]
    ):
        raise ValidationError("the closure record and the commercial review disagree")
    if closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"] != THIRD_PARTY_SUB_RESULT.get(
        third_party["verdict"]
    ):
        raise ValidationError("the closure record and the third-party review disagree")

    both = closure["r2_pass_requires_both"]
    if both["A_commercial_purpose_compatible"] is not (
        closure["sub_results"]["R2_A_COMMERCIAL_USE"] == "PERMITTED_WITHIN_TERMS"
    ):
        raise ValidationError("the R2-A half does not follow its own sub-result")
    if both["B_third_party_targets_within_permitted_use"] is not (
        closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"] == "WITHIN_PERMITTED_USE"
    ):
        raise ValidationError("the R2-B half does not follow its own sub-result")

    # §25. R2 needs BOTH halves.
    if both["verdict"] == "R2_PASS" and not (
        both["A_commercial_purpose_compatible"]
        and both["B_third_party_targets_within_permitted_use"]
    ):
        raise ValidationError("R2 passes without both halves")
    if (
        both["A_commercial_purpose_compatible"]
        and both["B_third_party_targets_within_permitted_use"]
        and both["verdict"] != "R2_PASS"
    ):
        raise ValidationError("both R2 halves hold and R2 does not pass")

    remaining = sum(1 for r in closure["residuals"] if not r["closed"])
    if remaining != closure["residuals_remaining"]:
        raise ValidationError("the remaining-residual count does not match the list")

    governance = closure["project_governance_classification"]
    if governance["classification"] not in {
        "PROVIDER_TERMS_FEASIBLE",
        "PROVIDER_TERMS_REQUIRE_CLARIFICATION",
        "PROVIDER_TERMS_BLOCK_INTENDED_ACTIVITY",
        "UNKNOWN",
    }:
        raise ValidationError("the provider-terms classification is undefined")
    _false(
        governance,
        ["refusing_under_ambiguity_is_legal_impossibility"],
        "refusing under ambiguity is called legal impossibility",
    )

    # §51. ADR-039 does not bend.
    adr = closure["adr_039_unchanged"]
    for flag in (
        "head_transport_route_preserved",
        "body_retention_restriction_preserved",
        "source_collection_precedence_preserved",
        "robots_policy_preserved",
        "target_exclusion_preserved",
        "load_limits_preserved",
        "run_authorization_separation_preserved",
        "get_route_still_incompatible_with_the_initial_profile",
    ):
        _true(adr, [flag], f"ADR-039 was weakened: {flag}")
    minimization = _load(MINIMIZATION_1_72)
    if minimization["body"]["BODY_PERSISTENCE_DEFAULT"] != "DISABLED":
        raise ValidationError("the Mission 1.72 body persistence default was weakened")

    enquiries = closure["enquiries"]
    _false(
        enquiries,
        ["prepared_before_public_review_was_exhausted"],
        "an enquiry was prepared before the public review was exhausted",
    )
    _false(
        enquiries, ["combined_ambiguous_question_asked"], "a combined ambiguous question was asked"
    )
    _true(
        enquiries,
        ["each_question_maps_to_exactly_one_gate"],
        "a question does not map to exactly one gate",
    )
    if enquiries["enquiries_sent"] != 0:
        raise ValidationError("an enquiry was sent")
    _false(enquiries, ["operator_approval_recorded"], "an operator approval was recorded")
    _false(enquiries, ["dispatch_authorised_by_this_mission"], "this mission authorised a dispatch")
    _false(enquiries, ["provider_contacted"], "the provider was contacted")


def _check_packets(packets: list[dict], closure: dict) -> None:
    """§28, §30 to §34."""
    residuals = {r["id"]: r for r in closure["residuals"]}
    prepared = {p["residual_id"] for p in packets}
    for residual_id in prepared:
        if residual_id not in residuals:
            raise ValidationError(f"a packet names {residual_id}, which is not a residual")
    for residual_id, residual in residuals.items():
        if residual["enquiry_prepared"] is not (residual_id in prepared):
            raise ValidationError(
                f"{residual_id} records enquiry_prepared="
                f"{residual['enquiry_prepared']} and the packets say otherwise"
            )
        if not residual["closed"] and not residual["enquiry_prepared"]:
            raise ValidationError(
                f"{residual_id} is open and no enquiry was prepared, so nothing can close it"
            )
    for packet in packets:
        if packet["send_status"] != "NOT_AUTHORIZED":
            raise ValidationError(f"{packet['question_id']} is not marked NOT_AUTHORIZED")
        _false(packet, ["sent"], f"{packet['question_id']} is marked sent")
        _false(
            packet,
            ["operator_approval_recorded"],
            f"{packet['question_id']} records an operator approval",
        )
        _false(
            packet, ["execution_record_created"], f"{packet['question_id']} has an execution record"
        )
        _false(packet, ["recipient_guessed"], f"{packet['question_id']} guessed its recipient")
        for field in (
            "recipient",
            "channel",
            "first_party_channel_basis",
            "subject",
            "body",
            "why_public_documentation_is_insufficient",
            "expected_answer_discriminator",
        ):
            if not str(packet[field]).strip():
                raise ValidationError(f"{packet['question_id']} has an empty {field}")

        binding = {key: packet[key] for key in packet["hash_covers"]}
        digest = hashlib.sha256(
            json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        if digest != packet["content_sha256"]:
            raise ValidationError(f"{packet['question_id']} does not answer to its recorded hash")
        for excluded in ("content_sha256", "send_status", "recorded_at"):
            if excluded in packet["hash_covers"]:
                raise ValidationError(f"{packet['question_id']} hashes {excluded}")


def _check_qualification(qualification: dict, redirect: dict, closure: dict) -> None:
    """§35, §36."""
    gates = {g["dimension"]: g for g in qualification["gates"]}
    for dimension in MANDATORY_DIMENSIONS:
        if dimension not in gates:
            raise ValidationError(f"{dimension} was not recomputed")
        if gates[dimension]["status"] not in GATE_STATUSES:
            raise ValidationError(f"{dimension} carries an undefined status")
        if not str(gates[dimension]["why"]).strip():
            raise ValidationError(f"{dimension} carries no reason")

    tally = {name: 0 for name in GATE_STATUSES}
    for gate in qualification["gates"]:
        tally[gate["status"]] += 1
    if tally != qualification["tally"]:
        raise ValidationError("the recorded tally does not match the matrix")

    # C6 must follow R1 and C9 must follow R2.
    r1_closed = redirect["verdict"] == "R1_PASS_DOCUMENTED_NO_REDIRECT"
    if (gates["C6_REQUEST_CONTRACT_RECONSTRUCTABILITY"]["status"] == "PASS") is not r1_closed:
        raise ValidationError("C6 does not follow the R1 verdict")
    r2_closed = closure["r2_pass_requires_both"]["verdict"] == "R2_PASS"
    if (gates["C9_RIGHTS_FEASIBILITY"]["status"] == "PASS") is not r2_closed:
        raise ValidationError("C9 does not follow the R2 verdict")

    all_pass = all(gates[d]["status"] == "PASS" for d in MANDATORY_DIMENSIONS)
    if qualification["verdict"] == "COUNTERPART_QUALIFIED" and not all_pass:
        raise ValidationError(
            "the counterpart is qualified while a mandatory dimension is not PASS"
        )
    if all_pass and qualification["verdict"] != "COUNTERPART_QUALIFIED":
        raise ValidationError(
            "every mandatory dimension passes and the counterpart is not qualified"
        )
    _true(qualification, ["no_score_issued"], "a score was issued")

    # §35. A passing dimension may only be reopened by contradicting evidence.
    if (
        qualification["passing_dimensions_reopened"]
        and not qualification["contradicting_evidence_found"]
    ):
        raise ValidationError("a passing dimension was reopened with no contradicting evidence")


def _check_readiness_and_decision(readiness: dict, decision: dict, qualification: dict) -> None:
    """§37, §40, §41, §61."""
    conditions = readiness["conditions_for_strategic_viability"]
    qualified = qualification["verdict"] == "COUNTERPART_QUALIFIED"
    if conditions["one_external_counterpart_qualified"] is not qualified:
        raise ValidationError("the readiness record and the qualification disagree")
    viable = conditions["verdict"] == "STRATEGICALLY_VIABLE"
    required = (
        "sros_governance_track_ready",
        "one_external_counterpart_qualified",
        "independent_production_plausible",
        "common_http_world_state_family_exists",
    )
    if viable and not all(conditions[c] is True for c in required):
        raise ValidationError("Q1 is called viable with a condition unmet")
    if not viable and all(conditions[c] is True for c in required):
        raise ValidationError("every viability condition holds and Q1 is not viable")

    independence = readiness["independence"]
    if independence["evidence_independence_groups"] != 0:
        raise ValidationError("an independence group was created")
    for flag in (
        "called_an_independent_evidence_pair",
        "called_a_validated_evidence_pair",
        "called_corroborating_measurements",
    ):
        _false(independence, [flag], f"the record uses pair language: {flag}")
    if readiness["pair_analysis"] != "PAIR_ANALYSIS_NOT_READY":
        raise ValidationError("pair analysis is declared ready at the wrong layer")

    outcome = decision["primary_outcome"]
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"the primary outcome {outcome!r} is not defined")
    if decision["counterpart_qualified"] is not qualified:
        raise ValidationError("the decision and the qualification disagree")
    if (
        outcome
        in {"GLOBALPING_COUNTERPART_QUALIFIED", "GLOBALPING_COUNTERPART_QUALIFIED_Q1_SELECTED"}
        and not qualified
    ):
        raise ValidationError("a qualifying outcome was reported with no qualified counterpart")

    remaining = sum(1 for r in _load(CLOSURE)["residuals"] if not r["closed"])
    if (
        outcome == "GLOBALPING_ONE_RESIDUAL_REMAINS_PROVIDER_CLARIFICATION_REQUIRED"
        and remaining != 1
    ):
        raise ValidationError("the one-residual outcome was reported with a different count")
    if outcome == "GLOBALPING_TWO_PROVIDER_CLARIFICATIONS_REQUIRED" and remaining != 2:
        raise ValidationError("the two-clarification outcome was reported with a different count")
    if outcome == "GLOBALPING_PROVIDER_TERMS_BLOCK_INTENDED_ACTIVITY":
        blocked = _load(CLOSURE)["project_governance_classification"][
            "provider_terms_block_the_intended_activity"
        ]
        if blocked is not True:
            raise ValidationError("the terms-block outcome was reported from ambiguity")

    selected = decision["selected_quantity_class"]
    if selected is None:
        if decision["selection_outcome"] != "NO_SELECTION":
            raise ValidationError("nothing was selected and the outcome is not NO_SELECTION")
        _false(
            decision,
            ["selected_class_artifact_created"],
            "no class was selected and an artifact was recorded",
        )
        if SELECTED_CLASS.exists():
            raise ValidationError("selected-quantity-class-v1.json exists and nothing was selected")
    elif not (viable and qualified):
        raise ValidationError("a class was selected without a qualified counterpart and viability")
    _false(decision, ["selected_construct_created"], "a construct was selected")
    if SELECTED_CONSTRUCT.exists():
        raise ValidationError("a selected-construct artifact exists")

    for name, entry in decision["outcomes_considered_and_refused"].items():
        if entry["refused"] and not str(entry["why"]).strip():
            raise ValidationError(f"{name} was refused with no reason")

    # §50.
    _false(decision, ["legal_conclusion_made"], "a legal conclusion was made")
    if decision["external_legal_conclusion"] != "NO_EXTERNAL_LEGAL_CONCLUSION":
        raise ValidationError("an external legal conclusion was drawn")
    for banned in FORBIDDEN_VOCABULARY:
        if banned == outcome:
            raise ValidationError(f"the outcome uses forbidden vocabulary: {banned}")

    accounting = decision["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")
    if accounting["FIRST_PARTY_DOCUMENT_REQUESTS"] > accounting["FIRST_PARTY_REQUEST_BUDGET"]:
        raise ValidationError("the documentation budget was exceeded")

    parallel = decision["parallel_state_untouched"]
    for flag in (
        "onyphe_mailbox_searched",
        "netlas_enquiry_sent",
        "globalping_contacted",
        "scanner_arc_reopened",
        "adr_039_weakened",
        "public_http_governance_altered",
        "source_collection_gate_weakened",
        "alternative_counterpart_discovery_performed",
    ):
        _false(parallel, [flag], f"{flag} is true, and this mission may not do it")
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the decision record moves the ONYPHE response status")
    if parallel["netlas_contact_state"] != "STILL_PENDING":
        raise ValidationError("the decision record moves the Netlas contact state")
    if decision["canonical_mutation_boundary"]["mutations_this_mission"] != 0:
        raise ValidationError("a canonical mutation was recorded")
    _true(
        decision,
        ["recommended_next_action", "mission_1_75_not_started"],
        "the next mission was started",
    )
    _true(
        decision,
        ["recommended_next_action", "dispatch_requires_a_separate_explicitly_authorized_action"],
        "dispatch does not require a separate authorization",
    )


def _check_registry_and_governance(decision: dict, baseline: dict, records: list[dict]) -> None:
    """§52 and the standing rules."""
    requirements = _load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
    if len(requirements) != 15:
        raise ValidationError(f"the registry holds {len(requirements)} requirements, not 15")
    registry = decision["requirement_registry"]
    if registry["count_before"] != 15 or registry["count_after"] != len(requirements):
        raise ValidationError("the decision and the registry disagree on the count")
    if registry["requirement_added"] is not None:
        raise ValidationError("a requirement was added without change control")
    _false(registry, ["registry_growth_forced"], "registry growth was forced")
    if baseline["requirement_registry"]["count_before"] != len(requirements):
        raise ValidationError("the baseline and the registry disagree")

    governance = _load(GOVERNANCE_DECISION)
    if governance["decision"] != "PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED":
        raise ValidationError("Mission 1.72's governance decision was edited")

    for record in records:
        if record.get("exact_predicate_frozen") not in (None, False):
            raise ValidationError("a record froze an exact predicate")
        if record.get("target_values_retrieved") not in (None, 0):
            raise ValidationError("a record retrieved target values")
        for node in _walk_outside_census(record):
            if not isinstance(node, dict):
                continue
            for key, value in node.items():
                if (
                    "reliability" in key.lower()
                    and isinstance(value, (int, float))
                    and not isinstance(value, bool)
                ):
                    raise ValidationError(f"a reliability number appears: {key}")


def validate() -> list[dict]:
    records = [_load(path) for path in ORDER]
    (
        baseline,
        ledger,
        redirect,
        terms,
        commercial,
        third_party,
        closure,
        qualification,
        readiness,
        decision,
        r1_packet,
        r2_packet,
    ) = records

    _check_preconditions(baseline, ledger)
    _check_r1(redirect)
    _check_r2(terms, commercial, third_party)
    _check_closure(closure, redirect, commercial, third_party)
    _check_packets([r1_packet, r2_packet], closure)
    _check_qualification(qualification, redirect, closure)
    _check_readiness_and_decision(readiness, decision, qualification)
    _check_registry_and_governance(decision, baseline, records)

    parallel = baseline["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    if parallel["netlas_contact"] != "STILL_PENDING":
        raise ValidationError("the Netlas contact state moved")

    return records


# ------------------------------------------------------------------------ renderers


def render_decision(decision: dict) -> str:
    closure = _load(CLOSURE)
    qualification = _load(QUALIFICATION)
    commercial = _load(COMMERCIAL)
    third_party = _load(THIRD_PARTY)
    readiness = _load(READINESS)
    r1 = _load(R1_PACKET)
    r2 = _load(R2_PACKET)

    lines = [
        "# Mission 1.74 — Two residuals, two questions, nothing sent",
        "",
        "Generated from `quantity-class-selection-decision-v4.json` and the residual reviews.",
        "Do not edit by hand.",
        "",
        f"**Primary outcome: `{decision['primary_outcome']}`**",
        "",
        "## The two residuals",
        "",
        "| id | verdict | closed | enquiry |",
        "|---|---|---|---|",
    ]
    for residual in closure["residuals"]:
        lines.append(
            f"| {residual['id']} | `{residual['verdict']}` | {residual['closed']} "
            f"| {residual['enquiry_prepared']} |"
        )
    lines += ["", "What moved even though neither closed:", ""]
    for residual in closure["residuals"]:
        lines.append(f"- **{residual['id']}** — {residual['what_moved']}")

    lines += [
        "",
        "## R2 splits, and only one half closes",
        "",
        f"- **commercial use** — `{closure['sub_results']['R2_A_COMMERCIAL_USE']}`, on the "
        f'provider\'s own answer: *"{commercial["first_party_evidence"]["provider_answer"]}"*',
        f"- **third-party target scope** — "
        f"`{closure['sub_results']['R2_B_THIRD_PARTY_TARGET_SCOPE']}`",
        "",
        third_party["verdict_reasoning"],
        "",
        "## The twelve dimensions, recomputed",
        "",
        "| dimension | status | recomputed |",
        "|---|---|---|",
    ]
    for gate in qualification["gates"]:
        lines.append(f"| `{gate['dimension']}` | `{gate['status']}` | {gate['recomputed']} |")
    tally = qualification["tally"]
    lines += [
        "",
        f"**{tally['PASS']} PASS, {tally['PARTIAL']} PARTIAL, {tally['FAIL']} FAIL.** "
        f"Tally changed: **{qualification['tally_changed']}**. "
        f"Passing dimensions reopened: **{qualification['passing_dimensions_reopened']}**.",
        "",
        "What the mission added even though the tally did not move:",
        "",
    ]
    for item in qualification["what_this_mission_added_even_though_the_tally_did_not_move"]:
        lines.append(f"- {item}")

    lines += [
        "",
        "## Why this outcome and not the others",
        "",
        "| outcome | refused because |",
        "|---|---|",
    ]
    for name, entry in decision["outcomes_considered_and_refused"].items():
        lines.append(f"| {name} | {entry['why']} |")

    lines += [
        "",
        "## The two frozen enquiries",
        "",
        "| id | residual | channel | hash | status |",
        "|---|---|---|---|---|",
        f"| {r1['question_id']} | {r1['residual_id']} | `{r1['channel']}` "
        f"| `{r1['content_sha256'][:16]}…` | **{r1['send_status']}** |",
        f"| {r2['question_id']} | {r2['residual_id']} | `{r2['channel']}` "
        f"| `{r2['content_sha256'][:16]}…` | **{r2['send_status']}** |",
        "",
        closure["enquiries"]["two_packets_because"],
        "",
        f"**Enquiries sent: {closure['enquiries']['enquiries_sent']}. Operator approval recorded: "
        f"{closure['enquiries']['operator_approval_recorded']}. Provider contacted: "
        f"{closure['enquiries']['provider_contacted']}.**",
        "",
        "## Q1",
        "",
        f"`{readiness['q1_status_after']}`, unchanged "
        f"({readiness['q1_status_changed_this_mission']}). Failing on "
        f"`{readiness['conditions_for_strategic_viability']['load_bearing_failure']}`.",
        "",
        f"Independence: `{readiness['independence']['classification']}`, "
        f"{readiness['independence']['evidence_independence_groups']} groups, "
        f"`{readiness['pair_analysis']}`.",
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    accounting = decision["mission_accounting"]
    for counter in (
        "GLOBALPING_API_EXECUTIONS",
        "GLOBALPING_MEASUREMENTS_CREATED",
        "TARGET_HTTP_REQUESTS",
        "SROS_FETCHER_RUNS",
        "ACCOUNTS_CREATED",
        "TOKENS_CREATED",
        "CREDENTIAL_READS",
        "ENQUIRIES_SENT",
        "PROVIDER_CONTACTS",
        "ALTERNATIVE_COUNTERPARTS_EVALUATED",
        "CLAIMS_CREATED",
        "INDEPENDENCE_GROUPS_CREATED",
        "MODEL_CALLS",
    ):
        lines.append(f"| {counter} | {accounting[counter]} |")
    lines.append("")
    return "\n".join(lines)


def render_redirect(redirect: dict) -> str:
    lines = [
        "# Mission 1.74 — The redirect evidence, graded",
        "",
        "Generated from `globalping-redirect-contract-review-v1.json`. Do not edit by hand.",
        "",
        "**The question:**",
        "",
        f"> {redirect['exact_question']['question']}",
        "",
        "## Why it is load-bearing",
        "",
        redirect["why_it_is_load_bearing"]["statement"],
        "",
        "## Surfaces reviewed",
        "",
        "| surface | redirect mentions | relevant to HTTP measurement |",
        "|---|---|---|",
    ]
    for surface in redirect["surfaces_reviewed"]:
        relevant = surface.get("relevant_to_http_measurement", True)
        lines.append(f"| {surface['surface']} | {surface['redirect_mentions']} | {relevant} |")
    lines += ["", "Notes:", ""]
    for surface in redirect["surfaces_reviewed"]:
        lines.append(f"- **{surface['surface']}** — {surface['note']}")

    lines += [
        "",
        f"**Documented in any reviewed surface: {redirect['documented_in_any_reviewed_surface']}.**",
        f"Zero matches mean `{redirect['zero_matches_means']}`, and that they prove no redirect is",
        f"**{redirect['zero_matches_proves_no_redirect']}**.",
        "",
        "## What the provider did say",
        "",
    ]
    for statement in redirect["provider_statements_found"]:
        lines += [
            f"From {statement['locator']}, by a {statement['author_role']}:",
            "",
            f"> {statement['quotation']}",
            "",
            f"*Establishes:* {statement['what_it_establishes']}",
            "",
            f"*Does not establish:* {statement['what_it_does_not_establish']}",
            "",
            f"*Graded:* `{statement['evidence_level']}`",
            "",
        ]

    implementation = redirect["implementation"]
    lines += [
        "## Implementation, kept in its place",
        "",
        f"- follows redirects: **{implementation['CURRENT_IMPLEMENTATION_FOLLOWS_REDIRECTS']}**",
        f"- contract status: **{implementation['IMPLEMENTATION_CONTRACT_STATUS']}**",
        f"- run against a live target: **{implementation['run_against_a_live_target']}**",
        f"- provider tests asserting redirect behaviour: "
        f"**{redirect['provider_tests']['tests_asserting_http_measurement_redirect_behaviour']}**",
        "",
        "## Verdict",
        "",
        f"**`{redirect['verdict']}`**, at evidence level `{redirect['evidence_level']}`.",
        "",
        redirect["verdict_reasoning"],
        "",
        f"*Why the maintainer statement did not upgrade it:* {redirect['why_not_upgraded']}",
        "",
    ]
    return "\n".join(lines)


RENDERERS = {DECISION: render_decision, REDIRECT: render_redirect}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  Globalping residual closure: {error}")
        return 1

    by_path = dict(zip(ORDER, records, strict=True))
    rendered = {RENDERED[path]: RENDERERS[path](by_path[path]) for path in RENDERERS}

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(f"ok       {len(rendered)} Globalping residual documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    print(f"outcome  {by_path[DECISION]['primary_outcome']}")
    print(f"R1       {by_path[REDIRECT]['verdict']}")
    print(f"R2       {by_path[CLOSURE]['r2_pass_requires_both']['verdict']}")
    print(f"verdict  {by_path[QUALIFICATION]['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
