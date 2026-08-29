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

# Sources this codebase can actually collect from.
#
# One entry since Mission 1.5, and it was added only after the collector's
# conformance suite passed (§26). Adding a name here is the LAST step of
# implementing a collector, never a way to prepare for one: everything that
# consults this set treats membership as "code exists that can collect from
# this", and a name added early would make that false.
#
# Two things consult it. `sros-source enable` refuses to switch on a collector
# that does not exist -- a switch that gets ahead of the thing it switches reads
# as "this is running" -- and the orchestrator answers the same question with
# its own fail-closed default, since a service may not import another service's
# package (`service-boundaries.md`).
#
# Eurostat is collector-eligible and is NOT here. Eligibility says a collector
# may be built; this says one was.
IMPLEMENTED_COLLECTORS: frozenset[str] = frozenset({"world-bank"})
