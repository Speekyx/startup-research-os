"""Mission 1.33 §19. The feasibility matrix, and the three questions it keeps apart.

A desk review produces a document, and a document can say anything. What these
tests hold is the structure that makes it checkable: every registered source is
answered, every answer states the grain it was judged on, and **no column is
allowed to imply another**. Right grain is not governance approval, governance
approval is not epistemic suitability, and a dimension may not be assigned
without a warrant written next to it.
"""

from __future__ import annotations

import json
import pathlib

from sros_opportunity import EvidenceDimension
from sros_opportunity.dimensions import DIMENSION_DEFINITIONS

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
MATRIX = DOCS / "commercial-dimension-source-feasibility-v1.json"

VERDICTS = frozenset(
    {
        "FEASIBLE_NOW",
        "FEASIBLE_AFTER_GOVERNANCE_REVIEW",
        "FEASIBLE_AFTER_COLLECTOR_IMPLEMENTATION",
        "FEASIBLE_AFTER_GOVERNANCE_AND_IMPLEMENTATION",
        "WRONG_GRAIN",
        "WRONG_DOMAIN",
        "NO_VALID_COMMERCIAL_DIMENSION",
        "RESTRICTED",
        "TECHNICALLY_BLOCKED",
        "UNKNOWN_REQUIRES_REVIEW",
    }
)


def matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def rows() -> list[dict]:
    return matrix()["sources"]


def catalog() -> dict:
    return json.loads((DOCS / "source-catalog-v1.json").read_text(encoding="utf-8"))


class TestEverySourceIsAnswered:
    """§3. A matrix that skipped the awkward ones would be an argument, not a review."""

    def test_it_covers_exactly_the_registered_sources(self) -> None:
        registered = {s["source_id"] for s in catalog()["sources"]}
        assert {r["source_id"] for r in rows()} == registered

    def test_there_are_twenty_nine_of_them(self) -> None:
        assert len(rows()) == 29
        assert len(catalog()["sources"]) == 29

    def test_every_row_carries_a_verdict_from_the_vocabulary(self) -> None:
        for row in rows():
            assert row["verdict"] in VERDICTS, row["source_id"]

    def test_every_row_states_the_grain_it_was_judged_on(self) -> None:
        """§1. A verdict with no stated identifier is unreviewable."""
        for row in rows():
            grain = row["identifier_grain"]
            assert grain["kind"].strip(), row["source_id"]
            assert grain["example"].strip(), row["source_id"]
            assert len(grain["note"].strip()) > 40, row["source_id"]

    def test_every_row_names_its_primary_blocker(self) -> None:
        for row in rows():
            assert len(row["primary_blocker"].strip()) > 40, row["source_id"]

    def test_the_matrix_records_which_catalog_it_read(self) -> None:
        """The governance columns are copied, so they can go stale. Naming the
        catalog version is what makes that detectable rather than silent."""
        assert matrix()["catalog_version"] == catalog()["catalog_version"]


class TestTheThreeQuestionsStayApart:
    """§2. The whole point of the exercise."""

    def test_right_grain_does_not_imply_governance_approval(self) -> None:
        """The case that proves the columns are independent: a source that can
        name Docker precisely and may not be touched."""
        blocked = [
            r for r in rows() if r["can_identify_docker"] == "YES" and r["verdict"] == "RESTRICTED"
        ]
        assert blocked, "no right-grain-but-restricted source; the distinction is untested"
        for row in blocked:
            assert row["acquisition_status"] == "REFUSED_AT_THE_GATE"

    def test_governance_approval_does_not_imply_epistemic_suitability(self) -> None:
        """The mirror case: authorized, collected, and useless for this subject."""
        useless = [
            r
            for r in rows()
            if r["acquisition_status"] == "AUTHORIZABLE_UNDER_LOCAL_PROFILE"
            and not r["potential_dimensions"]
        ]
        assert useless, "no authorized-but-unusable source; the distinction is untested"
        assert any(r["collector_status"] == "IMPLEMENTED" for r in useless)

    def test_no_row_derives_its_verdict_from_the_other_column(self) -> None:
        """A WRONG_GRAIN verdict must not be recorded merely because a source is
        restricted, and a RESTRICTED verdict must not be recorded merely because
        the grain is wrong. Checked the only way a document can be: the grain
        verdicts carry a grain answer, and the governance verdicts do not depend
        on it."""
        for row in rows():
            if row["verdict"] in ("WRONG_GRAIN", "WRONG_DOMAIN"):
                assert row["can_identify_docker"] in ("NO", "MENTION"), row["source_id"]
            if row["verdict"] == "RESTRICTED":
                assert "GOVERNANCE" in row["primary_blocker"], row["source_id"]

    def test_a_source_with_no_local_review_is_refused_whatever_its_terms_say(self) -> None:
        """ADR-027: approval never transfers between profiles. A source reviewed
        only under the commercial profile is refused at the gate today, and the
        matrix must not present its commercial verdict as a standing."""
        for row in rows():
            if row["local_review"] == "NONE":
                assert row["acquisition_status"] == "REFUSED_AT_THE_GATE", row["source_id"]


class TestADimensionNeedsAWarrant:
    """§11. The column that would otherwise be a wish list."""

    def test_every_named_dimension_exists_in_the_taxonomy(self) -> None:
        """§9 of Mission 1.32 applies here too: no dimension is invented so a
        source has somewhere to go."""
        known = {d.value for d in EvidenceDimension}
        for row in rows():
            for name in row["potential_dimensions"]:
                assert name in known, f"{row['source_id']}: {name}"

    def test_a_row_naming_a_dimension_carries_a_warrant(self) -> None:
        for row in rows():
            if row["potential_dimensions"]:
                assert len(row["epistemic_warrant"].strip()) > 80, row["source_id"]

    def test_a_row_naming_a_dimension_says_what_it_would_not_establish(self) -> None:
        for row in rows():
            if row["potential_dimensions"]:
                assert len(row["would_not_establish"]) >= 3, row["source_id"]

    def test_a_row_naming_no_dimension_claims_no_warrant(self) -> None:
        """The inverse, so an empty dimension list cannot carry prose that reads
        like support for one."""
        for row in rows():
            if not row["potential_dimensions"]:
                assert row["epistemic_warrant"] == "", row["source_id"]

    def test_the_limits_quote_the_dimension_s_own_never_means(self) -> None:
        """A limitation invented for the occasion is weaker than the one the
        taxonomy already committed to."""
        supply = DIMENSION_DEFINITIONS[EvidenceDimension.COMPETITIVE_SUPPLY]
        text = " ".join(
            " ".join(r["would_not_establish"])
            for r in rows()
            if "COMPETITIVE_SUPPLY" in r["potential_dimensions"]
        )
        assert any(phrase.split(",")[0] in text for phrase in supply.never_means)


class TestPriceIsNotWillingnessToPay:
    """§12. The strictest rule in the mission, and the taxonomy already held it."""

    def test_no_source_is_credited_with_willingness_to_pay(self) -> None:
        for row in rows():
            assert "WILLINGNESS_TO_PAY" not in row["potential_dimensions"], row["source_id"]

    def test_the_taxonomy_itself_refuses_the_three_near_misses(self) -> None:
        wtp = DIMENSION_DEFINITIONS[EvidenceDimension.WILLINGNESS_TO_PAY]
        joined = " ".join(wtp.never_means)
        assert "listed price" in joined
        assert "budget line" in joined
        assert "public contract total" in joined

    def test_no_source_is_credited_with_a_buyer_or_a_value_at_this_grain(self) -> None:
        """§13. Procurement observes real buyers and real money, at a category
        grain that is not this subject."""
        for row in rows():
            for forbidden in ("BUYER_OR_BUDGET_EXISTENCE", "ECONOMIC_VALUE", "MARKET_ACTIVITY"):
                assert forbidden not in row["potential_dimensions"], row["source_id"]


class TestABroadCategoryIsNotTheSubject:
    """§9 and §13. The finding the whole mission turns on."""

    def test_the_procurement_sources_cannot_identify_docker(self) -> None:
        for source_id in ("ted-eu", "usaspending"):
            row = next(r for r in rows() if r["source_id"] == source_id)
            assert row["can_identify_docker"] == "NO"
            assert row["verdict"] == "WRONG_GRAIN"
            assert not row["potential_dimensions"]

    def test_ted_is_recorded_as_capable_and_mis_scoped_rather_than_useless(self) -> None:
        """The distinction that makes the recommendation what it is: TED is fully
        built and carries real commercial semantics. It cannot name Docker."""
        row = next(r for r in rows() if r["source_id"] == "ted-eu")
        assert row["collector_status"] == "IMPLEMENTED"
        assert row["acquisition_status"] == "AUTHORIZABLE_UNDER_LOCAL_PROFILE"
        assert "MARKET_ACTIVITY" in row["primary_blocker"]

    def test_a_vendor_name_is_not_the_subject(self) -> None:
        """USAspending could match `Docker, Inc.` as a recipient. The canonical
        registry says the subject is the platform and NOT the company."""
        registry = json.loads(
            (DOCS / "canonical-subject-registry-v1.json").read_text(encoding="utf-8")
        )
        docker = next(s for s in registry["subjects"] if s["subject_id"] == "docker")
        assert "NOT the company" in docker["description"]
        row = next(r for r in rows() if r["source_id"] == "usaspending")
        assert "NOT the company" in row["identifier_grain"]["note"]

    def test_the_canonical_registry_gained_no_identifier(self) -> None:
        """§18. A desk review may not quietly widen the subject."""
        registry = json.loads(
            (DOCS / "canonical-subject-registry-v1.json").read_text(encoding="utf-8")
        )
        docker = next(s for s in registry["subjects"] if s["subject_id"] == "docker")
        assert {i["source_id"] for i in docker["identifiers"]} == {
            "wikimedia-pageviews",
            "stack-exchange",
        }
        assert {s["subject_id"] for s in registry["subjects"]} == {
            "docker",
            "kubernetes",
            "podman",
        }

    def test_no_similarity_mechanism_is_proposed_anywhere(self) -> None:
        """§1. The grain gap is not to be closed by resemblance.

        Scanned over the per-source ROWS rather than the whole file, because the
        artifact's `grain_rule` says the words in order to forbid them and a
        substring scan cannot tell a rule from a violation (`testing-strategy.md`
        §23). Where a mechanism would actually be proposed is a source's own
        grain note or warrant, and that is what this reads.
        """
        text = json.dumps(matrix()["sources"]).lower()
        for forbidden in (
            "embedding",
            "cosine",
            "similarity score",
            "fuzzy match",
            "edit distance",
        ):
            assert forbidden not in text, forbidden
        assert "no similarity, embedding or model matching" in matrix()["grain_rule"]

    def test_the_parked_relation_is_only_ever_named_as_parked(self) -> None:
        """§8 forbids using SAME_PROBLEM_FAMILY. Banning the WORD would have
        failed on the row that names it in order to refuse it, so what is
        asserted is the stronger thing: every mention says it is parked."""
        for row in rows():
            blob = json.dumps(row)
            if "SAME_PROBLEM_FAMILY" in blob:
                assert "PARKED" in blob, row["source_id"]


class TestNothingWasDone:
    """§18 and §20. A desk review changes no state."""

    def test_the_docker_packet_is_untouched(self) -> None:
        report = json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))
        packet = next(p for p in report["packets"] if p.get("canonical_subject_id") == "docker")
        assert packet["size"] == 8
        assert sorted(packet["counting_dimensions"]) == [
            "AUDIENCE_OR_USAGE",
            "PROBLEM_OR_NEED",
        ]
        assert packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        assert packet["scoring_eligible"] == 0

    def test_no_model_call_and_no_new_opportunity(self) -> None:
        totals = json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))[
            "totals"
        ]
        assert totals["model_calls"] == 0
        assert totals["cost_units"] == 0.0
        assert totals["opportunity_hypotheses_generated"] == 0

    def test_the_matrix_asserts_no_authorization(self) -> None:
        """A feasibility verdict is not a permission, and the artifact says so in
        the one place a reader starts."""
        note = matrix()["$comment"]
        assert "Nothing here is an acquisition, an authorization" in note

    def test_the_outcome_is_the_grain_mismatch(self) -> None:
        assert matrix()["outcome"] == "COMMERCIAL_SOURCE_GRAIN_MISMATCH"


class TestTheProseAgreesWithTheMatrix:
    """Two hand-maintained copies of one fact drift, and the drift is found by
    whoever trusted the wrong one (ADR-009, applied to a desk review). The
    document is authored rather than generated, so what is asserted is that its
    §2 table says what the JSON says."""

    def _prose(self) -> str:
        """Whitespace-normalised: these sentences are wrapped, and a line break
        must not decide whether a claim is present."""
        return " ".join(
            (DOCS / "commercial-dimension-source-feasibility-v1.md")
            .read_text(encoding="utf-8")
            .split()
        )

    def _matrix_section(self) -> str:
        """Raw, NOT normalised: the table is read line by line."""
        text = (DOCS / "commercial-dimension-source-feasibility-v1.md").read_text(encoding="utf-8")
        return text.split("## 2. The matrix")[1].split("## 3.")[0]

    def test_every_source_has_exactly_one_row_in_the_table(self) -> None:
        section = self._matrix_section()
        for row in rows():
            lines = [ln for ln in section.splitlines() if ln.startswith(f"| `{row['source_id']}`")]
            assert len(lines) == 1, row["source_id"]

    def test_each_row_states_the_verdict_the_matrix_holds(self) -> None:
        section = self._matrix_section()
        for row in rows():
            line = next(
                ln for ln in section.splitlines() if ln.startswith(f"| `{row['source_id']}`")
            )
            assert row["verdict"] in line, row["source_id"]
            for dimension in row["potential_dimensions"]:
                assert dimension in line, f"{row['source_id']}: {dimension}"

    def test_the_collector_marks_agree(self) -> None:
        section = self._matrix_section()
        for row in rows():
            line = next(
                ln for ln in section.splitlines() if ln.startswith(f"| `{row['source_id']}`")
            )
            assert (row["collector_status"] == "IMPLEMENTED") == ("✔" in line), row["source_id"]

    def test_the_counts_the_prose_states_are_the_counts(self) -> None:
        text = self._prose()
        yes = sum(1 for r in rows() if r["can_identify_docker"] == "YES")
        mention = sum(1 for r in rows() if r["can_identify_docker"] == "MENTION")
        no = sum(1 for r in rows() if r["can_identify_docker"] == "NO")
        assert f"**{yes} YES, {mention} MENTION, {no} NO." in text
        named = sum(1 for r in rows() if r["potential_dimensions"])
        assert f"{named} rows name a dimension" in text.replace("**", "")

    def test_the_prose_states_the_local_review_split(self) -> None:
        """§3's structural fact, which the whole table leans on."""
        text = self._prose()
        without = sum(1 for r in rows() if r["local_review"] == "NONE")
        assert without == 21
        assert "Twenty-one of the twenty-nine sources have no" in text

    def test_the_recommendation_names_no_acquisition_target(self) -> None:
        """§15. A desk review that quietly nominated a source would be an
        acquisition plan wearing a review's title."""
        text = self._prose()
        assert "NO_CURRENT_SOURCE_CAN_CLOSE_DOCKER_COMMERCIAL_DIMENSION" in text
        assert "Multi-Scope Opportunity Evidence Architecture V1" in text
        assert "PRIORITY_1 — none, unconditionally." in text
