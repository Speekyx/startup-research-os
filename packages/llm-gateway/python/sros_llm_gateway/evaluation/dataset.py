"""Versioned evaluation datasets.

Mission 0.4 §25. `llm-reasoning-rules.md` §10: *"LLM components require explicit
evaluation datasets. Do not assume that a fluent answer is a correct answer."*

**Every dataset is versioned and every dataset declares whether it is
synthetic.** The `synthetic` flag is not a label for tidiness: a metric computed
over invented examples measures whether the machinery works, and a metric
computed over real labelled data measures whether the model works. Reporting the
first as if it were the second is the same error as reporting an ESTIMATED
completeness as a MEASURED one.

The datasets shipped here are **small synthetic fixtures**, sized to prove the
runner, the metrics and the comparison work. They are deliberately not
production-quality evaluation sets, and building those is Data Engineering work
that needs labelled examples this system has not collected.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "TaskType",
    "EvaluationItem",
    "EvaluationDataset",
    "DatasetError",
    "load_dataset",
    "builtin_datasets",
    "DATASET_DIR",
]

DATASET_DIR = pathlib.Path(__file__).parent / "datasets"


class DatasetError(ValueError):
    """A dataset file is malformed or contradicts its own declaration."""


class TaskType(StrEnum):
    """What an evaluated component is being asked to do.

    The task drives which metrics are meaningful (§26). Accuracy over a
    structured-extraction task, for instance, says nothing useful: what matters
    there is whether the output validates and whether the extracted fields
    match.
    """

    CLAIM_CLASSIFICATION = "CLAIM_CLASSIFICATION"
    PAIN_DESIRE_EXTRACTION = "PAIN_DESIRE_EXTRACTION"
    OPPORTUNITY_CLASSIFICATION = "OPPORTUNITY_CLASSIFICATION"
    STRUCTURED_EXTRACTION = "STRUCTURED_EXTRACTION"
    CONTRADICTION_DETECTION = "CONTRADICTION_DETECTION"
    RESEARCH_SYNTHESIS = "RESEARCH_SYNTHESIS"


@dataclass(frozen=True)
class EvaluationItem:
    """One labelled example.

    `expected` is deliberately untyped: a classification expects a label, an
    extraction expects an object, and a synthesis task may expect a set of
    required assertions. Forcing one shape would push every task toward
    classification, which is the failure §26 warns about.
    """

    item_id: str
    input: dict[str, Any]
    expected: Any = None
    # Free-form tags for slicing results: locale, source family, difficulty.
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.item_id:
            raise DatasetError("every evaluation item needs a stable id")
        if not isinstance(self.input, dict):
            raise DatasetError(f"item {self.item_id}: input must be an object")


@dataclass(frozen=True)
class EvaluationDataset:
    dataset_id: str
    version: str
    task: TaskType
    description: str
    items: tuple[EvaluationItem, ...]
    synthetic: bool
    # For structured tasks: the schema an output must validate against.
    output_schema: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.dataset_id or not self.version:
            raise DatasetError("a dataset requires an id and a version")
        if not self.items:
            raise DatasetError(
                f"dataset {self.dataset_id}@{self.version} has no items. An empty dataset "
                "produces metrics that look like a perfect score."
            )
        seen: set[str] = set()
        for item in self.items:
            if item.item_id in seen:
                raise DatasetError(f"duplicate item id {item.item_id!r}")
            seen.add(item.item_id)

    @property
    def key(self) -> str:
        return f"{self.dataset_id}@{self.version}"

    def labels(self) -> tuple[str, ...]:
        """The distinct expected labels, for a classification task."""
        return tuple(
            sorted({str(item.expected) for item in self.items if item.expected is not None})
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "task": self.task.value,
            "description": self.description,
            "synthetic": self.synthetic,
            "output_schema": self.output_schema,
            "items": [
                {
                    "item_id": item.item_id,
                    "input": item.input,
                    "expected": item.expected,
                    "tags": list(item.tags),
                }
                for item in self.items
            ],
        }

    @classmethod
    def from_json(cls, payload: object) -> EvaluationDataset:
        if not isinstance(payload, dict):
            raise DatasetError("a dataset file must contain an object")

        missing = {"dataset_id", "version", "task", "items", "synthetic"} - set(payload)
        if missing:
            raise DatasetError(f"dataset is missing required fields: {sorted(missing)}")

        try:
            task = TaskType(payload["task"])
        except ValueError as exc:
            raise DatasetError(
                f"unknown task {payload['task']!r}. Tasks are a closed set: adding one "
                "changes which metrics are meaningful (§26)."
            ) from exc

        raw_items = payload["items"]
        if not isinstance(raw_items, list):
            raise DatasetError("items must be a list")

        items = tuple(
            EvaluationItem(
                item_id=str(entry["item_id"]),
                input=entry.get("input") or {},
                expected=entry.get("expected"),
                tags=tuple(entry.get("tags") or ()),
            )
            for entry in raw_items
            if isinstance(entry, dict)
        )
        return cls(
            dataset_id=str(payload["dataset_id"]),
            version=str(payload["version"]),
            task=task,
            description=str(payload.get("description") or ""),
            items=items,
            synthetic=bool(payload["synthetic"]),
            output_schema=payload.get("output_schema") or {},
        )


def load_dataset(path: str | pathlib.Path) -> EvaluationDataset:
    file = pathlib.Path(path)
    if not file.exists():
        raise DatasetError(f"no dataset at {file}")
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise DatasetError(f"{file} is not valid JSON: {exc}") from exc
    return EvaluationDataset.from_json(payload)


def builtin_datasets() -> tuple[EvaluationDataset, ...]:
    """Every dataset shipped with the package, sorted by key."""
    if not DATASET_DIR.exists():
        return ()
    return tuple(
        sorted(
            (load_dataset(path) for path in DATASET_DIR.glob("*.json")),
            key=lambda dataset: dataset.key,
        )
    )
