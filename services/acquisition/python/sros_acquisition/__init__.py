"""Acquisition context.

**Collection is not implemented.** What exists is the Source Registry: the
governance layer that decides whether a source may ever be collected from
(Mission 1.0, D-07).

`service-boundaries.md` §5 assigns the source registry and its legal-review
records to this context, and marks them GLOBAL rather than tenant-scoped: a
source review that differed per workspace would make provenance incomparable
across workspaces.
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
    "SourceCatalog",
    "SourceRecord",
    "SourceRegistryError",
    "EligibilityResult",
    "load_catalog",
    "evaluate_eligibility",
    "resolve_retention",
]
