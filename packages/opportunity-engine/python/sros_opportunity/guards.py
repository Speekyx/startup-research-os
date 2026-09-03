"""The vocabulary a hypothesis may not use without evidence for that exact thing.

Mission 1.28 §11. This is the layer that stops the failure the whole repository
is arranged against: an interpretation acquiring the status of a fact one
sentence at a time.

**Each forbidden term names the dimension that would license it.** `revenue` is
not banned; it is banned unless eligible evidence maps to `ECONOMIC_VALUE`.
That is stricter than a blocklist and more useful: the refusal says which
evidence is missing rather than which word was typed, so the remedy is an
acquisition rather than a rewording.

**Matching is over TOKENS, never substrings.** `supermarket` is not `market`,
and Mission 1.13.1 paid for that distinction already. Hyphens and slashes split;
possessives and plurals fold.

**A term under a DENIAL is not an assertion** (added in 1.1.0, Mission 1.31). The
guard exists to stop this engine ASSERTING an unsupported commercial fact. A
sentence that says *no statement establishes whether anyone would pay* is
enumerating an absence, which is the most valuable thing a hypothesis can do and
is exactly what §6 and §16 require of one. Version 1.0.0 flagged it, refused a
sound output, and cost Mission 1.31 its outcome -- the same shape as
`testing-strategy.md` §23, where a substring scan fired on the docstring
explaining the rule. A denial marker earlier in the same sentence now clears the
term, and only in that sentence: `no evidence of X. Buyers would pay.` still
fails on the second sentence.

**A term can also be the SUBJECT of its own denial** (added in 1.2.0, Mission
1.31.1 §1, before that mission's call). *Competitors are not established by the
evidence* is a denial whose marker FOLLOWS the term, so the ordering rule alone
flagged it. The two forms are told apart by grammar rather than by order: there
the term is the subject and the negation is its copula, whereas in *buyers would
pay, which is not established* the negation sits in a relative clause behind a
comma and must not license what precedes it. Only
`<term> (is|are|was|were|has|have|had) (not|never|no)` clears, and an intervening
comma or contrastive word cancels it.

**A guard is the second line.** The first is not asking the model for the
sentence at all -- the §10 output schema separates `supported_dimensions` from
`unsupported_dimensions` and requires every factual statement to name a Claim or
Evidence id. A guard that fires means the prompt failed, and it is written to
refuse rather than to sanitise: silently deleting the clause would leave a
hypothesis that reads as though it never made the claim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .dimensions import EvidenceDimension

__all__ = [
    "DENIAL_MARKERS",
    "GUARD_VERSION",
    "FORBIDDEN_TERMS",
    "VALIDATION_WORDS",
    "GuardViolation",
    "check_statement",
    "check_no_validation_language",
]

GUARD_VERSION = "opportunity-claim-guard@1.2.0"

_D = EvidenceDimension

#: term -> the dimension that must be supported for the term to be permissible.
#: `None` means the term is never permissible from this engine, whatever the
#: evidence: no observation in any registered source measures a market's total
#: size, a probability of success or a competitor's weakness, so a dimension that
#: would license those does not exist and must not be invented to.
FORBIDDEN_TERMS: dict[str, EvidenceDimension | None] = {
    # Never permissible: nothing in the portfolio measures these at all.
    "tam": None,
    "sam": None,
    "som": None,
    "market size": None,
    "addressable market": None,
    "mrr": None,
    "arr": None,
    "profitability": None,
    "profitable": None,
    "growth rate": None,
    "product-market fit": None,
    "product market fit": None,
    # Permissible only with evidence for that exact dimension.
    "revenue": _D.ECONOMIC_VALUE,
    "price": _D.ECONOMIC_VALUE,
    "pricing": _D.ECONOMIC_VALUE,
    "willingness to pay": _D.WILLINGNESS_TO_PAY,
    "will pay": _D.WILLINGNESS_TO_PAY,
    "would pay": _D.WILLINGNESS_TO_PAY,
    "customers": _D.BUYER_OR_BUDGET_EXISTENCE,
    "customer count": _D.BUYER_OR_BUDGET_EXISTENCE,
    "buyers": _D.BUYER_OR_BUDGET_EXISTENCE,
    "budget": _D.BUYER_OR_BUDGET_EXISTENCE,
    "demand": _D.MARKET_ACTIVITY,
    "market demand": _D.MARKET_ACTIVITY,
    "adoption": _D.AUDIENCE_OR_USAGE,
    "users": _D.AUDIENCE_OR_USAGE,
    "competitors": _D.COMPETITIVE_SUPPLY,
    "competitor weakness": _D.COMPETITIVE_SUPPLY,
}

#: Words that would turn a hypothesis into a conclusion. Mission 1.28 §18
#: requires this enforced in code rather than in prose, so it is a hard refusal
#: independent of what evidence exists: no amount of evidence makes an
#: OPPORTUNITY_HYPOTHESIS a VALIDATED_OPPORTUNITY, because validation is a
#: separate act nobody has performed.
VALIDATION_WORDS: frozenset[str] = frozenset(
    {
        "validated",
        "proven",
        "confirmed",
        "guaranteed",
        "winning",
        "high-confidence",
        "high confidence",
        "certain",
        "established fact",
    }
)


#: Markers that turn a forbidden term into an enumerated ABSENCE rather than an
#: assertion, when they appear EARLIER IN THE SAME SENTENCE. Deliberately narrow:
#: each is a phrase that scopes what follows it, so a later clause in the same
#: sentence is inside the denial.
DENIAL_MARKERS: tuple[str, ...] = (
    "no statement",
    "no evidence",
    "no claim",
    "nothing",
    "not establish",
    "does not",
    "do not",
    "did not",
    "cannot",
    "is not",
    "are not",
    "was not",
    "were not",
    "never",
    "without",
    "absent",
    "unsupported",
    "unknown",
    "whether",
    "neither",
    "lacks",
    "lacking",
)


@dataclass(frozen=True)
class GuardViolation:
    term: str
    required_dimension: EvidenceDimension | None
    message: str


def _tokens(text: str) -> list[str]:
    lowered = text.lower().replace("’", "'")
    words = re.split(r"[^a-z0-9]+", lowered)
    folded: list[str] = []
    for word in words:
        if not word:
            continue
        if word.endswith("'s"):
            word = word[:-2]
        folded.append(word)
    return folded


def _contains_phrase(tokens: list[str], phrase: str) -> bool:
    parts = phrase.split()
    if len(parts) == 1:
        target = parts[0]
        return any(token == target or token == target + "s" for token in tokens)
    for index in range(len(tokens) - len(parts) + 1):
        window = tokens[index : index + len(parts)]
        if all(w == p or w == p + "s" for w, p in zip(window, parts, strict=True)):
            return True
    return False


def _sentences(text: str) -> list[str]:
    """Split on sentence enders, keeping em-dash clauses together.

    A denial scopes the clauses that follow it within one sentence, so the
    sentence is the right unit: `no evidence of X. Buyers would pay.` must still
    fail on the second sentence.
    """
    return [part for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


#: Words that, between a term and a following negation, mean the negation belongs
#: to a DIFFERENT clause -- so it cannot be the term's own copula.
_CLAUSE_BREAKS: tuple[str, ...] = (
    ",",
    ";",
    " which ",
    " although ",
    " though ",
    " but ",
    " yet ",
)

#: `<term> (is|are|was|were|has|have|had) (not|never|no) ...` -- the term is the
#: subject and the negation is its own predicate.
_COPULAR_DENIAL = re.compile(r"^\s*(?:is|are|was|were|has|have|had)\s+(?:not|never|no)\b")


def _subject_of_its_own_denial(lowered: str, phrase: str, position: int) -> bool:
    """Whether the term at `position` is the subject of a negation that follows.

    Deliberately narrow. The negated copula must begin immediately after the
    phrase, and any clause break in between disqualifies it -- which is what
    keeps `buyers would pay, which is not established` an assertion while
    clearing `competitors are not established by the evidence`.
    """
    tail = lowered[position + len(phrase) :]
    prefix = tail[: max(tail.lower().find("not"), 0)] if "not" in tail[:40] else tail[:40]
    if any(marker in prefix for marker in _CLAUSE_BREAKS):
        return False
    return bool(_COPULAR_DENIAL.match(tail))


def _asserted(text: str, phrase: str) -> bool:
    """Whether `phrase` is ASSERTED somewhere in `text`, rather than denied.

    True when at least one sentence contains the phrase, with no denial marker
    before it and no negated copula immediately after it. A sentence enumerating
    an absence clears; a bare assertion does not, even if another sentence in the
    same text denies something else.
    """
    for sentence in _sentences(text):
        tokens = _tokens(sentence)
        if not _contains_phrase(tokens, phrase):
            continue
        lowered = sentence.lower()
        position = _phrase_position(lowered, phrase)
        if position is None:
            return True
        if any(
            (index := lowered.find(marker)) != -1 and index < position for marker in DENIAL_MARKERS
        ):
            continue
        # 1.2.0. The term may be the SUBJECT of its own denial, where the marker
        # necessarily follows it rather than preceding it.
        if _subject_of_its_own_denial(lowered, phrase, position):
            continue
        return True
    return False


def _phrase_position(lowered: str, phrase: str) -> int | None:
    """Where the phrase's first word starts, for comparing against a marker.

    `match.end() - len(first)`, NOT `match.start()`: the pattern captures the
    character before the word so that `supermarket` cannot match `market`, and
    `start()` therefore points at that character rather than at the word. The
    difference is one byte and it silently misaligned the tail for every term
    not at the beginning of a sentence -- so `market demand is never
    established` cleared and `demand is never established` did not.
    """
    first = phrase.split()[0]
    match = re.search(rf"(^|[^a-z]){re.escape(first)}", lowered)
    return match.end() - len(first) if match else None


def check_statement(
    text: str, supported_dimensions: frozenset[EvidenceDimension]
) -> tuple[GuardViolation, ...]:
    """Every unsupported commercial claim in `text`, not merely the first."""
    tokens = _tokens(text)
    violations: list[GuardViolation] = []
    for term, required in sorted(FORBIDDEN_TERMS.items()):
        if not _contains_phrase(tokens, term):
            continue
        # Added in 1.1.0. Enumerating an absence is not asserting a fact.
        if not _asserted(text, term):
            continue
        if required is None:
            violations.append(
                GuardViolation(
                    term,
                    None,
                    f"{term!r} is not supportable by any registered source: no "
                    "observation in this portfolio measures it, and no dimension "
                    "may be invented so that it can be asserted.",
                )
            )
        elif required not in supported_dimensions:
            violations.append(
                GuardViolation(
                    term,
                    required,
                    f"{term!r} asserts {required.value}, which no eligible evidence in "
                    "this packet supports. The missing commercial evidence must appear "
                    "as missing evidence, not as a hedged sentence.",
                )
            )
    return tuple(violations)


def check_no_validation_language(text: str) -> tuple[GuardViolation, ...]:
    """Validation vocabulary, refused unconditionally."""
    tokens = _tokens(text)
    return tuple(
        GuardViolation(
            word,
            None,
            f"{word!r} states a conclusion. Records produced here are "
            "OPPORTUNITY_HYPOTHESIS and never VALIDATED_OPPORTUNITY, PROVEN_MARKET, "
            "WINNING_IDEA, PRODUCT_MARKET_FIT or HIGH_CONFIDENCE_BUSINESS.",
        )
        for word in sorted(VALIDATION_WORDS)
        if _contains_phrase(tokens, word.replace("-", " "))
    )
