"""Mission 1.85.14. The second blind human annotation (operator-b) and the frozen A/B agreement analysis.

No test reaches a provider, a model or the database. Preparation runs with synthetic surfaces in a temporary
folder; the agreement analysis runs on the committed operator-a file and a synthetic operator-b file built in
a temporary folder. Nothing is written to the repository.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest
from sros_semantic_extraction_contract.annotation import HoldoutAccessError
from sros_semantic_extraction_contract.annotation_session import SessionQuit, run_session

REPO = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO / "docs" / "data"
SCRIPTS = REPO / "infrastructure" / "scripts"
A_SHA256 = "449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c"
RFA = "REPORTED_FAILED_ATTEMPT"
NEG = "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"second_blind_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load(name: str):
    return json.loads((DATA / name).read_text("utf-8"))


APPROVED = set(
    load("stack-overflow-semantic-egress-eligibility-development-v1.json")["approved_record_ids"]
)


@pytest.fixture
def annotation(monkeypatch):
    module = load_script("semantic_annotation")
    blank = json.loads(module.BLANK_DEVELOPMENT.read_text("utf-8"))
    surfaces = {
        r["normalized_record_id"]: f"synthetic surface {i}" for i, r in enumerate(blank["records"])
    }
    monkeypatch.setattr(module, "development_surfaces", lambda: surfaces)
    return module


@pytest.fixture
def prepared(annotation, tmp_path):
    out = tmp_path / "operator-b"
    assert (
        annotation.prepare("operator-b", "HUMAN_OPERATOR", out, annotation.SCOPE_EGRESS_APPROVED)
        == 0
    )
    pack = json.loads((out / "pack-development-operator-b.json").read_text("utf-8"))
    return out, pack


# -- history ---------------------------------------------------------------------------------------------


def test_the_original_blind_annotation_and_every_evaluation_are_unchanged() -> None:
    assert (
        hashlib.sha256(
            (
                DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
            ).read_bytes()
        ).hexdigest()
        == A_SHA256
    )
    evaluator = load_script("evaluate_semantic_extraction_pilot")
    for pilot in (evaluator.V1, evaluator.V2):
        assert evaluator.dump(evaluator.evaluate(pilot)) == pilot.evaluation.read_bytes()
    assert load_script("semantic_disagreement_review").check() == 0
    assert load_script("balanced_disagreement_review").check() == 0


def test_packet_v5_is_pinned_to_the_annotation_it_bound() -> None:
    renderer = load_script("render_semantic_extraction_packet")
    source = (SCRIPTS / "render_semantic_extraction_packet.py").read_text("utf-8")
    assert (
        "ANNOTATION_GLOB" not in source
        and "glob(" not in source.split("def build")[1].split("def ")[0]
    )
    assert renderer.REFERENCE_ANNOTATION_FILES == (
        "stack-overflow-semantic-annotations-development-operator-a-v1.json",
    )
    assert renderer.dump(renderer.build()) == renderer.PACKET.read_bytes()


# -- the operator-b working material ---------------------------------------------------------------------


def test_operator_b_starts_with_46_unlabelled_records_and_nothing_else(prepared) -> None:
    out, pack = prepared
    assert len(pack["records"]) == 46
    assert {r["normalized_record_id"] for r in pack["records"]} == APPROVED
    assert pack["record_scope"] == "DEVELOPMENT_EGRESS_APPROVED"
    assert all(c["state"] == "UNLABELLED" for r in pack["records"] for c in r["labels"].values())
    assert all(
        not c.get("evidence") and c.get("subject") is None
        for r in pack["records"]
        for c in r["labels"].values()
    )
    assert pack["annotator_id"] == "operator-b" and pack["reference_origin"] == "HUMAN_OPERATOR"
    assert all(
        v is None
        for k, v in pack["attestation"].items()
        if k not in ("attestation_id", "annotator_id")
    )
    assert not pack.get("annotation_started_at") and not pack.get("annotation_completed_at")
    assert sorted(p.name for p in out.iterdir()) == ["pack-development-operator-b.json", "surfaces"]
    assert len(list((out / "surfaces").iterdir())) == 46


def test_no_model_output_previous_label_or_review_status_reaches_operator_b(prepared) -> None:
    out, pack = prepared
    # The attestation's own flag names (no_model_output_seen, ...) are the annotator's promise, not content.
    text = json.dumps({k: v for k, v in pack.items() if k != "attestation"})
    for surface in (out / "surfaces").iterdir():
        text += surface.read_text("utf-8")
    forbidden = (
        "operator-a",
        '"PRESENT"',
        '"ABSENT"',
        '"UNCERTAIN"',
        "prediction",
        "model_output",
        "finding",
        "evidence_quote",
        "post_model",
        "POST_MODEL",
        "OVERREAD",
        "UNDERREAD",
        "KNOWN_OVERREAD",
        "POSITIVE_SENSITIVITY",
        "disagreement",
        "false_present",
        "FALSE_NEGATIVE",
        "rfa-regression",
        "regression_spec",
        "regression-spec",
        "prompt",
        "claude",
        "anthropic",
    )
    for token in forbidden:
        assert token not in text, token
    # The scope is named and hashed; nothing says why any record is in it.
    assert (
        pack["record_scope_ids_sha256"]
        == hashlib.sha256("\n".join(sorted(APPROVED)).encode()).hexdigest()
    )


def test_the_form_asks_the_original_questions_and_reveals_nothing(prepared) -> None:
    from sros_semantic_extraction_contract import annotation_session

    source = pathlib.Path(annotation_session.__file__).read_text("utf-8")
    for token in ("prompt", "model", "agreement", "operator-a", "disagree", "review"):
        assert token not in source.split("QUESTIONS: dict")[1].split("def _now")[0].lower(), token


def test_there_is_no_default_and_no_bulk_answer(prepared) -> None:
    _, pack = prepared
    surfaces = {r["normalized_record_id"]: "synthetic" for r in pack["records"]}
    answers = iter(["", "yes", "all", "a", "*", "q"])
    with pytest.raises(SessionQuit):
        run_session(
            pack, surfaces, ask=lambda _: next(answers), say=lambda _: None, save=lambda _: None
        )
    assert all(c["state"] == "UNLABELLED" for r in pack["records"] for c in r["labels"].values())


def test_every_answered_record_is_saved_and_the_session_resumes(prepared) -> None:
    _, pack = prepared
    surfaces = {r["normalized_record_id"]: "synthetic" for r in pack["records"]}
    saved: list[dict] = []
    first = iter(["n"] * 8 + ["o", "q"])
    with pytest.raises(SessionQuit):
        run_session(
            pack,
            surfaces,
            ask=lambda _: next(first),
            say=lambda _: None,
            save=lambda p: saved.append(copy.deepcopy(p)),
        )
    first_id = pack["record_order"][0]
    done = {r["normalized_record_id"]: r for r in saved[-1]["records"]}
    assert all(c["state"] == "ABSENT" for c in done[first_id]["labels"].values())
    shown: list[str] = []
    second = iter(["q"])
    with pytest.raises(SessionQuit):
        run_session(
            saved[-1], surfaces, ask=lambda _: next(second), say=shown.append, save=lambda _: None
        )
    assert any("QUESTION 2/46" in line for line in shown)
    assert not any("QUESTION 1/46" in line for line in shown)


def test_holdout_cannot_be_loaded(annotation, tmp_path) -> None:
    holdout = tmp_path / "pack-holdout-operator-b.json"
    holdout.write_text("{}", encoding="utf-8")
    with pytest.raises(HoldoutAccessError):
        annotation.refuse_holdout_path(holdout)
    corpus = load("stack-overflow-semantic-evaluation-corpus-v1.json")
    holdout_ids = {r["normalized_record_id"] for r in corpus["records"] if r["split"] == "HOLDOUT"}
    assert not holdout_ids & annotation.scope_ids(annotation.SCOPE_EGRESS_APPROVED)


# -- the agreement ---------------------------------------------------------------------------------------


def synthetic_b(flips: dict[str, dict[str, str]]) -> dict:
    """operator-b as the committed importer would write it: operator-a's cells on the 46, then some flipped."""
    a = load("stack-overflow-semantic-annotations-development-operator-a-v1.json")
    b = copy.deepcopy(a)
    b["annotator_id"] = "operator-b"
    b["attestation"] = dict(b["attestation"], annotator_id="operator-b")
    b["records"] = [r for r in b["records"] if r["normalized_record_id"] in APPROVED]
    for record in b["records"]:
        for label, state in flips.get(record["normalized_record_id"], {}).items():
            cell = record["labels"][label]
            cell["state"] = state
            if state != "PRESENT" and "spans" in cell:
                cell["spans"], cell["subject"] = [], None
    b["record_scope"] = "DEVELOPMENT_EGRESS_APPROVED"
    b["record_scope_ids_sha256"] = hashlib.sha256("\n".join(sorted(APPROVED)).encode()).hexdigest()
    b["blind_to_model_outputs"] = True
    b["blind_to_other_annotators"] = True
    return b


@pytest.fixture
def agreement_tool(tmp_path, monkeypatch):
    tool = load_script("inter_human_agreement")
    for name in ("B_FILE", "AGREEMENT", "PAGE", "DISAGREEMENTS"):
        monkeypatch.setattr(tool, name, tmp_path / getattr(tool, name).name)
    return tool


def write_b(tool, b: dict) -> None:
    tool.B_FILE.write_bytes(tool.dump(b))


def test_agreement_cannot_run_before_operator_b_is_frozen(agreement_tool) -> None:
    assert agreement_tool.main(["--check"]) == 0
    assert agreement_tool.main(["--write"]) == 0
    assert not agreement_tool.AGREEMENT.exists() and not agreement_tool.DISAGREEMENTS.exists()
    agreement_tool.AGREEMENT.write_text("{}", encoding="utf-8")
    assert agreement_tool.main(["--check"]) == 1, (
        "an agreement written before operator-b exists is refused"
    )


def test_identical_blind_annotations_agree_fully_and_keep_shared_uncertainty_open(
    agreement_tool,
) -> None:
    write_b(agreement_tool, synthetic_b({}))
    doc, disagreements = agreement_tool.build()
    rfa = doc["labels"][RFA]
    assert doc["records_compared"] == 46
    assert rfa["raw_agreement_three_state"] == 1.0 and rfa["cohen_kappa_three_state"] == 1.0
    assert doc["adjudicated"] is False and doc["consensus_reference_created"] is False
    d = disagreements["labels"][RFA]
    for kind in ("A_PRESENT_B_ABSENT", "A_ABSENT_B_PRESENT", "SPAN_ONLY", "SUBJECT_ONLY"):
        assert d[kind] == [], kind
    # A shared UNCERTAIN is still an open question: identical files are not a reason to skip adjudication.
    assert d["A_OR_B_UNCERTAIN"] and doc["status"] == agreement_tool.ADJUDICATION_REQUIRED


def test_disagreements_are_derived_by_kind(agreement_tool) -> None:
    a = load("stack-overflow-semantic-annotations-development-operator-a-v1.json")
    cells = {
        r["normalized_record_id"]: r["labels"][RFA]["state"]
        for r in a["records"]
        if r["normalized_record_id"] in APPROVED
    }
    present = sorted(r for r, s in cells.items() if s == "PRESENT")
    absent = sorted(r for r, s in cells.items() if s == "ABSENT")
    flips = {
        present[0]: {RFA: "ABSENT"},
        absent[0]: {RFA: "PRESENT"},
        absent[1]: {RFA: "UNCERTAIN"},
    }
    write_b(agreement_tool, synthetic_b(flips))
    doc, disagreements = agreement_tool.build()
    d = disagreements["labels"][RFA]
    assert d["A_PRESENT_B_ABSENT"] == [present[0]]
    assert d["A_ABSENT_B_PRESENT"] == [absent[0]]
    assert absent[1] in d["A_OR_B_UNCERTAIN"]
    assert doc["status"] == agreement_tool.ADJUDICATION_REQUIRED
    confusion = doc["labels"][RFA]["confusion"]
    assert confusion["A_PRESENT__B_ABSENT"] == 1 and confusion["A_ABSENT__B_PRESENT"] == 1
    assert sum(confusion.values()) == 46


def test_negative_evaluation_positive_support_is_reported_as_insufficient(agreement_tool) -> None:
    write_b(agreement_tool, synthetic_b({}))
    doc, _ = agreement_tool.build()
    neg = doc["labels"][NEG]
    assert neg["state_counts"]["A"]["PRESENT"] == 0
    assert neg["positive_class_support"]["sufficient"] is False
    assert neg["present_specific_agreement"] == "UNDEFINED"


def test_post_model_reviews_never_enter_the_agreement(
    agreement_tool, tmp_path, monkeypatch
) -> None:
    write_b(agreement_tool, synthetic_b({}))
    baseline, _ = agreement_tool.build()
    forged = tmp_path / "forged-review.json"
    review = load("semantic-extraction-post-model-review-development-v1.json")
    for decision in review["decisions"]:
        decision["decision"] = "POST_MODEL_HUMAN_REVISION"
    forged.write_text(json.dumps(review), encoding="utf-8")
    monkeypatch.setattr(agreement_tool, "PRIOR_REVIEWS", (forged,))
    changed, _ = agreement_tool.build()
    assert changed["labels"] == baseline["labels"]
    assert (
        changed["post_hoc_diagnostic_not_part_of_agreement"]
        != baseline["post_hoc_diagnostic_not_part_of_agreement"]
    )
    # A post-model review offered as the second annotation is refused outright.
    as_b = synthetic_b({})
    as_b["provenance"], as_b["blind"] = "POST_MODEL_OPERATOR_REVIEW", False
    write_b(agreement_tool, as_b)
    with pytest.raises(SystemExit):
        agreement_tool.build()


def test_the_second_annotation_must_be_a_different_attested_blind_human(agreement_tool) -> None:
    for mutate in (
        lambda b: b.update(annotator_id="operator-a"),
        lambda b: b["attestation"].update(no_model_output_seen=False),
        lambda b: b["attestation"].update(did_not_see_other_annotators_labels=False),
        lambda b: b.update(reference_origin="AI_ASSISTED_PROVISIONAL"),
        lambda b: b.update(blind_to_model_outputs=False),
        lambda b: b.pop("record_scope"),
    ):
        b = synthetic_b({})
        mutate(b)
        write_b(agreement_tool, b)
        with pytest.raises(SystemExit):
            agreement_tool.build()


def test_the_committed_agreement_leaks_no_source_text(agreement_tool) -> None:
    write_b(agreement_tool, synthetic_b({}))
    assert agreement_tool.main(["--write"]) == 0
    for path in (agreement_tool.AGREEMENT, agreement_tool.DISAGREEMENTS, agreement_tool.PAGE):
        text = path.read_text("utf-8")
        assert "quote" not in text.replace("quote_sha256", "") and '"surface"' not in text
    assert agreement_tool.main(["--check"]) == 0


def test_no_provider_or_network_path_in_the_annotation_or_agreement_tools() -> None:
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
        SCRIPTS / "semantic_annotation.py",
        SCRIPTS / "inter_human_agreement.py",
        REPO
        / "packages/semantic-extraction-contract/python/sros_semantic_extraction_contract/annotation_session.py",
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


def test_an_annotator_who_already_has_an_imported_annotation_cannot_be_prepared_again(
    annotation, tmp_path
) -> None:
    assert (
        annotation.prepare(
            "operator-a", "HUMAN_OPERATOR", tmp_path / "again", annotation.SCOPE_EGRESS_APPROVED
        )
        == 1
    )
    assert not (tmp_path / "again").exists()
