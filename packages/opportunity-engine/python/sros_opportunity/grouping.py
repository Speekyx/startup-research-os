"""Grouping candidate Evidence into coherent packets, deterministically.

Mission 1.28 §8. The procedure is `source-native-subject-grouping@1.0.0`.

**Two Evidence rows may share a packet only when they name the SAME
source-native subject.** The subject key is built from identifiers the source
itself published and that the Signal already carries in its scope -- a Wikipedia
article name, a World Bank indicator and geography, a GDELT term under its
language label, a CPV classification. Nothing is parsed out of a claim statement,
because a statement is prose and prose changes when an interpreter version bumps.

**No semantic grouping, in either direction.** `Docker_(software)`, `Podman` and
`Kubernetes` are three subjects and stay three packets. Merging them would be
asserting they are the same thing, which is a `SAME_PROBLEM_FAMILY`-shaped
judgement -- the relation Mission 1.27 parked -- reached by hand instead of by a
classifier. Doing it deterministically would not make it deterministic; it would
make it unargued. Mission 1.28 §8 forbids inventing semantic equivalence
deterministically and this module has no path to it: there is no string distance,
no token overlap, no stem, no synonym table and no threshold.

**A packet may be a single row, and that is a real answer.** `group_by_subject`
does not drop singletons: whether one row is enough is `sufficiency.py`'s
question, and silently discarding the groups that will fail would hide the shape
of the corpus from the report.

**Mission 1.30 added the one exception, and it is a registry rather than a rule.**
A source-native key starts with the source id, so evidence from two source
families could never share a packet however obviously it concerned the same
subject. `CanonicalSubjectRegistry` maps EXACT rendered keys onto a canonical
subject, by equality and by nothing else, with a stated basis per entry. Passing
no registry leaves the behaviour of 1.0.0 exactly unchanged; an unmapped
identifier keeps its own key and its own packet either way.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .facets import EvidenceFacets
from .subjects import CanonicalSubjectRegistry

__all__ = [
    "GROUPING_PROCEDURE_VERSION",
    "SubjectKey",
    "CandidateGroup",
    "subject_key",
    "group_by_subject",
]

GROUPING_PROCEDURE_VERSION = "source-native-subject-grouping@1.1.0"


@dataclass(frozen=True, order=True)
class SubjectKey:
    """A source-native subject, addressable and comparable by equality only.

    `parts` are ordered and already normalised by the source: no case folding, no
    stripping of punctuation, no transliteration. `Docker_(software)` is the name
    Wikimedia publishes and it is kept verbatim, for the same reason
    `observation_key` escapes rather than restricts (Mission 1.9.3): a key format
    that tidied real values would silently merge two subjects.
    """

    source_id: str
    scheme: str
    parts: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.source_id}:{self.scheme}:{'|'.join(self.parts)}"


def _strs(scope: Mapping[str, Any], field: str) -> tuple[str, ...]:
    value = scope.get(field)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(sorted(str(item) for item in value))


def subject_key(
    source_id: str, signal_type_id: str | None, scope: Mapping[str, Any] | None
) -> SubjectKey | None:
    """The subject a Signal is about, or None where the type has no rule.

    None means *this signal type has no registered subject rule*, which sends the
    row to its own singleton group rather than into somebody else's packet. A
    fallback that grouped unknown types together would put two unrelated things
    in one packet on the strength of both being unrecognised.
    """
    if signal_type_id is None or scope is None:
        return None

    if signal_type_id == "content_request_change":
        platforms = _strs(scope, "content_platforms")
        contents = _strs(scope, "content_ids")
        if not contents:
            return None
        return SubjectKey(source_id, "content", platforms + contents)

    if signal_type_id in ("lexical_frequency_change", "lexical_frequency_contrast"):
        terms = _strs(scope, "terms")
        labels = _strs(scope, "source_language_labels")
        if not terms:
            return None
        return SubjectKey(source_id, "lexical-term", labels + terms)

    if signal_type_id == "numeric_period_change":
        metrics = _strs(scope, "metric_ids")
        geographies = _strs(scope, "geography_codes")
        if not metrics:
            return None
        return SubjectKey(source_id, "metric-geography", metrics + geographies)

    if signal_type_id == "community_question_volume":
        # Mission 1.30, ADR-034. The site AND the tag: the same tag string means
        # different things on different sites, so a key carrying only the tag
        # would merge two vocabularies.
        tags = _strs(scope, "community_tags")
        sites = _strs(scope, "community_sites")
        if not tags:
            return None
        return SubjectKey(source_id, "community-tag", sites + tags)

    if signal_type_id == "procurement_value_contrast":
        codes = _strs(scope, "classification_codes")
        scheme = str(scope.get("classification_scheme") or "")
        if not codes or not scheme:
            return None
        # The DIVISION, which is the first two digits of a CPV code and the
        # coarsest grouping the scheme itself defines. Mission 1.15.9 already
        # established that two divisions are two markets; grouping at the full
        # eight-digit code would split one procurement cohort into four packets
        # for a distinction the notices themselves do not draw.
        divisions = tuple(sorted({code[:2] for code in codes if len(code) >= 2}))
        return SubjectKey(source_id, f"{scheme}-division", divisions)

    return None


@dataclass(frozen=True)
class CandidateGroup:
    """Evidence rows sharing one subject, source-native or canonical."""

    key: SubjectKey | None
    facets: tuple[EvidenceFacets, ...]
    #: Set where a reviewed registry mapped this group's source-native keys onto
    #: one canonical subject. `key` is then None, because the group has several
    #: source-native keys and naming one would make its source the subject's
    #: owner.
    canonical_subject_id: str | None = None

    @property
    def label(self) -> str:
        if self.canonical_subject_id is not None:
            return f"subject:{self.canonical_subject_id}"
        return str(self.key) if self.key is not None else "UNGROUPED"


def group_by_subject(
    rows: Sequence[tuple[EvidenceFacets, Mapping[str, Any] | None]],
    registry: CanonicalSubjectRegistry | None = None,
) -> list[CandidateGroup]:
    """Group by subject key, ordered so the result is reproducible.

    Rows whose signal type has no subject rule each become their own group,
    labelled `UNGROUPED`, rather than being merged or discarded.

    When a `registry` is supplied and a rendered source-native key appears in it,
    the CANONICAL subject id becomes the group token, so two source families that
    a person mapped to one subject land in one packet. An unmapped key is
    untouched, and passing no registry reproduces 1.0.0 exactly.
    """
    buckets: dict[str, list[EvidenceFacets]] = defaultdict(list)
    keys: dict[str, SubjectKey | None] = {}
    ungrouped: list[CandidateGroup] = []

    for facets, scope in rows:
        key = subject_key(facets.source_id, facets.signal_type_id, scope)
        if key is None:
            ungrouped.append(CandidateGroup(None, (facets,)))
            continue
        canonical = registry.subject_for(str(key)) if registry is not None else None
        token = canonical if canonical is not None else str(key)
        # A canonical group has NO single SubjectKey, because it has several --
        # one per contributing source. Recording the first would name one source
        # as the subject's owner, so it records none and the LABEL carries the
        # identity.
        keys[token] = None if canonical is not None else key
        buckets[token].append(facets)

    groups = [
        CandidateGroup(
            keys[token],
            tuple(sorted(buckets[token], key=lambda f: f.evidence_id)),
            canonical_subject_id=token if keys[token] is None else None,
        )
        for token in sorted(buckets)
    ]
    groups.extend(sorted(ungrouped, key=lambda g: g.facets[0].evidence_id))
    return groups
