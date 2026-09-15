"""Mission 1.84.25, CI gate 102. Why gate v1.4.0 refused V10 at stage 6, re-derived, and nothing changed.

A diagnosis, not a repair. The two stage 6 refusals of the one V10 request are reproduced from the
retained answer by the frozen gate v1.4.0, with the packet rebuilt from Mission 1.84.10's authenticated
snapshot as gate 101 rebuilds it, and each refused word is traced through the gate's own clause reader:
the sentences, the clause boundaries and which pattern made them, the occurrence state and why, and
the lexical support. A synthetic matrix, on the frozen v1.3.0 test fixture and never on the V10 answer,
then runs sentences of the same general shapes through the frozen gate in three fields, and compares
each verdict with the verdict the documented policy gives, where the policy gives one.

Every policy sentence the classification rests on is quoted, and the quote must still be found in the
file it is quoted from. The frozen gate, the clause reader it inherits from v1.2.0 and the fixture are
pinned, so a gate changed after this diagnosis no longer reproduces it. V10 itself is held to gate 101:
its record, its approval and its response unchanged, its approval consumed, and its runner still
refusing a second request before any transport.

Nothing here calls a model, builds a transport or writes outside this record and its page.

    uv run python infrastructure/scripts/render_second_opportunity_stage6_diagnostic_v10.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from collections.abc import Sequence
from typing import Any, NamedTuple

from sros_opportunity import assertion_audit_v1_3 as audit
from sros_opportunity import assertion_context as context
from sros_opportunity.guards import _sentences
from sros_opportunity.lexical_inflection import inflection_spans
from sros_opportunity.second_opportunity_gate_v1_2 import (
    SECOND_OPPORTUNITY_FIELD_POLICY,
    build_trusted_context,
)
from sros_opportunity.second_opportunity_gate_v1_4 import evaluate_second_opportunity_output_v1_4
from sros_opportunity.second_opportunity_prompt_v1_5 import SECOND_OPPORTUNITY_SYSTEM_V1_5
from sros_opportunity.second_opportunity_prompt_v1_6 import SECOND_OPPORTUNITY_SYSTEM_V1_6
from sros_opportunity.support_origin import build_typed_support_universe

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
PACKAGE = ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"
TESTS = ROOT / "packages" / "opportunity-engine" / "python" / "tests"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-stage6-diagnostic-v10.json"
RECORD_MD = DATA / "second-opportunity-stage6-diagnostic-v10.md"
RESPONSE_V9 = DATA / "second-opportunity-synthesis-response-v9.json"
FIXTURE = TESTS / "test_semantic_gate_v1_3.py"

MISSION = "mission-1.84.25"
START_COMMIT = "91cbb19f12eb408a14f4fbe97e7d7add9999975f"
BRANCH = "sprint-1/mission-1.84.25"
PRIMARY_OUTCOME = "STAGE_6_ROOT_CAUSE_ESTABLISHED_OPERATOR_DECISION_REQUIRED"

#: The mission's hard invariants, as the operator set them. Nothing below may contradict one.
INVARIANTS: dict[str, object] = {
    "PROVIDER_CALLS": 0,
    "MODEL_INFERENCES": 0,
    "RETRIES": 0,
    "PERSISTENCE": 0,
    "NEW_EXECUTION_PACKET": "NO",
    "V11_CREATION": "NO",
    "OPPORTUNITY_2_CREATION": "NO",
    "HISTORICAL_VERDICTS_MUTABLE": "NO",
    "V10_REEXECUTION": "FORBIDDEN",
    "V10_OUTPUT_REWRITE_OR_REPAIR": "FORBIDDEN",
}
UNCHANGED: dict[str, bool] = {
    "SEMANTIC_GATE_MODIFIED": False,
    "CLAUSE_READER_MODIFIED": False,
    "OUTPUT_SCHEMA_MODIFIED": False,
    "PROMPT_MODIFIED": False,
    "PROVIDER_PROJECTION_MODIFIED": False,
    "EXECUTION_ARCHITECTURE_MODIFIED": False,
    "REPAIR_IMPLEMENTED": False,
}

#: Gate v1.4.0's implementation digest (CI gate 87) and v1.2.0's (CI gate 75), which carries the
#: clause reader v1.4.0 inherits; the reader's own file; and the frozen v1.3.0 test file (CI gate 77)
#: whose synthetic packet the matrix is run on.
GATE_V1_4_SHA256 = "eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb"
GATE_V1_2_SHA256 = "47bbcb459b0b69153d23c7dcc7f273e0e47d0b84a72522d25f773cd462db82b0"
CLAUSE_READER_FILE = "packages/opportunity-engine/python/sros_opportunity/assertion_context.py"
CLAUSE_READER_SHA256 = "3afcffc210393400241b7ed5b818d4caab615e882c30cf6c7b2495eee2c3081b"
FIXTURE_SHA256 = "6d7ad83150323293c78a998f9a880e6abd27e229a576b7b6f4d8fd6b940b80c3"

FIELDS_UNDER_TEST: tuple[tuple[str, bool], ...] = (
    ("observed_need", False),
    ("critical_uncertainties", True),
    ("commercial_claims_not_supported", True),
)


class ValidationError(RuntimeError):
    """The diagnosis no longer re-derives, or something it holds constant moved."""


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: pathlib.Path) -> str:
    return _sha_bytes(path.read_bytes())


def _module(name: str, path: pathlib.Path) -> Any:
    if not path.exists():
        raise ValidationError(f"{path.name} is missing")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load(path: pathlib.Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


#: Gate 101 holds V10 and rebuilds its inputs; gates 75 and 87 own the frozen digests.
G101 = _module(
    "gate_101_for_gate_102", SCRIPTS / "render_second_opportunity_execution_record_v10.py"
)
G75 = _module("gate_75_for_gate_102", SCRIPTS / "render_second_opportunity_semantic_gate_v1_2.py")
G87 = _module("gate_87_for_gate_102", SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py")


# --------------------------------------------------------------------------- the policy, quoted

#: Every sentence the classification rests on, where it is written. A quote that is no longer in its
#: file is refused: the classification would rest on a sentence the repository does not say.
POLICY_QUOTES: dict[str, tuple[str, str]] = {
    "ASSERTION_NOT_TOKEN_PRESENCE": (
        "docs/reports/mission-1.84.10-report.md",
        "A concept is refused when it is ASSERTED. It is not refused when it is denied in its own "
        "clause, requested as evidence that would be required, framed as an uncertainty, listed as "
        "not supported, or classified by the answer itself as unknown.",
    ),
    "ONE_DENIAL_COVERS_A_LIST": (
        CLAUSE_READER_FILE,
        "a plain comma inside a list does not break one, so *does not establish need, gap or "
        "willingness to pay* stays one denial.",
    ),
    "A_COORDINATED_CLAUSE_HAS_ITS_OWN_SUBJECT": (
        CLAUSE_READER_FILE,
        "Clauses break at a semicolon, a dash, a contrastive conjunction, a non-restrictive relative "
        "clause and a coordinated clause with its own subject;",
    ),
    "A_CONTRAST_REASSERTS": (
        CLAUSE_READER_FILE,
        "A denial followed by a contrastive continuation that predicates something of the same "
        "subject re-asserts it",
    ),
    "THE_SPLIT_IS_KNOWN_AND_CORRECTED_ELSEWHERE": (
        "packages/opportunity-engine/python/sros_opportunity/assertion_audit_v1_3.py",
        "v1.2.0's clause splitter also breaks at a comma-less `or` followed by a subject and a verb "
        "(`no X or Y were ...`); that is still one clause here, read under its denial.",
    ),
    "A_MARKER_IS_CHECKED_WHERE_ASSERTED": (
        "packages/opportunity-engine/python/sros_opportunity/assertion_audit_v1_3.py",
        "if universe.content_carries(marker) or not is_asserted(text, marker):",
    ),
    "AN_ASSERTING_FIELD_MAY_DENY": (
        "packages/opportunity-engine/python/sros_opportunity/second_opportunity_gate_v1_2.py",
        "asserted reasoning, which may deny",
    ),
    "A_DENIED_GATED_WORD_PASSES_IN_AN_ASSERTING_FIELD": (
        "packages/opportunity-engine/python/tests/test_semantic_gate_v1_2.py",
        'text = f"The packet does not establish {phrase}."',
    ),
    "A_DENIAL_IS_NOT_AN_ASSERTION": (
        "docs/CLAUDE.md",
        "A forbidden term under a DENIAL is not an assertion.",
    ),
    "ONLY_THE_SUBJECT_OF_A_TRAILING_DENIAL_IS_CLEARED": (
        "packages/opportunity-engine/python/sros_opportunity/guards.py",
        "Only `<term> (is|are|was|were|has|have|had) (not|never|no)` clears, and an intervening "
        "comma or contrastive word cancels it.",
    ),
    "HYPHENS_SPLIT_TOKENS": (
        "packages/opportunity-engine/python/sros_opportunity/guards.py",
        "Hyphens and slashes split;",
    ),
    "NO_SINGLE_WORD_OF_MARKET_ACTIVITY_IS_LICENSED": (
        "docs/reports/mission-1.84.10-report.md",
        "No paraphrase and no single word is licensed: *the market wants a scheduling platform* and "
        "*this market is growing* still fail on `market`.",
    ),
    "PROSE_FIELDS_ARE_CHECKED_MARKER_BY_MARKER": (
        "docs/reports/mission-1.84.11-report.md",
        "**Prose fields are not refused by this rule.** They are still checked marker by marker.",
    ),
    "THE_ACCEPTED_LIMITATION_IS_UNDER_REFUSAL": (
        "docs/data/second-opportunity-synthesis-execution-approval-v10.json",
        "system and is not a complete natural-language proof system.",
    ),
}

#: What prompt v1.6.0 told the model, read from the system region it sent. The last line is what
#: v1.6.0 added to v1.5.0, and v1.5.0 must not carry it.
PROMPT_V1_6_LINES: tuple[str, ...] = (
    "candidate_intervention_class names the class and only the class, and NAME_THE_CLASS_ONLY does "
    "not mean free vocabulary",
    "name a more neutral class grounded in what they do supply",
    "General knowledge of the world is not support",
    "whether a market exists",
    "every substantive concept that describes the domain comes from",
    "Name the class in terms the supplied statements and the packet's structural facts already use",
)
ADDED_IN_V1_6 = PROMPT_V1_6_LINES[-1]


#: Earlier wording that explains the `software` refusal as a field-level rule. The documented rule is
#: clause-level assertion, so each is corrected here and left, byte for byte, where it was written: the
#: V10 record is pinned by gate 101, and a report and a changelog row are history.
EARLIER_WORDING: dict[str, tuple[str, str]] = {
    "V10_RECORD_SEMANTIC_NOTE": (
        "docs/data/second-opportunity-synthesis-execution-record-v10.json",
        "Gate v1.4.0 refuses a substantive word in a supported-assertion field when no supplied "
        "statement carries it, and it did so here wherever the word stood",
    ),
    "MISSION_1_84_24_REPORT": (
        "docs/reports/mission-1.84.24-report.md",
        "the word stands in an asserted field, and no supplied statement carries it.",
    ),
    "CLAUDE_MD_1_159": (
        "docs/CLAUDE.md",
        "A WORD IN A DENIAL IS STILL A WORD IN AN ASSERTED FIELD.",
    ),
}
CORRECTION = (
    "Gate v1.4.0 refuses an unsupplied gated word in a supported-assertion field only where the word "
    "is ASSERTED, clause by clause. In observed_need the word was asserted because the clause reader "
    "cut the last item of a list off from the leading `whether` that questions it; a word the answer "
    "frames as an uncertainty in one clause is not refused, in that field or any other."
)


def _quoted(quotes: dict[str, tuple[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for key, (path, quote) in quotes.items():
        source = ROOT / path
        if not source.exists():
            raise ValidationError(f"{key}: {path} is missing")
        if _flat(quote) not in _flat(source.read_text(encoding="utf-8")):
            raise ValidationError(f"{key}: the quoted sentence is no longer in {path}")
        out[key] = {"source": path, "quote": quote}
    return out


def check_quotes() -> dict[str, dict[str, str]]:
    return _quoted(POLICY_QUOTES)


def earlier_wording() -> dict[str, object]:
    return {
        "quotes": _quoted(EARLIER_WORDING),
        "correction": CORRECTION,
        "EDITED_WHERE_WRITTEN": False,
    }


def prompt_lines() -> dict[str, object]:
    v16, v15 = _flat(SECOND_OPPORTUNITY_SYSTEM_V1_6), _flat(SECOND_OPPORTUNITY_SYSTEM_V1_5)
    found = {line: _flat(line) in v16 for line in PROMPT_V1_6_LINES}
    missing = [line for line, present in found.items() if not present]
    if missing:
        raise ValidationError(f"prompt v1.6.0 no longer states {missing[0]!r}")
    if _flat(ADDED_IN_V1_6) in v15:
        raise ValidationError("prompt v1.5.0 carries a line v1.6.0 was supposed to add")
    return {
        "PROMPT_V1_6_STATES": list(PROMPT_V1_6_LINES),
        "STRUCTURAL_CHANNEL_SENTENCE_IN_V1_5": False,
        "STRUCTURAL_CHANNEL_SENTENCE_IN_V1_6": True,
        "DIMENSION_NAME_WHOLE_PHRASE_BOUNDARY_STATED": _flat("market activity") in v16.lower(),
    }


# --------------------------------------------------------------------------- frozen things


def frozen() -> dict[str, object]:
    found = {
        "SEMANTIC_GATE_V1_4_SHA256": G87.implementation_sha256(),
        "SEMANTIC_GATE_V1_2_SHA256": G75.implementation_sha256(),
        "CLAUSE_READER_SHA256": _sha_file(ROOT / CLAUSE_READER_FILE),
        "SYNTHETIC_FIXTURE_SHA256": _sha_file(FIXTURE),
    }
    expected = {
        "SEMANTIC_GATE_V1_4_SHA256": GATE_V1_4_SHA256,
        "SEMANTIC_GATE_V1_2_SHA256": GATE_V1_2_SHA256,
        "CLAUSE_READER_SHA256": CLAUSE_READER_SHA256,
        "SYNTHETIC_FIXTURE_SHA256": FIXTURE_SHA256,
    }
    for key, value in expected.items():
        if found[key] != value:
            raise ValidationError(f"{key} is {found[key]}, not the frozen {value}")
    if CLAUSE_READER_FILE not in G75.IMPLEMENTATION_FILES:
        raise ValidationError("the clause reader is no longer inside gate v1.2.0's frozen digest")
    return {
        **found,
        "V10_RESPONSE_FILE_SHA256": _sha_file(G101.RESPONSE),
        "V10_RECORD_FILE_SHA256": _sha_file(G101.RECORD),
        "V10_APPROVAL_FILE_SHA256": _sha_file(G101.APPROVAL),
    }


# --------------------------------------------------------------------------- V10, reproduced


def _inputs() -> dict[str, Any]:
    packet, statements, evidence_to_claim = G101.snapshot_packet()
    metadata = G101.runner().source_metadata_for(list(packet.source_ids))
    trusted = build_trusted_context(packet)
    universe = build_typed_support_universe(packet, statements, trusted, metadata)
    return {
        "packet": packet,
        "statements": statements,
        "evidence_to_claim": evidence_to_claim,
        "metadata": metadata,
        "trusted": trusted,
        "universe": universe,
    }


def _disposition(field: str) -> tuple[str, str]:
    for fc in SECOND_OPPORTUNITY_FIELD_POLICY:
        if fc.field_name == field:
            return fc.disposition.value, fc.shape.value
    raise ValidationError(f"{field} has no field context")


def _clause_trace(sentence: str) -> dict[str, object]:
    lowered = context._norm(sentence)
    return {
        "sentence": sentence,
        "boundaries": [
            {"pattern": m.lastgroup, "matched": m.group(), "at": m.start()}
            for m in context._CLAUSE_BOUNDARY.finditer(lowered)
        ],
        "clauses": [{"boundary": c.boundary, "text": c.text} for c in context._clauses(sentence)],
    }


def _occurrences(text: str, phrase: str) -> list[dict[str, str]]:
    return [
        {"clause": o.clause, "state": o.state.value, "why": o.why}
        for o in audit.classify(text, phrase)
    ]


def trace(field: str, word: str, text: str, inputs: dict[str, Any]) -> dict[str, object]:
    universe = inputs["universe"]
    disposition, shape = _disposition(field)
    supported = frozenset(inputs["packet"].counting_dimensions)
    masked = context._mask_dimension_terms(text, supported)
    return {
        "field": field,
        "word": word,
        "disposition": disposition,
        "shape": shape,
        "text": text,
        "sentences": [_clause_trace(s) for s in _sentences(text) if word in context._norm(s)],
        "occurrences": _occurrences(text, word),
        "content_carries_word": bool(universe.content_carries(word)),
        "metadata_labels_carrying_word": list(universe.metadata_labels_carrying(word)),
        "word_survives_the_supported_dimension_mask": bool(
            inflection_spans(context._norm(masked), word)
        ),
    }


def reproduce(inputs: dict[str, Any]) -> dict[str, object]:
    response = _load(G101.RESPONSE)
    if _sha_file(G101.RESPONSE) != G101.RESPONSE_FILE_SHA256:
        raise ValidationError("V10's retained response changed after gate 101 pinned it")
    parsed = response["parsed_output"]
    decision = evaluate_second_opportunity_output_v1_4(
        parsed,
        inputs["packet"],
        inputs["statements"],
        inputs["evidence_to_claim"],
        trusted_context=inputs["trusted"],
        source_metadata=inputs["metadata"],
    )
    reasons = list(decision.refusal_reasons)
    retained = list(response["validation"]["reasons"])
    if reasons != retained:
        raise ValidationError("the frozen gate no longer returns the reasons V10 retained")
    refused = []
    for reason in reasons:
        match = re.match(r"^([a-z_]+) audited UNSUPPORTED: '([^']+)' appears in no source", reason)
        if match is None:
            raise ValidationError(f"a V10 refusal is not a lexical support refusal: {reason}")
        refused.append((match.group(1), match.group(2)))
    return {
        "persist": bool(decision.persist),
        "reasons": reasons,
        "equals_retained": True,
        "refused": [{"field": f, "word": w} for f, w in refused],
        "traces": [trace(f, w, str(parsed[f]), inputs) for f, w in refused],
    }


def v9_market() -> dict[str, object]:
    response = _load(RESPONSE_V9)
    text = str(response["parsed_output"]["candidate_intervention_class"])
    reasons = [
        r
        for r in response["validation"]["reasons"]
        if r.startswith("candidate_intervention_class audited UNSUPPORTED: 'market'")
    ]
    if len(reasons) != 1:
        raise ValidationError("V9's retained reasons no longer carry its one refusal on 'market'")
    return {
        "prompt": "1.5.0",
        "text": text,
        "reason": reasons[0],
        "occurrences": _occurrences(text, "market"),
    }


def request_forms() -> dict[str, object]:
    out: dict[str, object] = {}
    for label, path in (("V9", RESPONSE_V9), ("V10", G101.RESPONSE)):
        rows = G101.request_shape_verdicts(_load(path)["parsed_output"])
        out[label] = {
            "items": len(rows),
            "request_shaped": sum(bool(r["request_shaped"]) for r in rows),
        }
    return out


# --------------------------------------------------------------------------- the synthetic matrix


class Case(NamedTuple):
    case_id: str
    group: str
    sentence: str
    phrase: str
    intended: str  # REFUSE | PASS | UNDETERMINED, for a SUPPORTED_ASSERTION field
    basis: str


GROUPS: dict[str, str] = {
    "ASSERTED_CONTROL": "the gated word is asserted; the policy refuses it",
    "SCOPED_CONTROL": "the gated word is denied or questioned in its own clause; the policy passes it",
    "LIST_UNDER_ONE_SCOPE": (
        "the gated word is the last item of a list inside a leading `whether` or denial, followed by "
        "a verb; the policy keeps the list under its one scope"
    ),
    "PREMODIFIER_OF_A_DENIED_SUBJECT": (
        "the gated word modifies the head noun of a subject its own clause denies; the policy's "
        "principle and its bounded rule give different answers"
    ),
}
BASES: dict[str, tuple[str, ...]] = {
    "ASSERTED_IS_REFUSED": ("ASSERTION_NOT_TOKEN_PRESENCE", "A_MARKER_IS_CHECKED_WHERE_ASSERTED"),
    "A_CONTRAST_REASSERTS": ("A_CONTRAST_REASSERTS",),
    "SCOPED_IN_ITS_OWN_CLAUSE": (
        "ASSERTION_NOT_TOKEN_PRESENCE",
        "A_DENIED_GATED_WORD_PASSES_IN_AN_ASSERTING_FIELD",
        "AN_ASSERTING_FIELD_MAY_DENY",
    ),
    "ONE_SCOPE_COVERS_THE_LIST": (
        "ONE_DENIAL_COVERS_A_LIST",
        "A_COORDINATED_CLAUSE_HAS_ITS_OWN_SUBJECT",
        "THE_SPLIT_IS_KNOWN_AND_CORRECTED_ELSEWHERE",
        "ASSERTION_NOT_TOKEN_PRESENCE",
    ),
    "PRINCIPLE_AND_BOUNDED_RULE_DIFFER": (
        "ASSERTION_NOT_TOKEN_PRESENCE",
        "ONLY_THE_SUBJECT_OF_A_TRAILING_DENIAL_IS_CLEARED",
    ),
}

_A, _S, _L, _M = (
    "ASSERTED_CONTROL",
    "SCOPED_CONTROL",
    "LIST_UNDER_ONE_SCOPE",
    "PREMODIFIER_OF_A_DENIED_SUBJECT",
)
#: Synthetic sentences over a placeholder subject. None is a V10 sentence; the shapes are general.
CASES: tuple[Case, ...] = (
    Case("A1", _A, "Software gap is established.", "software", "REFUSE", "ASSERTED_IS_REFUSED"),
    Case("A2", _A, "The buyers need software.", "software", "REFUSE", "ASSERTED_IS_REFUSED"),
    Case(
        "A3",
        _A,
        "A software gap exists, and it is not established by these statements.",
        "software",
        "REFUSE",
        "ASSERTED_IS_REFUSED",
    ),
    Case(
        "A4",
        _A,
        "Buyers use software; this is not established by these statements.",
        "software",
        "REFUSE",
        "ASSERTED_IS_REFUSED",
    ),
    Case("A5", _A, "A market exists for this.", "market", "REFUSE", "ASSERTED_IS_REFUSED"),
    Case(
        "A6",
        _A,
        "The class is a market-analysis service.",
        "market",
        "REFUSE",
        "ASSERTED_IS_REFUSED",
    ),
    Case(
        "A7", _A, "There is an underserved segment.", "underserved", "REFUSE", "ASSERTED_IS_REFUSED"
    ),
    Case(
        "A8",
        _A,
        "A software gap is not established, but it probably exists.",
        "software",
        "REFUSE",
        "A_CONTRAST_REASSERTS",
    ),
    Case(
        "A9",
        _A,
        "Software is not established, but it probably exists.",
        "software",
        "REFUSE",
        "A_CONTRAST_REASSERTS",
    ),
    Case("S1", _S, "Software is not established.", "software", "PASS", "SCOPED_IN_ITS_OWN_CLAUSE"),
    Case(
        "S2", _S, "No software gap is established.", "software", "PASS", "SCOPED_IN_ITS_OWN_CLAUSE"
    ),
    Case(
        "S3",
        _S,
        "A gap in software is not established.",
        "software",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S4",
        _S,
        "Whether a software gap exists is unknown.",
        "software",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S5",
        _S,
        "Whether this reflects a software gap is not established.",
        "software",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S6",
        _S,
        "Whether software exists is unknown.",
        "software",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S7",
        _S,
        "Whether dissatisfaction exists is unknown.",
        "dissatisfaction",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S8",
        _S,
        "No evidence establishes a need, problem, or software gap.",
        "software",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S9",
        _S,
        "It is not established whether this reflects a need, problem, or software gap.",
        "software",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S10",
        _S,
        "The packet does not establish need, gap or willingness to pay.",
        "willingness to pay",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "S11",
        _S,
        "No statement establishes a market for this.",
        "market",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case("S12", _S, "The market is not established.", "market", "PASS", "SCOPED_IN_ITS_OWN_CLAUSE"),
    Case(
        "S13",
        _S,
        "None of the notices show that a software gap exists.",
        "software",
        "PASS",
        "SCOPED_IN_ITS_OWN_CLAUSE",
    ),
    Case(
        "L1",
        _L,
        "Whether a need or software exists is unknown.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L2",
        _L,
        "Whether a need or dissatisfaction exists is unknown.",
        "dissatisfaction",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L3",
        _L,
        "Whether this reflects a need, problem, or software gap is not established.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L4",
        _L,
        "Whether this reflects a need, problem or software gap is not established.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L5",
        _L,
        "Whether this reflects a need or software gap is not established.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L6",
        _L,
        "Whether this reflects a need, problem, or software gap is unknown.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L7",
        _L,
        "Whether this reflects a need, problem, or dissatisfaction remains to be seen.",
        "dissatisfaction",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L8",
        _L,
        "Whether this reflects a need, problem, or underserved segment is not established.",
        "underserved",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L9",
        _L,
        "None of the notices show that a need, problem, or software gap exists.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L10",
        _L,
        "Whether this reflects a need, problem, or competitor weakness is not established.",
        "competitor",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L11",
        _L,
        "Whether this reflects a need, problem, or software is not established.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L12",
        _L,
        "Whether this reflects a need, problem, or market is not established.",
        "market",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L13",
        _L,
        "Whether this reflects a need, problem, or a gap in software is not established.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "L14",
        _L,
        "Whether this reflects a need, problem, or any underlying software gap is not established.",
        "software",
        "PASS",
        "ONE_SCOPE_COVERS_THE_LIST",
    ),
    Case(
        "M1",
        _M,
        "Software gap is not established.",
        "software",
        "UNDETERMINED",
        "PRINCIPLE_AND_BOUNDED_RULE_DIFFER",
    ),
    Case(
        "M2",
        _M,
        "Market gap is not established.",
        "market",
        "UNDETERMINED",
        "PRINCIPLE_AND_BOUNDED_RULE_DIFFER",
    ),
    Case(
        "M3",
        _M,
        "Underserved segment is not established.",
        "underserved",
        "UNDETERMINED",
        "PRINCIPLE_AND_BOUNDED_RULE_DIFFER",
    ),
)
#: What the matrix must find, so the report cannot drift from it: the cases whose gate verdict in a
#: SUPPORTED_ASSERTION field differs from the verdict the documented policy gives.
EXPECTED_DIVERGENCES: tuple[str, ...] = tuple(f"L{n}" for n in range(1, 11))
#: The smallest general failing pattern, and its control: the same sentence with one list item.
SMALLEST_FAILING = ("L1", "S6")


def _fixture() -> Any:
    return _module("frozen_v1_3_fixture_for_gate_102", FIXTURE)


def run_matrix() -> dict[str, object]:
    t = _fixture()
    base = evaluate_second_opportunity_output_v1_4(
        t.good_output(),
        t.PACKET,
        t.STATEMENTS,
        t.E2C,
        trusted_context=t.TRUSTED,
        source_metadata=t.META,
    )
    if base.refusal_reasons:
        raise ValidationError("the frozen fixture's good answer no longer passes gate v1.4.0")
    content = " ".join(t.STATEMENTS.values()).lower()
    rows: list[dict[str, object]] = []
    for case in CASES:
        if case.group not in GROUPS or case.basis not in BASES:
            raise ValidationError(f"{case.case_id}: an unknown group or basis")
        if inflection_spans(content, case.phrase):
            raise ValidationError(f"{case.case_id}: the synthetic statements carry {case.phrase!r}")
        verdicts: dict[str, dict[str, object]] = {}
        for field, is_list in FIELDS_UNDER_TEST:
            value: object = [case.sentence] if is_list else case.sentence
            reasons = evaluate_second_opportunity_output_v1_4(
                t.good_output(**{field: value}),
                t.PACKET,
                t.STATEMENTS,
                t.E2C,
                trusted_context=t.TRUSTED,
                source_metadata=t.META,
            ).refusal_reasons
            prefix = f"{field}[0] " if is_list else f"{field} "
            elsewhere = [r for r in reasons if not r.startswith(prefix)]
            if elsewhere:
                raise ValidationError(f"{case.case_id} is refused outside {field}: {elsewhere[0]}")
            verdicts[field] = {
                "verdict": "REFUSE" if reasons else "PASS",
                "reasons": list(reasons),
            }
        gate = str(verdicts["observed_need"]["verdict"])
        rows.append(
            {
                "case": case.case_id,
                "group": case.group,
                "sentence": case.sentence,
                "phrase": case.phrase,
                "clauses": [
                    {"boundary": c.boundary, "text": c.text}
                    for s in _sentences(case.sentence)
                    for c in context._clauses(s)
                ],
                "occurrences": _occurrences(case.sentence, case.phrase),
                "uncertainty_shaped": bool(context.is_uncertainty_shaped(case.sentence)),
                "gate": verdicts,
                "intended_supported_assertion": case.intended,
                "basis": case.basis,
                "diverges": case.intended in ("PASS", "REFUSE") and gate != case.intended,
            }
        )
    divergences = [str(r["case"]) for r in rows if r["diverges"]]
    if tuple(divergences) != EXPECTED_DIVERGENCES:
        raise ValidationError(
            f"the matrix finds divergences {divergences}, not {list(EXPECTED_DIVERGENCES)}"
        )
    by_id = {str(r["case"]): r for r in rows}
    failing, control = (by_id[c] for c in SMALLEST_FAILING)
    if failing["gate"]["observed_need"]["verdict"] != "REFUSE" or (  # type: ignore[index]
        control["gate"]["observed_need"]["verdict"] != "PASS"  # type: ignore[index]
    ):
        raise ValidationError("the smallest failing pattern and its control no longer differ")
    in_uncertainty_field = [
        str(r["case"])
        for r in rows
        if r["group"] == _L
        and r["uncertainty_shaped"]
        and r["gate"]["critical_uncertainties"]["verdict"] == "REFUSE"  # type: ignore[index]
    ]
    undetermined = [
        {"case": str(r["case"]), "gate": r["gate"]["observed_need"]["verdict"]}  # type: ignore[index]
        for r in rows
        if r["intended_supported_assertion"] == "UNDETERMINED"
    ]
    return {
        "fixture": "packages/opportunity-engine/python/tests/test_semantic_gate_v1_3.py",
        "fields": [f for f, _ in FIELDS_UNDER_TEST],
        "groups": GROUPS,
        "bases": {k: list(v) for k, v in BASES.items()},
        "cases": rows,
        "divergences": divergences,
        "divergences_reaching_the_uncertainty_field": in_uncertainty_field,
        "undetermined": undetermined,
        "smallest_failing_pattern": {
            "failing": failing["sentence"],
            "control": control["sentence"],
            "difference": "one list item, `a need or`, before the gated word",
        },
    }


# --------------------------------------------------------------------------- the diagnosis

#: The operator's four categories, and no other.
CATEGORIES = frozenset(
    {"GENUINE_OUTPUT_DEFECT", "PROMPT_GATE_ALIGNMENT_DEFECT", "GATE_DEFECT", "SOURCE_SUPPORT_GAP"}
)
CLASSIFICATIONS: tuple[dict[str, object], ...] = (
    {
        "field": "observed_need",
        "word": "software",
        "classification": "GATE_DEFECT",
        "cause": (
            "The clause reader's `coord` pattern splits the last item of a list off from the leading "
            "`whether` that questions the whole list, because a verb follows it within three tokens: "
            "`, or software gap is not established ...` is read as a coordinated clause with its own "
            "subject. In the detached clause no marker precedes the word, and the trailing denial "
            "does not clear it, because it is the head noun `gap` and not `software` that the "
            "copula follows. The word is therefore ASSERTED, and the marker check, which runs on "
            "asserted occurrences only, refuses it."
        ),
        "rests_on": [
            "ASSERTION_NOT_TOKEN_PRESENCE",
            "ONE_DENIAL_COVERS_A_LIST",
            "A_COORDINATED_CLAUSE_HAS_ITS_OWN_SUBJECT",
            "THE_SPLIT_IS_KNOWN_AND_CORRECTED_ELSEWHERE",
            "A_MARKER_IS_CHECKED_WHERE_ASSERTED",
            "A_DENIED_GATED_WORD_PASSES_IN_AN_ASSERTING_FIELD",
            "AN_ASSERTING_FIELD_MAY_DENY",
        ],
        "not": {
            "GENUINE_OUTPUT_DEFECT": (
                "the answer frames the word as an uncertainty in its own sentence, and the gate's "
                "documented policy does not refuse a word framed as an uncertainty"
            ),
            "PROMPT_GATE_ALIGNMENT_DEFECT": (
                "the refusal comes from the gate's clause reader, not from a form the prompt failed "
                "to state; prompt v1.6.0's grounding line is stricter than the gate, which cannot "
                "cause a refusal"
            ),
            "SOURCE_SUPPORT_GAP": (
                "nothing about software is asserted, so no support is missing; the absence of the "
                "word from the statements matters only once the reader has made it an assertion"
            ),
        },
    },
    {
        "field": "candidate_intervention_class",
        "word": "market",
        "classification": "GENUINE_OUTPUT_DEFECT",
        "cause": (
            "The class is one clause with no denial, uncertainty or request: `market`, split from "
            "`market-observation` as hyphens split tokens, is asserted. No supplied content statement "
            "carries it, and the one structural fact that contains it, MARKET_ACTIVITY, licenses "
            "its canonical phrase whole and no single word of it."
        ),
        "rests_on": [
            "ASSERTION_NOT_TOKEN_PRESENCE",
            "HYPHENS_SPLIT_TOKENS",
            "NO_SINGLE_WORD_OF_MARKET_ACTIVITY_IS_LICENSED",
            "PROSE_FIELDS_ARE_CHECKED_MARKER_BY_MARKER",
        ],
        "not": {
            "GATE_DEFECT": (
                "every step is the gate's documented rule: one clause, no scope marker, a hyphen "
                "splits tokens, and only the whole canonical phrase of a supported dimension is "
                "licensed"
            ),
            "PROMPT_GATE_ALIGNMENT_DEFECT": (
                "prompt v1.6.0 states that the class is asserted and not free vocabulary, to name a "
                "more neutral class where a richer label needs an unsupplied concept, and that "
                "whether a market exists is not established. It does not state that a dimension "
                "name licenses only its whole phrase, but V9 used the same word under v1.5.0, which "
                "had no structural-channel sentence, so that wording cannot be shown to have caused "
                "it"
            ),
            "SOURCE_SUPPORT_GAP": (
                "the boundary that leaves the single word unlicensed was decided (Mission 1.84.10, "
                "§16 and §17); widening it would be a boundary change, not a gap"
            ),
        },
    },
)

GENERATION_ASSESSMENT: dict[str, object] = {
    "V11_RECOMMENDED": False,
    "ANOTHER_ATTEMPT_UNDER_UNCHANGED_PROMPT_SCHEMA_AND_GATE_JUSTIFIED": False,
    "because": [
        "the class of intervention named an unsupplied word in both answers that reached stage 6, "
        "under prompt v1.5.0 and under prompt v1.6.0, which states the class rule as a surface rule",
        "the one surface change that moved an answer, the request form (V9 0 of 6, V10 7 of 7), is "
        "not evidence that the class vocabulary would move: two answers establish no rate",
        "gate v1.4.0 still refuses a gated word that ends a list under a leading `whether` or "
        "denial, so an answer sound under the policy can still be refused at stage 6",
        "whether anything changes first, and whether synthesis on this packet continues at all, is "
        "the operator's decision; this mission implemented nothing and prepared no packet",
    ],
}

OPERATOR_DECISIONS: tuple[dict[str, object], ...] = (
    {
        "id": "D1_SUCCESSOR_GATE_FOR_THE_LIST_SCOPE_DEFECT",
        "question": (
            "Authorise, or not, a separate successor-gate mission: a gate v1.5.0 beside v1.4.0 in "
            "which the last item of a list stays inside the leading `whether` or denial that scopes "
            "the list, frozen and tested on synthetic cases before any replay."
        ),
        "constraints": [
            "gate v1.4.0 stays byte for byte as frozen, and V10's verdict stays as recorded",
            "no answer is whitelisted and no forbidden concept or marker is removed",
            "an asserted conjunct with its own subject (`..., and buyers pay`) must still split",
        ],
    },
    {
        "id": "D2_PREMODIFIER_OF_A_DENIED_SUBJECT",
        "question": (
            "Decide which the contract means for a gated word that modifies the head noun of a "
            "subject its own clause denies (`Software gap is not established.`): the principle that "
            "a word denied in its own clause is not asserted, or the bounded rule that only the "
            "subject itself is cleared. Either a successor gate carries it, or it is recorded as "
            "accepted narrowness."
        ),
        "constraints": ["decided as policy first, and never from how V10 would fare under it"],
    },
    {
        "id": "D3_CLASS_FIELD_VOCABULARY",
        "question": (
            "Decide whether anything changes for `candidate_intervention_class` before any further "
            "attempt: nothing; a structural constraint on the field (a schema or contract change); "
            "further prompt wording, knowing the rule has been stated twice and the word came back "
            "twice; or the MARKET_ACTIVITY whole-phrase licence, which would widen an evidence "
            "boundary."
        ),
        "constraints": ["the supported-assertion policy is not weakened to admit a word"],
    },
    {
        "id": "D4_WHETHER_TO_ATTEMPT_AGAIN",
        "question": (
            "Decide whether second-opportunity synthesis on this packet continues at all. If it "
            "does, it needs a new packet, a new digest and a new explicit approval, after D1 to D3; "
            "if not, it stops with V10."
        ),
        "constraints": ["no V11 is created by this mission, and V1 to V10 are never re-executed"],
    },
    {
        "id": "D5_PROMPT_STRICTER_THAN_THE_GATE",
        "question": (
            "Prompt v1.6.0 tells the model that every substantive domain concept in an asserting "
            "field comes from the supplied material, with no exception for a denial; the gate "
            "admits a denied word. Keep the prompt stricter, or align it, as generation guidance "
            "only."
        ),
        "constraints": ["the gate is not changed to match the prompt"],
    },
)

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


def governance() -> dict[str, object]:
    try:
        v10 = G101.validate()
    except G101.ValidationError as exc:
        raise ValidationError(f"V10 no longer stands as recorded: gate 101 refuses: {exc}") from exc
    later = [
        "7_evidence_boundary_and_no_distortion",
        "8_attribution_and_provenance",
        "9_persistence_eligibility",
        "10_human_review",
    ]
    stages = v10["VALIDATION_STAGES"]
    if any(stages.get(s) != "NOT_REACHED" for s in later):
        raise ValidationError("a stage after V10's failure is marked other than NOT_REACHED")
    return {
        "V10_PRIMARY_OUTCOME": v10["PRIMARY_OUTCOME"],
        "V10_EXECUTION_APPROVAL_CONSUMED": v10["EXECUTION_APPROVAL_CONSUMED"],
        "V10_FURTHER_CALLS_AUTHORIZED": v10["FURTHER_CALLS_AUTHORIZED_BY_V10"],
        "V10_STAGES_7_TO_10": {s: stages[s] for s in later},
        "V10_HELD_TO_GATE_101": True,
        "V1_TO_V6_HELD_TO_GATE_91_AND_V9_TO_GATE_98": True,
        "V10_RUNNER_REFUSES_A_SECOND_EXECUTE_BEFORE_ANY_TRANSPORT": True,
        "HUMAN_REVIEW_PACKET_V10_EXISTS": G101.REVIEW_PACKET.exists(),
        "CANONICAL_COUNTERS_OBSERVED_READ_ONLY": CANONICAL_COUNTERS_OBSERVED,
        "OPPORTUNITY_2_EXISTS": False,
    }


def check_classifications(refused_fields: set[str]) -> None:
    """One classification per refusal, each from the four categories, each resting on quotes."""
    classified = {str(c["field"]) for c in CLASSIFICATIONS}
    if refused_fields != classified:
        raise ValidationError(f"the refusals {refused_fields} are not the ones classified")
    for c in CLASSIFICATIONS:
        others = CATEGORIES - {c["classification"]}
        if c["classification"] not in CATEGORIES or set(c["not"]) != others:  # type: ignore[call-overload]
            raise ValidationError(f"{c['field']} is not classified once, against the other three")
        for key in c["rests_on"]:  # type: ignore[attr-defined]
            if key not in POLICY_QUOTES:
                raise ValidationError(f"{c['field']} rests on an unquoted rule {key}")


def derive() -> dict[str, Any]:
    quotes = check_quotes()
    inputs = _inputs()
    v10 = reproduce(inputs)
    refused_fields = {str(r["field"]) for r in v10["refused"]}  # type: ignore[index]
    check_classifications(refused_fields)
    software = next(t for t in v10["traces"] if t["word"] == "software")  # type: ignore[attr-defined]
    market = next(t for t in v10["traces"] if t["word"] == "market")  # type: ignore[attr-defined]
    patterns = [b["pattern"] for s in software["sentences"] for b in s["boundaries"]]
    if "coord" not in patterns or software["occurrences"][0]["state"] != "ASSERTED":
        raise ValidationError(
            "the software refusal no longer traces to the coordinated-clause split"
        )
    if (
        market["occurrences"][0]["state"] != "ASSERTED"
        or len(market["sentences"][0]["clauses"]) != 1
        or not market["word_survives_the_supported_dimension_mask"]
        or market["content_carries_word"]
    ):
        raise ValidationError(
            "the market refusal no longer traces to one asserted, unsupplied word"
        )
    return {
        "$comment": (
            "Generated by infrastructure/scripts/render_second_opportunity_stage6_diagnostic_v10.py "
            "(CI gate 102). Every field is re-derived at check time; nothing here is a verdict of a "
            "stage, and V10's recorded verdict is unchanged."
        ),
        "MISSION": MISSION,
        "START_COMMIT": START_COMMIT,
        "BRANCH": BRANCH,
        "PRIMARY_OUTCOME": PRIMARY_OUTCOME,
        "INVARIANTS": INVARIANTS,
        "UNCHANGED": UNCHANGED,
        "FROZEN": frozen(),
        "V10_REPRODUCED": v10,
        "V10_VERDICT_STANDS_WITHOUT_THE_GATE_DEFECT": any(
            c["classification"] == "GENUINE_OUTPUT_DEFECT" and c["field"] in refused_fields
            for c in CLASSIFICATIONS
        ),
        "V9_MARKET": v9_market(),
        "REQUEST_FORMS": request_forms(),
        "PROMPT": prompt_lines(),
        "POLICY_QUOTES": quotes,
        "CLASSIFICATIONS": list(CLASSIFICATIONS),
        "EARLIER_WORDING_CORRECTED": earlier_wording(),
        "SYNTHETIC_MATRIX": run_matrix(),
        "GENERATION_ASSESSMENT": GENERATION_ASSESSMENT,
        "OPERATOR_DECISIONS": list(OPERATOR_DECISIONS),
        "GOVERNANCE": governance(),
    }


def validate() -> dict[str, Any]:
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} is missing")
    derived = derive()
    if _load(RECORD) != derived:
        raise ValidationError(f"{RECORD.name} is not what the diagnosis re-derives")
    return derived


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_stage6_diagnostic_v10.py "
    "from second-opportunity-stage6-diagnostic-v10.json. Do not edit by hand. -->\n\n"
)


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _verdicts(row: dict[str, Any]) -> list[str]:
    return [str(row["gate"][f]["verdict"]) for f, _ in FIELDS_UNDER_TEST]


def render(record: dict[str, Any]) -> str:
    v10 = record["V10_REPRODUCED"]
    matrix = record["SYNTHETIC_MATRIX"]
    out = [
        HEADER.rstrip("\n"),
        "",
        "# Stage 6 diagnostic of V10",
        "",
        f"**`{record['PRIMARY_OUTCOME']}`** ({record['MISSION']}, from `{record['START_COMMIT']}`)",
        "",
        "No provider call, no model inference, no retry, nothing persisted, no packet, no V11. The "
        "semantic gate, the clause reader, the schema, the prompt and the projection are unchanged.",
        "",
        "## The two refusals, reproduced",
        "",
        f"Gate v1.4.0 (`{record['FROZEN']['SEMANTIC_GATE_V1_4_SHA256']}`) over V10's retained answer "
        "returns exactly the reasons the execution retained:",
        "",
        "```",
        *v10["reasons"],
        "```",
        "",
    ]
    for t in v10["traces"]:
        out += [
            f"### `{t['field']}`: *{t['word']}*",
            "",
            f"Disposition `{t['disposition']}`, shape `{t['shape']}`.",
            "",
        ]
        for s in t["sentences"]:
            out.append(f"- sentence: *{s['sentence']}*")
            for b in s["boundaries"]:
                out.append(f"  - boundary `{b['pattern']}` on `{b['matched']}` at {b['at']}")
            for c in s["clauses"]:
                out.append(f"  - clause `{c['boundary']}`: *{c['text']}*")
        for o in t["occurrences"]:
            out.append(f"- occurrence: `{o['state']}` ({o['why']}) in *{o['clause']}*")
        out += [
            f"- a source content statement carries the word: {t['content_carries_word']}; source "
            f"metadata labels carrying it: {t['metadata_labels_carrying_word'] or 'none'}",
            "- the word survives the mask of supported dimension names: "
            f"{t['word_survives_the_supported_dimension_mask']}",
            "",
        ]
    out += ["## Classification", ""]
    out += ["| field | word | classification |", "|---|---|---|"]
    for c in record["CLASSIFICATIONS"]:
        out.append(f"| `{c['field']}` | *{c['word']}* | **{c['classification']}** |")
    out.append("")
    for c in record["CLASSIFICATIONS"]:
        out += [f"**{c['field']} / {c['word']}: {c['classification']}.** {c['cause']}", ""]
        out += [f"- rests on: {', '.join(f'`{k}`' for k in c['rests_on'])}"]
        out += [f"- not {k}: {v}" for k, v in c["not"].items()]
        out.append("")
    earlier = record["EARLIER_WORDING_CORRECTED"]
    out += ["**Earlier wording, corrected here and left where it was written.**", ""]
    out += [f"- `{q['source']}`: *{q['quote']}*" for q in earlier["quotes"].values()]
    out += ["", earlier["correction"], ""]
    v9 = record["V9_MARKET"]
    forms = record["REQUEST_FORMS"]
    out += [
        f"V9 (prompt {v9['prompt']}) was refused on the same word: *{v9['text']}*. Requests shaped as "
        f"requests: V9 {forms['V9']['request_shaped']} of {forms['V9']['items']}, V10 "
        f"{forms['V10']['request_shaped']} of {forms['V10']['items']}.",
        "",
        "## Synthetic matrix",
        "",
        f"On the frozen fixture `{matrix['fixture']}`, each sentence replacing one field of its good "
        "answer. Intended is the verdict the documented policy gives in a SUPPORTED_ASSERTION field.",
        "",
        "| case | group | sentence | observed_need | critical_uncertainties | "
        "commercial_claims_not_supported | intended | state of the word |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in matrix["cases"]:
        states = ", ".join(o["state"] for o in row["occurrences"])
        mark = " **diverges**" if row["diverges"] else ""
        out.append(
            f"| {row['case']} | {row['group']} | {_cell(row['sentence'])} | "
            + " | ".join(_verdicts(row))
            + f" | {row['intended_supported_assertion']}{mark} | {states} |"
        )
    small = matrix["smallest_failing_pattern"]
    out += [
        "",
        f"Divergences: {', '.join(matrix['divergences'])}. Reaching the uncertainty field too: "
        f"{', '.join(matrix['divergences_reaching_the_uncertainty_field']) or 'none'}.",
        "",
        f"Smallest general failing pattern: *{small['failing']}* is refused and *{small['control']}* "
        f"passes; the difference is {small['difference']}.",
        "",
        "## Generation assessment",
        "",
        f"`V11_RECOMMENDED = {record['GENERATION_ASSESSMENT']['V11_RECOMMENDED']}`, "
        "`ANOTHER_ATTEMPT_UNDER_UNCHANGED_PROMPT_SCHEMA_AND_GATE_JUSTIFIED = "
        f"{record['GENERATION_ASSESSMENT']['ANOTHER_ATTEMPT_UNDER_UNCHANGED_PROMPT_SCHEMA_AND_GATE_JUSTIFIED']}`:",
        "",
        *(f"- {b}" for b in record["GENERATION_ASSESSMENT"]["because"]),
        "",
        "## Operator decisions required",
        "",
    ]
    for d in record["OPERATOR_DECISIONS"]:
        out += [f"- **{d['id']}**: {d['question']}"]
        out += [f"  - {c}" for c in d["constraints"]]
    gov = record["GOVERNANCE"]
    out += [
        "",
        "## Governance",
        "",
        f"V10 `{gov['V10_PRIMARY_OUTCOME']}`, approval consumed `{gov['V10_EXECUTION_APPROVAL_CONSUMED']}`, "
        f"further calls `{gov['V10_FURTHER_CALLS_AUTHORIZED']}`, stages 7 to 10 NOT_REACHED, held to gate "
        "101; V1 to V6 held to gate 91 and V9 to gate 98; a second `--execute` refused before any "
        "transport; no human-review packet; Opportunity #2 does not exist.",
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
        "ok       V10's two stage 6 refusals re-derive, one a gate defect and one a genuine output "
        "defect, and nothing the diagnosis holds constant moved"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
