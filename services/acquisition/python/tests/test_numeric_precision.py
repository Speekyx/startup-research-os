"""Source numbers survive collection and normalization exactly.

Mission 1.6.1 §6 and §7. The gap analysis
(`docs/data/raw-numeric-precision-gap-analysis-v1.md`) measured four losses in
`world-bank-indicators@1.0.0`; this suite is the standing proof that `1.1.0`
closes them and does not reopen them.

**Every case drives the real collector against a fake transport.** Asserting on
`canonical_number` alone would test the serializer and miss the two places the
old defect actually lived — the JSON parse and the `float()` in `_observation`.
The value has to make the whole trip.

No test here reaches the internet.
"""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal

import pytest
from sros_acquisition.collection import (
    RequestPacer,
    WorldBankCollector,
    WorldBankRequest,
    canonical_number,
)
from sros_acquisition.collection.pacing import WORLD_BANK_PACING
from sros_acquisition.collection.transport import HttpRequest, HttpResponse
from sros_acquisition.compliance import build_authorization, load_compliance
from sros_acquisition.normalization import decimal_from
from sros_acquisition.normalization.repositories import _view

from .conftest import LEGACY_PROFILE, REPO_ROOT, WORKSPACE_P

INDICATOR = "SP.POP.TOTL"


@pytest.fixture(scope="module")
def context(catalog):
    compliance = load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")
    return build_authorization(catalog.get("world-bank"), LEGACY_PROFILE, compliance, environ={})


class _Fixed:
    """Returns one body. Never opens a socket."""

    def __init__(self, body: str) -> None:
        self.body = body

    def get(
        self, base_url: str, request: HttpRequest, allowed_hosts: frozenset[str]
    ) -> HttpResponse:
        return HttpResponse(200, self.body, 0.01, request.path)


def _body(value_literal: str) -> str:
    """A response whose `value` is written EXACTLY as the source would send it.

    Built as text rather than via `json.dumps` on purpose: the whole question is
    what happens to a literal on its way in, and serializing a Python object
    would decide part of the answer before the collector saw it.
    """
    return (
        '[{"page":1,"pages":1,"per_page":50,"total":1,"lastupdated":"2025-07-01"},'
        '[{"indicator":{"id":"SP.POP.TOTL","value":"Population, total"},'
        '"country":{"id":"FR","value":"France"},"countryiso3code":"FRA",'
        f'"date":"2020","value":{value_literal},"unit":"","obs_status":"","decimal":0}}]]'
    )


def _collect_one(context, value_literal: str):
    collector = WorldBankCollector(
        _Fixed(_body(value_literal)),  # type: ignore[arg-type]
        pacer=RequestPacer(WORLD_BANK_PACING, sleep=lambda _: None),
    )
    result = collector.collect(
        context,
        WorldBankRequest(indicators=(INDICATOR,), countries=("FR",)),
        workspace_id=WORKSPACE_P,
        correlation_id="precision-test",
    )
    assert result.succeeded, result.failures
    assert len(result.drafts) == 1
    return result.drafts[0]


# §6 asks for exactly these shapes, and no more than are needed to prove the
# mechanism. Each is a source literal paired with what must be stored.
CASES = [
    ("integer", "67158348", "67158348"),
    ("large integer beyond 2^53", "9007199254740993", "9007199254740993"),
    ("decimal", "1.25", "1.25"),
    ("small decimal, not binary-exact", "0.1", "0.1"),
    ("zero", "0", "0"),
    ("negative", "-0.35", "-0.35"),
]


class TestSourceValuesSurviveCollection:
    """§7. The value that reaches the RawRecord is the value the source sent."""

    @pytest.mark.parametrize(("label", "sent", "expected"), CASES)
    def test_the_value_is_stored_exactly(
        self, context, label: str, sent: str, expected: str
    ) -> None:
        draft = _collect_one(context, sent)
        assert draft.payload["value"] == expected, label

    def test_a_null_stays_null_and_never_becomes_zero(self, context) -> None:
        draft = _collect_one(context, "null")
        assert draft.payload["value"] is None
        # The assertion that matters: not the string "None", not "0", not 0.
        assert draft.payload["value"] != "0"
        assert draft.payload["value"] != "None"

    def test_an_integer_beyond_2_53_is_not_rounded(self, context) -> None:
        """The measured LOSS 2. A double moves this to the nearest representable
        integer, which is one less."""
        draft = _collect_one(context, "9007199254740993")
        assert draft.payload["value"] == "9007199254740993"
        assert draft.payload["value"] != "9007199254740992"

    def test_a_decimal_beyond_17_significant_digits_is_not_truncated(self, context) -> None:
        """The measured LOSS 3."""
        sent = "1.23456789012345678"
        draft = _collect_one(context, sent)
        assert draft.payload["value"] == sent
        assert draft.payload["value"] != "1.2345678901234567"

    def test_a_value_never_passes_through_float(self, context) -> None:
        """The property behind all of the above, asserted directly.

        `0.1` as a double is 0.1000000000000000055511151231257827. If the value
        had been through IEEE-754 and back, an exact comparison against the
        source literal would fail.
        """
        draft = _collect_one(context, "0.1")
        assert Decimal(str(draft.payload["value"])) == Decimal("0.1")
        assert Decimal(str(draft.payload["value"])) != Decimal(0.1)  # noqa: RUF032


class TestTypePreservation:
    """§4. `1` and `1.0` are different statements and stay different."""

    def test_an_integer_and_a_one_decimal_float_are_distinguishable(self, context) -> None:
        as_int = _collect_one(context, "1")
        as_float = _collect_one(context, "1.0")
        assert as_int.payload["value"] == "1"
        assert as_float.payload["value"] == "1.0"
        assert as_int.payload["value"] != as_float.payload["value"]

    def test_they_are_therefore_different_records(self, context) -> None:
        """The consequence that matters -- the measured LOSS 4.

        Under 1.0.0 both collapsed to `1.0`, so they hashed identically: a real
        upstream revision from `1` to `1.0` would have been persisted as
        UNCHANGED, and the change would simply not be in the history.
        """
        as_int = _collect_one(context, "1")
        as_float = _collect_one(context, "1.0")
        assert as_int.content_hash != as_float.content_hash
        assert as_int.record_id != as_float.record_id

    def test_zero_and_zero_point_zero_are_also_distinguishable(self, context) -> None:
        assert _collect_one(context, "0").payload["value"] == "0"
        assert _collect_one(context, "0.0").payload["value"] == "0.0"

    def test_two_values_differing_beyond_float_precision_do_not_collide(self, context) -> None:
        """The other half of LOSS 4: distinct observations, one record."""
        a = _collect_one(context, "9007199254740993")
        b = _collect_one(context, "9007199254740992")
        assert a.payload["value"] != b.payload["value"]
        assert a.content_hash != b.content_hash


class TestCanonicalSerialization:
    """§6. Deterministic, plain, and stable between runs."""

    @pytest.mark.parametrize(("label", "sent", "expected"), CASES)
    def test_the_hash_is_stable_across_runs(
        self, context, label: str, sent: str, expected: str
    ) -> None:
        first = _collect_one(context, sent)
        second = _collect_one(context, sent)
        assert first.content_hash == second.content_hash, label
        assert first.record_id == second.record_id, label

    def test_no_value_is_serialized_in_scientific_notation(self, context) -> None:
        """The measured LOSS 5.

        `json.dumps` writes `1.2345678901234568e+17` for a large float and
        PostgreSQL JSONB rewrites it plainly, so the hashed text and the stored
        text disagreed about a record nobody had changed.
        """
        for sent in ("123456789012345678", "0.0000001", "1000000000000000000000"):
            draft = _collect_one(context, sent)
            stored = str(draft.payload["value"])
            assert "e" not in stored.lower(), f"{sent} serialized as {stored}"

    def test_the_canonical_form_round_trips_through_json_and_jsonb_text(self, context) -> None:
        """What Python hashes must be what a reader of the payload sees.

        A string survives `json.dumps` and PostgreSQL's JSONB rendering
        unchanged; a number does not, which is why the value is a string.
        """
        for sent in ("0.1", "9007199254740993", "1.0", "0"):
            draft = _collect_one(context, sent)
            round_tripped = json.loads(json.dumps(draft.payload))["value"]
            assert round_tripped == draft.payload["value"]
            assert Decimal(round_tripped) == Decimal(sent)

    def test_canonical_number_is_plain_exact_and_type_preserving(self) -> None:
        assert canonical_number(Decimal("1")) == "1"
        assert canonical_number(Decimal("1.0")) == "1.0"
        assert canonical_number(Decimal("1E+3")) == "1000"
        assert canonical_number(Decimal("1e-7")) == "0.0000001"
        assert canonical_number(Decimal("-0.50")) == "-0.50"


class TestPrecisionSurvivesNormalization:
    """§7. The whole trip: fake HTTP -> collector -> RawRecord -> normalization."""

    @pytest.mark.parametrize(("label", "sent", "expected"), CASES)
    def test_the_normalizer_reads_back_what_the_source_sent(
        self, context, label: str, sent: str, expected: str
    ) -> None:
        from .normalization_fixtures import NORMALIZED_AT, make_normalizer, raw_view

        draft = _collect_one(context, sent)
        # The raw payload as the normalizer will see it, i.e. through the same
        # JSON text parse the repository performs.
        as_stored = json.loads(json.dumps(draft.payload), parse_float=Decimal)
        record = replace(
            raw_view(collector_version="1.1.0"),
            payload=as_stored,
            observation_key=draft.observation_key,
        )
        normalized = make_normalizer().normalize(
            record, correlation_id="c", normalized_at=NORMALIZED_AT
        )
        observation = normalized.payload["observation"]
        assert Decimal(str(observation["value"])) == Decimal(sent), label

    def test_a_population_integer_is_semantically_unchanged_from_1_0_0(self, context) -> None:
        """§7's second half, and a property worth having deliberately.

        A 1.0.0 record stored `67158348.0` and a 1.1.0 record stores
        `67158348`. They must NORMALIZE to the same canonical value, or the
        collector bump would look like a data change to everything downstream.
        """
        from sros_acquisition.normalization import canonical_decimal_text

        old_shape = canonical_decimal_text(decimal_from(Decimal("67158348.0")))
        new_shape = canonical_decimal_text(decimal_from("67158348"))
        assert old_shape == new_shape == "67158348"

    def test_the_repository_view_parses_the_payload_without_float(self) -> None:
        """`_view` is where a stored payload becomes Python again.

        It must use `parse_float=Decimal`, or every value would be re-damaged on
        the way out no matter how carefully it was written.
        """
        row = (
            "11111111-1111-4111-8111-111111111111",
            WORKSPACE_P,
            None,
            "world-bank",
            "k",
            "0" * 64,
            "PUBLIC_API",
            json.dumps({"value": "0.1", "extra": 0.1}),
            "{}",
            2,
            "world-bank-indicators",
            "1.1.0",
            "corr",
            None,
            None,
            None,
        )
        view = _view(row)
        assert view.payload["value"] == "0.1"
        # The neighbouring JSON number came back as a Decimal, not a float.
        assert isinstance(view.payload["extra"], Decimal)
