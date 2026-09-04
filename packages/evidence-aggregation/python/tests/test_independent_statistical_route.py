"""Mission 1.46 §33. The independence gates, exercised on real-shaped fixtures.

The failure mode this guards is the attractive one: two respectable publishers
of the same number being written up as two independent lines of evidence,
because their hostnames differ. Every fixture below is DISPOSABLE and nothing
here persists a row.

**Both KNOWN_INDEPENDENT and KNOWN_DEPENDENT are exercised with non-empty
fixtures**, so the reporting branch for each actually runs -- the requirement
Missions 1.36.1, 1.42.1 and 1.44 each paid for by shipping a branch no data had
ever entered.

`unittest`, not pytest: `run_python_tests.py` discovers this package.
"""

from __future__ import annotations

import json
import pathlib
import unittest

from sros_contracts import EvidenceDirection, EvidenceIndependenceState
from sros_evidence_aggregation.independence import group_by_independence
from sros_evidence_aggregation.items import EvidenceItem, ItemContribution

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
FEASIBILITY = DOCS / "independent-statistical-route-feasibility-v1.json"
HOLDINGS = DOCS / "statistical-holdings-baseline-v1.json"

WORLD_BANK = "world-bank"
EUROSTAT = "eurostat"
FRED = "fred"


def record() -> dict:
    return json.loads(FEASIBILITY.read_text(encoding="utf-8"))


def holdings() -> dict:
    return json.loads(HOLDINGS.read_text(encoding="utf-8"))


def pair(pair_id: str) -> dict:
    return next(p for p in record()["candidate_pairs"] if p["pair_id"] == pair_id)


def item(evidence_id: str, state: EvidenceIndependenceState, group: str | None = None):
    """One scorable supporting item, shaped like a real statistical Evidence row."""
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=EvidenceDirection.SUPPORTS,
        relevance=1.0,
        directness=1.0,
        reliability=0.6,
        extraction_confidence=1.0,
        independence_state=state,
        independence_group_id=group,
        observed_at=None,
    )


def contributions(*items) -> dict[str, ItemContribution]:
    return {
        element.evidence_id: ItemContribution(
            evidence_id=element.evidence_id,
            direction=element.direction,
            components={
                "relevance": element.relevance,
                "directness": element.directness,
                "reliability": element.reliability,
                "extraction_confidence": element.extraction_confidence,
                "freshness": 1.0,
            },
            scorable=True,
            q=element.reliability,
            limiting_component="reliability",
        )
        for element in items
    }


def groups(*items):
    return group_by_independence(items, contributions(*items), EvidenceDirection.SUPPORTS)


# ================================ the model can hold the target shape (§22)


class TheTargetShapeIsRepresentable(unittest.TestCase):
    """Mission 1.43 proved the arithmetic. This asserts only the SHAPE, which is
    what §22 asks: could a real pair inhabit two groups if one existed."""

    def test_two_known_independent_items_form_two_groups(self):
        result = groups(
            item("a", EvidenceIndependenceState.KNOWN_INDEPENDENT),
            item("b", EvidenceIndependenceState.KNOWN_INDEPENDENT),
        )
        self.assertEqual(len(result), 2)

    def test_two_unknown_items_collapse_into_one_group(self):
        """The state every real Evidence row in this corpus is in."""
        result = groups(
            item("a", EvidenceIndependenceState.UNKNOWN),
            item("b", EvidenceIndependenceState.UNKNOWN),
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].member_evidence_ids), 2)

    def test_two_dependent_items_sharing_a_lineage_form_one_group(self):
        """The FRED case, if it were ever recorded: same lineage, one group."""
        result = groups(
            item("a", EvidenceIndependenceState.KNOWN_DEPENDENT, "world-bank-wdi"),
            item("b", EvidenceIndependenceState.KNOWN_DEPENDENT, "world-bank-wdi"),
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].member_evidence_ids), 2)

    def test_dependent_items_with_different_lineages_are_two_groups(self):
        """Sharing the STATE does not make two records share an origin."""
        result = groups(
            item("a", EvidenceIndependenceState.KNOWN_DEPENDENT, "lineage-x"),
            item("b", EvidenceIndependenceState.KNOWN_DEPENDENT, "lineage-y"),
        )
        self.assertEqual(len(result), 2)

    def test_no_fourth_independence_state_was_invented(self):
        self.assertEqual(
            {member.value for member in EvidenceIndependenceState},
            {"KNOWN_INDEPENDENT", "KNOWN_DEPENDENT", "UNKNOWN"},
        )


# ============================================ what the mission actually found


class DifferentPublisherIsNotIndependence(unittest.TestCase):
    """§ Critical rule. The finding, asserted rather than left to prose."""

    def test_neither_pair_reaches_yes_plus_yes(self):
        for name, gates in record()["two_gate_matrix"].items():
            if name.startswith("$"):
                continue
            self.assertFalse(
                gates["semantic_match"] == "YES" and gates["provenance_independence"] == "YES",
                name,
            )

    def test_no_route_was_selected(self):
        self.assertIsNone(record()["selected_route"])

    def test_the_outcome_is_the_common_upstream_one(self):
        self.assertEqual(
            record()["primary_outcome"], "COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE"
        )

    def test_the_deciding_rule_is_about_lineage_not_hostnames(self):
        rule = record()["the_rule_that_decided_it"].lower()
        self.assertIn("different publishers are not independent evidence", rule)
        self.assertIn("measurement lineage", rule)
        for surface in ("api hostname", "organisation name", "publication page"):
            self.assertIn(surface, rule)


class FredRepublishesWorldBank(unittest.TestCase):
    """§13. Detected from FRED's own page, not assumed."""

    def test_the_pair_is_dependent_republication(self):
        entry = pair("world-bank + fred")
        self.assertEqual(entry["verdict"], "DEPENDENT_REPUBLICATION")
        self.assertEqual(entry["provenance_independence"], "NO")
        self.assertEqual(entry["independence_state_if_forced"], "KNOWN_DEPENDENT")

    def test_semantic_match_is_yes_and_that_is_the_problem(self):
        """The trap: the pair that matches perfectly matches because it is the
        same series. Semantic equivalence alone is not evidence of anything."""
        entry = pair("world-bank + fred")
        self.assertEqual(entry["semantic_match"], "YES")
        self.assertIn("same", entry["semantic_match_note"].lower())

    def test_the_chain_records_world_bank_as_the_producer(self):
        chain = record()["provenance_chains"]["fred/POPTOTDEA647NWDB"]
        stated = " ".join(chain["stated_sources"])
        self.assertIn("Source: World Bank", stated)
        self.assertIn("SP.POP.TOTL", stated)
        self.assertIn("retrieved from FRED", chain["underlying_producer"])


class EurostatSharesTheUpstream(unittest.TestCase):
    """§12. Eurostat is named BY the World Bank as one of its own sources."""

    def test_the_pair_is_common_upstream(self):
        entry = pair("world-bank + eurostat")
        self.assertEqual(entry["verdict"], "COMMON_UPSTREAM_SOURCE")
        self.assertEqual(entry["provenance_independence"], "NO")

    def test_world_bank_names_eurostat_among_its_sources(self):
        chain = record()["provenance_chains"]["world-bank/SP.POP.TOTL"]
        self.assertTrue(
            any("Eurostat" in source for source in chain["stated_sources"]),
            chain["stated_sources"],
        )

    def test_eurostat_compiles_rather_than_produces(self):
        chain = record()["provenance_chains"]["eurostat/population"]
        stated = " ".join(chain["stated_sources"]).lower()
        self.assertIn("collected by eurostat from national statistical institutes", stated)
        self.assertIn("1260/2013", stated)
        self.assertIn("national statistical institutes", chain["underlying_producer"].lower())

    def test_it_also_fails_the_semantic_gate_independently(self):
        """§16 and the population universe. Either alone is disqualifying."""
        entry = pair("world-bank + eurostat")
        self.assertEqual(entry["semantic_match"], "NO")
        note = entry["semantic_match_note"].lower()
        self.assertIn("de facto", note)
        self.assertIn("usually resident", note)
        self.assertIn("midyear", note)
        self.assertIn("1 january", note)


class UnknownStaysUnknown(unittest.TestCase):
    """§6. A load-bearing provenance fact that is unknown keeps the state."""

    def test_the_eurostat_pair_would_have_to_stay_unknown(self):
        entry = pair("world-bank + eurostat")
        self.assertIn("UNKNOWN", entry["independence_state_if_forced"])

    def test_the_held_world_bank_evidence_is_still_unknown_with_no_groups(self):
        held = record()["held_baseline"]["world_bank"]
        self.assertIn("UNKNOWN", held["independence_state"])
        self.assertIn("0 groups", held["independence_state"])


# ================================== the gates that were not the blocker here


class TheOtherGatesWereMeasuredAndReported(unittest.TestCase):
    """Recording which gates did NOT decide is what stops a later mission
    rediscovering them as blockers."""

    def test_geography_mapping_is_not_reported_as_required(self):
        finding = record()["geography"]["finding"]
        self.assertIn("GEOGRAPHY IS NOT THE BLOCKER", finding)
        self.assertIn("STATISTICAL_GEOGRAPHY_MAPPING_REQUIRED is NOT reported", finding)

    def test_no_unit_conversion_was_contemplated(self):
        finding = record()["unit"]["finding"].lower()
        self.assertIn("no fx", finding)
        self.assertIn("no deflator", finding)
        self.assertIn("nothing was converted", finding)

    def test_the_time_basis_mismatch_is_recorded_for_the_eurostat_pair(self):
        self.assertIn("TIME BASIS IS A REAL BLOCKER", record()["temporal"]["finding"])

    def test_revision_is_recorded_separately_from_contradiction(self):
        finding = record()["revision"]["finding"].lower()
        self.assertIn("would not be a contradiction", finding)
        self.assertIn("nothing was recorded as contradicts", finding)


class NothingWasCreated(unittest.TestCase):
    """§27, §28, §29, §30."""

    def test_no_research_data_was_requested(self):
        activity = record()["network_activity"]
        self.assertEqual(activity["RESEARCH_DATA_REQUESTS"], 0)

    def test_the_metadata_call_persisted_no_raw_record(self):
        activity = record()["network_activity"]
        self.assertEqual(activity["METADATA_ONLY"], 1)
        detail = " ".join(activity["detail"])
        self.assertIn("NO observations", detail)
        self.assertIn("no RawRecord persisted", detail)

    def test_eurostat_and_fred_hold_nothing(self):
        held = holdings()["holdings"]
        for source_id in (EUROSTAT, FRED):
            self.assertEqual(held[source_id]["raw_records"], 0, source_id)
            self.assertEqual(held[source_id]["normalized_records"], 0, source_id)

    def test_the_world_bank_holdings_are_the_ones_already_present(self):
        held = holdings()["holdings"][WORLD_BANK]
        self.assertEqual(held["raw_records"], 6)
        self.assertEqual(held["metrics"], 1)
        self.assertEqual(len(holdings()["claims"][WORLD_BANK]), 4)
        self.assertEqual(len(holdings()["evidence"][WORLD_BANK]), 4)

    def test_no_reliability_was_created_for_any_candidate(self):
        reliability = record()["reliability"]
        for source_id in (WORLD_BANK, EUROSTAT, FRED):
            self.assertEqual(reliability[source_id].split(".")[0], "NO_APPLICABLE_ASSESSMENT")
        self.assertIn("NO ASSESSMENT WAS CREATED", reliability["note"])

    def test_the_held_world_bank_evidence_is_non_scorable(self):
        for row in holdings()["evidence"][WORLD_BANK]:
            self.assertIsNone(row["reliability"])
            self.assertEqual(row["independence_state"], "UNKNOWN")
            self.assertIsNone(row["independence_group_id"])

    def test_no_independence_group_was_persisted(self):
        self.assertIn("0 independence groups", record()["architecture_check"]["what_is_missing"])


class NoOverclaim(unittest.TestCase):
    """The sentences this record may not contain."""

    FORBIDDEN = (
        "independently corroborated",
        "two independent sources",
        "confirmed by a second source",
        "cross-validated",
        "eurostat is independent",
        "fred is independent",
    )

    def test_the_record_makes_no_independence_claim(self):
        blob = json.dumps(record()).lower()
        for phrase in self.FORBIDDEN:
            self.assertNotIn(phrase, blob, phrase)

    def test_no_semantic_similarity_machinery_was_used(self):
        """§11. The decision is document-backed and auditable."""
        blob = json.dumps(record()).lower()
        self.assertIn("no llm, embedding or similarity judgement decided any equivalence", blob)

    def test_the_structural_finding_is_not_dressed_up_as_a_route(self):
        alternative = record()["qualified_alternative"]
        self.assertIn("NONE INSIDE THE ELIGIBLE STATISTICAL PORTFOLIO", alternative["finding"])
        self.assertIn("not_recommended_as_a_next_mission", alternative)


class TheClaimArchitectureQuestionWasAnswered(unittest.TestCase):
    """§10. Answered even though no route was selected."""

    def test_source_id_is_proposition_identity_on_the_held_claims(self):
        for claim in holdings()["claims"][WORLD_BANK]:
            facts = claim["proposition_facts"]
            self.assertEqual(facts["source_id"], WORLD_BANK)
            self.assertEqual(facts["proposition"], "source_reported_metric_period_change")

    def test_the_inferred_outcome_was_considered_and_not_reported(self):
        architecture = record()["claim_architecture"]
        self.assertIn(
            "INDEPENDENT_ROUTE_REQUIRES_INFERRED_STATISTICAL_CLAIM is therefore NOT the outcome",
            architecture["which_would_be_required"],
        )

    def test_source_attribution_was_not_proposed_for_deletion(self):
        architecture = record()["claim_architecture"]
        routes = " ".join(architecture["the_two_available_routes"])
        self.assertIn("must NOT be reached by deleting source_id", routes)


if __name__ == "__main__":
    unittest.main()
