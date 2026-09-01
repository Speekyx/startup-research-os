"""Review versioning and conditional eligibility.

Mission 1.3 §35. Mission 1.0's suite proved the gate refuses; this one proves
the two things that mission could not yet express: that a re-review creates a
new version instead of overwriting the old one, and that
`APPROVED_WITH_CONDITIONS` does not quietly mean "a collector may run".

The test worth reading first is
`TestConditionalEligibility.test_an_approving_review_is_still_blocked_by_its_conditions`.
Three sources became approving in Mission 1.3 and none became collector-eligible.
That is the whole point of §24, and it is the one property a future change is
most likely to break by accident.

**Nothing here contacts a platform.** Reading official documentation was the
review; the tests read the recorded result of it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sros_acquisition.registry import (
    APPROVING_STATES,
    ReviewCondition,
    SourceRegistryError,
    evaluate_eligibility,
    resolve_retention,
)
from sros_acquisition.registry.repositories import read_eligibility
from sros_contracts import ConditionVerification, SourceApprovalState

from .conftest import LEGACY_PROFILE, needs_postgres

APPROVED_IN_1_3 = {"world-bank", "eurostat", "fred"}

# The thirteen candidates Mission 1.0 registered. Later rounds add sources whose
# first review is their own, so "the first review is Mission 1.0's" is a claim
# about these thirteen and not about the catalog.
REGISTERED_IN_1_0 = {
    "reddit",
    "hacker-news",
    "stack-exchange",
    "product-hunt",
    "github",
    "apple-app-store",
    "google-play",
    "youtube",
    "tiktok",
    "google-trends",
    "world-bank",
    "eurostat",
    "fred",
}


# ============================================================ review versioning


class TestReviewVersioning:
    def test_every_source_carries_its_review_history(self, catalog) -> None:
        """§27. Mission 1.0 concluded X, Mission 1.3 found Y. Both are readable,
        because overwriting the first would destroy the part a reader needs in
        order to trust the second."""
        for source in catalog:
            # >= 1, not >= 2. A candidate registered in this round has exactly
            # one review and that is correct; requiring two asserted the shape
            # of the Mission 1.3 catalog rather than the property. What must
            # hold is that versions are ordered, distinct, and never rewritten.
            assert source.review_history, source.source_id
            # Ordered and distinct WITHIN a profile: version 1 under a second
            # profile is a first review of a new question (Mission 1.15.5).
            for profile in source.use_profiles:
                versions = [
                    r.review_version
                    for r in source.review_history
                    if r.assessed_use_profile == profile
                ]
                assert versions == sorted(versions), (source.source_id, profile)
                assert len(set(versions)) == len(versions), (source.source_id, profile)

    def test_the_current_review_is_the_highest_version_of_its_profile(self, catalog) -> None:
        """Per PROFILE since Mission 1.15.5. `source.review` is the current
        LEGACY review specifically, and each profile's line has its own head."""
        for source in catalog:
            for profile, current in source.reviews_by_profile().items():
                assert current.review_version == max(
                    r.review_version
                    for r in source.review_history
                    if r.assessed_use_profile == profile
                ), (source.source_id, profile)
            if source.review is not None:
                assert source.review.assessed_use_profile == LEGACY_PROFILE

    def test_the_mission_1_0_review_is_recoverable_unchanged(self, catalog) -> None:
        """§46. The earlier verdict survives verbatim, including the states a
        later mission moved away from.

        Asserted for the sources Mission 1.0 actually registered. Requiring
        `reviewed_by == "mission-1.0"` of EVERY source was true of a catalog
        that had only ever had one round; it became false the moment a new
        candidate was registered by a later one, and it was never the property
        being tested.
        """
        by_id = {s.source_id: s for s in catalog}
        first = {s: by_id[s].review_history[0] for s in by_id}
        assert first["youtube"].approval_state is SourceApprovalState.REQUIRES_REVIEW
        assert first["github"].approval_state is SourceApprovalState.REQUIRES_REVIEW
        assert first["tiktok"].approval_state is SourceApprovalState.PROHIBITED
        for source_id in REGISTERED_IN_1_0:
            assert first[source_id].reviewed_by == "mission-1.0", source_id
        # And every source's first review is version 1, whoever wrote it.
        for source_id, review in first.items():
            assert review.review_version == 1, source_id

    def test_a_duplicate_review_version_is_refused(self) -> None:
        """Two reviews sharing a version cannot be told apart, and the later one
        would silently shadow the earlier."""
        import json
        import pathlib
        import tempfile

        from sros_acquisition.registry import load_catalog

        from .conftest import REPO_ROOT

        raw = json.loads(
            (REPO_ROOT / "docs/data/source-catalog-v1.json").read_text(encoding="utf-8")
        )
        raw["sources"][0]["reviews"][1]["review_version"] = raw["sources"][0]["reviews"][0][
            "review_version"
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(raw, f)
            path = pathlib.Path(f.name)
        with pytest.raises(SourceRegistryError, match=r"duplicate \(use profile, review_version\)"):
            load_catalog(path)
        path.unlink()

    def test_a_changed_verdict_rests_on_evidence_retrieved_for_it(self, catalog) -> None:
        """§27. A status change with no document behind it is an opinion. Every
        source whose state moved in Mission 1.3 cites at least one document
        retrieved for THAT review."""
        for source in catalog:
            previous, current = source.review_history[0], source.review_history[-1]
            if current.approval_state is previous.approval_state:
                continue
            assert current.evidence, (
                f"{source.source_id} changed from {previous.approval_state.value} to "
                f"{current.approval_state.value} with no evidence"
            )
            assert all(e.retrieved_at is not None for e in current.evidence)

    def test_every_current_review_records_retrieval_dates(self, catalog) -> None:
        for source in catalog:
            for item in source.review.evidence:
                assert item.retrieved_at is not None, source.source_id
                assert item.document_url.startswith("https://"), source.source_id


# ==================================================== conditions and eligibility


class TestConditionalEligibility:
    def test_every_approving_review_declares_conditions(self, catalog) -> None:
        """An approving review with no condition is an APPROVED in all but name.

        The membership check that used to sit here pinned the approving set to
        the three sources of Mission 1.3. That made the test fail when a review
        legitimately approved a fourth, which is a tripwire for catalog growth
        rather than an assertion about conditions.
        """
        for source in catalog:
            if source.review.approval_state in APPROVING_STATES:
                assert source.review.required_conditions, source.source_id

    def test_an_approving_review_is_still_blocked_by_its_conditions(self, catalog) -> None:
        """§24, and the property most likely to be broken by accident.

        Approving the review is not the same act as clearing the gate. Every
        blocker for these three is cleared EXCEPT their conditions, which is
        what makes this a real test rather than a tautology."""
        for source in catalog:
            if source.source_id not in APPROVED_IN_1_3:
                continue
            result = evaluate_eligibility(source, LEGACY_PROFILE)
            assert not result.eligible, source.source_id
            assert len(result.blocking_reasons) == 1, result.blocking_reasons
            assert result.blocking_reasons[0].startswith("review conditions not satisfied")

    def test_satisfying_every_condition_clears_the_gate(self, catalog) -> None:
        """The unblocked branch must be reachable, or the condition model would
        be a permanent refusal dressed as a check. Satisfaction is supplied by
        the caller here; in production it comes from the environment."""
        for source in catalog:
            if source.source_id not in APPROVED_IN_1_3:
                continue
            keys = frozenset(c.key for c in source.review.required_conditions)
            assert evaluate_eligibility(source, LEGACY_PROFILE, satisfied_conditions=keys).eligible

    def test_satisfying_only_some_conditions_does_not_clear_it(self, catalog) -> None:
        for source in catalog:
            if source.source_id not in APPROVED_IN_1_3:
                continue
            keys = [c.key for c in source.review.required_conditions]
            partial = frozenset(keys[:-1])
            result = evaluate_eligibility(source, LEGACY_PROFILE, satisfied_conditions=partial)
            assert not result.eligible
            assert keys[-1] in result.blocking_reasons[0]

    def test_conditions_of_a_non_approving_review_do_not_mask_the_state(self, catalog) -> None:
        """A RESTRICTED source is blocked by being RESTRICTED, not by an
        unsatisfied condition — otherwise satisfying the condition would appear
        to unblock it."""
        for source in catalog:
            if source.review.approval_state in APPROVING_STATES:
                continue
            reasons = evaluate_eligibility(source, LEGACY_PROFILE).blocking_reasons
            assert any(r.startswith("policy review for use profile") for r in reasons), (
                source.source_id
            )

    def test_a_mechanical_condition_must_name_what_it_checks(self) -> None:
        with pytest.raises(SourceRegistryError, match="must name what is checked"):
            ReviewCondition("k", "d", ConditionVerification.CONFIG_REFERENCE)

    def test_human_confirmation_may_name_nothing(self) -> None:
        """§24. A condition no machine can verify must say so rather than
        pretending. HUMAN_CONFIRMATION is a real answer."""
        condition = ReviewCondition("k", "d", ConditionVerification.HUMAN_CONFIRMATION)
        assert not condition.mechanically_verifiable

    def test_no_source_is_collector_eligible_from_the_catalog_alone(self, catalog) -> None:
        """§31, still true and now narrower.

        A catalog can never assert its own conditions satisfied, so evaluating
        the gate with no verification supplied must still refuse every source.
        That was Mission 1.3's whole outcome; since Mission 1.4 it is one of two
        views, and the environment view lives in
        `test_compliance.py::TestGates`."""
        assert [
            s.source_id for s in catalog if evaluate_eligibility(s, LEGACY_PROFILE).eligible
        ] == []


# ================================================================ carried rules


class TestPreviouslyEstablishedRules:
    def test_the_youtube_retention_override_survives(self, catalog) -> None:
        """§16, §35. Mission 1.0 recorded a 30-day cap; Mission 1.3 re-verified
        it against the current Developer Policies and it holds. It is retained
        even though YouTube is now PROHIBITED: a verified fact costs nothing to
        keep and removing it would lose it."""
        youtube = next(s for s in catalog if s.source_id == "youtube")
        assert youtube.retention_override is not None
        effective = resolve_retention(youtube.retention_override)
        assert effective.raw_days == 30
        assert effective.normalized_days == 30
        assert "30" in (effective.basis or "")

    def test_youtube_is_prohibited_on_current_evidence(self, catalog) -> None:
        youtube = next(s for s in catalog if s.source_id == "youtube")
        assert youtube.review.approval_state is SourceApprovalState.PROHIBITED
        assert any("aggregat" in e.summarized_finding.lower() for e in youtube.review.evidence)

    def test_tiktok_was_not_lowered(self, catalog) -> None:
        """§22. PROHIBITED stays PROHIBITED, and now cites the eligibility
        criteria that exclude a commercial SaaS rather than inferring them."""
        tiktok = next(s for s in catalog if s.source_id == "tiktok")
        assert tiktok.review.approval_state is SourceApprovalState.PROHIBITED
        assert tiktok.review.evidence

    def test_an_override_still_cannot_lengthen_retention(self, catalog) -> None:
        for source in catalog:
            if source.retention_override is None:
                continue
            effective = resolve_retention(source.retention_override)
            assert effective.raw_days <= 30
            assert effective.normalized_days <= 365

    def test_a_stale_review_fails_closed(self, catalog) -> None:
        """§35. An approval nobody has re-checked is a statement about the past
        presented as a statement about now."""
        source = next(s for s in catalog if s.source_id == "fred")
        keys = frozenset(c.key for c in source.review.required_conditions)
        future = datetime.now(UTC) + timedelta(days=3650)
        result = evaluate_eligibility(source, LEGACY_PROFILE, now=future, satisfied_conditions=keys)
        assert not result.eligible
        assert any("stale" in r for r in result.blocking_reasons)

    def test_no_per_source_reliability_weight_appeared(self, catalog) -> None:
        """§33. Governance answers 'may we use it'; aggregation answers 'how does
        this evidence contribute'. An APPROVED source is not a reliable one."""
        import json

        from .conftest import REPO_ROOT

        raw = json.loads(
            (REPO_ROOT / "docs/data/source-catalog-v1.json").read_text(encoding="utf-8")
        )
        blob = json.dumps(raw).lower()
        for term in ("reliability_weight", "source_weight", "evidence_weight", "trust_score"):
            assert term not in blob, term


# ================================================================ the database


@needs_postgres
class TestLoadedRegistry:
    def test_python_and_sql_still_agree(self, conn, catalog) -> None:
        """§29. Two implementations of one rule, compared rather than trusted.

        This caught a real defect while the mission was being written: the
        deterministic evidence row id did not include the review version, so a
        re-review citing the same URL re-parented the old row and left the new
        review with no evidence — which SQL then blocked on and Python did not.
        """
        from .conftest import recorded_satisfied_keys

        divergences = []
        for source in catalog:
            from_db = read_eligibility(conn, source.source_id, LEGACY_PROFILE)
            # The satisfaction the DATABASE holds, so the two implementations
            # are compared on the same inputs (Mission 1.4).
            from_python = evaluate_eligibility(
                source,
                LEGACY_PROFILE,
                satisfied_conditions=recorded_satisfied_keys(conn, source.source_id),
            )
            assert from_db is not None, source.source_id
            if from_db.eligible != from_python.eligible or set(from_db.blocking_reasons) != set(
                from_python.blocking_reasons
            ):
                divergences.append(source.source_id)
        assert divergences == []

    def test_the_history_is_persisted_and_superseded(self, conn, catalog) -> None:
        current = conn.execute(
            "SELECT count(*) FROM registry.source_policy_reviews WHERE superseded_at IS NULL"
        ).fetchone()[0]
        superseded = conn.execute(
            "SELECT count(*) FROM registry.source_policy_reviews WHERE superseded_at IS NOT NULL"
        ).fetchone()[0]
        total_reviews = sum(len(s.review_history) for s in catalog)
        # One current review per source; every other review in the history is
        # superseded and still present. Derived from the catalog rather than
        # asserted as a number, so the next registered source does not break it.
        # One current review per (source, PROFILE) since Mission 1.15.5, so a
        # source reviewed under two profiles contributes two.
        assert current == sum(len(s.use_profiles) for s in catalog)
        assert superseded == total_reviews - sum(len(s.use_profiles) for s in catalog)
        assert current + superseded == total_reviews

    def test_a_catalog_load_can_never_satisfy_a_condition(self, conn, catalog) -> None:
        """§24, §30. A catalog load declares conditions; it can never assert
        them satisfied. If it could, APPROVED_WITH_CONDITIONS would mean
        nothing.

        Asserted against the LOAD rather than against the current table, which
        is what this test did until Mission 1.4 made satisfaction reachable. The
        old form passed only while nothing had ever been verified, so it was
        really testing the state of one database rather than the behaviour of
        the loader."""
        from sros_acquisition.registry.repositories import load_catalog_into

        conn.execute("SAVEPOINT probe")
        conn.execute("UPDATE registry.source_review_conditions SET satisfied = FALSE")
        load_catalog_into(conn, catalog)
        total, unsatisfied = conn.execute(
            """SELECT count(*), count(*) FILTER (WHERE NOT satisfied)
                 FROM registry.source_review_conditions"""
        ).fetchone()
        assert total > 0
        assert total == unsatisfied
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_the_database_refuses_a_satisfied_condition_with_no_provenance(self, conn) -> None:
        """'Satisfied by nobody, at no time' is the shape an accidental UPDATE
        leaves behind.

        Two guards now stand here, and both are asserted because they catch
        different mistakes. Mission 1.4's trigger fires FIRST -- a BEFORE
        trigger runs ahead of a CHECK -- and refuses a satisfaction with no
        verification record at all. Mission 1.3's CHECK is what remains once a
        verification exists: it refuses the row that says satisfied and cannot
        say by whom."""
        # A probe condition, CREATED rather than borrowed. An earlier version
        # searched for a condition with no verification behind it, which worked
        # only until every condition had one; the row a test needs in a
        # particular state is the test's to build.
        conn.execute("SAVEPOINT probe")
        from .test_compliance import _unverified_condition

        condition_id = _unverified_condition(conn)
        with pytest.raises(Exception, match="no verification record"):
            conn.execute(
                """UPDATE registry.source_review_conditions
                      SET satisfied = TRUE, satisfied_at = now(), satisfied_by = 'probe'
                    WHERE id = %s""",
                (condition_id,),
            )
        conn.execute("ROLLBACK TO SAVEPOINT probe")

        # With a verification present, the outer guard is satisfied and the
        # inner one is reachable again.
        conn.execute("SAVEPOINT probe")
        condition_id = _unverified_condition(conn)
        conn.execute(
            """INSERT INTO registry.source_condition_verifications
                   (id, condition_id, source_id, condition_key, verifier, verifier_version,
                    result, reason, verified_at)
               SELECT gen_random_uuid(), id, source_id, condition_key, 'test-probe', '0',
                      'SATISFIED', 'a probe, rolled back', now()
                 FROM registry.source_review_conditions WHERE id = %s""",
            (condition_id,),
        )
        with pytest.raises(Exception, match="satisfaction_provenance"):
            conn.execute(
                """UPDATE registry.source_review_conditions
                      SET satisfied = TRUE, satisfied_at = NULL, satisfied_by = NULL
                    WHERE id = %s""",
                (condition_id,),
            )
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_nothing_is_collected_from_a_source_that_has_no_collector(self, conn) -> None:
        """The RULE, since Mission 1.5 made collection real.

        This assertion used to read `enabled == 0 and raw_records == 0`, which
        was true of every mission up to 1.4 and stopped being a property the
        moment one collector existed. Asserting it still would have been
        asserting a moment.

        What must hold forever is the ordering: nothing is enabled that has no
        collector, and nothing is collected from a source that is not enabled.
        Both hold whether the deployment has collected anything or not.
        """
        import sros_acquisition

        implemented = sros_acquisition.IMPLEMENTED_COLLECTORS

        enabled = {
            row[0]
            for row in conn.execute(
                "SELECT id FROM registry.sources WHERE collector_enabled"
            ).fetchall()
        }
        assert enabled <= implemented, f"enabled with no collector: {enabled - implemented}"

        collected = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source_id FROM acquisition.raw_records"
            ).fetchall()
        }
        assert collected <= implemented, f"collected with no collector: {collected - implemented}"

        # Deliberately NOT `collected <= enabled`. Disabling a collector does
        # not retroactively make what it already collected illegitimate, and an
        # assertion that said so would forbid ever turning one off.

        # NARROWED in Mission 1.6, not deleted. This read
        # `normalized_records == 0`, which was true of every mission until one
        # normalized something -- the same stale absolute the two lines above
        # replaced one mission earlier, in the same test.
        #
        # The rule that survives is the ordering, one link further along:
        # nothing is normalized that no normalizer serves, and nothing is
        # normalized that was not collected first.
        normalizable = sros_acquisition.IMPLEMENTED_NORMALIZERS
        normalized = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source_id FROM acquisition.normalized_records"
            ).fetchall()
        }
        assert normalized <= normalizable, (
            f"normalized with no normalizer: {normalized - normalizable}"
        )
        assert normalized <= collected, f"normalized but never collected: {normalized - collected}"

    def test_the_sql_view_reports_condition_counts(self, conn, catalog) -> None:
        """The view's counts must match the condition table exactly.

        Compared against the table rather than asserted as a fixed number:
        satisfaction is environment state now, and a test that hard-coded
        "all unsatisfied" would pass only on a database nobody had verified."""
        # SCOPED BY PROFILE on both sides since Mission 1.17. The view has one
        # row per (source, profile) and always did; the subqueries counted every
        # current review of the source, which was the same number for as long as
        # only one profile had reviews. Adding local-profile reviews made
        # eurostat report 3 in the view and 6 in the subquery -- a real
        # disagreement between the test and the view, caused by the test.
        rows = conn.execute(
            """SELECT e.source_id, e.condition_count, e.unsatisfied_condition_count,
                      (SELECT count(*) FROM registry.source_review_conditions c
                        JOIN registry.source_policy_reviews r ON r.id = c.review_id
                       WHERE c.source_id = e.source_id AND r.superseded_at IS NULL
                         AND r.assessed_use_profile = e.use_profile_id),
                      (SELECT count(*) FROM registry.source_review_conditions c
                        JOIN registry.source_policy_reviews r ON r.id = c.review_id
                       WHERE c.source_id = e.source_id AND r.superseded_at IS NULL
                         AND r.assessed_use_profile = e.use_profile_id
                         AND NOT c.satisfied)
                 FROM registry.source_eligibility e
                WHERE e.condition_count > 0 ORDER BY e.source_id, e.use_profile_id"""
        ).fetchall()
        # Compared against the CATALOG rather than a frozen set of source ids:
        # which sources carry conditions is a fact the catalog owns, and pinning
        # it here made this test fail whenever a later review approved a source
        # -- a growth tripwire wearing the clothes of a count assertion.
        expected = {s.source_id for s in catalog if s.review and s.review.required_conditions}
        assert expected, "no source carries a condition; this test would prove nothing"
        # ted-eu joined this set when it gained required conditions under
        # local-private-research-v1 (Mission 1.15.5).
        assert {r[0] for r in rows} == expected | {"ted-eu"}
        for source_id, total, unsatisfied, actual_total, actual_unsatisfied in rows:
            assert total == actual_total, source_id
            assert unsatisfied == actual_unsatisfied, source_id


class TestCollectionStaysInsideItsBoundary:
    """Mission 1.3 asserted that no collector and no network client existed.

    Mission 1.5 built one, so those assertions were NARROWED rather than
    deleted -- the same move Mission 1.2 made with the D-03 aggregation guard
    and Mission 1.4 with the enablement guard. Naming the one file that may
    reach a network, and the one package that may hold a collector, is a
    stronger statement than forbidding both everywhere: it says where the
    boundary is, not merely that nothing has crossed it yet.

    The full structural suite lives in `test_collector_conformance.py`; these
    are the two properties Mission 1.3 was protecting, restated.
    """

    def test_governance_modules_still_fetch_nothing(self) -> None:
        """The registry decides whether a source may be collected from. A
        network client there would put the decision and its execution in one
        place."""
        import pathlib as _pathlib

        import sros_acquisition

        root = _pathlib.Path(sros_acquisition.__file__).parent
        forbidden = (
            "import requests",
            "import httpx",
            "import aiohttp",
            "import urllib.request",
            "from urllib.request",
            "playwright",
            "selenium",
        )
        for package in ("registry", "compliance"):
            for path in sorted((root / package).rglob("*.py")):
                text = path.read_text(encoding="utf-8")
                for token in forbidden:
                    assert token not in text, f"{package}/{path.name} imports {token!r}"

    def test_exactly_one_collector_exists_and_it_is_world_bank(self) -> None:
        """Eurostat is collector-eligible and has no collector. Eligibility says
        one may be built; this says which ones were.

        Mission 1.9.3 added `gdelt`, after Mission 1.9.2 authorised the resources
        it collects. Mission 1.15.7 added `ted-eu` the same way round. Eurostat is
        still eligible with neither a resource nor a collector, which is the
        pairing that keeps the facts apart.
        """
        import sros_acquisition

        assert (
            frozenset({"world-bank", "gdelt", "ted-eu"}) == sros_acquisition.IMPLEMENTED_COLLECTORS
        )
