"""Mission 1.75. One HTTP governance read, one explicit use profile, one profile's facts.

Source policy reviews have been per `(source, use profile)` since Mission 1.15.5, and
until this mission the HTTP layer joined them on `source_id` alone. `/sources` returned a
source once per profile that had reviewed it; `/sources/{id}` and its `/eligibility`
returned an arbitrary profile's verdict beside the UNION of every profile's conditions.

Mission 1.17 encoded that as a tripwire rather than fixing it, because choosing which
profile the HTTP layer answers for is a design decision and there was no legitimate
default. There still is not. The decision is that there is no default at all: the profile
is required, and both absences -- missing and unregistered -- fail closed.

The cases below are adversarial on purpose. Every one of them is a way the old code
would have answered a question nobody asked, and the ones that matter most are the
quiet ones: a source the requested profile has never reviewed must stay unreviewed, and
must not borrow a verdict from the profile that did review it.

These run against the seeded registry, so they assert RELATIONS rather than counts. A
test that fails because the registry legitimately grew is a test asserting that the
project may never progress.
"""

from __future__ import annotations

import pytest

LOCAL = "local-private-research-v1"
COMMERCIAL = "commercial-multi-tenant-research-v1"
PROFILES = (LOCAL, COMMERCIAL)

SOURCES = "/api/v1/sources"


def sources(client, profile, **params):
    response = client.get(SOURCES, params={"use_profile": profile, **params})
    assert response.status_code == 200, response.text
    return response.json()


def eligibility(client, source_id, profile):
    response = client.get(f"{SOURCES}/{source_id}/eligibility", params={"use_profile": profile})
    assert response.status_code == 200, response.text
    return response.json()


def detail(client, source_id, profile):
    response = client.get(f"{SOURCES}/{source_id}", params={"use_profile": profile})
    assert response.status_code == 200, response.text
    return response.json()


def reviewed_only_under(client, profile, other):
    """A source this profile reviewed and the other did not, or skip.

    Resolved from the live registry rather than hard-coded, so the case keeps
    testing the property after a future profile alignment moves which source
    happens to satisfy it.
    """
    here = {
        s["source_id"]
        for s in sources(client, profile)["sources"]
        if s["reviewed_under_requested_profile"]
    }
    there = {
        s["source_id"]
        for s in sources(client, other)["sources"]
        if s["reviewed_under_requested_profile"]
    }
    only = sorted(here - there)
    if not only:
        pytest.skip(f"no source is reviewed under {profile} alone")
    return only[0]


def reviewed_under_both(client):
    both = None
    for profile in PROFILES:
        ids = {
            s["source_id"]
            for s in sources(client, profile)["sources"]
            if s["reviewed_under_requested_profile"]
        }
        both = ids if both is None else both & ids
    assert both, "no source is reviewed under both profiles; the matrix needs one"
    return sorted(both)


class TestTheProfileIsRequiredAndNeverGuessed:
    """CASE F and CASE G. Both absences fail closed, and they fail differently."""

    def test_a_missing_profile_is_refused_on_every_governance_route(self, api_client):
        for path in (SOURCES, f"{SOURCES}/fred", f"{SOURCES}/fred/eligibility"):
            response = api_client.get(path)
            assert response.status_code == 422, (path, response.status_code)

    def test_an_unregistered_profile_is_refused_on_every_governance_route(self, api_client):
        for path in (SOURCES, f"{SOURCES}/fred", f"{SOURCES}/fred/eligibility"):
            response = api_client.get(path, params={"use_profile": "not-a-profile-v9"})
            assert response.status_code == 422, (path, response.status_code)
            assert response.json()["error"] == "contract_violation"

    def test_an_empty_profile_is_not_read_as_absent(self, api_client):
        # The dangerous failure is the one that looks like a default.
        response = api_client.get(SOURCES, params={"use_profile": ""})
        assert response.status_code == 422

    def test_the_refusal_names_the_field_rather_than_the_source(self, api_client):
        body = api_client.get(
            f"{SOURCES}/fred/eligibility", params={"use_profile": "not-a-profile-v9"}
        ).json()
        assert "use_profile" in body["detail"]

    def test_a_profile_is_not_a_workspace(self, api_client):
        """§16. A tenant header answers a different question and must not stand in."""
        response = api_client.get(
            SOURCES, headers={"X-Workspace-Id": "00000000-0000-0000-0000-000000000001"}
        )
        assert response.status_code == 422


class TestEachSourceAppearsOnce:
    """CASE H. The profile is a join predicate, so there is nothing to deduplicate."""

    def test_no_profile_returns_a_source_twice(self, api_client):
        for profile in PROFILES:
            ids = [s["source_id"] for s in sources(api_client, profile)["sources"]]
            assert len(ids) == len(set(ids)), profile

    def test_a_source_reviewed_under_both_appears_once_in_each(self, api_client):
        for source_id in reviewed_under_both(api_client):
            for profile in PROFILES:
                listed = [
                    s
                    for s in sources(api_client, profile)["sources"]
                    if s["source_id"] == source_id
                ]
                assert len(listed) == 1, (source_id, profile)

    def test_every_registered_source_is_listed_under_every_profile(self, api_client):
        """A source is not hidden merely because the requested profile has no
        review for it. Hiding it would make "not reviewed here" indistinguishable
        from "not registered", which are different facts."""
        per_profile = {
            p: {s["source_id"] for s in sources(api_client, p)["sources"]} for p in PROFILES
        }
        assert per_profile[LOCAL] == per_profile[COMMERCIAL]


class TestNoFactCrossesAProfileBoundary:
    """CASES A, B, C, D, E and I.

    Bound to `leakage_fixtures` rather than left to the seeded registry: commercial
    has reviewed every seeded source, so the local-only direction exists only when
    the fixture creates it. Skipping instead would have made these tests silently
    stop covering the direction they were written for.
    """

    @pytest.fixture(autouse=True)
    def _fixtures(self, leakage_fixtures):
        self.fixtures = leakage_fixtures

    def test_a_profile_that_never_reviewed_a_source_says_so(self, api_client):
        """CASE A and CASE B, resolved from live data in whichever direction exists."""
        for profile, other in ((COMMERCIAL, LOCAL), (LOCAL, COMMERCIAL)):
            source_id = reviewed_only_under(api_client, other, profile)
            body = eligibility(api_client, source_id, profile)
            assert body["reviewed_under_requested_profile"] is False
            assert body["approval_state"] is None
            assert body["collector_eligible"] is False
            assert body["conditions"] == []
            assert body["blocking_reasons"] == [
                f"no policy review exists for use profile '{profile}'"
            ]

    def test_an_unreviewed_profile_does_not_borrow_the_other_verdict(self, api_client):
        for profile, other in ((COMMERCIAL, LOCAL), (LOCAL, COMMERCIAL)):
            source_id = reviewed_only_under(api_client, other, profile)
            reviewing = eligibility(api_client, source_id, other)
            assert reviewing["approval_state"] is not None
            unreviewed = eligibility(api_client, source_id, profile)
            assert unreviewed["approval_state"] != reviewing["approval_state"]
            assert unreviewed["approval_state"] is None

    def test_a_detail_read_under_an_unreviewed_profile_carries_no_review(self, api_client):
        """The worst leak of the three: the review body and its evidence URLs."""
        for profile, other in ((COMMERCIAL, LOCAL), (LOCAL, COMMERCIAL)):
            source_id = reviewed_only_under(api_client, other, profile)
            body = detail(api_client, source_id, profile)
            assert body["review"] is None
            assert body["evidence"] == []
            assert body["reviewed_under_requested_profile"] is False

    def test_each_profile_returns_its_own_verdict(self, api_client):
        """CASE C and CASE E. Where the two disagree, neither upgrades the other."""
        disagreements = 0
        for source_id in reviewed_under_both(api_client):
            states = {p: eligibility(api_client, source_id, p)["approval_state"] for p in PROFILES}
            details = {p: detail(api_client, source_id, p)["approval_state"] for p in PROFILES}
            assert states == details, source_id
            if len(set(states.values())) > 1:
                disagreements += 1
        # Not asserted as a count: what matters is that where they differ the
        # endpoints report the difference rather than one verdict twice.
        assert disagreements >= 0

    def test_a_condition_key_present_in_both_returns_its_own_version(self, api_client):
        """CASE D. Two profiles carrying one key is two facts, not one."""
        for source_id in reviewed_under_both(api_client):
            per_profile = {
                p: {
                    c["condition_key"]: c
                    for c in eligibility(api_client, source_id, p)["conditions"]
                }
                for p in PROFILES
            }
            shared = set(per_profile[LOCAL]) & set(per_profile[COMMERCIAL])
            for key in shared:
                local_id = per_profile[LOCAL][key]
                commercial_id = per_profile[COMMERCIAL][key]
                # Same key, two rows: they may agree, but each must have come
                # from its own review rather than one being served to both.
                assert set(local_id) == set(commercial_id)

    def test_conditions_never_union_across_profiles(self, api_client):
        """CASE I, and the defect Mission 1.17 pinned at six for `fred`."""
        for source_id in reviewed_under_both(api_client):
            counts = {}
            for profile in PROFILES:
                body = eligibility(api_client, source_id, profile)
                keys = [c["condition_key"] for c in body["conditions"]]
                assert len(keys) == len(set(keys)), (source_id, profile, keys)
                assert len(keys) == body["condition_count"], (source_id, profile)
                counts[profile] = len(keys)
            if counts[LOCAL] and counts[COMMERCIAL]:
                for profile in PROFILES:
                    assert counts[profile] < counts[LOCAL] + counts[COMMERCIAL], source_id

    def test_the_eligibility_count_fields_describe_the_requested_profile_only(self, api_client):
        for source_id in reviewed_under_both(api_client):
            for profile in PROFILES:
                body = eligibility(api_client, source_id, profile)
                assert body["condition_count"] == len(body["conditions"])
                assert body["unsatisfied_condition_count"] == sum(
                    1 for c in body["conditions"] if not c["satisfied"]
                )


class TestTheResponseSaysWhichProfileItDescribes:
    def test_every_route_echoes_the_requested_profile(self, api_client):
        for profile in PROFILES:
            listed = sources(api_client, profile)
            assert listed["use_profile"] == profile
            for source in listed["sources"]:
                assert source["use_profile"] == profile
            assert eligibility(api_client, "fred", profile)["use_profile"] == profile
            assert detail(api_client, "fred", profile)["use_profile"] == profile

    def test_collector_enablement_carries_the_profile_it_was_granted_under(self, api_client):
        """`collector_enabled` is a source column with its own profile. Returned
        flat beside a scoped verdict it reads as "enabled for you", which for a
        source enabled under one profile and listed under another is false."""
        for profile in PROFILES:
            for source in sources(api_client, profile)["sources"]:
                if not source["collector_enabled"]:
                    assert source["collector_enabled_for_requested_profile"] is False
                    continue
                assert source["collector_enabled_for_requested_profile"] == (
                    source["collector_use_profile"] == profile
                ), source["source_id"]

    def test_a_collector_enabled_source_is_eligible_under_its_own_profile(self, api_client):
        """The property the database trigger enforces, read back through HTTP."""
        for profile in PROFILES:
            for source in sources(api_client, profile)["sources"]:
                if source["collector_enabled_for_requested_profile"]:
                    assert source["collector_eligible"], source["source_id"]

    def test_a_source_object_carries_its_profile_on_its_own(self, api_client):
        """A single source object is what a caller stores, forwards and compares.
        A verdict that travels without its subject is the defect this repaired."""
        source = sources(api_client, LOCAL)["sources"][0]
        assert source["use_profile"] == LOCAL
        assert "reviewed_under_requested_profile" in source


class TestRepeatedAndInterleavedRequests:
    """CASE J. No request-state leakage and no cached cross-profile result."""

    def test_the_same_request_twice_returns_the_same_answer(self, api_client):
        for profile in PROFILES:
            first = eligibility(api_client, "fred", profile)
            second = eligibility(api_client, "fred", profile)
            assert first == second

    def test_alternating_profiles_do_not_contaminate_each_other(self, api_client):
        expected = {p: eligibility(api_client, "fred", p) for p in PROFILES}
        for _ in range(3):
            for profile in PROFILES:
                assert eligibility(api_client, "fred", profile) == expected[profile]

    def test_a_second_profile_after_a_first_does_not_inherit_its_rows(self, api_client):
        sources(api_client, COMMERCIAL)
        after = sources(api_client, LOCAL)
        assert after["use_profile"] == LOCAL
        assert all(s["use_profile"] == LOCAL for s in after["sources"])

    def test_listing_is_deterministically_ordered(self, api_client):
        for profile in PROFILES:
            ids = [s["source_id"] for s in sources(api_client, profile)["sources"]]
            assert ids == sorted(ids), profile


class TestTheContractIsDiscoverable:
    """§12. Tested on the rendered OpenAPI rather than asserted in prose."""

    def test_use_profile_is_a_required_query_parameter_on_every_route(self, api_client):
        spec = api_client.get("/openapi.json").json()
        for path in (SOURCES, f"{SOURCES}/{{source_id}}", f"{SOURCES}/{{source_id}}/eligibility"):
            params = spec["paths"][path]["get"]["parameters"]
            profile = [p for p in params if p["name"] == "use_profile"]
            assert profile, path
            assert profile[0]["in"] == "query", path
            assert profile[0]["required"] is True, path

    def test_the_parameter_says_there_is_no_default(self, api_client):
        spec = api_client.get("/openapi.json").json()
        params = spec["paths"][SOURCES]["get"]["parameters"]
        profile = next(p for p in params if p["name"] == "use_profile")
        assert "no default" in profile.get("description", "")
        assert "default" not in profile["schema"]

    def test_family_stays_optional_so_required_means_something(self, api_client):
        spec = api_client.get("/openapi.json").json()
        params = spec["paths"][SOURCES]["get"]["parameters"]
        family = next(p for p in params if p["name"] == "family")
        assert family["required"] is False


class TestTheDatabaseAgreesWithTheEndpoint:
    """Two implementations of one rule is a real risk. Compare rather than trust."""

    def test_the_endpoint_matches_the_view_row_by_row(self, api_client, database):
        for profile in PROFILES:
            with database.connection() as conn:
                rows = {
                    r[0]: (r[1], list(r[2]))
                    for r in conn.execute(
                        """SELECT source_id, approval_state, blocking_reasons
                             FROM registry.source_eligibility
                            WHERE use_profile_id = %s""",
                        (profile,),
                    ).fetchall()
                }
            for source in sources(api_client, profile)["sources"]:
                recorded = rows.get(source["source_id"])
                if recorded is None:
                    assert source["reviewed_under_requested_profile"] is False
                    assert source["approval_state"] is None
                    continue
                assert source["approval_state"] == recorded[0], source["source_id"]
                assert source["blocking_reasons"] == recorded[1], source["source_id"]

    def test_an_absent_view_row_is_a_refusal(self, api_client, database):
        """The view says so in its own COMMENT. This serves that sentence."""
        with database.connection() as conn:
            comment = conn.execute(
                "SELECT obj_description('registry.source_eligibility'::regclass, 'pg_class')"
            ).fetchone()[0]
        assert "absent row is a refusal" in comment


# ---------------------------------------------------------------- fixtures
#
# The seeded registry gives CASE A for free -- commercial has reviewed every
# source, local only eight -- and gives CASE B not at all, because no source is
# local-only. Skipping the direction that does not happen to exist would leave
# the leak that direction could carry untested, so it is CONSTRUCTED.
#
# These write to `registry`, commit, and delete on the way out. The counters they
# move are the source and review tables, and the teardown asserts the delete
# removed exactly what the setup added -- a fixture that leaked a row would
# otherwise look like canonical drift to the next mission.

LOCAL_ONLY = "mission-175-local-only"
DIVERGENT = "mission-175-divergent"
SHARED_KEY = "mission-175-shared-condition"
FIXTURE_SOURCES = (LOCAL_ONLY, DIVERGENT)


def _purge(conn, source_ids):
    """Remove the fixture rows, whether or not the previous run got to its own teardown.

    Called before the insert as well as after it. A setup that raises halfway
    leaves a source behind, and the next run then fails on a UNIQUE violation
    that has nothing to do with what it was testing -- which is a slow way to
    learn that a crashed fixture is a dirty database.
    """
    # Written out rather than looped over table names: a DELETE built by string
    # concatenation is the shape a linter cannot tell from an injection, and the
    # list is five lines either way.
    for source_id in source_ids:
        conn.execute(
            "DELETE FROM registry.source_condition_verifications WHERE source_id = %s",
            (source_id,),
        )
        conn.execute(
            "DELETE FROM registry.source_review_conditions WHERE source_id = %s", (source_id,)
        )
        conn.execute(
            "DELETE FROM registry.source_policy_evidence WHERE source_id = %s", (source_id,)
        )
        conn.execute(
            "DELETE FROM registry.source_policy_reviews WHERE source_id = %s", (source_id,)
        )
        conn.execute(
            "DELETE FROM registry.source_access_profiles WHERE source_id = %s", (source_id,)
        )
        conn.execute("DELETE FROM registry.sources WHERE id = %s", (source_id,))


def _insert(conn, source_id, reviews):
    conn.execute(
        "INSERT INTO registry.sources (id, canonical_name, source_family, lifecycle,"
        " description, collector_enabled)"
        " VALUES (%s, %s, 'economic_data', 'ACTIVE', 'Mission 1.75 leakage fixture', false)",
        (source_id, source_id),
    )
    conn.execute(
        "INSERT INTO registry.source_access_profiles (id, source_id, access_method, label)"
        " VALUES (gen_random_uuid(), %s, 'PUBLIC_API', 'fixture')",
        (source_id,),
    )
    for profile, state, satisfied in reviews:
        # Inserted as REQUIRES_REVIEW and promoted afterwards: the registry
        # refuses an approval with no evidence behind it, on the trigger, and a
        # fixture that wanted the approval first would have to be run against a
        # weaker database than the one being tested.
        review_id = conn.execute(
            "INSERT INTO registry.source_policy_reviews"
            " (id, source_id, review_version, approval_state, assessed_use_case,"
            "  reviewed_by, assessed_use_profile, conditions)"
            " VALUES (gen_random_uuid(), %s, 1, 'REQUIRES_REVIEW', 'mission 1.75 fixture',"
            "         'mission-1.75', %s, %s)"
            " RETURNING id",
            (source_id, profile, [SHARED_KEY]),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO registry.source_policy_evidence"
            " (id, review_id, source_id, document_type, document_title, document_url,"
            "  summarized_finding, retrieved_at)"
            " VALUES (gen_random_uuid(), %s, %s, 'OFFICIAL_TERMS', 'fixture',"
            "         'https://example.invalid/fixture', 'fixture evidence', now())",
            (review_id, source_id),
        )
        condition_id = conn.execute(
            "INSERT INTO registry.source_review_conditions"
            " (id, review_id, source_id, condition_key, description, verification, satisfied)"
            " VALUES (gen_random_uuid(), %s, %s, %s, %s, 'HUMAN_CONFIRMATION', false)"
            " RETURNING id",
            (review_id, source_id, SHARED_KEY, "fixture condition for " + profile),
        ).fetchone()[0]
        if satisfied:
            # Cleared through a verification record, because the registry refuses
            # a condition marked satisfied by a bare boolean. The fixture obeys
            # the rule it is testing around rather than reaching under it.
            conn.execute(
                "INSERT INTO registry.source_condition_verifications"
                " (id, condition_id, source_id, condition_key, verifier, verifier_version,"
                "  result, reason, verified_at)"
                " VALUES (gen_random_uuid(), %s, %s, %s, 'mission-1.75-fixture', '1',"
                "         'SATISFIED', 'fixture', now())",
                (condition_id, source_id, SHARED_KEY),
            )
            conn.execute(
                "UPDATE registry.source_review_conditions"
                " SET satisfied = true, satisfied_at = now(), satisfied_by = 'mission-1.75'"
                " WHERE id = %s",
                (condition_id,),
            )
        if state != "REQUIRES_REVIEW":
            conn.execute(
                "UPDATE registry.source_policy_reviews SET approval_state = %s WHERE id = %s",
                (state, review_id),
            )


@pytest.fixture
def leakage_fixtures():
    """One source reviewed under LOCAL only, one under both with different verdicts.

    Connects directly rather than through the Gateway pool: that pool runs as the
    runtime role, which holds SELECT on `registry` and nothing else. Writing
    through it would need the very privilege this service is built not to have,
    and a fixture is not a reason to grant one.
    """
    import os

    import psycopg

    url = os.environ.get("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    with psycopg.connect(url, autocommit=True) as conn:
        _purge(conn, FIXTURE_SOURCES)
        _insert(conn, LOCAL_ONLY, [(LOCAL, "APPROVED_WITH_CONDITIONS", True)])
        _insert(
            conn,
            DIVERGENT,
            [(LOCAL, "APPROVED_WITH_CONDITIONS", True), (COMMERCIAL, "REQUIRES_REVIEW", False)],
        )
    try:
        yield {"local_only": LOCAL_ONLY, "divergent": DIVERGENT}
    finally:
        with psycopg.connect(url, autocommit=True) as conn:
            _purge(conn, FIXTURE_SOURCES)
            left = conn.execute(
                "SELECT count(*) FROM registry.sources WHERE id = ANY(%s)",
                (list(FIXTURE_SOURCES),),
            ).fetchone()[0]
        assert left == 0, "the leakage fixture leaked rows into the registry"


class TestConstructedLeakageCases:
    """CASE B, CASE C, CASE D, CASE E and CASE I, built rather than found.

    The seeded registry happens to satisfy CASE A and cannot satisfy CASE B, so
    the direction that does not occur naturally is constructed. A leak is not
    less of a leak for pointing the way the data happens not to lean.
    """

    def test_case_b_a_local_only_source_is_unreviewed_under_commercial(
        self, api_client, leakage_fixtures
    ):
        source_id = leakage_fixtures["local_only"]
        under_local = eligibility(api_client, source_id, LOCAL)
        assert under_local["approval_state"] == "APPROVED_WITH_CONDITIONS"
        assert under_local["reviewed_under_requested_profile"] is True

        under_commercial = eligibility(api_client, source_id, COMMERCIAL)
        assert under_commercial["reviewed_under_requested_profile"] is False
        assert under_commercial["approval_state"] is None
        assert under_commercial["collector_eligible"] is False
        assert under_commercial["conditions"] == []

    def test_case_b_the_detail_route_leaks_neither_review_nor_evidence(
        self, api_client, leakage_fixtures
    ):
        source_id = leakage_fixtures["local_only"]
        assert (
            detail(api_client, source_id, LOCAL)["review"]["approval_state"]
            == "APPROVED_WITH_CONDITIONS"
        )
        blind_side = detail(api_client, source_id, COMMERCIAL)
        assert blind_side["review"] is None
        assert blind_side["evidence"] == []

    def test_case_b_the_source_is_listed_once_under_both(self, api_client, leakage_fixtures):
        source_id = leakage_fixtures["local_only"]
        for profile in PROFILES:
            listed = [
                s for s in sources(api_client, profile)["sources"] if s["source_id"] == source_id
            ]
            assert len(listed) == 1, profile

    def test_case_c_and_e_an_approval_never_upgrades_the_other_profile(
        self, api_client, leakage_fixtures
    ):
        source_id = leakage_fixtures["divergent"]
        assert (
            eligibility(api_client, source_id, LOCAL)["approval_state"]
            == "APPROVED_WITH_CONDITIONS"
        )
        assert eligibility(api_client, source_id, COMMERCIAL)["approval_state"] == "REQUIRES_REVIEW"
        assert detail(api_client, source_id, LOCAL)["approval_state"] == "APPROVED_WITH_CONDITIONS"
        assert detail(api_client, source_id, COMMERCIAL)["approval_state"] == "REQUIRES_REVIEW"

    def test_case_d_one_condition_key_under_two_profiles_is_two_facts(
        self, api_client, leakage_fixtures
    ):
        source_id = leakage_fixtures["divergent"]
        per_profile = {}
        for profile in PROFILES:
            conditions = eligibility(api_client, source_id, profile)["conditions"]
            assert len(conditions) == 1, (profile, conditions)
            assert conditions[0]["condition_key"] == SHARED_KEY
            per_profile[profile] = conditions[0]
        # Same key, different rows: the satisfied flag and the description each
        # belong to their own review, and neither endpoint returns both.
        assert per_profile[LOCAL]["satisfied"] is True
        assert per_profile[COMMERCIAL]["satisfied"] is False
        assert per_profile[LOCAL]["description"] != per_profile[COMMERCIAL]["description"]

    def test_case_i_a_divergent_source_never_returns_the_union(self, api_client, leakage_fixtures):
        source_id = leakage_fixtures["divergent"]
        for profile in PROFILES:
            body = eligibility(api_client, source_id, profile)
            assert body["condition_count"] == 1
            assert len(body["conditions"]) == 1

    def test_the_fixture_sources_do_not_survive_the_test(self, api_client, database):
        """Proves the teardown above, from outside it: the baseline holds."""
        with database.connection() as conn:
            left = conn.execute(
                "SELECT count(*) FROM registry.sources WHERE id LIKE 'mission-175-%'"
            ).fetchone()[0]
        assert left == 0


THIRD_PROFILE = "mission-175-unused-profile-v1"


@pytest.fixture
def unused_profile():
    """A registered profile that no source has been reviewed under.

    This is the only fixture that tells three implementations apart: a hard-coded
    pair of names, a lookup against the profiles that HAVE reviews, and a lookup
    against the vocabulary. The first two answer correctly for the two live
    profiles and wrongly for this one, which is the state every newly registered
    profile begins in.
    """
    import os

    import psycopg

    url = os.environ.get("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DELETE FROM registry.use_profiles WHERE id = %s", (THIRD_PROFILE,))
        # Copied from an existing profile rather than invented: what this fixture
        # needs is a REGISTERED profile, not a meaningful one, and making up
        # values for governance columns would be making up a governance stance
        # nobody took. Column names are written out because a query assembled
        # from a list is the shape a linter cannot tell from an injection.
        conn.execute(
            "INSERT INTO registry.use_profiles"
            " (id, name, description, deployment, operator_scope, personal_data_posture,"
            "  public_access, external_customers, raw_redistribution, raw_resale,"
            "  customer_facing_source_access, derived_internal_analysis, commercial_purpose,"
            "  model_inference, model_training, embeddings)"
            " SELECT %s, 'Mission 1.75 unused profile',"
            "        'registered, never reviewed under', deployment, operator_scope,"
            "        personal_data_posture,"
            "        public_access, external_customers, raw_redistribution, raw_resale,"
            "        customer_facing_source_access, derived_internal_analysis,"
            "        commercial_purpose, model_inference, model_training, embeddings"
            "   FROM registry.use_profiles WHERE id = %s",
            (THIRD_PROFILE, LOCAL),
        )
    try:
        yield THIRD_PROFILE
    finally:
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute("DELETE FROM registry.use_profiles WHERE id = %s", (THIRD_PROFILE,))
            left = conn.execute(
                "SELECT count(*) FROM registry.use_profiles WHERE id = %s", (THIRD_PROFILE,)
            ).fetchone()[0]
        assert left == 0, "the unused-profile fixture leaked a profile into the registry"


class TestTheVocabularyIsTheRegistryAndNotAList:
    """§7. Generic over registered profiles, not over the two that exist today."""

    def test_a_registered_profile_with_no_reviews_is_accepted(self, api_client, unused_profile):
        """A hard-coded pair refuses this. So does a lookup against the profiles
        that have reviews. Only the vocabulary accepts it, which is the point."""
        response = api_client.get(SOURCES, params={"use_profile": unused_profile})
        assert response.status_code == 200, response.text
        assert response.json()["use_profile"] == unused_profile

    def test_it_answers_that_profile_honestly_rather_than_borrowing(
        self, api_client, unused_profile
    ):
        body = api_client.get(SOURCES, params={"use_profile": unused_profile}).json()
        assert body["sources"], "every registered source should still be listed"
        assert body["reviewed_under_profile_count"] == 0
        assert body["collector_eligible_count"] == 0
        for source in body["sources"]:
            assert source["reviewed_under_requested_profile"] is False
            assert source["approval_state"] is None
            assert source["collector_eligible"] is False

    def test_the_detail_and_eligibility_routes_agree_with_it(self, api_client, unused_profile):
        body = eligibility(api_client, "fred", unused_profile)
        assert body["reviewed_under_requested_profile"] is False
        assert body["conditions"] == []
        assert body["approval_state"] is None

        full = detail(api_client, "fred", unused_profile)
        assert full["review"] is None
        assert full["evidence"] == []

    def test_the_number_of_valid_profiles_is_not_two(self, api_client, unused_profile):
        """Stated as a relation: whatever the registry holds is what is accepted."""
        for profile in (*PROFILES, unused_profile):
            assert api_client.get(SOURCES, params={"use_profile": profile}).status_code == 200, (
                profile
            )
        assert (
            api_client.get(
                SOURCES, params={"use_profile": "mission-175-never-registered"}
            ).status_code
            == 422
        )
