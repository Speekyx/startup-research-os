"""The deterministic OBSERVED interpreter, over synthetic Signals only.

Mission 1.13.1 §37. **No network, no database, no model.** Every Signal below is
constructed in this file; the ones shaped after the seven real ones say so.

What the suite is organised around:

    §5   the interpreter is structurally incapable of a non-OBSERVED claim
    §6   a numeric restatement names its source, metric, geography and periods
    §7   a lexical change says "source bucket", never a clock
    §8   a contrast says "same bucket", never an ordering
    §9   attribution is mandatory -- "Germany's population increased" is not OBSERVED
    §25  H-29: no instant, no UTC, no cross-source alignment
    §26  H-30: the source language LABEL, never a canonical language
    §27  determinism: runtime metadata does not move the proposition
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sros_claim_model import proposition_key
from sros_contracts import (
    ClaimEvidenceRefusalReason,
    ClaimInterpretationKind,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
    SignalDirection,
)
from sros_nlp.interpreters import (
    InterpretationRequest,
    ObservedSignalRestatementInterpreter,
    SignalLineage,
    SignalView,
)

WORKSPACE = "00000000-0000-4000-8000-0000000000aa"
REQUEST = InterpretationRequest(
    workspace_id=WORKSPACE,
    correlation_id="corr-1",
    interpreted_at=datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
    research_session_id="00000000-0000-4000-8000-0000000000bb",
)
INTERPRETER = ObservedSignalRestatementInterpreter()

# SYNTHETIC, shaped after the real World Bank signal DE 2018 -> 2019.
_WB_PAYLOAD = {
    "metric": {"id": "SP.POP.TOTL", "scheme": "world-bank-indicator", "name": None},
    "series": {"resource_id": "indicator/SP.POP.TOTL", "dataset": "indicators"},
    "geography": {
        "kind": "COUNTRY",
        "source_code": "DEU",
        "source_name": "Germany",
        "canonical_code": "DE",
    },
}

# SYNTHETIC, shaped after the real GDELT WEB-NGRAM records.
_GDELT_PAYLOAD = {
    "term": {"text": "climate", "scheme": "gdelt-web-ngram", "gram_size": 1},
    "series": {"resource_id": "web-ngrams/1gram", "dataset": "web-ngrams-1gram"},
    "language": {
        "source_label": "ENGLISH",
        "source_scheme": "cld2-language-name",
        "canonical_tag": None,
        "mapping_state": "NOT_ESTABLISHED",
    },
}


def _lineage(payload: dict, source_id: str, label: str, index: int) -> SignalLineage:
    return SignalLineage(
        normalized_record_id=f"rec-{index}",
        raw_record_id=f"raw-{index}",
        source_id=source_id,
        observation_key=f"{source_id}|{label}|{index}",
        record_kind_id="numeric_observation"
        if source_id == "world-bank"
        else "lexical_frequency_observation",
        period_label=label,
        role="CONTRIBUTED",
        payload=payload,
    )


def numeric(**overrides) -> SignalView:
    labels = overrides.pop("period_labels", ("2018", "2019"))
    payload = overrides.pop("payload", _WB_PAYLOAD)
    kwargs = {
        "signal_id": "sig-numeric",
        "signal_type_id": "numeric_period_change",
        "source_ids": ("world-bank",),
        "magnitude": Decimal("187180"),
        "magnitude_kind": "ABSOLUTE_CHANGE",
        "magnitude_unit": None,
        "magnitude_unit_state": "NOT_ESTABLISHED",
        "direction": SignalDirection.INCREASING,
        "derivation_confidence": 1.0,
        "extractor_id": "numeric-period-change",
        "extractor_version": "1.0.0",
        "scope": {
            "source_ids": ["world-bank"],
            "metric_ids": ["SP.POP.TOTL"],
            "geography_codes": ["DE"],
        },
        "source_name": "World Bank Open Data",
        "temporal_basis": "COMPARABLE_INSTANTS",
        "temporal_window": {"period_labels": list(labels), "resolution": "YEAR"},
        "inputs": tuple(
            _lineage(payload, "world-bank", label, i) for i, label in enumerate(labels)
        ),
    }
    kwargs.update(overrides)
    return SignalView(**kwargs)


def lexical_change(**overrides) -> SignalView:
    labels = overrides.pop("period_labels", ("20260830184500", "20260830190000"))
    payload = overrides.pop("payload", _GDELT_PAYLOAD)
    kwargs = {
        "signal_id": "sig-change",
        "signal_type_id": "lexical_frequency_change",
        "source_ids": ("gdelt",),
        "magnitude": Decimal("11"),
        "magnitude_kind": "ABSOLUTE_CHANGE",
        "magnitude_unit": None,
        "magnitude_unit_state": "NOT_ESTABLISHED",
        "direction": SignalDirection.INCREASING,
        "derivation_confidence": 1.0,
        "extractor_id": "lexical-frequency-change",
        "extractor_version": "1.0.0",
        "scope": {
            "source_ids": ["gdelt"],
            "terms": ["climate"],
            "source_language_labels": ["ENGLISH"],
            "source_language_scheme": "cld2-language-name",
        },
        "source_name": "The GDELT Project",
        "temporal_basis": "ORDERED_PERIODS",
        "temporal_window": {"period_labels": list(labels), "resolution": "INTERVAL"},
        "inputs": tuple(_lineage(payload, "gdelt", label, i) for i, label in enumerate(labels)),
    }
    kwargs.update(overrides)
    return SignalView(**kwargs)


def lexical_contrast(**overrides) -> SignalView:
    label = overrides.pop("label", "20260830091500")
    payload = overrides.pop("payload", _GDELT_PAYLOAD)
    kwargs = {
        "signal_id": "sig-contrast",
        "signal_type_id": "lexical_frequency_contrast",
        "source_ids": ("gdelt",),
        "magnitude": Decimal("19"),
        "magnitude_kind": "ABSOLUTE_DIFFERENCE",
        "magnitude_unit": None,
        "magnitude_unit_state": "NOT_ESTABLISHED",
        "direction": SignalDirection.NOT_APPLICABLE,
        "derivation_confidence": 1.0,
        "extractor_id": "lexical-frequency-contrast",
        "extractor_version": "1.0.0",
        "scope": {
            "source_ids": ["gdelt"],
            "terms": ["climate", "weather"],
            "source_language_labels": ["ENGLISH"],
            "source_language_scheme": "cld2-language-name",
        },
        "source_name": "The GDELT Project",
        "temporal_basis": "SAME_PERIOD_LABEL",
        "temporal_window": {"period_labels": [label, label], "resolution": "INTERVAL"},
        "inputs": tuple(_lineage(payload, "gdelt", label, i) for i in range(2)),
    }
    kwargs.update(overrides)
    return SignalView(**kwargs)


def draft_of(signal: SignalView):
    outcome = INTERPRETER.interpret(signal, REQUEST)
    assert outcome.refusal is None, outcome.refusal
    assert outcome.draft is not None
    return outcome.draft


def refusal_of(signal: SignalView) -> ClaimEvidenceRefusalReason:
    outcome = INTERPRETER.interpret(signal, REQUEST)
    assert outcome.draft is None, outcome.draft.statement
    assert outcome.refusal is not None
    return outcome.refusal.reason


# ================================================================ §5 OBSERVED only


class TestStructurallyObserved:
    def test_every_template_produces_observed(self):
        for signal in (numeric(), lexical_change(), lexical_contrast()):
            assert draft_of(signal).claim_type is ClaimType.OBSERVED

    def test_the_interpreter_exposes_no_way_to_ask_for_another_type(self):
        """§5. Not "it defaults to OBSERVED" -- there is no parameter."""
        import inspect

        signature = inspect.signature(INTERPRETER.interpret)
        assert list(signature.parameters) == ["signal", "request"]

    def test_origin_and_temporality_are_fixed(self):
        draft = draft_of(numeric())
        assert draft.origin is ClaimOrigin.DETERMINISTIC_EXTRACTION
        # A claim about a FIXED pair of periods does not decay, whatever the
        # source's cadence is.
        assert draft.temporality is ClaimTemporality.EVERGREEN

    def test_a_15_minute_bucket_claim_is_also_evergreen(self):
        assert draft_of(lexical_change()).temporality is ClaimTemporality.EVERGREEN

    def test_the_interpretation_is_deterministic_and_names_no_model(self):
        interpretation = draft_of(numeric()).interpretation
        assert interpretation is not None
        assert interpretation.kind is ClaimInterpretationKind.DETERMINISTIC
        assert interpretation.model_version is None
        assert interpretation.prompt_version is None
        assert interpretation.interpreter_id == "observed-signal-restatement"
        assert interpretation.interpreter_version == "1.3.0"

    def test_interpretation_confidence_is_one(self):
        """It says the template read the Signal correctly. Nothing else."""
        assert draft_of(numeric()).interpretation_confidence == 1.0

    def test_an_unsupported_signal_type_is_refused_not_paraphrased(self):
        assert (
            refusal_of(numeric(signal_type_id="sentiment_polarity"))
            is ClaimEvidenceRefusalReason.UNSUPPORTED_SIGNAL_TYPE
        )


# ============================================================= §6 numeric template


class TestNumericPeriodChange:
    def test_the_statement_names_source_metric_geography_periods_and_magnitude(self):
        statement = draft_of(numeric()).statement
        assert statement == (
            'World Bank Open Data reported that "SP.POP.TOTL" for "Germany" increased '
            'between "2018" and "2019" by 187180.'
        )

    def test_the_geography_is_the_source_name_not_our_canonical_code(self):
        """§9. `Germany` is what World Bank called it; `DE` is what a reviewed
        mapping decided it is, and OBSERVED reports the first."""
        statement = draft_of(numeric()).statement
        assert "Germany" in statement
        assert '"DE"' not in statement

    def test_a_decrease_says_decreased(self):
        signal = numeric(direction=SignalDirection.DECREASING, magnitude=Decimal("-5000"))
        assert "decreased" in draft_of(signal).statement
        assert "by 5000." in draft_of(signal).statement

    def test_unchanged_states_no_magnitude(self):
        signal = numeric(direction=SignalDirection.UNCHANGED, magnitude=Decimal("0"))
        statement = draft_of(signal).statement
        assert "was unchanged" in statement
        assert " by " not in statement

    def test_an_indeterminate_direction_is_refused(self):
        """The extractor could not say which way it moved. A sentence that
        picked one would assert what the derivation refused to."""
        signal = numeric(direction=SignalDirection.INDETERMINATE)
        assert refusal_of(signal) is ClaimEvidenceRefusalReason.UNSUPPORTED_INTERPRETATION

    def test_the_facts_carry_the_source_native_geography_code(self):
        facts = draft_of(numeric()).cited_facts
        assert facts["geography_source_code"] == "DEU"
        assert facts["metric_id"] == "SP.POP.TOTL"
        assert facts["resource_id"] == "indicator/SP.POP.TOTL"


# ============================================================ §7 lexical change


class TestLexicalFrequencyChange:
    def test_the_statement_is_source_relative_throughout(self):
        statement = draft_of(lexical_change()).statement
        assert statement == (
            'The GDELT Project reported that, in its "web-ngrams/1gram" stream under '
            'source language label "ENGLISH", the term "climate" appeared 11 more times '
            'in source bucket "20260830190000" than in the preceding source bucket '
            '"20260830184500".'
        )

    def test_it_never_says_utc_or_a_clock_time(self):
        """§25. H-29 is open: the bucket label is a source label and nothing
        places it on a shared timeline."""
        statement = draft_of(lexical_change()).statement.lower()
        for forbidden in ("utc", "gmt", "o'clock", " at 18", "timestamp", "timezone"):
            assert forbidden not in statement

    def test_it_names_the_source_language_label_and_no_canonical_language(self):
        """§26. H-30 is open: `ENGLISH` from CLD2 is not BCP-47 `en`."""
        draft = draft_of(lexical_change())
        assert 'source language label "ENGLISH"' in draft.statement
        assert "in English" not in draft.statement
        assert draft.cited_facts["language_source_scheme"] == "cld2-language-name"
        assert "canonical_tag" not in draft.cited_facts

    def test_a_decrease_says_fewer(self):
        signal = lexical_change(direction=SignalDirection.DECREASING, magnitude=Decimal("-4"))
        assert "appeared 4 fewer times" in draft_of(signal).statement

    def test_an_unzoned_change_signal_on_an_instant_basis_is_refused(self):
        """Failing closed. A basis this template cannot phrase is not described
        with wording chosen for a different one."""
        signal = lexical_change(temporal_basis="COMPARABLE_INSTANTS")
        assert refusal_of(signal) is ClaimEvidenceRefusalReason.INCOMPATIBLE_TEMPORAL_SEMANTICS

    def test_two_terms_in_a_change_signal_are_refused(self):
        signal = lexical_change(
            scope={"terms": ["climate", "weather"], "source_ids": ["gdelt"]},
        )
        assert refusal_of(signal) is ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE


# ========================================================== §8 lexical contrast


class TestLexicalFrequencyContrast:
    def test_the_statement_asserts_a_within_bucket_comparison_only(self):
        statement = draft_of(lexical_contrast()).statement
        assert statement == (
            'The GDELT Project reported that, in its "web-ngrams/1gram" stream under '
            'source language label "ENGLISH", within source bucket "20260830091500", the '
            'term "climate" appeared 19 more times than the term "weather".'
        )

    def test_it_asserts_no_ordering_and_no_change(self):
        statement = draft_of(lexical_contrast()).statement.lower()
        for forbidden in ("increased", "decreased", "rose", "fell", "preceding", "later"):
            assert forbidden not in statement

    def test_the_relation_comes_from_the_magnitude_sign(self):
        fewer = lexical_contrast(magnitude=Decimal("-19"))
        assert "19 fewer times" in draft_of(fewer).statement
        assert draft_of(fewer).cited_facts["relation"] == "FEWER"

    def test_an_equal_contrast_states_no_magnitude(self):
        equal = lexical_contrast(magnitude=Decimal("0"))
        statement = draft_of(equal).statement
        assert "the same number of times" in statement
        assert draft_of(equal).cited_facts["relation"] == "EQUAL"

    def test_two_different_bucket_labels_are_refused(self):
        signal = lexical_contrast(
            temporal_window={"period_labels": ["20260830091500", "20260830093000"]}
        )
        assert refusal_of(signal) is ClaimEvidenceRefusalReason.INCOMPATIBLE_TEMPORAL_SEMANTICS

    def test_the_relation_not_the_value_is_part_of_identity(self):
        """A revised count that keeps the ordering is the SAME proposition; one
        that flips it is a different one."""
        base = draft_of(lexical_contrast())
        bigger = draft_of(lexical_contrast(magnitude=Decimal("42")))
        flipped = draft_of(lexical_contrast(magnitude=Decimal("-19")))
        assert base.proposition_key == bigger.proposition_key
        assert base.proposition_key != flipped.proposition_key


# ============================================================ §9 attribution


class TestAttribution:
    def test_every_statement_names_its_source(self):
        for signal in (numeric(), lexical_change(), lexical_contrast()):
            statement = draft_of(signal).statement
            assert statement.split(" reported")[0] in (
                "World Bank Open Data",
                "The GDELT Project",
            )
            assert " reported that" in statement

    def test_no_statement_asserts_the_fact_without_the_source(self):
        """§9. "Germany's population increased" removes the attribution and
        changes the epistemic meaning."""
        statement = draft_of(numeric()).statement
        assert not statement.startswith("Germany")
        assert not statement.startswith('"SP.POP.TOTL"')

    def test_the_source_id_falls_back_when_the_registry_has_no_name(self):
        assert draft_of(numeric(source_name=None)).statement.startswith("world-bank reported")

    def test_a_signal_spanning_two_sources_is_refused(self):
        mixed = numeric(
            inputs=(
                _lineage(_WB_PAYLOAD, "world-bank", "2018", 0),
                _lineage(_WB_PAYLOAD, "eurostat", "2019", 1),
            ),
            source_ids=("world-bank", "eurostat"),
        )
        assert refusal_of(mixed) is ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE

    def test_a_signal_with_no_readable_lineage_is_refused(self):
        assert (
            refusal_of(numeric(inputs=(), source_ids=("world-bank",)))
            is ClaimEvidenceRefusalReason.SIGNAL_LINEAGE_UNAVAILABLE
        )

    def test_lineage_that_disagrees_on_the_resource_is_refused(self):
        other = dict(_GDELT_PAYLOAD)
        other["series"] = {"resource_id": "web-ngrams/2gram", "dataset": "web-ngrams-2gram"}
        signal = lexical_change(
            inputs=(
                _lineage(_GDELT_PAYLOAD, "gdelt", "20260830184500", 0),
                _lineage(other, "gdelt", "20260830190000", 1),
            )
        )
        assert refusal_of(signal) is ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE


# ==================================================== §10 the vocabulary guard


class TestVocabularyGuard:
    def test_no_generated_statement_uses_market_or_user_vocabulary(self):
        for signal in (numeric(), lexical_change(), lexical_contrast()):
            prose = draft_of(signal).statement.lower()
            for forbidden in (
                "demand",
                "interest",
                "attention",
                "popular",
                "market",
                "opportunity",
                "trending",
                "revenue",
                "want",
            ):
                assert forbidden not in prose, forbidden

    def test_a_source_term_that_is_market_vocabulary_still_produces_a_claim(self):
        """The guard exempts QUOTED source data. `demand` is a real English word
        a news corpus contains, and refusing it would refuse the most faithful
        restatement available -- the exact thing the guard protects."""
        payload = {**_GDELT_PAYLOAD, "term": {**_GDELT_PAYLOAD["term"], "text": "demand"}}
        signal = lexical_change(
            scope={"terms": ["demand"], "source_ids": ["gdelt"]}, payload=payload
        )
        draft = draft_of(signal)
        assert '"demand"' in draft.statement
        assert draft.claim_type is ClaimType.OBSERVED

    def test_the_same_holds_for_market_and_pain(self):
        for term in ("market", "pain", "opportunity"):
            payload = {**_GDELT_PAYLOAD, "term": {**_GDELT_PAYLOAD["term"], "text": term}}
            signal = lexical_change(
                scope={"terms": [term], "source_ids": ["gdelt"]}, payload=payload
            )
            assert draft_of(signal).claim_type is ClaimType.OBSERVED


# =============================================================== §14-§19 evidence


class TestEvidence:
    def test_one_evidence_row_citing_the_originating_signal(self):
        draft = draft_of(numeric())
        assert len(draft.evidence) == 1
        assert draft.evidence[0].signal_id == "sig-numeric"

    def test_direction_is_supports(self):
        assert draft_of(numeric()).evidence[0].direction is EvidenceDirection.SUPPORTS

    def test_relevance_and_directness_are_one_and_justified(self):
        item = draft_of(numeric()).evidence[0]
        assert item.relevance == 1.0
        assert item.directness == 1.0

    def test_reliability_is_absent_not_invented(self):
        """§17. Purpose-relative, D-03 blocked. A constant here would be the
        per-source coefficient the framework refuses."""
        assert draft_of(numeric()).evidence[0].reliability is None
        assert "reliability" not in draft_of(numeric()).evidence[0].to_json()

    def test_extraction_confidence_is_one(self):
        assert draft_of(numeric()).evidence[0].extraction_confidence == 1.0

    def test_independence_is_unknown(self):
        item = draft_of(numeric()).evidence[0]
        assert item.independence_state is EvidenceIndependenceState.UNKNOWN
        assert item.independence_group_id is None

    def test_two_gdelt_signals_are_not_declared_independent(self):
        """One publication stream, two Signals. Not independent because they are
        two, and not dependent either -- that judgement is aggregation's."""
        for signal in (lexical_change(), lexical_contrast()):
            item = draft_of(signal).evidence[0]
            assert item.independence_state is EvidenceIndependenceState.UNKNOWN
            assert item.source_id == "gdelt"

    def test_observation_category_is_uncategorised_for_both_sources(self):
        """A population count is not MARKET_ACTIVITY; a news frequency is not
        anybody's behaviour."""
        for signal in (numeric(), lexical_change(), lexical_contrast()):
            item = draft_of(signal).evidence[0]
            assert item.observation_category is EvidenceObservationCategory.UNCATEGORISED

    def test_evidence_carries_no_score(self):
        payload = draft_of(numeric()).evidence[0].to_json()
        for forbidden in ("evidence_score", "score", "weight", "strength"):
            assert forbidden not in payload


# ============================================================== §11-§12, §27 identity


class TestPropositionIdentity:
    def test_the_key_is_over_the_facts_and_recomputable(self):
        draft = draft_of(numeric())
        assert draft.proposition_key == proposition_key(draft.cited_facts)

    def test_the_magnitude_is_not_part_of_identity(self):
        """A source revising its figure has restated the SAME proposition. The
        amount is wording, which revisions handle."""
        base = draft_of(numeric())
        revised = draft_of(numeric(magnitude=Decimal("187200")))
        assert base.proposition_key == revised.proposition_key
        assert base.statement != revised.statement

    def test_the_direction_is_part_of_identity(self):
        base = draft_of(numeric())
        down = draft_of(numeric(direction=SignalDirection.DECREASING))
        assert base.proposition_key != down.proposition_key

    def test_different_geographies_are_different_propositions(self):
        other = dict(_WB_PAYLOAD)
        other["geography"] = {"source_code": "FRA", "source_name": "France", "kind": "COUNTRY"}
        france = draft_of(numeric(payload=other))
        assert draft_of(numeric()).proposition_key != france.proposition_key

    def test_the_three_proposition_shapes_never_collide(self):
        keys = {
            draft_of(s).proposition_key for s in (numeric(), lexical_change(), lexical_contrast())
        }
        assert len(keys) == 3

    def test_runtime_metadata_does_not_move_the_proposition(self):
        """§27. A different clock, correlation id and session produce the same
        proposition, the same statement and the same evidence relation."""
        other = InterpretationRequest(
            workspace_id=WORKSPACE,
            correlation_id="a-completely-different-correlation",
            interpreted_at=datetime(2031, 1, 1, tzinfo=UTC),
            research_session_id="00000000-0000-4000-8000-0000000000cc",
        )
        first = draft_of(numeric())
        second_outcome = INTERPRETER.interpret(numeric(), other)
        second = second_outcome.draft
        assert second is not None
        assert first.proposition_key == second.proposition_key
        assert first.statement == second.statement
        assert first.interpretation_confidence == second.interpretation_confidence
        assert first.evidence[0].to_json() == second.evidence[0].to_json()

    def test_the_signal_id_is_not_part_of_identity(self):
        """Two derivations of one proposition converge on one claim. The Signal
        is cited as evidence, which is where the lineage belongs."""
        assert (
            draft_of(numeric()).proposition_key
            == draft_of(numeric(signal_id="a-different-signal")).proposition_key
        )


# ==================================================== what is NOT implemented


class TestNotImplemented:
    def test_no_module_in_this_package_produces_an_inferred_claim(self):
        import ast
        import pathlib

        import sros_nlp.interpreters as package

        root = pathlib.Path(package.__file__).parent
        found: list[str] = []
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                # `ClaimType.X` as an ATTRIBUTE ACCESS, over the AST -- a
                # docstring naming INFERRED must not fail this
                # (`testing-strategy.md` §23).
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "ClaimType"
                    and node.attr != "OBSERVED"
                ):
                    found.append(f"{path.name}: ClaimType.{node.attr}")
        assert found == []

    @pytest.mark.parametrize("forbidden", ["canonical_tag", "canonical_scheme"])
    def test_no_template_reads_a_canonical_language_tag(self, forbidden):
        """§26. H-30 is open, so reading the mapping would assert one.

        Over CALL ARGUMENTS and SUBSCRIPTS, not over the file's text: a comment
        or docstring explaining the rule must not fail it
        (`testing-strategy.md` §23).
        """
        import ast
        import pathlib

        import sros_nlp.interpreters as package

        reads: list[str] = []
        for path in pathlib.Path(package.__file__).parent.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    literals = [
                        a.value
                        for a in [*node.args, *(k.value for k in node.keywords)]
                        if isinstance(a, ast.Constant)
                    ]
                    if forbidden in literals:
                        reads.append(f"{path.name}:{node.lineno} call")
                elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                    if node.slice.value == forbidden:
                        reads.append(f"{path.name}:{node.lineno} subscript")
        assert reads == []


# ---------------------------------------------------------------------------
# Mission 1.15.11 -- the procurement value contrast.
#
# The template whose whole difficulty is what it must NOT say. Every test below
# is either "the bound is in the sentence" or "the market interpretation is
# not".
# ---------------------------------------------------------------------------

# SYNTHETIC, shaped after the real TED signal: three division-90 award notices
# with EUR total values 73415.22, 440000 and 759960.24.
_TED_NOTICES = ("125972-2023", "126676-2023", "127668-2023")


def _ted_payload(notice_id: str) -> dict:
    return {
        "notice": {
            "class": "CONTRACT_AWARD_NOTICE",
            "publication_number": notice_id,
            "source_type": "can-standard",
            "source_type_scheme": "ted-notice-type",
        },
        "series": {"resource_id": "notices/eforms-contract-and-award"},
        # Present in the real payload and deliberately never read: the offset's
        # meaning is H-37, and this template states nothing temporal.
        "period": {"label": "2023-03-01+01:00", "timezone_state": "NOT_ESTABLISHED"},
        "classification": {"codes": [{"code": "90911200", "scheme": "CPV", "label": None}]},
    }


def procurement(**overrides) -> SignalView:
    notices = overrides.pop("notice_ids", _TED_NOTICES)
    kwargs = {
        "signal_id": "sig-procurement",
        "signal_type_id": "procurement_value_contrast",
        "source_ids": ("ted-eu",),
        "magnitude": Decimal("686545.02"),
        "magnitude_kind": "ABSOLUTE_DIFFERENCE",
        "magnitude_unit": "EUR",
        "magnitude_unit_state": "INHERITED",
        "direction": SignalDirection.NOT_APPLICABLE,
        "derivation_confidence": 1.0,
        "extractor_id": "procurement-value-contrast",
        "extractor_version": "1.0.1",
        "scope": {
            "source_ids": ["ted-eu"],
            "currencies": ["EUR"],
            "amount_types": ["TOTAL_VALUE"],
            "amount_scopes": ["NOTICE"],
            "notice_classes": ["CONTRACT_AWARD_NOTICE"],
            "classification_scheme": "CPV",
            "classification_codes": ["90715200", "90911200", "90911300", "90919300"],
        },
        "source_name": "Tenders Electronic Daily (EU public procurement)",
        "temporal_basis": "NONE",
        "temporal_window": {
            "basis": "NONE",
            "resolution": "DAY",
            "observation_count": len(notices),
            # Carried by the real Signal and never read by this template.
            "period_labels": ["2023-03-01+01:00"] * len(notices),
        },
        "inputs": tuple(
            SignalLineage(
                normalized_record_id=f"rec-ted-{i}",
                raw_record_id=f"raw-ted-{i}",
                source_id="ted-eu",
                observation_key=f"ted-eu|{notice}",
                record_kind_id="procurement_notice",
                period_label="2023-03-01+01:00",
                role="CONTRIBUTED",
                payload=_ted_payload(notice),
            )
            for i, notice in enumerate(notices)
        ),
    }
    kwargs.update(overrides)
    return SignalView(**kwargs)


def _statement(signal: SignalView) -> str:
    outcome = INTERPRETER.interpret(signal, REQUEST)
    assert outcome.refusal is None, outcome.refusal
    assert outcome.draft is not None
    return outcome.draft.statement


class TestTheProcurementRestatement:
    def test_it_says_the_whole_bounded_proposition(self) -> None:
        assert _statement(procurement()) == (
            "Tenders Electronic Daily (EU public procurement) reported that, in its "
            '"notices/eforms-contract-and-award" resource, within a bounded set of 3 '
            '"CONTRACT_AWARD_NOTICE" notices classified under "CPV" division "90", the '
            'largest "TOTAL_VALUE" amount at "NOTICE" scope stated in "EUR" exceeded the '
            "smallest by 686545.02."
        )

    def test_the_bound_is_in_the_sentence(self) -> None:
        """The one shortening that would change what is asserted.

        "Division 90 contracts vary by 686545.02" is a claim about every
        division-90 contract. The words that stop it are "within a bounded set
        of 3", and they are asserted here rather than trusted to survive an
        edit.
        """
        statement = _statement(procurement())
        assert "within a bounded set of 3" in statement
        assert "notices classified under" in statement

    def test_it_is_a_maximum_minus_a_minimum_and_says_so(self) -> None:
        statement = _statement(procurement())
        assert "the largest" in statement
        assert "exceeded the smallest by" in statement
        for word in ("average", "median", "mean", "typical", "price", "per contract"):
            assert word not in statement.lower()

    def test_the_magnitude_is_exact(self) -> None:
        assert "686545.02" in _statement(procurement())

    def test_an_equal_cohort_does_not_borrow_the_exceeded_wording(self) -> None:
        statement = _statement(procurement(magnitude=Decimal("0")))
        assert "was equal to the smallest" in statement
        assert "exceeded" not in statement

    def test_it_is_observed_and_deterministic(self) -> None:
        outcome = INTERPRETER.interpret(procurement(), REQUEST)
        draft = outcome.draft
        assert draft is not None
        assert draft.claim_type is ClaimType.OBSERVED
        assert draft.origin is ClaimOrigin.DETERMINISTIC_EXTRACTION
        assert draft.temporality is ClaimTemporality.EVERGREEN
        assert draft.interpretation.kind is ClaimInterpretationKind.DETERMINISTIC
        assert draft.interpretation.interpreter_version == "1.3.0"
        assert draft.interpretation.model_version is None
        assert draft.interpretation.prompt_version is None

    def test_it_is_attributed_and_never_asserts_the_fact_bare(self) -> None:
        statement = _statement(procurement())
        assert statement.startswith("Tenders Electronic Daily (EU public procurement) reported")


class TestWhatItRefusesToSay:
    """The mission brief's forbidden list, asserted rather than described."""

    FORBIDDEN = (
        "market",
        "demand",
        "willingness",
        "customers",
        "buyers",
        "revenue",
        "opportunity",
        "growth",
        "attractive",
        "profitable",
        "pricing",
        "saas",
        "arpu",
        "cleaning",
        "environmental",
    )

    def test_no_market_vocabulary_survives_the_template(self) -> None:
        statement = _statement(procurement()).lower()
        for word in self.FORBIDDEN:
            assert word not in statement, word

    def test_the_cpv_division_is_not_translated_into_a_market_name(self) -> None:
        """Division 90 is cleaning and environmental services, and the claim
        does not know that. Naming the market would be a classification this
        layer has no vocabulary for and no reviewed mapping behind."""
        statement = _statement(procurement())
        assert '"CPV" division "90"' in statement

    def test_the_model_guard_would_catch_a_market_wording_anyway(self) -> None:
        """The template is the protection; this asserts the backstop exists.

        A statement naming a market is refused by `build_claim` for any OBSERVED
        claim, so an edit to the template that reintroduced the word does not
        reach the database.
        """
        from sros_claim_model import INTERPRETIVE_VOCABULARY

        assert "market" in INTERPRETIVE_VOCABULARY
        assert "willingness to pay" in INTERPRETIVE_VOCABULARY


class TestNothingTemporal:
    """H-37 is open, and this template is why it does not have to close."""

    def test_the_statement_carries_no_date_no_window_and_no_chronology(self) -> None:
        statement = _statement(procurement()).lower()
        for token in (
            "2023",
            "march",
            "recently",
            "between",
            "before",
            "after",
            "during",
            "increase",
            "decrease",
            "trend",
        ):
            assert token not in statement, token

    def test_the_period_label_reaches_the_signal_and_not_the_claim(self) -> None:
        """The acquisition window bounded RETRIEVAL, not the proposition.

        The label is present on every contributing record and in the Signal's
        own window; the claim states none of it.
        """
        signal = procurement()
        assert signal.period_labels  # the Signal carries them
        outcome = INTERPRETER.interpret(signal, REQUEST)
        draft = outcome.draft
        assert draft is not None
        assert "2023-03-01" not in draft.statement
        assert "period_label" not in draft.cited_facts
        assert "2023-03-01+01:00" not in str(draft.cited_facts)

    def test_a_temporal_basis_is_refused_rather_than_phrased(self) -> None:
        outcome = INTERPRETER.interpret(procurement(temporal_basis="ORDERED_PERIODS"), REQUEST)
        assert outcome.draft is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is ClaimEvidenceRefusalReason.INCOMPATIBLE_TEMPORAL_SEMANTICS


class TestTheCohortSurvivesIntoTheProposition:
    def test_all_three_notices_are_named_and_support_is_not_reduced(self) -> None:
        outcome = INTERPRETER.interpret(procurement(), REQUEST)
        draft = outcome.draft
        assert draft is not None
        assert draft.cited_facts["notice_ids"] == list(_TED_NOTICES)

    def test_the_member_amounts_are_not_copied_into_the_claim(self) -> None:
        """Reachable through provenance, so not duplicated here.

        The magnitude is wording rather than identity, and the member values are
        one join away through Evidence -> Signal -> signal_inputs.
        """
        outcome = INTERPRETER.interpret(procurement(), REQUEST)
        draft = outcome.draft
        assert draft is not None
        facts = str(draft.cited_facts)
        for value in ("73415.22", "440000", "759960.24", "686545.02"):
            assert value not in facts, value

    def test_every_cohort_dimension_is_in_the_identity(self) -> None:
        outcome = INTERPRETER.interpret(procurement(), REQUEST)
        draft = outcome.draft
        assert draft is not None
        facts = draft.cited_facts
        assert facts["proposition"] == "source_reported_procurement_value_contrast"
        assert facts["source_id"] == "ted-eu"
        assert facts["notice_class"] == "CONTRACT_AWARD_NOTICE"
        assert facts["amount_type"] == "TOTAL_VALUE"
        assert facts["amount_scope"] == "NOTICE"
        assert facts["currency"] == "EUR"
        assert facts["classification_scheme"] == "CPV"
        assert facts["classification_division"] == "90"
        assert facts["classification_codes"] == [
            "90715200",
            "90911200",
            "90911300",
            "90919300",
        ]
        assert facts["relation"] == "DIFFERS"

    def test_a_revised_amount_restates_the_same_proposition(self) -> None:
        """The magnitude is wording. TED correcting 759960.24 does not create a
        second claim; it appends a revision to this one."""
        first = INTERPRETER.interpret(procurement(), REQUEST).draft
        revised = INTERPRETER.interpret(procurement(magnitude=Decimal("686545.03")), REQUEST).draft
        assert first is not None and revised is not None
        assert first.proposition_key == revised.proposition_key
        assert first.statement != revised.statement

    def test_a_fourth_notice_is_a_different_proposition(self) -> None:
        """The cohort IS the subject, so its membership is its identity.

        This is the half that differs from the lexical templates: there the
        periods are fixed by the query, here the members are the claim.
        """
        first = INTERPRETER.interpret(procurement(), REQUEST).draft
        wider = INTERPRETER.interpret(
            procurement(notice_ids=(*_TED_NOTICES, "999999-2023")), REQUEST
        ).draft
        assert first is not None and wider is not None
        assert first.proposition_key != wider.proposition_key

    def test_an_all_equal_cohort_is_a_different_proposition(self) -> None:
        differs = INTERPRETER.interpret(procurement(), REQUEST).draft
        equal = INTERPRETER.interpret(procurement(magnitude=Decimal("0")), REQUEST).draft
        assert differs is not None and equal is not None
        assert differs.proposition_key != equal.proposition_key

    def test_a_repeated_notice_is_refused_rather_than_counted_twice(self) -> None:
        outcome = INTERPRETER.interpret(
            procurement(notice_ids=("125972-2023", "125972-2023")), REQUEST
        )
        assert outcome.draft is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE

    def test_a_notice_without_an_identifier_is_refused(self) -> None:
        signal = procurement()
        first = signal.inputs[0]
        broken = {**first.payload, "notice": {"class": "CONTRACT_AWARD_NOTICE"}}
        inputs = (
            SignalLineage(
                normalized_record_id=first.normalized_record_id,
                raw_record_id=first.raw_record_id,
                source_id=first.source_id,
                observation_key=first.observation_key,
                record_kind_id=first.record_kind_id,
                period_label=first.period_label,
                role=first.role,
                payload=broken,
            ),
            *signal.inputs[1:],
        )
        outcome = INTERPRETER.interpret(procurement(inputs=inputs), REQUEST)
        assert outcome.draft is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is ClaimEvidenceRefusalReason.SIGNAL_LINEAGE_UNAVAILABLE


class TestTheCohortDimensionsAreRefusedRatherThanPicked:
    @pytest.mark.parametrize(
        "field,values",
        [
            ("currencies", ["EUR", "PLN"]),
            ("amount_types", ["TOTAL_VALUE", "ESTIMATED_VALUE"]),
            ("amount_scopes", ["NOTICE", "LOT"]),
            ("notice_classes", ["CONTRACT_AWARD_NOTICE", "CONTRACT_NOTICE"]),
        ],
    )
    def test_two_values_on_one_dimension_is_ambiguous(self, field: str, values: list) -> None:
        scope = {**procurement().scope, field: values}
        outcome = INTERPRETER.interpret(procurement(scope=scope), REQUEST)
        assert outcome.draft is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE

    def test_codes_spanning_two_divisions_have_no_single_subject(self) -> None:
        """The real acquisition excluded exactly these notices one layer down.

        `127009-2023` spans divisions 77 and 90. If such a cohort ever reached
        this template, naming one division would say the contrast is about a
        category half of it is not in.
        """
        scope = {**procurement().scope, "classification_codes": ["77310000", "90911200"]}
        outcome = INTERPRETER.interpret(procurement(scope=scope), REQUEST)
        assert outcome.draft is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE

    def test_no_classification_scheme_is_refused(self) -> None:
        scope = {k: v for k, v in procurement().scope.items() if k != "classification_scheme"}
        outcome = INTERPRETER.interpret(procurement(scope=scope), REQUEST)
        assert outcome.draft is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is ClaimEvidenceRefusalReason.SIGNAL_LINEAGE_UNAVAILABLE


class TestTheEvidenceItProduces:
    def _evidence(self):
        outcome = INTERPRETER.interpret(procurement(), REQUEST)
        assert outcome.draft is not None
        assert len(outcome.draft.evidence) == 1
        return outcome.draft.evidence[0]

    def test_it_supports_the_claim_it_restates(self) -> None:
        evidence = self._evidence()
        assert evidence.direction is EvidenceDirection.SUPPORTS
        assert evidence.signal_id == "sig-procurement"
        assert evidence.source_id == "ted-eu"

    def test_support_three_is_still_one_source(self) -> None:
        """Three notices from TED are three rows from ONE publisher.

        The Signal has support 3 and the Evidence is a single row naming a
        single `source_id`, which is what stops aggregation from reading it as
        three independent observations.
        """
        assert self._evidence().independence_state is EvidenceIndependenceState.UNKNOWN
        assert self._evidence().independence_group_id is None

    def test_a_concluded_purchase_does_not_become_market_activity_here(self) -> None:
        """The mission's closest call, pinned so it cannot drift silently.

        MARKET_ACTIVITY is the only gate to EvidenceLevel 4. What this row
        carries is a maximum minus a minimum over published notices, which is a
        property of records rather than economic activity.
        """
        assert self._evidence().observation_category is EvidenceObservationCategory.UNCATEGORISED

    def test_derivation_confidence_does_not_become_reliability(self) -> None:
        """1.0 says the arithmetic is established. It says nothing about TED."""
        signal = procurement()
        assert signal.derivation_confidence == 1.0
        evidence = self._evidence()
        assert evidence.reliability is None
        assert evidence.relevance == 1.0
        assert evidence.directness == 1.0
        assert evidence.extraction_confidence == 1.0

    def test_the_claim_confidence_is_about_the_reading_not_the_world(self) -> None:
        outcome = INTERPRETER.interpret(procurement(), REQUEST)
        assert outcome.draft is not None
        assert outcome.draft.interpretation_confidence == 1.0
        assert outcome.draft.evidence[0].reliability is None


class TestTheExistingThreeTemplatesDidNotMove:
    """The version bump is additive, and this is what makes that checkable."""

    def test_the_numeric_statement_is_unchanged(self) -> None:
        assert _statement(numeric()) == (
            'World Bank Open Data reported that "SP.POP.TOTL" for "Germany" increased '
            'between "2018" and "2019" by 187180.'
        )

    def test_the_numeric_proposition_key_is_unchanged(self) -> None:
        outcome = INTERPRETER.interpret(numeric(), REQUEST)
        assert outcome.draft is not None
        assert outcome.draft.proposition_key == proposition_key(
            {
                "proposition": "source_reported_metric_period_change",
                "source_id": "world-bank",
                "resource_id": "indicator/SP.POP.TOTL",
                "metric_scheme": "world-bank-indicator",
                "metric_id": "SP.POP.TOTL",
                "geography_source_code": "DEU",
                "period_label_from": "2018",
                "period_label_to": "2019",
                "direction": "INCREASING",
            }
        )

    def test_the_lexical_change_statement_is_unchanged(self) -> None:
        assert _statement(lexical_change()) == (
            'The GDELT Project reported that, in its "web-ngrams/1gram" stream under source '
            'language label "ENGLISH", the term "climate" appeared 11 more times in source '
            'bucket "20260830190000" than in the preceding source bucket "20260830184500".'
        )
