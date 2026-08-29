"""Running an evaluation.

Mission 0.4 §24. An evaluation run records everything §24 lists: dataset, task,
expected output, metric, model and configuration, prompt version, timestamp,
cost, latency and result.

**A run pins its provider and model, and disables fallback.** ADR-006: *"Never
fall back for evaluation runs. Benchmarks pin a provider and model explicitly,
or they measure nothing."* A silent fallback mid-benchmark produces a score
attributed to the wrong model, and nothing in the numbers reveals it.

**The model under evaluation is a callable, not a gateway.** `EvaluatedModel` is
`(item, dataset) -> Prediction`, so a fake model, a recorded fixture and a real
gateway call are all evaluable through the same path. That is what lets §38 be
proved without a provider key.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .dataset import EvaluationDataset, EvaluationItem, TaskType
from .metrics import (
    METRICS_FOR_TASK,
    MetricSet,
    accuracy,
    brier_score,
    exact_match,
    macro_f1,
    precision_recall_f1,
    schema_validity,
)

__all__ = [
    "Prediction",
    "ItemOutcome",
    "RunConfig",
    "EvaluationRun",
    "EvaluatedModel",
    "run_evaluation",
    "compute_metrics",
]


@dataclass(frozen=True)
class Prediction:
    """What a model returned for one item.

    `confidence` is on the unit interval like every other confidence in the
    system (`scoring-framework-v1.1.md` §4.1), and is optional: a model that
    does not express one is not scored for calibration rather than being
    assigned a default, which would fabricate the very quantity being measured.
    """

    value: Any
    confidence: float | None = None
    schema_valid: bool = True
    cost_units: float = 0.0
    error: str | None = None

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be on [0,1], got {self.confidence}")


EvaluatedModel = Callable[[EvaluationItem, EvaluationDataset], Prediction]


@dataclass(frozen=True)
class ItemOutcome:
    item_id: str
    expected: Any
    predicted: Any
    correct: bool
    confidence: float | None
    schema_valid: bool
    latency_ms: float
    cost_units: float
    error: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "expected": self.expected,
            "predicted": self.predicted,
            "correct": self.correct,
            "confidence": self.confidence,
            "schema_valid": self.schema_valid,
            "latency_ms": round(self.latency_ms, 3),
            "cost_units": self.cost_units,
            "error": self.error,
        }


@dataclass(frozen=True)
class RunConfig:
    """Everything needed to reproduce the run.

    Provider and model are explicit strings rather than a tier: a tier resolves
    through configuration that may since have changed, and a benchmark that
    cannot name what it measured measured nothing.
    """

    provider: str
    model: str
    prompt_id: str = ""
    prompt_version: str = ""
    tier: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    # ADR-006: a fallback changes the model, therefore the result. A run with
    # fallback enabled cannot attribute its score.
    fallback_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.provider or not self.model:
            raise ValueError(
                "an evaluation run must pin a provider and a model explicitly (ADR-006). "
                "A run that cannot name what produced its numbers cannot be compared "
                "with the run before it."
            )
        if self.fallback_enabled:
            raise ValueError(
                "fallback must be disabled for evaluation runs: a silent fallback "
                "attributes a score to the wrong model (ADR-006)."
            )

    def to_json(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "tier": self.tier,
            "parameters": self.parameters,
            "fallback_enabled": self.fallback_enabled,
        }


@dataclass(frozen=True)
class EvaluationRun:
    run_id: str
    dataset_id: str
    dataset_version: str
    task: TaskType
    synthetic_dataset: bool
    config: RunConfig
    started_at: str
    outcomes: tuple[ItemOutcome, ...]
    metrics: MetricSet

    @property
    def total_cost_units(self) -> float:
        return sum(outcome.cost_units for outcome in self.outcomes)

    @property
    def error_count(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.error)

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "task": self.task.value,
            # Carried into the result so a reader cannot mistake a machinery
            # check for a measurement of model quality.
            "synthetic_dataset": self.synthetic_dataset,
            "config": self.config.to_json(),
            "started_at": self.started_at,
            "metrics": self.metrics.to_json(),
            "outcomes": [outcome.to_json() for outcome in self.outcomes],
        }


def run_evaluation(
    dataset: EvaluationDataset,
    model: EvaluatedModel,
    config: RunConfig,
    *,
    run_id: str | None = None,
    now: datetime | None = None,
) -> EvaluationRun:
    """Run every item and compute the task's metrics.

    A model that raises does not abort the run: the item is recorded with its
    error and counted as incorrect. A benchmark that stops on the first failure
    reports nothing about the other ninety-nine items, and "it crashed on item
    three" is itself a result worth measuring.
    """
    outcomes: list[ItemOutcome] = []

    for item in dataset.items:
        started = time.monotonic()
        try:
            prediction = model(item, dataset)
        except Exception as exc:  # a failing model is a measurable outcome
            prediction = Prediction(
                value=None, schema_valid=False, error=f"{type(exc).__name__}: {exc}"
            )
        latency_ms = (time.monotonic() - started) * 1000

        outcomes.append(
            ItemOutcome(
                item_id=item.item_id,
                expected=item.expected,
                predicted=prediction.value,
                correct=_is_correct(item.expected, prediction.value),
                confidence=prediction.confidence,
                schema_valid=prediction.schema_valid,
                latency_ms=latency_ms,
                cost_units=prediction.cost_units,
                error=prediction.error,
            )
        )

    return EvaluationRun(
        run_id=run_id or f"run-{uuid.uuid4().hex[:12]}",
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.version,
        task=dataset.task,
        synthetic_dataset=dataset.synthetic,
        config=config,
        started_at=(now or datetime.now(UTC)).isoformat(),
        outcomes=tuple(outcomes),
        metrics=compute_metrics(dataset.task, outcomes),
    )


def compute_metrics(task: TaskType, outcomes: Sequence[ItemOutcome]) -> MetricSet:
    """Compute only the metrics that mean something for this task (§26)."""
    expected = [o.expected for o in outcomes]
    predicted = [o.predicted for o in outcomes]
    wanted = METRICS_FOR_TASK.get(task, ("accuracy",))
    values: dict[str, float] = {}

    if "accuracy" in wanted:
        values["accuracy"] = accuracy(expected, predicted)
    if "exact_match" in wanted:
        values["exact_match"] = exact_match(expected, predicted)
    if "macro_f1" in wanted:
        values["macro_f1"] = macro_f1(expected, predicted)
    if {"precision", "recall", "f1"} & set(wanted):
        precision, recall, f1 = precision_recall_f1(expected, predicted, positive=True)
        if "precision" in wanted:
            values["precision"] = precision
        if "recall" in wanted:
            values["recall"] = recall
        if "f1" in wanted:
            values["f1"] = f1
    if "schema_validity" in wanted:
        values["schema_validity"] = schema_validity([o.schema_valid for o in outcomes])
    if "brier" in wanted:
        scored = [(o.confidence, o.correct) for o in outcomes if o.confidence is not None]
        # Only computed where confidence was actually expressed. Defaulting a
        # missing confidence to 0.5 would manufacture calibration data.
        if scored:
            values["brier"] = brier_score([c for c, _ in scored], [hit for _, hit in scored])

    # Always recorded, never quality (see metrics.QUALITY_METRICS).
    latencies = sorted(o.latency_ms for o in outcomes)
    if latencies:
        values["latency_ms_mean"] = sum(latencies) / len(latencies)
        values["latency_ms_p95"] = latencies[min(len(latencies) - 1, int(0.95 * len(latencies)))]
    values["cost_units_total"] = sum(o.cost_units for o in outcomes)
    values["error_rate"] = sum(1 for o in outcomes if o.error) / len(outcomes) if outcomes else 0.0

    return MetricSet(task=task, values=values, sample_size=len(outcomes))


def _is_correct(expected: Any, predicted: Any) -> bool:
    if isinstance(expected, dict) or isinstance(predicted, dict):
        return bool(_canonical(expected) == _canonical(predicted))
    return bool(expected == predicted)


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((k, _canonical(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_canonical(v) for v in value)
    return value
