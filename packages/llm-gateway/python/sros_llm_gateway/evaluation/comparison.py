"""Regression comparison between two evaluation runs.

Mission 0.4 §27: *"Future upgrades should be rejected if quality regresses
beyond a configurable tolerance even when cost improves. Do not automate
production rollout yet."*

That sentence contains the whole design. Three consequences follow from it:

**Cost cannot offset quality.** `metrics.QUALITY_METRICS` excludes cost and
latency, and only quality metrics can produce a regression verdict. A candidate
that is half the price and worse is rejected, and the report says so with the
cost delta printed next to the rejection rather than folded into it. Any
weighting that let one buy the other would eventually be tuned until every
upgrade passed.

**A comparison across different datasets is refused, not adjusted.** Two runs
over different data measure different things; producing a delta anyway is the
most convincing way to be wrong.

**Nothing is rolled out.** This module returns a verdict. It does not promote a
model, edit configuration or touch routing. A benchmark that deploys is a
benchmark that will deploy something nobody read.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .metrics import HIGHER_IS_BETTER, QUALITY_METRICS, MetricName
from .runner import EvaluationRun

__all__ = ["Verdict", "MetricDelta", "ComparisonReport", "compare_runs", "DEFAULT_TOLERANCE"]

# A metric may drop by this much before it counts as a regression. Deliberately
# small and deliberately configurable: the right value depends on the sample
# size, and a tolerance chosen once for every task would be wrong for most.
DEFAULT_TOLERANCE = 0.01


class Verdict(StrEnum):
    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    REGRESSED = "REGRESSED"
    INCOMPARABLE = "INCOMPARABLE"


@dataclass(frozen=True)
class MetricDelta:
    metric: MetricName
    baseline: float
    candidate: float
    higher_is_better: bool
    tolerance: float

    @property
    def raw_delta(self) -> float:
        return self.candidate - self.baseline

    @property
    def improvement(self) -> float:
        """Signed improvement, normalized so positive always means better.

        Without this normalization the Brier score — a loss — would be read as a
        regression every time calibration improved.
        """
        return self.raw_delta if self.higher_is_better else -self.raw_delta

    @property
    def regressed(self) -> bool:
        return self.improvement < -self.tolerance

    def to_json(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "baseline": round(self.baseline, 6),
            "candidate": round(self.candidate, 6),
            "improvement": round(self.improvement, 6),
            "regressed": self.regressed,
        }


@dataclass(frozen=True)
class ComparisonReport:
    verdict: Verdict
    reasons: tuple[str, ...]
    quality: tuple[MetricDelta, ...] = ()
    observational: tuple[MetricDelta, ...] = ()
    baseline_run_id: str = ""
    candidate_run_id: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def accepted(self) -> bool:
        """Whether the candidate may be considered for promotion BY A HUMAN.

        Not "may be deployed". §27 forbids automated rollout, and this property
        is the input to a decision, never the decision.
        """
        return self.verdict in (Verdict.IMPROVED, Verdict.UNCHANGED)

    def to_json(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "baseline_run_id": self.baseline_run_id,
            "candidate_run_id": self.candidate_run_id,
            "quality": [d.to_json() for d in self.quality],
            "observational": [d.to_json() for d in self.observational],
            "notes": list(self.notes),
        }


def compare_runs(
    baseline: EvaluationRun,
    candidate: EvaluationRun,
    tolerance: float = DEFAULT_TOLERANCE,
) -> ComparisonReport:
    """Compare two runs and return a verdict with its reasoning."""
    if tolerance < 0:
        raise ValueError("tolerance must not be negative")

    incomparable = _incomparability(baseline, candidate)
    if incomparable:
        return ComparisonReport(
            verdict=Verdict.INCOMPARABLE,
            reasons=incomparable,
            baseline_run_id=baseline.run_id,
            candidate_run_id=candidate.run_id,
        )

    quality: list[MetricDelta] = []
    observational: list[MetricDelta] = []
    for metric, candidate_value in candidate.metrics.values.items():
        if metric not in baseline.metrics.values:
            continue
        delta = MetricDelta(
            metric=metric,
            baseline=baseline.metrics.values[metric],
            candidate=candidate_value,
            higher_is_better=HIGHER_IS_BETTER.get(metric, True),
            tolerance=tolerance,
        )
        (quality if metric in QUALITY_METRICS else observational).append(delta)

    quality.sort(key=lambda d: d.metric)
    observational.sort(key=lambda d: d.metric)

    regressions = [d for d in quality if d.regressed]
    notes: list[str] = []

    cheaper = next(
        (d for d in observational if d.metric == "cost_units_total" and d.improvement > 0), None
    )
    if cheaper is not None and regressions:
        # Stated explicitly rather than left for a reader to notice, because
        # this is the exact trade §27 exists to refuse.
        notes.append(
            f"the candidate is cheaper by {abs(cheaper.raw_delta):.6g} cost units and is "
            "still rejected: cost does not offset quality"
        )

    if baseline.synthetic_dataset or candidate.synthetic_dataset:
        notes.append(
            "at least one run used a SYNTHETIC dataset. These numbers demonstrate the "
            "evaluation machinery; they do not measure model quality on real data."
        )

    if regressions:
        return ComparisonReport(
            verdict=Verdict.REGRESSED,
            reasons=tuple(
                f"{d.metric} regressed by {abs(d.improvement):.6g} (tolerance {tolerance:.6g})"
                for d in regressions
            ),
            quality=tuple(quality),
            observational=tuple(observational),
            baseline_run_id=baseline.run_id,
            candidate_run_id=candidate.run_id,
            notes=tuple(notes),
        )

    improvements = [d for d in quality if d.improvement > tolerance]
    verdict = Verdict.IMPROVED if improvements else Verdict.UNCHANGED
    reasons = tuple(f"{d.metric} improved by {d.improvement:.6g}" for d in improvements) or (
        "no quality metric moved beyond the tolerance",
    )

    return ComparisonReport(
        verdict=verdict,
        reasons=reasons,
        quality=tuple(quality),
        observational=tuple(observational),
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        notes=tuple(notes),
    )


def _incomparability(baseline: EvaluationRun, candidate: EvaluationRun) -> tuple[str, ...]:
    """Reasons the two runs cannot be compared at all.

    Refusing beats adjusting. Two runs over different datasets measure different
    things, and a delta computed anyway is wrong in a way that looks precise.
    """
    reasons: list[str] = []
    if baseline.dataset_id != candidate.dataset_id:
        reasons.append(f"different datasets: {baseline.dataset_id} vs {candidate.dataset_id}")
    if baseline.dataset_version != candidate.dataset_version:
        reasons.append(
            f"different dataset versions: {baseline.dataset_version} vs "
            f"{candidate.dataset_version}. A dataset change alters what the metric means."
        )
    if baseline.task is not candidate.task:
        reasons.append(f"different tasks: {baseline.task.value} vs {candidate.task.value}")
    if not baseline.metrics.values or not candidate.metrics.values:
        reasons.append("one of the runs produced no metrics")
    return tuple(reasons)
