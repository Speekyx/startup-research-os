"""Mission 1.84.23, CI gate 99. Prompt v1.6.0: v1.5.0 with the generation-surface block.

The operator accepted V9's refusal, kept schema v1.2.0, gate v1.4.0, the strict architecture, the
timeout, the ceiling and the headroom, and asked for a prompt successor that states the bounded surface
forms the gate already reads. This gate re-derives one record from the live code and the merged
artifacts:

    second-opportunity-synthesis-prompt-v7.json   the v1.6.0 regions over the snapshot, V9's refusals
                                                  reproduced and classified, the census, the
                                                  conformance cases and the exposure checks

It refuses: gate v1.4.0 not the frozen one, before or after the conformance cases run; a merged artifact
moved; V9's record, response or approval not what gate 98 validates, its seven refusals not reproduced
by gate v1.4.0 from the retained answer, or a refusal outside the two families; the approved
representation or prompt v1.5.0's digest moved; a v1.6.0 trusted context, untrusted region or task other
than v1.5.0's; a system region that is not v1.5.0's, byte for byte, followed by the surface block and
nothing else; a surface, schema, semantic or headroom rule unstated, or a check that would pass prompt
v1.5.0; a canonical request form the frozen gate does not read as a request, or an instruction it does;
a synthetic case the frozen gate judges otherwise than the policy says; a V9 sentence, a file read or a
private gate pattern reachable from the policy or the prompt; a digit in the block or a number in the
prompt module; and a model call or network request of any kind.

    uv run python infrastructure/scripts/render_second_opportunity_prompt_v1_6.py --check
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from collections.abc import Mapping, Sequence
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

PROMPT_RECORD = DATA / "second-opportunity-synthesis-prompt-v7.json"
PROMPT_RECORD_MD = DATA / "second-opportunity-synthesis-prompt-v7.md"
PROMPT_V6_RECORD = DATA / "second-opportunity-synthesis-prompt-v6.json"
PACKAGE = ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"
POLICY_MODULE = PACKAGE / "generation_surface_policy.py"
PROMPT_MODULE = PACKAGE / "second_opportunity_prompt_v1_6.py"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_81 = SCRIPTS / "render_second_opportunity_execution_packet_v4.py"
GATE_87 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"
GATE_98 = SCRIPTS / "render_second_opportunity_execution_record_v9.py"

MISSION = "mission-1.84.23"
SUBJECT = "ted-eu:CPV-class:9261"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
PROMPT_V1_5_SHA256 = "0713eb8053e83627e1156324cc9003031fff1f8e81289efe5cc89f182f542abb"
GATE_V1_4_IMPLEMENTATION_SHA256 = "eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb"
V9_SHA256 = "ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d"
V9_FAILED_STAGE = "6_semantic_output_gate_v1_4_0"

#: Every merged artifact this gate reads and may not rewrite, byte for byte as merged.
HISTORY_SHA256: dict[str, str] = {
    "docs/data/second-opportunity-synthesis-prompt-v6.json": (
        "1affcd2d18f4d189a88869c758eaba1c50867d3799a1375c823713a169ece9fe"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v9.json": (
        "90bcbcb871aaa20a3f024fcbcd6a4030dc197afc502675740e680c4a2b84881e"
    ),
    "docs/data/second-opportunity-synthesis-execution-approval-v9.json": (
        "86f73a61ca8178be3a43708c5e775789c5ffc5a7bb32187f032c8f188ab59854"
    ),
    "docs/data/second-opportunity-synthesis-response-v9.json": (
        "f129e8edba6bbf0bb8c4d182888a9ecdc7f34f4f4ca9dce09a3377cfdc4b6bdd"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v9.json": (
        "6b2eeba732df1f5ecf7ed52032625d3ab0204cee2f1ee935663fa25bfcf3ea61"
    ),
    "docs/data/second-opportunity-output-gate-v1.4-freeze-v1.json": (
        "cfac46842312a532471e24466c989922fcdffc7da1a17e332063ba2aac01917d"
    ),
    "packages/opportunity-engine/python/sros_opportunity/second_opportunity_prompt_v1_5.py": (
        "9bbe6a016fcc0a7c29616aada446ff85e0bcb2eab3b1d0fbbd48d4ed9abd007a"
    ),
}

#: The files the prompt v1.6.0 freeze commits, before any V10 artifact exists.
FREEZE_FILES: tuple[str, ...] = (
    "packages/opportunity-engine/python/sros_opportunity/generation_surface_policy.py",
    "packages/opportunity-engine/python/sros_opportunity/second_opportunity_prompt_v1_6.py",
    "packages/opportunity-engine/python/tests/test_generation_surface_policy.py",
    "packages/opportunity-engine/python/tests/test_second_opportunity_prompt_v1_6.py",
    "infrastructure/scripts/render_second_opportunity_prompt_v1_6.py",
)

FAMILY_A = "GENUINE_OUTPUT_SUPPORT_FAILURE_UNDER_CURRENT_POLICY"
FAMILY_B = "GENERATION_SURFACE_FORM_MISALIGNMENT"

#: Sections 17 and 18. Synthetic answers over the fixture packet, and what the frozen gate must do with
#: each. None of these strings comes from an answer a model produced.
CONFORMANCE_CASES: tuple[dict[str, Any], ...] = (
    {
        "case": "SUPPORTED_CLASS_PASSES",
        "field": "candidate_intervention_class",
        "value": "A comparison of the stated amounts in published notices.",
        "persist": True,
        "reason": None,
    },
    {
        "case": "UNSUPPORTED_CLASS_CONCEPT_FAILS",
        "field": "candidate_intervention_class",
        "value": "Software for buyers.",
        "persist": False,
        "reason": "audited UNSUPPORTED",
    },
    {
        "case": "HYPOTHESIS_FRAMED_UNSUPPORTED_CLASS_STILL_FAILS",
        "field": "candidate_intervention_class",
        "value": "A class to be tested: a subscription product.",
        "persist": False,
        "reason": "audited UNSUPPORTED",
    },
    {
        "case": "EVIDENCE_OF_IS_A_REQUEST",
        "field": "recommended_next_evidence",
        "value": ["Evidence of whether the same authorities publish comparable notices again."],
        "persist": True,
        "reason": None,
    },
    {
        "case": "OBSERVATION_OF_IS_A_REQUEST",
        "field": "recommended_next_evidence",
        "value": ["Observation of the frequency of such notices across periods."],
        "persist": True,
        "reason": None,
    },
    {
        "case": "IDENTIFICATION_OF_IS_A_REQUEST",
        "field": "recommended_next_evidence",
        "value": ["Identification of the suppliers associated with these notices."],
        "persist": True,
        "reason": None,
    },
    {
        "case": "IMPERATIVE_FAILS",
        "field": "recommended_next_evidence",
        "value": ["Investigate whether the same authorities publish comparable notices again."],
        "persist": False,
        "reason": "it is not request-shaped",
    },
    {
        "case": "DECLARATIVE_FINDING_FAILS",
        "field": "recommended_next_evidence",
        "value": ["Payments under these notices are established."],
        "persist": False,
        "reason": "it is not request-shaped",
    },
    {
        "case": "PRESUPPOSED_CONFIRMATION_FAILS",
        "field": "recommended_next_evidence",
        "value": ["Evidence of the confirmed payments under these notices."],
        "persist": False,
        "reason": "promote a FUTURE_EVIDENCE_REQUEST to a conclusion",
    },
)

#: Common instructions the policy says a request never opens with, each checked against the gate.
INSTRUCTION_VERBS: tuple[str, ...] = (
    "Investigate",
    "Find",
    "Identify",
    "Determine",
    "Obtain",
    "Check",
    "Verify",
    "Establish",
    "Observe",
)

ZERO_ACCOUNTING = {
    "MODEL_CALLS": 0,
    "PROVIDER_REQUESTS": 0,
    "MESSAGES_API_REQUESTS": 0,
    "TOKEN_COUNT_API_REQUESTS": 0,
    "TED_BYTES_SENT": 0,
    "CANONICAL_MUTATIONS": 0,
}


class ValidationError(RuntimeError):
    """A record disagrees with the live code, the merged artifacts or gate v1.4.0's freeze."""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _integers(path: pathlib.Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) is int]


def _shingles(text: str, width: int = 6) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i : i + width]) for i in range(len(words) - width + 1)}


# ============================================================================= preconditions


def history() -> dict[str, str]:
    for relative, digest in HISTORY_SHA256.items():
        if file_sha(relative) != digest:
            raise ValidationError(f"{relative} is not the file that was merged")
    return dict(HISTORY_SHA256)


def gate_v1_4_digest() -> str:
    """Section 6: gate v1.4.0's implementation digest, which no part of this mission may move."""
    gate = _module("gate_87_for_gate_99", GATE_87)
    live = gate.implementation_sha256()
    if live != gate.FROZEN_IMPLEMENTATION_SHA256 or live != GATE_V1_4_IMPLEMENTATION_SHA256:
        raise ValidationError(
            "PROMPT_SUCCESSOR_WOULD_MODIFY_FROZEN_SEMANTIC_GATE: gate v1.4.0's implementation is "
            f"{live}, not the frozen {GATE_V1_4_IMPLEMENTATION_SHA256}"
        )
    if gate.file_sha(gate.TEST_FILE) != gate.FROZEN_TEST_SHA256:
        raise ValidationError(
            "PROMPT_SUCCESSOR_WOULD_MODIFY_FROZEN_SEMANTIC_GATE: its test file moved"
        )
    return str(live)


# ============================================================================= V9, re-derived


def family_of(detail: Mapping[str, Any]) -> tuple[str, Any]:
    """Section 4: which of the two families a stage 6 refusal belongs to, from the field policy."""
    from sros_opportunity.assertion_context import Disposition, Shape
    from sros_opportunity.second_opportunity_gate_v1_2 import SECOND_OPPORTUNITY_FIELD_POLICY

    policy = {fc.field_name: fc for fc in SECOND_OPPORTUNITY_FIELD_POLICY}
    field = str(detail["field"]).split("[")[0]
    context = policy.get(field)
    if context is None:
        raise ValidationError(f"{field} is not a field the policy names")
    if (
        detail["kind"] == "UNSUPPORTED_TERM"
        and context.disposition is Disposition.SUPPORTED_ASSERTION
    ):
        return FAMILY_A, context
    if (
        detail["kind"] == "NOT_REQUEST_SHAPED"
        and context.disposition is Disposition.FUTURE_EVIDENCE_REQUEST
        and context.shape is Shape.REQUEST
    ):
        return FAMILY_B, context
    raise ValidationError(
        f"{detail['field']} ({detail['kind']}) belongs to neither family, so this mission's premise "
        "does not hold"
    )


def v9_block() -> tuple[dict[str, Any], list[str]]:
    """Section 3: V9 re-derived from what it kept, and its seven refusals reproduced by gate v1.4.0."""
    g98 = _module("gate_98_for_gate_99", GATE_98)
    try:
        record = g98.validate()
    except g98.ValidationError as error:
        raise ValidationError(f"V9_RECORD_NOT_REPRODUCED: {error}") from error
    artifact = _load(g98.RESPONSE)
    packet_file = _load(g98.PACKET_V9)
    if record["execution_packet_sha256"] != V9_SHA256:
        raise ValidationError("the V9 record names another packet")
    report, statements, _found = g98.replay(artifact, packet_file)
    reasons = list(report["reasons"])
    if (
        report["failed_stage"] != V9_FAILED_STAGE
        or reasons != record["SEMANTIC_GATE_REFUSAL_REASONS"]
    ):
        raise ValidationError(
            "gate v1.4.0 does not reproduce V9's refusals from the retained answer"
        )
    details = g98.semantic_details(artifact["parsed_output"], statements, reasons)
    rows: list[dict[str, Any]] = []
    for detail in details:
        family, context = family_of(detail)
        row: dict[str, Any] = {
            "field": detail["field"],
            "disposition": context.disposition.value,
            "shape": context.shape.value,
            "verdict": detail["verdict"],
            "kind": detail["kind"],
            "family": family,
        }
        if detail["kind"] == "UNSUPPORTED_TERM":
            row["unsupported_term"] = detail["term"]
        else:
            row["first_word"] = detail["first_word"]
            row["promotion_words"] = detail["confirmation_words"]
        rows.append(row)
    a = [r for r in rows if r["family"] == FAMILY_A]
    b = [r for r in rows if r["family"] == FAMILY_B]
    usage = record["ACTUAL_USAGE"]
    block = {
        "EXECUTION_PACKET_ID": record["execution_packet_id"],
        "EXECUTION_PACKET_SHA256": record["execution_packet_sha256"],
        "PRIMARY_OUTCOME": record["PRIMARY_OUTCOME"],
        "OPERATOR_ACCEPTS_V9_RESULT": True,
        "PROVIDER_REQUESTS": record["actual_provider_requests"],
        "HTTP_STATUS": record["HTTP_STATUS"],
        "ELAPSED_SECONDS": record["timing"]["elapsed_seconds"],
        "STOP_REASON": record["STOP_REASON"],
        "USAGE": {
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "thinking_tokens": usage["thinking_tokens"],
            "total_tokens": usage["total_tokens"],
        },
        "ACTUAL_COST": record["ACTUAL_COST"]["cost_units"],
        "ROOT_KEYS_RETURNED": record["ROOT_KEYS_RETURNED"],
        "UNKNOWN_ROOT_PROPERTIES_RETURNED": len(record["UNKNOWN_ROOT_PROPERTIES_RETURNED"]),
        "VALIDATION_STAGES": record["VALIDATION_STAGES"],
        "SEMANTIC_REFUSALS": len(reasons),
        "SEMANTIC_REFUSALS_REPRODUCED_BY_GATE_V1_4_0": True,
        "reproduced_by": (
            "gate 98's validation of the V9 record, then the V9 runner's own stages replayed from "
            "Mission 1.84.10's authenticated snapshot with no database, gate v1.4.0 at stage 6"
        ),
        "REFUSALS": rows,
        "FAMILIES": {
            FAMILY_A: {
                "refusals": len(a),
                "fields": sorted({str(r["field"]) for r in a}),
                "disposition": "SUPPORTED_ASSERTION",
                "reading": (
                    "a concept in an asserted field that no supplied statement supports; under the "
                    "current policy the answer, not the gate, is at fault, and the policy is kept"
                ),
            },
            FAMILY_B: {
                "refusals": len(b),
                "fields": sorted({str(r["field"]).split("[")[0] for r in b}),
                "disposition": "FUTURE_EVIDENCE_REQUEST",
                "shape": "REQUEST",
                "with_promotion_words": sum(1 for r in b if r["promotion_words"]),
                "reading": (
                    "each item opens as an instruction, which the gate does not read as a request; "
                    "the bounded form exists and was not surfaced to the model, and the request "
                    "parser is kept"
                ),
            },
        },
        "SUPPORTED_ASSERTION_POLICY_WEAKENED": False,
        "REQUEST_PARSER_EXPANDED": False,
        "V9_REPLAYED_AS_A_PASS_CANDIDATE": False,
        "V9_WOULD_HAVE_PASSED_CLAIMED": False,
    }
    if (len(a), len(b)) != (1, 6):
        raise ValidationError(f"V9's refusals split {len(a)} and {len(b)}, not one and six")
    texts = [str(detail["text"]) for detail in details]
    return block, texts


# ============================================================================= the regions


def regions() -> dict[str, Any]:
    from sros_opportunity.second_opportunity_prompt_v1_5 import (
        render_second_opportunity_prompt_v1_5,
        second_opportunity_prompt_hash_v1_5,
    )
    from sros_opportunity.second_opportunity_prompt_v1_6 import (
        render_second_opportunity_prompt_v1_6,
    )

    snap = _module("gate_81_for_gate_99", GATE_81).snapshot()
    if snap.representation_sha256 != REPRESENTATION_SHA256:
        raise ValidationError("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")
    arguments = (snap.packet, snap.statements, snap.pairs)
    v1_5 = render_second_opportunity_prompt_v1_5(*arguments, source_metadata=snap.metadata)
    recorded = _load(PROMPT_V6_RECORD)["PROMPT_SHA256"]
    if second_opportunity_prompt_hash_v1_5(v1_5) != PROMPT_V1_5_SHA256 or recorded != (
        PROMPT_V1_5_SHA256
    ):
        raise ValidationError("prompt v1.5.0 no longer renders to its frozen digest")
    fx = _module("fixtures_for_gate_99", FIXTURES)
    return {
        "snap": snap,
        "v1_5": v1_5,
        "v1_6": render_second_opportunity_prompt_v1_6(*arguments, source_metadata=snap.metadata),
        "synthetic": render_second_opportunity_prompt_v1_6(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
        ),
    }


def prompt_differential(parts: Mapping[str, Any]) -> dict[str, Any]:
    """Section 15: v1.6.0 is v1.5.0 byte for byte, then the surface block, and nothing else."""
    from sros_opportunity.generation_surface_policy import render_generation_surface_block
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_SYSTEM
    from sros_opportunity.second_opportunity_prompt_v1_5 import (
        GENERATION_HEADROOM_BLOCK_V1_5,
        OUTPUT_CONTRACT_BLOCK_V1_5,
        SECOND_OPPORTUNITY_SYSTEM_V1_5,
        SEMANTIC_GENERATION_RULES_BLOCK_V1_5,
    )

    v1_5, v1_6 = parts["v1_5"], parts["v1_6"]
    for region in ("trusted_context", "untrusted", "task"):
        if getattr(v1_5, region) != getattr(v1_6, region):
            raise ValidationError(f"PROMPT_V1_6_HAS_UNAPPROVED_DRIFT: the {region} moved")
    if "SOURCE NAMES" not in str(v1_6.trusted_context):
        raise ValidationError("the SOURCE NAMES section is no longer in the trusted context")
    old, new = str(v1_5.system_instructions), str(v1_6.system_instructions)
    if old != SECOND_OPPORTUNITY_SYSTEM_V1_5:
        raise ValidationError("prompt v1.5.0's system region is not its module's")
    if not new.startswith(old):
        raise ValidationError(
            "PROMPT_V1_6_HAS_UNAPPROVED_DRIFT: v1.5.0's system region is not a byte-identical prefix"
        )
    if new[len(old) :] != "\n" + render_generation_surface_block() + "\n":
        raise ValidationError(
            "PROMPT_V1_6_HAS_UNAPPROVED_DRIFT: the system region adds something other than the "
            "surface block"
        )
    for name, block in (
        ("base system instruction", SECOND_OPPORTUNITY_SYSTEM),
        ("output-contract block", OUTPUT_CONTRACT_BLOCK_V1_5),
        ("semantic block", SEMANTIC_GENERATION_RULES_BLOCK_V1_5),
        ("headroom block", GENERATION_HEADROOM_BLOCK_V1_5),
    ):
        if block not in old:
            raise ValidationError(f"the {name} is not carried byte for byte")
    before, after = old.split("\n"), new.split("\n")
    return {
        "REGIONS_BYTE_IDENTICAL_TO_V1_5_0": ["trusted_context", "untrusted", "task"],
        "TED_UNTRUSTED_REGION_BYTE_IDENTICAL": True,
        "TRUSTED_STATEMENTS_IDS_AND_SOURCE_NAMES_BYTE_IDENTICAL": True,
        "TASK_BYTE_IDENTICAL": True,
        "BASE_SYSTEM_INSTRUCTION_BYTE_IDENTICAL": True,
        "OUTPUT_CONTRACT_BLOCK_BYTE_IDENTICAL": True,
        "SEMANTIC_POLICY_BLOCK_BYTE_IDENTICAL": True,
        "HEADROOM_BLOCK_BYTE_IDENTICAL": True,
        "V1_5_0_SYSTEM_REGION_IS_A_BYTE_IDENTICAL_PREFIX": True,
        "SYSTEM_LINES_V1_5_0": len(before),
        "SYSTEM_LINES_V1_6_0": len(after),
        "SYSTEM_LINES_ADDED": len(after) - len(before),
        "SYSTEM_LINES_REMOVED": 0,
        "SYSTEM_LINES_MOVED": 0,
        "WHAT_WAS_ADDED": (
            "one blank line, then the generation-surface block rendered from the policy objects, "
            "after the last line of v1.5.0's system region"
        ),
        "PROMPT_V1_6_HAS_UNAPPROVED_DRIFT": False,
    }


def prompt_checks(parts: Mapping[str, Any]) -> dict[str, Any]:
    """Section 16: nothing unstated, the checks discriminate, and no number of the module's own."""
    from sros_opportunity.generation_surface_policy import SURFACE_RULE_IDS
    from sros_opportunity.second_opportunity_prompt_v1_6 import (
        GENERATION_SURFACE_BLOCK_V1_6,
        unstated_constraints_in,
        unstated_headroom_in,
        unstated_semantic_rules_in,
        unstated_surface_rules_in,
    )

    v1_5, v1_6 = parts["v1_5"], parts["v1_6"]
    unstated = {
        "constraints": unstated_constraints_in(v1_6),
        "semantic": unstated_semantic_rules_in(v1_6),
        "headroom": unstated_headroom_in(v1_6),
        "surface": unstated_surface_rules_in(v1_6),
    }
    if any(unstated.values()):
        raise ValidationError(f"prompt v1.6.0 leaves {unstated} unstated")
    stale = unstated_surface_rules_in(v1_5)
    if stale != list(SURFACE_RULE_IDS):
        raise ValidationError(
            f"the surface checks do not catch prompt v1.5.0, which states none of them: {stale}"
        )
    if _integers(PROMPT_MODULE):
        raise ValidationError("the prompt v1.6.0 module carries a number of its own")
    if re.search(r"\d", GENERATION_SURFACE_BLOCK_V1_6):
        raise ValidationError("the surface block carries a digit")
    rules = dict.fromkeys(SURFACE_RULE_IDS, True)
    return {
        "UNSTATED_GENERATION_CONSTRAINTS": 0,
        "UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES": 0,
        "UNSTATED_GENERATION_TARGETS": 0,
        "UNSTATED_GENERATION_SURFACE_RULES": 0,
        "SURFACE_RULES_STATED": rules,
        "SUPPORTED_ASSERTION_GROUNDING_SURFACED": rules["SUPPORTED_ASSERTION_GROUNDING"],
        "CANDIDATE_INTERVENTION_CLASS_SUPPORT_STATUS_SURFACED": rules[
            "CLASS_FIELD_IS_A_SUPPORTED_ASSERTION"
        ],
        "FUTURE_EVIDENCE_REQUEST_SURFACE_FORM_SURFACED": rules[
            "FUTURE_EVIDENCE_REQUEST_SURFACE_FORM"
        ],
        "IMPERATIVE_FUTURE_EVIDENCE_DISALLOWED_IN_GENERATION": rules[
            "NO_IMPERATIVE_FUTURE_EVIDENCE_REQUEST"
        ],
        "UNRESOLVED_REQUEST_WORDING_SURFACED": rules["UNRESOLVED_REQUEST_WORDING"],
        "CERTAINTY_AND_CONFIRMATION_WORDING_SURFACED": rules[
            "NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST"
        ],
        "PROMPT_V1_5_0_UNSTATED_SURFACE_RULES": stale,
        "discrimination_note": (
            "the same census finds every surface rule unstated in prompt v1.5.0, so its zero on "
            "v1.6.0 means something"
        ),
        "DIGITS_IN_SURFACE_BLOCK": 0,
        "HAND_MAINTAINED_NUMBERS_IN_PROMPT_MODULE": 0,
    }


# ============================================================================= conformance


def _gate_verdict(fx: Any, field: str, value: Any) -> Any:
    from sros_opportunity.second_opportunity_gate_v1_2 import build_trusted_context
    from sros_opportunity.second_opportunity_gate_v1_4 import (
        evaluate_second_opportunity_output_v1_4,
    )

    packet = fx.packet()
    return evaluate_second_opportunity_output_v1_4(
        fx.good_output(**{field: value}),
        packet,
        dict(fx.statements()),
        {**fx.EVIDENCE_TO_CLAIM, fx.EXTRA_ROW[0]: fx.EXTRA_ROW[1]},
        trusted_context=build_trusted_context(packet),
        source_metadata=fx.metadata(),
    )


def conformance(cases: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Sections 13, 17 and 18: the policy's forms against the frozen gate, which does not move."""
    from sros_opportunity.assertion_context import is_request_shaped
    from sros_opportunity.generation_surface_policy import (
        CANONICAL_REQUEST_HEADS,
        IMPERATIVE_CONTRASTS,
        UNRESOLVED_CONSTRUCTIONS,
    )

    before = gate_v1_4_digest()
    forms = [f"{h} {c} X" for h in CANONICAL_REQUEST_HEADS for c in UNRESOLVED_CONSTRUCTIONS]
    unread = [form for form in forms if not is_request_shaped(form)]
    if unread:
        raise ValidationError(f"the frozen gate does not read {unread} as requests")
    for wrong, right in IMPERATIVE_CONTRASTS:
        if is_request_shaped(wrong) or not is_request_shaped(right):
            raise ValidationError(
                f"the gate does not read {wrong!r} and {right!r} as the policy says"
            )
    instructions = [f"{verb} whether X" for verb in INSTRUCTION_VERBS]
    read = [text for text in instructions if is_request_shaped(text)]
    if read:
        raise ValidationError(f"the gate reads the instructions {read} as requests")

    fx = _module("fixtures_for_gate_99_conformance", FIXTURES)
    if not _gate_verdict(
        fx, "recommended_next_evidence", fx.good_output()["recommended_next_evidence"]
    ).persist:
        raise ValidationError("the fixture's own answer does not pass the frozen gate")
    rows: list[dict[str, Any]] = []
    for case in CONFORMANCE_CASES if cases is None else cases:
        decision = _gate_verdict(fx, case["field"], case["value"])
        reasons = list(decision.refusal_reasons)
        other = [r for r in reasons if not r.startswith(case["field"])]
        matched = case["reason"] is None or (
            bool(reasons) and all(case["reason"] in r for r in reasons)
        )
        if decision.persist is not case["persist"] or other or not matched:
            raise ValidationError(
                f"{case['case']}: the frozen gate judged it {decision.persist} with {reasons}, "
                f"not {case['persist']} on {case['field']}"
            )
        rows.append(
            {
                "case": case["case"],
                "field": case["field"],
                "expected_persist": case["persist"],
                "persist": decision.persist,
                "stage_6": "PASSED" if decision.persist else "FAILED",
                "refusals": len(reasons),
            }
        )
    after = gate_v1_4_digest()
    if before != after:
        raise ValidationError("PROMPT_SUCCESSOR_WOULD_MODIFY_FROZEN_SEMANTIC_GATE: it moved")
    return {
        "REQUEST_SHAPE_POLICY_SOURCE": "OPTION_A_VERSIONED_PROMPT_SIDE_GENERATION_SURFACE_POLICY",
        "request_shape_note": (
            "the request shape is decided by the frozen gate's public is_request_shaped over "
            "patterns the census classes as internal; the policy names three canonical heads and "
            "neutral constructions, imports no private pattern, and this gate proves every form it "
            "teaches against the frozen function and every instruction it forbids refused by it"
        ),
        "CANONICAL_FORMS_CHECKED": len(forms),
        "CANONICAL_FORMS_READ_AS_REQUESTS": len(forms) - len(unread),
        "INSTRUCTIONS_CHECKED": len(instructions) + len(IMPERATIVE_CONTRASTS),
        "INSTRUCTIONS_READ_AS_REQUESTS": 0,
        "CASES": rows,
        "CASES_AS_THE_POLICY_SAYS": len(rows),
        "GATE_V1_4_DIGEST_BEFORE": before,
        "GATE_V1_4_DIGEST_AFTER": after,
        "GATE_BEHAVIOR_CHANGED": False,
    }


# ============================================================================= exposure


def _names(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.ImportFrom):
            found.update(alias.name for alias in node.names)
    return found


def exposure(parts: Mapping[str, Any], v9_texts: Sequence[str]) -> dict[str, Any]:
    """Sections 5 and 12: no V9 sentence, no file read and no private gate pattern reachable."""
    from sros_opportunity.assertion_context import CERTAINTY_MARKERS
    from sros_opportunity.generation_surface_policy import CANONICAL_REQUEST_HEADS
    from sros_opportunity.guards import VALIDATION_WORDS
    from sros_opportunity.second_opportunity_prompt_v1_6 import GENERATION_SURFACE_BLOCK_V1_6

    system = str(parts["v1_6"].system_instructions)
    block = GENERATION_SURFACE_BLOCK_V1_6
    sources = {
        path.name: path.read_text(encoding="utf-8") for path in (POLICY_MODULE, PROMPT_MODULE)
    }
    for text in v9_texts:
        if text in system or any(text in source for source in sources.values()):
            raise ValidationError(
                "a sentence V9's answer carried is in the v1.6.0 prompt or its code"
            )
    shared = sorted(set().union(*(_shingles(t) for t in v9_texts)) & _shingles(block))
    if shared:
        raise ValidationError(f"the surface block shares word sequences with V9's answer: {shared}")
    forbidden_names = {
        "open",
        "read_text",
        "read_bytes",
        "load",
        "loads",
        "is_request_shaped",
        "CERTAINTY_MARKERS",
        "VALIDATION_WORDS",
    }
    for name, source in sources.items():
        tree = ast.parse(source)
        names = _names(tree)
        private = sorted(n for n in names if n.startswith("_REQUEST") or n == "_UNCERTAINTY_SHAPE")
        reads = sorted(names & forbidden_names)
        paths = [
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and re.search(r"docs/data|\.json\b|response-v|execution-record", n.value)
        ]
        if private or reads or paths:
            raise ValidationError(
                f"{name} reaches what prompt generation may not: {private + reads + paths}"
            )
    tokens = set(re.findall(r"[a-z]+", block.lower()))
    listed = sorted(tokens & (set(CERTAINTY_MARKERS) | set(VALIDATION_WORDS)))
    if listed:
        raise ValidationError(f"the surface block names members of a gate list: {listed}")
    quoted_heads = re.findall(r'"([A-Z][a-z]+ of) \.\.\."', block)
    if quoted_heads != list(CANONICAL_REQUEST_HEADS):
        raise ValidationError(f"the block teaches the heads {quoted_heads}, not the canonical ones")
    result = {
        "V9_SENTENCES_IN_PROMPT_OR_CODE": 0,
        "V9_SIX_WORD_SEQUENCES_IN_SURFACE_BLOCK": 0,
        "FILES_READ_BY_PROMPT_GENERATION": 0,
        "PRIVATE_GATE_PATTERNS_IMPORTED": 0,
        "GATE_LIST_MEMBERS_IN_SURFACE_BLOCK": 0,
        "QUOTED_REQUEST_HEADS": quoted_heads,
        "HISTORICAL_EXECUTION_NAMED_IN_SYSTEM_REGION": re.search(r"\bV[1-9]\b", system) is not None,
        "SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION": "Tenders Electronic Daily" in system,
        "SYSTEM_REGION_PACKET_INDEPENDENT": system == str(parts["synthetic"].system_instructions),
    }
    if (
        result["HISTORICAL_EXECUTION_NAMED_IN_SYSTEM_REGION"]
        or result["SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION"]
        or not result["SYSTEM_REGION_PACKET_INDEPENDENT"]
    ):
        raise ValidationError(f"the prompt exposes what it must not: {result}")
    return result


# ============================================================================= the record


def _untrusted_sha(parts: Any) -> str:
    return _sha(
        json.dumps([list(p) for p in parts.untrusted], ensure_ascii=False, separators=(",", ":"))
    )


def build_record() -> dict[str, Any]:
    from sros_opportunity.generation_surface_policy import (
        CANONICAL_REQUEST_HEADS,
        GENERATION_SURFACE_POLICY_VERSION,
        GENERATION_SURFACE_RENDERER_VERSION,
        IMPERATIVE_CONTRASTS,
        UNRESOLVED_CONSTRUCTIONS,
        class_only_supported_fields,
        request_fields,
        supported_assertion_fields,
    )
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        SECOND_OPPORTUNITY_PROMPT_ID,
    )
    from sros_opportunity.second_opportunity_prompt_v1_6 import (
        GENERATION_SURFACE_BLOCK_V1_6,
        PROMPT_V1_6_OUTPUT_SCHEMA,
        PROMPT_V1_6_OUTPUT_SCHEMA_VERSION,
        PROMPT_V1_6_SEMANTIC_GATE_VERSION,
        SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6,
        second_opportunity_prompt_hash_v1_6,
    )
    from sros_opportunity.second_opportunity_schema_v1_2 import output_schema_sha256

    history()
    gate = gate_v1_4_digest()
    v9, v9_texts = v9_block()
    parts = regions()
    v1_5, v1_6, snap = parts["v1_5"], parts["v1_6"], parts["snap"]
    system = str(v1_6.system_instructions)
    return {
        "$comment": (
            "Mission 1.84.23. The v1.6.0 prompt regions over the authenticated packet snapshot, "
            "frozen and hashed and never transmitted, with V9's refusals reproduced and classified. "
            "Prompt v1.5.0 and its record are not edited. CI gate 99 re-derives every field."
        ),
        "record_version": "second-opportunity-synthesis-prompt@1.6.0",
        "mission": "1.84.23",
        "recorded_by": MISSION,
        "HISTORY_UNCHANGED": history(),
        "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
        "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6,
        "PROCEDURE": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        "PROMPT_SHA256": second_opportunity_prompt_hash_v1_6(v1_6),
        "PREDECESSOR_PROMPT_VERSION": "1.5.0",
        "PREDECESSOR_PROMPT_SHA256": PROMPT_V1_5_SHA256,
        "PREDECESSOR_UNCHANGED": True,
        "SUBJECT": SUBJECT,
        "PACKET_ID": snap.packet.packet_id,
        "OUTPUT_SCHEMA_VERSION": PROMPT_V1_6_OUTPUT_SCHEMA_VERSION,
        "OUTPUT_SCHEMA_SHA256": output_schema_sha256(PROMPT_V1_6_OUTPUT_SCHEMA),
        "SEMANTIC_GATE_VERSION": PROMPT_V1_6_SEMANTIC_GATE_VERSION,
        "SEMANTIC_GATE_IMPLEMENTATION_SHA256": gate,
        "SEMANTIC_GATE_UNCHANGED": True,
        "GENERATION_SURFACE_POLICY": GENERATION_SURFACE_POLICY_VERSION,
        "GENERATION_SURFACE_RENDERER": GENERATION_SURFACE_RENDERER_VERSION,
        "GENERATION_SURFACE_BLOCK_SHA256": _sha(GENERATION_SURFACE_BLOCK_V1_6),
        "SUPPORTED_ASSERTION_FIELDS": supported_assertion_fields(),
        "CLASS_ONLY_SUPPORTED_FIELDS": class_only_supported_fields(),
        "FUTURE_EVIDENCE_REQUEST_FIELDS": request_fields(),
        "CANONICAL_REQUEST_HEADS": list(CANONICAL_REQUEST_HEADS),
        "UNRESOLVED_CONSTRUCTIONS": list(UNRESOLVED_CONSTRUCTIONS),
        "IMPERATIVE_CONTRASTS": [list(pair) for pair in IMPERATIVE_CONTRASTS],
        "V9_RECONFIRMATION": v9,
        "SYSTEM_INSTRUCTION": system,
        "SYSTEM_SHA256": _sha(system),
        "PREDECESSOR_SYSTEM_SHA256": _sha(str(v1_5.system_instructions)),
        "TRUSTED_CONTEXT_SHA256": _sha(str(v1_6.trusted_context)),
        "TASK_SHA256": _sha(str(v1_6.task)),
        "UNTRUSTED_SHA256": _untrusted_sha(v1_6),
        "UNTRUSTED_ITEMS": len(v1_6.untrusted),
        "DIFFERENTIAL": prompt_differential(parts),
        "CENSUS": prompt_checks(parts),
        "CONFORMANCE": conformance(),
        "EXPOSURE": exposure(parts, v9_texts),
        "FREEZE_FILES": {relative: file_sha(relative) for relative in FREEZE_FILES},
        "TED_REPRESENTATION_SHA256": REPRESENTATION_SHA256,
        "TED_REPRESENTATION_CHARACTERS": REPRESENTATION_CHARACTERS,
        "TED_REPRESENTATION_UNCHANGED": True,
        "SENT": False,
        "sent_note": (
            "This document records regions that were frozen and never transmitted. No approval names "
            "a packet that binds this prompt version, and 0 provider requests were made by the "
            "mission that wrote it"
        ),
        "accounting": dict(ZERO_ACCOUNTING),
    }


def validate() -> dict[str, Any]:
    built = build_record()
    if not PROMPT_RECORD.exists():
        raise ValidationError(f"{PROMPT_RECORD.name} does not exist; run --write")
    if _load(PROMPT_RECORD) != json.loads(json.dumps(built)):
        raise ValidationError(f"{PROMPT_RECORD.name} is not what the live code derives")
    return built


# ============================================================================= rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_prompt_v1_6.py from "
    "{source}. Do not edit by hand; re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def render(record: Mapping[str, Any]) -> str:
    v9 = record["V9_RECONFIRMATION"]
    diff = record["DIFFERENTIAL"]
    census = record["CENSUS"]
    conf = record["CONFORMANCE"]
    families = v9["FAMILIES"]
    lines = [
        HEADER.format(source=PROMPT_RECORD.name)
        + f"# Second-Opportunity synthesis prompt v{record['PROMPT_VERSION']}",
        "",
        f"Mission {record['mission']}. Prompt `{record['PROMPT_SHA256']}`, successor of v"
        f"{record['PREDECESSOR_PROMPT_VERSION']} `{record['PREDECESSOR_PROMPT_SHA256']}`, which is "
        f"not edited. Output schema `{record['OUTPUT_SCHEMA_VERSION']}`, judged by "
        f"`{record['SEMANTIC_GATE_VERSION']}` (implementation "
        f"`{record['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}`, unchanged). Generation-surface policy "
        f"`{record['GENERATION_SURFACE_POLICY']}`, block `{record['GENERATION_SURFACE_BLOCK_SHA256']}`.",
        "",
        "## V9, re-derived",
        "",
        f"{v9['EXECUTION_PACKET_ID']} `{v9['EXECUTION_PACKET_SHA256']}`: "
        f"{v9['PROVIDER_REQUESTS']} request, HTTP {v9['HTTP_STATUS']}, {v9['ELAPSED_SECONDS']} s, "
        f"`{v9['STOP_REASON']}`, {v9['USAGE']['input_tokens']} in / {v9['USAGE']['output_tokens']} "
        f"out / {v9['USAGE']['thinking_tokens']} thinking / {v9['USAGE']['total_tokens']} total, "
        f"cost {v9['ACTUAL_COST']}, {v9['ROOT_KEYS_RETURNED']} root keys, "
        f"{v9['UNKNOWN_ROOT_PROPERTIES_RETURNED']} unknown. Outcome `{v9['PRIMARY_OUTCOME']}`.",
        "",
        "| stage | verdict |",
        "| --- | --- |",
        *[f"| {stage} | {verdict} |" for stage, verdict in v9["VALIDATION_STAGES"].items()],
        "",
        f"Gate v1.4.0 reproduces all {v9['SEMANTIC_REFUSALS']} stage 6 refusals from the retained "
        "answer, and each belongs to one of two families:",
        "",
        "| field | disposition / shape | kind | family |",
        "| --- | --- | --- | --- |",
        *[
            f"| `{row['field']}` | {row['disposition']} / {row['shape']} | {row['kind']} | "
            f"{row['family']} |"
            for row in v9["REFUSALS"]
        ],
        "",
        *[
            f"- **{name}** ({block['refusals']}): {block['reading']}."
            for name, block in families.items()
        ],
        "",
        "The supported-assertion policy is not weakened, the request parser is not expanded, and V9 "
        "is not replayed as a pass candidate.",
        "",
        "## What v1.6.0 adds",
        "",
        f"{diff['SYSTEM_LINES_V1_5_0']} system lines in v1.5.0, {diff['SYSTEM_LINES_V1_6_0']} in "
        f"v1.6.0: {diff['SYSTEM_LINES_ADDED']} added, {diff['SYSTEM_LINES_REMOVED']} removed, "
        f"{diff['SYSTEM_LINES_MOVED']} moved. Byte-identical to v1.5.0: "
        + ", ".join(diff["REGIONS_BYTE_IDENTICAL_TO_V1_5_0"])
        + ", the base system instruction, the output-contract, semantic and headroom blocks. "
        f"PROMPT_V1_6_HAS_UNAPPROVED_DRIFT = {str(diff['PROMPT_V1_6_HAS_UNAPPROVED_DRIFT']).lower()}.",
        "",
        "## Census",
        "",
        *_code(
            [
                f"{k} = {v}"
                for k, v in census.items()
                if not isinstance(v, dict | list) and not k.endswith("_note")
            ]
        ),
        "## Conformance against the frozen gate",
        "",
        f"{conf['CANONICAL_FORMS_READ_AS_REQUESTS']} of {conf['CANONICAL_FORMS_CHECKED']} canonical "
        f"forms read as requests; {conf['INSTRUCTIONS_READ_AS_REQUESTS']} of "
        f"{conf['INSTRUCTIONS_CHECKED']} instructions. GATE_BEHAVIOR_CHANGED = "
        f"{str(conf['GATE_BEHAVIOR_CHANGED']).lower()}.",
        "",
        "| case | field | stage 6 |",
        "| --- | --- | --- |",
        *[f"| {row['case']} | `{row['field']}` | {row['stage_6']} |" for row in conf["CASES"]],
        "",
        f"TED representation `{record['TED_REPRESENTATION_SHA256']}` "
        f"({record['TED_REPRESENTATION_CHARACTERS']} characters), unchanged. Sent: "
        f"{str(record['SENT']).lower()}.",
        "",
        "## The generation-surface block",
        "",
        *_code(str(record["SYSTEM_INSTRUCTION"]).split("\n")[diff["SYSTEM_LINES_V1_5_0"] :]),
    ]
    return "\n".join(lines)


def _write_json(path: pathlib.Path, data: Mapping[str, Any]) -> None:
    path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            _write_json(PROMPT_RECORD, build_record())
        record = validate()
    except ValidationError as error:
        print(f"FAIL: {error}")
        return 1
    text = render(record)
    if args.write:
        PROMPT_RECORD_MD.write_bytes(text.encode("utf-8"))
    elif not PROMPT_RECORD_MD.exists() or PROMPT_RECORD_MD.read_text(encoding="utf-8") != text:
        print(f"FAIL: {PROMPT_RECORD_MD.name} is stale; run with --write")
        return 1
    print("ok       prompt v1.6.0 is v1.5.0 plus the surface block, and the frozen gate agrees")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
