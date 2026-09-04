"""One item's request count across adjacent days; everything else refused. Mission 1.19.

**No network and no database.** Observations are built from the shape
`wikimedia-pageview@1.0.0` produces, so the extractor is exercised against the
payload it will actually read.

The properties this file exists to protect:

    one day's count is an observation, not a Signal
    two REQUESTER CLASSES never become one series
    two ITEMS never become one series
    a gap is never bridged (ADR-023)
    a request count never carries a metric, and the model enforces it
    the calendar confounder is named rather than discovered later
    and none of it is called attention, adoption or demand
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sros_contracts import (
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
from sros_nlp.extractors.content_request_change import ContentRequestChangeExtractor
from sros_nlp.observations import NormalizedObservation
from sros_signal_model import SignalRefusedError

EXTRACTOR_SOURCE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "sros_nlp"
    / "extractors"
    / "content_request_change.py"
)

MOMENT = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
WORKSPACE = "11111111-1111-1111-1111-111111111111"

# The real sample, by article and UTC day. 2024-03-02 and 2024-03-03 are a
# Saturday and a Sunday, and both larger articles fall roughly 40 per cent
# across them. That is the confounder this extractor's docstring names, and it
# is kept here as data so the tests reason about what the source actually
# published rather than about invented numbers.
REAL_KUBERNETES = {
    "2024-03-01": 2058,
    "2024-03-02": 1188,
    "2024-03-03": 1139,
    "2024-03-04": 2051,
    "2024-03-05": 2101,
    "2024-03-06": 2183,
    "2024-03-07": 2133,
}


def observation(
    day: str,
    views: int,
    *,
    article: str = "Kubernetes",
    agent: str = "user",
    access: str = "all-access",
    platform: str = "en.wikipedia.org",
    quality: NormalizedRecordQuality = NormalizedRecordQuality.VALID,
) -> NormalizedObservation:
    """One normalized article-day, shaped as `wikimedia-pageview@1.0.0` writes it."""
    start = datetime.fromisoformat(day).replace(tzinfo=UTC)
    return NormalizedObservation(
        normalized_record_id=f"n-{article}-{agent}-{day}",
        raw_record_id=f"r-{article}-{agent}-{day}",
        source_id="wikimedia-pageviews",
        observation_key=f"wikimedia-pageviews|{platform}|{agent}|{article}|{day}",
        record_kind_id="content_request_count",
        quality=quality,
        quality_reasons=frozenset(),
        payload={
            "record_kind": "content_request_count",
            "content": {"id": article, "platform": platform, "url": None},
            "audience": {
                "class": agent,
                "access_channel": access,
                "semantics": "the platform's own class for traffic it did not attribute…",
            },
            "period": {
                "type": "DAY",
                "label": day,
                "start": start.isoformat(),
                "end": (start + timedelta(days=1)).isoformat(),
                "end_inclusive": False,
                "timezone_state": "ESTABLISHED",
            },
            "observation": {
                "count": views,
                "unit": "requests",
                "semantics": "a count of requests for the page that received HTTP 200 or 304…",
            },
            "subject": None,
        },
    )


@pytest.fixture
def extractor() -> ContentRequestChangeExtractor:
    return ContentRequestChangeExtractor()


@pytest.fixture
def request_() -> DerivationRequest:
    return DerivationRequest(
        workspace_id=WORKSPACE,
        correlation_id="mission-1.19-test",
        derived_at=MOMENT,
        expires_at=MOMENT + timedelta(days=365),
        research_session_id=None,
    )


def derive(extractor, request_, observations):
    derivation = extractor.resolve({})
    key = extractor.group_key(observations[0], extractor.resolve({})) or "group"
    group = CandidateGroup(key=key, observations=tuple(observations))
    return extractor.derive(group, derivation, request_)


def real_days(*labels: str):
    return [observation(day, REAL_KUBERNETES[day]) for day in labels]


# ============================================================== the derivation


class TestOnePairIsOneSignal:
    def test_two_adjacent_days_derive_one_signal(self, extractor, request_) -> None:
        outcome = derive(extractor, request_, real_days("2024-03-03", "2024-03-04"))
        assert len(outcome.drafts) == 1
        assert outcome.refusals == ()
        draft = outcome.drafts[0]
        assert draft.magnitude.value == Decimal(2051 - 1139)
        assert draft.direction is SignalDirection.INCREASING

    def test_seven_days_derive_six_adjacent_pairs(self, extractor, request_) -> None:
        """ADJACENT pairs, deliberately not every combination. Over seven days
        that is six signals; day1 to day7 is a different question and would need
        a strategy that says so."""
        outcome = derive(extractor, request_, real_days(*sorted(REAL_KUBERNETES)))
        assert len(outcome.drafts) == 6
        assert outcome.refusals == ()

    def test_one_day_is_an_observation_not_a_signal(self, extractor, request_) -> None:
        outcome = derive(extractor, request_, real_days("2024-03-01"))
        assert outcome.drafts == ()
        assert outcome.refusals[0].reason is SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS

    def test_the_magnitude_is_exact_and_carries_the_source_unit(self, extractor, request_) -> None:
        draft = derive(extractor, request_, real_days("2024-03-01", "2024-03-02")).drafts[0]
        assert draft.magnitude.value == Decimal(1188 - 2058)
        assert draft.magnitude.kind is SignalMagnitudeKind.ABSOLUTE_CHANGE
        assert draft.magnitude.unit == "requests"
        assert draft.magnitude.unit_state is SignalMagnitudeUnitState.INHERITED

    def test_no_percentage_and_no_ratio(self, extractor, request_) -> None:
        """A percentage needs a denominator rule and a rounding rule, and a
        repeating decimal rounded to an unstated precision is fake precision."""
        draft = derive(extractor, request_, real_days("2024-03-03", "2024-03-04")).drafts[0]
        assert draft.magnitude.kind is not SignalMagnitudeKind.RATIO

    def test_an_unchanged_count_is_a_signal_with_no_direction_claim(
        self, extractor, request_
    ) -> None:
        pair = [observation("2024-03-01", 500), observation("2024-03-02", 500)]
        draft = derive(extractor, request_, pair).drafts[0]
        assert draft.direction is SignalDirection.UNCHANGED
        assert draft.magnitude.value == Decimal(0)


# ============================================================ what stays apart


class TestTwoPopulationsNeverBecomeOneSeries:
    def test_the_requester_class_is_part_of_the_group_key(self, extractor) -> None:
        """The field easiest to drop and worst to drop. `user` and `all-agents`
        are different counts of the same article-day, and a group that mixed
        them would subtract one population from another."""
        user = extractor.group_key(
            observation("2024-03-01", 100, agent="user"), extractor.resolve({})
        )
        every = extractor.group_key(
            observation("2024-03-01", 400, agent="all-agents"), extractor.resolve({})
        )
        assert user != every

    def test_mixing_requester_classes_is_refused_not_averaged(self, extractor, request_) -> None:
        mixed = [
            observation("2024-03-01", 100, agent="user"),
            observation("2024-03-02", 400, agent="all-agents"),
        ]
        outcome = derive(extractor, request_, mixed)
        assert outcome.drafts == ()
        assert outcome.refusals[0].reason is SignalRefusalReason.INCOMPATIBLE_SERIES

    def test_two_items_are_never_one_series(self, extractor, request_) -> None:
        mixed = [
            observation("2024-03-01", 2058, article="Kubernetes"),
            observation("2024-03-02", 1014, article="Docker_(software)"),
        ]
        outcome = derive(extractor, request_, mixed)
        assert outcome.drafts == ()
        assert outcome.refusals[0].reason is SignalRefusalReason.INCOMPATIBLE_SERIES

    def test_two_access_channels_are_never_one_series(self, extractor) -> None:
        a = extractor.group_key(
            observation("2024-03-01", 100, access="all-access"), extractor.resolve({})
        )
        b = extractor.group_key(
            observation("2024-03-01", 60, access="desktop"), extractor.resolve({})
        )
        assert a != b

    def test_another_record_kind_is_refused_by_kind(self, extractor, request_) -> None:
        other = observation("2024-03-01", 100)
        object.__setattr__(other, "record_kind_id", "numeric_observation")
        outcome = derive(extractor, request_, [observation("2024-03-02", 100), other])
        assert outcome.refusals[0].reason is SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS


# ================================================================ adjacency


class TestAGapIsNeverBridged:
    def test_two_days_apart_is_refused(self, extractor, request_) -> None:
        """ADR-023. A change computed across a day nobody read is
        indistinguishable from one that happened, and a daily request series has
        gaps whenever an item drew no requests at all."""
        outcome = derive(extractor, request_, real_days("2024-03-01", "2024-03-03"))
        assert outcome.drafts == ()
        assert outcome.refusals[0].reason is SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS

    def test_a_gap_refuses_only_the_pair_that_spans_it(self, extractor, request_) -> None:
        """The other adjacent pairs are still derivable. A gap invalidates the
        derivation across it, not the whole series."""
        outcome = derive(extractor, request_, real_days("2024-03-01", "2024-03-02", "2024-03-04"))
        assert len(outcome.drafts) == 1
        assert len(outcome.refusals) == 1
        assert outcome.refusals[0].reason is SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS

    def test_a_missing_day_never_becomes_a_zero(self, extractor, request_) -> None:
        """The counterpart of the collector's 404 rule, one layer up: no code
        path here invents a count for a period nobody read."""
        outcome = derive(extractor, request_, real_days("2024-03-01", "2024-03-04"))
        assert outcome.drafts == ()
        assert all(d.magnitude.value != Decimal(0) for d in outcome.drafts)

    def test_two_rows_for_one_day_are_ambiguous_lineage(self, extractor, request_) -> None:
        pair = [observation("2024-03-01", 100), observation("2024-03-01", 101)]
        outcome = derive(extractor, request_, pair)
        assert outcome.refusals[0].reason is SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE


# ================================================================ the scope


class TestTheScopeSaysWhatItIsAbout:
    def test_it_names_the_item_platform_and_requester_class(self, extractor, request_) -> None:
        draft = derive(extractor, request_, real_days("2024-03-03", "2024-03-04")).drafts[0]
        assert draft.scope.content_ids == ("Kubernetes",)
        assert draft.scope.content_platforms == ("en.wikipedia.org",)
        assert draft.scope.audience_classes == ("user",)
        assert draft.scope.access_channels == ("all-access",)

    def test_it_carries_no_metric_and_no_geography(self, extractor, request_) -> None:
        """ADR-032. A request count is not an instance of a measured series and
        carries no place. The MODEL refuses a metric here, which is the
        enforcement; this asserts the extractor does not try."""
        draft = derive(extractor, request_, real_days("2024-03-03", "2024-03-04")).drafts[0]
        assert draft.scope.metric_ids == ()
        assert draft.scope.geography_codes == ()
        assert draft.scope.terms == ()

    def test_the_family_is_the_new_one(self, extractor) -> None:
        assert extractor.family is SignalQuantityFamily.CONTENT_REQUEST_VOLUME

    def test_the_window_is_on_a_shared_timeline(self, extractor, request_) -> None:
        """COMPARABLE_INSTANTS, which this source earns and GDELT does not: the
        day bucket's timezone is ESTABLISHED on the platform's documentation."""
        draft = derive(extractor, request_, real_days("2024-03-03", "2024-03-04")).drafts[0]
        assert draft.window.basis is SignalTemporalBasis.COMPARABLE_INSTANTS
        assert draft.window.period_labels == ("2024-03-03", "2024-03-04")


# ============================================================== the boundary


class TestNothingHereInterprets:
    def test_the_derivation_confidence_is_about_the_arithmetic(self, extractor, request_) -> None:
        draft = derive(extractor, request_, real_days("2024-03-03", "2024-03-04")).drafts[0]
        assert draft.derivation_confidence == 1.0

    def test_no_word_in_this_module_names_a_conclusion(self) -> None:
        """Over the CODE, excluding docstrings and comments -- the same shape
        `validate_normalization` uses. The prose above deliberately contains
        "demand" and "adoption" in order to refuse them, and a substring scan
        over the file would fail on the sentence that states the rule."""
        tree = ast.parse(EXTRACTOR_SOURCE.read_text(encoding="utf-8"))
        # Excluded BY NODE IDENTITY, not by comparing text: `ast.get_docstring`
        # returns a cleaned string that never equals the raw constant, so a
        # text comparison would silently exclude nothing and this test would
        # fail on the paragraph that states the rule.
        docstring_nodes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef):
                body = getattr(node, "body", [])
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    docstring_nodes.add(id(body[0].value))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstring_nodes
            ):
                value = node.value.lower()
                for forbidden in ("demand", "adoption", "popularity", "attention", "market"):
                    assert forbidden not in value, (forbidden, value[:90])

    def test_the_extractor_reads_no_clock_and_converts_no_timezone(self) -> None:
        tree = ast.parse(EXTRACTOR_SOURCE.read_text(encoding="utf-8"))
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        for forbidden in ("now", "utcnow", "astimezone", "localtime", "today"):
            assert forbidden not in called, forbidden

    def test_it_is_registered_under_its_own_id(self) -> None:
        assert EXTRACTOR_REGISTRY["content-request-change"].extractor_version == "1.0.0"


# =========================================================== the parameters


class TestParameters:
    def test_an_unimplemented_pairing_strategy_is_refused(self, extractor) -> None:
        with pytest.raises(SignalRefusedError):
            extractor.resolve({"pairing_strategy": "every_combination"})

    def test_a_parameter_that_affects_nothing_is_refused(self, extractor) -> None:
        """A parameter accepted and ignored is a hidden behaviour with a name."""
        with pytest.raises(SignalRefusedError):
            extractor.resolve({"minimum_views": 50})
