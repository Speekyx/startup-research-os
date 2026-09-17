"""Mission 1.85.10. The post-model operator review of the nine REPORTED_FAILED_ATTEMPT disagreements.

No test reaches a provider, a model or the database. The review set and its bindings are computed from the
committed artifacts; server tests use synthetic surfaces in a temporary folder. No choice is ever made except
by an explicit POST, as a click would send.
"""

from __future__ import annotations

import ast
import hashlib
import http.client
import importlib.util
import json
import pathlib
import sys
import threading

import pytest
from sros_semantic_extraction_contract import post_model_review as pmr
from sros_semantic_extraction_contract import render_question_surface, surface_sha256

REPO = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO / "docs" / "data"
SCRIPTS = REPO / "infrastructure" / "scripts"
NINE = [
    "17064c93-71cf-5474-ba7f-39ccd516782f",
    "1a659352-390f-5c53-97de-0f725d017f46",
    "203268d4-baf6-5410-a001-cf77843e96e3",
    "37bf2146-b9fc-5e5a-b35b-d59f5f6bfc57",
    "9f91eeea-25e6-5a9e-89e6-54d4490ecd7c",
    "ac423fe4-a4b4-589d-ac49-96932ed51d54",
    "bf04af60-1364-5fd0-8f4f-a8104d131aff",
    "d6bff833-780d-55d3-a5ad-1effebb8a328",
    "e35f990d-117a-59d1-b54e-5165632378bf",
]
BLIND_ANNOTATION_SHA256 = "449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c"
PILOT_EVALUATION_SHA256 = "da468421824e6d66b332057afc0e1873680c28d7c50350ba2be5dfd9192d35ba"
NOW = "2026-09-17T18:00:00+04:00"


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"pmr_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tool():
    return load_script("semantic_disagreement_review")


def synthetic_folder(tool, folder: pathlib.Path, n: int = 3) -> tuple[pathlib.Path, list[dict]]:
    surfaces = {
        f"rec-{i}": render_question_surface(
            f"Question {i}", f"<p>I tried option {i} and it failed with an error here.</p>"
        )
        for i in range(n)
    }
    records = []
    material_records = []
    for position, (rid, surface) in enumerate(surfaces.items(), 1):
        quote = f"I tried option {position - 1} and it failed"
        start = surface.index(quote)
        finding = {
            "finding_id": f"f-{rid}",
            "finding_type": pmr.LABEL,
            "evidence_start": start,
            "evidence_end": start + len(quote),
            "evidence_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(),
        }
        record = {
            "normalized_record_id": rid,
            "surface_sha256": surface_sha256(surface),
            "original_blind_state": "ABSENT",
            "model_state": "PRESENT",
            "model_findings_sha256": pmr.findings_digest([finding]),
        }
        records.append(record)
        material_records.append(tool.material_record(position, record, surface, [finding], False))
    bindings = {"packet_sha256": "p", "approval_sha256": "a"}
    folder.mkdir(parents=True, exist_ok=True)
    (folder / tool.MATERIAL_NAME).write_bytes(
        tool.dump(
            {
                "bindings": bindings,
                "label_definition": tool.label_definition(),
                "records": material_records,
            }
        )
    )
    working = pmr.blank_working_file("operator-a", bindings, records)
    (folder / "post-model-review-working-operator-a.json").write_bytes(tool.dump(working))
    return folder, records


@pytest.fixture
def served(tool, tmp_path):
    folder, records = synthetic_folder(tool, tmp_path / "review")
    server, session = tool.build_server(folder, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    def request(method, path, body=None, *, host=None, token=True):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        headers = {"Host": host or f"127.0.0.1:{port}"}
        if token:
            headers["X-Review-Token"] = session.token
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=data, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, json.loads(payload) if payload.startswith(b"{") else payload

    yield request, session, folder, records, server
    server.shutdown()
    server.server_close()


def click(request, record, choice, note=""):
    return request(
        "POST",
        "/api/decide",
        {
            "normalized_record_id": record["normalized_record_id"],
            "surface_sha256": record["surface_sha256"],
            "model_findings_sha256": record["model_findings_sha256"],
            "decision": choice,
            "note": note,
        },
    )


def test_the_blind_annotation_and_the_pilot_evaluation_are_byte_for_byte_unchanged(tool) -> None:
    assert hashlib.sha256(tool.ANNOTATION.read_bytes()).hexdigest() == BLIND_ANNOTATION_SHA256
    assert hashlib.sha256(tool.EVALUATION.read_bytes()).hexdigest() == PILOT_EVALUATION_SHA256
    annotation = json.loads(tool.ANNOTATION.read_text("utf-8"))
    assert annotation["attestation"]["no_model_output_seen"] is True
    evaluator = load_script("evaluate_semantic_extraction_pilot")
    assert evaluator.dump(evaluator.evaluate()) == evaluator.EVALUATION.read_bytes()
    gate = next(
        r
        for r in json.loads(tool.EVALUATION.read_text("utf-8"))["readings"]
        if r["item_id"] == "false_present_rate_upper_95::REPORTED_FAILED_ATTEMPT"
    )
    assert gate["reading"] == "PILOT_OUTSIDE_PROPOSED_BOUND"


def test_the_review_set_is_exactly_the_nine_disagreements_bound_to_the_pilot(tool) -> None:
    bindings, records, findings = tool.review_inputs()
    assert [r["normalized_record_id"] for r in records] == NINE
    assert all(
        r["original_blind_state"] == "ABSENT" and r["model_state"] == "PRESENT" for r in records
    )
    assert (
        bindings["packet_sha256"]
        == "5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e"
    )
    assert (
        bindings["approval_sha256"]
        == "77cdea89eba08f768b135e099478884d82b2120f8d0fab13e5f8f018b0b48d95"
    )
    assert bindings["original_annotation_sha256"] == BLIND_ANNOTATION_SHA256
    assert bindings["pilot_evaluation_sha256"] == PILOT_EVALUATION_SHA256
    assert bindings["label_definition"] == "first-person-semantic-labels@1.0.0"
    assert sum(len(f) for f in findings.values()) == 13
    definition = tool.label_definition()
    assert "in their own words" in definition["label_set_definition"]
    assert "only asks how to do something" in definition["label_set_definition"]
    assert "A failed workaround counts" in definition["prompt_definition"]
    assert "quoted" in definition["annotation_holder_rule"]


def test_the_page_binds_loopback_only_and_refuses_foreign_hosts(served) -> None:
    request, session, folder, records, server = served
    assert server.server_address[0] == "127.0.0.1"
    status, _ = request("GET", "/api/state", host="evil.example:80")
    assert status == 421
    status, _ = request("GET", "/api/state", token=False)
    assert status == 403
    status, page = request("GET", "/")
    assert status == 200 and b"http://" not in page.replace(b"http://127.0.0.1", b"")
    assert b"https://" not in page


def test_no_choice_exists_without_a_click_and_there_is_no_bulk_path(served) -> None:
    request, session, folder, records, _ = served
    for _ in range(3):
        status, state = request("GET", "/api/state")
        assert status == 200
    working = json.loads((folder / "post-model-review-working-operator-a.json").read_text("utf-8"))
    assert working["decisions"] == [] and state["decided"] == 0
    assert all(r["decision"] is None for r in state["records"])
    status, _ = request("POST", "/api/bulk", {})
    assert status == 404


def test_only_records_under_review_can_be_decided(served) -> None:
    request, *_ = served
    status, body = request(
        "POST",
        "/api/decide",
        {
            "normalized_record_id": NINE[0],
            "surface_sha256": "x",
            "model_findings_sha256": "y",
            "decision": pmr.OVERREAD,
        },
    )
    assert status == 422 and "RECORD_NOT_UNDER_REVIEW" in body["error"]


def test_a_click_is_saved_bound_and_survives_a_restart(tool, served) -> None:
    request, session, folder, records, _ = served
    status, _ = click(request, records[0], pmr.OVERREAD)
    assert status == 200
    status, body = click(request, records[1], pmr.REVISION)
    assert status == 422 and "NOTE_REQUIRED" in body["error"]
    status, _ = click(
        request, records[1], pmr.REVISION, "the asker names the version that kept failing"
    )
    assert status == 200
    wrong = dict(records[2], surface_sha256="0" * 64)
    status, body = click(request, wrong, pmr.AMBIGUOUS, "either reading")
    assert status == 422 and "SURFACE_DIGEST_MISMATCH" in body["error"]
    wrong = dict(records[2], model_findings_sha256="0" * 64)
    status, body = click(request, wrong, pmr.AMBIGUOUS, "either reading")
    assert status == 422 and "MODEL_FINDINGS_DIGEST_MISMATCH" in body["error"]
    resumed = tool.ReviewSession(folder)
    decisions = {d["normalized_record_id"]: d for d in resumed.working["decisions"]}
    assert set(decisions) == {
        records[0]["normalized_record_id"],
        records[1]["normalized_record_id"],
    }
    saved = decisions[records[1]["normalized_record_id"]]
    assert saved["surface_sha256"] == records[1]["surface_sha256"]
    assert saved["model_findings_sha256"] == records[1]["model_findings_sha256"]
    assert saved["provenance"] == pmr.PROVENANCE and saved["blind"] is False
    assert saved["decided_by"] == "operator-a"
    status, _ = request(
        "POST", "/api/undo", {"normalized_record_id": records[0]["normalized_record_id"]}
    )
    assert status == 200 and len(tool.ReviewSession(folder).working["decisions"]) == 1


def test_a_note_that_pastes_the_question_is_refused(served) -> None:
    request, session, folder, records, _ = served
    surface = session.records[records[0]["normalized_record_id"]]["surface"]
    status, body = click(request, records[0], pmr.AMBIGUOUS, surface[:80])
    assert status == 422 and "NOTE_QUOTES_SOURCE_TEXT" in body["error"]


def test_post_model_provenance_cannot_pass_as_a_blind_annotation(tool) -> None:
    bindings, records, _ = tool.review_inputs()
    working = pmr.blank_working_file("operator-a", bindings, records)
    for key in pmr.BLIND_ATTESTATION_KEYS:
        assert key not in working
    assert working["provenance"] == "POST_MODEL_OPERATOR_REVIEW"
    disguised = dict(working, no_model_output_seen=True, reference_origin="HUMAN_OPERATOR")
    codes = {
        c
        for c, _ in pmr.validate_working(
            disguised, expected_bindings=bindings, expected_records=records
        )
    }
    assert "BLIND_ATTESTATION_NOT_PERMITTED" in codes
    relabelled = dict(working, provenance="HUMAN_OPERATOR")
    codes = {
        c
        for c, _ in pmr.validate_working(
            relabelled, expected_bindings=bindings, expected_records=records
        )
    }
    assert "PROVENANCE_OR_LABEL_INVALID" in codes


def test_stale_inputs_mark_the_review_stale(tool) -> None:
    bindings, records, _ = tool.review_inputs()
    working = pmr.blank_working_file("operator-a", bindings, records)
    changed = dict(bindings, run_summary_sha256="0" * 64)
    problems = pmr.validate_working(working, expected_bindings=changed, expected_records=records)
    assert pmr.review_status(working, problems) == "STALE"
    moved = [dict(records[0], surface_sha256="1" * 64), *records[1:]]
    problems = pmr.validate_working(working, expected_bindings=bindings, expected_records=moved)
    assert pmr.review_status(working, problems) == "STALE"


def decide_all(tool, choices: list[str]) -> dict:
    bindings, records, _ = tool.review_inputs()
    working = pmr.blank_working_file("operator-a", bindings, records)
    for record, choice in zip(records, choices, strict=True):
        working["decisions"].append(
            pmr.make_decision(
                working,
                record["normalized_record_id"],
                surface_sha256=record["surface_sha256"],
                model_findings_sha256=record["model_findings_sha256"],
                choice=choice,
                note="a reason in my own words" if choice in pmr.NOTE_REQUIRED else "",
                decided_at=NOW,
            )
        )
    return working


def test_an_incomplete_review_is_never_complete_and_derives_nothing(tool) -> None:
    working = decide_all(tool, [pmr.OVERREAD] * 8 + [pmr.UNRESOLVED])
    status = pmr.review_status(working, [])
    assert status == "INCOMPLETE"
    assert pmr.analyse(working, status)["development_recommendations"] == []
    partial = decide_all(tool, [pmr.OVERREAD] * 9)
    partial["decisions"] = partial["decisions"][:5]
    assert pmr.review_status(partial, []) == "INCOMPLETE"


def test_recommendations_follow_the_frozen_rule(tool) -> None:
    def rec(choices):
        working = decide_all(tool, choices)
        return pmr.analyse(working, pmr.review_status(working, []))["development_recommendations"]

    o, r, a = pmr.OVERREAD, pmr.REVISION, pmr.AMBIGUOUS
    assert rec([o] * 7 + [r, a]) == ["PROMPT_OR_EXTRACTION_CONTRACT_PRECISION_REVISION_REQUIRED"]
    assert rec([r] * 6 + [o] * 3) == ["REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED"]
    assert rec([o] * 4 + [r] * 4 + [a]) == [
        "PROMPT_OR_EXTRACTION_CONTRACT_PRECISION_REVISION_REQUIRED",
        "REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED",
    ]
    assert rec([o] * 5 + [a] * 3 + [r]) == [
        "PROMPT_OR_EXTRACTION_CONTRACT_PRECISION_REVISION_REQUIRED",
        "LABEL_DEFINITION_DECISION_REQUIRED",
    ]


def test_a_complete_committed_review_reproduces_and_leaks_no_text(
    tool, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(tool, "REVIEW", tmp_path / "review.json")
    monkeypatch.setattr(tool, "REVIEW_PAGE", tmp_path / "review.md")
    working = decide_all(tool, [pmr.OVERREAD] * 6 + [pmr.REVISION] * 2 + [pmr.AMBIGUOUS])
    doc, page = tool.render_review(working, [])
    tool.REVIEW.write_bytes(tool.dump(doc))
    tool.REVIEW_PAGE.write_bytes(page)
    assert tool.check() == 0
    assert doc["analysis"]["status"] == "COMPLETE"
    assert doc["blind"] is False and doc["replaces_original_reference"] is False
    assert doc["mission_1_85_9_gate_unchanged"]["reading"] == "PILOT_OUTSIDE_PROPOSED_BOUND"
    diagnostic = doc["post_model_review_diagnostic"]
    assert diagnostic["post_hoc"] is True and diagnostic["preregistered"] is False
    assert diagnostic["is_the_mission_1_85_9_gate_result"] is False
    assert diagnostic["ambiguous_counted_as_false_present"]["false_present"] == 7
    text = tool.REVIEW.read_text("utf-8")
    assert '"quote"' not in text and '"surface"' not in text and '"before"' not in text
    tampered = json.loads(text)
    tampered["decisions"][0]["decision"] = pmr.REVISION
    tool.REVIEW.write_bytes(tool.dump(tampered))
    assert tool.check() == 1


def test_no_network_or_provider_client_in_the_review_path(tool) -> None:
    forbidden = {
        "urllib",
        "urllib.request",
        "socket",
        "requests",
        "httpx",
        "sros_llm_gateway",
        "anthropic",
    }
    for path in (
        SCRIPTS / "semantic_disagreement_review.py",
        REPO
        / "packages/semantic-extraction-contract/python/sros_semantic_extraction_contract/post_model_review.py",
    ):
        tree = ast.parse(path.read_text("utf-8"))
        imported = {
            name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for name in (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
        }
        assert not imported & forbidden, path.name
        assert "--execute" not in path.read_text("utf-8")


def test_the_whole_review_flow_reaches_no_provider(tool, tmp_path, monkeypatch) -> None:
    from sros_llm_gateway import transport

    def no_transport(*args, **kwargs):
        raise AssertionError("a provider transport was built")

    monkeypatch.setattr(transport.UrllibTransport, "__init__", no_transport)
    folder, records = synthetic_folder(tool, tmp_path / "flow")
    session = tool.ReviewSession(folder)
    for record in records:
        session.decide(
            {
                "normalized_record_id": record["normalized_record_id"],
                "surface_sha256": record["surface_sha256"],
                "model_findings_sha256": record["model_findings_sha256"],
                "decision": pmr.OVERREAD,
            }
        )
    assert len(session.working["decisions"]) == 3
    assert tool.check() == 0
