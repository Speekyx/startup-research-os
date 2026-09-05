"""Render and validate the Mission 1.70 fixed-corpus web route qualification.

Ten records, and one discipline underneath all of them:

    A COVERAGE SURFACE IS NOT A POPULATION UNTIL SOMEBODY SAYS WHAT MEMBERSHIP
    IN IT MEANS.

`validate()` enforces the readings this mission was most tempted to make and did
not:

  - a successful observation is not a planned target, and an index of captures is
    not an attempted set;
  - co-coverage is not preregistered merely because the rule was written first,
    because the rule is only as good as what coverage means;
  - an HTTP status code sitting in an index is measurement content, whatever
    column it occupies;
  - two different observed denominators are two propositions;
  - a dated artifact is not an immutable one;
  - a browser page load is not a crawler fetch, and the main document AFTER
    redirects is not the response to the requested URL;
  - a recommendation to seek legal advice is not a grant;
  - an operator-run fetcher is not independent because we run it, and is not
    authorised because it is feasible;
  - and Common Crawl's URL selection stays unestablished, because no first-party
    page carrying it was opened.

    uv run python infrastructure/scripts/render_web_route_qualification.py
    uv run python infrastructure/scripts/render_web_route_qualification.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.70-baseline-v1.json"
POPULATION = DATA / "fixed-corpus-population-preselection-review-v1.json"
CC = DATA / "common-crawl-route-qualification-v1.json"
HA = DATA / "http-archive-route-qualification-v1.json"
CONTRACT_COMPAT = DATA / "http-request-contract-compatibility-v1.json"
TEMPORAL = DATA / "web-route-temporal-compatibility-v1.json"
RIGHTS = DATA / "web-route-rights-feasibility-v1.json"
FETCHER = DATA / "sros-bounded-http-fetcher-feasibility-v1.json"
QUALIFICATION = DATA / "fixed-corpus-web-route-qualification-v1.json"
DECISION = DATA / "quantity-class-selection-decision-v2.json"

SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
APPARATUS_CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
DECISION_V1 = DATA / "quantity-class-selection-decision-v1.json"

ORDER = [
    BASELINE,
    POPULATION,
    CC,
    HA,
    CONTRACT_COMPAT,
    TEMPORAL,
    RIGHTS,
    FETCHER,
    QUALIFICATION,
    DECISION,
]

RENDERED = {
    DECISION: DATA / "mission-1.70-web-route-qualification-v1.md",
    POPULATION: DATA / "fixed-corpus-population-preselection-review-v1.md",
}

POPULATION_DECISIONS = (
    "PRE_VALUE_COCOVERAGE_RULE_IS_VALID",
    "MISSINGNESS_PRESERVING_POPULATION_IS_VALID",
    "EXTERNALLY_FROZEN_POPULATION_REQUIRES_OPERATOR_FETCHER",
    "REALIZED_COCOVERAGE_IS_POST_HOC_AND_INVALID",
    "POPULATION_ARCHITECTURE_REMAINS_UNRESOLVED",
)

ROUTE_STATUSES = (
    "ROUTE_QUALIFIED_FOR_CLASS",
    "ROUTE_PLAUSIBLE_REQUIRES_CONSTRUCT_DETAIL",
    "ROUTE_BLOCKED",
    "ROUTE_UNRESOLVED",
)

COMPAT_CLASSES = (
    "MATCHABLE",
    "DIFFERENT_BUT_NON_LOAD_BEARING",
    "DIFFERENT_AND_LOAD_BEARING",
    "UNKNOWN",
)

# §55. Fields whose presence in a coverage surface makes it measurement-bearing. An HTTP
# status is measurement content wherever it sits.
MEASUREMENT_FIELDS = frozenset(
    {"status", "fetch_status", "content_truncated", "payload", "response_headers", "response_body"}
)

HARD_ZERO_COUNTERS = (
    "TARGET_VALUE_EXPOSURES",
    "MEASUREMENT_VALUES_RETRIEVED",
    "CRAWLS",
    "TARGET_HTTP_REQUESTS",
    "HTTP_MEASUREMENT_REQUESTS",
    "COMMON_CRAWL_INDEX_QUERIES",
    "WARC_WAT_WET_DOWNLOADS",
    "BIGQUERY_EXECUTIONS",
    "HAR_DOWNLOADS",
    "API_EXECUTIONS",
    "DATASET_DOWNLOADS",
    "COUNT_ENDPOINT_EXECUTIONS",
    "TRIALS",
    "PURCHASES",
    "ACCOUNTS_CREATED",
    "CREDENTIAL_READS",
    "MAILBOX_SEARCHES",
    "ENQUIRIES_SENT",
    "SOURCES_REGISTERED",
    "SOURCE_GOVERNANCE_MUTATIONS",
    "GOVERNANCE_APPROVALS",
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
    "CONSTRUCTS_FROZEN",
    "PREDICATES_CHOSEN",
    "PAIRS_SELECTED",
    "CRAWLERS_IMPLEMENTED",
)


class ValidationError(RuntimeError):
    """A record says something this mission's rules refuse."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _walk(node):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _entries(block: dict):
    """A `$comment` is where a RULE is written; it is never a row (Mission 1.42, §23)."""
    return [(k, v) for k, v in block.items() if not k.startswith("$")]


def _check_scope(baseline: dict) -> None:
    """§1. Q1 only, and the scanner class stays parked."""
    scope = baseline["scope"]
    if scope["in_scope_class"] != "FIXED_CORPUS_HTTP_OBSERVATION":
        raise ValidationError("the mission scope is not the fixed-corpus web class")
    if scope["broad_class_discovery_performed"] is not False:
        raise ValidationError("broad quantity-class discovery was performed")
    if scope["scanner_class_reopened"] is not False:
        raise ValidationError("the scanner class was reopened")
    for cid in ("Q0", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"):
        if cid not in scope["classes_not_reopened"]:
            raise ValidationError(f"{cid} is not recorded as out of scope")

    parallel = baseline["parallel_state_untouched"]
    if parallel["scanner_arc_status"] != "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE":
        raise ValidationError("the scanner arc status changed")

    budget = baseline["documentation_budget"]
    if budget["used"] > budget["maximum_first_party_requests"]:
        raise ValidationError("the documentation budget was exceeded")
    for key, cap in budget["caps"].items():
        if budget["split"][key] > cap:
            raise ValidationError(f"the {key} sub-budget was exceeded")
    if sum(budget["split"].values()) != budget["used"]:
        raise ValidationError("the budget split does not sum to the requests used")


def _check_registry(baseline: dict, decision: dict) -> None:
    """§43. Fifteen unless a second instance in a different shape was established."""
    requirements = _load(APPARATUS_CONTRACT)["requirement_registry"]["requirements"]
    if len(requirements) != 15:
        raise ValidationError(f"the registry holds {len(requirements)} requirements, not 15")
    if baseline["requirement_registry"]["requirement_added_this_mission"] is not None:
        raise ValidationError("the baseline records a requirement added this mission")
    registry = decision["requirement_registry"]
    if registry["count_after"] != len(requirements):
        raise ValidationError("the decision and the contract disagree on the registry count")
    if registry["requirement_added"] is not None:
        raise ValidationError("a requirement was added without change control")
    if registry["registry_growth_forced"] is not False:
        raise ValidationError("registry growth was forced")
    offered = registry["candidate_offered_and_not_added"]
    names = {item["name"] for item in requirements}
    if offered["name"] in names:
        raise ValidationError("a rule recorded as NOT added is in the registry")
    if not str(offered["why_it_was_not_added"]).strip():
        raise ValidationError("a candidate rule was declined with no reason")


def _check_coverage_classification(population: dict, cc: dict, ha: dict) -> None:
    """§4, §5 and §6. Success is not target, and an index of captures is not an attempt set."""
    concepts = population["the_four_population_concepts"]
    for concept in (
        "TARGET_POPULATION",
        "ATTEMPTED_POPULATION",
        "OBSERVABLE_POPULATION",
        "SUCCESSFUL_OBSERVATION_SET",
    ):
        if not str(concepts.get(concept, "")).strip():
            raise ValidationError(f"{concept} is not defined")
    if concepts["used_interchangeably"] is not False:
        raise ValidationError("the population concepts are used interchangeably")

    for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
        entry = population["coverage_classification_per_route"][route]
        # A route may not claim a targeted or attempted set it cannot reconstruct.
        if entry["targeted_set_reconstructable"] is True and route == "COMMON_CRAWL":
            raise ValidationError(
                "Common Crawl's targeted set is recorded as reconstructable, and no retrieved "
                "page publishes a target list"
            )
        if entry["captured_set_reconstructable"] is not True:
            raise ValidationError(f"{route} cannot reconstruct even its captured set")
        if not str(entry["why"]).strip():
            raise ValidationError(f"{route} coverage classification carries no reason")
        # Successful coverage may not be labelled as planned coverage.
        if entry["classification"] == "ATTEMPTED_SET":
            raise ValidationError(
                f"{route} coverage is classified as an attempted set, which no retrieved page "
                "establishes"
            )

    outcome = population["outcome_dependence"]
    for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
        if outcome[route] not in {
            "COVERAGE_MAY_BE_OUTCOME_DEPENDENT",
            "COVERAGE_NOT_OUTCOME_DEPENDENT",
        }:
            raise ValidationError(f"{route} outcome dependence is not classified")
    if outcome["established_as_outcome_dependent"] is not False:
        raise ValidationError(
            "coverage is asserted to BE outcome dependent, which the evidence does not establish"
        )

    boundary = population["metadata_value_boundary"]
    if boundary["the_semantic_boundary_is_not"] in (None, ""):
        raise ValidationError("the semantic metadata boundary is not addressed")
    for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
        fields = set(boundary["measurement_fields_present_in_coverage_surfaces"][route])
        if not fields & MEASUREMENT_FIELDS:
            raise ValidationError(
                f"{route} records no measurement field in its coverage surface, which "
                "contradicts the route record"
            )


def _check_population_decision(population: dict) -> None:
    """§36, §37 and §38."""
    decision = population["decision"]
    if decision not in POPULATION_DECISIONS:
        raise ValidationError(f"the population decision {decision!r} is not one of the five")

    a = population["conditions_for_A"]
    b = population["conditions_for_B"]
    a_unknown = [k for k, v in a.items() if isinstance(v, str) and v == "UNKNOWN"]
    if decision == "PRE_VALUE_COCOVERAGE_RULE_IS_VALID":
        if a["verdict"] != "SATISFIED":
            raise ValidationError("decision A recorded while its conditions are not satisfied")
        if a_unknown:
            raise ValidationError(f"decision A recorded with UNKNOWN conditions: {a_unknown}")
    if decision == "MISSINGNESS_PRESERVING_POPULATION_IS_VALID" and b["verdict"] != "SATISFIED":
        raise ValidationError("decision B recorded while its conditions are not satisfied")
    if a["verdict"] == "SATISFIED" and a_unknown:
        raise ValidationError("the A conditions are marked satisfied with unknowns among them")

    strategies = population["strategies_evaluated"]
    strategies = dict(_entries(strategies))
    for name in (
        "P1_provider_native_intersection",
        "P2_frozen_C_plus_planned_target_coverage",
        "P3_frozen_C_plus_attempted_coverage",
        "P4_frozen_C_plus_realized_successful_coverage",
        "P5_missingness_preserving",
    ):
        if name not in strategies:
            raise ValidationError(f"strategy {name} was not evaluated")
        if not str(strategies[name]["why"]).strip():
            raise ValidationError(f"strategy {name} carries no reason")
    # §7. P4 is the high-risk one and may not be accepted quietly.
    if strategies["P4_frozen_C_plus_realized_successful_coverage"]["accepted"] is not False:
        raise ValidationError("realized successful co-coverage was accepted as the population")
    if strategies["P5_missingness_preserving"]["considered_seriously"] is not True:
        raise ValidationError("the missingness-preserving strategy was not considered seriously")

    # §9. Denominators.
    if (
        population["denominator_discipline"]["different_denominators_called_the_same_proposition"]
        is not False
    ):
        raise ValidationError("different denominators were called the same proposition")

    # §10. Ordering is necessary and not sufficient.
    if population["temporal_ordering"]["called_automatically_preregistered"] is not False:
        raise ValidationError("a coverage rule was called automatically preregistered")
    if not str(population["temporal_ordering"]["why_that_ordering_is_not_sufficient"]).strip():
        raise ValidationError("the record does not say why ordering alone is insufficient")

    if not population["what_this_does_not_establish"]:
        raise ValidationError("the population review does not say what it fails to establish")


def _check_routes(cc: dict, ha: dict, qualification: dict) -> None:
    """§13 to §22 and §39."""
    # §16 and §18. A date is not immutability.
    if cc["crawl_identity"]["date_alone_is_not_immutability"] is not True:
        raise ValidationError("Common Crawl treats a date as immutability")
    if cc["immutability"]["inferred_from_a_date"] is not False:
        raise ValidationError("Common Crawl infers immutability from a date")
    if ha["run_identity"]["immutability"] not in {
        "PARTIAL",
        "UNKNOWN",
        "IMMUTABLE_OR_VERSION_BOUND",
    }:
        raise ValidationError("HTTP Archive immutability is not classified")

    # §14. URL selection must not be guessed.
    selection = cc["url_selection"]
    if selection["status"] not in {"NOT_ESTABLISHED_THIS_MISSION", "ESTABLISHED"}:
        raise ValidationError("Common Crawl URL selection carries an unknown status")
    summary = selection["a_search_summary_offered_an_answer_and_it_was_not_used"]
    if summary["used"] is not False:
        raise ValidationError("a search summary was used to establish Common Crawl URL selection")
    if selection["status"] == "ESTABLISHED" and not selection.get("source_says"):
        raise ValidationError("Common Crawl URL selection is ESTABLISHED with no quotation")

    # §17 and §20. Availability claims need evidence.
    if ha["response_availability"]["assumed_rather_than_evidenced"] is not False:
        raise ValidationError("HTTP Archive header availability was assumed rather than evidenced")
    if ha["response_availability"]["classification"] not in {
        "RAW_RESPONSE_HEADERS_AVAILABLE",
        "STRUCTURED_RESPONSE_HEADERS_AVAILABLE",
        "DERIVED_METRICS_ONLY",
        "BODY_AVAILABLE",
        "UNKNOWN",
    }:
        raise ValidationError("HTTP Archive response availability is not classified")

    # §21. Redirect binding is not chosen here.
    if ha["redirects"]["predicate_binding_chosen"] is not False:
        raise ValidationError("a redirect predicate binding was chosen, which belongs later")

    # §22. A browser load is not a bot fetch.
    if ha["browser_semantics"]["treated_as_identical_to_a_bot_fetch"] is not False:
        raise ValidationError("a browser page load was treated as identical to a crawler fetch")

    # Sampling honesty.
    if cc["sampling"]["called_a_complete_web_corpus"] is not False:
        raise ValidationError("Common Crawl was called a complete web corpus")

    # No execution.
    for flag in ("no_index_query_executed", "no_warc_wat_wet_downloaded"):
        if cc[flag] is not True:
            raise ValidationError(f"Common Crawl route record does not assert {flag}")
    for flag in ("no_bigquery_executed", "no_har_downloaded"):
        if ha[flag] is not True:
            raise ValidationError(f"HTTP Archive route record does not assert {flag}")

    routes = dict(_entries(qualification["routes"]))
    for name, entry in routes.items():
        if entry["status"] not in ROUTE_STATUSES:
            raise ValidationError(f"{name} carries an unknown route status")
        if (
            entry["status"] != "ROUTE_QUALIFIED_FOR_CLASS"
            and not entry.get("unresolved")
            and name != "SROS_BOUNDED_HTTP_FETCHER"
        ):
            raise ValidationError(f"{name} is not qualified and lists nothing unresolved")
    if qualification["route_status_meaning"]["neither_route_reached_it"] is not (
        all(r["status"] != "ROUTE_QUALIFIED_FOR_CLASS" for r in routes.values())
    ):
        raise ValidationError("the record disagrees with its own route statuses")


def _check_compatibility(compat: dict) -> None:
    """§23, §24 and §25."""
    if compat["opaque_pass_issued_without_the_table"] is not False:
        raise ValidationError("an overall pass was issued without the compatibility table")
    if not compat["fields"]:
        raise ValidationError("the compatibility table is empty")
    tally = {name: 0 for name in COMPAT_CLASSES}
    for entry in compat["fields"]:
        if entry["classification"] not in COMPAT_CLASSES:
            raise ValidationError(f"{entry['field']} carries an unknown compatibility class")
        tally[entry["classification"]] += 1
    if tally != compat["tally"]:
        raise ValidationError(
            f"the recorded tally {compat['tally']} does not match the table {tally}"
        )
    if compat["overall"] == "REQUEST_CONTRACT_COMPATIBILITY_ESTABLISHED" and (
        tally["DIFFERENT_AND_LOAD_BEARING"] or tally["UNKNOWN"]
    ):
        raise ValidationError(
            "request-contract compatibility is called established with load-bearing "
            "differences or unknowns outstanding"
        )

    family = compat["same_world_state_family"]
    if family["browser_load_treated_as_identical_to_a_bot_fetch"] is not False:
        raise ValidationError("a browser load was treated as identical to a bot fetch")
    if family["classification"] == "SAME_HTTP_WORLD_STATE_FAMILY_PLAUSIBLE" and (
        tally["DIFFERENT_AND_LOAD_BEARING"] or tally["UNKNOWN"]
    ):
        raise ValidationError(
            "a shared world-state family is asserted unconditionally while the request "
            "contract is unestablished"
        )
    if (
        family["client_relative_propositions_are_allowed_if_explicit"]["equivalence_documented"]
        is True
    ):
        raise ValidationError("request-contract equivalence is claimed as documented")


def _check_rights(rights: dict) -> None:
    """§28 to §30. Feasibility, never approval."""
    if rights["this_is_not_a_governance_review"] is not True:
        raise ValidationError("the rights record presents itself as a governance review")
    if rights["sources_registered"] != 0 or rights["source_governance_mutated"] != 0:
        raise ValidationError("the rights review registered a source or mutated governance")
    if rights["turned_into_governance_approval"] is not False:
        raise ValidationError("rights feasibility was turned into governance approval")
    for route, entry in _entries(rights["routes"]):
        if entry["classification"] not in {
            "ROUTE_RIGHTS_PLAUSIBLE",
            "ROUTE_RIGHTS_REVIEW_REQUIRED",
            "ROUTE_RIGHTS_BLOCKED",
            "UNKNOWN",
        }:
            raise ValidationError(f"{route} rights classification is not one of the four")
        # A recommendation to seek advice is not a grant.
        if entry["classification"] == "ROUTE_RIGHTS_PLAUSIBLE" and entry.get("commercial_use") in {
            "NOT_GRANTED_AND_NOT_PROHIBITED",
            "NOT_STATED",
            None,
        }:
            raise ValidationError(
                f"{route} rights are called plausible while commercial use is not granted"
            )
    if rights["commercial_purpose_compatibility"] == "ESTABLISHED":
        raise ValidationError("commercial-purpose compatibility is claimed as established")


def _check_fetcher(fetcher: dict) -> None:
    """§31 to §35. Architecture only."""
    if fetcher["implemented"] is not False or fetcher["crawled"] is not False:
        raise ValidationError("the operator fetcher was implemented or crawled")
    if fetcher["http_measurement_requests"] != 0:
        raise ValidationError("the operator fetcher made HTTP measurement requests")
    governance = fetcher["governance_feasibility"]
    if governance["classification"] not in {
        "GOVERNANCE_FEASIBLE_IN_PRINCIPLE",
        "REQUIRES_DEDICATED_REVIEW",
        "NOT_ACCEPTABLE",
        "UNKNOWN",
    }:
        raise ValidationError("the fetcher governance classification is not one of the four")
    if governance["authorised_by_this_mission"] is not False:
        raise ValidationError("the operator fetcher was authorised by this mission")
    if not governance["conditions_a_future_review_would_have_to_settle"]:
        raise ValidationError("the fetcher governance names no conditions")
    independence = fetcher["independence_architecture"]
    if independence["automatically_independent"] is not False:
        raise ValidationError("the operator fetcher was treated as automatically independent")
    if independence["classification"] not in {
        "INDEPENDENCE_ARCHITECTURE_PLAUSIBLE",
        "INDEPENDENCE_ARCHITECTURE_UNRESOLVED",
        "INDEPENDENCE_ARCHITECTURE_REFUTED",
    }:
        raise ValidationError("the fetcher independence classification is undefined")
    if not str(fetcher["fallback_not_forced_solution"]["the_honest_residual"]).strip():
        raise ValidationError("the fetcher record does not state its residual")


def _check_decision(decision: dict, qualification: dict, population: dict) -> None:
    """§40, §41, §42 and §58."""
    viable = qualification["q1_strategic_conditions"]["verdict"] == "STRATEGICALLY_VIABLE"
    if decision["strategically_viable"] is not viable:
        raise ValidationError("the decision and the qualification disagree on viability")

    selected = decision["selected_quantity_class"]
    if selected is None:
        if decision["selection_outcome"] != "NO_SELECTION":
            raise ValidationError("nothing was selected and the outcome is not NO_SELECTION")
        if decision["selected_class_artifact_created"] is not False:
            raise ValidationError("no class was selected and an artifact was recorded")
        if SELECTED_CLASS.exists():
            raise ValidationError("selected-quantity-class-v1.json exists and nothing was selected")
    else:
        if not viable:
            raise ValidationError("a class was selected while it is not strategically viable")
        if not SELECTED_CLASS.exists():
            raise ValidationError("a class was selected and no artifact exists")

    # §42. A selected class never brings a construct with it.
    if decision["selected_construct_created"] is not False:
        raise ValidationError("a construct was selected, which belongs to a later mission")
    if SELECTED_CONSTRUCT.exists():
        raise ValidationError("a selected-construct artifact exists")

    # §41 and §40. Population validity gates class selection.
    if selected is not None and population["decision"] not in {
        "PRE_VALUE_COCOVERAGE_RULE_IS_VALID",
        "MISSINGNESS_PRESERVING_POPULATION_IS_VALID",
    }:
        raise ValidationError("a class was selected on an unresolved population architecture")

    outcome = decision["primary_outcome"]
    allowed = {
        "FIXED_CORPUS_WEB_MEASUREMENT_CLASS_SELECTED",
        "PRE_VALUE_COCOVERAGE_ARCHITECTURE_VALID_ROUTE_QUALIFICATION_CONTINUES",
        "MISSINGNESS_PRESERVING_WEB_POPULATION_VALID_ROUTE_QUALIFICATION_CONTINUES",
        "FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE",
        "FIXED_CORPUS_WEB_POPULATION_ARCHITECTURE_INVALID",
        "HTTP_ARCHIVE_ROUTE_INSUFFICIENTLY_SPECIFIED",
        "COMMON_CRAWL_ROUTE_INSUFFICIENTLY_SPECIFIED",
        "COMMERCIAL_PURPOSE_ROUTE_GAP",
        "FIXED_CORPUS_WEB_ROUTE_QUALIFICATION_REMAINS_UNRESOLVED",
        "FIXED_CORPUS_WEB_ROUTE_QUALIFICATION_BLOCKED",
    }
    if outcome not in allowed:
        raise ValidationError(f"the primary outcome {outcome!r} is not defined")
    if outcome == "FIXED_CORPUS_WEB_MEASUREMENT_CLASS_SELECTED" and selected is None:
        raise ValidationError("the selecting outcome was reported with nothing selected")
    if (
        outcome == "FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE"
        and population["decision"] != "EXTERNALLY_FROZEN_POPULATION_REQUIRES_OPERATOR_FETCHER"
    ):
        raise ValidationError(
            "the operator-route outcome was reported without the matching population decision"
        )

    accounting = decision["mission_accounting"]
    for counter in HARD_ZERO_COUNTERS:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")
    if accounting["FIRST_PARTY_DOCUMENT_REQUESTS"] > accounting["FIRST_PARTY_REQUEST_BUDGET"]:
        raise ValidationError("the documentation budget was exceeded")

    parallel = decision["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    for key in (
        "onyphe_mailbox_searched",
        "onyphe_gmail_polled",
        "onyphe_reply_read",
        "onyphe_follow_up_sent",
        "onyphe_state_changed",
        "netlas_address_decoded",
        "netlas_address_guessed",
        "netlas_enquiry_sent",
        "netlas_state_changed",
        "scanner_arc_reopened",
    ):
        if parallel[key] is not False:
            raise ValidationError(f"{key} is true, and this mission may not do it")
    if decision["canonical_mutation_boundary"]["mutations_this_mission"] != 0:
        raise ValidationError("a canonical mutation was recorded")
    if decision["recommended_next_mission"]["mission_1_71_not_started"] is not True:
        raise ValidationError("the next mission was started")

    # Mission 1.69's record stays as it wrote it.
    if decision["mission_1_69_record_edited"] is not False:
        raise ValidationError("the record claims Mission 1.69's decision was edited")
    previous = _load(DECISION_V1)
    if previous["selected_quantity_class"] is not None:
        raise ValidationError("Mission 1.69's decision record now selects a class")
    if previous["primary_outcome"] != (
        "FIXED_CORPUS_WEB_MEASUREMENT_PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED"
    ):
        raise ValidationError("Mission 1.69's decision record was edited")


# §23, met for the eleventh time. `reliability_assessments` is a ROW COUNT of the
# canonical database, and it lives in exactly two named census blocks. A guard that
# refuses any number under a reliability-named key fires on it. The repair is to scope
# the guard to the records where an assignment could occur -- never to loosen what it
# compares -- and to require the two censuses to agree, so the exemption cannot be
# claimed by renaming an arbitrary block.
# `mission_accounting` is exempt for a different reason and it is not a loosening:
# every one of its reliability-named entries is in HARD_ZERO_COUNTERS, so
# `_check_decision` already refuses any value there that is not 0.
CENSUS_BLOCKS = ("canonical_baseline", "canonical_mutation_boundary", "mission_accounting")


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


def _check_no_predicate_or_reliability(records: list[dict], baseline: dict, decision: dict) -> None:
    """§2 and the standing reliability rule."""
    census = baseline["canonical_baseline"]["reliability_assessments"]
    if decision["canonical_mutation_boundary"]["reliability_assessments"] != census:
        raise ValidationError("the two canonical censuses disagree on the assessment count")
    if decision["mission_accounting"]["RELIABILITY_VALUES_ASSIGNED"] != 0:
        raise ValidationError("a reliability value was assigned this mission")

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
    baseline, population, cc, ha, compat, temporal, rights, fetcher, qualification, decision = (
        records
    )

    _check_scope(baseline)
    _check_registry(baseline, decision)
    _check_coverage_classification(population, cc, ha)
    _check_population_decision(population)
    _check_routes(cc, ha, qualification)
    _check_compatibility(compat)
    _check_rights(rights)
    _check_fetcher(fetcher)
    _check_decision(decision, qualification, population)
    _check_no_predicate_or_reliability(records, baseline, decision)

    if baseline["canonical_baseline"]["drift_from_mission_1_69"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["repository_precondition"]["mission_1_69_merged"] is not True:
        raise ValidationError("the baseline does not record Mission 1.69 as merged")
    for flag in ("selected_quantity_class_artifact_absent", "selected_construct_artifact_absent"):
        if baseline["repository_precondition"][flag] is not True:
            raise ValidationError(f"the baseline does not record {flag}")

    if temporal["overall"] not in {
        "TEMPORAL_COMPATIBILITY_ESTABLISHED",
        "TEMPORAL_COMPATIBILITY_PLAUSIBLE_NOT_ESTABLISHED",
        "TEMPORAL_COMPATIBILITY_REFUTED",
    }:
        raise ValidationError("temporal compatibility is not classified")
    for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
        if temporal["routes"][route]["date_treated_as_immutability"] is not False:
            raise ValidationError(f"{route} treats a date as immutability")

    return records


# ------------------------------------------------------------------------ renderers


def render_population(review: dict) -> str:
    lines = [
        "# Mission 1.70 — Can a common web population be frozen honestly?",
        "",
        "Generated from `fixed-corpus-population-preselection-review-v1.json`.",
        "Do not edit by hand.",
        "",
        f"**Decision: `{review['decision']}`**",
        "",
        "## What each route's coverage actually means",
        "",
        "| route | classification | targeted | attempted | captured |",
        "|---|---|---|---|---|",
    ]
    for route, entry in _entries(review["coverage_classification_per_route"]):
        lines.append(
            f"| {route} | `{entry['classification']}` | {entry['targeted_set_reconstructable']} "
            f"| {entry['attempted_set_reconstructable']} | {entry['captured_set_reconstructable']} |"
        )
    lines += ["", "Why, in each case:", ""]
    for route, entry in _entries(review["coverage_classification_per_route"]):
        lines.append(f"- **{route}** — {entry['why']}")

    boundary = review["metadata_value_boundary"]
    lines += [
        "",
        "## The metadata boundary is navigable and the semantic one is not",
        "",
        f"{boundary['the_semantic_boundary_is_not']}",
        "",
        "| route | classification | measurement fields in the coverage surface |",
        "|---|---|---|",
    ]
    for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
        fields = ", ".join(
            f"`{f}`" for f in boundary["measurement_fields_present_in_coverage_surfaces"][route]
        )
        lines.append(f"| {route} | `{boundary[route]}` | {fields} |")

    lines += ["", "## The five strategies", "", "| strategy | verdict |", "|---|---|"]
    for name, entry in _entries(review["strategies_evaluated"]):
        lines.append(f"| `{name}` | {entry['verdict']} |")
    lines += [""]
    for name, entry in _entries(review["strategies_evaluated"]):
        lines.append(f"- **{name}** — {entry['why']}")

    lines += [
        "",
        "## Why this decision",
        "",
    ]
    for key, why in _entries(review["decision_reasoning"]):
        lines.append(f"- **{key.replace('_', ' ')}** — {why}")

    lines += ["", "## What this does not establish", ""]
    for item in review["what_this_does_not_establish"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def render_decision(decision: dict) -> str:
    qualification = _load(QUALIFICATION)
    compat = _load(CONTRACT_COMPAT)
    rights = _load(RIGHTS)
    fetcher = _load(FETCHER)

    lines = [
        "# Mission 1.70 — Fixed-corpus web route qualification",
        "",
        "Generated from `quantity-class-selection-decision-v2.json` and the route records.",
        "Do not edit by hand.",
        "",
        f"**Primary outcome: `{decision['primary_outcome']}`**",
        "",
        f"**Class status: `{decision['class_status']}`. "
        f"Selected class: {decision['selected_quantity_class'] or 'NONE'}.**",
        "",
        "## Routes",
        "",
        "| route | status | produces its own observations |",
        "|---|---|---|",
    ]
    for name, entry in _entries(qualification["routes"]):
        lines.append(
            f"| {name} | `{entry['status']}` | {entry['produces_its_own_http_observations']} |"
        )

    lines += ["", "## Q1 strategic conditions", "", "| condition | state |", "|---|---|"]
    for key, value in _entries(qualification["q1_strategic_conditions"]):
        if key in {"verdict", "load_bearing_failure"}:
            continue
        lines.append(f"| {key.replace('_', ' ')} | {value} |")
    lines += [
        "",
        f"**Verdict: {qualification['q1_strategic_conditions']['verdict']}**, failing on "
        f"{qualification['q1_strategic_conditions']['load_bearing_failure']}.",
        "",
        "## Request-contract compatibility",
        "",
        "| field | Common Crawl | HTTP Archive | classification |",
        "|---|---|---|---|",
    ]
    for entry in compat["fields"]:
        lines.append(
            f"| `{entry['field']}` | {entry['common_crawl']} | {entry['http_archive']} "
            f"| {entry['classification']} |"
        )
    lines += [
        "",
        f"**{compat['overall']}** — {compat['tally']['DIFFERENT_AND_LOAD_BEARING']} load-bearing "
        f"differences and {compat['tally']['UNKNOWN']} unknowns.",
        "",
        "## Rights",
        "",
        "| route | classification |",
        "|---|---|",
    ]
    for route, entry in _entries(rights["routes"]):
        lines.append(f"| {route} | `{entry['classification']}` |")
    lines += [
        "",
        f"Commercial-purpose compatibility: **{rights['commercial_purpose_compatibility']}**.",
        "",
        "## The operator route",
        "",
        f"**{fetcher['governance_feasibility']['classification']}.** "
        f"{fetcher['governance_feasibility']['what_is_novel_and_why_a_review_is_needed']}",
        "",
        f"*The honest residual:* {fetcher['fallback_not_forced_solution']['the_honest_residual']}",
        "",
        "## What changed and what did not",
        "",
        "**Resolved this mission:**",
        "",
    ]
    for item in qualification["what_did_change"]["resolved_this_mission"]:
        lines.append(f"- {item}")
    lines += ["", "**Still unresolved:**", ""]
    for item in qualification["what_did_change"]["still_unresolved"]:
        lines.append(f"- {item}")

    lines += [
        "",
        "## Registry",
        "",
        f"Unchanged at {decision['requirement_registry']['count_after']}. A candidate rule was "
        f"offered and not added: "
        f"`{decision['requirement_registry']['candidate_offered_and_not_added']['name']}`.",
        "",
        decision["requirement_registry"]["candidate_offered_and_not_added"]["why_it_was_not_added"],
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    accounting = decision["mission_accounting"]
    for counter in (
        "TARGET_VALUE_EXPOSURES",
        "CRAWLS",
        "TARGET_HTTP_REQUESTS",
        "COMMON_CRAWL_INDEX_QUERIES",
        "WARC_WAT_WET_DOWNLOADS",
        "BIGQUERY_EXECUTIONS",
        "CREDENTIAL_READS",
        "MAILBOX_SEARCHES",
        "SOURCES_REGISTERED",
        "GOVERNANCE_APPROVALS",
        "CONSTRUCTS_FROZEN",
        "PREDICATES_CHOSEN",
        "CRAWLERS_IMPLEMENTED",
        "MODEL_CALLS",
    ):
        lines.append(f"| {counter} | {accounting[counter]} |")
    lines.append("")
    return "\n".join(lines)


RENDERERS = {DECISION: render_decision, POPULATION: render_population}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  web route qualification: {error}")
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
        print(f"ok       {len(rendered)} web-route documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    decision = by_path[DECISION]
    print(f"outcome  {decision['primary_outcome']}")
    print(f"population {by_path[POPULATION]['decision']}")
    print(f"selected {decision['selected_quantity_class'] or 'NONE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
