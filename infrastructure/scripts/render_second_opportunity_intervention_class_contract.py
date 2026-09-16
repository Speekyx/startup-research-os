"""Mission 1.84.27, CI gate 104. The intervention-class contract: schema v1.3.0, gate v1.6.0, prompt v1.7.0.

Operator decision D3 asked that `candidate_intervention_class` stop forcing a model to invent a class,
and D5 that the prompt say what the gate asserts. Both are resolved at the contract level, offline, and
this gate derives every field of its record from the live code:

* **frozen, beside history.** Gates v1.2.0 to v1.5.0 recompute to their pinned digests, gates 102 and
  103 are byte for byte the merged records, schema v1.2.0 and its strict projection keep their digests,
  and prompt v1.6.0 rendered over the snapshot still hashes to the V10 digest. The successor modules and
  their frozen test file are pinned here.
* **the contract.** Schema v1.3.0 moves one leaf, the class field's description, which states the
  existing sentinel; its strict projection moves the same leaf and nothing else. Prompt v1.7.0 states
  every constraint, rule, target and contract rule, and no longer carries the sentence that forced a
  class.
* **the class matrix.** Absence, grounded classes, uncited words, invented vocabulary, dimension and
  source names, quoted codes, look-alike characters, denials and clauses, each with the verdict the
  contract intends, through gates v1.5.0 and v1.6.0. Every divergence is a class-grounding reason.
* **every other field, unchanged.** Every sentence of gate 103's matrix, read in `observed_need` with the class
  absent, and a set of displacement cases get exactly v1.5.0's reasons from v1.6.0. The displacement
  cases still pass both: that debt is recorded, not repaired.
* **V9 and V10, diagnostically.** Their records are untouched and still validate; gate v1.5.0 still
  gives what gate 103 recorded; what gate v1.6.0 would say is recorded beside it, and both stay refused.

Nothing here calls a model, builds a transport, binds a runner, reads the database or writes outside
this record.

    uv run python infrastructure/scripts/render_second_opportunity_intervention_class_contract.py --check
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
from collections.abc import Iterator, Sequence
from typing import Any, NamedTuple

from sros_llm_gateway.providers.anthropic_strict import (
    ANTHROPIC_STRICT_TOOL_PROFILE_V1,
    canonical_json_sha256,
    project_strict_input_schema,
)
from sros_opportunity import generation_contract_policy as contract
from sros_opportunity import intervention_class_grounding as grounding
from sros_opportunity.lexical_inflection import inflection_spans
from sros_opportunity.second_opportunity_gate_v1_2 import build_trusted_context
from sros_opportunity.second_opportunity_gate_v1_5 import (
    COMPONENT_VERSIONS_V1_5,
    evaluate_second_opportunity_output_v1_5,
)
from sros_opportunity.second_opportunity_gate_v1_6 import (
    CHANGED_COMPONENTS,
    CLASS_GROUNDING_REASON_PREFIX,
    COMPONENT_VERSIONS_V1_6,
    OPERATOR_DECISION_V1_6,
    PREDECESSOR_GATE_VERSION,
    PREDECESSOR_STRUCTURAL_REASON_PREFIX,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_6,
    STRUCTURAL_REASON_PREFIX,
    evaluate_second_opportunity_output_v1_6,
)
from sros_opportunity.second_opportunity_prompt_v1_6 import (
    SECOND_OPPORTUNITY_SYSTEM_V1_6,
    render_second_opportunity_prompt_v1_6,
    second_opportunity_prompt_hash_v1_6,
)
from sros_opportunity.second_opportunity_prompt_v1_7 import (
    GENERATION_CONTRACT_BLOCK_V1_7,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_7,
    SECOND_OPPORTUNITY_SYSTEM_V1_7,
    render_second_opportunity_prompt_v1_7,
    second_opportunity_prompt_hash_v1_7,
    unstated_constraints_in,
    unstated_contract_rules_in,
    unstated_headroom_in,
    unstated_semantic_rules_in,
)
from sros_opportunity.second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    semantic_schema_diff,
)
from sros_opportunity.second_opportunity_schema_v1_3 import (
    INTERVENTION_CLASS_DESCRIPTION,
    INTERVENTION_CLASS_NOT_ESTABLISHED,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3,
)
from sros_opportunity.support_origin import build_typed_support_universe

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-intervention-class-contract-v1.json"
RECORD_MD = DATA / "second-opportunity-intervention-class-contract-v1.md"
THIS_SCRIPT = "infrastructure/scripts/render_second_opportunity_intervention_class_contract.py"
PACKAGE = "packages/opportunity-engine/python/sros_opportunity"
TESTS = "packages/opportunity-engine/python/tests"
FIXTURE = ROOT / TESTS / "test_semantic_gate_v1_3.py"

MISSION = "mission-1.84.27"
START_COMMIT = "e29b3b437c7e869017bd76066ad118286875b4e0"
BRANCH = "sprint-1/mission-1.84.27"
PRIMARY_OUTCOME = (
    "INTERVENTION_CLASS_CONTRACT_IMPLEMENTED_OFFLINE_SENTINEL_AND_CITED_CLAIM_GROUNDING"
)

SUCCESSOR_MODULES = (
    f"{PACKAGE}/second_opportunity_schema_v1_3.py",
    f"{PACKAGE}/intervention_class_grounding.py",
    f"{PACKAGE}/second_opportunity_gate_v1_6.py",
    f"{PACKAGE}/generation_contract_policy.py",
    f"{PACKAGE}/second_opportunity_prompt_v1_7.py",
)
TEST_FILE = f"{TESTS}/test_intervention_class_contract_v1_3.py"

#: Pinned at the freeze. Editing either is re-freezing, and re-freezing is a new contract version.
FROZEN_IMPLEMENTATION_SHA256 = "0e3db2d2eddc1191b3554aa8bf116f33ef42ac9e749b4455236b031a5a2f912c"
FROZEN_TEST_SHA256 = "4ded39a4572ae1d0346034d2c565aa41079df07f934a6be56d9edb1f13f54712"

#: What the successors are, pinned: a moved digest here is a new version, never an edit.
SCHEMA_V1_3_SHA256 = "1e5e86245b36cc4151742dc412bc473e5c06282717704d219849227c76a84d23"
STRICT_PROJECTION_V1_3_SHA256 = "cf98958a9b61742de1974cc96faed731816e88663b439b16624f12d52378a4d3"
PROMPT_V1_7_SHA256 = "16117619dc68472afcbd4b8af6503e0fad3b0e77cc47448fe4a211a7f3f375e9"
PROMPT_V1_7_SYSTEM_SHA256 = "9fe05f6a41901cf7a569721c86319ffe628984c7e7ff454b20a48c6bc45aaaab"

#: The predecessors as their own gates and executions froze them.
SCHEMA_V1_2_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
STRICT_PROJECTION_V1_2_SHA256 = "87028f451205494a948e83740e73b9ca59ce3243f54e24c123b7cc2354c69783"
PROMPT_V1_6_SHA256 = "a89960ceb62794c42a84fe7110da6397045c2f57933a721f19cd543e4c221ed5"
GATE_V1_5_IMPLEMENTATION_SHA256 = "b188ba4c2cfee92fe56d4bda376d69f280e63a39efde13b4c80e14d96975d7df"
MERGED_RECORD_FILES: dict[str, str] = {
    "docs/data/second-opportunity-stage6-diagnostic-v10.json": (
        "dfc9fde4fd104a01e61f085d3b58360426fa993db4a333048bb5c8fe757ee1da"
    ),
    "docs/data/second-opportunity-stage6-diagnostic-v10.md": (
        "bbd267d84095d92afc9b1386190c47c2596a653ae8c0b985332b8bf47d75c9f2"
    ),
    "docs/data/second-opportunity-output-gate-v1.5-freeze-v1.json": (
        "66fe7ca08fc5e7bc441beca003148cd1f4403d4dc23d65d12e711a30a35595f5"
    ),
    "docs/data/second-opportunity-output-gate-v1.5-freeze-v1.md": (
        "8433422768fb9ebf8801d0a901ad87927eeab7e9097e8d9691f3d47db4fde4e4"
    ),
}
#: The sentence of prompt v1.6.0 that asked for a class where none was supplied.
FORCING_SENTENCE = "name a more neutral class grounded in what they do supply"

INVARIANTS: dict[str, object] = {
    "PROVIDER_CALLS": 0,
    "MODEL_INFERENCES": 0,
    "TOKEN_COUNTS": 0,
    "RETRIES": 0,
    "PERSISTENCE": 0,
    "NEW_EXECUTION_PACKET": "NO",
    "V11_CREATION": "NO",
    "OPPORTUNITY_2_CREATION": "NO",
    "RUNNER_BOUND_TO_PROMPT_V1_7_0": False,
    "SCHEMA_V1_2_0_CHANGED": False,
    "PROMPT_V1_6_0_CHANGED": False,
    "GATES_V1_4_0_AND_V1_5_0_CHANGED": False,
    "HISTORICAL_V1_TO_V10_ARTIFACTS_EDITED": False,
    "D4_AUTHORISED": False,
}
NOT_CHANGED: dict[str, bool] = {
    "DATABASE_SCHEMA_CHANGED": False,
    "STRICT_PROJECTION_CODE_CHANGED": False,
    "STRICT_TOOL_PROFILE_CHANGED": False,
    "FIELD_POLICY_CHANGED": False,
    "FORBIDDEN_CONCEPT_REMOVED_OR_WEAKENED": False,
    "MARKET_ACTIVITY_LICENCE_BROADENED": False,
    "VOCABULARY_WHITELIST_ADDED": False,
    "NLP_DEPENDENCY_ADDED": False,
    "LLM_IN_THE_GATE": False,
}
#: What this contract does not solve, stated so no later reader takes the gate for more than it is.
SEMANTIC_DEBT: tuple[str, ...] = (
    "CROSS_FIELD_DISPLACEMENT: intervention vocabulary written in hypothesis_statement, observed_need, "
    "target_actor_if_supported or the list fields instead of the class is still held only by the "
    "denylist audit; the displacement cases below pass both gates",
    "LEXICAL_IS_NOT_SEMANTIC: a class assembled from cited words can restate the evidence rather than "
    "name an intervention (for example `published notices`); human review stays mandatory",
    "OTHER_FIELDS_TOKENIZER: look-alike and invisible characters are refused in the class only",
    "INHERITED_PRONOUN_CASE: `Software is not established, and it is probably large.` is out of scope",
    "CENSUS_NOT_ASSERTED_ITEMS: the census rule on added concepts is not checked on free-text "
    "not-supported items or on HYPOTHESIS and UNKNOWN classifications",
)

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


class ValidationError(RuntimeError):
    """The record disagrees with the live code, or with what the operator decided."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(relative: str) -> str:
    return _sha((ROOT / relative).read_bytes())


def implementation_sha256() -> str:
    """One digest over the successor modules, path and bytes, in a fixed order (gate 77's rule)."""
    return _sha("".join(f"{p}\x00{file_sha(p)}\n" for p in SUCCESSOR_MODULES).encode("utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    if not path.exists():
        raise ValidationError(f"{path.name} is missing")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G103 = _module("gate_103_for_gate_104", SCRIPTS / "render_second_opportunity_semantic_gate_v1_5.py")


@contextlib.contextmanager
def no_network() -> Iterator[None]:
    """Gate 76's transport tripwire, and one on urlopen."""
    original = urllib.request.urlopen

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("gate 104 reached urlopen")

    urllib.request.urlopen = refuse  # type: ignore[assignment]
    try:
        with G103.G76.no_transport():
            yield
    finally:
        urllib.request.urlopen = original


def _pinned(name: str, found: str, pinned: str) -> str:
    if found != pinned:
        raise ValidationError(f"{name} is {found}, not the pinned {pinned}")
    return found


# --------------------------------------------------------------------------- frozen things


def frozen_block() -> dict[str, Any]:
    predecessors = {}
    for key, (script, digest) in G103.PREDECESSOR_DIGESTS.items():
        found = _module(f"{key}_for_gate_104", SCRIPTS / script).implementation_sha256()
        predecessors[key] = _pinned(key, found, digest)
    predecessors["gate_103_v1_5_0"] = _pinned(
        "gate v1.5.0", G103.implementation_sha256(), GATE_V1_5_IMPLEMENTATION_SHA256
    )
    _pinned("gate 103's pin", G103.FROZEN_IMPLEMENTATION_SHA256, GATE_V1_5_IMPLEMENTATION_SHA256)
    _pinned("gate v1.5.0's tests", file_sha(G103.TEST_FILE), G103.FROZEN_TEST_SHA256)
    for relative, digest in MERGED_RECORD_FILES.items():
        _pinned(relative, file_sha(relative), digest)
    moved = sorted(
        k
        for k in set(COMPONENT_VERSIONS_V1_5) | set(COMPONENT_VERSIONS_V1_6)
        if COMPONENT_VERSIONS_V1_5.get(k) != COMPONENT_VERSIONS_V1_6.get(k)
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
        "MERGED_RECORD_FILES": MERGED_RECORD_FILES,
        "SUCCESSOR_FILES": {p: file_sha(p) for p in SUCCESSOR_MODULES},
        "CONTRACT_IMPLEMENTATION_SHA256": _pinned(
            "the contract implementation", implementation_sha256(), FROZEN_IMPLEMENTATION_SHA256
        ),
        "FROZEN_TEST_FILE": {
            TEST_FILE: _pinned("the contract test file", file_sha(TEST_FILE), FROZEN_TEST_SHA256)
        },
        "COMPONENT_VERSIONS_V1_6": dict(COMPONENT_VERSIONS_V1_6),
        "CHANGED_COMPONENTS": list(CHANGED_COMPONENTS),
        "SUCCESSOR_NETWORK_OR_NLP_IMPORTS": 0,
    }


# --------------------------------------------------------------------------- schema and projection


def schema_block() -> dict[str, Any]:
    _pinned(
        "schema v1.2.0",
        canonical_json_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2),
        SCHEMA_V1_2_SHA256,
    )
    diff = semantic_schema_diff(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3
    )
    leaf = "properties.candidate_intervention_class.description"
    if [p for p, _, _ in diff] != [leaf] or diff[0][2] != INTERVENTION_CLASS_DESCRIPTION:
        raise ValidationError(f"schema v1.3.0 moves {[p for p, _, _ in diff]}, not one description")
    if (
        f"the exact string {INTERVENTION_CLASS_NOT_ESTABLISHED}"
        not in INTERVENTION_CLASS_DESCRIPTION
    ):
        raise ValidationError("the class description does not state the sentinel")
    old = project_strict_input_schema(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2, ANTHROPIC_STRICT_TOOL_PROFILE_V1
    )
    new = project_strict_input_schema(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3, ANTHROPIC_STRICT_TOOL_PROFILE_V1
    )
    if old.blockers or new.blockers or old.schema is None or new.schema is None:
        raise ValidationError("a strict projection is blocked")
    _pinned(
        "the v1.2.0 strict projection",
        canonical_json_sha256(old.schema),
        STRICT_PROJECTION_V1_2_SHA256,
    )
    projected_diff = [p for p, _, _ in semantic_schema_diff(old.schema, new.schema)]
    if projected_diff != [leaf]:
        raise ValidationError(f"the strict projection moves {projected_diff}, not one description")
    if (old.optional_parameters, old.union_parameters) != (
        new.optional_parameters,
        new.union_parameters,
    ):
        raise ValidationError("the strict projection's parameter accounting moved")
    return {
        "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3,
        "SCHEMA_V1_2_0_SHA256": SCHEMA_V1_2_SHA256,
        "SCHEMA_V1_3_0_SHA256": _pinned(
            "schema v1.3.0",
            canonical_json_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3),
            SCHEMA_V1_3_SHA256,
        ),
        "SCHEMA_LEAVES_MOVED": [leaf],
        "CLASS_DESCRIPTION": INTERVENTION_CLASS_DESCRIPTION,
        "SENTINEL": INTERVENTION_CLASS_NOT_ESTABLISHED,
        "STRICT_PROFILE_UNCHANGED": True,
        "STRICT_PROJECTION_V1_2_0_SHA256": STRICT_PROJECTION_V1_2_SHA256,
        "STRICT_PROJECTION_V1_3_0_SHA256": _pinned(
            "the v1.3.0 strict projection",
            canonical_json_sha256(new.schema),
            STRICT_PROJECTION_V1_3_SHA256,
        ),
        "STRICT_PROJECTION_LEAVES_MOVED": projected_diff,
    }


# --------------------------------------------------------------------------- the prompt


def prompt_block(snapshot: tuple[Any, Any, Any, Any]) -> dict[str, Any]:
    packet, statements, pairs, metadata = snapshot
    parts_v1_6 = render_second_opportunity_prompt_v1_6(
        packet, statements, pairs, source_metadata=metadata
    )
    _pinned(
        "prompt v1.6.0 over the snapshot",
        second_opportunity_prompt_hash_v1_6(parts_v1_6),
        PROMPT_V1_6_SHA256,
    )
    parts = render_second_opportunity_prompt_v1_7(
        packet, statements, pairs, source_metadata=metadata
    )
    if parts.trusted_context != parts_v1_6.trusted_context or parts.task != parts_v1_6.task:
        raise ValidationError("prompt v1.7.0 moved a region other than the system region")
    if parts.untrusted != parts_v1_6.untrusted:
        raise ValidationError("prompt v1.7.0 moved the untrusted region")
    unstated = {
        "CONSTRAINTS": unstated_constraints_in(parts),
        "SEMANTIC_RULES": unstated_semantic_rules_in(parts),
        "HEADROOM": unstated_headroom_in(parts),
        "CONTRACT_RULES": unstated_contract_rules_in(parts),
    }
    if any(unstated.values()):
        raise ValidationError(f"prompt v1.7.0 leaves unstated {unstated}")
    flat_v1_6 = " ".join(SECOND_OPPORTUNITY_SYSTEM_V1_6.split())
    flat_v1_7 = " ".join(SECOND_OPPORTUNITY_SYSTEM_V1_7.split())
    if FORCING_SENTENCE not in flat_v1_6 or FORCING_SENTENCE in flat_v1_7:
        raise ValidationError("the forcing sentence is not where the record says it is")
    if re.search(r"\d", GENERATION_CONTRACT_BLOCK_V1_7):
        raise ValidationError("the generation-contract block carries a digit")
    left_by_v1_6 = contract.unstated_contract_rules(SECOND_OPPORTUNITY_SYSTEM_V1_6)
    return {
        "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_7,
        "GENERATION_CONTRACT_POLICY": contract.GENERATION_CONTRACT_POLICY_VERSION,
        "PROMPT_V1_6_0_SHA256_OVER_SNAPSHOT": PROMPT_V1_6_SHA256,
        "PROMPT_V1_7_0_SHA256_OVER_SNAPSHOT": _pinned(
            "prompt v1.7.0 over the snapshot",
            second_opportunity_prompt_hash_v1_7(parts),
            PROMPT_V1_7_SHA256,
        ),
        "SYSTEM_V1_7_0_SHA256": _pinned(
            "the v1.7.0 system region",
            _sha(SECOND_OPPORTUNITY_SYSTEM_V1_7.encode("utf-8")),
            PROMPT_V1_7_SYSTEM_SHA256,
        ),
        "SYSTEM_CHARACTERS": {
            "v1_6_0": len(SECOND_OPPORTUNITY_SYSTEM_V1_6),
            "v1_7_0": len(SECOND_OPPORTUNITY_SYSTEM_V1_7),
        },
        "UNSTATED_IN_V1_7_0": unstated,
        "CONTRACT_RULES_UNSTATED_BY_V1_6_0": left_by_v1_6,
        "FORCING_SENTENCE": FORCING_SENTENCE,
        "FORCING_SENTENCE_IN_V1_6_0": True,
        "FORCING_SENTENCE_IN_V1_7_0": False,
        "CONTRACT_RULES": [
            {"rule_id": r.rule_id, "enforcement": r.enforcement} for r in contract.CONTRACT_RULES
        ],
        "RUNNER_BOUND": False,
    }


# --------------------------------------------------------------------------- the class matrix

ACCEPT, REFUSE = "ACCEPT", "REFUSE"
BOTH, ONLY0, ONLY1, NONE, FOREIGN = "BOTH", "ONLY0", "ONLY1", "NONE", "FOREIGN"


class ClassCase(NamedTuple):
    case_id: str
    group: str
    value: str
    cites: str
    intended: str


CLASS_CASES: tuple[ClassCase, ...] = tuple(
    ClassCase(*row)
    for row in (
        ("NE-00", "ABSENCE", INTERVENTION_CLASS_NOT_ESTABLISHED, BOTH, ACCEPT),
        ("NE-01", "ABSENCE_NEAR_MISS", "", BOTH, REFUSE),
        ("NE-02", "ABSENCE_NEAR_MISS", "   ", BOTH, REFUSE),
        ("NE-03", "ABSENCE_NEAR_MISS", " UNKNOWN_NOT_SUPPORTED ", BOTH, REFUSE),
        ("NE-04", "ABSENCE_NEAR_MISS", "unknown_not_supported", BOTH, REFUSE),
        ("NE-05", "ABSENCE_NEAR_MISS", "NOT_ESTABLISHED", BOTH, REFUSE),
        ("NE-06", "ABSENCE_NEAR_MISS", "NOT ESTABLISHED", BOTH, REFUSE),
        ("NE-07", "ABSENCE_NEAR_MISS", "UNKNOWN_NOT_SUPPORTED: notice review", BOTH, REFUSE),
        ("NE-08", "ABSENCE_NEAR_MISS", "None", BOTH, REFUSE),
        ("SUP-01", "GROUNDED", "published notices", ONLY1, ACCEPT),
        ("SUP-02", "GROUNDED", "stated amounts of notices", BOTH, ACCEPT),
        ("SUP-03", "GROUNDED", "notice amounts", BOTH, ACCEPT),
        ("SUP-04", "GROUNDED", "classified notices", BOTH, ACCEPT),
        ("SUP-05", "GROUNDED", "set of notices from the resource", BOTH, ACCEPT),
        ("REF-01", "CITATION", "published notices", ONLY0, REFUSE),
        ("REF-02", "CITATION", "published notices", NONE, REFUSE),
        ("REF-03", "CITATION", "published notices", FOREIGN, REFUSE),
        ("UNS-01", "INVENTED", "notice monitoring", BOTH, REFUSE),
        ("UNS-02", "INVENTED", "published notices review", BOTH, REFUSE),
        ("UNS-03", "INVENTED", "procurement analytics", BOTH, REFUSE),
        ("UNS-04", "INVENTED", "notice analytics", BOTH, REFUSE),
        ("UNS-05", "INVENTED", "SaaS tool for contracting authorities", BOTH, REFUSE),
        ("UNS-06", "INVENTED", "software platform", BOTH, REFUSE),
        ("MKT-01", "MARKET_ACTIVITY", "market-observation exercise", BOTH, REFUSE),
        ("MKT-02", "MARKET_ACTIVITY", "marketplace for notices", BOTH, REFUSE),
        ("MKT-03", "MARKET_ACTIVITY", "e-market notices", BOTH, REFUSE),
        ("MKT-04", "MARKET_ACTIVITY", "market_activity notices", BOTH, REFUSE),
        ("MKT-05", "MARKET_ACTIVITY", "Market Activity monitoring", BOTH, REFUSE),
        ("MKT-06", "MARKET_ACTIVITY", "market activity review", BOTH, REFUSE),
        ("MKT-07", "MARKET_ACTIVITY", "market activity", BOTH, REFUSE),
        ("MKT-08", "MARKET_ACTIVITY", "markets for notices", BOTH, REFUSE),
        ("CH-01", "CHANNEL", "register notices", BOTH, REFUSE),
        ("CH-02", "CHANNEL", "daily notices", BOTH, REFUSE),
        ("CH-03", "CHANNEL", "synthetic notices", BOTH, REFUSE),
        ("CH-04", "CHANNEL", "economic value notices", BOTH, REFUSE),
        ("CH-05", "CHANNEL", "buyer budget", BOTH, REFUSE),
        ("CH-06", "CHANNEL", "contract notices", BOTH, REFUSE),
        ("CH-07", "CHANNEL", "awards notices", BOTH, REFUSE),
        ("ID-01", "IDENTIFIER", "CPV", BOTH, REFUSE),
        ("ID-02", "IDENTIFIER", "CPV notices", BOTH, REFUSE),
        ("ID-03", "IDENTIFIER", "TOTAL_VALUE", BOTH, REFUSE),
        ("ID-04", "IDENTIFIER", "BT-161 notices", BOTH, REFUSE),
        ("ID-05", "IDENTIFIER", "CONTRACT_NOTICE", BOTH, REFUSE),
        ("ID-06", "IDENTIFIER", "notices under CPV class 5555", BOTH, REFUSE),
        ("ID-07", "IDENTIFIER", "notices exceeding 120000 EUR", BOTH, REFUSE),
        ("UNI-01", "CHARACTERS", "Márket review", BOTH, REFUSE),
        ("UNI-02", "CHARACTERS", "m a r k e t review", BOTH, REFUSE),
        ("UNI-03", "CHARACTERS", "MARKET review", BOTH, REFUSE),
        ("UNI-04", "CHARACTERS", "mar​ket notices", BOTH, REFUSE),
        ("UNI-05", "CHARACTERS", "mаrket notices", BOTH, REFUSE),
        ("UNI-06", "CHARACTERS", "ｍａｒｋｅｔ notices", BOTH, REFUSE),
        ("UNI-07", "CHARACTERS", "publishеd notices", BOTH, REFUSE),
        ("UNI-08", "CHARACTERS", "SaaS­ platform", BOTH, REFUSE),
        ("DEN-01", "DENIAL_OR_CLAUSE", "no market study", BOTH, REFUSE),
        ("DEN-02", "DENIAL_OR_CLAUSE", "no intervention class is supported", BOTH, REFUSE),
        ("DEN-03", "DENIAL_OR_CLAUSE", "not published notices", BOTH, REFUSE),
        (
            "DEN-04",
            "DENIAL_OR_CLAUSE",
            "published notices review; buyers are willing to pay",
            BOTH,
            REFUSE,
        ),
        ("DEN-05", "DENIAL_OR_CLAUSE", "notices exceeded the smallest amount", BOTH, REFUSE),
        (
            "DEN-06",
            "DENIAL_OR_CLAUSE",
            "No intervention class is supported; only an inquiry into the published notices could "
            "be scoped.",
            BOTH,
            REFUSE,
        ),
        (
            "LEN-01",
            "SHAPE",
            "stated amounts of notices in the bounded set of the resource",
            BOTH,
            REFUSE,
        ),
        ("LEN-02", "SHAPE", "of the and", BOTH, REFUSE),
    )
)


def _citations(fx: Any, cites: str) -> tuple[list[str], list[str]]:
    c0, c1 = fx.CLAIMS
    e0, e1 = fx.EVIDENCE
    return {
        BOTH: ([c0, c1], [e0, e1]),
        ONLY0: ([c0], [e0]),
        ONLY1: ([c1], [e1]),
        NONE: ([], []),
        FOREIGN: (["cccccccc-cccc-4ccc-8ccc-000000000000"], [e1]),
    }[cites]


def _gates(
    output: dict[str, Any], packet: Any, statements: Any, pairs: Any, trusted: Any, meta: Any
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    arguments = {"trusted_context": trusted, "source_metadata": meta}
    old = evaluate_second_opportunity_output_v1_5(output, packet, statements, pairs, **arguments)
    new = evaluate_second_opportunity_output_v1_6(output, packet, statements, pairs, **arguments)
    return old.refusal_reasons, new.refusal_reasons


def differential(old: Sequence[str], new: Sequence[str]) -> list[str]:
    """v1.6.0's reasons are v1.5.0's, structure renamed, then class-grounding reasons only."""
    renamed = [
        STRUCTURAL_REASON_PREFIX + r[len(PREDECESSOR_STRUCTURAL_REASON_PREFIX) :]
        if r.startswith(PREDECESSOR_STRUCTURAL_REASON_PREFIX)
        else r
        for r in old
    ]
    if list(new[: len(renamed)]) != renamed:
        raise ValidationError(f"gate v1.6.0 does not keep v1.5.0's reasons: {list(new)[:2]}")
    added = list(new[len(renamed) :])
    if any(not r.startswith(CLASS_GROUNDING_REASON_PREFIX) for r in added):
        raise ValidationError(f"gate v1.6.0 adds a reason that is not class grounding: {added}")
    return added


def class_block(fx: Any) -> dict[str, Any]:
    if "MARKET_ACTIVITY" not in {d.value for d in fx.PACKET.counting_dimensions}:
        raise ValidationError("the fixture does not supply MARKET_ACTIVITY, so no leak is tested")
    universe = build_typed_support_universe(fx.PACKET, fx.STATEMENTS, fx.TRUSTED, fx.META)
    content = " ".join(s.content for s in universe.statements).lower()
    rows = []
    seen: set[str] = set()
    for case in CLASS_CASES:
        if case.case_id in seen:
            raise ValidationError(f"{case.case_id} appears twice")
        seen.add(case.case_id)
        claims, evidence = _citations(fx, case.cites)
        output = fx.good_output(
            candidate_intervention_class=case.value,
            supporting_claim_ids=claims,
            supporting_evidence_ids=evidence,
        )
        old, new = _gates(output, fx.PACKET, fx.STATEMENTS, fx.E2C, fx.TRUSTED, fx.META)
        added = differential(old, new)
        stray = [r for r in new if not r.startswith("candidate_intervention_class ")]
        if stray and case.cites not in (NONE, FOREIGN):
            raise ValidationError(f"{case.case_id} is refused outside the class: {stray[0]}")
        verdict = REFUSE if new else ACCEPT
        if verdict != case.intended:
            raise ValidationError(
                f"{case.case_id} {case.value!r}: v1.6.0 {verdict}, intended {case.intended}"
            )
        if case.group == "MARKET_ACTIVITY" and not added:
            raise ValidationError(
                f"{case.case_id}: the class grounding does not refuse {case.value!r}"
            )
        rows.append(
            {
                "case": case.case_id,
                "group": case.group,
                "value": case.value,
                "cites": case.cites,
                "intended": case.intended,
                "v1_5_0": REFUSE if old else ACCEPT,
                "v1_6_0": verdict,
                "class_grounding_reasons": [r[len(CLASS_GROUNDING_REASON_PREFIX) :] for r in added],
                "v1_6_0_other_reasons": len(new) - len(added),
            }
        )
    opened = [r["case"] for r in rows if r["v1_5_0"] == REFUSE and r["v1_6_0"] == ACCEPT]
    if opened:
        raise ValidationError(f"gate v1.6.0 accepts what v1.5.0 refused: {opened}")
    groups: dict[str, int] = {}
    for r in rows:
        groups[r["group"]] = groups.get(r["group"], 0) + 1
    return {
        "fixture": f"{TESTS}/test_semantic_gate_v1_3.py",
        "CASES": len(rows),
        "BY_GROUP": dict(sorted(groups.items())),
        "cases": rows,
        "AS_INTENDED": len(rows),
        "NEWLY_REFUSED_BY_V1_6_0": [
            r["case"] for r in rows if r["v1_5_0"] == ACCEPT and r["v1_6_0"] == REFUSE
        ],
        "ACCEPTED_BY_V1_5_0_AND_REFUSED_BY_V1_6_0_IS_THE_ONLY_MOVEMENT": True,
        "MARKET_ACTIVITY_SUPPLIED_IN_FIXTURE": True,
        "MARKET_WORD_IN_FIXTURE_CONTENT": bool(inflection_spans(content, "market")),
        "MARKET_ACTIVITY_LEAKS_INTO_THE_CLASS": False,
        "GROUNDING_VERSION": grounding.INTERVENTION_CLASS_GROUNDING_VERSION,
        "CLASS_FUNCTION_WORDS": sorted(grounding.CLASS_FUNCTION_WORDS),
        "MAX_CLASS_WORDS": grounding.MAX_CLASS_WORDS,
    }


# --------------------------------------------------------------------------- every other field

#: Intervention vocabulary written outside the class while the class is absent. Recorded, not repaired.
DISPLACEMENT_CASES: tuple[tuple[str, str, object], ...] = (
    (
        "SMG-01",
        "hypothesis_statement",
        "Contracting authorities could adopt a notice monitoring service.",
    ),
    ("SMG-02", "observed_need", "Authorities need a notice monitoring service."),
    (
        "SMG-03",
        "recommended_next_evidence",
        ["Evidence of whether authorities would buy a notice monitoring service."],
    ),
    (
        "SMG-04",
        "critical_uncertainties",
        ["Whether a notice monitoring service suits these authorities."],
    ),
    ("SMG-05", "commercial_claims_not_supported", ["A notice monitoring service is wanted."]),
    (
        "SMG-06",
        "target_actor_if_supported",
        "Authorities that would use a notice monitoring service.",
    ),
    ("SMG-07", "observed_need", "The notices record market activity."),
    ("SMG-08", "hypothesis_statement", "Whether a market for notice software exists is unknown."),
)


def other_fields_block(fx: Any) -> dict[str, Any]:
    sentinel = INTERVENTION_CLASS_NOT_ESTABLISHED
    compared = 0
    for case in G103.CASES:
        output = fx.good_output(candidate_intervention_class=sentinel, observed_need=case.sentence)
        old, new = _gates(output, fx.PACKET, fx.STATEMENTS, fx.E2C, fx.TRUSTED, fx.META)
        if old != new:
            raise ValidationError(f"gate 103's {case.case_id} reads differently under v1.6.0")
        compared += 1
    displacement = []
    for case_id, field, value in DISPLACEMENT_CASES:
        output = fx.good_output(candidate_intervention_class=sentinel, **{field: value})
        old, new = _gates(output, fx.PACKET, fx.STATEMENTS, fx.E2C, fx.TRUSTED, fx.META)
        if old != new:
            raise ValidationError(f"{case_id} reads differently under v1.6.0")
        displacement.append(
            {
                "case": case_id,
                "field": field,
                "value": value,
                "v1_5_0": REFUSE if old else ACCEPT,
                "v1_6_0": REFUSE if new else ACCEPT,
                "status": "UNCHANGED_DEBT",
            }
        )
    return {
        "GATE_103_SENTENCES_IN_OBSERVED_NEED_WITH_THE_CLASS_ABSENT": compared,
        "REASON_DIFFERENCES": 0,
        "DISPLACEMENT_CASES": displacement,
        "DISPLACEMENT_ACCEPTED_BY_BOTH": [d["case"] for d in displacement if d["v1_6_0"] == ACCEPT],
    }


# --------------------------------------------------------------------------- V9 and V10


def snapshot() -> tuple[Any, Any, Any, Any]:
    packet, statements, pairs = G103.G101.snapshot_packet()
    metadata = G103.G101.runner().source_metadata_for(list(packet.source_ids))
    return packet, statements, pairs, metadata


def history_block(snap: tuple[Any, Any, Any, Any]) -> dict[str, Any]:
    """V9 and V10 read diagnostically: records untouched, v1.5.0 as gate 103 recorded, v1.6.0 beside."""
    try:
        v10 = G103.G101.validate()
        v9 = G103.G98.validate()
    except (G103.G101.ValidationError, G103.G98.ValidationError) as exc:
        raise ValidationError(
            f"a historical execution no longer stands as recorded: {exc}"
        ) from exc
    recorded = json.loads(G103.RECORD.read_text(encoding="utf-8"))["HISTORY"]
    packet, statements, pairs, metadata = snap
    trusted = build_trusted_context(packet)
    out: dict[str, Any] = {}
    for label, gate, record in (("V9", G103.G98, v9), ("V10", G103.G101, v10)):
        _pinned(
            f"{label}'s response",
            file_sha(str(gate.RESPONSE.relative_to(ROOT))),
            gate.RESPONSE_FILE_SHA256,
        )
        _pinned(
            f"{label}'s record",
            file_sha(str(gate.RECORD.relative_to(ROOT))),
            gate.RECORD_FILE_SHA256,
        )
        parsed = json.loads(gate.RESPONSE.read_text(encoding="utf-8"))["parsed_output"]
        old, new = _gates(parsed, packet, statements, pairs, trusted, metadata)
        if list(old) != recorded[label]["V1_5_0_WOULD_REFUSE_WITH"]:
            raise ValidationError(f"gate v1.5.0 no longer gives what gate 103 recorded for {label}")
        added = differential(old, new)
        if not new:
            raise ValidationError(f"gate v1.6.0 would accept {label}")
        out[label] = {
            "HISTORICAL_OUTCOME": record["PRIMARY_OUTCOME"],
            "HISTORICAL_RECORD_EDITED": False,
            "CANDIDATE_INTERVENTION_CLASS": parsed.get("candidate_intervention_class"),
            "V1_5_0_REFUSES_WITH": list(old),
            "V1_6_0_WOULD_REFUSE_WITH": list(new),
            "V1_6_0_WOULD_ADD": added,
            "V1_6_0_WOULD_PERSIST": False,
        }
    v11 = sorted(
        str(p.relative_to(ROOT))
        for base in (DATA, SCRIPTS, ROOT / PACKAGE, ROOT / TESTS)
        for p in base.glob("*v11*")
    )
    if v11:
        raise ValidationError(f"a V11 artifact exists: {v11}")
    bound = sorted(
        p.name
        for p in SCRIPTS.glob("*.py")
        if p.name != pathlib.Path(THIS_SCRIPT).name
        and re.search(
            r"second_opportunity_prompt_v1_7|second_opportunity_gate_v1_6|second_opportunity_schema_v1_3",
            p.read_text(encoding="utf-8"),
        )
    )
    if bound:
        raise ValidationError(f"a script binds the successor contract: {bound}")
    out["V11_ARTIFACTS"] = 0
    out["SCRIPTS_BINDING_THE_SUCCESSOR_CONTRACT"] = 0
    return out


# --------------------------------------------------------------------------- the record


def derive() -> dict[str, Any]:
    fx = _module("frozen_v1_3_fixture_for_gate_104", FIXTURE)
    with no_network():
        snap = snapshot()
        frozen = frozen_block()
        schema = schema_block()
        prompt = prompt_block(snap)
        classes = class_block(fx)
        others = other_fields_block(fx)
        history = history_block(snap)
    return {
        "$comment": (
            "Generated by infrastructure/scripts/render_second_opportunity_intervention_class_contract.py "
            "(CI gate 104). Every field is re-derived at check time; V9's and V10's recorded verdicts are "
            "unchanged, and what gate v1.6.0 would say is recorded beside them, never over them."
        ),
        "MISSION": MISSION,
        "START_COMMIT": START_COMMIT,
        "BRANCH": BRANCH,
        "PRIMARY_OUTCOME": PRIMARY_OUTCOME,
        "GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_6,
        "PREDECESSOR_GATE_VERSION": PREDECESSOR_GATE_VERSION,
        "OPERATOR_DECISION": list(OPERATOR_DECISION_V1_6),
        "INVARIANTS": INVARIANTS,
        "NOT_CHANGED": NOT_CHANGED,
        "FROZEN": frozen,
        "SCHEMA": schema,
        "PROMPT": prompt,
        "CLASS_MATRIX": classes,
        "OTHER_FIELDS": others,
        "HISTORY": history,
        "SEMANTIC_DEBT": list(SEMANTIC_DEBT),
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
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_intervention_class_contract.py "
    "from second-opportunity-intervention-class-contract-v1.json. Do not edit by hand. -->\n\n"
)


def _cell(text: object) -> str:
    return json.dumps(text, ensure_ascii=True).replace("|", "\\|").replace("\n", " ")


def render(record: dict[str, Any]) -> str:
    frozen, schema, prompt = record["FROZEN"], record["SCHEMA"], record["PROMPT"]
    classes, others, history = record["CLASS_MATRIX"], record["OTHER_FIELDS"], record["HISTORY"]
    out = [
        HEADER.rstrip("\n"),
        "",
        f"# The intervention-class contract ({record['MISSION']})",
        "",
        f"**`{record['PRIMARY_OUTCOME']}`**, from `{record['START_COMMIT']}`.",
        "",
        f"`{record['GATE_VERSION']}` beside `{record['PREDECESSOR_GATE_VERSION']}`, over "
        f"`{schema['OUTPUT_SCHEMA_VERSION']}`, stated by prompt `{prompt['PROMPT_VERSION']}` "
        f"(`{prompt['GENERATION_CONTRACT_POLICY']}`). No runner is bound; D4 is not authorised.",
        "",
        "## Frozen",
        "",
        f"- contract implementation `{frozen['CONTRACT_IMPLEMENTATION_SHA256']}`",
        *(f"- test file `{p}` `{d}`" for p, d in frozen["FROZEN_TEST_FILE"].items()),
        *(
            f"- {k} `{d}` (recomputed)"
            for k, d in frozen["PREDECESSOR_IMPLEMENTATION_SHA256"].items()
        ),
        *(f"- `{p}` `{d}`" for p, d in frozen["MERGED_RECORD_FILES"].items()),
        f"- components moved: {', '.join(frozen['CHANGED_COMPONENTS'])}",
        "",
        "## Schema and projection",
        "",
        f"- schema v1.2.0 `{schema['SCHEMA_V1_2_0_SHA256']}`, v1.3.0 `{schema['SCHEMA_V1_3_0_SHA256']}`; "
        f"leaves moved: {', '.join(schema['SCHEMA_LEAVES_MOVED'])}",
        f"- strict projection over v1.2.0 `{schema['STRICT_PROJECTION_V1_2_0_SHA256']}`, over v1.3.0 "
        f"`{schema['STRICT_PROJECTION_V1_3_0_SHA256']}`; profile unchanged; leaves moved: "
        f"{', '.join(schema['STRICT_PROJECTION_LEAVES_MOVED'])}",
        f"- class description: {schema['CLASS_DESCRIPTION']}",
        "",
        "## Prompt",
        "",
        f"- v1.6.0 over the snapshot `{prompt['PROMPT_V1_6_0_SHA256_OVER_SNAPSHOT']}` (unchanged); v1.7.0 "
        f"`{prompt['PROMPT_V1_7_0_SHA256_OVER_SNAPSHOT']}`, system region "
        f"`{prompt['SYSTEM_V1_7_0_SHA256']}`",
        f"- system characters {prompt['SYSTEM_CHARACTERS']['v1_6_0']} (v1.6.0), "
        f"{prompt['SYSTEM_CHARACTERS']['v1_7_0']} (v1.7.0); nothing unstated in v1.7.0",
        f"- contract rules v1.6.0 leaves unstated: {', '.join(prompt['CONTRACT_RULES_UNSTATED_BY_V1_6_0'])}",
        f"- the forcing sentence (*{prompt['FORCING_SENTENCE']}*) is in v1.6.0 and not in v1.7.0",
        *(f"- `{r['rule_id']}` {r['enforcement']}" for r in prompt["CONTRACT_RULES"]),
        "",
        "## Class matrix",
        "",
        f"{classes['CASES']} cases on `{classes['fixture']}`, all as intended. Newly refused by v1.6.0: "
        f"{', '.join(classes['NEWLY_REFUSED_BY_V1_6_0'])}. Nothing v1.5.0 refused is accepted. "
        "MARKET_ACTIVITY is supplied and no class carrying `market` passes.",
        "",
        "| case | group | value | cites | v1.5.0 | v1.6.0 | class grounding |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in classes["cases"]:
        out.append(
            f"| {r['case']} | {r['group']} | {_cell(r['value'])} | {r['cites']} | {r['v1_5_0']} | "
            f"{r['v1_6_0']} | {len(r['class_grounding_reasons'])} |"
        )
    out += [
        "",
        "## Every other field",
        "",
        f"{others['GATE_103_SENTENCES_IN_OBSERVED_NEED_WITH_THE_CLASS_ABSENT']} gate 103 sentences in "
        "`observed_need` with the class absent: reasons identical under both gates.",
        "",
        "Displacement cases (unchanged debt):",
        "",
        "| case | field | value | v1.5.0 | v1.6.0 |",
        "|---|---|---|---|---|",
        *(
            f"| {d['case']} | {d['field']} | {_cell(d['value'])} | {d['v1_5_0']} | {d['v1_6_0']} |"
            for d in others["DISPLACEMENT_CASES"]
        ),
        "",
        "## V9 and V10, diagnostically",
        "",
    ]
    for label in ("V9", "V10"):
        h = history[label]
        out.append(
            f"- **{label}** `{h['HISTORICAL_OUTCOME']}`, record unchanged; class "
            f"{_cell(h['CANDIDATE_INTERVENTION_CLASS'])}; v1.5.0 refuses with "
            f"{len(h['V1_5_0_REFUSES_WITH'])}, v1.6.0 would refuse with "
            f"{len(h['V1_6_0_WOULD_REFUSE_WITH'])} (adding {len(h['V1_6_0_WOULD_ADD'])})."
        )
    out += ["", "## Semantic debt", "", *(f"- {d}" for d in record["SEMANTIC_DEBT"]), ""]
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
        "ok       schema v1.3.0, gate v1.6.0 and prompt v1.7.0 hold the class contract; every "
        "predecessor and V9 and V10 untouched"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
