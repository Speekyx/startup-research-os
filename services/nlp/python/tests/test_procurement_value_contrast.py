"""Comparable contracts, contrasted; everything else refused. Mission 1.15.9.

**No network and no database.** Observations are built from the shape Mission
1.15.8's normalizer produces, so the extractor is exercised against the payload
it will actually read.

The properties this file exists to protect:

    one contract stating an amount is an observation, not a Signal
    four monetary semantics never become one distribution
    two currencies never become one distribution
    an unpaired amount never becomes a number (H-38)
    nothing here reads a date, an order or an instant (H-37)
    and none of it is called willingness to pay
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sros_contracts import (
    NormalizationQualityReason,
    NormalizedRecordQuality,
    SignalDirection,
    SignalMagnitudeKind,
    SignalMagnitudeUnitState,
    SignalQuantityFamily,
    SignalRefusalReason,
    SignalTemporalBasis,
)
from sros_nlp.extractors import EXTRACTOR_REGISTRY
from sros_nlp.extractors.base import CandidateGroup, DerivationRequest
from sros_nlp.extractors.procurement_value_contrast import (
    MINIMUM_COHORT_MEMBERS,
    ProcurementValueContrastExtractor,
)
from sros_nlp.observations import NormalizedObservation
from sros_signal_model import SignalRefusedError

EXTRACTOR_SOURCE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "sros_nlp"
    / "extractors"
    / "procurement_value_contrast.py"
)

MOMENT = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
WORKSPACE = "11111111-1111-1111-1111-111111111111"

# Every real TED record carries this, so every case here does too. It is the
# whole point: a temporal limitation must not invalidate a derivation that uses
# no temporal semantics.
TED_REASONS = frozenset({NormalizationQualityReason.PERIOD_TIMEZONE_NOT_ESTABLISHED})


def amount(
    amount_type: str = "TOTAL_VALUE",
    value: str = "50000",
    currency: str = "EUR",
    scope: str = "NOTICE",
    pairing: str = "ESTABLISHED",
    *,
    amounts: list[str] | None = None,
    currencies: list[str] | None = None,
) -> dict[str, object]:
    return {
        "amount_type": amount_type,
        "source_field": "total-value",
        "scope": scope,
        "amounts": amounts if amounts is not None else [value],
        "currencies": currencies if currencies is not None else [currency],
        "currency_source_field": "total-value-cur",
        "pairing": pairing,
    }


def notice(
    key: str,
    *,
    cpv: tuple[str, ...] = ("72000000",),
    notice_class: str = "CONTRACT_AWARD_NOTICE",
    amounts: list[dict[str, object]] | None = None,
    quality: NormalizedRecordQuality = NormalizedRecordQuality.PARTIAL,
    reasons: frozenset[NormalizationQualityReason] = TED_REASONS,
) -> NormalizedObservation:
    """One normalized TED notice, shaped as `ted-search-api-notice@1.0.0` writes it."""
    return NormalizedObservation(
        normalized_record_id=f"n-{key}",
        raw_record_id=f"r-{key}",
        source_id="ted-eu",
        observation_key=f"ted-eu|notice|{key}",
        record_kind_id="procurement_notice",
        quality=quality,
        quality_reasons=reasons,
        payload={
            "record_kind": "procurement_notice",
            "notice": {
                "publication_number": key,
                "class": notice_class,
                "source_type": (
                    "can-standard" if notice_class == "CONTRACT_AWARD_NOTICE" else "cn-standard"
                ),
                "source_type_scheme": "ted-notice-type",
            },
            "period": {
                "type": "DAY",
                "label": "2023-03-01+01:00",
                "start": "2023-03-01T00:00:00",
                "end": "2023-03-02T00:00:00",
                "end_inclusive": False,
                "timezone_state": "NOT_ESTABLISHED",
            },
            "classification": {
                "codes": [{"code": code, "scheme": "CPV", "label": None} for code in cpv],
                "contract_nature": ["services"],
            },
            "amounts": amounts if amounts is not None else [amount()],
            "series": {"resource_id": "notices/eforms-contract-and-award"},
        },
    )


@pytest.fixture
def extractor() -> ProcurementValueContrastExtractor:
    return ProcurementValueContrastExtractor()


@pytest.fixture
def request_() -> DerivationRequest:
    return DerivationRequest(
        workspace_id=WORKSPACE,
        correlation_id="mission-1.15.9-test",
        derived_at=MOMENT,
        expires_at=MOMENT + timedelta(days=365),
        research_session_id=None,
    )


def derive(extractor, request_, observations, amount_type: str = "TOTAL_VALUE"):
    derivation = extractor.resolve({"amount_type": amount_type})
    key = (
        extractor.group_key(observations[0], extractor.resolve({"amount_type": "TOTAL_VALUE"}))
        or "group"
    )
    return extractor.derive(
        CandidateGroup(key=key, observations=tuple(observations)), derivation, request_
    )


def reasons_of(outcome) -> set[SignalRefusalReason]:
    return {r.reason for r in outcome.refusals}


# ============================================================ registration


class TestRegistration:
    def test_the_extractor_is_registered(self) -> None:
        # 1.1.0: Mission 1.41 put currency and amount scope in the cohort key.
        assert EXTRACTOR_REGISTRY["procurement-value-contrast"].extractor_version == ("1.1.0")

    def test_it_is_the_transaction_value_family(self, extractor) -> None:
        assert extractor.family is SignalQuantityFamily.TRANSACTION_VALUE
        assert extractor.record_kind_id == "procurement_notice"

    def test_the_existing_extractors_are_untouched(self) -> None:
        """§26. A new type, never a repurposed one."""
        assert set(EXTRACTOR_REGISTRY) == {
            "numeric-period-change",
            "lexical-frequency-contrast",
            "lexical-frequency-change",
            "procurement-value-contrast",
            # Mission 1.19, ADR-032. The fifth extractor and the first over a
            # `content_request_count`. Still an EQUALITY: an extractor
            # appearing without a record kind that needs it is what this
            # catches.
            "content-request-change",
            # Mission 1.30, ADR-034. The sixth, and the first over a
            # `community_question` -- a record kind that had existed since
            # Mission 1.18 with nothing able to read it. The EQUALITY is kept
            # deliberately: a subset check here would let an extractor appear
            # without anybody deciding it should.
            "community-question-volume",
            # Mission 1.32. The seventh, and the SECOND over a
            # `community_question`: a different measurement over the same
            # records, registered as its own type rather than as a parameter on
            # the sixth, because "how many questions" and "how many without an
            # accepted answer" are different propositions.
            "community-question-without-accepted-answer",
        }
        for name in ("numeric-period-change", "lexical-frequency-contrast"):
            assert EXTRACTOR_REGISTRY[name].family is not SignalQuantityFamily.TRANSACTION_VALUE


# =============================================================== parameters


class TestParameters:
    def test_the_amount_type_is_required(self, extractor) -> None:
        """A default would pick the monetary semantic for the caller, which is
        how an estimate becomes an amount somebody paid."""
        with pytest.raises(SignalRefusedError):
            extractor.resolve({})

    def test_an_unknown_parameter_is_refused(self, extractor) -> None:
        with pytest.raises(SignalRefusedError):
            extractor.resolve({"amount_type": "TOTAL_VALUE", "top_n": 5})

    def test_the_parameter_reaches_the_fingerprint(self, extractor) -> None:
        one = extractor.resolve({"amount_type": "TOTAL_VALUE"})
        two = extractor.resolve({"amount_type": "ESTIMATED_VALUE"})
        assert one.parameter_fingerprint != two.parameter_fingerprint


# ================================================================ eligibility


class TestEligibility:
    def test_two_comparable_contracts_derive(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                notice("a", amounts=[amount(value="50000")]),
                notice("b", amounts=[amount(value="80000")]),
            ],
        )
        assert outcome.refusals == ()
        assert len(outcome.drafts) == 1

    def test_one_contract_is_not_a_signal(self, extractor, request_) -> None:
        """§3, and the rule it rests on: a derivation whose assertion is
        recoverable from one observation is that observation renamed."""
        outcome = derive(extractor, request_, [notice("a")])
        assert outcome.drafts == ()
        assert SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS in reasons_of(outcome)

    def test_the_minimum_is_two(self) -> None:
        assert MINIMUM_COHORT_MEMBERS == 2

    def test_a_contract_with_no_amount_contributes_nothing(self, extractor, request_) -> None:
        outcome = derive(extractor, request_, [notice("a"), notice("b", amounts=[])])
        assert outcome.drafts == ()

    def test_a_different_amount_type_is_not_this_cohort(self, extractor, request_) -> None:
        """§8. A total value and an estimated value are different facts.

        Since 1.1.0 the exclusion happens at GROUPING rather than after it: a
        notice carrying no amount of the wanted semantic gets no key at all, so
        the real job never puts it in this cohort. Asserting that directly is
        stronger than asserting the refusal a hand-built mixed group produces,
        and it is the behaviour the job actually has.
        """
        derivation = extractor.resolve({"amount_type": "TOTAL_VALUE"})
        estimated = notice("b", amounts=[amount(amount_type="ESTIMATED_VALUE")])
        assert extractor.group_key(estimated, derivation) is None
        assert extractor.group_key(notice("a"), derivation) is not None

        # And a caller who forces them together anyway is still refused.
        outcome = derive(extractor, request_, [notice("a"), estimated])
        assert outcome.drafts == ()

    def test_an_unpaired_amount_never_enters(self, extractor, request_) -> None:
        """§6, H-38. The source declares arrays and states nothing about their
        correspondence, so there is no amount here readable with a currency."""
        unpaired = amount(
            pairing="NOT_ESTABLISHED", amounts=["10000", "20000"], currencies=["EUR", "SEK"]
        )
        outcome = derive(extractor, request_, [notice("a"), notice("b", amounts=[unpaired])])
        assert outcome.drafts == ()

    def test_an_amount_with_no_currency_never_enters(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [notice("a"), notice("b", amounts=[amount(currencies=[], pairing="NOT_ESTABLISHED")])],
        )
        assert outcome.drafts == ()

    def test_a_malformed_amount_is_refused_not_read(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [notice("a"), notice("b", amounts=[amount(amounts=["about fifty thousand"])])],
        )
        assert outcome.drafts == ()

    def test_a_repeated_observation_key_is_refused(self, extractor, request_) -> None:
        """D-08. Two rows for one observation would manufacture a spread out of
        one contract."""
        outcome = derive(extractor, request_, [notice("a"), notice("a")])
        assert SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE in reasons_of(outcome)


# ============================================================= comparability


class TestComparability:
    def test_two_currencies_are_never_one_distribution(self, extractor, request_) -> None:
        """§8, §20. And no rate exists that could make them one."""
        outcome = derive(
            extractor,
            request_,
            [notice("a"), notice("b", amounts=[amount(currency="SEK")])],
        )
        assert outcome.drafts == ()
        assert SignalRefusalReason.INCOMPATIBLE_SERIES in reasons_of(outcome)

    def test_two_amount_scopes_are_not_one_quantity(self, extractor, request_) -> None:
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(scope="LOT")])]
        )
        assert outcome.drafts == ()
        assert SignalRefusalReason.INCOMPATIBLE_SERIES in reasons_of(outcome)

    def test_notice_classes_do_not_share_a_cohort(self, extractor) -> None:
        """§9. A call for competition and a report of an outcome describe
        different procurement stages."""
        award = extractor.group_key(notice("a"), extractor.resolve({"amount_type": "TOTAL_VALUE"}))
        call = extractor.group_key(
            notice("b", notice_class="CONTRACT_NOTICE"),
            extractor.resolve({"amount_type": "TOTAL_VALUE"}),
        )
        assert award != call

    def test_different_cpv_divisions_do_not_share_a_cohort(self, extractor) -> None:
        """The decision this design turns on, and the reason the three real
        records produced nothing: cleaning and insurance are not one market."""
        cleaning = extractor.group_key(
            notice("a", cpv=("90911200",)), extractor.resolve({"amount_type": "TOTAL_VALUE"})
        )
        insurance = extractor.group_key(
            notice("b", cpv=("66510000",)), extractor.resolve({"amount_type": "TOTAL_VALUE"})
        )
        assert cleaning != insurance

    def test_one_division_across_several_codes_is_one_cohort(self, extractor) -> None:
        """`90911200` and `90911300` are cleaning services twice. Requiring the
        full code would split a genuine cohort into singletons."""
        one = extractor.group_key(
            notice("a", cpv=("90911200",)), extractor.resolve({"amount_type": "TOTAL_VALUE"})
        )
        two = extractor.group_key(
            notice("b", cpv=("90911300", "90911200")),
            extractor.resolve({"amount_type": "TOTAL_VALUE"}),
        )
        assert one == two

    def test_a_notice_spanning_divisions_joins_no_cohort(self, extractor) -> None:
        """It has no one subject. Reading `codes[0]` would make the cohort
        depend on the order the source happened to publish them in."""
        assert (
            extractor.group_key(
                notice("a", cpv=("33000000", "34000000")),
                extractor.resolve({"amount_type": "TOTAL_VALUE"}),
            )
            is None
        )

    def test_a_notice_with_no_classification_joins_no_cohort(self, extractor) -> None:
        assert (
            extractor.group_key(
                notice("a", cpv=()), extractor.resolve({"amount_type": "TOTAL_VALUE"})
            )
            is None
        )

    def test_another_record_kind_is_refused(self, extractor, request_) -> None:
        lexical = NormalizedObservation(
            normalized_record_id="n-x",
            raw_record_id="r-x",
            source_id="gdelt",
            observation_key="gdelt|x",
            record_kind_id="lexical_frequency_observation",
            quality=NormalizedRecordQuality.PARTIAL,
            quality_reasons=frozenset(),
            payload={},
        )
        outcome = derive(extractor, request_, [notice("a"), lexical])
        assert SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS in reasons_of(outcome)


# =================================================================== the signal


class TestTheSignal:
    def test_the_magnitude_is_the_exact_spread(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                notice("a", amounts=[amount(value="73415.22")]),
                notice("b", amounts=[amount(value="25000")]),
            ],
        )
        magnitude = outcome.drafts[0].magnitude
        assert magnitude.value == Decimal("73415.22") - Decimal("25000")
        assert magnitude.kind is SignalMagnitudeKind.ABSOLUTE_DIFFERENCE

    def test_no_value_passes_through_a_float(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                notice("a", amounts=[amount(value="12345678901234567.89")]),
                notice("b", amounts=[amount(value="0.01")]),
            ],
        )
        assert outcome.drafts[0].magnitude.value == Decimal("12345678901234567.88")

    def test_the_currency_is_the_unit_and_is_inherited(self, extractor, request_) -> None:
        """A dimensionless spread over money would lose the one fact that makes
        it readable."""
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        magnitude = outcome.drafts[0].magnitude
        assert magnitude.unit == "EUR"
        assert magnitude.unit_state is SignalMagnitudeUnitState.INHERITED

    def test_the_scope_names_the_monetary_semantic(self, extractor, request_) -> None:
        """§21. A consumer must be able to tell exactly what was aggregated."""
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        scope = outcome.drafts[0].scope.to_json()
        assert scope["amount_types"] == ["TOTAL_VALUE"]
        assert scope["currencies"] == ["EUR"]
        assert scope["amount_scopes"] == ["NOTICE"]
        assert scope["notice_classes"] == ["CONTRACT_AWARD_NOTICE"]
        assert scope["classification_scheme"] == "CPV"

    def test_the_scope_carries_every_members_codes(self, extractor, request_) -> None:
        """Mission 1.15.10. The scope describes the COHORT, not its first member.

        The first real cohort had three members with three different CPV codes,
        all in division 90. Version 1.0.0 named only the first member's, chosen
        by amount order -- so the scope claimed two codes that two of the three
        contracts did not carry. Every fixture until then shared one code, which
        is exactly why real data found it and the suite had not.
        """
        members = [
            notice("a", cpv=("90911200", "90911300"), amounts=[amount(value="10")]),
            notice("b", cpv=("90715200",), amounts=[amount(value="20")]),
            notice("c", cpv=("90919300",), amounts=[amount(value="30")]),
        ]
        scope = derive(extractor, request_, members).drafts[0].scope.to_json()
        assert scope["classification_codes"] == [
            "90715200",
            "90911200",
            "90911300",
            "90919300",
        ]

    def test_the_scope_names_one_source(self, extractor, request_) -> None:
        """§14. Three notices from TED are repeated within-source observations,
        never multi-source evidence."""
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        assert outcome.drafts[0].scope.to_json()["source_ids"] == ["ted-eu"]


# ================================================================ H-37 boundary


class TestTemporalBoundary:
    def test_the_basis_is_none(self, extractor, request_) -> None:
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        assert outcome.drafts[0].window.basis is SignalTemporalBasis.NONE

    def test_the_direction_is_not_applicable(self, extractor, request_) -> None:
        """A spread is not a movement, and there is no order to have one."""
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        assert outcome.drafts[0].direction is SignalDirection.NOT_APPLICABLE

    def test_the_window_carries_no_bounds(self, extractor, request_) -> None:
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        window = outcome.drafts[0].window
        assert window.start is None and window.end is None

    def test_the_result_does_not_depend_on_publication_date(self, extractor, request_) -> None:
        """The proof that no ordering is used: change one member's publication
        date and the derivation is identical."""
        base = [notice("a"), notice("b", amounts=[amount(value="9")])]
        moved = [notice("a"), notice("b", amounts=[amount(value="9")])]
        moved[1].payload["period"]["label"] = "2019-01-01+01:00"  # type: ignore[index]
        one = derive(extractor, request_, base).drafts[0]
        two = derive(extractor, request_, moved).drafts[0]
        assert one.magnitude.value == two.magnitude.value
        assert one.direction is two.direction

    def test_the_module_reads_no_temporal_fact(self) -> None:
        """§28, over the AST. The temporal facts exist and this derivation must
        not ask for one while H-37 is open."""
        tree = ast.parse(EXTRACTOR_SOURCE.read_text(encoding="utf-8"))
        attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        for forbidden in (
            "SOURCE_RELATIVE_ORDER",
            "COMPARABLE_INSTANT",
            "period_start",
            "period_end",
            "observed_at",
        ):
            assert forbidden not in attributes, forbidden

    def test_a_partial_input_is_usable_here(self, extractor, request_) -> None:
        """§24, and it is mechanical rather than a judgement.
        `PERIOD_TIMEZONE_NOT_ESTABLISHED` withholds the two temporal facts, and
        this derivation asks for neither."""
        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        assert outcome.drafts != ()
        assert all(o.quality is NormalizedRecordQuality.PARTIAL for o in [notice("a")])


# ============================================================== WTP boundary


class TestWillingnessToPayBoundary:
    def test_the_signal_type_is_not_willingness_to_pay(self, extractor) -> None:
        assert "willingness" not in extractor.signal_type_id
        assert "wtp" not in extractor.signal_type_id.lower()

    def test_the_family_is_not_a_demand_family(self, extractor) -> None:
        assert extractor.family.value not in {"PAIN", "DESIRE", "BEHAVIORAL", "MARKET"}

    def test_no_payload_field_claims_demand_or_pricing(self, extractor, request_) -> None:
        """§29. The distinction must be visible in what is stored, not only in
        prose."""
        import json

        outcome = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        )
        draft = outcome.drafts[0]
        text = json.dumps(
            {
                "scope": draft.scope.to_json(),
                "window": draft.window.to_json(),
                "magnitude": draft.magnitude.to_json(),
            }
        ).lower()
        for forbidden in (
            "willingness",
            "wtp",
            "demand",
            "price",
            "pricing",
            "arpu",
            "purchase_intent",
            "market_size",
        ):
            assert forbidden not in text, forbidden

    def test_the_module_never_names_a_flattened_amount(self) -> None:
        """§21, §30."""
        tree = ast.parse(EXTRACTOR_SOURCE.read_text(encoding="utf-8"))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        values = {
            n.value.strip()
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
        }
        for forbidden in ("price_paid", "generic_amount", "contract_value"):
            assert forbidden not in names and forbidden not in values, forbidden

    def test_the_module_converts_no_currency(self) -> None:
        tree = ast.parse(EXTRACTOR_SOURCE.read_text(encoding="utf-8"))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        for token in ("exchange_rate", "to_eur", "convert_currency", "fx_rate"):
            assert token not in names, token

    def test_the_module_uses_no_float(self) -> None:
        tree = ast.parse(EXTRACTOR_SOURCE.read_text(encoding="utf-8"))
        calls = {
            n.func.id
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }
        assert "float" not in calls


# ================================================================= provenance


class TestProvenance:
    def test_every_member_is_in_the_lineage(self, extractor, request_) -> None:
        """§31. A multi-observation signal referencing one member would be a
        summary presented as a derivation."""
        members = [
            notice("a", amounts=[amount(value="10")]),
            notice("b", amounts=[amount(value="20")]),
            notice("c", amounts=[amount(value="30")]),
        ]
        draft = derive(extractor, request_, members).drafts[0]
        keys = {i.observation.observation_key for i in draft.inputs}
        assert keys == {o.observation_key for o in members}
        assert len(draft.inputs) == 3

    def test_the_support_count_matches_the_lineage(self, extractor, request_) -> None:
        members = [notice("a"), notice("b", amounts=[amount(value="9")])]
        draft = derive(extractor, request_, members).drafts[0]
        assert draft.window.observation_count == len(draft.inputs) == 2

    def test_the_extractor_version_is_recorded(self, extractor, request_) -> None:
        draft = derive(
            extractor, request_, [notice("a"), notice("b", amounts=[amount(value="9")])]
        ).drafts[0]
        assert draft.derivation.extractor_id == "procurement-value-contrast"
        assert draft.derivation.extractor_version == "1.1.0"


# ================================================================ determinism


class TestDeterminism:
    def test_member_order_does_not_change_the_signal(self, extractor, request_) -> None:
        """§13, §25. Identity must not depend on the order rows came back in."""
        a = notice("a", amounts=[amount(value="10")])
        b = notice("b", amounts=[amount(value="20")])
        one = derive(extractor, request_, [a, b]).drafts[0]
        two = derive(extractor, request_, [b, a]).drafts[0]
        assert one.id == two.id
        assert one.magnitude.value == two.magnitude.value

    def test_the_same_cohort_derives_the_same_signal(self, extractor, request_) -> None:
        members = [notice("a"), notice("b", amounts=[amount(value="9")])]
        assert (
            derive(extractor, request_, members).drafts[0].id
            == derive(extractor, request_, members).drafts[0].id
        )

    def test_a_different_member_set_is_a_different_signal(self, extractor, request_) -> None:
        two = [notice("a"), notice("b", amounts=[amount(value="9")])]
        three = [*two, notice("c", amounts=[amount(value="11")])]
        assert (
            derive(extractor, request_, two).drafts[0].id
            != derive(extractor, request_, three).drafts[0].id
        )


def test_no_test_in_this_file_reaches_the_network() -> None:
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "psycopg", "socket"}
