"""Mission 1.84.26, CI gate 103. The semantic output gate v1.5.0: D1 and D2, and nothing else moved.

Mission 1.84.25 established two ways in which gate v1.4.0 reads a word as ASSERTED that its own policy
does not assert, and the operator authorised exactly two repairs: D1, a noun list governed by one
leading denial or uncertainty keeps that scope; D2, a gated modifier inside an explicitly denied subject
noun phrase is not asserted. This gate makes the successor checkable, and derives every field of its
record from the live code:

* **frozen, beside history.** Gate v1.4.0 (gate 87), v1.3.0 (gate 77) and v1.2.0 (gate 75), which holds
  the clause reader, still recompute to their pinned digests, and gate 102's diagnosis is byte for
  byte the merged one. The v1.5.0 implementation and its frozen test file are pinned here.
* **re-bound, not rewritten.** Every v1.5.0 audit function is v1.3.0's syntax tree with only its declared
  renames, the evaluator is gate v1.3.0's with only its declared renames, and every helper that is not
  re-bound is v1.3.0's object. The successor's reading loop over v1.2.0's own splitter and state reader
  reproduces v1.3.0's `classify` on every sentence the matrix and the sweep read.
* **the differential.** A 130-case matrix, the 39 cases of gate 102 and 91 more, runs through both gates.
  Each divergence is attributed by reading the sentence with D1 alone and with D2 alone: a divergence
  neither explains fails the gate, as does any occurrence the successor reads as ASSERTED that v1.4.0
  did not, and any case the policy refuses that v1.5.0 passes. The authorised divergence set is pinned.
* **the sweep.** Every sentence of the frozen gate test files and the census fixtures is read by both
  readers: every changed reading must be ASSERTED to not asserted, and attributable to D1 or D2.
* **V9 and V10, diagnostically.** Gate v1.4.0 still reproduces the reasons each execution retained, and
  their records are untouched. What gate v1.5.0 would say is recorded beside them: V10 loses its
  `software` refusal and keeps `market`, so it is no candidate for review or persistence.

Nothing here calls a model, builds a transport, reads the database or writes outside this record.

    uv run python infrastructure/scripts/render_second_opportunity_semantic_gate_v1_5.py --check
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
import urllib.request
from collections.abc import Callable, Iterator, Sequence
from typing import Any, NamedTuple

from sros_opportunity import assertion_audit_v1_3 as audit_v1_3
from sros_opportunity import assertion_audit_v1_5 as audit_v1_5
from sros_opportunity import assertion_scope_v1_5 as scope
from sros_opportunity.assertion_context import SCORE_TERMS
from sros_opportunity.guards import FORBIDDEN_TERMS, _sentences
from sros_opportunity.lexical_inflection import inflection_spans
from sros_opportunity.second_opportunity import PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS
from sros_opportunity.second_opportunity_gate_v1_2 import (
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
    build_trusted_context,
)
from sros_opportunity.second_opportunity_gate_v1_4 import (
    COMPONENT_VERSIONS_V1_4,
    evaluate_second_opportunity_output_v1_4,
)
from sros_opportunity.second_opportunity_gate_v1_5 import (
    CHANGED_COMPONENTS,
    COMPONENT_VERSIONS_V1_5,
    OPERATOR_DECISION_V1_5,
    PREDECESSOR_GATE_VERSION,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_5,
    evaluate_second_opportunity_output_v1_5,
)
from sros_opportunity.support_origin import build_typed_support_universe

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-output-gate-v1.5-freeze-v1.json"
RECORD_MD = DATA / "second-opportunity-output-gate-v1.5-freeze-v1.md"
PACKAGE = "packages/opportunity-engine/python/sros_opportunity"
TESTS = "packages/opportunity-engine/python/tests"
FIXTURE = ROOT / TESTS / "test_semantic_gate_v1_3.py"

MISSION = "mission-1.84.26"
START_COMMIT = "5b6417f71318e660436668b62a8039fb3490d19a"
BRANCH = "sprint-1/mission-1.84.26"
PRIMARY_OUTCOME = "SEMANTIC_GATE_V1_5_0_D1_D2_IMPLEMENTED_DIVERGENCE_LIMITED_TO_AUTHORISED_REPAIRS"

SUCCESSOR_MODULES = (
    f"{PACKAGE}/assertion_scope_v1_5.py",
    f"{PACKAGE}/assertion_audit_v1_5.py",
    f"{PACKAGE}/second_opportunity_gate_v1_5.py",
)
IMPLEMENTATION_FILES = (
    f"{PACKAGE}/lexical_inflection.py",
    f"{PACKAGE}/support_origin.py",
    f"{PACKAGE}/assertion_context.py",
    f"{PACKAGE}/assertion_audit_v1_3.py",
    f"{PACKAGE}/second_opportunity_gate_v1_3.py",
    f"{PACKAGE}/second_opportunity_schema_v1_2.py",
    f"{PACKAGE}/second_opportunity_gate_v1_4.py",
    *SUCCESSOR_MODULES,
)
TEST_FILE = f"{TESTS}/test_semantic_gate_v1_5.py"

#: Pinned at the freeze. Editing either is re-freezing, and re-freezing is a new gate version.
FROZEN_IMPLEMENTATION_SHA256 = "b188ba4c2cfee92fe56d4bda376d69f280e63a39efde13b4c80e14d96975d7df"
FROZEN_TEST_SHA256 = "f45344d9636fa1132c9f69a08ae90c5cb42ca71659846fa81d80362b858eebf7"

#: The predecessors as their own gates froze them, and gate 102's diagnosis as it was merged.
PREDECESSOR_DIGESTS: dict[str, tuple[str, str]] = {
    "gate_75_v1_2_0": (
        "render_second_opportunity_semantic_gate_v1_2.py",
        "47bbcb459b0b69153d23c7dcc7f273e0e47d0b84a72522d25f773cd462db82b0",
    ),
    "gate_77_v1_3_0": (
        "render_second_opportunity_semantic_gate_v1_3.py",
        "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3",
    ),
    "gate_87_v1_4_0": (
        "render_second_opportunity_semantic_gate_v1_4.py",
        "eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb",
    ),
}
CLAUSE_READER_SHA256 = "3afcffc210393400241b7ed5b818d4caab615e882c30cf6c7b2495eee2c3081b"
DIAGNOSIS_FILES: dict[str, str] = {
    "docs/data/second-opportunity-stage6-diagnostic-v10.json": (
        "dfc9fde4fd104a01e61f085d3b58360426fa993db4a333048bb5c8fe757ee1da"
    ),
    "docs/data/second-opportunity-stage6-diagnostic-v10.md": (
        "bbd267d84095d92afc9b1386190c47c2596a653ae8c0b985332b8bf47d75c9f2"
    ),
    "infrastructure/scripts/render_second_opportunity_stage6_diagnostic_v10.py": (
        "1862a75f56670325a92f7cdb7ae3a2328184e9284ceeb53a95cd97feb771790a"
    ),
}

INVARIANTS: dict[str, object] = {
    "PROVIDER_CALLS": 0,
    "MODEL_INFERENCES": 0,
    "TOKEN_COUNTS": 0,
    "RETRIES": 0,
    "PERSISTENCE": 0,
    "NEW_EXECUTION_PACKET": "NO",
    "V11_CREATION": "NO",
    "OPPORTUNITY_2_CREATION": "NO",
    "V10_OUTCOME": "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY",
    "GATE_V1_4_0_IMMUTABLE": True,
    "V10_RESPONSE_REWRITTEN": False,
    "HISTORICAL_V1_TO_V10_ARTIFACTS_EDITED": False,
}
NOT_CHANGED: dict[str, bool] = {
    "OUTPUT_SCHEMA_CHANGED": False,
    "PROMPT_V1_6_0_CHANGED": False,
    "PROMPT_V1_7_0_CREATED": False,
    "STRICT_TOOL_USE_CHANGED": False,
    "CANDIDATE_INTERVENTION_CLASS_CHANGED": False,
    "EVIDENCE_DIMENSION_BROADENED": False,
    "MARKET_ACTIVITY_LICENCE_BROADENED": False,
    "FORBIDDEN_CONCEPT_REMOVED_OR_WEAKENED": False,
    "DISJUNCTION_RULE_CHANGED": False,
    "REQUEST_OR_UNCERTAINTY_SHAPE_CHANGED": False,
    "NLP_DEPENDENCY_ADDED": False,
    "LLM_IN_THE_GATE": False,
    "D3_D4_D5_IMPLEMENTED": False,
}

#: Read locally, read-only, during this mission (the research database; CI holds none).
CANONICAL_COUNTERS_OBSERVED: dict[str, object] = {
    "raw_records": 325,
    "normalized_records": 325,
    "signals": 60,
    "claims": 91,
    "claim_revisions": 92,
    "evidence": 112,
    "reliability_assessments": 4,
    "evidence_independence_groups": 0,
    "opportunities": 1,
    "opportunity_hypothesis_revisions": 2,
    "opportunity_hypothesis_evidence": 14,
    "embedding_provenance": 0,
    "scores": "absent",
    "source_policy_reviews": 71,
}

GATED: tuple[str, ...] = tuple(
    sorted(
        {
            *PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
            *(p for c in FORBIDDEN_CONCEPTS_V1_2 for p in c.phrases),
            *FORBIDDEN_TERMS,
            *SCORE_TERMS,
        }
    )
)


class ValidationError(RuntimeError):
    """The freeze record disagrees with the live code, or with what the operator authorised."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(relative: str) -> str:
    return _sha((ROOT / relative).read_bytes())


def implementation_sha256() -> str:
    """One digest over the implementation files, path and bytes, in a fixed order (gate 77's rule)."""
    return _sha("".join(f"{p}\x00{file_sha(p)}\n" for p in IMPLEMENTATION_FILES).encode("utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    if not path.exists():
        raise ValidationError(f"{path.name} is missing")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G76 = _module("gate_76_for_gate_103", SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py")
G98 = _module("gate_98_for_gate_103", SCRIPTS / "render_second_opportunity_execution_record_v9.py")
G101 = _module(
    "gate_101_for_gate_103", SCRIPTS / "render_second_opportunity_execution_record_v10.py"
)


@contextlib.contextmanager
def no_network() -> Iterator[None]:
    """Gate 76's transport tripwire, and one on urlopen."""
    original = urllib.request.urlopen

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("gate 103 reached urlopen")

    urllib.request.urlopen = refuse  # type: ignore[assignment]
    try:
        with G76.no_transport():
            yield
    finally:
        urllib.request.urlopen = original


# --------------------------------------------------------------------------- the matrix

A, B, N = "REPAIR_A_SCOPED_LIST", "REPAIR_B_DENIED_SUBJECT_MODIFIER", "NONE"


class Case(NamedTuple):
    case_id: str
    group: str
    sentence: str
    phrase: str
    intended: str  # REFUSE | PASS, in the field under test, from the policy
    divergence_class: str  # NONE, or the repair that would move v1.4.0's verdict


#: Mission 1.84.25's 39 cases verbatim, and 91 more, every intended verdict derived from the policy and
#: the operator's decisions, never from how any execution would fare.
CASES: tuple[Case, ...] = tuple(
    Case(*row)
    for row in (
        ("A1", "ASSERTED_CONTROL", "Software gap is established.", "software", "REFUSE", N),
        ("A2", "ASSERTED_CONTROL", "The buyers need software.", "software", "REFUSE", N),
        (
            "A3",
            "ASSERTED_CONTROL",
            "A software gap exists, and it is not established by these statements.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "A4",
            "ASSERTED_CONTROL",
            "Buyers use software; this is not established by these statements.",
            "software",
            "REFUSE",
            N,
        ),
        ("A5", "ASSERTED_CONTROL", "A market exists for this.", "market", "REFUSE", N),
        (
            "A6",
            "ASSERTED_CONTROL",
            "The class is a market-analysis service.",
            "market",
            "REFUSE",
            N,
        ),
        ("A7", "ASSERTED_CONTROL", "There is an underserved segment.", "underserved", "REFUSE", N),
        (
            "A8",
            "ASSERTED_CONTROL",
            "A software gap is not established, but it probably exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "A9",
            "ASSERTED_CONTROL",
            "Software is not established, but it probably exists.",
            "software",
            "REFUSE",
            N,
        ),
        ("S1", "SCOPED_CONTROL", "Software is not established.", "software", "PASS", N),
        ("S2", "SCOPED_CONTROL", "No software gap is established.", "software", "PASS", N),
        ("S3", "SCOPED_CONTROL", "A gap in software is not established.", "software", "PASS", N),
        (
            "S4",
            "SCOPED_CONTROL",
            "Whether a software gap exists is unknown.",
            "software",
            "PASS",
            N,
        ),
        (
            "S5",
            "SCOPED_CONTROL",
            "Whether this reflects a software gap is not established.",
            "software",
            "PASS",
            N,
        ),
        ("S6", "SCOPED_CONTROL", "Whether software exists is unknown.", "software", "PASS", N),
        (
            "S7",
            "SCOPED_CONTROL",
            "Whether dissatisfaction exists is unknown.",
            "dissatisfaction",
            "PASS",
            N,
        ),
        (
            "S8",
            "SCOPED_CONTROL",
            "No evidence establishes a need, problem, or software gap.",
            "software",
            "PASS",
            N,
        ),
        (
            "S9",
            "SCOPED_CONTROL",
            "It is not established whether this reflects a need, problem, or software gap.",
            "software",
            "PASS",
            N,
        ),
        (
            "S10",
            "SCOPED_CONTROL",
            "The packet does not establish need, gap or willingness to pay.",
            "willingness to pay",
            "PASS",
            N,
        ),
        (
            "S11",
            "SCOPED_CONTROL",
            "No statement establishes a market for this.",
            "market",
            "PASS",
            N,
        ),
        ("S12", "SCOPED_CONTROL", "The market is not established.", "market", "PASS", N),
        (
            "S13",
            "SCOPED_CONTROL",
            "None of the notices show that a software gap exists.",
            "software",
            "PASS",
            N,
        ),
        (
            "L1",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or software exists is unknown.",
            "software",
            "PASS",
            A,
        ),
        (
            "L2",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or dissatisfaction exists is unknown.",
            "dissatisfaction",
            "PASS",
            A,
        ),
        (
            "L3",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or software gap is not established.",
            "software",
            "PASS",
            A,
        ),
        (
            "L4",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem or software gap is not established.",
            "software",
            "PASS",
            A,
        ),
        (
            "L5",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need or software gap is not established.",
            "software",
            "PASS",
            A,
        ),
        (
            "L6",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or software gap is unknown.",
            "software",
            "PASS",
            A,
        ),
        (
            "L7",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or dissatisfaction remains to be seen.",
            "dissatisfaction",
            "PASS",
            A,
        ),
        (
            "L8",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or underserved segment is not established.",
            "underserved",
            "PASS",
            A,
        ),
        (
            "L9",
            "LIST_UNDER_ONE_SCOPE",
            "None of the notices show that a need, problem, or software gap exists.",
            "software",
            "PASS",
            A,
        ),
        (
            "L10",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or competitor weakness is not established.",
            "competitor",
            "PASS",
            A,
        ),
        (
            "L11",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or software is not established.",
            "software",
            "PASS",
            N,
        ),
        (
            "L12",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or market is not established.",
            "market",
            "PASS",
            N,
        ),
        (
            "L13",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or a gap in software is not established.",
            "software",
            "PASS",
            N,
        ),
        (
            "L14",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or any underlying software gap is not established.",
            "software",
            "PASS",
            N,
        ),
        (
            "M1",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Software gap is not established.",
            "software",
            "PASS",
            B,
        ),
        (
            "M2",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Market gap is not established.",
            "market",
            "PASS",
            B,
        ),
        (
            "M3",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Underserved segment is not established.",
            "underserved",
            "PASS",
            B,
        ),
        (
            "N1",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need and software exist is unknown.",
            "software",
            "PASS",
            A,
        ),
        (
            "N2",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or software gap exists is unknown.",
            "software",
            "PASS",
            A,
        ),
        (
            "N3",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or market demand exists is unknown.",
            "market demand",
            "PASS",
            A,
        ),
        (
            "N4",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or willingness to pay exists is unknown.",
            "willingness to pay",
            "PASS",
            A,
        ),
        (
            "N5",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or market size exists is unknown.",
            "market size",
            "PASS",
            A,
        ),
        (
            "N7",
            "LIST_UNDER_ONE_SCOPE",
            "It is unclear whether a need or software gap exists.",
            "software",
            "PASS",
            A,
        ),
        (
            "N8",
            "LIST_UNDER_ONE_SCOPE",
            "It is unknown whether a need, problem or underserved segment exists.",
            "underserved",
            "PASS",
            A,
        ),
        (
            "N9",
            "LIST_UNDER_ONE_SCOPE",
            "It is not established that a need, problem, or software gap exists.",
            "software",
            "PASS",
            A,
        ),
        (
            "N10",
            "LIST_UNDER_ONE_SCOPE",
            "No evidence shows that a need or software gap exists.",
            "software",
            "PASS",
            A,
        ),
        (
            "N11",
            "LIST_UNDER_ONE_SCOPE",
            "The notices never show that a need or software gap exists.",
            "software",
            "PASS",
            A,
        ),
        (
            "N12",
            "LIST_UNDER_ONE_SCOPE",
            "The packet does not establish that a need or competitor weakness exists.",
            "competitor weakness",
            "PASS",
            A,
        ),
        (
            "N13",
            "LIST_UNDER_ONE_SCOPE",
            "The notices cannot show that a need or dissatisfaction exists.",
            "dissatisfaction",
            "PASS",
            A,
        ),
        (
            "N14",
            "LIST_UNDER_ONE_SCOPE",
            "None of the notices show that a need or underserved segment exists.",
            "underserved",
            "PASS",
            A,
        ),
        (
            "N15",
            "LIST_UNDER_ONE_SCOPE",
            "Whether this reflects a need, problem, or market demand remains to be seen.",
            "market demand",
            "PASS",
            A,
        ),
        (
            "N40",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or software remains to be seen.",
            "software",
            "PASS",
            A,
        ),
        (
            "N96",
            "LIST_UNDER_ONE_SCOPE",
            "No evidence establishes a need or software gap exists.",
            "software",
            "PASS",
            A,
        ),
        (
            "N97",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a notice review or software tool is suitable is unknown.",
            "software",
            "PASS",
            A,
        ),
        (
            "N16",
            "LIST_UNDER_ONE_SCOPE",
            "No evidence establishes that a need, or software gap, exists.",
            "software",
            "PASS",
            N,
        ),
        (
            "N17",
            "LIST_UNDER_ONE_SCOPE",
            "No evidence establishes a need or willingness to pay.",
            "willingness to pay",
            "PASS",
            N,
        ),
        (
            "N18",
            "LIST_UNDER_ONE_SCOPE",
            "Whether a need or a gap in software supply exists is unknown.",
            "software",
            "PASS",
            N,
        ),
        (
            "N21",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Software demand is not established.",
            "software",
            "PASS",
            B,
        ),
        (
            "N22",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Market size is not established.",
            "market",
            "PASS",
            B,
        ),
        (
            "N23",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Competitor weakness is not established.",
            "competitor",
            "PASS",
            B,
        ),
        (
            "N24",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Underserved buyers are not established.",
            "underserved",
            "PASS",
            B,
        ),
        (
            "N25",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Customer willingness to pay is not established.",
            "customer",
            "PASS",
            B,
        ),
        (
            "N26",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "The software gap is unknown.",
            "software",
            "PASS",
            B,
        ),
        (
            "N27",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "A software gap cannot be established from these notices.",
            "software",
            "PASS",
            B,
        ),
        (
            "N28",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Software supply does not appear in these statements.",
            "software",
            "PASS",
            B,
        ),
        (
            "N30",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "A gap in software supply is not established.",
            "software",
            "PASS",
            B,
        ),
        (
            "N98",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Whether a need exists is unknown; underserved segment is not established.",
            "underserved",
            "PASS",
            B,
        ),
        (
            "N101",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Market demand is not established.",
            "market",
            "PASS",
            B,
        ),
        (
            "N29",
            "PREMODIFIER_OF_A_DENIED_SUBJECT",
            "Market activity has never been measured here.",
            "market",
            "PASS",
            N,
        ),
        (
            "N34",
            "SCOPED_CONTROL",
            "Dissatisfaction is not established.",
            "dissatisfaction",
            "PASS",
            N,
        ),
        ("N42", "ASSERTED_CONTROL", "Buyers show dissatisfaction.", "dissatisfaction", "REFUSE", N),
        ("N43", "ASSERTED_CONTROL", "The segment is underserved.", "underserved", "REFUSE", N),
        ("N44", "ASSERTED_CONTROL", "Buyers are willing to pay.", "willing to pay", "REFUSE", N),
        (
            "N46",
            "ASSERTED_CONTROL",
            "Competitor weakness is evident.",
            "competitor weakness",
            "REFUSE",
            N,
        ),
        (
            "N31",
            "CONTRASTIVE_CONTINUATION",
            "Software gap is not established, but this requires evidence.",
            "software",
            "PASS",
            B,
        ),
        (
            "N32",
            "CONTRASTIVE_CONTINUATION",
            "Software gap is not established, however it needs to be tested.",
            "software",
            "PASS",
            B,
        ),
        (
            "N33",
            "CONTRASTIVE_CONTINUATION",
            "Software gap is not established; it remains unknown.",
            "software",
            "PASS",
            B,
        ),
        (
            "N49",
            "CONTRASTIVE_CONTINUATION",
            "Software gap is not established, but software demand probably exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N50",
            "CONTRASTIVE_CONTINUATION",
            "No evidence establishes software demand, but buyers are willing to pay.",
            "willing to pay",
            "REFUSE",
            N,
        ),
        (
            "N51",
            "CONTRASTIVE_CONTINUATION",
            "Software gap is not established, but the market clearly needs a solution.",
            "market",
            "REFUSE",
            N,
        ),
        (
            "N52",
            "CONTRASTIVE_CONTINUATION",
            "Software gap is not established, but it probably exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N53",
            "CONTRASTIVE_CONTINUATION",
            "Software gap is not established yet is probably large.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N55",
            "CONTRASTIVE_CONTINUATION",
            "Whether a need or software exists is unknown, but it probably exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N56",
            "CONTRASTIVE_CONTINUATION",
            "Whether a need or software gap exists is unknown, however it is clearly large.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N57",
            "CONTRASTIVE_CONTINUATION",
            "Market size is not established, yet it is probably large.",
            "market",
            "REFUSE",
            N,
        ),
        (
            "N58",
            "COORDINATED_PREDICATE",
            "Software gap is not established and is probably large.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N59",
            "COORDINATED_PREDICATE",
            "Software is not established and is probably large.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N60",
            "COORDINATED_PREDICATE",
            "Whether a need or software exists is unknown and is probably large.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N62",
            "COORDINATED_PREDICATE",
            "Software gap is not established and needs to be tested.",
            "software",
            "PASS",
            B,
        ),
        (
            "N63",
            "GENUINE_NEW_SUBJECT",
            "No evidence establishes software demand, and buyers are willing to pay.",
            "willing to pay",
            "REFUSE",
            N,
        ),
        (
            "N64",
            "GENUINE_NEW_SUBJECT",
            "No evidence establishes a need, and software gap exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N65",
            "GENUINE_NEW_SUBJECT",
            "No evidence establishes a need, or software gap exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N66",
            "GENUINE_NEW_SUBJECT",
            "Whether a need exists or software is sold is unknown.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N67",
            "GENUINE_NEW_SUBJECT",
            "Whether buyers need a tool or software is sold is unknown.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N68",
            "GENUINE_NEW_SUBJECT",
            "Software gap is not established, and market demand exists.",
            "market demand",
            "REFUSE",
            N,
        ),
        (
            "N69",
            "GENUINE_NEW_SUBJECT",
            "Whether a need exists is unknown, and software supply is growing.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N99",
            "GENUINE_NEW_SUBJECT",
            "Software gap is not established, and buyers are willing to pay.",
            "willing to pay",
            "REFUSE",
            N,
        ),
        (
            "N100",
            "GENUINE_NEW_SUBJECT",
            "Whether a need or software gap exists is unknown, and buyers are willing to pay.",
            "willing to pay",
            "REFUSE",
            N,
        ),
        (
            "N71",
            "PRONOUN_SUBJECT",
            "Software is not established, and it is probably large.",
            "software",
            "PASS",
            N,
        ),
        (
            "N103",
            "PRONOUN_SUBJECT",
            "Software is not established and it is probably large.",
            "software",
            "PASS",
            N,
        ),
        (
            "N72",
            "PRONOUN_SUBJECT",
            "Whether a need or software exists is unknown, and it is probably large.",
            "software",
            "PASS",
            A,
        ),
        (
            "N73",
            "PRONOUN_SUBJECT",
            "Software gap is not established, and they are probably large.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N76",
            "PRONOUN_SUBJECT",
            "Software gap is not established, and it is not measured.",
            "software",
            "PASS",
            B,
        ),
        (
            "N74",
            "PRONOUN_SUBJECT",
            "No evidence establishes a need, and it is probably software.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N77",
            "RELATIVE_OR_NESTED",
            "The software gap, which buyers report, is not established.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N78",
            "RELATIVE_OR_NESTED",
            "The software gap that buyers report is not established.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N80",
            "RELATIVE_OR_NESTED",
            "Whether a need exists, which software would meet, is unknown.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N81",
            "RELATIVE_OR_NESTED",
            "A need, which is not a software gap, is not established.",
            "software",
            "PASS",
            N,
        ),
        (
            "N83",
            "MALICIOUS_NEAR_MATCH",
            "Software gap is not established; software demand exists.",
            "software demand",
            "REFUSE",
            N,
        ),
        (
            "N84",
            "MALICIOUS_NEAR_MATCH",
            "Software gap and market demand are not established.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N85",
            "MALICIOUS_NEAR_MATCH",
            "Software gap or market size is not established.",
            "software",
            "REFUSE",
            N,
        ),
        ("N86", "MALICIOUS_NEAR_MATCH", "Software gap is not only large.", "software", "REFUSE", N),
        (
            "N87",
            "MALICIOUS_NEAR_MATCH",
            "Software gap remains to be seen.",
            "software",
            "REFUSE",
            N,
        ),
        ("N95", "MALICIOUS_NEAR_MATCH", "Software remains to be seen.", "software", "REFUSE", N),
        (
            "N88",
            "MALICIOUS_NEAR_MATCH",
            "Software buyers exist, and the gap is not established.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N90",
            "MALICIOUS_NEAR_MATCH",
            "Whether a need or software gap exists is unknown; software gap exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N93",
            "MALICIOUS_NEAR_MATCH",
            "The market gap is established and software demand is not established.",
            "market",
            "REFUSE",
            N,
        ),
        (
            "N94",
            "MALICIOUS_NEAR_MATCH",
            "Software is not established, it exists.",
            "software",
            "PASS",
            N,
        ),
        (
            "N92",
            "MALICIOUS_NEAR_MATCH",
            "Software gap is not established, it exists.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "N104",
            "MALICIOUS_NEAR_MATCH",
            "No staff bid or buyers are willing to pay.",
            "willing to pay",
            "REFUSE",
            N,
        ),
        ("C1", "CLASS_FIELD", "A market-observation exercise.", "market", "REFUSE", N),
        (
            "C2",
            "CLASS_FIELD",
            "A software tool for contracting authorities.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "C4",
            "CLASS_FIELD",
            "A review of notices, not a software product.",
            "software",
            "PASS",
            N,
        ),
        (
            "C5",
            "CLASS_FIELD",
            "A notice review; no software is established.",
            "software",
            "PASS",
            N,
        ),
        ("C7", "CLASS_FIELD", "Software intervention is not established.", "software", "PASS", B),
        (
            "C8",
            "CLASS_FIELD",
            "Whether a notice review or software tool is suitable is unknown.",
            "software",
            "PASS",
            A,
        ),
        (
            "C9",
            "CLASS_FIELD",
            "A software intervention class, which is not established.",
            "software",
            "REFUSE",
            N,
        ),
        (
            "C10",
            "CLASS_FIELD",
            "A market-observation exercise is not established, but it clearly exists.",
            "market",
            "REFUSE",
            N,
        ),
        (
            "C11",
            "CLASS_FIELD",
            "A market-observation exercise is not established.",
            "market",
            "PASS",
            B,
        ),
    )
)
#: Groups whose every intended verdict is REFUSE-or-assertion: explicit proofs that nothing opened.
ASSERTION_PROOF_GROUPS = (
    "ASSERTED_CONTROL",
    "GENUINE_NEW_SUBJECT",
    "CONTRASTIVE_CONTINUATION",
    "COORDINATED_PREDICATE",
    "MALICIOUS_NEAR_MATCH",
)
FIELDS = ("critical_uncertainties", "commercial_claims_not_supported")

#: What the matrix must find. Pinned here, so the report cannot drift from the code.
EXPECTED_VERDICT_CHANGES: tuple[str, ...] = (
    "L1",
    "L2",
    "L3",
    "L4",
    "L5",
    "L6",
    "L7",
    "L8",
    "L9",
    "L10",
    "M1",
    "M2",
    "M3",
    "N1",
    "N2",
    "N3",
    "N4",
    "N5",
    "N7",
    "N8",
    "N9",
    "N10",
    "N11",
    "N12",
    "N13",
    "N14",
    "N15",
    "N40",
    "N97",
    "N21",
    "N22",
    "N23",
    "N24",
    "N26",
    "N27",
    "N98",
    "N101",
    "N31",
    "N32",
    "N33",
    "N62",
    "N72",
    "N76",
    "C7",
    "C8",
    "C11",
)
EXPECTED_REASON_ONLY_CHANGES: tuple[str, ...] = ("N51", "N68", "N99", "N100", "N84", "N85", "N93")
EXPECTED_RESIDUAL_OVER_REFUSALS: tuple[str, ...] = ("N96", "N25", "N28", "N30")
EXPECTED_SECONDARY_FIELD_CHANGES: tuple[str, ...] = (
    "L2:critical_uncertainties",
    "L7:critical_uncertainties",
    "L8:critical_uncertainties",
    "N3:critical_uncertainties",
    "N4:critical_uncertainties",
    "N5:critical_uncertainties",
    "N8:critical_uncertainties",
    "N15:critical_uncertainties",
    "N98:critical_uncertainties",
)
#: The two authorised repairs, and nothing else.
AUTHORISED_ATTRIBUTIONS = frozenset({"A", "B"})

#: The frozen files whose sentences the sweep reads: every gate test file and the census fixtures.
SWEEP_FILES = (
    f"{TESTS}/test_semantic_gate_v1_2.py",
    f"{TESTS}/test_semantic_gate_v1_3.py",
    f"{TESTS}/test_semantic_gate_v1_4.py",
    "infrastructure/scripts/second_opportunity_synthetic_fixtures.py",
)


# --------------------------------------------------------------------------- reading

Reader = tuple[Callable[..., Any], Callable[..., Any]]
READERS: dict[str, Reader] = {
    "v1_4_0": (scope.clauses_v1_2, scope.state_v1_2),
    "d1_only": (scope.scoped_clauses, scope.state_v1_2),
    "d2_only": (scope.clauses_v1_2, scope.scoped_state),
    "v1_5_0": (scope.scoped_clauses, scope.scoped_state),
}


def _present(text: str) -> list[str]:
    lowered = text.lower()
    return [g for g in GATED if inflection_spans(lowered, g)]


def asserted_under(text: str, reader: str, words: Sequence[str]) -> set[str]:
    splitter, state = READERS[reader]
    return {
        w
        for w in words
        if any(
            o.asserted
            for o in scope.read_occurrences(text, w, splitter=splitter, state_reader=state)
        )
    }


def attribution(text: str) -> dict[str, Any]:
    """Which gated words each reading asserts, and which repair clears each one v1.4.0 asserted."""
    words = _present(text)
    sets = {name: asserted_under(text, name, words) for name in READERS}
    base = sets["v1_4_0"]
    for name in ("d1_only", "d2_only", "v1_5_0"):
        added = sets[name] - base
        if added:
            raise ValidationError(f"{name} asserts {sorted(added)} that v1.4.0 did not: {text!r}")
    repairs = set()
    if base - sets["d1_only"]:
        repairs.add("A")
    if base - sets["d2_only"]:
        repairs.add("B")
    return {
        "cleared": sorted(base - sets["v1_5_0"]),
        "attribution": sorted(repairs),
        "clauses_v1_4_0": [c.text for s in _sentences(text) for c in scope.clauses_v1_2(s)],
        "clauses_v1_5_0": [c.text for s in _sentences(text) for c in scope.scoped_clauses(s)],
    }


def seam_block(sentences: Sequence[str]) -> dict[str, Any]:
    """The successor's loop over v1.2.0's own functions reproduces v1.3.0's `classify` exactly."""
    checked = 0
    for text in sentences:
        for word in _present(text):
            for head in (False, True):
                seam = scope.read_occurrences(
                    text,
                    word,
                    splitter=scope.clauses_v1_2,
                    state_reader=scope.state_v1_2,
                    scoped_head=head,
                )
                if seam != audit_v1_3.classify(text, word, scoped_head=head):
                    raise ValidationError(
                        f"the seam is not v1.3.0's classify on {text!r}, {word!r}"
                    )
                checked += 1
    return {"SENTENCES": len(sentences), "READINGS_COMPARED": checked, "DIFFERENCES": 0}


# --------------------------------------------------------------------------- the gates


def _field_findings(decision: Any) -> dict[str, set[str]]:
    return {f.field_name: set(f.findings) for f in decision.audit.fields} if decision.audit else {}


def _non_audit_reasons(decision: Any) -> list[str]:
    return [r for r in decision.refusal_reasons if " audited " not in r]


def _pair(output: dict[str, Any], fx: Any) -> tuple[Any, Any]:
    arguments = {"trusted_context": fx.TRUSTED, "source_metadata": fx.META}
    old = evaluate_second_opportunity_output_v1_4(
        output, fx.PACKET, fx.STATEMENTS, fx.E2C, **arguments
    )
    new = evaluate_second_opportunity_output_v1_5(
        output, fx.PACKET, fx.STATEMENTS, fx.E2C, **arguments
    )
    return old, new


def _audit_pair(text: str, field: str, universe: Any, supported: frozenset[Any]) -> tuple[Any, Any]:
    fc = next(f for f in SECOND_OPPORTUNITY_FIELD_POLICY if f.field_name == field)
    assert fc.disposition is not None  # noqa: S101 -- every listed field has one
    arguments = (
        fc.disposition,
        fc.shape,
        universe,
        FORBIDDEN_CONCEPTS_V1_2,
        PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
        supported,
    )
    return audit_v1_3.audit_text(text, *arguments), audit_v1_5.audit_text(text, *arguments)


def matrix_block(fx: Any) -> dict[str, Any]:
    content = " ".join(fx.STATEMENTS.values()).lower()
    universe = build_typed_support_universe(fx.PACKET, fx.STATEMENTS, fx.TRUSTED, fx.META)
    supported = frozenset(fx.PACKET.counting_dimensions)
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for case in CASES:
        if case.case_id in seen:
            raise ValidationError(f"{case.case_id} appears twice")
        seen.add(case.case_id)
        if not inflection_spans(case.sentence.lower(), case.phrase):
            raise ValidationError(f"{case.case_id} does not carry {case.phrase!r}")
        if inflection_spans(content, case.phrase):
            raise ValidationError(f"{case.case_id}: the fixture statements carry {case.phrase!r}")
        field = "candidate_intervention_class" if case.group == "CLASS_FIELD" else "observed_need"
        old, new = _pair(fx.good_output(**{field: case.sentence}), fx)
        stray = [
            r for r in (*old.refusal_reasons, *new.refusal_reasons) if not r.startswith(f"{field} ")
        ]
        if stray:
            raise ValidationError(f"{case.case_id} is refused outside {field}: {stray[0]}")
        old_findings, new_findings = _field_findings(old), _field_findings(new)
        for name, findings in new_findings.items():
            if not findings <= old_findings.get(name, set()):
                raise ValidationError(f"{case.case_id}: v1.5.0 adds a finding in {name}")
        if _non_audit_reasons(old) != _non_audit_reasons(new):
            raise ValidationError(f"{case.case_id}: a reason outside the audit moved")
        verdict_old = "REFUSE" if old.refusal_reasons else "PASS"
        verdict_new = "REFUSE" if new.refusal_reasons else "PASS"
        reading = attribution(case.sentence)
        secondary = {}
        for other in FIELDS:
            was, now = _audit_pair(case.sentence, other, universe, supported)
            if not set(now[1]) <= set(was[1]):
                raise ValidationError(f"{case.case_id}: v1.5.0 adds a finding in {other}")
            secondary[other] = {"v1_4_0": was[0].value, "v1_5_0": now[0].value}
        changed = old.refusal_reasons != new.refusal_reasons or any(
            v["v1_4_0"] != v["v1_5_0"] for v in secondary.values()
        )
        if changed and not (
            set(reading["attribution"]) and set(reading["attribution"]) <= AUTHORISED_ATTRIBUTIONS
        ):
            raise ValidationError(f"{case.case_id} diverges and neither repair explains it")
        if case.intended == "REFUSE" and verdict_new == "PASS":
            raise ValidationError(f"{case.case_id}: the policy refuses it and v1.5.0 passes it")
        if case.divergence_class == N and verdict_old != verdict_new:
            raise ValidationError(f"{case.case_id}: a verdict moved where no repair was authorised")
        if verdict_new == case.intended:
            status = "AS_INTENDED_UNCHANGED" if verdict_old == verdict_new else "REPAIRED"
        else:
            status = "RESIDUAL_OVER_REFUSAL"
        rows.append(
            {
                "case": case.case_id,
                "group": case.group,
                "sentence": case.sentence,
                "phrase": case.phrase,
                "field": field,
                "intended": case.intended,
                "divergence_class": case.divergence_class,
                "v1_4_0": verdict_old,
                "v1_5_0": verdict_new,
                "v1_4_0_reasons": list(old.refusal_reasons),
                "v1_5_0_reasons": list(new.refusal_reasons),
                "status": status,
                **reading,
                "secondary_fields": secondary,
            }
        )
    by_id = {r["case"]: r for r in rows}
    verdict_changes = [r["case"] for r in rows if r["v1_4_0"] != r["v1_5_0"]]
    reason_only = [
        r["case"]
        for r in rows
        if r["v1_4_0"] == r["v1_5_0"] and r["v1_4_0_reasons"] != r["v1_5_0_reasons"]
    ]
    residual = [r["case"] for r in rows if r["status"] == "RESIDUAL_OVER_REFUSAL"]
    secondary_changes = [
        f"{r['case']}:{f}"
        for r in rows
        for f, v in r["secondary_fields"].items()
        if v["v1_4_0"] != v["v1_5_0"]
    ]
    mismatches = [
        f"{name} {found}, not {list(expected)}"
        for name, found, expected in (
            ("EXPECTED_VERDICT_CHANGES", verdict_changes, EXPECTED_VERDICT_CHANGES),
            ("EXPECTED_REASON_ONLY_CHANGES", reason_only, EXPECTED_REASON_ONLY_CHANGES),
            ("EXPECTED_RESIDUAL_OVER_REFUSALS", residual, EXPECTED_RESIDUAL_OVER_REFUSALS),
            (
                "EXPECTED_SECONDARY_FIELD_CHANGES",
                secondary_changes,
                EXPECTED_SECONDARY_FIELD_CHANGES,
            ),
        )
        if tuple(found) != expected
    ]
    if mismatches:
        raise ValidationError("the matrix finds " + " | ".join(mismatches))
    for case_id in verdict_changes:
        if by_id[case_id]["divergence_class"] == N:
            raise ValidationError(f"{case_id} changed verdict outside an authorised repair")
    proofs = _proofs(rows)
    by_attribution: dict[str, int] = {}
    for case_id in (*verdict_changes, *reason_only):
        key = "+".join(by_id[case_id]["attribution"])
        by_attribution[key] = by_attribution.get(key, 0) + 1
    groups: dict[str, int] = {}
    for r in rows:
        groups[r["group"]] = groups.get(r["group"], 0) + 1
    return {
        "fixture": f"{TESTS}/test_semantic_gate_v1_3.py",
        "CASES": len(rows),
        "BY_GROUP": dict(sorted(groups.items())),
        "cases": rows,
        "VERDICT_CHANGES": verdict_changes,
        "REASON_ONLY_CHANGES": reason_only,
        "RESIDUAL_OVER_REFUSALS": residual,
        "SECONDARY_FIELD_CHANGES": secondary_changes,
        "DIVERGENCES_BY_ATTRIBUTION": dict(sorted(by_attribution.items())),
        "UNATTRIBUTED_DIVERGENCES": 0,
        "SUCCESSOR_ADDED_ASSERTIONS": 0,
        "POLICY_REFUSALS_PASSED_BY_V1_5_0": 0,
        **proofs,
    }


def _proofs(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """The three explicit proofs: assertions fail, a genuine clause splits, a re-assertion fails."""
    assertions = [
        r for r in rows if r["group"] in ASSERTION_PROOF_GROUPS and r["intended"] == "REFUSE"
    ]
    if any(r["v1_5_0"] != "REFUSE" for r in assertions):
        raise ValidationError("a genuine assertion passes gate v1.5.0")
    genuine = [r for r in rows if r["group"] == "GENUINE_NEW_SUBJECT"]
    for r in genuine:
        # The genuine proposition closes each of these sentences: it must stay a clause of its own,
        # word for word, whatever D1 did to a scoped list before it.
        if len(r["clauses_v1_5_0"]) < 2 or r["clauses_v1_5_0"][-1] != r["clauses_v1_4_0"][-1]:
            raise ValidationError(f"{r['case']}: a genuine coordinated clause no longer splits")
    reassertions = [
        r for r in rows if r["group"] == "CONTRASTIVE_CONTINUATION" and r["intended"] == "REFUSE"
    ]
    if any(r["v1_5_0"] != "REFUSE" for r in reassertions):
        raise ValidationError("a contrastive re-assertion passes gate v1.5.0")
    return {
        "GENUINE_ASSERTIONS_STILL_REFUSED": len(assertions),
        "GENUINE_COORDINATED_CLAUSES_STILL_SPLIT": len(genuine),
        "CONTRASTIVE_REASSERTIONS_STILL_REFUSED": len(reassertions),
    }


# --------------------------------------------------------------------------- the sweep

#: A sentence of three words or more: every string constant is split into sentences and read.
_STRING = re.compile(r"\S+(?:\s+\S+){2,}")


def sweep_sentences() -> list[str]:
    found: set[str] = set()
    for relative in SWEEP_FILES:
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for sentence in _sentences(node.value):
                    text = sentence.strip()
                    if _STRING.fullmatch(text) and _present(text):
                        found.add(text)
    return sorted(found)


def sweep_block(sentences: Sequence[str]) -> dict[str, Any]:
    changed: list[dict[str, Any]] = []
    for text in sentences:
        reading = attribution(text)
        if reading["cleared"] or reading["clauses_v1_4_0"] != reading["clauses_v1_5_0"]:
            if reading["cleared"] and not set(reading["attribution"]) <= AUTHORISED_ATTRIBUTIONS:
                raise ValidationError(f"the sweep finds an unattributed change: {text!r}")
            changed.append({"sentence": text, **reading})
    return {
        "files": list(SWEEP_FILES),
        "SENTENCES_WITH_A_GATED_WORD": len(sentences),
        "READINGS_CHANGED": len([c for c in changed if c["cleared"]]),
        "CLAUSE_LISTS_CHANGED": len(
            [c for c in changed if c["clauses_v1_4_0"] != c["clauses_v1_5_0"]]
        ),
        "UNATTRIBUTED": 0,
        "ASSERTIONS_ADDED": 0,
        "changed": changed,
    }


# --------------------------------------------------------------------------- frozen things


def _functions(relative: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


class _Rename(ast.NodeTransformer):
    def __init__(self, names: dict[str, str]) -> None:
        self.names = names

    def visit_Name(self, node: ast.Name) -> ast.Name:
        node.id = self.names.get(node.id, node.id)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.name = self.names.get(node.name, node.name)
        self.generic_visit(node)
        return node


def _without_docstring(node: ast.FunctionDef) -> ast.FunctionDef:
    if (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    ):
        node.body = node.body[1:]
    return node


EVALUATOR_RENAMES = {
    "evaluate_second_opportunity_output_v1_3": "evaluate_second_opportunity_output_v1_5",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1": "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1": "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2",
    "evaluate_persistence_v1_3": "evaluate_persistence_v1_4",
    "SECOND_OPPORTUNITY_GATE_VERSION_V1_3": "SECOND_OPPORTUNITY_GATE_VERSION_V1_5",
}


def rebinding_block() -> dict[str, Any]:
    old = _functions(f"{PACKAGE}/assertion_audit_v1_3.py")
    new = _functions(f"{PACKAGE}/assertion_audit_v1_5.py")
    if list(new) != list(audit_v1_5.REBOUND_FUNCTIONS.values()):
        raise ValidationError(f"the v1.5.0 audit defines {list(new)}, not its re-bound functions")
    for old_name, new_name in audit_v1_5.REBOUND_FUNCTIONS.items():
        renamed = _Rename(dict(audit_v1_5.REBOUND_NAMES)).visit(old[old_name])
        if ast.dump(renamed) != ast.dump(new[new_name]):
            raise ValidationError(f"{new_name} is not v1.3.0's {old_name} with only its renames")
    shared = ("maskable_labels", "disjunctive_connectives", "_mask_identifiers", "_form")
    for name in shared:
        if getattr(audit_v1_5, name) is not getattr(audit_v1_3, name):
            raise ValidationError(f"{name} is not v1.3.0's object")
    if audit_v1_5.classify is not scope.classify or audit_v1_5.is_asserted is not scope.is_asserted:
        raise ValidationError("the v1.5.0 audit does not read through the successor scope")
    gate_old = _without_docstring(
        _functions(f"{PACKAGE}/second_opportunity_gate_v1_3.py")[
            "evaluate_second_opportunity_output_v1_3"
        ]
    )
    gate_new = _without_docstring(
        _functions(f"{PACKAGE}/second_opportunity_gate_v1_5.py")[
            "evaluate_second_opportunity_output_v1_5"
        ]
    )
    if ast.dump(_Rename(EVALUATOR_RENAMES).visit(gate_old)) != ast.dump(gate_new):
        raise ValidationError("the v1.5.0 evaluator is not v1.3.0's with only its renames")
    if list(_functions(f"{PACKAGE}/second_opportunity_gate_v1_5.py")) != [
        "evaluate_second_opportunity_output_v1_5"
    ]:
        raise ValidationError("the v1.5.0 gate module defines more than its evaluator")
    return {
        "AUDIT_REBOUND_FUNCTIONS": dict(audit_v1_5.REBOUND_FUNCTIONS),
        "AUDIT_RENAMES": dict(audit_v1_5.REBOUND_NAMES),
        "AUDIT_SHARED_BY_IDENTITY": list(shared),
        "EVALUATOR_RENAMES": EVALUATOR_RENAMES,
        "SYNTAX_TREES_EQUAL_AFTER_RENAMES": True,
    }


def frozen_block() -> dict[str, Any]:
    predecessors = {}
    for key, (script, digest) in PREDECESSOR_DIGESTS.items():
        found = _module(f"{key}_for_gate_103", SCRIPTS / script).implementation_sha256()
        if found != digest:
            raise ValidationError(f"{key} recomputes to {found}, not its frozen {digest}")
        predecessors[key] = digest
    if file_sha(f"{PACKAGE}/assertion_context.py") != CLAUSE_READER_SHA256:
        raise ValidationError("the v1.2.0 clause reader moved")
    for relative, digest in DIAGNOSIS_FILES.items():
        if file_sha(relative) != digest:
            raise ValidationError(f"gate 102's diagnosis {relative} moved")
    implementation = implementation_sha256()
    test = file_sha(TEST_FILE)
    if implementation != FROZEN_IMPLEMENTATION_SHA256:
        raise ValidationError(f"the v1.5.0 implementation is {implementation}, not the frozen one")
    if test != FROZEN_TEST_SHA256:
        raise ValidationError(f"the v1.5.0 test file is {test}, not the frozen one")
    moved = sorted(
        k
        for k in set(COMPONENT_VERSIONS_V1_4) | set(COMPONENT_VERSIONS_V1_5)
        if COMPONENT_VERSIONS_V1_4.get(k) != COMPONENT_VERSIONS_V1_5.get(k)
    )
    if moved != sorted(CHANGED_COMPONENTS):
        raise ValidationError(f"components moved {moved}, not {sorted(CHANGED_COMPONENTS)}")
    for relative in SUCCESSOR_MODULES:
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for name in names:
                if any(
                    bad in name
                    for bad in (
                        "urllib",
                        "http",
                        "socket",
                        "transport",
                        "anthropic",
                        "sros_llm_gateway",
                        "spacy",
                        "nltk",
                    )
                ):
                    raise ValidationError(f"{relative} imports {name}")
    return {
        "PREDECESSOR_IMPLEMENTATION_SHA256": predecessors,
        "CLAUSE_READER_SHA256": CLAUSE_READER_SHA256,
        "GATE_102_DIAGNOSIS_FILES": DIAGNOSIS_FILES,
        "IMPLEMENTATION_FILES": {p: file_sha(p) for p in IMPLEMENTATION_FILES},
        "SEMANTIC_GATE_V1_5_IMPLEMENTATION_SHA256": implementation,
        "FROZEN_TEST_FILE": {TEST_FILE: test},
        "COMPONENT_VERSIONS_V1_5": dict(COMPONENT_VERSIONS_V1_5),
        "CHANGED_COMPONENTS": list(CHANGED_COMPONENTS),
        "SUCCESSOR_NETWORK_OR_NLP_IMPORTS": 0,
    }


# --------------------------------------------------------------------------- V9 and V10


def history_block() -> dict[str, Any]:
    """V9 and V10 replayed diagnostically: their records untouched, their verdicts unchanged."""
    try:
        v10 = G101.validate()
        v9 = G98.validate()
    except (G101.ValidationError, G98.ValidationError) as exc:
        raise ValidationError(
            f"a historical execution no longer stands as recorded: {exc}"
        ) from exc
    packet, statements, evidence_to_claim = G101.snapshot_packet()
    metadata = G101.runner().source_metadata_for(list(packet.source_ids))
    trusted = build_trusted_context(packet)
    out: dict[str, Any] = {}
    for label, gate, record in (("V9", G98, v9), ("V10", G101, v10)):
        if file_sha(str(gate.RESPONSE.relative_to(ROOT))) != gate.RESPONSE_FILE_SHA256:
            raise ValidationError(f"{label}'s retained response moved")
        if file_sha(str(gate.RECORD.relative_to(ROOT))) != gate.RECORD_FILE_SHA256:
            raise ValidationError(f"{label}'s execution record moved")
        response = json.loads(gate.RESPONSE.read_text(encoding="utf-8"))
        parsed = response["parsed_output"]
        arguments = {"trusted_context": trusted, "source_metadata": metadata}
        old = evaluate_second_opportunity_output_v1_4(
            parsed, packet, statements, evidence_to_claim, **arguments
        )
        new = evaluate_second_opportunity_output_v1_5(
            parsed, packet, statements, evidence_to_claim, **arguments
        )
        if list(old.refusal_reasons) != list(response["validation"]["reasons"]):
            raise ValidationError(f"gate v1.4.0 no longer reproduces {label}'s retained reasons")
        removed = [r for r in old.refusal_reasons if r not in new.refusal_reasons]
        added = [r for r in new.refusal_reasons if r not in old.refusal_reasons]
        if added:
            raise ValidationError(f"gate v1.5.0 adds a reason to {label}: {added[0]}")
        out[label] = {
            "HISTORICAL_OUTCOME": record["PRIMARY_OUTCOME"],
            "HISTORICAL_STAGES": record["VALIDATION_STAGES"],
            "HISTORICAL_RECORD_EDITED": False,
            "RETAINED_REASONS": list(response["validation"]["reasons"]),
            "V1_4_0_REPRODUCES_RETAINED_REASONS": True,
            "V1_5_0_WOULD_REFUSE_WITH": list(new.refusal_reasons),
            "V1_5_0_WOULD_REMOVE": removed,
            "V1_5_0_WOULD_PERSIST": bool(new.persist),
        }
    v10_new = out["V10"]["V1_5_0_WOULD_REFUSE_WITH"]
    if (
        out["V10"]["V1_5_0_WOULD_PERSIST"]
        or len(v10_new) != 1
        or not v10_new[0].startswith("candidate_intervention_class audited UNSUPPORTED: 'market'")
        or len(out["V10"]["V1_5_0_WOULD_REMOVE"]) != 1
        or not out["V10"]["V1_5_0_WOULD_REMOVE"][0].startswith(
            "observed_need audited UNSUPPORTED: 'software'"
        )
    ):
        raise ValidationError("gate v1.5.0 does not leave V10 refused on 'market' alone")
    if out["V9"]["V1_5_0_WOULD_REFUSE_WITH"] != out["V9"]["RETAINED_REASONS"]:
        raise ValidationError("gate v1.5.0 would move V9's reasons, which neither repair touches")
    out["V10"].update(
        {
            "ELIGIBLE_CANDIDATE": False,
            "HUMAN_REVIEW_CANDIDATE": False,
            "PERSISTENCE_CANDIDATE": False,
            "REFUSED_UNDER_V1_5_0_BECAUSE": "market in candidate_intervention_class",
        }
    )
    for name in (
        "second-opportunity-human-review-packet-v9.json",
        "second-opportunity-human-review-packet-v10.json",
    ):
        if (DATA / name).exists():
            raise ValidationError(f"{name} exists")
    v11 = sorted(p.name for p in DATA.glob("*v11*"))
    if v11:
        raise ValidationError(f"a V11 artifact exists: {v11}")
    out["V11_ARTIFACTS"] = 0
    out["HUMAN_REVIEW_PACKETS"] = 0
    return out


# --------------------------------------------------------------------------- the record


def derive() -> dict[str, Any]:
    fx = _module("frozen_v1_3_fixture_for_gate_103", FIXTURE)
    with no_network():
        frozen = frozen_block()
        rebinding = rebinding_block()
        matrix = matrix_block(fx)
        sentences = sweep_sentences()
        sweep = sweep_block(sentences)
        seam = seam_block([c.sentence for c in CASES] + list(sentences))
        history = history_block()
    return {
        "$comment": (
            "Generated by infrastructure/scripts/render_second_opportunity_semantic_gate_v1_5.py (CI "
            "gate 103). Every field is re-derived at check time; V9's and V10's recorded verdicts are "
            "unchanged, and what gate v1.5.0 would say is recorded beside them, never over them."
        ),
        "MISSION": MISSION,
        "START_COMMIT": START_COMMIT,
        "BRANCH": BRANCH,
        "PRIMARY_OUTCOME": PRIMARY_OUTCOME,
        "GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_5,
        "PREDECESSOR_GATE_VERSION": PREDECESSOR_GATE_VERSION,
        "OPERATOR_DECISION": list(OPERATOR_DECISION_V1_5),
        "INVARIANTS": INVARIANTS,
        "NOT_CHANGED": NOT_CHANGED,
        "RULES": {
            "D1": scope.SCOPED_LIST_RULE,
            "D2": scope.DENIED_SUBJECT_MODIFIER_RULE,
            "ASSERTION_SCOPE_POLICY_VERSION": scope.ASSERTION_SCOPE_POLICY_VERSION,
        },
        "FROZEN": frozen,
        "REBINDING": rebinding,
        "SEAM": seam,
        "MATRIX": matrix,
        "SWEEP": sweep,
        "HISTORY": history,
        "CANONICAL_COUNTERS_OBSERVED_READ_ONLY": CANONICAL_COUNTERS_OBSERVED,
    }


def validate() -> dict[str, Any]:
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} is missing")
    derived = derive()
    committed: dict[str, Any] = json.loads(RECORD.read_text(encoding="utf-8"))
    if committed != derived:
        raise ValidationError(f"{RECORD.name} is not what the code derives")
    return derived


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_semantic_gate_v1_5.py from "
    "second-opportunity-output-gate-v1.5-freeze-v1.json. Do not edit by hand. -->\n\n"
)


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render(record: dict[str, Any]) -> str:
    frozen, matrix, sweep, history = (
        record["FROZEN"],
        record["MATRIX"],
        record["SWEEP"],
        record["HISTORY"],
    )
    out = [
        HEADER.rstrip("\n"),
        "",
        f"# Semantic output gate v1.5.0 ({record['MISSION']})",
        "",
        f"**`{record['PRIMARY_OUTCOME']}`**, from `{record['START_COMMIT']}`.",
        "",
        f"`{record['GATE_VERSION']}` beside `{record['PREDECESSOR_GATE_VERSION']}`. "
        f"D1 `{record['RULES']['D1']}`, D2 `{record['RULES']['D2']}`, "
        f"`{record['RULES']['ASSERTION_SCOPE_POLICY_VERSION']}`.",
        "",
        "## Frozen",
        "",
        f"- implementation `{frozen['SEMANTIC_GATE_V1_5_IMPLEMENTATION_SHA256']}`",
        *(f"- test file `{p}` `{d}`" for p, d in frozen["FROZEN_TEST_FILE"].items()),
        *(
            f"- {k} `{d}` (recomputed)"
            for k, d in frozen["PREDECESSOR_IMPLEMENTATION_SHA256"].items()
        ),
        f"- clause reader `{frozen['CLAUSE_READER_SHA256']}`, gate 102's diagnosis byte for byte",
        f"- components moved: {', '.join(frozen['CHANGED_COMPONENTS'])}",
        "",
        "## Differential matrix",
        "",
        f"{matrix['CASES']} cases on `{matrix['fixture']}`. Verdict changes: "
        f"{', '.join(matrix['VERDICT_CHANGES'])}. Reason-only changes: "
        f"{', '.join(matrix['REASON_ONLY_CHANGES'])}. Residual over-refusals (v1.4.0's verdict kept, "
        f"refusing): {', '.join(matrix['RESIDUAL_OVER_REFUSALS'])}. Secondary-field changes: "
        f"{', '.join(matrix['SECONDARY_FIELD_CHANGES'])}. By attribution: "
        f"{json.dumps(matrix['DIVERGENCES_BY_ATTRIBUTION'])}. Unattributed divergences 0; assertions "
        "added by the successor 0; policy refusals passed by v1.5.0 0.",
        "",
        f"Genuine assertions still refused: {matrix['GENUINE_ASSERTIONS_STILL_REFUSED']}. Genuine "
        f"coordinated clauses still split: {matrix['GENUINE_COORDINATED_CLAUSES_STILL_SPLIT']}. "
        f"Contrastive re-assertions still refused: {matrix['CONTRASTIVE_REASSERTIONS_STILL_REFUSED']}.",
        "",
        "| case | group | sentence | v1.4.0 | v1.5.0 | intended | status | repair | cleared |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in matrix["cases"]:
        out.append(
            f"| {r['case']} | {r['group']} | {_cell(r['sentence'])} | {r['v1_4_0']} | {r['v1_5_0']} | "
            f"{r['intended']} | {r['status']} | {'+'.join(r['attribution']) or '-'} | "
            f"{', '.join(r['cleared']) or '-'} |"
        )
    out += [
        "",
        "## Sweep",
        "",
        f"{sweep['SENTENCES_WITH_A_GATED_WORD']} sentences with a gated word in the frozen gate test "
        f"files and the census fixtures; readings changed {sweep['READINGS_CHANGED']}, clause lists "
        f"changed {sweep['CLAUSE_LISTS_CHANGED']}, every change attributed, none adding an assertion.",
        "",
        f"Seam: {record['SEAM']['READINGS_COMPARED']} readings through v1.2.0's own functions, 0 "
        "differences from v1.3.0's `classify`.",
        "",
        "## V9 and V10, diagnostically",
        "",
    ]
    for label in ("V9", "V10"):
        h = history[label]
        out += [
            f"- **{label}** `{h['HISTORICAL_OUTCOME']}`, record unchanged; v1.4.0 reproduces its "
            f"{len(h['RETAINED_REASONS'])} retained reasons; v1.5.0 would refuse with "
            f"{len(h['V1_5_0_WOULD_REFUSE_WITH'])} and remove {len(h['V1_5_0_WOULD_REMOVE'])}.",
        ]
    out += [
        f"- V10 under v1.5.0 is refused on *market* alone: eligible candidate "
        f"{history['V10']['ELIGIBLE_CANDIDATE']}, human-review candidate "
        f"{history['V10']['HUMAN_REVIEW_CANDIDATE']}, persistence candidate "
        f"{history['V10']['PERSISTENCE_CANDIDATE']}.",
        "",
    ]
    return "\n".join(out)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            record = derive()
            RECORD.write_bytes(
                (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            )
            RECORD_MD.write_bytes(render(record).encode("utf-8"))
            print(f"wrote    {RECORD.name}, {RECORD_MD.name}")
            return 0
        record = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    if not RECORD_MD.exists() or RECORD_MD.read_text(encoding="utf-8") != render(record):
        print(f"FAIL     {RECORD_MD.name} is not the rendering of its record")
        return 1
    print(
        "ok       gate v1.5.0 repairs D1 and D2 and nothing else; v1.4.0 and history untouched; V10 "
        "still refused on 'market'"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
