"""Render and validate the Mission 1.69 quantity-class selection.

Thirteen records, and one discipline underneath all of them:

    TWO PUBLISHERS OF A NUMBER ARE NOT TWO WITNESSES TO IT. ONLY TWO PRODUCERS
    ARE.

`validate()` enforces the readings this mission was most tempted to make and did
not:

  - the scanner arc is PARKED, never refuted, because Mission 1.68 explicitly
    declined the stronger claim and this mission may not make it on its behalf;
  - an aggregator, a mirror and a publisher of somebody's submitted document are
    not independent producers, however different their organisations;
  - downloads and stars, views and searches, questions and pageviews are
    complementary and are not two witnesses to one proposition;
  - GitHub and GitLab are different populations, not two routes;
  - a shared domain list does not make a shared measurement, because the request
    is part of the predicate;
  - a provider-defined population is not an externally frozen one;
  - and a class failing the independence experiment is still useful to the
    Opportunity Engine, which is a different question and is recorded apart.

    uv run python infrastructure/scripts/render_quantity_class_selection.py
    uv run python infrastructure/scripts/render_quantity_class_selection.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.69-baseline-v1.json"
UNIVERSE = DATA / "quantity-class-universe-v1.json"
MATRIX = DATA / "quantity-class-route-matrix-v1.json"
LINEAGE = DATA / "independent-measurement-lineage-review-v1.json"
FIXED_CORPUS = DATA / "fixed-corpus-http-class-review-v1.json"
COMPARISON = DATA / "quantity-class-comparison-v1.json"
RULE_REVIEW = DATA / "mission-1-68-candidate-rule-review-v1.json"
DECISION = DATA / "quantity-class-selection-decision-v1.json"
SELECTED = DATA / "selected-quantity-class-v1.json"

CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
CONSTRUCT_DECISION = DATA / "construct-selection-decision-v1.json"

CLASS_IDS = ("Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")
PACKAGES = tuple(DATA / f"quantity-class-package-{cid.lower()}-v1.json" for cid in CLASS_IDS)

ORDER = [
    BASELINE,
    UNIVERSE,
    MATRIX,
    LINEAGE,
    FIXED_CORPUS,
    COMPARISON,
    RULE_REVIEW,
    DECISION,
    *PACKAGES,
]

RENDERED = {
    DECISION: DATA / "mission-1.69-quantity-class-selection-v1.md",
    FIXED_CORPUS: DATA / "fixed-corpus-http-class-review-v1.md",
}

PRODUCTION_VOCABULARY = frozenset(
    {
        "OWN_MEASUREMENT",
        "MIRROR",
        "AGGREGATOR",
        "SHARED_UPSTREAM",
        "PUBLISHER_OF_SUBMITTED_DOCUMENTS",
        "UNKNOWN",
    }
)

# Only a producer witnesses. Everything else reads somebody's published number, which is
# READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT in the registry already.
PRODUCER_KINDS = frozenset({"OWN_MEASUREMENT"})

CLASS_VERDICTS = frozenset(
    {
        "STRATEGICALLY_VIABLE",
        "PROMISING_REQUIRES_ROUTE_QUALIFICATION",
        "COMPLEMENTARY_ONLY",
        "NOT_VIABLE_FOR_INDEPENDENCE_EXPERIMENT",
        "UNRESOLVED",
    }
)

RELEVANCE_ORDER = {"NON_PRODUCT": 0, "WEAK": 1, "MODERATE": 2, "STRONG": 3}

POPULATION_VOCABULARY = frozenset(
    {"POPULATION_EXTERNALLY_FREEZABLE", "PROVIDER_DEFINED_POPULATION", "PARTIAL", "UNKNOWN"}
)

SAME_PROPOSITION_VOCABULARY = frozenset(
    {"ESTABLISHED", "PLAUSIBLE_BUT_NOT_ESTABLISHED", "NOT_ESTABLISHED", "NOT_AVAILABLE"}
)

HARD_ZERO_COUNTERS = (
    "MEASUREMENT_API_EXECUTIONS",
    "DATASET_DOWNLOADS",
    "BIGQUERY_EXECUTIONS",
    "CRAWLS",
    "HTTP_MEASUREMENT_REQUESTS",
    "PACKAGE_COUNT_QUERIES",
    "REPOSITORY_EVENT_QUERIES",
    "PUBLICATION_COUNT_QUERIES",
    "PROCUREMENT_VALUE_QUERIES",
    "SEARCH_TREND_QUERIES",
    "DNS_MEASUREMENT_QUERIES",
    "COUNT_ENDPOINT_EXECUTIONS",
    "VALUES_RETRIEVED",
    "TRIALS",
    "PURCHASES",
    "ACCOUNTS_CREATED",
    "CREDENTIAL_READS",
    "MAILBOX_SEARCHES",
    "ENQUIRIES_SENT",
    "SOURCES_REGISTERED",
    "GOVERNANCE_REVIEWS",
    "GOVERNANCE_MUTATIONS",
    "SOURCE_REVIEWS_MUTATED",
    "THRESHOLDS_REGISTERED",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "RELIABILITY_ASSESSMENTS_CREATED",
    "RELIABILITY_VALUES_ASSIGNED",
    "SCORES",
    "OPPORTUNITY_MUTATIONS",
    "MODEL_CALLS",
    "EMBEDDINGS",
    "MIGRATIONS",
    "CONSTRUCTS_FROZEN",
    "PAIRS_SELECTED",
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


def _check_scanner_arc(baseline: dict) -> None:
    """§1. Mission 1.68 refused the stronger claim; this mission may not make it for it."""
    arc = baseline["scanner_arc_preserved"]
    if arc["scanner_class_result"] != "NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED":
        raise ValidationError("the scanner class result was rewritten")
    if arc["status"] != "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE":
        raise ValidationError(f"the scanner arc status reads {arc['status']!r}")
    for forbidden in ("SCANNERS_CANNOT_WORK", "SCANNER_CLASS_IMPOSSIBLE", "SCANNER_CLASS_INVALID"):
        if arc["scanner_class_result"] == forbidden:
            raise ValidationError(f"the scanner arc was rewritten as {forbidden}")
        if forbidden not in arc["result_is_not"]:
            raise ValidationError(f"the record no longer refuses the label {forbidden}")
    if not arc["reopening_conditions"]:
        raise ValidationError("the scanner arc is parked with no reopening condition")
    if arc["historical_missions_rewritten"] != 0:
        raise ValidationError("a historical mission was rewritten")

    # The construct decision Mission 1.68 wrote stays as it wrote it.
    previous = _load(CONSTRUCT_DECISION)
    if previous["primary_outcome"] != "NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED":
        raise ValidationError("Mission 1.68's decision record was edited")
    if previous["selected_construct"] is not None:
        raise ValidationError("Mission 1.68's decision record now selects a construct")


def _check_registry(baseline: dict, rule_review: dict) -> None:
    """§40. The registry grows only on a second instance in a different shape."""
    requirements = _load(CONTRACT)["requirement_registry"]["requirements"]
    if len(requirements) != 15:
        raise ValidationError(f"the registry holds {len(requirements)} requirements, not 15")
    if baseline["requirement_registry"]["count_after"] != 15:
        raise ValidationError("the baseline records a registry count other than 15")
    if baseline["requirement_registry"]["requirement_added_this_mission"] is not None:
        raise ValidationError("the baseline records a requirement added this mission")

    decision = rule_review["decision"]
    if decision not in {"ADOPT", "DO_NOT_ADOPT"}:
        raise ValidationError(f"the candidate-rule decision reads {decision!r}")
    names = {item["name"] for item in requirements}
    if decision == "DO_NOT_ADOPT":
        if rule_review["candidate_requirement"]["name"] in names:
            raise ValidationError("a rule recorded as NOT adopted is in the registry")
        if rule_review["registry_count_after"] != 15:
            raise ValidationError("DO_NOT_ADOPT recorded with a registry other than 15")
        if not rule_review["candidate_second_instances_examined"]:
            raise ValidationError("a rule was declined without examining any second instance")
        if any(
            c["verdict"] == "SECOND_INSTANCE"
            for c in rule_review["candidate_second_instances_examined"]
        ):
            raise ValidationError(
                "a second instance was established and the rule was declined anyway"
            )
    else:
        if rule_review["candidate_requirement"]["name"] not in names:
            raise ValidationError("a rule recorded as ADOPTED is absent from the registry")
        if rule_review["registry_count_after"] != 16:
            raise ValidationError("ADOPT recorded without incrementing the registry")
    if rule_review["registry_growth_forced"] is not False:
        raise ValidationError("registry growth was forced")


def _check_package(package: dict) -> None:
    """§20, §22, §23, §26 and §33 for one class package."""
    cid = package["class_id"]

    relevance = package["product_relevance"]
    if relevance not in RELEVANCE_ORDER:
        raise ValidationError(f"{cid} carries an unknown relevance {relevance!r}")
    if relevance == "NON_PRODUCT":
        raise ValidationError(f"{cid} is NON_PRODUCT and was not rejected")
    if not str(package.get("product_relevance_reason", "")).strip():
        raise ValidationError(f"{cid} states no product-relevance reason")

    # §23. A class with no identifiable world-state unit is rejected.
    if not str(package.get("exact_world_state_unit", "")).strip():
        raise ValidationError(f"{cid} identifies no world-state unit")

    if package["population_externally_freezable"] not in POPULATION_VOCABULARY:
        raise ValidationError(f"{cid} carries an unknown population classification")
    if package["same_proposition"] not in SAME_PROPOSITION_VOCABULARY:
        raise ValidationError(f"{cid} carries an unknown same-proposition state")

    routes = package["routes"]
    if len(routes) < 2:
        raise ValidationError(f"{cid} records fewer than two routes")
    for r in routes:
        if r["production"] not in PRODUCTION_VOCABULARY:
            raise ValidationError(f"{cid}/{r['apparatus']} carries an unknown production kind")
        if not str(r.get("note", "")).strip():
            raise ValidationError(f"{cid}/{r['apparatus']} carries no note")
        if r.get("source_says") and not r.get("source_says_provenance"):
            raise ValidationError(f"{cid}/{r['apparatus']} quotes a source with no provenance")

    # A producer of THIS quantity, not merely a producer. Q6 exposed the difference: its
    # two routes both measure their own events perfectly and the events are not the same
    # one, so counting own-measurement alone would have called them two witnesses. §20 is
    # exactly that rule, and this makes it machine-checked rather than implied.
    for r in routes:
        if "produces_the_class_world_state_unit" not in r:
            raise ValidationError(
                f"{cid}/{r['apparatus']} does not say whether it produces the class's unit"
            )
    producers = [
        r
        for r in routes
        if r["production"] in PRODUCER_KINDS and r["produces_the_class_world_state_unit"]
    ]

    # §13, §26 and §38. Independence needs two PRODUCERS. A mirror or an aggregator reads
    # a number somebody else produced, and two readers of one counter are one measurement.
    if package["independence_plausible"] and len(producers) < 2:
        raise ValidationError(
            f"{cid} claims independence plausible with {len(producers)} independent producer(s)"
        )
    # Two producers and no independence claim is not an error in itself, and the record
    # must say why. Q6 is exactly that case before the unit rule was added.
    if (
        not package["independence_plausible"]
        and len(producers) >= 2
        and not str(package.get("same_proposition_reason", "")).strip()
    ):
        raise ValidationError(f"{cid} has two producers, denies independence, and gives no reason")

    # §20. Same-proposition may not be claimed where the routes measure different events.
    if (
        package["same_proposition"] in {"ESTABLISHED", "PLAUSIBLE_BUT_NOT_ESTABLISHED"}
        and len(producers) < 2
    ):
        raise ValidationError(
            f"{cid} claims a shared proposition without two independent producers"
        )
    if (
        package["same_proposition"] == "NOT_AVAILABLE"
        and not str(package.get("same_proposition_reason", "")).strip()
    ):
        raise ValidationError(f"{cid} refuses the shared proposition with no reason")

    verdict = package["class_verdict"]
    if verdict not in CLASS_VERDICTS:
        raise ValidationError(f"{cid} carries an unknown class verdict {verdict!r}")

    # §33. Strategic viability is a conjunction and every part is checked.
    if verdict == "STRATEGICALLY_VIABLE":
        if len(producers) < 2:
            raise ValidationError(f"{cid} is STRATEGICALLY_VIABLE on {len(producers)} producer(s)")
        if package["same_proposition"] != "ESTABLISHED":
            raise ValidationError(
                f"{cid} is STRATEGICALLY_VIABLE without an established proposition"
            )
        if not package["independence_plausible"]:
            raise ValidationError(
                f"{cid} is STRATEGICALLY_VIABLE without independence plausibility"
            )
        if RELEVANCE_ORDER[relevance] < RELEVANCE_ORDER["MODERATE"]:
            raise ValidationError(f"{cid} is STRATEGICALLY_VIABLE on {relevance} relevance")
        if package["bounded_pilot_feasible"] in {"NO", "UNKNOWN"}:
            raise ValidationError(f"{cid} is STRATEGICALLY_VIABLE with no bounded pilot")
        if "current state" in str(package["temporal_preselection"]).lower():
            raise ValidationError(f"{cid} is STRATEGICALLY_VIABLE over a current-state surface")

    # §21. The two judgements are recorded apart, always.
    if "useful_complementary_signal" not in package:
        raise ValidationError(f"{cid} does not record complementary usefulness")
    if "suitable_for_same_proposition_independence_experiment" not in package:
        raise ValidationError(f"{cid} does not record experiment suitability")
    if package["suitable_for_same_proposition_independence_experiment"] is True and verdict not in {
        "STRATEGICALLY_VIABLE",
        "PROMISING_REQUIRES_ROUTE_QUALIFICATION",
    }:
        raise ValidationError(f"{cid} is called experiment-suitable while its verdict is {verdict}")

    if package["exact_construct_frozen"] is not False:
        raise ValidationError(f"{cid} froze a construct, which belongs to a later mission")
    if package["values_consulted"] != 0:
        raise ValidationError(f"{cid} was assessed with values consulted")


def _check_populations(packages: list[dict]) -> None:
    """§14 and §24. A different platform is a different population, not a second route."""
    q3 = next(p for p in packages if p["class_id"] == "Q3")
    other_forge = [
        r
        for r in q3["routes"]
        if "gitlab" in r["apparatus"].lower() or "forge" in r["apparatus"].lower()
    ]
    if not other_forge:
        raise ValidationError("Q3 does not consider a second forge at all")
    if not any("DIFFERENT POPULATION" in r["note"] for r in other_forge):
        raise ValidationError("Q3 treats a different forge as a route rather than a population")

    for package in packages:
        # The strong claim needs the record to say how, since no apparatus in this
        # mission could be directed at a corpus.
        if (
            package["population_externally_freezable"] == "POPULATION_EXTERNALLY_FREEZABLE"
            and not str(package.get("population_finding", "")).strip()
        ):
            raise ValidationError(
                f"{package['class_id']} claims an externally freezable population with no basis"
            )


def _check_fixed_corpus(review: dict, packages: list[dict]) -> None:
    """§5 to §11. The deep Q1 review, and the distinction it must not lose."""
    delivered = review["what_was_delivered"]
    # A boolean, not a sentence. The first version of this guard compared the field to the
    # literal "NO" and refused a record whose value read "NO. Neither can be pointed at a
    # corpus we choose." — `testing-strategy.md` §23 for the tenth time. Splitting the
    # verdict from its reason is the structural fix; loosening the comparison to a prefix
    # match would have left the next explanatory sentence free to break it again.
    if delivered["apparatus_directable_at_C"] is not False:
        raise ValidationError(
            "the fixed-corpus review claims an apparatus can be pointed at the corpus"
        )
    if not str(delivered.get("apparatus_directable_at_C_reason", "")).strip():
        raise ValidationError("the fixed-corpus review states no reason for that")
    if not str(review["the_load_bearing_finding"]["source_says"]).strip():
        raise ValidationError("the load-bearing finding carries no quotation")
    if "sample of the web" not in review["the_load_bearing_finding"]["source_says"]:
        raise ValidationError("the load-bearing sampling sentence is not the one quoted")

    # §7. A shared list is not a shared measurement, and the differences must be listed.
    semantics = review["request_semantics"]
    if len(semantics["differences_that_would_have_to_be_reconciled"]) < 4:
        raise ValidationError("the request-semantics differences are not enumerated")

    # §11 and §37. Architecture only.
    operator = review["operator_route"]
    if operator["crawled"] is not False or operator["implemented"] is not False:
        raise ValidationError("the operator route was executed rather than assessed")
    if operator["not_automatically_independent"] is not True:
        raise ValidationError("self-operation was treated as automatically independent")
    if not operator["safeguards_it_would_require"]:
        raise ValidationError("the operator route names no safeguards")

    q1 = next(p for p in packages if p["class_id"] == "Q1")
    if review["verdict"] != q1["class_verdict"]:
        raise ValidationError("the fixed-corpus review and the Q1 package disagree on the verdict")


def _check_lineage(lineage: dict, packages: list[dict]) -> None:
    """§10, §26 and §38."""
    by_class = {f["class"]: f for f in lineage["findings"]}
    for package in packages:
        cid = package["class_id"]
        if cid == "Q0":
            continue
        if cid not in by_class:
            raise ValidationError(f"{cid} has no lineage finding")
        finding = by_class[cid]
        producers = sum(
            1
            for r in package["routes"]
            if r["production"] in PRODUCER_KINDS and r["produces_the_class_world_state_unit"]
        )
        if finding["verdict"] == "TWO_INDEPENDENT_PRODUCERS" and producers < 2:
            raise ValidationError(
                f"{cid} lineage claims two producers and its routes show {producers}"
            )
        if finding["verdict"] != "TWO_INDEPENDENT_PRODUCERS" and producers >= 2:
            raise ValidationError(f"{cid} has two producers and its lineage finding says otherwise")
        if finding.get("source_says") and not finding.get("source_says_provenance"):
            raise ValidationError(f"{cid} lineage quotes a source with no provenance")
        if not finding.get("source_says") and not finding.get("basis"):
            raise ValidationError(f"{cid} lineage rests on neither a quotation nor a stated basis")
        if (
            finding.get("basis")
            and not finding.get("source_says")
            and finding.get("not_newly_retrieved_this_mission") is not True
        ):
            raise ValidationError(
                f"{cid} lineage rests on held evidence without saying it was not retrieved"
            )


def _check_matrix(matrix: dict, packages: list[dict]) -> None:
    """§32."""
    by_id = {p["class_id"]: p for p in packages}
    if set(matrix["rows"]) != set(by_id):
        raise ValidationError("the matrix and the package set disagree on which classes exist")
    for cid, row in matrix["rows"].items():
        package = by_id[cid]
        if row["CLASS_VERDICT"] != package["class_verdict"]:
            raise ValidationError(f"{cid} has two different class verdicts")
        if row["SAME_PROPOSITION"] != package["same_proposition"]:
            raise ValidationError(f"{cid} has two different same-proposition states")
        if row["INDEPENDENCE_PLAUSIBLE"] != package["independence_plausible"]:
            raise ValidationError(f"{cid} has two different independence states")
    expected = [
        p["class_id"]
        for p in packages
        if sum(
            1
            for r in p["routes"]
            if r["production"] in PRODUCER_KINDS and r["produces_the_class_world_state_unit"]
        )
        >= 2
    ]
    if matrix["classes_with_two_own_measurement_routes"] != expected:
        raise ValidationError("the matrix miscounts which classes have two producers")


def _check_comparison(comparison: dict, packages: list[dict]) -> None:
    """§21, §29 and §34."""
    if comparison["scoring_method"]["weighted_numeric_score_used"] is not False:
        raise ValidationError("a weighted numeric score was used")
    by_id = {p["class_id"]: p for p in packages}
    if {row["class_id"] for row in comparison["rows"]} != set(by_id):
        raise ValidationError("the comparison does not cover every class")
    for row in comparison["rows"]:
        if row["class_verdict"] != by_id[row["class_id"]]["class_verdict"]:
            raise ValidationError(f"{row['class_id']} has two different verdicts")

    separation = comparison["the_separation_that_matters"]
    complementary = set(separation["useful_complementary_signal"])
    experiment = set(separation["suitable_for_the_independence_experiment"])
    if experiment - complementary:
        raise ValidationError("a class is experiment-suitable and not complementary-useful")
    actual = {p["class_id"] for p in packages if p["useful_complementary_signal"]}
    if complementary != actual:
        raise ValidationError("the complementary list does not match the packages")


def _check_decision(decision: dict, packages: list[dict]) -> None:
    """§33, §34, §44 and §50."""
    viable = [p for p in packages if p["class_verdict"] == "STRATEGICALLY_VIABLE"]
    if decision["strategically_viable_count"] != len(viable):
        raise ValidationError("the decision miscounts strategically viable classes")

    selected = decision["selected_quantity_class"]
    if selected is None:
        if decision["selection_outcome"] != "NO_SELECTION":
            raise ValidationError("nothing was selected and the outcome is not NO_SELECTION")
        if decision["selected_class_artifact_created"] is not False:
            raise ValidationError("no class was selected and an artifact was recorded")
        if SELECTED.exists():
            raise ValidationError("selected-quantity-class-v1.json exists and nothing was selected")
    else:
        by_id = {p["class_id"]: p for p in packages}
        if selected not in by_id:
            raise ValidationError(f"the selected class {selected!r} has no package")
        if by_id[selected]["class_verdict"] != "STRATEGICALLY_VIABLE":
            raise ValidationError("a class that is not strategically viable was selected")
        if not SELECTED.exists():
            raise ValidationError("a class was selected and no selected-class artifact exists")

    outcome = decision["primary_outcome"]
    selecting = {
        "INDEPENDENT_PRODUCT_RELEVANT_QUANTITY_CLASS_SELECTED",
        "FIXED_CORPUS_HTTP_OBSERVATION_CLASS_SELECTED",
        "PACKAGE_ECOSYSTEM_CLASS_SELECTED",
        "PUBLIC_CODE_ACTIVITY_CLASS_SELECTED",
        "PUBLICATION_ACTIVITY_CLASS_SELECTED",
        "PROCUREMENT_ACTIVITY_CLASS_SELECTED",
        "DNS_OR_WEB_INFRASTRUCTURE_CLASS_SELECTED",
    }
    allowed = selecting | {
        "NO_INDEPENDENT_PRODUCT_RELEVANT_QUANTITY_CLASS_IDENTIFIED",
        "FIXED_CORPUS_WEB_MEASUREMENT_PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED",
        "QUANTITY_CLASS_SELECTION_BLOCKED",
    }
    if outcome not in allowed:
        raise ValidationError(f"the primary outcome {outcome!r} is not defined")
    if outcome in selecting and selected is None:
        raise ValidationError(f"{outcome} reported with nothing selected")
    if outcome == "FIXED_CORPUS_WEB_MEASUREMENT_PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED":
        # §50 outcome I explicitly does NOT select the class.
        if selected is not None:
            raise ValidationError("outcome I reported while a class was selected")
        if not str(decision["the_class_that_came_closest"]["one_load_bearing_question"]).strip():
            raise ValidationError("outcome I reported with no load-bearing question named")

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
    ):
        if parallel[key] is not False:
            raise ValidationError(f"{key} is true, and this mission may not do it")
    if parallel["scanner_arc_status"] != "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE":
        raise ValidationError("the scanner arc status changed in the decision record")

    if decision["canonical_mutation_boundary"]["mutations_this_mission"] != 0:
        raise ValidationError("a canonical mutation was recorded")
    if decision["recommended_next_mission"]["mission_1_70_not_started"] is not True:
        raise ValidationError("the next mission was started")


def _check_no_reliability_value(packages: list[dict]) -> None:
    """No reliability number is assigned to anything, anywhere in these records."""
    for package in packages:
        for node in _walk(package):
            if not isinstance(node, dict):
                continue
            for key, value in node.items():
                if (
                    "reliability" in key.lower()
                    and isinstance(value, (int, float))
                    and not isinstance(value, bool)
                ):
                    raise ValidationError(
                        f"{package['class_id']} assigns a reliability number: {key}"
                    )


def validate() -> list[dict]:
    records = [_load(path) for path in ORDER]
    baseline, universe, matrix, lineage, fixed_corpus, comparison, rule_review, decision = records[
        :8
    ]
    packages = records[8:]

    _check_scanner_arc(baseline)
    _check_registry(baseline, rule_review)
    for package in packages:
        _check_package(package)
    _check_populations(packages)
    _check_fixed_corpus(fixed_corpus, packages)
    _check_lineage(lineage, packages)
    _check_matrix(matrix, packages)
    _check_comparison(comparison, packages)
    _check_decision(decision, packages)
    _check_no_reliability_value(packages)

    if baseline["canonical_baseline"]["drift_from_mission_1_68"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["repository_precondition"]["mission_1_68_merged"] is not True:
        raise ValidationError("the baseline does not record Mission 1.68 as merged")
    if baseline["repository_precondition"]["selected_construct_artifact_absent"] is not True:
        raise ValidationError("the baseline does not record the absent construct artifact")

    budget = universe["budget"]
    if budget["serious_classes"] > budget["maximum_serious_classes"]:
        raise ValidationError("the serious-class budget was exceeded")
    if budget["serious_classes"] < budget["minimum_meaningful_classes_required"]:
        raise ValidationError("fewer than the required minimum of classes were evaluated")
    if budget["serious_classes"] != len(packages):
        raise ValidationError("the universe and the package set disagree on how many classes exist")
    if budget["used"] > budget["maximum_first_party_requests"]:
        raise ValidationError("the documentation budget was exceeded")
    if budget["requests_spent_on_Q0"] > budget["Q0_request_cap"]:
        raise ValidationError(
            "more than the permitted budget was spent re-opening the scanner class"
        )
    if universe["exhaustiveness"]["claimed"] is not False:
        raise ValidationError("the class universe claims to be exhaustive")
    if universe["held_evidence_reused"]["sources_registered"] != 0:
        raise ValidationError("a source was registered")
    if universe["held_evidence_reused"]["source_reviews_mutated"] != 0:
        raise ValidationError("a source review was mutated")

    return records


# ------------------------------------------------------------------------ renderers


def render_fixed_corpus(review: dict) -> str:
    lines = [
        "# Mission 1.69 — Fixed-corpus HTTP observation, reviewed",
        "",
        "Generated from `fixed-corpus-http-class-review-v1.json`. Do not edit by hand.",
        "",
        f"**Verdict: `{review['verdict']}`**",
        "",
        "## The architecture that was hoped for",
        "",
        review["the_architecture_that_was_hoped_for"]["shape"],
        "",
        f"*Why it mattered:* {review['the_architecture_that_was_hoped_for']['why_it_mattered']}",
        "",
        "## What was delivered",
        "",
        "| property | delivered |",
        "|---|---|",
    ]
    for key, value in review["what_was_delivered"].items():
        lines.append(f"| {key.replace('_', ' ')} | {value} |")

    finding = review["the_load_bearing_finding"]
    lines += [
        "",
        "## The load-bearing finding",
        "",
        f"> {finding['source_says']}",
        "",
        f"*Source:* {finding['source_says_provenance']}",
        "",
        finding["project_interpretation"],
        "",
        f"**Why this is not fatal.** {finding['why_this_is_not_fatal']}",
        "",
        f"**Why it is not waved away.** {finding['why_it_is_not_waved_away']}",
        "",
        "## Request semantics",
        "",
        "A shared domain list does not make a shared measurement. These would have to be",
        "reconciled before any proposition is frozen:",
        "",
    ]
    for item in review["request_semantics"]["differences_that_would_have_to_be_reconciled"]:
        lines.append(f"- {item}")

    operator = review["operator_route"]
    lines += [
        "",
        "## The operator route, assessed and not built",
        "",
        f"**What it would solve.** {operator['what_it_would_solve']}",
        "",
        "**Safeguards it would require.**",
        "",
    ]
    for item in operator["safeguards_it_would_require"]:
        lines.append(f"- {item}")
    lines += [
        "",
        f"**Governance complexity.** {operator['governance_complexity']}",
        "",
        f"Crawled: {operator['crawled']}. Implemented: {operator['implemented']}.",
        "",
        "## The one load-bearing question",
        "",
        review["one_load_bearing_question"],
        "",
    ]
    return "\n".join(lines)


def render_decision(decision: dict) -> str:
    comparison = _load(COMPARISON)
    matrix = _load(MATRIX)
    lineage = _load(LINEAGE)
    rule_review = _load(RULE_REVIEW)

    lines = [
        "# Mission 1.69 — Quantity class selection",
        "",
        "Generated from `quantity-class-selection-decision-v1.json` and the eight class",
        "packages. Do not edit by hand.",
        "",
        f"**Primary outcome: `{decision['primary_outcome']}`**",
        "",
        f"**Selected class: {decision['selected_quantity_class'] or 'NONE'}.**",
        "",
        decision["why_nothing_was_selected"] if decision["selected_quantity_class"] is None else "",
        "",
        "## Comparison",
        "",
        "| class | relevance | producers | same proposition | verdict |",
        "|---|---|---|---|---|",
    ]
    for row in comparison["rows"]:
        lines.append(
            f"| `{row['class_id']}` {row['name']} | {row['product_relevance']} "
            f"| {row['own_measurement_routes']} | {row['same_proposition']} "
            f"| {row['class_verdict']} |"
        )

    pattern = comparison["the_pattern_across_rows"]
    lines += [
        "",
        "## The pattern",
        "",
        f"**{pattern['observation']}**",
        "",
        pattern["reading"],
        "",
        f"**The exception, and why.** {pattern['the_exception_and_why']}",
        "",
        "## Lineage",
        "",
        lineage["the_rule_applied"],
        "",
        "| class | lineage |",
        "|---|---|",
    ]
    for finding in lineage["findings"]:
        lines.append(f"| `{finding['class']}` | {finding['verdict']} |")
    lines += ["", lineage["the_pattern"], ""]

    separation = comparison["the_separation_that_matters"]
    lines += [
        "## Complementary value is a different question",
        "",
        separation["statement"],
        "",
        f"- useful complementary signal: {', '.join(separation['useful_complementary_signal'])}",
        f"- suitable for the independence experiment: "
        f"{', '.join(separation['suitable_for_the_independence_experiment']) or 'none'}",
        "",
        "## Two classes have two producers",
        "",
        f"{', '.join(matrix['classes_with_two_own_measurement_routes'])} — {matrix['the_reading']}",
        "",
    ]

    closest = decision["the_class_that_came_closest"]
    lines += [
        "## The class that came closest",
        "",
        f"**`{closest['class_id']}` {closest['name']}.** {closest['why']}",
        "",
        f"*The one load-bearing question:* {closest['one_load_bearing_question']}",
        "",
        f"*What makes it answerable:* {closest['what_makes_the_question_answerable']}",
        "",
        f"*Why it was not selected anyway:* {closest['why_it_was_not_selected_anyway']}",
        "",
        "## Registry",
        "",
        f"Unchanged at {rule_review['registry_count_after']}. Mission 1.68's candidate rule "
        f"was examined for a second instance and none was found.",
        "",
        rule_review["the_standard_applied"],
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    accounting = decision["mission_accounting"]
    for counter in (
        "VALUES_RETRIEVED",
        "CRAWLS",
        "HTTP_MEASUREMENT_REQUESTS",
        "DATASET_DOWNLOADS",
        "BIGQUERY_EXECUTIONS",
        "MEASUREMENT_API_EXECUTIONS",
        "CREDENTIAL_READS",
        "MAILBOX_SEARCHES",
        "SOURCES_REGISTERED",
        "CONSTRUCTS_FROZEN",
        "CLAIMS_CREATED",
        "EVIDENCE_CREATED",
        "PAIRS_SELECTED",
        "MODEL_CALLS",
    ):
        lines.append(f"| {counter} | {accounting[counter]} |")
    lines.append("")
    return "\n".join(lines)


RENDERERS = {DECISION: render_decision, FIXED_CORPUS: render_fixed_corpus}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  quantity class selection: {error}")
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
        print(f"ok       {len(rendered)} quantity-class documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    decision = by_path[DECISION]
    matrix = by_path[MATRIX]
    print(f"outcome  {decision['primary_outcome']}")
    print(f"selected {decision['selected_quantity_class'] or 'NONE'}")
    print(
        f"routes   classes with two independent producers: "
        f"{', '.join(matrix['classes_with_two_own_measurement_routes']) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
