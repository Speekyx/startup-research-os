"""Render and validate the Mission 1.72 public HTTP observation governance policies.

Eleven records, one ADR, and one discipline underneath all of them:

    WHICH GATE APPLIES IS A FUNCTION OF WHAT IS RETAINED, NEVER A LABEL THE
    CALLER CHOOSES.

`validate()` enforces the readings this mission was most tempted to make and did
not:

  - a new track is not a weakening of the old one, and no target becomes a source;
  - public visibility is still not permission, and a track pass is not a legal
    conclusion;
  - governance feasibility is still not run authorization;
  - a body-retaining configuration is not expressible in the observation track,
    so the boundary is structural rather than a note beside it;
  - robots is a state machine with one outcome per condition, quoted from the
    standard where it follows the standard and marked as ours where it is stricter;
  - a header allowlist that a run could widen into the secret-bearing set is not
    an allowlist;
  - not persisting a body is not the same as not receiving bytes;
  - an excluded target stays in the population and takes a terminal state;
  - unknown terms are neither permission nor an impossible review requirement;
  - and every load bound is finite or explicitly disabled, and every number says
    it is a project policy default rather than a discovered fact.

    uv run python infrastructure/scripts/render_public_http_governance.py
    uv run python infrastructure/scripts/render_public_http_governance.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
ADR_DIR = ROOT / "docs" / "architecture" / "adr"

BASELINE = DATA / "mission-1.72-baseline-v1.json"
DECISION = DATA / "public-http-observation-governance-decision-v1.json"
PRECEDENCE = DATA / "governance-track-precedence-v1.json"
POLICY = DATA / "public-http-observation-policy-v1.json"
ROBOTS = DATA / "public-http-robots-policy-v1.json"
MINIMIZATION = DATA / "public-http-data-minimization-policy-v1.json"
RETENTION = DATA / "public-http-retention-policy-v1.json"
TARGET = DATA / "public-http-target-policy-v1.json"
EXCLUSIONS = DATA / "public-http-target-exclusion-registry-contract-v1.json"
LOAD = DATA / "bounded-http-load-profile-v1.json"
LINKAGE = DATA / "bounded-http-apparatus-policy-linkage-v1.json"

ADR = ADR_DIR / "ADR-039-public-http-observation-governance-track.md"
APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
APPARATUS_CONTRACT = DATA / "sros-bounded-http-apparatus-contract-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
COUNTERPART = DATA / "bounded-http-independent-counterpart-requirements-v1.json"

ORDER = [
    BASELINE,
    DECISION,
    PRECEDENCE,
    POLICY,
    ROBOTS,
    MINIMIZATION,
    RETENTION,
    TARGET,
    EXCLUSIONS,
    LOAD,
    LINKAGE,
]

RENDERED = {
    DECISION: DATA / "mission-1.72-public-http-governance-v1.md",
    LOAD: DATA / "bounded-http-load-profile-v1.md",
}

GOV1_DECISIONS = (
    "PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED",
    "SOURCE_COLLECTION_TRACK_REMAINS_REQUIRED",
    "PER_TARGET_OPERATOR_REVIEW_REQUIRED",
    "NO_GOVERNED_PUBLIC_HTTP_ROUTE_ESTABLISHED",
)

# §4. Uses the observation track may never be stretched to cover.
PROHIBITED_USES = (
    "article ingestion",
    "document corpus acquisition",
    "page-content research",
    "web scraping for ideation",
    "news ingestion",
    "forum ingestion",
    "dataset ingestion",
    "commercial content harvesting",
    "general-purpose site crawling",
)

# §19. Header names a run may never add to its allowlist.
SECRET_BEARING_HEADERS = (
    "Set-Cookie",
    "WWW-Authenticate",
    "Proxy-Authenticate",
    "Authorization",
)

# §34. Every bound a load profile must carry.
REQUIRED_BOUNDS = (
    "MAX_CORPUS_TARGETS",
    "GLOBAL_CONCURRENCY",
    "PER_ORIGIN_CONCURRENCY",
    "PER_ORIGIN_REQUEST_RATE",
    "CONNECT_TIMEOUT",
    "READ_TIMEOUT",
    "MAX_REDIRECTS",
    "MAX_RETRIES",
    "MAX_HEADER_BYTES",
    "MAX_RESPONSE_READ_BYTES",
    "MAX_TOTAL_BYTES_PER_TARGET",
    "MAX_RUN_DURATION",
    "ROBOTS_REQUEST_BUDGET",
    "MAX_REQUESTS_PER_TARGET",
    "BACKOFF_POLICY",
)

# §36. Spellings of "no limit was set".
FORBIDDEN_BOUND_VALUES = (
    None,
    "",
    "unlimited",
    "UNLIMITED",
    "infinite",
    "INFINITE",
    "none",
    "None",
    "automatic",
    "AUTOMATIC",
    "library_default",
)

# §13. Robots conditions that must each have exactly one deterministic outcome.
REQUIRED_ROBOTS_CONDITIONS = (
    "ROBOTS_2XX_PARSEABLE",
    "ROBOTS_404_OR_410",
    "ROBOTS_401_OR_403",
    "ROBOTS_5XX",
    "ROBOTS_NETWORK_FAILURE",
    "ROBOTS_TIMEOUT",
    "ROBOTS_UNPARSEABLE_LINES",
    "ROBOTS_DISALLOWED_FOR_OUR_TOKEN",
)

CENSUS_BLOCKS = ("canonical_baseline", "canonical_mutation_boundary", "mission_accounting")


class ValidationError(RuntimeError):
    """A record says something this mission's rules refuse."""


def _check_the_current_class_selection_is_consistent(path) -> None:
    """A later mission may select a class. It may not select a run.

    Re-pointed by Mission 1.76.6. This replaced a check that the selection artifact must not
    exist, which pinned the repository's future to one mission's historical verdict. What is
    checked now is that whatever selection exists is well formed and authorises nothing.
    """
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    if not str(record.get("class_id") or "").strip():
        raise ValidationError("a quantity-class selection exists and names no class")
    if record.get("state") != "CLASS_SELECTED":
        raise ValidationError(
            f"the quantity-class selection is in state {record.get('state')!r}; selecting a "
            "class is not selecting a construct and is not authorising a run"
        )
    states = record.get("states_kept_apart") or {}
    if not states.get("CLASS_SELECTED"):
        raise ValidationError("the selection does not record that a class was selected")
    for forbidden in ("CONSTRUCT_SELECTED", "RUN_AUTHORIZED"):
        if states.get(forbidden):
            raise ValidationError(
                f"the quantity-class selection records {forbidden}; that is a different "
                "decision and this artifact may not carry it"
            )
    if record.get("corpus_frozen"):
        raise ValidationError("the quantity-class selection freezes a corpus")
    if record.get("measurements_executed") != 0:
        raise ValidationError("the quantity-class selection records a measurement")
    if record.get("exact_predicate_frozen"):
        raise ValidationError("the quantity-class selection freezes a predicate")


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
    """§0 and §50."""
    pre = baseline["repository_precondition"]
    _true(
        baseline,
        ["repository_precondition", "mission_1_71_merged"],
        "the baseline does not record Mission 1.71 as merged",
    )
    if pre["observed_main"] != pre["expected_main"]:
        raise ValidationError("the observed main does not match the expected commit")
    for flag in (
        "local_matches_origin",
        "working_tree_clean",
        "selected_quantity_class_artifact_absent",
        "selected_construct_artifact_absent",
    ):
        _true(baseline, ["repository_precondition", flag], f"the precondition {flag} is not met")
    for flag in ("crawler_implementation_exists", "counterpart_selected"):
        _false(baseline, ["repository_precondition", flag], f"the baseline records {flag}")

    if baseline["canonical_baseline"]["drift_from_mission_1_71"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["canonical_baseline"]["migration_head"] != "0035_refusal_provenance":
        raise ValidationError("the migration head moved")
    if baseline["canonical_baseline"]["registered_sources"] != 29:
        raise ValidationError("the registered source count moved")

    scope = baseline["scope"]
    if scope["resolves"] != ["GOV-1", "GOV-2", "GOV-3", "GOV-4", "GOV-5"]:
        raise ValidationError("the mission scope is not the five decisions")
    for flag in (
        "counterpart_discovery_performed",
        "quantity_class_discovery_performed",
        "construct_selected",
        "predicate_selected",
        "crawler_implemented",
        "scanner_class_reopened",
    ):
        _false(baseline, ["scope", flag], f"the scope records {flag}")

    budget = baseline["documentation_budget"]
    if budget["used"] > budget["maximum_requests"]:
        raise ValidationError("the documentation budget was exceeded")
    if len(budget["requests"]) != budget["used"]:
        raise ValidationError("the recorded requests do not match the count used")
    for request in budget["requests"]:
        _false(request, ["is_a_target_inspection"], "a documentation request inspected a target")
    if budget["target_sites_inspected"] != 0 or budget["targets_browsed"] != 0:
        raise ValidationError("target sites were inspected or browsed")


def _check_gov1(decision: dict) -> None:
    """§1 to §8, §49."""
    if decision["decision"] not in GOV1_DECISIONS:
        raise ValidationError(f"the GOV-1 decision {decision['decision']!r} is not one of the four")
    if not decision.get("adr"):
        raise ValidationError("the GOV-1 decision names no ADR")
    if not ADR.exists():
        raise ValidationError("the ADR file does not exist")

    for model in (
        "MODEL_A_SOURCE_COLLECTION_ONLY",
        "MODEL_B_PUBLIC_HTTP_OBSERVATION_TRACK",
        "MODEL_C_PER_TARGET_OPERATOR_REVIEW",
        "MODEL_D_NO_GOVERNED_ROUTE",
    ):
        if model not in decision["models_evaluated"]:
            raise ValidationError(f"{model} was not evaluated")
        if not str(decision["models_evaluated"][model]["why"]).strip():
            raise ValidationError(f"{model} carries no reason")
    adopted = [m for m, v in decision["models_evaluated"].items() if v["adopted"]]
    if len(adopted) != 1:
        raise ValidationError(f"exactly one model must be adopted, found {len(adopted)}")

    # §49. The new track may never be a weakening of the old gate.
    _false(
        decision,
        ["source_collection_governance_weakened"],
        "source collection governance was weakened",
    )
    _true(
        decision,
        ["no_target_becomes_a_source_automatically"],
        "a target may become a source automatically",
    )
    if decision["registered_sources_before"] != decision["registered_sources_after"]:
        raise ValidationError("the registered source count changed")

    # §54.
    _false(decision, ["legal_conclusion_made"], "a legal conclusion was made")
    for banned in (
        "LEGAL",
        "COMPLIANT_WITH_ALL_TARGET_TERMS",
        "ROBOTS_EQUALS_PERMISSION",
        "PUBLIC_MEANS_ALLOWED",
    ):
        if banned in decision["vocabulary_used"]:
            raise ValidationError(f"the decision uses the forbidden vocabulary {banned}")

    _true(
        decision,
        ["run_authorization_required"],
        "GOV-1 was decided without requiring run authorization",
    )
    _false(decision, ["authorised_by_this_mission"], "this mission authorised a run")

    # The conditionality that makes the adoption defensible.
    if decision["decision"] == "PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED":
        condition = decision["the_condition"]
        if not str(condition["statement"]).strip():
            raise ValidationError("the track was adopted with no stated condition")
        _true(
            condition,
            ["satisfied_by_gov_3"],
            "the track was adopted and its condition is not satisfied by GOV-3",
        )
        test = decision["distinguishing_test"]
        if test["answer_1"] != "no" or test["answer_2"] != "yes":
            raise ValidationError(
                "the distinguishing test does not distinguish, so the track rests on a name"
            )
        _true(
            test,
            ["and_it_holds_only_under_the_condition_above"],
            "the distinguishing test is claimed to hold unconditionally",
        )


def _check_precedence(precedence: dict, minimization: dict) -> None:
    """§4, §7, §48."""
    for track in ("SOURCE_COLLECTION", "PUBLIC_HTTP_OBSERVATION"):
        if track not in precedence["tracks"]:
            raise ValidationError(f"{track} is not described")
    _true(
        precedence,
        ["tracks", "SOURCE_COLLECTION", "unchanged_by_this_mission"],
        "the source collection track was changed",
    )

    rule = precedence["precedence_rule"]
    _false(rule, ["caller_may_choose_its_track"], "the caller may choose its own track")
    if rule["when_both_could_apply"] != "SOURCE_COLLECTION wins":
        raise ValidationError("source collection does not win when both tracks could apply")
    if not str(rule["rule"]).strip():
        raise ValidationError("the precedence rule is empty")

    for use in PROHIBITED_USES:
        if use not in precedence["the_observation_track_may_not_be_used_for"]:
            raise ValidationError(f"the observation track does not prohibit: {use}")
    _true(
        precedence,
        ["enforced_structurally_rather_than_by_prose"],
        "the track boundary is enforced by prose alone",
    )
    _true(
        precedence,
        ["a_caller_can_determine_the_gate_deterministically"],
        "a caller cannot deterministically determine which gate applies",
    )

    forbidden = precedence["forbidden_repository_changes"]
    for flag in (
        "making_arbitrary_public_sites_eligible_sources",
        "making_unknown_source_rights_pass",
        "relabelling_measurement_targets_as_registered_sources",
    ):
        _false(forbidden, [flag], f"the record permits: {flag}")

    # The structural claim must actually be true of the retention contract.
    persisted = {
        row["class"] for row in minimization["data_classes"] if row["persist_allowed"] is True
    }
    if "RESPONSE_BODY" in persisted:
        raise ValidationError(
            "the observation track's own contract persists a body, so the boundary the "
            "precedence rule claims to enforce structurally is not enforced"
        )


def _check_policy(policy: dict) -> None:
    """§5, §26, §41, §42, §43."""
    for requirement in policy["eligibility_requirements"]:
        _false(
            requirement,
            ["defaults_to_approval_when_unknown"],
            f"the requirement {requirement['requirement']!r} defaults to approval when unknown",
        )
    if len(policy["eligibility_requirements"]) != policy["requirement_count"]:
        raise ValidationError("the eligibility requirement count does not match the list")

    purpose = policy["measurement_purpose"]
    _true(purpose, ["required"], "a run may proceed without a measurement purpose")
    _false(purpose, ["no_reason_supplied_is_acceptable"], "no reason supplied is acceptable")
    _false(
        purpose,
        ["general_exploration_is_authorization"],
        "general exploration is treated as measurement authorization",
    )
    for binding in (
        "measurement purpose",
        "corpus manifest",
        "request contract",
        "apparatus contract",
        "run manifest",
        "operator authorization",
    ):
        if binding not in purpose["a_run_must_bind"]:
            raise ValidationError(f"a run does not bind {binding}")

    visibility = policy["public_visibility_and_permission"]
    _false(visibility, ["public_implies_permission"], "public visibility is treated as permission")
    _false(
        visibility,
        ["this_is_a_claim_about_external_legal_rights"],
        "the track rule is presented as a claim about external legal rights",
    )
    _true(
        visibility,
        ["target_specific_review_may_still_apply"],
        "the policy denies that target-specific review may still apply",
    )

    authorization = policy["run_authorization"]
    _true(authorization, ["required"], "run authorization is not required")
    _false(authorization, ["granted_by_this_mission"], "this mission granted run authorization")
    _false(
        authorization,
        ["governance_track_membership_is_operator_authorization"],
        "track membership is conflated with operator authorization",
    )

    boundary = policy["future_construct_boundary"]
    for key in (
        "header_selected",
        "status_code_selected",
        "html_token_selected",
        "technology_selected",
    ):
        if boundary[key] is not None:
            raise ValidationError(f"the policy selected {key}, which belongs to a construct")
    if boundary["what_fact_will_be_measured"] != "NOT_CHOSEN_BY_THIS_MISSION":
        raise ValidationError("this mission chose what fact will be measured")

    if "LEGAL" in policy["overall"] or "COMPLIANT" in policy["overall"]:
        raise ValidationError("the policy verdict claims legality or compliance")
    if policy["external_legal_conclusion"] != "NO_EXTERNAL_LEGAL_CONCLUSION":
        raise ValidationError("an external legal conclusion was drawn")


def _check_robots(robots: dict) -> None:
    """§9 to §15."""
    selected = [k for k, v in robots["options_evaluated"].items() if v["selected"]]
    if len(selected) != 1:
        raise ValidationError(f"exactly one robots option must be selected, found {len(selected)}")
    if robots["decision"] != selected[0]:
        raise ValidationError("the robots decision does not match the selected option")
    for name, option in robots["options_evaluated"].items():
        if not str(option["why"]).strip():
            raise ValidationError(f"the robots option {name} carries no reason")

    _false(
        robots,
        ["robots_is_a_legal_permission_system"],
        "robots is presented as a legal permission system",
    )

    machine = {row["condition"]: row for row in robots["state_machine"]}
    for condition in REQUIRED_ROBOTS_CONDITIONS:
        if condition not in machine:
            raise ValidationError(f"the robots state machine does not define {condition}")
        if not str(machine[condition]["outcome"]).strip():
            raise ValidationError(f"{condition} has no outcome")
    if len(machine) != robots["state_count"]:
        raise ValidationError("the robots state count does not match the machine")
    _true(
        robots,
        ["every_condition_has_exactly_one_outcome"],
        "a robots condition may have more than one outcome",
    )
    _false(
        robots, ["a_target_may_switch_behaviour_silently"], "a target may switch behaviour silently"
    )

    # A row stricter than the standard must say so, and one that is not must not
    # attribute the project's choice to the standard.
    for row in robots["state_machine"]:
        if row["stricter_than_the_rfc"] not in (True, False):
            raise ValidationError(f"{row['condition']} does not say whether it is stricter")
        if row["stricter_than_the_rfc"] and not str(row.get("why") or "").strip():
            raise ValidationError(
                f"{row['condition']} is stricter than the standard and gives no reason"
            )
        if not str(row["rfc_9309_position"]).strip():
            raise ValidationError(f"{row['condition']} states no standard position")

    provenance = robots["rfc_provenance"]
    _true(provenance, ["quoted_rather_than_recalled"], "the standard was recalled rather than read")
    _true(provenance, ["retrieved_this_mission"], "the standard was not retrieved")
    if not str(provenance["retrieved_from"]).strip():
        raise ValidationError("the standard's provenance names no source")

    preflight = robots["preflight"]
    _true(preflight, ["robots_fetch_required"], "robots retrieval is not required")
    _true(preflight, ["consumes_request_budget"], "robots retrieval does not consume budget")
    _true(
        preflight,
        ["counted_toward_per_origin_budget"],
        "robots requests are not counted toward the origin budget",
    )
    _false(
        preflight,
        ["an_excluded_target_leaves_the_population"],
        "a robots-excluded target leaves the population",
    )

    agent = robots["user_agent_binding"]
    _true(
        agent, ["apparatus_has_a_named_product_token"], "the apparatus has no named product token"
    )
    _true(
        agent,
        ["the_token_is_the_same_string_sent_in_user_agent"],
        "the robots token differs from the User-Agent actually sent",
    )
    _false(
        agent,
        ["evaluating_the_wildcard_group_when_a_specific_group_exists"],
        "the wildcard group is evaluated when a specific group exists",
    )

    if robots["requests_made_this_mission"] != 0 or robots["robots_target_requests"] != 0:
        raise ValidationError("robots requests were made against targets")


def _check_minimization(minimization: dict) -> None:
    """§16 to §22."""
    selected = [k for k, v in minimization["options_evaluated"].items() if v["selected"]]
    if len(selected) != 1:
        raise ValidationError("exactly one minimization option must be selected")
    if minimization["decision"] != selected[0]:
        raise ValidationError("the minimization decision does not match the selected option")

    body = minimization["body"]
    if body["BODY_PERSISTENCE_DEFAULT"] != "DISABLED":
        raise ValidationError("body persistence is not disabled by default")
    _false(
        body,
        ["body_bytes_may_be_persisted_in_the_initial_profile"],
        "body bytes may be persisted in the initial profile",
    )
    _false(
        body,
        ["available_because_the_client_supports_it"],
        "body capture is available because the client supports it",
    )
    _false(
        body,
        ["not_persisting_is_the_same_as_not_receiving"],
        "not persisting a body is conflated with not receiving bytes",
    )
    _true(
        body,
        ["network_read_still_bounded"],
        "the network read is unbounded because no body is persisted",
    )

    headers = minimization["headers"]
    _false(headers, ["all_response_headers_persisted"], "all response headers are persisted")
    excluded = {h.lower() for h in headers["always_excluded"]}
    for header in SECRET_BEARING_HEADERS:
        if header.lower() not in excluded:
            raise ValidationError(f"{header} is not always excluded")
    _false(
        headers,
        ["a_run_may_extend_it_into_the_always_excluded_set"],
        "a run may extend the allowlist into the secret-bearing set",
    )
    for header in headers["default_persisted_allowlist"]:
        if header.lower() in excluded:
            raise ValidationError(f"{header} is both allowlisted by default and always excluded")
    _false(headers, ["perfect_secret_detection_claimed"], "perfect secret detection is claimed")

    location = minimization["location_header"]
    if location["raw_value"] != "TRANSIENT_ONLY":
        raise ValidationError("a raw Location value is persisted")
    _false(location, ["query_string_persisted"], "a Location query string is persisted")
    _false(
        location,
        ["information_discarded_while_claiming_exact_provenance"],
        "information is discarded while exact provenance is claimed",
    )

    classes = {row["class"]: row for row in minimization["data_classes"]}
    if classes["RESPONSE_BODY"]["persist_allowed"] is not False:
        raise ValidationError("the response body is persistable")
    if classes["RESPONSE_HEADERS"]["persist_allowed"] is True:
        raise ValidationError("response headers are persistable without an allowlist")
    _false(minimization, ["one_global_retention_rule"], "one global retention rule is applied")

    sensitive = minimization["sensitive_content"]
    for flag in (
        "arbitrary_full_body_persistence_by_default",
        "credential_or_token_persistence_by_default",
        "target_response_content_copied_into_debug_logs",
    ):
        _false(sensitive, [flag], f"the policy permits: {flag}")
    if minimization["content_retrieved_this_mission"] != 0:
        raise ValidationError("content was retrieved")


def _check_retention(retention: dict, minimization: dict) -> None:
    """§23."""
    if not retention["retention_by_class"]:
        raise ValidationError("no retention class is defined")
    for row in retention["retention_by_class"]:
        if row["decision_kind"] != "PROJECT_POLICY_DEFAULT":
            raise ValidationError(
                f"the retention value for {row['retention_class']} is not marked a project "
                "policy default, so it reads as a discovered fact"
            )
        if not isinstance(row["retention_days"], int) or row["retention_days"] < 0:
            raise ValidationError(f"{row['retention_class']} has no finite retention")
        if not str(row["why"]).strip():
            raise ValidationError(f"{row['retention_class']} carries no reason")
    for flag in (
        "values_presented_as_evidence_derived",
        "values_presented_as_industry_safe",
        "values_presented_as_legally_required",
        "values_presented_as_provider_recommended",
    ):
        _false(retention, [flag], f"retention values are presented as {flag}")
    _false(
        retention,
        [
            "relationship_to_the_project_retention_policy",
            "this_policy_lengthens_any_existing_retention",
        ],
        "this policy lengthens an existing retention, which the stricter-rule wins",
    )

    # A class that persists nothing must not be given a retention span.
    not_persisted = {
        row["class"]
        for row in minimization["data_classes"]
        if row["retention_class"] == "NOT_PERSISTED"
    }
    for row in retention["retention_by_class"]:
        if row["retention_class"] == "NOT_PERSISTED" and row["retention_days"] != 0:
            raise ValidationError("a non-persisted class carries a retention span")
    if not not_persisted:
        raise ValidationError("no data class is marked NOT_PERSISTED, so nothing is minimized")


def _check_target(target: dict, exclusions: dict) -> None:
    """§25 to §32."""
    classes = {row["class"]: row for row in target["classes"]}
    for required in (
        "ELIGIBLE_PUBLIC_TARGET",
        "ROBOTS_EXCLUDED",
        "KNOWN_OPT_OUT",
        "AUTH_REQUIRED",
        "DESTINATION_SAFETY_BLOCKED",
        "UNSUPPORTED_SCHEME",
        "OPERATOR_EXCLUDED",
        "KNOWN_AUTOMATION_RESTRICTION",
        "UNKNOWN_POLICY_CONDITION",
    ):
        if required not in classes:
            raise ValidationError(f"the target policy does not define {required}")
    proceeding = [name for name, row in classes.items() if row["proceeds"]]
    if proceeding != ["ELIGIBLE_PUBLIC_TARGET"]:
        raise ValidationError(f"classes other than the eligible one proceed: {proceeding}")
    if classes["UNKNOWN_POLICY_CONDITION"]["proceeds"] is not False:
        raise ValidationError("an unclassifiable condition proceeds")

    _false(
        target,
        ["public_visibility_and_permission", "public_implies_permission"],
        "public visibility is treated as permission",
    )
    known = target["known_restrictions"]
    for flag in (
        "an_explicit_opt_out_excludes",
        "a_known_automation_restriction_relevant_to_this_activity_excludes",
        "an_operator_exclusion_excludes",
    ):
        _true(known, [flag], f"a known restriction does not exclude: {flag}")
    _false(
        known,
        ["a_known_restriction_may_be_deliberately_ignored"],
        "a known restriction may be deliberately ignored",
    )

    unknown = target["unknown_terms"]
    if unknown["state"] != "TARGET_TERMS_NOT_INDIVIDUALLY_REVIEWED":
        raise ValidationError("unknown terms carry the wrong state")
    _false(
        unknown,
        ["absence_of_inspection_read_as_absence_of_restriction"],
        "an absence of inspection is read as an absence of restriction",
    )
    _false(
        unknown,
        ["manual_terms_review_of_every_corpus_item_required"],
        "a manual review of every corpus item is required, which reinstates Model C",
    )
    _true(
        unknown,
        ["target_specific_review_may_still_apply"],
        "the policy denies that target-specific review may still apply",
    )

    ordering = target["preflight_ordering"]
    _true(ordering, ["first_match_wins"], "the preflight ordering is not first-match-wins")
    for name in classes:
        if name not in ordering["order"]:
            raise ValidationError(f"{name} is not in the preflight ordering")
    if len(ordering["order"]) != len(set(ordering["order"])):
        raise ValidationError("the preflight ordering repeats a class")
    if ordering["order"][-1] != "ELIGIBLE_PUBLIC_TARGET":
        raise ValidationError("the eligible class is not last, so a check could be skipped")

    population = target["excluded_targets_and_the_population"]
    _false(
        population,
        ["an_excluded_target_is_removed_from_the_corpus"],
        "an excluded target is removed from the corpus, which shrinks N",
    )
    _false(population, ["the_original_frozen_corpus_is_edited"], "the frozen corpus is edited")

    if target["targets_classified_this_mission"] != 0 or target["corpus_exists"] is not False:
        raise ValidationError("targets were classified or a corpus exists")

    required = {row["field"] for row in exclusions["entry_fields"] if row["required"]}
    for field in (
        "target_scope",
        "reason",
        "basis",
        "recorded_at",
        "effective_from",
        "operator",
        "status",
    ):
        if field not in required:
            raise ValidationError(f"an exclusion entry does not require {field}")
    _true(
        exclusions,
        ["hashing", "a_run_binds_a_registry_version_and_hash"],
        "a run does not bind an exclusion registry hash",
    )
    _true(
        exclusions,
        ["freeze", "effective_set_frozen_before_execution"],
        "the exclusion set is not frozen before execution",
    )
    _false(
        exclusions,
        ["freeze", "the_pre_run_manifest_may_be_silently_rewritten"],
        "the pre-run manifest may be silently rewritten",
    )
    if exclusions["entries"] or exclusions["entry_count"] != 0:
        raise ValidationError("exclusion entries were created, and no corpus exists")


def _check_load(load: dict) -> None:
    """§33 to §40."""
    bounds = {row["bound"]: row for row in load["bounds"]}
    for required in REQUIRED_BOUNDS:
        if required not in bounds:
            raise ValidationError(f"the load profile does not set {required}")
    if len(bounds) != load["bound_count"]:
        raise ValidationError("the load bound count does not match the profile")

    for name, row in bounds.items():
        value = row["value"]
        if value in FORBIDDEN_BOUND_VALUES and value != "DISABLED":
            raise ValidationError(f"{name} carries a non-limit value: {value!r}")
        if isinstance(value, str) and value != "DISABLED":
            raise ValidationError(f"{name} carries a non-numeric value that is not DISABLED")
        if isinstance(value, (int, float)) and value < 0:
            raise ValidationError(f"{name} is negative")
        if row["value_source"] != "PROJECT_POLICY_DEFAULT":
            raise ValidationError(
                f"{name} does not carry PROJECT_POLICY_DEFAULT provenance, so it reads as a "
                "discovered safety fact"
            )
        if not str(row["why"]).strip():
            raise ValidationError(f"{name} carries no reason")

    _true(
        load,
        ["every_value_is_finite_or_explicitly_disabled"],
        "some load bound is neither finite nor explicitly disabled",
    )
    _true(
        load,
        ["every_value_source_is_project_policy"],
        "some load value is not a project policy default",
    )
    for flag in (
        "safe_according_to_industry",
        "legally_required",
        "provider_recommended",
        "evidence_derived",
    ):
        _false(load, ["values_presented_as", flag], f"load values are presented as {flag}")

    accounting = load["per_origin_accounting"]
    _false(accounting, ["one_target_equals_one_request"], "one target is treated as one request")
    _true(
        accounting,
        ["redirects_count_toward_the_origin_budget"],
        "redirects do not count toward the origin budget",
    )
    _true(
        accounting,
        ["robots_requests_count_toward_the_origin_budget"],
        "robots requests do not count toward the origin budget",
    )

    interaction = load["body_and_network_interaction"]
    _false(
        interaction,
        ["not_persisting_a_body_means_not_receiving_bytes"],
        "not persisting a body is conflated with not receiving bytes",
    )
    _true(
        interaction,
        ["the_apparatus_terminates_reading_under_a_finite_bound"],
        "the apparatus does not terminate reading under a finite bound",
    )

    # A per-target request budget that cannot cover its own redirect limit is incoherent.
    if bounds["MAX_REQUESTS_PER_TARGET"]["value"] < bounds["MAX_REDIRECTS"]["value"] + 1:
        raise ValidationError(
            "MAX_REQUESTS_PER_TARGET cannot cover one request plus MAX_REDIRECTS hops"
        )
    if bounds["MAX_TOTAL_BYTES_PER_TARGET"]["value"] < bounds["MAX_RESPONSE_READ_BYTES"]["value"]:
        raise ValidationError("the per-target byte cap is below a single response read cap")
    if bounds["MAX_RETRIES"]["value"] != 0 and load["retry_reasoning"].get("why_non_zero") is None:
        raise ValidationError("retries are enabled with no stated reason")


def _check_linkage(linkage: dict, baseline: dict) -> None:
    """§11, §45, §46, §47."""
    resolved = {row["gov"] for row in linkage["resolved_rows"]}
    for gov in ("GOV-1", "GOV-2", "GOV-3", "GOV-4", "GOV-5"):
        if gov not in resolved:
            raise ValidationError(f"{gov} is not linked to a resolving artifact")
    for row in linkage["resolved_rows"]:
        if not str(row["resolved_by"]).strip() or not str(row["decision"]).strip():
            raise ValidationError(f"{row['gov']} names no artifact or no decision")

    _false(linkage, ["fetcher_implemented"], "the fetcher was implemented")
    _true(linkage, ["run_authorization_required"], "run authorization is not required")
    _true(
        linkage,
        ["second_independent_route_still_required"],
        "a second independent route is no longer required",
    )

    held = linkage["held_state_not_reopened"]
    for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
        if held[route] != "unchanged from Mission 1.70":
            raise ValidationError(f"{route}'s state was changed")
    _false(
        held,
        ["a_new_internal_track_repairs_their_missingness"],
        "the new track is claimed to repair external missingness",
    )
    if held["scanner_arc"] != "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE":
        raise ValidationError("the scanner arc status changed")

    registry = linkage["requirement_registry"]
    requirements = _load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
    if len(requirements) != 15:
        raise ValidationError(f"the registry holds {len(requirements)} requirements, not 15")
    if registry["count_before"] != 15 or registry["count_after"] != 15:
        raise ValidationError("the linkage disagrees with the registry count")
    _false(registry, ["added"], "the candidate rule was added from design evidence")
    if baseline["requirement_registry"]["count_before"] != len(requirements):
        raise ValidationError("the baseline and the registry disagree")
    names = {row["name"] for row in requirements}
    if registry["candidate_rule"] in names:
        raise ValidationError("a rule recorded as NOT added is in the registry")


def _check_no_execution(records: list[dict]) -> None:
    """§44, §51, §52."""
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

    _check_the_current_class_selection_is_consistent(SELECTED_CLASS)
    if SELECTED_CONSTRUCT.exists():
        raise ValidationError("selected-construct-v1.json exists and no construct was selected")

    # Mission 1.71's own records stay as they were written.
    apparatus = _load(APPARATUS_CONTRACT)
    if apparatus["implemented"] is not False:
        raise ValidationError("Mission 1.71's apparatus record now says implemented")
    counterpart = _load(COUNTERPART)
    if counterpart["counterpart_selected"] is not False:
        raise ValidationError("a counterpart was selected")
    if counterpart["counterpart_candidates_evaluated"] != 0:
        raise ValidationError("counterpart candidates were evaluated, which §44 prohibits")


def validate() -> list[dict]:
    records = [_load(path) for path in ORDER]
    (
        baseline,
        decision,
        precedence,
        policy,
        robots,
        minimization,
        retention,
        target,
        exclusions,
        load,
        linkage,
    ) = records

    _check_preconditions(baseline)
    _check_gov1(decision)
    _check_precedence(precedence, minimization)
    _check_policy(policy)
    _check_robots(robots)
    _check_minimization(minimization)
    _check_retention(retention, minimization)
    _check_target(target, exclusions)
    _check_load(load)
    _check_linkage(linkage, baseline)
    _check_no_execution(records)

    parallel = baseline["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    if parallel["netlas_contact"] != "STILL_PENDING":
        raise ValidationError("the Netlas contact state moved")
    if parallel["q1_status"] != "PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED":
        raise ValidationError("the Q1 status changed")

    return records


# ------------------------------------------------------------------------ renderers


def render_governance(decision: dict) -> str:
    precedence = _load(PRECEDENCE)
    policy = _load(POLICY)
    robots = _load(ROBOTS)
    minimization = _load(MINIMIZATION)
    target = _load(TARGET)
    linkage = _load(LINKAGE)

    lines = [
        "# Mission 1.72 — Public HTTP observation governance",
        "",
        "Generated from `public-http-observation-governance-decision-v1.json` and the policy",
        "records. Do not edit by hand.",
        "",
        f"**GOV-1: `{decision['decision']}`**, conditionally "
        f"({decision['adopted_conditionally']}), under {decision['adr']}.",
        "",
        "## The condition, which is what makes it defensible",
        "",
        decision["the_condition"]["statement"],
        "",
        f"Satisfied by GOV-3: **{decision['the_condition']['satisfied_by_gov_3']}** "
        f"(`{decision['the_condition']['gov_3_decision_that_satisfies_it']}`). "
        f"{decision['the_condition']['if_gov_3_had_chosen_full_response'].capitalize()}.",
        "",
        "## Is the distinction real, or a smaller name for the same act?",
        "",
        "| question | answer |",
        "|---|---|",
        f"| {decision['distinguishing_test']['question_1']} | "
        f"**{decision['distinguishing_test']['answer_1']}** |",
        f"| {decision['distinguishing_test']['question_2']} | "
        f"**{decision['distinguishing_test']['answer_2']}** |",
        "",
        decision["distinguishing_test"]["conclusion"],
        "",
        "## Models evaluated",
        "",
        "| model | adopted |",
        "|---|---|",
    ]
    for model, entry in decision["models_evaluated"].items():
        lines.append(f"| {model} | {entry['adopted']} |")
    lines += ["", "Why, for each:", ""]
    for model, entry in decision["models_evaluated"].items():
        lines.append(f"- **{model}** — {entry['why']}")

    lines += [
        "",
        "## Precedence",
        "",
        precedence["precedence_rule"]["rule"],
        "",
        f"Caller may choose its track: **{precedence['precedence_rule']['caller_may_choose_its_track']}**. "
        f"When both could apply: **{precedence['precedence_rule']['when_both_could_apply']}**.",
        "",
        f"*How it is enforced:* {precedence['how_it_is_enforced']}",
        "",
        "The observation track may not be used for:",
        "",
    ]
    for use in precedence["the_observation_track_may_not_be_used_for"]:
        lines.append(f"- {use}")

    lines += [
        "",
        "## The five decisions",
        "",
        "| | decision | resolved by |",
        "|---|---|---|",
    ]
    for row in linkage["resolved_rows"]:
        lines.append(f"| {row['gov']} | `{row['decision']}` | {row['resolved_by']} |")

    lines += [
        "",
        "## Robots, condition by condition",
        "",
        "| condition | outcome | stricter than RFC 9309 |",
        "|---|---|---|",
    ]
    for row in robots["state_machine"]:
        lines.append(
            f"| `{row['condition']}` | `{row['outcome']}` | {row['stricter_than_the_rfc']} |"
        )
    lines += [
        "",
        f"Standard read rather than recalled: **{robots['rfc_provenance']['quoted_rather_than_recalled']}** "
        f"({robots['rfc_provenance']['retrieved_from']}).",
        "",
        "## What is retained",
        "",
        "| data class | capture | persist | retention |",
        "|---|---|---|---|",
    ]
    for row in minimization["data_classes"]:
        lines.append(
            f"| {row['class']} | {row['capture_allowed']} | {row['persist_allowed']} "
            f"| {row['retention_class']} |"
        )
    lines += [
        "",
        f"Body persistence: **{minimization['body']['BODY_PERSISTENCE_DEFAULT']}**, and "
        f"not persisting is the same as not receiving: "
        f"**{minimization['body']['not_persisting_is_the_same_as_not_receiving']}**.",
        "",
        "## Targets",
        "",
        "| class | proceeds |",
        "|---|---|",
    ]
    for row in target["classes"]:
        lines.append(f"| `{row['class']}` | {row['proceeds']} |")
    lines += [
        "",
        f"Unknown terms: **{target['unknown_terms']['state']}**. "
        f"{target['unknown_terms']['what_the_state_asserts']}",
        "",
        f"An excluded target is removed from the corpus: "
        f"**{target['excluded_targets_and_the_population']['an_excluded_target_is_removed_from_the_corpus']}**. "
        f"{target['excluded_targets_and_the_population']['why']}",
        "",
        "## Nothing is authorized",
        "",
        f"- run authorization required: **{policy['run_authorization']['required']}**",
        f"- granted by this mission: **{policy['run_authorization']['granted_by_this_mission']}**",
        f"- fetcher implemented: **{linkage['fetcher_implemented']}**",
        f"- second independent route still required: "
        f"**{linkage['second_independent_route_still_required']}**",
        f"- external legal conclusion: **{policy['external_legal_conclusion']}**",
        "",
    ]
    return "\n".join(lines)


def render_load(load: dict) -> str:
    lines = [
        "# Mission 1.72 — The bounded HTTP load profile",
        "",
        "Generated from `bounded-http-load-profile-v1.json`. Do not edit by hand.",
        "",
        f"**`{load['profile_id']}`.** {load['selection_principle']['principle']}, optimised for",
        "a bounded pilot rather than throughput.",
        "",
        "**Every value below is a project policy default.** None of them is a discovered safety",
        "fact, an industry standard, a legal requirement or a provider recommendation.",
        "",
        "| bound | value | unit | source |",
        "|---|---|---|---|",
    ]
    for row in load["bounds"]:
        lines.append(
            f"| `{row['bound']}` | {row['value']} | {row['unit']} | `{row['value_source']}` |"
        )
    lines += ["", "Why, for each:", ""]
    for row in load["bounds"]:
        lines.append(f"- **{row['bound']}** — {row['why']}")

    accounting = load["per_origin_accounting"]
    lines += [
        "",
        "## One target is not one request",
        "",
        f"One target equals one request: **{accounting['one_target_equals_one_request']}**. "
        f"Redirects and robots retrievals both count toward the origin budget, and a run must",
        "report:",
        "",
    ]
    for item in accounting["the_run_must_report"]:
        lines.append(f"- {item}")

    interaction = load["body_and_network_interaction"]
    lines += [
        "",
        "## Body disabled, network still bounded",
        "",
        f"Body persistence is `{interaction['body_persistence']}` and the network read is bounded",
        f"by `{interaction['network_read_bound']}`. Not persisting a body means not receiving",
        f"bytes: **{interaction['not_persisting_a_body_means_not_receiving_bytes']}**.",
        "",
    ]
    return "\n".join(lines)


RENDERERS = {DECISION: render_governance, LOAD: render_load}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  public HTTP governance: {error}")
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
        print(f"ok       {len(rendered)} public-HTTP governance documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    print(f"GOV-1    {by_path[DECISION]['decision']}")
    print(f"GOV-2    {by_path[ROBOTS]['decision']}")
    print(f"GOV-3    {by_path[MINIMIZATION]['decision']}")
    print(f"GOV-5    {by_path[LOAD]['bound_count']} bounds, all project policy defaults")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
