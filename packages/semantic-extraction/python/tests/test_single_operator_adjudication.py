"""Mission 1.85.15. The single-operator adjudication protocol: delayed reread, adjudication, labelled reference.

No test reaches a provider, a model or the database. Surfaces are synthetic, committed outputs are redirected
to a temporary folder, and nothing is written to the repository.
"""

from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest
from sros_semantic_extraction_contract import single_operator_adjudication as soa

REPO = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO / "docs" / "data"
SCRIPTS = REPO / "infrastructure" / "scripts"
RFA, NEG = soa.REREAD_LABELS
ORIGINAL_SHA256 = "449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c"
LAST_EXPOSURE = "2026-09-18T23:57:02+04:00"
EARLIEST = "2026-09-19T23:57:02+04:00"


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"soa_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load(name: str):
    return json.loads((DATA / name).read_text("utf-8"))


ORIGINAL = load("stack-overflow-semantic-annotations-development-operator-a-v1.json")
APPROVED = set(
    load("stack-overflow-semantic-egress-eligibility-development-v1.json")["approved_record_ids"]
)


def synthetic(rid: str) -> str:
    return f"synthetic surface for {rid}"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def tool(tmp_path, monkeypatch):
    """The script with synthetic surfaces (a corpus copy whose digests match them) and outputs in tmp."""
    module = load_script("single_operator_adjudication")
    corpus = json.loads(module.CORPUS.read_text("utf-8"))
    for record in corpus["records"]:
        record["surface_sha256"] = digest(synthetic(record["normalized_record_id"]))
    (tmp_path / "corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
    monkeypatch.setattr(module, "CORPUS", tmp_path / "corpus.json")
    monkeypatch.setattr(module, "surfaces_for", lambda ids: {rid: synthetic(rid) for rid in ids})
    for name in ("REREAD", "REFERENCE", "REFERENCE_PAGE"):
        monkeypatch.setattr(module, name, tmp_path / getattr(module, name).name)
    return module


def synthetic_reread(changes: dict[tuple[str, str], str] | None = None) -> dict:
    """A committed reread that repeats the original states on the 46, except where `changes` says."""
    records = []
    for record in ORIGINAL["records"]:
        rid = record["normalized_record_id"]
        if rid not in APPROVED:
            continue
        cells = {}
        for label in soa.REREAD_LABELS:
            cell = copy.deepcopy(record["labels"][label])
            state = (changes or {}).get((rid, label), cell["state"])
            if state != cell["state"]:
                cell = {
                    "state": state,
                    "spans": [],
                    "subject": None,
                    "note_present": state == "UNCERTAIN",
                }
            cells[label] = cell
        records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": record["surface_sha256"],
                "labels": cells,
            }
        )
    return {
        "protocol": soa.PROTOCOL_ID,
        "reading": soa.READING,
        "split": "DEVELOPMENT",
        "operator_id": "operator-a",
        "record_scope": "DEVELOPMENT_EGRESS_APPROVED",
        "blind_to_previous_labels_at_reading": True,
        "blind_to_model_outputs": False,
        "is_a_second_annotator": False,
        "records": records,
    }


# -- history and the delay --------------------------------------------------------------------------------


def test_the_original_blind_annotation_is_unchanged_and_the_delay_is_derived(tool) -> None:
    assert (
        hashlib.sha256(
            (
                DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
            ).read_bytes()
        ).hexdigest()
        == ORIGINAL_SHA256
    )
    assert tool.last_exposure() == LAST_EXPOSURE
    assert soa.earliest_reread(LAST_EXPOSURE) == EARLIEST
    with pytest.raises(soa.AdjudicationRefusedError):
        soa.earliest_reread("2026-09-18T23:57:02")


# -- step 1: the reread -----------------------------------------------------------------------------------


def test_the_reread_pack_is_46_unlabelled_records_in_a_fresh_order_and_shows_nothing_else(
    tool, tmp_path
) -> None:
    out = tmp_path / "reread"
    assert tool.prepare_reread(out) == 0
    pack = json.loads((out / tool.PACK_NAME).read_text("utf-8"))
    assert {r["normalized_record_id"] for r in pack["records"]} == APPROVED and len(
        pack["records"]
    ) == 46
    assert all(set(r["labels"]) == set(soa.REREAD_LABELS) for r in pack["records"])
    assert all(c["state"] == "UNLABELLED" for r in pack["records"] for c in r["labels"].values())
    assert pack["earliest_permitted_start"] == EARLIEST
    original_order = [r["normalized_record_id"] for r in ORIGINAL["records"]]
    assert pack["record_order"] != sorted(APPROVED) and pack["record_order"] != [
        r for r in original_order if r in APPROVED
    ]
    text = json.dumps({k: v for k, v in pack.items() if k not in ("attestation", "$comment")})
    for token in (
        '"PRESENT"',
        '"ABSENT"',
        '"UNCERTAIN"',
        "OVERREAD",
        "UNDERREAD",
        "post_model",
        "finding",
        "quote_sha256",
        "spans",
    ):
        assert token not in text, token
    assert sorted(p.name for p in out.iterdir()) == [tool.PACK_NAME, "surfaces"]


def test_the_reread_refuses_to_start_before_the_minimum_delay(tool, tmp_path, monkeypatch) -> None:
    out = tmp_path / "reread"
    assert tool.prepare_reread(out) == 0
    for position, rid in enumerate(
        json.loads((out / tool.PACK_NAME).read_text("utf-8"))["record_order"], start=1
    ):
        (out / "surfaces" / f"{position:03d}-{rid}.txt").write_bytes(synthetic(rid).encode())
    asked: list[str] = []
    monkeypatch.setattr(builtins, "input", lambda prompt: asked.append(prompt) or "q")
    assert tool.reread(out / tool.PACK_NAME, clock=lambda: "2026-09-19T12:00:00+04:00") == 1
    assert asked == [], "nothing may be asked before the delay"
    assert tool.reread(out / tool.PACK_NAME, clock=lambda: "2026-09-20T09:00:00+04:00") == 0
    assert asked, "after the delay the form asks"


def complete_pack(tool, tmp_path) -> dict:
    out = tmp_path / "reread"
    tool.prepare_reread(out)
    pack = json.loads((out / tool.PACK_NAME).read_text("utf-8"))
    for record in pack["records"]:
        for cell in record["labels"].values():
            cell["state"] = "ABSENT"
    pack["annotation_started_at"] = "2026-09-20T09:00:00+04:00"
    pack["annotation_completed_at"] = "2026-09-20T10:00:00+04:00"
    pack["attestation"] = {
        "attested_at": "2026-09-20T10:00:00+04:00",
        **dict.fromkeys(soa.REREAD_ATTESTATION, True),
    }
    return pack


def validate(tool, pack):
    return soa.validate_reread_pack(
        pack,
        scope_record_ids=APPROVED,
        surfaces={rid: synthetic(rid) for rid in APPROVED},
        earliest=EARLIEST,
    )


def test_a_complete_reread_commits_as_a_same_operator_reading_not_blind_to_the_model(
    tool, tmp_path
) -> None:
    refusals, committed = validate(tool, complete_pack(tool, tmp_path))
    assert refusals == [] and committed is not None
    assert committed["is_a_second_annotator"] is False
    assert committed["blind_to_model_outputs"] is False
    assert committed["blind_to_previous_labels_at_reading"] is True
    assert committed["reading"] == "SAME_OPERATOR_DELAYED_REREAD"
    assert "quote" not in json.dumps(committed).replace("quote_sha256", "").replace(
        "quote_length", ""
    )


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (
            lambda p: p.update(annotation_started_at="2026-09-19T12:00:00+04:00"),
            "REREAD_STARTED_BEFORE_THE_MINIMUM_DELAY",
        ),
        (
            lambda p: p["attestation"].update(prior_model_exposure_acknowledged=False),
            "ATTESTATION_INCOMPLETE",
        ),
        (
            lambda p: p["attestation"].update(no_model_output_seen=True),
            "BLIND_ATTESTATION_NOT_PERMITTED",
        ),
        (lambda p: p["records"].pop(), "RECORD_SET_MISMATCH"),
        (lambda p: p["records"][0]["labels"][RFA].update(state="UNLABELLED"), "UNLABELLED_CELL"),
        (
            lambda p: p["records"][0]["labels"][RFA].update(state="UNCERTAIN"),
            "UNCERTAIN_WITHOUT_NOTE",
        ),
        (lambda p: p["records"][0]["labels"][RFA].update(state="PRESENT"), "PRESENT_WITHOUT_SPAN"),
    ],
)
def test_an_invalid_reread_is_refused_never_repaired(tool, tmp_path, mutate, code) -> None:
    pack = complete_pack(tool, tmp_path)
    mutate(pack)
    refusals, committed = validate(tool, pack)
    assert committed is None and code in {c for c, _ in refusals}


# -- step 2: what is adjudicated --------------------------------------------------------------------------


def test_only_disagreeing_or_uncertain_cells_are_adjudicated(tool) -> None:
    states, _ = tool.post_model_states()
    queue = soa.cells_to_adjudicate(ORIGINAL, synthetic_reread(), states)
    rfa = [q for q in queue if q["label_id"] == RFA]
    # A reread identical to the original leaves exactly the cells a post-model review contradicted (9 revised
    # to PRESENT and 1 to ABSENT in Mission 1.85.13) and the cells the original left UNCERTAIN.
    contradicted = [
        q for q in rfa if "POST_MODEL_REVIEW" in q["readings"] and "READINGS_DIFFER" in q["reasons"]
    ]
    assert len(contradicted) == 10
    uncertain = [q for q in queue if "UNCERTAIN_GIVEN" in q["reasons"]]
    assert {(q["normalized_record_id"][:8], q["label_id"]) for q in uncertain} == {
        ("5d0a1e34", RFA),
        ("db663e12", RFA),
        ("db663e12", NEG),
    }
    # The 7 Mission 1.85.10 over-reads and the 5 confirmed under-reads agree with the original: not adjudicated.
    assert len(queue) == 13


def test_a_reread_that_disagrees_adds_its_cell(tool) -> None:
    states, _ = tool.post_model_states()
    target = next(
        r["normalized_record_id"]
        for r in ORIGINAL["records"]
        if r["normalized_record_id"] in APPROVED and r["labels"][NEG]["state"] == "ABSENT"
    )
    queue = soa.cells_to_adjudicate(ORIGINAL, synthetic_reread({(target, NEG): "PRESENT"}), states)
    assert any(q["normalized_record_id"] == target and q["label_id"] == NEG for q in queue)


def adjudicate_all(tool, reread: dict, state: str = "ABSENT") -> list[dict]:
    states, _ = tool.post_model_states()
    return [
        soa.make_adjudication(
            item,
            final_state=state,
            note="my reason",
            spans=[],
            subject=None,
            decided_at="2026-09-21T09:00:00+04:00",
            operator_id="operator-a",
        )
        for item in soa.cells_to_adjudicate(ORIGINAL, reread, states)
    ]


def test_an_adjudication_needs_a_reason_and_a_span_for_present(tool) -> None:
    states, _ = tool.post_model_states()
    item = soa.cells_to_adjudicate(ORIGINAL, synthetic_reread(), states)[0]
    with pytest.raises(soa.AdjudicationRefusedError, match="NOTE_REQUIRED"):
        soa.make_adjudication(
            item,
            final_state="ABSENT",
            note=" ",
            spans=[],
            subject=None,
            decided_at="2026-09-21T09:00:00+04:00",
            operator_id="operator-a",
        )
    with pytest.raises(soa.AdjudicationRefusedError, match="PRESENT_WITHOUT_SPAN"):
        soa.make_adjudication(
            item,
            final_state="PRESENT",
            note="why",
            spans=[],
            subject=None,
            decided_at="2026-09-21T09:00:00+04:00",
            operator_id="operator-a",
        )
    with pytest.raises(soa.AdjudicationRefusedError, match="DECIDED_AT_NOT_TIMEZONE_AWARE"):
        soa.make_adjudication(
            item,
            final_state="ABSENT",
            note="why",
            spans=[],
            subject=None,
            decided_at="2026-09-21T09:00:00",
            operator_id="operator-a",
        )


def test_the_reference_is_complete_labelled_for_what_it_is_and_never_consensus(tool) -> None:
    reread = synthetic_reread()
    states, _ = tool.post_model_states()
    reference = soa.build_reference(ORIGINAL, reread, states, adjudicate_all(tool, reread))
    assert reference["reference_strength"] == "SINGLE_HUMAN_ADJUDICATED_REFERENCE"
    for key in (
        "is_consensus",
        "is_inter_human",
        "is_blind",
        "replaces_original_blind_annotation",
        "certification",
    ):
        assert reference[key] is False, key
    assert len(reference["records"]) == 46
    assert reference["cells_adjudicated"] == 13 and reference["cells_consistent"] == 46 * 2 - 13
    with pytest.raises(soa.AdjudicationRefusedError, match="ADJUDICATION_SET_MISMATCH"):
        soa.build_reference(ORIGINAL, reread, states, adjudicate_all(tool, reread)[1:])
    stale = adjudicate_all(tool, reread)
    stale[0]["readings"] = dict(stale[0]["readings"], DELAYED_REREAD="PRESENT")
    with pytest.raises(soa.AdjudicationRefusedError, match="STALE_ADJUDICATION"):
        soa.build_reference(ORIGINAL, reread, states, stale)


def test_intra_rater_agreement_is_never_inter_human(tool) -> None:
    result = soa.intra_rater_agreement(ORIGINAL, synthetic_reread())
    assert (
        result["kind"] == "INTRA_RATER_DELAYED_REREAD"
        and result["is_inter_human_reliability"] is False
    )
    assert result["labels"][RFA]["raw_agreement_three_state"] == 1.0


# -- committed artifacts and boundaries -------------------------------------------------------------------


def test_the_committed_reference_reproduces_and_carries_no_text(tool) -> None:
    reread = synthetic_reread()
    tool.REREAD.write_bytes(tool.dump(reread))
    assert tool.check() == 0
    doc, page = tool.render(adjudicate_all(tool, reread))
    tool.REFERENCE.write_bytes(tool.dump(doc))
    tool.REFERENCE_PAGE.write_bytes(page)
    assert tool.check() == 0
    text = tool.REFERENCE.read_text("utf-8")
    assert '"quote"' not in text and '"surface"' not in text
    tampered = json.loads(text)
    tampered["adjudications"][0]["final_state"] = "PRESENT"
    tool.REFERENCE.write_bytes(tool.dump(tampered))
    assert tool.check() == 1


def test_check_waits_and_refuses_a_reference_without_a_reread(tool) -> None:
    assert tool.check() == 0
    tool.REFERENCE.write_text("{}", encoding="utf-8")
    assert tool.check() == 1


def test_no_provider_or_network_path_on_the_protocol() -> None:
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
        SCRIPTS / "single_operator_adjudication.py",
        REPO
        / "packages/semantic-extraction-contract/python/sros_semantic_extraction_contract/single_operator_adjudication.py",
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
