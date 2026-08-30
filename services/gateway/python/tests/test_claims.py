"""Claim and Evidence persistence — the model A-13 was opened for.

Mission 1.2 §47. Two workspaces throughout, because a tenancy assertion with one
workspace has nothing to be isolated from (ADR-005).

Those two are P and Q, and they exist only while a test is running: the
`own_workspaces` fixture below creates them before each test and drops them
after. Nothing here writes into the seeded development workspaces.

The tests worth reading first are `TestCrossTenantIntegrity` and
`TestHistoricalReproducibility`. The first proves that a cross-workspace
reference is not merely forbidden but structurally impossible — the composite
foreign keys carry `workspace_id`, so the database refuses before any
application check runs. The second proves a revised claim does not silently
rewrite what an earlier aggregation evaluated, which is the whole reason
revisions are append-only.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from sros_contracts import (
    ClaimLifecycle,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    ContractError,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
    MarketScope,
    ObservationKind,
)
from sros_gateway.db.claims import (
    ClaimRepository,
    ClaimStatementUnchangedError,
    EvidenceRepository,
)
from sros_gateway.db.repositories import (
    NotFoundError,
    OpportunityRepository,
    ResearchProjectRepository,
    ResearchSessionRepository,
)

from .conftest import DATABASE_URL, WORKSPACE_P, WORKSPACE_Q, header, needs_postgres

NOW = datetime.now(UTC)
EXPIRES = NOW + timedelta(days=30)

D = EvidenceDirection
IND = EvidenceIndependenceState
CAT = EvidenceObservationCategory

CONTEXT = {"market_scope": {"type": "COUNTRY", "countries": ["FR"]}}


# ==================================================================== workspaces


@pytest.fixture(autouse=True)
def own_workspaces(probe_workspaces) -> None:
    """Every test in this module runs in workspaces of its own.

    Autouse, and it hands nothing back, because no test here needs to be handed
    a workspace: the helpers below already carry P and Q as defaults, so what a
    test needs is not a value but a guarantee -- that the two exist when it
    starts and are gone when it finishes. Requesting `probe_workspaces` by name
    in fifty signatures would state the same thing fifty times and leave the
    fifty-first test silently writing into a seeded workspace.

    Without it these tests committed into the seeded development workspace and
    left everything there. A full run of the suites accumulated 39 claims and 36
    evidence records that no test had asked for, which Mission 1.6 then hit from
    the other side: a normalization test asserting that no Claims existed found
    39 and had to be weakened to a delta to pass. The rows were never a
    normalization concern; they were this suite's litter.
    """


# ===================================================================== helpers


def make_opportunity(database, workspace=WORKSPACE_P, title="Test opportunity") -> uuid.UUID:
    """Explicit creation. Mission 1.2 §36: tests insert opportunities directly
    rather than exercising identity resolution, which remains open."""
    return OpportunityRepository(database).create(workspace, title, MarketScope.country("FR"))


def make_session(database, workspace=WORKSPACE_P) -> uuid.UUID:
    from sros_contracts import CONTRACT_VERSION, ONTOLOGY_VERSION, ResearchContext

    project = ResearchProjectRepository(database).create(workspace, "claim tests")
    return (
        ResearchSessionRepository(database)
        .create(
            workspace,
            project.id,
            ResearchContext.from_json(CONTEXT),
            CONTRACT_VERSION,
            ONTOLOGY_VERSION,
        )
        .id
    )


def make_claim(
    database,
    opportunity_id: uuid.UUID,
    workspace=WORKSPACE_P,
    statement: str = "A meaningful segment expresses willingness to pay.",
    temporality=ClaimTemporality.EVERGREEN,
    **kwargs,
) -> uuid.UUID:
    return ClaimRepository(database).create(
        workspace,
        opportunity_id,
        statement,
        ClaimType.INFERRED,
        temporality,
        ClaimOrigin.MANUAL,
        **kwargs,
    )


def add_evidence(database, claim_id, workspace=WORKSPACE_P, **kwargs) -> uuid.UUID:
    defaults = {
        "evidence_level": 1,
        "collected_at": NOW,
        "expires_at": EXPIRES,
        "relevance": 0.6,
        "directness": 0.6,
        "reliability": 0.6,
        "extraction_confidence": 0.6,
    }
    direction = kwargs.pop("direction", D.SUPPORTS)
    return EvidenceRepository(database).create(
        workspace, claim_id, direction, **{**defaults, **kwargs}
    )


# =================================================================== the claim


@needs_postgres
class TestClaimPersistence:
    def test_p_claim_is_created_with_its_first_revision(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        claim = ClaimRepository(database).get(WORKSPACE_P, claim_id)
        assert claim.current_revision == 1
        assert claim.statement.startswith("A meaningful segment")
        assert claim.lifecycle == ClaimLifecycle.ACTIVE.value

    def test_p_claim_belongs_to_one_opportunity(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        assert ClaimRepository(database).get(WORKSPACE_P, claim_id).opportunity_id == opportunity

    def test_one_opportunity_carries_many_independently_evaluated_claims(self, database) -> None:
        """The point of the model. Aggregating at the opportunity level would
        average a well-supported claim together with a contradicted one."""
        opportunity = make_opportunity(database)
        supported = make_claim(database, opportunity, statement="Users show strong interest.")
        contradicted = make_claim(
            database, opportunity, statement="The market has few alternatives."
        )

        add_evidence(database, supported, direction=D.SUPPORTS)
        add_evidence(database, contradicted, direction=D.CONTRADICTS)

        claims = ClaimRepository(database).list_for_opportunity(WORKSPACE_P, opportunity)
        assert {c.id for c in claims} == {supported, contradicted}

        repository = EvidenceRepository(database)
        assert [e["direction"] for e in repository.list_for_claim(WORKSPACE_P, supported)] == [
            "SUPPORTS"
        ]
        assert [e["direction"] for e in repository.list_for_claim(WORKSPACE_P, contradicted)] == [
            "CONTRADICTS"
        ]

    def test_claim_identity_is_not_claim_type(self, database) -> None:
        """Mission 1.2 §6. Five ClaimType values; any number of claims. A system
        that used one as the other would have exactly five claims."""
        opportunity = make_opportunity(database)
        first = make_claim(database, opportunity, statement="Statement one.")
        second = make_claim(database, opportunity, statement="Statement two.")
        assert first != second
        repository = ClaimRepository(database)
        assert repository.get(WORKSPACE_P, first).claim_type == ClaimType.INFERRED.value
        assert repository.get(WORKSPACE_P, second).claim_type == ClaimType.INFERRED.value

    def test_temporality_is_explicit_and_has_no_default(self, database) -> None:
        """§12. Never inferred from the source: one platform carries an
        evergreen fact and a trend stale in a week."""
        opportunity = make_opportunity(database)
        evergreen = make_claim(
            database,
            opportunity,
            statement="Teams need a way to share notes.",
            temporality=ClaimTemporality.EVERGREEN,
        )
        sensitive = make_claim(
            database,
            opportunity,
            statement="Interest in this category is rising.",
            temporality=ClaimTemporality.TEMPORALLY_SENSITIVE,
            claim_feature="trend-momentum",
        )
        repository = ClaimRepository(database)
        assert repository.get(WORKSPACE_P, evergreen).temporality == "EVERGREEN"
        assert repository.get(WORKSPACE_P, sensitive).temporality == "TEMPORALLY_SENSITIVE"
        # The claim NAMES the feature; the half-life lives in the profile, and
        # no profile has one (framework §9).
        assert repository.get(WORKSPACE_P, sensitive).claim_feature == "trend-momentum"

    def test_provenance_answers_where_the_assertion_came_from(self, database) -> None:
        opportunity = make_opportunity(database)
        session = make_session(database)
        claim_id = ClaimRepository(database).create(
            WORKSPACE_P,
            opportunity,
            "Extracted assertion.",
            ClaimType.OBSERVED,
            ClaimTemporality.EVERGREEN,
            ClaimOrigin.LLM_EXTRACTION,
            # A generated OBSERVED claim may not be stored unsupported, and the
            # requirement is a DEFERRABLE trigger firing at COMMIT -- so the
            # evidence has to land in THIS transaction, not a later one
            # (Mission 1.13 §22, ADR-024).
            evidence=[
                {
                    "direction": D.SUPPORTS,
                    "evidence_level": 1,
                    "collected_at": NOW,
                    "expires_at": EXPIRES,
                }
            ],
            origin_session_id=session,
            origin_detail="extracted from a review corpus",
            model_version="test-model-v3",
            prompt_version="claim-extraction@1",
            created_by="test",
        )
        claim = ClaimRepository(database).get(WORKSPACE_P, claim_id)
        assert claim.origin == "LLM_EXTRACTION"
        assert claim.origin_session_id == session
        # The model name is provenance, never the origin enum: a new model must
        # not require a contract change (§11).
        assert claim.model_version == "test-model-v3"
        assert "LLM_EXTRACTION" not in (claim.model_version or "")

    def test_p_claim_accumulates_evidence_across_sessions(self, database) -> None:
        """§10. A claim is not owned by the session that first met it.
        Duplicating it because a second session found it would split its
        evidence in two."""
        opportunity = make_opportunity(database)
        first_session = make_session(database)
        second_session = make_session(database)
        claim_id = make_claim(database, opportunity, origin_session_id=first_session)

        repository = ClaimRepository(database)
        repository.record_observation(
            WORKSPACE_P, claim_id, first_session, ObservationKind.DISCOVERED
        )
        repository.record_observation(
            WORKSPACE_P, claim_id, second_session, ObservationKind.CORROBORATED
        )
        add_evidence(database, claim_id)
        add_evidence(database, claim_id, research_session_id=second_session)

        observations = repository.observations(WORKSPACE_P, claim_id)
        assert {o["observation_kind"] for o in observations} == {"DISCOVERED", "CORROBORATED"}
        # One claim, two sessions, one evidence set.
        assert len(EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)) == 2
        assert len(repository.list_for_opportunity(WORKSPACE_P, opportunity)) == 1

    def test_deleting_a_session_leaves_the_claim_standing(self, database) -> None:
        """A claim is not owned by the session that discovered it, so deleting
        the session must clear the reference and keep the claim.

        This is a regression test. The first version of migration 0005 used a
        bare `ON DELETE SET NULL` on a COMPOSITE key, which nulls every column in
        it -- including `workspace_id`, which is NOT NULL. Deleting a session
        therefore failed with a constraint violation naming a column nobody had
        touched. `ON DELETE SET NULL (origin_session_id)` fixes it; CASCADE would
        have been worse than the bug, because it would delete the claim.
        """
        opportunity = make_opportunity(database)
        session = make_session(database)
        claim_id = make_claim(database, opportunity, origin_session_id=session)
        add_evidence(database, claim_id)

        with database.tenant_transaction(WORKSPACE_P) as conn:
            conn.execute(
                "DELETE FROM research.research_sessions WHERE workspace_id = %s AND id = %s",
                (WORKSPACE_P, session),
            )

        claim = ClaimRepository(database).get(WORKSPACE_P, claim_id)
        assert claim.origin_session_id is None
        assert claim.workspace_id == WORKSPACE_P
        # The evidence went nowhere either.
        assert len(EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)) == 1

    def test_a_group_with_members_cannot_simply_be_deleted(self, database) -> None:
        """RESTRICT, and the refusal is the designed behaviour.

        The first version of the migration used SET NULL here, which
        contradicted the shape CHECK: nulling the group leaves a
        KNOWN_DEPENDENT record depending on nothing. A grouping with members is
        a claim about provenance that other rows rely on, so removing it is a
        decision about each of them -- and the database should make somebody
        take it rather than quietly discarding the relationship.
        """
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        repository = EvidenceRepository(database)
        group = repository.create_independence_group(
            WORKSPACE_P, claim_id, basis="shared origin", detection_method="manual"
        )
        evidence_id = add_evidence(
            database,
            claim_id,
            independence_state=IND.KNOWN_DEPENDENT,
            independence_group_id=group,
        )

        with (
            pytest.raises(Exception, match="evidence_independence_group_same_claim_fkey"),
            database.tenant_transaction(WORKSPACE_P) as conn,
        ):
            conn.execute(
                """DELETE FROM scoring.evidence_independence_groups
                    WHERE workspace_id = %s AND id = %s""",
                (WORKSPACE_P, group),
            )

        # Correct the members first, and the group can then go.
        with database.tenant_transaction(WORKSPACE_P) as conn:
            conn.execute(
                """UPDATE scoring.evidence
                      SET independence_state = 'UNKNOWN', independence_group_id = NULL
                    WHERE workspace_id = %s AND id = %s""",
                (WORKSPACE_P, evidence_id),
            )
            conn.execute(
                """DELETE FROM scoring.evidence_independence_groups
                    WHERE workspace_id = %s AND id = %s""",
                (WORKSPACE_P, group),
            )
        records = repository.list_for_claim(WORKSPACE_P, claim_id)
        assert len(records) == 1
        assert records[0]["independence_state"] == "UNKNOWN"

    def test_withdrawal_is_editorial_and_keeps_the_history(self, database) -> None:
        """§38. There is no VALIDATED state and no REJECTED one: evidence
        changes, and a lifecycle derived from it would freeze a conclusion."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        add_evidence(database, claim_id)
        repository = ClaimRepository(database)
        repository.withdraw(WORKSPACE_P, claim_id, "duplicated another claim")

        assert repository.get(WORKSPACE_P, claim_id).lifecycle == "WITHDRAWN"
        assert repository.list_for_opportunity(WORKSPACE_P, opportunity) == []
        assert (
            len(repository.list_for_opportunity(WORKSPACE_P, opportunity, include_withdrawn=True))
            == 1
        )
        # The evidence survives. Deleting it would destroy the record of what
        # was once believed.
        assert EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)

    def test_withdrawal_requires_a_reason(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        with pytest.raises(ContractError):
            ClaimRepository(database).withdraw(WORKSPACE_P, claim_id, "   ")

    def test_no_lifecycle_value_asserts_the_claim_is_true(self) -> None:
        """The absence IS the feature. A VALIDATED state would be an epistemic
        conclusion stored as an editorial one."""
        values = {member.value for member in ClaimLifecycle}
        assert values == {"ACTIVE", "WITHDRAWN"}
        assert not values & {"VALIDATED", "REJECTED", "CONFIRMED", "DISPROVEN"}

    def test_a_blank_statement_is_refused(self, database) -> None:
        opportunity = make_opportunity(database)
        with pytest.raises(ContractError):
            make_claim(database, opportunity, statement="   ")


# ================================================== versioning and reproducibility


@needs_postgres
class TestHistoricalReproducibility:
    def test_revising_does_not_mutate_the_previous_revision(self, database) -> None:
        """§25. An aggregation that evaluated revision 1 must still be able to
        read revision 1 -- otherwise every historical result becomes
        unreproducible the moment somebody fixes a typo."""
        opportunity = make_opportunity(database)
        repository = ClaimRepository(database)
        claim_id = make_claim(database, opportunity, statement="Users want faster exports.")

        original = repository.get(WORKSPACE_P, claim_id).statement
        revision = repository.revise(
            WORKSPACE_P,
            claim_id,
            "Enterprise users want faster exports.",
            revision_reason="narrowed the population",
            material_change=True,
        )

        assert revision == 2
        assert repository.get(WORKSPACE_P, claim_id).statement.startswith("Enterprise")
        # The evaluated text, still readable.
        assert repository.statement_at(WORKSPACE_P, claim_id, 1) == original

    def test_identity_survives_a_rewrite(self, database) -> None:
        """§5. Under supersession the id would change and every attached
        evidence record would be orphaned exactly when the claim is clarified."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        add_evidence(database, claim_id)
        ClaimRepository(database).revise(
            WORKSPACE_P,
            claim_id,
            "A rewritten statement.",
            revision_reason="clarity",
            material_change=False,
        )
        assert ClaimRepository(database).get(WORKSPACE_P, claim_id).id == claim_id
        assert len(EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)) == 1

    def test_the_history_records_whether_the_meaning_changed(self, database) -> None:
        """`material_change` is author-declared and nothing acts on it in V1.
        It is recorded now because only the editor knows, and it cannot be
        reconstructed later (D-08 will need it)."""
        opportunity = make_opportunity(database)
        repository = ClaimRepository(database)
        claim_id = make_claim(database, opportunity)
        repository.revise(
            WORKSPACE_P,
            claim_id,
            "Fixed a typo in the statement.",
            revision_reason="typo",
            material_change=False,
        )
        repository.revise(
            WORKSPACE_P,
            claim_id,
            "A materially different assertion entirely.",
            revision_reason="scope change",
            material_change=True,
        )
        history = repository.revisions(WORKSPACE_P, claim_id)
        assert [h["revision"] for h in history] == [1, 2, 3]
        assert [h["material_change"] for h in history] == [False, False, True]
        assert all(h["revision_reason"] for h in history)

    def test_a_revision_that_changes_nothing_is_refused(self, database) -> None:
        opportunity = make_opportunity(database)
        repository = ClaimRepository(database)
        claim_id = make_claim(database, opportunity, statement="Unchanged.")
        with pytest.raises(ClaimStatementUnchangedError):
            repository.revise(
                WORKSPACE_P, claim_id, "Unchanged.", revision_reason="none", material_change=False
            )

    def test_a_revision_requires_a_stated_reason(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        with pytest.raises(ContractError):
            ClaimRepository(database).revise(
                WORKSPACE_P,
                claim_id,
                "Something else.",
                revision_reason="  ",
                material_change=False,
            )

    def test_the_pointer_always_names_a_real_revision(self, database) -> None:
        """The deferred composite foreign key. A pointer to a nonexistent
        revision would make the current statement unreadable."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        with psycopg.connect(DATABASE_URL) as conn:
            with pytest.raises(Exception, match="claims_current_revision_fkey"):
                conn.execute(
                    "UPDATE research.claims SET current_revision = 99 WHERE id = %s",
                    (claim_id,),
                )
                conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            conn.rollback()


# ================================================================== evidence


@needs_postgres
class TestEvidencePersistence:
    def test_evidence_references_p_claim_not_an_opportunity(self, database) -> None:
        """Mission 1.1 I-2, resolved. The aggregation unit is the claim."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        evidence_id = add_evidence(database, claim_id)
        records = EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)
        assert [r["evidence_id"] for r in records] == [str(evidence_id)]
        assert records[0]["claim_id"] == str(claim_id)

    def test_all_three_directions_persist(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        for direction in (D.SUPPORTS, D.CONTRADICTS, D.NEUTRAL):
            add_evidence(database, claim_id, direction=direction)
        directions = {
            r["direction"]
            for r in EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)
        }
        assert directions == {"SUPPORTS", "CONTRADICTS", "NEUTRAL"}

    def test_dependent_evidence_is_grouped(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        repository = EvidenceRepository(database)
        group = repository.create_independence_group(
            WORKSPACE_P,
            claim_id,
            basis="all three repeat one product announcement",
            detection_method="manual fixture",
            origin_reference="https://example.invalid/announcement",
        )
        for _ in range(3):
            add_evidence(
                database,
                claim_id,
                independence_state=IND.KNOWN_DEPENDENT,
                independence_group_id=group,
            )
        records = repository.list_for_claim(WORKSPACE_P, claim_id)
        assert {r["independence_group_id"] for r in records} == {str(group)}
        assert repository.independence_groups(WORKSPACE_P, claim_id)[0]["basis"].startswith("all")

    def test_known_independent_carries_no_group(self, database) -> None:
        """§17. A nullable group id alone is NOT the independence model: it
        cannot distinguish 'checked, independent' from 'never checked'."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        add_evidence(database, claim_id, independence_state=IND.KNOWN_INDEPENDENT)
        record = EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)[0]
        assert record["independence_state"] == "KNOWN_INDEPENDENT"
        assert record["independence_group_id"] is None

    def test_unknown_independence_stays_unknown_in_storage(self, database) -> None:
        """§18. The engine builds its conservative runtime bucket without
        writing one here. An unresolved question must not look resolved."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        add_evidence(database, claim_id)  # default state
        record = EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)[0]
        assert record["independence_state"] == "UNKNOWN"
        assert record["independence_group_id"] is None

    def test_invalid_independence_combinations_are_refused(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        group = EvidenceRepository(database).create_independence_group(
            WORKSPACE_P, claim_id, basis="shared origin", detection_method="manual"
        )
        with pytest.raises(ContractError):
            add_evidence(database, claim_id, independence_state=IND.KNOWN_DEPENDENT)
        with pytest.raises(ContractError):
            add_evidence(
                database,
                claim_id,
                independence_state=IND.KNOWN_INDEPENDENT,
                independence_group_id=group,
            )
        with pytest.raises(ContractError):
            add_evidence(
                database,
                claim_id,
                independence_state=IND.UNKNOWN,
                independence_group_id=group,
            )

    def test_the_database_refuses_the_bad_shape_even_without_the_repository(self, database) -> None:
        """The CHECK constraint, not just the application check. A future writer
        that bypasses this repository still cannot store an incoherent record."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        with psycopg.connect(DATABASE_URL) as conn:
            with pytest.raises(psycopg.errors.CheckViolation) as exc:
                conn.execute(
                    """INSERT INTO scoring.evidence
                           (id, workspace_id, claim_id, direction,
                            evidence_level, observation_category, independence_state,
                            collected_at, expires_at)
                       VALUES (%s,%s,%s,'SUPPORTS',1,'UNCATEGORISED',
                               'KNOWN_DEPENDENT',now(),now())""",
                    (uuid.uuid4(), WORKSPACE_P, claim_id),
                )
            # The constraint by NAME, not a substring of the message. This
            # assertion read `"independence" in str(exc.value).lower()` until
            # Mission 1.13 dropped `claim_type` from the table -- at which point
            # it kept passing on an UndefinedColumn error that never reached the
            # CHECK (`testing-strategy.md` §24).
            assert exc.value.diag.constraint_name == "evidence_independence_shape_check"
            conn.rollback()

    def test_a_missing_factor_is_stored_as_missing(self, database) -> None:
        """§22. Not 0.5, not 0.0. Aggregation reports such a record
        non-scorable and names the field; a zero would be a measured weakness."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        add_evidence(database, claim_id, extraction_confidence=None, reliability=None)
        record = EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)[0]
        assert record["extraction_confidence"] is None
        assert record["reliability"] is None

    def test_an_out_of_range_factor_is_refused(self, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        with pytest.raises(ContractError):
            add_evidence(database, claim_id, relevance=1.4)

    def test_a_grouping_requires_a_stated_basis(self, database) -> None:
        """Grouping collapses several records into one contribution -- the
        operation with the largest effect on a result. One with no stated reason
        cannot be re-checked."""
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        with pytest.raises(ContractError):
            EvidenceRepository(database).create_independence_group(
                WORKSPACE_P, claim_id, basis="  ", detection_method="manual"
            )

    def test_the_scalar_independence_column_is_gone(self, database) -> None:
        """Mission 1.1 I-1, resolved. A scalar could not say WHICH records share
        an origin, and it invited q * independence -- discounting instead of
        grouping, which lets ten discounted duplicates outweigh one original."""
        with database.privileged_transaction() as conn:
            columns = {
                r[0]
                for r in conn.execute(
                    """SELECT column_name FROM information_schema.columns
                        WHERE table_schema = 'scoring' AND table_name = 'evidence'"""
                ).fetchall()
            }
        assert "independence" not in columns
        assert {"independence_state", "independence_group_id"} <= columns


# ======================================================= cross-tenant integrity


@needs_postgres
class TestCrossTenantIntegrity:
    def test_workspace_p_cannot_read_workspace_q_claims(self, database) -> None:
        opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        claim_id = make_claim(database, opportunity, workspace=WORKSPACE_Q)
        with pytest.raises(NotFoundError):
            ClaimRepository(database).get(WORKSPACE_P, claim_id)

    def test_workspace_p_cannot_read_workspace_q_evidence(self, database) -> None:
        opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        claim_id = make_claim(database, opportunity, workspace=WORKSPACE_Q)
        add_evidence(database, claim_id, workspace=WORKSPACE_Q)
        assert EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id) == []

    def test_p_claim_cannot_reference_an_opportunity_in_another_workspace(self, database) -> None:
        """The composite foreign key carries workspace_id, so this is a
        structural impossibility rather than a rule somebody must remember."""
        opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        with pytest.raises(Exception) as exc:
            make_claim(database, opportunity, workspace=WORKSPACE_P)
        assert "foreign key" in str(exc.value).lower() or "policy" in str(exc.value).lower()

    def test_evidence_cannot_reference_p_claim_in_another_workspace(self, database) -> None:
        opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        claim_id = make_claim(database, opportunity, workspace=WORKSPACE_Q)
        with pytest.raises(Exception, match="evidence_claim_same_workspace_fkey"):
            add_evidence(database, claim_id, workspace=WORKSPACE_P)

    def test_an_independence_group_cannot_span_claims(self, database) -> None:
        """The evidence foreign key carries workspace AND claim, so a record
        cannot join a group that belongs to a different claim."""
        opportunity = make_opportunity(database)
        first = make_claim(database, opportunity, statement="First claim.")
        second = make_claim(database, opportunity, statement="Second claim.")
        group = EvidenceRepository(database).create_independence_group(
            WORKSPACE_P, first, basis="shared origin", detection_method="manual"
        )
        with pytest.raises(Exception) as exc:
            add_evidence(
                database,
                second,
                independence_state=IND.KNOWN_DEPENDENT,
                independence_group_id=group,
            )
        assert "foreign key" in str(exc.value).lower()

    def test_an_independence_group_cannot_span_workspaces(self, database) -> None:
        opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        claim_id = make_claim(database, opportunity, workspace=WORKSPACE_Q)
        with pytest.raises(Exception, match="independence_groups_claim_same_workspace_fkey"):
            EvidenceRepository(database).create_independence_group(
                WORKSPACE_P, claim_id, basis="shared origin", detection_method="manual"
            )

    def test_a_workspace_is_required_on_every_call(self, database) -> None:
        with pytest.raises(ContractError):
            ClaimRepository(database).get(None, uuid.uuid4())  # type: ignore[arg-type]


# ============================================================ RLS on new tables


@needs_postgres
class TestClaimRowLevelSecurity:
    NEW_TABLES = (
        "research.claims",
        "research.claim_revisions",
        "research.claim_session_observations",
        "scoring.evidence_independence_groups",
    )

    def test_every_new_table_is_policy_bearing(self, database) -> None:
        with database.privileged_transaction() as conn:
            for qualified in self.NEW_TABLES:
                schema, table = qualified.split(".")
                row = conn.execute(
                    """SELECT c.relrowsecurity, c.relforcerowsecurity,
                              (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid)
                         FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = %s AND c.relname = %s""",
                    (schema, table),
                ).fetchone()
                assert row is not None, qualified
                assert row[0] and row[1], f"{qualified} needs ENABLE and FORCE"
                assert row[2] >= 1, f"{qualified} has no policy"

    def test_a_query_with_no_workspace_filter_still_sees_one_tenant(self, database) -> None:
        """The test that justifies RLS: every other layer depends on someone
        remembering something. This one asks for everything and gets one
        tenant's rows."""
        p_opportunity = make_opportunity(database)
        q_opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        p_claim = make_claim(database, p_opportunity, statement="A claim.")
        make_claim(database, q_opportunity, workspace=WORKSPACE_Q, statement="B claim.")

        with database.tenant_transaction(WORKSPACE_P) as conn:
            visible = {r[0] for r in conn.execute("SELECT id FROM research.claims").fetchall()}
        assert p_claim in visible
        with database.tenant_transaction(WORKSPACE_Q) as conn:
            q_visible = {r[0] for r in conn.execute("SELECT id FROM research.claims").fetchall()}
        assert p_claim not in q_visible

    def test_a_tenant_cannot_insert_a_row_tagged_for_another(self, database) -> None:
        """WITH CHECK, not just USING. Without it a workspace could write a row
        visible to nobody who wrote it and to exactly the wrong tenant."""
        opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        with (
            pytest.raises(Exception, match="row-level security"),
            database.tenant_transaction(WORKSPACE_P) as conn,
        ):
            conn.execute(
                """INSERT INTO research.claims
                       (id, workspace_id, opportunity_id, claim_type, temporality, origin)
                   VALUES (%s,%s,%s,'INFERRED','EVERGREEN','MANUAL')""",
                (uuid.uuid4(), WORKSPACE_Q, opportunity),
            )


# ====================================================== aggregation compatibility


@needs_postgres
class TestAggregationCompatibility:
    """§47. The reference engine must be able to aggregate evidence that came
    out of the database, or the specification is only ever tested against
    hand-built objects and nothing proves the persisted model feeds it.

    The engine is imported HERE, in a test. No service imports it, and a CI
    guard asserts that (ADR-014)."""

    def test_the_reference_engine_aggregates_repository_loaded_evidence(self, database) -> None:
        from sros_evidence_aggregation import (
            REFERENCE_PROFILE_V1,
            aggregate,
            evidence_items_from_rows,
        )

        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        repository = EvidenceRepository(database)

        group = repository.create_independence_group(
            WORKSPACE_P,
            claim_id,
            basis="three records repeating one announcement",
            detection_method="manual fixture",
        )
        add_evidence(
            database,
            claim_id,
            relevance=0.8,
            directness=0.8,
            reliability=0.8,
            extraction_confidence=0.8,
            independence_state=IND.KNOWN_INDEPENDENT,
            observation_category=CAT.MARKET_ACTIVITY,
        )
        for _ in range(3):
            add_evidence(
                database,
                claim_id,
                independence_state=IND.KNOWN_DEPENDENT,
                independence_group_id=group,
            )
        add_evidence(
            database,
            claim_id,
            direction=D.CONTRADICTS,
            relevance=0.5,
            directness=0.5,
            reliability=0.5,
            extraction_confidence=0.5,
        )

        claim = ClaimRepository(database).get(WORKSPACE_P, claim_id)
        rows = repository.list_for_claim(WORKSPACE_P, claim_id)
        result = aggregate(
            f"{claim.id}@r{claim.current_revision}",
            evidence_items_from_rows(rows),
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality(claim.temporality),
            now=NOW,
            allow_uncalibrated=True,
        )

        # Five records, three of which share an origin -> three contributions.
        assert result.raw_evidence_count == 5
        assert result.support_group_count == 2
        assert result.contradiction_group_count == 1
        # The dependent trio collapsed to one contribution at its strongest member.
        collapsed = next(g for g in result.groups.support if g.collapsed_member_count)
        assert collapsed.collapsed_member_count == 2
        assert not result.calibrated

    def test_persisted_unknown_independence_becomes_one_runtime_group(self, database) -> None:
        """Storage keeps ten UNKNOWN records as ten unknowns; the engine
        collapses them into one conservative contribution. Neither layer
        pretends the question was answered."""
        from sros_evidence_aggregation import (
            REFERENCE_PROFILE_V1,
            aggregate,
            evidence_items_from_rows,
        )

        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        for _ in range(10):
            add_evidence(database, claim_id)

        rows = EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)
        assert all(r["independence_state"] == "UNKNOWN" for r in rows)
        assert all(r["independence_group_id"] is None for r in rows)

        result = aggregate(
            "claim",
            evidence_items_from_rows(rows),
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality.EVERGREEN,
            now=NOW,
            allow_uncalibrated=True,
        )
        assert result.support_group_count == 1
        assert result.unknown_independence_count == 10

    def test_aggregation_is_reproducible_from_a_stored_claim_revision(self, database) -> None:
        """§25 end to end. Revising the claim does not change the evidence set,
        and the result names the revision it evaluated."""
        from sros_evidence_aggregation import (
            REFERENCE_PROFILE_V1,
            aggregate,
            evidence_items_from_rows,
        )

        opportunity = make_opportunity(database)
        claims = ClaimRepository(database)
        claim_id = make_claim(database, opportunity)
        add_evidence(database, claim_id, independence_state=IND.KNOWN_INDEPENDENT)

        rows = EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)
        before = aggregate(
            f"{claim_id}@r1",
            evidence_items_from_rows(rows),
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality.EVERGREEN,
            now=NOW,
            allow_uncalibrated=True,
        )

        claims.revise(
            WORKSPACE_P,
            claim_id,
            "A revised statement.",
            revision_reason="clarity",
            material_change=False,
        )
        rows_after = EvidenceRepository(database).list_for_claim(WORKSPACE_P, claim_id)
        after = aggregate(
            f"{claim_id}@r1",
            evidence_items_from_rows(rows_after),
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality.EVERGREEN,
            now=NOW,
            allow_uncalibrated=True,
        )
        assert before.canonical_json() == after.canonical_json()
        assert before.evidence_snapshot_digest == after.evidence_snapshot_digest
        # And revision 1 still reads as it did.
        assert claims.statement_at(WORKSPACE_P, claim_id, 1).startswith("A meaningful segment")

    def test_no_aggregation_result_is_persisted(self, database) -> None:
        """§39, §26. The model is prepared; the table is not created. Storing a
        result would be scoring, and scoring needs a calibrated profile."""
        with database.privileged_transaction() as conn:
            tables = {
                r[0]
                for r in conn.execute(
                    """SELECT table_name FROM information_schema.tables
                        WHERE table_schema IN ('scoring', 'research')"""
                ).fetchall()
            }
        assert not any("aggregation" in name for name in tables), tables


# ========================================================================= API


@needs_postgres
class TestClaimApi:
    def test_the_claim_lifecycle_through_the_api(self, api_client, database) -> None:
        opportunity = make_opportunity(database)
        created = api_client.post(
            "/api/v1/claims",
            headers=header(WORKSPACE_P),
            json={
                "opportunity_id": str(opportunity),
                "statement": "Users show strong interest in this category.",
                "claim_type": "INFERRED",
                "temporality": "EVERGREEN",
                "origin": "MANUAL",
            },
        )
        assert created.status_code == 201
        claim_id = created.json()["claim_id"]

        revised = api_client.post(
            f"/api/v1/claims/{claim_id}/revisions",
            headers=header(WORKSPACE_P),
            json={
                "statement": "Enterprise users show strong interest in this category.",
                "revision_reason": "narrowed the population",
                "material_change": True,
            },
        )
        assert revised.status_code == 201
        assert revised.json()["revision"] == 2

        detail = api_client.get(f"/api/v1/claims/{claim_id}", headers=header(WORKSPACE_P)).json()
        assert [r["revision"] for r in detail["revisions"]] == [1, 2]
        assert detail["statement"].startswith("Enterprise")

        listing = api_client.get(
            f"/api/v1/opportunities/{opportunity}/claims", headers=header(WORKSPACE_P)
        ).json()
        assert listing["count"] == 1

    def test_the_evidence_endpoint_returns_inputs_not_a_score(self, api_client, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        add_evidence(database, claim_id, independence_state=IND.KNOWN_INDEPENDENT)
        add_evidence(database, claim_id, direction=D.CONTRADICTS)

        body = api_client.get(
            f"/api/v1/claims/{claim_id}/evidence", headers=header(WORKSPACE_P)
        ).json()
        assert body["counts"]["supports"] == 1
        assert body["counts"]["contradicts"] == 1
        assert body["counts"]["unknown_independence"] == 1
        # No score, no strength, no mass. Serving one would be scoring.
        serialised = str(body)
        for forbidden in ("evidence_score", "support_strength", "supported_mass"):
            assert forbidden not in serialised

    def test_a_missing_workspace_header_fails_closed(self, api_client, database) -> None:
        opportunity = make_opportunity(database)
        claim_id = make_claim(database, opportunity)
        assert api_client.get(f"/api/v1/claims/{claim_id}").status_code == 400

    def test_a_cross_workspace_read_is_a_404(self, api_client, database) -> None:
        opportunity = make_opportunity(database, WORKSPACE_Q, "Q opportunity")
        claim_id = make_claim(database, opportunity, workspace=WORKSPACE_Q)
        response = api_client.get(f"/api/v1/claims/{claim_id}", headers=header(WORKSPACE_P))
        assert response.status_code == 404
