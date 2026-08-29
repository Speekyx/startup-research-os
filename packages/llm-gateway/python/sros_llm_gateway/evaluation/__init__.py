"""Evaluation framework for LLM-backed components.

Mission 0.4 §24-§27. `llm-reasoning-rules.md` §10: *"LLM components require
explicit evaluation datasets. Do not assume that a fluent answer is a correct
answer."*

    dataset.py     versioned datasets, with a `synthetic` flag that travels
    metrics.py     per-task metrics, with their direction stated explicitly
    runner.py      run a model over a dataset; pins provider and model
    comparison.py  A vs B, where cost can never offset quality
    store.py       one JSON file per run, append-only in spirit

**The datasets shipped here are synthetic fixtures.** They prove the machinery
runs; they measure nothing about model quality. The flag is carried all the way
into the comparison report so a reader cannot mistake one for the other.

**Nothing here deploys anything.** §27 forbids automated rollout: the comparison
returns a verdict, and a human reads it.
"""

from .comparison import DEFAULT_TOLERANCE, ComparisonReport, MetricDelta, Verdict, compare_runs
from .dataset import (
    DATASET_DIR,
    DatasetError,
    EvaluationDataset,
    EvaluationItem,
    TaskType,
    builtin_datasets,
    load_dataset,
)
from .metrics import (
    HIGHER_IS_BETTER,
    METRICS_FOR_TASK,
    PRIMARY_METRIC,
    QUALITY_METRICS,
    MetricSet,
    accuracy,
    brier_score,
    exact_match,
    macro_f1,
    precision_recall_f1,
    schema_validity,
)
from .runner import (
    EvaluatedModel,
    EvaluationRun,
    ItemOutcome,
    Prediction,
    RunConfig,
    compute_metrics,
    run_evaluation,
)
from .store import EvaluationStore, StoreError

__all__ = [
    # dataset
    "TaskType",
    "EvaluationItem",
    "EvaluationDataset",
    "DatasetError",
    "load_dataset",
    "builtin_datasets",
    "DATASET_DIR",
    # metrics
    "MetricSet",
    "METRICS_FOR_TASK",
    "PRIMARY_METRIC",
    "QUALITY_METRICS",
    "HIGHER_IS_BETTER",
    "accuracy",
    "exact_match",
    "macro_f1",
    "precision_recall_f1",
    "brier_score",
    "schema_validity",
    # runner
    "Prediction",
    "ItemOutcome",
    "RunConfig",
    "EvaluationRun",
    "EvaluatedModel",
    "run_evaluation",
    "compute_metrics",
    # comparison
    "compare_runs",
    "ComparisonReport",
    "MetricDelta",
    "Verdict",
    "DEFAULT_TOLERANCE",
    # store
    "EvaluationStore",
    "StoreError",
]
