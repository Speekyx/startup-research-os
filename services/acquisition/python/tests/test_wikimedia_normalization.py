"""The content-request-count normalizer. Mission 1.19.

What this suite is organised around, and each is a way a request count could
quietly become something it is not:

    the kind is named for a SHAPE      -- not for the first platform to reach it
    the requester class is REQUIRED    -- two populations cannot wear one name
    the period is a UTC DAY            -- an interval, established on documentation
    "requests", never "views"          -- the payload states its own semantics
    a per-person field is REFUSED      -- not stripped, because it was fetched
    and no field anywhere says reader, user, demand or adoption
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sros_acquisition.normalization.errors import NormalizationFailedError
from sros_acquisition.normalization.geography import GeographyMap
from sros_acquisition.normalization.model import RECORD_KINDS, RawRecordView
from sros_acquisition.normalization.normalizers import NormalizationContext
from sros_acquisition.normalization.wikimedia_pageviews import (
    WM_NORMALIZER_ID,
    WM_NORMALIZER_VERSION,
    WikimediaPageviewNormalizer,
)
from sros_acquisition.registry.retention import EffectiveRetention

MOMENT = datetime(2026, 9, 2, 12, 0, 0, tzinfo=UTC)
WORKSPACE = "00000000-0000-4000-8000-0000000000aa"
ARTICLE_URL = "https://en.wikipedia.org/wiki/Kubernetes"

RETENTION = EffectiveRetention(
    raw_days=30,
    normalized_days=365,
    aggregate_permitted=True,
    raw_source="baseline",
    normalized_source="baseline",
)

# Empty on purpose. A request count has no geography, and handing this adapter a
# populated map would suggest it consults one.
NO_GEOGRAPHY = GeographyMap(canonical_scheme="ISO-3166-1-alpha-2", entries={})


def raw(**overrides: object) -> RawRecordView:
    """One raw record, shaped as `read_raw_records` returns it."""
    payload: dict[str, object] = {
        "project": "en.wikipedia",
        "article": "Kubernetes",
        "granularity": "daily",
        "timestamp": "2024030100",
        "access": "all-access",
        "agent": "user",
        "views": 2058,
    }
    payload.update(overrides.pop("payload_extra", {}))  # type: ignore[arg-type]
    for key in overrides.pop("payload_drop", ()):  # type: ignore[union-attr]
        payload.pop(key, None)
    provenance: dict[str, object] = {
        "source_id": "wikimedia-pageviews",
        "resource_id": "metrics/pageviews/per-article/en.wikipedia.org",
        "project": "en.wikipedia.org",
        "article": "Kubernetes",
        "agent": "user",
        "access": "all-access",
        "use_profile": "local-private-research-v1",
        "attribution": {
            "text": "Wikimedia Foundation, Wikimedia Analytics API CC0 1.0",
            "elements": [
                {"element": "SOURCE_CREDIT", "value": "Wikimedia Foundation"},
                {"element": "LICENCE_IDENTIFIER", "value": "CC0 1.0"},
                {"element": "SOURCE_ITEM_LINK", "value": ARTICLE_URL},
            ],
        },
        "review_version": 1,
    }
    provenance.update(overrides.pop("provenance_extra", {}))  # type: ignore[arg-type]
    if "provenance" in overrides:
        provenance = overrides.pop("provenance")  # type: ignore[assignment]
    base: dict[str, object] = {
        "record_id": "22222222-2222-4222-8222-222222222222",
        "workspace_id": WORKSPACE,
        "research_session_id": None,
        "source_id": "wikimedia-pageviews",
        "observation_key": "wikimedia-pageviews|en.wikipedia.org|user|Kubernetes|2024030100",
        "content_hash": "sha256:deadbeef",
        "acquisition_method": "OFFICIAL_API",
        "payload": payload,
        "provenance": provenance,
        "review_version": 1,
        "collector_id": "wikimedia-pageviews-per-article",
        "collector_version": "1.0.0",
        "correlation_id": "mission-1.19-test",
        "collected_at": MOMENT,
        "observed_at": None,
        "expires_at": MOMENT,
    }
    base.update(overrides)
    return RawRecordView(**base)  # type: ignore[arg-type]


@pytest.fixture
def normalizer() -> WikimediaPageviewNormalizer:
    return WikimediaPageviewNormalizer(
        NormalizationContext(retention=RETENTION, geography=NO_GEOGRAPHY)
    )


def run(normalizer, record: RawRecordView | None = None):
    return normalizer.normalize(
        record if record is not None else raw(),
        correlation_id="mission-1.19-test",
        normalized_at=MOMENT,
    )


# ============================================================ the record kind


class TestTheRecordKindIsGenericAndNew:
    def test_content_request_count_is_registered(self) -> None:
        assert "content_request_count" in RECORD_KINDS

    def test_it_is_not_named_after_the_platform_that_reached_it(self) -> None:
        joined = " ".join(RECORD_KINDS)
        assert "wikimedia" not in joined
        assert "pageview" not in joined

    def test_the_name_says_request_and_not_view(self) -> None:
        """The platform's own definition is a REQUEST that received 200 or 304.
        "View" implies a person looked, and in the VOCABULARY that implication
        is one nothing downstream could unmake."""
        kind = RECORD_KINDS["content_request_count"]
        assert "observation.count" in kind.required
        assert not any("view" in field for field in (*kind.required, *kind.optional))

    def test_the_requester_class_is_required_not_optional(self) -> None:
        """The one design decision worth arguing. The same item on the same day
        carries a different count for `user` than for `all-agents`; a record
        that could not say which it held would be two measurements wearing one
        name."""
        assert "audience.class" in RECORD_KINDS["content_request_count"].required

    def test_it_did_not_widen_an_existing_kind(self) -> None:
        assert RECORD_KINDS["numeric_observation"].required == (
            "metric.id",
            "period",
            "geography.source_code",
            "observation.value_state",
        )
        assert "content.id" not in RECORD_KINDS["lexical_frequency_observation"].required


# ============================================================== normalization


class TestOneArticleDayBecomesOneObservation:
    def test_the_identity_and_kind_are_the_sources_own(self, normalizer) -> None:
        draft = run(normalizer)
        assert draft.record_kind_id == "content_request_count"
        assert draft.payload["content"]["id"] == "Kubernetes"
        assert draft.payload["content"]["platform"] == "en.wikipedia.org"

    def test_the_count_is_carried_with_its_unit_and_its_semantics(self, normalizer) -> None:
        observation = run(normalizer).payload["observation"]
        assert observation["count"] == 2058
        assert observation["unit"] == "requests"
        assert "Not readers, not people" in str(observation["semantics"])

    def test_the_requester_class_is_carried_with_its_caveat(self, normalizer) -> None:
        """`user` means "not identified as automated", never "human", and the
        platform documents its own detection as heuristic."""
        audience = run(normalizer).payload["audience"]
        assert audience["class"] == "user"
        assert "never 'human'" in str(audience["semantics"])
        assert "heuristic" in str(audience["semantics"])

    def test_the_period_is_an_established_utc_day(self, normalizer) -> None:
        """ESTABLISHED on the operator's documentation rather than on the shape
        of the value. GDELT's H-29 stays open for the opposite reason: nothing
        there states the zone at all."""
        payload = run(normalizer).payload
        assert payload["period"]["type"] == "DAY"
        assert payload["period"]["timezone_state"] == "ESTABLISHED"
        assert payload["period"]["start"] == "2024-03-01T00:00:00+00:00"
        assert payload["period"]["end"] == "2024-03-02T00:00:00+00:00"
        assert payload["period"]["end_inclusive"] is False

    def test_observed_at_is_the_intervals_start_and_not_an_event_time(self, normalizer) -> None:
        """A day is an interval, not a moment -- the same treatment a World Bank
        year gets. The start bound must never be read as the instant a request
        happened."""
        draft = run(normalizer)
        assert draft.observed_at == datetime(2024, 3, 1, tzinfo=UTC)
        assert draft.payload["period"]["type"] != "INSTANT"

    def test_every_record_is_valid_and_the_adapter_has_no_partial_branch(self, normalizer) -> None:
        """Every GDELT record is PARTIAL for H-29 and H-30, every TED record for
        H-37. Nothing of that kind is open here."""
        assert run(normalizer).quality.value == "VALID"

    def test_the_platform_comes_from_provenance_not_from_parsing_a_url(self, normalizer) -> None:
        record = raw(provenance_extra={"project": "fr.wikipedia.org"})
        assert run(normalizer, record).payload["content"]["platform"] == "fr.wikipedia.org"

    def test_the_item_url_is_read_from_the_rendered_attribution(self, normalizer) -> None:
        """`SOURCE_ITEM_LINK` is the element ADR-031 added for exactly this. A
        link composed here would be a link nobody rendered."""
        assert run(normalizer).payload["content"]["url"] == ARTICLE_URL

    def test_normalization_is_deterministic(self, normalizer) -> None:
        assert run(normalizer).payload == run(normalizer).payload


# ================================================================== refusals


class TestRefusalsRatherThanInvention:
    @pytest.mark.parametrize("field_name", ["article", "views", "agent", "timestamp"])
    def test_a_record_missing_a_required_source_fact_is_refused(
        self, normalizer, field_name
    ) -> None:
        with pytest.raises(NormalizationFailedError):
            run(normalizer, raw(payload_drop=(field_name,)))

    def test_a_non_integer_count_is_refused_not_coerced(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError, match="MISSING IS NEVER ZERO"):
            run(normalizer, raw(payload_extra={"views": "many"}))

    def test_a_malformed_day_bucket_is_refused(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError):
            run(normalizer, raw(payload_extra={"timestamp": "2024993100"}))

    @pytest.mark.parametrize("field_name", ["editor", "user_id", "ip", "country"])
    def test_a_raw_record_carrying_identity_is_refused_not_quietly_dropped(
        self, normalizer, field_name
    ) -> None:
        """The collector refuses such a RESPONSE and this refuses such a RECORD.
        They are different moments, and a record already in the database can
        only be caught here."""
        with pytest.raises(NormalizationFailedError, match="excludes at"):
            run(normalizer, raw(payload_extra={field_name: "x"}))


# ============================================================ no promotion


class TestNoSemanticPromotion:
    def test_no_field_name_in_the_payload_names_a_conclusion(self, normalizer) -> None:
        """Scanned over the KEYS, because the risk is a field NAME reading as a
        verdict. Deliberately not over the whole payload: the semantics strings
        contain "demand" and "adoption" in order to refuse them."""

        def keys(node: object) -> list[str]:
            if isinstance(node, dict):
                return [k for k in node] + [x for v in node.values() for x in keys(v)]
            if isinstance(node, list):
                return [x for v in node for x in keys(v)]
            return []

        names = [k.lower() for k in keys(run(normalizer).payload)]
        for word in ("reader", "user_count", "visitor", "demand", "adoption", "popularity"):
            assert not any(word in name for name in names), word

    def test_the_payload_carries_no_subject(self, normalizer) -> None:
        """Not omitted for tidiness -- the endpoint publishes an aggregate and
        nothing else was ever acquired."""
        assert run(normalizer).payload["subject"] is None

    def test_nothing_in_the_payload_states_a_trend(self, normalizer) -> None:
        flat = str(run(normalizer).payload).lower()
        for word in ("trend", "growth", "momentum", "seasonal"):
            assert word not in flat, word

    def test_the_normalizer_identifies_itself(self, normalizer) -> None:
        assert normalizer.normalizer_id == WM_NORMALIZER_ID
        assert normalizer.normalizer_version == WM_NORMALIZER_VERSION
