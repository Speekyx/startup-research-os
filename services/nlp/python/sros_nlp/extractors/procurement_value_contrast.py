"""`procurement-value-contrast@1.0.0` -- what several comparable contracts settled at.

`ted-eu-transaction-signals-v1.md`. Mission 1.15.9, ADR-029.

**What it asserts, in full:** within one source, several procurement
transactions that share an amount semantic, an amount scope, a currency, a
notice class and a procurement classification settled at values whose spread is
exactly this much, across exactly this many contracts.

**What it does not assert**, and each of these was reachable from the same
numbers:

- that a market exists, or that demand does. A public body buying cleaning
  services is a transaction that happened;
- **willingness to pay.** That a named buyer paid a named supplier a stated
  amount is established. That a comparable buyer would pay a comparable amount
  for a *different* product is not, and no field here says otherwise;
- what a product could charge. The spread is a fact about contracts already
  signed, not a price recommendation;
- anything about time. See below.

**H-37 is respected by construction, not by care.** The temporal basis is
`NONE`, the direction is `NOT_APPLICABLE`, and this module reads no period, no
date, no order and no instant. Members are ordered for output by AMOUNT and then
by observation key -- a total ordering over values and identities, never over
time. There is no growth, no trend, no change and no window.

**H-38 is respected by exclusion.** An observation whose monetary entry is not
`pairing = ESTABLISHED` supplies no `PAIRED_MONETARY_AMOUNT`, so it never enters
a cohort. Both sequences stay in the normalized record as context; neither
becomes a number here.

**The cohort key includes the procurement classification, and that is the
decision most worth arguing with.** Without it a cohort is *"EUR totals in this
slice of TED"* -- a statement about a query rather than about anything in the
world, and two contracts for cleaning and for insurance would be summarised as
one distribution. `signal-contract-v1.md` prefers a smaller truthful cohort to a
larger ambiguous one, and the CPV division is the source's own subject
classification, so requiring it invents nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from sros_contracts import (
    SignalDerivationKind,
    SignalDirection,
    SignalMagnitudeKind,
    SignalMagnitudeUnitState,
    SignalQuantityFamily,
    SignalRefusalReason,
    SignalRequiredFact,
    SignalTemporalBasis,
)
from sros_signal_model import (
    PROCUREMENT_NOTICE,
    SignalDerivation,
    SignalDerivationRefusal,
    SignalMagnitude,
    SignalRefusedError,
    SignalScope,
    SignalWindow,
    assess_inputs,
    build_signal,
)

from ..observations import NormalizedObservation, decimal_from
from .base import CandidateGroup, DerivationRequest, GroupOutcome, GroupRefusal, group_key_of

__all__ = [
    "CPV_DIVISION_LENGTH",
    "MINIMUM_COHORT_MEMBERS",
    "ProcurementValueContrastExtractor",
]

# TWO. The contrast rule (S-1) states the floor and this extractor does not
# raise it: a spread over two contracts is thin and says so through its own
# support count, and a higher threshold here would be a number nobody reviewed
# standing between real observations and a truthful summary.
MINIMUM_COHORT_MEMBERS = 2

# The CPV division: the first two digits, which is the coarsest level at which
# the source's own vocabulary separates subject areas. Chosen rather than the
# full 8-digit code because two contracts for `90911200` and `90911300` are
# cleaning services twice, and requiring exact equality would split a genuine
# cohort into singletons; chosen rather than nothing because `90` and `66` are
# cleaning and insurance and are not one market.
CPV_DIVISION_LENGTH = 2

_PARAMETER_NAMES = frozenset({"amount_type"})

# **`PAIRED_MONETARY_AMOUNT` and nothing temporal.** This is the whole reason a
# PARTIAL TED record is usable here: every one carries
# `PERIOD_TIMEZONE_NOT_ESTABLISHED`, which withholds `SOURCE_RELATIVE_ORDER` and
# `COMPARABLE_INSTANT`, and this derivation asks for neither.
_REQUIRED_FACTS = frozenset({SignalRequiredFact.PAIRED_MONETARY_AMOUNT})


class ProcurementValueContrastExtractor:
    """One cohort of comparable settled procurement values, contrasted."""

    extractor_id = "procurement-value-contrast"
    # 1.0.1 -- Mission 1.15.10. The scope carried the CPV codes of ONE member,
    # picked by amount order, and presented them as the cohort's. The first real
    # cohort had three members with three different codes -- 90911200/90911300,
    # 90715200, 90919300 -- so the scope named two codes that two of the three
    # contracts do not carry. A defect real data exposed and fixtures had not:
    # every fixture notice shared one code.
    #
    # A fix rather than a semantic change, and still a version bump, because the
    # same identity would otherwise produce different content -- which the model
    # reports as NON_DETERMINISTIC_OUTPUT rather than writing over.
    extractor_version = "1.0.1"
    signal_type_id = "procurement_value_contrast"
    record_kind_id = PROCUREMENT_NOTICE
    family = SignalQuantityFamily.TRANSACTION_VALUE

    # ------------------------------------------------------------ parameters

    def resolve(self, requested: Mapping[str, object]) -> SignalDerivation:
        """`amount_type` is REQUIRED, and the requirement is the design.

        A total value, a tender value, an estimated value and a framework
        maximum are four different facts. An extractor that swept all of them
        would produce one cohort per semantic anyway, and a default would pick
        the semantic for the caller -- which is how an estimate becomes a price
        somebody paid.
        """
        unknown = sorted(set(requested) - _PARAMETER_NAMES)
        if unknown:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"{unknown} affect nothing this extractor computes. A parameter "
                        "that is accepted and ignored is a hidden behaviour with a name"
                    ),
                )
            )
        amount_type = requested.get("amount_type")
        if not isinstance(amount_type, str) or not amount_type.strip():
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        "`amount_type` is required and names ONE monetary semantic. There "
                        "is no default: a total value, an estimated value and a framework "
                        "maximum are different facts, and choosing between them for the "
                        "caller is how an estimate becomes an amount somebody paid"
                    ),
                )
            )
        return SignalDerivation(
            extractor_id=self.extractor_id,
            extractor_version=self.extractor_version,
            kind=SignalDerivationKind.DETERMINISTIC,
            required_facts=_REQUIRED_FACTS,
            parameter_names=_PARAMETER_NAMES,
            parameters={"amount_type": amount_type},
        )

    # -------------------------------------------------------------- grouping

    def group_key(self, observation: NormalizedObservation) -> str | None:
        """One key per comparable cohort. Five dimensions, each load-bearing.

        **Notice class**, because a call for competition and a report of an
        outcome describe different procurement stages: an estimated value in a
        contract notice is what a buyer expected to spend, and a total value in
        an award notice is what a contract settled at.

        **Amount scope**, because a per-lot value and a whole-notice value are
        not the same quantity.

        **Currency**, because two currencies are never one distribution and no
        rate anybody reviewed exists to make them one.

        **CPV division**, because a cohort without a subject is a statement
        about a query. See the module docstring.

        The amount semantic is the derivation PARAMETER rather than a grouping
        dimension, so a run states which one it is about instead of silently
        emitting one signal per semantic.
        """
        if observation.record_kind_id != self.record_kind_id:
            return None
        notice = observation.section("notice")
        division = self._cpv_division(observation)
        if division is None:
            return None
        return group_key_of(
            [
                ("source_id", observation.source_id),
                ("record_kind_id", observation.record_kind_id),
                ("resource_id", observation.resource_id),
                ("notice_class", notice.get("class")),
                ("cpv_division", division),
            ]
        )

    @staticmethod
    def _cpv_division(observation: NormalizedObservation) -> str | None:
        """The single CPV division this notice is in, or `None`.

        A notice classified across SEVERAL divisions has no one subject, so it
        joins no cohort rather than joining the first division listed. Reading
        `codes[0]` would make the cohort depend on the order the source happened
        to publish the codes in.
        """
        classification = observation.section("classification")
        codes = classification.get("codes")
        if not isinstance(codes, list) or not codes:
            return None
        divisions = {
            str(entry.get("code"))[:CPV_DIVISION_LENGTH]
            for entry in codes
            if isinstance(entry, dict) and entry.get("code")
        }
        if len(divisions) != 1:
            return None
        return divisions.pop()

    # ---------------------------------------------------------------- derive

    def derive(
        self,
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        homogeneity = self._homogeneous(group)
        if homogeneity is not None:
            return GroupOutcome(refusals=(homogeneity,))

        wanted = str(derivation.parameters.get("amount_type"))
        members: list[tuple[NormalizedObservation, Decimal, str, str]] = []
        seen_keys: set[str] = set()
        for observation in group.observations:
            if observation.observation_key in seen_keys:
                return GroupOutcome(
                    refusals=(
                        GroupRefusal(
                            reason=SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE,
                            detail=(
                                f"{observation.observation_key!r} has more than one "
                                "normalized row in this cohort. Two rows for one "
                                "observation is D-08, and counting both would manufacture "
                                "a spread out of one contract"
                            ),
                            group_key=group.key,
                            observation_keys=group.observation_keys,
                        ),
                    )
                )
            seen_keys.add(observation.observation_key)
            entry = self._eligible_amount(observation, wanted)
            if entry is not None:
                members.append((observation, *entry))

        if len(members) < MINIMUM_COHORT_MEMBERS:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
                        detail=(
                            f"{len(members)} contract(s) in this cohort carry a "
                            f"{wanted!r} amount paired with exactly one currency; a "
                            f"contrast needs {MINIMUM_COHORT_MEMBERS}. One contract "
                            "stating an amount is an observation, not a derivation, and "
                            "lowering the floor would make it one by decree"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        currencies = {currency for _, _, currency, _ in members}
        if len(currencies) != 1:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INCOMPATIBLE_SERIES,
                        detail=(
                            f"this cohort mixes {sorted(currencies)}. Two currencies are "
                            "never one distribution, and there is no reviewed rate that "
                            "could make them one"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )
        scopes = {scope for _, _, _, scope in members}
        if len(scopes) != 1:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INCOMPATIBLE_SERIES,
                        detail=(
                            f"this cohort mixes amount scopes {sorted(scopes)}. A per-lot "
                            "value and a whole-notice value are not the same quantity"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        # By AMOUNT, then by observation key. A total order over values and
        # identities, and deliberately not over anything temporal: H-37 leaves
        # TED publication-date semantics unestablished, and a sort by date would
        # be the ordering this derivation must not need.
        ordered = tuple(sorted(members, key=lambda m: (m[1], m[0].observation_key)))
        return self._contrast(ordered, group, derivation, request, currencies.pop(), scopes.pop())

    # ---------------------------------------------------------------- checks

    def _homogeneous(self, group: CandidateGroup) -> GroupRefusal | None:
        if not group.observations:
            return None
        first = group.observations[0]
        expected = self.group_key(first)
        for observation in group.observations[1:]:
            if observation.record_kind_id != self.record_kind_id:
                return GroupRefusal(
                    reason=SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS,
                    detail=(
                        f"{observation.normalized_record_id} is a "
                        f"{observation.record_kind_id}; this extractor reads "
                        f"{self.record_kind_id}"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
            if self.group_key(observation) != expected:
                return GroupRefusal(
                    reason=SignalRefusalReason.INCOMPATIBLE_SERIES,
                    detail=(
                        f"{observation.observation_key!r} and {first.observation_key!r} do "
                        "not share a notice class, a resource and a CPV division. A "
                        "contrast across procurement subjects would summarise unrelated "
                        "contracts as one distribution"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
        return None

    def _eligible_amount(
        self, observation: NormalizedObservation, wanted: str
    ) -> tuple[Decimal, str, str] | None:
        """The one amount of the wanted semantic, or `None` with a reason recorded.

        Four ways an entry is refused, and none of them is a judgement:

        * a different semantic -- not this cohort's question;
        * `pairing != ESTABLISHED` -- H-38. The source publishes amounts and
          currencies as arrays and says nothing about their correspondence, so
          there is no amount here that can be read with a currency;
        * more than one amount or currency -- the same thing, restated by the
          data rather than by the flag;
        * a value that is not an exact decimal.
        """
        # `amounts` is a LIST, not a section mapping, so it is read from the
        # payload directly rather than through `section`.
        entries = observation.payload.get("amounts")
        if not isinstance(entries, list):
            return None
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("amount_type") != wanted:
                continue
            if entry.get("pairing") != "ESTABLISHED":
                return None
            amounts = entry.get("amounts")
            currencies = entry.get("currencies")
            if not isinstance(amounts, list) or not isinstance(currencies, list):
                return None
            if len(amounts) != 1 or len(currencies) != 1:
                return None
            value = decimal_from(amounts[0])
            if value is None:
                return None
            scope = entry.get("scope")
            if not isinstance(scope, str) or not isinstance(currencies[0], str):
                return None
            return value, currencies[0], scope
        return None

    # ------------------------------------------------------------- contrast

    def _contrast(
        self,
        ordered: tuple[tuple[NormalizedObservation, Decimal, str, str], ...],
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
        currency: str,
        amount_scope: str,
    ) -> GroupOutcome:
        observations = tuple(member[0] for member in ordered)
        inputs = tuple(o.to_input() for o in observations)
        resolution = inputs[0].period_type
        assessment = assess_inputs(inputs, derivation, family=self.family, resolution=resolution)
        if assessment.refusal is not None:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=assessment.refusal.reason,
                        detail=assessment.refusal.detail,
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        values = [member[1] for member in ordered]
        notice = observations[0].section("notice")
        # The UNION across every member, not the first member's. The cohort is
        # keyed on the CPV division, so its members share a division and differ
        # below it -- and a scope naming one member's codes describes that
        # member rather than the cohort.
        classification_codes = tuple(
            sorted(
                {
                    str(entry.get("code"))
                    for observation in observations
                    for entry in _codes_of(observation)
                    if isinstance(entry, dict) and entry.get("code")
                }
            )
        )
        window = SignalWindow(
            # NONE. The members are related by being comparable, and by nothing
            # temporal. Not SAME_PERIOD_LABEL either: they were published on
            # whatever days they were published, and this derivation neither
            # knows nor needs that.
            #
            # The labels are still carried, because the model requires a window
            # to say which source periods it covered and that is PROVENANCE. The
            # basis is what says none of it was used as a relation, and no bound
            # is carried, so nothing here places a notice on a timeline (H-37).
            basis=SignalTemporalBasis.NONE,
            period_labels=tuple(o.period_label for o in observations),
            resolution=resolution,
            observation_count=len(ordered),
        )
        draft = build_signal(
            workspace_id=request.workspace_id,
            signal_type_id=self.signal_type_id,
            observations=inputs,
            derivation=derivation,
            # Required to be NOT_APPLICABLE under a NONE basis, and correct on
            # its own terms: a spread is not a movement.
            direction=SignalDirection.NOT_APPLICABLE,
            magnitude=SignalMagnitude(
                # max - min, exactly. `ABSOLUTE_DIFFERENCE` rather than
                # `ABSOLUTE_CHANGE`: nothing changed, and the temporal kind
                # would assert a movement H-37 leaves unestablished.
                value=values[-1] - values[0],
                kind=SignalMagnitudeKind.ABSOLUTE_DIFFERENCE,
                unit=currency,
                # The currency IS the unit, carried up from the inputs rather
                # than named here. A dimensionless spread over money would lose
                # the one fact that makes it readable.
                unit_state=SignalMagnitudeUnitState.INHERITED,
            ),
            derivation_confidence=1.0,
            scope=SignalScope(
                source_ids=(observations[0].source_id,),
                amount_types=(str(derivation.parameters.get("amount_type")),),
                amount_scopes=(amount_scope,),
                currencies=(currency,),
                notice_classes=(str(notice.get("class")),),
                classification_codes=classification_codes,
                classification_scheme="CPV",
            ),
            window=window,
            derived_at=request.derived_at,
            expires_at=request.expires_at,
            correlation_id=request.correlation_id,
            research_session_id=request.research_session_id,
        )
        return GroupOutcome(drafts=(draft,))


def _codes_of(observation: NormalizedObservation) -> list[object]:
    """The classification entries of one observation, or an empty list."""
    codes = observation.section("classification").get("codes")
    return codes if isinstance(codes, list) else []
