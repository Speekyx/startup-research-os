"""Render and validate the Mission 1.68 measurement-construct selection.

Eleven records, and one discipline underneath all of them:

    A CONSTRUCT IS JUDGED ON WHAT TWO APPARATUSES CAN BOTH WITNESS, AT THE EXACT
    OBSERVATION LEVEL, ON THE SAME POPULATION.

`validate()` enforces the readings this mission was most tempted to make and did
not:

  - a SYN response is a transport-layer fact and never an SSH server, however
    conventionally port 22 is assigned;
  - an apparatus blocker is GLOBAL or CONSTRUCT-SPECIFIC, and a global temporal
    architecture is not repaired by changing the predicate;
  - a construct-specific blocker may not be carried into a construct that does
    not need what it blocked;
  - two apparatuses counting different populations are not two routes, and a
    count of names is never a count of addresses;
  - one plausible route is one, and a route needs a named apparatus with a
    first-party basis;
  - a dated filename is not observation semantics until something says what the
    date denotes;
  - Sonar's TCP study and Sonar's HTTP study are different resources;
  - and nothing was retrieved, downloaded, executed, registered or measured.

    uv run python infrastructure/scripts/render_construct_selection.py
    uv run python infrastructure/scripts/render_construct_selection.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.68-baseline-v1.json"
MATRIX = DATA / "scanner-apparatus-capability-matrix-v1.json"
UNIVERSE = DATA / "construct-candidate-universe-v1.json"
COMPARISON = DATA / "product-relevant-construct-comparison-v1.json"
FEASIBILITY = DATA / "construct-route-feasibility-v1.json"
DECISION = DATA / "construct-selection-decision-v1.json"
SELECTED = DATA / "selected-construct-v1.json"

CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"

PACKAGES = (
    DATA / "construct-package-c0-ssh-identification-v1.json",
    DATA / "construct-package-c1-tcp22-syn-responsiveness-v1.json",
    DATA / "construct-package-c2-http-response-to-ip-addressed-get-v1.json",
    DATA / "construct-package-c3-tls-certificate-observation-v1.json",
    DATA / "construct-package-c4-dns-record-configuration-v1.json",
)

ORDER = [BASELINE, MATRIX, UNIVERSE, COMPARISON, FEASIBILITY, DECISION, *PACKAGES]

RENDERED = {
    DECISION: DATA / "mission-1.68-construct-selection-v1.md",
    FEASIBILITY: DATA / "construct-route-feasibility-v1.md",
}

APPARATUSES = (
    "Censys",
    "Netlas",
    "LeakIX",
    "Shadowserver",
    "ONYPHE",
    "Rapid7 Project Sonar",
    "Shodan",
)

CELL_VOCABULARY = frozenset(
    {
        "PLAUSIBLE_ROUTE",
        "BLOCKED_TEMPORAL",
        "BLOCKED_PREDICATE_NOT_RETRIEVABLE",
        "BLOCKED_FRAME",
        "BLOCKED_CONFIGURATION",
        "BLOCKED_LINEAGE",
        "BLOCKED_ACCESS",
        "UNRESOLVED",
        "NOT_APPLICABLE",
    }
)

RELEVANCE_ORDER = {
    "NON_PRODUCT_RELEVANT": 0,
    "WEAK_PRODUCT_RELEVANCE": 1,
    "MODERATE_PRODUCT_RELEVANCE": 2,
    "STRONG_PRODUCT_RELEVANCE": 3,
}

# §3 and §11. An apparatus whose blocker is a property of its temporal architecture is
# blocked under every construct: no change of predicate repairs where a timestamp points.
GLOBAL_TEMPORAL_APPARATUSES = frozenset({"Shodan", "LeakIX"})
GLOBAL_FRAME_APPARATUSES = frozenset({"Shadowserver"})

# §40. Semantic promotions this mission must never make. Each maps a forbidden phrase to
# the observation it would have been promoted from.
FORBIDDEN_PROMOTIONS = {
    "ssh server": "a SYN response is a transport-layer fact and identifies no application",
    "number of ssh servers": "the same promotion, stated as a count",
    "is a customer": "an address is not a customer",
    "are customers": "an address is not a customer",
    "hostname is a user": "a name is not a person",
    "certificate proves purchase": "a certificate is not a transaction",
    "market size": "no observation here bears on market size",
    "product-market fit": "no observation here bears on it",
    "willingness to pay": "no observation here bears on it",
}

HARD_ZERO_COUNTERS = (
    "TARGET_VALUE_EXPOSURES",
    "MEASUREMENT_VALUES_RETRIEVED",
    "RESEARCH_DATA_REQUESTS",
    "API_EXECUTIONS",
    "MEASUREMENT_API_EXECUTIONS",
    "COUNT_ENDPOINT_EXECUTIONS",
    "TARGET_COUNTS_FETCHED",
    "HOSTS_FETCHED",
    "BANNERS_FETCHED",
    "DATASET_DOWNLOADS",
    "DOWNLOADS",
    "TRIALS",
    "PURCHASES",
    "ACCOUNTS_CREATED",
    "CREDENTIAL_READS",
    "MAILBOX_SEARCHES",
    "ENQUIRIES_SENT",
    "SOURCES_REGISTERED",
    "GOVERNANCE_REVIEWS",
    "GOVERNANCE_MUTATIONS",
    "THRESHOLDS_REGISTERED",
    "CLAIMS_CREATED",
    "CLAIM_REVISIONS_CREATED",
    "SIGNALS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "RELIABILITY_ASSESSMENTS_CREATED",
    "RELIABILITY_VALUES_ASSIGNED",
    "SCORES",
    "OPPORTUNITY_MUTATIONS",
    "MODEL_CALLS",
    "EMBEDDINGS",
    "MIGRATIONS",
    "PAIRS_SELECTED",
    "APPARATUS_PAIRS_COMPARED",
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


def _prose(record: dict) -> str:
    """Every string in a record except the ones that EXPLAIN a rule.

    A `$comment` is where a rule is written and a rule may name the thing it forbids; a
    field may not. Same shape as Mission 1.66.2's stripped-comment scan, and the reason
    is `testing-strategy.md` §23: a scan aimed at wording fires on the prose doing the
    work unless the explanatory regions are excluded structurally.
    """
    pieces: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key.startswith("$") or key.startswith("why_") or key.startswith("explicit_"):
                    continue
                if key in {
                    "why_tcp_responsiveness_is_not_ssh",
                    "non_claims",
                    "explicit_non_claims",
                    "forbidden",
                    "project_interpretation",
                    "reading",
                    "note",
                    "statement",
                    "weakest_truthful_interpretation",
                    "what_a_positive_observation_establishes",
                }:
                    continue
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            pieces.append(node)

    walk(record)
    return " \n ".join(pieces).lower()


def _check_registry(baseline: dict, decision: dict) -> None:
    """§33. The registry stays at 15 unless a rule passed change control, and none did."""
    requirements = _load(CONTRACT)["requirement_registry"]["requirements"]
    if len(requirements) != 15:
        raise ValidationError(f"the registry holds {len(requirements)} requirements, not 15")
    if baseline["requirement_registry"]["count_after"] != 15:
        raise ValidationError("the baseline records a registry count other than 15")
    if baseline["requirement_registry"]["requirement_added_this_mission"] is not None:
        raise ValidationError("the baseline records a requirement added this mission")
    if decision["requirement_registry"]["count_after"] != 15:
        raise ValidationError("the decision records a registry count other than 15")
    if decision["requirement_registry"]["requirement_added"] is not None:
        raise ValidationError("a requirement was added without passing change control")

    offered = decision["requirement_registry"]["candidate_offered_and_not_added"]
    names = {item["name"] for item in requirements}
    if offered["name"] in names:
        raise ValidationError("a requirement recorded as NOT added is in the registry")
    if not str(offered["why_it_was_not_added"]).strip():
        raise ValidationError("an offered requirement was declined with no reason")


def _check_ssh_preserved(baseline: dict, decision: dict) -> None:
    """§2. The control construct is preserved, not retired."""
    ssh = baseline["current_ssh_construct"]
    if ssh["status"] != "NO_TWO_QUALIFIED_APPARATUS_ROUTE_IDENTIFIED":
        raise ValidationError(f"the SSH construct status reads {ssh['status']!r}")
    for forbidden in ("FAILED", "BAD_CONSTRUCT", "INVALID"):
        if ssh["status"] == forbidden:
            raise ValidationError(f"the SSH construct was marked {forbidden}")
        if forbidden not in ssh["status_is_not"]:
            raise ValidationError(f"the record no longer refuses the label {forbidden}")
    if ssh["historical_missions_rewritten"] != 0:
        raise ValidationError("a historical mission was rewritten")
    if not ssh["evaluated_as_a_control_this_mission"]:
        raise ValidationError("the control construct was not evaluated")
    if decision["current_ssh_construct_outcome"]["evaluated_through_the_same_matrix"] is not True:
        raise ValidationError("the control was exempted from the matrix")


def _check_capability_matrix(matrix: dict) -> None:
    """§3. Every blocker is classified global or construct-specific, with a basis."""
    kinds: dict[str, set[str]] = {}
    for apparatus in matrix["apparatuses"]:
        name = apparatus["name"]
        if name not in APPARATUSES:
            raise ValidationError(f"the capability matrix names an unknown apparatus {name!r}")
        if not apparatus["surfaces_evaluated"]:
            raise ValidationError(f"{name} records no evaluated surface")
        kinds[name] = set()
        for blocker in apparatus["blockers"]:
            kind = blocker["kind"]
            if kind not in {"APPARATUS_GLOBAL_BLOCKER", "CONSTRUCT_SPECIFIC_BLOCKER"}:
                raise ValidationError(f"{name} carries an unclassified blocker kind {kind!r}")
            if not str(blocker.get("project_interpretation", "")).strip():
                raise ValidationError(f"{name} carries a blocker with no interpretation")
            kinds[name].add(kind)

    # §16 and §22. Sonar's two studies are different resources and must be listed apart, or
    # a finding about one silently becomes a finding about the other.
    sonar = next(a for a in matrix["apparatuses"] if a["name"] == "Rapid7 Project Sonar")
    surfaces = " ".join(sonar["surfaces_evaluated"]).lower()
    if "sonar.tcp" not in surfaces or "http" not in surfaces:
        raise ValidationError("Sonar's TCP and HTTP studies are not evaluated as separate surfaces")

    censys = next(a for a in matrix["apparatuses"] if a["name"] == "Censys")
    if len(censys["surfaces_evaluated"]) < 2:
        raise ValidationError("Censys was evaluated on a single surface")
    if censys["access"]["used_as_an_epistemic_disqualifier"] is not False:
        raise ValidationError("Censys access terms were used as an epistemic disqualifier")


def _check_package(package: dict) -> None:
    """§7 to §13, §25 and §38 for one construct package."""
    cid = package["construct_id"]

    relevance = package["product_relevance"]["class"]
    if relevance not in RELEVANCE_ORDER:
        raise ValidationError(f"{cid} carries an unknown relevance class {relevance!r}")
    if relevance == "NON_PRODUCT_RELEVANT":
        raise ValidationError(f"{cid} is NON_PRODUCT_RELEVANT and was not hard-rejected")
    if not str(package["product_relevance"]["weakest_truthful_interpretation"]).strip():
        raise ValidationError(f"{cid} states no weakest truthful interpretation")

    proposition = package["proposition"]
    for field in (
        "canonical_subject",
        "population",
        "population_type",
        "unit",
        "deduplication_unit",
        "observation_window_semantics",
        "predicate",
        "inclusion_rule",
        "exclusion_rule",
        "vantage_semantics",
        "configuration_assumptions",
    ):
        if not str(proposition.get(field, "")).strip():
            raise ValidationError(f"{cid} leaves {field} empty, and §9 requires it frozen")

    if proposition["population_type"] not in {"IP_ADDRESS", "DOMAIN_NAME"}:
        raise ValidationError(f"{cid} carries an unknown population type")

    # §17 and §40. A distinct-address count is never a row count.
    if proposition["population_type"] == "IP_ADDRESS":
        if "distinct" not in proposition["unit"].lower():
            raise ValidationError(f"{cid} counts an IP population without a distinct unit")
        if "row" in proposition["deduplication_unit"].lower():
            raise ValidationError(f"{cid} deduplicates by row rather than by address")

    if not package["explicit_non_claims"]:
        raise ValidationError(f"{cid} states no explicit non-claims")

    # §40. The semantic promotion must not appear outside the regions that REFUSE it.
    prose = _prose(package)
    for phrase, why in FORBIDDEN_PROMOTIONS.items():
        if phrase in prose:
            raise ValidationError(f"{cid} promotes an observation: {phrase!r} — {why}")

    # The SSH promotion is the one this construct family invites, so it is checked
    # structurally as well as lexically.
    if "SYN" in proposition["predicate"] and "ssh" in proposition["canonical_subject"].lower():
        raise ValidationError(f"{cid} gives a SYN predicate an SSH subject")
    if "SYN" in proposition["predicate"]:
        if not str(package.get("why_tcp_responsiveness_is_not_ssh", "")).strip():
            raise ValidationError(
                f"{cid} has a SYN predicate and does not state why that is not SSH"
            )
        if not any("NOT that an SSH server" in claim for claim in package["explicit_non_claims"]):
            raise ValidationError(f"{cid} has a SYN predicate and does not refuse the SSH reading")

    # §19 and §43. A route names a real apparatus and carries a verdict from the vocabulary.
    routes = package["routes"]
    if set(routes) != set(APPARATUSES):
        raise ValidationError(f"{cid} does not evaluate exactly the seven known apparatuses")
    for name, cell in routes.items():
        if cell["verdict"] not in CELL_VOCABULARY:
            raise ValidationError(f"{cid}/{name} carries an unknown verdict {cell['verdict']!r}")
        if cell["verdict"] != "PLAUSIBLE_ROUTE" and not cell.get("decisive_blocker"):
            raise ValidationError(f"{cid}/{name} is not plausible and names no decisive blocker")
        if cell["verdict"] == "PLAUSIBLE_ROUTE" and cell.get("decisive_blocker") is not None:
            raise ValidationError(f"{cid}/{name} is plausible and names a blocker")
        if not str(cell.get("note", "")).strip():
            raise ValidationError(f"{cid}/{name} carries no note")

    # §11 and §23. A global temporal architecture is not repaired by a new predicate.
    for name in GLOBAL_TEMPORAL_APPARATUSES:
        if routes[name]["verdict"] != "BLOCKED_TEMPORAL":
            raise ValidationError(
                f"{cid}/{name} waives a global temporal blocker by changing the predicate"
            )
    for name in GLOBAL_FRAME_APPARATUSES:
        if routes[name]["verdict"] != "BLOCKED_FRAME":
            raise ValidationError(f"{cid}/{name} waives a global frame blocker")

    plausible = [n for n, c in routes.items() if c["verdict"] == "PLAUSIBLE_ROUTE"]
    if package["plausible_apparatus_route_count"] != len(plausible):
        raise ValidationError(
            f"{cid} reports {package['plausible_apparatus_route_count']} plausible routes "
            f"and its matrix has {len(plausible)}"
        )

    # §44. One is one.
    if len(plausible) == 1 and package["route_shortfall"] != "SECOND_ROUTE_MISSING":
        raise ValidationError(f"{cid} has one route and does not record SECOND_ROUTE_MISSING")
    if len(plausible) == 0 and package["route_shortfall"] != "NO_ROUTE":
        raise ValidationError(f"{cid} has no route and does not record NO_ROUTE")

    # §25. Structural viability requires two routes and moderate relevance.
    verdict = package["structural_verdict"]
    if verdict not in {"STRUCTURALLY_VIABLE", "NOT_STRUCTURALLY_VIABLE"}:
        raise ValidationError(f"{cid} carries an unknown structural verdict")
    if verdict == "STRUCTURALLY_VIABLE":
        if len(plausible) < 2:
            raise ValidationError(f"{cid} is STRUCTURALLY_VIABLE on {len(plausible)} route(s)")
        if RELEVANCE_ORDER[relevance] < RELEVANCE_ORDER["MODERATE_PRODUCT_RELEVANCE"]:
            raise ValidationError(f"{cid} is STRUCTURALLY_VIABLE on {relevance}")
        if package["failed_hard_conditions"]:
            raise ValidationError(f"{cid} is STRUCTURALLY_VIABLE with failed hard conditions")
        # §13. Two routes must witness the same population.
        types = {proposition["population_type"]}
        if len(types) != 1:
            raise ValidationError(f"{cid} is viable across more than one population type")
    else:
        if not package["failed_hard_conditions"]:
            raise ValidationError(f"{cid} is NOT_STRUCTURALLY_VIABLE and names no failed condition")

    if package["values_consulted_to_choose_this_construct"] != 0:
        raise ValidationError(f"{cid} was chosen with values consulted")

    # §21. A dated filename is not observation semantics.
    if any("Sonar" in n for n, c in routes.items() if c["verdict"] == "PLAUSIBLE_ROUTE"):
        unresolved = json.dumps(package.get("unresolved_load_bearing_questions", []))
        if "date" in unresolved.lower() or cid != "C1_TCP22_SYN_RESPONSIVENESS":
            return
        raise ValidationError(
            f"{cid} rests on Sonar without recording that the filename date semantics are unresolved"
        )


def _check_populations(packages: list[dict]) -> None:
    """§10 and §13. A name population and an address population never mix."""
    for package in packages:
        if package["proposition"]["population_type"] != "DOMAIN_NAME":
            continue
        note = package.get("population_incomparability")
        if not note or not str(note.get("statement", "")).strip():
            raise ValidationError(
                f"{package['construct_id']} counts names and does not record that a count of "
                "names is not a count of addresses"
            )


def _check_construct_specificity(matrix: dict, packages: list[dict]) -> None:
    """§3. A construct-specific blocker may not behave like a global one.

    Sonar is the case this exists for. Mission 1.67 blocked it because its arbitrary-TCP
    resource carries no response bytes, and that blocker must NOT reappear under a
    predicate that reads no response bytes. If it did, the mission would have repeated
    Mission 1.67's answer without repeating its work.
    """
    for apparatus in matrix["apparatuses"]:
        name = apparatus["name"]
        kinds = {b["kind"] for b in apparatus["blockers"]}
        if kinds != {"CONSTRUCT_SPECIFIC_BLOCKER"}:
            continue
        verdicts = {p["routes"][name]["verdict"] for p in packages}
        if verdicts == {"BLOCKED_PREDICATE_NOT_RETRIEVABLE"}:
            raise ValidationError(
                f"{name}'s blocker is recorded CONSTRUCT_SPECIFIC and blocks every construct, "
                "which is a global blocker wearing the wrong label"
            )


def _check_feasibility(feasibility: dict, packages: list[dict]) -> None:
    """§19 and §43."""
    if list(feasibility["apparatus_columns"]) != list(APPARATUSES):
        raise ValidationError("the feasibility matrix columns do not match the known apparatuses")
    by_id = {p["construct_id"]: p for p in packages}
    if set(feasibility["matrix"]) != set(by_id):
        raise ValidationError("the feasibility matrix and the packages disagree on constructs")
    for cid, row in feasibility["matrix"].items():
        for name, verdict in row.items():
            if by_id[cid]["routes"][name]["verdict"] != verdict:
                raise ValidationError(f"{cid}/{name} has two different verdicts")
    for cid, count in feasibility["plausible_route_counts"].items():
        if count != by_id[cid]["plausible_apparatus_route_count"]:
            raise ValidationError(f"{cid} has two different plausible-route counts")

    stated = feasibility["a_plausible_route_is_not_a_qualified_apparatus"]
    if stated["qualified_apparatus_count"] != 0:
        raise ValidationError("a plausible route was counted as a qualified apparatus")
    if stated["pair_analysis_state"] != "PAIR_ANALYSIS_NOT_READY":
        raise ValidationError("pair readiness was claimed from plausible routes")

    if feasibility["independence_plausibility"]["assessment"] not in {
        "INDEPENDENCE_NOT_DISPROVEN",
        "INDEPENDENCE_PLAUSIBLE",
        "INDEPENDENCE_DISPROVEN",
    }:
        raise ValidationError("the independence assessment is not one of the defined states")
    if not str(feasibility["independence_plausibility"]["not_established"]).strip():
        raise ValidationError("the independence assessment does not say what it fails to establish")


def _check_comparison(comparison: dict, packages: list[dict]) -> None:
    """§29 and §39."""
    if comparison["scoring_method"]["weighted_numeric_score_used"] is not False:
        raise ValidationError("a weighted numeric score was used")
    by_id = {p["construct_id"]: p for p in packages}
    if {row["construct_id"] for row in comparison["rows"]} != set(by_id):
        raise ValidationError("the comparison does not cover every serious construct")
    for row in comparison["rows"]:
        package = by_id[row["construct_id"]]
        if row["structural_verdict"] != package["structural_verdict"]:
            raise ValidationError(f"{row['construct_id']} has two different structural verdicts")
        if row["plausible_apparatus_route_count"] != package["plausible_apparatus_route_count"]:
            raise ValidationError(f"{row['construct_id']} has two different route counts")

    # §39. The required comparison set.
    ids = set(by_id)
    if "C0_SSH_IDENTIFICATION" not in ids:
        raise ValidationError("the existing SSH construct is missing from the comparison")
    if "C1_TCP22_SYN_RESPONSIVENESS" not in ids:
        raise ValidationError("a TCP responsiveness construct is missing from the comparison")
    if not any("HTTP" in cid for cid in ids):
        raise ValidationError("an HTTP-level construct is missing from the comparison")
    if not any("TLS" in cid or "DNS" in cid for cid in ids):
        raise ValidationError("a TLS or DNS construct is missing from the comparison")


def _check_decision(decision: dict, packages: list[dict]) -> None:
    """§30, §44 and §45."""
    viable = [p for p in packages if p["structural_verdict"] == "STRUCTURALLY_VIABLE"]
    if decision["structurally_viable_count"] != len(viable):
        raise ValidationError("the decision miscounts structurally viable constructs")

    selected = decision["selected_construct"]
    if selected is None:
        if decision["selection_outcome"] != "NO_SELECTION":
            raise ValidationError("nothing was selected and the outcome is not NO_SELECTION")
        if decision["selected_construct_artifact_created"] is not False:
            raise ValidationError("no construct was selected and an artifact was recorded")
        if SELECTED.exists():
            raise ValidationError("selected-construct-v1.json exists and no construct was selected")
    else:
        by_id = {p["construct_id"]: p for p in packages}
        if selected not in by_id:
            raise ValidationError(f"the selected construct {selected!r} has no package")
        package = by_id[selected]
        if package["structural_verdict"] != "STRUCTURALLY_VIABLE":
            raise ValidationError("a construct that is not structurally viable was selected")
        if package["plausible_apparatus_route_count"] < 2:
            raise ValidationError("a construct with fewer than two routes was selected")
        if not SELECTED.exists():
            raise ValidationError(
                "a construct was selected and no selected-construct artifact exists"
            )
        # §8. A weak candidate may never beat a structurally comparable stronger one.
        weak = RELEVANCE_ORDER[package["product_relevance"]["class"]]
        for other in viable:
            if other["construct_id"] == selected:
                continue
            if RELEVANCE_ORDER[other["product_relevance"]["class"]] > weak:
                raise ValidationError(
                    "a weaker-relevance construct was selected over a viable stronger one"
                )

    outcome = decision["primary_outcome"]
    allowed = {
        "PRODUCT_RELEVANT_CONSTRUCT_SELECTED_TWO_ROUTES_IDENTIFIED",
        "TCP_SYN_RESPONSIVENESS_SELECTED",
        "HTTP_LEVEL_CONSTRUCT_SELECTED",
        "TLS_OR_DNS_CONSTRUCT_SELECTED",
        "NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED",
        "CURRENT_SCANNER_CLASS_INSUFFICIENT_FOR_INDEPENDENT_MEASUREMENT",
        "CONSTRUCT_SELECTION_BLOCKED",
    }
    if outcome not in allowed:
        raise ValidationError(f"the primary outcome {outcome!r} is not defined")
    selecting = {
        "PRODUCT_RELEVANT_CONSTRUCT_SELECTED_TWO_ROUTES_IDENTIFIED",
        "TCP_SYN_RESPONSIVENESS_SELECTED",
        "HTTP_LEVEL_CONSTRUCT_SELECTED",
        "TLS_OR_DNS_CONSTRUCT_SELECTED",
    }
    if outcome in selecting and selected is None:
        raise ValidationError(f"{outcome} reported with no construct selected")
    if outcome == "NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED" and selected:
        raise ValidationError("outcome E reported while a construct was selected")

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

    if decision["canonical_mutation_boundary"]["mutations_this_mission"] != 0:
        raise ValidationError("a canonical mutation was recorded")
    if decision["recommended_next_mission"]["mission_1_69_not_started"] is not True:
        raise ValidationError("the next mission was started")


def validate() -> list[dict]:
    records = [_load(path) for path in ORDER]
    baseline, matrix, universe, comparison, feasibility, decision = records[:6]
    packages = records[6:]

    _check_registry(baseline, decision)
    _check_ssh_preserved(baseline, decision)
    _check_capability_matrix(matrix)
    for package in packages:
        _check_package(package)
    _check_populations(packages)
    _check_construct_specificity(matrix, packages)
    _check_feasibility(feasibility, packages)
    _check_comparison(comparison, packages)
    _check_decision(decision, packages)

    if baseline["canonical_baseline"]["drift_from_mission_1_67"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["repository_precondition"]["mission_1_67_merged"] is not True:
        raise ValidationError("the baseline does not record Mission 1.67 as merged")

    budget = universe["budget"]
    if budget["serious_constructs"] > budget["maximum_serious_constructs"]:
        raise ValidationError("the serious-construct budget was exceeded")
    if budget["serious_constructs"] != len(packages):
        raise ValidationError(
            "the universe and the package set disagree on how many constructs exist"
        )
    if budget["used"] > budget["maximum_additional_first_party_requests"]:
        raise ValidationError("the documentation budget was exceeded")

    return records


# ------------------------------------------------------------------------ renderers


def render_feasibility(feasibility: dict) -> str:
    short = {
        "PLAUSIBLE_ROUTE": "**plausible**",
        "BLOCKED_TEMPORAL": "temporal",
        "BLOCKED_PREDICATE_NOT_RETRIEVABLE": "predicate",
        "BLOCKED_FRAME": "frame",
        "BLOCKED_CONFIGURATION": "config",
        "BLOCKED_LINEAGE": "lineage",
        "BLOCKED_ACCESS": "access",
        "UNRESOLVED": "unresolved",
        "NOT_APPLICABLE": "n/a",
    }
    lines = [
        "# Mission 1.68 — Construct reachability matrix",
        "",
        "Generated from `construct-route-feasibility-v1.json`. Do not edit by hand.",
        "",
        "A cell says whether an apparatus could plausibly witness that construct. A",
        "**plausible route** names an apparatus with a first-party basis and unresolved",
        "questions. It is not a qualified apparatus.",
        "",
        "| construct | " + " | ".join(feasibility["apparatus_columns"]) + " |",
        "|---" * (len(feasibility["apparatus_columns"]) + 1) + "|",
    ]
    for cid, row in feasibility["matrix"].items():
        cells = [short[row[name]] for name in feasibility["apparatus_columns"]]
        lines.append(f"| `{cid}` | " + " | ".join(cells) + " |")

    lines += [
        "",
        "| construct | plausible routes |",
        "|---|---|",
    ]
    for cid, count in feasibility["plausible_route_counts"].items():
        lines.append(f"| `{cid}` | {count} |")

    split = feasibility["global_versus_construct_specific"]
    lines += [
        "",
        "## What survives a change of predicate",
        "",
        "### Global blockers, unchanged by any construct",
        "",
    ]
    for name, why in split["global_blockers_that_persist_across_every_construct"].items():
        lines.append(f"- **{name}** — {why}")

    lines += ["", "### Construct-specific blockers that correctly disappeared", ""]
    for name, why in split["construct_specific_blockers_that_correctly_disappeared"].items():
        lines.append(f"- **{name}** — {why}")

    lines += ["", "### Construct-specific blockers that appeared", ""]
    for name, why in split["construct_specific_blockers_that_appeared"].items():
        lines.append(f"- **{name}** — {why}")

    lines += [
        "",
        "### Elevated rather than removed",
        "",
        f"- **vantage** — {split['elevated_rather_than_removed']['vantage']}",
        "",
        "## Independence",
        "",
        f"**{feasibility['independence_plausibility']['assessment']}.** "
        f"{feasibility['independence_plausibility']['reasoning']}",
        "",
        f"*Not established:* {feasibility['independence_plausibility']['not_established']}",
        "",
    ]
    return "\n".join(lines)


def render_decision(decision: dict) -> str:
    comparison = _load(COMPARISON)
    universe = _load(UNIVERSE)
    packages = [_load(p) for p in PACKAGES]

    lines = [
        "# Mission 1.68 — Product-relevant measurement construct selection",
        "",
        "Generated from `construct-selection-decision-v1.json`,",
        "`product-relevant-construct-comparison-v1.json` and the five construct packages.",
        "Do not edit by hand.",
        "",
        f"**Primary outcome: `{decision['primary_outcome']}`**",
        "",
        f"**Selected construct: {decision['selected_construct'] or 'NONE'}.** "
        f"{decision['why_nothing_was_selected'] if decision['selected_construct'] is None else ''}",
        "",
        "## Comparison",
        "",
        "| construct | relevance | population | routes | verdict |",
        "|---|---|---|---|---|",
    ]
    for row in comparison["rows"]:
        routes = ", ".join(row["plausible_routes"]) or "—"
        lines.append(
            f"| `{row['construct_id']}` | {row['product_relevance'].replace('_PRODUCT_RELEVANCE', '')} "
            f"| {row['population_type']} | {row['plausible_apparatus_route_count']} ({routes}) "
            f"| {row['structural_verdict']} |"
        )

    pattern = comparison["the_pattern_across_rows"]
    lines += [
        "",
        "## The pattern across rows",
        "",
        f"**{pattern['observation']}**",
        "",
        "| construct | its one route |",
        "|---|---|",
    ]
    for cid, who in pattern["detail"].items():
        lines.append(f"| `{cid}` | {who} |")
    lines += [
        "",
        f"{pattern['reading']}",
        "",
        f"**Why it happens.** {pattern['why_it_happens']}",
        "",
        f"*{pattern['this_is_an_observation_not_a_verdict']}*",
        "",
        "## The propositions, at the observation level",
        "",
    ]
    for package in packages:
        lines += [
            f"### `{package['construct_id']}`",
            "",
            f"**Proposition.** {package['proposition']['predicate']}",
            "",
            f"- population: {package['proposition']['population']} "
            f"(`{package['proposition']['population_type']}`)",
            f"- unit: {package['proposition']['unit']}",
            f"- deduplication: {package['proposition']['deduplication_unit']}",
            f"- window: {package['proposition']['observation_window_semantics']}",
            f"- relevance: `{package['product_relevance']['class']}`",
            "",
            "**What it does not establish.**",
            "",
        ]
        for claim in package["explicit_non_claims"]:
            lines.append(f"- {claim}")
        lines.append("")

    closest = decision["the_construct_that_came_closest"]
    lines += [
        "## The one that came closest",
        "",
        f"**`{closest['construct_id']}`.** {closest['why']}",
        "",
        f"*What would change it:* {closest['what_would_change_it']}",
        "",
        f"*Why it was not selected anyway:* {closest['why_it_was_not_selected_anyway']}",
        "",
        "## Registry",
        "",
        f"Unchanged at {decision['requirement_registry']['count_after']}. "
        f"A candidate rule was offered and not added: "
        f"`{decision['requirement_registry']['candidate_offered_and_not_added']['name']}`.",
        "",
        decision["requirement_registry"]["candidate_offered_and_not_added"]["why_it_was_not_added"],
        "",
        "## What held evidence bought",
        "",
        universe["reuse_of_held_evidence"]["cost_reduction_observed"],
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    accounting = decision["mission_accounting"]
    for counter in (
        "MEASUREMENT_VALUES_RETRIEVED",
        "TARGET_VALUE_EXPOSURES",
        "API_EXECUTIONS",
        "DATASET_DOWNLOADS",
        "TRIALS",
        "CREDENTIAL_READS",
        "MAILBOX_SEARCHES",
        "SOURCES_REGISTERED",
        "THRESHOLDS_REGISTERED",
        "CLAIMS_CREATED",
        "EVIDENCE_CREATED",
        "RELIABILITY_VALUES_ASSIGNED",
        "PAIRS_SELECTED",
        "MODEL_CALLS",
    ):
        lines.append(f"| {counter} | {accounting[counter]} |")
    lines.append("")
    return "\n".join(lines)


RENDERERS = {DECISION: render_decision, FEASIBILITY: render_feasibility}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  construct selection: {error}")
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
        print(f"ok       {len(rendered)} construct documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    decision = by_path[DECISION]
    print(f"outcome  {decision['primary_outcome']}")
    print(f"selected {decision['selected_construct'] or 'NONE'}")
    print(
        f"routes   max plausible per construct "
        f"{max(by_path[FEASIBILITY]['plausible_route_counts'].values())}, minimum required 2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
