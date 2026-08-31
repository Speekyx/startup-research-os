"""Reviewed reliability, and the resolver that refuses to guess one.

`docs/data/evidence-reliability-contract-v1.md`, ADR-026.

**Reliability is purpose-relative**, so an assessment applies to a five-part
scope -- source, resource, record kind, claim type, proposition kind -- and never
to a source. `world-bank` alone matches nothing.

**A scope nobody assessed produces no number.** `NO_APPLICABLE_ASSESSMENT`, the
record stays NON_SCORABLE, and that is the honest state rather than a gap: a
default here would be the coefficient this layer exists to prevent.

Separate from `packages/evidence-aggregation` on purpose. That package may not
contain a registered source id at all -- asserted against the source catalog --
which is what keeps source identity out of the mathematics. The resolver
matches on source, so it lives here, on the same side of the seam as the row
adapter.
"""

from .model import (
    DOCUMENT_BACKED_BASIS_TYPES,
    ReliabilityAssessment,
    ReliabilityBasis,
    ReliabilityBinding,
    ReliabilityResolution,
    ReliabilityScope,
    assessment_key,
    canonical_json,
    resolve_reliability,
    scope_from_claim,
)

__all__ = [
    "DOCUMENT_BACKED_BASIS_TYPES",
    "ReliabilityAssessment",
    "ReliabilityBasis",
    "ReliabilityBinding",
    "ReliabilityResolution",
    "ReliabilityScope",
    "assessment_key",
    "canonical_json",
    "resolve_reliability",
    "scope_from_claim",
]
