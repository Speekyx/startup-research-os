"""The two task surfaces: routing, context and the fail-closed defaults.

Mission 1.6 §56, and the Mission 1.5 surface it also covers -- `acquisition_tasks`
had no test of its own, so a change to the header merge or the connection
refusal would have been caught by nothing.

**No broker, and no Celery.** These modules exist so that everything decidable is
decided outside a task decorator, and this suite is the proof: it exercises the
payload merge, the routing and the fail-closed refusal with a stub app. A test
that needed a worker running is a test that gets skipped, and a skipped test on
the process boundary is where a missing tenant would survive.
"""

from __future__ import annotations

import unittest
from typing import Any

from sros_workers import Queue, route_task
from sros_workers.acquisition_tasks import (
    GDELT_WEB_NGRAM_COLLECT,
    WORLD_BANK_COLLECT,
    acquisition_payload,
    register_acquisition_tasks,
    world_bank_payload,
)
from sros_workers.context import MissingContextError
from sros_workers.normalization_tasks import (
    NORMALIZE_RAW_RECORDS,
    normalization_payload,
    register_normalization_tasks,
)

WORKSPACE = "00000000-0000-4000-8000-000000000001"
SESSION = "11111111-1111-4111-8111-111111111111"
HEADERS = {
    "workspace_id": WORKSPACE,
    "research_session_id": SESSION,
    "correlation_id": "corr-1",
}


class _StubApp:
    """Just enough Celery to register a task and call it.

    A real app would need a broker URL and would make this suite depend on
    Redis being up, which is precisely the dependency the split into
    `job.py` exists to avoid.
    """

    def __init__(self) -> None:
        self.registered: dict[str, Any] = {}

    def task(self, name: str, bind: bool = False):  # noqa: FBT001, FBT002 - Celery's shape
        def decorate(fn):
            self.registered[name] = (fn, bind)
            return fn

        return decorate

    def call(self, name: str, *args: Any) -> Any:
        fn, bind = self.registered[name]
        request = type("Request", (), {"id": "task-abc"})()
        stub_self = type("Task", (), {"request": request})()
        return fn(stub_self, *args) if bind else fn(*args)


class TestRouting(unittest.TestCase):
    """Both task names route where the queue topology says they do."""

    def test_the_collector_task_routes_to_the_acquisition_queue(self) -> None:
        self.assertIs(route_task(WORLD_BANK_COLLECT), Queue.ACQUISITION)

    def test_the_normalization_task_routes_to_the_acquisition_queue(self) -> None:
        """§32: no second scheduler and no new queue.

        Normalization is bounded, cheap work over records already held. Giving
        it a pool of its own would split one for no measured reason -- and if it
        ever competes with collection for slots, that is a routing change with
        evidence behind it rather than a guess made in advance.
        """
        self.assertIs(route_task(NORMALIZE_RAW_RECORDS), Queue.ACQUISITION)

    def test_the_ngram_collector_task_routes_to_the_acquisition_queue(self) -> None:
        """Mission 1.9.3 §41. The existing queue, not a new one: a bulk file is
        bigger work than an API page and it is still acquisition, and a pool of
        its own would be a split made in advance of any measurement."""
        self.assertIs(route_task(GDELT_WEB_NGRAM_COLLECT), Queue.ACQUISITION)

    def test_every_task_name_is_distinct(self) -> None:
        names = {WORLD_BANK_COLLECT, GDELT_WEB_NGRAM_COLLECT, NORMALIZE_RAW_RECORDS}
        self.assertEqual(len(names), 3)


class TestContext(unittest.TestCase):
    """ADR-005. A worker never resolves a workspace and never defaults one."""

    def test_the_headers_win_over_the_payload(self) -> None:
        merged = normalization_payload(HEADERS, {"workspace_id": "an-imposter"})
        self.assertEqual(merged["workspace_id"], WORKSPACE)

    def test_the_collector_payload_merge_behaves_identically(self) -> None:
        merged = world_bank_payload(HEADERS, {"workspace_id": "an-imposter"})
        self.assertEqual(merged["workspace_id"], WORKSPACE)

    def test_a_payload_with_no_workspace_is_refused(self) -> None:
        for headers in (
            {"research_session_id": SESSION, "correlation_id": "c"},
            {"workspace_id": WORKSPACE, "correlation_id": "c"},
            {"workspace_id": WORKSPACE, "research_session_id": SESSION},
            {},
        ):
            with self.assertRaises(MissingContextError):
                normalization_payload(headers, {})

    def test_the_job_payload_keeps_its_own_fields(self) -> None:
        merged = normalization_payload(HEADERS, {"max_records": 10, "source_id": "world-bank"})
        self.assertEqual(merged["max_records"], 10)
        self.assertEqual(merged["source_id"], "world-bank")


class TestFailClosed(unittest.TestCase):
    """A task with no connection factory refuses rather than inventing one."""

    def test_normalization_refuses_without_a_connection_factory(self) -> None:
        app = _StubApp()
        register_normalization_tasks(app)
        with self.assertRaises(RuntimeError) as caught:
            app.call(NORMALIZE_RAW_RECORDS, HEADERS, {})
        self.assertIn("must not construct its own database access", str(caught.exception))

    def test_acquisition_refuses_without_a_connection_factory(self) -> None:
        app = _StubApp()
        register_acquisition_tasks(app)
        for name in (WORLD_BANK_COLLECT, GDELT_WEB_NGRAM_COLLECT):
            with self.assertRaises(RuntimeError):
                app.call(name, HEADERS, {})

    def test_the_ngram_task_merge_behaves_identically(self) -> None:
        merged = acquisition_payload(HEADERS, {"workspace_id": "an-imposter"})
        self.assertEqual(merged["workspace_id"], WORKSPACE)

    def test_a_smuggled_authorization_key_survives_the_merge_and_means_nothing(self) -> None:
        """§41, from the WORKER's side only.

        The merge is deliberately dumb: it keeps whatever the payload carried and
        lets the tenancy headers win. So a key called `authorization` passes
        through here untouched — and reaches a job that rebuilds the
        authorization from the registry and never looks at it.

        **The payload class itself is asserted in the acquisition suite**, not
        here. This module runs in the ZERO-DEPENDENCY suite with no workspace
        packages installed, so importing `sros_acquisition` fails in CI while
        passing on any developer machine that has it — which is how this test
        was written and how CI caught it. `service-boundaries.md` says the same
        thing for a different reason: a service does not import another
        service's package.
        """
        merged = acquisition_payload(HEADERS, {"authorization": {"allowed": True}})
        self.assertEqual(merged["authorization"], {"allowed": True})
        self.assertEqual(merged["workspace_id"], WORKSPACE)

    def test_registration_is_explicit(self) -> None:
        """A process that should not normalize simply does not register it."""
        app = _StubApp()
        register_acquisition_tasks(app, connection_factory=lambda _: None)
        self.assertNotIn(NORMALIZE_RAW_RECORDS, app.registered)


class _Result:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def to_json(self) -> dict[str, object]:
        return {"normalized": True}


class TestDelivery(unittest.TestCase):
    """§35. Two deliveries of one job share an idempotency key."""

    def test_the_task_idempotency_key_is_stable_across_deliveries(self) -> None:
        app = _StubApp()
        seen: list[dict[str, object]] = []

        def runner(payload: dict[str, object], _factory: object) -> _Result:
            seen.append(payload)
            return _Result()

        register_normalization_tasks(app, runner=runner, connection_factory=lambda _: None)
        payload = {"source_id": "world-bank"}
        first = app.call(NORMALIZE_RAW_RECORDS, HEADERS, payload)
        second = app.call(NORMALIZE_RAW_RECORDS, HEADERS, payload)

        self.assertEqual(first["task_idempotency_key"], second["task_idempotency_key"])
        # The Celery task id differs per delivery and must NOT be the
        # idempotency key: a redelivery would then look like new work.
        self.assertNotEqual(first["task_idempotency_key"], first["task_id"])

    def test_the_correlation_headers_reach_the_job(self) -> None:
        app = _StubApp()
        seen: list[dict[str, object]] = []

        def runner(payload: dict[str, object], _factory: object) -> _Result:
            seen.append(payload)
            return _Result()

        register_normalization_tasks(app, runner=runner, connection_factory=lambda _: None)
        app.call(NORMALIZE_RAW_RECORDS, HEADERS, {"source_id": "world-bank"})
        self.assertEqual(seen[0]["workspace_id"], WORKSPACE)
        self.assertEqual(seen[0]["research_session_id"], SESSION)
        self.assertEqual(seen[0]["correlation_id"], "corr-1")

    def test_the_result_carries_the_job_result_verbatim(self) -> None:
        app = _StubApp()
        register_normalization_tasks(
            app,
            runner=lambda _payload, _factory: _Result(),
            connection_factory=lambda _: None,
        )
        result = app.call(NORMALIZE_RAW_RECORDS, HEADERS, {})
        self.assertTrue(result["normalized"])


if __name__ == "__main__":
    unittest.main()
