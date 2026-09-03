"""Ordering candidate pairs for problem-family review.

Mission 1.25 §6, and the answer to the question the brief asks is measured
rather than assumed.

**Is `docker-lexical-candidates@1.0.0` structurally too narrow for family
detection? No.** It surfaces 731 of the 3 916 possible pairs over the 89-question
corpus, it reaches 84 of the 89 observations, and it surfaced the one pair the
Mission 1.24 reference set called SAME -- by shared TAGS, with no shared title
token and no shared diagnostic. Its qualifying rule is a "worth asking about"
rule and it works for both relations.

**Its ORDERING is wrong for this relation, and that is a different defect.** It
scores a shared diagnostic fragment by raw character length, which is right for
exact equivalence -- a 106-character shared runc string is the strongest possible
reason to ask whether two failures are the same. For FAMILY it is close to
worthless: Mission 1.20 established that the same wrapper precedes unrelated
goals. Under that ordering the runc trio ranks 1-3 and the one family-shaped pair
ranks **39**, so a reviewer handed the top 20 would see almost no family
candidates.

**So the recall is reused and only the ordering is versioned.** This module
imports the qualifying predicate from `candidates.py` rather than restating it, a
test asserts the two consider exactly the same pairs, and the recall limitation
sentence is inherited unchanged.

    rarest shared tag  its RARITY in this corpus, computed from the corpus
    title tokens       a small per-token weight
    shared diagnostic  WEIGHT ZERO

**Why the rarest shared tag rather than the sum.** Summing over every shared tag
rewards pairs that share a whole STACK -- Java plus Spring Boot plus Maven -- and
`FAMILY_INSUFFICIENT_ALONE` lists exactly that as insufficient. Measured on the
corpus, the summing variant ranked the one family-shaped pair 315th of 731 and
kept the runc trio in the top six. The maximum rewards sharing ONE specific
thing, which is closer to sharing a concern.

**Why the diagnostic weight is zero, not small.** Mission 1.20 established that
an identical 106-character wrapper precedes three unrelated blocked goals. For
THIS relation a shared wrapper therefore contributes nothing, and a small
positive constant would be the claim that it contributes a little -- which the
evidence refutes. At zero the runc trio falls from rank 3 to rank 239, which is
where a wrapper belongs when the question is about goals. **The hard negatives
still reach the review batch**, by explicit inclusion rather than by ordering,
because a batch must contain the cases the classifier must get right.

**AND RARITY IS A PROXY FOR SPECIFICITY, NOT FOR CONCERN.** This is the honest
limit of a deterministic generator and it is stated rather than hidden. `github`
and `docker-desktop` are rare and name technologies; `environment-variables` is
rare and names a concern. Nothing lexical separates them without a hand-written
list of which tags count as concerns -- a judgement nobody reviewed, wrong on the
next corpus, and exactly the kind of tuning this stage must not contain. So the
top of the ordering is a MIX of concern-shaped and stack-shaped pairs, and
separating them is the reviewer's job. That is what "worth asking about" means.

**This is still not a prediction.** A high rank means *worth asking about*. It
never means *likely the same family*, and no downstream artifact carries the
score.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from .candidates import (
    MIN_SHARED_DIAGNOSTIC,
    MIN_SHARED_TAGS,
    MIN_SHARED_TITLE_TOKENS,
    CandidatePair,
    CandidateSet,
    QuestionObservation,
    _longest_common_substring,
)

__all__ = [
    "FAMILY_CANDIDATE_GENERATOR_VERSION",
    "DIAGNOSTIC_WEIGHT",
    "DEFAULT_FAMILY_CAP",
    "tag_rarity",
    "generate_family_candidates",
]

FAMILY_CANDIDATE_GENERATOR_VERSION = "docker-problem-family-candidates@1.0.0"

# ZERO, and the zero is the argument. A shared wrapper is evidence about the
# machine's reporting and not about anyone's goal, so for this relation it
# contributes nothing. It still QUALIFIES a pair -- the predicate is imported
# unchanged -- it just does not promote one.
DIAGNOSTIC_WEIGHT = 0.0

TITLE_TOKEN_WEIGHT = 1.0
DEFAULT_FAMILY_CAP = 60


def tag_rarity(observations: tuple[QuestionObservation, ...]) -> dict[str, float]:
    """Inverse document frequency per tag, over this corpus.

    `log(N / count)`, so a tag on every observation scores 0 and a tag on three
    of eighty-nine scores about 3.4. Computed from the corpus handed in rather
    than from a fixed list: a hard-coded stop list of "generic" tags would be a
    judgement about Docker that nobody reviewed, and it would be wrong on the
    next corpus.
    """
    total = len(observations)
    if total == 0:
        return {}
    counts: Counter[str] = Counter()
    for observation in observations:
        counts.update({tag.lower() for tag in observation.tags})
    return {tag: math.log(total / count) for tag, count in counts.items()}


@dataclass(frozen=True)
class _Features:
    score: float
    reasons: tuple[str, ...]
    shared_tags: tuple[str, ...]
    shared_tokens: tuple[str, ...]
    longest: str


def _features(
    a: QuestionObservation,
    b: QuestionObservation,
    query_tag: str,
    rarity: dict[str, float],
) -> _Features | None:
    """The same QUALIFYING rule as `candidates.py`, scored differently.

    Qualification and ordering are separated deliberately: a pair either is or
    is not worth asking about, and that judgement belongs to one place. What
    differs between the two relations is which of the qualifying pairs a
    reviewer should see first.
    """
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

    qualifies_on_tags = len(shared_tags) >= MIN_SHARED_TAGS
    qualifies_on_tokens = len(shared_tokens) >= MIN_SHARED_TITLE_TOKENS
    if not (qualifies_on_tags or qualifies_on_tokens or longest):
        return None

    score = 0.0
    reasons: list[str] = []
    if qualifies_on_tags:
        rarest = max(shared_tags, key=lambda t: rarity.get(t, 0.0))
        score += rarity.get(rarest, 0.0)
        reasons.append(
            f"shares {len(shared_tags)} site tag(s) beyond the query tag, rarest "
            f"{rarest!r} (rarity {rarity.get(rarest, 0.0):.1f})"
        )
    if qualifies_on_tokens:
        score += TITLE_TOKEN_WEIGHT * len(shared_tokens)
        reasons.append(f"shares {len(shared_tokens)} title token(s)")
    if longest:
        score += DIAGNOSTIC_WEIGHT
        reasons.append(
            f"shares a {len(longest)}-character diagnostic fragment, which qualifies the "
            "pair and promotes it by nothing: a shared wrapper is not a shared goal"
        )
    return _Features(score, tuple(reasons), shared_tags, shared_tokens, longest)


def generate_family_candidates(
    observations: tuple[QuestionObservation, ...] | list[QuestionObservation],
    *,
    query_tag: str = "docker",
    cap: int = DEFAULT_FAMILY_CAP,
) -> CandidateSet:
    """Every qualifying pair, ordered for family review, then capped.

    Returns the same `CandidateSet` type as the exact-equivalence generator, and
    carries its own version so an artifact can never be ambiguous about which
    ordering produced it. `CandidatePair.score` is an int on that type, so the
    weighted score is rounded for storage -- the ORDER is computed on the
    unrounded value, and a test asserts the two agree.
    """
    if cap < 1:
        raise ValueError("a candidate cap must be at least 1: 0 would silently disable the stage")

    corpus = tuple(observations)
    rarity = tag_rarity(corpus)
    possible = len(corpus) * (len(corpus) - 1) // 2

    scored: list[tuple[float, CandidatePair]] = []
    for a, b in combinations(sorted(corpus, key=lambda o: o.question_id), 2):
        features = _features(a, b, query_tag, rarity)
        if features is None:
            continue
        scored.append(
            (
                features.score,
                CandidatePair(
                    a_key=a.observation_key,
                    b_key=b.observation_key,
                    a_question_id=a.question_id,
                    b_question_id=b.question_id,
                    score=round(features.score),
                    reasons=features.reasons,
                    shared_tags=features.shared_tags,
                    shared_title_tokens=features.shared_tokens,
                    longest_shared_diagnostic=features.longest,
                ),
            )
        )

    # Total order: weighted score descending, then the id pair ascending. The
    # second key is what makes the cut reproducible; without it, equal-scoring
    # pairs would be ordered by whatever `combinations` happened to yield.
    scored.sort(key=lambda item: (-item[0], item[1].a_question_id, item[1].b_question_id))
    selected = tuple(pair for _, pair in scored[:cap])

    return CandidateSet(
        generator_version=FAMILY_CANDIDATE_GENERATOR_VERSION,
        corpus_size=len(corpus),
        possible_pairs=possible,
        considered_pairs=len(selected),
        cap=cap,
        pairs=selected,
        truncated=len(scored) > cap,
        query_tag=query_tag,
        selection_rules=(
            "the QUALIFYING rule is `docker-lexical-candidates@1.0.0`'s, unchanged and "
            "imported rather than restated, so both relations consider the same pairs",
            f"score = rarity of the RAREST shared tag + {TITLE_TOKEN_WEIGHT} per shared "
            f"title token + {DIAGNOSTIC_WEIGHT} for a shared diagnostic fragment",
            "tag rarity is log(N / observations carrying the tag), computed from this "
            "corpus. A tag on every observation contributes 0",
            "the RAREST shared tag rather than the sum: summing rewards sharing a whole "
            "technology stack, which the rubric lists as insufficient",
            "a shared diagnostic weighs ZERO. Mission 1.20 established that an identical "
            "wrapper precedes unrelated blocked goals, so it qualifies a pair and "
            "promotes it by nothing",
            "rarity measures SPECIFICITY, not concern: a rare technology tag and a rare "
            "concern tag are indistinguishable here, so the ordering mixes both and the "
            "reviewer separates them",
            "ordered by score descending then by (a_question_id, b_question_id) ascending",
            f"the first {cap} are kept; the ordering is total, so the cut is reproducible",
            "no embeddings, no model, no vector similarity, and no source field other "
            "than tags, title and body is read",
        ),
    )
