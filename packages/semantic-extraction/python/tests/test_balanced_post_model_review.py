"""Mission 1.85.13. The balanced post-model review of the prompt 1.1.0 disagreements.

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
from sros_semantic_extraction_contract import balanced_post_model_review as bpmr
from sros_semantic_extraction_contract import render_question_surface, surface_sha256

REPO = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO / "docs" / "data"
SCRIPTS = REPO / "infrastructure" / "scripts"
BLIND_ANNOTATION_SHA256 = "449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c"
NEW_FALSE_PRESENT_PREFIXES = (
    "3194f76d",
    "3d0568c4",
    "42642469",
    "58966c7e",
    "6dfbef0a",
    "7eed79ff",
    "88376fa5",
    "c128f807",
    "f53c6872",
)
FALSE_NEGATIVE_PREFIXES = (
    "4a3fc738",
    "96054702",
    "b7996f9d",
    "e2162aae",
    "e9edbbaa",
    "f876b0be",
)
NOW = "2026-09-18T09:00:00+04:00"


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"balanced_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tool():
    return load_script("balanced_disagreement_review")


def synthetic_folder(tool, folder: pathlib.Path) -> tuple[pathlib.Path, list[dict]]:
    """One record per side, with surfaces and model output built here rather than read from the database."""
    records, material_records = [], []
    for position, side in enumerate(bpmr.SIDES, start=1):
        rid = f"rec-{side.lower()}"
        surface = render_question_surface(
            f"Question {position}", f"<p>I tried option {position} and it failed with an error.</p>"
        )
        quote = f"I tried option {position} and it failed"
        start = surface.index(quote)
        findings = (
            [
                {
                    "finding_id": f"f-{rid}",
                    "finding_type": bpmr.LABEL,
                    "evidence_start": start,
                    "evidence_end": start + len(quote),
                    "evidence_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(),
                }
            ]
            if side == bpmr.NEW_FALSE_PRESENT
            else []
        )
        extraction = {
            "extraction_state": "FINDINGS_PRESENT" if findings else "NO_FINDING_ESTABLISHED",
            "findings": findings,
        }
        blind_state, model_state = bpmr.EXPECTED_STATES[side]
        record = {
            "normalized_record_id": rid,
            "side": side,
            "surface_sha256": surface_sha256(surface),
            "original_blind_state": blind_state,
            "model_state": model_state,
            "model_output_sha256": bpmr.model_output_digest(extraction),
        }
        records.append(record)
        material_records.append(
            tool.material_record(
                position,
                record,
                surface,
                {"normalized_record_id": rid, "extraction": extraction},
                {"note_present": False, "spans": []},
            )
        )
    bindings = {"packet_sha256": "p", "approval_sha256": "a"}
    folder.mkdir(parents=True, exist_ok=True)
    (folder / tool.MATERIAL_NAME).write_bytes(
        tool.dump(
            {
                "bindings": bindings,
                "label_definition": tool.label_definition(),
                "prior_review_reused": {"records": []},
                "records": material_records,
            }
        )
    )
    working = bpmr.blank_working_file("operator-a", bindings, records)
    (folder / "balanced-review-working-operator-a.json").write_bytes(tool.dump(working))
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
            "model_output_sha256": record["model_output_sha256"],
            "decision": choice,
            "note": note,
        },
    )


# -- history ---------------------------------------------------------------------------------------------


def test_every_historical_artifact_still_reproduces(tool) -> None:
    assert hashlib.sha256(tool.ANNOTATION.read_bytes()).hexdigest() == BLIND_ANNOTATION_SHA256
    evaluator = load_script("evaluate_semantic_extraction_pilot")
    for pilot in (evaluator.V1, evaluator.V2):
        evaluation = evaluator.evaluate(pilot)
        assert evaluator.dump(evaluation) == pilot.evaluation.read_bytes()
        assert evaluator.page(evaluation, pilot) == pilot.page.read_bytes()
    prior_tool = load_script("semantic_disagreement_review")
    assert prior_tool.check() == 0
    diagnostics = load_script("evaluate_prompt_revision_diagnostics")
    assert diagnostics.pilot_evaluator.dump(diagnostics.build()) == diagnostics.OUTPUT.read_bytes()


# -- the corrected accounting ----------------------------------------------------------------------------


def test_the_balanced_sets_are_derived_from_the_committed_artifacts(tool) -> None:
    accounting = tool.accounting()
    counts = accounting["counts"]
    assert counts["current_false_present"] == 16
    assert counts["current_false_negative"] == 6
    assert counts["reviewed_in_mission_1_85_10"] == 9
    assert counts["previously_reviewed_current_false_present"] == 7
    assert counts["new_unreviewed_false_present"] == 9
    assert counts["balanced_review_set"] == 15
    assert [r[:8] for r in accounting["new_unreviewed_false_present"]] == list(
        NEW_FALSE_PRESENT_PREFIXES
    )
    assert [r[:8] for r in accounting["current_false_negative"]] == list(FALSE_NEGATIVE_PREFIXES)


def test_subtracting_the_historical_review_count_is_not_the_intersection(tool) -> None:
    """The Mission 1.85.12 report's counting error, made impossible to repeat without noticing.

    16 current false PRESENT minus 9 historically reviewed records = 7 is arithmetic on the wrong sets: two of
    the nine reviewed records stopped disagreeing under prompt 1.1.0, so only seven of them are still false
    PRESENT and nine current false PRESENT have never been reviewed.
    """
    accounting = tool.accounting()
    counts = accounting["counts"]
    naive = counts["current_false_present"] - counts["reviewed_in_mission_1_85_10"]
    assert naive == 7
    assert counts["new_unreviewed_false_present"] == 9
    assert naive != counts["new_unreviewed_false_present"]
    prior = json.loads(
        (DATA / "semantic-extraction-post-model-review-development-v1.json").read_text("utf-8")
    )
    reviewed = {d["normalized_record_id"] for d in prior["decisions"]}
    current = set(accounting["current_false_present"])
    assert len(reviewed & current) == counts["previously_reviewed_current_false_present"] == 7
    assert len(reviewed - current) == 2, "two reviewed records were corrected by prompt 1.1.0"
    assert sorted(current - reviewed) == accounting["new_unreviewed_false_present"]


def test_the_review_set_is_exactly_fifteen_records_and_nothing_else(tool) -> None:
    bindings, records, prior = tool.review_inputs()
    assert len(records) == 15
    sides = {side: [r for r in records if r["side"] == side] for side in bpmr.SIDES}
    assert len(sides[bpmr.NEW_FALSE_PRESENT]) == 9 and len(sides[bpmr.FALSE_NEGATIVE]) == 6
    ids = [r["normalized_record_id"] for r in records]
    assert len(set(ids)) == 15, "a record may not be reviewed on both sides"
    reused = {r["normalized_record_id"] for r in prior["records"]}
    assert len(reused) == 7 and not reused & set(ids)
    for record in records:
        blind, model = bpmr.EXPECTED_STATES[record["side"]]
        assert (record["original_blind_state"], record["model_state"]) == (blind, model)
    for name in ("packet_sha256", "approval_sha256", "run_summary_sha256", "prior_review_sha256"):
        assert len(bindings[name]) == 64


def test_the_prior_seven_are_reused_and_never_re_asked(tool) -> None:
    _, records, prior = tool.review_inputs()
    assert prior["origin"] == bpmr.PRIOR_REVIEW_REUSE
    assert prior["reviewed_and_still_false_present"] == 7
    assert len(prior["reviewed_and_corrected_by_prompt_1_1_0"]) == 2
    assert all(
        r["decision"] == "HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD" for r in prior["records"]
    )
    # No prior record is offered as a new decision, and no timestamp is invented for one.
    reviewable = {r["normalized_record_id"] for r in records}
    for record in prior["records"]:
        assert record["normalized_record_id"] not in reviewable
        assert record["decided_at"].startswith("2026-09-17")


# -- the review itself ------------------------------------------------------------------------------------


def test_the_page_binds_loopback_only_and_refuses_foreign_hosts(served) -> None:
    request, session, _, _, server = served
    assert server.server_address[0] == "127.0.0.1"
    status, _ = request("GET", "/", host="example.com")
    assert status == 421
    status, body = request("GET", "/api/state", token=False)
    assert status == 403 and body["error"] == "TOKEN_REQUIRED"
    status, page = request("GET", "/")
    assert status == 200 and b"http://" not in page.replace(b"http://127.0.0.1", b"")


def test_no_choice_exists_without_a_click_and_there_is_no_bulk_path(served) -> None:
    request, session, _, records, _ = served
    status, state = request("GET", "/api/state")
    assert status == 200
    assert state["decided"] == 0 and all(r["decision"] is None for r in state["records"])
    assert state["choices_by_side"] == {
        side: list(bpmr.CHOICES_BY_SIDE[side]) for side in bpmr.SIDES
    }
    for path in ("/api/decide_all", "/api/bulk", "/api/accept_all"):
        status, _ = request("POST", path, {})
        assert status == 404
    page = request("GET", "/")[1].decode("utf-8")
    assert "decide_all" not in page and "bulk" not in page


def test_a_choice_from_the_other_side_is_refused(served) -> None:
    request, _, _, records, _ = served
    false_present = next(r for r in records if r["side"] == bpmr.NEW_FALSE_PRESENT)
    false_negative = next(r for r in records if r["side"] == bpmr.FALSE_NEGATIVE)
    status, body = click(request, false_present, bpmr.UNDERREAD)
    assert status == 422 and body["error"].startswith("CHOICE_NOT_AVAILABLE_ON_THIS_SIDE")
    status, body = click(request, false_negative, bpmr.REVISION_TO_PRESENT, note="a reason")
    assert status == 422 and body["error"].startswith("CHOICE_NOT_AVAILABLE_ON_THIS_SIDE")
    status, _ = click(request, false_negative, bpmr.UNDERREAD)
    assert status == 200


def test_only_records_under_review_can_be_decided(served) -> None:
    request, _, _, records, _ = served
    status, body = request(
        "POST",
        "/api/decide",
        {
            "normalized_record_id": "17064c93-71cf-5474-ba7f-39ccd516782f",
            "surface_sha256": records[0]["surface_sha256"],
            "model_output_sha256": records[0]["model_output_sha256"],
            "decision": bpmr.OVERREAD,
        },
    )
    assert status == 422 and body["error"].startswith("RECORD_NOT_UNDER_REVIEW")


def test_a_click_is_bound_to_what_was_shown_and_survives_a_restart(tool, served) -> None:
    request, session, folder, records, _ = served
    record = records[0]
    status, body = click(request, dict(record, surface_sha256="0" * 64), bpmr.OVERREAD)
    assert status == 422 and body["error"].startswith("SURFACE_DIGEST_MISMATCH")
    status, body = click(request, dict(record, model_output_sha256="0" * 64), bpmr.OVERREAD)
    assert status == 422 and body["error"].startswith("MODEL_OUTPUT_DIGEST_MISMATCH")
    status, body = click(request, record, bpmr.REVISION_TO_PRESENT)
    assert status == 422 and body["error"].startswith("NOTE_REQUIRED")
    status, state = click(request, record, bpmr.OVERREAD)
    assert status == 200 and state["state"]["decided"] == 1
    decision = state["state"]["records"][0]["decision"]
    assert decision["decision"] == bpmr.OVERREAD
    assert decision["blind"] is False and decision["provenance"] == bpmr.PROVENANCE
    assert decision["review_origin"] == bpmr.THIS_MISSION_REVIEW
    assert decision["side"] == bpmr.NEW_FALSE_PRESENT
    resumed = tool.ReviewSession(folder)
    assert len(resumed.working["decisions"]) == 1


def test_a_note_that_pastes_the_question_is_refused(served) -> None:
    request, session, _, records, _ = served
    surface = session.records[records[0]["normalized_record_id"]]["surface"]
    status, body = click(request, records[0], bpmr.AMBIGUOUS, note=surface[:120])
    assert status == 422 and body["error"].startswith("NOTE_QUOTES_SOURCE_TEXT")


# -- provenance and staleness -----------------------------------------------------------------------------


def test_post_model_provenance_cannot_pass_as_a_blind_annotation(tool) -> None:
    bindings, records, _ = tool.review_inputs()
    working = bpmr.blank_working_file("operator-a", bindings, records)
    assert working["provenance"] == "POST_MODEL_OPERATOR_REVIEW"
    for key in ("no_model_output_seen", "attestation", "reference_origin"):
        claimed = dict(working, **{key: True})
        problems = bpmr.validate_working(
            claimed, expected_bindings=bindings, expected_records=records
        )
        assert ("BLIND_ATTESTATION_NOT_PERMITTED", key) in problems
    decision = bpmr.make_decision(
        working,
        records[0]["normalized_record_id"],
        surface_sha256=records[0]["surface_sha256"],
        model_output_sha256=records[0]["model_output_sha256"],
        choice=bpmr.OVERREAD,
        note="",
        decided_at=NOW,
    )
    assert decision["blind"] is False and decision["review_origin"] == bpmr.THIS_MISSION_REVIEW
    forged = dict(working, decisions=[dict(decision, review_origin=bpmr.PRIOR_REVIEW_REUSE)])
    problems = bpmr.validate_working(forged, expected_bindings=bindings, expected_records=records)
    assert any(code == "DECISION_REVIEW_ORIGIN_INVALID" for code, _ in problems)


def test_stale_inputs_mark_the_review_stale(tool) -> None:
    bindings, records, _ = tool.review_inputs()
    working = bpmr.blank_working_file("operator-a", bindings, records)
    for name in ("run_summary_sha256", "prior_review_sha256", "original_annotation_sha256"):
        changed = dict(bindings, **{name: "0" * 64})
        problems = bpmr.validate_working(
            working, expected_bindings=changed, expected_records=records
        )
        assert bpmr.review_status(working, problems) == "STALE"
    moved = [dict(records[0], surface_sha256="1" * 64), *records[1:]]
    problems = bpmr.validate_working(working, expected_bindings=bindings, expected_records=moved)
    assert bpmr.review_status(working, problems) == "STALE"


# -- diagnostics ------------------------------------------------------------------------------------------


def decide_all(tool, choices: dict[str, str]) -> dict:
    bindings, records, _ = tool.review_inputs()
    working = bpmr.blank_working_file("operator-a", bindings, records)
    for record in records:
        choice = choices[record["normalized_record_id"]]
        working["decisions"].append(
            bpmr.make_decision(
                working,
                record["normalized_record_id"],
                surface_sha256=record["surface_sha256"],
                model_output_sha256=record["model_output_sha256"],
                choice=choice,
                note="a reason in my own words" if choice in bpmr.NOTE_REQUIRED else "",
                decided_at=NOW,
            )
        )
    return working


def by_side(tool, false_present: list[str], false_negative: list[str]) -> dict[str, str]:
    _, records, _ = tool.review_inputs()
    ids = {
        side: [r["normalized_record_id"] for r in records if r["side"] == side]
        for side in bpmr.SIDES
    }
    return {
        **dict(zip(ids[bpmr.NEW_FALSE_PRESENT], false_present, strict=True)),
        **dict(zip(ids[bpmr.FALSE_NEGATIVE], false_negative, strict=True)),
    }


def test_an_incomplete_review_is_never_complete_and_derives_nothing(tool) -> None:
    working = decide_all(
        tool, by_side(tool, [bpmr.OVERREAD] * 8 + [bpmr.UNRESOLVED], [bpmr.UNDERREAD] * 6)
    )
    status = bpmr.review_status(working, [])
    assert status == "INCOMPLETE"
    analysis = bpmr.analyse(working, status)
    assert analysis["development_recommendations"] == []
    doc, _ = tool.render_review(working, [])
    assert doc["combined_diagnostic"] is None
    partial = decide_all(tool, by_side(tool, [bpmr.OVERREAD] * 9, [bpmr.UNDERREAD] * 6))
    partial["decisions"] = partial["decisions"][:5]
    assert bpmr.review_status(partial, []) == "INCOMPLETE"


def test_recommendations_follow_the_frozen_rule(tool) -> None:
    def rec(false_present, false_negative):
        working = decide_all(tool, by_side(tool, false_present, false_negative))
        return bpmr.analyse(working, bpmr.review_status(working, []))["development_recommendations"]

    o, rp, a = bpmr.OVERREAD, bpmr.REVISION_TO_PRESENT, bpmr.AMBIGUOUS
    u, ra = bpmr.UNDERREAD, bpmr.REVISION_TO_ABSENT
    # Both sides confirmed strongly: the prompt-only route is reported as insufficient.
    assert rec([o] * 9, [u] * 6) == [
        "RFA_PRECISION_REMAINS_MODEL_OR_EXTRACTION_CONTRACT_PROBLEM",
        "RFA_PROMPT_1_1_OVERCONSTRAINS_TRUE_POSITIVES",
        "PROMPT_ONLY_REVISION_INSUFFICIENT_CONSIDER_STRUCTURED_EXTRACTION_CONTRACT",
    ]
    # Over-reads confirmed, the reference revised on the other side.
    assert rec([o] * 9, [ra] * 6) == [
        "RFA_PRECISION_REMAINS_MODEL_OR_EXTRACTION_CONTRACT_PROBLEM",
        "REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED",
    ]
    # Ambiguity on a third of the reviewed records reaches the label-definition decision.
    assert rec([a] * 5 + [o] * 4, [u] * 6) == [
        "RFA_PROMPT_1_1_OVERCONSTRAINS_TRUE_POSITIVES",
        "LABEL_DEFINITION_DECISION_REQUIRED",
    ]
    # Revisions on one side only, below a third: no adjudication recommendation.
    assert "REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED" not in rec([rp] * 3 + [o] * 6, [u] * 6)


def test_a_complete_committed_review_reproduces_and_leaks_no_text(
    tool, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(tool, "REVIEW", tmp_path / "review.json")
    monkeypatch.setattr(tool, "REVIEW_PAGE", tmp_path / "review.md")
    working = decide_all(
        tool,
        by_side(
            tool,
            [bpmr.OVERREAD] * 7 + [bpmr.REVISION_TO_PRESENT, bpmr.AMBIGUOUS],
            [bpmr.UNDERREAD] * 6,
        ),
    )
    doc, page = tool.render_review(working, [])
    tool.REVIEW.write_bytes(tool.dump(doc))
    tool.REVIEW_PAGE.write_bytes(page)
    assert tool.check() == 0
    assert doc["analysis"]["status"] == "COMPLETE"
    assert doc["blind"] is False and doc["replaces_original_reference"] is False
    diagnostic = doc["combined_diagnostic"]
    assert diagnostic["post_hoc"] is True and diagnostic["preregistered"] is False
    assert diagnostic["is_the_mission_1_85_12_gate_result"] is False
    assert diagnostic["mission_1_85_12_unchanged"]["reading"] == "PILOT_OUTSIDE_PROPOSED_BOUND"
    assert diagnostic["mission_1_85_12_unchanged"]["false_present"] == 16
    assert diagnostic["mission_1_85_12_unchanged"]["true_present"] == 9
    assert diagnostic["false_present"]["prior_reviewed_persistent"]["count"] == 7
    assert diagnostic["false_present"]["reviewed_here"]["count"] == 9
    assert diagnostic["false_negative"]["reviewed_here"]["count"] == 6
    assert diagnostic["false_negative"]["total"] == 6
    text = tool.REVIEW.read_text("utf-8")
    for forbidden in ('"quote"', '"surface"', '"before"', '"after"', "evidence_quote"):
        assert forbidden not in text
    tampered = json.loads(text)
    tampered["decisions"][0]["decision"] = bpmr.AMBIGUOUS
    tool.REVIEW.write_bytes(tool.dump(tampered))
    assert tool.check() == 1


# -- boundaries -------------------------------------------------------------------------------------------


def test_no_network_or_provider_client_on_the_review_path(tool) -> None:
    forbidden = {
        "urllib",
        "urllib.request",
        "socket",
        "requests",
        "httpx",
        "sros_llm_gateway",
        "anthropic",
        "sros_semantic_extraction",
    }
    for path in (
        SCRIPTS / "balanced_disagreement_review.py",
        REPO
        / "packages/semantic-extraction-contract/python/sros_semantic_extraction_contract/balanced_post_model_review.py",
    ):
        source = path.read_text("utf-8")
        tree = ast.parse(source)
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
        assert "--execute" not in source
        assert "run_semantic_extraction_evaluation" not in source


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
                "model_output_sha256": record["model_output_sha256"],
                "decision": bpmr.CONFIRMED_BY_SIDE[record["side"]],
            }
        )
    assert len(session.working["decisions"]) == 2
    assert tool.check() == 0


def test_no_committed_review_yet_means_waiting_not_complete(tool) -> None:
    if tool.REVIEW.exists():
        pytest.skip("the operator has recorded the balanced review")
    assert tool.check() == 0


def test_the_committed_operator_review_is_complete_bound_and_reproduces(tool) -> None:
    if not tool.REVIEW.exists():
        pytest.skip("the operator has not recorded the balanced review yet")
    assert tool.check() == 0
    doc = json.loads(tool.REVIEW.read_text("utf-8"))
    assert doc["analysis"]["status"] == "COMPLETE"
    assert doc["blind"] is False and doc["provenance"] == "POST_MODEL_OPERATOR_REVIEW"
    assert len(doc["decisions"]) == 15
    assert all(d["review_origin"] == bpmr.THIS_MISSION_REVIEW for d in doc["decisions"])
    assert len(doc["prior_review_reused"]["records"]) == 7
    assert hashlib.sha256(tool.ANNOTATION.read_bytes()).hexdigest() == BLIND_ANNOTATION_SHA256
    unchanged = doc["combined_diagnostic"]["mission_1_85_12_unchanged"]
    assert (unchanged["false_present"], unchanged["reading"]) == (
        16,
        "PILOT_OUTSIDE_PROPOSED_BOUND",
    )
