"""Acquisition context.

**Collection is not implemented.** What exists is the Source Registry -- the
governance layer that decides whether a source may ever be collected from
(Mission 1.0, D-07) -- and, since Mission 1.4, the compliance capabilities that
a conditional approval requires before that decision can come out yes.

`service-boundaries.md` §5 assigns the source registry and its legal-review
records to this context, and marks them GLOBAL rather than tenant-scoped: a
source review that differed per workspace would make provenance incomparable
across workspaces.

    registry/    may this source be collected from, and why not
    compliance/  what a collector would have to obey, and whether it can

Neither package opens a network connection, and CI asserts it.
"""

from .registry import (
    EligibilityResult,
    SourceCatalog,
    SourceRecord,
    SourceRegistryError,
    evaluate_eligibility,
    load_catalog,
    resolve_retention,
)

__all__ = [
    "IMPLEMENTED_COLLECTORS",
    "EligibilityResult",
    "SourceCatalog",
    "SourceRecord",
    "SourceRegistryError",
    "evaluate_eligibility",
    "load_catalog",
    "resolve_retention",
]

# Sources this codebase can actually collect from. Empty, and that is the whole
# statement: Mission 1.4 made two sources collector-ELIGIBLE, which says a
# collector may be built and not that one was.
#
# It exists as a named, empty set rather than as an unwritten fact because two
# things now have to consult it. `sros-source enable` refuses to switch on a
# collector that does not exist -- a switch that gets ahead of the thing it
# switches reads as "this is running" -- and the orchestrator answers the same
# question with its own fail-closed default, since a service may not import
# another service's package (`service-boundaries.md`).
#
# Adding an entry here is part of implementing a collector, never a way to
# prepare for one.
IMPLEMENTED_COLLECTORS: frozenset[str] = frozenset()
