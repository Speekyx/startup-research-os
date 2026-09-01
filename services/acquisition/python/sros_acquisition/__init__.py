"""Acquisition context.

**Collection is not implemented.** What exists is the Source Registry -- the
governance layer that decides whether a source may ever be collected from
(Mission 1.0, D-07) -- and, since Mission 1.4, the compliance capabilities that
a conditional approval requires before that decision can come out yes.

`service-boundaries.md` §5 assigns the source registry and its legal-review
records to this context, and marks them GLOBAL rather than tenant-scoped: a
source review that differed per workspace would make provenance incomparable
across workspaces.

    registry/       may this source be collected from, and why not
    compliance/     what a collector would have to obey, and whether it can
    collection/     the World Bank and GDELT WEB-NGRAM collectors, and the
                    HTTP boundary
    normalization/  RawRecord to canonical observation

Neither governance package opens a network connection, and CI asserts it --
along with the narrower Mission 1.5 rule that exactly one file in
`collection/` may, and the Mission 1.6 rule that no file in `normalization/`
may reach a network, a model or an embedding library at all.
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
    "IMPLEMENTED_NORMALIZERS",
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
# Two entries. Each was added only after its own conformance suite passed --
# Mission 1.5 §26 for World Bank, Mission 1.9.3 §40 for GDELT. Adding a name
# here is the LAST step of implementing a collector, never a way to prepare for
# one: everything that consults this set treats membership as "code exists that
# can collect from this", and a name added early would make that false.
#
# Two things consult it. `sros-source enable` refuses to switch on a collector
# that does not exist -- a switch that gets ahead of the thing it switches reads
# as "this is running" -- and the orchestrator answers the same question with
# its own fail-closed default, since a service may not import another service's
# package (`service-boundaries.md`).
#
# Eurostat is collector-eligible and is NOT here, and since Mission 1.9.2 there
# is a sharper way to say why: it has no authorised RESOURCE either, so even a
# collector would have nothing it could ask for. Eligibility says a collector
# may be built; resource-readiness says there is something to build against;
# this says one was built.
IMPLEMENTED_COLLECTORS: frozenset[str] = frozenset(
    # `stack-exchange` joined in Mission 1.18. The guard that caught its
    # absence is the one worth naming: `assert_registry_grants_nothing`
    # refused a database holding raw records for a source this codebase
    # "cannot collect from", which was true of the SET and false of the
    # repository -- the collector existed and had not been declared here.
    {"world-bank", "gdelt", "ted-eu", "stack-exchange"}
)


# Sources this codebase can actually NORMALIZE.
#
# A FOURTH separate fact, and the mission that added it is the one that proved
# the separation was not academic. Before Mission 1.6 the planner blocked
# normalization under "no collector is implemented" -- a reason that stopped
# being true the moment Mission 1.5 built one, while normalization remained just
# as impossible. A false blocking reason is worse than a vague one: it invites
# someone to conclude the block no longer applies.
#
#     eligible      may we collect from this source
#     enabled       is collection switched on in this deployment
#     implemented   does a collector exist
#     normalizable  does a NORMALIZER exist for what that collector writes
#
# Eurostat is collector-eligible, has no collector and is not here. World Bank
# has both. Derived from the registered adapters rather than written twice, so
# the set cannot drift from the table that actually dispatches -- and the
# orchestrator gets it from the composition root, because a service may not
# import another service's package (`service-boundaries.md`).
def _normalizable_sources() -> frozenset[str]:
    from .normalization import supported_sources

    return supported_sources()


IMPLEMENTED_NORMALIZERS: frozenset[str] = _normalizable_sources()
