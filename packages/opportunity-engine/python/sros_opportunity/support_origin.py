"""Where a piece of support comes from, typed, so that a source's NAME never becomes a domain FACT.

Mission 1.84.11. Gate v1.2.0 had three channels: A, the supplied statements; B, the packet's
structural facts; C, trusted limiting or definitional context. A was one undifferentiated string, so
every word of a claim statement licensed the same things, including the words of the source's own
name that the interpretation template writes at the head of the statement. The operator decided
(`SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false`) that a source name, publisher
name, registry display label or provenance label is NOT factual support merely because a domain word
occurs inside it.

So A is split, and there are four origins, each licensing exactly one thing:

    SOURCE_CONTENT_STATEMENT               what the source reported. Lexical support for markers,
                                           concepts and numbers, under the existing rules only.
    SOURCE_METADATA_LABEL                  where the data came from. Licenses the label's own whole
                                           occurrence as a NAME, a provenance reference, and nothing
                                           else: none of its words and none of its numbers.
    PACKET_STRUCTURAL_FACT                 ids, families, dimensions, scorability, identity. B,
                                           unchanged, and no label is ever moved into it.
    TRUSTED_LIMITING_OR_DEFINITIONAL_FACT  definitional identifiers only. C, unchanged.

**A label never becomes content silently.** Labels arrive through an explicit, typed channel that
carries a provenance, as trusted context does. A packet source with no declaration is reported by
the gate by name, because its statements cannot be split and reading them whole would put its name
back into the content channel.
"""

from __future__ import annotations

import enum
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .assertion_context import PacketStructuralFacts, TrustedContext, _norm
from .lexical_inflection import inflection_spans, normalized_forms
from .packet import OpportunityEvidencePacket
from .validation import _numbers

__all__ = [
    "SUPPORT_UNIVERSE_VERSION_V2",
    "SupportOrigin",
    "SourceMetadataLabelKind",
    "SourceMetadataLabel",
    "SourceMetadataContext",
    "TypedStatement",
    "TypedSupportUniverse",
    "label_spans",
    "mask_labels",
    "split_statement",
    "build_typed_support_universe",
]

#: The successor of `opportunity-support-universe@1.0.0`, which stays in `assertion_context.py`. A
#: MAJOR version: the channel `SOURCE_STATEMENTS` no longer exists as one thing.
SUPPORT_UNIVERSE_VERSION_V2 = "opportunity-support-universe@2.0.0"


class SupportOrigin(enum.Enum):
    """The four origins a piece of support may have. Each licenses exactly one kind of thing."""

    SOURCE_CONTENT_STATEMENT = "SOURCE_CONTENT_STATEMENT"
    SOURCE_METADATA_LABEL = "SOURCE_METADATA_LABEL"
    PACKET_STRUCTURAL_FACT = "PACKET_STRUCTURAL_FACT"
    TRUSTED_LIMITING_OR_DEFINITIONAL_FACT = "TRUSTED_LIMITING_OR_DEFINITIONAL_FACT"


class SourceMetadataLabelKind(enum.Enum):
    """What kind of name a label is. Every kind is provenance, and none is content."""

    PUBLISHER_NAME = "PUBLISHER_NAME"
    SOURCE_NAME = "SOURCE_NAME"
    REGISTRY_DISPLAY_NAME = "REGISTRY_DISPLAY_NAME"
    DATASET_TITLE = "DATASET_TITLE"
    PROVIDER_LABEL = "PROVIDER_LABEL"
    PROVENANCE_LABEL = "PROVENANCE_LABEL"


@dataclass(frozen=True)
class SourceMetadataLabel:
    """One name a source is known by, the source it names, and the document that says so."""

    label_id: str
    source_id: str
    kind: SourceMetadataLabelKind
    text: str
    provenance: str

    def __post_init__(self) -> None:
        if not re.search(r"[a-z0-9]", _norm(self.text)):
            raise ValueError(f"{self.label_id}: a label names something")
        if not self.provenance.strip():
            raise ValueError(f"{self.label_id}: a label without provenance is a guess")


@dataclass(frozen=True)
class SourceMetadataContext:
    """The explicit metadata channel. Built by a caller from the registry, never from an answer."""

    version: str
    labels: tuple[SourceMetadataLabel, ...]

    @property
    def declared_sources(self) -> frozenset[str]:
        return frozenset(label.source_id for label in self.labels)

    def labels_for(self, source_ids: Sequence[str]) -> tuple[SourceMetadataLabel, ...]:
        wanted = set(source_ids)
        return tuple(label for label in self.labels if label.source_id in wanted)

    def as_data(self) -> dict[str, object]:
        return {
            "version": self.version,
            "labels": [
                {
                    "label_id": label.label_id,
                    "source_id": label.source_id,
                    "kind": label.kind.value,
                    "text": label.text,
                    "provenance": label.provenance,
                }
                for label in self.labels
            ],
        }

    def digest(self) -> str:
        payload = json.dumps(self.as_data(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def label_spans(lowered: str, text: str) -> list[tuple[int, int]]:
    """Every whole occurrence of a label in `lowered`: its exact characters, whitespace flexible.

    A name is not inflected, so a label is matched as written, never under the inflection policy.
    """
    parts = _norm(text).split()
    pattern = r"(?<![a-z0-9])" + r"\s+".join(map(re.escape, parts)) + r"(?![a-z0-9])"
    return [(m.start(), m.end()) for m in re.finditer(pattern, lowered)]


def _claimed(
    lowered: str, labels: Sequence[SourceMetadataLabel]
) -> list[tuple[int, int, SourceMetadataLabel]]:
    """Non-overlapping label occurrences, the longest label first, in text order."""
    taken: list[tuple[int, int, SourceMetadataLabel]] = []
    for label in sorted(labels, key=lambda lb: (-len(_norm(lb.text)), lb.label_id)):
        for start, end in label_spans(lowered, label.text):
            if all(end <= s or start >= e for s, e, _ in taken):
                taken.append((start, end, label))
    return sorted(taken, key=lambda item: item[0])


def split_statement(
    text: str, labels: Sequence[SourceMetadataLabel]
) -> tuple[str, tuple[tuple[str, str], ...]]:
    """One supplied statement, split into its content and the metadata labels it carries."""
    lowered = _norm(text)
    content: list[str] = []
    metadata: list[tuple[str, str]] = []
    last = 0
    for start, end, label in _claimed(lowered, labels):
        content.append(lowered[last:start])
        metadata.append((label.label_id, lowered[start:end]))
        last = end
    content.append(lowered[last:])
    return " | ".join(part for part in content if part.strip()), tuple(metadata)


def mask_labels(text: str, labels: Sequence[SourceMetadataLabel], mask: str) -> str:
    """`text` with every whole label occurrence replaced by `mask`: a name read as a name."""
    lowered = _norm(text)
    pieces: list[str] = []
    last = 0
    for start, end, _label in _claimed(lowered, labels):
        pieces.append(lowered[last:start])
        pieces.append(mask)
        last = end
    pieces.append(lowered[last:])
    return "".join(pieces)


@dataclass(frozen=True)
class TypedStatement:
    """A supplied claim statement after the split: what it reported, and the names it carries."""

    claim_id: str
    content: str
    metadata: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class TypedSupportUniverse:
    """The four origins, kept apart. Content licenses words and numbers; metadata licenses names."""

    version: str
    statements: tuple[TypedStatement, ...]
    structural: PacketStructuralFacts
    trusted: TrustedContext
    metadata: SourceMetadataContext
    labels: tuple[SourceMetadataLabel, ...]
    undeclared_sources: tuple[str, ...]

    @property
    def content_text(self) -> str:
        return " | ".join(s.content for s in self.statements)

    def content_forms(self) -> frozenset[str]:
        return normalized_forms(self.content_text)

    def supplied_numbers(self) -> frozenset[str]:
        """Numbers in what the sources reported, and the packet's structural counts. Never a
        number inside a label."""
        return frozenset(_numbers(self.content_text)) | self.structural.numbers()

    def content_carries(self, phrase: str) -> bool:
        return bool(inflection_spans(self.content_text, phrase))

    def metadata_labels_carrying(self, phrase: str) -> tuple[str, ...]:
        """The labels whose own words contain `phrase` under the inflection policy."""
        return tuple(
            sorted(
                {
                    label_id
                    for s in self.statements
                    for label_id, segment in s.metadata
                    if inflection_spans(segment, phrase)
                }
            )
        )

    def origin_of(self, phrase: str) -> SupportOrigin | None:
        """Where a supplied occurrence of `phrase` comes from, content before metadata."""
        if self.content_carries(phrase):
            return SupportOrigin.SOURCE_CONTENT_STATEMENT
        if self.metadata_labels_carrying(phrase):
            return SupportOrigin.SOURCE_METADATA_LABEL
        return None


def build_typed_support_universe(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    trusted: TrustedContext,
    metadata: SourceMetadataContext,
) -> TypedSupportUniverse:
    """The four origins for one packet. Its statements are its own claims, split by its sources'
    declared labels; a source with no declaration is recorded, never read as content."""
    labels = metadata.labels_for(packet.source_ids)
    statements = []
    for cid in packet.claim_ids:
        if cid not in claim_statements:
            continue
        content, carried = split_statement(claim_statements[cid], labels)
        statements.append(TypedStatement(claim_id=cid, content=content, metadata=carried))
    return TypedSupportUniverse(
        version=SUPPORT_UNIVERSE_VERSION_V2,
        statements=tuple(statements),
        structural=PacketStructuralFacts.from_packet(packet),
        trusted=trusted,
        metadata=metadata,
        labels=labels,
        undeclared_sources=tuple(sorted(set(packet.source_ids) - metadata.declared_sources)),
    )
