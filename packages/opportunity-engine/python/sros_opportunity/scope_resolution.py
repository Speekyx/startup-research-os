"""Deriving one Evidence row's observation scope, deterministically or not at all.

Mission 1.34 §2, §3, §12, §20. The procedure is `observation-scope-resolution@1.0.0`.

**Nothing is persisted, and that is the design rather than an omission** (§12).
The scope is DERIVED at packet-build time from identifiers the deployment
already holds -- the Signal's own scope, the canonical subject registry, and the
source-native rules -- by the same `subject_key` procedure grouping already uses.
Adding a column would freeze a derivation in a table, which is what
`source-registry-v1.md` §3 refuses for eligibility and for the same reason: a
persisted copy of a derivation is a second answer that drifts from the first.

So no migration, no new tenant table, no RLS change, and no historical row to
backfill. Every existing Evidence row resolves or is honestly UNDETERMINED, and
the answer changes only when a reviewed registry changes.

**Two authorities, in a fixed order, and the order matters.** The canonical
subject registry is asked FIRST, because it records what a person decided a
particular identifier names. Only where no registry entry maps the key is the
source-native rule table consulted, which says what a SCHEME's identifiers are.
Reversing them would let a scheme-level rule overrule a per-identifier review.

**A scheme whose identifiers may name different levels gets no rule at all.** An
encyclopedia article can be about a product, a person or a country, so
`wikimedia-pageviews:content` is deliberately absent from the rule table and its
rows reach a level only through the registry. Writing a rule there would classify
by SOURCE instead of by SUBJECT, which is the mistake this whole mission is about
one level down.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .grouping import subject_key
from .scopes import (
    ObservationScope,
    ScopeOrigin,
    ScopeStatus,
    SubjectScopeType,
    undetermined,
)
from .subjects import CanonicalSubjectRegistry

__all__ = [
    "SCOPE_RESOLUTION_VERSION",
    "SourceNativeScopeRule",
    "ObservationScopeRules",
    "load_scope_rules",
    "resolve_observation_scope",
    "opportunity_subject_scope",
]

SCOPE_RESOLUTION_VERSION = "observation-scope-resolution@1.0.0"


@dataclass(frozen=True)
class SourceNativeScopeRule:
    """What one source's identifier SCHEME names, on the publisher's authority."""

    source_id: str
    scheme: str
    scope_type: SubjectScopeType
    origin: ScopeOrigin
    basis: str

    def __post_init__(self) -> None:
        if not self.basis.strip():
            raise ValueError(
                f"{self.source_id}:{self.scheme}: no basis. A rule classifying every "
                "identifier a source publishes needs to say what makes that true."
            )


@dataclass(frozen=True)
class ObservationScopeRules:
    registry_version: str
    rules: tuple[SourceNativeScopeRule, ...]

    def rule_for(self, source_id: str, scheme: str) -> SourceNativeScopeRule | None:
        """Exact equality on both parts. No prefix match, no wildcard."""
        for rule in self.rules:
            if rule.source_id == source_id and rule.scheme == scheme:
                return rule
        return None


def load_scope_rules(path: str | pathlib.Path) -> ObservationScopeRules:
    raw: dict[str, Any] = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return ObservationScopeRules(
        registry_version=str(raw.get("registry_version") or ""),
        rules=tuple(
            SourceNativeScopeRule(
                source_id=str(row["source_id"]),
                scheme=str(row["scheme"]),
                scope_type=SubjectScopeType(str(row["scope_type"])),
                origin=ScopeOrigin(str(row["origin"])),
                basis=str(row["basis"]),
            )
            for row in raw.get("rules") or ()
        ),
    )


def opportunity_subject_scope(
    canonical_subject_id: str, registry: CanonicalSubjectRegistry
) -> ObservationScope:
    """The scope an Opportunity is ABOUT, from the subject it names.

    The Opportunity's own scope comes from the registry and from nowhere else: it
    is a property of the subject, declared once, and never inferred from whatever
    evidence happens to be in the packet. Inferring it from the evidence is how a
    packet full of category rows would quietly become a category Opportunity.
    """
    for subject in registry.subjects:
        if subject.subject_id == canonical_subject_id:
            return ObservationScope(
                scope_type=subject.scope_type,
                scope_id=f"subject:{subject.subject_id}",
                display_name=subject.display_name,
                status=ScopeStatus.RESOLVED,
                origin=ScopeOrigin.HUMAN_REVIEWED,
                source_native_identifiers=tuple(i.key for i in subject.identifiers),
                basis=(
                    f"`{subject.subject_id}` is declared "
                    f"{subject.scope_type.value} in {registry.registry_version}, on the "
                    "entry a person wrote."
                ),
            )
    return undetermined(
        f"subject:{canonical_subject_id}",
        canonical_subject_id,
        f"{canonical_subject_id!r} is not in {registry.registry_version}, so nothing "
        "declares what level of thing it is.",
    )


def resolve_observation_scope(
    source_id: str,
    signal_type_id: str | None,
    signal_scope: Mapping[str, Any] | None,
    registry: CanonicalSubjectRegistry,
    rules: ObservationScopeRules,
) -> ObservationScope:
    """What one Evidence row observes. UNDETERMINED where nothing establishes it."""
    key = subject_key(source_id, signal_type_id, signal_scope)
    if key is None:
        return undetermined(
            f"{source_id}:UNKEYED",
            f"{source_id} row with no source-native subject key",
            f"no subject rule exists for signal type {signal_type_id!r} on "
            f"{source_id!r}, so the row names no addressable subject at all.",
        )

    rendered = str(key)

    # 1. A person's decision about THIS identifier wins over any scheme rule.
    canonical = registry.subject_for(rendered)
    if canonical is not None:
        scope = opportunity_subject_scope(canonical, registry)
        if scope.resolved:
            return ObservationScope(
                scope_type=scope.scope_type,
                scope_id=scope.scope_id,
                display_name=scope.display_name,
                status=ScopeStatus.RESOLVED,
                origin=ScopeOrigin.HUMAN_REVIEWED,
                source_native_identifiers=(rendered,),
                basis=(
                    f"{rendered!r} is mapped to {scope.scope_id!r} by "
                    f"{registry.registry_version}, which declares that subject "
                    f"{scope.scope_type.value if scope.scope_type else 'UNDETERMINED'}."
                ),
            )
        return scope

    # 2. Otherwise the scheme's own rule, where the source's vocabulary says what
    #    it publishes.
    rule = rules.rule_for(key.source_id, key.scheme)
    if rule is not None:
        return ObservationScope(
            scope_type=rule.scope_type,
            scope_id=rendered,
            display_name=rendered,
            status=ScopeStatus.RESOLVED,
            origin=rule.origin,
            source_native_identifiers=(rendered,),
            basis=rule.basis,
        )

    # 3. Nothing establishes it. §12: do not manufacture a scope.
    return undetermined(
        rendered,
        rendered,
        f"no canonical subject maps {rendered!r} and no rule covers scheme "
        f"{key.scheme!r} on {key.source_id!r}. The level of thing it names is not "
        "established, and is not guessed.",
    )
