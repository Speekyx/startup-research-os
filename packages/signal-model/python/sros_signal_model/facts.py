"""Which canonical facts a derivation may require, and what withholds each one.

`signal-contract-v1.md` §10, Mission 1.11 §10 and §11.

The rule this module exists to enforce is that **`PARTIAL` does not mean
unusable**. A normalized record's quality state says whether the source
observation could be structurally represented; it does not say whether the thing
that is missing matters to the derivation in front of it. Every GDELT record is
`PARTIAL`, and a contrast between two terms in one bucket needs neither of the
two facts it is missing.

So a derivation declares what it requires and this module computes what each
input withholds -- from that record's own quality reasons and its record kind.
Neither side guesses.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sros_contracts import (
    NormalizationQualityReason as Reason,
)
from sros_contracts import (
    SignalRequiredFact as Fact,
)

__all__ = [
    "CONTENT_REQUEST_COUNT",
    "FACT_RULES",
    "LEXICAL_FREQUENCY_OBSERVATION",
    "NUMERIC_OBSERVATION",
    "ORDER_ESTABLISHED_WITHOUT_TIMEZONE",
    "FactRule",
    "TemporalOrderCertification",
    "order_certification",
    "withheld_facts",
]

# The two canonical record kinds that exist (`normalized-record-v1.md` §4).
# Named rather than imported: `sros_acquisition` is a service package and this
# is a shared model, so the dependency would run the wrong way.
NUMERIC_OBSERVATION = "numeric_observation"
LEXICAL_FREQUENCY_OBSERVATION = "lexical_frequency_observation"
# The third, added in Mission 1.15.8 and reachable by a derivation since 1.15.9.
PROCUREMENT_NOTICE = "procurement_notice"
# The fifth kind and the fourth reachable one, added in Mission 1.19 (ADR-032).
CONTENT_REQUEST_COUNT = "content_request_count"


@dataclass(frozen=True)
class FactRule:
    """Which record kinds can supply a fact, and which reasons withhold it.

    `withheld_by` may be empty and the rule is still load-bearing: `LEXICAL_TERM`
    is withheld by no quality reason and is supplied by exactly one record kind,
    so a derivation asking for it over a numeric observation is refused rather
    than reading a field that is not there.
    """

    supplied_by: frozenset[str]
    withheld_by: frozenset[Reason]


_BOTH_KINDS = frozenset({NUMERIC_OBSERVATION, LEXICAL_FREQUENCY_OBSERVATION})
# Mission 1.19. The kinds that carry a countable quantity over a period. Named
# separately from `_BOTH_KINDS` rather than folded into it, because the facts a
# content request count supplies are a STRICT SUBSET of what a numeric
# observation supplies -- it has no geography and no term -- and a single widened
# constant would have granted it those by omission.
_COUNTING_KINDS = frozenset({*_BOTH_KINDS, CONTENT_REQUEST_COUNT})

FACT_RULES: Mapping[Fact, FactRule] = MappingProxyType(
    {
        Fact.EXACT_NUMERIC_VALUE: FactRule(
            supplied_by=_COUNTING_KINDS,
            withheld_by=frozenset({Reason.VALUE_NOT_REPORTED, Reason.MALFORMED_NUMERIC_VALUE}),
        ),
        Fact.LEXICAL_TERM: FactRule(
            supplied_by=frozenset({LEXICAL_FREQUENCY_OBSERVATION}),
            withheld_by=frozenset(),
        ),
        # Needs no timezone. String equality over a value the source published.
        Fact.SOURCE_PERIOD_LABEL: FactRule(
            supplied_by=_COUNTING_KINDS,
            withheld_by=frozenset({Reason.PERIOD_NOT_SUPPORTED}),
        ),
        # ORDER and GLOBAL INSTANT are different questions. This one is withheld
        # by an unestablished timezone ONLY because no source is certified below;
        # a certification would grant it without anyone asserting a zone (H-32).
        Fact.SOURCE_RELATIVE_ORDER: FactRule(
            supplied_by=_COUNTING_KINDS,
            withheld_by=frozenset(
                {Reason.PERIOD_NOT_SUPPORTED, Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED}
            ),
        ),
        Fact.COMPARABLE_INSTANT: FactRule(
            supplied_by=_COUNTING_KINDS,
            withheld_by=frozenset(
                {Reason.PERIOD_NOT_SUPPORTED, Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED}
            ),
        ),
        Fact.SOURCE_LANGUAGE_LABEL: FactRule(
            supplied_by=frozenset({LEXICAL_FREQUENCY_OBSERVATION}),
            withheld_by=frozenset(),
        ),
        Fact.CANONICAL_LANGUAGE: FactRule(
            supplied_by=frozenset({LEXICAL_FREQUENCY_OBSERVATION}),
            withheld_by=frozenset({Reason.LANGUAGE_NOT_MAPPED}),
        ),
        Fact.CLASSIFIED_GEOGRAPHY: FactRule(
            supplied_by=frozenset({NUMERIC_OBSERVATION}),
            withheld_by=frozenset({Reason.GEOGRAPHY_NOT_CLASSIFIED, Reason.GEOGRAPHY_MISSING}),
        ),
        # Mission 1.15.9. An amount that says what KIND of amount it is and
        # carries exactly one currency.
        #
        # **The two reasons that withhold it are the two Mission 1.15.8 added**,
        # and the mapping is the whole point of this table being mechanical: a
        # source that publishes amounts and currencies as arrays, and says
        # nothing about their positional correspondence, has not supplied a
        # paired amount (H-38).
        #
        # **`PERIOD_TIMEZONE_NOT_ESTABLISHED` is deliberately ABSENT.** Every TED
        # record carries it and is therefore PARTIAL, and a monetary fact does
        # not stop being one because the publication date's offset means
        # something nobody established. This is the second production case of
        # the rule §10 of the contract exists for: what matters is whether the
        # SPECIFIC missing fact matters to the SPECIFIC derivation.
        Fact.PAIRED_MONETARY_AMOUNT: FactRule(
            supplied_by=frozenset({PROCUREMENT_NOTICE}),
            withheld_by=frozenset(
                {Reason.MONETARY_PAIRING_NOT_ESTABLISHED, Reason.MONETARY_CURRENCY_ABSENT}
            ),
        ),
    }
)


@dataclass(frozen=True)
class TemporalOrderCertification:
    """A reviewed finding that one publication stream's labels are ordered.

    Mission 1.12, ADR-022. It certifies **B without C**: two labels from this
    stream can be placed in chronological order, and neither can be placed on a
    timeline shared with anything else.

    Every field is part of the scope rather than decoration:

        source_id      whose stream
        resource_ids   WHICH resources, named exactly. Never a prefix: the
                       WEB-NGRAM directory also publishes a `chargram` file that
                       no review has assessed, and a prefix match on
                       `web-ngrams/` would have silently covered it
        label_scheme   the shape being certified, so a source publishing two
                       label schemes cannot have one inherit the other's finding
        review_version which review established it
        basis          the retrieved evidence. Mandatory, for the reason a
                       geography map entry records one: a certification nobody
                       can re-check is a guess with a citation field
        scope          what it does NOT grant, in words, next to what it does
    """

    source_id: str
    resource_ids: frozenset[str]
    label_scheme: str
    review_version: int
    basis: str
    scope: str

    def __post_init__(self) -> None:
        if not self.resource_ids:
            raise ValueError(
                "a certification names the resources it covers. An entry covering "
                "nothing grants nothing, and one covering everything is not a finding"
            )
        if not self.basis.strip():
            raise ValueError(
                "a temporal order certification records the evidence that established "
                "it. Ordering asserted with no basis is the inference this mechanism "
                "exists to replace"
            )

    def covers(self, source_id: str, resource_id: str | None) -> bool:
        """Whether this certification applies to one observation.

        A record with no resource id is NOT covered. Ordering is a property of a
        publication stream, and an observation that cannot say which stream it
        came from cannot claim one stream's finding.
        """
        return source_id == self.source_id and resource_id in self.resource_ids


# Streams whose order is established WITHOUT a timezone being established.
#
# Mission 1.11 left this EMPTY and was right to: the argument available then --
# a fixed-width stamp sorts lexicographically and the stamp is a filename that
# cannot repeat inside a directory -- was an inference about the publisher's
# mechanism rather than a retrieved statement about the data.
#
# Mission 1.12 retrieved the statements. GDELT's own BigQuery analysis over
# `gdelt-bq.gdeltv2.web_1grams` uses DATE as a chronological axis; its own
# MASTERFILELIST is sequenced by the label at 15-minute resolution across 7.6
# years; and its own LASTUPDATE names the maximal label as the newest
# publication. `gdelt-web-ngram-temporal-evidence-v1.md` §2 sets it out.
#
# An entry remains a REVIEWED FINDING carrying its basis, exactly as an entry in
# the geography map does. Adding one on the strength of it being obvious is
# still the move `geography-mapping-v1.json` exists to prevent.
ORDER_ESTABLISHED_WITHOUT_TIMEZONE: tuple[TemporalOrderCertification, ...] = (
    TemporalOrderCertification(
        source_id="gdelt",
        resource_ids=frozenset({"web-ngrams/1gram", "web-ngrams/2gram"}),
        label_scheme="gdelt-web-ngram-bucket",
        review_version=3,
        basis=(
            "GDELT's own published BigQuery analysis over gdelt-bq.gdeltv2.web_1grams "
            "reads SUBSTR(DATE,0,8) as a calendar day and ORDER BY DATE ASC to chart a "
            "nine-month series; MASTERFILELIST.TXT is published in ascending label "
            "order at 15-minute resolution from 20190101000000 to the current bucket; "
            "LASTUPDATE.TXT names the maximal label as the newest publication. "
            "Retrieved 2026-08-30, gdelt-web-ngram-temporal-evidence-v1.md"
        ),
        scope=(
            "Grants SOURCE_RELATIVE_ORDER within this stream only. Grants NO timezone, "
            "NO COMPARABLE_INSTANT, NO observed_at and NO comparison with any other "
            "source. H-29 remains open"
        ),
    ),
)


def order_certification(
    source_id: str, resource_id: str | None
) -> TemporalOrderCertification | None:
    """The certification covering this observation, or `None`.

    Fails closed: an unreviewed source, an unreviewed resource, or an
    observation that cannot say which resource it came from gets nothing.
    """
    for certification in ORDER_ESTABLISHED_WITHOUT_TIMEZONE:
        if certification.covers(source_id, resource_id):
            return certification
    return None


def withheld_facts(
    required: frozenset[Fact],
    *,
    record_kind_id: str,
    quality_reasons: frozenset[Reason],
    source_id: str,
    resource_id: str | None = None,
) -> frozenset[Fact]:
    """The required facts this record cannot supply.

    Two independent ways to withhold a fact, and they answer different
    questions: the record KIND says whether the field exists at all, and the
    quality REASONS say whether the value in it was established.

    `resource_id` defaults to `None` and that default is a REFUSAL, not a
    convenience: a caller that does not say which resource an observation came
    from gets no ordering certification.
    """
    order_certified = order_certification(source_id, resource_id) is not None
    withheld: set[Fact] = set()
    for fact in required:
        rule = FACT_RULES[fact]
        if record_kind_id not in rule.supplied_by:
            withheld.add(fact)
            continue
        blocking = rule.withheld_by
        if (
            fact is Fact.SOURCE_RELATIVE_ORDER
            and order_certified
            and blocking & quality_reasons == {Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED}
        ):
            # The zone is unestablished and the ORDER is separately certified for
            # this source, which is the whole point of keeping the two apart.
            continue
        if blocking & quality_reasons:
            withheld.add(fact)
    return frozenset(withheld)
