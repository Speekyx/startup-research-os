"""One human decision, recorded — and everything it did not grant (Mission 1.15.6.1).

**No external call.** Nothing here reaches TED.

The property this file exists to protect is one sentence: **a human decision
clears a condition and nothing else.**

The mission ran twice. The first statement was refused, because three of the
seven acknowledgements were absent and inferring them would have been the system
supplying the part of an acceptance the human did not — the exact act a
`HUMAN_CONFIRMATION` condition exists to make impossible. The operator then
supplied the complete acknowledgement, and one row was written.

**The assertions from the first run are inverted here, not deleted**
(`testing-strategy.md` §43). What flipped is whether an acceptance exists. What
did not flip, and is asserted at greater length than the acceptance itself: H-36
stays open, the commercial profile stays refused, bulk XML stays blocked, the
field gate stays closed, and training, embeddings and redistribution stay
forbidden. **A risk acceptance that widened any of those would be a different
thing wearing its name.**
"""

from __future__ import annotations

import pathlib
import re

import pytest
from sros_acquisition.compliance import (
    AcquisitionNotAuthorizedError,
    build_authorization,
    satisfied_condition_keys,
    verify_source,
)
from sros_acquisition.compliance.config import load_compliance
from sros_acquisition.compliance.verification import ConditionVerificationRecord
from sros_acquisition.registry import evaluate_eligibility
from sros_contracts import (
    ConditionVerification,
    ConditionVerificationResult,
    PolicyAssessment,
    SourceApprovalState,
)

from .conftest import (
    DATABASE_URL,
    LEGACY_PROFILE,
    LOCAL_PROFILE,
    REPO_ROOT,
    _postgres_available,
    needs_postgres,
)


class _RollbackError(Exception):
    """Unwinds a transaction that must not commit. Named so the `except` reads."""


def _acceptance_recorded() -> bool:
    """Whether THIS deployment holds the operator's acceptance.

    **A human confirmation is deployment state, not repository state**, and the
    distinction is the reason this function exists rather than a constant.
    `source-registry-v1.md` §3 and Mission 1.3 §24 already say it: satisfaction
    depends on what is deployed, and a catalog that could assert its own
    conditions satisfied would make `APPROVED_WITH_CONDITIONS` meaningless.

    So the row travels with the database, not with git. On the operator's
    machine it exists; in CI, which starts from an empty database and has no
    operator, it does not — and TED is correctly ineligible there.

    This was learned the hard way: the first version of this file asserted the
    acceptance unconditionally and went red in CI, which is the same mistake as
    quoting one database's research counts as a property of the repository.
    """
    if not _postgres_available():
        return False
    import psycopg

    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            row = conn.execute(
                """SELECT count(*)
                     FROM registry.source_condition_verifications v
                     JOIN registry.source_review_conditions c ON c.id = v.condition_id
                     JOIN registry.source_policy_reviews r ON r.id = c.review_id
                    WHERE v.condition_key = %s
                      AND v.result = 'SATISFIED'
                      AND r.assessed_use_profile = %s
                      AND r.review_version = 2""",
                (RESIDUAL, LOCAL_PROFILE),
            ).fetchone()
        return bool(row and row[0])
    except psycopg.errors.UndefinedTable:
        # The registry is not loaded here. Absent, not broken.
        return False


@pytest.fixture
def needs_recorded_acceptance() -> None:
    """Skip unless THIS deployment holds the acceptance.

    A fixture rather than a module-level `skipif`, because the latter is
    evaluated at IMPORT time: the database is asked before the session has
    started, any hiccup is indistinguishable from a real absence, and the whole
    file then skips silently while looking like it ran. Asked at test time, the
    answer is the one that matters and a failure to ask is visible.
    """
    if not _acceptance_recorded():
        pytest.skip(
            "no operator acceptance is recorded in this deployment. That is the correct "
            "state for CI and for a fresh clone: a HUMAN_CONFIRMATION is environment "
            "state and does not travel through git"
        )


RESIDUAL = "ted-database-right-residual-exposure-accepted"
ROUTE_ONLY = "ted-official-route-only"
MINIMISATION = "ted-personal-data-minimisation"

SEARCH_API = "ted-search-api"
OPEN_DATA = "ted-open-data-sparql"
BULK_XML = "ted-bulk-xml"

DOCS = REPO_ROOT / "docs" / "data"
PENDING = DOCS / "ted-eu-operator-acceptance-pending-v1.md"
RECORDED = DOCS / "ted-eu-operator-risk-acceptance-v1.md"


@pytest.fixture(scope="module")
def compliance():
    return load_compliance(DOCS / "source-compliance-v1.json")


@pytest.fixture
def ted(catalog):
    return next(s for s in catalog if s.source_id == "ted-eu")


@pytest.fixture
def ted_local(compliance):
    return compliance.get("ted-eu", LOCAL_PROFILE)


@pytest.fixture
def records(ted, compliance):
    return verify_source(ted, LOCAL_PROFILE, compliance, environ={})


def flat(path: pathlib.Path) -> str:
    """Lowercased, whitespace-collapsed, and stripped of markdown emphasis.

    `testing-strategy.md` §39 asserts against normalised text rather than line
    breaks. The same argument covers `**bold**` and `` `code` ``: a document
    that emphasised a phrase would otherwise stop containing it.
    """
    text = " ".join(path.read_text(encoding="utf-8").split()).lower()
    return text.replace("`", "").replace("**", "").replace("*", "")


# ======================================== the acceptance was supplied, not recorded


class TestTheDecisionIsStillTheHumansAlone:
    """Inverted from the first run, where these asserted that nothing had been
    accepted. What is asserted now is narrower and more important: an acceptance
    exists, and **no verifier produced it**."""

    def test_the_condition_is_still_declared_human(self, ted) -> None:
        """The classification did not move to make the acceptance possible."""
        condition = next(
            c for c in ted.review_for(LOCAL_PROFILE).required_conditions if c.key == RESIDUAL
        )
        assert condition.verification is ConditionVerification.HUMAN_CONFIRMATION
        assert condition.verification_detail is None

    def test_the_live_verifier_still_reaches_only_unknown(self, records) -> None:
        """**The load-bearing assertion of this file.** A recorded decision must
        not have taught any verifier to produce one. `verify_source` answers
        `UNKNOWN` for this condition today exactly as it did before the operator
        decided anything, and that is why the decision means something."""
        record = next(r for r in records if r.condition_key == RESIDUAL)
        assert record.result is ConditionVerificationResult.UNKNOWN
        assert record.verifier == "human-confirmation"

    def test_the_live_path_alone_still_refuses(self, ted, compliance) -> None:
        """Unchanged, and correct. `build_authorization` with no recorded state
        cannot see a human decision, because the live verifiers cannot produce
        one. The authorization in the next class is built by SUPPLYING the
        recorded decision, which is what the parameter exists for."""
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LOCAL_PROFILE, compliance, environ={})
        assert caught.value.reasons == (f"review conditions not satisfied: {RESIDUAL}",)

    def test_the_three_machine_conditions_are_satisfied_by_verifiers(self, records) -> None:
        by_key = {r.condition_key: r for r in records}
        for key in ("ted-attribution", ROUTE_ONLY, MINIMISATION):
            assert by_key[key].result is ConditionVerificationResult.SATISFIED, key

    def test_both_documents_exist_and_the_refusal_was_not_erased(self) -> None:
        """§15. The recorded acceptance exists AND the refused first attempt is
        preserved. Rewriting history to pretend Outcome B never happened would
        delete the only record of why the bar is where it is."""
        assert RECORDED.exists()
        assert PENDING.exists()
        assert "superseded" in flat(PENDING)


# ============================================ the statement was preserved, not rewritten


class TestTheRefusedFirstStatementIsPreserved:
    """About the FIRST statement and the document that refused it. Kept whole:
    the refusal is why the recorded acknowledgement is the complete one."""

    def test_the_french_original_is_reproduced_verbatim(self) -> None:
        """§1, §7. The operator's words are evidence. Rewording them into
        stronger legal language would be the system improving a human's
        statement, which is the same act as inventing one."""
        # Normalised across the blockquote's line breaks and `> ` prefixes,
        # never across its characters (`testing-strategy.md` §39). The operator
        # wrote U+2019 rather than an ASCII apostrophe, and this assertion
        # caught the document quietly substituting one -- which is the smallest
        # possible version of rewriting somebody's statement.
        quoted = " ".join(
            line.lstrip("> ").strip()
            for line in PENDING.read_text(encoding="utf-8").splitlines()
            if line.startswith(">")
        )
        assert "J’accepte le risque résiduel TED pour" in quoted
        assert "l’utilisation 100 % locale réduit l’exposition" in quoted
        assert "ne constitue pas une garantie juridique ni une résolution de H-36" in quoted

    def test_the_document_credits_what_the_statement_does_establish(self) -> None:
        """Refusing to record is not the same as dismissing. The statement is a
        real acceptance of the core risk and the document says so."""
        text = flat(PENDING)
        assert "not a rejection of the operator's decision" in text
        assert "knowing it is unresolved" in text

    def test_it_names_which_acknowledgements_are_missing(self) -> None:
        """§8. The exact governance requirement it fails to satisfy, not a
        general complaint."""
        text = flat(PENDING)
        assert "has read" in text
        assert "falls" in text
        assert "three of the seven are absent" in text

    def test_it_carries_the_complete_text_still_required(self) -> None:
        """§8. No additional wording beyond what existing documentation requires,
        so the operator can see exactly what is being asked."""
        text = PENDING.read_text(encoding="utf-8")
        for marker in (
            "H-36A is NOT ESTABLISHED",
            "H-36B is NOT ADDRESSED",
            "at review version 2, and for nothing else",
        ):
            assert marker in text, marker

    def test_no_acknowledgement_was_attributed_to_the_operator(self) -> None:
        """The document must not assert that the operator read the documents,
        understood the four bases, or accepted the boundary conditions -- none
        of which the FIRST statement said."""
        text = flat(PENDING)
        for invented in (
            "the operator has read",
            "the operator confirms having read",
            "the operator understands that h-36a",
            "the operator accepts at review version 2",
        ):
            assert invented not in text, invented


# ======================================== the recorded acknowledgement, verbatim


class TestTheRecordedAcknowledgementIsFaithful:
    """§5. Stored as the operator wrote it, in the language they wrote it."""

    def test_every_clause_of_the_acknowledgement_is_present(self) -> None:
        quoted = " ".join(
            line.lstrip("> ").strip()
            for line in RECORDED.read_text(encoding="utf-8").splitlines()
            if line.startswith(">")
        )
        for clause in (
            "J\u2019ai lu int\u00e9gralement",
            "H-36A est `NOT ESTABLISHED`",
            "H-36B est `NOT ADDRESSED` pour l\u2019extraction large du corpus",
            "d\u00e9cision 2011/833/UE",
            "requ\u00eates born\u00e9es et cibl\u00e9es",
            "cesse de s\u2019appliquer",
            "aucun avocat n\u2019a valid\u00e9",
            "review version 2, et pour rien d\u2019autre",
            "ne s\u2019\u00e9tend pas \u00e0 `commercial-multi-tenant-research-v1`",
        ):
            assert clause in quoted, clause

    def test_it_was_not_summarised_into_something_stronger(self) -> None:
        """§5 names the exact paraphrase to avoid. The decision is the acceptance
        of a RESIDUAL UNRESOLVED exposure, not a grant."""
        text = flat(RECORDED)
        for stronger in (
            "ted database rights accepted",
            "database right cleared",
            "database rights permitted",
            "h-36 closed",
        ):
            # Every occurrence must be a DENIAL. The document quotes the
            # paraphrases it must not make, which is worth more than never
            # naming them -- so the test asks whether each one is negated
            # rather than whether the characters appear.
            for match in re.finditer(re.escape(stronger), text):
                preceding = text[max(0, match.start() - 60) : match.start()]
                assert "not" in preceding or "never" in preceding, (stronger, preceding)
        assert "residual" in text and "unresolved" in text

    def test_the_operators_own_hedge_was_kept_rather_than_normalised(self) -> None:
        """The operator wrote "\u00e0 lui seul" and "explicite" where the canonical
        text says none of the four IS a grant. Their wording is kept and the
        difference is recorded -- smoothing it into the template would be
        improving somebody's recorded words, which is how an acknowledgement
        they did not make gets added later."""
        quoted = RECORDED.read_text(encoding="utf-8")
        assert "\u00e0 lui seul" in quoted
        assert "wording difference" in flat(RECORDED)

    def test_the_actor_is_the_neutral_identifier(self) -> None:
        """§4. No real legal name invented in governance data."""
        text = RECORDED.read_text(encoding="utf-8")
        assert "local-operator" in text
        assert "acknowledgement-v1" in text


# ============================ the authorization the recorded decision unlocks


@needs_postgres
@pytest.mark.usefixtures("needs_recorded_acceptance")
class TestTheAuthorizationBuilds:
    """§7, §8, §9, §11, §19.

    The context is built from the COMPLETE verification set: the three capability
    results the verifiers found now, plus the decision the operator recorded.
    Neither half is complete on its own -- `verify_source` can never satisfy a
    human condition, and the three capability results were never written to the
    database -- which is the gap recorded in
    `ted-eu-operator-risk-acceptance-v1.md` §8.

    Supplying them is what `build_authorization`'s `verifications` parameter is
    for. It is not a way past the gate: `evaluate_eligibility` is asserted on the
    same set first, so the authorization is shown to follow the gate rather than
    to bypass it.
    """

    @pytest.fixture
    def complete(self, ted, compliance):
        """Live capability results + the recorded human decision, read back."""
        import psycopg

        live = [
            record
            for record in verify_source(ted, LOCAL_PROFILE, compliance, environ={})
            if record.condition_key != RESIDUAL
        ]
        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(
                """SELECT v.verifier, v.verifier_version, v.result, v.reason, v.reference,
                          v.verified_at
                     FROM registry.source_condition_verifications v
                     JOIN registry.source_review_conditions c ON c.id = v.condition_id
                     JOIN registry.source_policy_reviews r ON r.id = c.review_id
                    WHERE v.condition_key = %s AND r.assessed_use_profile = %s
                      AND r.review_version = 2""",
                (RESIDUAL, LOCAL_PROFILE),
            ).fetchone()
        assert row is not None, "no recorded acceptance to read back"
        recorded = ConditionVerificationRecord(
            source_id="ted-eu",
            review_version=2,
            condition_key=RESIDUAL,
            verification=ConditionVerification.HUMAN_CONFIRMATION,
            verifier=row[0],
            verifier_version=row[1],
            result=ConditionVerificationResult(row[2]),
            reason=row[3],
            reference=row[4],
            verified_at=row[5],
        )
        return (*live, recorded)

    def test_all_four_conditions_are_satisfied(self, complete) -> None:
        assert len(complete) == 4
        assert satisfied_condition_keys(complete) == {
            "ted-attribution",
            ROUTE_ONLY,
            MINIMISATION,
            RESIDUAL,
        }

    def test_the_gate_passes(self, ted, complete) -> None:
        """Asserted BEFORE the authorization, so the authorization is shown to
        follow the gate rather than to be an alternative to it."""
        result = evaluate_eligibility(ted, LOCAL_PROFILE, None, satisfied_condition_keys(complete))
        assert result.eligible, result.blocking_reasons

    def test_the_context_builds(self, ted, compliance, complete) -> None:
        context = build_authorization(ted, LOCAL_PROFILE, compliance, complete, environ={})
        assert context.source_id == "ted-eu"
        assert context.use_profile_id == LOCAL_PROFILE
        assert context.review_version == 2
        assert context.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS

    def test_it_carries_exactly_the_two_authorised_routes(self, ted, compliance, complete) -> None:
        """§8. The assertion this whole mechanism exists for."""
        context = build_authorization(ted, LOCAL_PROFILE, compliance, complete, environ={})
        assert set(context.authorized_route_labels) == {SEARCH_API, OPEN_DATA}

    def test_it_does_not_carry_bulk_xml(self, ted, compliance, complete) -> None:
        """§8, stated separately because it is the one that matters. The registry
        DOES record `ted-bulk-xml` as a real route; the context must not."""
        context = build_authorization(ted, LOCAL_PROFILE, compliance, complete, environ={})
        assert BULK_XML in {profile.label for profile in ted.access_profiles}
        assert BULK_XML not in context.authorized_route_labels
        assert all(access.label != BULK_XML for access in context.access)
        assert context.authorize_route(BULK_XML)

    def test_the_search_api_is_the_preferred_route(self, ted, compliance, complete) -> None:
        """§9. An implementation preference among authorised routes, never
        broader permission -- and it must name one of them."""
        context = build_authorization(ted, LOCAL_PROFILE, compliance, complete, environ={})
        assert context.route_authorization.preferred_label == SEARCH_API
        assert context.route_authorization.preferred_label in context.authorized_route_labels

    def test_the_field_gate_is_unchanged_on_the_built_context(
        self, ted, compliance, complete
    ) -> None:
        """§11. The acceptance widened no field."""
        context = build_authorization(ted, LOCAL_PROFILE, compliance, complete, environ={})
        allowed = context.data_minimisation.allowed
        assert context.authorize_fields(allowed) == ()
        for prohibited in context.data_minimisation.excluded:
            assert context.authorize_fields((*allowed, prohibited)), prohibited
        assert context.authorize_fields(("tender_full_text",))
        assert context.authorize_fields(None)

    def test_the_context_still_authorises_no_concrete_resource(
        self, ted, compliance, complete
    ) -> None:
        """§10, and the qualifier `AUTHORIZATION_READY` must not hide.

        TED authorises zero datasets, so a collector holding this context would
        be refused every resource it asked for. `resource_ready` is NO, and the
        collector mission's first act is a governance one.
        """
        context = build_authorization(ted, LOCAL_PROFILE, compliance, complete, environ={})
        assert context.datasets == ()
        assert context.authorized_dataset("anything") is None

    def test_the_commercial_profile_still_refuses_with_the_same_records(
        self, ted, compliance, complete
    ) -> None:
        """§13. Even handed the recorded acceptance, the wider profile refuses --
        because it fails at the VERDICT, before any condition is consulted."""
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LEGACY_PROFILE, compliance, complete, environ={})
        reasons = " ".join(caught.value.reasons).lower()
        assert "requires_review" in reasons


@needs_postgres
class TestTheAcceptanceIsDeploymentStateEitherWay:
    """The invariant that is true on **both** machines, and the reason the
    classes above are gated.

    Whether an acceptance exists depends on the deployment. What must never
    depend on the deployment is that an acceptance, IF present, came from a
    person and carries the right scope — and that TED is refused for exactly
    that condition when it is absent.
    """

    @staticmethod
    def _rows():
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            return conn.execute(
                """SELECT v.verifier, v.result, r.assessed_use_profile, r.review_version
                     FROM registry.source_condition_verifications v
                     JOIN registry.source_review_conditions c ON c.id = v.condition_id
                     JOIN registry.source_policy_reviews r ON r.id = c.review_id
                    WHERE v.condition_key = %s AND v.result = 'SATISFIED'""",
                (RESIDUAL,),
            ).fetchall()

    def test_any_acceptance_present_came_from_a_person(self) -> None:
        """Vacuously true where none is recorded, load-bearing where one is."""
        for verifier, _, _, _ in self._rows():
            assert verifier != "human-confirmation", (
                "the human-confirmation verifier produced SATISFIED; it returns UNKNOWN "
                "unconditionally and must never write one"
            )
            for machine in (
                "capability:",
                "access-restriction:",
                "credential-availability",
                "compliance-config",
                "unregistered",
            ):
                assert not verifier.startswith(machine), verifier

    def test_any_acceptance_present_is_scoped_to_the_local_review_v2(self) -> None:
        for _, _, profile, version in self._rows():
            assert profile == LOCAL_PROFILE
            assert version == 2

    def test_there_is_never_more_than_one(self) -> None:
        """§19. One decision, not a history of changes of mind."""
        assert len(self._rows()) <= 1

    def test_without_it_ted_is_refused_for_exactly_that_condition(self, ted, compliance) -> None:
        """The other side of the same invariant. Where no acceptance is recorded
        — CI, a fresh clone — TED must be refused, and refused by name rather
        than for some incidental reason."""
        if self._rows():
            pytest.skip("an acceptance is recorded in this deployment")
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LOCAL_PROFILE, compliance, environ={})
        assert caught.value.reasons == (f"review conditions not satisfied: {RESIDUAL}",)


# =================================================== H-36 is unchanged


class TestH36IsUnchanged:
    def test_both_limbs_are_still_open_in_the_review(self, ted) -> None:
        """§4. An acceptance is a decision to proceed with uncertainty. It is
        not a finding that the uncertainty is gone."""
        questions = " ".join(ted.review_for(LOCAL_PROFILE).open_questions).lower()
        assert "h-36a" in questions
        assert "h-36b" in questions
        assert "not established" in questions

    def test_no_document_claims_a_legal_clearance(self) -> None:
        """§6. The words that must never appear as assertions."""
        for path in (PENDING, RECORDED):
            text = flat(path)
            for forbidden in (
                "h-36 closed",
                "database right cleared",
                "ted database rights permitted",
            ):
                assert forbidden not in text, (path.name, forbidden)

    def test_both_documents_state_that_both_limbs_remain(self) -> None:
        for path in (PENDING, RECORDED):
            text = flat(path)
            assert "h-36a remains not established" in text, path.name
            assert "h-36b remains not addressed" in text, path.name

    def test_authorization_ready_is_stated_apart_from_legal_clearance(self) -> None:
        """§15. `AUTHORIZATION_READY`, never `LEGAL_CLEARANCE` -- and the
        distinction spelled out rather than left to the reader."""
        text = flat(RECORDED)
        assert "authorization_ready" in text
        assert "not a legal clearance" in text


# ============================================ nothing leaked to another scope


class TestNothingLeaked:
    def test_the_commercial_profile_is_still_requires_review(self, ted) -> None:
        """§16. The local decision must not reach the wider profile."""
        assert ted.review_for(LEGACY_PROFILE).approval_state is SourceApprovalState.REQUIRES_REVIEW

    def test_the_commercial_profile_still_refuses_for_its_own_reason(self, ted, compliance) -> None:
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LEGACY_PROFILE, compliance, environ={})
        reasons = " ".join(caught.value.reasons).lower()
        assert "requires_review" in reasons
        assert RESIDUAL not in reasons

    def test_the_residual_condition_exists_under_no_other_profile(self, ted) -> None:
        """The structural guarantee: the commercial review does not carry the
        condition an acceptance would clear, so one cannot reach it."""
        legacy = ted.review_for(LEGACY_PROFILE)
        assert RESIDUAL not in {c.key for c in legacy.required_conditions}

    def test_no_other_source_carries_this_condition(self, catalog) -> None:
        """§22. An acceptance cannot leak to another source, because no other
        source's review names the condition."""
        for source in catalog:
            for profile, review in source.reviews_by_profile().items():
                if source.source_id == "ted-eu" and profile == LOCAL_PROFILE:
                    continue
                assert RESIDUAL not in {c.key for c in review.required_conditions}, (
                    source.source_id,
                    profile,
                )


# ======================================= every restriction Mission 1.15.6 built


class TestNoRestrictionWasWeakened:
    def test_the_route_gate_is_unchanged(self, ted_local) -> None:
        """§13. An acceptance of a legal risk grants no route."""
        routes = ted_local.route_authorization
        assert routes.refusals(SEARCH_API) == ()
        assert routes.refusals(OPEN_DATA) == ()
        assert routes.refusals(BULK_XML)
        assert routes.refusals("ted-html-scrape")
        assert routes.refusals(None)

    def test_the_field_gate_is_unchanged(self, ted_local) -> None:
        """§14. Nor any field."""
        minimisation = ted_local.data_minimisation
        assert minimisation.refusals(minimisation.allowed) == ()
        for prohibited in minimisation.excluded:
            assert minimisation.refusals((*minimisation.allowed, prohibited)), prohibited
        assert minimisation.refusals(("tender_full_text",))
        assert minimisation.refusals(None)

    def test_the_excluded_dataset_families_are_unchanged(self, ted_local) -> None:
        """§12. Bulk XML and the historical CSV stay refused at the resource gate."""
        scope = ted_local.resource_scope
        assert {
            "ted-bulk-xml-daily",
            "ted-bulk-xml-monthly",
            "ted-csv-historical",
        } <= scope.excluded_dataset_families
        assert scope.require_dataset_family

    def test_training_embeddings_and_redistribution_are_unchanged(self, catalog, ted) -> None:
        """§15. The acceptance grants none of these, and could not."""
        for profile in catalog.use_profiles:
            assert profile.model_training is False, profile.use_profile_id
            assert profile.embeddings is False, profile.use_profile_id
        local = next(p for p in catalog.use_profiles if p.use_profile_id == LOCAL_PROFILE)
        assert local.raw_redistribution is False
        assert local.raw_resale is False
        assert ted.review_for(LOCAL_PROFILE).assessments["redistribution"] is (
            PolicyAssessment.NOT_PERMITTED
        )

    def test_the_three_machine_conditions_are_still_satisfied(self, records) -> None:
        """The other three did not regress while this one stayed outstanding."""
        by_key = {r.condition_key: r for r in records}
        for key in ("ted-attribution", ROUTE_ONLY, MINIMISATION):
            assert by_key[key].result is ConditionVerificationResult.SATISFIED, key


# ================================================= no automation was added


class TestNoAutoAcceptancePathExists:
    def test_no_cli_flag_can_confirm_a_condition(self) -> None:
        """§9, §10. Not `--accept-risk`, not `--yes`, not `--force`, and no
        environment variable."""
        cli = (
            REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition" / "cli.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "--accept-risk",
            "--accept",
            "--yes",
            "--force",
            "--confirm",
            "human_confirmation",
        ):
            assert forbidden not in cli, forbidden

    def test_the_human_branch_can_only_reach_unknown(self) -> None:
        """§9. Asserted over the SOURCE of the branch, not by calling it.

        A behavioural test proves the branch returns UNKNOWN for the inputs it
        was given. This proves there is no input for which it returns anything
        else: inside the `if condition.verification is HUMAN_CONFIRMATION`
        block, the only `ConditionVerificationResult` member named is `UNKNOWN`.
        A future edit adding a conditional SATISFIED fails here even if no test
        exercises it.
        """
        import ast

        module = (
            REPO_ROOT
            / "services"
            / "acquisition"
            / "python"
            / "sros_acquisition"
            / "compliance"
            / "verification.py"
        )
        tree = ast.parse(module.read_text(encoding="utf-8"))

        branches = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.If) and "HUMAN_CONFIRMATION" in ast.dump(node.test)
        ]
        assert branches, "the human-confirmation branch was not found; has it been renamed?"

        for branch in branches:
            reached = {
                inner.attr
                for statement in branch.body
                for inner in ast.walk(statement)
                if isinstance(inner, ast.Attribute)
                and isinstance(inner.value, ast.Name)
                and inner.value.id == "ConditionVerificationResult"
            }
            assert reached <= {"UNKNOWN"}, reached

    def test_the_verifier_returns_unknown_for_any_human_condition(self, ted, ted_local) -> None:
        """Probed with the real source and the real configuration in hand, so a
        configuration-driven path to SATISFIED would show up here."""
        from sros_acquisition.compliance import verify_condition
        from sros_acquisition.registry.models import ReviewCondition

        probe = ReviewCondition(
            key="acceptance-probe",
            description="A probe asserting no configuration reaches a human condition.",
            verification=ConditionVerification.HUMAN_CONFIRMATION,
        )
        outcome = verify_condition(ted, LOCAL_PROFILE, probe, ted_local, {}, None)
        assert outcome.result is ConditionVerificationResult.UNKNOWN


# ==================================================== nothing was built or written


class TestNothingWasBuilt:
    def test_no_ted_collector_or_normalizer_exists(self) -> None:
        from sros_acquisition import IMPLEMENTED_COLLECTORS, IMPLEMENTED_NORMALIZERS

        assert "ted-eu" not in IMPLEMENTED_COLLECTORS
        assert "ted-eu" not in IMPLEMENTED_NORMALIZERS

    def test_no_ted_module_exists(self) -> None:
        """§20. Even though authorization readiness was the subject."""
        package = REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition"
        offenders = [
            p.relative_to(REPO_ROOT).as_posix()
            for p in package.rglob("*.py")
            if "ted" in p.stem.lower() or "sparql" in p.stem.lower()
        ]
        assert offenders == [], offenders


@needs_postgres
@pytest.mark.usefixtures("needs_recorded_acceptance")
class TestTheRegistryHoldsExactlyOneAcceptance:
    @staticmethod
    def _count(query: str, *params: object) -> int:
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(query, params or None).fetchone()
        return int(row[0]) if row else -1

    def test_exactly_one_verification_row_exists_and_no_duplicate(self) -> None:
        """§19. One acceptance, not two. Re-recording would put a second
        SATISFIED row in an append-only log and make one decision look like a
        withdrawal followed by a change of mind."""
        assert (
            self._count(
                "SELECT count(*) FROM registry.source_condition_verifications "
                "WHERE condition_key = %s",
                RESIDUAL,
            )
            == 1
        )
        assert (
            self._count(
                "SELECT count(*) FROM registry.source_condition_verifications "
                "WHERE condition_key = %s AND result = 'SATISFIED'",
                RESIDUAL,
            )
            == 1
        )

    def test_the_row_is_attached_to_the_right_source_profile_review_condition(self) -> None:
        """§3. Structural scope, asserted through the joins rather than trusted."""
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(
                """SELECT v.source_id, r.assessed_use_profile, r.review_version,
                          v.condition_key, v.result, v.verifier, v.verifier_version,
                          c.satisfied
                     FROM registry.source_condition_verifications v
                     JOIN registry.source_review_conditions c ON c.id = v.condition_id
                     JOIN registry.source_policy_reviews r ON r.id = c.review_id
                    WHERE v.condition_key = %s""",
                (RESIDUAL,),
            ).fetchone()
        assert row == (
            "ted-eu",
            LOCAL_PROFILE,
            2,
            RESIDUAL,
            "SATISFIED",
            "local-operator",
            "acknowledgement-v1",
            True,
        ), row

    def test_the_acknowledgement_is_stored_verbatim_in_the_row(self) -> None:
        """§5. The operator's words are the evidence, so the row carries them
        rather than a summary of them."""
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            reason = conn.execute(
                "SELECT reason FROM registry.source_condition_verifications "
                "WHERE condition_key = %s",
                (RESIDUAL,),
            ).fetchone()[0]
        assert "J’ai lu intégralement" in reason
        assert "review version 2, et pour rien d’autre" in reason
        assert "aucun avocat n’a validé" in reason

    def test_only_the_current_review_version_is_satisfied(self) -> None:
        """§14. v1 owns its own row and stays FALSE. A future v3 would too."""
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            rows = conn.execute(
                """SELECT r.review_version, c.satisfied
                     FROM registry.source_review_conditions c
                     JOIN registry.source_policy_reviews r ON r.id = c.review_id
                    WHERE c.source_id = 'ted-eu' AND c.condition_key = %s
                    ORDER BY r.review_version""",
                (RESIDUAL,),
            ).fetchall()
        assert rows == [(1, False), (2, True)], rows

    def test_the_database_still_refuses_a_boolean_with_no_evidence(self) -> None:
        """The trigger, asserted against a condition that has NO verification.

        The residual condition on review v2 now has evidence behind it, so
        setting its boolean would legitimately pass -- which is the trigger
        working, not a hole. Local review v1's row is the honest subject: same
        key, superseded review, nothing recorded against it.
        """
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            with pytest.raises(psycopg.errors.CheckViolation):
                conn.execute(
                    """UPDATE registry.source_review_conditions c
                          SET satisfied = TRUE
                         FROM registry.source_policy_reviews r
                        WHERE r.id = c.review_id AND c.source_id = 'ted-eu'
                          AND c.condition_key = %s AND r.review_version = 1""",
                    (RESIDUAL,),
                )
            conn.rollback()

    def test_reverification_preserves_the_acceptance(self) -> None:
        """**Inverted by Mission 1.15.6.2, exactly as this test predicted.**

        It asserted the opposite -- that `verify --apply` CLEARED a recorded
        acceptance -- and said in its own docstring that a future mission
        deciding how re-verification should treat human conditions would make it
        fail, and should invert it rather than delete it
        (`testing-strategy.md` §43). Mission 1.15.6.2 decided: a machine pass
        that cannot answer a human condition writes nothing for it, so an
        acceptance survives re-verification and only a person can withdraw one.

        Still asserted inside a ROLLED-BACK transaction: the property is about
        what the write path does, not about leaving the database changed.
        """
        import psycopg
        from sros_acquisition.compliance.repositories import record_verifications
        from sros_acquisition.registry import load_catalog

        catalog_ = load_catalog(REPO_ROOT / "docs" / "data" / "source-catalog-v1.json")
        source = next(entry for entry in catalog_ if entry.source_id == "ted-eu")
        config = load_compliance(DOCS / "source-compliance-v1.json")

        def satisfied(conn) -> bool:
            return conn.execute(
                """SELECT c.satisfied FROM registry.source_review_conditions c
                     JOIN registry.source_policy_reviews r ON r.id = c.review_id
                    WHERE c.source_id = 'ted-eu' AND c.condition_key = %s
                      AND r.review_version = 2""",
                (RESIDUAL,),
            ).fetchone()[0]

        with psycopg.connect(DATABASE_URL) as conn:
            assert satisfied(conn) is True
            try:
                with conn.transaction():
                    record_verifications(
                        conn, verify_source(source, LOCAL_PROFILE, config, environ={})
                    )
                    assert satisfied(conn) is True, (
                        "re-verification cleared a recorded human confirmation. A machine "
                        "pass must not revoke a decision nobody withdrew (Mission 1.15.6.2)"
                    )
                    raise _RollbackError
            except _RollbackError:
                pass
            assert satisfied(conn) is True, "the acceptance did not survive"

    def test_reverification_writes_no_row_for_the_human_condition(self) -> None:
        """§30. Idempotent, and silent about what it cannot answer.

        Preserving the boolean is half of it. The other half is that no row is
        written either: an append-only log that gained an UNKNOWN entry every
        time somebody ran the verifiers would bury the one decision that matters
        under a history of machines shrugging.
        """
        import psycopg
        from sros_acquisition.compliance.repositories import record_verifications
        from sros_acquisition.registry import load_catalog

        catalog_ = load_catalog(REPO_ROOT / "docs" / "data" / "source-catalog-v1.json")
        source = next(entry for entry in catalog_ if entry.source_id == "ted-eu")
        config = load_compliance(DOCS / "source-compliance-v1.json")

        def rows(conn) -> int:
            return conn.execute(
                "SELECT count(*) FROM registry.source_condition_verifications "
                "WHERE condition_key = %s",
                (RESIDUAL,),
            ).fetchone()[0]

        with psycopg.connect(DATABASE_URL) as conn:
            before = rows(conn)
            try:
                with conn.transaction():
                    report = record_verifications(
                        conn, verify_source(source, LOCAL_PROFILE, config, environ={})
                    )
                    assert rows(conn) == before, "a machine pass appended to the human log"
                    assert RESIDUAL in report.left_to_a_human
                    raise _RollbackError
            except _RollbackError:
                pass

    def test_each_review_version_owns_its_condition_rows(self) -> None:
        """§17, and the answer is fail-closed with no change needed.

        `registry.source_review_conditions` is keyed `(review_id, condition_key)`
        and the row id derives from the review version, so local v1 and v2 hold
        SEPARATE rows for the same key. A verification attached to v2 cannot
        satisfy a future v3, because v3 would get a fresh row with
        `satisfied = FALSE`.
        """
        import psycopg

        with psycopg.connect(DATABASE_URL) as conn:
            rows = conn.execute(
                """SELECT r.review_version, c.id
                     FROM registry.source_review_conditions c
                     JOIN registry.source_policy_reviews r ON r.id = c.review_id
                    WHERE c.source_id = 'ted-eu' AND c.condition_key = %s
                    ORDER BY r.review_version""",
                (RESIDUAL,),
            ).fetchall()
        versions = [r[0] for r in rows]
        identifiers = [r[1] for r in rows]
        assert versions == [1, 2], versions
        assert len(set(identifiers)) == 2, "v1 and v2 must not share a condition row"

    def test_no_ted_research_row_exists(self) -> None:
        """§21. TED rows stay 0 whatever this machine holds elsewhere."""
        assert (
            self._count("SELECT count(*) FROM acquisition.raw_records WHERE source_id = 'ted-eu'")
            == 0
        )
        assert (
            self._count(
                "SELECT count(*) FROM acquisition.normalized_records WHERE source_id = 'ted-eu'"
            )
            == 0
        )


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
