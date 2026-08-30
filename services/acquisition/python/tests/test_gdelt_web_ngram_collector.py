"""The GDELT WEB-NGRAM collector: what it may reach, and what it refuses.

Mission 1.9.3. **No test in this module touches GDELT.** Every byte comes from
`web_ngram_fixtures`, which builds files against the documented four-column
contract and says plainly that it is doing so.

The assertions are grouped by the question they answer, and the ones that matter
most are the refusals: a collector is judged by what it cannot do, and each
"zero network calls" assertion is written against the fake transport's own
request log rather than against a mock's call count, so a refusal that happened
one line too late would still fail.
"""

from __future__ import annotations

import pytest
from sros_acquisition.collection import (
    GdeltWebNgramCollector,
    NgramBounds,
    NgramObservation,
    WebNgramRequest,
    build_raw_record,
)
from sros_acquisition.collection.errors import AcquisitionFailedError
from sros_acquisition.collection.gdelt_web_ngram import (
    COLLECTOR_ID,
    COLLECTOR_VERSION,
    GRAM_KINDS,
    gram_kind_of,
    validate_bucket_label,
)
from sros_acquisition.collection.pacing import WEB_NGRAM_PACING, RequestPacer
from sros_acquisition.compliance import build_authorization
from sros_contracts import AcquisitionErrorCode, RightsBasis

from .conftest import REPO_ROOT
from .web_ngram_fixtures import (
    BUCKET,
    EMPTY_GZIP,
    MALFORMED,
    NO_NEWLINE,
    NOT_GZIP,
    OTHER_BUCKET,
    PIPE_IN_NGRAM,
    TRUNCATED_GZIP,
    FakeStreamingTransport,
    amplified_gzip,
    gzipped,
    revised_unigram_file,
    rows_to_bytes,
    transport_with_defaults,
    unigram_file,
)

WORKSPACE = "00000000-0000-4000-8000-0000000000aa"
CORRELATION = "web-ngram-test"
UNIGRAM = "web-ngrams/1gram"
BIGRAM = "web-ngrams/2gram"


@pytest.fixture(scope="session")
def compliance():
    from sros_acquisition.compliance import load_compliance

    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


@pytest.fixture(scope="session")
def context(catalog, compliance):
    return build_authorization(catalog.get("gdelt"), compliance)


def make_collector(transport, **kwargs):
    """A collector whose pacing costs no wall-clock time.

    A test that really waited two seconds between files would be slow enough
    that somebody would eventually delete it — the same argument
    `RequestPacer`'s injectable clock was built for.
    """
    return GdeltWebNgramCollector(
        transport,
        pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None),
        **kwargs,
    )


def collect(collector, context, request, **kwargs):
    return collector.collect(
        context,
        request,
        workspace_id=WORKSPACE,
        correlation_id=CORRELATION,
        **kwargs,
    )


# ============================================================ request and route


class TestTheRequestCannotCarryAUrl:
    def test_the_request_has_no_host_path_or_filename_field(self) -> None:
        """§7, asserted structurally. A behavioural test would pass against a
        request that grew a `path` nobody had used yet."""
        fields = set(WebNgramRequest.__dataclass_fields__)
        assert fields == {"buckets", "grams", "languages", "ngrams", "ngram_prefix"}
        for forbidden in ("path", "host", "url", "base_url", "filename", "query"):
            assert forbidden not in fields

    def test_the_filename_is_constructed_from_validated_parts(self) -> None:
        request = WebNgramRequest(buckets=(BUCKET,), grams=("1gram", "2gram"))
        assert request.filename(BUCKET, "1gram") == f"{BUCKET}.1gram.txt.gz"
        assert request.filename(BUCKET, "2gram") == f"{BUCKET}.2gram.txt.gz"

    @pytest.mark.parametrize(
        "label",
        [
            "2026083009150",  # thirteen digits
            "202608300915000",  # fifteen
            "2026-08-30T09:15",  # a datetime, not a label
            "20260230091500",  # 30 February
            "20260830091700",  # off the quarter-hour grid
            "20260830091530",  # seconds
            "2026083009150a",  # not digits
            "20260830251500",  # hour 25
        ],
    )
    def test_a_bucket_label_that_is_not_the_documented_form_is_refused(self, label) -> None:
        with pytest.raises(ValueError):
            validate_bucket_label(label)

    def test_a_valid_label_survives_verbatim(self) -> None:
        """§8. Returned unchanged, not parsed and re-rendered."""
        assert validate_bucket_label(BUCKET) == BUCKET

    def test_no_timezone_is_attached_anywhere_in_validation(self) -> None:
        """§8 and §18. The value stays a string, so there is no zone to get wrong."""
        assert isinstance(validate_bucket_label(BUCKET), str)
        assert not validate_bucket_label(BUCKET).endswith("Z")

    @pytest.mark.parametrize("gram", ["3gram", "4gram", "quadgram", "webngrams", "artlist", ""])
    def test_an_unreviewed_gram_kind_cannot_even_be_requested(self, gram) -> None:
        """§4. Refused when the request is CONSTRUCTED, before any authorization
        runs — so there is no spelling of `3gram` that reaches a filename."""
        with pytest.raises(ValueError):
            WebNgramRequest(buckets=(BUCKET,), grams=(gram,))

    def test_only_the_two_reviewed_resources_are_nameable(self) -> None:
        assert GRAM_KINDS == {"1gram": UNIGRAM, "2gram": BIGRAM}

    def test_the_gram_kind_comes_from_the_resource_not_from_the_text(self) -> None:
        """§26. A two-word term in a unigram file would be a contract violation,
        and counting spaces would hide it instead of surfacing it."""
        assert gram_kind_of(UNIGRAM) == "1gram"
        assert gram_kind_of(BIGRAM) == "2gram"
        assert gram_kind_of("web-ngrams/3gram") is None

    def test_a_duplicate_file_request_is_refused(self) -> None:
        with pytest.raises(ValueError, match="twice"):
            WebNgramRequest(buckets=(BUCKET, BUCKET))


class TestOnlyTheReviewedRouteIsReachable:
    def test_the_collector_uses_the_named_profile_not_the_first_one(self, context) -> None:
        """§10. GDELT carries a second, DEFERRED profile for the DOC API.

        Taking `context.access[0]` would work today and would authorise
        `api.gdeltproject.org` the day the profile order changed.
        """
        transport = transport_with_defaults()
        collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert transport.hosts == [frozenset({"data.gdeltproject.org"})]
        assert transport.bases == ["https://data.gdeltproject.org/gdeltv3/web/ngrams/"]

    def test_the_api_host_is_not_in_the_allowlist_this_collector_uses(self, context) -> None:
        """The source's OWN other host is unreachable from here."""
        transport = transport_with_defaults()
        collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert "api.gdeltproject.org" not in transport.hosts[0]
        assert "storage.googleapis.com" not in transport.hosts[0]

    def test_only_the_constructed_filename_is_ever_requested(self, context) -> None:
        transport = transport_with_defaults()
        collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), grams=("1gram", "2gram")),
        )
        assert transport.requests == [f"{BUCKET}.1gram.txt.gz", f"{BUCKET}.2gram.txt.gz"]


# ================================================================ authorization


class TestNothingReachesTheNetworkWithoutAuthorization:
    def test_the_context_is_the_required_first_parameter(self) -> None:
        """§5, asserted on the signature. There is no overload that omits it."""
        import inspect

        parameters = list(inspect.signature(GdeltWebNgramCollector.collect).parameters)
        assert parameters[1] == "context"
        signature = inspect.signature(GdeltWebNgramCollector.collect)
        assert signature.parameters["context"].default is inspect.Parameter.empty

    def test_another_sources_authorization_is_refused(self, catalog, compliance) -> None:
        transport = transport_with_defaults()
        world_bank = build_authorization(catalog.get("world-bank"), compliance)
        with pytest.raises(AcquisitionFailedError):
            collect(make_collector(transport), world_bank, WebNgramRequest(buckets=(BUCKET,)))
        assert transport.requests == []

    def test_a_job_over_the_reviewed_ceiling_makes_zero_network_calls(self, context) -> None:
        """§11. Nine files, one over the reviewed eight."""
        transport = transport_with_defaults()
        buckets = tuple(f"202608300{h}{m}00" for h in ("1", "2") for m in ("00", "15", "30", "45"))
        request = WebNgramRequest(buckets=(*buckets[:8], "20260830220000"), grams=("1gram",))
        assert request.file_count == 9
        result = collect(make_collector(transport), context, request)
        assert transport.requests == []
        assert not result.succeeded
        assert result.failures[0].code is AcquisitionErrorCode.AUTHORIZATION_REJECTED
        assert "ceiling" in result.failures[0].detail

    def test_the_ceiling_is_not_silently_split_into_two_permitted_jobs(self, context) -> None:
        """§11. Refused whole. A collector that split the request would be
        granting itself a ceiling the review did not."""
        transport = transport_with_defaults()
        buckets = tuple(f"20260830{h:02d}0000" for h in range(9))
        result = collect(
            make_collector(transport), context, WebNgramRequest(buckets=buckets, grams=("1gram",))
        )
        assert transport.requests == []
        assert result.drafts == []

    def test_two_gram_kinds_count_as_two_files_each_bucket(self, context) -> None:
        """The ceiling is over FILES, and asking for both kinds doubles them."""
        buckets = tuple(f"20260830{h:02d}0000" for h in range(5))
        request = WebNgramRequest(buckets=buckets, grams=("1gram", "2gram"))
        assert request.file_count == 10
        transport = transport_with_defaults()
        result = collect(make_collector(transport), context, request)
        assert transport.requests == []
        assert not result.succeeded

    def test_the_collector_never_redefines_the_reviewed_ceiling(self) -> None:
        """§11, asserted structurally: the number lives in governance, and the
        collector has no constant of its own that could drift from it."""
        source = (
            REPO_ROOT / "services/acquisition/python/sros_acquisition/collection/gdelt_web_ngram.py"
        ).read_text(encoding="utf-8")
        assert "max_files_per_job" not in source
        assert "authorize_job_size" in source

    def test_an_unauthorised_resource_makes_zero_network_calls(self, catalog, compliance) -> None:
        """A GDELT authorization whose dataset entries have been emptied."""
        from dataclasses import replace

        context = build_authorization(catalog.get("gdelt"), compliance)
        stripped = replace(context, datasets=())
        transport = transport_with_defaults()
        result = collect(make_collector(transport), stripped, WebNgramRequest(buckets=(BUCKET,)))
        assert transport.requests == []
        assert result.refused_resources == [UNIGRAM]
        assert result.failures[0].code is AcquisitionErrorCode.RESOURCE_NOT_PERMITTED

    def test_a_resource_the_scope_refuses_makes_zero_network_calls(
        self, catalog, compliance
    ) -> None:
        """The descriptor is built from governance, so the way to make the gate
        refuse is to change governance — which is the point."""
        from dataclasses import replace

        context = build_authorization(catalog.get("gdelt"), compliance)
        narrowed = replace(
            context,
            resource_scope=replace(
                context.resource_scope,
                allowed_dataset_families=frozenset({"something-else"}),
            ),
        )
        transport = transport_with_defaults()
        result = collect(make_collector(transport), narrowed, WebNgramRequest(buckets=(BUCKET,)))
        assert transport.requests == []
        assert result.refused_resources == [UNIGRAM]

    def test_a_refused_first_resource_does_not_stop_the_second(self, catalog, compliance) -> None:
        """A refusal is per resource, and the reviewed one still runs."""
        from dataclasses import replace

        context = build_authorization(catalog.get("gdelt"), compliance)
        only_bigram = replace(
            context, datasets=tuple(d for d in context.datasets if d.resource_id == BIGRAM)
        )
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            only_bigram,
            WebNgramRequest(buckets=(BUCKET,), grams=("1gram", "2gram")),
        )
        assert result.refused_resources == [UNIGRAM]
        assert transport.requests == [f"{BUCKET}.2gram.txt.gz"]
        assert result.drafts


class TestTheDescriptorComesFromGovernance:
    def test_every_draft_records_a_direct_grant_and_no_licence(self, context) -> None:
        """§6. The collector never composes a licence; there is none to compose."""
        transport = transport_with_defaults()
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.drafts
        for draft in result.drafts:
            assert draft.provenance["rights_basis"] == RightsBasis.DIRECT_GRANT.value
            assert draft.provenance["licence"] is None

    def test_no_licence_string_is_hard_coded_in_the_collector(self) -> None:
        source = (
            REPO_ROOT / "services/acquisition/python/sros_acquisition/collection/gdelt_web_ngram.py"
        ).read_text(encoding="utf-8")
        for fabrication in ("CC-BY", "GDELT Terms", "OTHER", '"NONE"', "N/A"):
            assert fabrication not in source


# ================================================================ streaming


class TestTheDownloadIsStreamedAndBounded:
    def test_the_body_is_consumed_in_chunks_rather_than_in_one_piece(self, context) -> None:
        """§45. Tested against something that genuinely streams.

        The fixture transport yields eight bytes at a time and records how many
        it sent. A parser that buffered the body would still work here, so this
        assertion is the weak half of the pair; the strong half is
        `test_the_decompressed_ceiling_stops_an_amplified_file`, which can only
        pass if decompression is incremental.
        """
        transport = transport_with_defaults()
        transport.chunk_size = 8
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.drafts
        assert transport.chunks_sent > 1
        assert transport.bytes_sent == len(transport.files[f"{BUCKET}.1gram.txt.gz"])

    def test_the_compressed_ceiling_stops_a_large_file(self, context) -> None:
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": unigram_file()})
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,)),
            bounds=NgramBounds(max_compressed_bytes=16, max_decompressed_bytes=1024),
        )
        assert not result.succeeded
        assert "our own operational ceiling" in result.failures[0].detail
        assert result.drafts == []

    def test_the_decompressed_ceiling_stops_an_amplified_file(self, context) -> None:
        """The bound the compressed ceiling cannot provide: a few kilobytes on
        the wire expanding to megabytes."""
        transport = FakeStreamingTransport(
            files={f"{BUCKET}.1gram.txt.gz": amplified_gzip(2_000_000)}
        )
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,)),
            bounds=NgramBounds(max_compressed_bytes=20_000, max_decompressed_bytes=50_000),
        )
        assert not result.succeeded
        assert "decompressed" in result.failures[0].detail
        assert result.drafts == []
        # The ceiling fired while the stream was still arriving, which is the
        # property under test: a decompressor handed the whole body could not
        # have stopped at 50 KB of a 2 MB expansion.
        assert transport.bytes_sent < len(transport.files[f"{BUCKET}.1gram.txt.gz"])

    def test_the_line_ceiling_stops_a_file_with_no_newline(self, context) -> None:
        """Without it, a file containing no newline grows the buffer until the
        worker dies, and every other bound still reads as satisfied."""
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": NO_NEWLINE})
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,)),
            bounds=NgramBounds(max_line_bytes=256),
        )
        assert not result.succeeded
        assert "line exceeded" in result.failures[0].detail

    def test_the_row_scan_ceiling_truncates_and_says_so(self, context) -> None:
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,)),
            bounds=NgramBounds(max_rows_scanned=3),
        )
        assert result.succeeded
        assert result.files[0].truncated_by_bound == "max_rows_scanned"

    def test_the_record_ceiling_truncates_and_keeps_what_was_accepted(self, context) -> None:
        """Our OWN ceiling truncates; it does not discard. That is the deliberate
        difference from a contract violation, which discards the file."""
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,)),
            bounds=NgramBounds(max_records=2),
        )
        assert len(result.drafts) == 2
        assert result.files[0].ok is True
        assert result.files[0].truncated_by_bound == "max_records"

    def test_the_operational_bounds_are_labelled_as_ours(self, context) -> None:
        """§12. A reader must not be able to mistake one for a provider quota."""
        assert NgramBounds.ORIGIN == "INTERNAL_SAFETY_POLICY"
        transport = transport_with_defaults()
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        bounds = result.drafts[0].provenance["operational_bounds"]
        assert bounds["origin"] == "INTERNAL_SAFETY_POLICY"

    def test_the_stream_is_closed_when_a_ceiling_stops_it_early(self, context) -> None:
        """The connection goes back to the pool rather than waiting to be reaped."""
        transport = transport_with_defaults()
        collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,)),
            bounds=NgramBounds(max_records=1),
        )
        assert transport.closed == 1


# ==================================================================== gzip


class TestGzipIsValidated:
    def test_a_valid_file_parses(self, context) -> None:
        transport = transport_with_defaults()
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded
        assert len(result.drafts) == 9

    def test_a_truncated_stream_is_reported_rather_than_read_as_a_short_file(self, context) -> None:
        """§14. The rows already read are not a complete file, so none is kept."""
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": TRUNCATED_GZIP})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert not result.succeeded
        assert "truncated" in result.failures[0].detail
        assert result.drafts == []

    def test_an_html_error_page_is_not_read_as_an_ngram_file(self, context) -> None:
        """§15. The realistic failure: a 200 carrying an error page."""
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": NOT_GZIP})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert not result.succeeded
        assert result.failures[0].code is AcquisitionErrorCode.PARSING_FAILURE
        assert "not valid gzip" in result.failures[0].detail

    def test_an_empty_gzip_yields_no_rows_and_no_failure(self, context) -> None:
        """Valid framing over nothing is a real, empty file — not a fault."""
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": EMPTY_GZIP})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded
        assert result.drafts == []
        assert result.files[0].ok is True
        assert result.files[0].rows_scanned == 0

    def test_a_mime_type_is_never_the_authorization(self, context) -> None:
        """§16. Mission 1.9.1 observed `text/plain` for a gzip resource, so a
        MIME check would refuse the real thing."""
        transport = transport_with_defaults()
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded
        source = (
            REPO_ROOT / "services/acquisition/python/sros_acquisition/collection/gdelt_web_ngram.py"
        ).read_text(encoding="utf-8")
        assert "application/gzip" not in source


# ================================================================== the parser


class TestTheRowContractIsStrict:
    @pytest.mark.parametrize("case", sorted(MALFORMED))
    def test_a_malformed_row_discards_its_file(self, context, case) -> None:
        """§17 and §32. Fatal rather than skipped, and the file contributes
        nothing: the contract is documented and observed, so a deviation means
        the contract changed or the file is not the one requested — and both
        need a person, not a filter."""
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": MALFORMED[case]})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert not result.succeeded, case
        assert result.drafts == [], case
        assert result.files[0].ok is False, case

    def test_a_term_containing_the_key_separator_is_accepted(self, context) -> None:
        """The defect the live smoke test found on the first real file.

        An earlier parser refused any NGRAM containing `|`, because the
        observation key is `|`-joined and forbade it in a part. News text
        contains pipes, so GDELT publishes terms containing them, and a whole
        file of legitimate observations was being discarded by our own key
        format. `observation_key` escapes the separator now.
        """
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": PIPE_IN_NGRAM})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded, [f.to_json() for f in result.failures]
        assert result.drafts[0].payload["ngram"] == "a|b"
        assert result.drafts[0].observation_key.endswith(r"ENGLISH|a\|b")

    def test_an_extra_tab_does_not_shift_columns(self, context) -> None:
        """§17's sharpest rule. A five-field row is not a row with a longer
        ngram, and treating it as one would produce records that look right."""
        transport = FakeStreamingTransport(
            files={f"{BUCKET}.1gram.txt.gz": MALFORMED["extra_field"]}
        )
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert "exactly four" in result.failures[0].detail

    def test_a_trailing_newline_is_not_a_malformed_row(self, context) -> None:
        body = gzipped(rows_to_bytes([(BUCKET, "ENGLISH", "climate", "10")]) + b"\n")
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": body})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded
        assert len(result.drafts) == 1

    def test_a_file_without_a_final_newline_still_yields_its_last_row(self, context) -> None:
        body = gzipped(f"{BUCKET}\tENGLISH\tclimate\t10".encode())
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": body})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded
        assert len(result.drafts) == 1

    def test_crlf_line_endings_do_not_corrupt_the_count(self, context) -> None:
        body = gzipped(f"{BUCKET}\tENGLISH\tclimate\t10\r\n".encode())
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": body})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded
        assert result.drafts[0].payload["count"] == "10"

    def test_invalid_utf8_is_refused_rather_than_replaced(self, context) -> None:
        """§20. A replacement character would become part of an ngram's identity
        and its fingerprint, indistinguishable from a term GDELT published."""
        transport = FakeStreamingTransport(
            files={f"{BUCKET}.1gram.txt.gz": MALFORMED["invalid_utf8"]}
        )
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.failures[0].code is AcquisitionErrorCode.PARSING_FAILURE
        assert "UTF-8" in result.failures[0].detail


class TestFieldSemantics:
    @pytest.fixture()
    def drafts(self, context):
        transport = transport_with_defaults()
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        return {(d.payload["lang"], d.payload["ngram"]): d for d in result.drafts}

    def test_the_date_is_the_source_label_with_no_timezone(self, drafts) -> None:
        """§18. Not `Z`, not an offset, not a datetime."""
        draft = drafts[("ENGLISH", "climate")]
        assert draft.payload["date"] == BUCKET
        assert draft.provenance["source_bucket_label"] == BUCKET
        assert draft.provenance["bucket_timezone"] is None
        assert draft.provenance["bucket_resolution_minutes"] == 15

    def test_observed_at_is_absent_because_the_zone_is_unknown(self, drafts) -> None:
        """H-29. `observed_at` is a TIMESTAMPTZ; writing one means naming a zone,
        and the assumption would land in the column a reader trusts most."""
        assert all(d.observed_at is None for d in drafts.values())

    def test_the_language_is_the_source_label_and_never_a_geography(self, drafts) -> None:
        """§19. Spanish is not Spain; the row says nothing about where."""
        draft = drafts[("ALBANIAN", "dhe")]
        assert draft.payload["lang"] == "ALBANIAN"
        assert draft.provenance["source_language_label"] == "ALBANIAN"
        assert draft.provenance["language_representation"] == "SOURCE_NATIVE_CLD2_NAME"
        assert "geography" not in draft.provenance
        assert "geography" not in draft.payload

    def test_the_canonical_language_column_stays_empty(self, drafts) -> None:
        """H-30. `content_language` is read as a code; GDELT emits a NAME, and no
        published mapping between them was found. The canonical slot stays empty
        and the label lives in the payload — the pattern
        `CanonicalGeography.unclassified` already sets for an unmappable code."""
        assert all(d.content_language is None for d in drafts.values())

    def test_the_ngram_is_preserved_and_not_classified(self, drafts) -> None:
        """§20. Not a theme, not an entity, not a topic."""
        draft = drafts[("ALBANIAN", "të")]
        assert draft.payload["ngram"] == "të"
        for classification in ("theme", "entity", "topic", "keyword", "intent"):
            assert classification not in draft.payload

    def test_unicode_survives_byte_for_byte(self, drafts) -> None:
        assert drafts[("JAPANESE", "気候")].payload["ngram"] == "気候"

    def test_the_count_is_the_sources_measurement(self, drafts) -> None:
        """§21. Not a score, not a strength, not a signal."""
        draft = drafts[("ENGLISH", "climate")]
        assert draft.payload["count"] == "48210"
        for forbidden in ("score", "signal", "strength", "popularity", "trend"):
            assert forbidden not in draft.payload

    def test_zero_is_a_measurement_and_survives_as_one(self, drafts) -> None:
        assert drafts[("FRENCH", "grêle")].payload["count"] == "0"

    def test_a_count_beyond_float_precision_is_exact(self, drafts) -> None:
        """§21. 9007199254740993 is not representable as a double; a float
        round-trip would silently return ...92."""
        assert drafts[("JAPANESE", "気候")].payload["count"] == "9007199254740993"

    def test_the_count_never_passes_through_a_float(self) -> None:
        source = (
            REPO_ROOT / "services/acquisition/python/sros_acquisition/collection/gdelt_web_ngram.py"
        ).read_text(encoding="utf-8")
        assert "float(" not in source

    def test_a_row_carries_its_own_bucket_not_the_requested_one(self, context) -> None:
        """A row states its own DATE. Relabelling it with the one we asked for
        would be a fabricated fact about when something was observed."""
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport), context, WebNgramRequest(buckets=(OTHER_BUCKET,))
        )
        # The fixture at OTHER_BUCKET deliberately carries BUCKET rows.
        assert {d.payload["date"] for d in result.drafts} == {BUCKET}


# ================================================================ identity


class TestObservationIdentity:
    def make(self, **overrides):
        fields = {
            "source_id": "gdelt",
            "resource_id": UNIGRAM,
            "gram_kind": "1gram",
            "bucket_label": BUCKET,
            "language_label": "ENGLISH",
            "ngram": "climate",
            "count": 10,
        }
        fields.update(overrides)
        return NgramObservation(**fields)

    def test_the_key_is_source_native_and_readable(self) -> None:
        """§24. Composed rather than hashed, so an operator debugging a revision
        can read which observation it is."""
        assert self.make().key == f"gdelt|{UNIGRAM}|{BUCKET}|ENGLISH|climate"

    def test_the_count_is_not_in_the_identity(self) -> None:
        """§24. A revised count is a revision of this observation, not a
        different one."""
        assert self.make(count=10).key == self.make(count=99).key

    def test_the_count_is_in_the_fingerprint(self) -> None:
        """§25. Same observation, different content."""
        assert self.make(count=10).content_hash != self.make(count=99).content_hash

    def test_the_two_resources_do_not_collide(self) -> None:
        """§26. The resource id is in the key, so a term appearing in both files
        is two observations rather than one."""
        unigram = self.make(resource_id=UNIGRAM, gram_kind="1gram")
        bigram = self.make(resource_id=BIGRAM, gram_kind="2gram")
        assert unigram.key != bigram.key
        assert unigram.content_hash != bigram.content_hash

    def test_the_fingerprint_excludes_retrieval_facts(self) -> None:
        """§25. Hashing a timestamp would make every retrieval a revision."""
        payload = self.make().payload
        for excluded in ("collected_at", "correlation_id", "job_id", "session_id", "filename"):
            assert excluded not in payload

    def test_a_negative_count_cannot_be_constructed(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            self.make(count=-1)

    def test_the_same_file_twice_produces_identical_record_ids(self, context) -> None:
        """§34. The basis of idempotency: the id is derived from the workspace,
        the key and the fingerprint, none of which is a clock."""
        first = collect(
            make_collector(transport_with_defaults()), context, WebNgramRequest(buckets=(BUCKET,))
        )
        second = collect(
            make_collector(transport_with_defaults()), context, WebNgramRequest(buckets=(BUCKET,))
        )
        assert [d.record_id for d in first.drafts] == [d.record_id for d in second.drafts]

    def test_a_revised_count_changes_the_id_but_not_the_key(self, context) -> None:
        original = collect(
            make_collector(transport_with_defaults()), context, WebNgramRequest(buckets=(BUCKET,))
        )
        revised_transport = FakeStreamingTransport(
            files={f"{BUCKET}.1gram.txt.gz": revised_unigram_file()}
        )
        revised = collect(
            make_collector(revised_transport), context, WebNgramRequest(buckets=(BUCKET,))
        )
        before = {d.observation_key: d for d in original.drafts}
        after = {d.observation_key: d for d in revised.drafts}
        assert set(before) == set(after)
        changed = [k for k in before if before[k].content_hash != after[k].content_hash]
        assert changed == [f"gdelt|{UNIGRAM}|{BUCKET}|ENGLISH|climate"]


# ============================================================= local filtering


class TestLocalFiltering:
    def test_a_language_filter_narrows_what_is_persisted(self, context) -> None:
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), languages=("ENGLISH",)),
        )
        assert {d.payload["lang"] for d in result.drafts} == {"ENGLISH"}

    def test_an_exact_ngram_filter_narrows_what_is_persisted(self, context) -> None:
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), ngrams=("climate",)),
        )
        assert {d.payload["ngram"] for d in result.drafts} == {"climate"}

    def test_a_prefix_filter_is_deterministic(self, context) -> None:
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), languages=("ENGLISH",), ngram_prefix="clim"),
        )
        assert {d.payload["ngram"] for d in result.drafts} == {"climate", "climatic"}

    def test_the_filter_does_not_change_what_a_record_claims(self, context) -> None:
        """§22. The stored observation is identical whether it arrived through a
        filter or not — filtering decides WHICH rows are kept, never what one
        says."""
        unfiltered = collect(
            make_collector(transport_with_defaults()), context, WebNgramRequest(buckets=(BUCKET,))
        )
        filtered = collect(
            make_collector(transport_with_defaults()),
            context,
            WebNgramRequest(buckets=(BUCKET,), ngrams=("climate",)),
        )
        target = next(d for d in unfiltered.drafts if d.payload["ngram"] == "climate")
        assert filtered.drafts[0].payload == target.payload
        assert filtered.drafts[0].content_hash == target.content_hash
        assert filtered.drafts[0].record_id == target.record_id

    def test_the_filter_is_recorded_as_ours_in_provenance(self, context) -> None:
        """§22. A later reader must not be able to mistake our narrowing for the
        source's."""
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), languages=("ENGLISH",), ngram_prefix="clim"),
        )
        applied = result.drafts[0].provenance["local_filter"]
        assert applied["applied_by"] == "collector"
        assert applied["languages"] == ["ENGLISH"]
        assert applied["ngram_prefix"] == "clim"

    def test_the_scan_counts_every_row_not_only_the_matches(self, context) -> None:
        """§52. The file contained more than we kept, and the report says so."""
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), ngrams=("climate",)),
        )
        assert result.rows_scanned == 9
        assert result.rows_matched == 1

    def test_no_semantic_filtering_exists(self) -> None:
        """§22. No LLM, no embedding, no model — asserted on the IMPORTS.

        A substring scan over the whole file is not a check: the module
        docstring says "does not embed" and would fail it, which teaches the
        next person to weaken the assertion rather than to trust it. What
        matters is whether anything is imported or called, so this walks the
        import statements the way `validate_normalization.py` does.
        """
        import ast

        tree = ast.parse(
            (
                REPO_ROOT
                / "services/acquisition/python/sros_acquisition/collection/gdelt_web_ngram.py"
            ).read_text(encoding="utf-8")
        )
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for forbidden in (
            "anthropic",
            "openai",
            "qdrant_client",
            "sentence_transformers",
            "torch",
            "transformers",
            "sros_llm_gateway",
        ):
            assert forbidden not in imported


# ============================================== retries, failures, cancellation


class TestFailureHandling:
    def test_a_missing_bucket_is_reported_and_never_retried(self, context) -> None:
        """§36 and §37. A 404 means the requested bucket is unavailable — not a
        cue to try adjacent dates until something works."""
        transport = FakeStreamingTransport(files={})
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert not result.succeeded
        assert result.failures[0].code is AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR
        assert result.failures[0].retryable is False
        assert len(transport.requests) == 1

    def test_a_transient_failure_is_retried_within_its_bound(self, context) -> None:
        transport = transport_with_defaults()
        transport.fail_times = {f"{BUCKET}.1gram.txt.gz": 2}
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.succeeded
        assert len(transport.requests) == 3

    def test_retries_are_bounded(self, context) -> None:
        transport = transport_with_defaults()
        transport.fail_times = {f"{BUCKET}.1gram.txt.gz": 99}
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert not result.succeeded
        assert len(transport.requests) == 3
        assert result.failures[0].context["attempts"] == 3

    def test_a_malformed_file_is_not_retried(self, context) -> None:
        """The same request produces the same file. Repeating it is how a rate
        limit becomes a ban."""
        transport = FakeStreamingTransport(files={f"{BUCKET}.1gram.txt.gz": NOT_GZIP})
        collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert len(transport.requests) == 1

    def test_a_retry_resets_the_counters_it_had_started(self, context) -> None:
        """A retry re-reads the file from the beginning, so anything the failed
        attempt counted has to go with it."""
        transport = transport_with_defaults()
        transport.fail_times = {f"{BUCKET}.1gram.txt.gz": 1}
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.files[0].rows_scanned == 9

    def test_one_failed_file_does_not_discard_the_others(self, context) -> None:
        """§33. Per-file semantics, stated honestly rather than claiming
        all-or-nothing across independent downloads."""
        transport = transport_with_defaults()
        transport.files[f"{BUCKET}.2gram.txt.gz"] = NOT_GZIP
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), grams=("1gram", "2gram")),
        )
        assert result.files_requested == 2
        assert result.files_processed == 1
        assert result.files_failed == 1
        assert {d.provenance["gram_kind"] for d in result.drafts} == {"1gram"}

    def test_cancellation_stops_the_next_file(self, context) -> None:
        """§38. An in-flight request may finish within its timeout; no NEW file
        starts."""
        transport = transport_with_defaults()
        calls = {"n": 0}

        def cancelled() -> bool:
            calls["n"] += 1
            return calls["n"] > 1

        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), grams=("1gram", "2gram")),
            cancelled=cancelled,
        )
        assert len(transport.requests) == 1
        assert any(f.code is AcquisitionErrorCode.CANCELLED for f in result.failures)

    def test_pacing_is_ours_and_says_so(self, context) -> None:
        """§35. The DOC API's 429 is not carried across to this route."""
        assert WEB_NGRAM_PACING.origin == "INTERNAL_SAFETY_POLICY"
        assert "different route" in WEB_NGRAM_PACING.basis
        transport = transport_with_defaults()
        result = collect(make_collector(transport), context, WebNgramRequest(buckets=(BUCKET,)))
        assert result.drafts[0].provenance["pacing_origin"] == "INTERNAL_SAFETY_POLICY"

    def test_the_rate_limit_stays_unknown_on_the_context(self, context) -> None:
        for access in context.access:
            assert access.rate_limit.known is False


# ================================================================ provenance


class TestProvenanceAnswersEveryQuestion:
    @pytest.fixture()
    def draft(self, context):
        transport = transport_with_defaults()
        result = collect(
            make_collector(transport),
            context,
            WebNgramRequest(buckets=(BUCKET,), languages=("ENGLISH",)),
        )
        return result.drafts[0]

    def test_every_required_fact_is_present_without_parsing_a_url(self, draft) -> None:
        """§27. The list is the brief's, in its order."""
        provenance = draft.provenance
        for key in (
            "source_id",
            "review_version",
            "access_profile",
            "resource_id",
            "dataset_family",
            "rights_basis",
            "attribution",
            "retention_days",
            "acquisition_bounds",
            "source_bucket_label",
            "gram_kind",
            "source_language_label",
            "source_ngram",
            "received_filename",
            "local_filter",
            "condition_snapshot",
        ):
            assert key in provenance, key
        assert draft.collector_id == COLLECTOR_ID
        assert draft.collector_version == COLLECTOR_VERSION
        assert draft.workspace_id == WORKSPACE
        assert draft.correlation_id == CORRELATION
        assert draft.collected_at is not None

    def test_the_reviewed_acquisition_ceiling_travels_with_the_record(self, draft) -> None:
        assert draft.provenance["acquisition_bounds"]["max_files_per_job"] == 8

    def test_attribution_is_rendered_from_the_obligation(self, draft) -> None:
        """§28. Not composed here — the collector has no parameter for it."""
        assert "GDELT Project" in draft.attribution_text
        assert "https://www.gdeltproject.org/" in draft.attribution_text

    def test_no_attribution_string_is_hard_coded_in_the_collector(self, draft) -> None:
        """§28. The NOTICE must come from configuration, not from the source file.

        Asserted on the rendered sentence rather than on the domain: the domain
        appears in comments naming the host this collector may NOT reach, and
        removing those would make the file less clear rather than more correct.
        """
        source = (
            REPO_ROOT / "services/acquisition/python/sros_acquisition/collection/gdelt_web_ngram.py"
        ).read_text(encoding="utf-8")
        assert draft.attribution_text
        assert draft.attribution_text not in source
        assert "Any use or redistribution" not in source
        assert "The GDELT Project" not in source

    def test_retention_is_governance_resolved(self, draft, context) -> None:
        """§29. The collector has no expiry parameter to pass."""
        assert draft.provenance["retention_days"] == context.retention.raw_days
        assert draft.provenance["retention_basis"] == "baseline"
        assert (draft.expires_at - draft.collected_at).days == context.retention.raw_days

    def test_the_collector_cannot_choose_an_expiry(self) -> None:
        import inspect

        parameters = set(inspect.signature(build_raw_record).parameters)
        assert "expires_at" not in parameters
        assert "attribution" not in parameters

    def test_no_personal_data_field_was_introduced(self, draft) -> None:
        """§30. Four authorized fields, and nothing that resolves a person."""
        assert set(draft.payload) == {
            "source_id",
            "resource_id",
            "gram_kind",
            "date",
            "lang",
            "ngram",
            "count",
        }
        for forbidden in ("url", "title", "author", "person", "profile", "image", "domain"):
            assert forbidden not in draft.payload
            assert forbidden not in draft.provenance
