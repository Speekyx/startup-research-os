"""Mission 1.85.3 (N08-A). The semantic extraction contract's labels map only to ontology that exists.

The contract names dimensions and observation categories as strings, so it does not depend on the
Opportunity engine. This test is where the two meet: an EXTRACTABLE label must name an existing dimension
and category, no label may reach willingness to pay or a solution gap, and the contract must not have
registered any new signal type mapping on the way past.
"""

from __future__ import annotations

import json
import pathlib

from sros_contracts import EvidenceObservationCategory
from sros_opportunity import EvidenceDimension
from sros_opportunity.mapping import SIGNAL_DIMENSION_MAP

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
CONTRACT = json.loads(
    (DATA / "first-person-semantic-extraction-contract-v1.json").read_text("utf-8")
)
ROADMAP = json.loads((DATA / "business-evidence-acquisition-roadmap-v1.json").read_text("utf-8"))
DIMENSIONS = {d.value for d in EvidenceDimension}
CATEGORIES = {c.value for c in EvidenceObservationCategory}


def test_every_named_dimension_and_category_exists() -> None:
    for label in CONTRACT["labels"]:
        if label["evidence_dimension"] is not None:
            assert label["evidence_dimension"] in DIMENSIONS, label["label_id"]
        if label["observation_category"] is not None:
            assert label["observation_category"] in CATEGORIES, label["label_id"]


def test_extractable_labels_map_to_existing_members_and_others_are_blocked() -> None:
    fits = {
        "SUPPORTED_BY_EXISTING_ONTOLOGY",
        "REQUIRES_TAXONOMY_EXTENSION",
        "REQUIRES_SCOPE_DECISION",
        "NOT_SAFE_TO_REPRESENT",
    }
    for label in CONTRACT["labels"]:
        assert label["ontology_fit"] in fits
        if label["status"] == "EXTRACTABLE":
            assert label["ontology_fit"] == "SUPPORTED_BY_EXISTING_ONTOLOGY"
            assert label["evidence_dimension"] in DIMENSIONS
            assert label["observation_category"] in {"REPORTED_BEHAVIOUR", "STATED_OPINION"}
        else:
            assert label["blocker"], label["label_id"]


def test_no_label_reaches_commercial_or_gap_dimensions() -> None:
    for label in CONTRACT["labels"]:
        assert label["evidence_dimension"] not in {
            "WILLINGNESS_TO_PAY",
            "SOLUTION_GAP",
            "MARKET_ACTIVITY",
        }
        assert label["observation_category"] not in {"MARKET_ACTIVITY", "DIRECT_VALIDATION"}


def test_no_signal_type_was_registered_for_semantic_findings() -> None:
    for signal_type in SIGNAL_DIMENSION_MAP:
        assert "semantic" not in str(signal_type).lower()
        assert "finding" not in str(signal_type).lower()


def test_roadmap_records_n08_as_preregistered_not_done() -> None:
    nodes = {n["id"]: n for n in ROADMAP["nodes"]}
    assert nodes["N08"]["status"] in {
        CONTRACT["outcome"],
        "EVALUATION_TOOLING_READY_HUMAN_LABELS_AND_EGRESS_REVIEW_PENDING",
        "SINGLE_HUMAN_REFERENCE_RECORDED_OPERATOR_DECISIONS_PENDING",
        "DEVELOPMENT_PILOT_SINGLE_HUMAN_REFERENCE",
        "EGRESS_REVIEW_COMPLETE_OPERATOR_DECISIONS_REMAIN",
        "FINAL_OPERATOR_DECISIONS_PREPARED",
        "READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL",
        "DEVELOPMENT_PILOT_EXECUTED_PARTIAL_RESULTS_READY_FOR_OPERATOR_REVIEW",
        "WAITING_FOR_POST_MODEL_OPERATOR_REVIEW",
        "POST_MODEL_DISAGREEMENT_REVIEW_COMPLETE",
        "PROMPT_1_1_DEVELOPMENT_PILOT_RESULTS_READY_FOR_OPERATOR_REVIEW",
        "WAITING_FOR_PROMPT_1_1_BALANCED_OPERATOR_REVIEW",
        "PROMPT_1_1_BALANCED_OPERATOR_REVIEW_COMPLETE",
    }
    assert nodes["N08"]["phases"]["N08-A"].startswith(CONTRACT["outcome"])
    assert nodes["N08"]["status"] != "DONE"
    assert nodes["N05"]["status"] == "DONE"
    assert nodes["N02"]["mission"] is None
    assert "status" not in nodes["N06"]
