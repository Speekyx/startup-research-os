"""Gate 79: the semantic rules of gate v1.3.0, the prompt block rendered from them, and prompt v1.3.0.

Mission 1.84.12. Two records, both derived from the live code and the merged artifacts, and nothing
else:

* `second-opportunity-semantic-prompt-alignment-v1.json`: the facts reconfirmed from merged records,
  the census of every deterministic semantic rule in gate v1.3.0 with its class, the refusal sites
  mapped to it, the fixture corpus that proves the census against the frozen gate, which rules
  prompt v1.2.0 states, the drift property, the disjunction cross-check, the exposure checks, the
  visibility of source names, and the synthetic prompt-compliance cases;
* `second-opportunity-synthesis-prompt-v4.json`: prompt v1.3.0's regions over the authenticated
  packet snapshot, what was added, and what did not move.

    uv run python infrastructure/scripts/render_second_opportunity_semantic_prompt_alignment.py --check
    uv run python infrastructure/scripts/render_second_opportunity_semantic_prompt_alignment.py --write

The gate refuses: a historical artifact that moved; gate v1.3.0, the output schema or prompt v1.2.0
changed; a reconfirmed fact that is not the one recorded; a refusal site the census does not map, or
a census rule no site produces; a fixture refusal claimed by no rule or by two; an enforced rule no
fixture reaches; a quoted v1.2.0 statement that is not in v1.2.0; a class-A rule prompt v1.3.0 leaves
unstated, or a drift check that would pass v1.2.0; a class-A mutation that does not move the block,
or a class-D mutation that does; a digit, the historical sentence or a hard-coded source name in the
system region; a source name the model is shown that is not already in the approved representation;
a moved representation; a record field the code does not derive.

ZERO model calls, provider requests or TED bytes: everything here runs on the snapshot, the registry
documents and synthetic fixtures.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from collections.abc import Callable, Iterator, Mapping
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-semantic-prompt-alignment-v1.json"
RECORD_MD = DATA / "second-opportunity-semantic-prompt-alignment-v1.md"
PROMPT_RECORD = DATA / "second-opportunity-synthesis-prompt-v4.json"
PROMPT_RECORD_MD = DATA / "second-opportunity-synthesis-prompt-v4.md"
SNAPSHOT_RECORD = DATA / "second-opportunity-v3-diagnostic-replay-v1.json"
REPLAY_V1_3 = DATA / "second-opportunity-v3-diagnostic-replay-gate-v1.3-v1.json"
V3_RECORD = DATA / "second-opportunity-synthesis-execution-record-v3.json"
V3_RESPONSE = DATA / "second-opportunity-synthesis-response-v3.json"
PROMPT_V3 = DATA / "second-opportunity-synthesis-prompt-v3.json"
GATE_76 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
GATE_77 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_3.py"
GATE_78 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay_v1_3.py"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
PACKAGE = ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"

MISSION = "mission-1.84.12"
PROMPT_V1_2_SHA256 = "1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d"
OUTPUT_SCHEMA_SHA256 = "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
GATE_IMPLEMENTATION_SHA256 = "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3"
V3_SENTENCE_FIELD = "statement_classifications[7].statement"

#: Every merged artifact this mission reads and may not rewrite, over its text with LF line ends.
HISTORY_SHA256: dict[str, str] = {
    "docs/data/second-opportunity-synthesis-execution-record-v3.json": (
        "abb093389664405f80878d2a1963beabfa4c271ed559437384146a92ccfb00a3"
    ),
    "docs/data/second-opportunity-synthesis-response-v3.json": (
        "cf5eb183aa7d329f29e8c2c0f04e3939f1661e488952acdf414d07ad8f488ed6"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v3.json": (
        "096eb1845e55a8792c4de7f07b35319de61b6e1af52bd9c4544bd2205533b130"
    ),
    "docs/data/second-opportunity-synthesis-execution-approval-v3.json": (
        "9f951e64d9bc93e1dfb907763c2fdfedc1f3df46b48e63acf927fef3671d027c"
    ),
    "docs/data/second-opportunity-synthesis-prompt-v3.json": (
        "f8e6610facf5cfba7b7aed2fd4b3b365187a74a01b9490915ab008760688ab4e"
    ),
    "docs/data/second-opportunity-v3-diagnostic-replay-v1.json": (
        "43ec43831229bd7afc91910bbe371c275f4c1f3a1f4663332b49d90d50f8fb15"
    ),
    "docs/data/second-opportunity-v3-diagnostic-replay-gate-v1.3-v1.json": (
        "43d80c29ea7bab6bc9c60c53bb20f40b232095c42c9ec50d5861f5b7d4c28468"
    ),
    "docs/data/second-opportunity-output-gate-v1.2-freeze-v1.json": (
        "4404336259dd2d18ce905f1c002f2ca5ccff511f9e4988911ea110084bb65cd1"
    ),
    "docs/data/second-opportunity-output-gate-v1.3-freeze-v1.json": (
        "2f0f07540a812b1054fbb5c696c599c934c18695cc85ddbd2dfaae83f38b79f7"
    ),
    "docs/data/source-metadata-evidence-boundary-decision-v1.json": (
        "11af9195da1c9d4aec4cad055d030a07fd515ecbe3019875f6c2e4a0b64cb610"
    ),
    "docs/architecture/adr/ADR-040-source-metadata-is-provenance-not-factual-support.md": (
        "4e28ac6a303d43ade89fc902cffc4bcb82825b7228b76d89903a87d266a3c102"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v1.json": (
        "7132fc35ab263b86bbe89016f84fd10e9ed54bcc7fb8b30d072e86279b472241"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v1.json": (
        "b769ddeb6ea4d4e773640c3ed83caeff52c52c857fd9125325140de4ab38c799"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v2.json": (
        "5a2f5a7ea20c6de9d4f50498f304e59b6918db63e5ccc9814f988fd3d4f14871"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v2.json": (
        "3fb8d5bae0cb2c64e165961518d9dfd3b1de98eef5244600ea0e5efc289001a7"
    ),
}

ZERO_ACCOUNTING = {
    "MODEL_CALLS": 0,
    "PROVIDER_REQUESTS": 0,
    "MESSAGES_API_REQUESTS": 0,
    "TED_BYTES_SENT": 0,
    "CANONICAL_MUTATIONS": 0,
}

_AUDIT_REASON = re.compile(r"^\S+ audited [A-Z_]+: ")


class ValidationError(RuntimeError):
    """The records disagree with the live code, the merged artifacts, or the frozen gate."""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def text_sha(path: pathlib.Path) -> str:
    return _sha(path.read_text(encoding="utf-8"))


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixtures() -> Any:
    return _module("synthetic_fixtures_for_gate_79", FIXTURES)


# ============================================================================= history and §3


def history() -> dict[str, str]:
    """Every merged artifact this mission reads, byte for byte the one merged."""
    found: dict[str, str] = {}
    for relative, digest in HISTORY_SHA256.items():
        live = text_sha(ROOT / relative)
        if live != digest:
            raise ValidationError(f"{relative} is not the file that was merged")
        found[relative] = live
    return found


def reconfirm() -> dict[str, Any]:
    """§3. What gates v1.1.0, v1.2.0 and v1.3.0 said about V3, read back from the merged records."""
    record, replay, response = _load(V3_RECORD), _load(REPLAY_V1_3), _load(V3_RESPONSE)
    if len(record["SEMANTIC_GATE_REFUSAL_REASONS"]) != 5:
        raise ValidationError("V3's record no longer carries five v1.1.0 reasons")
    if (
        replay["HISTORICAL_V3_GATE_V1_1_REASON_COUNT"] != 5
        or not replay["HISTORICAL_V3_GATE_V1_1_REASONS_REPRODUCED"]
    ):
        raise ValidationError("the v1.3.0 replay no longer reproduces V3's five v1.1.0 reasons")
    v1_2 = replay["HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS"]
    if len(v1_2) != 1 or "'tender'" not in v1_2[0]:
        raise ValidationError("gate v1.2.0's one diagnostic reason is not the one recorded")
    unsupported = replay["UNSUPPORTED_PROPOSITIONS"]
    if len(unsupported) != 1 or unsupported[0]["field"] != V3_SENTENCE_FIELD:
        raise ValidationError("gate v1.3.0 no longer stops on exactly one field")
    sentence = str(unsupported[0]["text"])
    findings = " ".join(unsupported[0]["findings"])
    codes = {
        "SOURCE_METADATA_LABEL_IS_NOT_FACTUAL_SUPPORT": (
            "SOURCE_METADATA_LABEL_IS_NOT_FACTUAL_SUPPORT" in findings
        ),
        "DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY": (
            "DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY" in findings
        ),
    }
    if not all(codes.values()):
        raise ValidationError(f"the one v1.3.0 finding no longer carries both codes: {codes}")
    item = response["parsed_output"]["statement_classifications"][7]
    if item["statement"] != sentence or item["classification"] != "OBSERVED_OR_EVIDENCE_SUPPORTED":
        raise ValidationError("the retained answer does not carry the refused OBSERVED statement")
    failed = [
        a["field"]
        for a in replay["DIAGNOSTIC_AUDIT"]
        if a["verdict"] not in ("SUPPORTED", "NOT_FACTUAL")
    ]
    if failed != [V3_SENTENCE_FIELD]:
        raise ValidationError(f"fields other than the one refused no longer pass: {failed}")
    status = {
        "V3_HISTORICALLY_REJECTED": replay["V3_HISTORICALLY_REJECTED"],
        "V3_CANDIDATE": replay["V3_CANDIDATE"],
        "V3_PERSISTABLE": replay["V3_PERSISTABLE"],
        "V3_HUMAN_REVIEW_PACKET": replay["V3_HUMAN_REVIEW_PACKET"],
        "V3_APPROVAL_CONSUMED": record["EXECUTION_APPROVAL_CONSUMED"],
    }
    if status != {
        "V3_HISTORICALLY_REJECTED": True,
        "V3_CANDIDATE": False,
        "V3_PERSISTABLE": False,
        "V3_HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
        "V3_APPROVAL_CONSUMED": True,
    }:
        raise ValidationError(f"V3's standing moved: {status}")
    return {
        "GATE_V1_1_0_REASONS": len(record["SEMANTIC_GATE_REFUSAL_REASONS"]),
        "GATE_V1_2_0_REASONS": 1,
        "GATE_V1_2_0_REASON_TERM": "tender",
        "GATE_V1_3_0_FAILED_FIELDS": [V3_SENTENCE_FIELD],
        "GATE_V1_3_0_REFUSED_STATEMENT": sentence,
        "GATE_V1_3_0_REFUSED_CLASSIFICATION": item["classification"],
        "GATE_V1_3_0_FINDINGS": sorted(codes),
        "EVERY_OTHER_FIELD_PASSES": True,
        **status,
    }


# ============================================================================= the snapshot


def snapshot() -> tuple[Any, dict[str, str], dict[str, str], Any, str]:
    """The authenticated packet, its statements, its metadata channel and its representation."""
    from sros_opportunity import (
        ExternalSynthesisDecision,
        SynthesisAvailability,
        serialize_packet_for_model,
    )
    from sros_opportunity.second_opportunity_gate_v1_3 import build_source_metadata_context

    gate_76 = _module("gate_76_for_gate_79", GATE_76)
    packet, statements, pairs = gate_76.packet_from_snapshot(
        _load(SNAPSHOT_RECORD)["PACKET_SNAPSHOT"]
    )
    authenticated = gate_76.authenticate(packet, statements, pairs)
    if authenticated["prompt_sha256"] != PROMPT_V1_2_SHA256:
        raise ValidationError("the snapshot no longer rebuilds prompt v1.2.0")
    metadata = build_source_metadata_context(
        _module("gate_78_for_gate_79", GATE_78).registry_entries(list(packet.source_ids))
    )
    measurement = ExternalSynthesisDecision(
        availability=SynthesisAvailability.AVAILABLE,
        packet_id=packet.packet_id,
        refusal_reasons=(),
        per_source=(("ted-eu", "RECOMPUTED_FOR_GATE_79"),),
    )
    representation = serialize_packet_for_model(packet, measurement, statements)
    if _sha(representation) != REPRESENTATION_SHA256 or len(representation) != (
        REPRESENTATION_CHARACTERS
    ):
        raise ValidationError("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")
    return packet, statements, pairs, metadata, representation


def unchanged() -> dict[str, Any]:
    """§4, §5, §16: gate v1.3.0, the schema and prompt v1.2.0 are the ones merged."""
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

    freeze = _module("gate_77_for_gate_79", GATE_77)
    try:
        freeze.validate()
    except freeze.ValidationError as exc:
        raise ValidationError(f"gate 77 no longer validates: {exc}") from exc
    implementation = freeze.implementation_sha256()
    schema = hashlib.sha256(
        json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if implementation != GATE_IMPLEMENTATION_SHA256:
        raise ValidationError("SEMANTIC_GATE_CHANGED: gate v1.3.0's implementation moved")
    if schema != OUTPUT_SCHEMA_SHA256:
        raise ValidationError("OUTPUT_SCHEMA_CHANGED: the v1.1.0 schema moved")
    return {
        "SEMANTIC_GATE_VERSION": "second-opportunity-output-gate@1.3.0",
        "SEMANTIC_GATE_IMPLEMENTATION_SHA256": implementation,
        "SEMANTIC_GATE_CHANGED": False,
        "OUTPUT_SCHEMA_VERSION": "second-opportunity-synthesis-output@1.1.0",
        "OUTPUT_SCHEMA_SHA256": schema,
        "OUTPUT_SCHEMA_CHANGED": False,
        "PROMPT_V1_2_SHA256": PROMPT_V1_2_SHA256,
        "PROMPT_V1_2_CHANGED": False,
    }


# ============================================================================= the census


def refusal_sites() -> list[tuple[str, str, int]]:
    """Every place the two frozen v1.3.0 modules produce a refusal, a finding or a note."""
    receivers = {"reasons", "findings", "unsupported", "exceeded", "audits", "notes"}
    found: list[tuple[str, str, int]] = []
    for name in ("assertion_audit_v1_3.py", "second_opportunity_gate_v1_3.py"):
        tree = ast.parse((PACKAGE / name).read_text(encoding="utf-8"))
        for function in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
            for node in ast.walk(function):
                line: int | None = None
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "append"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in receivers
                ) or (
                    isinstance(node, ast.AugAssign)
                    and isinstance(node.target, ast.Name)
                    and node.target.id in receivers
                ):
                    line = node.lineno
                elif isinstance(node, ast.Return) and isinstance(node.value, ast.List):
                    line = node.lineno if node.value.elts else None
                elif (
                    isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "reasons" for t in node.targets)
                    and isinstance(node.value, ast.List)
                    and node.value.elts
                ):
                    line = node.lineno
                elif (
                    isinstance(node, ast.keyword)
                    and node.arg == "refusal_reasons"
                    and isinstance(node.value, ast.Tuple)
                    and node.value.elts
                ):
                    line = node.value.lineno
                if line is not None:
                    found.append((name, function.name, line))
    return sorted(set(found))


def census() -> dict[str, Any]:
    from sros_opportunity.semantic_generation_rules import (
        GATE_ENFORCED,
        REFUSAL_SITE_RULES,
        SEMANTIC_RULE_CENSUS,
        SEMANTIC_RULE_CENSUS_VERSION,
        census_by_id,
    )

    rules = census_by_id()
    sites = refusal_sites()
    unmapped = [list(s) for s in sites if s not in REFUSAL_SITE_RULES]
    stale = [list(k) for k in REFUSAL_SITE_RULES if k not in sites]
    if unmapped or stale:
        raise ValidationError(f"refusal sites unmapped {unmapped}, mapped but absent {stale}")
    produced: set[str] = set()
    for key, ids in REFUSAL_SITE_RULES.items():
        for rule_id in ids:
            if rule_id not in rules:
                raise ValidationError(f"site {key} maps to {rule_id}, not a census rule")
            produced.add(rule_id)
    enforced = sorted(r.rule_id for r in SEMANTIC_RULE_CENSUS if r.enforcement == GATE_ENFORCED)
    silent = [r for r in enforced if r not in produced]
    if silent:
        raise ValidationError(f"enforced rules no refusal site produces: {silent}")
    counts = {c: sum(1 for r in SEMANTIC_RULE_CENSUS if r.rule_class == c) for c in "ABCD"}
    return {
        "CENSUS_VERSION": SEMANTIC_RULE_CENSUS_VERSION,
        "CENSUS": [r.to_json() for r in SEMANTIC_RULE_CENSUS],
        "CENSUS_RULES": len(SEMANTIC_RULE_CENSUS),
        "CENSUS_CLASS_COUNTS": counts,
        "CENSUS_ENFORCEMENT_COUNTS": {
            e: sum(1 for r in SEMANTIC_RULE_CENSUS if r.enforcement == e)
            for e in ("GATE_ENFORCED", "GATE_MECHANISM", "INSTRUCTION_BEYOND_THE_GATE")
        },
        "REFUSAL_SITES": len(sites),
        "REFUSAL_SITES_MAPPED": len(sites),
        "REFUSAL_SITES_UNMAPPED": 0,
        "ENFORCED_RULES": enforced,
    }


# ============================================================================= coverage


def _claims(decision: Any) -> list[str]:
    """Each refusal the gate produced, with an audit refusal split into its findings."""
    out = [r for r in decision.refusal_reasons if not _AUDIT_REASON.match(r)]
    if decision.audit is not None:
        for field in decision.audit.failed:
            out.extend(field.findings)
    return out


def corpus(fx: Any) -> list[tuple[str, dict[str, Any], dict[str, Any], str]]:
    """(fixture id, answer, gate arguments, the rule it is written to reach). Synthetic only."""
    good = fx.good_output
    base = good()
    summary = base["evidence_bound_reasoning_summary"]
    observed = "OBSERVED_OR_EVIDENCE_SUPPORTED"
    marked = "Supplier Notice Weekly (synthetic register)"
    zero = fx.packet(scoring=False)
    stray_e = "7e7e7e7e-7e7e-4e7e-8e7e-7e7e7e7e7e7e"
    stray_c = "aeaeaeae-aeae-4aea-8aea-aeaeaeaeaeae"
    without = {k: v for k, v in base.items() if k != "observed_need"}
    return [
        ("schema_missing_field", without, {}, "SCHEMA_V1_1_0_VALIDATION"),
        (
            "confidence_other",
            good(confidence_classification="HIGH"),
            {},
            "CONFIDENCE_IS_EXPLORATORY",
        ),
        ("next_evidence_empty", good(recommended_next_evidence=[]), {}, "NEXT_EVIDENCE_NOT_EMPTY"),
        (
            "classifications_empty",
            good(statement_classifications=[]),
            {},
            "CLASSIFICATIONS_NOT_EMPTY",
        ),
        (
            "classification_unknown_kind",
            fx.with_statement("Notices were published.", "OTHER"),
            {},
            "CLASSIFICATION_KINDS_CLOSED",
        ),
        (
            "classification_unknown_label",
            fx.with_statement("Notices were published.", "OTHER"),
            {},
            "CLASSIFICATION_LABEL_KNOWN",
        ),
        (
            "all_observed",
            good(
                statement_classifications=[
                    {
                        "statement": "Notices under CPV class 7777 state differing amounts.",
                        "classification": observed,
                    }
                ]
            ),
            {},
            "SOMETHING_REMAINS_UNKNOWN",
        ),
        (
            "insufficient_evidence",
            good(decision="INSUFFICIENT_EVIDENCE"),
            {},
            "INSUFFICIENT_EVIDENCE_IS_AN_OUTCOME",
        ),
        ("decision_other", good(decision="MAYBE"), {}, "DECISION_IS_ONE_OF_TWO"),
        (
            "undeclared_source",
            good(),
            {"names": fx.metadata(source="another-synthetic-source")},
            "EVERY_SOURCE_DECLARES_ITS_NAMES",
        ),
        ("subject_other", good(subject="another subject"), {}, "SUBJECT_IS_THE_PACKET_IDENTITY"),
        (
            "stray_evidence",
            good(supporting_evidence_ids=[*fx.EVIDENCE, stray_e]),
            {},
            "CITED_EVIDENCE_IN_PACKET",
        ),
        (
            "stray_claim",
            good(supporting_claim_ids=[*fx.CLAIMS, stray_c]),
            {},
            "CITED_CLAIMS_IN_PACKET",
        ),
        ("no_evidence", good(supporting_evidence_ids=[]), {}, "AT_LEAST_ONE_EVIDENCE_CITED"),
        ("no_claim", good(supporting_claim_ids=[]), {}, "AT_LEAST_ONE_CLAIM_CITED"),
        (
            "evidence_without_claim",
            good(supporting_claim_ids=[fx.CLAIMS[0]]),
            {},
            "EVIDENCE_CITED_WITH_ITS_CLAIM",
        ),
        ("stray_family", good(source_families=["knowledge"]), {}, "SOURCE_FAMILIES_FROM_PACKET"),
        (
            "overclaimed_dimension",
            good(supported_dimensions=[*base["supported_dimensions"], "AUDIENCE_OR_USAGE"]),
            {},
            "SUPPORTED_DIMENSIONS_FROM_PACKET",
        ),
        (
            "both_lists",
            good(unsupported_dimensions=[*base["unsupported_dimensions"], "ECONOMIC_VALUE"]),
            {},
            "SUPPORTED_AND_UNSUPPORTED_DISJOINT",
        ),
        (
            "mandatory_missing",
            good(unsupported_dimensions=[]),
            {},
            "MANDATORY_UNSUPPORTED_REPORTED",
        ),
        (
            "independence_not_unknown",
            good(independence_status="Two source families."),
            {},
            "INDEPENDENCE_RECORDS_UNKNOWN",
        ),
        (
            "independence_called_independent",
            good(independence_status="Independence is UNKNOWN; these are independent sources."),
            {},
            "INDEPENDENCE_RECORDS_UNKNOWN",
        ),
        (
            "reliability_scorable_dropped",
            good(reliability_status="Rows are reviewed."),
            {},
            "RELIABILITY_RESTATES_SCORABILITY",
        ),
        (
            "reliability_non_scorable_dropped",
            good(reliability_status="Rows are reviewed."),
            {"evidence_packet": zero},
            "RELIABILITY_RESTATES_SCORABILITY",
        ),
        ("extra_field", good(notes="an extra field"), {}, "FIELD_HAS_A_CONTEXT"),
        (
            "unsupplied_identifier",
            good(evidence_bound_reasoning_summary=summary + " BT-999 applies here."),
            {},
            "DEFINITIONAL_IDENTIFIER_SUPPLIED",
        ),
        (
            "unsupplied_number",
            good(evidence_bound_reasoning_summary=summary + " The median is 123456 EUR."),
            {},
            "NUMBERS_ARE_SUPPLIED",
        ),
        (
            "uncertainty_not_shaped",
            good(critical_uncertainties=["Authorities publish notices again."]),
            {},
            "FIELD_SHAPE_KEPT",
        ),
        (
            "request_not_shaped",
            good(recommended_next_evidence=["Payments were made under these notices."]),
            {},
            "FIELD_SHAPE_KEPT",
        ),
        (
            "transformation_concept",
            good(evidence_bound_reasoning_summary=summary + " Buyers are willing to pay."),
            {},
            "TRANSFORMATION_CONCEPTS_NOT_ASSERTED",
        ),
        (
            "added_concept",
            good(evidence_bound_reasoning_summary=summary + " The authorities have an unmet need."),
            {},
            "ADDED_CONCEPTS_NOT_ASSERTED",
        ),
        (
            "limiting_fact_restated",
            good(evidence_bound_reasoning_summary=summary + " BT-161 shows actual expenditure."),
            {},
            "LIMITING_FACT_NEVER_SUPPORTS_ITS_CONCEPT",
        ),
        (
            "score_asserted",
            good(reliability_status="Both rows are SCORABLE and scored."),
            {},
            "NO_SCORE_ASSERTED",
        ),
        (
            "word_only_in_a_source_name",
            fx.with_statement("Suppliers publish notices.", observed),
            {"supplied": fx.statements(name=marked), "names": fx.metadata(name=marked)},
            "SOURCE_NAME_IS_NOT_A_SUPPLIED_WORD",
        ),
        (
            "word_supplied_nowhere",
            good(evidence_bound_reasoning_summary=summary + " Gyms publish these notices."),
            {},
            "PRIOR_KNOWLEDGE_IS_NOT_SUPPORT",
        ),
        (
            "unmeasured_quantity",
            good(evidence_bound_reasoning_summary=summary + " The notices reveal the TAM."),
            {},
            "UNMEASURED_COMMERCIAL_QUANTITIES_NEVER_ASSERTED",
        ),
        (
            "commercial_term_without_its_dimension",
            good(evidence_bound_reasoning_summary=summary + " Adoption is rising."),
            {},
            "COMMERCIAL_TERMS_NEED_THEIR_DIMENSION",
        ),
        (
            "validation_wording",
            good(evidence_bound_reasoning_summary=summary + " This is a validated pattern."),
            {},
            "NO_VALIDATION_LANGUAGE",
        ),
        (
            "observed_disjunction",
            fx.with_statement(
                "Notices under CPV class 7777 state amounts in EUR or in another currency.",
                observed,
            ),
            {},
            "OBSERVED_DISJUNCTION_FAILS_CLOSED",
        ),
        (
            "hypothesis_promoted",
            good(
                hypothesis_statement=(
                    "One question worth testing is whether these authorities publish comparable "
                    "notices again; they certainly will."
                )
            ),
            {},
            "NOTHING_PROMOTED_TO_A_CONCLUSION",
        ),
        (
            "not_supported_item_claims_support",
            good(
                commercial_claims_not_supported=[
                    "Willingness to pay is established by the register."
                ]
            ),
            {},
            "NOT_SUPPORTED_ITEM_NEVER_CLAIMS_SUPPORT",
        ),
    ]


def coverage() -> dict[str, Any]:
    """Every fixture refusal claimed by exactly one census rule, and every enforced rule reached."""
    from sros_opportunity.semantic_generation_rules import GATE_ENFORCED, SEMANTIC_RULE_CENSUS

    fx = fixtures()
    if fx.gate(fx.good_output()).refusal_reasons:
        raise ValidationError("the synthetic good answer no longer passes gate v1.3.0")
    enforced = [r for r in SEMANTIC_RULE_CENSUS if r.enforcement == GATE_ENFORCED]
    by_fixture: dict[str, list[str]] = {}
    reached: set[str] = set()
    claimed = 0
    for fixture_id, answer, arguments, target in corpus(fx):
        decision = fx.gate(answer, **arguments)
        rules: list[str] = []
        for claim in _claims(decision):
            owners = [
                r.rule_id
                for r in enforced
                if r.refusal_signature is not None and re.search(r.refusal_signature, claim)
            ]
            if len(owners) != 1:
                raise ValidationError(
                    f"{fixture_id}: {claim[:120]!r} is claimed by {owners}, and exactly one rule "
                    "must claim every refusal"
                )
            rules.append(owners[0])
            claimed += 1
        if target not in rules:
            raise ValidationError(f"{fixture_id} was written to reach {target} and reached {rules}")
        by_fixture[fixture_id] = sorted(set(rules))
        reached.update(rules)
    missing = sorted(r.rule_id for r in enforced if r.rule_id not in reached)
    if missing:
        raise ValidationError(f"enforced rules no fixture reaches: {missing}")
    return {
        "FIXTURES": len(by_fixture),
        "REFUSALS_CLAIMED": claimed,
        "REFUSALS_UNCLAIMED": 0,
        "REFUSALS_CLAIMED_TWICE": 0,
        "ENFORCED_RULES_REACHED": len(reached),
        "ENFORCED_RULES": len(enforced),
        "BY_FIXTURE": by_fixture,
    }


# ============================================================================= explicitness, drift


def explicitness(v1_2: Any, v1_3: Any) -> dict[str, Any]:
    from sros_opportunity.semantic_generation_rules import (
        SEMANTIC_RULE_CENSUS,
        unstated_semantic_rules,
    )

    regions = {
        "system": v1_2.system_instructions,
        "trusted_context": v1_2.trusted_context,
        "task": v1_2.task,
    }
    quoted: list[str] = []
    for rule in SEMANTIC_RULE_CENSUS:
        if rule.v1_2_evidence is None:
            continue
        region, text = rule.v1_2_evidence
        if text not in regions[region]:
            raise ValidationError(f"{rule.rule_id} quotes v1.2.0's {region}, which does not say it")
        quoted.append(rule.rule_id)
    unstated_v1_2 = unstated_semantic_rules(
        v1_2.system_instructions, v1_2.trusted_context, v1_2.task
    )
    unstated_v1_3 = unstated_semantic_rules(
        v1_3.system_instructions, v1_3.trusted_context, v1_3.task
    )
    if unstated_v1_3:
        raise ValidationError(f"prompt v1.3.0 leaves {unstated_v1_3} unstated")
    if not unstated_v1_2:
        raise ValidationError("the drift check would pass prompt v1.2.0, so it checks nothing")
    rendered_in_v1_2 = [
        r.rule_id
        for r in SEMANTIC_RULE_CENSUS
        if r.must_be_explicit_in_v1_3 and not r.explicit_in_v1_2 and r.rule_id not in unstated_v1_2
    ]
    if rendered_in_v1_2:
        raise ValidationError(f"{rendered_in_v1_2} are called absent from v1.2.0 and are there")
    return {
        "RULES_QUOTED_FROM_V1_2": quoted,
        "UNSTATED_IN_V1_2": unstated_v1_2,
        "UNSTATED_IN_V1_2_COUNT": len(unstated_v1_2),
        "UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES": len(unstated_v1_3),
    }


@contextlib.contextmanager
def _patched(target: Any, name: str, value: object) -> Iterator[None]:
    original = getattr(target, name)
    setattr(target, name, value)
    try:
        yield
    finally:
        setattr(target, name, original)


def drift() -> dict[str, Any]:
    """§18. A class-A input moved moves the block; a class-D list moved leaves it byte-identical."""
    from sros_opportunity import (
        assertion_context,
        guards,
        lexical_inflection,
        second_opportunity,
    )
    from sros_opportunity import semantic_generation_rules as sgr
    from sros_opportunity.assertion_context import Disposition, ForbiddenConcept, Shape

    policy = sgr.SEMANTIC_GENERATION_POLICY
    baseline = sgr.render_semantic_generation_rules(policy)
    fields = list(policy.field_policy)
    need = next(i for i, f in enumerate(fields) if f.field_name == "observed_need")
    concepts = list(policy.forbidden_concepts)
    added = next(i for i, c in enumerate(concepts) if c.name not in policy.transformation_names)
    decision = dict(policy.metadata_decision)
    census = list(policy.census)
    instructed = next(i for i, r in enumerate(census) if r.instruction)
    mechanism = next(i for i, r in enumerate(census) if r.rule_class == "D")
    observed = next(
        k
        for k, v in policy.classification_dispositions.items()
        if v is Disposition.SUPPORTED_ASSERTION
    )

    def with_field() -> Any:
        moved = list(fields)
        moved[need] = dataclasses.replace(
            fields[need], disposition=Disposition.HYPOTHESIS_TO_VALIDATE
        )
        return dataclasses.replace(policy, field_policy=tuple(moved))

    def with_concept(change: Callable[[ForbiddenConcept], ForbiddenConcept]) -> Any:
        moved = list(concepts)
        moved[added] = change(concepts[added])
        return dataclasses.replace(policy, forbidden_concepts=tuple(moved))

    def with_census(index: int, **changes: object) -> Any:
        moved = list(census)
        moved[index] = dataclasses.replace(census[index], **changes)
        return dataclasses.replace(policy, census=tuple(moved))

    class_a: dict[str, Callable[[], str]] = {
        "field_disposition": lambda: sgr.render_semantic_generation_rules(with_field()),
        "concept_never_text": lambda: sgr.render_semantic_generation_rules(
            with_concept(lambda c: dataclasses.replace(c, never=c.never + " mutated"))
        ),
        "concept_added": lambda: sgr.render_semantic_generation_rules(
            dataclasses.replace(
                policy,
                forbidden_concepts=(
                    *concepts,
                    ForbiddenConcept("MUTATED_CONCEPT", ("mutated phrase",), "a mutated bound"),
                ),
            )
        ),
        "metadata_may_not_support": lambda: sgr.render_semantic_generation_rules(
            dataclasses.replace(
                policy,
                metadata_decision={
                    **decision,
                    "metadata_may_not_support": [
                        *decision["metadata_may_not_support"],
                        "a mutated proposition",
                    ],
                },
            )
        ),
        "metadata_is": lambda: sgr.render_semantic_generation_rules(
            dataclasses.replace(
                policy,
                metadata_decision={**decision, "metadata_is": decision["metadata_is"][1:]},
            )
        ),
        "disjunction_connectives": lambda: sgr.render_semantic_generation_rules(
            dataclasses.replace(
                policy,
                disjunction=dataclasses.replace(
                    policy.disjunction,
                    connectives=(*policy.disjunction.connectives, "nor"),
                ),
            )
        ),
        "classification_label": lambda: sgr.render_semantic_generation_rules(
            dataclasses.replace(
                policy,
                classification_dispositions={
                    (f"{k}_MUTATED" if k == observed else k): v
                    for k, v in policy.classification_dispositions.items()
                },
            )
        ),
        "census_instruction": lambda: sgr.render_semantic_generation_rules(
            with_census(instructed, instruction=str(census[instructed].instruction) + " mutated")
        ),
    }
    moved_a = {name: render() != baseline for name, render in class_a.items()}
    for name, table, key in (
        (
            "disposition_wording",
            sgr.DISPOSITION_WORDING,
            (Disposition.SUPPORTED_ASSERTION, Shape.FREE),
        ),
        ("classification_meaning", sgr.CLASSIFICATION_MEANING, Disposition.HYPOTHESIS_TO_VALIDATE),
    ):
        original = table[key]  # type: ignore[index]
        table[key] = original + " mutated"  # type: ignore[index]
        try:
            moved_a[name] = sgr.render_semantic_generation_rules(policy) != baseline
        finally:
            table[key] = original  # type: ignore[index]

    class_d: dict[str, str] = {
        "concept_phrases": sgr.render_semantic_generation_rules(
            with_concept(lambda c: dataclasses.replace(c, phrases=(*c.phrases, "mutated phrase")))
        ),
        "census_mechanism_rationale": sgr.render_semantic_generation_rules(
            with_census(mechanism, rationale="a mutated rationale")
        ),
    }
    for name, module, attribute, value in (
        (
            "external_knowledge_markers",
            second_opportunity,
            "PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS",
            (*second_opportunity.PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS, "mutatedmarker"),
        ),
        (
            "forbidden_terms",
            guards,
            "FORBIDDEN_TERMS",
            {**guards.FORBIDDEN_TERMS, "mutated term": None},
        ),
        ("validation_words", guards, "VALIDATION_WORDS", guards.VALIDATION_WORDS | {"mutated"}),
        (
            "certainty_markers",
            assertion_context,
            "CERTAINTY_MARKERS",
            (*assertion_context.CERTAINTY_MARKERS, "mutatedly"),
        ),
        (
            "support_predicates",
            assertion_context,
            "SUPPORT_PREDICATES",
            (*assertion_context.SUPPORT_PREDICATES, "mutates"),
        ),
        (
            "denial_markers",
            assertion_context,
            "DENIAL_MARKERS_V1_3",
            (*assertion_context.DENIAL_MARKERS_V1_3, "mutatedly not"),
        ),
        (
            "inflection_rules",
            lexical_inflection,
            "INFLECTION_RULES",
            (*lexical_inflection.INFLECTION_RULES, ("MUTATED", "m", "m", "m -> m")),
        ),
    ):
        with _patched(module, attribute, value):
            class_d[name] = sgr.render_semantic_generation_rules(policy)
    moved_d = {name: text != baseline for name, text in class_d.items()}
    if not all(moved_a.values()):
        raise ValidationError(f"class-A inputs that do not move the block: {moved_a}")
    if any(moved_d.values()):
        raise ValidationError(f"class-D lists that reach the block: {moved_d}")
    return {
        "CLASS_A_MUTATIONS": sorted(moved_a),
        "CLASS_A_MOVED": sum(moved_a.values()),
        "CLASS_D_MUTATIONS": sorted(moved_d),
        "CLASS_D_MOVED": sum(moved_d.values()),
    }


def disjunction_cross_check() -> dict[str, Any]:
    """The rendered connectives are the frozen detector's, joining alternatives and denied."""
    from sros_opportunity.assertion_audit_v1_3 import disjunctive_connectives
    from sros_opportunity.semantic_generation_rules import SEMANTIC_GENERATION_POLICY

    examples = {
        "or": "Notices state amounts in EUR or in another currency.",
        "either ... or": "Either notices state amounts in EUR or they state none.",
    }
    denied = "No notice states a price or a payment."
    rendered = list(SEMANTIC_GENERATION_POLICY.disjunction.connectives)
    if sorted(rendered) != sorted(examples):
        raise ValidationError(f"the rendered connectives {rendered} are not the checked ones")
    detected = {c: list(disjunctive_connectives(t)) for c, t in examples.items()}
    if not all(detected.values()) or disjunctive_connectives(denied):
        raise ValidationError("the frozen detector disagrees with the rendered disjunction rule")
    return {
        "CONNECTIVES": rendered,
        "DETECTED": detected,
        "DENIED_TOGETHER_DETECTED": False,
    }


# ============================================================================= the prompt


def prompt_regions() -> dict[str, Any]:
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2,
        SECOND_OPPORTUNITY_SYSTEM_V1_2,
        render_second_opportunity_prompt_v1_2,
    )
    from sros_opportunity.second_opportunity_prompt_v1_3 import (
        SEMANTIC_GENERATION_RULES_BLOCK_V1_3,
        render_second_opportunity_prompt_v1_3,
        second_opportunity_prompt_hash_v1_3,
    )

    packet, statements, pairs, metadata, representation = snapshot()
    v1_2 = render_second_opportunity_prompt_v1_2(packet, statements, pairs)
    v1_3 = render_second_opportunity_prompt_v1_3(
        packet, statements, pairs, source_metadata=metadata
    )
    fx = fixtures()
    synthetic = render_second_opportunity_prompt_v1_3(
        fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
    )
    return {
        "packet": packet,
        "statements": statements,
        "metadata": metadata,
        "representation": representation,
        "v1_2": v1_2,
        "v1_3": v1_3,
        "synthetic": synthetic,
        "block": SEMANTIC_GENERATION_RULES_BLOCK_V1_3,
        "contract": SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2,
        "system_v1_2": SECOND_OPPORTUNITY_SYSTEM_V1_2,
        "prompt_sha256": second_opportunity_prompt_hash_v1_3(v1_3),
    }


def exposure(regions: Mapping[str, Any], sentence: str) -> dict[str, Any]:
    block = str(regions["block"])
    system = str(regions["v1_3"].system_instructions)
    added = system[len(str(regions["system_v1_2"])) :]
    found = {
        "DIGITS_IN_SEMANTIC_BLOCK": len(re.findall(r"\d", block)),
        "REGEX_FRAGMENTS_IN_SEMANTIC_BLOCK": len(re.findall(r"\\b|\(\?|\[a-z|\\s", block)),
        "HISTORICAL_SENTENCE_IN_PROMPT": sentence.lower() in system.lower()
        or sentence.lower() in str(regions["v1_3"].trusted_context).lower(),
        "WORD_TENDER_IN_ADDED_SYSTEM_TEXT": "tender" in added.lower(),
        "HISTORICAL_EXECUTION_NAMED_IN_ADDED_SYSTEM_TEXT": re.search(r"\bV3\b", added) is not None,
        "SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION": "Tenders Electronic Daily" in system,
        "SYSTEM_REGION_PACKET_INDEPENDENT": system == str(regions["synthetic"].system_instructions),
    }
    expected = {
        "DIGITS_IN_SEMANTIC_BLOCK": 0,
        "REGEX_FRAGMENTS_IN_SEMANTIC_BLOCK": 0,
        "HISTORICAL_SENTENCE_IN_PROMPT": False,
        "WORD_TENDER_IN_ADDED_SYSTEM_TEXT": False,
        "HISTORICAL_EXECUTION_NAMED_IN_ADDED_SYSTEM_TEXT": False,
        "SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION": False,
        "SYSTEM_REGION_PACKET_INDEPENDENT": True,
    }
    if found != expected:
        raise ValidationError(f"the prompt exposes what it must not: {found}")
    return found


def source_origin(regions: Mapping[str, Any]) -> dict[str, Any]:
    """§13, §14: the model can tell a name from content, and nothing new leaves."""
    from sros_opportunity.semantic_generation_rules import source_labels_in_statements

    labels = source_labels_in_statements(
        regions["packet"], regions["statements"], regions["metadata"]
    )
    representation = str(regions["representation"])
    outside = [label.text for label in labels if label.text not in representation]
    if not labels or outside:
        raise ValidationError(f"SOURCE_ORIGIN_NOT_VISIBLE_ENOUGH_TO_MODEL or new bytes: {outside}")
    return {
        "SOURCE_LABELS_SHOWN": [
            {"text": label.text, "kind": label.kind.value, "source_id": label.source_id}
            for label in labels
        ],
        "SOURCE_LABELS_OCCUR_IN_APPROVED_REPRESENTATION": True,
        "SOURCE_ORIGIN_VISIBLE_TO_MODEL": True,
        "REPRESENTATION_SHA256": _sha(representation),
        "REPRESENTATION_CHARACTERS": len(representation),
        "REPRESENTATION_CHANGED": False,
    }


def compliance_cases(regions: Mapping[str, Any]) -> list[dict[str, Any]]:
    """§19. The rule each case needs is in the v1.3.0 prompt; the gate's verdict on both sides."""
    from sros_opportunity.semantic_generation_rules import unstated_semantic_rules

    fx = fixtures()
    observed = "OBSERVED_OR_EVIDENCE_SUPPORTED"
    hypothesis = "HYPOTHESIS_TO_VALIDATE"
    unknown = "UNKNOWN_REQUIRES_EVIDENCE"
    plain = "Contracts Weekly (synthetic register)"
    marked = "Supplier Contracts Weekly (synthetic register)"

    def named(name: str) -> dict[str, Any]:
        return {"supplied": fx.statements(name=name), "names": fx.metadata(name=name)}

    cases: list[tuple[str, str, tuple[str, ...], list[tuple[str, dict, dict]]]] = [
        (
            "A",
            "a source name containing a domain word never yields an OBSERVED fact of that word",
            ("SOURCE_NAME_IS_NOT_A_SUPPLIED_WORD", "OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED"),
            [
                ("forbidden", fx.with_statement("Contracts occur.", observed), named(plain)),
                (
                    "forbidden_gated_word",
                    fx.with_statement("Supplier contracts occur.", observed),
                    named(marked),
                ),
            ],
        ),
        (
            "B",
            "an atomic OBSERVED statement a source content statement establishes is allowed",
            ("OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED",),
            [
                (
                    "compliant",
                    fx.with_statement(
                        "Notices under CPV class 7777 state amounts in EUR.", observed
                    ),
                    {},
                )
            ],
        ),
        (
            "C",
            "an OBSERVED statement never joins alternatives",
            ("OBSERVED_DISJUNCTION_FAILS_CLOSED",),
            [
                (
                    "forbidden",
                    fx.with_statement(
                        "Notices under CPV class 7777 state amounts in EUR or in another currency.",
                        observed,
                    ),
                    {},
                )
            ],
        ),
        (
            "D",
            "two statements are preferred to one joined statement",
            ("OBSERVED_DISJUNCTION_FAILS_CLOSED",),
            [
                (
                    "compliant",
                    {
                        **fx.good_output(),
                        "statement_classifications": [
                            *fx.good_output()["statement_classifications"],
                            {
                                "statement": "Notices under CPV class 7777 state amounts in EUR.",
                                "classification": observed,
                            },
                            {
                                "statement": "Whether any notice states another currency is "
                                "unknown.",
                                "classification": unknown,
                            },
                        ],
                    },
                    {},
                )
            ],
        ),
        (
            "E",
            "incomplete support gives HYPOTHESIS_TO_VALIDATE or UNKNOWN_REQUIRES_EVIDENCE",
            ("OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED", "OBSERVED_DISJUNCTION_FAILS_CLOSED"),
            [
                (
                    "forbidden",
                    fx.with_statement("Authorities publish these notices every year.", observed),
                    {},
                ),
                (
                    "compliant",
                    fx.with_statement(
                        "Notices under CPV class 7777 state amounts in EUR or in another currency.",
                        hypothesis,
                    ),
                    {},
                ),
            ],
        ),
        (
            "F",
            "a publisher's name may appear, whole, as provenance",
            ("SOURCE_NAME_LICENSES_ITS_WHOLE_OCCURRENCE",),
            [
                (
                    "compliant",
                    fx.with_statement(
                        "Supplier Contracts Weekly reported notices under CPV class 7777.",
                        observed,
                    ),
                    named(marked),
                )
            ],
        ),
        (
            "G",
            "a forbidden concept may appear as not supported or as unknown, never as observed",
            ("TRANSFORMATION_CONCEPTS_NOT_ASSERTED", "FIELD_TEXT_READ_BY_ITS_DISPOSITION"),
            [
                ("forbidden", fx.with_statement("Buyers are willing to pay.", observed), {}),
                (
                    "compliant",
                    fx.with_statement("Whether buyers are willing to pay is unknown.", unknown),
                    {},
                ),
            ],
        ),
    ]
    v1_3 = regions["v1_3"]
    unstated = set(
        unstated_semantic_rules(v1_3.system_instructions, v1_3.trusted_context, v1_3.task)
    )
    out: list[dict[str, Any]] = []
    for case, claim, rules, variants in cases:
        if unstated & set(rules):
            raise ValidationError(f"case {case}: {sorted(unstated & set(rules))} not in v1.3.0")
        verdicts: dict[str, str] = {}
        for variant, answer, arguments in variants:
            decision = fx.gate(answer, **arguments)
            verdicts[variant] = "PASSES_GATE" if decision.persist else "REFUSED_BY_GATE"
        out.append(
            {"case": case, "claim": claim, "prompt_rules": list(rules), "gate_verdicts": verdicts}
        )
    expected = {
        "A": {"forbidden": "PASSES_GATE", "forbidden_gated_word": "REFUSED_BY_GATE"},
        "B": {"compliant": "PASSES_GATE"},
        "C": {"forbidden": "REFUSED_BY_GATE"},
        "D": {"compliant": "PASSES_GATE"},
        "E": {"forbidden": "PASSES_GATE", "compliant": "PASSES_GATE"},
        "F": {"compliant": "PASSES_GATE"},
        "G": {"forbidden": "REFUSED_BY_GATE", "compliant": "PASSES_GATE"},
    }
    found = {c["case"]: c["gate_verdicts"] for c in out}
    if found != expected:
        raise ValidationError(f"the compliance cases moved: {found}")
    return out


def _added_lines(before: str, after: str) -> list[str]:
    if not after.startswith(before):
        raise ValidationError("a v1.3.0 region does not extend its v1.2.0 region verbatim")
    return [line for line in after[len(before) :].split("\n") if line.strip()]


def prompt_record(regions: Mapping[str, Any]) -> dict[str, Any]:
    from sros_opportunity.output_constraints import (
        MUST_BE_EXPLICIT_IN_PROMPT,
        OUTPUT_CONSTRAINT_RENDERER_VERSION,
        constraint_inventory,
        is_explicit,
    )
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        SECOND_OPPORTUNITY_PROMPT_ID,
    )
    from sros_opportunity.semantic_generation_rules import (
        SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
        SEMANTIC_RULE_CENSUS_VERSION,
        SOURCE_LABEL_BLOCK_RENDERER_VERSION,
        policy_digest,
        render_source_label_block,
    )

    predecessor = _load(PROMPT_V3)
    v1_2, v1_3 = regions["v1_2"], regions["v1_3"]
    system, trusted = v1_3.system_instructions, v1_3.trusted_context
    checks = {
        "system v1.2.0": (_sha(v1_2.system_instructions), predecessor["SYSTEM_SHA256"]),
        "trusted v1.2.0": (_sha(v1_2.trusted_context), predecessor["TRUSTED_CONTEXT_SHA256"]),
        "task v1.2.0": (_sha(v1_2.task), predecessor["TASK_SHA256"]),
        "contract block": (
            _sha(str(regions["contract"])),
            predecessor["OUTPUT_CONTRACT_BLOCK_SHA256"],
        ),
    }
    moved = [name for name, (live, frozen) in checks.items() if live != frozen]
    if moved:
        raise ValidationError(f"v1.2.0 regions that no longer match their record: {moved}")
    if v1_3.untrusted != v1_2.untrusted or v1_3.task != v1_2.task:
        raise ValidationError("the TED statements or the task moved under prompt v1.3.0")
    anti = system.index("WHAT THIS PACKET IS AND IS NOT.")
    confidence = "CONFIDENCE. `confidence_classification` is EXPLORATORY and nothing else."
    unchanged = {
        "TED_CONTENT_BYTE_IDENTICAL": v1_3.untrusted == v1_2.untrusted,
        "TRUSTED_EVIDENCE_AND_CLAIMS_BYTE_IDENTICAL": v1_3.untrusted == v1_2.untrusted,
        "TASK_BYTE_IDENTICAL": v1_3.task == v1_2.task,
        "SCHEMA_CONSTRAINT_BLOCK_BYTE_IDENTICAL": str(regions["contract"]) in system,
        "COMMERCIAL_BOUNDARIES_BYTE_IDENTICAL": anti >= 0
        and v1_2.system_instructions[anti:] == system[anti : len(v1_2.system_instructions)],
        "CONFIDENCE_PARAGRAPH_BYTE_IDENTICAL": confidence in system,
        "V1_2_SYSTEM_REGION_IS_A_PREFIX": system.startswith(v1_2.system_instructions),
        "V1_2_TRUSTED_CONTEXT_IS_A_PREFIX": trusted.startswith(v1_2.trusted_context),
    }
    if not all(unchanged.values()):
        raise ValidationError(f"prompt v1.3.0 moved what it must not: {unchanged}")
    unstated_bounds = [
        f"{c.path} {c.keyword}"
        for c in constraint_inventory(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
        if c.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT and not is_explicit(c, system)
    ]
    if unstated_bounds:
        raise ValidationError(f"prompt v1.3.0 leaves schema bounds unstated: {unstated_bounds}")
    labels = render_source_label_block(
        regions["packet"], regions["statements"], regions["metadata"]
    )
    return {
        "$comment": (
            "Mission 1.84.12. The v1.3.0 prompt regions over the authenticated packet snapshot, "
            "frozen and hashed and never transmitted. Prompt v1.2.0 and its record are unchanged; "
            "v1.3.0 extends its system region and its trusted context verbatim and leaves the TED "
            "statements and the task byte-identical. CI gate 79 re-derives every field."
        ),
        "record_version": "second-opportunity-synthesis-prompt@1.3.0",
        "mission": "1.84.12",
        "recorded_by": MISSION,
        "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
        "PROMPT_VERSION": "1.3.0",
        "PROCEDURE": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        "PROMPT_SHA256": regions["prompt_sha256"],
        "PREDECESSOR_PROMPT_VERSION": "1.2.0",
        "PREDECESSOR_PROMPT_SHA256": PROMPT_V1_2_SHA256,
        "PREDECESSOR_UNCHANGED": True,
        "SUBJECT": "ted-eu:CPV-class:9261",
        "PACKET_ID": regions["packet"].packet_id,
        "OUTPUT_CONSTRAINT_RENDERER": OUTPUT_CONSTRAINT_RENDERER_VERSION,
        "SEMANTIC_GENERATION_RULES_RENDERER": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
        "SEMANTIC_RULE_CENSUS": SEMANTIC_RULE_CENSUS_VERSION,
        "SOURCE_LABEL_BLOCK_RENDERER": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
        "SEMANTIC_GENERATION_POLICY_DIGEST": policy_digest(),
        "SYSTEM_INSTRUCTION": system,
        "SYSTEM_SHA256": _sha(system),
        "PREDECESSOR_SYSTEM_SHA256": predecessor["SYSTEM_SHA256"],
        "OUTPUT_CONTRACT_BLOCK_SHA256": predecessor["OUTPUT_CONTRACT_BLOCK_SHA256"],
        "SEMANTIC_BLOCK": str(regions["block"]),
        "SEMANTIC_BLOCK_SHA256": _sha(str(regions["block"])),
        "TRUSTED_CONTEXT": trusted,
        "TRUSTED_CONTEXT_SHA256": _sha(trusted),
        "PREDECESSOR_TRUSTED_CONTEXT_SHA256": predecessor["TRUSTED_CONTEXT_SHA256"],
        "SOURCE_LABEL_BLOCK": labels,
        "SOURCE_LABEL_BLOCK_SHA256": _sha(labels),
        "TASK_SHA256": _sha(v1_3.task),
        "UNTRUSTED_SHA256": _sha(json.dumps([list(p) for p in v1_3.untrusted], ensure_ascii=False)),
        "UNTRUSTED_ITEMS": len(v1_3.untrusted),
        "REGIONS_IDENTICAL_TO_V1_2_0": ["untrusted", "task"],
        "REGIONS_EXTENDED_VERBATIM": ["system_instructions", "trusted_context"],
        "SEMANTIC_DIFF": {
            "SYSTEM_ADDED_LINES": _added_lines(v1_2.system_instructions, system),
            "SYSTEM_REMOVED_LINES": [],
            "TRUSTED_CONTEXT_ADDED_LINES": _added_lines(v1_2.trusted_context, trusted),
            "TRUSTED_CONTEXT_REMOVED_LINES": [],
            "UNTRUSTED_CHANGED": False,
            "TASK_CHANGED": False,
        },
        "UNCHANGED": unchanged,
        "UNSTATED_GENERATION_CONSTRAINTS": 0,
        "UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES": 0,
        "OUTPUT_SCHEMA_VERSION": "second-opportunity-synthesis-output@1.1.0",
        "OUTPUT_SCHEMA_SHA256": OUTPUT_SCHEMA_SHA256,
        "OUTPUT_GATE_VERSION": "second-opportunity-output-gate@1.3.0",
        "TED_REPRESENTATION_SHA256": REPRESENTATION_SHA256,
        "TED_REPRESENTATION_UNCHANGED": True,
        "SENT": False,
        "sent_note": (
            "This document records regions that were frozen and never transmitted. Execution "
            "packet V4 binds this prompt version, no approval names V4, and 0 provider requests "
            "were made."
        ),
    }


# ============================================================================= the records


def build_records() -> tuple[dict[str, Any], dict[str, Any]]:
    from sros_opportunity.semantic_generation_rules import (
        OPERATOR_DECISION_SEMANTIC_PROMPT_ALIGNMENT,
        SEMANTIC_GENERATION_POLICY_VERSION,
        SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
        policy_digest,
    )

    merged = history()
    facts = reconfirm()
    regions = prompt_regions()
    prompt = prompt_record(regions)
    record: dict[str, Any] = {
        "$comment": (
            "Mission 1.84.12. The census of gate v1.3.0's deterministic semantic rules, the prompt "
            "block rendered from its first-class policy objects, and the checks that bind them. "
            "Nothing here reads an answer to render text; CI gate 79 re-derives every field."
        ),
        "record_version": "second-opportunity-semantic-prompt-alignment@1.0.0",
        "mission": MISSION,
        "OPERATOR_DECISION": list(OPERATOR_DECISION_SEMANTIC_PROMPT_ALIGNMENT),
        "HISTORY_UNCHANGED": merged,
        "RECONFIRMED_FROM_MERGED_ARTIFACTS": facts,
        **unchanged(),
        **census(),
        "COVERAGE": coverage(),
        **explicitness(regions["v1_2"], regions["v1_3"]),
        "RENDERER": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
        "POLICY_VERSION": SEMANTIC_GENERATION_POLICY_VERSION,
        "POLICY_DIGEST": policy_digest(),
        "SEMANTIC_BLOCK_SHA256": _sha(str(regions["block"])),
        "SEMANTIC_BLOCK_LINES": len(str(regions["block"]).split("\n")),
        "DRIFT": drift(),
        "DISJUNCTION_CROSS_CHECK": disjunction_cross_check(),
        "EXPOSURE": exposure(regions, str(facts["GATE_V1_3_0_REFUSED_STATEMENT"])),
        "SOURCE_ORIGIN": source_origin(regions),
        "PROMPT_V1_3_SHA256": prompt["PROMPT_SHA256"],
        "PROMPT_V1_3_RECORD": PROMPT_RECORD.name,
        "COMPLIANCE_CASES": compliance_cases(regions),
        "V3_REPLAYED": False,
        "V3_WHITELISTED": False,
        "V3_TEXT_USED_TO_RENDER": False,
        "accounting": dict(ZERO_ACCOUNTING),
    }
    return record, prompt


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    record, prompt = build_records()
    for path, built in ((RECORD, record), (PROMPT_RECORD, prompt)):
        if not path.exists():
            raise ValidationError(f"{path.name} does not exist; run --write")
        if _load(path) != built:
            raise ValidationError(f"{path.name} is not what the live code derives")
    return record, prompt


# ============================================================================= rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_semantic_prompt_alignment.py "
    "from {source}. Do not edit by hand; edit the code and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def render(record: Mapping[str, Any]) -> str:
    facts = record["RECONFIRMED_FROM_MERGED_ARTIFACTS"]
    coverage_ = record["COVERAGE"]
    drift_ = record["DRIFT"]
    origin = record["SOURCE_ORIGIN"]
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: semantic prompt alignment",
        "",
        f"Mission {record['mission'].removeprefix('mission-')}. Gate v1.3.0 is unchanged "
        f"(`{record['SEMANTIC_GATE_IMPLEMENTATION_SHA256'][:12]}...`), the schema is unchanged "
        f"(`{record['OUTPUT_SCHEMA_SHA256'][:12]}...`), and prompt v1.2.0 is unchanged "
        f"(`{record['PROMPT_V1_2_SHA256'][:12]}...`). Prompt v1.3.0 adds the rules the gate "
        "applies and v1.2.0 never stated.",
        "",
        "## The operator's decision",
        "",
        *_code(list(record["OPERATOR_DECISION"])),
        "## Reconfirmed from the merged artifacts",
        "",
        f"Gate v1.1.0 refused V3 on {facts['GATE_V1_1_0_REASONS']} reasons, gate v1.2.0 on "
        f"{facts['GATE_V1_2_0_REASONS']} (`{facts['GATE_V1_2_0_REASON_TERM']}`), and gate v1.3.0 "
        f"on one field, `{facts['GATE_V1_3_0_FAILED_FIELDS'][0]}`, classified "
        f"`{facts['GATE_V1_3_0_REFUSED_CLASSIFICATION']}`, with findings "
        + ", ".join(f"`{f}`" for f in facts["GATE_V1_3_0_FINDINGS"])
        + ". Every other field passes. V3 stays rejected: candidate "
        f"`{str(facts['V3_CANDIDATE']).lower()}`, persistable "
        f"`{str(facts['V3_PERSISTABLE']).lower()}`, human-review packet "
        f"`{facts['V3_HUMAN_REVIEW_PACKET']}`, approval consumed "
        f"`{str(facts['V3_APPROVAL_CONSUMED']).lower()}`.",
        "",
        "## The census",
        "",
        f"{record['CENSUS_RULES']} rules in `{record['CENSUS_VERSION']}`: "
        + ", ".join(f"{k} {v}" for k, v in record["CENSUS_CLASS_COUNTS"].items())
        + ". Enforcement: "
        + ", ".join(f"{k} {v}" for k, v in record["CENSUS_ENFORCEMENT_COUNTS"].items())
        + f". {record['REFUSAL_SITES']} refusal sites in the two frozen modules, every one mapped.",
        "",
        "| rule | class | enforcement | explicit in v1.2.0 | fields |",
        "|---|---|---|---|---|",
        *[
            f"| `{r['rule_id']}` | {r['class']} | {r['enforcement']} | "
            f"{'yes' if r['explicit_in_v1_2'] else 'no'} | "
            f"{', '.join(r['fields'][:3])}{', ...' if len(r['fields']) > 3 else ''} |"
            for r in record["CENSUS"]
        ],
        "",
        "## The census proved against the frozen gate",
        "",
        f"{coverage_['FIXTURES']} synthetic fixtures, {coverage_['REFUSALS_CLAIMED']} refusals, "
        f"each claimed by exactly one rule; {coverage_['ENFORCED_RULES_REACHED']} of "
        f"{coverage_['ENFORCED_RULES']} enforced rules reached.",
        "",
        "## What prompt v1.2.0 left unstated",
        "",
        f"{record['UNSTATED_IN_V1_2_COUNT']} class-A rules: "
        + ", ".join(f"`{r}`" for r in record["UNSTATED_IN_V1_2"])
        + ". Prompt v1.3.0 leaves "
        f"{record['UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES']}.",
        "",
        "## Drift",
        "",
        f"Class-A mutations that move the block: {drift_['CLASS_A_MOVED']} of "
        f"{len(drift_['CLASS_A_MUTATIONS'])}. Class-D mutations that move it: "
        f"{drift_['CLASS_D_MOVED']} of {len(drift_['CLASS_D_MUTATIONS'])}.",
        "",
        "## Source names",
        "",
        "The model is shown, as names, the registry labels that occur in the supplied statements, "
        "every one already inside the approved representation "
        f"(`{origin['REPRESENTATION_SHA256'][:12]}...`, {origin['REPRESENTATION_CHARACTERS']} "
        "characters, unchanged):",
        "",
        *[f"- `{label['text']}` ({label['kind']})" for label in origin["SOURCE_LABELS_SHOWN"]],
        "",
        "## Synthetic prompt-compliance cases",
        "",
        "| case | claim | gate verdicts |",
        "|---|---|---|",
        *[
            f"| {c['case']} | {c['claim']} | "
            + ", ".join(f"{k}: {v}" for k, v in c["gate_verdicts"].items())
            + " |"
            for c in record["COMPLIANCE_CASES"]
        ],
        "",
        "A synthetic pass is evidence that the rules and the machinery agree on well-formed text, "
        "never evidence about a model's answer. Where a forbidden variant passes the gate, the "
        "rule is an instruction the gate does not evaluate, and the record says so.",
        "",
        f"Prompt v1.3.0: `{record['PROMPT_V1_3_SHA256']}`. Accounting: "
        + ", ".join(f"{k.lower()} {v}" for k, v in record["accounting"].items())
        + ".",
        "",
    ]
    return "\n".join(out)


def render_prompt(prompt: Mapping[str, Any]) -> str:
    diff = prompt["SEMANTIC_DIFF"]
    out = [
        HEADER.format(source=PROMPT_RECORD.name),
        "# Second opportunity: synthesis prompt v1.3.0",
        "",
        f"`{prompt['PROMPT_SHA256']}`, predecessor v1.2.0 `{prompt['PREDECESSOR_PROMPT_SHA256']}` "
        "unchanged. Never transmitted.",
        "",
        *_code(
            [
                f"system region          {prompt['SYSTEM_SHA256']}",
                f"v1.2.0 system (prefix) {prompt['PREDECESSOR_SYSTEM_SHA256']}",
                f"output-contract block  {prompt['OUTPUT_CONTRACT_BLOCK_SHA256']}",
                f"semantic block         {prompt['SEMANTIC_BLOCK_SHA256']}",
                f"trusted context        {prompt['TRUSTED_CONTEXT_SHA256']}",
                f"v1.2.0 trusted(prefix) {prompt['PREDECESSOR_TRUSTED_CONTEXT_SHA256']}",
                f"source-name section    {prompt['SOURCE_LABEL_BLOCK_SHA256']}",
                f"task (unchanged)       {prompt['TASK_SHA256']}",
                f"untrusted (unchanged)  {prompt['UNTRUSTED_SHA256']}",
                f"representation         {prompt['TED_REPRESENTATION_SHA256']}",
            ]
        ),
        "## What was added to the system region",
        "",
        *_code(list(diff["SYSTEM_ADDED_LINES"])),
        "## What was added to the trusted context",
        "",
        *_code(list(diff["TRUSTED_CONTEXT_ADDED_LINES"])),
        "Removed lines: none in either region. Untrusted region changed: "
        f"`{str(diff['UNTRUSTED_CHANGED']).lower()}`; task changed: "
        f"`{str(diff['TASK_CHANGED']).lower()}`.",
        "",
        "## Unchanged",
        "",
        *[f"- `{k}`: `{str(v).lower()}`" for k, v in prompt["UNCHANGED"].items()],
        "",
    ]
    return "\n".join(out)


def _write_json(path: pathlib.Path, data: Mapping[str, Any]) -> None:
    path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            record, prompt = build_records()
            _write_json(RECORD, record)
            _write_json(PROMPT_RECORD, prompt)
            RECORD_MD.write_bytes(render(record).encode("utf-8"))
            PROMPT_RECORD_MD.write_bytes(render_prompt(prompt).encode("utf-8"))
            print(f"wrote    {RECORD.name}, {PROMPT_RECORD.name} and their pages")
        record, prompt = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    for path, text in ((RECORD_MD, render(record)), (PROMPT_RECORD_MD, render_prompt(prompt))):
        if path.read_text(encoding="utf-8") != text:
            print(f"FAIL     {path.name} is not the rendering of its record")
            return 1
    print(
        "ok       the semantic prompt block states every class-A rule of gate v1.3.0, from "
        "first-class policy objects, and prompt v1.3.0 moves nothing else"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
