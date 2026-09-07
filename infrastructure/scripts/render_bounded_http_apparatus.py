"""Render and validate the Mission 1.71 bounded HTTP apparatus design.

Thirteen records, and one discipline underneath all of them:

    A MEASUREMENT APPARATUS WE CONTROL IS ONLY WORTH BUILDING IF IT PUBLISHES
    WHAT THE EXTERNAL ROUTES WOULD NOT: WHICH ITEMS IT ASKED ABOUT, WHICH IT
    REACHED, AND WHY THE REST ARE MISSING.

`validate()` enforces the readings this design was most tempted to make and did
not:

  - governance feasibility is not run authorization, and a design is not a permission;
  - a public-looking URL is not a safe destination, and one validated address does
    not validate a host;
  - a redirect is a new destination, checked again, every hop;
  - an item that was never attempted is still in the population;
  - attempted is not successful, and an apparatus failure is not the target's silence;
  - a retry does not overwrite the attempt before it, and a redirect does not
    quietly change which entity was measured;
  - capability is not permitted retention, and what is retained decides which
    governance regime applies;
  - running an apparatus ourselves supplies directability, never independence, and
    two local processes are one apparatus run twice;
  - and designing around a failure mode is not observing a second instance of it.

    uv run python infrastructure/scripts/render_bounded_http_apparatus.py
    uv run python infrastructure/scripts/render_bounded_http_apparatus.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.71-baseline-v1.json"
GOVERNANCE = DATA / "bounded-http-governance-feasibility-v1.json"
APPARATUS = DATA / "sros-bounded-http-apparatus-contract-v1.json"
REQUEST = DATA / "bounded-http-request-contract-schema-v1.json"
CORPUS = DATA / "bounded-http-corpus-manifest-contract-v1.json"
RUN = DATA / "bounded-http-run-manifest-contract-v1.json"
TERMINALS = DATA / "bounded-http-terminal-outcome-taxonomy-v1.json"
MISSINGNESS = DATA / "bounded-http-missingness-contract-v1.json"
NETWORK = DATA / "bounded-http-network-safety-contract-v1.json"
MINIMIZATION = DATA / "bounded-http-data-minimization-review-v1.json"
COUNTERPART = DATA / "bounded-http-independent-counterpart-requirements-v1.json"
PILOT = DATA / "bounded-http-bounded-pilot-feasibility-v1.json"
CANDIDATE = DATA / "coverage-semantics-candidate-rule-review-v1.json"

APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
DECISION_V2 = DATA / "quantity-class-selection-decision-v2.json"
FETCHER_1_70 = DATA / "sros-bounded-http-fetcher-feasibility-v1.json"

ORDER = [
    BASELINE,
    GOVERNANCE,
    APPARATUS,
    REQUEST,
    CORPUS,
    RUN,
    TERMINALS,
    MISSINGNESS,
    NETWORK,
    MINIMIZATION,
    COUNTERPART,
    PILOT,
    CANDIDATE,
]

RENDERED = {
    GOVERNANCE: DATA / "mission-1.71-bounded-http-apparatus-v1.md",
    TERMINALS: DATA / "bounded-http-accounting-model-v1.md",
}

RUBRIC_VERDICTS = ("PASS_IN_PRINCIPLE", "REQUIRES_DEDICATED_POLICY", "BLOCKED", "UNKNOWN")

RUBRIC_DIMENSIONS = (
    "TARGET_SCOPE",
    "NETWORK_SAFETY",
    "REQUEST_SAFETY",
    "LOAD_SAFETY",
    "AUTHENTICATION_BOUNDARY",
    "ANTI_BOT_BOUNDARY",
    "DATA_MINIMIZATION",
    "SENSITIVE_CONTENT_HANDLING",
    "ROBOTS_POLICY",
    "TARGET_TERMS_HANDLING",
    "LOGGING",
    "RETENTION",
    "OPERATOR_AUTHORIZATION",
    "ABORTABILITY",
    "AUDITABILITY",
    "RUN_REPRODUCIBILITY",
)

# §6. Destination classes the design must refuse. A missing one is a hole in the guard.
REQUIRED_BLOCKED = (
    "IPV4_LOOPBACK",
    "IPV4_PRIVATE",
    "IPV4_LINK_LOCAL",
    "IPV4_UNSPECIFIED",
    "IPV4_MULTICAST",
    "IPV6_LOOPBACK",
    "IPV6_UNSPECIFIED",
    "IPV6_LINK_LOCAL",
    "IPV6_UNIQUE_LOCAL",
    "IPV6_MULTICAST",
    "CLOUD_METADATA_ENDPOINTS",
    "LOCALHOST_NAMES",
    "INTERNAL_OR_SINGLE_LABEL_HOSTNAMES",
)

# §4. Capabilities that must be absent rather than merely switched off.
REQUIRED_PROHIBITED = (
    "authentication_bypass",
    "session_hijacking",
    "captcha_bypass",
    "anti_bot_circumvention",
    "rate_limit_circumvention",
    "vulnerability_probing",
    "directory_brute_forcing",
    "credential_testing",
    "hidden_endpoint_discovery",
    "parameter_fuzzing",
    "port_scanning",
    "non_http_service_probing",
    "retry_with_varied_identity_after_refusal",
)

# §25, §27, §46. Bounds a run may not be authorized without.
REQUIRED_BOUNDS = (
    "number_of_targets",
    "requests_per_target",
    "redirect_count",
    "retries",
    "global_concurrency",
    "per_host_concurrency",
    "per_origin_rate",
    "total_run_duration",
    "maximum_bytes",
)

REQUIRED_REQUEST_FIELDS = (
    "http_method",
    "scheme_policy",
    "port_policy",
    "host_header_rule",
    "sni_rule",
    "user_agent",
    "accept",
    "accept_language",
    "accept_encoding",
    "connection_behavior",
    "cookie_policy",
    "authentication_policy",
    "redirect_policy",
    "max_redirects",
    "body_handling",
    "response_byte_cap",
    "header_byte_cap",
    "connect_timeout",
    "read_timeout",
    "retry_policy",
    "dns_policy",
    "ip_version_policy",
    "cache_policy",
    "proxy_policy",
    "vantage_identity",
    "robots_policy",
    "javascript_execution",
)

HARD_ZERO = (
    "TARGET_HTTP_REQUESTS",
    "CRAWLS",
    "BROWSER_MEASUREMENT_RUNS",
    "CURL_TARGET_EXECUTIONS",
    "WGET_TARGET_EXECUTIONS",
    "COMMON_CRAWL_INDEX_QUERIES",
    "COMMON_CRAWL_DATA_DOWNLOADS",
    "HTTP_ARCHIVE_BIGQUERY_EXECUTIONS",
    "HAR_DOWNLOADS",
    "MEASUREMENT_API_EXECUTIONS",
    "TARGET_VALUE_EXPOSURES",
    "ACCOUNTS_CREATED",
    "TRIALS",
    "PURCHASES",
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
    "CRAWLERS_IMPLEMENTED",
    "CORPORA_CREATED",
    "RUNS_EXECUTED",
    "COUNTERPARTS_SELECTED",
    "CONSTRUCTS_SELECTED",
    "QUANTITY_CLASSES_SELECTED",
)

# The exemption for database row-count censuses, carried from Mission 1.70's §23 repair.
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


def _entries(block: dict):
    """A `$comment` is where a RULE is written; it is never a row (Mission 1.42, §23)."""
    return [(k, v) for k, v in block.items() if not k.startswith("$")]


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


def _false(record: dict, path: list[str], message: str) -> None:
    node = record
    for key in path:
        if not isinstance(node, dict) or key not in node:
            raise ValidationError(f"{'.'.join(path)} is not recorded, so {message} is unchecked")
        node = node[key]
    if node is not False:
        raise ValidationError(message)


def _true(record: dict, path: list[str], message: str) -> None:
    node = record
    for key in path:
        if not isinstance(node, dict) or key not in node:
            raise ValidationError(f"{'.'.join(path)} is not recorded, so {message} is unchecked")
        node = node[key]
    if node is not True:
        raise ValidationError(message)


def _check_preconditions(baseline: dict) -> None:
    """§0 and §1."""
    pre = baseline["repository_precondition"]
    _true(
        baseline,
        ["repository_precondition", "mission_1_70_merged"],
        "the baseline does not record Mission 1.70 as merged",
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

    if baseline["canonical_baseline"]["drift_from_mission_1_70"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["canonical_baseline"]["migration_head"] != "0035_refusal_provenance":
        raise ValidationError("the migration head moved")

    scope = baseline["scope"]
    if scope["in_scope"] != "SROS_BOUNDED_HTTP_FETCHER":
        raise ValidationError("the mission scope is not the operator apparatus")
    for flag in (
        "broad_apparatus_discovery_performed",
        "scanner_class_reopened",
        "common_crawl_http_archive_population_analysis_reopened",
        "construct_selected",
        "predicate_selected",
    ):
        _false(baseline, ["scope", flag], f"the scope records {flag}")

    budget = baseline["documentation_budget"]
    if budget["used"] > budget["maximum_first_party_requests"]:
        raise ValidationError("the documentation budget was exceeded")
    if budget["target_site_terms_inspected"] != 0:
        raise ValidationError("target-site terms were inspected, and no corpus exists")
    if budget["targets_browsed"] != 0:
        raise ValidationError("targets were browsed as future measurement subjects")


def _check_governance(governance: dict) -> None:
    """§3, §40, §50. Feasibility is never authorization."""
    _true(
        governance,
        ["run_authorization_required"],
        "a governance verdict was issued without requiring run authorization",
    )
    _false(governance, ["authorised_by_this_mission"], "this mission authorised the apparatus")
    _true(
        governance,
        ["this_is_not_a_run_authorization"],
        "the governance record does not deny being a run authorization",
    )
    _true(
        governance,
        ["this_is_not_legal_advice"],
        "the governance record does not deny being legal advice",
    )

    rubric = {row["dimension"]: row for row in governance["rubric"]}
    for dimension in RUBRIC_DIMENSIONS:
        if dimension not in rubric:
            raise ValidationError(f"the rubric does not evaluate {dimension}")
        row = rubric[dimension]
        if row["verdict"] not in RUBRIC_VERDICTS:
            raise ValidationError(f"{dimension} carries an undefined verdict")
        if not str(row["why"]).strip():
            raise ValidationError(f"{dimension} carries no reason")

    tally = {name: 0 for name in RUBRIC_VERDICTS}
    for row in governance["rubric"]:
        tally[row["verdict"]] += 1
    if tally != governance["rubric_tally"]:
        raise ValidationError("the recorded rubric tally does not match the rubric")
    _false(governance, ["numerical_score_issued"], "a numerical governance score was issued")

    # §50. No blanket authorization vocabulary.
    allowed_overall = {
        "GOVERNANCE_FEASIBLE_IN_PRINCIPLE",
        "GOVERNANCE_NOT_YET_FEASIBLE_IN_PRINCIPLE_NAMED_DECISIONS_REQUIRED",
        "TARGET_SPECIFIC_REVIEW_REQUIRED",
        "DEDICATED_POLICY_REQUIRED",
        "BLOCKED_BY_KNOWN_POLICY",
        "UNKNOWN",
    }
    if governance["overall"] not in allowed_overall:
        raise ValidationError(f"the governance verdict {governance['overall']!r} is not defined")
    for banned in ("LEGAL", "COMPLIANT", "PERMITTED_EVERYWHERE", "AUTHORIZED_TO_RUN"):
        if banned in governance["overall"]:
            raise ValidationError(f"the governance verdict claims {banned}")

    # A REQUIRES_DEDICATED_POLICY row must be matched by a named decision.
    outstanding = {d for d, row in rubric.items() if row["verdict"] == "REQUIRES_DEDICATED_POLICY"}
    if outstanding and not governance["named_policy_decisions_required"]:
        raise ValidationError("policies are outstanding and none is named")
    for decision in governance["named_policy_decisions_required"]:
        _false(decision, ["settled_here"], f"{decision['id']} is recorded as settled here")
    if governance["overall"] == "GOVERNANCE_FEASIBLE_IN_PRINCIPLE" and outstanding:
        raise ValidationError(
            "governance is called feasible in principle while dedicated policies are outstanding"
        )

    if (
        governance["blocked_by_an_existing_rule"] is True
        and not str(governance.get("which_rule", "")).strip()
    ):
        raise ValidationError("the architecture is called blocked with no rule named")
    for counter in ("sources_registered", "source_governance_mutated", "governance_approvals"):
        if governance[counter] != 0:
            raise ValidationError(f"{counter} is not zero")


def _check_apparatus(apparatus: dict) -> None:
    """§2, §4, §13, §21, §26, §35, §36."""
    if apparatus["status"] not in {"DESIGNED_NOT_ADOPTED", "ADOPTED"}:
        raise ValidationError("the apparatus contract status is undefined")
    _false(apparatus, ["implemented"], "the apparatus was implemented")
    _false(apparatus, ["adopted_into_governance"], "the apparatus was adopted into governance")
    _true(
        apparatus,
        ["run_authorization_required"],
        "the apparatus contract does not require run authorization",
    )

    measures = apparatus["what_it_measures"]
    for flag in (
        "predicate_selected",
        "the_apparatus_evaluates_no_predicate_itself",
        "response_header_chosen",
        "status_code_chosen",
        "html_token_chosen",
        "server_software_chosen",
        "technology_fingerprint_chosen",
    ):
        if flag == "the_apparatus_evaluates_no_predicate_itself":
            _true(measures, [flag], "the apparatus evaluates a predicate itself")
        else:
            _false(measures, [flag], f"the apparatus contract records {flag}")

    stages = apparatus["stages"]
    if stages["ordered"] != ["SCHEDULED", "ATTEMPTED", "RESPONSE_RECEIVED", "PREDICATE_EVALUABLE"]:
        raise ValidationError("the four stages are not as designed")
    _false(stages, ["attempted_equals_successful"], "attempted and successful were collapsed")
    _false(
        stages,
        ["response_absence_means_target_absent_from_population"],
        "a response absence was treated as absence from the population",
    )

    prohibited = apparatus["prohibited_capabilities"]
    for capability in REQUIRED_PROHIBITED:
        if capability not in prohibited:
            raise ValidationError(f"{capability} is not addressed by the apparatus contract")
        if prohibited[capability] is not False:
            raise ValidationError(f"{capability} is permitted")

    expansion = apparatus["crawl_expansion"]
    for flag in (
        "recursive_discovery",
        "links_in_responses_become_targets",
        "sitemap_expansion",
        "robots_discovered_expansion",
        "redirects_expand_the_corpus",
    ):
        _false(expansion, [flag], f"the apparatus permits {flag}")
    _true(
        expansion,
        ["the_measured_population_is_exactly_the_frozen_manifest"],
        "the measured population is not the frozen manifest",
    )

    javascript = apparatus["javascript"]
    _false(javascript, ["enabled_by_default"], "JavaScript is enabled by default")
    _false(
        javascript,
        ["required_by_the_default_architecture"],
        "the default architecture requires JavaScript",
    )
    if javascript["browser_rendered_mode"] != (
        "A_SEPARATE_APPARATUS_MODE_AND_A_SEPARATE_GOVERNANCE_REVIEW"
    ):
        raise ValidationError("a browser-rendered mode is not held separate")

    provenance = apparatus["operator_and_apparatus_are_separate_provenance"]
    _false(
        provenance,
        ["same_human_implies_same_apparatus"],
        "one operator is treated as one apparatus",
    )
    _false(
        provenance,
        ["different_process_implies_independent_apparatus"],
        "a different process is treated as an independent apparatus",
    )

    independence = apparatus["independence"]
    if independence["classification"] == "INDEPENDENT_EVIDENCE_GROUP_READY":
        raise ValidationError("an independent evidence group is declared ready")
    if independence["classification"] not in {
        "INDEPENDENCE_ARCHITECTURE_PLAUSIBLE",
        "INDEPENDENCE_ARCHITECTURE_UNRESOLVED",
        "INDEPENDENCE_ARCHITECTURE_REFUTED",
    }:
        raise ValidationError("the independence classification is undefined")
    _false(
        independence,
        ["self_operation_establishes_independence"],
        "self-operation was treated as establishing independence",
    )
    _false(
        independence,
        ["independent_evidence_group_ready"],
        "an independent evidence group is declared ready",
    )
    _false(
        independence,
        ["two_local_processes_are_two_independence_groups"],
        "two local processes were treated as two independence groups",
    )
    _true(
        independence,
        ["second_independent_route_still_required"],
        "the record does not require a second independent route",
    )
    if independence["independence_groups_created"] != 0:
        raise ValidationError("an independence group was created")

    reproducibility = apparatus["reproducibility"]
    _true(reproducibility, ["the_run_is_reconstructible"], "the run is not reconstructible")
    _false(
        reproducibility,
        ["the_observation_is_reproducible"],
        "the observation is claimed to be reproducible, which claims the web is static",
    )


def _check_network(network: dict) -> None:
    """§5, §6, §7."""
    _false(
        network, ["a_public_looking_url_is_assumed_safe"], "a public-looking URL is assumed safe"
    )
    _true(
        network,
        ["destination_check_required_before_every_connection"],
        "the destination check is not required before every connection",
    )

    blocked = {row["class"] for row in network["blocked_destination_classes"]}
    for required in REQUIRED_BLOCKED:
        if required not in blocked:
            raise ValidationError(f"{required} is not blocked")
    for row in network["blocked_destination_classes"]:
        if not str(row["authority"]).strip():
            raise ValidationError(f"{row['class']} names no authority")

    _false(
        network,
        ["numeric_ranges", "written_into_this_document"],
        "recalled numeric address ranges were written into the design",
    )

    schemes = network["schemes"]
    if set(schemes["allowed"]) != {"http", "https"}:
        raise ValidationError("the allowed scheme set is not exactly http and https")
    for refused in ("file", "ftp", "gopher", "data", "javascript"):
        if refused not in schemes["refused"]:
            raise ValidationError(f"the scheme {refused} is not refused")

    _true(
        network,
        ["redirects", "destination_revalidated_after_every_redirect"],
        "a redirect destination is not revalidated",
    )
    _false(
        network,
        ["redirects", "the_original_hostname_is_sufficient"],
        "the original hostname is treated as sufficient across redirects",
    )

    dns = network["dns_safety"]
    if dns["status"] != "DNS_SAFETY_REQUIRED":
        raise ValidationError("DNS safety is not required")
    for flag in (
        "resolution_timing_must_be_stated",
        "accepted_address_set_must_be_stated",
        "connection_pinned_to_a_validated_resolved_address",
        "redirects_trigger_re_resolution",
        "a_hostname_resolving_public_then_private_is_refused",
        "rebinding_addressed",
        "every_resolved_address_must_pass",
    ):
        _true(dns, [flag], f"DNS safety does not require {flag}")
    _false(
        dns,
        ["one_passing_address_is_enough"],
        "one passing address is treated as validating a host",
    )

    _false(network, ["implemented"], "the network safety contract was implemented")
    if network["requests_made"] != 0:
        raise ValidationError("the network safety design made requests")


def _check_accounting(terminals: dict, missingness: dict) -> None:
    """§12, §13, §14, §15, §43. The invariant this whole arc is for."""
    invariant = terminals["invariant"]
    if invariant["statement"] != "corpus_manifest_count == terminal_target_records_count":
        raise ValidationError("the accounting invariant is not stated")
    _true(
        invariant,
        ["exactly_one_terminal_per_target_per_run"],
        "more than one terminal per target per run is permitted",
    )
    _false(invariant, ["a_target_may_disappear_silently"], "a target may disappear silently")
    _false(
        invariant,
        ["retries_create_extra_population_members"],
        "retries create extra population members",
    )

    classes = {row["class"] for row in missingness["classes"]}
    if not classes:
        raise ValidationError("the missingness taxonomy is empty")

    rows = terminals["terminals"]
    if not rows:
        raise ValidationError("the terminal taxonomy is empty")
    seen = set()
    for row in rows:
        if row["terminal"] in seen:
            raise ValidationError(f"{row['terminal']} appears twice")
        seen.add(row["terminal"])
        if row["missingness_class"] not in classes:
            raise ValidationError(
                f"{row['terminal']} maps to {row['missingness_class']}, which is not a declared class"
            )
        if row["furthest_stage_certified"] not in terminals["stages"]:
            raise ValidationError(f"{row['terminal']} reaches an undeclared stage")
        if not str(row["why"]).strip():
            raise ValidationError(f"{row['terminal']} carries no reason")
    if terminals["terminal_count"] != len(rows):
        raise ValidationError("the recorded terminal count does not match the table")

    # A missingness class nothing can reach is a class that never fires.
    mapped = {row["missingness_class"] for row in rows}
    orphans = classes - mapped
    if orphans:
        raise ValidationError(f"missingness classes no terminal reaches: {sorted(orphans)}")

    # An OBSERVATION_AVAILABLE terminal that never received a response is incoherent.
    for row in rows:
        if row["missingness_class"] == "OBSERVATION_AVAILABLE" and (
            row["furthest_stage_certified"] != "RESPONSE_RECEIVED"
        ):
            raise ValidationError(
                f"{row['terminal']} claims an available observation without a received response"
            )
        if row["furthest_stage_certified"] == "SCHEDULED":
            attempted = {c["class"]: c["counts_as_attempted"] for c in missingness["classes"]}
            if attempted[row["missingness_class"]] is True:
                raise ValidationError(
                    f"{row['terminal']} never left SCHEDULED and its class counts as attempted"
                )

    # §13 and the correction that keeps the taxonomy honest.
    if "PREDICATE_EVALUABLE" in terminals["stages"]:
        raise ValidationError(
            "PREDICATE_EVALUABLE is listed as an apparatus stage, and the apparatus cannot "
            "certify evaluability against a predicate that does not exist"
        )
    if terminals["predicate_evaluable_is_not_an_apparatus_stage"]["determined_by"] != (
        "THE_CONSTRUCT, over the apparatus's records"
    ):
        raise ValidationError("predicate evaluability is not deferred to the construct")

    denominator = missingness["denominator_integrity"]
    for counter in ("N_population", "A_attempted", "R_response_observed"):
        _true(
            denominator,
            [counter, "computable_by_the_apparatus"],
            f"{counter} is not computable by the apparatus",
        )
    for counter in ("E_predicate_evaluable", "P_positive"):
        _false(
            denominator,
            [counter, "computable_by_the_apparatus"],
            f"{counter} is claimed computable without a construct",
        )
    if denominator["which_classes_enter_the_denominator"] != "NOT_CHOSEN_BY_THIS_MISSION":
        raise ValidationError("this mission chose the denominator, which belongs to a construct")

    forbidden = missingness["forbidden_readings"]
    for flag in (
        "response_absence_means_target_absent_from_population",
        "attempted_and_successful_are_the_same_set",
        "missingness_may_be_dropped_from_the_record",
        "only_positive_observations_are_stored",
        "only_responses_are_stored",
    ):
        _false(forbidden, [flag], f"the missingness contract permits: {flag}")


def _check_corpus(corpus: dict) -> None:
    """§8, §9, §10, §11."""
    if corpus["corpus_created"] is not False or corpus["targets_in_any_corpus"] != 0:
        raise ValidationError("a corpus was created")
    required = {row["field"] for row in corpus["fields"] if row["required"]}
    for field in (
        "corpus_manifest_id",
        "corpus_version",
        "created_at",
        "provenance",
        "canonical_target_identifier",
        "requested_url_verbatim",
        "entity_id",
        "inclusion_basis",
    ):
        if field not in required:
            raise ValidationError(f"the corpus manifest does not require {field}")

    _true(
        corpus,
        ["hashing", "required_before_a_run_may_reference_it"],
        "a run may reference an unhashed manifest",
    )
    immutability = corpus["immutability"]
    _true(immutability, ["immutable_once_referenced_by_a_run"], "the manifest is mutable in a run")
    _false(
        immutability,
        ["membership_may_change_after_execution_begins"],
        "corpus membership may change after execution begins",
    )
    _false(
        immutability,
        ["the_old_manifest_may_be_mutated_under_the_same_run_identity"],
        "a manifest may be mutated under an unchanged run identity",
    )

    rules = corpus["canonical_url_rules"]
    for aspect in (
        "scheme",
        "host_case",
        "idn_punycode",
        "default_ports",
        "path_normalization",
        "trailing_slash",
        "fragment",
        "query_string",
        "duplicate_urls",
    ):
        if not str(rules[aspect]).strip():
            raise ValidationError(f"the canonical URL rules do not address {aspect}")
    _false(
        rules,
        ["http_and_https_are_the_same_entity"],
        "http and https were declared the same entity, which decides a construct",
    )

    query = corpus["query_string_policy"]
    if query["status"] != "QUERY_STRING_POLICY_REQUIRED":
        raise ValidationError("the query-string policy is not required")
    _false(query, ["settled_by_this_mission"], "the query-string policy was settled here")
    _false(query, ["silently_stripped"], "query strings are silently stripped")
    _false(query, ["preference_is_a_decision"], "a stated preference was recorded as a decision")


def _check_run(run: dict) -> None:
    """§16, §18, §22, §31, §32, §33, §34, §41, §42."""
    if run["runs_executed"] != 0:
        raise ValidationError("a run was executed")
    required = {row["field"] for row in run["fields"] if row["required"]}
    for field in (
        "run_id",
        "apparatus_contract_id",
        "apparatus_contract_sha256",
        "corpus_manifest_id",
        "corpus_manifest_sha256",
        "request_contract_id",
        "request_contract_sha256",
        "software_version",
        "git_commit",
        "dependency_lock_state",
        "runtime_version",
        "configuration_hash",
        "vantage_id",
        "operator_authorization_reference",
        "run_status",
    ):
        if field not in required:
            raise ValidationError(f"a run does not require {field}")
    for digest in (
        "apparatus_contract_sha256",
        "corpus_manifest_sha256",
        "request_contract_sha256",
    ):
        if digest not in run["three_hashes_are_mandatory"]:
            raise ValidationError(f"{digest} is not mandatory")
    _false(
        run,
        ["containerization", "containerization_is_required_for_provenance"],
        "containerization is required merely for provenance",
    )

    abort = run["abortability"]
    for flag in (
        "immediate_safe_stop_supported",
        "no_new_attempts_after_abort",
        "the_accounting_invariant_survives_an_abort",
    ):
        _true(abort, [flag], f"abort does not guarantee {flag}")
    _false(abort, ["targets_may_disappear_on_abort"], "targets may disappear on abort")
    if abort["remaining_items_become"] != "RUN_ABORTED_BEFORE_ATTEMPT":
        raise ValidationError("aborted items do not take a terminal state")

    resume = run["resumability"]
    _false(
        resume,
        ["an_interrupted_run_resumes_automatically"],
        "an interrupted run resumes automatically",
    )
    _false(
        resume,
        ["run_identity_is_preserved_across_a_resume"],
        "run identity is preserved across a resume, presenting two windows as one",
    )
    if not str(resume["rule"]).strip():
        raise ValidationError("resumability states no rule")

    time = run["time_semantics"]
    for stamp in ("attempt_started_at", "attempt_finished_at"):
        if stamp not in time["per_attempt_timestamps"]:
            raise ValidationError(f"{stamp} is not recorded per attempt")
    if time["timezone"] != "UTC":
        raise ValidationError("timestamps are not UTC")
    _false(
        time, ["unlabeled_local_timestamps_permitted"], "unlabeled local timestamps are permitted"
    )
    if time["which_time_is_load_bearing"] != "CHOSEN_BY_THE_CONSTRUCT_NOT_BY_THE_APPARATUS":
        raise ValidationError("the apparatus chose which time is load-bearing")

    retry = run["retry_semantics"]
    _true(retry, ["retries_governed"], "retries are ungoverned")
    _false(
        retry, ["attempt_1_may_be_overwritten_by_attempt_2"], "a retry overwrites a prior attempt"
    )
    _true(retry, ["all_attempts_are_retained"], "attempts are not retained individually")
    if retry["which_attempt_defines_the_observation"] != (
        "CHOSEN_BY_THE_CONSTRUCT_NOT_BY_THE_APPARATUS"
    ):
        raise ValidationError("the apparatus chose which attempt defines the observation")

    vantage = run["vantage"]
    _true(vantage, ["vantage_id_required"], "no vantage id is required")
    _false(
        vantage,
        ["sensitive_local_network_detail_published"],
        "sensitive local network detail is published",
    )
    _true(
        vantage,
        ["a_different_machine_or_network_is_a_distinct_vantage"],
        "a different machine is not a distinct vantage",
    )


def _check_request(request: dict) -> None:
    """§19, §20, §22, §27, §30."""
    fields = {row["field"]: row for row in request["fields"]}
    for field in REQUIRED_REQUEST_FIELDS:
        if field not in fields:
            raise ValidationError(f"the request contract does not carry {field}")
        if fields[field]["required_before_run"] is not True:
            raise ValidationError(f"{field} is not required before a run")
    if fields["authentication_policy"]["value_fixed_by_this_contract"] != "NONE":
        raise ValidationError("authentication is not fixed to NONE")
    if fields["cookie_policy"]["value_fixed_by_this_contract"] != "NO_COOKIES":
        raise ValidationError("cookies are not fixed to NO_COOKIES")
    if fields["scheme_policy"]["value_fixed_by_this_contract"] != "HTTP_OR_HTTPS_ONLY":
        raise ValidationError("the scheme policy is not fixed to http and https")
    if fields["javascript_execution"]["value_fixed_by_this_contract"] != "DISABLED":
        raise ValidationError("JavaScript execution is not fixed to DISABLED")
    _false(
        request, ["unbounded_is_representable"], "an unbounded request contract is representable"
    )
    _true(
        request,
        ["every_field_is_required_before_a_run"],
        "some request-contract field is optional before a run",
    )
    _false(
        request,
        ["default_minimality", "get_versus_head_frozen_here"],
        "GET versus HEAD was frozen here, which belongs to the construct",
    )

    headers = request["header_handling"]
    _true(headers, ["raw_header_structure_preserved"], "raw header structure is not preserved")
    for flag in (
        "duplicate_headers_collapsed",
        "header_order_discarded",
        "raw_values_normalized_away",
        "response_hop_identity_discarded",
    ):
        _false(headers, [flag], f"header handling permits {flag}")

    redirects = request["redirects"]
    _false(
        redirects,
        ["a_redirect_may_silently_change_the_measured_entity"],
        "a redirect may silently change the measured entity",
    )
    if redirects["which_response_the_predicate_applies_to"] != (
        "CHOSEN_BY_THE_CONSTRUCT_NOT_BY_THE_APPARATUS"
    ):
        raise ValidationError("the apparatus chose which response the predicate applies to")
    for field in (
        "source_url",
        "status",
        "location_target",
        "resolved_destination_safety_decision",
        "timestamp",
    ):
        if field not in redirects["per_hop_record_fields"]:
            raise ValidationError(f"a redirect hop does not record {field}")


def _check_minimization(minimization: dict) -> None:
    """§28, §29."""
    retention = minimization["permitted_retention"]
    if retention["status"] != "BODY_CAPTURE_POLICY_REQUIRED_BEFORE_RUN":
        raise ValidationError("body capture policy is not required before a run")
    _false(retention, ["settled_by_this_mission"], "the body capture policy was settled here")
    _false(
        retention,
        ["arbitrary_full_body_retention_assumed"],
        "arbitrary full body retention is assumed",
    )

    sensitive = minimization["sensitive_content"]
    _true(
        sensitive,
        ["a_public_page_may_return_personal_or_sensitive_data"],
        "the design denies that a public page may return sensitive data",
    )
    for flag in (
        "redaction_hooks_required_before_body_retention",
        "retention_hooks_required_before_body_retention",
    ):
        _true(sensitive, [flag], f"body retention does not require {flag}")
    if sensitive["content_retrieved_in_this_mission"] != 0:
        raise ValidationError("content was retrieved")

    if not str(
        minimization["why_this_is_not_a_side_policy"]["and_the_bound_on_that_claim"]
    ).strip():
        raise ValidationError("the retention-regime claim carries no stated bound")


def _check_counterpart(counterpart: dict) -> None:
    """§37, §38, §39."""
    _false(counterpart, ["counterpart_selected"], "a counterpart was selected")
    _false(counterpart, ["counterpart_ranked"], "a counterpart was ranked")
    if counterpart["counterpart_candidates_evaluated"] != 0:
        raise ValidationError("counterpart candidates were evaluated, which is a later mission")
    if len(counterpart["requirements"]) != counterpart["requirement_count"]:
        raise ValidationError("the counterpart requirement count does not match the list")
    for requirement in counterpart["requirements"]:
        if not str(requirement["why"]).strip():
            raise ValidationError(f"{requirement['id']} carries no reason")

    held = counterpart["held_state_not_reopened"]
    for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
        _true(
            held,
            [route, "independently_produces_http_observations"],
            f"{route} is no longer recorded as producing its own observations",
        )
        if held[route]["population_and_attempt_semantics"] != "INSUFFICIENT_UNDER_CURRENT_EVIDENCE":
            raise ValidationError(f"{route}'s Mission 1.70 state was rewritten")
        _false(held, [route, "state_changed_this_mission"], f"{route}'s state changed this mission")
    _false(
        held,
        ["the_operator_fetcher_repairs_their_records_retroactively"],
        "the operator fetcher is claimed to repair external records retroactively",
    )
    _true(
        counterpart,
        ["second_independent_route_still_required"],
        "the record does not require a second independent route",
    )
    if counterpart["independence_groups_created"] != 0:
        raise ValidationError("an independence group was created")


def _check_pilot(pilot: dict) -> None:
    """§25, §27, §45, §46."""
    dimensions = {row["dimension"]: row for row in pilot["dimensions_that_must_be_bounded"]}
    for dimension in REQUIRED_BOUNDS:
        if dimension not in dimensions:
            raise ValidationError(f"{dimension} is not required to be bounded")
        if dimensions[dimension]["bounded_required"] is not True:
            raise ValidationError(f"{dimension} may be unbounded")
    _false(pilot, ["unbounded_permitted_on_any_dimension"], "some dimension may be unbounded")
    _false(pilot, ["pilot_size_selected"], "a pilot size was selected")
    if not str(pilot["why_no_size_was_selected"]).strip():
        raise ValidationError("no reason is given for declining a pilot size")

    local = pilot["local_first_constraint"]
    _false(local, ["distributed_infrastructure_required"], "distributed infrastructure is required")
    for waiver in (
        "local_first_waives_rate_limits",
        "local_first_waives_target_policies",
        "local_first_waives_security_controls",
        "local_first_waives_commercial_purpose_rights",
    ):
        _false(local, [waiver], f"local-first is treated as waiving something: {waiver}")

    if pilot["classification"] not in {
        "BOUNDED_PILOT_FEASIBLE_IN_PRINCIPLE",
        "BOUNDED_PILOT_DIMENSIONS_CLOSED_GOVERNANCE_PENDING",
        "BOUNDED_PILOT_NOT_FEASIBLE",
    }:
        raise ValidationError("the pilot classification is undefined")


def _check_candidate_rule(candidate: dict, baseline: dict) -> None:
    """§49. Designing around a failure mode is not observing it twice."""
    requirements = _load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
    if len(requirements) != 15:
        raise ValidationError(f"the registry holds {len(requirements)} requirements, not 15")
    if candidate["registry_count_before"] != 15 or candidate["registry_count_after"] != 15:
        raise ValidationError("the candidate review disagrees with the registry count")
    if baseline["requirement_registry"]["count_before"] != len(requirements):
        raise ValidationError("the baseline and the registry disagree")
    _false(candidate, ["registry_growth_forced"], "registry growth was forced")
    _false(candidate, ["added_because_it_is_useful"], "the rule was added because it is useful")

    names = {row["name"] for row in requirements}
    if candidate["decision"] == "NOT_ADDED" and candidate["candidate"]["name"] in names:
        raise ValidationError("a rule recorded as NOT added is in the registry")
    if candidate["decision"] == "ADDED":
        if candidate["registry_count_after"] != candidate["registry_count_before"] + 1:
            raise ValidationError("a rule was added and the count did not move")
        if not candidate["second_instance_in_a_different_shape"]:
            raise ValidationError("a rule was added without a second instance in a different shape")

    counted = [i for i in candidate["instances_considered"] if i["counts_as_a_distinct_instance"]]
    if len(counted) != candidate["distinct_instances_found"]:
        raise ValidationError("the counted instances do not match the recorded number")
    for instance in candidate["instances_considered"]:
        if (
            not instance["counts_as_a_distinct_instance"]
            and not str(instance.get("why_it_does_not_count", "")).strip()
        ):
            raise ValidationError(f"{instance['instance']} is excluded with no reason")
    # The apparatus we designed may never be counted as an instance.
    for instance in candidate["instances_considered"]:
        if "SROS" in instance["instance"] and instance["counts_as_a_distinct_instance"]:
            raise ValidationError(
                "the apparatus designed in this mission was counted as a failure instance, "
                "and designing around a failure mode is not observing one"
            )


def _check_no_execution(records: list[dict]) -> None:
    """§52, §53, §54, and the standing reliability rule."""
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

    # Mission 1.70's own records stay as they were written.
    decision = _load(DECISION_V2)
    if decision["selected_quantity_class"] is not None:
        raise ValidationError("Mission 1.70's decision record now selects a class")
    if decision["primary_outcome"] != "FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE":
        raise ValidationError("Mission 1.70's decision record was edited")
    fetcher = _load(FETCHER_1_70)
    if fetcher["implemented"] is not False or fetcher["crawled"] is not False:
        raise ValidationError("Mission 1.70's fetcher record was edited")

    _check_the_current_class_selection_is_consistent(SELECTED_CLASS)
    if SELECTED_CONSTRUCT.exists():
        raise ValidationError("selected-construct-v1.json exists and no construct was selected")


def validate() -> list[dict]:
    records = [_load(path) for path in ORDER]
    (
        baseline,
        governance,
        apparatus,
        request,
        corpus,
        run,
        terminals,
        missingness,
        network,
        minimization,
        counterpart,
        pilot,
        candidate,
    ) = records

    _check_preconditions(baseline)
    _check_governance(governance)
    _check_apparatus(apparatus)
    _check_network(network)
    _check_accounting(terminals, missingness)
    _check_corpus(corpus)
    _check_run(run)
    _check_request(request)
    _check_minimization(minimization)
    _check_counterpart(counterpart)
    _check_pilot(pilot)
    _check_candidate_rule(candidate, baseline)
    _check_no_execution(records)

    parallel = baseline["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    if parallel["netlas_contact"] != "STILL_PENDING":
        raise ValidationError("the Netlas contact state moved")
    if parallel["scanner_arc_status"] != "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE":
        raise ValidationError("the scanner arc status changed")
    if parallel["q1_status"] != "PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED":
        raise ValidationError("the Q1 status changed")

    return records


# ------------------------------------------------------------------------ renderers


def render_apparatus(governance: dict) -> str:
    apparatus = _load(APPARATUS)
    pilot = _load(PILOT)
    counterpart = _load(COUNTERPART)
    candidate = _load(CANDIDATE)

    lines = [
        "# Mission 1.71 — A bounded HTTP apparatus, designed and not authorised",
        "",
        "Generated from `bounded-http-governance-feasibility-v1.json` and the contract records.",
        "Do not edit by hand.",
        "",
        f"**Governance: `{governance['overall']}`.**",
        f"**Run authorization required: {governance['run_authorization_required']}. "
        f"Authorised by this mission: {governance['authorised_by_this_mission']}.**",
        "",
        "## The governance rubric",
        "",
        "| dimension | verdict |",
        "|---|---|",
    ]
    for row in governance["rubric"]:
        lines.append(f"| {row['dimension']} | `{row['verdict']}` |")
    tally = governance["rubric_tally"]
    lines += [
        "",
        f"**{tally['PASS_IN_PRINCIPLE']} pass in principle, "
        f"{tally['REQUIRES_DEDICATED_POLICY']} require a dedicated policy, "
        f"{tally['BLOCKED']} blocked, {tally['UNKNOWN']} unknown.** No numerical score.",
        "",
        "Why, for each:",
        "",
    ]
    for row in governance["rubric"]:
        lines.append(f"- **{row['dimension']}** — {row['why']}")

    dominant = governance["the_dominant_finding"]
    lines += [
        "",
        "## The dominant finding is not any single row",
        "",
        dominant["consequence_if_routed_through_the_existing_gate"],
        "",
        "The rules that produce it:",
        "",
    ]
    for rule in dominant["what_the_rules_say_about_an_arbitrary_public_target"]:
        lines.append(f"- {rule}")
    lines += [
        "",
        f"**And the collapse that would follow.** {dominant['the_collapse_that_would_follow']}",
        "",
        "### The mechanism is not novel, and here is the evidence",
        "",
        dominant["the_mechanism_is_not_novel_and_here_is_the_evidence"]["claim"],
        "",
        "*And the distinction that survives it:* "
        + dominant["the_mechanism_is_not_novel_and_here_is_the_evidence"][
            "and_the_distinction_that_survives_it"
        ],
        "",
        "## The named decisions",
        "",
        "| id | decision | settled here |",
        "|---|---|---|",
    ]
    for decision in governance["named_policy_decisions_required"]:
        lines.append(f"| {decision['id']} | {decision['decision']} | {decision['settled_here']} |")

    lines += [
        "",
        "## What the apparatus is, and is not",
        "",
        "| | |",
        "|---|---|",
        f"| status | `{apparatus['status']}` |",
        f"| implemented | {apparatus['implemented']} |",
        f"| adopted into governance | {apparatus['adopted_into_governance']} |",
        f"| predicate selected | {apparatus['what_it_measures']['predicate_selected']} |",
        f"| independence | `{apparatus['independence']['classification']}` |",
        f"| self-operation establishes independence | "
        f"{apparatus['independence']['self_operation_establishes_independence']} |",
        f"| independence groups created | "
        f"{apparatus['independence']['independence_groups_created']} |",
        f"| second independent route still required | "
        f"{apparatus['independence']['second_independent_route_still_required']} |",
        "",
        f"*Two local processes are two independence groups:* "
        f"**{apparatus['independence']['two_local_processes_are_two_independence_groups']}**. "
        f"{apparatus['independence']['why_not']}",
        "",
        "## The bounded pilot",
        "",
        f"**`{pilot['classification']}`.** {pilot['why_not_feasible_in_principle']}",
        "",
        "| dimension | must be bounded | value chosen |",
        "|---|---|---|",
    ]
    for row in pilot["dimensions_that_must_be_bounded"]:
        lines.append(f"| {row['dimension']} | {row['bounded_required']} | {row['value_chosen']} |")

    lines += [
        "",
        "## What a counterpart would have to be",
        "",
        "| id | requirement |",
        "|---|---|",
    ]
    for requirement in counterpart["requirements"]:
        lines.append(f"| {requirement['id']} | {requirement['requirement']} |")
    lines += [
        "",
        f"**Counterpart selected: {counterpart['counterpart_selected']}. "
        f"Candidates evaluated: {counterpart['counterpart_candidates_evaluated']}.**",
        "",
        "## The candidate registry rule",
        "",
        f"`{candidate['candidate']['name']}` — **{candidate['decision']}**, registry "
        f"{candidate['registry_count_before']} to {candidate['registry_count_after']}.",
        "",
        candidate["why_usefulness_is_not_the_standard"],
        "",
    ]
    return "\n".join(lines)


def render_accounting(terminals: dict) -> str:
    missingness = _load(MISSINGNESS)
    attempted = {row["class"]: row["counts_as_attempted"] for row in missingness["classes"]}

    lines = [
        "# Mission 1.71 — The accounting model",
        "",
        "Generated from `bounded-http-terminal-outcome-taxonomy-v1.json` and the missingness",
        "contract. Do not edit by hand.",
        "",
        f"**`{terminals['invariant']['statement']}`**",
        "",
        "Exactly one terminal record per manifest item per governed run. No item disappears,",
        "and a retry is a child attempt rather than a new population member.",
        "",
        "## Terminal outcomes",
        "",
        "| terminal | furthest stage certified | missingness class | attempted |",
        "|---|---|---|---|",
    ]
    for row in terminals["terminals"]:
        lines.append(
            f"| `{row['terminal']}` | {row['furthest_stage_certified']} "
            f"| `{row['missingness_class']}` | {attempted[row['missingness_class']]} |"
        )

    lines += [
        "",
        f"**{terminals['terminal_count']} terminals over "
        f"{missingness['class_count']} missingness classes.** Every terminal maps to exactly one",
        "class, and no class is unreachable.",
        "",
        "Why, for each:",
        "",
    ]
    for row in terminals["terminals"]:
        lines.append(f"- **{row['terminal']}** — {row['why']}")

    deferred = terminals["predicate_evaluable_is_not_an_apparatus_stage"]
    lines += [
        "",
        "## What the apparatus cannot certify",
        "",
        deferred["why"],
        "",
        f"Determined by: **{deferred['determined_by']}**.",
        "",
        "## Missingness classes",
        "",
        "| class | means | counts as attempted |",
        "|---|---|---|",
    ]
    for row in missingness["classes"]:
        lines.append(f"| `{row['class']}` | {row['means']} | {row['counts_as_attempted']} |")

    added = missingness["added_beyond_the_brief_minimum"]
    lines += [
        "",
        f"**One class was added beyond the required minimum: `{added['class']}`.** {added['why']}",
        "",
        "## Denominators a later construct can state",
        "",
        "| counter | definition | computable by the apparatus |",
        "|---|---|---|",
    ]
    denominator = missingness["denominator_integrity"]
    for counter in (
        "N_population",
        "A_attempted",
        "R_response_observed",
        "E_predicate_evaluable",
        "P_positive",
    ):
        row = denominator[counter]
        lines.append(f"| {counter} | {row['definition']} | {row['computable_by_the_apparatus']} |")
    lines += [
        "",
        f"Which classes enter the denominator: **{denominator['which_classes_enter_the_denominator']}**. "
        f"{denominator['why_not_chosen']}",
        "",
        "## Why this is the whole point",
        "",
        missingness["why_this_is_the_whole_point"],
        "",
    ]
    return "\n".join(lines)


RENDERERS = {GOVERNANCE: render_apparatus, TERMINALS: render_accounting}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  bounded HTTP apparatus: {error}")
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
        print(f"ok       {len(rendered)} bounded-HTTP documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    governance = by_path[GOVERNANCE]
    print(f"governance {governance['overall']}")
    print(f"authorised {governance['authorised_by_this_mission']}")
    print(f"terminals  {by_path[TERMINALS]['terminal_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
