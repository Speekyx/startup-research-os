"""Mission 1.36 §27. A prepared question, and the judgement software may not make.

The load-bearing assertions here are negative: **no number sits in any judgement
position, and no adjective ranks a source.** A packet that quietly suggested a
value would be worse than no packet, because it would arrive wearing the
authority of having read the documentation.

Everything else holds the scope arithmetic (three scopes, eight rows, exactly one
scope each), the exclusions that keep reliability from becoming a source
coefficient, and the state that must not have moved.
"""

from __future__ import annotations

import json
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
PACKET = DOCS / "docker-evidence-reliability-review-packet-v1.json"
WORKSHEET = DOCS / "docker-evidence-reliability-review-packet-v1.md"
DEMONSTRATION = DOCS / "scope-architecture-demonstration-v1.json"

SCOPE_FIELDS = (
    "source_id",
    "resource_id",
    "record_kind_id",
    "claim_type",
    "proposition_kind",
)


def packet() -> dict:
    return json.loads(PACKET.read_text(encoding="utf-8"))


def scopes() -> list[dict]:
    return packet()["scopes"]


def _without_comments(value: object) -> object:
    """Strip every `$comment` key, at any depth.

    A `$comment` is where a RULE is written -- *`reliability: null` means NO
    ASSESSMENT EXISTS. It does not mean 0.0, 0.5* -- and a rule may name the
    values it forbids. A FIELD may not. Scanning both together is the
    `testing-strategy.md` §23 mistake, met four times in this repository now, so
    the distinction is drawn once here rather than patched per case.
    """
    if isinstance(value, dict):
        return {k: _without_comments(v) for k, v in value.items() if k != "$comment"}
    if isinstance(value, list):
        return [_without_comments(v) for v in value]
    return value


# ================================================== the scope arithmetic (§0, §1)


class TestTheScopesWereComputedNotAssumed:
    def test_there_are_exactly_three(self) -> None:
        """§0 forbids assuming two scopes because two source families exist."""
        assert packet()["scope_count"] == 3
        assert len(scopes()) == 3

    def test_they_cover_exactly_the_eight_docker_rows(self) -> None:
        assert packet()["evidence_rows_covered"] == 8
        assert sum(s["evidence_count"] for s in scopes()) == 8

    def test_every_row_belongs_to_exactly_one_scope(self) -> None:
        seen: list[str] = []
        for scope in scopes():
            seen.extend(scope["evidence_ids"])
        assert len(seen) == len(set(seen)) == 8

    def test_the_row_count_agrees_with_the_scope_demonstration(self) -> None:
        demo = json.loads(DEMONSTRATION.read_text(encoding="utf-8"))
        assert demo["docker_packet"]["direct_evidence"] == packet()["evidence_rows_covered"]

    def test_every_scope_names_all_five_fields(self) -> None:
        for scope in scopes():
            for field in SCOPE_FIELDS:
                assert str(scope["scope"][field]).strip(), f"{scope['scope']}: {field}"

    def test_the_two_stack_exchange_scopes_differ_only_in_proposition_kind(self) -> None:
        """The mission's sharpest finding: four fields identical, two questions."""
        se = [s["scope"] for s in scopes() if s["scope"]["source_id"] == "stack-exchange"]
        assert len(se) == 2
        a, b = se
        for field in ("source_id", "resource_id", "record_kind_id", "claim_type"):
            assert a[field] == b[field], field
        assert a["proposition_kind"] != b["proposition_kind"]

    def test_signal_type_is_not_part_of_scope_identity(self) -> None:
        """§1. It is reported alongside, and it is not one of the five."""
        for scope in scopes():
            assert "signal_type_id" not in scope["scope"]
            assert scope["signal_types_represented"]
        excluded = " ".join(packet()["contract"]["deliberately_excluded_from_scope_identity"])
        assert "signal_type_id" in excluded

    def test_the_wikimedia_scope_holds_six_rows_under_one_signal_type(self) -> None:
        wiki = next(s for s in scopes() if s["scope"]["source_id"] == "wikimedia-pageviews")
        assert wiki["evidence_count"] == 6
        assert wiki["signal_types_represented"] == ["content_request_change"]


# ============================================ software supplied no judgement (§3)


class TestNoValueWasSuggested:
    """The assertions this file exists for."""

    def test_every_reliability_field_is_null(self) -> None:
        for scope in scopes():
            assert scope["operator_judgement"]["reliability"] is None, scope["scope"]

    def test_every_reviewer_field_is_blank(self) -> None:
        for scope in scopes():
            judgement = scope["operator_judgement"]
            assert judgement["reviewed_by"] is None
            assert judgement["reviewer_rationale"] == ""
            assert judgement["stated_limitation"] == ""
            assert judgement["reviewer_decision"] is None

    def test_no_value_is_suggested_where_a_suggestion_would_live(self) -> None:
        """A recommendation would hide in the RESEARCH content or the judgement,
        not in the contract.

        The contract and the worksheet legitimately quote the values they
        forbid -- *not 0.0, not 0.5*, *no meaning for 0.9 or 0.7*, *"0.5 because
        unknown"* -- and a blanket scan fails on exactly the sentences doing the
        work (`testing-strategy.md` §23, met three times in this repository now).
        So this reads the per-scope findings, failure modes, unresolved
        questions, basis rows and judgement: the places a value would appear if
        software had reached for one. A RULE may name a number; a FINDING may
        not.
        """
        for scope in scopes():
            content = {
                key: scope[key]
                for key in (
                    "measurement_definition",
                    "proposition_definition",
                    "methodology_findings",
                    "failure_modes",
                    "unresolved_questions",
                    "candidate_basis_rows",
                    "authoritative_documents",
                    "operator_judgement",
                )
            }
            suspicious = re.findall(r"(?<![\d.])0\.\d+", json.dumps(_without_comments(content)))
            assert not suspicious, f"{scope['scope']}: {suspicious}"

    def test_the_judgement_block_holds_no_number_at_all(self) -> None:
        for scope in scopes():
            for key, value in scope["operator_judgement"].items():
                assert not isinstance(value, int | float), f"{key} = {value!r}"

    def test_no_adjective_ranks_a_source(self) -> None:
        text = json.dumps(packet()).lower()
        for forbidden in (
            "high reliability",
            "highly reliable",
            "very reliable",
            "low reliability",
            "trustworthy",
            "authoritative source is",
            "we recommend a value",
            "suggested value",
        ):
            assert forbidden not in text, forbidden

    def test_the_scale_carries_no_threshold_labels(self) -> None:
        """§4. The architecture defines no meaning for 0.9 or 0.7."""
        scale = packet()["contract"]["scale"]
        assert "no threshold labels" in scale.lower()
        for label in ("excellent", "good", "medium", "poor"):
            assert label not in json.dumps(packet()).lower(), label

    def test_null_is_documented_as_no_assessment_and_never_a_default(self) -> None:
        assert "UNKNOWN / NO ASSESSMENT" in packet()["contract"]["null_means"]
        assert "does not mean 0.0" in packet()["contract"]["null_means"]

    def test_there_is_no_model_origin(self) -> None:
        """§3. A model may help read documentation and may never be the source."""
        assert packet()["contract"]["closed_origins"] == [
            "HUMAN_REVIEW",
            "DOCUMENTED_METHOD",
            "CALIBRATED_EMPIRICALLY",
        ]
        # Asserted positively rather than by banning the words: the contract
        # names them in order to say they do not exist, and a substring scan
        # cannot tell a rule from a violation.
        statement = packet()["contract"]["there_is_no_model_origin"]
        assert "No MODEL_GUESSED" in statement
        assert "never be the epistemic source" in statement
        for scope in scopes():
            assert scope["operator_judgement"]["origin_if_reviewed"] == "HUMAN_REVIEW"

    def test_human_review_requires_reviewer_limitation_and_basis(self) -> None:
        requires = " ".join(packet()["contract"]["human_review_requires"])
        assert "reviewed_by naming the person" in requires
        assert "stated_limitation" in requires
        assert "document-backed basis" in requires
        assert "NO calibration_dataset_ref" in requires


# ==================================================== the preparation itself (§9, §10)


class TestThePreparationIsUsable:
    def test_every_scope_defines_the_measurement_and_the_proposition(self) -> None:
        """§5. Two different things, neither broadened."""
        for scope in scopes():
            assert len(scope["measurement_definition"]) > 120, scope["scope"]
            assert len(scope["proposition_definition"]) > 120, scope["scope"]

    def test_every_scope_lists_failure_modes_with_the_required_columns(self) -> None:
        """§9's table, per row."""
        for scope in scopes():
            assert scope["failure_modes"], scope["scope"]
            for mode in scope["failure_modes"]:
                assert mode["failure_mode"].strip()
                assert isinstance(mode["supported_by_documentation"], bool)
                assert mode["how_it_could_misrepresent_the_claim"].strip()
                assert mode["mitigation_or_bound"].strip()
                assert mode["residual_unknown"].strip()

    def test_every_scope_names_what_remains_unknown(self) -> None:
        for scope in scopes():
            assert scope["unresolved_questions"], scope["scope"]

    def test_every_scope_carries_at_least_one_candidate_basis_row(self) -> None:
        """§10. A HUMAN_REVIEW assessment needs a document-backed basis, so a
        scope shipped with none could not be reviewed accountably."""
        for scope in scopes():
            assert scope["candidate_basis_rows"], scope["scope"]
            for basis in scope["candidate_basis_rows"]:
                assert basis["document_title"].strip()
                assert basis["retrieved_at"].strip()
                assert basis["summarized_finding"].strip()

    def test_an_unreachable_publisher_is_recorded_as_unreachable(self) -> None:
        """No mirror, no cached copy, no third-party substitute."""
        se = [s for s in scopes() if s["scope"]["source_id"] == "stack-exchange"]
        assert se
        for scope in se:
            assert scope["documentation_status"] == "PARTIAL_PUBLISHER_DOCUMENTATION_UNREACHABLE"
            unreachable = [
                d for d in scope["authoritative_documents"] if d["basis_type"] == "UNREACHABLE"
            ]
            assert unreachable
            assert "No retry with a varied header" in " ".join(
                d["summarized_finding"] for d in scope["authoritative_documents"]
            ) or "No bypass attempted" in " ".join(
                d["summarized_finding"] for d in scope["authoritative_documents"]
            )

    def test_the_retrieved_scope_names_its_documents_and_sections(self) -> None:
        wiki = next(s for s in scopes() if s["scope"]["source_id"] == "wikimedia-pageviews")
        assert wiki["documentation_status"] == "RETRIEVED"
        for document in wiki["authoritative_documents"]:
            assert document["url"].startswith("https://")
            assert document["section"].strip()
            assert document["retrieved_at"] == "2026-09-03"

    def test_acquisition_provenance_is_carried_rather_than_re_acquired(self) -> None:
        """§8. The completeness facts are cited, not re-run."""
        se = next(s for s in scopes() if s["scope"]["source_id"] == "stack-exchange")
        provenance = se["acquisition_provenance"]
        assert provenance["page_size"] == 100
        assert provenance["tagged"] == "docker"
        assert provenance["date_window"] == ["2024-03-01", "2024-03-31"]

    def test_extraction_confidence_is_kept_separate_from_reliability(self) -> None:
        """§12. Different components answering different questions."""
        for scope in scopes():
            separate = scope["separately_known_and_not_reliability"]
            assert "extraction_confidence" in separate
            assert "$comment" in separate
            assert "reliability" not in [k for k in separate if k != "$comment"]


# ======================================================= nothing inherited, nothing moved


class TestNothingWasInheritedOrChanged:
    def test_the_ted_assessment_matches_no_docker_scope(self) -> None:
        """§16. No inheritance, and the packet says so where a reader starts."""
        existing = packet()["existing_assessments_and_why_they_do_not_apply"]
        assert existing["matches_any_docker_scope"] is False
        ted = existing["assessments"]
        assert len(ted) == 1
        for scope in scopes():
            differing = [f for f in SCOPE_FIELDS if ted[0][f] != scope["scope"][f]]
            # Four differ. The fifth, `claim_type`, is shared -- every row here is
            # OBSERVED -- which is exactly why a partial or nearest match must
            # never be permitted. Four mismatches are as final as five.
            assert len(differing) == 4, (scope["scope"], differing)
            assert "claim_type" not in differing
            assert ted[0]["claim_type"] == scope["scope"]["claim_type"] == "OBSERVED"

    def test_no_assessment_was_created(self) -> None:
        assert packet()["outcome"] == "READY_FOR_OPERATOR_RELIABILITY_REVIEW"

    def test_every_scope_still_resolves_to_no_applicable_assessment(self) -> None:
        for scope in scopes():
            status = scope["current_resolver_status"]
            assert status["resolution"] == "NO_APPLICABLE_ASSESSMENT"
            assert status["scorable"] is False
            assert status["reliability_on_evidence_rows"] == ["NULL"]

    def test_reliability_was_not_written_onto_evidence_rows(self) -> None:
        """§18. Resolved late; the column stays NULL by design."""
        for scope in scopes():
            assert scope["current_resolver_status"]["reliability_on_evidence_rows"] == ["NULL"]

    def test_independence_is_untouched(self) -> None:
        """§23. Reliability does not establish independence."""
        for scope in scopes():
            assert scope["separately_known_and_not_reliability"]["independence_state"] == [
                "UNKNOWN"
            ]

    def test_governance_state_appears_nowhere_in_the_scope(self) -> None:
        """§11. A source's approval is not evidence of measurement reliability."""
        text = json.dumps([s["scope"] for s in scopes()])
        for governance in ("APPROVED", "use_profile", "review_version", "PERMITTED"):
            assert governance not in text, governance

    def test_the_docker_packet_is_unchanged(self) -> None:
        demo = json.loads(DEMONSTRATION.read_text(encoding="utf-8"))["docker_packet"]
        assert demo["direct_evidence"] == 8
        assert demo["direct_counting_dimensions"] == ["AUDIENCE_OR_USAGE", "PROBLEM_OR_NEED"]


# ===================================================== the worksheet the operator gets


class TestTheWorksheetIsBlank:
    def _text(self) -> str:
        return WORKSHEET.read_text(encoding="utf-8")

    def test_it_asks_whether_there_is_enough_information_first(self) -> None:
        """§14 question 1, and NO is a real answer with a defined consequence."""
        questions = packet()["worksheet"]["questions"]
        assert "enough documented information" in questions[0]
        assert "leave reliability absent" in questions[1].lower()

    def test_it_requires_the_seven_negative_confirmations(self) -> None:
        text = self._text()
        for confirmation in (
            "a source-quality score",
            "legal or governance approval score",
            '"0.5 because unknown"',
            "model-generated",
            "a calibrated probability",
        ):
            assert confirmation in text, confirmation

    def test_the_blanks_are_actually_blank(self) -> None:
        text = self._text()
        assert "Reliability value in [0.0, 1.0]        ____________" in text
        assert "Reviewer identity                      ____________" in text

    def test_it_warns_against_the_source_coefficient_reading(self) -> None:
        """§2. Never `Stack Exchange reliability = X`."""
        reminders = " ".join(packet()["worksheet"]["reminders"])
        assert "not scoring Stack Exchange or Wikimedia" in reminders
        assert "several different assessments" in reminders

    def test_it_states_that_a_value_does_not_calibrate(self) -> None:
        """§19. Reliability review is not calibration."""
        reminders = " ".join(packet()["worksheet"]["reminders"])
        assert "does not calibrate the aggregation profile" in reminders
        text = self._text()
        assert "stays `UNCALIBRATED`" in text
        assert "does not make production scoring ready" in text

    def test_the_document_promises_no_score_and_no_ranking(self) -> None:
        """§21."""
        text = self._text()
        assert "create an Opportunity score, or permit ranking" in text
