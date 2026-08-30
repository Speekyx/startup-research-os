"""The normalizer boundary, and how one is selected.

Mission 1.6 §19 and §20.

**The minimal interface the first adapter justifies, and no more.** §19 is
explicit that this must not become a plugin framework with speculative
complexity, so there is no lifecycle, no hook chain, no capability negotiation
and no dynamic discovery. A `NormalizerSpec` says which source and collector an
adapter serves, which collector versions it understands and which canonical
schema it writes; a `Normalizer` turns one `RawRecordView` into one
`NormalizedRecordDraft`. A future Eurostat or FRED adapter implements exactly
that and nothing more.

**The spec is separate from the instance**, for one concrete reason: selection
must be answerable without configuration. `sros-normalize validate` and the
planner both ask *is there an adapter for this* long before any governance input
has been resolved, and a registry that could only answer by constructing an
adapter would force them to resolve retention for a source they may not even
normalize.

**Selection is explicit, keyed and fails closed** (§20). The key is
`(source_id, collector_id)` -- not the source alone, because a second collector
for one source parses a different shape, and handing it to the wrong adapter
would produce plausible nonsense rather than an error.

    (source_id, collector_id)  ->  spec           -- registered
    anything else              ->  UNSUPPORTED_SOURCE

A caller may pass its own registry, and passing an empty one refuses everything.
A missing wire must read as "we cannot", never as "we may" -- the same rule the
planner's `implemented_collectors` is under, and for the same reason.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from sros_contracts import NormalizationErrorCode

from ..registry.retention import EffectiveRetention
from .errors import NormalizationFailedError, NormalizationFailure
from .geography import GeographyMap
from .model import NormalizationCounts, NormalizedRecordDraft, RawRecordView

__all__ = [
    "NORMALIZER_REGISTRY",
    "NormalizationContext",
    "Normalizer",
    "NormalizerResult",
    "NormalizerSpec",
    "register_normalizer",
    "select_normalizer",
    "supported_sources",
]


@dataclass(frozen=True)
class NormalizationContext:
    """The governance and configuration inputs an adapter is constructed with.

    `retention` is resolved by `resolve_retention` before it gets here, so an
    adapter receives a window rather than the ability to choose one (§10).
    `geography` is the reviewed classification map (§15). Both are inputs to the
    transformation, which is why changing either requires bumping a normalizer
    version rather than quietly producing different output.
    """

    retention: EffectiveRetention
    geography: GeographyMap


class Normalizer(Protocol):
    """What every normalizer is, and the whole of it."""

    normalizer_id: str
    normalizer_version: str
    source_id: str
    schema_id: str
    schema_version: int

    def normalize(
        self, record: RawRecordView, *, correlation_id: str, normalized_at: datetime
    ) -> NormalizedRecordDraft:
        """One raw record into one canonical record.

        Raises `NormalizationFailedError` when no record can be produced at all.
        A record that can be produced but is incomplete is **returned**, with a
        quality state and reasons -- §26 forbids discarding it, because a raw
        record that could not be normalized is a fact someone has to find.
        """
        ...


@dataclass(frozen=True)
class NormalizerSpec:
    """What is registered: an adapter's identity, its bounds and how to build it.

    `supported_collector_versions` is not decoration. A collector version this
    adapter has never seen may have changed the payload shape, and a parse that
    half-works on an unknown shape is worse than one that stops (§20, §54).
    """

    normalizer_id: str
    normalizer_version: str
    source_id: str
    collector_id: str
    supported_collector_versions: frozenset[str]
    schema_id: str
    schema_version: int
    build: Callable[[NormalizationContext], Normalizer]

    @property
    def key(self) -> tuple[str, str]:
        return (self.source_id, self.collector_id)

    def to_json(self) -> dict[str, object]:
        return {
            "normalizer": f"{self.normalizer_id}@{self.normalizer_version}",
            "source_id": self.source_id,
            "collector_id": self.collector_id,
            "supported_collector_versions": sorted(self.supported_collector_versions),
            "schema": f"{self.schema_id}/{self.schema_version}",
        }


# Registered adapters. ONE entry, because one adapter exists -- the same rule
# IMPLEMENTED_COLLECTORS is under. Registering a name here is the LAST step of
# writing a normalizer, never preparation for one: everything that consults this
# table treats membership as "code exists that can normalize this".
NORMALIZER_REGISTRY: dict[tuple[str, str], NormalizerSpec] = {}


def register_normalizer(spec: NormalizerSpec) -> None:
    if spec.key in NORMALIZER_REGISTRY:
        raise ValueError(
            f"a normalizer is already registered for {spec.key}. Two adapters for one "
            "collector is two answers to one question"
        )
    NORMALIZER_REGISTRY[spec.key] = spec


def supported_sources(
    registry: Mapping[tuple[str, str], NormalizerSpec] | None = None,
) -> frozenset[str]:
    """Sources some registered normalizer can handle."""
    table = NORMALIZER_REGISTRY if registry is None else registry
    return frozenset(source_id for source_id, _ in table)


def select_normalizer(
    record: RawRecordView,
    registry: Mapping[tuple[str, str], NormalizerSpec] | None = None,
    *,
    correlation_id: str | None = None,
) -> NormalizerSpec:
    """The adapter for this record, or a refusal that says which gate closed.

    Two gates, reported separately on purpose. "No adapter exists for this
    source" is fixed by writing one; "this adapter does not know this collector
    version" is fixed by reviewing the parse and widening the declaration.
    Collapsing them into one message would send the reader to the wrong work.
    """
    table = NORMALIZER_REGISTRY if registry is None else registry
    spec = table.get((record.source_id, record.collector_id))
    if spec is None:
        raise NormalizationFailedError(
            NormalizationFailure(
                code=NormalizationErrorCode.UNSUPPORTED_SOURCE,
                detail=(
                    f"no normalizer is registered for source {record.source_id!r} written "
                    f"by collector {record.collector_id!r}. Selection is keyed on both, and "
                    "an unknown pair is never handed to whichever adapter happens to exist"
                ),
                source_id=record.source_id,
                raw_record_id=record.record_id,
                correlation_id=correlation_id,
                context={"collector_id": record.collector_id},
            )
        )

    if record.collector_version not in spec.supported_collector_versions:
        raise NormalizationFailedError(
            NormalizationFailure(
                code=NormalizationErrorCode.UNSUPPORTED_COLLECTOR_VERSION,
                detail=(
                    f"{spec.normalizer_id} declares support for collector versions "
                    f"{sorted(spec.supported_collector_versions)} and this record was "
                    f"written by {record.collector_version}. Refused rather than attempted: "
                    "a parse that half-works on an unknown shape is worse than one that stops"
                ),
                source_id=record.source_id,
                raw_record_id=record.record_id,
                correlation_id=correlation_id,
                context={
                    "collector_id": record.collector_id,
                    "collector_version": record.collector_version,
                    "supported": sorted(spec.supported_collector_versions),
                },
            )
        )
    return spec


@dataclass
class NormalizerResult:
    """What one normalization pass produced, including what it refused.

    §52. Counts and failures travel together: a pass that normalized forty
    records and refused ten is not a success, and a result reporting only the
    forty would say it was.
    """

    source_id: str
    drafts: list[NormalizedRecordDraft] = field(default_factory=list)
    failures: list[NormalizationFailure] = field(default_factory=list)
    counts: NormalizationCounts = field(default_factory=NormalizationCounts)
    normalizers: set[str] = field(default_factory=set)

    @property
    def succeeded(self) -> bool:
        return not self.failures

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "normalizers": sorted(self.normalizers),
            "counts": self.counts.to_json(),
            # Already sanitised: a failure carries a message this codebase wrote
            # and safe diagnostic context, never a payload or a stack trace.
            "failures": [f.to_json() for f in self.failures],
            "succeeded": self.succeeded,
        }
