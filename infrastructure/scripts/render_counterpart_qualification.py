"""Render and validate the Mission 1.73 independent HTTP counterpart qualification.

Eleven records, and one discipline underneath all of them:

    THE PRODUCER OF AN OBSERVATION IS NOT THE BRAND ON THE API, AND A CONTRACT
    THAT IS MERELY IMPLEMENTED IS NOT A CONTRACT THAT IS DOCUMENTED.

`validate()` enforces the readings this mission was most tempted to make and did
not:

  - a reseller, a proxy, or the SROS fetcher on somebody else's cloud is not a
    second apparatus;
  - shared software is not shared measurement, and a different vantage is not
    independence;
  - an externally triggered job can still be independently produced, and an
    external analysis of an SROS response cannot;
  - a provider job failure is not the target's silence, and a target may not
    vanish after submission;
  - a body may not be ingested in order to extract a status;
  - an undocumented redirect default is not an equivalent request contract,
    however clearly the source happens to behave today;
  - a free API is not commercial permission, silence is not permission, and the
    provider's terms do not replace ADR-039;
  - and Q1 is not selected while no counterpart is qualified.

    uv run python infrastructure/scripts/render_counterpart_qualification.py
    uv run python infrastructure/scripts/render_counterpart_qualification.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.73-baseline-v1.json"
UNIVERSE = DATA / "independent-http-counterpart-universe-v1.json"
PRESCREEN = DATA / "independent-http-counterpart-prescreen-v1.json"
LEDGER = DATA / "mission-1.73-documentation-ledger-v1.json"
QUALIFICATION = DATA / "independent-http-counterpart-qualification-v1.json"
LINEAGE = DATA / "counterpart-measurement-lineage-v1.json"
CONTRACT = DATA / "counterpart-request-contract-compatibility-v1.json"
MINIMIZATION = DATA / "counterpart-result-minimization-v1.json"
RIGHTS = DATA / "counterpart-rights-feasibility-v1.json"
READINESS = DATA / "q1-two-route-readiness-v1.json"
DECISION = DATA / "quantity-class-selection-decision-v3.json"

SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
ADR_039 = (
    ROOT / "docs" / "architecture" / "adr" / "ADR-039-public-http-observation-governance-track.md"
)
GOVERNANCE_DECISION = DATA / "public-http-observation-governance-decision-v1.json"
APPARATUS_CONTRACT = DATA / "sros-bounded-http-apparatus-contract-v1.json"

ORDER = [
    BASELINE,
    UNIVERSE,
    PRESCREEN,
    LEDGER,
    QUALIFICATION,
    LINEAGE,
    CONTRACT,
    MINIMIZATION,
    RIGHTS,
    READINESS,
    DECISION,
]

RENDERED = {
    DECISION: DATA / "mission-1.73-counterpart-qualification-v1.md",
    QUALIFICATION: DATA / "counterpart-qualification-matrix-v1.md",
}

GATE_STATUSES = (
    "PASS",
    "PARTIAL",
    "FAIL",
    "UNKNOWN",
    "NOT_APPLICABLE",
    "NOT_EVALUATED_AFTER_DECISIVE_FAIL",
)

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

PRODUCER_KINDS = (
    "PROVIDER_OWN_MEASUREMENT",
    "PROVIDER_OPERATED_OPEN_SOURCE_ENGINE",
    "THIRD_PARTY_MEASUREMENT_UPSTREAM",
    "CUSTOMER_EXECUTED_CODE",
    "PURE_PROXY",
    "UNKNOWN",
)

# §6. Producer kinds that can never be an independent counterpart.
DISQUALIFYING_PRODUCERS = ("THIRD_PARTY_MEASUREMENT_UPSTREAM", "PURE_PROXY", "UNKNOWN")

VERDICTS = ("COUNTERPART_QUALIFIED", "COUNTERPART_NOT_QUALIFIED", "COUNTERPART_UNRESOLVED")

PRIMARY_OUTCOMES = (
    "INDEPENDENT_HTTP_COUNTERPART_QUALIFIED",
    "INDEPENDENT_HTTP_COUNTERPART_QUALIFIED_Q1_SELECTED",
    "COUNTERPART_EPISTEMICALLY_QUALIFIED_ACCESS_REVIEW_REQUIRED",
    "COUNTERPART_FOUND_REQUEST_CONTRACT_UNRESOLVED",
    "COUNTERPART_FOUND_MISSINGNESS_SEMANTICS_UNRESOLVED",
    "COUNTERPART_FOUND_RESULT_SURFACE_INCOMPATIBLE",
    "COUNTERPART_FOUND_LINEAGE_UNRESOLVED",
    "COUNTERPART_FOUND_COMMERCIAL_PURPOSE_GAP",
    "NO_COMPATIBLE_INDEPENDENT_HTTP_COUNTERPART_IDENTIFIED_WITHIN_BOUNDED_SEARCH",
)

RIGHTS_CLASSIFICATIONS = (
    "COMMERCIAL_PURPOSE_PLAUSIBLE",
    "DEDICATED_GOVERNANCE_REVIEW_REQUIRED",
    "NONCOMMERCIAL_ONLY",
    "PROHIBITED_FOR_INTENDED_USE",
    "UNKNOWN",
)

HARD_ZERO = (
    "COUNTERPART_API_EXECUTIONS",
    "TARGET_HTTP_REQUESTS",
    "SROS_FETCHER_RUNS",
    "EXTERNAL_MEASUREMENT_JOBS",
    "COMMON_CRAWL_QUERIES",
    "HTTP_ARCHIVE_BIGQUERY",
    "HAR_DOWNLOADS",
    "WARC_DOWNLOADS",
    "TARGET_VALUE_EXPOSURES",
    "ACCOUNTS_CREATED",
    "TRIALS",
    "PURCHASES",
    "CREDENTIAL_READS",
    "MAILBOX_SEARCHES",
    "ENQUIRIES_SENT",
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
    "COUNTERPARTS_SELECTED",
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


def _check_preconditions(baseline: dict) -> None:
    """§0, §1, §58."""
    pre = baseline["repository_precondition"]
    _true(
        baseline,
        ["repository_precondition", "mission_1_72_merged"],
        "the baseline does not record Mission 1.72 as merged",
    )
    if pre["observed_main"] != pre["expected_main"]:
        raise ValidationError("the observed main does not match the expected commit")
    for flag in (
        "local_matches_origin",
        "working_tree_clean",
        "adr_039_present",
        "public_http_governance_artifacts_present",
        "apparatus_contract_present",
        "selected_quantity_class_artifact_absent",
        "selected_construct_artifact_absent",
    ):
        _true(baseline, ["repository_precondition", flag], f"the precondition {flag} is not met")
    _false(
        baseline,
        ["repository_precondition", "sros_fetcher_implementation_exists"],
        "an SROS fetcher implementation exists",
    )
    if not ADR_039.exists():
        raise ValidationError("ADR-039 does not exist")

    if baseline["canonical_baseline"]["drift_from_mission_1_72"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["canonical_baseline"]["migration_head"] != "0035_refusal_provenance":
        raise ValidationError("the migration head moved")

    for flag in (
        "quantity_class_discovery_performed",
        "scanner_discovery_performed",
        "general_web_source_discovery_performed",
        "common_crawl_http_archive_analysis_reopened",
        "construct_selected",
        "predicate_selected",
        "market_landscape_produced",
    ):
        _false(baseline, ["scope", flag], f"the scope records {flag}")


def _check_universe(universe: dict, ledger: dict) -> None:
    """§2, §3, §52."""
    if universe["serious_candidates"] > universe["serious_candidate_cap"]:
        raise ValidationError("more serious candidates than the cap permits")
    _false(universe, ["cap_exceeded"], "the serious candidate cap was exceeded")
    _false(
        universe, ["exhaustive_market_coverage_claimed"], "exhaustive market coverage is claimed"
    )

    # §2's cap is a budget on DEEP evaluation, so a candidate that reached a verdict
    # consumed a slot. DISCOVERED and PRE_GATE_FAILED never did.
    seriously_evaluated = {"SERIOUS", "QUALIFIED", "NOT_QUALIFIED", "UNRESOLVED"}
    serious = sum(1 for c in universe["candidates"] if c["status"] in seriously_evaluated)
    if serious != universe["serious_candidates"]:
        raise ValidationError("the serious candidate count does not match the list")
    if len(universe["candidates"]) != universe["candidates_discovered"]:
        raise ValidationError("the discovered count does not match the list")
    for candidate in universe["candidates"]:
        if candidate["status"] not in {
            "DISCOVERED",
            "PRE_GATE_FAILED",
            "SERIOUS",
            "QUALIFIED",
            "NOT_QUALIFIED",
            "UNRESOLVED",
        }:
            raise ValidationError(f"{candidate['name']} carries an undefined status")
        if (
            candidate["status"] == "PRE_GATE_FAILED"
            and not str(candidate.get("pre_gate_failure", "")).strip()
        ):
            raise ValidationError(f"{candidate['name']} failed a pre-gate with no reason")

    # §2. Discovery must stop once something qualifies.
    qualified = sum(1 for c in universe["candidates"] if c["status"] == "QUALIFIED")
    if qualified != universe["qualified_counterparts"]:
        raise ValidationError("the qualified count does not match the list")
    if qualified and not universe["discovery_stopped_after_first_qualification"]:
        raise ValidationError("a counterpart qualified and discovery continued")

    if ledger["used"] > ledger["maximum_requests"]:
        raise ValidationError("the documentation budget was exceeded")
    if len(ledger["requests"]) != ledger["used"]:
        raise ValidationError("the recorded requests do not match the count used")
    _true(ledger, ["failed_counted_against_budget"], "failed retrievals were not counted")
    _true(
        ledger,
        ["search_engines_used_for_navigation_only"],
        "search engines were used for more than navigation",
    )
    for counter in ("target_sites_measured", "counterpart_api_executions"):
        if ledger[counter] != 0:
            raise ValidationError(f"{counter} is not zero")


def _check_qualification(qualification: dict) -> None:
    """§44, §45, §46, §47."""
    gates = {g["dimension"]: g for g in qualification["gates"]}
    for dimension in MANDATORY_DIMENSIONS:
        if dimension not in gates:
            raise ValidationError(f"{dimension} was not evaluated")
        gate = gates[dimension]
        if gate["status"] not in GATE_STATUSES:
            raise ValidationError(f"{dimension} carries an undefined status")
        if gate["status"] == "PASS" and not str(gate["basis"]).strip():
            raise ValidationError(f"{dimension} passes with no basis")
        if not str(gate["why"]).strip():
            raise ValidationError(f"{dimension} carries no reason")
        if gate["status"] in {"PARTIAL", "UNKNOWN"} and not str(gate.get("residual") or "").strip():
            raise ValidationError(f"{dimension} is unresolved and names no residual")
    if len(gates) != qualification["gate_count"]:
        raise ValidationError("the gate count does not match the matrix")

    tally = {name: 0 for name in GATE_STATUSES}
    for gate in qualification["gates"]:
        tally[gate["status"]] += 1
    if {k: v for k, v in tally.items() if k in qualification["tally"]} != qualification["tally"]:
        raise ValidationError("the recorded tally does not match the matrix")

    verdict = qualification["verdict"]
    if verdict not in VERDICTS:
        raise ValidationError(f"the verdict {verdict!r} is not one of the three")

    mandatory = [gates[d] for d in MANDATORY_DIMENSIONS]
    all_pass = all(g["status"] == "PASS" for g in mandatory)
    any_fail = any(g["status"] == "FAIL" for g in mandatory)
    if verdict == "COUNTERPART_QUALIFIED" and not all_pass:
        raise ValidationError("a counterpart is qualified while a mandatory dimension is not PASS")
    if verdict == "COUNTERPART_NOT_QUALIFIED" and not any_fail:
        raise ValidationError("a counterpart is rejected with no hard FAIL")
    if verdict == "COUNTERPART_UNRESOLVED" and (all_pass or any_fail):
        raise ValidationError("the verdict is UNRESOLVED and the matrix says otherwise")

    _true(qualification, ["no_score_issued"], "a score was issued")
    family = qualification["qualification_is_construct_family_level"]
    if family["exact_predicate_chosen_by"] != "Mission 1.74":
        raise ValidationError("this mission chose the exact predicate")
    if verdict != "COUNTERPART_QUALIFIED":
        if not qualification["residuals"]:
            raise ValidationError("the counterpart is not qualified and names no residual")
        for residual in qualification["residuals"]:
            _false(
                residual,
                ["requires_a_new_search"],
                f"{residual['id']} is recorded as requiring a new search",
            )


def _check_lineage(lineage: dict) -> None:
    """§6, §7, §8, §30, §31, §33, §34."""
    if lineage["producer_classification"] not in PRODUCER_KINDS:
        raise ValidationError("the producer classification is undefined")
    if lineage["producer_classification"] in DISQUALIFYING_PRODUCERS:
        raise ValidationError(
            f"the producer is {lineage['producer_classification']}, which cannot be a counterpart"
        )
    if not str(lineage["why_that_classification"]).strip():
        raise ValidationError("the producer classification carries no reason")

    _false(lineage, ["reseller_or_passthrough"], "a reseller was treated as a producer")
    _false(lineage, ["is_a_proxy_for_an_sros_request"], "a proxy was treated as an apparatus")
    _false(
        lineage,
        ["shared_observation_upstream_with_sros"],
        "the counterpart shares an observation upstream with SROS",
    )

    common = lineage["common_upstream_measurement"]
    for upstream in ("common_crawl", "http_archive", "sros"):
        _false(common, [upstream], f"the counterpart obtains observations from {upstream}")
    _false(
        common,
        ["auxiliary_sharing_defeats_independence"],
        "auxiliary shared infrastructure is treated as defeating independence",
    )

    shared = lineage["shared_software_with_sros"]
    if not str(shared["and_it_would_not_matter_by_itself"]).strip():
        raise ValidationError("shared software is not distinguished from shared measurement")

    triggered = lineage["externally_triggered_but_independently_produced"]
    _false(
        triggered,
        ["that_makes_the_measurement_sros_produced"],
        "an externally triggered job is treated as SROS-produced",
    )

    infra = lineage["sros_execution_infrastructure_is_not_a_counterpart"]
    _false(
        infra,
        ["running_the_sros_fetcher_elsewhere_creates_a_second_apparatus"],
        "the SROS fetcher elsewhere is treated as a second apparatus",
    )

    vantage = lineage["vantage_is_not_independence"]
    _false(
        vantage,
        ["a_different_geography_is_independence"],
        "a different geography is treated as independence",
    )
    _false(
        vantage,
        ["a_matching_geography_is_the_same_apparatus"],
        "a matching geography is treated as the same apparatus",
    )
    _true(vantage, ["kept_separate_from_lineage"], "vantage is not kept separate from lineage")

    _false(
        lineage, ["marketing_language_used_as_evidence"], "marketing language was used as evidence"
    )


def _check_contract(contract: dict, qualification: dict) -> None:
    """§23, §24, §25, §26."""
    if not contract["fields"]:
        raise ValidationError("the request contract matrix is empty")
    tally = {}
    for field in contract["fields"]:
        if field["classification"] not in {
            "CONFIGURABLE",
            "FIXED_AND_DOCUMENTED",
            "DERIVABLE",
            "UNKNOWN",
            "NOT_APPLICABLE",
        }:
            raise ValidationError(f"{field['field']} carries an undefined classification")
        tally[field["classification"]] = tally.get(field["classification"], 0) + 1
    if len(contract["fields"]) != contract["field_count"]:
        raise ValidationError("the field count does not match the matrix")
    if tally != contract["tally"]:
        raise ValidationError("the recorded contract tally does not match the matrix")

    _false(
        contract,
        ["a_fixed_documented_contract_was_rejected_for_being_fixed"],
        "a fixed documented contract was rejected merely for being fixed",
    )
    _false(
        contract,
        ["browser_page_load_equated_with_a_single_get"],
        "a browser page load was equated with a single GET",
    )

    unknown = [f["field"] for f in contract["fields"] if f["classification"] == "UNKNOWN"]
    if contract["overall"] == "REQUEST_CONTRACT_COMPATIBILITY_ESTABLISHED" and unknown:
        raise ValidationError(
            f"the request contract is called established with unknowns outstanding: {unknown}"
        )
    if unknown and contract["overall"] != "REQUEST_CONTRACT_COMPATIBILITY_UNRESOLVED":
        raise ValidationError("unknown request fields exist and the contract is not UNRESOLVED")

    gap = contract["the_single_load_bearing_gap"]
    _false(
        gap,
        ["implementation_is_a_documented_contract"],
        "an observed implementation is treated as a documented contract",
    )
    if not str(gap["why_that_distinction_is_not_pedantry"]).strip():
        raise ValidationError("the implementation-versus-contract distinction carries no reason")

    # The matrix and the gate must agree.
    gates = {g["dimension"]: g for g in qualification["gates"]}
    contract_gate = gates["C6_REQUEST_CONTRACT_RECONSTRUCTABILITY"]["status"]
    if contract["overall"] == "REQUEST_CONTRACT_COMPATIBILITY_UNRESOLVED" and (
        contract_gate == "PASS"
    ):
        raise ValidationError("the request contract is unresolved and C6 passes")


def _check_minimization(minimization: dict) -> None:
    """§15, §16, §17, §60."""
    path = minimization["transport_only_result_path"]
    if path not in {
        "TRANSPORT_ONLY_RESULT_PATH_AVAILABLE",
        "TRANSPORT_ONLY_RESULT_PATH_NOT_ESTABLISHED",
    }:
        raise ValidationError("the transport-only result path is unclassified")
    _false(
        minimization,
        ["body_would_be_ingested_to_extract_a_status"],
        "a body would be ingested in order to extract a status",
    )
    if path == "TRANSPORT_ONLY_RESULT_PATH_AVAILABLE" and not str(minimization["how"]).strip():
        raise ValidationError("a transport-only path is claimed with no mechanism")
    if not minimization["transport_fields_available"]:
        raise ValidationError("no transport-level field is available")

    adr = minimization["adr_039_compatibility"]
    _false(
        adr,
        ["governance_weakened_to_accommodate_the_candidate"],
        "governance was weakened to accommodate the candidate",
    )
    _true(adr, ["satisfied_under_head"], "the observation track condition is not satisfied")


def _check_rights(rights: dict) -> None:
    """§36, §37, §38, §39, §43."""
    if rights["classification"] not in RIGHTS_CLASSIFICATIONS:
        raise ValidationError("the rights classification is undefined")
    if rights["access_status"] not in {
        "PUBLIC_NO_ACCOUNT",
        "PUBLIC_RATE_LIMITED",
        "ACCOUNT_REQUIRED",
        "API_KEY_REQUIRED",
        "PAID_PLAN_REQUIRED",
        "ENTERPRISE_REQUIRED",
        "UNKNOWN",
    }:
        raise ValidationError("the access status is undefined")
    for flag in ("account_created", "trial_started", "purchase_made", "credential_read"):
        _false(rights, [flag], f"the mission performed: {flag}")

    _false(
        rights,
        ["free_api_treated_as_commercial_permission"],
        "a free API was treated as commercial permission",
    )
    _false(
        rights, ["terms_silence_treated_as_permission"], "terms silence was treated as permission"
    )
    _false(
        rights,
        ["provider_terms_replace_sros_governance"],
        "the provider's terms were used to replace SROS governance",
    )
    _false(
        rights,
        ["final_legal_or_governance_approval_performed"],
        "a final legal or governance approval was performed",
    )
    if rights["external_legal_conclusion"] != "NO_EXTERNAL_LEGAL_CONCLUSION":
        raise ValidationError("an external legal conclusion was drawn")

    # A clause read in context must say what it is, and both readings must be refused.
    clause = rights["the_commercial_clause_read_in_context"]
    _false(
        clause,
        ["read_as_a_blanket_commercial_prohibition"],
        "a consumer-scoped clause was read as a blanket commercial prohibition",
    )
    if not str(clause["why_not"]).strip():
        raise ValidationError("the contextual reading of the commercial clause carries no reason")
    scope = rights["the_scope_sentence_that_does_bite"]
    _false(scope, ["is_a_prohibition"], "a scope sentence was read as a prohibition")
    _false(scope, ["is_a_grant"], "a scope sentence was read as a grant")

    if rights["classification"] == "COMMERCIAL_PURPOSE_PLAUSIBLE" and (
        rights["clearly_permits_the_intended_use"] is not True
    ):
        raise ValidationError(
            "commercial purpose is called plausible while the terms do not clearly permit it"
        )


def _check_readiness_and_decision(readiness: dict, decision: dict, qualification: dict) -> None:
    """§48, §49, §61, §68, §69."""
    conditions = readiness["conditions_for_strategic_viability"]
    viable = conditions["verdict"] == "STRATEGICALLY_VIABLE"
    required = (
        "sros_governance_track_ready",
        "one_external_counterpart_qualified",
        "independent_production_plausible",
        "common_http_world_state_family_exists",
    )
    if viable and not all(conditions[c] is True for c in required):
        raise ValidationError("Q1 is called strategically viable with a condition unmet")
    if not viable and all(conditions[c] is True for c in required):
        raise ValidationError("every viability condition is met and Q1 is not viable")

    qualified = qualification["verdict"] == "COUNTERPART_QUALIFIED"
    if conditions["one_external_counterpart_qualified"] is not qualified:
        raise ValidationError("the readiness record and the qualification disagree")

    if readiness["q1_status_changed_this_mission"] is not (
        readiness["q1_status_before"] != readiness["q1_status_after"]
    ):
        raise ValidationError("the record disagrees with its own Q1 status")
    if readiness["evidence_independence_groups"] != 0:
        raise ValidationError("an independence group was created")
    if readiness["pair_analysis"] != "PAIR_ANALYSIS_NOT_READY":
        raise ValidationError("pair analysis is declared ready at the wrong layer")

    outcome = decision["primary_outcome"]
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"the primary outcome {outcome!r} is not defined")
    if decision["q1_strategically_viable"] is not viable:
        raise ValidationError("the decision and the readiness record disagree on viability")

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
    else:
        if not viable:
            raise ValidationError("a class was selected while Q1 is not strategically viable")
        if not qualified:
            raise ValidationError("a class was selected with no qualified counterpart")
        if not SELECTED_CLASS.exists():
            raise ValidationError("a class was selected and no artifact exists")

    _false(decision, ["selected_construct_created"], "a construct was selected")
    if SELECTED_CONSTRUCT.exists():
        raise ValidationError("a selected-construct artifact exists")
    _false(decision, ["counterpart_selected"], "a counterpart was selected")

    if (
        outcome
        in {
            "INDEPENDENT_HTTP_COUNTERPART_QUALIFIED",
            "INDEPENDENT_HTTP_COUNTERPART_QUALIFIED_Q1_SELECTED",
        }
        and not qualified
    ):
        raise ValidationError("a qualifying outcome was reported with no qualified counterpart")
    if outcome == "INDEPENDENT_HTTP_COUNTERPART_QUALIFIED_Q1_SELECTED" and selected is None:
        raise ValidationError("the Q1-selecting outcome was reported with nothing selected")
    if (
        outcome == "NO_COMPATIBLE_INDEPENDENT_HTTP_COUNTERPART_IDENTIFIED_WITHIN_BOUNDED_SEARCH"
        and qualification["verdict"] == "COUNTERPART_UNRESOLVED"
    ):
        raise ValidationError(
            "the no-counterpart outcome was reported while a candidate is UNRESOLVED, which "
            "understates what was established"
        )
    if (
        decision["outcome_fits_imperfectly"]
        and not str(decision["why_it_fits_imperfectly"]).strip()
    ):
        raise ValidationError("an imperfect fit is recorded with no explanation")
    for name, entry in decision["outcomes_considered_and_refused"].items():
        if entry["refused"] and not str(entry["why"]).strip():
            raise ValidationError(f"{name} was refused with no reason")

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
        "counterpart_provider_contacted",
        "scanner_arc_reopened",
        "adr_039_weakened",
        "public_http_governance_altered",
        "source_collection_gate_weakened",
    ):
        _false(parallel, [flag], f"{flag} is true, and this mission may not do it")
    if decision["canonical_mutation_boundary"]["mutations_this_mission"] != 0:
        raise ValidationError("a canonical mutation was recorded")
    _true(
        decision,
        ["recommended_next_mission", "mission_1_74_not_started"],
        "the next mission was started",
    )


def _check_registry(decision: dict, baseline: dict) -> None:
    """§59."""
    requirements = _load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
    if len(requirements) != 15:
        raise ValidationError(f"the registry holds {len(requirements)} requirements, not 15")
    registry = decision["requirement_registry"]
    if registry["count_before"] != 15 or registry["count_after"] != len(requirements):
        raise ValidationError("the decision and the registry disagree on the count")
    _false(registry, ["candidate_rule_added"], "the candidate rule was added")
    _false(registry, ["registry_growth_forced"], "registry growth was forced")
    if registry["requirement_added"] is not None:
        raise ValidationError("a requirement was added without change control")
    if not str(registry["why_not_added"]).strip():
        raise ValidationError("the candidate rule was declined with no reason")
    names = {row["name"] for row in requirements}
    if registry["mission_1_70_candidate_rule"] in names:
        raise ValidationError("a rule recorded as NOT added is in the registry")
    if baseline["requirement_registry"]["count_before"] != len(requirements):
        raise ValidationError("the baseline and the registry disagree")


def _check_governance_untouched(records: list[dict]) -> None:
    """§60 and the standing rules."""
    governance = _load(GOVERNANCE_DECISION)
    if governance["decision"] != "PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED":
        raise ValidationError("Mission 1.72's governance decision was edited")
    _false(
        governance,
        ["source_collection_governance_weakened"],
        "source collection governance is now recorded as weakened",
    )
    apparatus = _load(APPARATUS_CONTRACT)
    if apparatus["implemented"] is not False:
        raise ValidationError("Mission 1.71's apparatus record now says implemented")

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
        universe,
        prescreen,
        ledger,
        qualification,
        lineage,
        contract,
        minimization,
        rights,
        readiness,
        decision,
    ) = records

    _check_preconditions(baseline)
    _check_universe(universe, ledger)
    _check_qualification(qualification)
    _check_lineage(lineage)
    _check_contract(contract, qualification)
    _check_minimization(minimization)
    _check_rights(rights)
    _check_readiness_and_decision(readiness, decision, qualification)
    _check_registry(decision, baseline)
    _check_governance_untouched(records)

    if not prescreen["what_this_does_not_establish"]:
        raise ValidationError("the prescreen does not say what it fails to establish")
    parallel = baseline["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    if parallel["netlas_contact"] != "STILL_PENDING":
        raise ValidationError("the Netlas contact state moved")

    return records


# ------------------------------------------------------------------------ renderers


def render_decision(decision: dict) -> str:
    universe = _load(UNIVERSE)
    qualification = _load(QUALIFICATION)
    lineage = _load(LINEAGE)
    readiness = _load(READINESS)
    ledger = _load(LEDGER)

    lines = [
        "# Mission 1.73 — An independent HTTP counterpart, two questions short",
        "",
        "Generated from `quantity-class-selection-decision-v3.json` and the qualification",
        "records. Do not edit by hand.",
        "",
        f"**Primary outcome: `{decision['primary_outcome']}`**",
        "",
        f"**Selected counterpart: {decision['secondary_outcomes']['SELECTED_COUNTERPART']}. "
        f"Selected quantity class: "
        f"{decision['secondary_outcomes']['SELECTED_QUANTITY_CLASS']}.**",
        "",
        "## Candidates",
        "",
        "| candidate | operator | status |",
        "|---|---|---|",
    ]
    for candidate in universe["candidates"]:
        lines.append(f"| {candidate['name']} | {candidate['operator']} | `{candidate['status']}` |")
    lines += [
        "",
        f"{universe['candidates_discovered']} discovered, {universe['serious_candidates']} "
        f"serious of a cap of {universe['serious_candidate_cap']}, "
        f"{universe['qualified_counterparts']} qualified. "
        f"{ledger['used']} of {ledger['maximum_requests']} documentation requests, "
        f"{ledger['failed_or_empty']} of which returned nothing usable and are counted.",
        "",
        "## Who produces the observation",
        "",
        f"**`{lineage['producer_classification']}`.** {lineage['why_that_classification']}",
        "",
        f"- reseller or pass-through: **{lineage['reseller_or_passthrough']}**",
        f"- a proxy for an SROS request: **{lineage['is_a_proxy_for_an_sros_request']}**",
        f"- shares an observation upstream with SROS: "
        f"**{lineage['shared_observation_upstream_with_sros']}**",
        f"- SROS initiates the job: "
        f"**{lineage['externally_triggered_but_independently_produced']['sros_initiates_the_job']}**, "
        f"and that makes the measurement SROS-produced: "
        f"**{lineage['externally_triggered_but_independently_produced']['that_makes_the_measurement_sros_produced']}**",
        "",
        "## The two residuals",
        "",
        "| id | dimension | residual |",
        "|---|---|---|",
    ]
    for residual in qualification["residuals"]:
        lines.append(f"| {residual['id']} | {residual['dimension']} | {residual['residual']} |")
    lines += [
        "",
        f"Neither requires a new search: "
        f"{', '.join(r['closable_by'] for r in qualification['residuals'])}.",
        "",
        "## Why this outcome and not the others",
        "",
        decision["why_it_fits_imperfectly"],
        "",
        "| outcome | refused because |",
        "|---|---|",
    ]
    for name, entry in decision["outcomes_considered_and_refused"].items():
        lines.append(f"| {name} | {entry['why']} |")

    lines += [
        "",
        "## Q1",
        "",
        "| condition | met |",
        "|---|---|",
    ]
    conditions = readiness["conditions_for_strategic_viability"]
    for key in (
        "sros_governance_track_ready",
        "one_external_counterpart_qualified",
        "independent_production_plausible",
        "common_http_world_state_family_exists",
    ):
        lines.append(f"| {key.replace('_', ' ')} | {conditions[key]} |")
    lines += [
        "",
        f"**{conditions['verdict']}**, failing on `{conditions['load_bearing_failure']}`. "
        f"Q1 stays `{readiness['q1_status_after']}`.",
        "",
        "**Resolved this mission:**",
        "",
    ]
    for item in readiness["what_did_change"]["resolved_this_mission"]:
        lines.append(f"- {item}")
    lines += ["", "**Still unresolved:**", ""]
    for item in readiness["what_did_change"]["still_unresolved"]:
        lines.append(f"- {item}")

    lines += [
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    accounting = decision["mission_accounting"]
    for counter in (
        "COUNTERPART_API_EXECUTIONS",
        "TARGET_HTTP_REQUESTS",
        "SROS_FETCHER_RUNS",
        "EXTERNAL_MEASUREMENT_JOBS",
        "TARGET_VALUE_EXPOSURES",
        "ACCOUNTS_CREATED",
        "TRIALS",
        "CREDENTIAL_READS",
        "SOURCES_REGISTERED",
        "CLAIMS_CREATED",
        "EVIDENCE_CREATED",
        "INDEPENDENCE_GROUPS_CREATED",
        "MODEL_CALLS",
    ):
        lines.append(f"| {counter} | {accounting[counter]} |")
    lines.append("")
    return "\n".join(lines)


def render_matrix(qualification: dict) -> str:
    contract = _load(CONTRACT)
    rights = _load(RIGHTS)
    minimization = _load(MINIMIZATION)

    lines = [
        "# Mission 1.73 — The counterpart qualification matrix",
        "",
        "Generated from `independent-http-counterpart-qualification-v1.json`.",
        "Do not edit by hand.",
        "",
        f"**Candidate: {qualification['candidate']} ({qualification['operator']}).**",
        f"**Verdict: `{qualification['verdict']}`.**",
        "",
        "| dimension | status | mandatory |",
        "|---|---|---|",
    ]
    for gate in qualification["gates"]:
        lines.append(f"| `{gate['dimension']}` | `{gate['status']}` | {gate['mandatory']} |")
    tally = qualification["tally"]
    lines += [
        "",
        f"**{tally['PASS']} PASS, {tally['PARTIAL']} PARTIAL, {tally['FAIL']} FAIL, "
        f"{tally['UNKNOWN']} UNKNOWN.** No score.",
        "",
        f"*{qualification['why_not_qualified']}*",
        "",
        f"*And why it is not a rejection:* {qualification['why_not_rejected']}",
        "",
        "Why, for each:",
        "",
    ]
    for gate in qualification["gates"]:
        lines.append(f"- **{gate['dimension']}** — {gate['why']}")
        if gate.get("residual"):
            lines.append(f"  - *residual:* {gate['residual']}")

    lines += [
        "",
        "## The request contract",
        "",
        "| field | classification | SROS can construct an equivalent |",
        "|---|---|---|",
    ]
    for field in contract["fields"]:
        lines.append(
            f"| `{field['field']}` | {field['classification']} "
            f"| {field['sros_can_construct_an_equivalent']} |"
        )
    gap = contract["the_single_load_bearing_gap"]
    lines += [
        "",
        f"**{contract['overall']}**, on one field: `{gap['field']}`.",
        "",
        f"{gap['evidence']}. {gap['implementation_observed']} — and that is an implementation "
        f"rather than a contract ({gap['implementation_is_a_documented_contract']}).",
        "",
        f"*{gap['why_that_distinction_is_not_pedantry']}*",
        "",
        "## Minimization",
        "",
        f"**{minimization['transport_only_result_path']}.** {minimization['how']}",
        "",
        "## Rights",
        "",
        f"**{rights['classification']}.** Access: `{rights['access_status']}`.",
        "",
        f"The clause that looks decisive in isolation sits under "
        f'*"{rights["the_commercial_clause_read_in_context"]["the_heading_it_sits_under"]}"*, '
        f"and reading it as a blanket prohibition is refused: "
        f"**{rights['the_commercial_clause_read_in_context']['read_as_a_blanket_commercial_prohibition']}**.",
        "",
        f"What does bite: {rights['the_scope_sentence_that_does_bite']['why_it_matters']} "
        f"It is a prohibition: "
        f"**{rights['the_scope_sentence_that_does_bite']['is_a_prohibition']}**. It is a grant: "
        f"**{rights['the_scope_sentence_that_does_bite']['is_a_grant']}**.",
        "",
    ]
    return "\n".join(lines)


RENDERERS = {DECISION: render_decision, QUALIFICATION: render_matrix}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  counterpart qualification: {error}")
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
        print(f"ok       {len(rendered)} counterpart documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    print(f"outcome  {by_path[DECISION]['primary_outcome']}")
    print(f"verdict  {by_path[QUALIFICATION]['verdict']}")
    print(f"q1       {by_path[READINESS]['q1_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
