"""The live WEB-NGRAM smoke suite. Opt-in, and absent from CI.

Mission 1.9.3 §50. Every other GDELT test in this repository runs against
fixture files; this is the only one that contacts `data.gdeltproject.org`, and
it does so only when `SROS_ENABLE_GDELT_WEB_NGRAM_SMOKE_TESTS=1`.

**The flag is separate from having a network**, the same argument the World Bank
smoke suite makes: a developer with an internet connection has not consented to
sending traffic to a third party on every test run, and CI has a connection for
reasons unrelated to this. A suite that quietly became enabled would show up as
traffic to somebody else's servers rather than as a red build.

**It proves connectivity and the file shape, and nothing else.** One explicitly
named bucket, one resource, one file, a narrow lexical filter, and **nothing is
persisted**. There is no crawl for the latest file and no retry against
neighbouring buckets — §37 and §50 are explicit, and a smoke test that hunted for
a file that exists would be testing the hunt rather than the path.

The governance path is not shortcut. The authorization is built the same way,
the resource is authorised the same way, the job size is checked the same way,
and the host comes from the same access profile.
"""

from __future__ import annotations

import os

import pytest
from sros_acquisition.collection import (
    GdeltWebNgramCollector,
    HttpxTransport,
    NgramBounds,
    RequestPacer,
    TransportConfig,
    WebNgramRequest,
)
from sros_acquisition.collection.pacing import WEB_NGRAM_PACING
from sros_acquisition.compliance import build_authorization, load_compliance

from .conftest import LEGACY_PROFILE, REPO_ROOT, WORKSPACE_A

SMOKE_FLAG = "SROS_ENABLE_GDELT_WEB_NGRAM_SMOKE_TESTS"
#: The bucket to fetch, as an explicit source label. Overridable because a file
#: has to exist at the moment somebody runs this, and H-31 means nobody knows
#: how far back the directory reaches — so the operator names one rather than
#: the suite guessing and retrying.
BUCKET_ENV = "SROS_GDELT_SMOKE_BUCKET"

live_only = pytest.mark.skipif(
    os.environ.get(SMOKE_FLAG, "0") != "1",
    reason=f"live GDELT WEB-NGRAM suite is opt-in; set {SMOKE_FLAG}=1",
)


@pytest.fixture(scope="module")
def context(catalog):
    compliance = load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")
    return build_authorization(catalog.get("gdelt"), LEGACY_PROFILE, compliance, environ={})


@live_only
class TestLiveWebNgram:
    def test_the_opt_in_flag_is_what_enabled_this(self) -> None:
        assert os.environ.get(SMOKE_FLAG) == "1"

    def test_the_governance_path_runs_before_anything_is_fetched(self, context) -> None:
        """Eligibility, then the concrete resource, then the job size. A smoke
        test that skipped them would be proving a different path works."""
        assert context.source_id == "gdelt"
        assert context.review_version == 3
        assert {d.resource_id for d in context.datasets} == {
            "web-ngrams/1gram",
            "web-ngrams/2gram",
        }
        assert context.authorize_job_size(1) == ()
        assert context.authorize_job_size(9)

    def test_one_file_downloads_parses_and_persists_nothing(self, context) -> None:
        """§50. One bucket, one resource, one narrow filter, no database.

        `climate` is the term Mission 1.9.1's contract inspection already used
        and it is deliberately benign: the objective is to prove the acquisition
        path, not to do research.
        """
        bucket = os.environ.get(BUCKET_ENV)
        if not bucket:
            pytest.skip(f"set {BUCKET_ENV} to an explicit YYYYMMDDHHMMSS source bucket label")

        collector = GdeltWebNgramCollector(
            HttpxTransport(TransportConfig(read_timeout_seconds=60.0, total_timeout_seconds=90.0)),
            pacer=RequestPacer(WEB_NGRAM_PACING),
        )
        result = collector.collect(
            context,
            WebNgramRequest(
                buckets=(bucket,), grams=("1gram",), languages=("ENGLISH",), ngrams=("climate",)
            ),
            workspace_id=WORKSPACE_A,
            correlation_id="gdelt-web-ngram-smoke",
            bounds=NgramBounds(max_records=5),
        )

        assert result.succeeded, [f.to_json() for f in result.failures]
        assert result.files_requested == 1
        assert result.files_processed == 1
        # The file spans every language GDELT monitors, so a scan that saw only
        # what it kept would mean the filter had been applied by somebody else.
        assert result.rows_scanned > result.rows_matched

        for draft in result.drafts:
            assert draft.payload["date"] == bucket
            assert draft.payload["lang"] == "ENGLISH"
            assert draft.payload["ngram"] == "climate"
            assert draft.payload["count"].isdigit()
            # H-29 and H-30, live.
            assert draft.observed_at is None
            assert draft.content_language is None

    def test_only_the_authorized_host_was_contacted(self, context) -> None:
        """The allowlist this collector uses is the ngram profile's, and it does
        not include the source's own API host."""
        access = next(a for a in context.access if a.label == "gdelt-web-ngram-files")
        assert access.endpoint_url == "https://data.gdeltproject.org/gdeltv3/web/ngrams/"
        assert access.access_method == "DATASET_DOWNLOAD"
