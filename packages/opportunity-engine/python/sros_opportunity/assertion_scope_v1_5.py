"""Assertion scope v1.0.0: the successor reading of where a denial or an uncertainty reaches.

Mission 1.84.26. Mission 1.84.25 proved two ways in which gate v1.4.0, through the v1.2.0 clause reader
it inherits, reads a word as ASSERTED that its own policy, *assertion, not token presence*, does not
assert. The operator decided both, and this module is those two decisions and nothing else:

1. **D1, A SCOPED LIST KEEPS ITS SCOPE.** The reader's coordinated-clause boundary fires on `and` or
   `or` followed by one to three words and a verb, so the last item of a list that a leading `whether`
   or denial governs was cut off from it whenever the sentence's predicate followed that item:
   *Whether a need or software exists is unknown.* Here such a boundary is kept only when it opens a
   genuine proposition. It is vetoed, and the list stays one clause under its scope, only on positive
   evidence of a list: the span since the last boundary opens with a scope anchor, the items between
   commas are bare nouns, the item after the conjunction is a short noun phrase that no pronoun or
   negator opens, and the scoped phrase has not yet received its own predicate. Anything else splits
   exactly as v1.2.0 splits, so *No evidence establishes software demand, and buyers are willing to
   pay.* is still two clauses.
2. **D2, A MODIFIER INSIDE A DENIED SUBJECT IS NOT ASSERTED.** v1.2.0 clears a term that is itself the
   subject of its own denial and nothing inside that subject, so the pre-modifier in *Software gap is
   not established.* stayed ASSERTED. Here a gated word that fills the one modifier slot of a
   clause-initial subject noun phrase, whose head is followed at once by a denial of its existence or
   establishment, is DENIED. The rule reads one noun phrase, never "a later `not`", and it stops where
   the answer predicates of that subject again: after the denial in the same clause, or in the next
   clause after any boundary (*software gap is not established, it exists*; *..., and they are
   probably large*), the modifier is asserted, as v1.2.0 re-asserts after a contrast.

**Everything else is v1.2.0's, called, not copied**: the boundary pattern, the denial markers, the
negated noun phrase, the subject denial, the request reading, the re-assertion rules. A sentence with
no scope anchor gets exactly v1.2.0's clause list, and an occurrence v1.2.0 does not read as ASSERTED
is read the same way here. Both repairs can only move an occurrence from ASSERTED to not asserted, so
each is bounded by the evidence it requires, and where the evidence is missing the reading is
v1.2.0's, which refuses. **This is not a general language engine**: every rule is a bounded pattern
over closed word lists, and a word the lists do not know is read the way that refuses.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from .assertion_context import (
    _CLAUSE_BOUNDARY,
    _EXEMPT,
    _LEADING_CONTRAST,
    _REPREDICATION,
    _TOKEN,
    Occurrence,
    OccurrenceState,
    _Clause,
    _clauses,
    _denies,
    _norm,
    _reasserted,
    _state,
)
from .guards import _sentences
from .lexical_inflection import inflection_spans, verbatim_spans

__all__ = [
    "ASSERTION_SCOPE_POLICY_VERSION",
    "SCOPED_LIST_RULE",
    "DENIED_SUBJECT_MODIFIER_RULE",
    "FINITE_VERBS",
    "CLOSED_CLASS_WORDS",
    "scoped_list_link",
    "denied_subject_modifier",
    "clauses_v1_2",
    "scoped_clauses",
    "state_v1_2",
    "scoped_state",
    "read_occurrences",
    "classify",
    "is_asserted",
]

ASSERTION_SCOPE_POLICY_VERSION = "second-opportunity-assertion-scope@1.0.0"
SCOPED_LIST_RULE = "A_SCOPED_NOUN_LIST_KEEPS_ITS_SCOPE"
DENIED_SUBJECT_MODIFIER_RULE = "A_MODIFIER_INSIDE_A_DENIED_SUBJECT_IS_NOT_ASSERTED"

# ============================================================================= closed word lists


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


#: Finite and predicating verb forms. Deliberately generous: a word read as a verb makes a list look
#: like a clause, and a clause splits, which is v1.2.0's reading and refuses.
FINITE_VERBS: frozenset[str] = _words(
    """
    is are was were be been being am has have had would will can could may might must should shall
    does do did show shows showed shown prove proves proved proven establish establishes established
    demonstrate demonstrates demonstrated exist exists existed remain remains remained seem seems
    seemed appear appears appeared reflect reflects reflected indicate indicates indicated suggest
    suggests suggested find finds found pay pays paid buy buys bought sell sells sold want wants
    wanted spend spends spent use uses used report reports reported offer offers offered serve serves
    served provide provides provided lack lacks lacked include includes included mean means cost costs
    grow grows grew hold holds held get gets got make makes made take takes took see sees saw know
    knows knew say says said become becomes became seek seeks sought require requires required
    support supports supported confirm confirms confirmed matter matters mattered occur occurs
    occurred
    """
)
#: Words that open a clause of their own rather than continue a noun list.
_PRONOUNS: frozenset[str] = _words(
    "it they these those this there we he she i you which who whom whose what that"
)
_NEGATOR_WORDS: frozenset[str] = _words("no not never none nor neither nothing")
_ITEM_DETERMINERS: frozenset[str] = _words("a an the any")
#: Function words, auxiliaries, hedges and predicating verbs: none of them is a modifier or a head.
CLOSED_CLASS_WORDS: frozenset[str] = _words(
    """
    a an the any this these those that which who whom whose what whether it its they their them we our
    you he she his her there here of for in on to with by from about at into over under between among
    within without against as than via per and or but nor yet so then if because although though
    while whereas however is are was were be been being has have had do does did can could will would
    may might must should shall not no never none neither only just merely simply even also still
    already probably likely presumably apparently clearly certainly definitely surely evidently
    arguably possibly perhaps indeed shows show proves prove establishes establish demonstrates
    demonstrate exists exist remains remain seems seem appears appear confirms confirm supports
    support suggests suggest indicates indicate
    """
)

# ============================================================================= D1: a scoped list

_WHETHER_ANCHOR = re.compile(r"^\s*whether(?![a-z0-9'])")
_SUBJECT_DENIAL_ANCHOR = re.compile(r"^\s*(?:no|none\s+of(?:\s+the)?|neither|nothing)(?![a-z0-9'])")
_COMPLEMENT = re.compile(r"(?<![a-z0-9'])(?:whether|that|if)(?![a-z0-9'])")
#: The predicate that closes a sentence-initial `whether` phrase: once the span carries it, the
#: phrase is saturated, and what follows a conjunction is a clause of its own.
_CLOSING_PREDICATE = re.compile(
    r"(?<![a-z0-9'])(?:is|are|was|were|remains?|remained)\s+(?:still\s+|yet\s+)?"
    r"(?:not\s+(?:yet\s+)?(?:established|known|shown|determined|verified|clear|observed|supported)"
    r"|unknown|unclear|uncertain|undetermined|unverified|unestablished|open|to\s+be\s+seen)"
    r"(?![a-z0-9'])"
)
#: The verbs v1.2.0's coordinated-clause pattern looks for after the conjunction, and no others.
_COORDINATION_VERBS: frozenset[str] = _words(
    """
    is are was were has have had would will can could may might must should show shows prove proves
    establish establishes demonstrate demonstrates exist exists remain remains seem seems appear
    appears does do did
    """
)
_MAX_CONJUNCT_WORDS = 3


def _verb_like(word: str, *, plural_counts: bool) -> bool:
    if word in FINITE_VERBS:
        return True
    long_enough = len(word) >= 4
    if long_enough and word.endswith("ed") and not word.endswith("eed"):
        return True
    return (
        plural_counts
        and long_enough
        and word.endswith("s")
        and not word.endswith(("ss", "is", "us"))
    )


def _verbs(words: list[str], *, plural_counts: bool) -> int:
    return sum(_verb_like(w, plural_counts=plural_counts) for w in words)


def _is_list_item(text: str) -> bool:
    """A bare noun between two commas: an optional determiner and exactly one word."""
    words = _TOKEN.findall(text)
    if words and words[0] in _ITEM_DETERMINERS:
        words = words[1:]
    if len(words) != 1:
        return False
    (word,) = words
    return not (
        word in _PRONOUNS
        or word in _NEGATOR_WORDS
        or word in CLOSED_CLASS_WORDS
        or _verb_like(word, plural_counts=False)
    )


def _conjunct_is_a_noun_phrase(tail: str) -> bool:
    """What follows the conjunction, up to the verb v1.2.0's pattern found, is one to three words,
    and none of them opens a clause or is a verb itself."""
    words = _TOKEN.findall(tail)
    cut = next((i for i, w in enumerate(words) if w in _COORDINATION_VERBS), len(words))
    phrase = words[:cut]
    if not phrase or len(phrase) > _MAX_CONJUNCT_WORDS or cut == len(words):
        return False
    if any(w in _PRONOUNS or w in _NEGATOR_WORDS for w in phrase):
        return False
    # An infinitive inside the noun phrase is not its verb: `willingness to pay`.
    return not any(
        w in FINITE_VERBS and (i == 0 or phrase[i - 1] != "to") for i, w in enumerate(phrase)
    )


def _scope_anchors(span: str) -> list[tuple[str, int]]:
    """Every place a scope that could govern a list opens, and what kind of scope each is.

    A clause-initial `whether` opens a subject phrase that awaits the sentence's predicate. A
    clause-initial `no`, `none of`, `neither` or `nothing` heads the subject itself. A later `whether`
    scopes what follows it wherever it stands; a later `that` or `if` does only after a denial.
    """
    anchors: list[tuple[str, int]] = []
    whether = _WHETHER_ANCHOR.match(span)
    if whether:
        anchors.append(("whether", whether.end()))
    denial = _SUBJECT_DENIAL_ANCHOR.match(span)
    if denial:
        anchors.append(("subject_denial", denial.end()))
    complements = [m for m in _COMPLEMENT.finditer(span) if not whether or m.start() > 0]
    if complements:
        last = complements[-1]
        if last.group() == "whether" or _denies(span[: last.start()]):
            anchors.append(("complement", last.end()))
    return anchors


def scoped_list_link(span: str, tail: str, *, comma: bool) -> bool:
    """D1. Whether a coordinated-clause boundary joins the last item of a scoped noun list.

    `span` is the lowered text from the last kept boundary to the conjunction, `tail` the text from
    the conjunction to the next boundary, and `comma` whether the conjunction follows a comma. True
    only on positive evidence of a list; every other boundary stays a boundary.
    """
    if not _conjunct_is_a_noun_phrase(tail):
        return False
    return any(
        _list_under(kind, span[at:], span, tail, comma=comma) for kind, at in _scope_anchors(span)
    )


def _list_under(kind: str, scoped: str, span: str, tail: str, *, comma: bool) -> bool:
    """Whether `scoped`, the text after one scope anchor, is a noun list the conjunction continues."""
    head, *items = scoped.split(",")
    if comma and not items:
        return False
    if not all(_is_list_item(item) for item in items):
        return False
    head_words = _TOKEN.findall(head)
    if not head_words or head_words[0] in _PRONOUNS - {"this", "that"}:
        return False
    if any(w in _NEGATOR_WORDS for w in head_words):
        return False
    if kind == "whether":
        if _CLOSING_PREDICATE.search(span):
            return False
        guessed = [
            w for w in head_words if w not in FINITE_VERBS and _verb_like(w, plural_counts=True)
        ]
        known = [i for i, w in enumerate(head_words) if w in FINITE_VERBS]
        if guessed:
            return False
        if not known:
            return True
        # One known verb, followed by the noun phrase the list continues, and the sentence's own
        # predicate still to come: `whether this reflects a need, problem, or X is not established`.
        # A verb that ends the head makes the head a clause: `whether a need exists or X is sold`.
        return (
            len(known) == 1
            and known[0] < len(head_words) - 1
            and bool(_CLOSING_PREDICATE.search(tail))
        )
    # After a denial or a complementizer the list's first item is a bare noun too: a longer head could
    # hide a verb the lexicon does not know (`no staff bid or buyers are willing to pay`).
    return _is_list_item(head)


def clauses_v1_2(sentence: str) -> list[_Clause]:
    """v1.2.0's clause list, by identity."""
    return _clauses(sentence)


def scoped_clauses(sentence: str) -> list[_Clause]:
    """v1.2.0's clause splitter, with a coordinated-clause boundary vetoed where D1 finds a list."""
    lowered = _norm(sentence)
    matches = list(_CLAUSE_BOUNDARY.finditer(lowered))
    pieces: list[_Clause] = []
    last, kind = 0, "start"
    for index, match in enumerate(matches):
        if match.lastgroup == "coord":
            following = matches[index + 1].start() if index + 1 < len(matches) else len(lowered)
            if scoped_list_link(
                lowered[last : match.start()],
                lowered[match.end() : following],
                comma=match.group().lstrip().startswith(","),
            ):
                continue
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


# ============================================================================= D2: a denied subject

_SUBJECT_DETERMINER = re.compile(r"(?:a|an|the|any|this|these|such) ")
_UNIT = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_ESTABLISHED = (
    r"(?:established|known|shown|proven|proved|supported|observed|measured|evidenced|evident|"
    r"demonstrated|confirmed|determined|verified|identified|documented|quantified)"
)
_ABSENT = (
    r"(?:unknown|unestablished|unsupported|unproven|unverified|undetermined|unclear|unobserved|"
    r"absent|missing)"
)
#: A denial of the subject's existence or establishment, and only that: `is not large` or `have no
#: budget` say something of a subject that exists, and do not clear what modifies it.
_EXISTENCE_DENIAL = re.compile(
    rf"^\s*(?::\s*(?:not\s+(?:yet\s+)?{_ESTABLISHED}|{_ABSENT})(?![a-z0-9'])"
    rf"|(?:is|are|was|were|remains?|remained|stays?)\s+(?:still\s+|yet\s+)?"
    rf"(?:not\s+(?:yet\s+)?{_ESTABLISHED}|{_ABSENT})(?![a-z0-9'])"
    rf"|(?:has|have|had)\s+(?:still\s+|yet\s+)?not\s+(?:yet\s+)?been\s+{_ESTABLISHED}(?![a-z0-9'])"
    rf"|(?:cannot|can\s+not|can't|could\s+not|may\s+not|might\s+not|will\s+not|won't|would\s+not)"
    rf"\s+be\s+{_ESTABLISHED}(?![a-z0-9'])"
    r"|(?:does\s+not|do\s+not|did\s+not|doesn't|don't|didn't)\s+exist(?![a-z0-9']))"
)
_MAX_SUBJECT_UNITS = 6


_PRONOUN_SUBJECT = re.compile(r"(?<![a-z0-9'])(?:it|they|this|these|those)\s+([a-z]+)")
_HEDGES = _words(
    "probably likely presumably apparently clearly certainly definitely surely evidently"
)


def _predicated_again(rest: str) -> bool:
    """Whether what follows the denial, in the same clause, predicates of the subject again through a
    pronoun and a verb: `software gap is not established, it exists`. `these statements` is a noun
    phrase, not a predication, and a further denial or a remark about testing or evidence is not a
    predication either (v1.2.0's own exemptions)."""
    for pronoun in _PRONOUN_SUBJECT.finditer(rest):
        if pronoun.group(1) not in FINITE_VERBS and pronoun.group(1) not in _HEDGES:
            continue
        continuation = rest[pronoun.start() :]
        if not _denies(continuation) and not _EXEMPT.search(continuation):
            return True
    return False


def denied_subject_modifier(clause: str, start: int, end: int) -> bool:
    """D2. Whether the span `clause[start:end]` fills the one modifier slot of a clause-initial
    subject noun phrase whose head is followed at once by a denial of its existence.

    The phrase is an optional determiner, then words joined by single spaces (a hyphenated compound
    is one word), none of them a closed-class word. Its head is the first word followed by the
    denial. Everything before the head is either one word or exactly the gated span.
    """
    determiner = _SUBJECT_DETERMINER.match(clause)
    position = determiner.end() if determiner else 0
    if start < position:
        return False
    units: list[re.Match[str]] = []
    while len(units) < _MAX_SUBJECT_UNITS:
        unit = _UNIT.match(clause, position)
        if unit is None or any(p in CLOSED_CLASS_WORDS for p in unit.group().split("-")):
            return False
        units.append(unit)
        denial = _EXISTENCE_DENIAL.match(clause[unit.end() :])
        if len(units) > 1 and denial:
            first, before_head = units[0].start(), units[-2].end()
            if not (first <= start and end <= before_head):
                return False
            if _predicated_again(clause[unit.end() + denial.end() :]):
                return False
            return len(units) == 2 or (start, end) == (first, before_head)
        if (
            clause[unit.end() : unit.end() + 1] != " "
            or clause[unit.end() + 1 : unit.end() + 2] == " "
        ):
            return False
        position = unit.end() + 1
    return False


def state_v1_2(
    clause: str, start: int, end: int, scoped_by_field: bool
) -> tuple[OccurrenceState, str]:
    """v1.2.0's occurrence state, by identity."""
    return _state(clause, start, end, scoped_by_field)


def scoped_state(
    clause: str, start: int, end: int, scoped_by_field: bool
) -> tuple[OccurrenceState, str]:
    """v1.2.0's occurrence state; where it reads ASSERTED, D2 may read the modifier of a denied
    subject as DENIED. No other state moves."""
    state, why = _state(clause, start, end, scoped_by_field)
    if state is OccurrenceState.ASSERTED and denied_subject_modifier(clause, start, end):
        return OccurrenceState.DENIED, _D2_WHY
    return state, why


_D2_WHY = "a modifier inside the subject of its own denial"


# ============================================================================= the reading

Splitter = Callable[[str], list[_Clause]]
StateReader = Callable[[str, int, int, bool], tuple[OccurrenceState, str]]


def read_occurrences(
    text: str,
    phrase: str,
    *,
    splitter: Splitter,
    state_reader: StateReader,
    scoped_head: bool = False,
    verbatim: bool = False,
) -> tuple[Occurrence, ...]:
    """`assertion_audit_v1_3.classify`, with the splitter and the state reader passed in.

    The audit's reading is this loop over `scoped_clauses` and `scoped_state`; the same loop over
    v1.2.0's two functions is gate v1.4.0's reading, which is how a differential attributes each
    divergence to D1 or D2 alone.
    """
    spans = verbatim_spans if verbatim else inflection_spans
    found: list[Occurrence] = []
    for s_index, sentence in enumerate(_sentences(text)):
        clauses = splitter(sentence)
        for c_index, clause in enumerate(clauses):
            for start, end in spans(clause.text, phrase):
                head = scoped_head and s_index == 0 and c_index == 0
                state, why = state_reader(clause.text, start, end, head)
                if state is not OccurrenceState.ASSERTED:
                    following = clauses[c_index + 1] if c_index + 1 < len(clauses) else None
                    again = _reasserted(clause.text, end, following)
                    if again is None and why == _D2_WHY:
                        again = _denied_subject_predicated_again(following)
                    if again is not None:
                        state, why = OccurrenceState.ASSERTED, again
                found.append(Occurrence(phrase, sentence.strip(), clause.text, state, why))
    return tuple(found)


def _denied_subject_predicated_again(following: _Clause | None) -> str | None:
    """D2's own limit. A modifier D2 cleared is asserted again when the next clause, after any
    boundary, predicates of the subject again (`software gap is not established, and they are
    probably large`). v1.2.0 reads that only after a contrast; for what D2 clears, every boundary
    counts, so the repair never reaches further than v1.2.0 already did."""
    if (
        following is not None
        and _REPREDICATION.match(following.text)
        and not _denies(following.text)
        and not _EXEMPT.search(following.text)
    ):
        return f"a denied subject predicated of again after a {following.boundary} boundary"
    return None


def classify(
    text: str, phrase: str, *, scoped_head: bool = False, verbatim: bool = False
) -> tuple[Occurrence, ...]:
    """The successor reading: D1's splitter and D2's state reader."""
    return read_occurrences(
        text,
        phrase,
        splitter=scoped_clauses,
        state_reader=scoped_state,
        scoped_head=scoped_head,
        verbatim=verbatim,
    )


def is_asserted(
    text: str, phrase: str, *, scoped_head: bool = False, verbatim: bool = False
) -> bool:
    return any(
        o.asserted for o in classify(text, phrase, scoped_head=scoped_head, verbatim=verbatim)
    )
