"""Mission 1.39 §23, §24. Two witnesses, one Claim, through the real persistence path.

**Every row here is SYNTHETIC and every write goes into a disposable workspace.**
No byte came from TED, no live research row is created, and the reliability
values fed to the aggregator are fixtures with no relation to the two reviewed
assessments (§26, §29). Their purpose is to prove CARDINALITY and MECHANICS, and
nothing about them is calibration data.

The proof this file exists for, in one line: `max(members)` finally receives more
than one member. Mission 1.37 measured that it never had.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sros_claim_model import (
    ClaimDraft,
    ClaimInterpretation,
    EvidenceDraft,
    build_claim,
    contract_for,
    convergent_proposition_key,
    distinct_witnesses,
    overlap_between,
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
from sros_nlp.interpreters.convergent_witness import convergent_draft

from .conftest import PROBE_SESSION, needs_postgres

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres

KIND = "source_published_classification_value_contrast_witnessed"
DETAILED_KIND = "source_reported_procurement_value_contrast"
SIGNAL_TYPE = "procurement_value_contrast"

_DETAILED_INTERPRETATION = ClaimInterpretation(
    interpreter_id="observed-signal-restatement",
    interpreter_version="1.1.0",
    kind=ClaimInterpretationKind.DETERMINISTIC,
)


def _seed_signal(conn, workspace_id: str, notice_ids: list[str], magnitude: str) -> str:
    """One synthetic procurement-contrast Signal. No byte came from TED."""
    signal_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    conn.execute(
        """INSERT INTO nlp.signals (
               id, workspace_id, quantity_family, signal_type_id, extraction_method,
               derived_at, expires_at, magnitude, magnitude_kind, magnitude_unit, magnitude_unit_state,
               direction, extractor_id, extractor_version, signal_schema_id,
               signal_schema_version, derivation_kind, parameters, parameter_fingerprint,
               derivation_fingerprint, scope, temporal_basis, temporal_window,
               correlation_id, research_session_id)
           VALUES (%s,%s,'TRANSACTION_VALUE',%s,'procurement-value-contrast@1.0.1',
                   %s,%s,%s,'ABSOLUTE_DIFFERENCE','EUR','INHERITED','NOT_APPLICABLE',
                   'procurement-value-contrast','1.0.1','sros.signal',1,'DETERMINISTIC',
                   %s,%s,%s,%s,'NONE',%s,'mission-1.39-fixture',%s)""",
        (
            signal_id,
            workspace_id,
            SIGNAL_TYPE,
            now,
            now + timedelta(days=365),
            magnitude,
            json.dumps({"fixture": True}),
            f"fp-{signal_id}",
            f"df-{signal_id}",
            json.dumps({"source_ids": ["ted-eu"], "notice_ids": notice_ids}),
            json.dumps({"basis": "NONE", "resolution": "DAY", "period_labels": []}),
            PROBE_SESSION,
        ),
    )
    return signal_id


def _detailed_facts(notice_ids: list[str], codes: list[str]) -> dict[str, object]:
    return {
        "proposition": DETAILED_KIND,
        "source_id": "ted-eu",
        "resource_id": "notices/eforms-contract-and-award",
        "notice_class": "CONTRACT_AWARD_NOTICE",
        "amount_type": "TOTAL_VALUE",
        "amount_scope": "NOTICE",
        "currency": "EUR",
        "classification_scheme": "CPV",
        "classification_division": "90",
        "classification_codes": codes,
        "notice_ids": notice_ids,
        "relation": "DIFFERS",
    }


def _detailed_draft(workspace_id: str, signal_id: str, facts: dict[str, object]) -> ClaimDraft:
    return build_claim(
        workspace_id=workspace_id,
        claim_type=ClaimType.OBSERVED,
        temporality=ClaimTemporality.EVERGREEN,
        origin=ClaimOrigin.DETERMINISTIC_EXTRACTION,
        statement=(
            f"A synthetic source reported that, within a bounded set of "
            f"{len(facts['notice_ids'])} notices, the largest amount exceeded the smallest."
        ),
        facts=facts,
        evidence=[
            EvidenceDraft(
                signal_id=signal_id,
                direction=EvidenceDirection.SUPPORTS,
                source_id="ted-eu",
                relevance=1.0,
                directness=1.0,
                extraction_confidence=1.0,
                independence_state=EvidenceIndependenceState.UNKNOWN,
            )
        ],
        interpretation=_DETAILED_INTERPRETATION,
        interpretation_confidence=1.0,
        research_session_id=PROBE_SESSION,
        rationale="fixture",
    )


def _two_witnesses(conn, workspace_id: str) -> tuple[ClaimDraft, ClaimDraft]:
    signal_a = _seed_signal(conn, workspace_id, ["N-1", "N-2", "N-3"], "686545.02")
    signal_b = _seed_signal(conn, workspace_id, ["N-4", "N-5"], "12000.00")
    facts_a = _detailed_facts(["N-1", "N-2", "N-3"], ["90500000", "90510000"])
    facts_b = _detailed_facts(["N-4", "N-5"], ["90900000"])
    return (
        convergent_draft(
            _detailed_draft(workspace_id, signal_a, facts_a), signal_type_id=SIGNAL_TYPE
        ),
        convergent_draft(
            _detailed_draft(workspace_id, signal_b, facts_b), signal_type_id=SIGNAL_TYPE
        ),
    )


class TestTwoWitnessesReachOneClaim:
    def test_one_claim_two_evidence_one_revision(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§23. The whole mission, in one assertion set."""
        with committing_tenant_conn(probe_workspace) as conn:
            draft_a, draft_b = _two_witnesses(conn, probe_workspace)
            assert draft_a.proposition_key == draft_b.proposition_key

            report = persist_claims(conn, [draft_a, draft_b])
            assert len(set(report.claim_ids)) == 1
            claim_id = report.claim_ids[0]

            rows = conn.execute(
                "SELECT id, signal_id FROM scoring.evidence WHERE claim_id = %s ORDER BY id",
                (claim_id,),
            ).fetchall()
            assert len(rows) == 2, "two witnesses must produce two Evidence rows"
            assert len({r[1] for r in rows}) == 2, "and they must cite different Signals"
            assert len({str(r[0]) for r in rows}) == 2

            revisions = conn.execute(
                "SELECT count(*) FROM research.claim_revisions WHERE claim_id = %s", (claim_id,)
            ).fetchone()[0]
            # §22: a revision is a changed assertion, not additional support.
            assert revisions == 1

    def test_replaying_one_signal_adds_nothing(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§20. Idempotent: the Claims are what is idempotent, not the delivery."""
        with committing_tenant_conn(probe_workspace) as conn:
            draft_a, _ = _two_witnesses(conn, probe_workspace)
            persist_claims(conn, [draft_a])
            before = conn.execute(
                "SELECT count(*) FROM scoring.evidence WHERE claim_id IN "
                "(SELECT id FROM research.claims WHERE proposition_key = %s)",
                (draft_a.proposition_key,),
            ).fetchone()[0]

            persist_claims(conn, [draft_a])
            after = conn.execute(
                "SELECT count(*) FROM scoring.evidence WHERE claim_id IN "
                "(SELECT id FROM research.claims WHERE proposition_key = %s)",
                (draft_a.proposition_key,),
            ).fetchone()[0]
            assert before == after == 1

    def test_the_detailed_claim_stays_a_different_claim(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§17. The broader proposition does not replace or mutate the detailed one."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal = _seed_signal(conn, probe_workspace, ["N-1", "N-2"], "5.00")
            facts = _detailed_facts(["N-1", "N-2"], ["90500000"])
            detailed = _detailed_draft(probe_workspace, signal, facts)
            broader = convergent_draft(detailed, signal_type_id=SIGNAL_TYPE)

            assert detailed.proposition_key != broader.proposition_key
            report = persist_claims(conn, [detailed, broader])
            assert len(set(report.claim_ids)) == 2

    def test_witness_identity_survives_in_the_signal_scope(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§3, §10. A witness fact is not discarded because it left the key."""
        with committing_tenant_conn(probe_workspace) as conn:
            draft_a, draft_b = _two_witnesses(conn, probe_workspace)
            persist_claims(conn, [draft_a, draft_b])
            scopes = conn.execute(
                """SELECT s.scope FROM scoring.evidence e
                     JOIN nlp.signals s ON s.id = e.signal_id
                    WHERE e.claim_id = (SELECT id FROM research.claims
                                         WHERE proposition_key = %s)""",
                (draft_a.proposition_key,),
            ).fetchall()
            recovered = [row[0]["notice_ids"] for row in scopes]
            assert sorted(map(tuple, recovered)) == [("N-1", "N-2", "N-3"), ("N-4", "N-5")]


class TestTheRealAggregatorReceivesTwoItems:
    """§24, §25. The mechanism, exercised and named."""

    def test_within_group_max_finally_sees_two_members(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        from sros_evidence_aggregation import (
            REFERENCE_PROFILE_V1,
            EvidenceItem,
            aggregate,
        )

        with committing_tenant_conn(probe_workspace) as conn:
            draft_a, draft_b = _two_witnesses(conn, probe_workspace)
            report = persist_claims(conn, [draft_a, draft_b])
            claim_id = report.claim_ids[0]
            rows = conn.execute(
                """SELECT id, direction, relevance, directness, extraction_confidence,
                          observation_category, independence_state, source_id
                     FROM scoring.evidence WHERE claim_id = %s ORDER BY id""",
                (claim_id,),
            ).fetchall()

        # FIXTURE reliabilities. Deliberately different so the within-group
        # maximum has something to choose between, and deliberately not 0.5 or
        # 0.65 so nobody can mistake them for the reviewed assessments (§26).
        fixtures = (0.4, 0.7)
        items = [
            EvidenceItem(
                evidence_id=str(row[0]),
                direction=EvidenceDirection(row[1]),
                relevance=row[2],
                directness=row[3],
                reliability=fixture,
                extraction_confidence=row[4],
                independence_state=EvidenceIndependenceState(row[6]),
                source_id=row[7],
            )
            for row, fixture in zip(rows, fixtures, strict=True)
        ]
        assert len(items) == 2

        result = aggregate(
            claim_id,
            items,
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality.EVERGREEN,
            allow_uncalibrated=True,
        )

        assert result.raw_evidence_count == 2
        assert result.scorable_evidence_count == 2

        # THE PROOF. Independence is UNKNOWN on both, so the conservative rule
        # collapses them into ONE group -- and that group has two members, which
        # is the first time `max(members)` has had a choice to make.
        assert result.support_group_count == 1
        group = result.groups.support[0]
        assert len(group.member_evidence_ids) == 2
        assert group.collapsed_member_count == 1
        assert group.strength == max(fixtures)

        # Saturation still receives ONE group. That is correct and must not be
        # dressed up as corroboration: two witnesses of unestablished provenance
        # raise observed volume, not evidence strength.
        assert result.masses.support_strength == max(fixtures)
        assert result.unknown_independence_count == 2
        assert not result.calibrated

    def test_independence_was_not_manufactured(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§12. Disjoint cohorts do not become independent Evidence."""
        with committing_tenant_conn(probe_workspace) as conn:
            draft_a, draft_b = _two_witnesses(conn, probe_workspace)
            report = persist_claims(conn, [draft_a, draft_b])
            states = conn.execute(
                "SELECT DISTINCT independence_state, independence_group_id "
                "FROM scoring.evidence WHERE claim_id = %s",
                (report.claim_ids[0],),
            ).fetchall()
            assert states == [("UNKNOWN", None)]

            groups = conn.execute(
                "SELECT count(*) FROM scoring.evidence_independence_groups WHERE claim_id = %s",
                (report.claim_ids[0],),
            ).fetchone()[0]
            assert groups == 0

    def test_disjoint_observation_overlap_is_not_independence(self) -> None:
        """The two axes, side by side, so the distinction is testable."""
        contract = contract_for(KIND)
        assert contract is not None
        left = {**_detailed_facts(["N-1"], ["90500000"]), "proposition": KIND}
        right = {**_detailed_facts(["N-2"], ["90900000"]), "proposition": KIND}
        assert convergent_proposition_key(contract, left) == convergent_proposition_key(
            contract, right
        )
        assert distinct_witnesses(contract, [left, right])
        assert overlap_between(contract, left, right, membership_field="notice_ids").value == (
            "DISJOINT"
        )
        # And it still says nothing about independence: the Evidence above is
        # UNKNOWN, and nothing in this mission promotes it.
