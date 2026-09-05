"""Render and validate the Mission 1.67 second-qualified-scanner discovery.

Nine records, and one discipline underneath all of them:

    A CANDIDATE IS JUDGED ON WHAT ITS OWN DOCUMENTS SAY ABOUT THE EXACT RESOURCE
    THE CONSTRUCT WOULD BE WITNESSED THROUGH.

`validate()` enforces the readings this mission was most tempted to make and did
not:

  - a name found in a search result is not a serious candidate, and a candidate
    whose first-party documentation could not be retrieved never becomes one;
  - an apparatus already evaluated in an earlier mission cannot be rediscovered
    as new;
  - a database documented as updated in real time is a maintained current state,
    however many timestamps it exposes, and a per-address history is not a
    window-addressable frame;
  - a SYN response says a port answered and carries no identification string, so
    a resource that publishes one cannot witness a protocol-native predicate,
    even where the apparatus states it measures that protocol elsewhere;
  - a count whose unit is undocumented cannot be a count of distinct addresses;
  - configuration heterogeneity is not sampling, is not the retrievable frame,
    and is not time-addressability;
  - a retrieval summary is not a quotation, so every load-bearing quote must
    name a document this mission actually retrieved;
  - and nothing was executed, trialled, registered, measured or contacted.

    uv run python infrastructure/scripts/render_scanner_discovery.py
    uv run python infrastructure/scripts/render_scanner_discovery.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.67-baseline-v1.json"
RULE_REVIEW = DATA / "apparatus-frame-uniformity-requirement-review-v1.json"
UNIVERSE = DATA / "scanner-discovery-universe-v1.json"
PRESCREEN = DATA / "scanner-candidate-prescreen-v1.json"
SONAR = DATA / "scanner-qualification-rapid7-sonar-v1.json"
SHODAN = DATA / "scanner-qualification-shodan-v1.json"
QUALIFICATION = DATA / "scanner-individual-qualification-v1.json"
READINESS = DATA / "qualified-apparatus-readiness-v4.json"
LEDGER = DATA / "mission-1.67-documentation-ledger-v1.json"

CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
ONYPHE_PACKAGE = DATA / "onyphe-package-recomputed-v2.json"
READINESS_V3 = DATA / "qualified-apparatus-readiness-v3.json"

ORDER = [
    BASELINE,
    RULE_REVIEW,
    UNIVERSE,
    PRESCREEN,
    SONAR,
    SHODAN,
    QUALIFICATION,
    READINESS,
    LEDGER,
]

RENDERED = {
    UNIVERSE: DATA / "mission-1.67-scanner-discovery-v1.md",
    RULE_REVIEW: DATA / "apparatus-frame-uniformity-requirement-review-v1.md",
    QUALIFICATION: DATA / "scanner-individual-qualification-v1.md",
}

# The apparatuses earlier missions already evaluated. §5 makes the first four frozen
# controls; Censys was evaluated and dropped in Missions 1.58 and 1.59. None of them may
# be rediscovered as new, which is the cheapest way for a discovery mission to look
# productive while establishing nothing.
FROZEN_CONTROLS = frozenset(
    {"Netlas", "ONYPHE", "LeakIX", "Shadowserver", "The Shadowserver Foundation", "Censys"}
)

PERMITTED_EXPOSURE_CLASSES = frozenset(
    {"RAW_IDENTIFICATION_STRING", "STRUCTURED_PROTOCOL_NATIVE_FIELD", "DETERMINISTIC_EQUIVALENT"}
)

# §14. Only these two temporal objects let an acquisition restricted to W recover an
# observation made during W. A maintained service state cannot, and an ambiguous or
# unknown one has not been established to.
APPEND_LIKE = frozenset({"OBSERVATION_EVENT_APPEND", "VERSIONED_OBSERVATION_HISTORY"})

ALLOWED_GATE_STATUS = frozenset(
    {"PASS", "FAIL", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE", "NOT_EVALUATED_AFTER_DECISIVE_FAIL"}
)

MANDATORY_GATES = (
    "A1_ACTIVE_MEASUREMENT_PRODUCER",
    "A2_OBSERVATION_ADDRESSABLE_EXPOSURE",
    "A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE",
    "A4_OBSERVATION_TIME_DOCUMENTED",
    "A5_FRAME_DOCUMENTED",
    "A6_NON_VALUE_DOCUMENTATION_AVAILABLE",
    "A7_AFFIRMATIVE_MEASUREMENT_LINEAGE",
    "A8_RELIABILITY_REVIEWABLE",
    "A9_PRODUCT_RELEVANT",
)

FRAME_KEYS = ("eligible_frame", "attempted_frame", "measured_frame", "retrievable_frame")

HARD_ZERO_COUNTERS = (
    "RESEARCH_DATA_REQUESTS",
    "API_EXECUTIONS",
    "MEASUREMENT_API_EXECUTIONS",
    "SEARCH_DATA_API_EXECUTIONS",
    "COUNT_ENDPOINT_EXECUTIONS",
    "TARGET_COUNTS_FETCHED",
    "HOST_RECORDS_FETCHED",
    "IP_RECORDS_FETCHED",
    "HOSTS_FETCHED",
    "BANNERS_FETCHED",
    "FACETS_FETCHED",
    "MEASUREMENT_DOWNLOADS",
    "DOWNLOADS",
    "TRIALS",
    "PURCHASES",
    "ACCOUNTS_CREATED",
    "CREDENTIAL_READS",
    "MAILBOX_SEARCHES",
    "ENQUIRIES_SENT",
    "FOLLOW_UPS_SENT",
    "SOURCES_REGISTERED",
    "GOVERNANCE_REVIEWS",
    "THRESHOLDS_REGISTERED",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "RELIABILITY_ASSESSMENTS_CREATED",
    "RELIABILITY_VALUES_ASSIGNED",
    "SCORES",
    "OPPORTUNITY_CHANGES",
    "MODEL_CALLS",
    "EMBEDDINGS",
    "MIGRATIONS",
    "PAIRS_SELECTED",
    "PAIRS_RANKED",
)

URL = re.compile(r"https?://[^\s,()\[\]\"]+")


class ValidationError(RuntimeError):
    """A record says something this mission's rules refuse."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _urls(value: object) -> list[str]:
    """Every URL anywhere inside a nested value."""
    if isinstance(value, str):
        return [u.rstrip(".,;") for u in URL.findall(value)]
    if isinstance(value, list):
        return [u for item in value for u in _urls(item)]
    if isinstance(value, dict):
        return [u for item in value.values() for u in _urls(item)]
    return []


def _provenance_urls(node: object) -> list[str]:
    """URLs sitting under a `*_provenance` key, at any depth."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.endswith("_provenance"):
                found.extend(_urls(value))
            else:
                found.extend(_provenance_urls(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_provenance_urls(item))
    return found


def _walk(node: object):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _check_registry(rule_review: dict) -> None:
    """§44. The decision drives the registry, and it may not be left ambiguous."""
    decision = rule_review["q8_decision"]["decision"]
    if decision not in {"ADOPT", "DECLINE"}:
        raise ValidationError(
            f"the requirement decision is {decision!r}, which is neither ADOPT nor DECLINE"
        )

    requirements = _load(CONTRACT)["requirement_registry"]["requirements"]
    names = [item["name"] for item in requirements]
    rule = "APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME"

    if decision == "ADOPT":
        if names.count(rule) != 1:
            raise ValidationError(
                f"the rule was ADOPTED and appears {names.count(rule)} times in the registry, not once"
            )
        if len(requirements) != 15:
            raise ValidationError(f"ADOPT requires a registry of 15, found {len(requirements)}")
        if rule_review["q8_decision"]["existing_rule_that_would_have_covered_it"] is not None:
            raise ValidationError("a rule was ADOPTED while naming an existing rule that covers it")
    else:
        if rule in names:
            raise ValidationError("the rule was DECLINED and is in the registry anyway")
        if len(requirements) != 14:
            raise ValidationError(f"DECLINE requires a registry of 14, found {len(requirements)}")
        if not rule_review["q8_decision"]["existing_rule_that_would_have_covered_it"]:
            raise ValidationError(
                "a rule was DECLINED without naming the existing rule that covers it"
            )

    # §20. The rule earns its place by being distinct from three named neighbours. A rule
    # adopted while conceding it duplicates one of them is a wording variant.
    for key, neighbour in (
        ("q2_distinct_from_sampling", "SAMPLING_IS_LOAD_BEARING"),
        ("q3_distinct_from_retrievable_frame", "THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME"),
        (
            "q4_distinct_from_time_addressability",
            "APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE",
        ),
    ):
        if decision == "ADOPT" and rule_review[key]["verdict"] != "DISTINCT":
            raise ValidationError(f"the rule was ADOPTED while not distinct from {neighbour}")

    # §1. Adopting one rule must not rename or merge the fourteen that were there.
    before = _load(BASELINE)["requirement_registry_before"]
    if before["count"] != 14:
        raise ValidationError(
            f"the recorded registry count before this mission is {before['count']}, not 14"
        )
    missing = [name for name in before["names_in_order"] if name not in names]
    if missing:
        raise ValidationError(f"existing requirements disappeared from the registry: {missing}")
    if names[: len(before["names_in_order"])] != before["names_in_order"]:
        raise ValidationError("the fourteen existing requirements were reordered or renamed")


def _check_universe(universe: dict) -> None:
    """§5 and §8. An apparatus an earlier mission already evaluated is not a discovery."""
    for item in universe["hits"]:
        name = item["name"]
        classification = item["classification"]
        if name in FROZEN_CONTROLS and classification != "DUPLICATE_EXISTING_APPARATUS":
            raise ValidationError(
                f"{name} is an existing apparatus and is classified {classification}"
            )
        if classification == "NEW_SERIOUS_CANDIDATE" and name in FROZEN_CONTROLS:
            raise ValidationError(
                f"{name} is an existing apparatus counted as a new serious candidate"
            )
        if not str(item.get("reason", "")).strip():
            raise ValidationError(f"{name} carries no classification reason")
        if not str(item.get("basis", "")).strip():
            raise ValidationError(f"{name} carries no basis")

    # A universe that claims to be exhaustive is claiming something a bounded search
    # cannot establish.
    if universe["exhaustiveness"]["claimed"] is not False:
        raise ValidationError("the discovery universe claims to be exhaustive")

    for name in ("Netlas", "ONYPHE", "LeakIX", "Shadowserver"):
        if name not in universe["frozen_controls"]["names"]:
            raise ValidationError(f"{name} is missing from the frozen-control list")


def _check_prescreen(prescreen: dict, ledger: dict) -> tuple[set[str], set[str]]:
    """§10 and §39. Documentation retrievability is a PRE-gate, not a later finding."""
    serious: set[str] = set()
    non_serious: set[str] = set()
    for candidate in prescreen["candidates"]:
        name = candidate["name"]
        verdict = candidate["verdict"]
        retrievable = candidate["first_party_method_docs_retrievable"]
        retrieved = candidate["documents_retrieved"]

        if verdict == "SERIOUS":
            serious.add(name)
            if retrievable is not True:
                raise ValidationError(
                    f"{name} is SERIOUS while its first-party method documentation is not retrievable"
                )
            if retrieved < 1:
                raise ValidationError(f"{name} is SERIOUS on {retrieved} retrieved documents")
            if candidate["active_measurement_plausible"] is not True:
                raise ValidationError(f"{name} is SERIOUS without active-measurement plausibility")
        else:
            non_serious.add(name)
            if verdict != "DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION":
                raise ValidationError(f"{name} carries the unknown prescreen verdict {verdict!r}")
            if retrievable is not False:
                raise ValidationError(
                    f"{name} is recorded as documentation-not-retrievable while its docs are retrievable"
                )
            # A prescreen failure is a fact about this mission's reach. Saying so is what
            # stops a later reader treating it as a finding about the apparatus.
            if not str(candidate.get("what_this_does_not_establish", "")).strip():
                raise ValidationError(
                    f"{name} was rejected at the pre-gate without recording what that does not establish"
                )

    if len(serious) > 6:
        raise ValidationError(f"{len(serious)} serious candidates, over the budget of 6")

    # §9. A candidate cannot be serious on documents nobody fetched.
    per_candidate: dict[str, int] = {}
    for request in ledger["requests"]:
        if request["outcome"] == "RETRIEVED_LOAD_BEARING":
            per_candidate[request["candidate"]] = per_candidate.get(request["candidate"], 0) + 1
    for name in serious:
        if per_candidate.get(name, 0) < 1:
            raise ValidationError(
                f"{name} is SERIOUS and the ledger records no load-bearing document for it"
            )

    if prescreen["no_retry_discipline"]["http_403_retried"] is not False:
        raise ValidationError("a 403 was retried")
    if prescreen["no_retry_discipline"]["headers_varied"] is not False:
        raise ValidationError("headers were varied to defeat a refusal")
    if prescreen["no_retry_discipline"]["anti_bot_measures_bypassed"] is not False:
        raise ValidationError("an anti-bot measure was bypassed")
    if (
        prescreen["no_retry_discipline"][
            "third_party_mirror_or_cache_substituted_for_a_first_party_document"
        ]
        is not False
    ):
        raise ValidationError("a third-party mirror stood in for a first-party document")

    return serious, non_serious


def _check_ledger(ledger: dict) -> set[str]:
    """§9 and §53. Failed retrievals count, and load-bearing quotes must name real ones."""
    requests = ledger["requests"]
    budget = ledger["budget"]
    if len(requests) != budget["used"]:
        raise ValidationError(
            f"the ledger records {len(requests)} requests and reports {budget['used']} used"
        )
    if budget["used"] > budget["maximum_first_party_requests"]:
        raise ValidationError("the first-party document budget was exceeded")
    if budget["used"] + budget["remaining_unspent"] != budget["maximum_first_party_requests"]:
        raise ValidationError("the budget does not add up")

    seen = [request["n"] for request in requests]
    if seen != list(range(1, len(requests) + 1)):
        raise ValidationError("ledger request numbers are not a gapless sequence from 1")

    counts = ledger["outcome_counts"]
    for outcome, key in (
        ("RETRIEVED_LOAD_BEARING", "load_bearing"),
        ("RETRIEVED_NO_LOAD_BEARING_CONTENT", "retrieved_without_load_bearing_content"),
        ("FAILED", "failed"),
    ):
        actual = sum(1 for request in requests if request["outcome"] == outcome)
        if actual != counts[key]:
            raise ValidationError(f"ledger reports {counts[key]} {key} and contains {actual}")
    if sum(counts.values()) != budget["used"]:
        raise ValidationError("the outcome counts do not sum to the requests used")

    # A budget that only counts successes is not a budget (Mission 1.66.2).
    if counts["failed"] < 1 and counts["retrieved_without_load_bearing_content"] < 1:
        raise ValidationError(
            "no unsuccessful retrieval is recorded, which no real search produces"
        )

    for request in requests:
        if request["outcome"] not in {
            "RETRIEVED_LOAD_BEARING",
            "RETRIEVED_NO_LOAD_BEARING_CONTENT",
            "FAILED",
        }:
            raise ValidationError(f"request {request['n']} carries an unknown outcome")
        if not str(request.get("detail", "")).strip():
            raise ValidationError(f"request {request['n']} records no detail")

    if ledger["search_navigation_requests"]["no_gate_closed_by_a_search_summary"] is not True:
        raise ValidationError("the ledger does not assert that no gate rests on a search summary")

    return {
        request["url"] for request in requests if request["outcome"] == "RETRIEVED_LOAD_BEARING"
    }


def _check_package(package: dict, load_bearing_urls: set[str]) -> None:
    """§36, §37 and §38 for one candidate package."""
    name = package["apparatus"]
    gates = package["gates"]

    for gate in MANDATORY_GATES:
        if gate not in gates:
            raise ValidationError(f"{name} has no entry for {gate}")
        status = gates[gate]["status"]
        if status not in ALLOWED_GATE_STATUS:
            raise ValidationError(f"{name} {gate} carries the unknown status {status!r}")

    # §12. A PASS on active measurement needs a quoted first-party statement, because
    # "our database contains Internet services" is not own probing.
    if gates["A1_ACTIVE_MEASUREMENT_PRODUCER"]["status"] == "PASS" and not gates[
        "A1_ACTIVE_MEASUREMENT_PRODUCER"
    ].get("source_says"):
        raise ValidationError(f"{name} passes A1 with no quoted first-party statement")

    a2 = gates["A2_OBSERVATION_ADDRESSABLE_EXPOSURE"]
    discriminator = package["repeated_service_discriminator"]
    answer = discriminator.get("answer") or discriminator.get("answer_at_frame_level")
    if not answer:
        raise ValidationError(f"{name} records no repeated-service discriminator answer")

    # A package may not record a maintained current state and an append-like
    # discriminator at once, whatever the gate status says. The probe found this: setting
    # the discriminator to OBSERVATION_EVENT_APPEND beside a documented real-time-updated
    # database ESCAPED, because the contradiction was only checked on the PASS branch —
    # so a record could carry the append claim while its gate read FAIL, and a later
    # mission reading the discriminator alone would inherit it. `last_seen` renamed an
    # observation event is the §55 failure this closes.
    if a2.get("temporal_object") == "MAINTAINED_SERVICE_STATE" and answer in APPEND_LIKE:
        raise ValidationError(
            f"{name} records a maintained service state and answers {answer} to the "
            "repeated-service discriminator, which cannot both be true"
        )

    if a2["status"] == "PASS":
        # §13 and §14. A timestamp existing is not a history, and a maintained state is
        # the temporal object Mission 1.59 rejected.
        if a2.get("temporal_object") == "MAINTAINED_SERVICE_STATE":
            raise ValidationError(f"{name} passes A2 over a maintained service state")
        if answer not in APPEND_LIKE:
            raise ValidationError(
                f"{name} passes A2 while its repeated-service discriminator answers {answer}"
            )

    a3 = gates["A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE"]
    if a3["status"] == "PASS" and a3.get("exposure_class") not in PERMITTED_EXPOSURE_CLASSES:
        # §15. A provider label saying protocol = ssh is not the identification string.
        raise ValidationError(f"{name} passes A3 with exposure class {a3.get('exposure_class')!r}")

    # §21. The four frames are recorded apart or not at all.
    a5 = gates["A5_FRAME_DOCUMENTED"]
    if a5["status"] in {"PASS", "PARTIAL"}:
        for key in FRAME_KEYS:
            if key not in a5:
                raise ValidationError(f"{name} A5 does not record {key}")
        if a5["status"] == "PASS" and a5["measured_frame"] != a5["retrievable_frame"]:
            raise ValidationError(
                f"{name} passes A5 while its measured and retrievable frames differ"
            )

    # §24. Own-collection plus open-ended external inputs is not a checkable lineage claim.
    a7 = gates["A7_AFFIRMATIVE_MEASUREMENT_LINEAGE"]
    if a7["status"] == "PASS" and a7.get("external_input_classification") in {
        None,
        "NOT_ENUMERATED",
        "UNKNOWN",
    }:
        raise ValidationError(f"{name} passes A7 without an enumerated exception list")

    # §28. Reviewability is classified and never valued.
    if gates["A8_RELIABILITY_REVIEWABLE"].get("reliability_value_assigned") not in (None,):
        raise ValidationError(f"{name} assigns a reliability value")

    slots = package["additional_slots"]
    for slot in (
        "configuration_membership_tcp_22",
        "configuration_time_addressability",
        "configuration_frame_uniformity",
        "sampling",
        "vantage",
        "retention",
        "access",
    ):
        if slot not in slots:
            raise ValidationError(f"{name} has no entry for {slot}")

    membership = slots["configuration_membership_tcp_22"]
    if membership["status"] == "PRESENT" and not membership.get("source_says"):
        # §17. Membership is not inferred from a generic top-ports phrase or another
        # resource's list.
        raise ValidationError(f"{name} records TCP/22 as PRESENT with no quoted port list")

    time_addr = slots["configuration_time_addressability"]
    if time_addr["status"] == "PASS" and not time_addr.get("dated_or_versioned_basis"):
        # §18. A current port list establishes today and binds no window.
        raise ValidationError(
            f"{name} passes configuration time-addressability on an undated basis"
        )

    uniformity = slots["configuration_frame_uniformity"]
    if uniformity["status"] == "HETEROGENEITY_OBSERVED" and "separable" not in uniformity:
        # §19 and §22. Scanner-partition differences are not cosmetic, and merging them
        # silently is the failure the new rule exists to name.
        raise ValidationError(
            f"{name} observes configuration heterogeneity without recording separability"
        )
    if uniformity["status"] == "PASS" and uniformity.get("heterogeneity_observed") is True:
        raise ValidationError(f"{name} passes frame uniformity while observing heterogeneity")

    # §25. "Internet-wide" is marketing until the sampling is documented, and silence
    # stays UNKNOWN rather than becoming a census.
    if slots["sampling"]["status"] == "PASS":
        raise ValidationError(
            f"{name} records sampling as PASS, which this mission never established"
        )

    # §29. Access is recorded and is never the reason for an epistemic verdict.
    if slots["access"].get("used_as_a_disqualifier") is not False:
        raise ValidationError(f"{name} uses its access model as a disqualifier")

    verdict = package["verdict"]
    status = verdict["individual_status"]
    if status not in {
        "INDIVIDUALLY_QUALIFIED",
        "INDIVIDUALLY_NOT_QUALIFIED",
        "INDIVIDUALLY_UNRESOLVED",
    }:
        raise ValidationError(f"{name} carries the unknown verdict {status!r}")
    if verdict.get("point_score_used") is not False:
        raise ValidationError(f"{name} used a point score")

    statuses = {gate: gates[gate]["status"] for gate in MANDATORY_GATES}
    blocking = {gate: value for gate, value in statuses.items() if value != "PASS"}

    # §37. Qualification requires every mandatory gate PASS. PARTIAL blocks. UNKNOWN
    # blocks. A hard FAIL produces NOT_QUALIFIED.
    if status == "INDIVIDUALLY_QUALIFIED" and blocking:
        raise ValidationError(f"{name} is QUALIFIED while {sorted(blocking)} do not PASS")
    if "FAIL" in statuses.values() and status != "INDIVIDUALLY_NOT_QUALIFIED":
        raise ValidationError(f"{name} has a hard FAIL and is not NOT_QUALIFIED")

    decisive = verdict.get("decisive_fail_gate")
    if status == "INDIVIDUALLY_NOT_QUALIFIED":
        if not decisive:
            raise ValidationError(f"{name} is NOT_QUALIFIED and names no decisive gate")
        if statuses.get(decisive) != "FAIL":
            raise ValidationError(
                f"{name} names {decisive} as decisive while that gate reads {statuses.get(decisive)!r}"
            )

    if verdict.get("package_complete") is not True:
        raise ValidationError(f"{name} is not marked complete")

    # §16. A load-bearing fact must name the exact resource, and semantics must not
    # travel between a provider's products.
    if package.get("resource_scope", {}).get("semantics_transferred_between_resources") not in (
        None,
        False,
    ):
        raise ValidationError(f"{name} transfers semantics between resources")

    # §41 and §42. A retrieval summary is not evidence. Every URL a package cites as
    # provenance must be a document the ledger records as actually retrieved.
    for url in _provenance_urls(package):
        if url not in load_bearing_urls:
            raise ValidationError(
                f"{name} cites {url} as provenance and the ledger records no load-bearing retrieval of it"
            )


def _check_count_unit(baseline: dict, packages: list[dict]) -> None:
    """§2. A row count is not a count of distinct addresses."""
    construct = baseline["frozen_construct_unchanged"]
    if construct["count_unit"] != "DISTINCT_IPV4":
        raise ValidationError("the frozen construct no longer counts distinct IPv4 addresses")
    for forbidden in ("ROW_COUNT", "SERVICE_ROW_COUNT", "BANNER_COUNT"):
        if forbidden not in construct["count_unit_must_never_be"]:
            raise ValidationError(f"the construct no longer forbids {forbidden}")

    for package in packages:
        for node in _walk(package):
            if not isinstance(node, dict) or "count_unit" not in node:
                continue
            unit = node["count_unit"]
            if unit == "DISTINCT_IPV4":
                continue
            # A resource whose count unit is undocumented or is a row count cannot carry
            # the construct, so it must not also be claiming protocol-native exposure.
            if node.get("A3_status") in PERMITTED_EXPOSURE_CLASSES:
                raise ValidationError(
                    f"{package['apparatus']} claims protocol-native exposure on a {unit} count"
                )


def _check_qualification(qualification: dict, packages: list[dict], serious: set[str]) -> None:
    """§37, §46 and §58."""
    named = {item["name"] for item in qualification["new_serious_candidates"]}
    if named != serious:
        raise ValidationError(
            f"the roll-up names {sorted(named)} and the prescreen made {sorted(serious)} serious"
        )
    if len(named) != len({package["apparatus"] for package in packages}):
        raise ValidationError(
            "the roll-up and the package set disagree on how many candidates exist"
        )

    by_name = {package["apparatus"]: package for package in packages}
    qualified = 0
    for item in qualification["new_serious_candidates"]:
        package = by_name[item["name"]]
        if item["individual_status"] != package["verdict"]["individual_status"]:
            raise ValidationError(f"{item['name']} has two different verdicts")
        if item.get("decisive_fail_gate") != package["verdict"].get("decisive_fail_gate"):
            raise ValidationError(f"{item['name']} names two different decisive gates")
        if item["individual_status"] == "INDIVIDUALLY_QUALIFIED":
            qualified += 1

    counts = qualification["counts"]
    if counts["new_serious_candidates"] != len(named):
        raise ValidationError("the serious-candidate count does not match the named candidates")
    if counts["new_individually_qualified"] != qualified:
        raise ValidationError("the qualified count does not match the verdicts")

    if qualification["verdict_vocabulary"]["partial_blocks_qualification"] is not True:
        raise ValidationError("the record no longer says PARTIAL blocks qualification")
    if qualification["verdict_vocabulary"]["unknown_blocks_qualification"] is not True:
        raise ValidationError("the record no longer says UNKNOWN blocks qualification")
    if qualification["verdict_vocabulary"]["point_score_used"] is not False:
        raise ValidationError("a point score was used")

    # §47. Individual qualification is where this mission ends.
    for key, value in qualification["no_pair_work_performed"].items():
        if key.startswith("$"):
            continue
        if value not in (0, False):
            raise ValidationError(f"pair work was performed: {key} is {value!r}")

    outcome = qualification["primary_outcome"]
    allowed = {
        "TWO_OR_MORE_NEW_QUALIFIED_APPARATUSES_IDENTIFIED",
        "ONE_NEW_QUALIFIED_APPARATUS_IDENTIFIED",
        "NO_NEW_QUALIFYING_APPARATUS_IDENTIFIED_WITHIN_BOUNDED_SEARCH",
        "NEW_CANDIDATES_BLOCKED_BY_OBSERVATION_ADDRESSABILITY",
        "NEW_CANDIDATES_BLOCKED_BY_PROTOCOL_NATIVE_EXPOSURE",
        "NEW_CANDIDATES_BLOCKED_BY_RETRIEVABLE_FRAME",
        "NEW_CANDIDATES_BLOCKED_BY_CONFIGURATION_ADDRESSABILITY",
        "NEW_CANDIDATES_BLOCKED_BY_CONFIGURATION_HETEROGENEITY",
        "NEW_CANDIDATES_BLOCKED_BY_LINEAGE",
        "NEW_CANDIDATE_DOCUMENTATION_INSUFFICIENT",
        "NEW_SCANNER_DISCOVERY_BLOCKED",
    }
    if outcome not in allowed:
        raise ValidationError(f"the primary outcome {outcome!r} is not one of the defined outcomes")
    if outcome == "TWO_OR_MORE_NEW_QUALIFIED_APPARATUSES_IDENTIFIED" and qualified < 2:
        raise ValidationError("outcome A reported with fewer than two qualified apparatuses")
    if outcome == "ONE_NEW_QUALIFIED_APPARATUS_IDENTIFIED" and qualified != 1:
        raise ValidationError("outcome B reported without exactly one qualified apparatus")
    if outcome == "NO_NEW_QUALIFYING_APPARATUS_IDENTIFIED_WITHIN_BOUNDED_SEARCH" and qualified:
        raise ValidationError("outcome C reported while an apparatus qualified")

    accounting = qualification["mission_accounting"]
    for counter in HARD_ZERO_COUNTERS:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")

    parallel = qualification["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    for key in (
        "onyphe_mailbox_searched",
        "onyphe_gmail_polled",
        "onyphe_reply_read",
        "onyphe_follow_up_sent",
        "onyphe_support_contacted",
        "onyphe_state_changed",
        "netlas_address_decoded",
        "netlas_address_guessed",
        "netlas_enquiry_sent",
        "netlas_state_changed",
    ):
        if parallel[key] is not False:
            raise ValidationError(f"{key} is true, and this mission may not do it")

    if qualification["canonical_mutation_boundary"]["mutations_this_mission"] != 0:
        raise ValidationError("a canonical mutation was recorded")

    if qualification["registry_decision"]["historical_verdicts_edited"] != 0:
        raise ValidationError("a historical verdict was edited")


def _check_readiness(readiness: dict, qualification: dict) -> None:
    """§46 and §48. Readiness counts; it never selects."""
    apparatuses = readiness["apparatuses"]
    qualified = [a for a in apparatuses if a["individual"] == "INDIVIDUALLY_QUALIFIED"]
    if readiness["qualified_apparatus_count"] != len(qualified):
        raise ValidationError("the readiness count does not match the recorded verdicts")
    if readiness["total_apparatus_count"] != len(apparatuses):
        raise ValidationError("the total apparatus count does not match the list")

    ready = readiness["pair_analysis_ready"]
    if ready is not (len(qualified) >= 2):
        raise ValidationError("pair readiness does not follow from the qualified count")
    expected_state = "PAIR_ANALYSIS_READY" if ready else "PAIR_ANALYSIS_NOT_READY"
    if readiness["pair_analysis_state"] != expected_state:
        raise ValidationError("the pair-analysis state contradicts the readiness flag")

    # §48. Ready means two exist. It never means one was chosen.
    for key, value in readiness["no_pair_work_was_performed"].items():
        if key.startswith("$"):
            continue
        if value not in (0, False):
            raise ValidationError(f"pair work appears in the readiness record: {key} is {value!r}")

    construct = readiness["measurement_construct_unchanged"]
    if construct["count_unit"] != "DISTINCT_IPV4":
        raise ValidationError(
            "the readiness record restates the construct with the wrong count unit"
        )
    if construct["relaxed_to_admit_a_candidate"] is not False:
        raise ValidationError("the construct was relaxed to admit a candidate")

    # §5. The four frozen controls stay in the readiness table and keep their verdicts.
    names = {a["name"] for a in apparatuses}
    for required in ("Netlas", "ONYPHE", "LeakIX", "The Shadowserver Foundation"):
        if required not in names:
            raise ValidationError(f"{required} vanished from the readiness table")

    # §45. A new rule does not reach back. Mission 1.66.2's ONYPHE verdict stands exactly
    # as that mission wrote it, and the readiness record for the four existing apparatuses
    # must still say what v3 said.
    previous = {a["name"]: a["individual"] for a in _load(READINESS_V3)["apparatuses"]}
    for apparatus in apparatuses:
        if apparatus.get("new_this_mission"):
            continue
        was = previous.get(apparatus["name"])
        if was is not None and apparatus["individual"] != was:
            raise ValidationError(
                f"{apparatus['name']} was {was} in readiness v3 and is now {apparatus['individual']}, "
                "which is a retrospective change §45 forbids"
            )

    onyphe = _load(ONYPHE_PACKAGE)
    if onyphe["individual_status"]["verdict"] != "INDIVIDUALLY_UNRESOLVED":
        raise ValidationError("Mission 1.66.2's ONYPHE package was edited")

    if (
        qualification["counts"]["new_individually_qualified"]
        != readiness["new_individually_qualified"]
    ):
        raise ValidationError("the roll-up and the readiness record disagree on new qualifications")


def _check_no_reliability_value(packages: list[dict], readiness: dict) -> None:
    """§28. Reviewability is classified. No reliability VALUE is assigned to an apparatus.

    Scoped to the candidate packages and the readiness table, which are the only records
    where an apparatus could be assigned one. The first version of this guard scanned
    every record for a number under a reliability-named key and refused the baseline's
    `reliability_assessments: 4` — a census of rows already in the deployment, which is
    not an assignment and which this mission did not change.

    `testing-strategy.md` §23 for the ninth time: a key-name scan cannot see the
    difference between counting assessments and making one. Fixed by anchoring the guard
    to the records where the forbidden act would occur, rather than by loosening what it
    refuses when it gets there.
    """
    for record in [*packages, readiness]:
        label = record.get("apparatus", record.get("mission", "record"))
        for node in _walk(record):
            if not isinstance(node, dict):
                continue
            for key, value in node.items():
                if "reliability" not in key.lower():
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                raise ValidationError(f"{label} assigns a reliability number: {key} = {value}")


def validate() -> list[dict]:
    records = [_load(path) for path in ORDER]
    baseline, rule_review, universe, prescreen, sonar, shodan, qualification, readiness, ledger = (
        records
    )
    packages = [sonar, shodan]

    _check_registry(rule_review)
    _check_universe(universe)
    load_bearing_urls = _check_ledger(ledger)
    serious, _ = _check_prescreen(prescreen, ledger)

    package_names = {package["apparatus"] for package in packages}
    if package_names != serious:
        raise ValidationError(
            f"packages exist for {sorted(package_names)} and the prescreen made {sorted(serious)} serious"
        )

    for package in packages:
        _check_package(package, load_bearing_urls)

    _check_count_unit(baseline, packages)
    _check_qualification(qualification, packages, serious)
    _check_readiness(readiness, qualification)
    _check_no_reliability_value(packages, readiness)

    if baseline["canonical_baseline"]["drift_from_mission_1_66_2"] != "none":
        raise ValidationError("the baseline records drift")
    if baseline["repository_precondition"]["mission_1_66_2_merged"] is not True:
        raise ValidationError("the baseline does not record Mission 1.66.2 as merged")

    return records


# ------------------------------------------------------------------------ renderers


def _status_row(name: str, status: str) -> str:
    return f"| `{name}` | {status} |"


def render_universe(universe: dict) -> str:
    prescreen = _load(PRESCREEN)
    ledger = _load(LEDGER)
    lines = [
        "# Mission 1.67 — Scanner discovery, prescreen and document ledger",
        "",
        "Generated from `scanner-discovery-universe-v1.json`,",
        "`scanner-candidate-prescreen-v1.json` and",
        "`mission-1.67-documentation-ledger-v1.json`. Do not edit by hand.",
        "",
        "## Search bounds",
        "",
        f"- Apparatus class: **{universe['apparatus_class']['included']}**",
        f"- Discovery hits: **{universe['counts']['total_hits']}**",
        f"- Serious candidates: **{universe['counts']['new_serious_candidates']}** of a budget of "
        f"{ledger['budget']['maximum_serious_candidates']}",
        f"- First-party document requests: **{ledger['budget']['used']}** of "
        f"{ledger['budget']['maximum_first_party_requests']}",
        f"- Search-navigation requests: **{ledger['search_navigation_requests']['count']}**",
        "",
        f"**Exhaustive:** no. {universe['exhaustiveness']['statement']}",
        "",
        "## Discovery universe",
        "",
        "| apparatus | classification | basis |",
        "|---|---|---|",
    ]
    for hit in universe["hits"]:
        lines.append(f"| {hit['name']} | `{hit['classification']}` | `{hit['basis']}` |")

    lines += [
        "",
        "## Prescreen",
        "",
        "A hit becomes a serious candidate only once active measurement is plausible,",
        "first-party method documentation is retrievable, and product relevance is",
        "plausible. The documentation pre-gate runs first.",
        "",
        "| candidate | docs retrievable | documents | verdict |",
        "|---|---|---|---|",
    ]
    for candidate in prescreen["candidates"]:
        lines.append(
            f"| {candidate['name']} | {candidate['first_party_method_docs_retrievable']} "
            f"| {candidate['documents_retrieved']} | `{candidate['verdict']}` |"
        )

    lines += ["", "### What a prescreen rejection does not establish", ""]
    for candidate in prescreen["candidates"]:
        note = candidate.get("what_this_does_not_establish")
        if note:
            lines.append(f"- **{candidate['name']}** — {note}")

    lines += [
        "",
        "## Retrieval-summary guard",
        "",
        "A search summary is not a quotation. This mission met the Mission 1.63 shape",
        "twice, and neither summary was used.",
        "",
    ]
    for instance in ledger["retrieval_summary_guard"]["instances"]:
        lines += [
            f"### {instance['candidate']}",
            "",
            f"*The summary reported:* {instance['what_the_summary_reported']}",
            "",
            f"*The live documents returned:* {instance['what_the_live_documents_returned']}",
            "",
            f"*Reading:* {instance['project_interpretation']}",
            "",
        ]

    lines += [
        "## Document ledger",
        "",
        f"{ledger['outcome_counts']['load_bearing']} carried load-bearing content, "
        f"{ledger['outcome_counts']['retrieved_without_load_bearing_content']} returned nothing "
        f"usable, and {ledger['outcome_counts']['failed']} failed. All of them are counted.",
        "",
        "| n | candidate | url | outcome |",
        "|---|---|---|---|",
    ]
    for request in ledger["requests"]:
        lines.append(
            f"| {request['n']} | {request['candidate']} | `{request['url']}` | `{request['outcome']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def render_rule_review(review: dict) -> str:
    decision = review["q8_decision"]
    lines = [
        "# Apparatus requirement review — configuration uniformity across the frame",
        "",
        "Generated from `apparatus-frame-uniformity-requirement-review-v1.json`.",
        "Do not edit by hand.",
        "",
        f"**Candidate rule:** `{review['candidate_requirement']['name']}`",
        "",
        f"**Decision: {decision['decision']}.** Registry "
        f"{decision['registry_count_before']} to {decision['registry_count_after']}.",
        "",
        "Produced before final candidate selection, because a rule adopted after seeing",
        "which candidates it would eliminate is a rule chosen for its outcome.",
        "",
        "## 1. The failure mode",
        "",
        review["q1_exact_failure_mode"]["answer"],
        "",
        f"*Worked case:* {review['q1_exact_failure_mode']['worked_case']}",
        "",
        f"*Why this is not merely incompleteness:* "
        f"{review['q1_exact_failure_mode']['why_it_is_not_merely_incompleteness']}",
        "",
        "## 2. Distinctness",
        "",
        "| compared against | verdict |",
        "|---|---|",
        f"| `SAMPLING_IS_LOAD_BEARING` | {review['q2_distinct_from_sampling']['verdict']} |",
        f"| `THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME` | "
        f"{review['q3_distinct_from_retrievable_frame']['verdict']} |",
        f"| `APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE` | "
        f"{review['q4_distinct_from_time_addressability']['verdict']} |",
        "",
        f"**Against sampling.** {review['q2_distinct_from_sampling']['reason']}",
        "",
        f"{review['q2_distinct_from_sampling']['ordering']}",
        "",
        f"**Against the retrievable frame.** {review['q3_distinct_from_retrievable_frame']['reason']}",
        "",
        f"**Against time-addressability.** {review['q4_distinct_from_time_addressability']['reason']}",
        "",
        "## 3. Demonstrated, twice, in two shapes",
        "",
        "### First instance — ONYPHE, declared regional partitions",
        "",
    ]
    for quote in review["q5_demonstrated_by_onyphe_evidence"]["source_says"]:
        lines.append(f"> {quote}")
        lines.append(">")
    lines += [
        "",
        f"*Source:* {review['q5_demonstrated_by_onyphe_evidence']['source_says_provenance']}",
        "",
        f"*Reading:* {review['q5_demonstrated_by_onyphe_evidence']['project_interpretation']}",
        "",
        "### Second instance — Shodan, per-step randomisation",
        "",
    ]
    second = review["q6_reusable_across_apparatuses"]["second_instance"]
    for quote in second["source_says"]:
        lines.append(f"> {quote}")
        lines.append(">")
    lines += [
        "",
        f"*Source:* {second['source_says_provenance']}",
        "",
        f"*Reading:* {second['project_interpretation']}",
        "",
        f"**Why two shapes matter.** {second['why_the_two_shapes_matter']}",
        "",
        "## 4. Effect on qualification",
        "",
        review["q7_changes_future_qualification"]["reason"],
        "",
        f"*What it does not do:* {review['q7_changes_future_qualification']['what_it_does_not_do']}",
        "",
        "## 5. The rule as added",
        "",
        f"> {review['rule_text_as_added']['rule']}",
        "",
        f"*No retrospective weakening:* "
        f"{review['q5_demonstrated_by_onyphe_evidence']['not_a_retrospective_finding_against_onyphe']}",
        "",
    ]
    return "\n".join(lines)


def _render_package(package: dict) -> list[str]:
    verdict = package["verdict"]
    lines = [
        f"### {package['apparatus']}",
        "",
        f"**{verdict['individual_status']}** — decisive gate "
        f"`{verdict.get('decisive_fail_gate', 'none')}`.",
        "",
        "| gate | status |",
        "|---|---|",
    ]
    for gate in MANDATORY_GATES:
        lines.append(_status_row(gate, package["gates"][gate]["status"]))
    for slot, entry in package["additional_slots"].items():
        lines.append(_status_row(slot, entry["status"]))
    lines.append("")

    discriminator = package["repeated_service_discriminator"]
    answer = discriminator.get("answer") or discriminator.get("answer_at_frame_level")
    lines += [
        "**Repeated-service discriminator.** Service S at address A:port P is observed",
        "during W and again after W. Can an acquisition restricted to W still recover the",
        f"observation from W? — `{answer}`",
        "",
        f"{discriminator.get('basis', '')}",
        "",
    ]

    lines += ["**What its own documents say.**", ""]
    for gate in MANDATORY_GATES:
        entry = package["gates"][gate]
        quotes = entry.get("source_says")
        if not quotes:
            continue
        if isinstance(quotes, str):
            quotes = [quotes]
        lines.append(f"*{gate}* — {entry['status']}")
        lines.append("")
        for quote in quotes:
            lines.append(f"> {quote}")
            lines.append(">")
        lines.append("")
        if entry.get("project_interpretation"):
            lines.append(f"Reading: {entry['project_interpretation']}")
            lines.append("")
    return lines


def render_qualification(qualification: dict) -> str:
    readiness = _load(READINESS)
    packages = [_load(SONAR), _load(SHODAN)]
    lines = [
        "# Mission 1.67 — Individual apparatus qualification",
        "",
        "Generated from `scanner-individual-qualification-v1.json`, the two candidate",
        "packages and `qualified-apparatus-readiness-v4.json`. Do not edit by hand.",
        "",
        f"**Primary outcome: `{qualification['primary_outcome']}`**",
        "",
        "COMPLETE does not mean QUALIFIED. A well-documented failure is successful",
        "mission output.",
        "",
        "## Verdicts",
        "",
        "| apparatus | verdict | decisive gate |",
        "|---|---|---|",
    ]
    for item in qualification["new_serious_candidates"]:
        lines.append(
            f"| {item['name']} | `{item['individual_status']}` | `{item['decisive_fail_gate']}` |"
        )
    lines += ["", "In one line each:", ""]
    for item in qualification["new_serious_candidates"]:
        lines.append(f"- **{item['name']}** — {item['one_line']}")

    lines += [
        "",
        "## Blocker distribution",
        "",
        "| dimension | candidates |",
        "|---|---|",
    ]
    distribution = qualification["blocker_distribution"]
    for key, value in distribution.items():
        if key.startswith("$") or not isinstance(value, int):
            continue
        lines.append(f"| {key.replace('_', ' ')} | {value} |")
    lines += ["", distribution["note_on_documentation"], ""]

    lines += ["## Packages", ""]
    for package in packages:
        lines.extend(_render_package(package))

    lines += [
        "## Pair readiness",
        "",
        f"Total apparatuses **{readiness['total_apparatus_count']}**, "
        f"qualified **{readiness['qualified_apparatus_count']}**, "
        f"minimum required **{readiness['minimum_required']}**.",
        "",
        f"**{readiness['pair_analysis_state']}**",
        "",
        "| apparatus | verdict | blocking | new |",
        "|---|---|---|---|",
    ]
    for apparatus in readiness["apparatuses"]:
        blocking = ", ".join(apparatus["blocking"]) or "—"
        lines.append(
            f"| {apparatus['name']} | `{apparatus['individual']}` | {blocking} "
            f"| {'yes' if apparatus.get('new_this_mission') else 'no'} |"
        )

    arc = readiness["the_arc_position"]
    lines += [
        "",
        "## Where the arc stands",
        "",
        f"**Target.** {arc['target']}",
        "",
        f"**Distance.** {arc['distance_from_it']}",
        "",
        f"**What this mission added.** {arc['what_this_mission_added']}",
        "",
        f"**The shape that recurred.** {arc['the_shape_that_recurred']}",
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    accounting = qualification["mission_accounting"]
    for counter in (
        "MEASUREMENT_API_EXECUTIONS",
        "COUNT_ENDPOINT_EXECUTIONS",
        "HOSTS_FETCHED",
        "BANNERS_FETCHED",
        "TRIALS",
        "PURCHASES",
        "CREDENTIAL_READS",
        "MAILBOX_SEARCHES",
        "ENQUIRIES_SENT",
        "SOURCES_REGISTERED",
        "RELIABILITY_VALUES_ASSIGNED",
        "MODEL_CALLS",
        "EMBEDDINGS",
        "PAIRS_SELECTED",
    ):
        lines.append(f"| {counter} | {accounting[counter]} |")
    lines.append("")
    return "\n".join(lines)


RENDERERS = {
    UNIVERSE: render_universe,
    RULE_REVIEW: render_rule_review,
    QUALIFICATION: render_qualification,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  scanner discovery: {error}")
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
        print(f"ok       {len(rendered)} discovery documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    qualification, readiness = by_path[QUALIFICATION], by_path[READINESS]
    print(f"outcome  {qualification['primary_outcome']}")
    print(
        f"registry {qualification['registry_decision']['registry_count_before']} -> "
        f"{qualification['registry_decision']['registry_count_after']} "
        f"({qualification['registry_decision']['decision']})"
    )
    print(
        f"pairs    qualified {readiness['qualified_apparatus_count']} of "
        f"{readiness['total_apparatus_count']}, {readiness['pair_analysis_state']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
