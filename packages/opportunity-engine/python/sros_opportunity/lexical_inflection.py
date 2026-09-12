"""One bounded inflection normalization, applied to the answer and to the supplied statements alike.

Mission 1.84.11. Gate v1.2.0 read the answer with a plural fold (the answer's `tenders` matched the
marker `tender`) and read the supplied statements with exact tokens, so a word supplied only in its
plural never licensed its own singular. The operator decided that asymmetry is a gate defect
(`FIX_SYMMETRIC_INFLECTION_NORMALIZATION = true`). It is repaired here by ONE function, and every
comparison between the answer's gated vocabulary and the supplied statements goes through it on both
sides.

**This is not a stemmer**, it adds no dependency, and it reads no locale. It covers English noun
NUMBER, in five written rules, and nothing else:

    REGULAR_IES_PLURAL   5+ letters, consonant + `ies` -> `y`          industries -> industry
    IE_SINGULAR          4+ letters, consonant + `ie`  -> `y`          movie      -> movy
    REGULAR_SSES_PLURAL  6+ letters, `sses` -> `ss`                     weaknesses -> weakness
    SSE_SINGULAR         5+ letters, `sse`  -> `ss`                     finesse    -> finess
    REGULAR_S_PLURAL     4+ letters, `s` but not `ss`/`us`/`is` -> drop  tenders    -> tender

Why each exists, from the gated vocabulary rather than from taste:

* `-s` is the fold v1.2.0 already applied to the answer. It is now applied to the support too.
* `-ies` because gated terms end in consonant + `y` (`industry`, `municipality`, `opportunity`,
  `profitability`), and `industries` escaped the marker `industry` under v1.2.0.
* `-sses` because gated nouns end in `ss` (`weakness`, `willingness`, `fitness`), and
  `competitor weaknesses` escaped the phrase `competitor weakness` under v1.2.0.
* `IE_SINGULAR` and `SSE_SINGULAR` exist only so the two plural rules above do not split a noun
  whose singular ends in `ie` or `sse` from its own plural (`movie`/`movies`, `finesse`/`finesses`),
  which v1.2.0's answer-side fold kept together. Both sides reach the same spelling, and nothing else
  ever reads it.

What is NOT covered, and why:

* **Other `-es` plurals** (after x, ch, sh, z or a single s): no gated term needs them, and each
  collides with a common singular (`size`/`sizes`, `niche`/`niches`, `axe`/`axes`).
* **Irregular morphology** (`analysis`/`analyses`, `person`/`people`, `money`/`monies`): never
  guessed. A future irregular pair needs an explicit, reviewed mapping, not a rule.
* **Derivation** (`market`/`marketing`, `pay`/`payment`, `score`/`scoring`, `value`/`valuable`): not
  inflection at all. Two different words stay two different words.
* **Verbs.** Noun number is not verb person. A closed list of verb forms, written out one form at
  a time, is matched verbatim (`verbatim_spans`), so the verb `supports` never folds onto the noun
  `support`.

Known and kept: a singular ending in a lone `s` (`news`, `means`, `lens`) folds as if it were a
plural, exactly as v1.2.0's answer-side fold already did. A token with a digit is never folded.
"""

from __future__ import annotations

from .assertion_context import _TOKEN, _norm

__all__ = [
    "LEXICAL_INFLECTION_POLICY_VERSION",
    "INFLECTION_RULES",
    "INFLECTION_NOT_COVERED",
    "normalize_token",
    "normalized_forms",
    "inflection_spans",
    "verbatim_spans",
]

LEXICAL_INFLECTION_POLICY_VERSION = "opportunity-lexical-inflection@1.0.0"

_CONSONANTS = frozenset("bcdfghjklmnpqrstvwxyz")

#: The whole policy, as data, in the order it is applied: rule, what it matches, what it produces,
#: one worked example.
INFLECTION_RULES: tuple[tuple[str, str, str, str], ...] = (
    (
        "REGULAR_IES_PLURAL",
        "5+ letters, consonant + ies",
        "consonant + y",
        "industries -> industry",
    ),
    ("IE_SINGULAR", "4+ letters, consonant + ie", "consonant + y", "movie -> movy"),
    ("REGULAR_SSES_PLURAL", "6+ letters, sses", "ss", "weaknesses -> weakness"),
    ("SSE_SINGULAR", "5+ letters, sse", "ss", "finesse -> finess"),
    (
        "REGULAR_S_PLURAL",
        "4+ letters, s but not ss, us or is",
        "drop the s",
        "contracts -> contract",
    ),
)

#: What the policy deliberately leaves alone, each with its reason.
INFLECTION_NOT_COVERED: tuple[tuple[str, str], ...] = (
    (
        "-es after x, ch, sh, z or a single s",
        "no gated term needs it, and it collides with size/sizes, niche/niches, axe/axes",
    ),
    ("irregular morphology", "never guessed; it needs an explicit reviewed mapping"),
    ("derivation", "not inflection: market/marketing, pay/payment, score/scoring, value/valuable"),
    ("verb person", "a closed list of verb forms is matched verbatim, form by form"),
)


def normalize_token(token: str) -> str:
    """The canonical lexical form of one lower-case token. The only normalization in the gate."""
    if not token.isalpha():
        return token
    if len(token) >= 5 and token.endswith("ies") and token[-4] in _CONSONANTS:
        return token[:-3] + "y"
    if len(token) >= 4 and token.endswith("ie") and token[-3] in _CONSONANTS:
        return token[:-2] + "y"
    if len(token) >= 6 and token.endswith("sses"):
        return token[:-2]
    if len(token) >= 5 and token.endswith("sse"):
        return token[:-1]
    if len(token) >= 4 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def normalized_forms(text: str) -> frozenset[str]:
    """Every token of `text`, in its canonical form."""
    return frozenset(normalize_token(t) for t in _TOKEN.findall(_norm(text)))


def _spans(lowered: str, phrase: str, fold: bool) -> list[tuple[int, int]]:
    def form(token: str) -> str:
        return normalize_token(token) if fold else token

    parts = tuple(form(p) for p in _TOKEN.findall(_norm(phrase)))
    if not parts:
        return []
    tokens = [(form(m.group()), m.start(), m.end()) for m in _TOKEN.finditer(lowered)]
    found: list[tuple[int, int]] = []
    for index in range(len(tokens) - len(parts) + 1):
        window = tokens[index : index + len(parts)]
        if all(w == p for (w, _, _), p in zip(window, parts, strict=True)):
            found.append((window[0][1], window[-1][2]))
    return found


def inflection_spans(lowered: str, phrase: str) -> list[tuple[int, int]]:
    """Every occurrence of `phrase` in `lowered` as a whole-token run, compared in canonical form.

    The same function reads an answer and a supplied statement, so neither side can fold a form the
    other does not.
    """
    return _spans(lowered, phrase, True)


def verbatim_spans(lowered: str, phrase: str) -> list[tuple[int, int]]:
    """Every occurrence of `phrase` token for token, as written: for a closed list of verb forms
    that spells out each form it means, and only for that. No inflection applies."""
    return _spans(lowered, phrase, False)
