"""Evaluation framework tests.

Mission 0.4 §38: the framework must be able to load a versioned dataset, run a
fake model, calculate metrics, store results, compare two runs and detect a
regression. Each of those has a test below, and none of them touches a network.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from sros_llm_gateway.evaluation import (
    DATASET_DIR,
    ComparisonReport,
    DatasetError,
    EvaluationDataset,
    EvaluationItem,
    EvaluationStore,
    Prediction,
    RunConfig,
    StoreError,
    TaskType,
    Verdict,
    brier_score,
    builtin_datasets,
    compare_runs,
    exact_match,
    load_dataset,
    macro_f1,
    precision_recall_f1,
    run_evaluation,
    schema_validity,
)
from sros_llm_gateway.evaluation.metrics import METRICS_FOR_TASK, QUALITY_METRICS

FIXED_TIME = datetime(2026, 8, 29, 12, 0, 0, tzinfo=UTC)
CLAIM_DATASET = DATASET_DIR / "claim-classification-synthetic.v1.json"


def config(model: str = "model-a") -> RunConfig:
    return RunConfig(provider="fake", model=model, prompt_id="p", prompt_version="1.0.0")


def perfect_model(item: EvaluationItem, dataset: EvaluationDataset) -> Prediction:
    return Prediction(value=item.expected, confidence=0.95, cost_units=1.0)


def always_observed(item: EvaluationItem, dataset: EvaluationDataset) -> Prediction:
    """Never predicts the rare class, and is cheap.

    The model macro-F1 exists to catch: it looks acceptable on accuracy while
    being useless for HYPOTHESIS, which is the label that stops a plausible idea
    from reading as a finding.
    """
    return Prediction(value="OBSERVED", confidence=0.95, cost_units=0.1)


# =================================================================== datasets


class Datasets(unittest.TestCase):
    def test_the_builtin_dataset_loads(self) -> None:
        dataset = load_dataset(CLAIM_DATASET)
        self.assertEqual(dataset.dataset_id, "claim-classification-synthetic")
        self.assertEqual(dataset.version, "1.0.0")
        self.assertIs(dataset.task, TaskType.CLAIM_CLASSIFICATION)
        self.assertEqual(len(dataset.items), 8)

    def test_every_shipped_dataset_declares_itself_synthetic(self) -> None:
        """A metric over invented examples measures the machinery. Reporting it
        as a measurement of model quality is the same error as reporting an
        ESTIMATED completeness as MEASURED."""
        datasets = builtin_datasets()
        self.assertTrue(datasets)
        for dataset in datasets:
            with self.subTest(dataset=dataset.key):
                self.assertTrue(dataset.synthetic)

    def test_the_five_canonical_claim_types_are_representable(self) -> None:
        dataset = load_dataset(CLAIM_DATASET)
        self.assertLessEqual(
            set(dataset.labels()),
            {"OBSERVED", "INFERRED", "PREDICTED", "RECOMMENDED", "HYPOTHESIS"},
        )
        self.assertIn("HYPOTHESIS", dataset.labels())

    def test_an_empty_dataset_is_refused(self) -> None:
        """It would produce metrics that look like a perfect score."""
        with self.assertRaises(DatasetError):
            EvaluationDataset(
                dataset_id="d",
                version="1",
                task=TaskType.CLAIM_CLASSIFICATION,
                description="",
                items=(),
                synthetic=True,
            )

    def test_duplicate_item_ids_are_refused(self) -> None:
        with self.assertRaises(DatasetError):
            EvaluationDataset(
                dataset_id="d",
                version="1",
                task=TaskType.CLAIM_CLASSIFICATION,
                description="",
                items=(EvaluationItem("x", {}), EvaluationItem("x", {})),
                synthetic=True,
            )

    def test_an_unknown_task_is_refused(self) -> None:
        with self.assertRaises(DatasetError):
            EvaluationDataset.from_json(
                {
                    "dataset_id": "d",
                    "version": "1",
                    "task": "VIBES",
                    "synthetic": True,
                    "items": [{"item_id": "a"}],
                }
            )

    def test_a_dataset_round_trips_through_json(self) -> None:
        dataset = load_dataset(CLAIM_DATASET)
        self.assertEqual(EvaluationDataset.from_json(dataset.to_json()), dataset)


# ==================================================================== metrics


class Metrics(unittest.TestCase):
    def test_the_task_selects_the_metrics(self) -> None:
        """§26: accuracy over a structured-extraction task measures nothing
        useful, so it is not computed for one."""
        self.assertIn("accuracy", METRICS_FOR_TASK[TaskType.CLAIM_CLASSIFICATION])
        self.assertNotIn("accuracy", METRICS_FOR_TASK[TaskType.STRUCTURED_EXTRACTION])
        self.assertIn("schema_validity", METRICS_FOR_TASK[TaskType.STRUCTURED_EXTRACTION])

    def test_cost_and_latency_are_never_quality_metrics(self) -> None:
        """This is what makes §27's "even when cost improves" enforceable."""
        for name in ("cost_units_total", "latency_ms_mean", "latency_ms_p95"):
            self.assertNotIn(name, QUALITY_METRICS)

    def test_macro_f1_punishes_ignoring_a_rare_class(self) -> None:
        expected = ["OBSERVED"] * 6 + ["HYPOTHESIS"] * 2
        predicted = ["OBSERVED"] * 8
        self.assertAlmostEqual(
            sum(1 for e, p in zip(expected, predicted, strict=True) if e == p) / 8, 0.75
        )
        self.assertLess(macro_f1(expected, predicted), 0.5)

    def test_exact_match_is_order_insensitive_for_objects(self) -> None:
        self.assertEqual(exact_match([{"a": 1, "b": 2}], [{"b": 2, "a": 1}]), 1.0)

    def test_precision_and_recall_separate_the_two_failure_modes(self) -> None:
        precision, recall, _ = precision_recall_f1([True, True, False], [True, False, True])
        self.assertAlmostEqual(precision, 0.5)
        self.assertAlmostEqual(recall, 0.5)

    def test_a_confident_wrong_model_scores_worse_on_calibration(self) -> None:
        """Brier is a LOSS: lower is better. It is the one inverted metric here,
        and a comparison that assumed otherwise would report every calibration
        improvement as a regression."""
        confident_wrong = brier_score([0.99, 0.99], [False, False])
        humble_wrong = brier_score([0.51, 0.51], [False, False])
        self.assertGreater(confident_wrong, humble_wrong)

    def test_confidence_outside_the_unit_interval_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            brier_score([82.0], [True])

    def test_schema_validity_is_a_fraction(self) -> None:
        self.assertEqual(schema_validity([True, True, False, True]), 0.75)


# ===================================================================== runner


class Runner(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset = load_dataset(CLAIM_DATASET)

    def test_a_fake_model_can_be_evaluated_end_to_end(self) -> None:
        run = run_evaluation(self.dataset, perfect_model, config(), now=FIXED_TIME)
        self.assertEqual(run.metrics.sample_size, 8)
        self.assertEqual(run.metrics.values["accuracy"], 1.0)
        self.assertEqual(run.metrics.values["macro_f1"], 1.0)
        self.assertEqual(run.total_cost_units, 8.0)

    def test_the_synthetic_flag_travels_into_the_result(self) -> None:
        run = run_evaluation(self.dataset, perfect_model, config(), now=FIXED_TIME)
        self.assertTrue(run.synthetic_dataset)
        self.assertTrue(run.to_json()["synthetic_dataset"])

    def test_a_run_records_the_reproducibility_fields(self) -> None:
        run = run_evaluation(self.dataset, perfect_model, config(), now=FIXED_TIME)
        payload = run.to_json()
        for field in ("dataset_id", "dataset_version", "task", "started_at", "config"):
            self.assertIn(field, payload)
        self.assertEqual(payload["config"]["prompt_version"], "1.0.0")
        self.assertEqual(payload["started_at"], FIXED_TIME.isoformat())

    def test_a_run_must_pin_a_provider_and_model(self) -> None:
        with self.assertRaises(ValueError):
            RunConfig(provider="", model="m")

    def test_fallback_must_be_disabled_for_a_benchmark(self) -> None:
        """ADR-006: a silent fallback attributes a score to the wrong model."""
        with self.assertRaises(ValueError):
            RunConfig(provider="p", model="m", fallback_enabled=True)

    def test_a_failing_model_is_measured_rather_than_aborting_the_run(self) -> None:
        def explodes(item: EvaluationItem, dataset: EvaluationDataset) -> Prediction:
            raise RuntimeError("model unavailable")

        run = run_evaluation(self.dataset, explodes, config(), now=FIXED_TIME)
        self.assertEqual(run.error_count, 8)
        self.assertEqual(run.metrics.values["error_rate"], 1.0)
        self.assertEqual(run.metrics.values["accuracy"], 0.0)

    def test_calibration_is_skipped_when_no_confidence_is_expressed(self) -> None:
        """Defaulting a missing confidence to 0.5 would manufacture the very
        quantity being measured."""

        def silent(item: EvaluationItem, dataset: EvaluationDataset) -> Prediction:
            return Prediction(value=item.expected)

        run = run_evaluation(self.dataset, silent, config(), now=FIXED_TIME)
        self.assertNotIn("brier", run.metrics.values)


# ====================================================================== store


class Store(unittest.TestCase):
    def test_a_run_is_saved_and_loaded_back_identically(self) -> None:
        dataset = load_dataset(CLAIM_DATASET)
        run = run_evaluation(dataset, perfect_model, config(), run_id="r1", now=FIXED_TIME)
        with tempfile.TemporaryDirectory() as tmp:
            store = EvaluationStore(Path(tmp))
            store.save(run)
            self.assertEqual(store.run_ids(), ("r1",))
            loaded = store.load("r1")
        self.assertEqual(loaded.metrics.values, run.metrics.values)
        self.assertEqual(loaded.config.model, "model-a")
        self.assertEqual(len(loaded.outcomes), 8)

    def test_overwriting_a_stored_result_is_refused(self) -> None:
        """A result is the record of what a configuration scored; overwriting
        one destroys the evidence that a comparison built on it was valid."""
        dataset = load_dataset(CLAIM_DATASET)
        run = run_evaluation(dataset, perfect_model, config(), run_id="r1", now=FIXED_TIME)
        with tempfile.TemporaryDirectory() as tmp:
            store = EvaluationStore(Path(tmp))
            store.save(run)
            with self.assertRaises(StoreError):
                store.save(run)


# ================================================================= comparison


class RegressionComparison(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset = load_dataset(CLAIM_DATASET)
        self.baseline = run_evaluation(
            self.dataset, perfect_model, config("model-a"), run_id="base", now=FIXED_TIME
        )

    def test_an_identical_run_is_unchanged(self) -> None:
        candidate = run_evaluation(
            self.dataset, perfect_model, config("model-a2"), run_id="cand", now=FIXED_TIME
        )
        report = compare_runs(self.baseline, candidate)
        self.assertIs(report.verdict, Verdict.UNCHANGED)
        self.assertTrue(report.accepted)

    def test_a_quality_drop_beyond_the_tolerance_is_a_regression(self) -> None:
        candidate = run_evaluation(
            self.dataset, always_observed, config("model-b"), run_id="cand", now=FIXED_TIME
        )
        report = compare_runs(self.baseline, candidate)
        self.assertIs(report.verdict, Verdict.REGRESSED)
        self.assertFalse(report.accepted)
        self.assertTrue(any("macro_f1" in reason for reason in report.reasons))

    def test_a_cheaper_worse_candidate_is_still_rejected(self) -> None:
        """§27, the core requirement: cost cannot buy quality."""
        candidate = run_evaluation(
            self.dataset, always_observed, config("model-b"), run_id="cand", now=FIXED_TIME
        )
        self.assertLess(candidate.total_cost_units, self.baseline.total_cost_units)

        report = compare_runs(self.baseline, candidate)
        self.assertIs(report.verdict, Verdict.REGRESSED)
        self.assertTrue(
            any("cost does not offset quality" in note for note in report.notes),
            report.notes,
        )

    def test_the_tolerance_is_configurable(self) -> None:
        def slightly_worse(item: EvaluationItem, dataset: EvaluationDataset) -> Prediction:
            wrong = item.item_id == "hyp-2"
            return Prediction(
                value="OBSERVED" if wrong else item.expected, confidence=0.9, cost_units=1.0
            )

        candidate = run_evaluation(
            self.dataset, slightly_worse, config("model-c"), run_id="cand", now=FIXED_TIME
        )
        self.assertIs(
            compare_runs(self.baseline, candidate, tolerance=0.001).verdict, Verdict.REGRESSED
        )
        self.assertIs(
            compare_runs(self.baseline, candidate, tolerance=0.9).verdict, Verdict.UNCHANGED
        )

    def test_an_improvement_is_reported_as_such(self) -> None:
        weak = run_evaluation(
            self.dataset, always_observed, config("model-b"), run_id="weak", now=FIXED_TIME
        )
        strong = run_evaluation(
            self.dataset, perfect_model, config("model-a"), run_id="strong", now=FIXED_TIME
        )
        report = compare_runs(weak, strong)
        self.assertIs(report.verdict, Verdict.IMPROVED)
        self.assertTrue(report.accepted)

    def test_runs_over_different_datasets_are_incomparable(self) -> None:
        """Refusing beats adjusting: a delta across different data is wrong in a
        way that looks precise."""
        other = EvaluationDataset(
            dataset_id="other",
            version="1.0.0",
            task=TaskType.CLAIM_CLASSIFICATION,
            description="",
            synthetic=True,
            items=(EvaluationItem("a", {}, "OBSERVED"),),
        )
        candidate = run_evaluation(other, perfect_model, config(), run_id="c", now=FIXED_TIME)
        report = compare_runs(self.baseline, candidate)
        self.assertIs(report.verdict, Verdict.INCOMPARABLE)
        self.assertFalse(report.accepted)

    def test_a_dataset_version_change_makes_runs_incomparable(self) -> None:
        revised = EvaluationDataset(
            dataset_id=self.dataset.dataset_id,
            version="1.1.0",
            task=self.dataset.task,
            description="",
            synthetic=True,
            items=self.dataset.items,
        )
        candidate = run_evaluation(revised, perfect_model, config(), run_id="c", now=FIXED_TIME)
        self.assertIs(compare_runs(self.baseline, candidate).verdict, Verdict.INCOMPARABLE)

    def test_a_synthetic_comparison_says_so_in_its_notes(self) -> None:
        candidate = run_evaluation(
            self.dataset, perfect_model, config("model-a2"), run_id="c", now=FIXED_TIME
        )
        report = compare_runs(self.baseline, candidate)
        self.assertTrue(any("SYNTHETIC" in note for note in report.notes))

    def test_the_report_does_not_promote_anything(self) -> None:
        """§27 forbids automated rollout. The report is an input to a decision,
        never the decision."""
        report = compare_runs(self.baseline, self.baseline)
        self.assertIsInstance(report, ComparisonReport)
        self.assertFalse(hasattr(report, "promote"))
        self.assertFalse(hasattr(report, "deploy"))

    def test_a_negative_tolerance_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            compare_runs(self.baseline, self.baseline, tolerance=-0.1)


if __name__ == "__main__":
    unittest.main()
