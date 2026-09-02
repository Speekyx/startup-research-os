"""Selecting the pairs a human is asked to label.

Mission 1.24 §8 and §9.

**The selection rule is declared before the batch exists and is deterministic**,
so nobody -- including whoever writes it -- can shape the reference set around
what they hope it will show. Choosing pairs by eye is exactly how a reference set
comes to contain the cases the classifier was going to get right.

    ranks 1..HEAD          every one, the strongest candidates
    ranks HEAD+1..end      every STRIDE-th, for spread across the score range

The head is where the interesting negatives live: Mission 1.20's trio has the
highest lexical evidence in the corpus and is three unrelated problems. The
stride is what stops the batch being one shape.

**No model prediction is computed, and none can be.** This module imports no
gateway and no classifier. The operator labels blind because there is nothing to
show them.

**The batch carries excerpts, not posts.** A reviewer needs enough to judge the
actionable failure concept; a full body is a licensed corpus pasted into a
review file for no gain, and it makes the batch unreadable, which costs label
quality.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .candidates import CandidatePair, CandidateSet, QuestionObservation
from .evaluation import Split, assign_split

__all__ = [
    "BATCH_SELECTION_VERSION",
    "HEAD",
    "STRIDE",
    "ReviewItem",
    "ReviewBatch",
    "select_review_batch",
]

BATCH_SELECTION_VERSION = "review-batch-selection@1.0.0"
# Sized so the HOLDOUT half clears the acceptance criterion's minimum of 12 with
# margin -- 17 at the time of writing -- rather than landing exactly on it. A
# batch that meets a threshold exactly fails it the moment one pair turns out to
# be unlabelable, and the fallback would then be EVALUATION_INSUFFICIENT for a
# reason that has nothing to do with the classifier.
HEAD = 20
STRIDE = 2

_WS = re.compile(r"\s+")


def _excerpt(observation: QuestionObservation, limit: int = 320) -> str:
    """The most decision-relevant passage, or the opening if none stands out.

    Prefers a diagnostic fragment, because the actionable failure concept is
    usually there. Falls back to the start of the body rather than to nothing:
    a question with no diagnostic is one of the pairs a reviewer most needs to
    see, since it is a likely ABSTAIN.
    """
    diagnostics = observation.diagnostics()
    if diagnostics:
        return _WS.sub(" ", diagnostics[0])[:limit]
    return _WS.sub(" ", observation.text())[:limit]


@dataclass(frozen=True)
class ReviewItem:
    """One pair as the operator sees it. No prediction, by construction."""

    pair_id: str
    rank: int
    split: Split
    a_question_id: str
    b_question_id: str
    a_title: str
    b_title: str
    a_tags: tuple[str, ...]
    b_tags: tuple[str, ...]
    a_excerpt: str
    b_excerpt: str
    surfaced_because: tuple[str, ...]
    shared_diagnostic: str = ""
    holdout_exclusion_reason: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "pair_id": self.pair_id,
            "rank": self.rank,
            "split": self.split.value,
            "a": {
                "question_id": self.a_question_id,
                "title": self.a_title,
                "tags": list(self.a_tags),
                "excerpt": self.a_excerpt,
            },
            "b": {
                "question_id": self.b_question_id,
                "title": self.b_title,
                "tags": list(self.b_tags),
                "excerpt": self.b_excerpt,
            },
            "surfaced_because": list(self.surfaced_because),
            "shared_diagnostic": self.shared_diagnostic,
            "holdout_exclusion_reason": self.holdout_exclusion_reason,
        }


@dataclass(frozen=True)
class ReviewBatch:
    selection_version: str
    candidate_generator_version: str
    rubric_version: str
    items: tuple[ReviewItem, ...]
    selection_rule: str
    recall_limitation: str

    @property
    def development(self) -> tuple[ReviewItem, ...]:
        return tuple(i for i in self.items if i.split is Split.DEVELOPMENT)

    @property
    def holdout(self) -> tuple[ReviewItem, ...]:
        return tuple(i for i in self.items if i.split is Split.HOLDOUT)

    def to_json(self) -> dict[str, object]:
        return {
            "selection_version": self.selection_version,
            "candidate_generator_version": self.candidate_generator_version,
            "rubric_version": self.rubric_version,
            "selection_rule": self.selection_rule,
            "recall_limitation": self.recall_limitation,
            "development_count": len(self.development),
            "holdout_count": len(self.holdout),
            "items": [i.to_json() for i in self.items],
        }


def select_review_batch(
    candidates: CandidateSet,
    observations: dict[str, QuestionObservation],
    *,
    rubric_version: str,
    head: int = HEAD,
    stride: int = STRIDE,
) -> ReviewBatch:
    """Head plus stride, in candidate order, split deterministically."""
    from .evaluation import HOLDOUT_EXCLUSIONS

    chosen: list[tuple[int, CandidatePair]] = []
    for rank, pair in enumerate(candidates.pairs, start=1):
        if rank <= head or (rank - head) % stride == 1:
            chosen.append((rank, pair))

    items = []
    for rank, pair in chosen:
        a = observations[pair.a_question_id]
        b = observations[pair.b_question_id]
        items.append(
            ReviewItem(
                pair_id=pair.pair_id,
                rank=rank,
                split=assign_split(pair.pair_id),
                a_question_id=a.question_id,
                b_question_id=b.question_id,
                a_title=a.title_text(),
                b_title=b.title_text(),
                a_tags=a.tags,
                b_tags=b.tags,
                a_excerpt=_excerpt(a),
                b_excerpt=_excerpt(b),
                surfaced_because=pair.reasons,
                shared_diagnostic=pair.longest_shared_diagnostic,
                holdout_exclusion_reason=HOLDOUT_EXCLUSIONS.get(pair.pair_id, ""),
            )
        )

    return ReviewBatch(
        selection_version=BATCH_SELECTION_VERSION,
        candidate_generator_version=candidates.generator_version,
        rubric_version=rubric_version,
        items=tuple(items),
        selection_rule=(
            f"ranks 1..{head} in candidate order, then every {stride}rd thereafter. "
            "Declared before the batch was produced and computed from the candidate "
            "ordering alone, so no pair was chosen for what it might show"
        ),
        recall_limitation=candidates.recall_limitation,
    )
