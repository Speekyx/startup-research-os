"""Mission 1.84.11, CI gate 77. The semantic output gate v1.3.0, frozen before the V3 diagnostic replay.

Gate v1.2.0's one diagnostic replay found an asymmetry in its own marker licence: a plural fold on
the answer's side of the check and exact tokens on the supplied side. The operator decided to repair
it generally, and decided that a source's name is not factual support. The repair is a new gate
version, frozen before V3's answer is replayed through it, because a gate changed after seeing how an
answer fares is tuned on that answer. This gate makes the order checkable:

* the freeze record is DERIVED from the live code, and must equal what the code derives now;
* the v1.3.0 implementation and its frozen test file are pinned by digest HERE, so a later `--write`
  cannot re-freeze a changed gate without an edit to this file that a reviewer sees;
* gate v1.2.0 still validates through CI gate 75, so it is byte-identical to its own freeze, and the
  modules v1.0.0 and v1.1.0 run on are still bb0f50a's;
* the ONE inflection function is checked by behaviour, not by name: every gated term is supplied and
  asserted in both of its numbers, and a word supplied only inside a source's name must be refused.
  A code change that folds one side and not the other fails here;
* no v1.3.0 module other than `lexical_inflection.py` takes a token apart;
* the source-metadata evidence-boundary decision is re-derived from the code, owner, type and all;
* no run of the historical answer is in the gate or its tests beyond the brief's own cases.

    uv run python infrastructure/scripts/render_second_opportunity_semantic_gate_v1_3.py --check
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import re
from typing import Any

from sros_opportunity import (
    EvidenceFacets,
    IndependenceState,
    PacketEligibility,
    ReliabilityStatus,
    build_packet,
)
from sros_opportunity.assertion_audit_v1_3 import (
    ANSWER_MARKER_NORMALIZATION_POLICY,
    ANSWER_MARKER_NORMALIZER,
    DISJUNCTION_POLICY_VERSION,
    DISJUNCTIVE_OBSERVED_STATEMENT,
    LEXICAL_MATCH_IS_FACTUAL_SUPPORT,
    SOURCE_METADATA_NOT_FACTUAL_SUPPORT,
    SUPPORT_TOKEN_NORMALIZATION_POLICY,
    SUPPORT_TOKEN_NORMALIZER,
    audit_text,
)
from sros_opportunity.assertion_context import (
    Disposition,
    PacketStructuralFacts,
    Shape,
    TrustedContext,
)
from sros_opportunity.guards import FORBIDDEN_TERMS
from sros_opportunity.lexical_inflection import (
    INFLECTION_NOT_COVERED,
    INFLECTION_RULES,
    LEXICAL_INFLECTION_POLICY_VERSION,
    normalize_token,
)
from sros_opportunity.mapping import SIGNAL_DIMENSION_MAP
from sros_opportunity.second_opportunity import (
    PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
)
from sros_opportunity.second_opportunity_gate_v1_2 import (
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_2,
)
from sros_opportunity.second_opportunity_gate_v1_3 import (
    COMPONENT_VERSIONS_V1_3,
    OPERATOR_DECISION_V1_3,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
    SOURCE_METADATA_CONTEXT_VERSION,
    SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION,
)
from sros_opportunity.support_origin import (
    SUPPORT_UNIVERSE_VERSION_V2,
    SourceMetadataContext,
    SourceMetadataLabel,
    SourceMetadataLabelKind,
    SupportOrigin,
    build_typed_support_universe,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
RECORD = DATA / "second-opportunity-output-gate-v1.3-freeze-v1.json"
RECORD_MD = DATA / "second-opportunity-output-gate-v1.3-freeze-v1.md"
DECISION = DATA / "source-metadata-evidence-boundary-decision-v1.json"
DECISION_MD = DATA / "source-metadata-evidence-boundary-decision-v1.md"
RESPONSE_V3 = DATA / "second-opportunity-synthesis-response-v3.json"
GATE_V1_2 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_2.py"
ADR = "docs/architecture/adr/ADR-040-source-metadata-is-provenance-not-factual-support.md"
PACKAGE = "packages/opportunity-engine/python/sros_opportunity"
TESTS = "packages/opportunity-engine/python/tests"

MISSION = "mission-1.84.11"
IMPLEMENTATION_FILES = (
    f"{PACKAGE}/lexical_inflection.py",
    f"{PACKAGE}/support_origin.py",
    f"{PACKAGE}/assertion_audit_v1_3.py",
    f"{PACKAGE}/second_opportunity_gate_v1_3.py",
)
TEST_FILE = f"{TESTS}/test_semantic_gate_v1_3.py"
#: The one module allowed to take a token apart.
CANONICAL_MODULE = f"{PACKAGE}/lexical_inflection.py"

#: Pinned at the freeze. Editing either is re-freezing, and re-freezing is a new gate version.
FROZEN_IMPLEMENTATION_SHA256 = "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3"
FROZEN_TEST_SHA256 = "6d7ad83150323293c78a998f9a880e6abd27e229a576b7b6f4d8fd6b940b80c3"

OUTPUT_SCHEMA_SHA256 = "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
PROMPT_SHA256 = "1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"

REQUIRED_DECISION = (
    "FIX_SYMMETRIC_INFLECTION_NORMALIZATION = true",
    "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false",
    "SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = true",
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_PROMPT_V1_2_0_UNCHANGED",
    "KEEP_HISTORICAL_GATE_V1_1_0_UNCHANGED",
    "KEEP_FROZEN_GATE_V1_2_0_UNCHANGED",
    "DO_NOT_WHITELIST_THE_V3_ANSWER",
    "DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES",
)
REQUIRED_BOUNDARY = {
    "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT": False,
    "SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS": True,
    "decision_owner": "OPERATOR",
    "decision_type": "EVIDENCE_BOUNDARY",
    "mathematically_derived": False,
    "moved_into_packet_structural_facts": False,
    "independent_of_any_answer": True,
}
REQUIRED_ORIGINS = (
    "SOURCE_CONTENT_STATEMENT",
    "SOURCE_METADATA_LABEL",
    "PACKET_STRUCTURAL_FACT",
    "TRUSTED_LIMITING_OR_DEFINITIONAL_FACT",
)
#: §6, §17: pairs the policy must fold together, and pairs it must never collapse.
MUST_FOLD = (
    ("tender", "tenders"),
    ("contract", "contracts"),
    ("notice", "notices"),
    ("buyer", "buyers"),
)
MUST_NOT_COLLAPSE = (
    ("market", "marketing"),
    ("pay", "payment"),
    ("score", "scoring"),
    ("value", "valuable"),
    ("analysis", "analyses"),
    ("person", "people"),
)
#: The cases the operator's briefs state word for word (1.84.11 §9, §14, §17 to §19, and 1.84.10's
#: which the parity tests reuse). They are the ONLY text the frozen tests may share with the
#: historical answer, and the implementation may share none at all.
BRIEF_CASES = (
    "Contracts were published.",
    "A contract was published.",
    "Notices exist.",
    "A notice exists.",
    "Contracts occur.",
    "Buyers exist in this market.",
    "Market activity is established.",
    "Tenders occur.",
    "Tenders occur in CPV class 9261.",
    "The source is Tenders Electronic Daily.",
    "The source family is public_procurement.",
    "Published tenders were observed for CPV class 9261.",
    "Customers are willing to pay.",
    "The evidence establishes willingness to pay.",
    "No evidence establishes willingness to pay.",
    "Willingness to pay is not established.",
    "Actual expenditure is not established, but is probably substantial.",
    "These rows are not unscored; they are scored.",
    "Evidence of actual expenditure would be required.",
    "Actual expenditure was 10 million EUR.",
)
#: The frozen test classes the brief's matrices live in, and the smallest case count each holds.
MATRIX_CLASSES = {
    "TestSection6InflectionPolicy": 36,
    "TestSection17InflectionMatrix": 11,
    "TestSection18MetadataMatrix": 4,
    "TestSection19ProvenanceMayUseMetadata": 5,
    "TestSection13LexicalMatchIsNotFactualSupport": 6,
    "TestSection15Disjunction": 12,
    "TestAdversarialNames": 6,
    "TestThePredecessorReadingIsKept": 8,
}
ZERO_ACCOUNTING = (
    "MODEL_CALLS",
    "PROVIDER_REQUESTS",
    "MESSAGES_API_REQUESTS",
    "TED_BYTES_SENT",
    "CANONICAL_MUTATIONS",
)


class ValidationError(RuntimeError):
    """The freeze record disagrees with the live code, or with what the brief requires."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(relative: str) -> str:
    return _sha((ROOT / relative).read_bytes())


def text_sha(path: pathlib.Path) -> str:
    """A document's digest over its text with LF line ends, whatever the checkout wrote."""
    return _sha(path.read_text(encoding="utf-8").encode("utf-8"))


def implementation_sha256() -> str:
    """One digest over the implementation files, path and bytes, in a fixed order."""
    return _sha("".join(f"{p}\x00{file_sha(p)}\n" for p in IMPLEMENTATION_FILES).encode("utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ============================================================================= synthetic probes

_EVIDENCE = ("55555555-5555-4555-8555-555555555555",)
_CLAIM = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
_SOURCE = "gate-77-synthetic-source"


def _packet() -> Any:
    mapping = SIGNAL_DIMENSION_MAP["procurement_value_contrast"]
    facets = EvidenceFacets(
        evidence_id=_EVIDENCE[0],
        claim_id=_CLAIM,
        source_id=_SOURCE,
        source_family="public_procurement",
        use_profile_id="local-private-research-v1",
        extraction_method="deterministic",
        claim_type="OBSERVED",
        claim_lifecycle="ACTIVE",
        claim_temporality="EVERGREEN",
        claim_origin="DETERMINISTIC_EXTRACTION",
        direction="SUPPORTS",
        observation_category="UNCATEGORISED",
        evidence_level=1,
        relevance=1.0,
        directness=1.0,
        extraction_confidence=1.0,
        reliability=0.5,
        reliability_status=ReliabilityStatus.RESOLVED,
        independence_state=IndependenceState.UNKNOWN,
        independence_group_id=None,
        observed_at=None,
        signal_type_id="procurement_value_contrast",
        dimensions=mapping.dimensions,
        dimension_bound=mapping.bound,
    )
    return build_packet(None, "gate-77", ((facets, PacketEligibility.ELIGIBLE_SCORING),))


_PACKET = _packet()


def _findings(answer: str, statement: str, label: str) -> tuple[str, ...]:
    universe = build_typed_support_universe(
        _PACKET,
        {_CLAIM: statement},
        TrustedContext(version="gate-77", facts=()),
        SourceMetadataContext(
            version=SOURCE_METADATA_CONTEXT_VERSION,
            labels=(
                SourceMetadataLabel(
                    "gate-77:0",
                    _SOURCE,
                    SourceMetadataLabelKind.SOURCE_NAME,
                    label,
                    "a synthetic label built by CI gate 77",
                ),
            ),
        ),
    )
    _verdict, findings = audit_text(
        answer,
        Disposition.SUPPORTED_ASSERTION,
        Shape.FREE,
        universe,
        FORBIDDEN_CONCEPTS_V1_2,
        PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
        frozenset(_PACKET.counting_dimensions),
    )
    return findings


def _form(phrase: str) -> str:
    return " ".join(normalize_token(t) for t in re.findall(r"[a-z0-9]+", phrase.lower()))


def symmetry_matrix() -> dict[str, int]:
    """Every gated marker and concept phrase, supplied and asserted in both of its numbers.

    Licensing must not depend on which side carries which number, a supplied occurrence must
    license, an absent one must not, and one inside a source's name must be refused by name.
    """
    counts = {
        "markers": 0,
        "concept_phrases": 0,
        "asymmetries": 0,
        "unlicensed_absences_missed": 0,
        "metadata_leaks": 0,
    }
    label = "Gate Gazette"
    seen: set[str] = set()
    for marker in PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS:
        if _form(marker) in seen:
            continue
        seen.add(_form(marker))
        counts["markers"] += 1
        forms = {marker}
        if normalize_token(marker + "s") == normalize_token(marker):
            forms.add(marker + "s")

        def refused(findings: tuple[str, ...], marker: str = marker) -> bool:
            return any(
                f.startswith(f"{marker!r} appears in no source content statement")
                or f.startswith(f"{SOURCE_METADATA_NOT_FACTUAL_SUPPORT}: {marker!r}")
                for f in findings
            )

        for supplied in forms:
            for asserted in forms:
                if refused(
                    _findings(f"Records show {asserted} here.", f"Notes mention {supplied}.", label)
                ):
                    counts["asymmetries"] += 1
        if not refused(_findings(f"Records show {marker} here.", "Notes were filed.", label)):
            counts["unlicensed_absences_missed"] += 1
        name = f"{marker.title()} Gazette"
        findings = _findings(
            f"Records show {marker} here.", f"{name} reported that notes were filed.", name
        )
        if not any(f.startswith(SOURCE_METADATA_NOT_FACTUAL_SUPPORT) for f in findings):
            counts["metadata_leaks"] += 1
    for concept in FORBIDDEN_CONCEPTS_V1_2:
        for phrase in concept.phrases:
            counts["concept_phrases"] += 1
            head = f"{concept.name}: {phrase!r} is asserted"

            def flagged(findings: tuple[str, ...], head: str = head) -> bool:
                return any(f.startswith(head) for f in findings)

            if flagged(
                _findings(f"Records show {phrase} here.", f"Notes mention {phrase}.", label)
            ):
                counts["asymmetries"] += 1
            if not flagged(_findings(f"Records show {phrase} here.", "Notes were filed.", label)):
                counts["unlicensed_absences_missed"] += 1
            name = f"{phrase.title()} Gazette"
            findings = _findings(
                f"Records show {phrase} here.", f"{name} reported that notes were filed.", name
            )
            if not any(f.startswith(head) and "metadata label" in f for f in findings):
                counts["metadata_leaks"] += 1
    return counts


def asymmetry_of_v1_2() -> str:
    """§3, re-derived: v1.2.0 folds the answer and compares the supply exactly."""
    from sros_opportunity.assertion_context import _spans, build_support_universe
    from sros_opportunity.assertion_context import audit_text as audit_text_v1_2

    universe = build_support_universe(
        _PACKET,
        {_CLAIM: "Suppliers published notices listing their tenders."},
        TrustedContext(version="gate-77", facts=()),
    )
    _verdict, findings = audit_text_v1_2(
        "A tender was published.",
        Disposition.SUPPORTED_ASSERTION,
        Shape.FREE,
        universe,
        FORBIDDEN_CONCEPTS_V1_2,
        PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
        frozenset(_PACKET.counting_dimensions),
    )
    folds_answer = bool(_spans("tenders", "tender"))
    exact_supply = "tender" not in universe.supplied_tokens()
    refused = any("'tender' appears in no supplied statement" in f for f in findings)
    return "ESTABLISHED" if folds_answer and exact_supply and refused else "NOT_REPRODUCED"


def one_canonical_function() -> list[str]:
    """Where a v1.3.0 module other than the canonical one takes a token apart itself."""
    problems: list[str] = []
    for path in IMPLEMENTATION_FILES:
        if path == CANONICAL_MODULE:
            continue
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in {
                "endswith",
                "rstrip",
                "removesuffix",
            }:
                problems.append(f"{path}:{node.lineno} calls .{node.attr}")
            if isinstance(node, ast.FunctionDef) and "normali" in node.name:
                problems.append(f"{path}:{node.lineno} defines {node.name}")
            if isinstance(node, ast.ImportFrom) and node.module == "assertion_context":
                banned = {a.name for a in node.names} & {
                    "_spans",
                    "_phrase_tokens",
                    "classify",
                    "is_asserted",
                    "audit_text",
                    "build_support_universe",
                }
                if banned:
                    problems.append(f"{path} imports v1.2.0's {sorted(banned)}")
    return problems


def justified_by() -> dict[str, list[str]]:
    """Which gated tokens each adopted plural rule is for, and which would need one not adopted."""
    tokens = sorted(
        {
            t
            for phrase in (
                *PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
                *(p for c in FORBIDDEN_CONCEPTS_V1_2 for p in c.phrases),
                *FORBIDDEN_TERMS,
            )
            for t in re.findall(r"[a-z]+", phrase.lower())
        }
    )
    nouns_ly = re.compile(r"ly$")
    return {
        "REGULAR_IES_PLURAL": [
            t
            for t in tokens
            if re.search(r"[bcdfghjklmnpqrstvwxz]y$", t) and not nouns_ly.search(t)
        ],
        "REGULAR_SSES_PLURAL": [t for t in tokens if t.endswith("ss")],
        "OTHER_ES_PLURALS_NEEDED": [t for t in tokens if re.search(r"(x|ch|sh|z)$", t)],
    }


# ============================================================================= the records


def decision_record() -> dict[str, Any]:
    lines = list(OPERATOR_DECISION_V1_3)
    return {
        "$comment": (
            "Mission 1.84.11. The operator's evidence-boundary decision on source metadata, first "
            "class and independent of any answer. CI gate 77 re-derives every field from the code."
        ),
        "record_version": "source-metadata-evidence-boundary-decision@1.0.0",
        "mission": MISSION,
        **SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION,
        "operator_decision": lines,
        "operator_decision_sha256": _sha("\n".join(lines).encode("utf-8")),
        "architecture_decision_record": ADR,
        "implemented_by": {
            "gate": SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
            "support_universe": SUPPORT_UNIVERSE_VERSION_V2,
            "source_metadata": SOURCE_METADATA_CONTEXT_VERSION,
        },
    }


def matrix_counts() -> dict[str, int]:
    """How many literal cases each matrix class holds, read from the frozen test file's syntax."""
    tree = ast.parse((ROOT / TEST_FILE).read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name not in MATRIX_CLASSES:
            continue
        total = 0
        for statement in node.body:
            if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Tuple):
                total += len(statement.value.elts)
        counts[node.name] = total
    return counts


def build_record() -> dict[str, Any]:
    """The freeze record, derived from the live code. `--check` requires the committed one to equal it."""
    gate_v1_2 = _module("semantic_gate_v1_2_for_v1_3_freeze", GATE_V1_2)
    return {
        "$comment": (
            "Mission 1.84.11. The semantic output gate v1.3.0, derived from the live code and frozen "
            "before the V3 diagnostic replay. CI gate 77 re-derives every field."
        ),
        "record_version": "second-opportunity-output-gate-freeze@1.0.0",
        "mission": MISSION,
        "GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
        "PREDECESSOR_GATE_VERSIONS": [
            SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
            SECOND_OPPORTUNITY_GATE_VERSION_V1_2,
        ],
        "PREDECESSOR_GATES_MUTATED": False,
        "V1_2_FREEZE": {
            "implementation_sha256": gate_v1_2.FROZEN_IMPLEMENTATION_SHA256,
            "test_sha256": gate_v1_2.FROZEN_TEST_SHA256,
            "still_validates": True,
        },
        "COMPONENT_VERSIONS": dict(COMPONENT_VERSIONS_V1_3),
        "OPERATOR_DECISION": list(OPERATOR_DECISION_V1_3),
        "INFLECTION_NORMALIZATION_ASYMMETRY": asymmetry_of_v1_2(),
        "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        "OUTPUT_SCHEMA_SHA256": gate_v1_2.schema_sha256(),
        "OUTPUT_SCHEMA_CHANGED": False,
        "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
        "PROMPT_SHA256": PROMPT_SHA256,
        "PROMPT_CHANGED": False,
        "TED_REPRESENTATION_SHA256": REPRESENTATION_SHA256,
        "TED_REPRESENTATION_CHANGED": False,
        "HISTORICAL_MODULES": {p: file_sha(p) for p in gate_v1_2.HISTORICAL_SHA256},
        "FROZEN_V1_2_MODULES": {p: file_sha(p) for p in gate_v1_2.IMPLEMENTATION_FILES},
        "IMPLEMENTATION_FILES": {p: file_sha(p) for p in IMPLEMENTATION_FILES},
        "IMPLEMENTATION_SHA256": implementation_sha256(),
        "FROZEN_TEST_FILE": {TEST_FILE: file_sha(TEST_FILE)},
        "INFLECTION_POLICY": {
            "version": LEXICAL_INFLECTION_POLICY_VERSION,
            "rules": [list(rule) for rule in INFLECTION_RULES],
            "not_covered": [list(item) for item in INFLECTION_NOT_COVERED],
            "justified_by": justified_by(),
            "must_fold": [[a, b, normalize_token(a) == normalize_token(b)] for a, b in MUST_FOLD],
            "must_not_collapse": [
                [a, b, normalize_token(a) != normalize_token(b)] for a, b in MUST_NOT_COLLAPSE
            ],
            "nlp_dependency": False,
            "general_stemmer": False,
        },
        "NORMALIZATION_INVARIANT": {
            "ANSWER_MARKER_NORMALIZATION_POLICY": ANSWER_MARKER_NORMALIZATION_POLICY,
            "SUPPORT_TOKEN_NORMALIZATION_POLICY": SUPPORT_TOKEN_NORMALIZATION_POLICY,
            "equal": ANSWER_MARKER_NORMALIZATION_POLICY == SUPPORT_TOKEN_NORMALIZATION_POLICY,
            "one_function": ANSWER_MARKER_NORMALIZER is SUPPORT_TOKEN_NORMALIZER is normalize_token,
            "canonical_function": "sros_opportunity.lexical_inflection.normalize_token",
            "second_normalizers": one_canonical_function(),
        },
        "SYMMETRY_MATRIX": symmetry_matrix(),
        "SUPPORT_ORIGINS": [o.value for o in SupportOrigin],
        "SOURCE_METADATA_LABEL_KINDS": [k.value for k in SourceMetadataLabelKind],
        "SOURCE_METADATA_POLICY": {
            "channel": "explicit SourceMetadataContext, built from registry entries, no default",
            "licenses": "THE_LABEL_S_OWN_WHOLE_OCCURRENCE_AS_A_NAME",
            "never_licenses": ["its words", "its numbers", "any forbidden concept"],
            "undeclared_source": "REFUSED_BY_NAME",
            "label_equal_to_a_gated_term": "NEVER_MASKS",
            "structural_facts_fields": [f.name for f in dataclasses.fields(PacketStructuralFacts)],
        },
        "LEXICAL_MATCH_IS_FACTUAL_SUPPORT": LEXICAL_MATCH_IS_FACTUAL_SUPPORT,
        "DISJUNCTION_POLICY": {
            "version": DISJUNCTION_POLICY_VERSION,
            "code": DISJUNCTIVE_OBSERVED_STATEMENT,
            "scope": "statement_classifications items classified OBSERVED_OR_EVIDENCE_SUPPORTED",
            "rule": (
                "an or / either joining alternatives outside a denial fails closed; alternatives "
                "denied or questioned together are not observed"
            ),
            "evaluates_disjunctions": False,
        },
        "SOURCE_METADATA_DECISION_SHA256": text_sha(DECISION),
        "FIELD_POLICY_IS_V1_2_0S": True,
        "FORBIDDEN_CONCEPTS_ARE_V1_2_0S": True,
        "FORBIDDEN_CONCEPTS_REMOVED": 0,
        "MATRICES": matrix_counts(),
        "GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY": True,
        "V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE": False,
        "V3_TEXT_USED_AS_TEST_CASE": False,
        "WHITELIST_ENTRIES": 0,
        "SPECIAL_CASES": 0,
        "accounting": {key: 0 for key in ZERO_ACCOUNTING},
    }


# ============================================================================= the checks


def _shingles(text: str, width: int = 6) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i : i + width]) for i in range(len(words) - width + 1)}


def _answer_shingles() -> set[str]:
    found: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str):
            found.update(_shingles(value))
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(json.loads(RESPONSE_V3.read_text(encoding="utf-8"))["parsed_output"])
    return found


def historical_overlap() -> set[str]:
    """Six-word runs of the historical answer in the frozen gate, or in its tests beyond the brief's."""
    brief: set[str] = set().union(*(_shingles(case) for case in BRIEF_CASES))
    implementation: set[str] = set().union(
        *(_shingles((ROOT / p).read_text(encoding="utf-8")) for p in IMPLEMENTATION_FILES)
    )
    tests = _shingles((ROOT / TEST_FILE).read_text(encoding="utf-8")) - brief
    return _answer_shingles() & (implementation | tests)


def validate_decision() -> dict[str, Any]:
    if not DECISION.exists():
        raise ValidationError(f"{DECISION.name} does not exist")
    record: dict[str, Any] = json.loads(DECISION.read_text(encoding="utf-8"))
    for key, value in REQUIRED_BOUNDARY.items():
        if SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION.get(key) != value:
            raise ValidationError(f"the evidence-boundary decision has {key} moved in the code")
    expected = decision_record()
    for key, value in expected.items():
        if key == "$comment":
            continue
        if record.get(key) != value:
            raise ValidationError(
                f"decision {key} is {record.get(key)!r}; the live code derives {value!r}"
            )
    stray = sorted(set(record) - set(expected))
    if stray:
        raise ValidationError(f"the decision carries fields the code does not derive: {stray}")
    if not (ROOT / ADR).exists():
        raise ValidationError(f"{ADR} does not exist")
    return record


def validate() -> dict[str, Any]:
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist")
    record: dict[str, Any] = json.loads(RECORD.read_text(encoding="utf-8"))

    # -- pinned here, not read from the record -----------------------------------------------
    if implementation_sha256() != FROZEN_IMPLEMENTATION_SHA256:
        raise ValidationError(
            "the v1.3.0 implementation is not the one frozen before the V3 diagnostic replay; a "
            "changed gate is a new gate version and needs a new freeze"
        )
    if file_sha(TEST_FILE) != FROZEN_TEST_SHA256:
        raise ValidationError("the frozen test file changed after the freeze")
    gate_v1_2 = _module("semantic_gate_v1_2_for_v1_3_check", GATE_V1_2)
    try:
        gate_v1_2.validate()
    except gate_v1_2.ValidationError as error:
        raise ValidationError(f"gate v1.2.0 is no longer its own freeze: {error}") from error
    if gate_v1_2.schema_sha256() != OUTPUT_SCHEMA_SHA256:
        raise ValidationError("the v1.1.0 output schema moved")

    # -- what the brief requires, against the live code --------------------------------------
    if tuple(OPERATOR_DECISION_V1_3) != REQUIRED_DECISION:
        raise ValidationError("the operator's decision is not carried as it was given")
    if tuple(o.value for o in SupportOrigin) != REQUIRED_ORIGINS:
        raise ValidationError("the support origins are not the four the brief names")
    if asymmetry_of_v1_2() != "ESTABLISHED":
        raise ValidationError("v1.2.0's asymmetry no longer reproduces: v1.2.0 moved")
    if ANSWER_MARKER_NORMALIZATION_POLICY != SUPPORT_TOKEN_NORMALIZATION_POLICY or not (
        ANSWER_MARKER_NORMALIZER is SUPPORT_TOKEN_NORMALIZER is normalize_token
    ):
        raise ValidationError("the answer and the support are not read by one function (§7)")
    second = one_canonical_function()
    if second:
        raise ValidationError(f"a second normalizer exists: {second[:3]}")
    matrix = symmetry_matrix()
    for key in ("asymmetries", "unlicensed_absences_missed", "metadata_leaks"):
        if matrix[key]:
            raise ValidationError(
                f"the symmetry matrix finds {matrix[key]} {key}: one side folds what the other "
                "does not, or a source's name licenses a word"
            )
    for a, b in MUST_FOLD:
        if normalize_token(a) != normalize_token(b):
            raise ValidationError(f"{a!r} and {b!r} are not one form")
    for a, b in MUST_NOT_COLLAPSE:
        if normalize_token(a) == normalize_token(b):
            raise ValidationError(f"{a!r} and {b!r} collapsed: that is stemming, not inflection")
    if justified_by()["OTHER_ES_PLURALS_NEEDED"]:
        raise ValidationError("a gated term needs an -es rule the policy does not cover")
    if LEXICAL_MATCH_IS_FACTUAL_SUPPORT is not False:
        raise ValidationError("a lexical match is being treated as factual support (§13)")
    from sros_opportunity import second_opportunity_gate_v1_3 as v1_3

    if v1_3.SECOND_OPPORTUNITY_FIELD_POLICY is not SECOND_OPPORTUNITY_FIELD_POLICY:
        raise ValidationError("the field policy is not v1.2.0's")
    if v1_3.FORBIDDEN_CONCEPTS_V1_2 is not FORBIDDEN_CONCEPTS_V1_2:
        raise ValidationError("the forbidden concepts are not v1.2.0's")
    validate_decision()
    counts = matrix_counts()
    for name, minimum in MATRIX_CLASSES.items():
        if counts.get(name, 0) < minimum:
            raise ValidationError(f"{name} holds {counts.get(name, 0)} cases; it needs {minimum}")
    overlap = historical_overlap()
    if overlap:
        raise ValidationError(
            f"a run of the historical answer is in the frozen gate or tests: {sorted(overlap)[:3]}"
        )

    # -- the record is exactly what the code derives -------------------------------------------
    expected = build_record()
    for key, value in expected.items():
        if key == "$comment":
            continue
        if record.get(key) != value:
            raise ValidationError(f"{key} is {record.get(key)!r}; the live code derives {value!r}")
    stray = sorted(set(record) - set(expected))
    if stray:
        raise ValidationError(f"the record carries fields the code does not derive: {stray}")
    return record


# ============================================================================= rendering


def _row(*cells: object) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def render(record: dict[str, Any]) -> str:
    policy = record["INFLECTION_POLICY"]
    invariant = record["NORMALIZATION_INVARIANT"]
    lines = [
        "<!-- Generated by infrastructure/scripts/render_second_opportunity_semantic_gate_v1_3.py."
        " Do not edit by hand. -->",
        "",
        "# Second-Opportunity output gate v1.3.0: frozen before the V3 diagnostic replay",
        "",
        f"Mission {record['mission'].removeprefix('mission-')}. Gate `{record['GATE_VERSION']}`, "
        "successor of "
        + ", ".join(f"`{v}`" for v in record["PREDECESSOR_GATE_VERSIONS"])
        + ", neither of which is mutated.",
        "",
        "## The operator's decision",
        "",
        *(f"- `{item}`" for item in record["OPERATOR_DECISION"]),
        "",
        f"INFLECTION_NORMALIZATION_ASYMMETRY (gate v1.2.0) = "
        f"`{record['INFLECTION_NORMALIZATION_ASYMMETRY']}`.",
        "",
        "## What is unchanged",
        "",
        f"- output schema `{record['OUTPUT_SCHEMA_VERSION']}` `{record['OUTPUT_SCHEMA_SHA256']}`",
        f"- prompt `{record['PROMPT_VERSION']}` `{record['PROMPT_SHA256']}`",
        f"- TED representation `{record['TED_REPRESENTATION_SHA256']}`",
        f"- gate v1.2.0, still its own freeze: implementation "
        f"`{record['V1_2_FREEZE']['implementation_sha256']}`, tests "
        f"`{record['V1_2_FREEZE']['test_sha256']}`",
        "- the modules v1.0.0 and v1.1.0 run on, byte-identical to bb0f50a:",
        *(f"  - `{p}` `{d}`" for p, d in record["HISTORICAL_MODULES"].items()),
        "",
        "## Components",
        "",
        _row("component", "version"),
        _row("---", "---"),
        *(_row(k, f"`{v}`") for k, v in record["COMPONENT_VERSIONS"].items()),
        "",
        f"Implementation digest `{record['IMPLEMENTATION_SHA256']}`.",
        "",
        "## One inflection policy, both sides",
        "",
        _row("rule", "matches", "produces", "example"),
        _row("---", "---", "---", "---"),
        *(_row(*rule) for rule in policy["rules"]),
        "",
        "Not covered:",
        "",
        *(f"- {name}: {why}" for name, why in policy["not_covered"]),
        "",
        "Justified by the gated vocabulary: `-ies` for "
        + ", ".join(f"`{t}`" for t in policy["justified_by"]["REGULAR_IES_PLURAL"])
        + "; `-sses` for "
        + ", ".join(f"`{t}`" for t in policy["justified_by"]["REGULAR_SSES_PLURAL"])
        + ". Other `-es` plurals needed: "
        + str(len(policy["justified_by"]["OTHER_ES_PLURALS_NEEDED"]))
        + ".",
        "",
        f"ANSWER_MARKER_NORMALIZATION_POLICY = `{invariant['ANSWER_MARKER_NORMALIZATION_POLICY']}`; "
        f"SUPPORT_TOKEN_NORMALIZATION_POLICY = `{invariant['SUPPORT_TOKEN_NORMALIZATION_POLICY']}`; "
        f"one function `{invariant['canonical_function']}`: "
        f"{str(invariant['one_function']).lower()}.",
        "",
        _row("symmetry matrix", "count"),
        _row("---", "---"),
        *(_row(k, v) for k, v in record["SYMMETRY_MATRIX"].items()),
        "",
        "## Support origins",
        "",
        *(f"- `{o}`" for o in record["SUPPORT_ORIGINS"]),
        "",
        f"A source metadata label licenses "
        f"`{record['SOURCE_METADATA_POLICY']['licenses']}`, and never "
        + ", ".join(record["SOURCE_METADATA_POLICY"]["never_licenses"])
        + ". An undeclared source is "
        f"`{record['SOURCE_METADATA_POLICY']['undeclared_source']}`. "
        f"LEXICAL_MATCH_IS_FACTUAL_SUPPORT = {str(record['LEXICAL_MATCH_IS_FACTUAL_SUPPORT']).lower()}.",
        "",
        f"Decision record `{record['SOURCE_METADATA_DECISION_SHA256']}`.",
        "",
        "## Disjunction",
        "",
        f"`{record['DISJUNCTION_POLICY']['code']}` ({record['DISJUNCTION_POLICY']['version']}), for "
        f"{record['DISJUNCTION_POLICY']['scope']}: {record['DISJUNCTION_POLICY']['rule']}.",
        "",
        "## Frozen matrices",
        "",
        _row("test class", "literal cases"),
        _row("---", "---"),
        *(_row(k, v) for k, v in record["MATRICES"].items()),
        "",
        "## The order",
        "",
        "- GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY = "
        f"{str(record['GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY']).lower()}",
        "- V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE = "
        f"{str(record['V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE']).lower()}",
        f"- V3_TEXT_USED_AS_TEST_CASE = {str(record['V3_TEXT_USED_AS_TEST_CASE']).lower()}",
        f"- WHITELIST_ENTRIES = {record['WHITELIST_ENTRIES']}",
        f"- SPECIAL_CASES = {record['SPECIAL_CASES']}",
        "",
        "Model calls, provider requests, Messages API requests, TED bytes and canonical mutations: "
        + ", ".join(str(v) for v in record["accounting"].values())
        + ".",
        "",
    ]
    return "\n".join(lines)


def render_decision(record: dict[str, Any]) -> str:
    lines = [
        "<!-- Generated by infrastructure/scripts/render_second_opportunity_semantic_gate_v1_3.py."
        " Do not edit by hand. -->",
        "",
        "# Source metadata is provenance, not factual support",
        "",
        f"Mission {record['mission'].removeprefix('mission-')}. Decision "
        f"`{record['decision_id']}`, recorded in `{record['architecture_decision_record']}`.",
        "",
        "```",
        "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = "
        f"{str(record['SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT']).lower()}",
        "SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = "
        f"{str(record['SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS']).lower()}",
        f"decision owner = {record['decision_owner']}",
        f"decision type = {record['decision_type']}",
        f"mathematically derived = {str(record['mathematically_derived']).lower()}",
        "```",
        "",
        f"Reason: {record['reason']}.",
        "",
        "Source metadata is: " + ", ".join(record["metadata_is"]) + ".",
        "",
        "It may support:",
        "",
        *(f"- {item}" for item in record["metadata_may_support"]),
        "",
        "It may not support:",
        "",
        *(f"- {item}" for item in record["metadata_may_not_support"]),
        "",
        "Moved into packet structural facts: "
        f"{str(record['moved_into_packet_structural_facts']).lower()}. Independent of any "
        f"answer: {str(record['independent_of_any_answer']).lower()}.",
        "",
        "The operator's decision, verbatim (`" + record["operator_decision_sha256"] + "`):",
        "",
        *(f"- `{line}`" for line in record["operator_decision"]),
        "",
        "Implemented by " + ", ".join(f"`{v}`" for v in record["implemented_by"].values()) + ".",
        "",
    ]
    return "\n".join(lines)


def _write_json(path: pathlib.Path, data: dict[str, Any]) -> None:
    path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        _write_json(DECISION, decision_record())
        _write_json(RECORD, build_record())
    try:
        record = validate()
        decision = validate_decision()
    except ValidationError as error:
        print(f"FAIL: {error}")
        return 1
    pages = ((RECORD_MD, render(record)), (DECISION_MD, render_decision(decision)))
    for path, text in pages:
        if args.write:
            path.write_bytes(text.encode("utf-8"))
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            print(f"FAIL: {path.name} is stale; run with --write")
            return 1
    print(f"ok: {RECORD.name} is the frozen gate v1.3.0 the live code derives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
