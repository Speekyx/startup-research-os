"""Live where live means something, persisted where only a person can answer.

Mission 1.15.6.2 §26, §27, §28, §30. **No external call, no database.** Every
case here is built from the real catalog and the real compliance configuration
plus hand-made verification records, so the resolver's rules are exercised
without depending on what any deployment happens to hold.

The property this file exists to protect has two halves that pull against each
other, and losing either one is a real failure:

**A machine verifier must never revoke a human decision.** `UNKNOWN` from a
verifier means *this cannot be checked*, and persisting it as a negative turned
a recorded acceptance into `satisfied = FALSE` in Mission 1.15.6.1 while the
operator had withdrawn nothing.

**A human decision must never make a machine condition sticky.** Persisting
judgement is not persisting everything. If a capability genuinely stops holding,
the authorization must fail even though the operator's acceptance is untouched.
"""

from __future__ import annotations

import pathlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sros_acquisition.compliance import (
    AcquisitionNotAuthorizedError,
    build_authorization,
    resolve_effective_verifications,
    satisfied_condition_keys,
    verify_source,
)
from sros_acquisition.compliance.config import load_compliance
from sros_acquisition.compliance.verification import (
    AWAITING_HUMAN_VERIFIER,
    ConditionVerificationRecord,
)
from sros_acquisition.registry import evaluate_eligibility
from sros_contracts import ConditionVerification, ConditionVerificationResult

from .conftest import LEGACY_PROFILE, LOCAL_PROFILE, REPO_ROOT, current_review_version

RESIDUAL = "ted-database-right-residual-exposure-accepted"
ROUTE_ONLY = "ted-official-route-only"
MINIMISATION = "ted-personal-data-minimisation"
ATTRIBUTION = "ted-attribution"

SEARCH_API = "ted-search-api"
OPEN_DATA = "ted-open-data-sparql"
BULK_XML = "ted-bulk-xml"

DOCS = REPO_ROOT / "docs" / "data"
CONTRACT = DOCS / "effective-condition-verification-v1.md"

MOMENT = datetime(2026, 8, 31, 20, 9, 29, tzinfo=UTC)


@pytest.fixture(scope="module")
def compliance():
    return load_compliance(DOCS / "source-compliance-v1.json")


@pytest.fixture
def ted(catalog):
    return next(s for s in catalog if s.source_id == "ted-eu")


def decision(
    *,
    condition_key: str = RESIDUAL,
    source_id: str = "ted-eu",
    review_version: int = current_review_version(),
    verifier: str = "local-operator",
    result: ConditionVerificationResult = ConditionVerificationResult.SATISFIED,
    verification: ConditionVerification = ConditionVerification.HUMAN_CONFIRMATION,
    verified_at: datetime = MOMENT,
) -> ConditionVerificationRecord:
    """One persisted decision, shaped like the row `read_human_decisions` returns."""
    return ConditionVerificationRecord(
        source_id=source_id,
        review_version=review_version,
        condition_key=condition_key,
        verification=verification,
        verifier=verifier,
        verifier_version="acknowledgement-v1",
        result=result,
        reason="a test fixture standing in for a recorded operator decision",
        reference="docs/data/ted-eu-operator-risk-acceptance-v1.md",
        verified_at=verified_at,
    )


def effective(ted, compliance, decisions=()):
    return resolve_effective_verifications(ted, LOCAL_PROFILE, compliance, decisions, {}, MOMENT)


def by_key(records):
    return {record.condition_key: record for record in records}


# ============================================== a human decision survives a pass


class TestPersistedHumanDecisionSurvives:
    def test_without_a_decision_the_human_condition_is_unknown(self, ted, compliance) -> None:
        """Fail-closed, and unchanged. No decision means the gate refuses."""
        record = by_key(effective(ted, compliance))[RESIDUAL]
        assert record.result is ConditionVerificationResult.UNKNOWN
        assert record.verifier == AWAITING_HUMAN_VERIFIER

    def test_with_a_decision_the_human_condition_is_satisfied(self, ted, compliance) -> None:
        record = by_key(effective(ted, compliance, (decision(),)))[RESIDUAL]
        assert record.result is ConditionVerificationResult.SATISFIED
        assert record.verifier == "local-operator"

    def test_live_unknown_never_overwrites_it(self, ted, compliance) -> None:
        """The defect, stated as the property. `verify_source` still answers
        UNKNOWN for this condition; the resolver must not consult it."""
        live = by_key(verify_source(ted, LOCAL_PROFILE, compliance, environ={}))
        assert live[RESIDUAL].result is ConditionVerificationResult.UNKNOWN

        resolved = by_key(effective(ted, compliance, (decision(),)))
        assert resolved[RESIDUAL].result is ConditionVerificationResult.SATISFIED

    def test_the_most_recent_decision_wins(self, ted, compliance) -> None:
        """History is append-only, so the current answer is the latest one."""
        older = decision(verified_at=MOMENT - timedelta(days=30), verifier="earlier-operator")
        resolved = by_key(effective(ted, compliance, (decision(), older)))
        assert resolved[RESIDUAL].verifier == "local-operator"

    def test_a_recorded_withdrawal_leaves_the_condition_unsatisfied(self, ted, compliance) -> None:
        """§11. A decision can be changed by another decision. A withdrawal is
        not SATISFIED, so it is not usable, so the condition falls back to the
        live verifier -- which answers UNKNOWN, which blocks."""
        withdrawn = decision(result=ConditionVerificationResult.UNSATISFIED)
        record = by_key(effective(ted, compliance, (withdrawn,)))[RESIDUAL]
        assert record.result is ConditionVerificationResult.UNKNOWN


# ===================================== what a supplied record may never do


class TestSuppliedRecordsCannotBecomeAWayIn:
    def test_the_placeholder_is_not_a_decision(self, ted, compliance) -> None:
        """The machine's own `human-confirmation` record, handed back in with
        SATISFIED forced on it. It must be ignored: the placeholder means *no
        verifier can decide this*, whatever result is attached to it."""
        forged = decision(verifier=AWAITING_HUMAN_VERIFIER)
        record = by_key(effective(ted, compliance, (forged,)))[RESIDUAL]
        assert record.result is ConditionVerificationResult.UNKNOWN

    def test_a_capability_record_cannot_be_injected(self, ted, compliance) -> None:
        """**The assertion that keeps `decisions` from being a bypass.** A
        caller supplying a SATISFIED CAPABILITY result for a machine condition
        must change nothing: machine conditions are always re-evaluated."""
        forged = decision(
            condition_key=ROUTE_ONLY,
            verification=ConditionVerification.CAPABILITY,
            verifier="capability:source-route-binding",
        )
        record = by_key(effective(ted, compliance, (forged,)))[ROUTE_ONLY]
        assert record.verifier == "capability:source-route-binding"
        # Satisfied because the capability genuinely passes, not because it was
        # supplied -- the next test proves the difference.
        assert record.result is ConditionVerificationResult.SATISFIED

    def test_an_injected_capability_cannot_rescue_a_failing_one(self, ted, compliance) -> None:
        """The same probe against a configuration where the capability FAILS.
        If supplied records could satisfy machine conditions, this would pass."""
        stripped = replace(compliance.get("ted-eu", LOCAL_PROFILE), route_authorization=None)
        broken = replace(compliance, sources=(stripped,))
        forged = decision(
            condition_key=ROUTE_ONLY,
            verification=ConditionVerification.CAPABILITY,
            verifier="capability:source-route-binding",
        )
        record = by_key(
            resolve_effective_verifications(
                ted, LOCAL_PROFILE, broken, (forged, decision()), {}, MOMENT
            )
        )[ROUTE_ONLY]
        assert record.result is ConditionVerificationResult.UNSATISFIED

    def test_a_decision_for_another_source_is_ignored(self, ted, compliance) -> None:
        record = by_key(effective(ted, compliance, (decision(source_id="world-bank"),)))[RESIDUAL]
        assert record.result is ConditionVerificationResult.UNKNOWN

    def test_a_decision_for_another_review_version_is_ignored(self, ted, compliance) -> None:
        """§7. An acceptance belongs to the review it was made about. A v1
        decision does not satisfy v2, and a v2 decision would not satisfy v3."""
        record = by_key(effective(ted, compliance, (decision(review_version=1),)))[RESIDUAL]
        assert record.result is ConditionVerificationResult.UNKNOWN

    def test_a_decision_for_an_unrequired_condition_is_ignored(self, ted, compliance) -> None:
        resolved = effective(ted, compliance, (decision(condition_key="invented-condition"),))
        assert "invented-condition" not in by_key(resolved)
        assert by_key(resolved)[RESIDUAL].result is ConditionVerificationResult.UNKNOWN

    def test_it_does_not_reach_the_commercial_profile(self, ted, compliance) -> None:
        """§26. The commercial review carries no condition an acceptance could
        clear, so the resolver returns its conditions -- none -- untouched."""
        resolved = resolve_effective_verifications(
            ted, LEGACY_PROFILE, compliance, (decision(),), {}, MOMENT
        )
        assert resolved == ()


# ============================================== machine conditions stay fresh


class TestMachineConditionsAreAlwaysLive:
    def test_all_three_capabilities_are_evaluated_now(self, ted, compliance) -> None:
        resolved = by_key(effective(ted, compliance, (decision(),)))
        for key in (ATTRIBUTION, ROUTE_ONLY, MINIMISATION):
            assert resolved[key].verifier.startswith("capability:"), key
            assert resolved[key].result is ConditionVerificationResult.SATISFIED, key

    @pytest.mark.parametrize(
        ("field", "condition"),
        [
            ("route_authorization", ROUTE_ONLY),
            ("data_minimisation", MINIMISATION),
            ("attribution", ATTRIBUTION),
        ],
    )
    def test_a_broken_capability_blocks_even_with_the_acceptance_recorded(
        self, ted, compliance, field: str, condition: str
    ) -> None:
        """§18, §27. **Human persistence must not make machine conditions
        sticky.** Each capability is broken in turn, the operator's acceptance
        is supplied intact, and the authorization must still refuse -- naming
        the capability rather than the acceptance.
        """
        entry = compliance.get("ted-eu", LOCAL_PROFILE)
        empty = {
            "route_authorization": None,
            "data_minimisation": replace(entry.data_minimisation, allowed=(), excluded=()),
            "attribution": replace(entry.attribution, requirements=entry.attribution.requirements),
        }[field]
        if field == "attribution":
            pytest.skip(
                "an attribution obligation cannot be emptied without failing its own "
                "model validation, which is the model refusing to describe a "
                "capability that checks nothing"
            )
        broken = replace(compliance, sources=(replace(entry, **{field: empty}),))

        resolved = resolve_effective_verifications(
            ted, LOCAL_PROFILE, broken, (decision(),), {}, MOMENT
        )
        assert by_key(resolved)[RESIDUAL].result is ConditionVerificationResult.SATISFIED
        assert by_key(resolved)[condition].result is not ConditionVerificationResult.SATISFIED

        result = evaluate_eligibility(
            ted, LOCAL_PROFILE, MOMENT, satisfied_condition_keys(resolved)
        )
        assert not result.eligible
        assert condition in " ".join(result.blocking_reasons)

        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LOCAL_PROFILE, broken, decisions=(decision(),), environ={})
        assert condition in " ".join(caught.value.reasons)

    def test_no_persisted_machine_state_is_ever_read(self, ted, compliance) -> None:
        """§14. The resolver's only persistence input is human decisions, and a
        source with none resolves exactly as `verify_source` does."""
        live = verify_source(ted, LOCAL_PROFILE, compliance, environ={}, now=MOMENT)
        resolved = effective(ted, compliance)
        assert [r.condition_key for r in resolved] == [r.condition_key for r in live]
        for machine in (ATTRIBUTION, ROUTE_ONLY, MINIMISATION):
            assert by_key(resolved)[machine].result is by_key(live)[machine].result


# ================================================ authorization, end to end


class TestEffectiveAuthorization:
    def test_it_builds_with_the_decision_supplied(self, ted, compliance) -> None:
        """§16, §28. Four of four, and no caller merged anything: the resolver
        did, inside `build_authorization`."""
        context = build_authorization(
            ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
        )
        assert satisfied_condition_keys(context.verifications) == {
            ATTRIBUTION,
            ROUTE_ONLY,
            MINIMISATION,
            RESIDUAL,
        }

    def test_it_refuses_without_one(self, ted, compliance) -> None:
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LOCAL_PROFILE, compliance, environ={}, now=MOMENT)
        assert caught.value.reasons == (f"review conditions not satisfied: {RESIDUAL}",)

    def test_the_context_still_carries_only_the_reviewed_routes(self, ted, compliance) -> None:
        """§19. Nothing about an effective verification set widens a route."""
        context = build_authorization(
            ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
        )
        assert set(context.authorized_route_labels) == {SEARCH_API, OPEN_DATA}
        assert BULK_XML not in context.authorized_route_labels
        assert context.route_authorization.preferred_label == SEARCH_API
        assert context.authorize_route(BULK_XML)

    def test_the_field_gate_is_unchanged(self, ted, compliance) -> None:
        context = build_authorization(
            ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
        )
        allowed = context.data_minimisation.allowed
        assert context.authorize_fields(allowed) == ()
        for prohibited in context.data_minimisation.excluded:
            assert context.authorize_fields((*allowed, prohibited)), prohibited
        assert context.authorize_fields(None)

    def test_the_resource_gate_is_unchanged(self, ted, compliance) -> None:
        """§19, amended by Mission 1.15.7 which authorised ONE concrete resource.

        The property this protects never was "zero datasets" -- it was that a
        satisfied human condition changes the SOURCE gate and reaches nothing
        below it. The excluded families are excluded for the same reason as
        before, with an authorised resource now sitting beside them.
        """
        context = build_authorization(
            ted, LOCAL_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
        )
        assert [d.resource_id for d in context.datasets] == ["notices/eforms-contract-and-award"]
        assert {
            "ted-bulk-xml-daily",
            "ted-bulk-xml-monthly",
            "ted-csv-historical",
        } <= context.resource_scope.excluded_dataset_families
        assert context.resource_scope.require_dataset_family

    def test_the_commercial_profile_still_refuses(self, ted, compliance) -> None:
        """§13 of Mission 1.15.6.1, re-asserted through the new path."""
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(
                ted, LEGACY_PROFILE, compliance, decisions=(decision(),), environ={}, now=MOMENT
            )
        assert "REQUIRES_REVIEW" in " ".join(caught.value.reasons)


# ==================================== sources with no human condition are untouched


class TestOtherSourcesBehaveExactlyAsBefore:
    @pytest.mark.parametrize("source_id", ["world-bank", "eurostat", "fred", "gdelt"])
    def test_the_resolver_matches_verify_source(self, catalog, compliance, source_id: str) -> None:
        """§21. Generic mechanism, no behaviour change for anything that has no
        human condition -- with or without decisions supplied."""
        source = next(s for s in catalog if s.source_id == source_id)
        live = verify_source(source, LEGACY_PROFILE, compliance, environ={}, now=MOMENT)
        resolved = resolve_effective_verifications(
            source, LEGACY_PROFILE, compliance, (decision(),), {}, MOMENT
        )
        assert [(r.condition_key, r.result) for r in resolved] == [
            (r.condition_key, r.result) for r in live
        ]

    def test_exactly_two_pairs_carry_a_human_condition(self, catalog) -> None:
        """Asserted rather than assumed, because the resolver's behaviour differs
        for these two and for nothing else. `openalex` is the one that is easy to
        forget: it has carried `openalex-spend-bounded` under the LEGACY profile
        since Mission 1.15, and it is the reason this mechanism had to be generic
        rather than written around TED."""
        carriers = {
            (source.source_id, profile)
            for source in catalog
            for profile, review in source.reviews_by_profile().items()
            for condition in review.required_conditions
            if condition.verification is ConditionVerification.HUMAN_CONFIRMATION
        }
        # Mission 1.17 added a local-profile review to openalex carrying the same
        # `openalex-spend-bounded` condition, so the count went from two to three.
        # The mechanism is unchanged and this is the evidence for it: a human
        # condition follows the (source, profile) pair it was written for, and
        # openalex now carries one under each of two profiles independently.
        assert carriers == {
            ("ted-eu", LOCAL_PROFILE),
            ("openalex", LEGACY_PROFILE),
            ("openalex", LOCAL_PROFILE),
        }, carriers

    def test_openalex_is_unaffected_by_teds_decision(self, catalog, compliance) -> None:
        """§21. The other human condition in the registry must not be satisfied
        by a decision recorded about a different source. Its own condition stays
        UNKNOWN, exactly as before this mission."""
        openalex = next(s for s in catalog if s.source_id == "openalex")
        resolved = by_key(
            resolve_effective_verifications(
                openalex, LEGACY_PROFILE, compliance, (decision(),), {}, MOMENT
            )
        )
        assert resolved["openalex-spend-bounded"].result is ConditionVerificationResult.UNKNOWN
        assert resolved["openalex-spend-bounded"].verifier == AWAITING_HUMAN_VERIFIER


# ================================================================ the contract


def test_the_contract_document_states_the_precedence() -> None:
    text = " ".join(CONTRACT.read_text(encoding="utf-8").split()).lower()
    text = text.replace("`", "").replace("**", "").replace("*", "")
    for claim in (
        # The precedence rule itself.
        "human_confirmation",
        "persisted",
        "live evaluation, every time",
        # The two properties that pull against each other, both stated.
        "a machine that cannot answer never counts as a no",
        "a machine condition is not a memory",
        # The boundary a reader must not have to infer.
        "the view alone does not prove runtime authorization",
        "a human decision is changed by another human decision, never by a machine",
    ):
        assert claim in text, claim


def test_no_test_in_this_file_reaches_the_network() -> None:
    import ast

    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "aiohttp", "socket"}
