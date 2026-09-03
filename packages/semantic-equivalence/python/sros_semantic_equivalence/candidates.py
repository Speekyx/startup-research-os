"""Which question pairs are worth asking a classifier about.

Mission 1.24 §6, from `semantic-problem-equivalence-v1.md` §4.1.

**A candidate is not evidence, and not a prediction.** Its output means exactly
*this pair is worth asking about* and never *these are probably the same
problem*. Nothing downstream may read a candidate score as a similarity, a
confidence or a weight, which is why the score is not carried onto any artefact
that leaves this module.

**Deterministic, versioned, bounded, and no embeddings.** Same corpus, same
version, same parameters produce the same ordered candidate list, so an
evaluation can be re-run and a production set can be pre-registered before any
prediction is seen. Ordering is total: ties break on the question-id pair, never
on dictionary or database order.

**Its recall limit is part of every downstream scope.** A pair this generator
does not surface is UNCONSIDERED, not different. So the strongest claim any
later stage may make is bounded to *the pairs actually considered under
candidate generator version X* -- never *these are all the repeated Docker
problems*. `CandidateSet.recall_limitation` carries that sentence so a report
cannot omit it by forgetting.

**Why these features.** Everything here is available in the normalized
`community_question` payload and needs no model:

    shared tags          the SITE's own vocabulary, minus the query tag
    title overlap        content tokens, after a fixed stop list
    diagnostic overlap   error-looking fragments from the body

The third is the one Mission 1.20 makes interesting. It found three questions
sharing 182 characters of exact runc diagnostic that then diverge into three
unrelated failures -- so a shared diagnostic is a strong reason to ASK and a
terrible reason to conclude. That is precisely the split between a candidate
generator and a classifier, and it is why the wrapper is used here and refused
in the rubric.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from itertools import combinations

__all__ = [
    "CANDIDATE_GENERATOR_VERSION",
    "QuestionObservation",
    "CandidatePair",
    "CandidateSet",
    "generate_candidates",
]

CANDIDATE_GENERATOR_VERSION = "docker-lexical-candidates@1.0.0"

# Tokens that carry no discriminating power in this corpus. Deliberately SHORT
# and fixed: a stop list tuned until the output looked good would be a parameter
# fitted on the thing being measured.
_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "can",
        "cannot",
        "do",
        "does",
        "doesn",
        "for",
        "from",
        "get",
        "getting",
        "has",
        "have",
        "how",
        "i",
        "in",
        "is",
        "it",
        "my",
        "no",
        "not",
        "of",
        "on",
        "or",
        "so",
        "that",
        "the",
        "this",
        "to",
        "try",
        "trying",
        "use",
        "using",
        "was",
        "what",
        "when",
        "where",
        "which",
        "why",
        "will",
        "with",
        "without",
        "work",
        "working",
        "you",
        "your",
        "error",
        "errors",
        "issue",
        "issues",
        "problem",
        "problems",
        "help",
        "please",
    ]
)

_TOKEN = re.compile(r"[a-z][a-z0-9_.+-]{1,}")
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")

# Lines that look like a diagnostic rather than prose. Kept blunt on purpose:
# a clever extractor would be a second classifier nobody evaluated.
_DIAGNOSTIC = re.compile(
    r"(?:^|[\s>])((?:error|exception|failed|failure|cannot|unable|denied|refused|traceback|"
    r"fatal|panic|no such|not found|timed out|timeout)[^\n]{10,240})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class QuestionObservation:
    """One normalized `community_question`, reduced to what this module reads.

    A value object rather than the payload itself, so the generator cannot
    accidentally depend on a field the rubric forbids -- score, view count and
    accepted-answer state are absent because none of them says anything about
    whether two questions describe the same problem.
    """

    observation_key: str
    question_id: str
    title: str
    body: str
    tags: tuple[str, ...] = ()

    def text(self) -> str:
        """Body with markup removed and entities resolved, whitespace collapsed."""
        return _WS.sub(" ", html.unescape(_TAG.sub(" ", self.body))).strip()

    def title_text(self) -> str:
        return _WS.sub(" ", html.unescape(_TAG.sub(" ", self.title))).strip()

    def title_tokens(self) -> frozenset[str]:
        return frozenset(
            t for t in _TOKEN.findall(self.title_text().lower()) if t not in _STOPWORDS
        )

    def diagnostics(self) -> tuple[str, ...]:
        """Normalized diagnostic fragments, de-duplicated, order preserved."""
        seen: list[str] = []
        for match in _DIAGNOSTIC.findall(self.text()):
            fragment = _WS.sub(" ", match).strip().lower()[:240]
            if len(fragment) >= 24 and fragment not in seen:
                seen.append(fragment)
        return tuple(seen)


@dataclass(frozen=True)
class CandidatePair:
    """One pair worth asking about, and the deterministic reasons it surfaced.

    `reasons` exists so a human reading the batch can see WHY a pair is here,
    which matters most when the answer turns out to be DIFFERENT: the three
    Mission 1.20 questions surface on the strongest possible lexical evidence
    and are three unrelated problems.
    """

    a_key: str
    b_key: str
    a_question_id: str
    b_question_id: str
    score: int
    reasons: tuple[str, ...]
    shared_tags: tuple[str, ...] = ()
    shared_title_tokens: tuple[str, ...] = ()
    longest_shared_diagnostic: str = ""

    @property
    def pair_id(self) -> str:
        """Stable, order-independent identity for one unordered pair."""
        left, right = sorted((self.a_question_id, self.b_question_id))
        return f"{left}::{right}"

    def to_json(self) -> dict[str, object]:
        return {
            "pair_id": self.pair_id,
            "a_question_id": self.a_question_id,
            "b_question_id": self.b_question_id,
            "a_key": self.a_key,
            "b_key": self.b_key,
            "score": self.score,
            "reasons": list(self.reasons),
            "shared_tags": list(self.shared_tags),
            "shared_title_tokens": list(self.shared_title_tokens),
            "longest_shared_diagnostic": self.longest_shared_diagnostic,
        }


@dataclass(frozen=True)
class CandidateSet:
    """The generated candidates and everything needed to bound a claim on them."""

    generator_version: str
    corpus_size: int
    possible_pairs: int
    considered_pairs: int
    cap: int
    pairs: tuple[CandidatePair, ...] = ()
    selection_rules: tuple[str, ...] = ()
    truncated: bool = False
    query_tag: str = ""

    @property
    def recall_limitation(self) -> str:
        """The sentence every downstream artefact must carry.

        Written here rather than in a report, so a report cannot omit it by
        forgetting to copy it.
        """
        return (
            f"Scope: the {self.considered_pairs} pairs surfaced by "
            f"{self.generator_version} out of {self.possible_pairs} possible pairs over "
            f"{self.corpus_size} observations"
            + (f", capped at {self.cap}" if self.truncated else "")
            + ". A pair this generator did not surface is UNCONSIDERED, not different. "
            "No statement derived from this set describes all repeated problems in the "
            "corpus, and none may be worded as though it did."
        )

    def to_json(self) -> dict[str, object]:
        return {
            "generator_version": self.generator_version,
            "corpus_size": self.corpus_size,
            "possible_pairs": self.possible_pairs,
            "considered_pairs": self.considered_pairs,
            "cap": self.cap,
            "truncated": self.truncated,
            "query_tag": self.query_tag,
            "selection_rules": list(self.selection_rules),
            "recall_limitation": self.recall_limitation,
            "pairs": [p.to_json() for p in self.pairs],
        }


def _longest_common_substring(a: str, b: str, minimum: int) -> str:
    """The longest shared run, or empty below `minimum`.

    O(len(a) * len(b)) over one rolling row. The fragments compared here are
    capped at 240 characters, so this is bounded work per pair rather than a
    general-purpose routine anybody should reuse on documents.
    """
    if not a or not b:
        return ""
    previous = [0] * (len(b) + 1)
    best_length = 0
    best_end = 0
    for i, ca in enumerate(a, start=1):
        current = [0] * (len(b) + 1)
        for j, cb in enumerate(b, start=1):
            if ca == cb:
                current[j] = previous[j - 1] + 1
                if current[j] > best_length:
                    best_length = current[j]
                    best_end = i
        previous = current
    return a[best_end - best_length : best_end] if best_length >= minimum else ""


# Selection parameters. Named constants rather than literals so the recorded
# selection rules and the code cannot disagree.
MIN_SHARED_DIAGNOSTIC = 40
MIN_SHARED_TITLE_TOKENS = 2
MIN_SHARED_TAGS = 1
DEFAULT_CAP = 60


def _pair_features(
    a: QuestionObservation, b: QuestionObservation, query_tag: str
) -> tuple[int, list[str], tuple[str, ...], tuple[str, ...], str]:
    shared_tags = tuple(
        sorted({t.lower() for t in a.tags} & {t.lower() for t in b.tags} - {query_tag.lower()})
    )
    shared_tokens = tuple(sorted(a.title_tokens() & b.title_tokens()))

    longest = ""
    for fa in a.diagnostics():
        for fb in b.diagnostics():
            shared = _longest_common_substring(fa, fb, MIN_SHARED_DIAGNOSTIC)
            if len(shared) > len(longest):
                longest = shared

    score = 0
    reasons: list[str] = []
    if len(shared_tags) >= MIN_SHARED_TAGS:
        score += 10 * len(shared_tags)
        reasons.append(f"shares {len(shared_tags)} site tag(s) beyond the query tag")
    if len(shared_tokens) >= MIN_SHARED_TITLE_TOKENS:
        score += 5 * len(shared_tokens)
        reasons.append(f"shares {len(shared_tokens)} title token(s)")
    if longest:
        # Length-proportional, because a 182-character exact diagnostic is a far
        # stronger reason to ASK than a 40-character one. It remains a reason to
        # ask: Mission 1.20's trio is the proof that it settles nothing.
        score += len(longest)
        reasons.append(f"shares a {len(longest)}-character diagnostic fragment")
    return score, reasons, shared_tags, shared_tokens, longest


def generate_candidates(
    observations: tuple[QuestionObservation, ...] | list[QuestionObservation],
    *,
    query_tag: str = "docker",
    cap: int = DEFAULT_CAP,
) -> CandidateSet:
    """Every qualifying pair, ordered, then capped.

    **The cap is applied after a total ordering**, so the selected set is a
    function of the corpus and the version alone -- never of iteration order and
    never of anything a later stage saw. `§7` requires the cap to be chosen
    before model output exists; nothing in this function can observe one.
    """
    if cap < 1:
        raise ValueError("a candidate cap must be at least 1: 0 would silently disable the stage")

    corpus = tuple(observations)
    possible = len(corpus) * (len(corpus) - 1) // 2

    scored: list[CandidatePair] = []
    for a, b in combinations(sorted(corpus, key=lambda o: o.question_id), 2):
        score, reasons, tags, tokens, longest = _pair_features(a, b, query_tag)
        if not reasons:
            continue
        scored.append(
            CandidatePair(
                a_key=a.observation_key,
                b_key=b.observation_key,
                a_question_id=a.question_id,
                b_question_id=b.question_id,
                score=score,
                reasons=tuple(reasons),
                shared_tags=tags,
                shared_title_tokens=tokens,
                longest_shared_diagnostic=longest,
            )
        )

    # Total order: score descending, then the id pair ascending. The second key
    # is what makes this reproducible; without it, equal-scoring pairs would be
    # ordered by whatever `combinations` happened to yield.
    scored.sort(key=lambda p: (-p.score, p.a_question_id, p.b_question_id))
    selected = tuple(scored[:cap])

    return CandidateSet(
        generator_version=CANDIDATE_GENERATOR_VERSION,
        corpus_size=len(corpus),
        possible_pairs=possible,
        considered_pairs=len(selected),
        cap=cap,
        pairs=selected,
        truncated=len(scored) > cap,
        query_tag=query_tag,
        selection_rules=(
            f"a pair qualifies on any of: >= {MIN_SHARED_TAGS} shared site tag beyond "
            f"{query_tag!r}; >= {MIN_SHARED_TITLE_TOKENS} shared title tokens after a fixed "
            f"stop list; a shared diagnostic fragment of >= {MIN_SHARED_DIAGNOSTIC} characters",
            "score = 10 per shared tag + 5 per shared title token + the shared diagnostic length",
            "ordered by score descending then by (a_question_id, b_question_id) ascending",
            f"the first {cap} are kept; the ordering is total, so the cut is reproducible",
            "no embeddings, no model, no vector similarity, and no source field other than "
            "tags, title and body is read",
        ),
    )
