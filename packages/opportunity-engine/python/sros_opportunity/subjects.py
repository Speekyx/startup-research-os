"""Canonical subjects: the one way Evidence from two sources may share a packet.

Mission 1.30 §4. Mission 1.28's grouping is **source-scoped by construction** --
a `SubjectKey` starts with the source id, so a Wikimedia packet and a Stack
Exchange packet could never merge however obviously they were about the same
thing. That is the right default, and this is the only mechanism §4 permits for
relaxing it: an explicit registry mapping reviewed in data.

**Matching is by EQUALITY on the full rendered key, and by nothing else.** There
is no string distance, no token overlap, no stem, no synonym table, no embedding
and no threshold. An identifier appears in the registry or it does not; an
unmapped identifier keeps its source-native key and its own packet, exactly as
before.

**This is not `SAME_PROBLEM_FAMILY` under another name**, and the difference is
not a matter of degree. That relation asks whether two OBSERVATIONS express the
same problem -- a judgement about meaning, made per pair, at scale, which
Mission 1.27 parked. This asserts that two IDENTIFIERS, in two published
vocabularies, name the same SUBJECT. It is decided once by a person reading two
pages, written down with its basis, and checkable by anybody who reads the same
two pages.

**Every entry states a basis and the loader requires it.** A mapping with no
stated basis is an assertion nobody can re-check, which is the same rule
`SourcePolicyStanding` and `evidence_independence_groups` already follow.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

from .scopes import SubjectScopeType

__all__ = [
    "SUBJECT_REGISTRY_VERSION",
    "CanonicalSubject",
    "SubjectIdentifier",
    "CanonicalSubjectRegistry",
    "load_subject_registry",
]

SUBJECT_REGISTRY_VERSION = "canonical-subject-registry@1.1.0"


@dataclass(frozen=True)
class SubjectIdentifier:
    """One source-native key, and why a person mapped it here."""

    key: str
    source_id: str
    basis: str

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("a subject identifier needs the source-native key it maps")
        if not self.basis.strip():
            raise ValueError(
                f"{self.key!r}: basis is required. A mapping with no stated basis is an "
                "assertion nobody can re-check, and this one joins evidence across "
                "source families"
            )


@dataclass(frozen=True)
class CanonicalSubject:
    subject_id: str
    display_name: str
    description: str
    identifiers: tuple[SubjectIdentifier, ...]
    #: Mission 1.34 §1. WHAT LEVEL OF THING this subject is, declared by the
    #: person who wrote the entry rather than derived from any source. Required
    #: at 1.1.0: the description already said it in prose -- *the Docker
    #: container platform* -- and a level a machine cannot read is a level that
    #: cannot stop a category observation being attached to a product.
    #:
    #: This is NOT a parent, a category or a relation. It says what the subject
    #: IS, and says nothing about what contains it (§33).
    scope_type: SubjectScopeType

    def __post_init__(self) -> None:
        if not self.identifiers:
            raise ValueError(
                f"{self.subject_id!r}: a canonical subject with no identifiers maps "
                "nothing and would silently do nothing"
            )


@dataclass(frozen=True)
class CanonicalSubjectRegistry:
    """Rendered source-native key -> canonical subject id."""

    registry_version: str
    subjects: tuple[CanonicalSubject, ...]

    def __post_init__(self) -> None:
        seen: dict[str, str] = {}
        for subject in self.subjects:
            for identifier in subject.identifiers:
                if identifier.key in seen:
                    raise ValueError(
                        f"{identifier.key!r} is mapped to both {seen[identifier.key]!r} "
                        f"and {subject.subject_id!r}. One identifier names one subject, "
                        "or the mapping decides nothing"
                    )
                seen[identifier.key] = subject.subject_id

    def subject_for(self, rendered_key: str) -> str | None:
        """The canonical subject id for a rendered key, or None.

        **None is the common and correct answer.** An unmapped identifier is not
        an error and not a gap: it keeps its own packet, which is what every
        subject did before this registry existed.
        """
        for subject in self.subjects:
            for identifier in subject.identifiers:
                if identifier.key == rendered_key:
                    return subject.subject_id
        return None

    def display_name(self, subject_id: str) -> str:
        for subject in self.subjects:
            if subject.subject_id == subject_id:
                return subject.display_name
        return subject_id


def load_subject_registry(path: str | pathlib.Path) -> CanonicalSubjectRegistry:
    raw: dict[str, Any] = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    subjects = []
    for entry in raw.get("subjects") or ():
        subjects.append(
            CanonicalSubject(
                subject_id=str(entry["subject_id"]),
                display_name=str(entry.get("display_name") or entry["subject_id"]),
                description=str(entry.get("description") or ""),
                identifiers=tuple(
                    SubjectIdentifier(
                        key=str(item["key"]),
                        source_id=str(item["source_id"]),
                        basis=str(item.get("basis") or ""),
                    )
                    for item in entry.get("identifiers") or ()
                ),
                # Required, with no default. A subject whose level nobody
                # declared would be silently classified by whichever consumer
                # read it first.
                scope_type=SubjectScopeType(str(entry["scope_type"])),
            )
        )
    return CanonicalSubjectRegistry(
        registry_version=str(raw.get("registry_version") or ""),
        subjects=tuple(subjects),
    )
