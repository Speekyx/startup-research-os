"""The collector conformance suite. Mission 1.4's debt, paid.

Mission 1.5 §5. Mission 1.4 built a compliance layer and could not prove a
collector goes through it, because no collector existed. Its gap analysis
recorded the obligation precisely:

> This places a requirement on Mission 1.5 [...]: the first collector must
> obtain every resource through the authorization context's resource gate, and a
> conformance test must assert that it has no other path to a URL. Until such a
> test exists, the guarantee is architectural, not observed.

This file is what turns that architectural guarantee into an observed one. It is
deliberately **structural** as well as behavioural: behaviour tests prove the
collector goes through the gate today, and the structural tests prove there is no
second door for it to start using tomorrow.

Nothing here reaches a network. The `RecordingTransport` counts calls and never
opens a socket, which is what makes "zero network calls" an assertion rather
than a hope.
"""

from __future__ import annotations

import inspect
import json
import pathlib
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest
import sros_acquisition
from sros_acquisition.collection import (
    HttpRequest,
    HttpResponse,
    HttpxTransport,
    RequestPacer,
    WorldBankCollector,
    WorldBankRequest,
)
from sros_acquisition.collection.errors import AcquisitionFailedError
from sros_acquisition.collection.pacing import WORLD_BANK_PACING
from sros_acquisition.compliance import (
    AcquisitionNotAuthorizedError,
    build_authorization,
    load_compliance,
)
from sros_contracts import AcquisitionErrorCode

from .conftest import LEGACY_PROFILE, REPO_ROOT

WORKSPACE = "00000000-0000-4000-8000-000000000001"
AUTHORIZED_INDICATOR = "SP.POP.TOTL"
UNAUTHORIZED_INDICATOR = "DT.DOD.DECT.CD"

# Every module in the acquisition package that may reach a network. Exactly one.
NETWORK_BOUNDARY = {"transport.py"}
NETWORK_IMPORTS = (
    "httpx",
    "requests",
    "aiohttp",
    "urllib.request",
    "http.client",
    "socket",
    "playwright",
    "selenium",
)


@dataclass
class RecordingTransport:
    """A transport that records and never connects.

    Returns a valid single-page envelope so the collector's success path is
    exercised; what the tests assert on is `calls`.
    """

    calls: list[tuple[str, str, dict[str, str]]] = field(default_factory=list)
    body: str | None = None

    def get(
        self, base_url: str, request: HttpRequest, allowed_hosts: frozenset[str]
    ) -> HttpResponse:
        self.calls.append((base_url, request.path, dict(request.query)))
        return HttpResponse(200, self.body or _page(), 0.01, request.path)


def _page(rows: list[dict[str, object]] | None = None, **meta: object) -> str:
    envelope = {"page": 1, "pages": 1, "per_page": 50, "total": 1, "lastupdated": "2025-07-01"}
    envelope.update(meta)
    return json.dumps([envelope, rows if rows is not None else [_row()]])


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "indicator": {"id": AUTHORIZED_INDICATOR, "value": "Population, total"},
        "country": {"id": "FR", "value": "France"},
        "countryiso3code": "FRA",
        "date": "2020",
        "value": 67571107,
        "unit": "",
        "obs_status": "",
        "decimal": 0,
    }
    row.update(overrides)
    return row


@pytest.fixture(scope="session")
def compliance():
    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


@pytest.fixture(scope="session")
def world_bank(catalog):
    return catalog.get("world-bank")


@pytest.fixture
def context(world_bank, compliance):
    return build_authorization(world_bank, LEGACY_PROFILE, compliance, environ={})


def _collector(transport: object) -> WorldBankCollector:
    return WorldBankCollector(
        transport,  # type: ignore[arg-type]
        pacer=RequestPacer(WORLD_BANK_PACING, sleep=lambda _: None),
        now=lambda: datetime(2026, 8, 30, tzinfo=UTC),
    )


# =============================================== the collector cannot self-authorise


class TestAuthorizationIsRequired:
    def test_collect_has_no_signature_without_a_context(self) -> None:
        """§4. The context is the FIRST positional parameter and has no default.

        Structural on purpose: a behaviour test proves today's call passes one,
        and this proves nobody can add an overload tomorrow that does not."""
        signature = inspect.signature(WorldBankCollector.collect)
        parameters = list(signature.parameters.values())
        assert parameters[1].name == "context"
        assert parameters[1].default is inspect.Parameter.empty
        assert parameters[1].annotation == "AcquisitionAuthorizationContext"

    def test_the_collector_cannot_build_its_own_authorization(self) -> None:
        """A collector that could authorise itself would be a collector that
        could approve itself.

        Asserted over the module NAMESPACE rather than its text: the name has to
        be imported before it can be called, and a source scan would also match
        the docstring that explains why it is absent."""
        module = inspect.getmodule(WorldBankCollector)
        assert module is not None
        for name in ("build_authorization", "load_compliance", "load_catalog"):
            assert not hasattr(module, name), name

    def test_an_ineligible_source_produces_no_authorization_and_no_request(
        self, catalog, compliance
    ) -> None:
        """§41. The refusal happens before a collector exists to be called, so
        there is nothing to count: no authorization, therefore no collector run."""
        transport = RecordingTransport()
        for source_id in ("youtube", "reddit", "github"):
            with pytest.raises(AcquisitionNotAuthorizedError):
                build_authorization(catalog.get(source_id), LEGACY_PROFILE, compliance, environ={})
        assert transport.calls == []

    def test_another_sources_authorization_is_refused(self, catalog, compliance, context) -> None:
        """One source's approval never authorises another's collection."""
        eurostat = build_authorization(
            catalog.get("eurostat"), LEGACY_PROFILE, compliance, environ={}
        )
        transport = RecordingTransport()
        with pytest.raises(AcquisitionFailedError) as caught:
            _collector(transport).collect(
                eurostat,
                WorldBankRequest(indicators=(AUTHORIZED_INDICATOR,)),
                workspace_id=WORKSPACE,
                correlation_id="probe",
            )
        assert caught.value.failure.code is AcquisitionErrorCode.AUTHORIZATION_REJECTED
        assert transport.calls == []


# ================================================ every resource goes through the gate


class TestEveryResourceIsAuthorized:
    def test_an_unauthorized_indicator_costs_zero_network_calls(self, context) -> None:
        """§41, and the assertion the whole mission turns on. Not "is refused" —
        **zero calls**: a gate that refuses after the request has gone out has
        not prevented anything."""
        transport = RecordingTransport()
        result = _collector(transport).collect(
            context,
            WorldBankRequest(indicators=(UNAUTHORIZED_INDICATOR,)),
            workspace_id=WORKSPACE,
            correlation_id="probe",
        )
        assert transport.calls == []
        assert result.drafts == []
        assert result.refused_resources == [f"indicator/{UNAUTHORIZED_INDICATOR}"]
        assert result.failures[0].code is AcquisitionErrorCode.RESOURCE_NOT_PERMITTED

    def test_one_refused_indicator_does_not_stop_an_authorized_one(self, context) -> None:
        """A refusal is per resource. Collapsing the batch would tempt a caller
        to drop the refused resource and retry everything, which is how an
        exclusion gets worked around."""
        transport = RecordingTransport()
        result = _collector(transport).collect(
            context,
            WorldBankRequest(indicators=(UNAUTHORIZED_INDICATOR, AUTHORIZED_INDICATOR)),
            workspace_id=WORKSPACE,
            correlation_id="probe",
        )
        assert len(transport.calls) == 1
        assert AUTHORIZED_INDICATOR in transport.calls[0][1]
        assert len(result.drafts) == 1

    def test_the_authorized_indicator_is_permitted(self, context) -> None:
        """The control case. A conformance suite that only proves refusal would
        pass against a collector that refuses everything."""
        transport = RecordingTransport()
        result = _collector(transport).collect(
            context,
            WorldBankRequest(indicators=(AUTHORIZED_INDICATOR,), countries=("FR",)),
            workspace_id=WORKSPACE,
            correlation_id="probe",
        )
        assert len(transport.calls) == 1
        assert len(result.drafts) == 1
        assert result.succeeded

    def test_microdata_is_refused(self, world_bank, compliance) -> None:
        """§41. The Microdata Library permits statistical and scientific research
        only. It is refused by the resource gate whatever a caller asks for,
        because no microdata resource is an authorized dataset."""
        context = build_authorization(world_bank, LEGACY_PROFILE, compliance, environ={})
        assert all(d.dataset_family != "microdata" for d in context.datasets)
        transport = RecordingTransport()
        result = _collector(transport).collect(
            context,
            WorldBankRequest(indicators=("LSMS",)),
            workspace_id=WORKSPACE,
            correlation_id="probe",
        )
        assert transport.calls == []
        assert result.failures[0].code is AcquisitionErrorCode.RESOURCE_NOT_PERMITTED

    def test_an_unknown_licence_is_refused_by_the_gate_itself(self, context) -> None:
        """§7. Even reaching past the dataset lookup, the resource gate denies a
        descriptor whose licence is not on the allowlist."""
        from sros_acquisition.compliance import ResourceDescriptor
        from sros_contracts import ResourceContentOrigin

        denied = context.authorize_resource(
            ResourceDescriptor(
                source_id="world-bank",
                resource_id="indicator/X",
                licence="License Specified Externally",
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                dataset_family="indicators",
            )
        )
        assert not denied.allowed

    def test_a_caller_cannot_declare_a_licence(self) -> None:
        """§7, structurally. `WorldBankRequest` has no licence, no dataset family
        and no content origin field, so a caller cannot assert its way past the
        gate. Those facts come from the authorized dataset entry."""
        fields = set(WorldBankRequest.__dataclass_fields__)
        assert fields == {"indicators", "countries", "start_year", "end_year", "per_page"}


# ====================================================== no arbitrary URL can enter


class TestNoUrlEscapeHatch:
    def test_no_public_signature_accepts_a_url(self) -> None:
        """§4. Checked over every public callable in the collection package: a
        parameter named for a URL or an endpoint is the shape an escape hatch
        takes when someone adds one 'just for testing'."""
        import sros_acquisition.collection as package

        forbidden = {"url", "urls", "endpoint", "full_url", "href", "target_url", "host"}
        # `host_of` parses a URL into a host. It performs no request and exists
        # so the allowlist can be derived from the access profile rather than
        # written as a literal -- which is the opposite of an escape hatch.
        exempt = {"host_of"}
        offenders = []
        for name in package.__all__:
            if name in exempt:
                continue
            member = getattr(package, name)
            if not (inspect.isfunction(member) or inspect.isclass(member)):
                continue
            callables = [member] if inspect.isfunction(member) else _public_methods(member)
            for func in callables:
                try:
                    parameters = set(inspect.signature(func).parameters)
                except (TypeError, ValueError):  # pragma: no cover - builtins
                    continue
                if parameters & forbidden:
                    offenders.append(f"{name}.{func.__name__}")
        # `base_url` and `allowed_hosts` on the Transport protocol are the
        # authorized endpoint and the allowlist, both supplied by the context.
        assert offenders == [], offenders

    def test_an_http_request_refuses_an_absolute_url(self) -> None:
        """The transport takes a path. Handing it a URL is a construction error,
        not something it quietly accepts."""
        for candidate in ("https://evil.example/x", "http://evil.example/x", "//evil.example/x"):
            with pytest.raises(ValueError, match="path is a path"):
                HttpRequest(path=candidate)

    def test_an_http_request_refuses_traversal(self) -> None:
        with pytest.raises(ValueError, match="traverse"):
            HttpRequest(path="country/../../admin")

    def test_an_indicator_cannot_reshape_the_request(self) -> None:
        """The indicator becomes a path segment, so anything that could change
        the shape of the path is refused at construction."""
        for candidate in ("A/B", "A?x=1", "A#f", "A B", "../etc", "A&b"):
            with pytest.raises(ValueError, match="not a valid code"):
                WorldBankRequest(indicators=(candidate,))

    def test_a_country_cannot_reshape_the_request(self) -> None:
        for candidate in ("F/R", "FR;../x", "FR?x"):
            with pytest.raises(ValueError, match="not a valid"):
                WorldBankRequest(indicators=(AUTHORIZED_INDICATOR,), countries=(candidate,))

    def test_an_unauthorized_host_is_refused_at_the_transport(self) -> None:
        """§10. Checked at the last place before a socket, not only further up:
        a guard that exists only at the collector is one a future caller routes
        around."""
        transport = HttpxTransport()
        with pytest.raises(AcquisitionFailedError) as caught:
            transport.get(
                "https://evil.example/v2/",
                HttpRequest(path="country/FR/indicator/X"),
                frozenset({"api.worldbank.org"}),
            )
        assert caught.value.failure.code is AcquisitionErrorCode.AUTHORIZATION_REJECTED
        assert "not in the authorized set" in caught.value.failure.detail

    def test_an_empty_allowlist_authorizes_nothing(self) -> None:
        """An empty allowlist is not permission to reach anything."""
        with pytest.raises(AcquisitionFailedError) as caught:
            HttpxTransport().get(
                "https://api.worldbank.org/v2/", HttpRequest(path="x"), frozenset()
            )
        assert caught.value.failure.code is AcquisitionErrorCode.AUTHORIZATION_REJECTED

    def test_a_non_https_endpoint_is_refused(self) -> None:
        with pytest.raises(AcquisitionFailedError, match="not https"):
            HttpxTransport().get(
                "http://api.worldbank.org/v2/",
                HttpRequest(path="x"),
                frozenset({"api.worldbank.org"}),
            )

    def test_the_allowlist_comes_from_the_registry_not_a_literal(self, context) -> None:
        """§10 forbids a hard-coded fallback domain. The host is derived from the
        access profile the review approved, so revoking the profile revokes the
        host."""
        transport = RecordingTransport()
        _collector(transport).collect(
            context,
            WorldBankRequest(indicators=(AUTHORIZED_INDICATOR,)),
            workspace_id=WORKSPACE,
            correlation_id="probe",
        )
        assert transport.calls[0][0] == context.access[0].endpoint_url

    def test_a_context_with_no_endpoint_authorizes_no_host(self, context) -> None:
        from dataclasses import replace

        stripped = replace(
            context,
            access=tuple(replace(a, endpoint_url=None) for a in context.access),
        )
        transport = RecordingTransport()
        with pytest.raises(AcquisitionFailedError, match="no host is authorized"):
            _collector(transport).collect(
                stripped,
                WorldBankRequest(indicators=(AUTHORIZED_INDICATOR,)),
                workspace_id=WORKSPACE,
                correlation_id="probe",
            )
        assert transport.calls == []


# ======================================================== the network boundary holds


class TestNetworkBoundary:
    def test_only_the_transport_module_may_reach_a_network(self) -> None:
        """Mission 1.0's blanket ban, NARROWED rather than deleted -- the same
        move Mission 1.2 made with the D-03 guard.

        Naming the one file that may hold a client is a stronger statement than
        forbidding all of them: it says where the network is, not merely that it
        is absent."""
        root = pathlib.Path(sros_acquisition.__file__).parent
        offenders = []
        for path in sorted(root.rglob("*.py")):
            if path.name in NETWORK_BOUNDARY:
                continue
            text = path.read_text(encoding="utf-8")
            for token in NETWORK_IMPORTS:
                if f"import {token}" in text or f"from {token}" in text:
                    offenders.append(f"{path.relative_to(root)} imports {token}")
        assert offenders == [], offenders

    def test_the_transport_imports_its_client_lazily(self) -> None:
        """ADR-009. The registry model, the compliance layer and every
        zero-dependency validator must keep running with nothing installed, and
        they would not if this module imported a client at module scope."""
        from sros_acquisition.collection import transport

        source = pathlib.Path(transport.__file__).read_text(encoding="utf-8")
        module_level = source.split("class HttpxTransport")[0]
        assert "import httpx" not in module_level
        assert "import httpx" in source

    def test_no_collector_module_outside_the_collection_package(self) -> None:
        """The registry and compliance packages govern collection. A collector
        appearing in either would put the decision and its execution in the same
        place."""
        root = pathlib.Path(sros_acquisition.__file__).parent
        for package in ("registry", "compliance"):
            found = list((root / package).rglob("*collector*.py"))
            assert found == [], found

    def test_only_the_collectors_that_were_authorised_are_registered(self) -> None:
        """§26, §57, extended in Mission 1.9.3.

        Three now, and the point is unchanged: Eurostat did not gain a collector
        because the others have one. Still an EQUALITY rather than a
        containment — a fourth name appearing without a conformance suite behind
        it is what this exists to catch.

        Mission 1.15.7 added `ted-eu`, after Mission 1.15.6.1 recorded the
        operator decision and Phase A of 1.15.7 authorised a concrete resource --
        the same order GDELT went in, and the order this equality exists to keep
        legible: resource first, collector second.
        """
        assert (
            frozenset({"world-bank", "gdelt", "ted-eu", "stack-exchange", "wikimedia-pageviews"})
            == sros_acquisition.IMPLEMENTED_COLLECTORS
        )


def _public_methods(cls: type) -> list[object]:
    return [
        member
        for name, member in inspect.getmembers(cls, inspect.isfunction)
        if not name.startswith("_")
    ]
