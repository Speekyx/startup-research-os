"""Mission 1.85.11. The REPORTED_FAILED_ATTEMPT precision revision (prompt 1.1.0) and the next DEVELOPMENT packet.

No provider, no model, no database. Everything is read from the prompt modules and the committed artifacts.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest
from sros_semantic_extraction import prompt as current
from sros_semantic_extraction import prompt_v1_0_0 as historical
from sros_semantic_extraction.request import MAX_SCHEMA_RETRIES_PER_RECORD
from sros_semantic_extraction_contract.labels import LABEL_SET_ID, LABEL_SET_VERSION, LABELS

REPO = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO / "docs" / "data"
SCRIPTS = REPO / "infrastructure" / "scripts"
OLD_PROMPT_SHA256 = "53bcc87f0c761f28326bdbeda37e1018a5e2e3ff71711d9705c3542f940221b9"
OLD_PACKET_SHA256 = "5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e"
SPENT_APPROVAL_SHA256 = "77cdea89eba08f768b135e099478884d82b2120f8d0fab13e5f8f018b0b48d95"
FROZEN = {
    "stack-overflow-semantic-annotations-development-operator-a-v1.json": "449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c",
    "semantic-extraction-pilot-evaluation-development-v1.json": "da468421824e6d66b332057afc0e1873680c28d7c50350ba2be5dfd9192d35ba",
    "semantic-extraction-post-model-review-development-v1.json": "390caadaaaacd8dd45b11e6a1ce837de76c83449f767cf001a53b580f4caa093",
    "semantic-extraction-evaluation-packet-development-v1.json": "0fbc4357b457a3255b832c48fbf868567799b4fc2cda33105f28595895192983",
    "semantic-extraction-evaluation-approval-development-v1.json": SPENT_APPROVAL_SHA256,
    "semantic-extraction-request-size-development-v1.json": "96c7ad0bf3a7a7f7462359214f6c4f616c56019035f73ae87c75957ad8777fa4",
    "semantic-extraction-operator-decision-package-development-v1.json": "9001c4ecf1d65c366cbbf4ece3ae09a25454dede000db6e95f66f33485da0d0b",
}


def load(name: str):
    return json.loads((DATA / name).read_text("utf-8"))


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"rev_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PACKET = load("semantic-extraction-evaluation-packet-development-v2.json")
SPEC = load("semantic-extraction-rfa-regression-spec-development-v1.json")


def rfa_section(text: str) -> str:
    return text.split("REPORTED_FAILED_ATTEMPT\nThe asker", 1)[1].split(
        "\n\nNEGATIVE_EVALUATION_OF_NAMED_SOLUTION\n", 1
    )[0]


def test_the_old_prompt_is_frozen_and_the_new_one_is_a_new_version() -> None:
    assert historical.PROMPT_VERSION == "1.0.0"
    assert historical.prompt_sha256() == OLD_PROMPT_SHA256
    assert current.PROMPT_ID == historical.PROMPT_ID
    assert current.PROMPT_VERSION == "1.1.0"
    assert current.prompt_sha256() != OLD_PROMPT_SHA256
    assert PACKET["prompt"] == {
        "id": current.PROMPT_ID,
        "version": "1.1.0",
        "sha256": current.prompt_sha256(),
    }


def test_the_label_set_definition_is_unchanged() -> None:
    assert f"{LABEL_SET_ID}@{LABEL_SET_VERSION}" == "first-person-semantic-labels@1.0.0"
    rfa = next(label for label in LABELS if label.label_id == "REPORTED_FAILED_ATTEMPT")
    assert rfa.definition == (
        "The asker states, in their own words, that they tried a specific approach and it did not work: "
        "an error, a wrong result, or no effect. A question that only asks how to do something, with no "
        "attempt reported as failing, is not this label. A failed workaround is this label."
    )


def test_the_prompt_carries_the_three_anchor_procedure_and_the_guardrails() -> None:
    section = rfa_section(current.SYSTEM_INSTRUCTIONS)
    for anchor in ("A. ATTEMPT:", "B. FAILURE:", "C. LINK:"):
        assert anchor in section
    assert "only implied, or needs inference" in section
    assert "an error, log or stack trace with no stated attempt" in section
    assert "a description of the current state or environment" in section
    assert "using or having a tool, library or configuration" in section
    assert "wanting or asking how to do something" in section
    for pattern in (
        '"I am using X"',
        '"I have X configured"',
        '"My app gives error Y"',
        '"X behaves like Y"',
        '"How can I make X do Y?"',
        '"Why does X do Y?"',
    ):
        assert pattern in section
    assert "Error output may support FAILURE but never establishes ATTEMPT" in section
    assert "shows both the attempted action and its failure" in section
    assert "an error message or a code block alone is not enough" in section
    # The 1.0.0 invitation to use error output as the evidence is gone.
    assert (
        "The evidence may be error output inside a code block." not in current.SYSTEM_INSTRUCTIONS
    )


def test_everything_outside_the_rfa_section_is_byte_identical() -> None:
    old, new = historical.SYSTEM_INSTRUCTIONS, current.SYSTEM_INSTRUCTIONS
    assert (
        old.split("REPORTED_FAILED_ATTEMPT\nThe asker", 1)[0]
        == new.split("REPORTED_FAILED_ATTEMPT\nThe asker", 1)[0]
    )
    assert (
        old.split("\n\nNEGATIVE_EVALUATION_OF_NAMED_SOLUTION\n", 1)[1]
        == new.split("\n\nNEGATIVE_EVALUATION_OF_NAMED_SOLUTION\n", 1)[1]
    )
    assert historical.TASK_INSTRUCTIONS == current.TASK_INSTRUCTIONS
    neg = new.split("\n\nNEGATIVE_EVALUATION_OF_NAMED_SOLUTION\n", 1)[1].split(
        "\n\nWHAT NEVER COUNTS"
    )[0]
    assert "The named solution must appear verbatim in the text and is given as the subject." in neg
    assert "never code, logs or quoted material" in neg
    assert (
        "subject_quote and subject_occurrence are required for NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"
        in new
    )


def test_no_regression_record_leaks_into_the_prompt() -> None:
    prompt = current.SYSTEM_INSTRUCTIONS + current.TASK_INSTRUCTIONS
    review = load("semantic-extraction-post-model-review-development-v1.json")
    tokens = set()
    for record in review["records"]:
        tokens |= {
            record["normalized_record_id"],
            record["normalized_record_id"][:8],
            record["surface_sha256"][:12],
            record["model_findings_sha256"][:12],
        }
    for set_ in SPEC["sets"].values():
        for record in set_["records"]:
            tokens |= {record["normalized_record_id"][:8], record["surface_sha256"][:12]}
    assert not any(token in prompt for token in tokens)
    assert "misclassified" not in prompt.lower() and "previous run" not in prompt.lower()
    assert "Invented illustrations" in rfa_section(prompt)


def test_the_historical_artifacts_are_byte_for_byte_unchanged() -> None:
    for name, digest in FROZEN.items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest, name
    evaluator = load_script("evaluate_semantic_extraction_pilot")
    assert evaluator.dump(evaluator.evaluate()) == evaluator.EVALUATION.read_bytes()
    review = load_script("semantic_disagreement_review")
    assert review.check() == 0


def test_the_new_packet_is_a_new_digest_and_the_spent_approval_unlocks_nothing(tmp_path) -> None:
    runner = load_script("run_semantic_extraction_evaluation")
    packet = runner.verify_packet()
    assert packet["packet_version"] == 5
    assert packet["packet_sha256"] != OLD_PACKET_SHA256
    assert (
        packet["status"] == "READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL" and packet["blockers"] == []
    )
    assert packet["supersedes"]["packet_sha256"] == OLD_PACKET_SHA256
    assert packet["supersedes"]["approval_sha256"] == SPENT_APPROVAL_SHA256
    # Mission 1.85.12: the v5 approval names the new digest, never the old one.
    assert (
        json.loads(runner.APPROVAL.read_text("utf-8"))["packet_sha256"] == packet["packet_sha256"]
    )
    with pytest.raises(runner.Refused) as refused:
        runner.check_approval(packet, runner.HISTORICAL_APPROVAL, SPENT_APPROVAL_SHA256)
    assert refused.value.refusal == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"


def test_request_sizes_and_cost_use_the_revised_prompt() -> None:
    sizes = load("semantic-extraction-request-size-development-v2.json")
    old = load("semantic-extraction-request-size-development-v1.json")
    assert (
        sizes["prompt"]["version"] == "1.1.0"
        and sizes["prompt"]["sha256"] == current.prompt_sha256()
    )
    assert old["prompt"]["sha256"] == OLD_PROMPT_SHA256
    delta = {
        b["request_body_utf8_bytes"] - a["request_body_utf8_bytes"]
        for a, b in zip(old["records"], sizes["records"], strict=True)
    }
    assert len(delta) == 1 and delta.pop() > 0
    package = load("semantic-extraction-operator-decision-package-development-v2.json")
    assert (
        package["inputs"]["request_sizes_sha256"]
        == hashlib.sha256(
            (DATA / "semantic-extraction-request-size-development-v2.json").read_bytes()
        ).hexdigest()
    )
    bounds = PACKET["execution_bounds"]
    assert bounds["hard_ceiling_usd_approved"] == "9.000000" == bounds["proposed_hard_ceiling_usd"]
    assert bounds["EXPECTED_CALLS"] == 46 and bounds["max_calls"] == 46 * (
        1 + MAX_SCHEMA_RETRIES_PER_RECORD
    )
    from decimal import Decimal

    assert Decimal(bounds["retry_worst_case_usd"]) + Decimal(
        bounds["per_call_documented_maximum_usd"]
    ) <= Decimal("9.000000")
    assert (
        PACKET["operator_decisions"]["package_sha256"]
        == hashlib.sha256(
            (
                DATA / "semantic-extraction-operator-decision-package-development-v2.json"
            ).read_bytes()
        ).hexdigest()
    )


def test_the_regression_spec_is_offline_and_not_a_threshold() -> None:
    assert [r["normalized_record_id"] for r in SPEC["sets"]["KNOWN_OVERREAD"]["records"]] == sorted(
        d["normalized_record_id"]
        for d in load("semantic-extraction-post-model-review-development-v1.json")["decisions"]
    )
    assert len(SPEC["sets"]["POSITIVE_SENSITIVITY"]["records"]) == 15
    assert SPEC["is_threshold"] is False and SPEC["sent_to_provider"] is False
    assert (
        PACKET["development_diagnostics"]["rfa_regression_spec_sha256"]
        == hashlib.sha256(
            (DATA / "semantic-extraction-rfa-regression-spec-development-v1.json").read_bytes()
        ).hexdigest()
    )
    text = (DATA / "semantic-extraction-rfa-regression-spec-development-v1.json").read_text("utf-8")
    assert "quote" not in text.lower().replace("post-model", "")
    assert load_script("render_rfa_regression_spec").main(["--check"]) == 0


def test_the_next_packet_scope_is_unchanged_apart_from_the_prompt() -> None:
    old = load("semantic-extraction-evaluation-packet-development-v1.json")
    assert (
        PACKET["selection"]["egress_approved_record_ids"]
        == old["selection"]["egress_approved_record_ids"]
    )
    assert PACKET["selection"]["holdout_included"] is False
    assert PACKET["provider"]["model"] == old["provider"]["model"] == "claude-sonnet-5"
    assert PACKET["tool"] == old["tool"]
    assert PACKET["retry_policy"]["rule_sha256"] == old["retry_policy"]["rule_sha256"]
    assert PACKET["reference"]["REFERENCE_STRENGTH"] == "SINGLE_HUMAN_REFERENCE"
    assert PACKET["operator_decisions"]["additional_repeatability_runs_authorised"] == 0
    assert PACKET["operator_approval_recorded"] is False


def test_the_analysis_artifact_carries_counts_only() -> None:
    analysis = load("semantic-extraction-rfa-failure-mode-analysis-development-v1.json")
    assert set(analysis["groups"]) == {"OVERREAD", "MODEL_AGREED", "HUMAN_PRESENT"}
    assert analysis["groups"]["OVERREAD"]["records"] == 9
    audit = analysis["evidence_representation_audit"]
    assert audit["records_needing_a_window_over_quote_max"] == 0
    assert audit["spans_longer_than_quote_max"] == 0
    for group in analysis["groups"].values():
        assert all(isinstance(v, int) for v in group["features"].values())


def test_no_provider_call_is_reachable_from_these_checks(monkeypatch) -> None:
    from sros_llm_gateway import transport

    def no_transport(*args, **kwargs):
        raise AssertionError("a provider transport was built")

    monkeypatch.setattr(transport.UrllibTransport, "__init__", no_transport)
    runner = load_script("run_semantic_extraction_evaluation")
    assert runner.main([]) == 0
    assert load_script("render_semantic_extraction_packet").main(["--check"]) == 0
    assert load_script("render_semantic_extraction_decision_package").main(["--check"]) == 0
