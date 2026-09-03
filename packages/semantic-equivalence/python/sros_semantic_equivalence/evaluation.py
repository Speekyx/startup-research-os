"""Human labels, the development/holdout split, and the predeclared criterion.

Mission 1.24 §8 to §12.

**Human labels are the reference and the model never creates its own.** A model
scored against its own output measures self-consistency, and self-consistency is
what a confidently wrong classifier has the most of.

**The split is computed from the pair id, before any label or prediction
exists.** A split chosen later -- however honestly -- is a split that could have
been chosen to help, and nobody reading the result afterwards can tell the
difference. `assign_split` is a pure function of the pair id and a declared
seed, so the assignment is reproducible and checkable.

**One assignment is forced, and it is the interesting one.** The rubric's worked
examples quote the Mission 1.20 runc pair by id and describe the pattern all
three share. Those pairs are therefore IN-SAMPLE by construction: classifying
them correctly demonstrates that the classifier can read its own rubric, which is
worth knowing and is not evidence of generalisation. They are pinned to
DEVELOPMENT, and `HOLDOUT_EXCLUSIONS` records why -- so that a later report
cannot quietly count them as holdout successes.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum

from .rubric import RUBRIC_VERSION, EquivalenceDecision

__all__ = [
    "ACCEPTANCE_CRITERIA",
    "SPLIT_SEED",
    "HOLDOUT_FRACTION",
    "HOLDOUT_EXCLUSIONS",
    "Split",
    "HumanDecision",
    "HumanLabel",
    "LabelSet",
    "AcceptanceCriterion",
    "V1_ACCEPTANCE",
    "V2_ACCEPTANCE",
    "EvaluationResult",
    "assign_split",
    "evaluate",
]

# Declared before any label exists, and recorded so a re-run can reproduce the
# assignment exactly.
SPLIT_SEED = "mission-1.24/problem-equivalence-rubric@1.0.0"
HOLDOUT_FRACTION = 0.5

# Pairs that may never be counted as holdout, whatever the split function says,
# with the reason attached to each. An exclusion with no stated reason is an
# exclusion somebody will delete.
HOLDOUT_EXCLUSIONS: dict[str, str] = {
    "78086542::78099680": (
        "quoted verbatim in the rubric's non-qualifying worked example, so the classifier "
        "is shown the answer in its own instructions"
    ),
    "78086542::78099519": (
        "the same shared-wrapper pattern the rubric describes and names; in-sample by "
        "description even though the ids are not quoted"
    ),
    "78099519::78099680": (
        "the same shared-wrapper pattern the rubric describes and names; in-sample by "
        "description even though the ids are not quoted"
    ),
    "78088430::78090396": (
        "quoted in the rubric's borderline worked example, with its decision stated"
    ),
    "78096175::78097071": (
        "quoted in the rubric's abstention worked example, with its decision stated"
    ),
}


class Split(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    HOLDOUT = "HOLDOUT"


class HumanDecision(StrEnum):
    """What an operator may answer.

    `UNCERTAIN` is the human counterpart of the classifier's ABSTAIN and is not
    a missing label: a reviewer who cannot decide from the published text has
    made a finding about the text, and discarding it would bias the reference
    set towards the pairs that happen to be easy.
    """

    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    UNCERTAIN = "UNCERTAIN"

    def as_model_decision(self) -> EquivalenceDecision:
        return {
            HumanDecision.SAME: EquivalenceDecision.SAME_PROBLEM,
            HumanDecision.DIFFERENT: EquivalenceDecision.DIFFERENT_PROBLEM,
            HumanDecision.UNCERTAIN: EquivalenceDecision.ABSTAIN,
        }[self]


def assign_split(
    pair_id: str, *, seed: str = SPLIT_SEED, holdout: float = HOLDOUT_FRACTION
) -> Split:
    """Deterministic, reproducible, and computable before any label exists.

    sha256 rather than `hash()`: Python's string hash is salted per process, so
    a split built on it would differ between the run that recorded it and the
    run that checked it.
    """
    if pair_id in HOLDOUT_EXCLUSIONS:
        return Split.DEVELOPMENT
    digest = hashlib.sha256(f"{seed}|{pair_id}".encode()).digest()
    bucket = int.from_bytes(digest[:4], "big") / 0xFFFFFFFF
    return Split.HOLDOUT if bucket < holdout else Split.DEVELOPMENT


@dataclass(frozen=True)
class HumanLabel:
    """One operator judgement, with the provenance §10 requires.

    No Stack Overflow author identity appears, because none was ever acquired.
    `reviewer` is the person accountable for the judgement, which is a different
    thing and is required: an unattributed reference label is one nobody can
    question later.
    """

    pair_id: str
    a_question_id: str
    b_question_id: str
    reviewer: str
    decision: HumanDecision
    labelled_at: str
    split: Split
    rubric_version: str = RUBRIC_VERSION
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.reviewer.strip() or self.reviewer.strip().lower() in {
            "todo",
            "n/a",
            "<name>",
            "unknown",
        }:
            raise ValueError(
                "a reference label requires a named reviewer. A validator that rejects "
                "emptiness has not yet rejected meaninglessness (testing-strategy.md)"
            )

    def to_json(self) -> dict[str, object]:
        return {
            "pair_id": self.pair_id,
            "a_question_id": self.a_question_id,
            "b_question_id": self.b_question_id,
            "reviewer": self.reviewer,
            "decision": self.decision.value,
            "labelled_at": self.labelled_at,
            "split": self.split.value,
            "rubric_version": self.rubric_version,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class LabelSet:
    labels: tuple[HumanLabel, ...] = ()

    def for_split(self, split: Split) -> tuple[HumanLabel, ...]:
        return tuple(label for label in self.labels if label.split is split)

    def distribution(self) -> dict[str, int]:
        return dict(Counter(label.decision.value for label in self.labels))

    @property
    def positives(self) -> tuple[HumanLabel, ...]:
        return tuple(label for label in self.labels if label.decision is HumanDecision.SAME)


@dataclass(frozen=True)
class AcceptanceCriterion:
    """Stated BEFORE holdout results are seen, and stated as a rule.

    V1 prioritises avoiding a false SAME. The criterion is therefore about false
    positives and about honesty regarding sample size, not about accuracy: an
    accuracy figure over a few dozen pairs would be a number with no interval,
    and quoting one would make a small experiment look calibrated.
    """

    name: str
    max_false_same: int
    min_labelled_holdout: int
    min_positive_labels: int
    statement: str

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "max_false_same": self.max_false_same,
            "min_labelled_holdout": self.min_labelled_holdout,
            "min_positive_labels": self.min_positive_labels,
            "statement": self.statement,
        }


V1_ACCEPTANCE = AcceptanceCriterion(
    name="v1-false-positive-avoidance",
    max_false_same=0,
    min_labelled_holdout=12,
    min_positive_labels=1,
    statement=(
        "The classifier passes only if it produces ZERO false SAME_PROBLEM decisions on the "
        "holdout -- a pair the reviewer labelled DIFFERENT or UNCERTAIN and the model called "
        "SAME. A model may ABSTAIN freely; abstention is never counted against it, because "
        "the alternative to an abstention here is a guess. The evaluation is only reportable "
        "at all with at least 12 labelled holdout pairs and at least one SAME anywhere in the "
        "reference set: with no positive, a classifier that answered DIFFERENT to everything "
        "would score perfectly, and nothing would have been measured. Below either threshold "
        "the outcome is EVALUATION_INSUFFICIENT rather than a pass. No accuracy, precision or "
        "recall figure is a pass condition, because a proportion over a few dozen pairs has an "
        "interval wider than any difference it could show."
    ),
)


V2_ACCEPTANCE = AcceptanceCriterion(
    name="v2-false-positive-avoidance-with-a-testable-split",
    max_false_same=0,
    min_labelled_holdout=12,
    min_positive_labels=1,
    statement=(
        "As V1, with one word changed and it is the word that mattered. The positive "
        "minimum applies to THE SPLIT BEING SCORED, not to the reference set as a whole. "
        "V1 said 'at least one SAME anywhere in the reference set', and Mission 1.24's run "
        "satisfied it with a single SAME that fell in DEVELOPMENT while the HOLDOUT held "
        "none -- so the holdout could not distinguish the classifier from one hard-coded to "
        "answer DIFFERENT, and it recorded a pass that a constant answer would also have "
        "recorded. The rest is unchanged: zero false SAME, at least 12 labelled pairs in the "
        "scored split, abstention never counted against the model, and no accuracy figure as "
        "a pass condition."
    ),
)

# Which criterion a run was scored under is part of its record. V1 is kept
# because Mission 1.24 was scored under it and rewriting it would leave that
# report describing a rule that no longer exists.
ACCEPTANCE_CRITERIA = {c.name: c for c in (V1_ACCEPTANCE, V2_ACCEPTANCE)}


@dataclass(frozen=True)
class EvaluationResult:
    """The measured outcome, and whether it meets the predeclared criterion."""

    criterion: AcceptanceCriterion
    split: Split
    labelled: int
    positives: int
    matrix: dict[str, int] = field(default_factory=dict)
    false_same: tuple[str, ...] = ()
    false_different: tuple[str, ...] = ()
    abstentions: int = 0
    agreements: int = 0
    outcome: str = ""
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.outcome == "MODEL_EVALUATION_PASSED"

    def to_json(self) -> dict[str, object]:
        return {
            "criterion": self.criterion.to_json(),
            "split": self.split.value,
            "labelled": self.labelled,
            "positives": self.positives,
            "confusion_matrix": dict(self.matrix),
            "false_same": list(self.false_same),
            "false_different": list(self.false_different),
            "abstentions": self.abstentions,
            "agreements": self.agreements,
            "outcome": self.outcome,
            "notes": list(self.notes),
        }


def evaluate(
    labels: LabelSet,
    predictions: dict[str, EquivalenceDecision],
    *,
    split: Split = Split.HOLDOUT,
    criterion: AcceptanceCriterion = V1_ACCEPTANCE,
) -> EvaluationResult:
    """Score predictions against human labels on one split.

    Only pairs that are BOTH labelled and predicted are scored. A labelled pair
    with no prediction is not an error and not an abstention -- it is a pair the
    run did not reach, and counting it either way would move the result.
    """
    scored = [label for label in labels.for_split(split) if label.pair_id in predictions]
    matrix: Counter[str] = Counter()
    false_same: list[str] = []
    false_different: list[str] = []
    abstentions = 0
    agreements = 0

    for label in scored:
        predicted = predictions[label.pair_id]
        matrix[f"{label.decision.value}->{predicted.value}"] += 1
        if predicted is EquivalenceDecision.ABSTAIN:
            abstentions += 1
        if (
            predicted is EquivalenceDecision.SAME_PROBLEM
            and label.decision is not HumanDecision.SAME
        ):
            false_same.append(label.pair_id)
        if (
            predicted is EquivalenceDecision.DIFFERENT_PROBLEM
            and label.decision is HumanDecision.SAME
        ):
            false_different.append(label.pair_id)
        if predicted is label.decision.as_model_decision():
            agreements += 1

    # V1 counts positives across the whole reference set; V2 counts them in the
    # split being scored. The criterion carries which, so a historical result
    # stays reproducible under the rule it was actually scored against.
    if criterion.name.startswith("v1-"):
        positives = len(labels.positives)
    else:
        positives = sum(
            1 for label in labels.for_split(split) if label.decision is HumanDecision.SAME
        )
    notes: list[str] = []
    if len(scored) < criterion.min_labelled_holdout:
        outcome = "EVALUATION_INSUFFICIENT"
        notes.append(
            f"{len(scored)} labelled and predicted pairs on {split.value}; the criterion "
            f"requires at least {criterion.min_labelled_holdout}"
        )
    elif positives < criterion.min_positive_labels:
        outcome = "EVALUATION_INSUFFICIENT"
        notes.append(
            "no SAME label is available to this criterion, so a classifier answering "
            "DIFFERENT to everything would score perfectly and nothing would have been "
            "measured about whether a SAME prediction can be trusted"
        )
    elif len(false_same) > criterion.max_false_same:
        outcome = "MODEL_EVALUATION_FAILED"
        notes.append(
            f"{len(false_same)} false SAME_PROBLEM decision(s); the criterion permits "
            f"{criterion.max_false_same}"
        )
    else:
        outcome = "MODEL_EVALUATION_PASSED"
        notes.append(
            f"zero false SAME over {len(scored)} labelled holdout pairs. This is a small "
            "sample and is NOT a calibration: no probability may be attached to any decision"
        )

    return EvaluationResult(
        criterion=criterion,
        split=split,
        labelled=len(scored),
        positives=positives,
        matrix=dict(matrix),
        false_same=tuple(false_same),
        false_different=tuple(false_different),
        abstentions=abstentions,
        agreements=agreements,
        outcome=outcome,
        notes=tuple(notes),
    )
