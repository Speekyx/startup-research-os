"""Mission 1.85.6. The local egress review server, on SYNTHETIC material in a temporary folder.

Requests go to 127.0.0.1 only, the way the operator's browser would send them. No held record, no
database and no provider is involved.
"""

from __future__ import annotations

import ast
import http.client
import importlib.util
import json
import pathlib
import sys
import threading

import pytest
from sros_semantic_extraction_contract.egress import scan_surface, transmission_integrity_problems
from sros_semantic_extraction_contract.egress_review import (
    blank_working_file,
    record_set_sha256,
)
from sros_semantic_extraction_contract.surface import render_question_surface, surface_sha256

REPO = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "infrastructure" / "scripts"
SCRIPT = SCRIPTS / "semantic_egress_review.py"
SURFACES = {
    "r-zero-1": render_question_surface("Loop", "<p>How do I loop over a list?</p>"),
    "r-zero-2": render_question_surface("Sort", "<p>How do I sort a dict by value?</p>"),
    "r-url": render_question_surface("Docs", "<p>See https://docs.python.org/3/ please.</p>"),
    "r-secret": render_question_surface(
        "Cfg", "<pre><code>password: hunter2hunter2\n</code></pre>"
    ),
}


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"n08b_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def review():
    return load_script("semantic_egress_review")


def scan_row(rid: str, surface: str) -> dict:
    return {
        "normalized_record_id": rid,
        "surface_sha256": surface_sha256(surface),
        "trigger_counts": {n: len(f) for n, f in scan_surface(surface).items()},
        "transmission_problems": sorted(
            {p.split(":")[0] for p in transmission_integrity_problems(surface)}
        ),
    }


def write_folder(review, folder: pathlib.Path) -> None:
    rows = [scan_row(rid, s) for rid, s in sorted(SURFACES.items())]
    material = {
        "split": "DEVELOPMENT",
        "scan_sha256": "synthetic-scan",
        "records": [
            review.material_record(i, row, SURFACES[row["normalized_record_id"]])
            for i, row in enumerate(rows, 1)
        ],
    }
    (folder / review.MATERIAL_NAME).write_bytes(review.dump(material))
    working = blank_working_file("operator-a", rows, "synthetic-scan")
    (folder / review.working_name("operator-a")).write_bytes(review.dump(working))


class Running:
    def __init__(self, review, folder: pathlib.Path) -> None:
        self.server, self.session = review.build_server(folder, 0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def request(self, method: str, path: str, body=None, *, host=None, token=True, ctype=True):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        if token:
            headers["X-Review-Token"] = self.session.token
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            if ctype:
                headers["Content-Type"] = "application/json"
        connection.request(method, path, body=data, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response, payload

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def running(review, tmp_path):
    write_folder(review, tmp_path)
    server = Running(review, tmp_path)
    yield server
    server.close()


def working(review, folder: pathlib.Path) -> dict:
    return json.loads((folder / review.working_name("operator-a")).read_text("utf-8"))


class TestBoundary:
    def test_the_server_binds_loopback_only(self, running, review) -> None:
        assert running.server.server_address[0] == "127.0.0.1"
        assert review.LOOPBACK == "127.0.0.1"
        tree = ast.parse(SCRIPT.read_text("utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node.func, "attr", "") == "ThreadingHTTPServer"
            ):
                address = node.args[0]
                assert isinstance(address, ast.Tuple)
                assert getattr(address.elts[0], "id", None) == "LOOPBACK"
        source = SCRIPT.read_text("utf-8")
        assert ".".join(["0"] * 4) not in source
        assert 'add_argument("--host"' not in source

    def test_no_external_network_path_or_asset(self, running, review) -> None:
        tree = ast.parse(SCRIPT.read_text("utf-8"))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        } | {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        for forbidden in (
            "urllib",
            "urllib.request",
            "http.client",
            "socket",
            "requests",
            "httpx",
            "anthropic",
            "sros_llm_gateway",
        ):
            assert forbidden not in imported, forbidden
        page = review.PAGE
        for marker in ("http://", "https://", "src=", "<link", "@import", "cdn"):
            assert marker not in page, marker
        response, _ = running.request("GET", "/")
        csp = response.getheader("Content-Security-Policy")
        assert "default-src 'none'" in csp and "connect-src 'self'" in csp

    def test_prepare_refuses_a_directory_inside_the_repository(self, review) -> None:
        assert review.prepare(REPO / "docs" / "egress-review-tmp", "operator-a") == 1
        assert not (REPO / "docs" / "egress-review-tmp").exists()
        assert review.serve(REPO / "docs", 0) == 1

    def test_a_foreign_host_or_missing_token_is_refused(self, running) -> None:
        response, _ = running.request("GET", "/api/state", host="evil.example:80")
        assert response.status == 421
        response, _ = running.request("GET", "/api/state", token=False)
        assert response.status == 403
        body = {"normalized_record_id": "r-url", "decision": "EGRESS_EXCLUDED"}
        response, _ = running.request("POST", "/api/decide", body, token=False)
        assert response.status == 403
        response, _ = running.request("POST", "/api/decide", body, ctype=False)
        assert response.status == 415


class TestHumanActions:
    def test_no_decision_appears_without_an_action(self, running, review, tmp_path) -> None:
        for path in ("/", "/api/state", "/api/state"):
            response, _ = running.request("GET", path)
            assert response.status == 200
        assert working(review, tmp_path)["decisions"] == []
        assert working(review, tmp_path)["bulk_decisions"] == []

    def test_a_click_is_saved_and_survives_a_restart(self, running, review, tmp_path) -> None:
        digest = surface_sha256(SURFACES["r-url"])
        response, payload = running.request(
            "POST",
            "/api/decide",
            {
                "normalized_record_id": "r-url",
                "surface_sha256": digest,
                "decision": "EGRESS_APPROVED",
                "reason": "TRIGGER_REVIEWED_PUBLIC_REFERENCE",
            },
        )
        assert response.status == 200, payload
        saved = working(review, tmp_path)["decisions"]
        assert [
            (d["normalized_record_id"], d["decision_origin"], d["decided_by"]) for d in saved
        ] == [("r-url", "HUMAN_OPERATOR", "operator-a")]
        running.close()
        again = Running(review, tmp_path)
        try:
            _, state = again.request("GET", "/api/state")
            rows = {r["normalized_record_id"]: r for r in json.loads(state)["records"]}
            assert rows["r-url"]["decision"]["reason"] == "TRIGGER_REVIEWED_PUBLIC_REFERENCE"
            assert rows["r-zero-1"]["decision"] is None
            assert json.loads(state)["unresolved"] == 3
        finally:
            again.close()
            running.server = again.server  # the fixture closes this one too, harmlessly

    def test_the_server_refuses_what_the_contract_refuses(self, running, review, tmp_path) -> None:
        secret = {
            "normalized_record_id": "r-secret",
            "surface_sha256": surface_sha256(SURFACES["r-secret"]),
            "decision": "EGRESS_APPROVED",
            "reason": "TRIGGER_REVIEWED_PUBLIC_REFERENCE",
        }
        response, payload = running.request("POST", "/api/decide", secret)
        assert response.status == 422
        assert (
            "SECRET_LIKE_APPROVAL_NEEDS_TRIGGER_REVIEWED_NOT_PERSONAL"
            in json.loads(payload)["error"]
        )
        stale = dict(secret, reason="TRIGGER_REVIEWED_NOT_PERSONAL", surface_sha256="0" * 64)
        response, payload = running.request("POST", "/api/decide", stale)
        assert response.status == 422 and "SURFACE_DIGEST_MISMATCH" in json.loads(payload)["error"]
        assert working(review, tmp_path)["decisions"] == []

    def test_bulk_needs_explicit_confirmation_and_zero_triggers(
        self, running, review, tmp_path
    ) -> None:
        _, state = running.request("GET", "/api/state")
        offer = json.loads(state)["zero_trigger_set"]
        assert offer["normalized_record_ids"] == ["r-zero-1", "r-zero-2"]
        unconfirmed = dict(offer, confirmation="")
        response, _ = running.request("POST", "/api/bulk", unconfirmed)
        assert response.status == 422
        ids = ["r-url", "r-zero-1", "r-zero-2"]
        widened = {
            "normalized_record_ids": ids,
            "surface_sha256": {rid: surface_sha256(SURFACES[rid]) for rid in ids},
            "record_set_sha256": record_set_sha256(ids),
            "confirmation": "I reviewed exactly these 3 zero-trigger records and approve them",
        }
        response, payload = running.request("POST", "/api/bulk", widened)
        assert response.status == 422
        assert "TRIGGERED" in json.loads(payload)["error"]
        assert working(review, tmp_path)["bulk_decisions"] == []
        response, _ = running.request("POST", "/api/bulk", offer)
        assert response.status == 200
        [bulk] = working(review, tmp_path)["bulk_decisions"]
        assert bulk["normalized_record_ids"] == ["r-zero-1", "r-zero-2"]
        assert bulk["decision_origin"] == "HUMAN_OPERATOR"
        assert bulk["reason"] == "BULK_ZERO_TRIGGER_ACCEPTED"


class TestPacketStillCannotExecute:
    def test_the_committed_packet_cannot_execute_again(self) -> None:
        # Mission 1.85.9: the one packet-scoped approval exists and was spent by its attempt.
        runner = load_script("run_semantic_extraction_evaluation")
        packet = runner.verify_packet()
        assert packet["status"] == runner.READY
        # Mission 1.85.11: the Mission 1.85.9 approval and attempt are history; the current packet has none.
        assert runner.HISTORICAL_APPROVAL.exists() and runner.HISTORICAL_ATTEMPT.exists()
        assert not runner.APPROVAL.exists() and not runner.ATTEMPT.exists()
        with pytest.raises(runner.Refused) as refused:
            runner.main(["--execute", "--approval-sha256", "0" * 64])
        assert refused.value.refusal == "OPERATOR_APPROVAL_NOT_RECORDED"
