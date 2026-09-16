"""Intervention-class grounding v1.0.0: what a class of intervention is allowed to be made of.

Mission 1.84.27, operator decision D3. Gate v1.5.0 audits `candidate_intervention_class` as a supported
assertion, and that audit refuses what it knows: a fixed list of outside-knowledge words, forbidden
concepts, numbers and identifiers. It never requires the class's words to come from anywhere, so a word
the list does not know passes, and a class had to be written whenever a hypothesis was formed. Schema
v1.3.0 gives the field its absence; this module gives an established class its grounding.

**Absence has exactly one representation.** The exact string `UNKNOWN_NOT_SUPPORTED`, compared byte for
byte. An empty or blank value, a near-miss of the sentinel and a denial written as prose are refused
and pointed at it: a reviewer should never have to decide whether a value means "none".

**An established class is one short noun phrase, grounded in what the answer cites.**
1. Plain ASCII letters in words joined by single spaces or hyphens: no digit, no punctuation, no
   underscore and no other character. A number or a code is not a class, a clause cannot be written in
   it, and no look-alike character can spell a word the check would not see.
2. At most `MAX_CLASS_WORDS` words, none of them a negator, a predicating verb, a past form taking a
   determiner as its object, or a code written in capitals: a class names a kind of intervention, it
   does not deny, state something or cite an identifier.
3. Every word that is not a closed grammatical word (`CLASS_FUNCTION_WORDS`: articles, prepositions,
   conjunctions) occurs, under the one inflection policy, in the CONTENT of the statements of the
   claims the answer cites in `supporting_claim_ids`, outside their quoted literals. Nothing else
   licenses a word of a class: not a claim the answer does not cite, not a source's name, not a quoted
   code, field name or resource, not a trusted definitional identifier, not a
   supported dimension's canonical name. `MARKET_ACTIVITY` is a classification of evidence, not a
   description of an intervention, so neither `market` nor `market activity` enters a class through it.

**No vocabulary list.** The only word lists here are closed grammatical classes and the reader's own
verb list; no domain word is allowed or refused by name. Lexical grounding is not semantic validity:
a class assembled from cited words can still be a poor class, and human review stays mandatory.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .assertion_scope_v1_5 import FINITE_VERBS
from .lexical_inflection import LEXICAL_INFLECTION_POLICY_VERSION, inflection_spans
from .second_opportunity_schema_v1_3 import (
    INTERVENTION_CLASS_FIELD,
    INTERVENTION_CLASS_NOT_ESTABLISHED,
)
from .support_origin import TypedSupportUniverse

__all__ = [
    "INTERVENTION_CLASS_GROUNDING_VERSION",
    "CLASS_FUNCTION_WORDS",
    "CLASS_NEGATORS",
    "MAX_CLASS_WORDS",
    "NEAR_SENTINELS",
    "class_grounding_findings",
]

INTERVENTION_CLASS_GROUNDING_VERSION = "second-opportunity-intervention-class-grounding@1.0.0"

#: The closed grammatical words a class may contain without support: articles, prepositions and
#: conjunctions. No noun, verb, adjective or adverb is here, and no negator ever will be.
CLASS_FUNCTION_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "of",
        "for",
        "in",
        "on",
        "to",
        "with",
        "by",
        "from",
        "at",
        "into",
        "under",
        "per",
        "via",
        "and",
        "or",
    }
)
CLASS_NEGATORS: frozenset[str] = frozenset(
    {"no", "not", "never", "none", "nor", "neither", "without"}
)
#: A short category, as the field's role has said since Mission 1.84.14.
MAX_CLASS_WORDS = 6
#: Letters-only spellings of an absence that are not the sentinel.
NEAR_SENTINELS: frozenset[str] = frozenset(
    {
        "unknownnotsupported",
        "notestablished",
        "notsupported",
        "unknown",
        "unsupported",
        "none",
        "na",
        "notapplicable",
        "notdetermined",
        "undetermined",
        "noclass",
        "nointerventionclass",
        "nointervention",
    }
)

_PHRASE = re.compile(r"[A-Za-z]+(?:[ -][A-Za-z]+)*")
_QUOTED = re.compile(r'"[^"]*"')
_DETERMINERS: frozenset[str] = frozenset(
    {"a", "an", "the", "any", "this", "these", "that", "those"}
)


def _cited_content(
    output: Mapping[str, object], universe: TypedSupportUniverse, packet_claim_ids: Sequence[str]
) -> str | None:
    raw = output.get("supporting_claim_ids")
    cited = {str(c) for c in raw} if isinstance(raw, list) else set()
    kept = cited & set(packet_claim_ids)
    if not kept:
        return None
    # A quoted literal is a value the source recorded (a code, a field name, a resource), not prose it
    # wrote: `"contract_notice"` never licenses `contract`.
    return " | ".join(
        _QUOTED.sub(" | ", s.content) for s in universe.statements if s.claim_id in kept
    )


def class_grounding_findings(
    output: Mapping[str, object],
    universe: TypedSupportUniverse,
    packet_claim_ids: Sequence[str],
) -> tuple[str, ...]:
    """Every reason the answer's class of intervention is neither the exact absence nor a grounded
    noun phrase. Empty when it is one or the other, or when the field is not text (structure's job)."""
    value = output.get(INTERVENTION_CLASS_FIELD)
    if not isinstance(value, str):
        return ()
    if value == INTERVENTION_CLASS_NOT_ESTABLISHED:
        return ()
    sentinel = INTERVENTION_CLASS_NOT_ESTABLISHED
    if not value.strip():
        return (
            f"an empty value is not a class and not an absence; a class the statements do not "
            f"establish is written exactly {sentinel}",
        )
    letters = re.sub(r"[^a-z]", "", value.casefold())
    if letters in NEAR_SENTINELS or sentinel.casefold() in value.casefold():
        return (
            f"{value!r} is not the absence of a class as the contract writes it: exactly {sentinel}, "
            "with nothing before or after",
        )
    if not _PHRASE.fullmatch(value):
        return (
            f"{value!r} is not one noun phrase in plain words: a class carries no digit, punctuation, "
            "underscore or character outside ASCII letters, spaces and hyphens",
        )
    words = [w.lower() for w in re.split(r"[ -]", value)]
    findings: list[str] = []
    if len(words) > MAX_CLASS_WORDS:
        findings.append(
            f"{len(words)} words is not a short category: a class names a kind of intervention in "
            f"at most {MAX_CLASS_WORDS}"
        )
    negators = sorted({w for w in words if w in CLASS_NEGATORS})
    if negators:
        findings.append(
            f"{negators} deny rather than name: a class the statements do not establish is written "
            f"exactly {sentinel}"
        )
    verbs = {w for w in words if w in FINITE_VERBS}
    # A past form followed by a determiner has taken an object: `notices exceeded the smallest`.
    verbs |= {
        w
        for w, following in zip(words, words[1:], strict=False)
        if len(w) >= 4 and w.endswith("ed") and not w.endswith("eed") and following in _DETERMINERS
    }
    if verbs:
        findings.append(f"{sorted(verbs)} state something: a class is a noun phrase, not a clause")
    codes = sorted({w for w in re.split(r"[ -]", value) if len(w) >= 2 and w.isupper()})
    if codes:
        findings.append(f"{codes} are codes, not the name of a kind of intervention")
    content_words = [w for w in words if w not in CLASS_FUNCTION_WORDS]
    if not content_words:
        findings.append("a class of only grammatical words names nothing")
        return tuple(findings)
    cited = _cited_content(output, universe, packet_claim_ids)
    if cited is None:
        findings.append(
            "an established class cites the claims its words come from, and supporting_claim_ids "
            "names none of this packet's claims"
        )
        return tuple(findings)
    unsupported = sorted(
        {w for w in content_words if w not in CLASS_NEGATORS and not inflection_spans(cited, w)}
    )
    if unsupported:
        findings.append(
            f"{unsupported} occur in no statement of the cited claims, compared under "
            f"{LEXICAL_INFLECTION_POLICY_VERSION}; a class takes its words from what the cited "
            "sources reported, never from a source's name, a dimension's name or prior knowledge"
        )
    return tuple(findings)
