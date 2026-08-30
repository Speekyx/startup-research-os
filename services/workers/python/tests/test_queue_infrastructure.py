"""Celery infrastructure tests.

These run without Celery, a broker or a database: `queues` and `context` are
deliberately dependency-free so the rules that matter can be asserted cheaply.

ADR-004 governs the expectations here.
"""

from __future__ import annotations

import unittest

from sros_workers import (
    QUEUES,
    REQUIRED_HEADERS,
    RETRY_POLICIES,
    MissingContextError,
    Queue,
    TaskContext,
    idempotency_key,
    retry_policy_for,
    route_task,
)
from sros_workers.celery_app import build_celery_config


class QueueTopology(unittest.TestCase):
    def test_all_five_required_queues_exist(self) -> None:
        self.assertEqual(
            {q.value for q in Queue},
            {"acquisition", "nlp", "embedding", "analysis", "maintenance"},
        )

    def test_every_queue_has_config_and_retry_policy(self) -> None:
        for queue in Queue:
            self.assertIn(queue, QUEUES)
            self.assertIn(queue, RETRY_POLICIES)

    def test_long_running_queues_do_not_prefetch_batches(self) -> None:
        """Prefetching slow jobs into one worker stalls the queue."""
        for queue in (Queue.ACQUISITION, Queue.NLP, Queue.EMBEDDING, Queue.MAINTENANCE):
            self.assertEqual(QUEUES[queue].prefetch_multiplier, 1, queue.value)


class Routing(unittest.TestCase):
    def test_routes_by_longest_prefix(self) -> None:
        cases = {
            "acquire.source": Queue.ACQUISITION,
            "normalize.batch": Queue.ACQUISITION,
            "nlp.extract": Queue.NLP,
            "nlp.classify": Queue.NLP,
            # Longest prefix wins: nlp.embed must not be swallowed by "nlp.".
            "nlp.embed": Queue.EMBEDDING,
            "nlp.cluster": Queue.EMBEDDING,
            "score.opportunity": Queue.ANALYSIS,
            "market.analyze": Queue.ANALYSIS,
            "competition.map": Queue.ANALYSIS,
            "execution.plan": Queue.ANALYSIS,
            "maintenance.retention": Queue.MAINTENANCE,
        }
        for task, expected in cases.items():
            with self.subTest(task=task):
                self.assertIs(route_task(task), expected)

    def test_unrouted_task_fails_loudly(self) -> None:
        """An unrouted task would silently land on the default queue."""
        with self.assertRaises(KeyError):
            route_task("totally.unknown.task")


class RetrySemantics(unittest.TestCase):
    def test_external_source_retries_use_jitter(self) -> None:
        """Synchronized retries across workers turn a rate limit into a ban."""
        self.assertTrue(RETRY_POLICIES[Queue.ACQUISITION].jitter)
        self.assertTrue(RETRY_POLICIES[Queue.NLP].jitter)

    def test_backoff_is_exponential_and_capped(self) -> None:
        policy = retry_policy_for("acquire.source")
        self.assertEqual(policy.backoff_for(1), 5.0)
        self.assertEqual(policy.backoff_for(2), 10.0)
        self.assertEqual(policy.backoff_for(3), 20.0)
        self.assertLessEqual(policy.backoff_for(50), policy.max_backoff_seconds)

    def test_attempt_is_one_based(self) -> None:
        with self.assertRaises(ValueError):
            retry_policy_for("acquire.source").backoff_for(0)


class DeliverySemantics(unittest.TestCase):
    """At-least-once is the contract. Nothing here pretends otherwise."""

    def test_acks_late_and_reject_on_worker_lost(self) -> None:
        config = build_celery_config()
        self.assertTrue(config["task_acks_late"])
        self.assertTrue(config["task_reject_on_worker_lost"])

    def test_json_only_serialization(self) -> None:
        """Pickle off a broker is a remote-code-execution shape."""
        config = build_celery_config()
        self.assertEqual(config["task_serializer"], "json")
        self.assertEqual(config["accept_content"], ["json"])

    def test_results_expire(self) -> None:
        """Redis is not canonical; an unbounded result set is a slow leak."""
        self.assertGreater(build_celery_config()["result_expires"], 0)

    def test_routes_cover_every_declared_prefix(self) -> None:
        routes = build_celery_config()["task_routes"]
        # 13 since Mission 1.11.1 added `signal.`. It routes to ACQUISITION, not
        # to `nlp`: deterministic arithmetic over records the deployment already
        # holds is bounded and CPU-cheap, and the `nlp` queue is sized for
        # LLM-backed work it would then compete with.
        self.assertEqual(len(routes), 13)
        self.assertEqual(routes["nlp.embed*"], {"queue": "embedding"})
        self.assertEqual(routes["signal.*"], {"queue": "acquisition"})


class Correlation(unittest.TestCase):
    def test_required_headers(self) -> None:
        self.assertEqual(
            set(REQUIRED_HEADERS),
            {"workspace_id", "research_session_id", "correlation_id"},
        )

    def test_context_round_trips(self) -> None:
        headers = {
            "workspace_id": "00000000-0000-4000-8000-000000000001",
            "research_session_id": "00000000-0000-4000-8000-0000000000aa",
            "correlation_id": "abc-123",
        }
        self.assertEqual(TaskContext.from_headers(headers).to_headers(), headers)

    def test_missing_workspace_fails_closed(self) -> None:
        """A worker never resolves the workspace itself (ADR-005)."""
        with self.assertRaises(MissingContextError):
            TaskContext.from_headers({"research_session_id": "s", "correlation_id": "c"})

    def test_empty_workspace_fails_closed(self) -> None:
        with self.assertRaises(MissingContextError):
            TaskContext.from_headers(
                {"workspace_id": "", "research_session_id": "s", "correlation_id": "c"}
            )

    def test_no_default_workspace_fallback_exists(self) -> None:
        """The dev workspace is a seed convenience, never a code path."""
        import inspect

        import sros_workers.context as module

        self.assertNotIn("00000000-0000-4000-8000", inspect.getsource(module))


class Idempotency(unittest.TestCase):
    """Duplicate delivery must be harmless. The key is how the DB absorbs it."""

    def _ctx(self, workspace: str = "ws-1") -> TaskContext:
        return TaskContext(workspace_id=workspace, research_session_id="s-1", correlation_id="c-1")

    def test_same_work_yields_the_same_key(self) -> None:
        a = idempotency_key("acquire.source", self._ctx(), {"source": "x", "page": 1})
        b = idempotency_key("acquire.source", self._ctx(), {"page": 1, "source": "x"})
        self.assertEqual(a, b, "key must not depend on payload key order")

    def test_different_workspace_yields_a_different_key(self) -> None:
        a = idempotency_key("acquire.source", self._ctx("ws-1"), {"source": "x"})
        b = idempotency_key("acquire.source", self._ctx("ws-2"), {"source": "x"})
        self.assertNotEqual(a, b, "keys must not collide across tenants")

    def test_different_task_yields_a_different_key(self) -> None:
        ctx = self._ctx()
        self.assertNotEqual(
            idempotency_key("acquire.source", ctx, {"source": "x"}),
            idempotency_key("normalize.batch", ctx, {"source": "x"}),
        )


class NoBusinessLogic(unittest.TestCase):
    def test_package_contains_no_business_job_bodies(self) -> None:
        """Mission 0.2 is infrastructure only."""
        import pathlib

        package = pathlib.Path(__file__).resolve().parents[1] / "sros_workers"
        forbidden = ("def acquire_", "def score_", "def embed_", "def classify_")
        offenders = [
            f"{path.name}: {token}"
            for path in package.glob("*.py")
            for token in forbidden
            if token in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
