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
    "GUARD_VERSION",
    "FORBIDDEN_TERMS",
    "VALIDATION_WORDS",
    "GuardViolation",
    "check_statement",
    "check_no_validation_language",
]

GUARD_VERSION = "opportunity-claim-guard@1.0.0"

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


def check_statement(
    text: str, supported_dimensions: frozenset[EvidenceDimension]
) -> tuple[GuardViolation, ...]:
    """Every unsupported commercial claim in `text`, not merely the first."""
    tokens = _tokens(text)
    violations: list[GuardViolation] = []
    for term, required in sorted(FORBIDDEN_TERMS.items()):
        if not _contains_phrase(tokens, term):
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
