"""Assertion context: whether a text ASSERTS a concept, read in the field it sits in.

Mission 1.84.10. The v1.0.0 output gate refused a forbidden phrase wherever it appeared, and Mission
1.84.9's one answer used every refused phrase only to say what the packet does NOT establish: in a
denial, in its list of unsupported commercial claims, in a statement it classified
`UNKNOWN_REQUIRES_EVIDENCE` and in a request for evidence. A token scan cannot tell those apart from
an assertion, and a gate that cannot tell them apart refuses the answer the prompt asked for.

This module is the repair, and it is deliberately NOT a general language engine. It reuses what the
claim guard already proved (the denial markers, the sentence split, the token rules) and adds three
bounded, deterministic things the guard lacked:

1. **CLAUSE SCOPE.** A denial scopes the clause it sits in, never the whole sentence. The guard
   cleared every term that followed a marker anywhere earlier in the sentence, so *these rows are not
   unscored; they are scored* read as a denial. Clauses break at a semicolon, a dash, a contrastive
   conjunction, a non-restrictive relative clause and a coordinated clause with its own subject; a
   plain comma inside a list does not break one, so *does not establish need, gap or willingness to
   pay* stays one denial.
2. **RE-ASSERTION.** A denial followed by a contrastive continuation that predicates something of the
   same subject re-asserts it: *actual expenditure is not established, but is probably substantial*.
3. **FIELD CONTEXT.** Whether text is asserted at all depends on the field: a commercial claim
   listed as NOT supported, an uncertainty, a request for evidence and a statement the answer itself
   classifies as unknown are not assertions of their content, and each has a SHAPE it must keep. A
   request that stops being request-shaped (*actual expenditure was 10 million EUR*) is read as the
   assertion it has become.

**Nothing is whitelisted.** No sentence, phrase or answer is exempted by content: every rule here is
stated over grammar, field and the typed support universe, and the tests run it on unseen
equivalents. **No forbidden concept was removed**; they are refused as ASSERTIONS rather than as
strings.

**The support universe is typed and has three separate channels** (§15, §19):

    A  SOURCE_STATEMENTS                        the supplied claim statements
    B  PACKET_STRUCTURAL_FACTS                  ids, families, dimensions, scorability, identity
    C  TRUSTED_LIMITING_OR_DEFINITIONAL_CONTEXT typed facts with provenance, passed explicitly

**The prompt text is not observed evidence.** Nothing reads a system region. A trusted fact reaches
the gate only as a typed `TrustedFact` with a provenance, and what it licenses is bounded to the
definitional IDENTIFIERS it carries (an eForms business term such as `BT-161`): never its words, never
its numbers as magnitudes, and never a concept it limits.
"""

from __future__ import annotations

import enum
import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from .dimensions import EvidenceDimension
from .guards import DENIAL_MARKERS, FORBIDDEN_TERMS, VALIDATION_WORDS, _sentences
from .packet import OpportunityEvidencePacket
from .validation import (
    FieldAudit,
    PersistenceDecision,
    StatementSupport,
    SynthesisAudit,
    _numbers,
    _string_list,
)

__all__ = [
    "ASSERTION_GUARD_VERSION",
    "ASSERTION_AUDIT_VERSION",
    "PERSISTENCE_GATE_VERSION_V1_2",
    "SUPPORT_UNIVERSE_VERSION",
    "PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE",
    "DENIAL_MARKERS_V1_3",
    "SCORE_TERMS",
    "CERTAINTY_MARKERS",
    "SUPPORT_PREDICATES",
    "Disposition",
    "Shape",
    "FieldContext",
    "OccurrenceState",
    "Occurrence",
    "ForbiddenConcept",
    "TrustedFactKind",
    "TrustedFact",
    "TrustedContext",
    "SupportCategory",
    "PacketStructuralFacts",
    "SupportUniverse",
    "build_support_universe",
    "canonical_dimension_phrase",
    "classify",
    "is_asserted",
    "is_request_shaped",
    "is_uncertainty_shaped",
    "audit_text",
    "audit_output",
    "evaluate_persistence_v1_2",
]

#: The successor of `opportunity-claim-guard@1.2.0`, which stays in `guards.py` byte-identical so
#: every gate that used it still resolves against the code it ran.
ASSERTION_GUARD_VERSION = "opportunity-claim-guard@1.3.0"
#: The successor of `opportunity-synthesis-audit@1.2.0`, which stays in `validation.py`.
ASSERTION_AUDIT_VERSION = "opportunity-synthesis-audit@1.3.0"
#: The successor of `opportunity-synthesis-persistence-gate@1.1.0`, which stays in `validation.py`.
PERSISTENCE_GATE_VERSION_V1_2 = "opportunity-synthesis-persistence-gate@1.2.0"
SUPPORT_UNIVERSE_VERSION = "opportunity-support-universe@1.0.0"

#: §19. Nothing in this module reads a prompt region. A trusted fact is typed, has a provenance,
#: and arrives through the explicit `TrustedContext` channel or not at all.
PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE = True


# ============================================================================= dispositions


class Disposition(enum.Enum):
    """What a piece of output text DOES, which decides whether its content is asserted."""

    #: The content is asserted as true of the packet or the world, and must be supported.
    SUPPORTED_ASSERTION = "SUPPORTED_ASSERTION"
    #: The content is a hypothesis to test. It may not be promoted to a conclusion.
    HYPOTHESIS_TO_VALIDATE = "HYPOTHESIS_TO_VALIDATE"
    #: The content is listed as NOT supported. Naming it is the enumeration §6 requires.
    EXPLICITLY_NOT_SUPPORTED = "EXPLICITLY_NOT_SUPPORTED"
    #: The content is stated as unknown. It is not an assertion, and it must stay uncertainty-shaped.
    UNKNOWN_REQUIRES_EVIDENCE = "UNKNOWN_REQUIRES_EVIDENCE"
    #: The content names what would have to be observed. It must stay request-shaped.
    FUTURE_EVIDENCE_REQUEST = "FUTURE_EVIDENCE_REQUEST"
    #: The content restates a structural fact about the packet (ids, dimensions, scorability).
    STRUCTURAL_FACT = "STRUCTURAL_FACT"
    #: A limiting or definitional fact from the trusted channel. A support category, never a
    #: disposition an output field may claim for itself.
    TRUSTED_LIMITING_FACT = "TRUSTED_LIMITING_FACT"


class Shape(enum.Enum):
    """The grammatical form a field's text must keep for its disposition to hold."""

    FREE = "FREE"  # prose; every clause read on its own terms
    REQUEST = "REQUEST"  # the head clause names what would have to be observed
    UNCERTAINTY = "UNCERTAINTY"  # the head clause states what is not known
    LABELLED = "LABELLED"  # framed by an explicit classification label the answer carries
    ENUMERATION = "ENUMERATION"  # closed vocabulary or identifiers, checked structurally


@dataclass(frozen=True)
class FieldContext:
    """One output field, what its text does, and the shape it must keep.

    `disposition` is None only for a field whose items carry their own label, and then
    `item_label_key` names the item key the disposition is read from.
    """

    field_name: str
    disposition: Disposition | None
    shape: Shape
    rationale: str
    item_label_key: str | None = None
    item_text_key: str | None = None

    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError(f"{self.field_name}: a field context states why")
        if (self.disposition is None) == (self.item_label_key is None):
            raise ValueError(
                f"{self.field_name}: a field either has one disposition or reads it from a label"
            )
        if self.disposition is Disposition.TRUSTED_LIMITING_FACT:
            raise ValueError(
                f"{self.field_name}: TRUSTED_LIMITING_FACT is a support category of the trusted "
                "channel, and an output field cannot claim it for itself"
            )


# ============================================================================= the classifier

_TOKEN = re.compile(r"[a-z0-9]+")

#: The claim guard's markers, plus the negations it did not know, matched on token boundaries so
#: `never` no longer matches inside `nevertheless`.
DENIAL_MARKERS_V1_3: tuple[str, ...] = (
    *DENIAL_MARKERS,
    "none",
    "nor",
    "no longer",
    "unestablished",
    "unverified",
    "unproven",
    "undetermined",
    "doesn't",
    "don't",
    "didn't",
    "isn't",
    "aren't",
    "wasn't",
    "weren't",
    "can't",
    "won't",
    "wouldn't",
    "hasn't",
    "haven't",
)

#: A marker followed by one of these intensifies rather than denies: *is not only X*.
_NOT_A_DENIAL = r"\s+(?:only|just|merely|simply)\b"
_MARKER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (
        marker,
        re.compile(
            r"(?<![a-z0-9'])" + r"\s+".join(map(re.escape, marker.split())) + r"(?![a-z0-9'])"
        ),
    )
    for marker in DENIAL_MARKERS_V1_3
)

#: Single tokens that negate the noun phrase they head: *no score*, *not scored*.
_NEGATORS = frozenset({"no", "not", "never", "nor", "none", "without", "neither"})
#: What may sit between such a negator and the term it negates.
_FILLER = frozenset(
    {"a", "an", "the", "any", "same", "as", "yet", "necessarily", "even", "such", "evidence", "of"}
)

_CLAUSE_BOUNDARY = re.compile(
    r"(?P<hard>\s*;\s*|\s+--\s+|\s*—\s*|\s+-\s+)"
    r"|(?P<contrast>,?\s+(?:but|yet|however|although|though|whereas|while|nevertheless|"
    r"nonetheless)\b,?\s*)"
    r"|(?P<relative>,\s+(?=(?:which|who|whose)\b))"
    r"|(?P<splice>,\s+(?=(?:it|they|these|those|this|there|we)\s+(?:is|are|was|were|has|have|"
    r"had|would|will|remain|remains)\b))"
    r"|(?P<coord>,?\s+(?:and|or|so|then)\s+(?=(?:[a-z0-9_'-]+\s+){1,3}(?:is|are|was|were|has|"
    r"have|had|would|will|can|could|may|might|must|should|shows?|proves?|establish(?:es)?|"
    r"demonstrates?|exists?|remains?|seems?|appears?|does|do|did)\b))"
)
_LEADING_CONTRAST = re.compile(
    r"^(?:but|yet|however|although|though|whereas|nevertheless|nonetheless)\b,?\s*"
)

#: `<term> is not / remains unknown / cannot ...`: the term is the subject of its own denial.
_SUBJECT_DENIAL = re.compile(
    r"^\s*(?::\s*(?:not|never|no|none|unknown|unestablished|unsupported|unproven|unverified|"
    r"undetermined|unclear|absent|missing)\b"
    r"|(?:is|are|was|were|has|have|had|remains?|remained|stays?)\s+(?:still\s+|yet\s+)?"
    r"(?:not\b(?!" + _NOT_A_DENIAL + r")|never\b|no\b|unknown\b|unestablished\b|unsupported\b|"
    r"unproven\b|unverified\b|undetermined\b|unclear\b|unobserved\b|absent\b|missing\b)"
    r"|(?:cannot|can\s+not|could\s+not|does\s+not|do\s+not|did\s+not|would\s+not|will\s+not|"
    r"may\s+not|might\s+not|must\s+not|should\s+not|isn't|aren't|wasn't|weren't|hasn't|"
    r"haven't|can't|doesn't|don't|didn't)\b)"
)

_REQUEST_HEADS = (
    "evidence|identification|observation|observations|data|record|records|confirmation|"
    "measurement|measurements|documentation|verification|determination|information|proof|"
    "count|counts|statement|statements"
)
_REQUEST_CONNECTORS = (
    "of|that|on|about|describing|showing|whether|for|from|identifying|establishing|indicating|"
    "regarding|concerning|linking|naming"
)
_REQUEST_GOVERNS = re.compile(rf"\b(?:{_REQUEST_HEADS})\s+(?:{_REQUEST_CONNECTORS})\b")
_REQUIREMENT = re.compile(
    r"\b(?:would|will|is|are)\s+(?:be\s+)?(?:required|needed|necessary)\b"
    r"|\b(?:required|needed|necessary)\s+to\b|\bwould\s+(?:need|require)\b|\brequires?\b"
    r"|\bremains?\s+to\s+be\b|\bwould\s+have\s+to\s+be\b"
    r"|\bmust\s+be\s+(?:observed|obtained|collected|established|shown)\b"
)
_REQUEST_SHAPE = re.compile(
    r"^\s*(?:(?:a|an|the)\s+)?(?:(?:direct|independent|further|additional|first-party|primary|"
    r"specific|new|more|dated|public|named|documented|verifiable)\s+)*"
    rf"(?:{_REQUEST_HEADS})\s+(?:{_REQUEST_CONNECTORS})\b"
)
_UNCERTAINTY_SHAPE = re.compile(
    r"^\s*(?:whether|how|what|which|who|when|why|if|to\s+what\s+extent)\b"
    r"|^\s*(?:it\s+(?:is|remains)\s+)?(?:unknown|unclear|uncertain|not\s+established|"
    r"not\s+known|undetermined|unverified)\b"
    r"|^\s*(?:no\s+(?:statement|evidence|claim)|nothing)\b"
    r"|\b(?:is|are|remains?)\s+(?:unknown|unclear|uncertain|not\s+established|not\s+known|"
    r"undetermined|unverified)\b"
)

#: A clause that opens by predicating of an elided or pronoun subject, after a CONTRASTIVE boundary
#: that follows a denial. Only a contrast signals a reversal: after a semicolon or a plain `and` a
#: pronoun usually introduces a new remark, and reading it as a re-assertion would refuse sound text.
_REPREDICATION = re.compile(
    r"^\s*(?:(?:it|they|this|these|that|those)\s+)?(?:is|are|was|were|remains?|seems?|appears?|"
    r"looks?|may|might|could|would|will|must|should|has|have|had|probably|likely|presumably|"
    r"apparently|clearly|certainly|definitely|surely|evidently|arguably|possibly|perhaps|still|"
    r"indeed)\b"
)
#: Inside the denying clause, a HEDGED re-predication: *is not established and is probably
#: substantial*. A contrast never survives inside a clause (it is a boundary), so the only
#: in-clause form is `and` plus a hedge, which is what makes the continuation an assertion.
_INLINE_REPREDICATION = re.compile(
    r"\band\s+(?:(?:it|they|this|these)\s+)?(?:(?:is|are|was|were|remains?|seems?|appears?|may|"
    r"might|could|would|will|must|should)\s+)?(?:probably|likely|presumably|apparently|clearly|"
    r"certainly|definitely|surely|evidently|arguably|possibly|perhaps)\b(?P<rest>.*)$"
)
#: A continuation that talks about testing, needing or not knowing is not a re-assertion.
_EXEMPT = re.compile(
    r"\b(?:test|tests|tested|testing|investigat\w*|evidence|evidenced|requir\w*|need|needs|"
    r"needed|verif\w*|observ\w*|establish\w*|examin\w*|determin\w*|unknown|unclear|uncertain|"
    r"whether|confirm\w*|measur\w*)\b"
)

#: §14. A score is asserted by any of these forms and denied only by grammar.
SCORE_TERMS: tuple[str, ...] = ("scored", "score")
#: Words that promote a hypothesis, an unknown or a request to a conclusion.
CERTAINTY_MARKERS: tuple[str, ...] = (
    "definitely",
    "certainly",
    "clearly",
    "obviously",
    "undoubtedly",
    "demonstrably",
    "unquestionably",
)
#: A NOT-supported item that says it IS established contradicts the field it sits in.
SUPPORT_PREDICATES: tuple[str, ...] = (
    "establish",
    "establishes",
    "established",
    "demonstrates",
    "demonstrated",
    "shows",
    "shown",
    "proves",
    "proven",
    "confirms",
    "confirmed",
    "supports",
    "supported",
    "evidences",
)


def _norm(text: str) -> str:
    return text.lower().replace("’", "'")


def _phrase_tokens(phrase: str) -> tuple[str, ...]:
    return tuple(_TOKEN.findall(_norm(phrase)))


def _spans(lowered: str, phrase: str) -> list[tuple[int, int]]:
    """Every occurrence of `phrase` as a whole-token sequence, plurals folded, as character spans."""
    parts = _phrase_tokens(phrase)
    if not parts:
        return []
    tokens = [(m.group(), m.start(), m.end()) for m in _TOKEN.finditer(lowered)]
    found: list[tuple[int, int]] = []
    for index in range(len(tokens) - len(parts) + 1):
        window = tokens[index : index + len(parts)]
        if all(w == p or w == p + "s" for (w, _, _), p in zip(window, parts, strict=True)):
            found.append((window[0][1], window[-1][2]))
    return found


@dataclass(frozen=True)
class _Clause:
    text: str
    boundary: str  # start | hard | contrast | relative | splice | coord


def _clauses(sentence: str) -> list[_Clause]:
    lowered = _norm(sentence)
    pieces: list[_Clause] = []
    last, kind = 0, "start"
    for match in _CLAUSE_BOUNDARY.finditer(lowered):
        pieces.append(_Clause(lowered[last : match.start()], kind))
        kind = match.lastgroup or "hard"
        last = match.end()
    pieces.append(_Clause(lowered[last:], kind))
    clauses: list[_Clause] = []
    for piece in pieces:
        text = piece.text.strip()
        opened = _LEADING_CONTRAST.match(text)
        if opened and piece.boundary != "start":
            clauses.append(_Clause(text[opened.end() :], "contrast"))
        elif text:
            clauses.append(_Clause(text, piece.boundary))
    return [c for c in clauses if c.text]


def _marker_before(clause: str, start: int) -> str | None:
    head = clause[:start]
    if re.match(r"^no\b", head):
        return "no"
    for marker, pattern in _MARKER_PATTERNS:
        for found in pattern.finditer(head):
            if re.match(_NOT_A_DENIAL, head[found.end() :]):
                continue
            return marker
    return None


def _negated_noun_phrase(clause: str, start: int) -> bool:
    head = clause[:start]
    if re.search(r"(?:rather\s+than|instead\s+of)\s+(?:(?:the|a|an|any)\s+)?$", head):
        return True
    for token in reversed(_TOKEN.findall(head)[-5:]):
        if token in _NEGATORS:
            return True
        if token not in _FILLER:
            return False
    return False


def _denies(text: str) -> bool:
    return (
        any(t in _NEGATORS for t in _TOKEN.findall(text))
        or _marker_before(text, len(text)) is not None
    )


class OccurrenceState(enum.Enum):
    ASSERTED = "ASSERTED"
    DENIED = "DENIED"
    UNCERTAIN = "UNCERTAIN"
    REQUESTED = "REQUESTED"
    SCOPED_BY_FIELD = "SCOPED_BY_FIELD"


@dataclass(frozen=True)
class Occurrence:
    phrase: str
    sentence: str
    clause: str
    state: OccurrenceState
    why: str

    @property
    def asserted(self) -> bool:
        return self.state is OccurrenceState.ASSERTED


def _state(clause: str, start: int, end: int, scoped_by_field: bool) -> tuple[OccurrenceState, str]:
    if scoped_by_field:
        return OccurrenceState.SCOPED_BY_FIELD, "inside the head clause the field frames"
    marker = _marker_before(clause, start)
    if marker is not None:
        state = OccurrenceState.UNCERTAIN if marker == "whether" else OccurrenceState.DENIED
        return state, f"under {marker!r} in the same clause"
    if _negated_noun_phrase(clause, start):
        return OccurrenceState.DENIED, "a negated noun phrase"
    if _SUBJECT_DENIAL.match(clause[end:]):
        return OccurrenceState.DENIED, "the subject of its own denial"
    if _REQUEST_GOVERNS.search(clause[:start]) and _REQUIREMENT.search(clause):
        return OccurrenceState.REQUESTED, "named as evidence that would be required"
    return OccurrenceState.ASSERTED, "asserted"


def _reasserted(clause: str, end: int, following: _Clause | None) -> str | None:
    inline = _INLINE_REPREDICATION.search(clause[end:])
    if inline and not _denies(inline.group("rest")) and not _EXEMPT.search(inline.group("rest")):
        return "denied, then predicated of again in the same clause"
    if (
        following is not None
        and following.boundary == "contrast"
        and _REPREDICATION.match(following.text)
        and not _denies(following.text)
        and not _EXEMPT.search(following.text)
    ):
        return f"denied, then re-asserted after a {following.boundary} boundary"
    return None


def classify(text: str, phrase: str, *, scoped_head: bool = False) -> tuple[Occurrence, ...]:
    """Every occurrence of `phrase` in `text`, each with whether it is asserted and why.

    `scoped_head` frames the FIRST clause of the FIRST sentence as request or uncertainty content,
    because the field says so and the text kept the shape the field requires. Nothing after that
    clause inherits the frame.
    """
    found: list[Occurrence] = []
    for s_index, sentence in enumerate(_sentences(text)):
        clauses = _clauses(sentence)
        for c_index, clause in enumerate(clauses):
            for start, end in _spans(clause.text, phrase):
                head = scoped_head and s_index == 0 and c_index == 0
                state, why = _state(clause.text, start, end, head)
                if state is not OccurrenceState.ASSERTED:
                    following = clauses[c_index + 1] if c_index + 1 < len(clauses) else None
                    again = _reasserted(clause.text, end, following)
                    if again is not None:
                        state, why = OccurrenceState.ASSERTED, again
                found.append(Occurrence(phrase, sentence.strip(), clause.text, state, why))
    return tuple(found)


def is_asserted(text: str, phrase: str, *, scoped_head: bool = False) -> bool:
    return any(o.asserted for o in classify(text, phrase, scoped_head=scoped_head))


def _head_clause(text: str) -> str:
    sentences = _sentences(text)
    if not sentences:
        return ""
    clauses = _clauses(sentences[0])
    return clauses[0].text if clauses else ""


def is_request_shaped(text: str) -> bool:
    """Whether the head clause names what would have to be observed, rather than asserting it."""
    return bool(_REQUEST_SHAPE.match(_head_clause(text)))


def is_uncertainty_shaped(text: str) -> bool:
    """Whether the head clause states what is not known, rather than asserting it."""
    return bool(_UNCERTAINTY_SHAPE.search(_head_clause(text)))


# ============================================================================= the support universe


@dataclass(frozen=True)
class ForbiddenConcept:
    """A transformation the packet does not license, the phrases that express it, what it is NOT."""

    name: str
    phrases: tuple[str, ...]
    never: str

    def __post_init__(self) -> None:
        if not self.phrases or not self.never.strip():
            raise ValueError(f"{self.name}: a forbidden concept names phrases and what it is not")


class TrustedFactKind(enum.Enum):
    DEFINITIONAL = "DEFINITIONAL"  # what a source-native term is
    LIMITING = "LIMITING"  # what a measurement is NOT


_IDENTIFIER = re.compile(r"\b([A-Za-z]{1,6})-(\d+)\b")


@dataclass(frozen=True)
class TrustedFact:
    """One limiting or definitional fact, typed, with where it came from.

    It licenses exactly its definitional identifiers (`BT-161`) and nothing else: not its words,
    not its numbers as magnitudes, and never a concept it names in `never_supports`.
    """

    fact_id: str
    kind: TrustedFactKind
    text: str
    provenance: str
    never_supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.provenance.strip():
            raise ValueError(f"{self.fact_id}: a trusted fact without provenance is prompt text")

    @property
    def identifiers(self) -> tuple[str, ...]:
        return tuple(sorted({f"{p.upper()}-{n}" for p, n in _IDENTIFIER.findall(self.text)}))


@dataclass(frozen=True)
class TrustedContext:
    """The explicit channel. Empty unless a caller builds it, and never read from a prompt."""

    version: str
    facts: tuple[TrustedFact, ...]

    @property
    def identifiers(self) -> frozenset[str]:
        return frozenset(i for f in self.facts for i in f.identifiers)

    @property
    def schemes(self) -> frozenset[str]:
        return frozenset(i.split("-", 1)[0] for i in self.identifiers)

    def as_data(self) -> dict[str, object]:
        return {
            "version": self.version,
            "facts": [
                {
                    "fact_id": f.fact_id,
                    "kind": f.kind.value,
                    "text": f.text,
                    "provenance": f.provenance,
                    "never_supports": list(f.never_supports),
                    "identifiers": list(f.identifiers),
                }
                for f in self.facts
            ],
        }

    def digest(self) -> str:
        payload = json.dumps(self.as_data(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SupportCategory(enum.Enum):
    SOURCE_STATEMENTS = "SOURCE_STATEMENTS"
    PACKET_STRUCTURAL_FACTS = "PACKET_STRUCTURAL_FACTS"
    TRUSTED_LIMITING_OR_DEFINITIONAL_CONTEXT = "TRUSTED_LIMITING_OR_DEFINITIONAL_CONTEXT"


@dataclass(frozen=True)
class PacketStructuralFacts:
    """B. What the packet says about itself, as facts rather than as prose."""

    subject_label: str
    evidence_ids: tuple[str, ...]
    claim_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    packet_dimensions: frozenset[EvidenceDimension]
    supported_dimensions: frozenset[EvidenceDimension]
    size: int
    scoring_eligible_count: int
    independence_summary: str

    @classmethod
    def from_packet(cls, packet: OpportunityEvidencePacket) -> PacketStructuralFacts:
        return cls(
            subject_label=packet.subject_label,
            evidence_ids=tuple(packet.evidence_ids),
            claim_ids=tuple(packet.claim_ids),
            source_families=tuple(packet.source_families),
            packet_dimensions=frozenset(packet.dimensions),
            supported_dimensions=frozenset(packet.counting_dimensions),
            size=packet.size,
            scoring_eligible_count=packet.scoring_eligible_count,
            independence_summary=packet.independence_summary(),
        )

    def numbers(self) -> frozenset[str]:
        counts = {
            self.size,
            self.scoring_eligible_count,
            self.size - self.scoring_eligible_count,
            len(self.source_families),
            len(self.supported_dimensions),
            len(self.packet_dimensions),
            len(self.evidence_ids),
            len(self.claim_ids),
        }
        return frozenset({str(n) for n in counts} | _numbers(self.subject_label))


@dataclass(frozen=True)
class SupportUniverse:
    """A, B and C, kept apart. C contributes identifiers only, never tokens or numbers."""

    version: str
    source_statements: Mapping[str, str]
    structural: PacketStructuralFacts
    trusted: TrustedContext

    @property
    def supplied_text(self) -> str:
        return " ".join(self.source_statements.values())

    def supplied_tokens(self) -> frozenset[str]:
        return frozenset(_TOKEN.findall(_norm(self.supplied_text)))

    def supplied_numbers(self) -> frozenset[str]:
        return frozenset(_numbers(self.supplied_text)) | self.structural.numbers()


def build_support_universe(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    trusted: TrustedContext,
) -> SupportUniverse:
    """The three channels for one packet. The statements are the packet's own claims only."""
    return SupportUniverse(
        version=SUPPORT_UNIVERSE_VERSION,
        source_statements={
            cid: claim_statements[cid] for cid in packet.claim_ids if cid in claim_statements
        },
        structural=PacketStructuralFacts.from_packet(packet),
        trusted=trusted,
    )


def canonical_dimension_phrase(dimension: EvidenceDimension) -> str:
    """§17. The canonical enum term in words: MARKET_ACTIVITY -> "market activity". Derived, never
    transcribed, so no answer's paraphrase can become a licensed phrase."""
    return dimension.value.lower().replace("_", " ")


# ============================================================================= the audit

_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
_MASK = " maskedidentifier "


def _mask_identifiers(text: str, universe: SupportUniverse) -> tuple[str, list[str]]:
    findings: list[str] = []
    known = set(universe.structural.evidence_ids) | set(universe.structural.claim_ids)
    masked = _UUID.sub(lambda m: _MASK if m.group() in known else m.group(), text)

    def replace(match: re.Match[str]) -> str:
        scheme, number = match.group(1).upper(), match.group(2)
        identifier = f"{scheme}-{number}"
        if identifier in universe.trusted.identifiers:
            return _MASK
        if scheme in universe.trusted.schemes:
            findings.append(
                f"the definitional identifier {identifier} is supplied by no trusted limiting or "
                "definitional fact; an external definition is prior knowledge (§7)"
            )
            return _MASK
        return match.group()

    return _IDENTIFIER.sub(replace, masked), findings


def _mask_dimension_terms(text: str, licensed: Iterable[EvidenceDimension]) -> str:
    masked = _norm(text)
    for dimension in licensed:
        words = canonical_dimension_phrase(dimension).split()
        pattern = r"(?<![a-z0-9])" + r"[\s_-]+".join(map(re.escape, words)) + r"(?![a-z0-9])"
        masked = re.sub(pattern, " dimensionterm ", masked)
    return masked


def _concept_findings(
    text: str,
    concepts: Sequence[ForbiddenConcept],
    universe: SupportUniverse,
    *,
    scoped_head: bool,
) -> list[str]:
    findings: list[str] = []
    supplied = universe.supplied_tokens()
    for concept in concepts:
        for phrase in concept.phrases:
            if all(t in supplied for t in _phrase_tokens(phrase)) and _spans(
                _norm(universe.supplied_text), phrase
            ):
                continue
            for occurrence in classify(text, phrase, scoped_head=scoped_head):
                if not occurrence.asserted:
                    continue
                findings.append(
                    f"{concept.name}: {phrase!r} is asserted ({occurrence.why}), and no supplied "
                    f"statement asserts it. This packet is not {concept.never}"
                )
                for fact in universe.trusted.facts:
                    cited = [
                        i for i in fact.identifiers if i.lower() in occurrence.sentence.lower()
                    ]
                    if cited and concept.name in fact.never_supports:
                        findings.append(
                            f"{cited[0]} is restated from the trusted {fact.kind.value.lower()} "
                            f"fact {fact.fact_id}, which limits {concept.name} and can never "
                            "support it"
                        )
                break
    return findings


def _scoring_status_findings(text: str, *, scoped_head: bool) -> list[str]:
    for term in SCORE_TERMS:
        for occurrence in classify(text, term, scoped_head=scoped_head):
            if occurrence.asserted:
                return [
                    f"{term!r} is asserted ({occurrence.why}). Scoring-ready is not scored, no "
                    "score exists in this repository, and REFERENCE_PROFILE_V1 is UNCALIBRATED"
                ]
    return []


def audit_text(
    text: str,
    disposition: Disposition,
    shape: Shape,
    universe: SupportUniverse,
    concepts: Sequence[ForbiddenConcept],
    markers: Sequence[str],
    supported: frozenset[EvidenceDimension],
) -> tuple[StatementSupport, tuple[str, ...]]:
    """One piece of output text, read in its field's context. Returns a verdict and every finding."""
    if not text.strip() or text.strip() == "UNKNOWN_NOT_SUPPORTED":
        return StatementSupport.NOT_FACTUAL, ()
    unsupported: list[str] = []
    exceeded: list[str] = []

    # -- identifiers and numbers, whatever the disposition: nothing may introduce a figure --------
    masked, identifier_findings = _mask_identifiers(text, universe)
    unsupported += identifier_findings
    for number in sorted(_numbers(masked) - universe.supplied_numbers()):
        unsupported.append(
            f"the number {number} appears in no supplied statement and in no structural fact about "
            "the packet"
        )

    asserting = disposition in (Disposition.SUPPORTED_ASSERTION, Disposition.STRUCTURAL_FACT) or (
        disposition is Disposition.HYPOTHESIS_TO_VALIDATE and shape is Shape.FREE
    )
    shaped = shape in (Shape.REQUEST, Shape.UNCERTAINTY)
    scoped_head = False
    if shaped:
        kept = is_request_shaped(text) if shape is Shape.REQUEST else is_uncertainty_shaped(text)
        if kept:
            scoped_head = True
        else:
            wanted, names = (
                ("request", "would have to be observed")
                if shape is Shape.REQUEST
                else ("uncertainty", "is not known")
            )
            exceeded.append(
                f"it is not {wanted}-shaped, so it is read as the assertion it has become. A "
                f"{disposition.value} names what {names}"
            )

    if asserting or shaped:
        exceeded += _concept_findings(text, concepts, universe, scoped_head=scoped_head)
        exceeded += _scoring_status_findings(text, scoped_head=scoped_head)

    if asserting:
        supplied = universe.supplied_tokens()
        masked_terms = _mask_dimension_terms(masked, supported)
        for marker in markers:
            if marker in supplied:
                continue
            if is_asserted(masked_terms, marker):
                unsupported.append(
                    f"{marker!r} appears in no supplied statement; prior knowledge is not "
                    "available as factual support (§7)"
                )
        for term, required in sorted(FORBIDDEN_TERMS.items()):
            if not is_asserted(masked_terms, term):
                continue
            if required is None:
                exceeded.append(
                    f"{term!r} is not supportable by any registered source: no observation in "
                    "this portfolio measures it"
                )
            elif required not in supported:
                exceeded.append(
                    f"{term!r} asserts {required.value}, which no eligible evidence in this "
                    "packet supports"
                )
        for word in sorted(VALIDATION_WORDS):
            if _spans(_norm(text), word.replace("-", " ")):
                exceeded.append(f"{word!r} states a conclusion; this is a hypothesis record")

    if disposition in (
        Disposition.HYPOTHESIS_TO_VALIDATE,
        Disposition.UNKNOWN_REQUIRES_EVIDENCE,
        Disposition.FUTURE_EVIDENCE_REQUEST,
    ):
        promoted = [w for w in CERTAINTY_MARKERS if is_asserted(text, w, scoped_head=False)]
        if not asserting:
            promoted += [
                w for w in sorted(VALIDATION_WORDS) if _spans(_norm(text), w.replace("-", " "))
            ]
        if promoted:
            exceeded.append(
                f"{sorted(set(promoted))} promote a {disposition.value} to a conclusion"
            )

    if disposition is Disposition.EXPLICITLY_NOT_SUPPORTED and shape is Shape.FREE:
        claimed = [p for p in SUPPORT_PREDICATES if is_asserted(text, p)]
        if claimed:
            exceeded.append(
                f"it says the claim is {claimed[0]!r}, which contradicts the NOT-supported field "
                "it sits in"
            )

    if unsupported:
        return StatementSupport.UNSUPPORTED, tuple(unsupported + exceeded)
    if exceeded:
        return StatementSupport.BOUND_EXCEEDED, tuple(exceeded)
    if asserting:
        return StatementSupport.SUPPORTED, ()
    return StatementSupport.NOT_FACTUAL, ()


def audit_output(
    output: Mapping[str, object],
    universe: SupportUniverse,
    policy: Sequence[FieldContext],
    concepts: Sequence[ForbiddenConcept],
    markers: Sequence[str],
    label_dispositions: Mapping[str, Disposition],
) -> SynthesisAudit:
    """Every text in the output, each in its field's context. A field the policy does not name
    fails closed: text nobody classified is text nobody may assume harmless."""
    declared = frozenset(
        d
        for d in EvidenceDimension
        if d.value in set(_string_list(output.get("supported_dimensions")))
    )
    supported = declared & universe.structural.supported_dimensions
    by_name = {fc.field_name: fc for fc in policy}
    audits: list[FieldAudit] = []

    for key in output:
        if key not in by_name:
            audits.append(
                FieldAudit(
                    key,
                    StatementSupport.UNSUPPORTED,
                    (f"{key} has no field context, so its text cannot be read as anything",),
                )
            )

    for fc in policy:
        value = output.get(fc.field_name)
        if fc.shape is Shape.ENUMERATION or value is None:
            continue
        items: list[tuple[str, str, Disposition, Shape]] = []
        if fc.item_label_key is not None:
            for index, item in enumerate(value if isinstance(value, list) else []):
                if not isinstance(item, Mapping):
                    continue
                label = str(item.get(fc.item_label_key) or "")
                disposition = label_dispositions.get(label)
                text = str(item.get(fc.item_text_key or "") or "")
                name = f"{fc.field_name}[{index}].{fc.item_text_key}"
                if disposition is None:
                    audits.append(
                        FieldAudit(
                            name, StatementSupport.UNSUPPORTED, (f"unknown label {label!r}",)
                        )
                    )
                    continue
                shape = (
                    Shape.FREE if disposition is Disposition.SUPPORTED_ASSERTION else Shape.LABELLED
                )
                items.append((name, text, disposition, shape))
        elif isinstance(value, list):
            assert fc.disposition is not None  # noqa: S101 -- guaranteed by FieldContext
            items += [
                (f"{fc.field_name}[{i}]", str(v), fc.disposition, fc.shape)
                for i, v in enumerate(value)
                if isinstance(v, str)
            ]
        elif isinstance(value, str):
            assert fc.disposition is not None  # noqa: S101 -- guaranteed by FieldContext
            items.append((fc.field_name, value, fc.disposition, fc.shape))
        for name, text, disposition, shape in items:
            verdict, findings = audit_text(
                text, disposition, shape, universe, concepts, markers, supported
            )
            audits.append(FieldAudit(name, verdict, findings))

    return SynthesisAudit(audit_version=ASSERTION_AUDIT_VERSION, fields=tuple(audits))


def evaluate_persistence_v1_2(
    output: Mapping[str, object],
    universe: SupportUniverse,
    evidence_to_claim: Mapping[str, str],
    mandatory_unsupported: Sequence[EvidenceDimension],
    *,
    policy: Sequence[FieldContext],
    concepts: Sequence[ForbiddenConcept],
    markers: Sequence[str],
    label_dispositions: Mapping[str, Disposition],
) -> PersistenceDecision:
    """persistence-gate@1.1.0's structural checks unchanged in meaning, its lexical SCORED check
    replaced by the assertion-aware one in the audit, and three structural facts it never checked."""
    facts = universe.structural
    reasons: list[str] = []
    notes: list[str] = []

    decision = str(output.get("decision") or "")
    if decision == "INSUFFICIENT_EVIDENCE":
        return PersistenceDecision(
            persist=False,
            gate_version=PERSISTENCE_GATE_VERSION_V1_2,
            refusal_reasons=(
                "the model answered INSUFFICIENT_EVIDENCE. That is a correct and expected "
                "outcome, not a failure, and no Opportunity is created.",
            ),
        )
    if decision != "FORM_HYPOTHESIS":
        reasons.append(f"decision {decision!r} is not one of the two permitted values")

    if str(output.get("subject") or "") != facts.subject_label:
        reasons.append(
            f"subject is {output.get('subject')!r}; the packet's subject identity is "
            f"{facts.subject_label!r}"
        )

    cited_evidence = set(_string_list(output.get("supporting_evidence_ids")))
    cited_claims = set(_string_list(output.get("supporting_claim_ids")))
    stray_evidence = sorted(cited_evidence - set(facts.evidence_ids))
    stray_claims = sorted(cited_claims - set(facts.claim_ids))
    if stray_evidence:
        reasons.append(
            f"cited Evidence ids not in the packet: {stray_evidence}. A hypothesis may cite only "
            "what it was given"
        )
    if stray_claims:
        reasons.append(f"cited Claim ids not in the packet: {stray_claims}")
    if not cited_evidence:
        reasons.append("no supporting Evidence id was cited")
    if not cited_claims:
        reasons.append("no supporting Claim id was cited")
    for evidence_id in sorted(cited_evidence):
        expected = evidence_to_claim.get(evidence_id)
        if expected is not None and expected not in cited_claims:
            reasons.append(
                f"Evidence {evidence_id} was cited without its Claim {expected}. Evidence is "
                "claim-relative, so a citation missing its claim cites nothing"
            )

    stray_families = sorted(
        set(_string_list(output.get("source_families"))) - set(facts.source_families)
    )
    if stray_families:
        reasons.append(f"source families the packet does not carry: {stray_families}")

    claimed_supported = set(_string_list(output.get("supported_dimensions")))
    packet_dimensions = {d.value for d in facts.packet_dimensions}
    over_claimed = sorted(claimed_supported - packet_dimensions)
    if over_claimed:
        reasons.append(
            f"dimensions claimed as supported that this packet does not carry: {over_claimed}"
        )
    reported_unsupported = set(_string_list(output.get("unsupported_dimensions")))
    both = sorted(claimed_supported & reported_unsupported)
    if both:
        reasons.append(f"dimensions reported both supported and unsupported: {both}")
    missing_report = sorted(
        d.value
        for d in mandatory_unsupported
        if d not in facts.packet_dimensions and d.value not in reported_unsupported
    )
    if missing_report:
        reasons.append(
            f"§6 requires an explicit unsupported report for {missing_report}, and the output does "
            "not mark them. A dimension nobody mentioned reads as one nobody checked"
        )

    independence = str(output.get("independence_status") or "").lower()
    if "unknown" not in independence:
        reasons.append(
            "independence_status does not record UNKNOWN. Two source families is diversity, never "
            "established independence"
        )
    for forbidden in ("independent source", "independent sources", "independently"):
        if forbidden in independence:
            reasons.append(
                f"independence_status contains {forbidden!r}; independence is UNKNOWN for every "
                "row in this packet"
            )
    reliability = str(output.get("reliability_status") or "").upper()
    if facts.scoring_eligible_count == 0:
        if "NON_SCORABLE" not in reliability and "MISSING_RELIABILITY" not in reliability:
            reasons.append(
                "no row in this packet is scoring-eligible and reliability_status does not "
                "preserve NON_SCORABLE / MISSING_RELIABILITY"
            )
    elif "SCORABLE" not in reliability and "SCORING" not in reliability:
        reasons.append(
            f"{facts.scoring_eligible_count} of {facts.size} rows are scoring-eligible and "
            "reliability_status does not say so. A packet's scorability is a fact about it"
        )

    audit = audit_output(output, universe, policy, concepts, markers, label_dispositions)
    for failed in audit.failed:
        reasons.append(
            f"{failed.field_name} audited {failed.verdict.value}: {'; '.join(failed.findings)}"
        )
    if all(f.verdict is StatementSupport.NOT_FACTUAL for f in audit.fields):
        notes.append(
            "every audited text was NOT_FACTUAL: there was nothing checkable in the output, which "
            "is recorded rather than read as a pass"
        )

    return PersistenceDecision(
        persist=not reasons,
        gate_version=PERSISTENCE_GATE_VERSION_V1_2,
        refusal_reasons=tuple(reasons),
        audit=audit,
        notes=tuple(notes),
    )
