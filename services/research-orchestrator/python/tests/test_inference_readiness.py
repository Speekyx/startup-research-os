"""Mission 1.24 §0.A — readiness is ten gates, not one environment variable.

The failure this pins is a specific and tempting one. Mission 1.23 proved the
governance gate refused with `PROVIDER_NOT_CONFIGURED`, derived from whether
`ANTHROPIC_API_KEY` was set. A reader could conclude that supplying the key makes
the system ready. It does not: Mission 1.22 found **every inference tier bound to
`null`**, and a key with an unbound tier routes nowhere.

So the tests below are mostly about **the gates that pass while the system still
cannot make a call**, because those are the ones a shallow check misses.
"""

from __future__ import annotations

import pathlib
from contextlib import contextmanager
from typing import Any

import pytest
from sros_contracts import LlmTier
from sros_orchestrator.inference_readiness import (
    APPROVED_PROVIDER,
    CREDENTIAL_ENV,
    SEMANTIC_EQUIVALENCE_TIER,
    evaluate_inference_readiness,
)

GOVERNANCE_OK = ("PERMITTED_WITH_CONDITIONS", "PERMITTED_TO_APPROVED_PROVIDERS")

CONFIGURED_ENV = {
    "LLM_TIER_STRONG_PROVIDER": "anthropic",
    "LLM_TIER_STRONG_MODEL": "a-model-identifier",
    CREDENTIAL_ENV: "not-a-real-key",
}


class _FakeRow(list):  # noqa: FURB189 - a row is a sequence; list is the shape psycopg returns
    pass


class _FakeCursor:
    def __init__(self, review: Any, profile: Any) -> None:
        self._review = review
        self._profile = profile

    def execute(self, sql: str, params: Any = None) -> _FakeCursor:
        self._result = self._review if "source_policy_reviews" in sql else self._profile
        return self

    def fetchone(self) -> Any:
        return self._result


class FakeDatabase:
    """A registry whose answers are given, so the gate logic is tested and the
    database is not. Governance state is a fixture here; the live values are
    asserted against the real database by the acquisition suite."""

    def __init__(
        self,
        *,
        model_processing: str | None = "PERMITTED_WITH_CONDITIONS",
        transmission: str | None = "PERMITTED_WITH_CONDITIONS",
        egress: str | None = "PERMITTED_TO_APPROVED_PROVIDERS",
        review_exists: bool = True,
    ) -> None:
        self._review = _FakeRow([2, "APPROVED_WITH_CONDITIONS", model_processing, transmission])
        if not review_exists:
            self._review = None  # type: ignore[assignment]
        self._profile = _FakeRow([egress])

    @contextmanager
    def connection(self) -> Any:
        yield _FakeCursor(self._review, self._profile)


def gates(result: Any) -> dict[str, bool]:
    return {g.name: g.passed for g in result.gates}


# The real provider policy, by absolute path. A relative default would resolve
# against whatever directory pytest was invoked from, and these tests must read
# the same reviewed file the runtime does rather than a fixture of it: the
# posture is a governance fact, and a test that stubbed it would assert the stub.
POLICY = (
    pathlib.Path(__file__).resolve().parents[4] / "docs" / "data" / "model-provider-policy-v1.json"
)


def evaluate(db: FakeDatabase, env: dict[str, str]) -> Any:
    return evaluate_inference_readiness(
        db, "stack-exchange", "local-private-research-v1", env, policy_path=POLICY
    )


class TestTheTierIsNotAnImplementationDetail:
    def test_the_component_requests_a_tier_and_never_a_provider(self) -> None:
        """ADR-006's whole indirection. A component naming a provider would make
        provider selection a code change and put routing outside configuration."""
        assert isinstance(SEMANTIC_EQUIVALENCE_TIER, LlmTier)

    def test_the_tier_is_strong_because_the_task_is_hard_judgement(self) -> None:
        """ADR-006 defines STRONG_MODEL as *complex synthesis, planning, hard
        judgment*, and says never to downgrade a tier silently.

        Semantic problem equivalence is that by construction: its canonical hard
        negatives are three questions sharing 182 characters of exact runc
        diagnostic that diverge into three unrelated failures, and the V1
        criterion prioritises avoiding a false SAME. This assertion exists so
        that moving to a cheaper tier is a visible decision rather than a quiet
        edit.
        """
        assert SEMANTIC_EQUIVALENCE_TIER is LlmTier.STRONG_MODEL

    def test_the_embedding_tier_is_not_the_one_requested(self) -> None:
        """The only tier this deployment has ever bound is EMBEDDING, and
        embeddings are forbidden. Reaching for the configured tier because it is
        the configured one is exactly the mistake worth failing on."""
        assert SEMANTIC_EQUIVALENCE_TIER is not LlmTier.EMBEDDING_MODEL


class TestACredentialAloneIsNotReadiness:
    def test_the_key_alone_leaves_the_system_unable_to_call(self) -> None:
        """**The load-bearing test.** Governance fully permits, the credential is
        present, and the deployment still cannot make a call because the tier is
        bound to `null` -- which is precisely the state Mission 1.22 found."""
        result = evaluate(
            FakeDatabase(),
            {"LLM_TIER_STRONG_PROVIDER": "null", CREDENTIAL_ENV: "not-a-real-key"},
        )
        assert not result.ready
        by_name = gates(result)
        assert by_name["provider-credential-present"] is True
        assert by_name["source-external-model-transmission-permitted"] is True
        assert by_name["gateway-tier-bound"] is False
        assert by_name["gateway-tier-model-named"] is False

    def test_an_unset_provider_and_the_string_null_are_both_unconfigured(self) -> None:
        """`config.py` treats the literal `null` as unconfigured and the shipped
        .env.example ships it. A readiness check that disagreed with the loader
        about the word would pass a deployment the loader refuses."""
        for value in ("null", "", None):
            env = dict(CONFIGURED_ENV)
            if value is None:
                env.pop("LLM_TIER_STRONG_PROVIDER")
            else:
                env["LLM_TIER_STRONG_PROVIDER"] = value
            assert not gates(evaluate(FakeDatabase(), env))["gateway-tier-bound"], value

    def test_a_tier_bound_to_another_provider_fails_the_policy_gate(self) -> None:
        """Configured is not approved. Binding the tier to a provider whose
        posture was reviewed and refused would route around Mission 1.23's
        policy using a variable."""
        env = dict(CONFIGURED_ENV) | {"LLM_TIER_STRONG_PROVIDER": "gemini"}
        by_name = gates(evaluate(FakeDatabase(), env))
        assert by_name["gateway-tier-bound"] is True
        assert by_name["gateway-tier-provider-approved"] is False

    def test_a_provider_without_a_model_routes_nowhere(self) -> None:
        env = dict(CONFIGURED_ENV) | {"LLM_TIER_STRONG_MODEL": ""}
        result = evaluate(FakeDatabase(), env)
        assert not result.ready
        assert gates(result)["gateway-tier-model-named"] is False


class TestGovernanceIsReadFromTheDatabaseAndFailsClosed:
    @pytest.mark.parametrize(
        ("kwargs", "gate"),
        [
            ({"model_processing": None}, "source-model-processing-permitted"),
            ({"transmission": None}, "source-external-model-transmission-permitted"),
            ({"transmission": "NOT_PERMITTED"}, "source-external-model-transmission-permitted"),
            ({"egress": None}, "profile-external-model-egress-permitted"),
            ({"egress": "DENIED"}, "profile-external-model-egress-permitted"),
            ({"egress": "NOT_ASSESSED"}, "profile-external-model-egress-permitted"),
        ],
    )
    def test_each_governance_absence_or_refusal_blocks(self, kwargs: dict, gate: str) -> None:
        """A NULL column reads NOT_ASSESSED and refuses, exactly as ADR-033
        specifies. `None` and an explicit refusal both block, and the point of
        keeping them distinct is what they say, not what they permit."""
        result = evaluate(FakeDatabase(**kwargs), dict(CONFIGURED_ENV))
        assert not result.ready
        assert gates(result)[gate] is False

    def test_a_missing_review_blocks_rather_than_defaulting(self) -> None:
        """ADR-027: approval never transfers between profiles, so no review means
        no permission -- never a fallback to another profile's answer."""
        result = evaluate(FakeDatabase(review_exists=False), dict(CONFIGURED_ENV))
        assert not result.ready
        by_name = gates(result)
        assert by_name["source-model-processing-permitted"] is False
        assert by_name["source-external-model-transmission-permitted"] is False

    def test_reading_may_be_permitted_while_transmission_is_not(self) -> None:
        """The distinction ADR-033 exists for, asserted as a gate rather than as
        prose. This is the exact state Stack Exchange was in before Mission 1.23."""
        result = evaluate(
            FakeDatabase(model_processing="PERMITTED_WITH_CONDITIONS", transmission=None),
            dict(CONFIGURED_ENV),
        )
        by_name = gates(result)
        assert by_name["source-model-processing-permitted"] is True
        assert by_name["source-external-model-transmission-permitted"] is False


class TestTheReportIsUsableByAnOperator:
    def test_every_gate_is_evaluated_even_after_one_fails(self) -> None:
        """The rule `authorize_external_inference` follows. An operator shown one
        failure fixes it and is refused again, once per remaining gate.

        Ten gates: four configuration, one adapter-capability, three
        governance and two provider-policy. With nothing configured and two
        governance answers missing, seven fail at once and three still pass --
        which is the report an operator can actually act on, rather than the
        first failure and silence about the rest."""
        result = evaluate(FakeDatabase(transmission=None, egress=None), {})
        assert len(result.gates) == 10
        assert len(result.failed) == 7
        assert [g.name for g in result.gates if g.passed] == [
            "source-model-processing-permitted",
            "provider-policy-approved",
            "adapter-is-on-the-assessed-route",
        ]

    def test_only_non_secret_actions_are_ever_suggested(self) -> None:
        """A readiness tool that told an operator where to put a key is a tool
        that will eventually be followed literally into a tracked file. The
        credential action names the variable and says the environment; it never
        names a file, and no action contains a value."""
        result = evaluate(FakeDatabase(), {})
        actions = " ".join(result.operator_actions)
        assert "LLM_TIER_STRONG_PROVIDER=anthropic" in actions
        assert CREDENTIAL_ENV in actions
        for forbidden in (".env", "compose", "commit", "paste", "file"):
            assert forbidden not in actions.lower(), forbidden

    def test_the_credential_value_never_appears_anywhere_in_the_report(self) -> None:
        """Presence is read; the value is not. Asserted over the whole serialised
        report rather than over the one field that was supposed to hold it."""
        secret = "sk-ant-this-would-be-a-real-key"
        result = evaluate(FakeDatabase(), dict(CONFIGURED_ENV) | {CREDENTIAL_ENV: secret})
        assert secret not in str(result.to_json())
        assert result.ready

    def test_a_passing_gate_suggests_nothing(self) -> None:
        result = evaluate(FakeDatabase(), dict(CONFIGURED_ENV))
        assert result.ready
        assert result.operator_actions == ()

    def test_readiness_is_the_conjunction_and_nothing_else(self) -> None:
        assert evaluate(FakeDatabase(), dict(CONFIGURED_ENV)).ready
        assert not evaluate(FakeDatabase(), dict(CONFIGURED_ENV) | {CREDENTIAL_ENV: ""}).ready

    def test_the_approved_provider_is_named_once(self) -> None:
        """Named here so a mismatch can be reported, and nowhere in the
        classifier: the component asks for a tier."""
        assert APPROVED_PROVIDER == "anthropic"
