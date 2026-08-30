"""The global-state check, and the two ways it is allowed to be wrong.

Mission 1.7 §31. `registry.*` carries no `workspace_id`, so the post-suite leak
check in `run_pytest_suites.py` cannot see it -- not by oversight but by the
shape of the query that finds tenant tables. This module covers the check that
closes that gap.

Two failure directions, and they are not symmetric:

  * **Too permissive** hides a leak. A suite leaves a collector enabled or a
    review rewritten and the run stays green. That is the expensive one.
  * **Too strict** fails every run. `load_catalog_into` upserts with
    `updated_at = now()` and the verification log grows on every session, so a
    naive byte-comparison would be red before anybody had done anything wrong --
    and a check that always fails gets deleted, which lands you back at the
    first case with extra steps.

The comparison logic is pure and needs no database, so most of this runs under
the zero-dependency runner too (ADR-009).
"""

from __future__ import annotations

import importlib.util
import sys

from .conftest import REPO_ROOT, needs_postgres

_spec = importlib.util.spec_from_file_location(
    "registry_state", REPO_ROOT / "infrastructure/testing/registry_state.py"
)
assert _spec and _spec.loader
registry_state = importlib.util.module_from_spec(_spec)
# Registered BEFORE execution: `@dataclass` resolves annotations through
# `sys.modules[cls.__module__]`.
sys.modules[_spec.name] = registry_state
_spec.loader.exec_module(registry_state)

GOVERNED = "registry.sources"
LOG = "registry.source_condition_verifications"


def _snap(**tables: dict[str, str]) -> dict[str, dict[str, str]]:
    return dict(tables)


def _rows(*texts: str) -> dict[str, str]:
    """A table as the check models it: digest -> row text."""
    return {f"d{i}": text for i, text in enumerate(texts)}


class TestAGovernedTableMustComeBackUnchanged:
    def test_no_change_is_clean(self) -> None:
        snap = {GOVERNED: _rows("a", "b")}
        assert registry_state.compare(snap, snap) == []

    def test_a_left_behind_row_is_a_leak(self) -> None:
        before = {GOVERNED: _rows("a")}
        after = {GOVERNED: {"d0": "a", "extra": "b"}}
        (diff,) = registry_state.compare(before, after)
        assert diff.is_leak
        assert diff.added == ("b",)

    def test_a_deleted_row_is_a_leak(self) -> None:
        before = {GOVERNED: _rows("a", "b")}
        after = {GOVERNED: {"d0": "a"}}
        (diff,) = registry_state.compare(before, after)
        assert diff.is_leak
        assert diff.removed == ("b",)

    def test_a_rewritten_row_is_a_leak_in_both_directions(self) -> None:
        """The case that motivates content over counts.

        `UPDATE registry.sources SET collector_enabled = TRUE` moves no row
        count at all, so the tenant check's mechanism could not find it however
        carefully it was applied to these tables.
        """
        before = {GOVERNED: {"d0": '{"id": "world-bank", "collector_enabled": false}'}}
        after = {GOVERNED: {"d9": '{"id": "world-bank", "collector_enabled": true}'}}
        (diff,) = registry_state.compare(before, after)
        assert diff.is_leak
        assert len(diff.removed) == 1
        assert len(diff.added) == 1
        assert len(before[GOVERNED]) == len(after[GOVERNED])


class TestTheVerificationLogMayGrowAndMayNotShrink:
    """`record_verifications` appends on every session; that is the design.

    `acquisition-authorization-v1.md`: the id is `uuid5` over a tuple including
    `verified_at`, so a re-run records a new answer rather than overwriting the
    previous one, and the history is part of what makes the current state
    trustworthy.
    """

    def test_growth_is_not_a_leak(self) -> None:
        before = {LOG: _rows("v1")}
        after = {LOG: {"d0": "v1", "new": "v2"}}
        (diff,) = registry_state.compare(before, after)
        assert diff.append_only
        assert not diff.is_leak

    def test_a_vanished_entry_is_a_leak(self) -> None:
        before = {LOG: _rows("v1", "v2")}
        after = {LOG: {"d0": "v1"}}
        (diff,) = registry_state.compare(before, after)
        assert diff.is_leak

    def test_a_rewritten_entry_is_a_leak_despite_the_count_holding(self) -> None:
        before = {LOG: {"d0": '{"result": "UNSATISFIED"}'}}
        after = {LOG: {"d1": '{"result": "SATISFIED"}'}}
        (diff,) = registry_state.compare(before, after)
        assert diff.is_leak, "an append-only table may gain rows, never edit one"

    def test_the_exemption_is_named_not_inferred(self) -> None:
        """Append-only-ness is a property of the writer, not of the schema.

        Deriving it would mean guessing, and a wrong guess in the permissive
        direction is invisible. The set stays small and explicit.
        """
        assert {LOG} == registry_state.APPEND_ONLY


class TestWhatIsExcludedFromTheDigestAndWhatIsNot:
    """The mistake this check made on its own first run, kept as a test.

    Eight conditions came back "changed" after a clean suite. Nothing was wrong:
    `satisfied_at` and `satisfaction_reference` point at the verification that
    most recently cleared the condition, so they move every time the append-only
    log grows -- which is every run. `satisfied` was identical in all eight.

    Excluding them is right. Excluding one column too many would be the
    permissive failure, so the boundary is asserted from both sides.
    """

    def test_the_excluded_columns_are_exactly_the_derived_ones(self) -> None:
        assert set(registry_state.IGNORED_COLUMNS) == {
            "created_at",
            "updated_at",
            "satisfied_at",
            "satisfaction_reference",
        }
        assert "satisfied" not in registry_state.IGNORED_COLUMNS

    def test_un_clearing_a_condition_is_still_a_leak(self) -> None:
        """`satisfied` is the governance fact and stays in the digest.

        A suite that clears a condition and fails to put it back would make a
        source eligible; the reverse would make a collector stop. Both must be
        visible.
        """
        before = {"registry.source_review_conditions": {"d0": '{"key": "x", "satisfied": true}'}}
        after = {"registry.source_review_conditions": {"d1": '{"key": "x", "satisfied": false}'}}
        (diff,) = registry_state.compare(before, after)
        assert diff.is_leak

    @needs_postgres
    def test_the_real_condition_rows_carry_satisfied_but_not_its_pointer(self) -> None:
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            rows = registry_state.snapshot(conn, ["registry.source_review_conditions"])

        texts = list(rows["registry.source_review_conditions"].values())
        assert texts, "the catalog is loaded, so this proves more than an empty pass"
        assert all('"satisfied"' in t for t in texts)
        assert all("satisfied_at" not in t for t in texts)
        assert all("satisfaction_reference" not in t for t in texts)


class TestFillingAnEmptyTableIsALoad:
    def test_empty_to_populated_is_not_reported(self) -> None:
        """CI snapshots before `sros-source load`, so this is the normal path.

        Safe by construction rather than by convention: a table that held
        nothing cannot have lost anything.
        """
        before = {GOVERNED: {}}
        after = {GOVERNED: _rows("a", "b", "c")}
        assert registry_state.compare(before, after) == []

    def test_but_populated_to_empty_is_still_a_leak(self) -> None:
        before = {GOVERNED: _rows("a", "b")}
        after = {GOVERNED: {}}
        (diff,) = registry_state.compare(before, after)
        assert diff.is_leak
        assert len(diff.removed) == 2


class TestTheReportRefusesToPassOnNothing:
    def test_no_tables_is_a_failure_not_a_pass(self) -> None:
        """An empty derivation would make every comparison trivially equal.

        The same trap `_report` guards in the tenant check: reporting success
        having measured nothing is worse than reporting an error.
        """
        clean, text = registry_state.format_report([], [])
        assert not clean
        assert "nothing was checked" in text

    def test_a_clean_run_says_how_many_tables_it_covered(self) -> None:
        clean, text = registry_state.format_report([GOVERNED, LOG], [])
        assert clean
        assert "2 tables" in text

    def test_growth_is_reported_but_still_clean(self) -> None:
        diff = registry_state.Difference(table=LOG, removed=(), added=("v2", "v3"))
        clean, text = registry_state.format_report([GOVERNED, LOG], [diff])
        assert clean
        assert "2 appended" in text

    def test_a_leak_names_the_row_and_not_only_the_count(self) -> None:
        diff = registry_state.Difference(
            table=GOVERNED, removed=('{"id": "world-bank"}',), added=()
        )
        clean, text = registry_state.format_report([GOVERNED], [diff])
        assert not clean
        assert "world-bank" in text, "a hash nobody can look up sends the reader to write SQL"


@needs_postgres
class TestAgainstTheRealDatabase:
    def test_the_registry_is_watched_and_the_tenant_tables_are_not(self) -> None:
        """The two checks partition the application's tables between them.

        Neither keeps a list, so a table added by a future migration is covered
        by exactly one of them from the moment it exists.
        """
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            watched = set(registry_state.global_tables(conn))

        assert "registry.sources" in watched
        assert "registry.source_policy_reviews" in watched
        assert "registry.source_review_conditions" in watched
        assert "registry.registry_entries" in watched, "the global lookup seed (§31)"
        # Tenant tables belong to the other check. A table appearing in both
        # would mean one of the two derivations is wrong.
        assert "acquisition.raw_records" not in watched
        assert "research.claims" not in watched

    def test_a_snapshot_of_the_real_registry_is_stable_across_reads(self) -> None:
        """No `now()`, no row order, no key order leaking into the digest.

        If this is flaky the check is worthless: it would fail runs at random
        and be switched off.
        """
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            tables = registry_state.global_tables(conn)
            first = registry_state.snapshot(conn, tables)
            second = registry_state.snapshot(conn, tables)

        assert registry_state.compare(first, second) == []
        assert first[GOVERNED], "the registry is loaded, so this proves more than an empty pass"

    def test_timestamps_are_excluded_so_a_catalog_reload_is_invisible(self) -> None:
        """`load_catalog_into` sets `updated_at = now()` on every upsert.

        The session fixture calls it, so if the digest covered `updated_at` this
        check would be red on every single run.
        """
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            rows = registry_state.snapshot(conn, [GOVERNED])[GOVERNED]

        assert rows
        for text in rows.values():
            assert "updated_at" not in text
            assert "created_at" not in text
