"""Evaluation metrics.

Mission 0.4 §26: *"Support appropriate metrics, depending on task... Do not
force every task into accuracy."*

Two rules shape this module.

**The task chooses the metrics.** `METRICS_FOR_TASK` maps each task to what is
meaningful for it. Accuracy over a structured-extraction task measures nothing
useful — what matters there is whether the output validates and whether the
fields match. Reporting accuracy anyway would produce a number that moves for
reasons unrelated to quality.

**Cost and latency are recorded but are never quality.** They are reported
alongside the quality metrics and never averaged into them, because the whole
point of the comparison in `comparison.py` is that a cheaper, worse model must
not be able to look better.

Calibration uses the **Brier score**, where a *lower* value is better. It is the
one metric here with an inverted direction, which is exactly the kind of detail
that produces a silently wrong comparison, so `HIGHER_IS_BETTER` states the
direction of every metric explicitly rather than leaving it to convention.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .dataset import TaskType

__all__ = [
    "MetricName",
    "MetricSet",
    "HIGHER_IS_BETTER",
    "QUALITY_METRICS",
    "METRICS_FOR_TASK",
    "PRIMARY_METRIC",
    "accuracy",
    "exact_match",
    "precision_recall_f1",
    "macro_f1",
    "brier_score",
    "schema_validity",
]

MetricName = str

# Direction, declared rather than assumed. `brier` is the trap: it is a loss,
# so an improvement is a DECREASE, and a comparison that assumed otherwise would
# report every calibration improvement as a regression.
HIGHER_IS_BETTER: dict[MetricName, bool] = {
    "accuracy": True,
    "exact_match": True,
    "precision": True,
    "recall": True,
    "f1": True,
    "macro_f1": True,
    "schema_validity": True,
    "brier": False,
    # Recorded, never quality. Listed so a comparison can present them without
    # having to special-case an unknown name.
    "latency_ms_mean": False,
    "latency_ms_p95": False,
    "cost_units_total": False,
    "error_rate": False,
}

# The subset a regression check may consider. Cost and latency are deliberately
# absent: §27 requires an upgrade to be rejected when quality regresses *even
# when cost improves*, and the cheapest way to guarantee that is to keep them
# out of the quality set entirely.
QUALITY_METRICS: frozenset[MetricName] = frozenset(
    {"accuracy", "exact_match", "precision", "recall", "f1", "macro_f1", "schema_validity", "brier"}
)

METRICS_FOR_TASK: dict[TaskType, tuple[MetricName, ...]] = {
    TaskType.CLAIM_CLASSIFICATION: ("accuracy", "macro_f1", "brier"),
    TaskType.OPPORTUNITY_CLASSIFICATION: ("accuracy", "macro_f1", "brier"),
    # Extraction is a set-recovery problem: precision and recall answer "did it
    # find the right things", which accuracy over whole outputs cannot.
    TaskType.PAIN_DESIRE_EXTRACTION: ("precision", "recall", "f1"),
    TaskType.STRUCTURED_EXTRACTION: ("schema_validity", "exact_match", "f1"),
    TaskType.CONTRADICTION_DETECTION: ("precision", "recall", "f1"),
    # Synthesis has no single correct answer. Only the mechanical property is
    # scored automatically; the rest needs human review
    # (llm-reasoning-rules.md §11), and pretending otherwise would be the
    # "fluent answer is a correct answer" assumption §10 warns about.
    TaskType.RESEARCH_SYNTHESIS: ("schema_validity",),
}

PRIMARY_METRIC: dict[TaskType, MetricName] = {
    TaskType.CLAIM_CLASSIFICATION: "macro_f1",
    TaskType.OPPORTUNITY_CLASSIFICATION: "macro_f1",
    TaskType.PAIN_DESIRE_EXTRACTION: "f1",
    TaskType.STRUCTURED_EXTRACTION: "schema_validity",
    TaskType.CONTRADICTION_DETECTION: "f1",
    TaskType.RESEARCH_SYNTHESIS: "schema_validity",
}


@dataclass(frozen=True)
class MetricSet:
    """Computed metrics for one run, with their sample size.

    `sample_size` travels with the values because a metric over six synthetic
    items and a metric over six thousand real ones are not comparable, and a
    bare float gives a reader no way to tell which they are looking at.
    """

    task: TaskType
    values: dict[MetricName, float]
    sample_size: int

    def quality(self) -> dict[MetricName, float]:
        return {k: v for k, v in self.values.items() if k in QUALITY_METRICS}

    def primary(self) -> tuple[MetricName, float] | None:
        name = PRIMARY_METRIC.get(self.task)
        if name is None or name not in self.values:
            return None
        return name, self.values[name]

    def to_json(self) -> dict[str, Any]:
        return {"task": self.task.value, "sample_size": self.sample_size, "values": self.values}


# -- primitives --------------------------------------------------------------


def accuracy(expected: Sequence[Any], predicted: Sequence[Any]) -> float:
    _require_same_length(expected, predicted)
    if not expected:
        return 0.0
    hits = sum(1 for e, p in zip(expected, predicted, strict=True) if e == p)
    return hits / len(expected)


def exact_match(expected: Sequence[Any], predicted: Sequence[Any]) -> float:
    """Whole-output equality, order-insensitive for objects.

    Distinct from accuracy: accuracy compares labels, exact match compares
    complete structures, and an extraction that gets four fields right out of
    five is 0.0 here and rightly so.
    """
    _require_same_length(expected, predicted)
    if not expected:
        return 0.0
    hits = sum(
        1 for e, p in zip(expected, predicted, strict=True) if _canonical(e) == _canonical(p)
    )
    return hits / len(expected)


def precision_recall_f1(
    expected: Sequence[Any], predicted: Sequence[Any], positive: Any = True
) -> tuple[float, float, float]:
    """Binary precision, recall and F1 against a nominated positive class."""
    _require_same_length(expected, predicted)
    true_positive = sum(
        1 for e, p in zip(expected, predicted, strict=True) if p == positive and e == positive
    )
    false_positive = sum(
        1 for e, p in zip(expected, predicted, strict=True) if p == positive and e != positive
    )
    false_negative = sum(
        1 for e, p in zip(expected, predicted, strict=True) if p != positive and e == positive
    )

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive)
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative)
        else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def macro_f1(expected: Sequence[Any], predicted: Sequence[Any]) -> float:
    """F1 averaged over classes, unweighted.

    Macro rather than micro because the classes here are deliberately
    imbalanced: `HYPOTHESIS` is rarer than `OBSERVED` and matters more. A micro
    average would let a model that never predicts the rare class score well,
    which is the exact failure `evidence-confidence-framework-v1.md` §9 exists
    to prevent.
    """
    _require_same_length(expected, predicted)
    classes = sorted({str(value) for value in (*expected, *predicted)})
    if not classes:
        return 0.0
    scores = [
        precision_recall_f1([str(v) for v in expected], [str(v) for v in predicted], positive=cls)[
            2
        ]
        for cls in classes
    ]
    return sum(scores) / len(scores)


def brier_score(confidences: Sequence[float], correct: Sequence[bool]) -> float:
    """Mean squared error between stated confidence and being right.

    LOWER IS BETTER. A model that says 0.9 and is wrong half the time is
    miscalibrated even when its accuracy is acceptable, and calibration is what
    makes a confidence figure usable downstream at all
    (`scoring-framework-v1.1.md` §4.1).
    """
    _require_same_length(confidences, correct)
    if not confidences:
        return 0.0
    for value in confidences:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"confidence must be on the unit interval, got {value}")
    return sum(
        (c - (1.0 if hit else 0.0)) ** 2 for c, hit in zip(confidences, correct, strict=True)
    ) / len(confidences)


def schema_validity(valid_flags: Sequence[bool]) -> float:
    """The fraction of outputs that validated against the requested schema."""
    if not valid_flags:
        return 0.0
    return sum(1 for flag in valid_flags if flag) / len(valid_flags)


def _require_same_length(left: Sequence[Any], right: Sequence[Any]) -> None:
    if len(left) != len(right):
        raise ValueError(
            f"metric inputs must align: {len(left)} expected vs {len(right)} predicted"
        )


def _canonical(value: Any) -> Any:
    """Order-insensitive comparison for nested objects."""
    if isinstance(value, dict):
        return tuple(sorted((k, _canonical(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_canonical(v) for v in value)
    return value
