"""Mission 1.34 §30. Scope boundaries, and every way they could be crossed.

The mission's whole value is a refusal, so most of this file is about what the
architecture will NOT do: a CATEGORY observation does not become a PRODUCT fact,
a relation is required and never inferred, and an absent relation is an answer
rather than a prompt to look harder.

**No network, no database, no model.** The synthetic cases are built here; the
real-corpus assertions read the committed demonstration artifact.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest
from sros_opportunity import (
    ContextRefusalReason,
    EvidenceDimension,
    EvidenceFacets,
    EvidenceSupportRole,
    IndependenceState,
    ObservationScope,
    PacketEligibility,
    ReliabilityStatus,
    ScopedDimension,
    ScopeOrigin,
    ScopeRelation,
    ScopeRelationRegistry,
    ScopeRelationStatus,
    ScopeRelationType,
    ScopeStatus,
    SubjectScopeType,
    admit_evidence,
    build_packet,
    build_scoped_packet,
    evaluate,
    load_scope_relations,
    load_subject_registry,
)
from sros_opportunity.scopes import SCOPE_TYPE_DEFINITIONS

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1] / "sros_opportunity"

SUBJECT_REGISTRY = DOCS / "canonical-subject-registry-v1.json"
SCOPE_RULES = DOCS / "observation-scope-rules-v1.json"
SCOPE_RELATIONS = DOCS / "scope-relation-registry-v1.json"
DEMONSTRATION = DOCS / "scope-architecture-demonstration-v1.json"


def demo() -> dict:
    return json.loads(DEMONSTRATION.read_text(encoding="utf-8"))


def scope(
    scope_id: str,
    scope_type: SubjectScopeType | None = SubjectScopeType.PRODUCT,
    *,
    resolved: bool = True,
    geography: str | None = None,
) -> ObservationScope:
    return ObservationScope(
        scope_type=scope_type if resolved else None,
        scope_id=scope_id,
        display_name=scope_id,
        status=ScopeStatus.RESOLVED if resolved else ScopeStatus.UNDETERMINED,
        origin=ScopeOrigin.HUMAN_REVIEWED if resolved else None,
        source_native_identifiers=(scope_id,),
        basis="a basis stated for the test, as the constructor requires",
        geography=geography,
    )


PRODUCT_SCOPE = scope("subject:docker", SubjectScopeType.PRODUCT)
CATEGORY_SCOPE = scope("ted-eu:CPV-division:90", SubjectScopeType.CATEGORY)
GEOGRAPHY_SCOPE = scope("world-bank:metric-geography:SP.POP.TOTL|DE", SubjectScopeType.GEOGRAPHY)


def facets(
    evidence_id: str = "e1",
    dimensions: frozenset[EvidenceDimension] = frozenset({EvidenceDimension.MARKET_ACTIVITY}),
    bound: str = "a bound the source's own wording supports",
) -> EvidenceFacets:
    return EvidenceFacets(
        evidence_id=evidence_id,
        claim_id="c1",
        source_id="ted-eu",
        source_family="public_procurement",
        use_profile_id="local-private-research-v1",
        extraction_method="observed-signal-restatement@1.4.1",
        claim_type="OBSERVED",
        claim_lifecycle="ACTIVE",
        claim_temporality="EVERGREEN",
        claim_origin="DETERMINISTIC_EXTRACTION",
        direction="SUPPORTS",
        observation_category="UNCATEGORISED",
        evidence_level=1,
        relevance=1.0,
        directness=1.0,
        extraction_confidence=1.0,
        reliability=None,
        reliability_status=ReliabilityStatus.NO_APPLICABLE_ASSESSMENT,
        independence_state=IndependenceState.UNKNOWN,
        independence_group_id=None,
        observed_at=None,
        signal_type_id="procurement_value_contrast",
        dimensions=dimensions,
        dimension_bound=bound,
    )


def registry_with(*relations: ScopeRelation) -> ScopeRelationRegistry:
    return ScopeRelationRegistry(registry_version="test@1.0.0", relations=relations)


DOCKER_WITHIN_CPV90 = ScopeRelation(
    narrower_scope_id="subject:docker",
    narrower_scope_type=SubjectScopeType.PRODUCT,
    broader_scope_id="ted-eu:CPV-division:90",
    broader_scope_type=SubjectScopeType.CATEGORY,
    relation_type=ScopeRelationType.SUBJECT_WITHIN_CATEGORY,
    origin=ScopeOrigin.HUMAN_REVIEWED,
    basis="INVENTED FOR THIS TEST ONLY. No such relation exists in the registry.",
    reviewed_by="a test",
    reviewed_at="2026-09-03T00:00:00+00:00",
)


# ======================================================== the vocabulary itself


class TestScopeTypeVocabulary:
    def test_it_has_exactly_the_four_levels(self) -> None:
        assert {t.value for t in SubjectScopeType} == {
            "PRODUCT",
            "CATEGORY",
            "MARKET",
            "GEOGRAPHY",
        }

    def test_every_level_states_what_it_means_and_what_it_is_not(self) -> None:
        """§1. A type defined only by its position in a hierarchy cannot refuse a
        case; the confusions are the definition's working part."""
        for scope_type in SubjectScopeType:
            definition = SCOPE_TYPE_DEFINITIONS[scope_type]
            assert len(definition.means.strip()) > 80, scope_type
            assert definition.never_means, scope_type

    def test_product_is_not_defined_as_narrower_than_category(self) -> None:
        product = SCOPE_TYPE_DEFINITIONS[SubjectScopeType.PRODUCT]
        assert "narrower" not in product.means.lower()
        assert "bounded, separately identifiable" in product.means

    def test_market_admits_it_has_no_example_here(self) -> None:
        """Nothing was invented so the vocabulary looks complete."""
        market = SCOPE_TYPE_DEFINITIONS[SubjectScopeType.MARKET]
        assert market.example_in_this_repository.startswith("none")

    def test_undetermined_is_a_status_and_not_a_fifth_type(self) -> None:
        assert "UNDETERMINED" not in {t.value for t in SubjectScopeType}
        assert ScopeStatus.UNDETERMINED.value == "UNDETERMINED"


class TestSubjectScopeIsNotGeographicScope:
    """§17. Two vocabularies containing the same word, answering different questions."""

    def test_a_category_may_carry_a_geography_independently(self) -> None:
        located = scope("ted-eu:CPV-division:90", SubjectScopeType.CATEGORY, geography="FR")
        assert located.scope_type is SubjectScopeType.CATEGORY
        assert located.geography == "FR"

    def test_an_absent_geography_is_unasked_and_never_global(self) -> None:
        assert PRODUCT_SCOPE.geography is None
        assert "GLOBAL" not in str(PRODUCT_SCOPE.geography)

    def test_the_definition_names_marketscope_as_the_other_question(self) -> None:
        geography = SCOPE_TYPE_DEFINITIONS[SubjectScopeType.GEOGRAPHY]
        assert any("MarketScope" in phrase for phrase in geography.never_means)

    def test_the_module_defines_no_marketscope_member(self) -> None:
        """Merging them would be one field answering a question that is two."""
        names = {t.value for t in SubjectScopeType}
        for member in ("GLOBAL", "REGION", "COUNTRY", "MULTI_COUNTRY"):
            assert member not in names


# ============================================================ subject identity


class TestSubjectIdentityIsUnchanged:
    def test_the_three_subjects_and_their_identifiers_are_the_same(self) -> None:
        """§20, §29. Adding a level changed no identifier and added no subject."""
        registry = load_subject_registry(SUBJECT_REGISTRY)
        assert {s.subject_id for s in registry.subjects} == {"docker", "kubernetes", "podman"}
        docker = next(s for s in registry.subjects if s.subject_id == "docker")
        assert {i.source_id for i in docker.identifiers} == {
            "wikimedia-pageviews",
            "stack-exchange",
        }

    def test_every_subject_declares_a_level(self) -> None:
        registry = load_subject_registry(SUBJECT_REGISTRY)
        for subject in registry.subjects:
            assert subject.scope_type is SubjectScopeType.PRODUCT

    def test_a_registry_entry_with_no_declared_level_is_refused(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Required with no default, so nothing is classified by whichever
        consumer reads it first. Asserted through the LOADER, which is the path a
        real registry takes."""
        raw = json.loads(SUBJECT_REGISTRY.read_text(encoding="utf-8"))
        for entry in raw["subjects"]:
            entry.pop("scope_type")
        path = tmp_path / "no-levels.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        with pytest.raises(KeyError, match="scope_type"):
            load_subject_registry(path)

    def test_the_registry_records_no_parent_for_any_subject(self) -> None:
        """§33. A level is not a parent, and no Docker category was invented."""
        raw = json.loads(SUBJECT_REGISTRY.read_text(encoding="utf-8"))
        text = json.dumps(raw)
        for forbidden in ("parent", "broader", "within", "contains"):
            assert f'"{forbidden}"' not in text, forbidden


# ============================================================ the relation model


class TestRelationsAreDrawnAndNeverDerived:
    def test_the_shipped_registry_is_empty(self) -> None:
        """§29, §33. The result, not an oversight."""
        relations = load_scope_relations(SCOPE_RELATIONS)
        assert relations.relations == ()

    def test_the_registry_says_why_it_is_empty(self) -> None:
        raw = json.loads(SCOPE_RELATIONS.read_text(encoding="utf-8"))
        assert raw["relations"] == []
        assert any(
            "CPV-division:90" in entry["would_be"] for entry in raw["explicitly_not_recorded"]
        )

    def test_a_relation_requires_a_basis(self) -> None:
        with pytest.raises(ValueError, match="no basis"):
            ScopeRelation(
                narrower_scope_id="a",
                narrower_scope_type=SubjectScopeType.PRODUCT,
                broader_scope_id="b",
                broader_scope_type=SubjectScopeType.CATEGORY,
                relation_type=ScopeRelationType.SUBJECT_WITHIN_CATEGORY,
                origin=ScopeOrigin.HUMAN_REVIEWED,
                basis="   ",
                reviewed_by="somebody",
                reviewed_at="2026-09-03",
            )

    def test_a_human_reviewed_relation_names_the_human(self) -> None:
        with pytest.raises(ValueError, match="nobody named"):
            ScopeRelation(
                narrower_scope_id="a",
                narrower_scope_type=SubjectScopeType.PRODUCT,
                broader_scope_id="b",
                broader_scope_type=SubjectScopeType.CATEGORY,
                relation_type=ScopeRelationType.SUBJECT_WITHIN_CATEGORY,
                origin=ScopeOrigin.HUMAN_REVIEWED,
                basis="read two pages",
                reviewed_by="",
                reviewed_at="2026-09-03",
            )

    def test_endpoint_types_are_enforced_by_relation_type(self) -> None:
        with pytest.raises(ValueError, match="cannot take a"):
            ScopeRelation(
                narrower_scope_id="a",
                narrower_scope_type=SubjectScopeType.CATEGORY,
                broader_scope_id="b",
                broader_scope_type=SubjectScopeType.CATEGORY,
                relation_type=ScopeRelationType.SUBJECT_WITHIN_CATEGORY,
                origin=ScopeOrigin.SOURCE_NATIVE,
                basis="a basis",
                reviewed_by="",
                reviewed_at="",
            )

    def test_a_scope_cannot_contain_itself(self) -> None:
        with pytest.raises(ValueError, match="cannot contain itself"):
            ScopeRelation(
                narrower_scope_id="same",
                narrower_scope_type=SubjectScopeType.PRODUCT,
                broader_scope_id="same",
                broader_scope_type=SubjectScopeType.CATEGORY,
                relation_type=ScopeRelationType.SUBJECT_WITHIN_CATEGORY,
                origin=ScopeOrigin.SOURCE_NATIVE,
                basis="a basis",
                reviewed_by="",
                reviewed_at="",
            )

    def test_there_is_no_model_inferred_origin(self) -> None:
        """§5. Not in this enum, and not anywhere in the mission."""
        assert {o.value for o in ScopeOrigin} == {
            "SOURCE_NATIVE",
            "HUMAN_REVIEWED",
            "DETERMINISTIC_REGISTRY",
        }

    def test_relations_are_not_transitive(self) -> None:
        """§4. Product-in-category and category-in-market do not make
        product-in-market."""
        market = scope("market:developer-tooling", SubjectScopeType.MARKET)
        category_in_market = ScopeRelation(
            narrower_scope_id=CATEGORY_SCOPE.scope_id,
            narrower_scope_type=SubjectScopeType.CATEGORY,
            broader_scope_id=market.scope_id,
            broader_scope_type=SubjectScopeType.MARKET,
            relation_type=ScopeRelationType.CATEGORY_WITHIN_MARKET,
            origin=ScopeOrigin.HUMAN_REVIEWED,
            basis="invented for this test",
            reviewed_by="a test",
            reviewed_at="2026-09-03",
        )
        relations = registry_with(DOCKER_WITHIN_CPV90, category_in_market)
        assert relations.relation_between(PRODUCT_SCOPE, CATEGORY_SCOPE) is not None
        assert relations.relation_between(CATEGORY_SCOPE, market) is not None
        assert relations.relation_between(PRODUCT_SCOPE, market) is None

    def test_a_withdrawn_relation_licenses_nothing(self) -> None:
        withdrawn = ScopeRelation(
            narrower_scope_id="subject:docker",
            narrower_scope_type=SubjectScopeType.PRODUCT,
            broader_scope_id="ted-eu:CPV-division:90",
            broader_scope_type=SubjectScopeType.CATEGORY,
            relation_type=ScopeRelationType.SUBJECT_WITHIN_CATEGORY,
            origin=ScopeOrigin.HUMAN_REVIEWED,
            basis="withdrawn",
            reviewed_by="a test",
            reviewed_at="2026-09-03",
            status=ScopeRelationStatus.WITHDRAWN,
        )
        assert registry_with(withdrawn).relation_between(PRODUCT_SCOPE, CATEGORY_SCOPE) is None


# ================================================================== the gate


class TestTheGateFailsClosed:
    """§15. Six conditions, and absence is refusal rather than a search."""

    def test_a_category_row_with_no_relation_is_refused(self) -> None:
        """THE demonstration case. TED offered to Docker, nothing connecting them."""
        decision = admit_evidence(
            facets(),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(),
            governance_permits_processing=True,
        )
        assert not decision.ok
        assert decision.refusal_reason == ContextRefusalReason.NO_PERMITTED_RELATION
        assert "no ACTIVE reviewed relation" in decision.detail

    def test_an_undetermined_evidence_scope_is_refused(self) -> None:
        decision = admit_evidence(
            facets(),
            scope("gdelt:lexical-term:ENGLISH|climate", resolved=False),
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        )
        assert decision.refusal_reason == ContextRefusalReason.SCOPE_UNDETERMINED

    def test_an_undetermined_opportunity_scope_is_refused(self) -> None:
        decision = admit_evidence(
            facets(),
            CATEGORY_SCOPE,
            scope("subject:mystery", resolved=False),
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        )
        assert decision.refusal_reason == ContextRefusalReason.OPPORTUNITY_SCOPE_UNDETERMINED

    def test_governance_is_a_separate_gate_a_relation_cannot_open(self) -> None:
        """§28. A scope relation is not a permission."""
        decision = admit_evidence(
            facets(),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=False,
        )
        assert decision.refusal_reason == ContextRefusalReason.GOVERNANCE_NOT_ESTABLISHED

    def test_a_contextual_row_with_no_dimension_is_refused(self) -> None:
        decision = admit_evidence(
            facets(dimensions=frozenset(), bound=""),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        )
        assert decision.refusal_reason == ContextRefusalReason.NO_DIMENSION

    def test_a_direct_row_with_no_dimension_is_admitted(self) -> None:
        """Mission 1.32 put exactly one dimensionless row in the Docker packet on
        purpose. The dimension clause is a CONTEXT condition."""
        decision = admit_evidence(
            facets(dimensions=frozenset(), bound=""),
            PRODUCT_SCOPE,
            PRODUCT_SCOPE,
            registry_with(),
            governance_permits_processing=True,
        )
        assert decision.ok
        assert decision.admitted is not None
        assert decision.admitted.role is EvidenceSupportRole.DIRECT_SUBJECT_EVIDENCE
        assert decision.admitted.scoped_dimensions == ()

    def test_provenance_is_enforced_upstream_rather_than_here(self) -> None:
        """§15's sixth clause. The gate does not re-check it, because two
        constructors make it unreachable -- and this asserts both, so the claim
        that it is covered is checked rather than asserted in a comment."""
        with pytest.raises(ValueError, match="dimensions carried with no bound"):
            facets(bound="  ")
        with pytest.raises(ValueError, match="RESOLVED with no basis"):
            ObservationScope(
                scope_type=SubjectScopeType.CATEGORY,
                scope_id="x",
                display_name="x",
                status=ScopeStatus.RESOLVED,
                origin=ScopeOrigin.SOURCE_NATIVE,
                source_native_identifiers=("x",),
                basis="   ",
            )

    def test_a_relation_admits_it_as_context_and_never_as_direct(self) -> None:
        decision = admit_evidence(
            facets(),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        )
        assert decision.ok
        assert decision.admitted is not None
        assert decision.admitted.role is EvidenceSupportRole.BROADER_SCOPE_CONTEXT
        assert not decision.admitted.role.is_direct
        assert decision.admitted.admitting_relation is DOCKER_WITHIN_CPV90

    def test_a_geography_row_takes_the_geographic_role(self) -> None:
        edge = ScopeRelation(
            narrower_scope_id=PRODUCT_SCOPE.scope_id,
            narrower_scope_type=SubjectScopeType.PRODUCT,
            broader_scope_id=GEOGRAPHY_SCOPE.scope_id,
            broader_scope_type=SubjectScopeType.GEOGRAPHY,
            relation_type=ScopeRelationType.SCOPE_WITHIN_GEOGRAPHY,
            origin=ScopeOrigin.HUMAN_REVIEWED,
            basis="invented for this test",
            reviewed_by="a test",
            reviewed_at="2026-09-03",
        )
        decision = admit_evidence(
            facets(),
            GEOGRAPHY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(edge),
            governance_permits_processing=True,
        )
        assert decision.admitted is not None
        assert decision.admitted.role is EvidenceSupportRole.GEOGRAPHIC_CONTEXT

    def test_a_matching_scope_is_direct_with_no_relation(self) -> None:
        decision = admit_evidence(
            facets(),
            PRODUCT_SCOPE,
            PRODUCT_SCOPE,
            registry_with(),
            governance_permits_processing=True,
        )
        assert decision.admitted is not None
        assert decision.admitted.role.is_direct
        assert decision.admitted.admitting_relation is None

    def test_two_undetermined_scopes_are_never_the_same_scope(self) -> None:
        a = scope("x", resolved=False)
        b = scope("x", resolved=False)
        assert not a.describes_same_scope_as(b)


# ================================================== the laundering §16 forbids


class TestScopeLaundering:
    """§7, §16, §25. Every one of these must remain impossible."""

    def _context(self, dimension: EvidenceDimension):
        decision = admit_evidence(
            facets(dimensions=frozenset({dimension})),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        )
        assert decision.admitted is not None
        return build_scoped_packet(PRODUCT_SCOPE, "subject:docker", (decision.admitted,))

    def test_category_market_activity_never_becomes_product_market_activity(self) -> None:
        packet = self._context(EvidenceDimension.MARKET_ACTIVITY)
        assert packet.direct_dimensions == frozenset()
        assert packet.direct_counting_dimensions == frozenset()
        assert "ted-eu:CPV-division:90" in packet.contextual_dimensions_by_scope

    def test_category_economic_value_never_becomes_product_value(self) -> None:
        packet = self._context(EvidenceDimension.ECONOMIC_VALUE)
        assert EvidenceDimension.ECONOMIC_VALUE not in packet.direct_dimensions

    def test_category_buyer_existence_never_becomes_product_buyer_existence(self) -> None:
        packet = self._context(EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE)
        assert EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE not in packet.direct_dimensions

    def test_the_packet_offers_no_union_of_direct_and_contextual(self) -> None:
        """The union IS the sentence *Docker supports MARKET_ACTIVITY*, and it
        must not be one attribute access away."""
        packet = self._context(EvidenceDimension.MARKET_ACTIVITY)
        for name in dir(packet):
            if name.startswith("_"):
                continue
            value = getattr(packet, name)
            if isinstance(value, frozenset) and value:
                assert EvidenceDimension.MARKET_ACTIVITY not in value, name

    def test_a_contextual_dimension_cannot_be_read_without_its_scope(self) -> None:
        packet = self._context(EvidenceDimension.MARKET_ACTIVITY)
        scoped = next(iter(packet.contextual_dimensions_by_scope.values()))[0]
        assert isinstance(scoped, ScopedDimension)
        assert scoped.scope.scope_id == "ted-eu:CPV-division:90"
        assert scoped.role is EvidenceSupportRole.BROADER_SCOPE_CONTEXT

    def test_the_statement_names_the_scope_and_denies_the_subject(self) -> None:
        """§26's wording contract."""
        packet = self._context(EvidenceDimension.MARKET_ACTIVITY)
        statement = packet.statements()[0]
        assert "ted-eu:CPV-division:90" in statement
        assert "It is not observed of the subject." in statement

    def test_the_limitation_says_the_broader_scope_establishes_nothing_inside_it(
        self,
    ) -> None:
        packet = self._context(EvidenceDimension.MARKET_ACTIVITY)
        limitation = packet.limitations()[0]
        assert "NOT observed of the subject" in limitation

    def test_a_direct_role_cannot_be_hand_built_at_a_category_scope(self) -> None:
        with pytest.raises(ValueError, match="Direct means the row observes the subject"):
            ScopedDimension(
                dimension=EvidenceDimension.MARKET_ACTIVITY,
                scope=CATEGORY_SCOPE,
                role=EvidenceSupportRole.DIRECT_SUBJECT_EVIDENCE,
            )

    def test_a_dimension_cannot_be_carried_at_an_undetermined_scope(self) -> None:
        with pytest.raises(ValueError, match="UNDETERMINED scope"):
            ScopedDimension(
                dimension=EvidenceDimension.MARKET_ACTIVITY,
                scope=scope("x", resolved=False),
                role=EvidenceSupportRole.BROADER_SCOPE_CONTEXT,
            )


class TestWillingnessToPayCannotBeCreated:
    """§18. Multi-scope context does not manufacture what Mission 1.33 found absent."""

    def test_no_context_role_produces_willingness_to_pay(self) -> None:
        for dimension in (
            EvidenceDimension.ECONOMIC_VALUE,
            EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE,
            EvidenceDimension.MARKET_ACTIVITY,
        ):
            decision = admit_evidence(
                facets(dimensions=frozenset({dimension})),
                CATEGORY_SCOPE,
                PRODUCT_SCOPE,
                registry_with(DOCKER_WITHIN_CPV90),
                governance_permits_processing=True,
            )
            assert decision.admitted is not None
            names = {s.dimension for s in decision.admitted.scoped_dimensions}
            assert EvidenceDimension.WILLINGNESS_TO_PAY not in names

    def test_a_dimension_is_carried_verbatim_and_never_translated(self) -> None:
        """No mapping table converts one dimension into another at any scope."""
        decision = admit_evidence(
            facets(dimensions=frozenset({EvidenceDimension.ECONOMIC_VALUE})),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        )
        assert decision.admitted is not None
        assert {s.dimension for s in decision.admitted.scoped_dimensions} == {
            EvidenceDimension.ECONOMIC_VALUE
        }

    def test_the_taxonomy_still_refuses_the_three_near_misses(self) -> None:
        from sros_opportunity.dimensions import DIMENSION_DEFINITIONS

        wtp = DIMENSION_DEFINITIONS[EvidenceDimension.WILLINGNESS_TO_PAY]
        joined = " ".join(wtp.never_means)
        assert "listed price" in joined
        assert "budget line" in joined
        assert "public contract total" in joined


# ====================================================== backward compatibility


class TestNothingExistingMoved:
    """§10, §11. The mission is additive or it is a regression."""

    def test_the_legacy_packet_procedure_is_unchanged(self) -> None:
        from sros_opportunity.packet import PACKET_PROCEDURE_VERSION
        from sros_opportunity.sufficiency import SUFFICIENCY_PROCEDURE_VERSION, SUFFICIENCY_V1

        assert PACKET_PROCEDURE_VERSION == "opportunity-evidence-packet@1.0.0"
        assert SUFFICIENCY_PROCEDURE_VERSION == "opportunity-sufficiency@1.0.0"
        assert SUFFICIENCY_V1.min_eligible_rows == 2
        assert SUFFICIENCY_V1.min_distinct_dimensions == 2

    def test_the_docker_packet_is_still_formable_on_the_same_rows(self) -> None:
        report = json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))
        packet = next(p for p in report["packets"] if p.get("canonical_subject_id") == "docker")
        assert packet["size"] == 8
        assert packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        assert sorted(packet["counting_dimensions"]) == [
            "AUDIENCE_OR_USAGE",
            "PROBLEM_OR_NEED",
        ]

    def test_the_direct_half_reproduces_the_legacy_packet(self) -> None:
        """The compatibility claim, asserted rather than assumed."""
        report = json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))
        legacy = next(p for p in report["packets"] if p.get("canonical_subject_id") == "docker")
        scoped = demo()["docker_packet"]
        assert scoped["direct_evidence"] == legacy["size"]
        assert scoped["direct_counting_dimensions"] == sorted(legacy["counting_dimensions"])

    def test_contextual_rows_cannot_reach_the_sufficiency_input(self) -> None:
        """§10. A category row must not satisfy a rule written for direct evidence."""
        direct = admit_evidence(
            facets("e-direct", frozenset({EvidenceDimension.PROBLEM_OR_NEED})),
            PRODUCT_SCOPE,
            PRODUCT_SCOPE,
            registry_with(),
            governance_permits_processing=True,
        ).admitted
        context = admit_evidence(
            facets("e-context", frozenset({EvidenceDimension.MARKET_ACTIVITY})),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        ).admitted
        assert direct is not None and context is not None
        packet = build_scoped_packet(PRODUCT_SCOPE, "subject:docker", (direct, context))
        assert packet.direct_counting_dimensions == frozenset({EvidenceDimension.PROBLEM_OR_NEED})
        assert len(packet.direct_counting_dimensions) == 1

    def test_a_scoped_packet_is_deterministic(self) -> None:
        admitted = admit_evidence(
            facets(),
            PRODUCT_SCOPE,
            PRODUCT_SCOPE,
            registry_with(),
            governance_permits_processing=True,
        ).admitted
        assert admitted is not None
        first = build_scoped_packet(PRODUCT_SCOPE, "subject:docker", (admitted,))
        second = build_scoped_packet(PRODUCT_SCOPE, "subject:docker", (admitted,))
        assert first.packet_id == second.packet_id

    def test_the_role_is_part_of_packet_identity(self) -> None:
        """The same rows in different roles support different sentences, so they
        are a different packet."""
        direct = admit_evidence(
            facets(),
            PRODUCT_SCOPE,
            PRODUCT_SCOPE,
            registry_with(),
            governance_permits_processing=True,
        ).admitted
        context = admit_evidence(
            facets(),
            CATEGORY_SCOPE,
            PRODUCT_SCOPE,
            registry_with(DOCKER_WITHIN_CPV90),
            governance_permits_processing=True,
        ).admitted
        assert direct is not None and context is not None
        assert (
            build_scoped_packet(PRODUCT_SCOPE, "s", (direct,)).packet_id
            != build_scoped_packet(PRODUCT_SCOPE, "s", (context,)).packet_id
        )

    def test_the_legacy_sufficiency_path_still_runs_unchanged(self) -> None:
        from .test_opportunity_engine import facets as legacy_facets

        rows = tuple(
            (
                legacy_facets(
                    evidence_id=f"e{i}",
                    claim_id=f"c{i}",
                    dimensions=frozenset({EvidenceDimension.PROBLEM_OR_NEED})
                    if i % 2
                    else frozenset({EvidenceDimension.AUDIENCE_OR_USAGE}),
                ),
                PacketEligibility.ELIGIBLE_CONTEXT,
            )
            for i in range(4)
        )
        result = evaluate(build_packet(None, "s", rows))
        assert result.status.value == "HYPOTHESIS_FORMABLE"


# ================================================ the real corpus demonstration


class TestTheRealDemonstration:
    """§32, over the committed artifact."""

    def test_it_inspected_the_whole_corpus(self) -> None:
        assert demo()["totals"]["evidence_rows_inspected"] == 28

    def test_docker_resolves_to_product_and_is_direct(self) -> None:
        """§32 A."""
        scopes = demo()["scopes_by_id"]
        assert scopes["subject:docker"]["scope_type"] == "PRODUCT"
        assert scopes["subject:docker"]["evidence_rows"] == 8
        packet = demo()["docker_packet"]
        assert packet["direct_evidence"] == 8
        assert packet["role_counts"] == {"DIRECT_SUBJECT_EVIDENCE": 8}

    def test_ted_resolves_to_category_and_stays_there(self) -> None:
        """§32 B."""
        scopes = demo()["scopes_by_id"]
        assert scopes["ted-eu:CPV-division:90"]["scope_type"] == "CATEGORY"
        assert scopes["ted-eu:CPV-division:90"]["origin"] == "SOURCE_NATIVE"
        for row in demo()["ted_evidence"]:
            assert row["scope_type"] == "CATEGORY"

    def test_ted_is_not_attached_to_docker_and_says_why(self) -> None:
        """§32 C, and §19. The refusal IS the demonstration."""
        for row in demo()["ted_evidence"]:
            assert row["attached_to_docker"] is False
            assert row["refused_because"] == "NO_PERMITTED_RELATION"

    def test_the_docker_packet_holds_no_contextual_evidence(self) -> None:
        packet = demo()["docker_packet"]
        assert packet["contextual_evidence"] == 0
        assert packet["scope_relations_used"] == 0
        assert packet["contextual_dimensions_by_scope"] == {}

    def test_no_commercial_dimension_reached_the_docker_packet(self) -> None:
        packet = demo()["docker_packet"]
        assert packet["direct_counting_dimensions"] == [
            "AUDIENCE_OR_USAGE",
            "PROBLEM_OR_NEED",
        ]
        for commercial in (
            "MARKET_ACTIVITY",
            "ECONOMIC_VALUE",
            "BUYER_OR_BUDGET_EXISTENCE",
            "WILLINGNESS_TO_PAY",
        ):
            assert commercial not in packet["direct_dimensions"]

    def test_gdelt_rows_are_honestly_undetermined(self) -> None:
        """§12. Nothing was mass-labelled to make the corpus tidy."""
        scopes = demo()["scopes_by_id"]
        undetermined = [k for k, v in scopes.items() if v["scope_type"] is None]
        assert len(undetermined) == 3
        assert all(k.startswith("gdelt:lexical-term") for k in undetermined)
        assert demo()["totals"]["scopes_undetermined"] == 3

    def test_no_relation_was_used_because_none_exists(self) -> None:
        assert demo()["totals"]["reviewed_scope_relations"] == 0

    def test_the_demonstration_wrote_nothing_and_called_nothing(self) -> None:
        totals = demo()["totals"]
        assert totals["model_calls"] == 0
        assert totals["network_calls"] == 0
        assert totals["rows_written"] == 0


# ============================================================= structural bans


class TestTheCodeReachesNothing:
    """§21, §22, §30. Asserted over the AST, not over the file's text."""

    MODULES = (
        "scopes.py",
        "scope_relations.py",
        "scope_resolution.py",
        "scoped_evidence.py",
        "scoped_packet.py",
    )

    def _imports(self, name: str) -> set[str]:
        tree = ast.parse((PACKAGE_ROOT / name).read_text(encoding="utf-8"))
        found: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add(node.module or "")
        return found

    def test_no_network_model_or_database_import(self) -> None:
        forbidden = ("httpx", "requests", "psycopg", "sqlalchemy", "openai", "anthropic")
        for name in self.MODULES:
            for imported in self._imports(name):
                assert not any(imported.startswith(f) for f in forbidden), f"{name}: {imported}"

    def test_no_gateway_and_no_parked_classifier(self) -> None:
        for name in self.MODULES:
            for imported in self._imports(name):
                assert "gateway" not in imported, name
                assert "semantic_equivalence" not in imported, name

    def test_no_similarity_mechanism_anywhere(self) -> None:
        """§3. Scope identity is equality or a reviewed registry entry."""
        for name in self.MODULES:
            source = (PACKAGE_ROOT / name).read_text(encoding="utf-8")
            tree = ast.parse(source)
            # Docstrings say these words in order to forbid them, so the scan is
            # over CODE with docstrings stripped (testing-strategy.md §23).
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    continue
                if isinstance(node, ast.Name | ast.Attribute):
                    label = getattr(node, "id", "") or getattr(node, "attr", "")
                    for forbidden in ("cosine", "embed", "similarity", "levenshtein", "fuzz"):
                        assert forbidden not in label.lower(), f"{name}: {label}"

    def test_problem_family_stays_parked(self) -> None:
        for name in self.MODULES:
            source = (PACKAGE_ROOT / name).read_text(encoding="utf-8")
            if "SAME_PROBLEM_FAMILY" in source:
                assert "PARKED" in source or "parked" in source, name
