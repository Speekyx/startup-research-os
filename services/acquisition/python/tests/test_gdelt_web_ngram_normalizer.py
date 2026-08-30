"""The GDELT WEB-NGRAM normalizer: what it maps, and what it refuses to invent.

Mission 1.10.1. Every raw record here is synthetic and **built to the documented
contract**, not captured from GDELT. Nothing in this module touches a network.

The assertions that matter most are the ones about absences. Two canonical facts
are known to be missing — the timezone (H-29) and the language mapping (H-30) —
and the adapter's job is to say so rather than to fill them in. A normalizer that
quietly produced `en` and a UTC offset would pass a naive test suite and be
wrong in the field a consumer trusts most.
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sros_acquisition.normalization import (
    GRAM_SIZES,
    GdeltWebNgramLexicalNormalizer,
    RawRecordView,
    canonical_json,
)
from sros_acquisition.normalization import gdelt_web_ngram as adapter_module
from sros_acquisition.normalization.errors import NormalizationFailedError
from sros_acquisition.normalization.gdelt_web_ngram import (
    GDELT_WEB_NGRAM_NORMALIZER_ID,
    GDELT_WEB_NGRAM_NORMALIZER_VERSION,
)
from sros_acquisition.registry.retention import resolve_retention
from sros_contracts import (
    NormalizationErrorCode,
    NormalizationQualityReason,
    NormalizedRecordQuality,
)

from .conftest import REPO_ROOT

BUCKET = "20260830091500"
WORKSPACE = "00000000-0000-4000-8000-0000000000bb"
NORMALIZED_AT = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
UNIGRAM = "web-ngrams/1gram"
BIGRAM = "web-ngrams/2gram"

TIMEZONE_REASON = NormalizationQualityReason.PERIOD_TIMEZONE_NOT_ESTABLISHED
LANGUAGE_REASON = NormalizationQualityReason.LANGUAGE_NOT_MAPPED


def raw(
    *,
    ngram: str = "climate",
    lang: str = "ENGLISH",
    count: object = "55",
    date: str = BUCKET,
    resource_id: str = UNIGRAM,
    gram_kind: str | None = None,
    source_id: str = "gdelt",
    collector_id: str = "gdelt-web-ngram",
    payload: dict[str, object] | None = None,
) -> RawRecordView:
    """A synthetic RawRecord in the shape the collector actually writes.

    Built to the documented four-column contract, and labelled synthetic here so
    nobody later mistakes it for a capture — the same distinction the collector's
    own fixtures draw.
    """
    body: dict[str, object] = {
        "source_id": source_id,
        "resource_id": resource_id,
        "gram_kind": gram_kind if gram_kind is not None else resource_id.rsplit("/", 1)[-1],
        "date": date,
        "lang": lang,
        "ngram": ngram,
        "count": count,
    }
    if payload is not None:
        body = payload
    return RawRecordView(
        record_id="11111111-1111-4111-8111-111111111111",
        workspace_id=WORKSPACE,
        research_session_id=None,
        source_id=source_id,
        observation_key=f"{source_id}|{resource_id}|{date}|{lang}|{ngram}",
        content_hash="hash",
        acquisition_method="DATASET_DOWNLOAD",
        payload=body,
        provenance={
            "dataset_family": "web-ngrams-1gram",
            "resource_id": resource_id,
            "access_profile": "gdelt-web-ngram-files",
            "access_method": "DATASET_DOWNLOAD",
            "rights_basis": "DIRECT_GRANT",
            "licence": None,
            "attribution": {
                "text": "The GDELT Project Any use or redistribution of the data must "
                "include a citation to the GDELT Project and a link to this website "
                "(https://www.gdeltproject.org/).",
                "elements": [],
            },
        },
        review_version=3,
        collector_id=collector_id,
        collector_version="1.0.0",
        correlation_id="c",
        collected_at=datetime(2026, 8, 30, 10, 0, tzinfo=UTC),
        observed_at=None,
        expires_at=datetime(2026, 9, 29, 10, 0, tzinfo=UTC),
    )


def normalize(record: RawRecordView):
    normalizer = GdeltWebNgramLexicalNormalizer(resolve_retention(None))
    return normalizer.normalize(record, correlation_id="c", normalized_at=NORMALIZED_AT)


def reasons_of(draft) -> list[NormalizationQualityReason]:
    return [reason.code for reason in draft.quality_reasons]


# =============================================================== the boundary


class TestTheAdapterIsOfflineAndDeterministic:
    def test_it_imports_no_network_client_model_or_lookup(self) -> None:
        """§5, asserted on the IMPORTS rather than by grepping prose.

        A substring scan over the file would fail on its own docstring, which
        says it calls no model — and that teaches the next person to weaken the
        assertion rather than to trust it.
        """
        tree = ast.parse(pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for forbidden in (
            "httpx",
            "requests",
            "urllib",
            "socket",
            "aiohttp",
            "anthropic",
            "openai",
            "qdrant_client",
            "sentence_transformers",
            "torch",
            "transformers",
            "sros_llm_gateway",
        ):
            assert forbidden not in imported, forbidden

    def test_the_same_record_always_produces_the_same_payload(self) -> None:
        """§5. Determinism is the property, and a different clock and
        correlation id are the way to test it."""
        first = normalize(raw())
        normalizer = GdeltWebNgramLexicalNormalizer(resolve_retention(None))
        second = normalizer.normalize(
            raw(), correlation_id="a-different-one", normalized_at=NORMALIZED_AT.replace(year=2027)
        )
        assert first.payload == second.payload
        assert first.content_hash == second.content_hash
        assert first.record_id == second.record_id

    def test_the_quality_reasons_are_in_a_deterministic_order(self) -> None:
        """§16. Two runs produce byte-identical reasons, and the order is the
        one a reader wants: what the observation is about, then what it
        measures."""
        for _ in range(3):
            assert reasons_of(normalize(raw())) == [TIMEZONE_REASON, LANGUAGE_REASON]


# ============================================================== what it accepts


class TestItServesOnlyTheReviewedRoute:
    def test_both_reviewed_resources_normalize(self) -> None:
        for resource_id in GRAM_SIZES:
            draft = normalize(raw(resource_id=resource_id))
            assert draft.record_kind_id == "lexical_frequency_observation"

    @pytest.mark.parametrize(
        "resource_id",
        [
            "web-ngrams/3gram",
            "webngrams/3.0",
            "weblegacy/quadgram",
            "weblegacy/toc",
            "doc-api/timeline-tone",
            "doc-api/artlist",
            "",
        ],
    )
    def test_an_unreviewed_resource_is_refused(self, resource_id) -> None:
        """§4. None has a reviewed canonical shape, and guessing one would
        produce records that look right and are not."""
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(raw(resource_id=resource_id))
        assert caught.value.failure.code is NormalizationErrorCode.UNSUPPORTED_SOURCE

    def test_another_sources_record_is_refused(self) -> None:
        with pytest.raises(NormalizationFailedError, match="never describes another"):
            normalize(raw(source_id="world-bank"))

    def test_another_collectors_record_is_refused(self) -> None:
        """A second collector for one source parses a different shape."""
        with pytest.raises(NormalizationFailedError, match="parses a different shape"):
            normalize(raw(collector_id="gdelt-doc-api"))

    def test_only_one_collector_version_is_declared_supported(self) -> None:
        assert GdeltWebNgramLexicalNormalizer.supported_collector_versions == frozenset({"1.0.0"})

    def test_an_empty_payload_is_refused(self) -> None:
        with pytest.raises(NormalizationFailedError, match="no payload"):
            normalize(raw(payload={}))


# ================================================================ DATE / H-29


class TestTheDateKeepsItsUnknownTimezone:
    def test_the_period_is_a_fifteen_minute_interval(self) -> None:
        period = normalize(raw()).payload["period"]
        assert period["type"] == "INTERVAL"
        assert period["label"] == BUCKET
        assert period["end_inclusive"] is False

    def test_the_bounds_are_naive_and_fifteen_minutes_apart(self) -> None:
        period = normalize(raw()).payload["period"]
        start = datetime.fromisoformat(period["start"])
        end = datetime.fromisoformat(period["end"])
        assert start.tzinfo is None
        assert end.tzinfo is None
        assert (end - start).total_seconds() == 900

    def test_no_utc_and_no_offset_appears_anywhere_in_the_payload(self) -> None:
        """§6. Not `Z`, not `+00:00`, not the machine's zone."""
        serialised = canonical_json(normalize(raw()).payload)
        assert "+00:00" not in serialised
        assert "UTC" not in serialised
        assert 'Z"' not in serialised

    def test_the_timezone_state_says_it_is_not_established(self) -> None:
        assert normalize(raw()).payload["period"]["timezone_state"] == "NOT_ESTABLISHED"

    def test_observed_at_is_null(self) -> None:
        """§6. A TIMESTAMPTZ filled from a wall-clock reading would be an
        assumption in the column a consumer trusts most."""
        assert normalize(raw()).observed_at is None

    def test_the_exact_source_label_survives(self) -> None:
        """§7. A future normalizer version must be able to re-derive an
        established timezone without reacquiring the RawRecord."""
        draft = normalize(raw())
        assert draft.payload["period"]["label"] == BUCKET

    def test_the_adapter_never_converts_a_timezone(self) -> None:
        """§6, asserted over the CODE rather than the file's text.

        A substring scan fails on the docstring that explains the rule — the
        module says it never calls `astimezone`, and a grep for that word finds
        the sentence. `testing-strategy.md` §22 records the same lesson from
        Mission 1.9.3; this is it recurring, so the check walks the AST.
        """
        tree = ast.parse(pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8"))
        called = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        for forbidden in ("astimezone", "utcnow", "now", "localtime", "replace_tzinfo"):
            assert forbidden not in called, forbidden
        keywords = {
            keyword.arg
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for keyword in node.keywords
        }
        assert "tzinfo" not in keywords

    @pytest.mark.parametrize(
        "label",
        ["2026-08-30", "20260830091700", "20260830091530", "2026083009150", "20260230091500", ""],
    )
    def test_a_label_off_the_documented_contract_makes_the_record_invalid(self, label) -> None:
        """A defensive second read (§6): the adapter validates the contract
        itself rather than trusting a collector version that may have changed."""
        draft = normalize(raw(date=label))
        assert draft.quality is NormalizedRecordQuality.INVALID
        assert NormalizationQualityReason.PERIOD_NOT_SUPPORTED in reasons_of(draft)


# ================================================================ LANG / H-30


class TestTheLanguageStaysUnmapped:
    @pytest.mark.parametrize("label", ["ENGLISH", "FRENCH", "SPANISH", "Korean", "SERBO_CROATIAN"])
    def test_no_language_tag_is_ever_produced(self, label) -> None:
        """§8. `ENGLISH` is not `en`, and the resemblance is exactly why this is
        dangerous: obvious for the labels a reader thinks of, silently wrong for
        the first one they do not."""
        language = normalize(raw(lang=label)).payload["language"]
        assert language["source_label"] == label
        assert language["canonical_tag"] is None
        assert language["canonical_scheme"] is None
        assert language["mapping_state"] == "NOT_ESTABLISHED"

    def test_the_source_scheme_says_which_vocabulary_it_is(self) -> None:
        assert normalize(raw()).payload["language"]["source_scheme"] == "cld2-language-name"

    def test_the_canonical_language_column_stays_null(self) -> None:
        """§8. That column's contract means a code."""
        assert normalize(raw()).content_language is None

    def test_no_language_table_is_embedded_in_the_adapter(self) -> None:
        """§8. A mapping cannot be applied that does not exist.

        Over the string CONSTANTS rather than the file's text: the module
        docstring names ISO 639 while explaining why it does not use it, and a
        grep would find the explanation.
        """
        tree = ast.parse(pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8"))
        constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        for tag in ("en", "fr", "es", "ko", "de", "ja", "BCP-47"):
            assert tag not in constants, tag

    def test_language_never_becomes_geography(self) -> None:
        """§8. No geography key exists, and no country is inferred."""
        draft = normalize(raw())
        assert "geography" not in draft.payload
        assert "geography" not in canonical_json(draft.payload)
        for term in ("country", "iso-3166", "region"):
            assert term not in canonical_json(draft.payload).lower()


# ========================================================== NGRAM and gram size


class TestTheTermIsPreservedAndNotClassified:
    @pytest.mark.parametrize(
        "term", ["climate", "të", "気候", "a|b", "back\\slash", "climate change", "  spaced  "]
    )
    def test_the_term_survives_verbatim(self, term) -> None:
        """§9. Not normalised, not case-folded, not stripped."""
        assert normalize(raw(ngram=term)).payload["term"]["text"] == term

    def test_the_gram_size_comes_from_the_resource(self) -> None:
        """§9. A single-word term in the BIGRAM file still has gram_size 2,
        because the resource says so and the text does not."""
        assert normalize(raw(resource_id=UNIGRAM)).payload["term"]["gram_size"] == 1
        assert normalize(raw(resource_id=BIGRAM, ngram="climate")).payload["term"]["gram_size"] == 2

    def test_a_two_word_term_in_the_unigram_file_is_not_relabelled(self) -> None:
        """§9. Counting spaces would silently correct a contract violation
        instead of leaving it visible in the data."""
        draft = normalize(raw(resource_id=UNIGRAM, ngram="climate change"))
        assert draft.payload["term"]["gram_size"] == 1
        assert draft.payload["term"]["text"] == "climate change"

    def test_the_adapter_never_tokenizes_the_term(self) -> None:
        source = pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8")
        block = source[source.index("def _observation") : source.index("def _period")]
        assert ".split(" not in block
        assert ".count(" not in block

    def test_a_payload_contradicting_its_own_resource_is_refused(self) -> None:
        """§9. Choosing a winner between two source facts would be a silent
        correction; the record fails instead."""
        with pytest.raises(NormalizationFailedError, match="disagree"):
            normalize(raw(resource_id=UNIGRAM, gram_kind="2gram"))

    def test_the_term_scheme_is_recorded(self) -> None:
        assert normalize(raw()).payload["term"]["scheme"] == "gdelt-web-ngram"

    def test_no_classification_appears_anywhere(self) -> None:
        """§10. Not a theme, a topic, an entity, an intent or a sentiment."""
        serialised = canonical_json(normalize(raw()).payload).lower()
        for classification in (
            "theme",
            "topic",
            "entity",
            "keyword",
            "intent",
            "sentiment",
            "market",
            "problem",
            "desire",
        ):
            assert classification not in serialised, classification

    def test_a_missing_term_is_refused(self) -> None:
        with pytest.raises(NormalizationFailedError, match="no ngram"):
            normalize(raw(ngram=""))

    def test_a_missing_language_is_refused(self) -> None:
        with pytest.raises(NormalizationFailedError, match="no language label"):
            normalize(raw(lang=""))


# ===================================================================== COUNT


class TestTheCountKeepsItsPrecision:
    def test_a_count_is_an_exact_decimal_string(self) -> None:
        observation = normalize(raw(count="55")).payload["observation"]
        assert observation["value"] == "55"
        assert observation["value_state"] == "REPORTED"

    def test_a_count_above_two_to_the_fifty_three_is_exact(self) -> None:
        """§11. A float round-trip returns ...92."""
        assert (
            normalize(raw(count="9007199254740993")).payload["observation"]["value"]
            == "9007199254740993"
        )

    def test_a_zero_count_is_a_measurement(self) -> None:
        """The source saying 'none in this bucket'. NOT_REPORTED would make it
        indistinguishable from a term the file never listed."""
        observation = normalize(raw(count="0")).payload["observation"]
        assert observation["value"] == "0"
        assert observation["value_state"] == "REPORTED"

    @pytest.mark.parametrize("bad", ["-5", "10.5", "many", "", " 5 5 ", None, True, 1.5])
    def test_a_count_that_is_not_a_non_negative_integer_is_unreadable(self, bad) -> None:
        """Including a float: it has already been through IEEE-754, and
        accepting one would bake in the rounding this layer exists to avoid."""
        draft = normalize(raw(count=bad))
        assert draft.payload["observation"]["value"] is None
        assert draft.payload["observation"]["value_state"] == "UNREADABLE"
        assert NormalizationQualityReason.MALFORMED_NUMERIC_VALUE in reasons_of(draft)

    def test_an_integer_count_is_accepted_exactly(self) -> None:
        assert normalize(raw(count=42)).payload["observation"]["value"] == "42"

    def test_the_adapter_uses_no_float(self) -> None:
        source = pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8")
        assert "float(" not in source

    def test_the_unit_is_not_published(self) -> None:
        """§12. `mentions`, `occurrences`, `count` and `articles` would each
        assert the source published a unit field it does not."""
        observation = normalize(raw()).payload["observation"]
        assert observation["unit"] is None
        assert observation["unit_state"] == "NOT_PUBLISHED"
        source = pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8")
        for invented in ('"mentions"', '"occurrences"', '"articles"'):
            assert invented not in source

    def test_the_count_is_never_a_signal(self) -> None:
        serialised = canonical_json(normalize(raw()).payload).lower()
        for derived in ("signal", "score", "strength", "rank", "popularity", "trend"):
            assert derived not in serialised


# =================================================================== quality


class TestQualityIsPartialAndSaysWhy:
    def test_a_well_formed_record_is_partial(self) -> None:
        """§15. Two canonical facts a consumer would expect are absent, and both
        have a reason code. VALID would say nothing is missing."""
        draft = normalize(raw())
        assert draft.quality is NormalizedRecordQuality.PARTIAL

    def test_both_open_questions_are_named(self) -> None:
        assert set(reasons_of(normalize(raw()))) == {TIMEZONE_REASON, LANGUAGE_REASON}

    def test_neither_open_question_makes_the_record_invalid(self) -> None:
        """§15. A known, representable absence is not a reason to make a record
        unreadable."""
        assert normalize(raw()).quality is not NormalizedRecordQuality.INVALID

    def test_a_genuine_defect_still_makes_it_invalid(self) -> None:
        assert normalize(raw(date="nonsense")).quality is NormalizedRecordQuality.INVALID

    def test_an_unreadable_count_stays_partial_rather_than_invalid(self) -> None:
        """The record still says which term, which language and which period —
        it is a usable observation with a caveat, not an unreadable one."""
        assert normalize(raw(count="-5")).quality is NormalizedRecordQuality.PARTIAL

    def test_every_reason_carries_a_canonical_code_and_a_field(self) -> None:
        """§16. The code is what a consumer branches on; the prose is what a
        human reads, and recording only the sentence would make the branch
        depend on a string somebody may reword."""
        for reason in normalize(raw()).quality_reasons:
            assert isinstance(reason.code, NormalizationQualityReason)
            assert reason.detail.strip()
            assert reason.field_path


# ======================================================== identity and lineage


class TestIdentityAndLineage:
    def test_the_observation_key_is_inherited_verbatim(self) -> None:
        """§17. Not reconstructed: the RawRecord already carries the resource,
        the date, the language and the term."""
        record = raw()
        assert normalize(record).observation_key == record.observation_key

    def test_a_changed_count_keeps_the_semantic_identity(self) -> None:
        """§18. COUNT is content, so a correction is a revision of the same
        observation rather than a different one."""
        low, high = normalize(raw(count="55")), normalize(raw(count="9999"))
        assert low.observation_key == high.observation_key
        assert low.content_hash != high.content_hash
        for key in ("term", "language", "period"):
            assert low.payload[key] == high.payload[key]

    def test_the_row_identity_is_the_existing_contract(self) -> None:
        """§19. Unchanged, and D-08 is not solved here."""
        draft = normalize(raw())
        assert draft.identity == (
            WORKSPACE,
            draft.raw_record_id,
            draft.normalization_schema_version,
            GDELT_WEB_NGRAM_NORMALIZER_ID,
            GDELT_WEB_NGRAM_NORMALIZER_VERSION,
        )

    def test_the_normalizer_version_is_recorded_on_the_row(self) -> None:
        draft = normalize(raw())
        assert draft.normalizer_id == "gdelt-web-ngram-lexical"
        assert draft.normalizer_version == "1.0.0"

    def test_the_collector_lineage_survives(self) -> None:
        """§20. Which collector wrote the record it came from."""
        draft = normalize(raw())
        assert draft.collector_id == "gdelt-web-ngram"
        assert draft.collector_version == "1.0.0"

    def test_the_acquisition_provenance_is_carried_forward(self) -> None:
        """§20, §21. Copied rather than joined: the raw record expires eleven
        months before this one does."""
        provenance = normalize(raw()).provenance
        assert provenance["raw_record_id"]
        assert provenance["acquisition"]["resource_id"] == UNIGRAM
        assert provenance["normalization"]["record_kind"] == "lexical_frequency_observation"

    def test_attribution_survives_and_cannot_be_dropped(self) -> None:
        """§21. The obligation the review recorded, carried forward verbatim."""
        provenance = normalize(raw()).provenance
        assert "GDELT Project" in provenance["attribution"]["text"]

    def test_a_record_with_no_attribution_is_refused(self) -> None:
        """`build_normalized` raises rather than writing a derived record with
        no credit attached."""
        record = raw()
        stripped = RawRecordView(**{**record.__dict__, "provenance": {}})
        with pytest.raises(ValueError, match="no rendered attribution"):
            normalize(stripped)

    def test_retention_is_the_normalized_window_not_the_raw_one(self) -> None:
        """§22. 365 days from normalization, resolved by governance — never the
        raw record's 30-day expiry copied across."""
        draft = normalize(raw())
        assert (draft.expires_at - draft.normalized_at).days == 365
        assert draft.provenance["retention"]["normalized_days"] == 365

    def test_the_adapter_cannot_choose_a_retention_window(self) -> None:
        import inspect

        parameters = set(inspect.signature(GdeltWebNgramLexicalNormalizer.normalize).parameters)
        assert "retention" not in parameters
        assert "expires_at" not in parameters


# =============================================== personal data and the boundary


class TestNothingIsDerived:
    def test_no_person_detection_exists(self) -> None:
        """§23. A term may happen to be a name. The adapter does not look."""
        draft = normalize(raw(ngram="MACRON"))
        assert draft.payload["term"]["text"] == "MACRON"
        serialised = canonical_json(draft.payload).lower()
        for derived in ("person", "profile", "author", "url", "title", "image"):
            assert derived not in serialised

    def test_the_payload_carries_exactly_the_contract_keys(self) -> None:
        """§14. No convenience fields were invented."""
        assert set(normalize(raw()).payload) == {
            "record_kind",
            "term",
            "language",
            "observation",
            "period",
            "series",
        }

    def test_the_extraction_method_says_nothing_inferred(self) -> None:
        assert normalize(raw()).extraction_method == "DETERMINISTIC_ADAPTER"


# =========================================== the World Bank fingerprint, pinned


class TestExistingNormalizationIsUnchanged:
    def test_a_world_bank_payload_still_hashes_to_its_historical_value(self) -> None:
        """§32. A LITERAL captured before Mission 1.10 touched the shared period
        serialisation, not a round-trip through the code that changed.

        A round-trip would agree with itself. This is the assertion that catches
        `timezone_state` leaking into an ESTABLISHED payload, which would report
        a revision on every record ever written.
        """
        from .normalization_fixtures import NORMALIZED_AT as WB_AT
        from .normalization_fixtures import make_normalizer, raw_view

        draft = make_normalizer().normalize(raw_view(), correlation_id="c", normalized_at=WB_AT)
        assert draft.content_hash == (
            "4470dca9ec72809a58daa3a6b61c590a07be8b102a27d302978061348477be90"
        )
        assert "timezone_state" not in draft.payload["period"]
        assert draft.payload["period"]["start"] == "2018-01-01T00:00:00+00:00"

    def test_the_two_adapters_produce_different_record_kinds(self) -> None:
        from .normalization_fixtures import NORMALIZED_AT as WB_AT
        from .normalization_fixtures import make_normalizer, raw_view

        world_bank = make_normalizer().normalize(
            raw_view(), correlation_id="c", normalized_at=WB_AT
        )
        assert world_bank.record_kind_id == "numeric_observation"
        assert normalize(raw()).record_kind_id == "lexical_frequency_observation"


def test_the_repo_root_fixture_is_available() -> None:
    """Guards the import above rather than asserting anything about the model."""
    assert (REPO_ROOT / "PROJECT_MANIFEST.md").exists()
    assert Decimal("1") == 1
