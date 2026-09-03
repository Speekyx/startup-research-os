"""Mission 1.35 §26. A refusal, and the state it must leave behind.

No relation was established, so what these hold is that the search happened, that
its finding is recorded reproducibly, and that **nothing moved as a result**: the
registry is still empty, Docker's direct dimensions are still two, and no
commercial dimension reached the product through any route.

The most useful assertions here are the ones about what a future reader could
check for themselves — every rejected candidate names its document and its
retrieval date, because *everyone knows Docker is X* is exactly what §23 forbids.
"""

from __future__ import annotations

import json
import pathlib

from sros_opportunity import (
    EvidenceDimension,
    SubjectScopeType,
    load_scope_relations,
    load_subject_registry,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
MAPPING = DOCS / "docker-commercial-scope-mapping-v1.json"
RELATIONS = DOCS / "scope-relation-registry-v1.json"
SUBJECTS = DOCS / "canonical-subject-registry-v1.json"
DEMONSTRATION = DOCS / "scope-architecture-demonstration-v1.json"


def mapping() -> dict:
    return json.loads(MAPPING.read_text(encoding="utf-8"))


class TestTheRegistryIsStillEmpty:
    """§25. The mission's result is that nothing was added."""

    def test_zero_relations_are_recorded(self) -> None:
        assert load_scope_relations(RELATIONS).relations == ()

    def test_zero_relations_in_the_document_too(self) -> None:
        assert json.loads(RELATIONS.read_text(encoding="utf-8"))["relations"] == []

    def test_the_registry_records_that_a_search_happened_and_failed(self) -> None:
        """A registry that is empty because nobody looked and one that is empty
        because somebody looked are different facts."""
        entries = json.loads(RELATIONS.read_text(encoding="utf-8"))["explicitly_not_recorded"]
        mission = [e for e in entries if e.get("reviewed_by") == "mission-1.35"]
        assert len(mission) == 1
        assert "found none" in mission[0]["why"]

    def test_no_docker_to_cpv_link_exists_anywhere(self) -> None:
        """§33 of Mission 1.34 and §3 of this one, still holding."""
        text = RELATIONS.read_text(encoding="utf-8")
        document = json.loads(text)
        for relation in document["relations"]:
            assert "CPV" not in relation.get("broader_scope_id", "")
        assert document["relations"] == []


class TestTheFindingIsReproducible:
    """§23. Another reviewer must be able to reach the same conclusion."""

    def test_the_outcome_is_the_no_relation_one(self) -> None:
        assert mapping()["outcome"] == "NO_AUTHORITATIVE_DOCKER_CATEGORY_RELATION_FOUND"
        assert mapping()["relation_sought"]["broader_scope_id"] is None

    def test_every_candidate_names_a_document_and_a_date(self) -> None:
        for candidate in mapping()["candidates"]:
            assert candidate["document"].strip(), candidate["taxonomy"]
            assert candidate["retrieved_at"] == "2026-09-03", candidate["taxonomy"]

    def test_every_candidate_carries_a_verdict_and_a_reason(self) -> None:
        for candidate in mapping()["candidates"]:
            assert candidate["verdict"].strip(), candidate["taxonomy"]
            assert len(candidate["why"].strip()) > 40, candidate["taxonomy"]

    def test_no_candidate_was_accepted(self) -> None:
        for candidate in mapping()["candidates"]:
            assert not candidate["can_contain_subject_docker"], candidate["taxonomy"]

    def test_the_cpv_finding_is_recorded_under_its_own_name(self) -> None:
        """§7 names the verdict this investigation was allowed to reach."""
        cpv = next(c for c in mapping()["candidates"] if "CPV" in c["taxonomy"])
        assert cpv["verdict"] == "CPV_NOT_SUITABLE_FOR_DIRECT_PRODUCT_RELATION"
        assert cpv["classifies_procurements"] is True
        assert cpv["classifies_products"] is False

    def test_the_cncf_rejection_rests_on_a_countable_fact(self) -> None:
        """The strongest candidate, refused because the map does not contain the
        subject -- not because of a judgement about its authority alone."""
        cncf = next(c for c in mapping()["candidates"] if "CNCF" in c["taxonomy"])
        assert "is not an item in the landscape at all" in cncf["finding"]
        assert "2,512 name fields" in cncf["finding"]

    def test_an_unreachable_source_is_unresolved_rather_than_guessed(self) -> None:
        """Uncertainty is never permission, one level out from source governance."""
        unspsc = next(c for c in mapping()["candidates"] if "UNSPSC" in c["taxonomy"])
        assert unspsc["verdict"] == "UNRESOLVED_SOURCE_UNREACHABLE"
        assert unspsc["can_contain_subject_docker"] is None
        assert unspsc["classifies_products"] is None
        assert "403" in unspsc["finding"]

    def test_the_relation_records_what_it_would_never_have_meant(self) -> None:
        """§1. The boundaries are written down even though no relation exists,
        because the next mission to attempt one starts from them."""
        never = mapping()["relation_sought"]["would_never_have_meant"]
        joined = " ".join(never)
        assert "Docker equals the category" in joined
        assert "buyers" in joined
        assert "demand" in joined


class TestProductIdentityStayedSeparateFromCompanyIdentity:
    """§4. The trap this subject has carried since the registry was written."""

    def test_the_subject_is_the_platform_and_not_the_company(self) -> None:
        registry = load_subject_registry(SUBJECTS)
        docker = next(s for s in registry.subjects if s.subject_id == "docker")
        assert docker.scope_type is SubjectScopeType.PRODUCT
        assert "NOT the company" in docker.description

    def test_the_mapping_refuses_company_evidence_by_name(self) -> None:
        subject = mapping()["subject_under_investigation"]
        assert "Docker, Inc." in subject["is_not"]
        assert "NAICS/PSC" in subject["is_not"]

    def test_the_cncf_company_entry_was_seen_and_excluded(self) -> None:
        """`Docker (member)` is in the landscape. It is the company."""
        cncf = next(c for c in mapping()["candidates"] if "CNCF" in c["taxonomy"])
        assert "Docker (member)" in cncf["finding"]
        assert "is the COMPANY" in cncf["limitations"]


class TestNothingMoved:
    """§12, §13, §27. A taxonomy search changes no evidence."""

    def test_the_canonical_subject_registry_is_untouched(self) -> None:
        registry = load_subject_registry(SUBJECTS)
        assert {s.subject_id for s in registry.subjects} == {"docker", "kubernetes", "podman"}
        docker = next(s for s in registry.subjects if s.subject_id == "docker")
        assert {i.source_id for i in docker.identifiers} == {
            "wikimedia-pageviews",
            "stack-exchange",
        }

    def test_docker_direct_dimensions_are_still_exactly_two(self) -> None:
        """§13. Before and after must be identical."""
        packet = json.loads(DEMONSTRATION.read_text(encoding="utf-8"))["docker_packet"]
        assert packet["direct_counting_dimensions"] == [
            "AUDIENCE_OR_USAGE",
            "PROBLEM_OR_NEED",
        ]

    def test_docker_gained_no_commercial_dimension(self) -> None:
        packet = json.loads(DEMONSTRATION.read_text(encoding="utf-8"))["docker_packet"]
        for commercial in (
            EvidenceDimension.MARKET_ACTIVITY,
            EvidenceDimension.ECONOMIC_VALUE,
            EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE,
            EvidenceDimension.WILLINGNESS_TO_PAY,
        ):
            assert commercial.value not in packet["direct_dimensions"]

    def test_ted_evidence_is_still_unattached(self) -> None:
        """§12. No contextual attachment was attempted, let alone made."""
        demo = json.loads(DEMONSTRATION.read_text(encoding="utf-8"))
        assert demo["docker_packet"]["contextual_evidence"] == 0
        assert demo["docker_packet"]["scope_relations_used"] == 0
        for row in demo["ted_evidence"]:
            assert row["attached_to_docker"] is False

    def test_the_opportunity_preparation_artifact_is_untouched(self) -> None:
        report = json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))
        packet = next(p for p in report["packets"] if p.get("canonical_subject_id") == "docker")
        assert packet["size"] == 8
        assert packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        assert report["totals"]["opportunity_hypotheses_generated"] == 0
        assert report["totals"]["model_calls"] == 0

    def test_the_mission_lists_what_it_did_not_do(self) -> None:
        did_not = " ".join(mapping()["what_was_not_done"])
        for promise in (
            "No ScopeRelation was created",
            "No TED Evidence was attached",
            "No model call",
            "No governance decision",
        ):
            assert promise in did_not, promise


class TestNoInferenceMechanismWasUsed:
    """§21. The relation had to be explainable from documents, or not exist."""

    def test_the_artifact_proposes_no_similarity_mechanism(self) -> None:
        """Scanned over the CANDIDATE rows rather than the whole document,
        because the artifact's `$comment` says these words in order to forbid
        them and a substring scan cannot tell a rule from a violation
        (`testing-strategy.md` §23). A mechanism would be proposed in a
        candidate's finding or basis, and that is what this reads."""
        text = json.dumps(mapping()["candidates"]).lower()
        for forbidden in ("embedding", "cosine", "similarity score", "edit distance"):
            assert forbidden not in text, forbidden

    def test_it_says_so_in_the_place_a_reader_starts(self) -> None:
        note = mapping()["$comment"]
        assert "NO MODEL WAS CALLED" in note
        assert "no fuzzy matching, embedding or similarity of any kind" in note

    def test_the_direction_of_reasoning_is_recorded(self) -> None:
        """§3. Starting from the available commercial evidence and working
        backwards is the failure this mission was shaped to avoid."""
        note = mapping()["$comment"]
        assert "DIRECTION OF REASONING" in note
        assert "NOT 'what evidence would connect Docker" in note
