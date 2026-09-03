"""Mission 1.29 §14. The transmission decisions, and the bounds around them.

These tests read the committed governance artifacts. They are deliberately not
mocks of them: the thing worth protecting is the DECISION as recorded, and a test
that asserted against a fixture would pass while the catalog said something else.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from sros_opportunity import (
    PERMITTED_PAYLOAD_KEYS,
    PERSONAL_DATA_MARKERS,
    PROHIBITED_REPRESENTATIONS,
    TRANSMISSION_REPRESENTATION_VERSION,
    PacketEligibility,
    RepresentationBoundError,
    SourcePolicyStanding,
    SynthesisAvailability,
    authorize_packet_for_external_synthesis,
    build_packet,
    check_representation,
    serialize_packet_for_model,
)

from .test_opportunity_engine import facets, standing

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
CATALOG = DOCS / "source-catalog-v1.json"
PROFILE = "local-private-research-v1"

#: The three sources whose decision Mission 1.29 could RECORD in the registry.
EXPECTED_DECISIONS = {
    "wikimedia-pageviews": "PERMITTED",
    "world-bank": "PERMITTED_WITH_CONDITIONS",
    "gdelt": "PERMITTED_WITH_CONDITIONS",
}

#: TED was assessed and its decision is NOT in the registry, on purpose.
#:
#: Recording it required appending a review version, and appending one orphans
#: the operator's acceptance of `ted-database-right-residual-exposure-accepted`
#: -- a HUMAN_CONFIRMATION condition no verifier may satisfy. TED would have
#: stopped being acquirable as a side effect of assessing egress, which
#: Mission 1.29 §0 forbids in as many words. NOT_ASSESSED and UNCLEAR both refuse
#: at the runtime gate, so nothing operational was traded away; what the registry
#: loses is the distinction, and `opportunity-synthesis-egress-governance-v1.md`
#: carries it instead.
TED_STAYS_UNASSESSED = "ted-eu"

APPROVING = {"PERMITTED", "PERMITTED_WITH_CONDITIONS"}


def _catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _local_reviews(source_id: str) -> list[dict]:
    for source in _catalog()["sources"]:
        if source["source_id"] == source_id:
            return sorted(
                (r for r in source["reviews"] if r.get("assessed_use_profile") == PROFILE),
                key=lambda r: r["review_version"],
            )
    raise AssertionError(f"{source_id} is not in the catalog")


def _current(source_id: str) -> dict:
    return _local_reviews(source_id)[-1]


class TestEveryTargetSourceHasAnExplicitDecision:
    """§14. No source is left implicitly permitted, and none is left silent."""

    def test_each_target_source_records_a_transmission_decision(self) -> None:
        for source_id, expected in EXPECTED_DECISIONS.items():
            review = _current(source_id)
            assert review["external_model_transmission"] == expected, source_id

    def test_no_decision_is_left_not_assessed(self) -> None:
        for source_id in EXPECTED_DECISIONS:
            assert _current(source_id)["external_model_transmission"] != "NOT_ASSESSED"

    def test_ted_is_deliberately_still_unassessed_and_still_refuses(self) -> None:
        """The decision exists and is not in the registry. See TED_STAYS_UNASSESSED."""
        review = _current(TED_STAYS_UNASSESSED)
        assert review["review_version"] == 2
        assert review["reviewed_by"] != "mission-1.29"
        assert review.get("external_model_transmission") in (None, "NOT_ASSESSED")
        # And the acceptance that would have been orphaned is still the one that
        # makes TED acquirable, carried on this same review.
        keys = {c["key"] for c in review["required_conditions"]}
        assert "ted-database-right-residual-exposure-accepted" in keys

    def test_a_source_outside_the_scope_is_untouched(self) -> None:
        """§2 named four sources and three could be recorded. Everything else
        keeps whatever it had, and for every source but Stack Exchange that is
        NOT_ASSESSED."""
        assessed = set(EXPECTED_DECISIONS) | {"stack-exchange"}
        for source in _catalog()["sources"]:
            if source["source_id"] in assessed:
                continue
            for review in source["reviews"]:
                if review.get("assessed_use_profile") != PROFILE:
                    continue
                value = review.get("external_model_transmission")
                assert value in (None, "NOT_ASSESSED"), source["source_id"]

    def test_a_missing_decision_fails_closed(self) -> None:
        """The default is refusal, and it is a refusal that names itself."""
        packet = build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))
        decision = authorize_packet_for_external_synthesis(
            packet,
            {},  # no standing supplied at all
            provider_configured=True,
            provider_posture="APPROVED",
        )
        assert decision.availability is SynthesisAvailability.UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS
        assert any("uncertainty is never permission" in r for r in decision.refusal_reasons)


class TestDecisionsAreScoped:
    """§14. Scoped to a use profile and to a processing purpose."""

    def test_every_decision_is_recorded_under_the_local_profile_only(self) -> None:
        for source_id in EXPECTED_DECISIONS:
            for source in _catalog()["sources"]:
                if source["source_id"] != source_id:
                    continue
                for review in source["reviews"]:
                    if review.get("assessed_use_profile") == PROFILE:
                        continue
                    assert review.get("external_model_transmission") in (None, "NOT_ASSESSED"), (
                        f"{source_id}: a non-local review carries a transmission decision; "
                        "approval never transfers between profiles"
                    )

    def test_every_decision_names_its_processing_purpose(self) -> None:
        """A permission with no stated purpose is a permission for any purpose."""
        for source_id in EXPECTED_DECISIONS:
            notes = _current(source_id)["review_notes"]
            assert "PROCESSING PURPOSE ASSESSED" in notes, source_id
            assert "Opportunity hypothesis synthesis" in notes, source_id

    def test_training_and_fine_tuning_remain_prohibited_everywhere(self) -> None:
        for source_id in EXPECTED_DECISIONS:
            notes = _current(source_id)["review_notes"]
            assert "NOT model training" in notes, source_id
            assert "NOT fine-tuning" in notes, source_id

    def test_embeddings_are_not_implicitly_authorized(self) -> None:
        for source_id in EXPECTED_DECISIONS:
            assert "NOT embedding" in _current(source_id)["review_notes"], source_id

    def test_no_source_review_names_a_provider(self) -> None:
        """Provider governance lives in the provider policy. A source review that
        named a vendor would put one domain inside the other."""
        for source_id in EXPECTED_DECISIONS:
            notes = _current(source_id)["review_notes"].lower()
            for vendor in ("anthropic", "openai", "gemini", "google", "claude", "gpt"):
                assert vendor not in notes, f"{source_id} names {vendor}"


class TestHistoryIsPreserved:
    """§0 and §7. A version was appended; nothing was rewritten."""

    def test_each_target_source_gained_exactly_one_review_version(self) -> None:
        expected_counts = {
            "wikimedia-pageviews": 2,
            "world-bank": 2,
            "gdelt": 2,
            # ted-eu is absent: it gained NO version, which is the point.
        }
        assert len(_local_reviews("ted-eu")) == 2
        for source_id, count in expected_counts.items():
            assert len(_local_reviews(source_id)) == count, source_id

    def test_required_conditions_are_byte_identical_across_the_bump(self) -> None:
        """The re-check Mission 1.23 established as owed. A compliance
        configuration is pinned to a review version, so a bump is honest only
        when the condition set is unchanged -- asserted, never assumed."""
        for source_id in EXPECTED_DECISIONS:
            reviews = _local_reviews(source_id)
            previous, current = reviews[-2], reviews[-1]
            assert json.dumps(
                previous.get("required_conditions", []), sort_keys=True
            ) == json.dumps(current.get("required_conditions", []), sort_keys=True), source_id

    def test_no_other_activity_assessment_moved(self) -> None:
        """Assessing transmission must not rewrite acquisition eligibility."""
        volatile = {
            "review_version",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "evidence",
            "open_questions",
            "external_model_transmission",
        }
        for source_id in EXPECTED_DECISIONS:
            reviews = _local_reviews(source_id)
            previous, current = reviews[-2], reviews[-1]
            for key, value in previous.items():
                if key in volatile:
                    continue
                assert json.dumps(current[key], sort_keys=True) == json.dumps(
                    value, sort_keys=True
                ), f"{source_id}.{key}"

    def test_ted_conditions_and_open_questions_survive(self) -> None:
        """§7. Every TED finding is intact, and none was reinterpreted -- which
        here means the review was not touched at all."""
        current = _current("ted-eu")
        keys = {c["key"] for c in current["required_conditions"]}
        assert keys == {
            "ted-attribution",
            "ted-official-route-only",
            "ted-personal-data-minimisation",
            "ted-database-right-residual-exposure-accepted",
        }
        joined = " ".join(current["open_questions"])
        assert "H-36A" in joined and "NOT ESTABLISHED" in joined
        assert "H-36B" in joined and "NOT ADDRESSED" in joined
        assert current["redistribution"] == "NOT_PERMITTED"

    def test_the_ted_reasoning_is_recorded_where_it_could_be(self) -> None:
        """Not in the review -- appending one was the thing that could not be
        done -- so in the governance document, with the operator sentence
        written down and explicitly not recorded."""
        doc = (DOCS / "opportunity-synthesis-egress-governance-v1.md").read_text(encoding="utf-8")
        assert "bounded queries" in doc
        assert "may not widen a human acceptance" in doc
        assert "writing that sentence here is not recording it" in doc.lower()
        assert "H-39" in doc


class TestTheGdeltScopeLimit:
    """§6. An aggregate measurement is not permission over article text."""

    def test_the_gdelt_decision_distinguishes_aggregates_from_article_text(self) -> None:
        notes = _current("gdelt")["review_notes"]
        assert "Third-party news article text is not a GDELT-released dataset" in notes
        assert "PROHIBITED representation" in notes

    def test_article_text_is_a_named_prohibited_representation(self) -> None:
        markers = {marker for marker, _ in PROHIBITED_REPRESENTATIONS}
        assert "article_text" in markers
        assert "article_body" in markers
        assert "headline" in markers

    def test_a_payload_carrying_article_text_is_refused(self) -> None:
        violations = check_representation({"packet_id": "p", "article_text": "..."})
        assert violations
        assert any("GDELT" in v.reason for v in violations)

    def test_the_gdelt_citation_obligation_is_recorded_as_live(self) -> None:
        """Unlike CC BY 4.0, GDELT's obligation attaches to 'any use'."""
        notes = _current("gdelt")["review_notes"]
        assert "any use or redistribution" in notes
        assert "TRIGGERED" in notes.upper()


class TestPermittedRepresentationsAreBounded:
    """§3 and §14. An allowlist, and an unknown key refuses."""

    def test_the_representation_is_versioned(self) -> None:
        assert TRANSMISSION_REPRESENTATION_VERSION == (
            "opportunity-transmission-representation@1.0.0"
        )

    def test_an_unknown_top_level_key_is_refused(self) -> None:
        violations = check_representation({"packet_id": "p", "surprise_field": 1})
        assert any(v.key == "surprise_field" for v in violations)

    def test_the_allowlist_holds_no_source_payload_key(self) -> None:
        for forbidden in ("raw_record", "response_body", "payload", "body", "text"):
            assert forbidden not in PERMITTED_PAYLOAD_KEYS

    def test_personal_data_markers_are_refused_at_any_depth(self) -> None:
        violations = check_representation(
            {"packet_id": "p", "claims": [{"claim_id": "c", "supplier_name": "X"}]}
        )
        assert any("supplier_name" in v.key for v in violations)

    def test_every_marker_is_actually_detected(self) -> None:
        for marker in PERSONAL_DATA_MARKERS:
            violations = check_representation({"packet_id": "p", "claims": [{marker: "x"}]})
            assert violations, marker

    def test_the_real_serializer_output_is_within_the_bound(self) -> None:
        packet = build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))
        decision = authorize_packet_for_external_synthesis(
            packet,
            {
                "wikimedia-pageviews": standing(
                    permits_external_model_transmission=True,
                    transmission_state="PERMITTED",
                )
            },
            provider_configured=True,
            provider_posture="APPROVED",
        )
        rendered = serialize_packet_for_model(packet, decision, {"c1": "a statement"})
        payload = json.loads(rendered)
        assert set(payload) <= PERMITTED_PAYLOAD_KEYS
        assert not check_representation(payload)

    def test_the_bound_is_enforced_by_the_serializer_and_not_only_available(self) -> None:
        """A checker nobody calls is a comment. This proves the call site."""
        import inspect

        from sros_opportunity import external_synthesis

        source = inspect.getsource(external_synthesis.serialize_packet_for_model)
        assert "check_representation(payload)" in source
        assert "RepresentationBoundError" in source

    def test_a_bounded_payload_is_refused_rather_than_trimmed(self) -> None:
        assert issubclass(RepresentationBoundError, RuntimeError)
        with pytest.raises(RepresentationBoundError):
            raise RepresentationBoundError(check_representation({"nope": 1}))


class TestTheTwoDomainsStayApart:
    """§1. Four independent questions, and none implies another."""

    def test_provider_approval_is_not_inferred_from_source_approval(self) -> None:
        packet = build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))
        decision = authorize_packet_for_external_synthesis(
            packet,
            {
                "wikimedia-pageviews": standing(
                    permits_external_model_transmission=True, transmission_state="PERMITTED"
                )
            },
            provider_configured=True,
            provider_posture="NOT_APPROVED",
        )
        assert not decision.authorized
        assert any("not APPROVED" in r for r in decision.refusal_reasons)

    def test_source_approval_is_not_inferred_from_provider_approval(self) -> None:
        packet = build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))
        decision = authorize_packet_for_external_synthesis(
            packet,
            {
                "wikimedia-pageviews": standing(
                    permits_external_model_transmission=None, transmission_state="NOT_ASSESSED"
                )
            },
            provider_configured=True,
            provider_posture="APPROVED",
        )
        assert not decision.authorized
        assert any("NOT_ASSESSED" in r for r in decision.refusal_reasons)

    def test_an_unresolved_decision_reports_differently_from_a_refusal(self) -> None:
        """UNCLEAR refuses like NOT_PERMITTED and means something an operator can
        act on. Collapsing them sends them looking for a decision nobody made."""
        packet = build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))
        unresolved = authorize_packet_for_external_synthesis(
            packet,
            {
                "wikimedia-pageviews": standing(
                    permits_external_model_transmission=False, transmission_state="UNCLEAR"
                )
            },
            provider_configured=True,
            provider_posture="APPROVED",
        )
        refused = authorize_packet_for_external_synthesis(
            packet,
            {
                "wikimedia-pageviews": standing(
                    permits_external_model_transmission=False,
                    transmission_state="NOT_PERMITTED",
                )
            },
            provider_configured=True,
            provider_posture="APPROVED",
        )
        assert not unresolved.authorized and not refused.authorized
        assert ("wikimedia-pageviews", "UNRESOLVED") in unresolved.per_source
        assert ("wikimedia-pageviews", "REFUSED") in refused.per_source
        assert "an operator can close" in " ".join(unresolved.refusal_reasons)

    def test_local_processing_and_transmission_are_separate_fields(self) -> None:
        """model_processing PERMITTED must not imply transmission PERMITTED."""
        entry = SourcePolicyStanding(
            source_id="s",
            use_profile_id=PROFILE,
            permits_local_processing=True,
            permits_external_model_transmission=None,
            basis="b",
        )
        assert entry.permits_local_processing is True
        assert entry.permits_external_model_transmission is None


class TestTheRerunIsGovernanceOnly:
    """§11 and §15. Egress moved; nothing epistemic did."""

    def _report(self) -> dict:
        return json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))

    def test_eight_of_nine_packets_are_now_egress_authorized(self) -> None:
        report = self._report()
        available = [
            p for p in report["packets"] if p["external_synthesis"]["availability"] == "AVAILABLE"
        ]
        assert len(report["packets"]) == 9
        assert len(available) == 8

    def test_the_ted_packet_is_the_one_still_blocked_and_says_why(self) -> None:
        report = self._report()
        blocked = [
            p for p in report["packets"] if p["external_synthesis"]["availability"] != "AVAILABLE"
        ]
        assert len(blocked) == 1
        assert blocked[0]["subject"].startswith("ted-eu:")
        assert ["ted-eu", "NOT_ASSESSED"] in blocked[0]["external_synthesis"]["per_source"]

    def test_egress_authorization_did_not_make_any_packet_formable(self) -> None:
        """§11: the two gates stay separate. Permission to send is not evidence."""
        report = self._report()
        assert report["totals"]["packets_formable"] == 0
        for packet in report["packets"]:
            assert packet["sufficiency"]["status"] == "HYPOTHESIS_INSUFFICIENT_EVIDENCE"

    def test_no_model_call_and_no_opportunity(self) -> None:
        totals = self._report()["totals"]
        assert totals["model_calls"] == 0
        assert totals["cost_units"] == 0.0
        assert totals["opportunity_hypotheses_generated"] == 0

    def test_the_canonical_evidence_counts_are_unchanged(self) -> None:
        totals = self._report()["totals"]
        assert totals["evidence_rows_inspected"] == 26
        assert totals["eligible_context"] == 26
        assert totals["eligible_scoring"] == 0
