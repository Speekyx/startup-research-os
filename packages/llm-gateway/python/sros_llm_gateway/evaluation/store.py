"""Storing evaluation results.

Mission 0.4 §24 requires a run's result to be stored, and §38 requires two runs
to be loadable and compared.

**Files, not a table.** Evaluation results are not tenant data and not part of
the research record: they describe the system, not a workspace. Putting them in
PostgreSQL would give them a `workspace_id` they have no meaning for, and would
tie a developer-facing benchmark to a running database.

Results are written as one JSON file per run, named by run id. Append-only in
spirit: a result is what a configuration scored on a date, and rewriting one
destroys the only record that the comparison it fed was ever valid.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

from .comparison import ComparisonReport
from .dataset import TaskType
from .metrics import MetricSet
from .runner import EvaluationRun, ItemOutcome, RunConfig

__all__ = ["EvaluationStore", "StoreError"]


class StoreError(RuntimeError):
    """A result could not be written or read back."""


class EvaluationStore:
    """A directory of evaluation runs."""

    def __init__(self, directory: str | pathlib.Path) -> None:
        self._dir = pathlib.Path(directory)

    @property
    def directory(self) -> pathlib.Path:
        return self._dir

    def save(self, run: EvaluationRun) -> pathlib.Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{run.run_id}.json"
        if path.exists():
            raise StoreError(
                f"{path} already exists. An evaluation result is a record of what a "
                "configuration scored; overwriting one destroys the evidence that any "
                "comparison built on it was valid."
            )
        path.write_text(
            json.dumps(run.to_json(), indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        return path

    def load(self, run_id: str) -> EvaluationRun:
        path = self._dir / f"{run_id}.json"
        if not path.exists():
            raise StoreError(f"no evaluation run {run_id!r} in {self._dir}")
        return _run_from_json(json.loads(path.read_text(encoding="utf-8")))

    def run_ids(self) -> tuple[str, ...]:
        if not self._dir.exists():
            return ()
        return tuple(sorted(path.stem for path in self._dir.glob("*.json")))

    def save_comparison(self, name: str, report: ComparisonReport) -> pathlib.Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"comparison-{name}.json"
        path.write_text(
            json.dumps(report.to_json(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return path


def _run_from_json(payload: Any) -> EvaluationRun:
    if not isinstance(payload, dict):
        raise StoreError("an evaluation result file must contain an object")

    config_payload = payload.get("config") or {}
    config = RunConfig(
        provider=config_payload.get("provider", ""),
        model=config_payload.get("model", ""),
        prompt_id=config_payload.get("prompt_id", ""),
        prompt_version=config_payload.get("prompt_version", ""),
        tier=config_payload.get("tier", ""),
        parameters=config_payload.get("parameters") or {},
        fallback_enabled=bool(config_payload.get("fallback_enabled", False)),
    )
    task = TaskType(payload["task"])
    metrics_payload = payload.get("metrics") or {}

    return EvaluationRun(
        run_id=payload["run_id"],
        dataset_id=payload["dataset_id"],
        dataset_version=payload["dataset_version"],
        task=task,
        synthetic_dataset=bool(payload.get("synthetic_dataset", False)),
        config=config,
        started_at=payload.get("started_at", ""),
        outcomes=tuple(
            ItemOutcome(
                item_id=entry["item_id"],
                expected=entry.get("expected"),
                predicted=entry.get("predicted"),
                correct=bool(entry.get("correct")),
                confidence=entry.get("confidence"),
                schema_valid=bool(entry.get("schema_valid", True)),
                latency_ms=float(entry.get("latency_ms") or 0.0),
                cost_units=float(entry.get("cost_units") or 0.0),
                error=entry.get("error"),
            )
            for entry in payload.get("outcomes") or []
        ),
        metrics=MetricSet(
            task=task,
            values={k: float(v) for k, v in (metrics_payload.get("values") or {}).items()},
            sample_size=int(metrics_payload.get("sample_size") or 0),
        ),
    )
