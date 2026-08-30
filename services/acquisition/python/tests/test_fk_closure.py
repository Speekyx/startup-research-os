"""The FK closure utility, against the real catalog.

Mission 1.6.1 §14. The relations asserted here are ones this repository actually
has, and each was chosen because a real incident in Sprint 1 turned on it:

  * `research.opportunities -> research.claims` is how a delete of 156 test
    opportunities also took 39 claims, their revisions, their observations and
    36 evidence rows past a guard that named none of them;
  * `acquisition.raw_records -> acquisition.normalized_records` is how a
    delete-and-recollect of six raw records destroyed six normalized ones;
  * `research.research_projects` is what `test_rls.py` deleted without a WHERE
    clause, and its closure is seventeen tables wide.

**Asserted as relations, not as counts.** "The closure has 6 entries" would
break on the next migration and teach whoever hits it to edit the number. What
must hold is that specific edges are found and that the traversal is transitive.
"""

from __future__ import annotations

import importlib.util
import sys

import pytest

from .conftest import REPO_ROOT, needs_postgres

_spec = importlib.util.spec_from_file_location(
    "fk_closure", REPO_ROOT / "infrastructure/scripts/fk_closure.py"
)
assert _spec and _spec.loader
fk_closure = importlib.util.module_from_spec(_spec)
# Registered BEFORE execution: `@dataclass` resolves annotations through
# `sys.modules[cls.__module__]`, so a module executed without being registered
# raises on its first frozen dataclass.
sys.modules[_spec.name] = fk_closure
_spec.loader.exec_module(fk_closure)


@pytest.fixture(scope="module")
def graph(request):
    import psycopg

    from .conftest import DATABASE_URL

    with psycopg.connect(DATABASE_URL) as conn:
        return fk_closure.edges(conn)


def _children(reached) -> set[str]:
    return {edge.child for _, edge in reached}


@needs_postgres
class TestTheGraphIsRead:
    """§14. From the catalog, never hard-coded."""

    def test_the_catalog_yields_a_graph_at_all(self, graph) -> None:
        assert graph, "no foreign keys found; the catalog query is wrong"
        # Enough edges that a passing test means something. The exact number is
        # deliberately not asserted -- it changes with every migration.
        assert len(graph) > 20

    def test_every_edge_carries_a_known_delete_action(self, graph) -> None:
        for edge in graph:
            assert edge.on_delete in fk_closure.DELETE_ACTIONS, edge.constraint
            assert edge.action != edge.on_delete or len(edge.action) > 1

    def test_composite_keys_are_read_whole(self, graph) -> None:
        """A two-column FK must arrive as two columns, in declaration order.

        The first version of this test asserted that every composite FK leads
        with `workspace_id`, which is false and usefully so: the registry
        references are composite for a different reason -- `(registry, id)` into
        `registry_entries`, which is a taxonomy key and carries no tenancy.
        Two kinds of composite key exist and the tool must read both.
        """
        composite = [e for e in graph if len(e.columns) > 1]
        assert composite, "no composite foreign key found; the unnest is wrong"

        tenant = [e for e in composite if e.columns[0] == "workspace_id"]
        registry = [e for e in composite if e.parent == "registry.registry_entries"]
        assert tenant, "Mission 1.2's tenant-carrying FKs are missing"
        assert registry, "the registry taxonomy FKs are missing"
        # Checked against the catalog rather than against a guess about the
        # schema. Two earlier versions of this assertion hard-coded a shape --
        # "always starts with workspace_id", then "always two columns" -- and
        # both were wrong: `claims_current_revision_fkey` has three.
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            expected = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT conname, array_length(conkey, 1) FROM pg_constraint WHERE contype = 'f'"
                ).fetchall()
            }
        for edge in graph:
            assert len(edge.columns) == expected[edge.constraint], (
                f"{edge.constraint} has {expected[edge.constraint]} column(s) in the "
                f"catalog and the tool read {len(edge.columns)}"
            )


@needs_postgres
class TestKnownClosures:
    """The three Sprint 1 incidents, as relations."""

    def test_deleting_opportunities_reaches_claims_and_their_dependents(self, graph) -> None:
        reached = fk_closure.closure(graph, "research.opportunities")
        children = _children(reached)
        # The direct hop that made the incident possible.
        assert "research.claims" in children
        # And the transitive ones a hand-written guard would not have listed.
        assert "research.claim_revisions" in children
        assert "research.claim_session_observations" in children
        assert "scoring.evidence" in children
        assert "scoring.evidence_independence_groups" in children

    def test_the_traversal_is_transitive_not_one_hop(self, graph) -> None:
        """`claim_revisions` hangs off `claims`, not off `opportunities`.

        Finding it proves the walk continues rather than reporting only what
        references the root directly -- which is exactly the difference between
        this and the guard it replaces.
        """
        reached = fk_closure.closure(graph, "research.opportunities")
        depths = {edge.child: depth for depth, edge in reached}
        assert depths["research.claims"] == 1
        assert depths["research.claim_revisions"] == 2

    def test_deleting_raw_records_reaches_normalized_records(self, graph) -> None:
        reached = fk_closure.closure(graph, "acquisition.raw_records")
        assert "acquisition.normalized_records" in _children(reached)

    def test_deleting_projects_reaches_the_acquisition_layer(self, graph) -> None:
        """The `test_rls.py` delete, whose closure nobody had looked at.

        It detaches raw and normalized records through the session, which is how
        twelve records lost their session link while every row count stayed the
        same.
        """
        reached = fk_closure.closure(graph, "research.research_projects")
        children = _children(reached)
        assert "research.research_sessions" in children
        assert "acquisition.raw_records" in children
        assert "acquisition.normalized_records" in children
        assert len(children) > 10, "the closure is far wider than one hop"

    def test_a_leaf_table_reaches_nothing(self, graph) -> None:
        """The empty case, on a table nothing actually references.

        The first version used `registry.source_policy_evidence`, which turned
        out to be referenced by `source_retention_policies` -- so the test would
        have passed only by accident and failed for the right reason instead.
        `nlp.embedding_provenance` is a genuine leaf: vectors live in Qdrant and
        nothing points back at their provenance rows.
        """
        assert fk_closure.closure(graph, "nlp.embedding_provenance") == []
        # And a non-leaf still reports its children, so the empty result above
        # means "nothing references it" rather than "the walk did not run".
        assert fk_closure.closure(graph, "acquisition.normalized_records")


@needs_postgres
class TestDestructiveVersusDetaching:
    """A row that survives with a nulled key is still a row the delete changed."""

    def test_set_null_edges_are_reported_by_default(self, graph) -> None:
        reached = fk_closure.closure(graph, "research.research_sessions")
        detaching = [e for _, e in reached if not e.destroys]
        assert detaching, "no SET NULL edge found from research_sessions"
        assert any(e.child == "acquisition.raw_records" for e in detaching)

    def test_destructive_only_excludes_them(self, graph) -> None:
        everything = _children(fk_closure.closure(graph, "research.research_sessions"))
        cascades = _children(
            fk_closure.closure(graph, "research.research_sessions", destructive_only=True)
        )
        assert cascades < everything
        # raw_records is detached, not deleted, so it must drop out.
        assert "acquisition.raw_records" in everything
        assert "acquisition.raw_records" not in cascades

    def test_the_report_names_both_kinds(self, graph) -> None:
        text = fk_closure.format_closure(
            "research.opportunities", fk_closure.closure(graph, "research.opportunities")
        )
        assert "rows DELETED in:" in text
        assert "research.claims" in text
        assert "not over a list written by hand" in text


@needs_postgres
class TestTerminationAndSafety:
    """It must not loop, and it must not write."""

    def test_a_self_referencing_table_terminates(self, graph) -> None:
        """`raw_records.parent_record_id` points at `raw_records`."""
        reached = fk_closure.closure(graph, "acquisition.raw_records")
        assert any(
            e.child == "acquisition.raw_records" and e.parent == "acquisition.raw_records"
            for _, e in reached
        )
        # It returned at all, which is the assertion: an unguarded walk hangs.
        assert len(reached) < 100

    def test_the_module_issues_no_write(self) -> None:
        source = (REPO_ROOT / "infrastructure/scripts/fk_closure.py").read_text(encoding="utf-8")
        for statement in ("DELETE FROM", "INSERT INTO", "UPDATE ", "DROP ", "TRUNCATE"):
            assert statement not in source.upper().replace("A DELETE FROM", ""), (
                f"the closure tool contains {statement!r}; it inspects and nothing else"
            )
