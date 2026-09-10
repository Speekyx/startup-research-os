"""Mission 1.81. The CPV grain is a parameter of the procurement contrast, and nothing else.

Four things this file defends.

MEMBERSHIP IS DECIDED BY CODES BEFORE ANY VALUE IS READ. At grain 3 a notice joins the
cohort of the one group every deep-enough code it carries names; a division-only code is an
ancestor and decides nothing; two groups are two subjects and the notice joins neither; a
notice across two divisions joins nothing at any grain.

THE GRAIN IS REQUIRED AND RECORDED. No default, like `amount_type`; it reaches the parameter
fingerprint, the key and the scope, so a group Signal and a division Signal over the same
notices are two derivations with two identities.

THE SENTENCE NAMES THE LEVEL AND KEEPS THE DIVISION. A group Signal restates to a claim
whose facts carry the level as identity; a division Signal restates exactly as 1.4.1 did.

A GROUP COHORT NEVER WITNESSES THE DIVISION'S PROPOSITION. The convergent projection keys
the level conditionally, so two windows of one group converge and a group never reaches
the division's witnessed claim.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sros_claim_model.convergence import contract_for, convergent_proposition_key
from sros_contracts import SignalDirection
from sros_nlp.extractors import EXTRACTOR_REGISTRY
from sros_nlp.extractors.base import CandidateGroup, DerivationRequest
from sros_nlp.extractors.procurement_value_contrast import CPV_LEVELS
from sros_nlp.interpreters.base import SignalLineage, SignalView
from sros_nlp.interpreters.convergent_witness import convergent_draft
from sros_nlp.interpreters.observed_restatement import (
    INTERPRETER_VERSION,
    InterpretationRequest,
    ObservedSignalRestatementInterpreter,
)
from sros_signal_model import SignalRefusedError

from tests.test_procurement_value_contrast import WORKSPACE, amount, notice

MOMENT = datetime(2026, 9, 10, tzinfo=UTC)
EXTRACTOR = EXTRACTOR_REGISTRY["procurement-value-contrast"]
INTERPRETER = ObservedSignalRestatementInterpreter()
REQUEST = InterpretationRequest(
    workspace_id=WORKSPACE,
    correlation_id="mission-1.81-test",
    interpreted_at=MOMENT,
    research_session_id=None,
)


def derivation(grain: int):
    return EXTRACTOR.resolve({"amount_type": "TOTAL_VALUE", "cpv_grain": grain})


def request_() -> DerivationRequest:
    return DerivationRequest(
        workspace_id=WORKSPACE,
        correlation_id="mission-1.81-test",
        derived_at=MOMENT,
        expires_at=MOMENT + timedelta(days=90),
        research_session_id=None,
    )


def keys_at(grain: int, *observations):
    d = derivation(grain)
    return [EXTRACTOR.group_key(o, d) for o in observations]


# ------------------------------------------------------------------ the parameter


class TestTheGrainParameter:
    def test_the_grain_is_required(self) -> None:
        with pytest.raises(SignalRefusedError):
            EXTRACTOR.resolve({"amount_type": "TOTAL_VALUE"})

    @pytest.mark.parametrize("bad", [1, 6, "3", True, 3.0])
    def test_a_grain_naming_no_level_is_refused(self, bad) -> None:
        with pytest.raises(SignalRefusedError):
            EXTRACTOR.resolve({"amount_type": "TOTAL_VALUE", "cpv_grain": bad})

    def test_every_level_the_vocabulary_names_is_accepted(self) -> None:
        for grain in CPV_LEVELS:
            assert derivation(grain).parameters["cpv_grain"] == grain

    def test_the_grain_reaches_the_fingerprint(self) -> None:
        assert derivation(2).parameter_fingerprint != derivation(3).parameter_fingerprint

    def test_the_version_moved(self) -> None:
        assert EXTRACTOR.extractor_version == "1.2.0"


# ------------------------------------------------------------------- membership


class TestMembershipAtGroupGrain:
    def test_two_notices_of_one_group_share_a_key_and_two_groups_do_not(self) -> None:
        a, b, c = keys_at(
            3,
            notice("a", cpv=("92512000",)),
            notice("b", cpv=("92521000",)),
            notice("c", cpv=("92610000",)),
        )
        assert a == b
        assert a != c
        assert '"cpv_prefix":"925"' in a
        assert '"cpv_grain":3' in a

    def test_at_the_division_all_three_share_a_key(self) -> None:
        a, b, c = keys_at(
            2,
            notice("a", cpv=("92512000",)),
            notice("b", cpv=("92521000",)),
            notice("c", cpv=("92610000",)),
        )
        assert a == b == c
        assert '"cpv_prefix":"92"' in a

    def test_a_division_only_code_is_an_ancestor_and_decides_nothing(self) -> None:
        (key,) = keys_at(3, notice("a", cpv=("92000000", "92521000")))
        assert key is not None
        assert '"cpv_prefix":"925"' in key

    def test_a_notice_stating_only_the_division_joins_no_group(self) -> None:
        (key,) = keys_at(3, notice("a", cpv=("92000000",)))
        assert key is None
        # and it still joins the division cohort
        assert keys_at(2, notice("a", cpv=("92000000",)))[0] is not None

    def test_a_notice_across_two_groups_joins_neither(self) -> None:
        (key,) = keys_at(3, notice("a", cpv=("92512000", "92610000")))
        assert key is None

    def test_a_shallower_sibling_is_not_an_ancestor(self) -> None:
        """`92320000` beside `92622000`: at grain 5 only the deeper code names a category,
        and the shallower one is a different group, not an ancestor. The notice joins
        neither, at grain 5 as at grain 3."""
        for grain in (3, 4, 5):
            assert keys_at(grain, notice("a", cpv=("92320000", "92622000")))[0] is None
        assert keys_at(5, notice("a", cpv=("92600000", "92622000")))[0] is not None

    def test_a_notice_across_two_divisions_joins_nothing_at_any_grain(self) -> None:
        for grain in (2, 3):
            assert keys_at(grain, notice("a", cpv=("90910000", "92620000")))[0] is None

    def test_a_group_cohort_is_a_strict_refinement_of_the_division_cohort(self) -> None:
        """Adding the prefix to the key can only SPLIT a division cohort, never merge two."""
        observations = [
            notice("a", cpv=("92512000",)),
            notice("b", cpv=("92521000",)),
            notice("c", cpv=("92610000",)),
            notice("d", cpv=("90911200",)),
        ]
        division = keys_at(2, *observations)
        group = keys_at(3, *observations)
        for i in range(4):
            for j in range(4):
                if group[i] == group[j]:
                    assert division[i] == division[j]


# -------------------------------------------------------------- the derivation


class TestTheDerivationAtGroupGrain:
    def _derive(self, grain: int, observations):
        d = derivation(grain)
        key = EXTRACTOR.group_key(observations[0], d)
        return EXTRACTOR.derive(
            CandidateGroup(key=key, observations=tuple(observations)), d, request_()
        )

    def test_the_scope_carries_the_level_and_its_code(self) -> None:
        outcome = self._derive(
            3,
            [
                notice("a", cpv=("92512000",), amounts=[amount(value="1000")]),
                notice("b", cpv=("92521000",), amounts=[amount(value="4000")]),
            ],
        )
        assert outcome.drafts
        scope = outcome.drafts[0].scope.to_json()
        assert scope["classification_level"] == "group"
        assert scope["classification_level_code"] == "925"
        assert scope["classification_codes"] == ["92512000", "92521000"]
        assert outcome.drafts[0].magnitude.value == Decimal("3000")

    def test_the_division_derivation_states_its_level_too(self) -> None:
        outcome = self._derive(
            2,
            [
                notice("a", cpv=("92512000",), amounts=[amount(value="1000")]),
                notice("b", cpv=("92610000",), amounts=[amount(value="4000")]),
            ],
        )
        scope = outcome.drafts[0].scope.to_json()
        assert scope["classification_level"] == "division"
        assert scope["classification_level_code"] == "92"

    def test_group_and_division_over_the_same_notices_are_two_signals(self) -> None:
        members = [
            notice("a", cpv=("92512000",), amounts=[amount(value="1000")]),
            notice("b", cpv=("92521000",), amounts=[amount(value="4000")]),
        ]
        two, three = self._derive(2, members), self._derive(3, members)
        assert two.drafts[0].id != three.drafts[0].id
        assert two.drafts[0].magnitude.value == three.drafts[0].magnitude.value

    def test_the_floor_is_the_procedures_own_two(self) -> None:
        outcome = self._derive(3, [notice("a", cpv=("92512000",))])
        assert not outcome.drafts
        assert {r.reason.value for r in outcome.refusals} == {"INSUFFICIENT_INPUT_OBSERVATIONS"}

    def test_the_same_cohort_derives_the_same_signal_twice(self) -> None:
        members = [
            notice("a", cpv=("92512000",), amounts=[amount(value="1000")]),
            notice("b", cpv=("92521000",), amounts=[amount(value="4000")]),
        ]
        assert (
            self._derive(3, members).drafts[0].id
            == self._derive(3, list(reversed(members))).drafts[0].id
        )


# ------------------------------------------------------------- the restatement


def _view(level: str | None, code: str | None, codes: tuple[str, ...]) -> SignalView:
    scope = {
        "source_ids": ["ted-eu"],
        "currencies": ["EUR"],
        "amount_types": ["TOTAL_VALUE"],
        "amount_scopes": ["NOTICE"],
        "notice_classes": ["CONTRACT_NOTICE"],
        "classification_scheme": "CPV",
        "classification_codes": list(codes),
    }
    if level is not None:
        scope["classification_level"] = level
    if code is not None:
        scope["classification_level_code"] = code
    notices = ("1-2023", "2-2023")
    return SignalView(
        signal_id=f"sig-{level}-{code}",
        signal_type_id="procurement_value_contrast",
        source_ids=("ted-eu",),
        magnitude=Decimal("3000"),
        magnitude_kind="ABSOLUTE_DIFFERENCE",
        magnitude_unit="EUR",
        magnitude_unit_state="INHERITED",
        direction=SignalDirection.NOT_APPLICABLE,
        derivation_confidence=1.0,
        extractor_id="procurement-value-contrast",
        extractor_version="1.2.0",
        scope=scope,
        source_name="Tenders Electronic Daily (EU public procurement)",
        temporal_basis="NONE",
        temporal_window={
            "basis": "NONE",
            "resolution": "DAY",
            "observation_count": 2,
            "period_labels": ["2023-03-01+01:00"] * 2,
        },
        inputs=tuple(
            SignalLineage(
                normalized_record_id=f"rec-{i}",
                raw_record_id=f"raw-{i}",
                source_id="ted-eu",
                observation_key=f"ted-eu|notice|{n}",
                record_kind_id="procurement_notice",
                period_label="2023-03-01+01:00",
                role="CONTRIBUTED",
                payload={
                    "notice": {
                        "class": "CONTRACT_NOTICE",
                        "publication_number": n,
                        "source_type": "cn-standard",
                        "source_type_scheme": "ted-notice-type",
                    },
                    "series": {"resource_id": "notices/eforms-contract-and-award"},
                    "period": {"label": "2023-03-01+01:00", "timezone_state": "NOT_ESTABLISHED"},
                    "classification": {
                        "codes": [{"code": codes[i], "scheme": "CPV", "label": None}]
                    },
                },
            )
            for i, n in enumerate(notices)
        ),
    )


class TestTheRestatementNamesTheLevel:
    def test_the_interpreter_version_moved(self) -> None:
        assert INTERPRETER_VERSION == "1.5.0"

    def test_a_group_signal_states_the_group_and_keeps_the_division(self) -> None:
        outcome = INTERPRETER.interpret(_view("group", "925", ("92512000", "92521000")), REQUEST)
        assert outcome.refusal is None, outcome.refusal
        draft = outcome.draft
        assert 'classified under "CPV" group "925" (division "92")' in draft.statement
        assert draft.cited_facts["classification_level"] == "group"
        assert draft.cited_facts["classification_level_code"] == "925"
        assert draft.cited_facts["classification_division"] == "92"

    def test_a_division_signal_states_exactly_what_it_did_before(self) -> None:
        stated = INTERPRETER.interpret(_view("division", "92", ("92512000", "92610000")), REQUEST)
        legacy = INTERPRETER.interpret(_view(None, None, ("92512000", "92610000")), REQUEST)
        assert stated.draft.statement == legacy.draft.statement
        assert 'classified under "CPV" division "92"' in legacy.draft.statement
        assert "group" not in legacy.draft.statement
        assert "classification_level" not in legacy.draft.cited_facts
        assert stated.draft.proposition_key == legacy.draft.proposition_key

    def test_a_group_and_the_division_over_the_same_notices_are_two_propositions(self) -> None:
        group = INTERPRETER.interpret(_view("group", "925", ("92512000", "92521000")), REQUEST)
        division = INTERPRETER.interpret(_view(None, None, ("92512000", "92521000")), REQUEST)
        assert group.draft.proposition_key != division.draft.proposition_key

    def test_a_level_without_its_code_is_refused(self) -> None:
        outcome = INTERPRETER.interpret(_view("group", None, ("92512000", "92521000")), REQUEST)
        assert outcome.refusal is not None

    def test_a_code_the_members_do_not_share_is_refused(self) -> None:
        outcome = INTERPRETER.interpret(_view("group", "925", ("92512000", "92610000")), REQUEST)
        assert outcome.refusal is not None

    def test_the_level_is_never_translated_into_a_label(self) -> None:
        statement = INTERPRETER.interpret(
            _view("group", "925", ("92512000", "92521000")), REQUEST
        ).draft.statement
        for word in ("museum", "library", "cultural", "market", "demand"):
            assert word not in statement.lower()


class TestTheGroupWitness:
    def _detailed(self, level, code, codes):
        return INTERPRETER.interpret(_view(level, code, codes), REQUEST).draft

    def test_a_group_cohort_witnesses_its_own_broader_claim(self) -> None:
        group = convergent_draft(
            self._detailed("group", "925", ("92512000", "92521000")),
            signal_type_id="procurement_value_contrast",
        )
        division = convergent_draft(
            self._detailed(None, None, ("92512000", "92521000")),
            signal_type_id="procurement_value_contrast",
        )
        assert group.proposition_key != division.proposition_key
        assert 'group "925" (division "92")' in group.statement
        assert 'division "92"' in division.statement
        assert "group" not in division.statement

    def test_two_windows_of_one_group_converge(self) -> None:
        one = convergent_draft(
            self._detailed("group", "925", ("92512000", "92521000")),
            signal_type_id="procurement_value_contrast",
        )
        other = convergent_draft(
            self._detailed("group", "925", ("92511000", "92521100")),
            signal_type_id="procurement_value_contrast",
        )
        assert one.proposition_key == other.proposition_key
        assert one.proposition_key == convergent_proposition_key(
            contract_for("source_published_classification_value_contrast_witnessed"),
            one.cited_facts,
        )
