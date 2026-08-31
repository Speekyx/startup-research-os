"""Fixtures for the Source Registry suite.

**No tenant fixture, and no `sros_gateway` import.** Source definitions and
their reviews are global platform metadata with no `workspace_id` and no
row-level security policy (Mission 1.0 §25), so these tests connect plainly.
A tenant fixture here would imply an isolation the registry does not have.

The database-backed tests skip when the local stack is not running, the same
way the gateway suite does: a contributor without Docker gets a green unit run
and an explicit note about what was not covered, rather than a red suite that
teaches them to ignore failures.
"""

from __future__ import annotations

import os
import pathlib
import sys
from collections.abc import Iterator

import pytest

# Mission 1.6.1 §17. One definition, imported by both suites that own
# destructive fixtures, rather than a copy in each that can drift.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "infrastructure"))
from testing.workspace_guard import disposable  # noqa: E402

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros"
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]

# Mission 1.15.3 §33. Three TED suites assert that no evidence came from a
# mirror, an archive or a search result, and the list of hosts that count as
# first-party grew when Mission 1.15.3 found the licence in the Publications
# Office's own open-data catalogue. Defined once, for the same reason the
# workspace guard is: three copies of a security-shaped list drift, and the one
# that drifts is the one nobody re-reads.
#
# Every entry is a domain the Publications Office or the Commission operates.
# Adding to it is a claim about who published a document, so it is the kind of
# edit that should be visible in a diff.
TED_FIRST_PARTY_PREFIXES = (
    "https://ted.europa.eu",
    "https://docs.ted.europa.eu",
    "https://developer.ted.europa.eu",
    "https://api.ted.europa.eu",
    # The TED Open Data Service, added by Mission 1.15.4. Its own footer reads
    # "This website is managed by: Publications Office of the European Union".
    "https://data.ted.europa.eu",
    "https://eur-lex.europa.eu",
    "https://op.europa.eu",
    "https://publications.europa.eu",
    "https://data.europa.eu",
)

# Hosts that are never evidence, whatever they happen to be serving (§3).
NEVER_EVIDENCE = ("google", "bing", "duckduckgo", "archive.org", "webcache", "github")


def _postgres_available() -> bool:
    try:
        import psycopg

        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


needs_postgres = pytest.mark.skipif(
    not _postgres_available(), reason="PostgreSQL not reachable; start infrastructure/compose"
)


@pytest.fixture(scope="session")
def catalog():
    """The real catalog. Deliberately not a fixture file.

    `docs/data/source-catalog-v1.json` is the artefact under review; testing a
    hand-made copy would leave the reviewed one unchecked, which is the failure
    mode these tests exist to prevent.
    """
    from sros_acquisition.registry import load_catalog

    return load_catalog(REPO_ROOT / "docs/data/source-catalog-v1.json")


@pytest.fixture(scope="session", autouse=True)
def registry_loaded(catalog) -> None:
    """Apply the catalog AND verify its conditions before any database test reads it.

    The suite must not depend on someone having run `sros-source load` first.
    That dependency is invisible while it holds -- a developer's database
    usually has the catalog in it from an earlier run -- and it fails only in a
    clean environment, which is to say in CI and on a new machine.

    **Verification is here for exactly the same reason, and it was added after
    the CI run that proved the point.** CI executes the suites before
    `sros-source verify --apply`, so on a fresh database no condition was
    satisfied, World Bank was not eligible, and
    `registry.require_eligibility_for_collector` correctly refused to let the
    enablement fixture turn its collector on. The database was right; the suite
    was assuming state somebody else had produced.

    Both steps grant nothing on their own. `load_catalog_into` writes
    `collector_enabled = FALSE` unconditionally, and a verification only records
    what a verifier found -- with no credential configured, FRED's condition
    stays unsatisfied here exactly as it does in production.
    """
    if not _postgres_available():
        return
    import psycopg
    from sros_acquisition.cli import _load_local_env
    from sros_acquisition.compliance import load_compliance, verify_source
    from sros_acquisition.compliance.repositories import record_verifications
    from sros_acquisition.registry.repositories import load_catalog_into

    # The SAME environment the CLI verifies against.
    #
    # `sros-source verify --apply` folds the git-ignored `infrastructure/compose/.env`
    # into its process; this fixture did not, so on a developer machine with
    # `FRED_API_KEY` configured the two disagreed: the CLI recorded FRED's
    # credential condition SATISFIED and the next `pytest` run recorded it
    # UNSATISFIED, silently taking FRED out of eligibility. Nothing surfaced it
    # until Mission 1.7 extended the post-suite leak check to `registry.*`.
    #
    # Folding it here makes a verification mean the same thing whoever runs it.
    # Absent in CI, where only `.env.example` exists, so this changes nothing
    # there -- and an explicitly exported variable still wins over the file.
    _load_local_env(REPO_ROOT)

    compliance = load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")
    with psycopg.connect(DATABASE_URL) as connection:
        load_catalog_into(connection, catalog)
        records = [r for source in catalog for r in verify_source(source, compliance)]
        record_verifications(connection, records)
        connection.commit()


def recorded_satisfied_keys(conn, source_id: str) -> frozenset[str]:
    """The conditions the DATABASE currently considers satisfied.

    Needed by every Python-versus-SQL comparison since Mission 1.4. Condition
    satisfaction is environment state that lives in the database, so a Python
    gate evaluated without it is not a second implementation of the same rule --
    it is the same rule with different inputs, and comparing the two would
    report a divergence that is really a missing argument.
    """
    rows = conn.execute(
        """SELECT c.condition_key
             FROM registry.source_review_conditions c
             JOIN registry.source_policy_reviews r ON r.id = c.review_id
            WHERE c.source_id = %s AND c.satisfied AND r.superseded_at IS NULL""",
        (source_id,),
    ).fetchall()
    return frozenset(row[0] for row in rows)


# A is the seeded development workspace, and since Mission 1.5 it holds REAL
# collected data. Tests therefore write into their own workspaces: P for
# persistence, B for the other side of an isolation assertion.
#
# A test that shared a workspace with real records would pass or fail depending
# on what somebody had collected that morning -- the same class of defect
# Mission 1.4 found in six tests that asserted a moment rather than a property.
WORKSPACE_A = "00000000-0000-4000-8000-000000000001"
WORKSPACE_B = "00000000-0000-4000-8000-000000000003"
WORKSPACE_P = "00000000-0000-4000-8000-000000000004"
# The second disposable workspace, added in Mission 1.6.1 §10. It replaces the
# seeded WORKSPACE_B on the other side of every isolation assertion: an
# assertion needs a workspace to be isolated FROM, and nothing about it requires
# that workspace to be one somebody else's data lives in.
WORKSPACE_Q = "00000000-0000-4000-8000-00000000000e"


def _make_workspace(workspace_id: str, slug: str) -> None:
    import psycopg

    disposable(workspace_id, what="_make_workspace")
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO core.workspaces (id, name, slug) VALUES (%s,%s,%s) "
            "ON CONFLICT (id) DO NOTHING",
            (workspace_id, f"test {slug}", slug),
        )
        connection.commit()


def _drop_workspace(workspace_id: str) -> None:
    """Remove a workspace this suite created, and its rows.

    The `disposable` guard replaced a hand-written `== WORKSPACE_P` assertion
    here. That assertion was correct and would have gone stale the moment a
    second disposable workspace existed -- which is what §10 then added.
    `disposable` states the rule instead of one instance of it.
    """
    import psycopg

    disposable(workspace_id, what="_drop_workspace")
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "DELETE FROM acquisition.normalized_records WHERE workspace_id = %s",
            (workspace_id,),
        )
        connection.execute(
            "DELETE FROM acquisition.raw_records WHERE workspace_id = %s", (workspace_id,)
        )
        connection.execute("DELETE FROM core.workspaces WHERE id = %s", (workspace_id,))
        connection.commit()


@pytest.fixture
def probe_workspace() -> Iterator[str]:
    """A workspace of this test's own, removed afterwards.

    Persistence assertions count rows, and counting rows in a workspace that
    also holds real collected data measures the environment rather than the
    behaviour under test.
    """
    _make_workspace(disposable(WORKSPACE_P, what="probe_workspace"), "acquisition-probe")
    yield WORKSPACE_P
    _drop_workspace(WORKSPACE_P)


@pytest.fixture
def tenant_conn():
    """A factory for connections inside a tenant transaction, rolled back.

    Both isolation layers are entered, because neither replaces the other:
    `SET LOCAL ROLE` so the row-level policies apply at all, and the
    transaction-local workspace so they resolve to this tenant. A test that only
    set the workspace would run as the migration role, which BYPASSES RLS — and
    would report an isolation guarantee it never exercised.
    """
    import contextlib
    import os

    import psycopg

    role = os.environ.get("APP_DB_ROLE", "sros_app")
    connections: list[object] = []

    @contextlib.contextmanager
    def factory(workspace_id: str):
        connection = psycopg.connect(DATABASE_URL)
        connections.append(connection)
        try:
            with connection.transaction(force_rollback=True):
                connection.execute(f"SET LOCAL ROLE {role}")
                connection.execute(
                    "SELECT set_config('app.workspace_id', %s, true)", (workspace_id,)
                )
                yield connection
        finally:
            connection.close()

    yield factory
    for connection in connections:
        with contextlib.suppress(Exception):
            connection.close()


@pytest.fixture
def committing_tenant_conn(probe_workspace: str):
    """A tenant connection factory that COMMITS, cleaned up with the workspace.

    `tenant_conn` rolls back, which is right for a persistence assertion and
    wrong for an idempotency one: "the second delivery finds the work already
    done" cannot be observed if the first delivery was undone. So this commits,
    and the probe workspace's teardown removes everything it wrote.

    Both isolation layers are still entered. A committing factory that skipped
    `SET LOCAL ROLE` would run as the migration role, which BYPASSES row-level
    security -- and every tenancy assertion made through it would be vacuous.
    """
    import contextlib
    import os

    import psycopg

    role = os.environ.get("APP_DB_ROLE", "sros_app")

    @contextlib.contextmanager
    def factory(workspace_id: str):
        connection = psycopg.connect(DATABASE_URL)
        try:
            with connection.transaction():
                connection.execute(f"SET LOCAL ROLE {role}")
                connection.execute(
                    "SELECT set_config('app.workspace_id', %s, true)", (workspace_id,)
                )
                yield connection
            connection.commit()
        finally:
            connection.close()

    return factory


@pytest.fixture
def second_workspace() -> Iterator[str]:
    """The other side of an isolation assertion, and disposable (§10).

    This used to yield the SEEDED workspace B and delete acquisition rows from
    it in teardown. It was harmless only because B happened to be empty: the
    day anything real was collected there, a passing test would have destroyed
    it. Mission 1.6.1 §9 classified it as the suite's one remaining
    shared-seed-mutating fixture.

    Nothing about the assertion needed a seeded workspace. "A workspace cannot
    read another workspace's rows" needs *another workspace*, and one this
    fixture creates and drops answers it exactly as well while being safe to
    empty.
    """
    _make_workspace(disposable(WORKSPACE_Q, what="second_workspace"), "acquisition-second")
    yield WORKSPACE_Q
    _drop_workspace(WORKSPACE_Q)


@pytest.fixture
def dev_session(probe_workspace: str) -> Iterator[str]:
    """A real research session in workspace A, removed afterwards.

    `raw_records.research_session_id` is a real foreign key, which the first job
    test discovered by failing on it. A random UUID is not a session, and the
    database is right to say so -- the alternative would have been a nullable
    link that quietly lost the connection between a record and the research that
    asked for it.
    """
    import json
    import uuid as _uuid

    import psycopg
    from sros_contracts import CONTRACT_VERSION, ONTOLOGY_VERSION

    project_id = _uuid.uuid4()
    session_id = _uuid.uuid4()
    context = {"market_scope": {"type": "COUNTRY", "countries": ["FR"]}}
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO research.research_projects (id, workspace_id, name) VALUES (%s,%s,%s)",
            (project_id, probe_workspace, "mission-1.5 acquisition test"),
        )
        connection.execute(
            """INSERT INTO research.research_sessions
                   (id, workspace_id, project_id, research_context,
                    research_context_hash, research_context_schema_version,
                    contract_version, ontology_version)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                session_id,
                probe_workspace,
                project_id,
                json.dumps(context),
                "probe-hash",
                "1",
                CONTRACT_VERSION,
                ONTOLOGY_VERSION,
            ),
        )
        connection.commit()
    yield str(session_id)
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute("DELETE FROM research.research_projects WHERE id = %s", (project_id,))
        connection.commit()


@pytest.fixture
def enabled_world_bank() -> Iterator[str]:
    """Turn the operational switch on for one test, then turn it back off.

    Enabled through the DATABASE, which refuses it for an ineligible source via
    `registry.require_eligibility_for_collector` -- so this fixture cannot make
    a source collectable that the gate would not clear. It is reversed in
    teardown because a test that leaves a collector enabled has changed the
    deployment, and the suite that follows would be testing a different system.
    """
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        # RESTORE, not force-false. An earlier version of this fixture reset
        # every source to FALSE in teardown, which silently reverted an
        # operator's deliberate enablement -- a test that changes the deployment
        # and does not put it back is a test that decides what production does.
        previous = connection.execute(
            "SELECT collector_enabled FROM registry.sources WHERE id = 'world-bank'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = TRUE WHERE id = 'world-bank'"
        )
        connection.commit()
    yield "world-bank"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = %s WHERE id = 'world-bank'",
            (previous,),
        )
        connection.commit()


@pytest.fixture
def disabled_world_bank() -> Iterator[str]:
    """Turn the operational switch OFF for one test, then restore it.

    The mirror of `enabled_world_bank`, and it exists for the same reason: a
    test that needs the deployment in a particular state must put it there and
    put it back, rather than depending on how somebody left it.
    """
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        previous = connection.execute(
            "SELECT collector_enabled FROM registry.sources WHERE id = 'world-bank'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = FALSE WHERE id = 'world-bank'"
        )
        connection.commit()
    yield "world-bank"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = %s WHERE id = 'world-bank'",
            (previous,),
        )
        connection.commit()


@pytest.fixture
def conn() -> Iterator[object]:
    """A plain connection, rolled back at the end of every test.

    Rollback rather than cleanup: these tests deliberately provoke constraint
    triggers, and a test that half-applied a load must leave nothing behind.
    """
    import psycopg

    connection = psycopg.connect(DATABASE_URL)
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def seeded_raw(probe_workspace: str, dev_session: str, catalog):
    """Real raw records in the probe workspace, written the way production writes them.

    Produced by the REAL collector against a fake transport, then persisted
    through the REAL repository. A fixture that inserted hand-written rows would
    be testing the normalizer against a shape nothing produces -- and the first
    thing to change in the collector would leave it green and wrong.

    Six observations, matching the Mission 1.5 acquisition: one indicator, two
    countries, three years. Removed with the workspace.
    """
    import json

    import psycopg
    from sros_acquisition.collection import (
        RequestPacer,
        WorldBankCollector,
        WorldBankRequest,
        persist_drafts,
    )
    from sros_acquisition.collection.pacing import WORLD_BANK_PACING
    from sros_acquisition.collection.transport import HttpRequest, HttpResponse
    from sros_acquisition.compliance import build_authorization, load_compliance
    from sros_acquisition.normalization import read_raw_records

    indicator = "SP.POP.TOTL"
    rows = [
        {
            "indicator": {"id": indicator, "value": "Population, total"},
            "country": {"id": iso2, "value": name},
            "countryiso3code": iso3,
            "date": str(year),
            "value": value,
            "unit": "",
            "obs_status": "",
            "decimal": 0,
        }
        for iso2, iso3, name, values in (
            ("FR", "FRA", "France", {2018: 66977107, 2019: 67157400, 2020: 67571107}),
            ("DE", "DEU", "Germany", {2018: 82905782, 2019: 83092962, 2020: 83160871}),
        )
        for year, value in values.items()
    ]
    body = json.dumps(
        [{"page": 1, "pages": 1, "per_page": 50, "total": 6, "lastupdated": "2025-07-01"}, rows]
    )

    class _Fixed:
        def get(self, base_url, request: HttpRequest, allowed_hosts) -> HttpResponse:
            return HttpResponse(200, body, 0.01, request.path)

    compliance = load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")
    context = build_authorization(catalog.get("world-bank"), compliance, environ={})
    collector = WorldBankCollector(
        _Fixed(),  # type: ignore[arg-type]
        pacer=RequestPacer(WORLD_BANK_PACING, sleep=lambda _: None),
    )
    result = collector.collect(
        context,
        WorldBankRequest(indicators=(indicator,), countries=("FR", "DE")),
        workspace_id=probe_workspace,
        correlation_id="seeded-raw",
        research_session_id=dev_session,
    )
    assert result.succeeded, result.failures
    assert len(result.drafts) == 6

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.transaction():
            connection.execute("SET LOCAL ROLE sros_app")
            connection.execute(
                "SELECT set_config('app.workspace_id', %s, true)", (probe_workspace,)
            )
            persist_drafts(connection, result.drafts)
        connection.commit()

    with psycopg.connect(DATABASE_URL) as connection, connection.transaction():
        connection.execute("SET LOCAL ROLE sros_app")
        connection.execute("SELECT set_config('app.workspace_id', %s, true)", (probe_workspace,))
        yield read_raw_records(connection, probe_workspace)
