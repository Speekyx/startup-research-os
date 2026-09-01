"""The TED Search API collector, gated and bounded. Mission 1.15.7.

**No network and no database.** Every case runs the real collector against the
real catalog and the real compliance configuration, with a fake transport and a
persisted operator decision supplied the way `read_human_decisions` returns one.
The one real acquisition this mission performs is not here: a test that reached
TED would make the suite depend on a third party's availability, and §41 puts
the smoke behind every offline gate rather than among them.

The properties this file exists to protect, in the order they are enforced:

    a query with no ceiling is refused, and there is no default that supplies one
    the route comes from the authorization context, by label, with no fallback
    the resource is the one reviewed, and the bulk families stay refused
    the field selection is authorised BEFORE the request body is composed
    what comes back is the source's own structure, not a flattened copy of it
"""

from __future__ import annotations

import ast
import json
import pathlib
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sros_acquisition.collection import (
    HttpResponse,
    JsonRequest,
    TedNotice,
    TedSearchApiCollector,
    TedSearchBounds,
    TedSearchRequest,
)
from sros_acquisition.collection.job import TedSearchJobPayload
from sros_acquisition.collection.ted_search_api import (
    CONCEPTUAL_FIELDS,
    DEFAULT_CONCEPTUAL_FIELDS,
    EFORMS_PUBLICATION_START,
    MAX_NOTICES_PER_PAGE,
    MAX_RETRIEVABLE_NOTICES,
    RESOURCE_ID,
    SEARCH_PATH,
    TED_COLLECTOR_ID,
    TED_COLLECTOR_VERSION,
    TED_PACING,
    TED_ROUTE_LABEL,
    native_fields_for,
)
from sros_acquisition.compliance import AcquisitionNotAuthorizedError, build_authorization
from sros_acquisition.compliance.config import load_compliance
from sros_acquisition.compliance.resources import ResourceDescriptor
from sros_acquisition.compliance.verification import ConditionVerificationRecord
from sros_contracts import (
    ConditionVerification,
    ConditionVerificationResult,
    ResourceContentOrigin,
    RightsBasis,
)

from . import ted_search_fixtures as fx
from .conftest import LEGACY_PROFILE, LOCAL_PROFILE, REPO_ROOT

COLLECTOR_SOURCE = (
    REPO_ROOT
    / "services"
    / "acquisition"
    / "python"
    / "sros_acquisition"
    / "collection"
    / "ted_search_api.py"
)

RESIDUAL = "ted-database-right-residual-exposure-accepted"
MOMENT = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
WORKSPACE = "11111111-1111-1111-1111-111111111111"


@pytest.fixture(scope="module")
def compliance():
    return load_compliance(REPO_ROOT / "docs" / "data" / "source-compliance-v1.json")


@pytest.fixture
def ted(catalog):
    return next(s for s in catalog if s.source_id == "ted-eu")


def decision() -> ConditionVerificationRecord:
    """The persisted operator acceptance, as `read_human_decisions` returns it."""
    return ConditionVerificationRecord(
        source_id="ted-eu",
        review_version=2,
        condition_key=RESIDUAL,
        verification=ConditionVerification.HUMAN_CONFIRMATION,
        verifier="local-operator",
        verifier_version="acknowledgement-v1",
        result=ConditionVerificationResult.SATISFIED,
        reason="a test fixture standing in for a recorded operator decision",
        reference="docs/data/ted-eu-operator-risk-acceptance-v1.md",
        verified_at=MOMENT,
    )


@pytest.fixture
def context(ted, compliance):
    """Built through the production path, with the decision supplied (§38)."""
    return build_authorization(
        ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
    )


def bounds(**overrides) -> TedSearchBounds:
    base = {
        "date_start": date(2023, 3, 1),
        "date_end": date(2023, 3, 7),
        "max_pages": 1,
        "max_records": 5,
        "page_size": 5,
    }
    return TedSearchBounds(**{**base, **overrides})


class FakeTransport:
    """Records every call and replays scripted bodies. Never a socket."""

    def __init__(self, *bodies: str, status: int = 200) -> None:
        self.bodies = list(bodies)
        self.status = status
        self.calls: list[tuple[str, JsonRequest, frozenset[str]]] = []

    def post_json(
        self, base_url: str, request: JsonRequest, allowed_hosts: frozenset[str]
    ) -> HttpResponse:
        self.calls.append((base_url, request, allowed_hosts))
        body = self.bodies.pop(0) if self.bodies else fx.response()
        return HttpResponse(
            status_code=self.status, text=body, elapsed_seconds=0.01, url_path=request.path
        )


class RefusingTransport:
    """A transport that fails the test if it is ever reached.

    The refusals below are supposed to happen BEFORE a request is composed, and
    a test that only checked the return value would pass just as happily if the
    request had gone out first.
    """

    def post_json(self, *args: object, **kwargs: object) -> HttpResponse:
        raise AssertionError("a request was composed for a collection that must be refused")


def collect(context, transport, request=None, **kw):
    collector = TedSearchApiCollector(transport, pacer=_NoWaitPacer())
    return collector.collect(
        context,
        request or TedSearchRequest(bounds=bounds()),
        workspace_id=WORKSPACE,
        research_session_id=None,
        correlation_id="mission-1.15.7-test",
        now=MOMENT,
        **kw,
    )


class _NoWaitPacer:
    """Pacing is asserted separately; sleeping here would only be slow."""

    def acquire(self) -> float:
        return 0.0


# =========================================================== resource governance


class TestResourceGovernance:
    def test_the_reviewed_resource_is_authorised(self, context) -> None:
        dataset = context.authorized_dataset(RESOURCE_ID)
        assert dataset is not None
        assert dataset.dataset_family == "ted-search-api-notices"
        assert dataset.rights_basis is RightsBasis.NAMED_LICENCE
        assert dataset.licence == (
            "Commission Decision 2011/833/EU on the reuse of Commission documents"
        )
        assert dataset.content_origin == "PLATFORM_LICENSED"

    def test_the_resource_is_the_only_one(self, context) -> None:
        """One resource, not TED. A second entry appearing is a review act."""
        assert [d.resource_id for d in context.datasets] == [RESOURCE_ID]

    @pytest.mark.parametrize(
        "family",
        ["ted-bulk-xml-daily", "ted-bulk-xml-monthly", "ted-csv-historical"],
    )
    def test_the_excluded_families_stay_refused(self, context, family: str) -> None:
        decision_ = context.authorize_resource(
            ResourceDescriptor(
                source_id="ted-eu",
                resource_id=f"{family}/anything",
                licence="Commission Decision 2011/833/EU on the reuse of Commission documents",
                rights_basis=RightsBasis.NAMED_LICENCE,
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                dataset_family=family,
            )
        )
        assert not decision_.allowed
        assert any(family in reason for reason in decision_.denial_reasons)

    def test_an_unclassified_resource_is_refused(self, context) -> None:
        decision_ = context.authorize_resource(
            ResourceDescriptor(
                source_id="ted-eu",
                resource_id="notices/mystery",
                licence="Commission Decision 2011/833/EU on the reuse of Commission documents",
                rights_basis=RightsBasis.NAMED_LICENCE,
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                dataset_family=None,
            )
        )
        assert not decision_.allowed

    def test_a_resource_with_no_rights_basis_is_refused(self, context) -> None:
        """§34. The basis is required, and an entry that forgot it fails closed."""
        decision_ = context.authorize_resource(
            ResourceDescriptor(
                source_id="ted-eu",
                resource_id=RESOURCE_ID,
                dataset_family="ted-search-api-notices",
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            )
        )
        assert not decision_.allowed

    def test_third_party_content_is_refused(self, context) -> None:
        decision_ = context.authorize_resource(
            ResourceDescriptor(
                source_id="ted-eu",
                resource_id=RESOURCE_ID,
                licence="Commission Decision 2011/833/EU on the reuse of Commission documents",
                rights_basis=RightsBasis.NAMED_LICENCE,
                content_origin=ResourceContentOrigin.THIRD_PARTY,
                dataset_family="ted-search-api-notices",
            )
        )
        assert not decision_.allowed

    def test_the_commercial_profile_authorises_nothing(self, ted, compliance) -> None:
        """The resource lives under one profile. The other cannot even build."""
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(
                ted, LEGACY_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
            )
        assert "REQUIRES_REVIEW" in " ".join(caught.value.reasons)

    def test_the_collector_refuses_a_context_without_the_resource(self, context) -> None:
        """§7. Code never precedes governance. This is the state TED was in for
        six missions -- source-authorized, resource-ready NO -- and a collector
        written first would have been the thing that made it collectable."""
        stripped = replace(context, datasets=())
        result = collect(stripped, RefusingTransport())
        assert not result.succeeded
        assert "not an authorized resource" in (result.failure.detail if result.failure else "")


# ==================================================================== the route


class TestRouteBinding:
    def test_the_search_api_route_is_taken_from_the_context(self, context) -> None:
        transport = FakeTransport(fx.response(fx.CONTRACT_NOTICE))
        result = collect(context, transport)
        assert result.succeeded, result.failure
        base_url, request, allowed = transport.calls[0]
        assert base_url == "https://api.ted.europa.eu/"
        assert request.path == SEARCH_PATH
        assert allowed == frozenset({"api.ted.europa.eu"})

    def test_the_blocked_bulk_route_is_not_in_the_context(self, context) -> None:
        labels = {a.label for a in context.access}
        assert "ted-bulk-xml" not in labels
        assert context.authorize_route("ted-bulk-xml")

    def test_the_collector_refuses_when_its_route_is_absent(self, ted, compliance) -> None:
        """Remove the route and the collector stops before the network. There is
        no second route it tries instead."""
        context = build_authorization(
            ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
        )
        without = replace(
            context, access=tuple(a for a in context.access if a.label != TED_ROUTE_LABEL)
        )
        result = collect(without, RefusingTransport())
        assert not result.succeeded
        assert "does not fall back" in (result.failure.detail if result.failure else "")

    def test_the_open_data_route_is_never_used_as_a_fallback(self, ted, compliance) -> None:
        """§9. `ted-open-data-sparql` IS authorised and IS in the context, and
        the collector still refuses when the Search API route is gone. That is
        the difference between one route implemented and one route preferred."""
        context = build_authorization(
            ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
        )
        assert "ted-open-data-sparql" in {a.label for a in context.access}
        without = replace(
            context, access=tuple(a for a in context.access if a.label != TED_ROUTE_LABEL)
        )
        result = collect(without, RefusingTransport())
        assert not result.succeeded

    def test_a_route_with_no_endpoint_is_refused(self, context) -> None:
        blanked = replace(
            context,
            access=tuple(
                replace(a, endpoint_url=None) if a.label == TED_ROUTE_LABEL else a
                for a in context.access
            ),
        )
        result = collect(blanked, RefusingTransport())
        assert not result.succeeded
        assert "no endpoint" in (result.failure.detail if result.failure else "")

    def test_the_module_names_no_other_ted_host(self) -> None:
        """The endpoint comes from the registry. A literal host in the module
        would be a second source of truth, and the one it would most plausibly
        name is the bulk package host."""
        text = COLLECTOR_SOURCE.read_text(encoding="utf-8")
        code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
        for host in ("ted.europa.eu/packages", "data.ted.europa.eu", "https://api.ted"):
            assert host not in code.split('"""')[-1], host


# ======================================================== field minimisation


class TestFieldMinimisation:
    def test_the_authorised_selection_is_accepted(self, context) -> None:
        assert context.authorize_fields(DEFAULT_CONCEPTUAL_FIELDS) == ()

    @pytest.mark.parametrize(
        "excluded",
        [
            "contact_point",
            "contact_name",
            "contact_email",
            "contact_telephone",
            "contact_fax",
            "postal_address",
            "natural_person_name",
            "personal_identifier",
        ],
    )
    def test_every_excluded_personal_field_is_refused_alone(self, context, excluded) -> None:
        assert context.authorize_fields((excluded,))

    @pytest.mark.parametrize("excluded", ["contact_email", "natural_person_name"])
    def test_an_excluded_field_hidden_among_approved_ones_is_refused(
        self, context, excluded
    ) -> None:
        """The shape a real over-broad request has: mostly fine, one field not."""
        assert context.authorize_fields(("notice_id", "publication_date", excluded))

    def test_an_unreviewed_field_is_refused(self, context) -> None:
        assert context.authorize_fields(("notice_id", "some_field_nobody_reviewed"))

    def test_an_empty_selection_is_refused(self, context) -> None:
        assert context.authorize_fields(())
        assert context.authorize_fields(None)

    def test_the_collector_refuses_before_composing_a_request(self, context) -> None:
        """§13, and the assertion that makes it mean something: the transport
        raises if it is reached at all."""
        request = TedSearchRequest(
            bounds=bounds(), conceptual_fields=("notice_id", "contact_email")
        )
        result = collect(context, RefusingTransport(), request)
        assert not result.succeeded
        assert "field selection refused" in (result.failure.detail if result.failure else "")

    def test_the_request_body_carries_only_mapped_native_fields(self, context) -> None:
        transport = FakeTransport(fx.response(fx.CONTRACT_NOTICE))
        collect(context, transport)
        sent = set(transport.calls[0][1].body["fields"])
        assert sent == set(native_fields_for(DEFAULT_CONCEPTUAL_FIELDS))
        for forbidden in ("contact", "email", "tel", "fax", "ubo", "person"):
            assert not [f for f in sent if forbidden in f], forbidden

    def test_every_conceptual_field_is_one_the_review_allows(self, context) -> None:
        """The mapping table cannot drift past the minimisation profile: if a
        row appeared here that the review does not allow, the gate would refuse
        the default selection and this says so before that happens."""
        allowed = set(context.data_minimisation.allowed)
        assert {e.conceptual for e in CONCEPTUAL_FIELDS} <= allowed

    def test_monetary_amount_requires_its_type(self, context) -> None:
        """§26. TED carries the semantic in the field name, so the type is not a
        separate value -- and requesting amounts without it is refused rather
        than silently allowed, because an amount whose kind is unrecorded is the
        flattening the review forbids."""
        request = TedSearchRequest(
            bounds=bounds(), conceptual_fields=("notice_id", "monetary_amount", "currency")
        )
        result = collect(context, RefusingTransport(), request)
        assert not result.succeeded
        assert "monetary_amount_type" in (result.failure.detail if result.failure else "")

    def test_a_conceptual_field_with_no_mapping_stops_the_request(self) -> None:
        with pytest.raises(ValueError, match="no TED field mapping"):
            native_fields_for(("notice_id", "award_status", "not_mapped_here"))


# ============================================================ acquisition bounds


class TestBounds:
    def test_bounds_have_no_defaults(self) -> None:
        """§16. `TedSearchBounds()` must not be constructible: a default ceiling
        is a number nobody reviewed applied to a source with no known limit."""
        with pytest.raises(TypeError):
            TedSearchBounds()  # type: ignore[call-arg]

    def test_a_request_cannot_be_made_without_bounds(self) -> None:
        with pytest.raises(TypeError):
            TedSearchRequest()  # type: ignore[call-arg]

    def test_a_window_before_eforms_is_refused(self) -> None:
        with pytest.raises(ValueError, match="precedes the start of eForms"):
            bounds(date_start=date(2023, 2, 28))

    def test_the_eforms_start_is_the_documented_one(self) -> None:
        assert date(2023, 3, 1) == EFORMS_PUBLICATION_START

    def test_a_reversed_window_is_refused(self) -> None:
        with pytest.raises(ValueError, match="precedes date_start"):
            bounds(date_start=date(2023, 5, 1), date_end=date(2023, 4, 1))

    @pytest.mark.parametrize("name", ["max_pages", "max_records", "page_size"])
    def test_a_zero_ceiling_is_not_a_bound(self, name: str) -> None:
        with pytest.raises(ValueError, match="at least 1"):
            bounds(**{name: 0})

    def test_the_page_size_cannot_exceed_the_documented_maximum(self) -> None:
        with pytest.raises(ValueError, match="notices per page"):
            bounds(page_size=MAX_NOTICES_PER_PAGE + 1)

    def test_max_records_cannot_exceed_the_documented_retrievable_limit(self) -> None:
        with pytest.raises(ValueError, match="retrievable notices"):
            bounds(max_records=MAX_RETRIEVABLE_NOTICES + 1, page_size=250, max_pages=100)

    def test_the_fields_per_page_product_is_checked(self) -> None:
        """TED's limit is page size TIMES field count, so neither bound can be
        checked alone. Checked before the request rather than discovered from a
        400 that would have already cost a round trip."""
        assert bounds(page_size=250, max_records=250).refusals_for_fields(41)
        assert bounds(page_size=250, max_records=250).refusals_for_fields(40) == ()

    def test_the_reviewed_selection_can_never_breach_that_limit(self) -> None:
        """And the honest note about the check above: with the 24 native fields
        the reviewed selection maps to, the largest page TED allows gives
        24 x 250 = 6000, under the 10k ceiling. The guard is unreachable TODAY
        and is kept because the field selection is the thing most likely to grow,
        and the failure it would otherwise produce arrives from the source after
        the request rather than from us before it."""
        widest = bounds(page_size=MAX_NOTICES_PER_PAGE, max_records=MAX_NOTICES_PER_PAGE)
        assert widest.refusals_for_fields(len(native_fields_for(DEFAULT_CONCEPTUAL_FIELDS))) == ()

    def test_pagination_stops_at_max_pages(self, context) -> None:
        pages = [fx.response(fx.CONTRACT_NOTICE, fx.AWARD_NOTICE) for _ in range(10)]
        transport = FakeTransport(*pages)
        request = TedSearchRequest(bounds=bounds(max_pages=3, max_records=100, page_size=2))
        result = collect(context, transport, request)
        assert result.pages_fetched == 3
        assert len(transport.calls) == 3
        assert "max_pages" in result.stopped_by

    def test_collection_stops_at_max_records(self, context) -> None:
        pages = [
            fx.response(fx.CONTRACT_NOTICE, fx.AWARD_NOTICE, fx.MULTI_LOT_NOTICE) for _ in range(5)
        ]
        transport = FakeTransport(*pages)
        request = TedSearchRequest(bounds=bounds(max_pages=5, max_records=2, page_size=3))
        result = collect(context, transport, request)
        assert len(result.drafts) == 2
        assert "max_records" in result.stopped_by

    def test_the_page_numbers_are_a_bounded_range(self, context) -> None:
        transport = FakeTransport(*[fx.response(fx.CONTRACT_NOTICE) for _ in range(4)])
        request = TedSearchRequest(bounds=bounds(max_pages=4, max_records=50, page_size=1))
        collect(context, transport, request)
        assert [call[1].body["page"] for call in transport.calls] == [1, 2, 3, 4]

    def test_there_is_no_exhaustion_iterator(self) -> None:
        """§37, asserted over the source rather than over behaviour. Scroll mode
        is one key away: `paginationMode: ITERATION` plus an `iterationNextToken`
        retrieves every notice for a query with no limit, and a `while` over the
        token is the shape that would get written by accident."""
        tree = ast.parse(COLLECTOR_SOURCE.read_text(encoding="utf-8"))
        assert [n for n in ast.walk(tree) if isinstance(n, ast.While)] == []

        # Scanned over the ONE method that composes what TED receives, not over
        # the file. The module explains why scroll mode is refused and
        # `TedSearchBounds` names it in the error a caller gets for asking for
        # more than pagination mode can return -- a substring search over the
        # source fails on the paragraph that explains the rule, and weakening
        # the rule until the explanation passes is how a structural check stops
        # checking (`testing-strategy.md` §23).
        body = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_body"
        )
        sent = {
            n.value
            for n in ast.walk(body)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
        }
        assert "ITERATION" not in sent
        assert "iterationNextToken" not in sent
        assert "PAGE_NUMBER" in sent

    def test_the_body_states_the_bounded_pagination_mode(self, context) -> None:
        transport = FakeTransport(fx.response(fx.CONTRACT_NOTICE))
        collect(context, transport)
        body = transport.calls[0][1].body
        assert body["paginationMode"] == "PAGE_NUMBER"
        assert "iterationNextToken" not in body
        assert body["limit"] == 5


# ============================================================== the expert query


class TestTheQuery:
    def test_the_query_is_composed_here_and_not_supplied(self, context) -> None:
        transport = FakeTransport(fx.response(fx.CONTRACT_NOTICE))
        collect(context, transport)
        query = transport.calls[0][1].body["query"]
        assert "notice-type IN (cn-standard can-standard)" in query
        assert "publication-date>=20230301" in query
        assert "publication-date<=20230307" in query

    def test_a_request_cannot_widen_the_notice_families(self) -> None:
        with pytest.raises(ValueError, match="outside this resource"):
            TedSearchRequest(bounds=bounds(), notice_types=("cn-standard", "pin-only"))

    def test_a_request_naming_no_family_is_refused(self) -> None:
        with pytest.raises(ValueError, match="every family"):
            TedSearchRequest(bounds=bounds(), notice_types=())

    def test_a_request_naming_no_field_is_refused(self) -> None:
        with pytest.raises(ValueError, match="not a request"):
            TedSearchRequest(bounds=bounds(), conceptual_fields=())

    def test_the_collector_takes_no_raw_query_parameter(self) -> None:
        """A caller-supplied query is a caller-supplied scope. The date window,
        the families and the ordering are the reviewed shape of this resource."""
        tree = ast.parse(COLLECTOR_SOURCE.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in {"collect", "__init__"}:
                names = {a.arg for a in node.args.args} | {a.arg for a in node.args.kwonlyargs}
                assert "query" not in names, node.name


# ================================================================ the response


class TestResponseHandling:
    def test_a_contract_notice_becomes_one_draft(self, context) -> None:
        result = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        assert result.succeeded, result.failure
        assert len(result.drafts) == 1
        draft = result.drafts[0]
        assert draft.source_id == "ted-eu"
        assert draft.collector_id == TED_COLLECTOR_ID
        assert draft.collector_version == TED_COLLECTOR_VERSION

    def test_an_award_notice_keeps_its_monetary_semantics(self, context) -> None:
        """§26. Four different amounts, four different names, and the names
        survive into the payload exactly as TED published them."""
        result = collect(context, FakeTransport(fx.response(fx.AWARD_NOTICE)))
        payload = result.drafts[0].payload
        # An exact decimal STRING as of collector 1.1.0, never a JSON float.
        # `1875000.5` rather than `1875000.50` because the FIXTURE is a Python
        # float and `json.dumps` drops the trailing zero before the collector
        # ever sees the text -- the collector preserves whatever digits arrive.
        assert payload["total-value"] == "1875000.5"
        assert payload["total-value-cur"] == ["EUR"]
        assert payload["tender-value"] == ["1875000.5"]
        assert "price_paid" not in json.dumps(payload)

    def test_an_absent_monetary_block_stays_absent(self, context) -> None:
        """Absent is not zero. No amount is fabricated and no currency either."""
        result = collect(context, FakeTransport(fx.response(fx.NOTICE_WITHOUT_MONEY)))
        payload = result.drafts[0].payload
        for key in ("total-value", "tender-value", "estimated-value-lot"):
            assert key not in payload

    def test_no_currency_is_converted(self, context) -> None:
        """§27. A SEK lot beside two EUR lots comes through as SEK."""
        result = collect(context, FakeTransport(fx.response(fx.MULTI_LOT_NOTICE)))
        assert result.drafts[0].payload["tender-value-cur"] == ["EUR", "EUR", "SEK"]

    def test_lots_are_preserved_and_never_collapsed(self, context) -> None:
        """§24. Three lots under one publication number. A collector that
        deduplicated on the notice number, or unwrapped arrays to their first
        element, would keep one of the three."""
        result = collect(context, FakeTransport(fx.response(fx.MULTI_LOT_NOTICE)))
        payload = result.drafts[0].payload
        assert len(payload["tender-value"]) == 3
        assert len(payload["place-of-performance-subdiv-lot"]) == 3
        assert len(payload["classification-cpv"]) == 3

    def test_multilingual_names_are_preserved_whole(self, context) -> None:
        """§25. The Search API request carries no language selector, so no
        language is chosen. The object TED returns is stored as it arrived."""
        result = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        buyer = result.drafts[0].payload["organisation-name-buyer"]
        assert buyer == {"eng": ["Example Public Buyer"], "fra": ["Acheteur Public"]}

    def test_the_body_carries_no_language_parameter(self, context) -> None:
        transport = FakeTransport(fx.response(fx.CONTRACT_NOTICE))
        collect(context, transport)
        assert "language" not in transport.calls[0][1].body

    def test_the_payload_is_the_source_structure_with_exact_numbers(self, context) -> None:
        """Mission 1.15.10 changed exactly one thing about this payload, and the
        distinction is worth stating rather than relaxing the assertion.

        **The STRUCTURE is untouched**: same keys, same nesting, same array
        lengths, same order. What changed is the REPRESENTATION of a non-integer
        number -- an exact decimal string instead of a JSON float -- which is the
        defect repair, and it is why the collector version was bumped rather
        than edited.
        """
        result = collect(context, FakeTransport(fx.response(fx.AWARD_NOTICE)))
        payload = result.drafts[0].payload
        assert payload.keys() == fx.AWARD_NOTICE.keys()
        for key, expected in fx.AWARD_NOTICE.items():
            if isinstance(expected, float):
                assert payload[key] == format(Decimal(str(expected)), "f")
            elif isinstance(expected, list) and any(isinstance(i, float) for i in expected):
                assert len(payload[key]) == len(expected)
            else:
                assert payload[key] == expected


# ================================================================ raw identity


class TestRawIdentity:
    def test_identity_is_source_native(self, context) -> None:
        result = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        key = result.drafts[0].observation_key
        assert "00123456-2023" in key
        assert "11111111-2222-3333-4444-555555555555" in key

    def test_identity_does_not_depend_on_page_or_position(self, context) -> None:
        """§23. The same notice on page 1 and on page 3 is the same notice."""
        first = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        later = collect(
            context,
            FakeTransport(
                fx.response(fx.AWARD_NOTICE),
                fx.response(fx.MULTI_LOT_NOTICE),
                fx.response(fx.CONTRACT_NOTICE),
            ),
            TedSearchRequest(bounds=bounds(max_pages=3, max_records=50, page_size=1)),
        )
        keys = {d.observation_key for d in later.drafts}
        assert first.drafts[0].observation_key in keys

    def test_a_version_makes_a_distinct_object(self, context) -> None:
        """A corrected notice and the notice it corrects are source-distinct.
        A key ignoring the version would make the second overwrite the first."""
        corrected = {**fx.CONTRACT_NOTICE, "notice-version": 2}
        one = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        two = collect(context, FakeTransport(fx.response(corrected)))
        assert one.drafts[0].observation_key != two.drafts[0].observation_key

    def test_a_notice_without_identity_is_refused(self, context) -> None:
        """§31. No source identity, no record. Persisting it would either
        collide with another notice or invent an identity for this one."""
        result = collect(context, FakeTransport(fx.response(fx.NOTICE_WITHOUT_IDENTITY)))
        assert not result.succeeded
        assert "no source identity" in (result.failure.detail if result.failure else "")
        assert result.drafts == ()

    def test_a_repeat_within_one_run_is_not_persisted_twice(self, context) -> None:
        """Pagination mode is documented as stateless and inconsistent across
        pages when an OJ S is released mid-collection, so a repeat is expected."""
        transport = FakeTransport(fx.response(fx.CONTRACT_NOTICE), fx.response(fx.CONTRACT_NOTICE))
        request = TedSearchRequest(bounds=bounds(max_pages=2, max_records=50, page_size=1))
        result = collect(context, transport, request)
        assert len(result.drafts) == 1
        assert result.notices_seen == 2

    def test_the_same_notice_produces_the_same_record_id(self, context) -> None:
        one = collect(context, FakeTransport(fx.response(fx.AWARD_NOTICE)))
        two = collect(context, FakeTransport(fx.response(fx.AWARD_NOTICE)))
        assert one.drafts[0].record_id == two.drafts[0].record_id

    def test_a_changed_payload_produces_a_different_record(self, context) -> None:
        """Existing revision semantics: same identity, different content hash."""
        amended = {**fx.AWARD_NOTICE, "total-value": 1900000.00}
        one = collect(context, FakeTransport(fx.response(fx.AWARD_NOTICE)))
        two = collect(context, FakeTransport(fx.response(amended)))
        assert one.drafts[0].observation_key == two.drafts[0].observation_key
        assert one.drafts[0].content_hash != two.drafts[0].content_hash
        assert one.drafts[0].record_id != two.drafts[0].record_id

    def test_observed_at_is_left_unset(self) -> None:
        """The publication date is IN the payload and is not promoted to the
        canonical instant. No mission has established TED's temporal semantics,
        and a plausible instant is worse than a declared absence."""
        notice = TedNotice(
            resource_id=RESOURCE_ID,
            publication_number="00123456-2023",
            notice_identifier=None,
            notice_version=None,
            fields={"publication-date": "2023-03-02Z"},
            retrieved_at=MOMENT,
        )
        assert notice.observed_at is None


# ========================================================= failure and drift


class TestFailureHandling:
    def test_a_missing_notices_key_is_reported_as_drift(self, context) -> None:
        """§32. Not an empty page. A required structural field disappearing is a
        contract change, and reading it as "no results" states something about
        the world instead."""
        result = collect(context, FakeTransport(fx.response_missing_notices()))
        assert not result.succeeded
        assert "response-contract change" in (result.failure.detail if result.failure else "")

    def test_notices_of_the_wrong_type_is_reported_as_drift(self, context) -> None:
        result = collect(context, FakeTransport(fx.response_notices_not_a_list()))
        assert not result.succeeded

    def test_a_non_json_body_is_reported(self, context) -> None:
        result = collect(context, FakeTransport(fx.MALFORMED_NOT_JSON))
        assert not result.succeeded
        assert "not JSON" in (result.failure.detail if result.failure else "")

    @pytest.mark.parametrize("status", [400, 404, 429, 500, 503])
    def test_a_non_2xx_status_produces_a_classified_failure(self, context, status) -> None:
        result = collect(context, FakeTransport(fx.response(), status=status))
        assert not result.succeeded
        assert result.failure is not None
        assert str(status) in result.failure.detail

    def test_the_response_body_never_enters_the_failure_detail(self, context) -> None:
        """§33 of Mission 1.5, and it matters more here: a 400 from the expert
        query parser echoes the query, and a third party's text may carry
        anything."""
        leak = json.dumps({"message": "SECRET-CANARY-VALUE", "error": {"type": "X"}})
        result = collect(context, FakeTransport(leak, status=400))
        assert result.failure is not None
        assert "SECRET-CANARY-VALUE" not in result.failure.detail

    def test_an_empty_page_stops_without_failing(self, context) -> None:
        result = collect(context, FakeTransport(fx.response()))
        assert result.succeeded
        assert result.drafts == ()

    def test_a_failure_mid_collection_keeps_the_drafts_already_built(self, context) -> None:
        transport = FakeTransport(fx.response(fx.CONTRACT_NOTICE), fx.MALFORMED_NOT_JSON)
        request = TedSearchRequest(bounds=bounds(max_pages=2, max_records=50, page_size=1))
        result = collect(context, transport, request)
        assert not result.succeeded
        assert len(result.drafts) == 1


# ================================================= provenance, pacing, retention


class TestProvenance:
    def test_the_draft_records_the_route_it_actually_used(self, context) -> None:
        result = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        provenance = result.drafts[0].provenance
        assert provenance["access_profile"] == TED_ROUTE_LABEL
        assert provenance["endpoint"] == "https://api.ted.europa.eu/"

    def test_the_draft_records_the_governance_facts(self, context) -> None:
        provenance = (
            collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE))).drafts[0].provenance
        )
        assert provenance["resource_id"] == RESOURCE_ID
        assert provenance["dataset_family"] == "ted-search-api-notices"
        assert provenance["rights_basis"] == "NAMED_LICENCE"
        assert provenance["review_version"] == 2
        assert provenance["condition_snapshot"][RESIDUAL] == "SATISFIED"

    def test_the_draft_records_the_query_that_produced_it(self, context) -> None:
        provenance = (
            collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE))).drafts[0].provenance
        )
        assert provenance["pagination_mode"] == "PAGE_NUMBER"
        assert provenance["rate_limit"] == "UNKNOWN"
        assert provenance["acquisition_bounds_origin"] == "INTERNAL_SAFETY_POLICY"
        assert provenance["date_window"] == ["2023-03-01", "2023-03-07"]

    def test_retention_comes_from_governance_not_from_the_collector(self, context) -> None:
        """§30. There is no retention parameter to pass, so the platform
        baseline applies and nothing here can widen it."""
        draft = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE))).drafts[0]
        assert draft.expires_at is not None
        assert draft.expires_at > draft.collected_at
        assert draft.provenance["retention_days"] == context.retention.raw_days

    def test_the_attribution_is_rendered_from_the_reviewed_licence(self, context) -> None:
        draft = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE))).drafts[0]
        assert "Tenders Electronic Daily" in (draft.attribution_text or "")
        assert "2011/833/EU" in (draft.attribution_text or "")

    def test_the_pacing_is_ours_and_says_so(self) -> None:
        """§17. TED publishes no limit; every number here is a choice we made."""
        assert TED_PACING.origin == "INTERNAL_SAFETY_POLICY"
        assert "no rate limit" in TED_PACING.basis
        assert TED_PACING.min_interval_seconds >= 1.0


# =========================================== the whole production sequence (§38)


class TestTheProductionSequence:
    def test_no_decision_means_no_context_and_therefore_no_collection(
        self, ted, compliance
    ) -> None:
        """The first link. Without the persisted operator acceptance the
        authorization does not build, so there is nothing to hand a collector."""
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LOCAL_PROFILE, compliance, environ={}, now=MOMENT)
        assert RESIDUAL in " ".join(caught.value.reasons)

    def test_the_full_chain_runs_end_to_end(self, ted, compliance) -> None:
        """profile -> persisted decision -> live verification -> authorization
        -> resource -> route -> fields -> bounds -> collector -> draft.

        Built through `build_authorization` with the decision supplied, which is
        what the job path does. No verification set is merged by hand."""
        context = build_authorization(
            ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
        )
        assert context.use_profile_id == LOCAL_PROFILE
        result = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        assert result.succeeded, result.failure
        assert len(result.drafts) == 1
        assert result.drafts[0].provenance["source_id"] == "ted-eu"

    def test_the_collector_cannot_be_constructed_with_an_authorization(self) -> None:
        """There is no convenience constructor that makes a context, and
        `collect` takes one positionally with no default."""
        import inspect

        signature = inspect.signature(TedSearchApiCollector.collect)
        first = list(signature.parameters.values())[1]
        assert first.name == "context"
        assert first.default is inspect.Parameter.empty


# ============================================================ the module fence


def test_the_collector_never_names_price_paid() -> None:
    """§26, asserted over the source. `price_paid` is the flattening Mission
    1.15.3 forbids, and the only way it enters is by somebody writing it."""
    text = COLLECTOR_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "price_paid" not in node.value or "forbids" in node.value
        if isinstance(node, ast.Name):
            assert node.id != "price_paid"


def test_the_collector_converts_no_currency() -> None:
    """§27. No rate, no table, no arithmetic on an amount."""
    text = COLLECTOR_SOURCE.read_text(encoding="utf-8").lower()
    body = text.split('"""', 2)[-1]
    for token in ("exchange_rate", "to_eur", "convert_currency", "fx_rate"):
        assert token not in body, token


def test_the_collector_imports_no_http_client() -> None:
    """The boundary is `collection/transport.py` and stays there."""
    tree = ast.parse(COLLECTOR_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "aiohttp", "socket", "http"}


def test_no_test_in_this_file_reaches_the_network() -> None:
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "aiohttp", "socket"}


def test_no_fixture_carries_a_natural_person_field() -> None:
    """The fixtures are invented and organisation-level. Asserted rather than
    trusted, because a fixture is where a contact block would most plausibly
    arrive without anybody deciding to add one."""
    text = pathlib.Path(fx.__file__).read_text(encoding="utf-8").lower()
    body = text.split('"""', 2)[-1]
    for token in ("contact-", "-email", "-tel", "-fax", "ubo-", "person"):
        assert token not in body, token


# ================================================ the production job payload (§19)


class TestTheJobPayload:
    """`run_ted_search_job` is the production entry point, and its payload is
    where an unbounded TED collection would most plausibly be requested."""

    BASE = {
        "workspace_id": WORKSPACE,
        "research_session_id": "22222222-2222-2222-2222-222222222222",
        "correlation_id": "mission-1.15.7",
        "date_start": "2023-03-01",
        "date_end": "2023-03-07",
        "max_pages": 1,
        "max_records": 5,
        "page_size": 5,
    }

    def test_a_complete_payload_parses(self) -> None:
        job = TedSearchJobPayload.from_payload(dict(self.BASE))
        assert job.request().bounds.max_records == 5
        assert job.source_id == "ted-eu"

    @pytest.mark.parametrize(
        "bound", ["date_start", "date_end", "max_pages", "max_records", "page_size"]
    )
    def test_every_bound_is_required(self, bound: str) -> None:
        """§16 at the job boundary. `WorldBankJobPayload` defaults its ceilings;
        this one cannot, because TED's rate limit is UNKNOWN and the operator
        acceptance behind this source is conditioned on bounded queries."""
        payload = {k: v for k, v in self.BASE.items() if k != bound}
        with pytest.raises(ValueError, match="states no"):
            TedSearchJobPayload.from_payload(payload)

    def test_the_tenant_headers_are_still_required(self) -> None:
        payload = {k: v for k, v in self.BASE.items() if k != "workspace_id"}
        with pytest.raises(ValueError, match="missing required headers"):
            TedSearchJobPayload.from_payload(payload)

    def test_the_idempotency_key_excludes_the_retrieval_time(self) -> None:
        one = TedSearchJobPayload.from_payload(dict(self.BASE)).idempotency_key
        two = TedSearchJobPayload.from_payload(dict(self.BASE)).idempotency_key
        assert one == two
        assert "2023-03-01" in one

    def test_a_different_window_is_a_different_job(self) -> None:
        other = {**self.BASE, "date_end": "2023-03-14"}
        assert (
            TedSearchJobPayload.from_payload(dict(self.BASE)).idempotency_key
            != TedSearchJobPayload.from_payload(other).idempotency_key
        )

    def test_the_payload_cannot_widen_the_notice_families(self) -> None:
        payload = {**self.BASE, "notice_types": ["cn-standard", "pin-only"]}
        with pytest.raises(ValueError, match="outside this resource"):
            TedSearchJobPayload.from_payload(payload).request()


# ============================================ the Decimal repair (Mission 1.15.10)


class TestExactNumericParsing:
    """Collector 1.1.0. The defect Mission 1.15.8 recorded, and its repair.

    **The values here are chosen to EXPOSE the difference**, which `73415.22`
    does not: it survives a float round trip intact, which is exactly why the
    defect went unnoticed for two missions.
    """

    # More significant digits than an IEEE-754 double can hold. A float would
    # return 12345678901234567.0 and the trailing `89` would be gone.
    LONG = "12345678901234567.89"
    # The canonical float-representation trap. As a double this is
    # 0.1000000000000000055511151231257827, and `0.1 + 0.2 != 0.3`.
    THIRD = "0.30000000000000004"

    def notice_with(self, value: str) -> str:
        """A response whose amount is written as a JSON NUMBER, as TED sends it."""
        body = json.dumps(
            {
                "notices": [{**fx.AWARD_NOTICE, "total-value": 0}],
                "totalNoticeCount": 1,
                "timedOut": False,
            }
        )
        # Substituted into the TEXT so the number reaches `json.loads` as a JSON
        # numeric literal. Building it in Python would put a float in before the
        # parser ever saw it, which is the very step under test.
        return body.replace('"total-value": 0', f'"total-value": {value}')

    def test_a_long_decimal_survives_collection_exactly(self, context) -> None:
        result = collect(context, FakeTransport(self.notice_with(self.LONG)))
        assert result.drafts[0].payload["total-value"] == self.LONG

    def test_the_float_trap_survives_collection_exactly(self, context) -> None:
        result = collect(context, FakeTransport(self.notice_with(self.THIRD)))
        assert result.drafts[0].payload["total-value"] == self.THIRD

    def test_the_old_behaviour_would_have_lost_it(self) -> None:
        """States the defect rather than only its absence.

        A plain `json.loads` is what collector 1.0.0 did, and the assertion is
        written to be TRUE: the value really does change. A future edit that
        reverts `parse_float=Decimal` turns the tests above red while this one
        stays green, which is how a reader learns what broke.
        """
        lost = json.loads(f'{{"v": {self.LONG}}}')["v"]
        assert isinstance(lost, float)
        assert format(Decimal(str(lost)), "f") != self.LONG

        kept = json.loads(f'{{"v": {self.LONG}}}', parse_float=Decimal)["v"]
        assert isinstance(kept, Decimal)
        assert format(kept, "f") == self.LONG

    def test_no_float_reaches_the_record(self, context) -> None:
        """§36. Not one value anywhere in the payload is a binary float."""

        def floats(value: object) -> list[float]:
            if isinstance(value, bool):
                return []
            if isinstance(value, float):
                return [value]
            if isinstance(value, dict):
                return [f for v in value.values() for f in floats(v)]
            if isinstance(value, list):
                return [f for v in value for f in floats(v)]
            return []

        result = collect(context, FakeTransport(self.notice_with(self.LONG)))
        assert floats(result.drafts[0].payload) == []

    def test_an_integer_stays_an_integer(self, context) -> None:
        """`parse_int` is deliberately NOT set. An integer is already exact, and
        converting it would erase the source's own distinction between `1` and
        `1.0` -- which a JSON number cannot carry and a string can."""
        result = collect(context, FakeTransport(self.notice_with("25000")))
        assert result.drafts[0].payload["total-value"] == 25000

    def test_new_records_record_the_new_collector_version(self, context) -> None:
        result = collect(context, FakeTransport(fx.response(fx.CONTRACT_NOTICE)))
        assert result.drafts[0].collector_version == "1.1.0"
        assert TED_COLLECTOR_VERSION == "1.1.0"

    def test_the_serialised_payload_round_trips_through_json(self, context) -> None:
        """The half that `canonical_number` exists for. `json.dumps` writes a
        large float in scientific notation and PostgreSQL JSONB rewrites that as
        an integer, so a fingerprint computed here would disagree with anything
        re-reading the stored payload."""
        result = collect(context, FakeTransport(self.notice_with(self.LONG)))
        payload = result.drafts[0].payload
        assert json.loads(json.dumps(payload))["total-value"] == self.LONG


# ================================== the payload's narrowing reaches the query


class TestNarrowingReachesTheQuery:
    """Mission 1.15.10. Every narrowing a payload states must appear in the
    expert query the source receives.

    **This class exists because one did not.** `cpv_division` was added to the
    dataclass, passed into `TedSearchRequest` and folded into the idempotency
    key -- three of the four places -- and never READ from the payload dict. It
    silently defaulted to `None`, and an acquisition ran broader than the one
    that had been declared before execution.

    A field asserted only at the dataclass boundary would not have caught it.
    These assert the composed QUERY, which is the only artefact the source
    actually sees.
    """

    BASE = {
        "workspace_id": WORKSPACE,
        "research_session_id": "22222222-2222-2222-2222-222222222222",
        "correlation_id": "mission-1.15.10",
        "date_start": "2023-03-01",
        "date_end": "2023-03-01",
        "max_pages": 1,
        "max_records": 5,
        "page_size": 5,
    }

    def query_for(self, **extra) -> str:
        return TedSearchJobPayload.from_payload({**self.BASE, **extra}).request().expert_query

    def test_the_cpv_division_reaches_the_query(self) -> None:
        assert "(classification-cpv=90*)" in self.query_for(cpv_division="90")

    def test_no_cpv_clause_when_none_is_stated(self) -> None:
        assert "classification-cpv" not in self.query_for()

    def test_the_notice_types_reach_the_query(self) -> None:
        assert "notice-type IN (can-standard)" in self.query_for(notice_types=["can-standard"])

    def test_both_narrowings_reach_the_query_together(self) -> None:
        query = self.query_for(notice_types=["can-standard"], cpv_division="90")
        assert "notice-type IN (can-standard)" in query
        assert "(classification-cpv=90*)" in query

    def test_the_cpv_division_reaches_the_idempotency_key(self) -> None:
        with_division = TedSearchJobPayload.from_payload({**self.BASE, "cpv_division": "90"})
        without = TedSearchJobPayload.from_payload(dict(self.BASE))
        assert with_division.idempotency_key != without.idempotency_key
        assert "90" in with_division.idempotency_key

    @pytest.mark.parametrize("bad", ["9", "900", "9a", ""])
    def test_a_value_that_is_not_a_division_is_refused(self, bad: str) -> None:
        """Two digits, because that is the granularity the Signal cohort key
        uses. A longer prefix would filter below it and a shorter one is not a
        division."""
        payload = {**self.BASE, "cpv_division": bad}
        if bad == "":
            assert "classification-cpv" not in self.query_for(cpv_division=bad)
            return
        with pytest.raises(ValueError, match="CPV division"):
            TedSearchJobPayload.from_payload(payload).request()

    def test_the_narrowing_never_widens_the_resource(self) -> None:
        """A CPV filter cannot reach a notice family the resource excludes."""
        with pytest.raises(ValueError, match="outside this resource"):
            TedSearchJobPayload.from_payload(
                {**self.BASE, "notice_types": ["pin-only"], "cpv_division": "90"}
            ).request()
