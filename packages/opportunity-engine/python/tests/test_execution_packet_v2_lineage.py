"""Mission 1.84.6. Four historical gates recorded that THEIR mission created no execution packet V2.

Each was re-pointed from "no V2 file exists" to "any V2 file names a later mission as its author",
because a check pinned to an absence pins the repository's future to one mission's verdict. These
tests hold both halves: a later mission's V2 is accepted, and a V2 claiming the historical mission,
an earlier one or nobody is refused, through the helper and through the whole `validate()`.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

GATES = (
    ("render_claude_subscription_route_feasibility.py", (1, 84, 1)),
    ("render_second_opportunity_output_capacity.py", (1, 84, 3)),
    ("render_second_opportunity_bounded_contract.py", (1, 84, 4)),
    ("render_second_opportunity_token_measurement.py", (1, 84, 5)),
)


def _load(filename: str):
    spec = importlib.util.spec_from_file_location(f"lineage_{filename[:-3]}", SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", params=GATES, ids=[name for name, _ in GATES])
def gate(request):
    filename, mission = request.param
    return _load(filename), mission


def _v2(tmp_path, monkeypatch, module, content: str) -> None:
    path = tmp_path / "second-opportunity-synthesis-execution-packet-v2.json"
    path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(module, "PACKET_V2", path)


def _mission(mission: tuple[int, ...]) -> str:
    return "mission-" + ".".join(str(part) for part in mission)


def test_each_gate_names_its_own_mission(gate) -> None:
    module, mission = gate
    assert mission == module.THIS_MISSION


def test_a_later_missions_v2_is_that_missions(gate, tmp_path, monkeypatch) -> None:
    module, _ = gate
    _v2(tmp_path, monkeypatch, module, json.dumps({"prepared_by": "mission-1.84.6"}))
    assert module._v2_prepared_by_a_later_mission() is True


@pytest.mark.parametrize(
    "prepared_by",
    ["THIS", "mission-1.84", "mission-1.84.0", None, "someone", "mission-", "mission-1.x", 1846],
)
def test_a_v2_claiming_this_an_earlier_or_no_mission_is_not(
    gate, tmp_path, monkeypatch, prepared_by
) -> None:
    module, mission = gate
    value = _mission(mission) if prepared_by == "THIS" else prepared_by
    _v2(tmp_path, monkeypatch, module, json.dumps({"prepared_by": value}))
    assert module._v2_prepared_by_a_later_mission() is False


@pytest.mark.parametrize("content", ["[]", "{not json", '"a string"', ""])
def test_a_malformed_v2_is_nobodys(gate, tmp_path, monkeypatch, content) -> None:
    module, _ = gate
    _v2(tmp_path, monkeypatch, module, content)
    assert module._v2_prepared_by_a_later_mission() is False


def test_validate_refuses_a_v2_claiming_the_historical_mission(gate, tmp_path, monkeypatch) -> None:
    module, mission = gate
    _v2(tmp_path, monkeypatch, module, json.dumps({"prepared_by": _mission(mission)}))
    with pytest.raises(module.ValidationError, match="V2"):
        module.validate()


def test_validate_accepts_a_v2_a_later_mission_prepared(gate, tmp_path, monkeypatch) -> None:
    module, _ = gate
    _v2(tmp_path, monkeypatch, module, json.dumps({"prepared_by": "mission-1.84.6"}))
    module.validate()
