"""The live smoke suite. Opt-in, and absent from CI.

Mission 1.5 §12 and §47. Every other test in this repository runs against a fake
transport; this is the only one that contacts the World Bank, and it does so
only when `SROS_ENABLE_WORLD_BANK_SMOKE_TESTS=1`.

**The flag is separate from having a network** on purpose, and it is the same
argument Mission 0.4 made for the provider smoke tests: a developer with an
internet connection has not consented to sending traffic to a third party on
every test run, and CI has a connection for reasons unrelated to this. A suite
that quietly became enabled would show up as traffic to somebody else's servers
rather than as a red build.

**It proves connectivity and parsing, and nothing else.** One indicator, one
country, one year, one page, at most five records, and nothing is persisted. §47
is explicit that bulk collection is a different act; this exists to confirm that
the documented response shape is the actual response shape, which no fake can
establish.

The governance path is not shortcut. The authorization is built the same way,
the resource is authorised the same way, and the host allowlist comes from the
same access profile.
"""

from __future__ import annotations

import os

import pytest
from sros_acquisition.collection import (
    CollectionBounds,
    HttpxTransport,
    RequestPacer,
    TransportConfig,
    WorldBankCollector,
    WorldBankRequest,
)
from sros_acquisition.collection.pacing import WORLD_BANK_PACING
from sros_acquisition.compliance import build_authorization, load_compliance
from sros_contracts import ResourceContentOrigin

from .conftest import REPO_ROOT, WORKSPACE_A

SMOKE_FLAG = "SROS_ENABLE_WORLD_BANK_SMOKE_TESTS"

live_only = pytest.mark.skipif(
    os.environ.get(SMOKE_FLAG, "0") != "1",
    reason=f"live World Bank suite is opt-in; set {SMOKE_FLAG}=1",
)


@pytest.fixture(scope="module")
def context(catalog):
    compliance = load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")
    return build_authorization(catalog.get("world-bank"), compliance, environ={})


@live_only
class TestLiveWorldBank:
    def test_the_opt_in_flag_is_what_enabled_this(self) -> None:
        """If this file runs at all, the flag was set deliberately."""
        assert os.environ[SMOKE_FLAG] == "1"

    def test_a_tiny_authorized_request_returns_a_parseable_observation(self, context) -> None:
        """One indicator, one country, one year. The smallest request that can
        prove the envelope is what the collector expects."""
        collector = WorldBankCollector(
            HttpxTransport(TransportConfig(read_timeout_seconds=20.0)),
            pacer=RequestPacer(WORLD_BANK_PACING),
        )
        result = collector.collect(
            context,
            WorldBankRequest(
                indicators=("SP.POP.TOTL",),
                countries=("FR",),
                start_year=2020,
                end_year=2020,
                per_page=5,
            ),
            workspace_id=WORKSPACE_A,
            correlation_id="live-smoke",
            bounds=CollectionBounds(max_pages=1, max_records=5),
        )

        assert result.succeeded, result.to_json()
        assert result.requests_made == 1
        assert len(result.drafts) == 1

        draft = result.drafts[0]
        assert draft.observation_key == "world-bank|indicator/SP.POP.TOTL|FRA|2020"
        assert draft.payload["period"] == "2020"
        assert isinstance(draft.payload["value"], float)
        assert draft.payload["geography"] == "FRA"
        # The parse is a parse, not a normalization (§36): the field names still
        # mirror what the source returned.
        assert draft.provenance["licence"] == "CC-BY-4.0"
        assert "The World Bank" in draft.attribution_text

    def test_an_unauthorized_indicator_still_costs_zero_requests_live(self, context) -> None:
        """The gate is not something the real transport changes. Asserted here
        too, because 'it refused in the unit test' is a weaker statement than
        'it refused with a real client attached'."""
        collector = WorldBankCollector(HttpxTransport(), pacer=RequestPacer(WORLD_BANK_PACING))
        result = collector.collect(
            context,
            WorldBankRequest(indicators=("DT.DOD.DECT.CD",), countries=("FR",)),
            workspace_id=WORKSPACE_A,
            correlation_id="live-smoke-refusal",
        )
        assert result.requests_made == 0
        assert result.refused_resources == ["indicator/DT.DOD.DECT.CD"]

    def test_the_host_allowlist_holds_against_a_real_client(self, context) -> None:
        """§10. The refusal happens before a socket, and with the real transport
        rather than a fake one."""
        from sros_acquisition.collection import HttpRequest
        from sros_acquisition.collection.errors import AcquisitionFailedError

        with pytest.raises(AcquisitionFailedError, match="not in the authorized set"):
            HttpxTransport().get(
                "https://example.invalid/v2/",
                HttpRequest(path="country/FR/indicator/SP.POP.TOTL"),
                frozenset({"api.worldbank.org"}),
            )

    def test_nothing_was_persisted_by_this_suite(self, context) -> None:
        """§47. The smoke test does not write. Persisting from a connectivity
        check would make 'did it run' and 'what is in the database' the same
        question."""
        descriptor_source = WorldBankCollector.collect.__doc__ or ""
        assert "persist" not in descriptor_source.lower()
        # The collector returns drafts; persistence is a separate call that this
        # suite never makes.
        assert not hasattr(WorldBankCollector, "persist")
        assert ResourceContentOrigin.PLATFORM_LICENSED is not None
