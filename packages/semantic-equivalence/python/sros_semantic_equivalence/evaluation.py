"""Reference labels, the development/holdout split, and the predeclared criterion.

Mission 1.24 §8 to §12.

**The reference labels are not the model's own output, and the model never
creates them.** A model scored against its own predictions measures
self-consistency, which is what a confidently wrong classifier has the most of.

**But a reference label is not automatically human, and this contract now says
which it is.** Mission 1.24's 40 labels were supplied `AI_ASSISTED_PROVISIONAL`
by a different assistant, not by an independent human domain expert. Describing
them as human ground truth would have been the most misleading sentence in this
repository, so `ReferenceOrigin` is required on every label and
`human_ground_truth_established` is derived from it rather than assumed.

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

from .relations import EquivalenceRelation
from .rubric import RUBRIC_VERSION, EquivalenceDecision

__all__ = [
    "ACCEPTANCE_CRITERIA",
    "SPLIT_SEED",
    "HOLDOUT_FRACTION",
    "HOLDOUT_EXCLUSIONS",
    "Split",
    "ReferenceDecision",
    "ReferenceLabel",
    "ReferenceOrigin",
    "LabelSet",
    "AcceptanceCriterion",
    "FAMILY_V1_ACCEPTANCE",
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


class ReferenceOrigin(StrEnum):
    """Where a reference label came from. Required, never defaulted.

    The distinction that matters is whether a HUMAN judged the pair. An
    AI-assisted label is a usable provisional reference -- blind to the model's
    predictions, written before any call, far cheaper to obtain -- and it is not
    ground truth. An evaluation scored against one has measured agreement
    between two assistants, which is worth knowing and is a different claim.
    """

    #: A person with domain knowledge judged the pair.
    HUMAN_EXPERT = "HUMAN_EXPERT"

    #: A person without domain knowledge judged the pair. Enough for a relation
    #: that does not require expertise, and not for one that does.
    HUMAN_NON_EXPERT = "HUMAN_NON_EXPERT"

    #: Produced with AI assistance and not confirmed by a person. Mission 1.24's
    #: reference set is this, and the repository must not describe it otherwise.
    AI_ASSISTED_PROVISIONAL = "AI_ASSISTED_PROVISIONAL"

    @property
    def establishes_human_ground_truth(self) -> bool:
        return self in (ReferenceOrigin.HUMAN_EXPERT, ReferenceOrigin.HUMAN_NON_EXPERT)


class ReferenceDecision(StrEnum):
    """What a reviewer may answer.

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
            ReferenceDecision.SAME: EquivalenceDecision.SAME_PROBLEM,
            ReferenceDecision.DIFFERENT: EquivalenceDecision.DIFFERENT_PROBLEM,
            ReferenceDecision.UNCERTAIN: EquivalenceDecision.ABSTAIN,
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
class ReferenceLabel:
    """One reference judgement, with the provenance §10 requires.

    No Stack Overflow author identity appears, because none was ever acquired.
    `reviewer` names whoever or whatever is accountable, which is a different
    thing and is required: an unattributed reference label is one nobody can
    question later. `origin` says what KIND of reviewer that was, and is the
    field that stops a provisional label being read as ground truth.
    """

    pair_id: str
    a_question_id: str
    b_question_id: str
    reviewer: str
    origin: ReferenceOrigin
    decision: ReferenceDecision
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
    labels: tuple[ReferenceLabel, ...] = ()

    def for_split(self, split: Split) -> tuple[ReferenceLabel, ...]:
        return tuple(label for label in self.labels if label.split is split)

    def distribution(self) -> dict[str, int]:
        return dict(Counter(label.decision.value for label in self.labels))

    @property
    def origins(self) -> frozenset[ReferenceOrigin]:
        return frozenset(label.origin for label in self.labels)

    @property
    def human_ground_truth_established(self) -> bool:
        """True only if EVERY label came from a human.

        All, not any. A set mixing human and AI-assisted labels is not human
        ground truth with an asterisk; it is a mixed set, and a reader told
        `True` would reasonably assume otherwise.
        """
        return bool(self.labels) and all(
            origin.establishes_human_ground_truth for origin in self.origins
        )

    @property
    def positives(self) -> tuple[ReferenceLabel, ...]:
        return tuple(label for label in self.labels if label.decision is ReferenceDecision.SAME)


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

    #: How many positives the model must actually GET RIGHT in the scored split.
    #: Zero on the exact-equivalence criteria, which measured false positives
    #: only; at least one on any criterion that must be unpassable by a
    #: classifier answering DIFFERENT or ABSTAIN to everything (Mission 1.25 §9).
    min_true_same: int = 0

    #: Which relation this criterion scores. A criterion applied to the wrong
    #: relation would compare a family decision against an equivalence label and
    #: report agreement it never measured.
    relation: EquivalenceRelation = EquivalenceRelation.EXACT_ACTIONABLE_EQUIVALENCE

    @property
    def defeats_a_constant_classifier(self) -> bool:
        """Can a classifier that never says SAME pass this criterion?

        The property Mission 1.25 §9 requires, computed from the numbers rather
        than asserted in the statement text -- a statement claiming it while the
        numbers allowed it would be worse than no claim.
        """
        return self.min_true_same >= 1

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "relation": self.relation.value,
            "max_false_same": self.max_false_same,
            "min_labelled_holdout": self.min_labelled_holdout,
            "min_positive_labels": self.min_positive_labels,
            "min_true_same": self.min_true_same,
            "defeats_a_constant_classifier": self.defeats_a_constant_classifier,
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

FAMILY_V1_ACCEPTANCE = AcceptanceCriterion(
    name="family-v1-positive-coverage-and-false-positive-avoidance",
    max_false_same=0,
    min_labelled_holdout=8,
    min_positive_labels=2,
    min_true_same=1,
    relation=EquivalenceRelation.SAME_PROBLEM_FAMILY,
    statement=(
        "Frozen before any family prediction existed. The classifier passes only if ALL "
        "of the following hold on the scored split: at least 8 labelled pairs; at least 2 "
        "pairs the reference calls SAME_FAMILY, IN THAT SPLIT rather than anywhere in the "
        "reference set; ZERO false SAME_PROBLEM_FAMILY, meaning a pair the reference "
        "called DIFFERENT or UNCERTAIN that the model called SAME; and at least ONE true "
        "SAME_PROBLEM_FAMILY, meaning a pair the reference called SAME that the model also "
        "called SAME.\n\n"
        "THE LAST CLAUSE IS THE ONE MISSION 1.24 LACKED. Without it a classifier that "
        "answers DIFFERENT to everything, or ABSTAIN to everything, records zero false "
        "positives and passes -- which is exactly what happened, and why that evaluation "
        "established nothing. Requiring a demonstrated positive makes both constant "
        "classifiers fail by construction.\n\n"
        "Abstention is still never counted as an error, because the alternative to an "
        "abstention is a guess. But abstaining on EVERY positive now fails the true-SAME "
        "clause, which is the honest way to price caution: free when it is caution, and "
        "not free when it is refusal to ever commit.\n\n"
        "No accuracy, precision or recall figure is a pass condition. A proportion over a "
        "few dozen pairs has an interval wider than any difference it could show, and "
        "quoting one would make a small experiment look calibrated."
    ),
)

# Which criterion a run was scored under is part of its record. V1 is kept
# because Mission 1.24 was scored under it and rewriting it would leave that
# report describing a rule that no longer exists.
ACCEPTANCE_CRITERIA = {c.name: c for c in (V1_ACCEPTANCE, V2_ACCEPTANCE, FAMILY_V1_ACCEPTANCE)}


@dataclass(frozen=True)
class EvaluationResult:
    """The measured outcome, and whether it meets the predeclared criterion."""

    criterion: AcceptanceCriterion
    split: Split
    labelled: int
    positives: int
    matrix: dict[str, int] = field(default_factory=dict)
    false_same: tuple[str, ...] = ()
    true_same: tuple[str, ...] = ()
    false_different: tuple[str, ...] = ()
    abstentions: int = 0
    agreements: int = 0
    outcome: str = ""
    notes: tuple[str, ...] = ()

    # Recorded on the RESULT, not merely on the labels, because the result is
    # what gets quoted. An outcome read without its reference origin is an
    # outcome read as ground truth.
    reference_origins: tuple[str, ...] = ()
    human_ground_truth_established: bool = False

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
            "true_same": list(self.true_same),
            "false_different": list(self.false_different),
            "abstentions": self.abstentions,
            "agreements": self.agreements,
            "outcome": self.outcome,
            "notes": list(self.notes),
            "reference_origins": list(self.reference_origins),
            "human_ground_truth_established": self.human_ground_truth_established,
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
    positive, negative, abstain = criterion.relation.decision_values()
    scored = [label for label in labels.for_split(split) if label.pair_id in predictions]
    matrix: Counter[str] = Counter()
    false_same: list[str] = []
    false_different: list[str] = []
    abstentions = 0
    agreements = 0

    true_same: list[str] = []
    for label in scored:
        predicted = str(predictions[label.pair_id])
        matrix[f"{label.decision.value}->{predicted}"] += 1
        if predicted == abstain:
            abstentions += 1
        if predicted == positive and label.decision is not ReferenceDecision.SAME:
            false_same.append(label.pair_id)
        if predicted == positive and label.decision is ReferenceDecision.SAME:
            true_same.append(label.pair_id)
        if predicted == negative and label.decision is ReferenceDecision.SAME:
            false_different.append(label.pair_id)
        if (
            predicted
            == {
                ReferenceDecision.SAME: positive,
                ReferenceDecision.DIFFERENT: negative,
                ReferenceDecision.UNCERTAIN: abstain,
            }[label.decision]
        ):
            agreements += 1

    # V1 counts positives across the whole reference set; V2 counts them in the
    # split being scored. The criterion carries which, so a historical result
    # stays reproducible under the rule it was actually scored against.
    if criterion.name.startswith("v1-"):
        positives = len(labels.positives)
    else:
        positives = sum(
            1 for label in labels.for_split(split) if label.decision is ReferenceDecision.SAME
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
    elif len(true_same) < criterion.min_true_same:
        outcome = "MODEL_EVALUATION_FAILED"
        notes.append(
            f"{len(true_same)} correctly identified positive(s); the criterion requires at "
            f"least {criterion.min_true_same}. A classifier that never says "
            f"{positive} cannot pass, which is the point of this clause"
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

    if not labels.human_ground_truth_established:
        notes.append(
            "HUMAN GROUND TRUTH IS NOT ESTABLISHED for this reference set ("
            + ", ".join(sorted(o.value for o in labels.origins))
            + "). The outcome above is agreement against that reference, never against truth"
        )

    return EvaluationResult(
        criterion=criterion,
        reference_origins=tuple(sorted(o.value for o in labels.origins)),
        human_ground_truth_established=labels.human_ground_truth_established,
        split=split,
        labelled=len(scored),
        positives=positives,
        matrix=dict(matrix),
        false_same=tuple(false_same),
        true_same=tuple(true_same),
        false_different=tuple(false_different),
        abstentions=abstentions,
        agreements=agreements,
        outcome=outcome,
        notes=tuple(notes),
    )
