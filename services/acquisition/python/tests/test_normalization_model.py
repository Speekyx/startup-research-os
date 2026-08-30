"""The canonical normalized model, and the boundaries it must not cross.

Mission 1.6 §53, plus the structural guarantees of §18, §40–§46.

**Structural, not behavioural, where the guarantee is structural.** §46 does not
ask that a normalizer happens to preserve attribution; it asks that there be *no
API through which one could drop it*. A test that normalized a record and found
attribution present would pass equally well against a builder with an
`attribution=None` parameter nobody had used yet. So the signature is asserted,
the same way Mission 1.5 asserted the collector's.

No test here touches a database or a network.
"""

from __future__ import annotations

import inspect
import json
import pathlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sros_acquisition.normalization import (
    NORMALIZATION_SCHEMA_ID,
    NORMALIZATION_SCHEMA_VERSION,
    RECORD_KIND_REGISTRY,
    RECORD_KINDS,
    CanonicalGeography,
    CanonicalValue,
    NormalizationContext,
    NormalizedRecordDraft,
    build_normalized,
    canonical_json,
    decimal_from,
    load_geography_map,
    year_period,
)
from sros_acquisition.normalization import model as model_module
from sros_contracts import (
    NormalizedGeographyKind,
    NormalizedPeriodType,
    NormalizedUnitState,
    NormalizedValueState,
)

from .conftest import REPO_ROOT
from .normalization_fixtures import (
    NORMALIZED_AT,
    make_normalizer,
    raw_view,
)

NORMALIZATION_PACKAGE = pathlib.Path(model_module.__file__).resolve().parent


# ------------------------------------------------------------------- identity


class TestIdentity:
    """§6. Three identities, and none of them is the clock."""

    def test_the_same_raw_record_and_versions_produce_the_same_record_id(self) -> None:
        normalizer = make_normalizer()
        record = raw_view()
        first = normalizer.normalize(record, correlation_id="c1", normalized_at=NORMALIZED_AT)
        second = normalizer.normalize(
            record,
            correlation_id="a-different-correlation",
            normalized_at=NORMALIZED_AT.replace(year=2027),
        )
        # A different clock and a different correlation id. Neither is part of
        # the identity, so a re-run converges on the row that exists rather than
        # inserting a parallel copy.
        assert first.record_id == second.record_id
        assert first.content_hash == second.content_hash

    def test_a_different_normalizer_version_is_a_different_representation(self) -> None:
        record = raw_view()
        first = make_normalizer().normalize(record, correlation_id="c", normalized_at=NORMALIZED_AT)
        newer = make_normalizer()
        newer.normalizer_version = "1.1.0"  # type: ignore[misc]
        second = newer.normalize(record, correlation_id="c", normalized_at=NORMALIZED_AT)

        # §24, §49: the two coexist. Same content, different identity.
        assert first.record_id != second.record_id
        assert first.identity != second.identity
        # And the CONTENT hash matches, because the content is the same. That is
        # the question an upgrade raises -- "did this change anything" -- and
        # folding the version into the hash would answer "yes" every time.
        assert first.content_hash == second.content_hash

    def test_a_revised_raw_record_is_a_different_representation(self) -> None:
        normalizer = make_normalizer()
        first = normalizer.normalize(
            raw_view(record_id="11111111-1111-4111-8111-111111111111"),
            correlation_id="c",
            normalized_at=NORMALIZED_AT,
        )
        second = normalizer.normalize(
            raw_view(
                record_id="22222222-2222-4222-8222-222222222222",
                value=Decimal("67390000"),
            ),
            correlation_id="c",
            normalized_at=NORMALIZED_AT,
        )
        assert first.record_id != second.record_id
        assert first.content_hash != second.content_hash
        # The OBSERVATION is the same one. That is what links the two versions.
        assert first.observation_key == second.observation_key

    def test_the_observation_key_is_inherited_verbatim(self) -> None:
        record = raw_view()
        draft = make_normalizer().normalize(record, correlation_id="c", normalized_at=NORMALIZED_AT)
        assert draft.observation_key == record.observation_key


# ---------------------------------------------------------------- fingerprint


class TestFingerprint:
    """§22. Over the content, and over nothing volatile."""

    def test_canonical_json_is_key_order_independent(self) -> None:
        assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})

    def test_the_fingerprint_excludes_every_volatile_field(self) -> None:
        # A DISTINCTIVE correlation id, not "c". A one-letter marker is a
        # substring of every payload, so the scan would match itself and the
        # test would fail for a reason unrelated to what it checks.
        draft = make_normalizer().normalize(
            raw_view(),
            correlation_id="corr-zzq-7f31",
            normalized_at=NORMALIZED_AT,
        )
        serialized = canonical_json(draft.payload)
        for volatile in (
            draft.correlation_id,
            draft.normalized_at.isoformat(),
            draft.raw_record_id,
            draft.normalizer_version,
            draft.normalizer_id,
        ):
            assert volatile not in serialized, (
                f"{volatile!r} is in the hashed payload; a re-run or an upgrade would "
                "report a revision that did not happen"
            )


# ------------------------------------------------------------------- numerics


class TestNumericSemantics:
    """§13 and §14. Exact decimals, and absence that stays absence."""

    def test_a_decimal_survives_serialization_exactly(self) -> None:
        # 0.1 is the canonical case: it has no exact binary representation, so a
        # value that went through a float would come back as
        # 0.1000000000000000055511151231257827.
        value = CanonicalValue(value=Decimal("0.1"), state=NormalizedValueState.REPORTED)
        assert value.to_json()["value"] == "0.1"

    def test_a_large_integer_is_not_widened_or_rounded(self) -> None:
        value = CanonicalValue(value=Decimal("67158348"), state=NormalizedValueState.REPORTED)
        assert value.to_json()["value"] == "67158348"

    def test_decimal_from_refuses_a_float(self) -> None:
        # A float has already been through IEEE-754. Accepting one here would
        # bake in the rounding this layer exists to avoid.
        assert decimal_from(0.1) is None

    def test_decimal_from_reads_int_decimal_and_string(self) -> None:
        assert decimal_from(7) == Decimal("7")
        assert decimal_from(Decimal("7.5")) == Decimal("7.5")
        assert decimal_from("7.5") == Decimal("7.5")
        assert decimal_from("not a number") is None
        assert decimal_from(None) is None
        assert decimal_from(True) is None

    def test_a_value_the_source_did_not_report_is_null_and_never_zero(self) -> None:
        value = CanonicalValue(value=None, state=NormalizedValueState.NOT_REPORTED)
        assert value.to_json()["value"] is None
        assert value.to_json()["value_state"] == "NOT_REPORTED"

    def test_a_reported_zero_stays_a_measurement(self) -> None:
        value = CanonicalValue(value=Decimal("0"), state=NormalizedValueState.REPORTED)
        payload = value.to_json()
        assert payload["value"] == "0"
        assert payload["value_state"] == "REPORTED"

    def test_a_number_cannot_be_stored_beside_a_not_reported_state(self) -> None:
        # The constructor is where "missing became zero" would have to pass.
        with pytest.raises(ValueError, match="must be null"):
            CanonicalValue(value=Decimal("0"), state=NormalizedValueState.NOT_REPORTED)

    def test_a_reported_state_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError, match="must carry a number"):
            CanonicalValue(value=None, state=NormalizedValueState.REPORTED)

    def test_unit_and_unit_state_must_agree(self) -> None:
        with pytest.raises(ValueError, match="must agree"):
            CanonicalValue(
                value=Decimal("1"),
                state=NormalizedValueState.REPORTED,
                unit=None,
                unit_state=NormalizedUnitState.PUBLISHED,
            )


# --------------------------------------------------------------------- period


class TestPeriodSemantics:
    """§16. A year is an interval, and January 1 is not an event time."""

    def test_a_year_is_a_half_open_interval_carrying_its_label(self) -> None:
        period = year_period("2018")
        assert period.type is NormalizedPeriodType.YEAR
        assert period.label == "2018"
        assert period.start == datetime(2018, 1, 1, tzinfo=UTC)
        assert period.end == datetime(2019, 1, 1, tzinfo=UTC)
        assert period.end_inclusive is False

    def test_the_type_and_label_travel_with_the_start(self) -> None:
        # The whole protection against reading January 1 as an exact moment is
        # that `type` and `label` sit beside it in the SAME object.
        payload = year_period("2020").to_json()
        assert payload["type"] == "YEAR"
        assert payload["label"] == "2020"
        assert payload["start"].startswith("2020-01-01")

    def test_a_non_year_is_refused_rather_than_guessed(self) -> None:
        for label in ("2020Q1", "2020-03", "twenty-twenty", "", "20200"):
            with pytest.raises(ValueError, match="four-digit year"):
                year_period(label)

    def test_observed_at_is_the_period_start(self) -> None:
        draft = make_normalizer().normalize(
            raw_view(period="2019"), correlation_id="c", normalized_at=NORMALIZED_AT
        )
        assert draft.observed_at == datetime(2019, 1, 1, tzinfo=UTC)
        assert draft.payload["period"]["type"] == "YEAR"  # type: ignore[index]


# ------------------------------------------------------------------ geography


class TestGeographySemantics:
    """§15. An aggregate is never a country, and an unknown is never promoted."""

    def test_an_aggregate_cannot_carry_a_country_code(self) -> None:
        with pytest.raises(ValueError, match="World is a country"):
            CanonicalGeography(
                source_code="WLD",
                source_name="World",
                kind=NormalizedGeographyKind.AGGREGATE,
                canonical_code="WL",
                canonical_scheme="ISO-3166-1-ALPHA-2",
            )

    def test_an_unclassified_code_keeps_its_source_form_and_gains_nothing(self) -> None:
        geography = CanonicalGeography.unclassified("WLD", "World")
        assert geography.source_code == "WLD"
        assert geography.kind is NormalizedGeographyKind.UNKNOWN
        assert geography.canonical_code is None
        assert geography.canonical_scheme is None

    def test_the_reviewed_map_classifies_only_what_it_records(self) -> None:
        geography = load_geography_map(REPO_ROOT / "docs/data/geography-mapping-v1.json")
        france = geography.classify("world-bank", "FRA")
        assert france is not None
        assert france.kind is NormalizedGeographyKind.COUNTRY
        assert france.canonical_code == "FR"
        # Nothing else. Widening the map is a review, not an edit.
        assert geography.classify("world-bank", "WLD") is None
        assert geography.classify("eurostat", "FRA") is None

    def test_every_map_entry_records_why(self) -> None:
        geography = load_geography_map(REPO_ROOT / "docs/data/geography-mapping-v1.json")
        for source_id, entries in geography.entries.items():
            for code, entry in entries.items():
                assert entry.basis.strip(), f"{source_id}/{code} classifies with no basis"


# --------------------------------------------------------------- record kinds


class TestRecordKinds:
    """§11. One kind, because one adapter exists."""

    def test_only_the_kinds_with_a_proven_shape_are_declared(self) -> None:
        """Mission 1.10 added the second, and the rule did not change.

        `numeric_observation` was alone because one adapter existed.
        `lexical_frequency_observation` was added because a real GDELT
        observation proved the first kind cannot hold it -- no geography, and a
        term that is not a metric. Still an EQUALITY: a third kind appearing
        without a source that needs it is what this catches.
        """
        assert set(RECORD_KINDS) == {"numeric_observation", "lexical_frequency_observation"}

    def test_no_hypothetical_kind_is_declared(self) -> None:
        # §11 names ten shapes future sources MIGHT have. A registered kind with
        # no adapter behind it is a promise the code does not keep.
        speculative = {
            "document",
            "discussion_post",
            "comment",
            "product",
            "review",
            "repository",
            "trend_observation",
            "event",
            "economic_indicator",
        }
        assert not speculative & set(RECORD_KINDS)

    def test_the_kind_declares_what_it_requires(self) -> None:
        kind = RECORD_KINDS["numeric_observation"]
        assert "observation.value_state" in kind.required
        # The VALUE is optional and the STATE is not. A record may legitimately
        # carry no measurement; it may never fail to say whether it has one.
        assert "observation.value" in kind.optional

    def test_the_registry_name_matches_the_contract(self) -> None:
        from sros_contracts import REGISTRY_NAMES

        assert RECORD_KIND_REGISTRY in REGISTRY_NAMES

    def test_every_declared_kind_is_inserted_by_a_migration(self) -> None:
        """A migration inserts the row and this module declares the shape. Two
        hand-maintained copies of one fact drift, and the drift is discovered by
        whoever trusted the wrong one.

        Reading EVERY migration rather than 0009 by name: a single filename was
        right while one kind existed and would have silently stopped covering
        the second the moment it arrived in a second file — still passing, over
        a smaller set than it claimed.
        """
        migrations = (REPO_ROOT / "infrastructure/db/migrations").glob("*.sql")
        sql = "\n".join(path.read_text(encoding="utf-8") for path in migrations)
        for kind_id in RECORD_KINDS:
            assert f"'{kind_id}'" in sql, kind_id


# ------------------------------------------------------------------ versioning


class TestVersioning:
    """§21. Two versions, independent, both on every row."""

    def test_every_draft_carries_both_versions(self) -> None:
        draft = make_normalizer().normalize(
            raw_view(), correlation_id="c", normalized_at=NORMALIZED_AT
        )
        assert draft.normalization_schema_id == NORMALIZATION_SCHEMA_ID
        assert draft.normalization_schema_version == NORMALIZATION_SCHEMA_VERSION
        assert draft.normalizer_id
        assert draft.normalizer_version

    def test_the_schema_version_is_an_integer_and_the_normalizer_version_is_not(
        self,
    ) -> None:
        # Not pedantry: they evolve independently, so they cannot share a
        # format that invites someone to compare them.
        assert isinstance(NORMALIZATION_SCHEMA_VERSION, int)
        draft = make_normalizer().normalize(
            raw_view(), correlation_id="c", normalized_at=NORMALIZED_AT
        )
        assert isinstance(draft.normalizer_version, str)


# ------------------------------------------------------- structural boundaries


class TestStructuralBoundaries:
    """The guarantees that must hold by construction, not by behaviour."""

    def test_build_normalized_has_no_attribution_parameter(self) -> None:
        """§46. There must be no API through which attribution can be dropped."""
        parameters = set(inspect.signature(build_normalized).parameters)
        for forbidden in ("attribution", "notice", "credit", "attribution_text"):
            assert forbidden not in parameters, (
                f"build_normalized accepts {forbidden!r}, so a normalizer could supply "
                "or omit an attribution. It must come from the raw record's provenance "
                "and from nowhere else"
            )

    def test_build_normalized_has_no_retention_parameter(self) -> None:
        """§10. A normalizer cannot choose how long its output is kept."""
        parameters = set(inspect.signature(build_normalized).parameters)
        for forbidden in ("expires_at", "expiry", "retention_days", "ttl"):
            assert forbidden not in parameters

    def test_the_retention_argument_is_a_resolved_window_not_a_number(self) -> None:
        # `retention` IS a parameter, and it is an EffectiveRetention -- the
        # output of the governance resolver. A plain int would be a number a
        # caller chose.
        annotation = inspect.signature(build_normalized).parameters["retention"].annotation
        assert "EffectiveRetention" in str(annotation)

    def test_a_raw_record_with_no_attribution_is_refused(self) -> None:
        """§46, behaviourally as well: failing closed, not writing a blank."""
        record = raw_view(attribution=None)
        with pytest.raises(ValueError, match="no rendered attribution"):
            make_normalizer().normalize(record, correlation_id="c", normalized_at=NORMALIZED_AT)

    def test_no_normalization_module_imports_a_network_client(self) -> None:
        """§40. Asserted mechanically, because a rule a reviewer must notice decays."""
        forbidden = (
            "httpx",
            "requests",
            "aiohttp",
            "urllib.request",
            "http.client",
            "socket",
            "playwright",
            "selenium",
        )
        for path in sorted(NORMALIZATION_PACKAGE.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for line in source.splitlines():
                stripped = line.strip()
                if not stripped.startswith(("import ", "from ")):
                    continue
                for name in forbidden:
                    assert not stripped.startswith((f"import {name}", f"from {name}")), (
                        f"{path.name} imports {name}"
                    )

    def test_no_normalization_module_imports_the_transport(self) -> None:
        """§40, the narrower half.

        The blanket ban would be satisfied by importing `collection.transport`,
        which is the one file allowed to hold a client. Reaching the network
        through the sanctioned door is still reaching the network.
        """
        for path in sorted(NORMALIZATION_PACKAGE.glob("*.py")):
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped.startswith(("import ", "from ")):
                    # Prose may NAME the transport -- these modules explain why
                    # they must not reach it. Scanning whole files would make
                    # documenting the rule violate the rule.
                    continue
                assert "transport" not in stripped.lower(), (
                    f"{path.name} imports the transport: {stripped!r}"
                )
                assert "Transport" not in stripped, (
                    f"{path.name} imports a transport symbol: {stripped!r}"
                )

    def test_no_normalization_module_imports_an_llm_or_an_embedding_library(
        self,
    ) -> None:
        """§41 and §42. Deterministic means deterministic."""
        forbidden = (
            "sros_llm_gateway",
            "anthropic",
            "google.generativeai",
            "openai",
            "sentence_transformers",
            "torch",
            "transformers",
            "sklearn",
            "hdbscan",
            "qdrant_client",
            "numpy",
        )
        for path in sorted(NORMALIZATION_PACKAGE.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for name in forbidden:
                assert f"import {name}" not in source, f"{path.name} imports {name}"

    def test_no_normalization_module_writes_a_signal_claim_or_evidence(self) -> None:
        """§43, §44, §45. The tables this layer must never touch."""
        for path in sorted(NORMALIZATION_PACKAGE.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for table in ("nlp.signals", "research.claims", "scoring.evidence"):
                assert table not in source, f"{path.name} references {table}"

    def test_the_draft_carries_no_score_confidence_or_reliability(self) -> None:
        """§25. Quality is structural; an epistemic number here would be read as one."""
        fields = {f for f in NormalizedRecordDraft.__dataclass_fields__}
        for forbidden in ("confidence", "reliability", "score", "independence", "weight"):
            assert not any(forbidden in name for name in fields), (
                f"a field containing {forbidden!r} is on the normalized record; "
                "aggregation semantics belong to the evidence model"
            )


# ------------------------------------------------------------------- retention


class TestRetention:
    """§10 and §47. The normalized window, resolved by governance, both ways."""

    def test_the_expiry_is_the_normalized_window_not_the_raw_one(self) -> None:
        record = raw_view()
        draft = make_normalizer().normalize(record, correlation_id="c", normalized_at=NORMALIZED_AT)
        # The raw record expires 30 days after collection. The normalized one
        # gets its own tier's window, anchored on normalization.
        assert draft.expires_at > record.expires_at
        assert (draft.expires_at - draft.normalized_at).days == 365

    def test_a_shorter_source_override_wins(self) -> None:
        from sros_acquisition.registry.models import RetentionOverride
        from sros_acquisition.registry.retention import resolve_retention

        override = RetentionOverride(
            basis="a source whose terms require 30-day derived retention",
            reviewed_by="mission-1.6-test",
            raw_days=7,
            normalized_days=30,
        )
        normalizer = make_normalizer(retention=resolve_retention(override))
        draft = normalizer.normalize(raw_view(), correlation_id="c", normalized_at=NORMALIZED_AT)
        assert (draft.expires_at - draft.normalized_at).days == 30

    def test_a_longer_source_override_does_not_win(self) -> None:
        from sros_acquisition.registry.models import RetentionOverride
        from sros_acquisition.registry.retention import resolve_retention

        override = RetentionOverride(
            basis="a source whose terms would permit ten years",
            reviewed_by="mission-1.6-test",
            raw_days=3650,
            normalized_days=3650,
        )
        normalizer = make_normalizer(retention=resolve_retention(override))
        draft = normalizer.normalize(raw_view(), correlation_id="c", normalized_at=NORMALIZED_AT)
        # The baseline is the ceiling. Lengthening requires necessity to be
        # established and recorded, which is a reviewed decision.
        assert (draft.expires_at - draft.normalized_at).days == 365

    def test_the_resolved_basis_is_recorded_on_the_record(self) -> None:
        draft = make_normalizer().normalize(
            raw_view(), correlation_id="c", normalized_at=NORMALIZED_AT
        )
        retention = draft.provenance["retention"]
        assert isinstance(retention, dict)
        assert retention["normalized_days"] == 365
        assert retention["normalized_source"] == "baseline"


# ------------------------------------------------------------------- lineage


class TestLineage:
    """§8. Nine questions, answered without a join and without a URL."""

    def test_every_lineage_question_is_answerable_from_the_record(self) -> None:
        record = raw_view()
        draft = make_normalizer().normalize(
            record, correlation_id="corr-1", normalized_at=NORMALIZED_AT
        )
        assert draft.raw_record_id == record.record_id
        assert draft.source_id == record.source_id
        assert draft.collector_id == record.collector_id
        assert draft.collector_version == record.collector_version
        assert draft.normalizer_id and draft.normalizer_version
        assert draft.review_version == record.review_version
        assert draft.observed_at is not None
        assert draft.collected_at == record.collected_at
        assert draft.normalized_at == NORMALIZED_AT
        assert draft.correlation_id == "corr-1"
        assert draft.provenance["acquisition"]["condition_snapshot"]  # type: ignore[index]

    def test_the_attribution_obligation_survives_verbatim(self) -> None:
        """§9 and §46."""
        record = raw_view()
        draft = make_normalizer().normalize(record, correlation_id="c", normalized_at=NORMALIZED_AT)
        assert draft.provenance["attribution"] == record.attribution
        assert "World Bank" in json.dumps(draft.provenance["attribution"])

    def test_the_lineage_is_copied_not_left_to_a_join(self) -> None:
        # The raw record is retained 30 days and this one 365. From day 31 a
        # join answers nothing, which is why data-retention-policy-v1.md §4
        # requires the metadata to travel with the derived record.
        draft = make_normalizer().normalize(
            raw_view(), correlation_id="c", normalized_at=NORMALIZED_AT
        )
        acquisition = draft.provenance["acquisition"]
        assert isinstance(acquisition, dict)
        assert acquisition["licence"] == "CC-BY-4.0"
        assert acquisition["content_origin"] == "PLATFORM_LICENSED"
        assert draft.provenance["raw_content_hash"]

    def test_the_extraction_method_records_that_nothing_inferred(self) -> None:
        """§18, §41: a reader can filter for transformations no model influenced."""
        draft = make_normalizer().normalize(
            raw_view(), correlation_id="c", normalized_at=NORMALIZED_AT
        )
        assert draft.extraction_method == "DETERMINISTIC_ADAPTER"


# ------------------------------------------------------------------- selection


class TestSelection:
    """§20. Keyed on source AND collector, and fails closed."""

    def test_an_unregistered_source_is_refused(self) -> None:
        from sros_acquisition.normalization import select_normalizer
        from sros_acquisition.normalization.errors import NormalizationFailedError
        from sros_contracts import NormalizationErrorCode

        with pytest.raises(NormalizationFailedError) as caught:
            select_normalizer(raw_view(source_id="eurostat"))
        assert caught.value.failure.code is NormalizationErrorCode.UNSUPPORTED_SOURCE

    def test_an_unregistered_collector_for_a_known_source_is_refused(self) -> None:
        from sros_acquisition.normalization import select_normalizer
        from sros_acquisition.normalization.errors import NormalizationFailedError
        from sros_contracts import NormalizationErrorCode

        with pytest.raises(NormalizationFailedError) as caught:
            select_normalizer(raw_view(collector_id="world-bank-microdata"))
        assert caught.value.failure.code is NormalizationErrorCode.UNSUPPORTED_SOURCE

    def test_an_unsupported_collector_version_is_refused(self) -> None:
        from sros_acquisition.normalization import select_normalizer
        from sros_acquisition.normalization.errors import NormalizationFailedError
        from sros_contracts import NormalizationErrorCode

        with pytest.raises(NormalizationFailedError) as caught:
            select_normalizer(raw_view(collector_version="2.0.0"))
        assert caught.value.failure.code is NormalizationErrorCode.UNSUPPORTED_COLLECTOR_VERSION

    def test_an_empty_registry_refuses_everything(self) -> None:
        from sros_acquisition.normalization import select_normalizer
        from sros_acquisition.normalization.errors import NormalizationFailedError

        with pytest.raises(NormalizationFailedError):
            select_normalizer(raw_view(), {})

    def test_the_registry_holds_one_adapter_per_collector(self) -> None:
        """Two now. The key is `(source_id, collector_id)` rather than the source
        alone — a second collector for one source parses a different shape, and
        handing it to the wrong adapter would produce plausible nonsense rather
        than an error."""
        from sros_acquisition.normalization import NORMALIZER_REGISTRY

        assert sorted(NORMALIZER_REGISTRY) == [
            ("gdelt", "gdelt-web-ngram"),
            ("world-bank", "world-bank-indicators"),
        ]

    def test_the_context_carries_governance_not_choices(self) -> None:
        parameters = set(NormalizationContext.__dataclass_fields__)
        assert parameters == {"retention", "geography"}
