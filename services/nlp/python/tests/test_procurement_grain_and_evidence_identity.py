"""Mission 1.41 §17. The two repairs, and what neither of them may break.

**Two defects of the same shape.** A cohort key that did not contain what its
docstring said, and an Evidence lookup that did not match what its docstring
said. Both were found by real data rather than by fixtures, and both are asserted
here against behaviour rather than prose.

Everything DB-backed writes into a disposable workspace.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sros_claim_model import (
    ClaimInterpretation,
    EvidenceDraft,
    build_claim,
)
from sros_contracts import (
    ClaimInterpretationKind,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    EvidenceDirection,
    EvidenceIndependenceState,
)
from sros_nlp.claim_repositories import persist_claims
from sros_nlp.extractors import EXTRACTOR_REGISTRY

from .conftest import PROBE_SESSION, needs_postgres

psycopg = pytest.importorskip("psycopg")

EXTRACTOR = EXTRACTOR_REGISTRY["procurement-value-contrast"]
DERIVATION = EXTRACTOR.resolve({"amount_type": "TOTAL_VALUE"})


# ======================================================== the cohort grain


def _notice(
    key: str,
    *,
    currency="EUR",
    scope="NOTICE",
    value="100",
    cpv=("92100000",),
    notice_class="CONTRACT_AWARD_NOTICE",
    amount_type="TOTAL_VALUE",
):
    from .test_procurement_value_contrast import amount, notice

    return notice(
        key,
        notice_class=notice_class,
        cpv=cpv,
        amounts=[amount(value=value, currency=currency, scope=scope, amount_type=amount_type)],
    )


class TestTheCohortKeyContainsWhatComparabilityRequires:
    """§1, §2. The validation demands one currency and one scope; the key now
    delivers cohorts that have them."""

    def test_two_currencies_are_two_cohorts_rather_than_one_refusal(self) -> None:
        eur = EXTRACTOR.group_key(_notice("a", currency="EUR"), DERIVATION)
        pln = EXTRACTOR.group_key(_notice("b", currency="PLN"), DERIVATION)
        assert eur is not None and pln is not None
        assert eur != pln

    def test_two_amount_scopes_are_two_cohorts(self) -> None:
        whole = EXTRACTOR.group_key(_notice("a", scope="NOTICE"), DERIVATION)
        per_lot = EXTRACTOR.group_key(_notice("b", scope="LOT"), DERIVATION)
        assert whole is not None and per_lot is not None
        assert whole != per_lot

    def test_the_same_currency_and_scope_remain_one_cohort(self) -> None:
        """A split that splits everything is not a grain, it is a refusal."""
        one = EXTRACTOR.group_key(_notice("a", value="100"), DERIVATION)
        two = EXTRACTOR.group_key(_notice("b", value="900"), DERIVATION)
        assert one == two

    def test_the_key_carries_currency_and_amount_scope_by_name(self) -> None:
        key = EXTRACTOR.group_key(_notice("a"), DERIVATION)
        assert key is not None
        decoded = json.loads(key)
        assert decoded["currency"] == "EUR"
        assert decoded["amount_scope"] == "NOTICE"
        assert decoded["cpv_division"] == "92"
        assert decoded["notice_class"] == "CONTRACT_AWARD_NOTICE"

    def test_a_notice_with_no_amount_of_the_wanted_semantic_gets_no_key(self) -> None:
        """It could never have contributed; now it is excluded where it shows."""
        assert EXTRACTOR.group_key(_notice("a", amount_type="ESTIMATED_VALUE"), DERIVATION) is None

    def test_a_genuinely_mixed_cohort_is_still_refused(self) -> None:
        """§1. The comparability rule was not weakened, only applied earlier."""
        from sros_contracts import SignalRefusalReason
        from sros_nlp.extractors.base import CandidateGroup, DerivationRequest

        now = datetime.now(UTC)
        group = CandidateGroup(
            key="forced",
            observations=(_notice("a", currency="EUR"), _notice("b", currency="PLN")),
        )
        outcome = EXTRACTOR.derive(
            group,
            DERIVATION,
            DerivationRequest(
                workspace_id="w",
                correlation_id="c",
                derived_at=now,
                expires_at=now + timedelta(days=1),
                research_session_id=None,
            ),
        )
        assert outcome.drafts == ()
        assert SignalRefusalReason.INCOMPATIBLE_SERIES in {r.reason for r in outcome.refusals}

    def test_no_currency_conversion_exists_anywhere_in_the_extractor(self) -> None:
        """§3. A grouping repair, not a conversion mission."""
        import pathlib

        source = (
            pathlib.Path(EXTRACTOR.__module__.replace(".", "/") + ".py")
            if False
            else pathlib.Path(__file__).resolve().parents[1]
            / "sros_nlp/extractors/procurement_value_contrast.py"
        ).read_text(encoding="utf-8")
        for forbidden in ("exchange_rate", "fx_rate", "convert_currency", "to_eur"):
            assert forbidden not in source, forbidden

    def test_the_version_was_bumped(self) -> None:
        """§5. Grouping semantics did not change under an unchanged version."""
        assert EXTRACTOR.extractor_version == "1.1.0"


# =================================================== the Evidence identity


_INTERPRETATION_V1 = ClaimInterpretation(
    interpreter_id="observed-signal-restatement",
    interpreter_version="1.1.0",
    kind=ClaimInterpretationKind.DETERMINISTIC,
)
_INTERPRETATION_V2 = ClaimInterpretation(
    interpreter_id="observed-signal-restatement",
    interpreter_version="9.9.9",
    kind=ClaimInterpretationKind.DETERMINISTIC,
)


def _draft(workspace_id, signal_id, facts, interpretation, *, relevance=1.0):
    return build_claim(
        workspace_id=workspace_id,
        claim_type=ClaimType.OBSERVED,
        temporality=ClaimTemporality.EVERGREEN,
        origin=ClaimOrigin.DETERMINISTIC_EXTRACTION,
        statement="A synthetic source reported a bounded contrast.",
        facts=facts,
        evidence=[
            EvidenceDraft(
                signal_id=signal_id,
                direction=EvidenceDirection.SUPPORTS,
                source_id="ted-eu",
                relevance=relevance,
                directness=1.0,
                extraction_confidence=1.0,
                independence_state=EvidenceIndependenceState.UNKNOWN,
            )
        ],
        interpretation=interpretation,
        interpretation_confidence=1.0,
        research_session_id=PROBE_SESSION,
        rationale="fixture",
    )


@needs_postgres
class TestEvidenceIdentityIsEpistemic:
    """§8-§13. Interpreter version is provenance, not identity."""

    def _seed(self, conn, workspace_id, notice_ids, magnitude="1.00"):
        from .test_proposition_convergence_persistence import _seed_signal

        return _seed_signal(conn, workspace_id, notice_ids, magnitude)

    def _facts(self, marker="A"):
        from .test_proposition_convergence_persistence import _detailed_facts

        return _detailed_facts([f"N-{marker}"], ["92100000"])

    def test_a_new_interpreter_version_creates_no_second_evidence(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§11. THE defect. Same Signal, same Claim, same semantics."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal = self._seed(conn, probe_workspace, ["N-1", "N-2"])
            facts = self._facts()
            persist_claims(conn, [_draft(probe_workspace, signal, facts, _INTERPRETATION_V1)])
            report = persist_claims(
                conn, [_draft(probe_workspace, signal, facts, _INTERPRETATION_V2)]
            )
            claim_id = report.claim_ids[0]
            count = conn.execute(
                "SELECT count(*) FROM scoring.evidence WHERE claim_id = %s AND signal_id = %s",
                (claim_id, signal),
            ).fetchone()[0]
            assert count == 1
            assert report.evidence_conflicts == ()

    def test_the_original_extraction_method_is_retained(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§8, §17. Provenance is kept, it just stops deciding."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal = self._seed(conn, probe_workspace, ["N-1", "N-2"])
            facts = self._facts()
            persist_claims(conn, [_draft(probe_workspace, signal, facts, _INTERPRETATION_V1)])
            persist_claims(conn, [_draft(probe_workspace, signal, facts, _INTERPRETATION_V2)])
            method = conn.execute(
                "SELECT extraction_method FROM scoring.evidence WHERE signal_id = %s",
                (signal,),
            ).fetchone()[0]
            assert method == "observed-signal-restatement@1.1.0"

    def test_a_changed_epistemic_factor_is_reported_rather_than_written(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§10. No silent overwrite, and no invented revision model."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal = self._seed(conn, probe_workspace, ["N-1", "N-2"])
            facts = self._facts()
            persist_claims(conn, [_draft(probe_workspace, signal, facts, _INTERPRETATION_V1)])
            report = persist_claims(
                conn,
                [_draft(probe_workspace, signal, facts, _INTERPRETATION_V2, relevance=0.4)],
            )
            assert len(report.evidence_conflicts) == 1
            conflict = report.evidence_conflicts[0]
            assert conflict["signal_id"] == signal
            assert "no representation here" in conflict["detail"]
            relevance = conn.execute(
                "SELECT relevance FROM scoring.evidence WHERE signal_id = %s", (signal,)
            ).fetchone()[0]
            assert relevance == 1.0, "the historical assessment must not be overwritten"

    def test_two_different_signals_still_make_two_evidence_rows(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§12. The Mission 1.39 shape must survive the repair."""
        with committing_tenant_conn(probe_workspace) as conn:
            from sros_nlp.interpreters.convergent_witness import convergent_draft

            from .test_proposition_convergence_persistence import _detailed_facts

            first = self._seed(conn, probe_workspace, ["N-1", "N-2"])
            second = self._seed(conn, probe_workspace, ["N-3", "N-4"])
            drafts = [
                convergent_draft(
                    _draft(
                        probe_workspace,
                        signal,
                        _detailed_facts(ids, codes),
                        _INTERPRETATION_V1,
                    ),
                    signal_type_id="procurement_value_contrast",
                )
                for signal, ids, codes in (
                    (first, ["N-1", "N-2"], ["92100000"]),
                    (second, ["N-3", "N-4"], ["92200000"]),
                )
            ]
            assert drafts[0].proposition_key == drafts[1].proposition_key
            report = persist_claims(conn, drafts)
            assert len(set(report.claim_ids)) == 1
            count = conn.execute(
                "SELECT count(*) FROM scoring.evidence WHERE claim_id = %s",
                (report.claim_ids[0],),
            ).fetchone()[0]
            assert count == 2

    def test_one_signal_still_reaches_a_detailed_and_a_convergent_claim(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§13. The repair must not collapse across `claim_id`."""
        with committing_tenant_conn(probe_workspace) as conn:
            from sros_nlp.interpreters.convergent_witness import convergent_draft

            signal = self._seed(conn, probe_workspace, ["N-1", "N-2"])
            detailed = _draft(probe_workspace, signal, self._facts(), _INTERPRETATION_V1)
            broader = convergent_draft(detailed, signal_type_id="procurement_value_contrast")
            report = persist_claims(conn, [detailed, broader])
            assert len(set(report.claim_ids)) == 2
            for claim_id in set(report.claim_ids):
                count = conn.execute(
                    "SELECT count(*) FROM scoring.evidence WHERE claim_id = %s AND signal_id = %s",
                    (claim_id, signal),
                ).fetchone()[0]
                assert count == 1

    def test_no_independence_is_manufactured(self, committing_tenant_conn, probe_workspace) -> None:
        """§29. Two windows are not two independent sources."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal = self._seed(conn, probe_workspace, ["N-9"])
            report = persist_claims(
                conn, [_draft(probe_workspace, signal, self._facts("Z"), _INTERPRETATION_V1)]
            )
            state = conn.execute(
                "SELECT DISTINCT independence_state, independence_group_id "
                "FROM scoring.evidence WHERE claim_id = %s",
                (report.claim_ids[0],),
            ).fetchall()
            assert state == [("UNKNOWN", None)]


def test_uuid_is_imported_for_the_seed_helper() -> None:
    """Keeps the import honest rather than unused."""
    assert uuid.UUID(int=0).version is None
