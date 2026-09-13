"""Mission 1.84.11. The semantic output gate v1.3.0: one inflection policy, and a name is not a fact.

Every case here is SYNTHETIC and was written before V3's retained answer was replayed through
v1.3.0. The packet is built from the repository's own procurement mapping over invented ids, an
invented source, an invented register name and an invented CPV class. The brief's own example
sentences are the only text these tests share with anything historical. What they pin is the
general property:

* one inflection function reads the answer and the supplied statements (§5 to §7, §17);
* a word supplied only inside a source's name licenses nothing, and the refusal says so (§8 to §14,
  §18), while a name used as a name is still a provenance reference (§19);
* a lexical licence clears one finding and no other rule (§13);
* an OBSERVED statement joining alternatives fails closed (§15);
* nothing is special-cased, v1.2.0's reading is kept, and v1.1.0 and v1.2.0 are byte-identical
  (§12, §21).
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import re

import pytest
from sros_opportunity import (
    EvidenceDimension,
    EvidenceFacets,
    IndependenceState,
    PacketEligibility,
    ReliabilityStatus,
    build_packet,
)
from sros_opportunity.assertion_audit_v1_3 import (
    ANSWER_MARKER_NORMALIZATION_POLICY,
    ANSWER_MARKER_NORMALIZER,
    DISJUNCTIVE_OBSERVED_STATEMENT,
    LEXICAL_MATCH_IS_FACTUAL_SUPPORT,
    SOURCE_METADATA_NOT_FACTUAL_SUPPORT,
    SUPPORT_TOKEN_NORMALIZATION_POLICY,
    SUPPORT_TOKEN_NORMALIZER,
    audit_text,
    disjunctive_connectives,
)
from sros_opportunity.assertion_context import (
    Disposition,
    PacketStructuralFacts,
    Shape,
    TrustedContext,
    TrustedFact,
    TrustedFactKind,
)
from sros_opportunity.assertion_context import audit_text as audit_text_v1_2
from sros_opportunity.assertion_context import build_support_universe as build_support_universe_v1_2
from sros_opportunity.guards import FORBIDDEN_TERMS, VALIDATION_WORDS
from sros_opportunity.lexical_inflection import (
    INFLECTION_NOT_COVERED,
    INFLECTION_RULES,
    LEXICAL_INFLECTION_POLICY_VERSION,
    normalize_token,
)
from sros_opportunity.mapping import SIGNAL_DIMENSION_MAP
from sros_opportunity.second_opportunity import (
    PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
)
from sros_opportunity.second_opportunity_gate_v1_2 import (
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
    build_trusted_context,
    evaluate_second_opportunity_output_v1_2,
)
from sros_opportunity.second_opportunity_gate_v1_3 import (
    COMPONENT_VERSIONS_V1_3,
    OPERATOR_DECISION_V1_3,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
    SOURCE_METADATA_CONTEXT_VERSION,
    SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION,
    build_source_metadata_context,
    evaluate_second_opportunity_output_v1_3,
)
from sros_opportunity.support_origin import (
    SourceMetadataContext,
    SourceMetadataLabel,
    SourceMetadataLabelKind,
    SupportOrigin,
    build_typed_support_universe,
    split_statement,
)
from sros_opportunity.synthesis import MANDATORY_UNSUPPORTED_REPORT

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
PACKAGE = REPO_ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"
DATA = REPO_ROOT / "docs" / "data"
GATE_V1_2 = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_semantic_gate_v1_2.py"
)
V1_3_MODULES = (
    "lexical_inflection.py",
    "support_origin.py",
    "assertion_audit_v1_3.py",
    "second_opportunity_gate_v1_3.py",
)

EVIDENCE = ("33333333-3333-4333-8333-333333333333", "44444444-4444-4444-8444-444444444444")
CLAIMS = ("cccccccc-cccc-4ccc-8ccc-cccccccccccc", "dddddddd-dddd-4ddd-8ddd-dddddddddddd")
SOURCE = "synthetic-register"
NAME = "Registry Daily (synthetic procurement register)"
RESOURCE = "notices/synthetic-contract-awards"
SUBJECT = "synthetic-register:CPV-class:5555"
STATEMENTS = {
    CLAIMS[0]: (
        f'{NAME} reported that, in its "{RESOURCE}" resource, within a bounded set of 4 '
        '"CONTRACT_NOTICE" notices classified under "CPV" class "5555" (division "55"), the '
        'largest "TOTAL_VALUE" amount stated in "EUR" exceeded the smallest by 120000.'
    ),
    CLAIMS[1]: (
        f'The source "{SOURCE}" published, in its "{RESOURCE}" resource, at least one bounded set '
        'of "CONTRACT_NOTICE" notices classified under "CPV" class "5555" whose stated '
        '"TOTAL_VALUE" amounts in "EUR" differ from one another.'
    ),
}
E2C = dict(zip(EVIDENCE, CLAIMS, strict=True))
MARKERS = PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS
D, S = Disposition, Shape


def _facets(evidence_id: str, claim_id: str, source: str, signal: str) -> EvidenceFacets:
    mapping = SIGNAL_DIMENSION_MAP[signal]
    return EvidenceFacets(
        evidence_id=evidence_id,
        claim_id=claim_id,
        source_id=source,
        source_family="public_procurement",
        use_profile_id="local-private-research-v1",
        extraction_method="deterministic",
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
        reliability=0.5,
        reliability_status=ReliabilityStatus.RESOLVED,
        independence_state=IndependenceState.UNKNOWN,
        independence_group_id=None,
        observed_at=None,
        signal_type_id=signal,
        dimensions=mapping.dimensions,
        dimension_bound=mapping.bound,
    )


def _packet(source: str = SOURCE, signal: str = "procurement_value_contrast"):
    return build_packet(
        None,
        SUBJECT,
        tuple(
            (_facets(e, c, source, signal), PacketEligibility.ELIGIBLE_SCORING)
            for e, c in zip(EVIDENCE, CLAIMS, strict=True)
        ),
    )


PACKET = _packet()
SUPPORTED = frozenset(PACKET.counting_dimensions)
MANDATORY = [d.value for d in MANDATORY_UNSUPPORTED_REPORT if d not in PACKET.dimensions]
TRUSTED = build_trusted_context(PACKET)
META = build_source_metadata_context(
    [
        {
            "source_id": SOURCE,
            "canonical_name": NAME,
            "datasets": [{"resource_id": RESOURCE, "name": "Synthetic contract award notices"}],
            "provenance": "a synthetic registry entry written for these tests",
        }
    ]
)


def good_output(**changes: object) -> dict:
    output: dict = {
        "decision": "FORM_HYPOTHESIS",
        "subject": SUBJECT,
        "target_actor_if_supported": (
            "Contracting authorities that published notices under CPV class 5555."
        ),
        "observed_need": (
            "The register records published notices with differing stated amounts; it does not "
            "establish a need."
        ),
        "candidate_intervention_class": (
            "No intervention class is supported; only an inquiry into the published notices "
            "could be scoped."
        ),
        "hypothesis_statement": (
            "One question worth testing is whether these authorities publish comparable notices "
            "again; nothing supplied establishes that they do."
        ),
        "supported_dimensions": ["BUYER_OR_BUDGET_EXISTENCE", "ECONOMIC_VALUE", "MARKET_ACTIVITY"],
        "unsupported_dimensions": list(MANDATORY),
        "supporting_evidence_ids": list(EVIDENCE),
        "supporting_claim_ids": list(CLAIMS),
        "source_families": ["public_procurement"],
        "independence_status": "Independence is UNKNOWN for 2 of 2 rows.",
        "reliability_status": "Both rows are SCORABLE; no score exists.",
        "evidence_bound_reasoning_summary": (
            "Registry Daily reported 4 notices under CPV class 5555 whose stated TOTAL_VALUE "
            "amounts differ by 120000 EUR, which is market activity in the bounded scope. The "
            "register does not establish willingness to pay or actual expenditure."
        ),
        "critical_uncertainties": ["Whether any authority publishes such notices again."],
        "commercial_claims_supported": [
            "Contracting authorities under CPV class 5555 published notices with stated amounts."
        ],
        "commercial_claims_not_supported": ["Buyers are willing to pay for software."],
        "recommended_next_evidence": ["Evidence of payments actually made under these notices."],
        "confidence_classification": "EXPLORATORY",
        "statement_classifications": [
            {
                "statement": "Notices under CPV class 5555 state differing amounts.",
                "classification": "OBSERVED_OR_EVIDENCE_SUPPORTED",
            },
            {
                "statement": "The same authority publishes such notices again.",
                "classification": "HYPOTHESIS_TO_VALIDATE",
            },
            {
                "statement": "An authority would pay for a new service.",
                "classification": "UNKNOWN_REQUIRES_EVIDENCE",
            },
        ],
    }
    output.update(changes)
    return output


def gate(output: dict, *, packet=PACKET, metadata: SourceMetadataContext = META):
    return evaluate_second_opportunity_output_v1_3(
        output,
        packet,
        STATEMENTS,
        E2C,
        trusted_context=build_trusted_context(packet),
        source_metadata=metadata,
    )


def reasons_with(field: str, value: object) -> tuple[str, ...]:
    return gate(good_output(**{field: value})).refusal_reasons


SUMMARY = "evidence_bound_reasoning_summary"


def _meta(*texts: str, source: str = SOURCE) -> SourceMetadataContext:
    return SourceMetadataContext(
        version=SOURCE_METADATA_CONTEXT_VERSION,
        labels=tuple(
            SourceMetadataLabel(
                label_id=f"{source}:SOURCE_NAME:{i}",
                source_id=source,
                kind=SourceMetadataLabelKind.SOURCE_NAME,
                text=text,
                provenance="a synthetic label written for these tests",
            )
            for i, text in enumerate(texts)
        ),
    )


def _universe(*statements: str, labels: tuple[str, ...] = (NAME,)):
    return build_typed_support_universe(
        PACKET,
        {CLAIMS[i]: s for i, s in enumerate(statements)},
        TrustedContext(version="synthetic", facts=()),
        _meta(*labels),
    )


def audit(
    answer: str,
    *statements: str,
    labels: tuple[str, ...] = (NAME,),
    markers: tuple[str, ...] = MARKERS,
    disposition: Disposition = D.SUPPORTED_ASSERTION,
    shape: Shape = S.FREE,
    observed: bool = False,
    supported: frozenset[EvidenceDimension] = SUPPORTED,
):
    return audit_text(
        answer,
        disposition,
        shape,
        _universe(*statements, labels=labels),
        FORBIDDEN_CONCEPTS_V1_2,
        markers,
        supported,
        observed_statement=observed,
    )


def licence_findings(findings: tuple[str, ...]) -> list[str]:
    """The marker-licence findings alone: every other rule reports in its own words."""
    return [
        f
        for f in findings
        if re.match(r"'[^']*' appears in no source content statement", f)
        or f.startswith(SOURCE_METADATA_NOT_FACTUAL_SUPPORT)
    ]


# ============================================================================ the baseline


class TestTheSyntheticBaseline:
    def test_a_well_formed_synthetic_answer_passes(self) -> None:
        decision = gate(good_output())
        assert decision.refusal_reasons == ()
        assert decision.persist is True
        assert decision.gate_version == SECOND_OPPORTUNITY_GATE_VERSION_V1_3

    def test_it_also_satisfies_the_unchanged_v1_1_0_schema(self) -> None:
        from sros_opportunity.schema_validation import schema_violations

        assert schema_violations(good_output(), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []

    def test_a_schema_violation_is_still_reported_first(self) -> None:
        reasons = reasons_with(SUMMARY, "x" * 901)
        assert reasons[0].startswith("second-opportunity-synthesis-output@1.1.0:")

    def test_insufficient_evidence_is_a_correct_answer_and_creates_nothing(self) -> None:
        decision = gate(good_output(decision="INSUFFICIENT_EVIDENCE"))
        assert decision.persist is False
        assert any("INSUFFICIENT_EVIDENCE" in r for r in decision.refusal_reasons)

    def test_the_gate_does_not_mutate_the_answer(self) -> None:
        output = good_output()
        before = copy.deepcopy(output)
        gate(output)
        assert output == before


# ============================================================================ §3, the asymmetry


class TestSection3TheAsymmetryWasRealAndIsRepaired:
    """1.84.10's own synthetic case: a supplied plural against an answer's singular."""

    SUPPLIED = "Suppliers published notices listing their tenders."
    ANSWER = "A tender was published."

    def test_v1_2_0_still_refuses_it_because_v1_2_0_is_frozen(self) -> None:
        universe = build_support_universe_v1_2(
            PACKET, {CLAIMS[0]: self.SUPPLIED}, TrustedContext(version="synthetic", facts=())
        )
        _verdict, findings = audit_text_v1_2(
            self.ANSWER, D.SUPPORTED_ASSERTION, S.FREE, universe, FORBIDDEN_CONCEPTS_V1_2,
            MARKERS, SUPPORTED,
        )  # fmt: skip
        assert any("'tender' appears in no supplied statement" in f for f in findings)

    def test_v1_3_0_licenses_it_from_the_same_content(self) -> None:
        verdict, findings = audit(self.ANSWER, self.SUPPLIED)
        assert licence_findings(findings) == []
        assert verdict.value == "SUPPORTED"


# ============================================================================ §5 and §6


class TestSection6InflectionPolicy:
    EQUIVALENT = (
        ("tender", "tenders"),
        ("contract", "contracts"),
        ("notice", "notices"),
        ("buyer", "buyers"),
        ("industry", "industries"),
        ("opportunity", "opportunities"),
        ("weakness", "weaknesses"),
        ("movie", "movies"),
        ("finesse", "finesses"),
        ("price", "prices"),
        ("licence", "licences"),
        ("gym", "gyms"),
    )
    APART = (
        ("market", "marketing"),
        ("pay", "payment"),
        ("score", "scoring"),
        ("value", "valuable"),
        ("analysis", "analyses"),
        ("person", "people"),
        ("money", "monies"),
        ("child", "children"),
        ("crisis", "crises"),
        ("tender", "tendering"),
        ("member", "membership"),
        ("supply", "supplier"),
    )
    UNCHANGED = (
        "business",
        "process",
        "status",
        "analysis",
        "basis",
        "class",
        "weakness",
        "gas",
        "its",
        "2023s",
    )
    #: Recorded, not hidden: a singular ending in a lone s folds, as v1.2.0's answer side did.
    KNOWN_OVERFOLD = (("new", "news"), ("mean", "means"))

    @pytest.mark.parametrize(("singular", "plural"), EQUIVALENT)
    def test_regular_number_inflection_is_one_form(self, singular: str, plural: str) -> None:
        assert normalize_token(singular) == normalize_token(plural)

    @pytest.mark.parametrize(("left", "right"), APART)
    def test_unrelated_or_irregular_morphology_is_not_collapsed(
        self, left: str, right: str
    ) -> None:
        assert normalize_token(left) != normalize_token(right)

    @pytest.mark.parametrize("token", UNCHANGED)
    def test_a_word_that_is_not_a_regular_plural_is_left_alone(self, token: str) -> None:
        assert normalize_token(token) == token

    @pytest.mark.parametrize(("left", "right"), KNOWN_OVERFOLD)
    def test_the_known_overfold_is_the_one_documented(self, left: str, right: str) -> None:
        assert normalize_token(left) == normalize_token(right)

    def test_normalization_is_idempotent(self) -> None:
        for token in {t for pair in (*self.EQUIVALENT, *self.APART) for t in pair}:
            once = normalize_token(token)
            assert normalize_token(once) == once, token

    def test_the_policy_is_five_named_rules_and_nothing_else(self) -> None:
        assert [r[0] for r in INFLECTION_RULES] == [
            "REGULAR_IES_PLURAL",
            "IE_SINGULAR",
            "REGULAR_SSES_PLURAL",
            "SSE_SINGULAR",
            "REGULAR_S_PLURAL",
        ]
        assert {n for n, _ in INFLECTION_NOT_COVERED} >= {"irregular morphology", "derivation"}
        assert LEXICAL_INFLECTION_POLICY_VERSION == "opportunity-lexical-inflection@1.0.0"

    def test_the_gated_vocabulary_is_what_justifies_ies_and_sses(self) -> None:
        tokens = {
            t
            for phrase in (
                *MARKERS,
                *(p for c in FORBIDDEN_CONCEPTS_V1_2 for p in c.phrases),
                *FORBIDDEN_TERMS,
            )
            for t in re.findall(r"[a-z]+", phrase.lower())
        }
        assert {"industry", "municipality"} <= tokens
        assert "weakness" in tokens
        assert not [t for t in tokens if re.search(r"(x|ch|sh|z)$", t)]

    def test_no_nlp_dependency_is_imported(self) -> None:
        tree = ast.parse((PACKAGE / "lexical_inflection.py").read_text(encoding="utf-8"))
        imported = {
            (n.module or "") if isinstance(n, ast.ImportFrom) else a.name
            for n in ast.walk(tree)
            if isinstance(n, ast.Import | ast.ImportFrom)
            for a in (n.names if isinstance(n, ast.Import) else [None])  # type: ignore[list-item]
        }
        assert imported <= {"__future__", "assertion_context"}


# ============================================================================ §7, both sides


class TestSection7OneFunctionBothSides:
    def test_the_two_policies_are_one(self) -> None:
        assert ANSWER_MARKER_NORMALIZATION_POLICY == SUPPORT_TOKEN_NORMALIZATION_POLICY
        assert ANSWER_MARKER_NORMALIZATION_POLICY == LEXICAL_INFLECTION_POLICY_VERSION
        assert ANSWER_MARKER_NORMALIZER is SUPPORT_TOKEN_NORMALIZER is normalize_token

    @pytest.mark.parametrize(("singular", "plural"), TestSection6InflectionPolicy.EQUIVALENT)
    def test_either_form_supplied_licenses_either_form_asserted(
        self, singular: str, plural: str
    ) -> None:
        for supplied in (singular, plural):
            for asserted in (singular, plural):
                _verdict, findings = audit(
                    f"The register lists {asserted}.",
                    f"The register listed the {supplied} it held.",
                    markers=(singular,),
                )
                assert licence_findings(findings) == [], (supplied, asserted)

    def test_the_whole_procurement_vocabulary_is_read_the_same_way_on_both_sides(self) -> None:
        for marker in MARKERS:
            forms = {marker}
            if normalize_token(marker + "s") == normalize_token(marker):
                forms.add(marker + "s")
            for supplied in forms:
                for asserted in forms:
                    _verdict, findings = audit(
                        f"Records show {asserted} here.", f"The notices mention {supplied}."
                    )
                    assert licence_findings(findings) == [], (marker, supplied, asserted)
            _verdict, findings = audit(f"Records show {marker} here.", "The notices were filed.")
            assert licence_findings(findings), marker

    def test_a_marker_supplied_only_in_a_name_is_refused_for_the_whole_vocabulary(self) -> None:
        for marker in MARKERS:
            label = f"{marker.title()} Gazette"
            _verdict, findings = audit(
                f"Records show {marker} here.",
                f"{label} reported that the notices were filed.",
                labels=(label,),
            )
            assert any(f.startswith(SOURCE_METADATA_NOT_FACTUAL_SUPPORT) for f in findings), marker

    def test_no_v1_3_0_module_holds_a_second_normalizer(self) -> None:
        """Only `lexical_inflection.py` may take a token apart; everything else calls it."""
        for name in V1_3_MODULES[1:]:
            tree = ast.parse((PACKAGE / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    assert node.attr not in {"endswith", "rstrip", "removesuffix"}, (name, node)
                if isinstance(node, ast.ImportFrom) and node.module == "assertion_context":
                    names = {a.name for a in node.names}
                    assert not names & {"_spans", "_phrase_tokens", "is_asserted", "classify"}, name


# ============================================================================ §17


class TestSection17InflectionMatrix:
    LICENSED = (
        ("Contracts were published.", "A contract was published.", "contract"),
        ("Notices exist.", "A notice exists.", "notice"),
        ("A contract was published.", "Contracts were published.", "contract"),
        ("A notice exists.", "Notices exist.", "notice"),
        ("Buyers were named in the notices.", "A buyer was named.", "buyer"),
        ("A buyer was named.", "Buyers were named in the notices.", "buyer"),
    )
    NOT_EQUAL = (
        ("Marketing was published.", "The market was published.", "market"),
        ("A payment was published.", "A pay was published.", "pay"),
        ("Scoring was published.", "A score was published.", "score"),
        ("Valuable notices were published.", "A value was published.", "value"),
        ("Analyses were published.", "An analysis was published.", "analysis"),
    )

    @pytest.mark.parametrize(("supplied", "answer", "marker"), LICENSED)
    def test_a_regular_form_is_licensed_by_its_other_number(
        self, supplied: str, answer: str, marker: str
    ) -> None:
        verdict, findings = audit(answer, supplied, markers=(marker,))
        assert findings == ()
        assert verdict.value == "SUPPORTED"

    @pytest.mark.parametrize(("supplied", "answer", "marker"), NOT_EQUAL)
    def test_unrelated_morphology_licenses_nothing(
        self, supplied: str, answer: str, marker: str
    ) -> None:
        _verdict, findings = audit(answer, supplied, markers=(marker,))
        assert any(f.startswith(f"{marker!r} appears in no source content") for f in findings)


# ============================================================================ §8 to §11


class TestSection8SupportOrigins:
    def test_the_four_origins(self) -> None:
        assert [o.value for o in SupportOrigin] == [
            "SOURCE_CONTENT_STATEMENT",
            "SOURCE_METADATA_LABEL",
            "PACKET_STRUCTURAL_FACT",
            "TRUSTED_LIMITING_OR_DEFINITIONAL_FACT",
        ]

    def test_the_six_kinds_of_name(self) -> None:
        assert [k.value for k in SourceMetadataLabelKind] == [
            "PUBLISHER_NAME",
            "SOURCE_NAME",
            "REGISTRY_DISPLAY_NAME",
            "DATASET_TITLE",
            "PROVIDER_LABEL",
            "PROVENANCE_LABEL",
        ]

    @pytest.mark.parametrize(("text", "provenance"), [("", "x"), ("  ", "x"), ("A name", " ")])
    def test_a_label_names_something_and_says_where_it_came_from(
        self, text: str, provenance: str
    ) -> None:
        with pytest.raises(ValueError):
            SourceMetadataLabel("id", SOURCE, SourceMetadataLabelKind.SOURCE_NAME, text, provenance)

    def test_a_statement_splits_into_what_was_reported_and_what_it_is_called(self) -> None:
        content, carried = split_statement(STATEMENTS[CLAIMS[0]], META.labels)
        assert "registry daily" not in content and "procurement register" not in content
        assert "notices classified under" in content and "120000" in content
        assert [text for _id, text in carried] == [NAME.lower(), RESOURCE]

    def test_the_longest_label_is_claimed_first(self) -> None:
        _content, carried = split_statement(
            "Contracts Daily (weekly edition) reported that notices were filed.",
            _meta("Contracts Daily", "Contracts Daily (weekly edition)").labels,
        )
        assert [text for _id, text in carried] == ["contracts daily (weekly edition)"]

    def test_the_registry_entry_yields_its_names_with_their_provenance(self) -> None:
        assert [(lb.kind.value, lb.text) for lb in META.labels] == [
            ("PROVENANCE_LABEL", SOURCE),
            ("REGISTRY_DISPLAY_NAME", NAME),
            ("SOURCE_NAME", "Registry Daily"),
            ("PROVENANCE_LABEL", RESOURCE),
            ("DATASET_TITLE", "Synthetic contract award notices"),
        ]
        assert all(lb.provenance.startswith("a synthetic registry entry") for lb in META.labels)
        assert META.version == SOURCE_METADATA_CONTEXT_VERSION
        assert len(META.digest()) == 64

    def test_origin_is_content_before_metadata(self) -> None:
        universe = _universe(
            "Contracts Daily reported that notices were filed.", labels=("Contracts Daily",)
        )
        assert universe.origin_of("notice") is SupportOrigin.SOURCE_CONTENT_STATEMENT
        assert universe.origin_of("contract") is SupportOrigin.SOURCE_METADATA_LABEL
        assert universe.origin_of("buyer") is None

    def test_a_label_is_never_silently_content(self) -> None:
        """A packet source with no declared names is refused by name, never read whole."""
        reasons = gate(good_output(), metadata=_meta(source="another-source")).refusal_reasons
        assert any(f"no source metadata is declared for ['{SOURCE}']" in r for r in reasons)

    def test_structural_facts_have_no_place_for_a_label(self) -> None:
        assert {f.name for f in dataclasses.fields(PacketStructuralFacts)} == {
            "subject_label",
            "evidence_ids",
            "claim_ids",
            "source_families",
            "packet_dimensions",
            "supported_dimensions",
            "size",
            "scoring_eligible_count",
            "independence_summary",
        }

    def test_a_label_carried_as_a_trusted_fact_licenses_no_word(self) -> None:
        trusted = TrustedContext(
            version="synthetic",
            facts=(
                TrustedFact(
                    "SYNTHETIC",
                    TrustedFactKind.DEFINITIONAL,
                    "Contracts Daily",
                    "a synthetic fact",
                    (),
                ),
            ),
        )
        universe = build_typed_support_universe(
            PACKET, {CLAIMS[0]: "Notices were filed."}, trusted, _meta(NAME)
        )
        _verdict, findings = audit_text(
            "Contracts occur.", D.SUPPORTED_ASSERTION, S.FREE, universe, FORBIDDEN_CONCEPTS_V1_2,
            ("contract",), SUPPORTED,
        )  # fmt: skip
        assert any("'contract' appears in no source content statement" in f for f in findings)


# ============================================================================ §18 and §14


class TestSection18MetadataMatrix:
    CASES = (
        (
            "Contracts Daily",
            "Contracts Daily reported that the notices were filed.",
            "Contracts occur.",
            ("contract", "contracts"),
            "contract",
        ),
        (
            "Buyers Weekly",
            "Buyers Weekly reported that the notices were filed.",
            "Buyers exist in this market.",
            ("buyer", "buyers"),
            "buyer",
        ),
        (
            "Market Activity Observatory",
            "Market Activity Observatory reported that the notices were filed.",
            "Market activity is established.",
            ("market",),
            "market",
        ),
        (
            "Tenders Electronic Daily",
            "Tenders Electronic Daily reported that the notices were filed.",
            "Tenders occur.",
            ("tender", "tenders"),
            "tender",
        ),
    )

    @pytest.mark.parametrize(("label", "supplied", "answer", "markers", "marker"), CASES)
    def test_a_word_supplied_only_in_a_name_is_not_factual_support(
        self,
        label: str,
        supplied: str,
        answer: str,
        markers: tuple[str, ...],
        marker: str,
    ) -> None:
        verdict, findings = audit(
            answer, supplied, labels=(label,), markers=markers, supported=frozenset()
        )
        assert verdict.value == "UNSUPPORTED"
        assert any(
            f.startswith(f"{SOURCE_METADATA_NOT_FACTUAL_SUPPORT}: {marker!r}") for f in findings
        )

    def test_the_refusal_is_truthful_rather_than_claiming_the_word_was_never_supplied(
        self,
    ) -> None:
        _verdict, findings = audit(
            "Tenders occur.",
            "Tenders Electronic Daily reported that the notices were filed.",
            labels=("Tenders Electronic Daily",),
        )
        assert not [f for f in findings if "appears in no" in f]
        assert any(
            "only supplied occurrence is inside the source metadata label" in f for f in findings
        )

    def test_structural_support_licenses_market_activity_and_the_label_still_does_not(
        self,
    ) -> None:
        label, supplied = "Market Activity Observatory", "The notices were filed."
        verdict, findings = audit(
            "Market activity is established.",
            f"{label} reported that the notices were filed.",
            labels=(label,),
            markers=("market",),
            supported=frozenset({EvidenceDimension.MARKET_ACTIVITY}),
        )
        assert findings == () and verdict.value == "SUPPORTED"
        _verdict, alone = audit(
            "Market activity is established.",
            supplied,
            labels=(label,),
            markers=("market",),
            supported=frozenset({EvidenceDimension.MARKET_ACTIVITY}),
        )
        assert alone == ()

    def test_independent_content_licenses_the_word_the_name_could_not(self) -> None:
        for answer in ("Tenders occur.", "Tenders occur in CPV class 9261."):
            verdict, findings = audit(
                answer,
                "Published tenders were observed for CPV class 9261.",
                labels=("Tenders Electronic Daily",),
            )
            assert findings == (), answer
            assert verdict.value == "SUPPORTED"

    def test_the_default_vocabulary_refuses_buyers_in_this_market_without_support(self) -> None:
        verdict, findings = audit(
            "Buyers exist in this market.",
            "Buyers Weekly reported that the notices were filed.",
            labels=("Buyers Weekly",),
            supported=frozenset(),
        )
        assert verdict.value == "UNSUPPORTED"
        assert any("'market' appears in no source content statement" in f for f in findings)
        assert any("'buyers' asserts BUYER_OR_BUDGET_EXISTENCE" in f for f in findings)


# ============================================================================ §19


class TestSection19ProvenanceMayUseMetadata:
    PROVENANCE = (
        ("Tenders Electronic Daily", "The source is Tenders Electronic Daily."),
        ("Contracts Daily", "Contracts Daily published the notices."),
        ("Willingness To Pay Index", "Willingness To Pay Index is the source."),
        ("Market Demand Monitor", "Market Demand Monitor is the provider."),
        ("Dataset 2023 Release", "Dataset 2023 Release is the dataset."),
    )

    @pytest.mark.parametrize(("label", "answer"), PROVENANCE)
    def test_a_name_used_as_a_name_is_a_provenance_reference(self, label: str, answer: str) -> None:
        verdict, findings = audit(
            answer, f"{label} reported that the notices were filed.", labels=(label,)
        )
        assert findings == (), findings
        assert verdict.value == "SUPPORTED"

    def test_the_source_family_is_a_structural_provenance_statement(self) -> None:
        verdict, findings = audit("The source family is public_procurement.", "Notices exist.")
        assert findings == () and verdict.value == "SUPPORTED"

    def test_a_provenance_label_does_not_license_willingness_to_pay(self) -> None:
        label = "Willingness To Pay Index"
        _verdict, findings = audit(
            "Willingness to pay is established.",
            f"{label} reported that the notices were filed.",
            labels=(label,),
        )
        joined = " ".join(findings)
        assert "WILLINGNESS_TO_PAY" in joined
        assert "occurs only inside the source metadata label" in joined

    def test_a_provenance_label_does_not_license_market_demand(self) -> None:
        label = "Market Demand Monitor"
        _verdict, findings = audit(
            "Market demand exists for these services.",
            f"{label} reported that the notices were filed.",
            labels=(label,),
        )
        joined = " ".join(findings)
        assert "MARKET_DEMAND" in joined
        assert SOURCE_METADATA_NOT_FACTUAL_SUPPORT in joined

    def test_a_figure_inside_a_label_licenses_no_number(self) -> None:
        label = "Dataset 2023 Release"
        _verdict, findings = audit(
            "Notices were filed in 2023.",
            f"{label} reported that the notices were filed.",
            labels=(label,),
        )
        assert any("the number 2023 appears in no source content statement" in f for f in findings)

    def test_a_label_that_is_a_gated_term_never_masks(self) -> None:
        _verdict, findings = audit(
            "Market Demand is the provider.",
            "Market Demand reported that the notices were filed.",
            labels=("Market Demand",),
        )
        assert any("MARKET_DEMAND" in f for f in findings)


# ============================================================================ §13


class TestSection13LexicalMatchIsNotFactualSupport:
    SUPPLIED = "Contracts were published for class 5555."
    STILL_REFUSED = (
        ("A contract worth 999 was published.", D.SUPPORTED_ASSERTION, S.FREE, "the number 999"),
        ("A contract shows willingness to pay.", D.SUPPORTED_ASSERTION, S.FREE, "WILLINGNESS"),
        ("Contracts were scored.", D.SUPPORTED_ASSERTION, S.FREE, "'scored' is asserted"),
        ("A contract is validated demand.", D.SUPPORTED_ASSERTION, S.FREE, "'validated'"),
        ("A contract will definitely follow.", D.HYPOTHESIS_TO_VALIDATE, S.FREE, "definitely"),
        ("A contract was published.", D.FUTURE_EVIDENCE_REQUEST, S.REQUEST, "request-shaped"),
    )

    def test_the_invariant_is_explicit(self) -> None:
        assert LEXICAL_MATCH_IS_FACTUAL_SUPPORT is False

    @pytest.mark.parametrize(("answer", "disposition", "shape", "expected"), STILL_REFUSED)
    def test_a_licensed_word_clears_its_own_finding_and_no_other_rule(
        self, answer: str, disposition: Disposition, shape: Shape, expected: str
    ) -> None:
        _verdict, findings = audit(
            answer, self.SUPPLIED, markers=("contract",), disposition=disposition, shape=shape
        )
        assert licence_findings(findings) == []
        assert any(expected in f for f in findings), findings


# ============================================================================ §15


class TestSection15Disjunction:
    REFUSED = (
        "Contracts or notices were published for class 5555.",
        "Either contracts or awards were filed under class 5555.",
        "Notices were filed under class 5555 or under class 55.",
        "Awards were filed, or notices were withdrawn.",
        "Contracts and/or notices were filed.",
        "Notices were published or withdrawn for class 5555.",
    )
    NOT_DISJUNCTIVE = (
        "No contracts or notices were published for class 5555.",
        "Contracts were not published or withdrawn for class 5555.",
        "It is unknown whether contracts or notices were filed.",
        "Contracts and notices were published for class 5555.",
        "Neither contracts nor notices were published.",
        "Without contracts or notices, nothing was filed.",
    )
    SUPPLIED = 'Notices classified under class "5555" (division "55") were filed.'

    @pytest.mark.parametrize("statement", REFUSED)
    def test_an_observed_disjunction_fails_closed(self, statement: str) -> None:
        verdict, findings = audit(statement, self.SUPPLIED, markers=(), observed=True)
        assert verdict.value == "UNSUPPORTED"
        assert any(f.startswith(DISJUNCTIVE_OBSERVED_STATEMENT) for f in findings)

    @pytest.mark.parametrize("statement", NOT_DISJUNCTIVE)
    def test_alternatives_denied_together_are_not_an_observed_disjunction(
        self, statement: str
    ) -> None:
        assert disjunctive_connectives(statement) == ()
        _verdict, findings = audit(statement, self.SUPPLIED, markers=(), observed=True)
        assert not [f for f in findings if f.startswith(DISJUNCTIVE_OBSERVED_STATEMENT)]

    def test_the_rule_is_scoped_to_statements_classified_observed(self) -> None:
        _verdict, findings = audit(self.REFUSED[0], self.SUPPLIED, markers=(), observed=False)
        assert not [f for f in findings if f.startswith(DISJUNCTIVE_OBSERVED_STATEMENT)]

    def test_through_the_gate_only_the_observed_classification_is_refused(self) -> None:
        items = [
            {"statement": self.REFUSED[0], "classification": "OBSERVED_OR_EVIDENCE_SUPPORTED"},
            {"statement": self.REFUSED[5], "classification": "HYPOTHESIS_TO_VALIDATE"},
            {"statement": self.REFUSED[1], "classification": "UNKNOWN_REQUIRES_EVIDENCE"},
        ]
        reasons = reasons_with("statement_classifications", items)
        flagged = [r for r in reasons if DISJUNCTIVE_OBSERVED_STATEMENT in r]
        assert len(flagged) == 1
        assert flagged[0].startswith("statement_classifications[0].statement")

    def test_a_prose_field_is_not_refused_by_this_rule(self) -> None:
        summary = (
            "Registry Daily reported 4 notices under CPV class 5555, filed as contract notices "
            "or award notices. It does not establish willingness to pay."
        )
        assert not [
            r for r in reasons_with(SUMMARY, summary) if DISJUNCTIVE_OBSERVED_STATEMENT in r
        ]


# ============================================================================ §12, no special case


class TestSection12NothingIsSpecialCased:
    FORBIDDEN_LITERALS = ("tender", "ted-eu", "electronic daily", "9261", "transaction")

    @pytest.mark.parametrize("name", V1_3_MODULES)
    def test_no_code_constant_names_the_word_or_the_source_that_prompted_it(
        self, name: str
    ) -> None:
        tree = ast.parse((PACKAGE / name).read_text(encoding="utf-8"))
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        }
        constants = [
            node.value.lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ]
        assert not [c for c in constants for w in self.FORBIDDEN_LITERALS if w in c]


# ============================================================================ adversarial


class TestAdversarialNames:
    CASES = (
        (
            "Tenders Electronic Daily",
            "Tenders Electronic Daily shows that tenders occur.",
            ("tender",),
        ),
        ("Tenders Electronic Daily", "Tender Electronic Daily lists tenders.", ("tender",)),
        ("Contracts Daily", "CONTRACTS   DAILY lists contracts.", ("contract",)),
        ("Contracts Daily", "Contracts are daily.", ("contract",)),
        ("Buyers Weekly", "Buyers Weekly buyers exist.", ("buyer",)),
        ("Contracts Daily", "Daily contracts occur.", ("contract",)),
    )

    @pytest.mark.parametrize(("label", "answer", "markers"), CASES)
    def test_a_name_cannot_be_rearranged_inflected_or_repeated_into_support(
        self, label: str, answer: str, markers: tuple[str, ...]
    ) -> None:
        _verdict, findings = audit(
            answer,
            f"{label} reported that the notices were filed.",
            labels=(label,),
            markers=markers,
        )
        assert any(f.startswith(SOURCE_METADATA_NOT_FACTUAL_SUPPORT) for f in findings), answer

    def test_an_answer_cannot_declare_its_own_label(self) -> None:
        """Labels come from the metadata channel only: a new name in an answer is read as words."""
        _verdict, findings = audit(
            "According to Tenders Monthly, tenders occur.", "The notices were filed."
        )
        assert any("'tender' appears in no source content statement" in f for f in findings)

    def test_a_different_case_and_spacing_is_still_the_same_name(self) -> None:
        verdict, findings = audit(
            "The source is CONTRACTS   daily.",
            "Contracts Daily reported that the notices were filed.",
            labels=("Contracts Daily",),
            markers=("contract",),
        )
        assert findings == () and verdict.value == "SUPPORTED"


# ============================================================================ v1.2.0 kept


class TestThePredecessorReadingIsKept:
    """The brief's own cases from Mission 1.84.10, through both gates: same verdict."""

    PARITY = (
        (SUMMARY, "Customers are willing to pay.", True),
        (SUMMARY, "The evidence establishes willingness to pay.", True),
        (SUMMARY, "No evidence establishes willingness to pay.", False),
        (SUMMARY, "Willingness to pay is not established.", False),
        (SUMMARY, "Actual expenditure is not established, but is probably substantial.", True),
        ("reliability_status", "SCORABLE. These rows are not unscored; they are scored.", True),
        ("recommended_next_evidence", ["Evidence of actual expenditure would be required."], False),
        ("recommended_next_evidence", ["Actual expenditure was 10 million EUR."], True),
    )

    @pytest.mark.parametrize(("field", "value", "refused"), PARITY)
    def test_the_same_verdict_as_v1_2_0(self, field: str, value: object, refused: bool) -> None:
        output = good_output(**{field: value})
        v1_2 = evaluate_second_opportunity_output_v1_2(
            output, PACKET, STATEMENTS, E2C, trusted_context=TRUSTED
        )
        v1_3 = gate(output)
        assert (not v1_2.persist) is refused
        assert (not v1_3.persist) is refused

    def test_the_field_policy_is_v1_2_0s_own(self) -> None:
        from sros_opportunity import second_opportunity_gate_v1_3 as module

        assert module.SECOND_OPPORTUNITY_FIELD_POLICY is SECOND_OPPORTUNITY_FIELD_POLICY
        assert module.FORBIDDEN_CONCEPTS_V1_2 is FORBIDDEN_CONCEPTS_V1_2

    def test_a_noun_is_never_read_as_a_verb_of_support(self) -> None:
        """`evidences` and `supports` are verb forms and stay verbatim: naming support is fine."""
        for item in ("Evidence of buyer demand.", "Customer support for these notices."):
            _verdict, findings = audit(
                item, "Notices exist.", disposition=D.EXPLICITLY_NOT_SUPPORTED
            )
            assert not [f for f in findings if "contradicts the NOT-supported" in f], item

    def test_validation_words_are_still_refused_unconditionally(self) -> None:
        assert "validated" in VALIDATION_WORDS
        _verdict, findings = audit("The demand is validated.", "Notices exist.")
        assert any("'validated' states a conclusion" in f for f in findings)


# ============================================================================ §21


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestSection21Versioning:
    def test_every_component_has_its_version(self) -> None:
        assert COMPONENT_VERSIONS_V1_3 == {
            "gate": "second-opportunity-output-gate@1.3.0",
            "output_schema": "second-opportunity-synthesis-output@1.1.0",
            "persistence_gate": "opportunity-synthesis-persistence-gate@1.3.0",
            "audit": "opportunity-synthesis-audit@1.4.0",
            "claim_guard": "opportunity-claim-guard@1.4.0",
            "field_context_policy": "second-opportunity-field-context-policy@1.0.0",
            "support_universe": "opportunity-support-universe@2.0.0",
            "trusted_context": "second-opportunity-trusted-context@1.0.0",
            "source_metadata": "second-opportunity-source-metadata@1.0.0",
            "lexical_inflection": "opportunity-lexical-inflection@1.0.0",
            "observed_statement_disjunction": "observed-statement-disjunction-policy@1.0.0",
        }

    def test_gate_v1_2_0_is_still_the_one_frozen(self) -> None:
        freeze = _module("semantic_gate_v1_2_freeze_from_v1_3_tests", GATE_V1_2)
        freeze.validate()
        assert freeze.implementation_sha256() == freeze.FROZEN_IMPLEMENTATION_SHA256

    def test_the_historical_modules_are_bb0f50a_s(self) -> None:
        freeze = _module("semantic_gate_v1_2_history_from_v1_3_tests", GATE_V1_2)
        for path, digest in freeze.HISTORICAL_SHA256.items():
            assert hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() == digest, path

    def test_the_operator_decision_is_carried_as_data(self) -> None:
        assert OPERATOR_DECISION_V1_3 == (
            "FIX_SYMMETRIC_INFLECTION_NORMALIZATION = true",
            "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false",
            "SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = true",
            "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
            "KEEP_PROMPT_V1_2_0_UNCHANGED",
            "KEEP_HISTORICAL_GATE_V1_1_0_UNCHANGED",
            "KEEP_FROZEN_GATE_V1_2_0_UNCHANGED",
            "DO_NOT_WHITELIST_THE_V3_ANSWER",
            "DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES",
        )

    def test_the_evidence_boundary_decision_is_the_operator_s(self) -> None:
        decision = SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION
        assert decision["SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT"] is False
        assert decision["decision_owner"] == "OPERATOR"
        assert decision["decision_type"] == "EVIDENCE_BOUNDARY"
        assert decision["mathematically_derived"] is False
        assert decision["independent_of_any_answer"] is True
        assert decision["moved_into_packet_structural_facts"] is False


# ============================================================================ §4, no whitelist


class TestNoAnswerIsWhitelisted:
    def _answer_texts(self) -> list[str]:
        response = json.loads(
            (DATA / "second-opportunity-synthesis-response-v3.json").read_text(encoding="utf-8")
        )
        return [v for v in json.dumps(response["parsed_output"]).split('"') if len(v.split()) >= 8]

    def test_no_case_in_this_file_is_the_historical_answer(self) -> None:
        own = pathlib.Path(__file__).read_text(encoding="utf-8")
        assert not [t for t in self._answer_texts() if t in own]

    @pytest.mark.parametrize("name", V1_3_MODULES)
    def test_no_module_carries_the_historical_answer(self, name: str) -> None:
        source = (PACKAGE / name).read_text(encoding="utf-8")
        assert not [t for t in self._answer_texts() if t in source]
