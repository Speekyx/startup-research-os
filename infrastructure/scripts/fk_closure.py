#!/usr/bin/env python3
"""What else does a DELETE reach? Derived from the catalog, never written down.

Mission 1.6.1 §13 and §14.

WHY THIS EXISTS

A cleanup ran inside a transaction whose guard asserted `opportunities = 0`,
`raw = 6`, `normalized = 6`, `project = 1`. It committed. It had also deleted 39
claims, their revisions, their session observations, 36 evidence rows and their
independence groups -- five tables the guard did not name, and therefore five it
silently approved. The reported count was what `DELETE` returned: the rows it
matched directly, not the closure.

The lesson generalises past that incident. **A guard that enumerates what must
survive only covers the tables somebody already thought of.** No amount of care
fixes that, because the failure is in the shape of the check rather than in its
contents. The FK graph is already in the database; a guard that asks it cannot
be surprised by it.

    python infrastructure/scripts/fk_closure.py research.opportunities
    python infrastructure/scripts/fk_closure.py --all --dangerous-only

DELIBERATELY SMALL. §13 asks for visibility and safety, not a migration
framework. It reads `pg_constraint`, walks the graph and prints it. It deletes
nothing, changes nothing, and has no opinion about whether a delete is wise.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import deque
from dataclasses import dataclass

__all__ = ["Edge", "closure", "edges", "format_closure"]

# What PostgreSQL stores in `confdeltype`, and what each means for a delete of
# the PARENT row. Only the first two propagate; the others refuse or blank a
# column, which is a different kind of consequence and is reported separately.
DELETE_ACTIONS = {
    "a": "NO ACTION",
    "r": "RESTRICT",
    "c": "CASCADE",
    "n": "SET NULL",
    "d": "SET DEFAULT",
}
# The actions that reach further rows. A CASCADE deletes them; a SET NULL keeps
# the row and detaches it, which is how six normalized records lost their
# session without anybody deleting them.
PROPAGATING = {"c", "n", "d"}
DESTRUCTIVE = {"c"}


@dataclass(frozen=True)
class Edge:
    """One foreign key, from the child that references to the parent referenced."""

    child: str
    parent: str
    constraint: str
    columns: tuple[str, ...]
    on_delete: str

    @property
    def propagates(self) -> bool:
        return self.on_delete in PROPAGATING

    @property
    def destroys(self) -> bool:
        return self.on_delete in DESTRUCTIVE

    @property
    def action(self) -> str:
        return DELETE_ACTIONS.get(self.on_delete, self.on_delete)

    def describe(self) -> str:
        cols = ", ".join(self.columns)
        return f"{self.child} ({cols}) -> {self.parent}  ON DELETE {self.action}"


_EDGE_SQL = """
SELECT c.conrelid::regclass::text  AS child,
       c.confrelid::regclass::text AS parent,
       c.conname                   AS constraint_name,
       c.confdeltype               AS on_delete,
       array_agg(a.attname ORDER BY k.ord) AS columns
  FROM pg_constraint c
  JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
  JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
 WHERE c.contype = 'f'
 GROUP BY c.oid, c.conrelid, c.confrelid, c.conname, c.confdeltype
 ORDER BY child, constraint_name
"""


def edges(conn: object) -> list[Edge]:
    """Every foreign key in the database, read from the catalog.

    Not filtered by schema: a cleanup that reaches across schemas is exactly the
    case worth seeing, and `acquisition.normalized_records -> research.research_sessions`
    is one that already exists.
    """
    rows = conn.execute(_EDGE_SQL).fetchall()  # type: ignore[attr-defined]
    return [
        Edge(
            child=row[0],
            parent=row[1],
            constraint=row[2],
            columns=tuple(row[4]),
            on_delete=row[3],
        )
        for row in rows
    ]


def closure(
    all_edges: list[Edge], root: str, *, destructive_only: bool = False
) -> list[tuple[int, Edge]]:
    """Every table a DELETE from `root` may reach, breadth-first with its depth.

    Breadth-first so the output reads as "these follow directly, then these
    follow from those" -- which is the order somebody reasoning about blast
    radius actually wants.

    `destructive_only` narrows to `CASCADE`. The default keeps `SET NULL` and
    `SET DEFAULT` too, because a row that survives with a nulled foreign key is
    still a row the delete changed, and that is precisely how twelve records lost
    a session link while every count stayed the same.

    Cycles terminate: a table already reached is not expanded again.
    """
    by_parent: dict[str, list[Edge]] = {}
    for edge in all_edges:
        if edge.propagates and (edge.destroys or not destructive_only):
            by_parent.setdefault(edge.parent, []).append(edge)

    seen = {root}
    found: list[tuple[int, Edge]] = []
    queue: deque[tuple[str, int]] = deque([(root, 0)])
    while queue:
        table, depth = queue.popleft()
        for edge in sorted(by_parent.get(table, []), key=lambda e: (e.child, e.constraint)):
            found.append((depth + 1, edge))
            if edge.child not in seen:
                seen.add(edge.child)
                queue.append((edge.child, depth + 1))
    return found


def format_closure(root: str, reached: list[tuple[int, Edge]]) -> str:
    if not reached:
        return f"{root}: nothing references it. A delete reaches this table only."

    # Prose for a terminal, not SQL. `root` is a table name this tool was
    # asked about and the string is printed, never executed -- the module
    # issues no write at all, which its own test asserts.
    reach = len({e.child for _, e in reached})
    lines = [f"a DELETE from {root} may reach {reach} table(s):", ""]  # noqa: S608
    destroyed = sorted({e.child for _, e in reached if e.destroys})
    detached = sorted({e.child for _, e in reached if not e.destroys})

    for depth, edge in reached:
        marker = "DELETES" if edge.destroys else "detaches"
        lines.append(f"  {'  ' * (depth - 1)}{marker:9} {edge.describe()}")

    lines.append("")
    if destroyed:
        lines.append(f"  rows DELETED in:  {', '.join(destroyed)}")
    if detached:
        lines.append(f"  rows DETACHED in: {', '.join(detached)}")
    lines.append("")
    lines.append(
        "  A guard for this delete must assert over the tables above, not over a "
        "list written by hand."
    )
    return "\n".join(lines)


def _connect(url: str) -> object | None:
    try:
        import psycopg
    except ImportError:
        print("psycopg is not installed; this tool needs a database", file=sys.stderr)
        return None
    try:
        return psycopg.connect(url, connect_timeout=5)
    except Exception as exc:  # noqa: BLE001 - the type varies and the message is enough
        print(f"could not connect: {type(exc).__name__}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="fk_closure", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("table", nargs="?", help="schema-qualified table, e.g. research.claims")
    parser.add_argument("--all", action="store_true", help="every table that anything references")
    parser.add_argument(
        "--destructive-only",
        action="store_true",
        help="follow ON DELETE CASCADE only, ignoring SET NULL and SET DEFAULT",
    )
    args = parser.parse_args()
    if not args.table and not args.all:
        parser.error("give a table, or --all")

    url = os.environ.get("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    conn = _connect(url)
    if conn is None:
        return 2

    with conn:  # type: ignore[attr-defined]
        graph = edges(conn)
        if not graph:
            print("no foreign keys found: the catalog query is wrong", file=sys.stderr)
            return 1

        roots = sorted({e.parent for e in graph}) if args.all else [args.table]
        for root in roots:
            reached = closure(graph, root, destructive_only=args.destructive_only)
            if args.all and not reached:
                continue
            print(format_closure(root, reached))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
