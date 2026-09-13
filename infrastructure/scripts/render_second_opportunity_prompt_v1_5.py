"""Mission 1.84.17, CI gate 88. Prompt v1.5.0, and the output capacity under schema v1.2.0.

Prompt v1.5.0 is prompt v1.4.0 rebuilt over schema v1.2.0 for gate v1.4.0, and it may exist only
after gate v1.4.0 is frozen. This gate re-derives two records from the live code and the merged
artifacts:

    second-opportunity-synthesis-prompt-v6.json          the v1.5.0 regions over the snapshot
    second-opportunity-output-capacity-analysis-v3.json  schema v1.2.0: finite, its maximum, its
                                                         headroom rows and its persistence

It refuses: gate v1.4.0 not frozen, or its record not the one its freeze derives; a merged artifact
moved; the approved representation or prompt v1.4.0's digest moved; a v1.5.0 trusted context,
untrusted region or task other than v1.4.0's; a v1.5.0 system region that moves any line but the
reasoning summary's hard maximum and its generation target, or moves those to numbers other than
schema v1.2.0's and the policy's; a bound, rule or target left unstated; a check that would pass
prompt v1.4.0 against schema v1.2.0; the old bound anywhere in the v1.5.0 regions; a number of its
own in the prompt module; a maximum instance that does not validate, or numbers other than the
rebuilt ones; a headroom row other than the summary's moved; a persistence audit that moved; and a
token count or network request of any kind.

    uv run python infrastructure/scripts/render_second_opportunity_prompt_v1_5.py --check
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
from collections.abc import Mapping
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

PROMPT_RECORD = DATA / "second-opportunity-synthesis-prompt-v6.json"
PROMPT_RECORD_MD = DATA / "second-opportunity-synthesis-prompt-v6.md"
CAPACITY = DATA / "second-opportunity-output-capacity-analysis-v3.json"
CAPACITY_MD = DATA / "second-opportunity-output-capacity-analysis-v3.md"
CAPACITY_V2 = DATA / "second-opportunity-output-capacity-analysis-v2.json"
PROMPT_V5_RECORD = DATA / "second-opportunity-synthesis-prompt-v5.json"
TOKEN_MEASUREMENT = DATA / "second-opportunity-provider-token-measurement-v1.json"
ENVELOPE = DATA / "second-opportunity-execution-envelope-decision-v1.json"
PACKAGE = ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"
PROMPT_MODULE = PACKAGE / "second_opportunity_prompt_v1_5.py"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_81 = SCRIPTS / "render_second_opportunity_execution_packet_v4.py"
GATE_86 = SCRIPTS / "render_second_opportunity_reasoning_summary_contract.py"
GATE_87 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"
BOUNDED_CONTRACT = SCRIPTS / "render_second_opportunity_bounded_contract.py"

MISSION = "mission-1.84.17"
SUBJECT = "ted-eu:CPV-class:9261"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
PROMPT_V1_4_SHA256 = "960955f44a7ac0b95c995941aeac6ca772e196f4e6cb309b44ecfaa741bd6f46"
SUMMARY = "evidence_bound_reasoning_summary"

#: Every merged artifact this gate reads and may not rewrite, byte for byte as merged.
HISTORY_SHA256: dict[str, str] = {
    "docs/data/second-opportunity-synthesis-prompt-v5.json": (
        "9d0fd099913f2c2a93ca00f6816315023dc71f985eb91c985ee224f65c728af3"
    ),
    "docs/data/second-opportunity-output-capacity-analysis-v2.json": (
        "507b12d794a51732d3c9f719d189dbc66371866c9f728770bd80484968d83e1d"
    ),
    "docs/data/second-opportunity-provider-token-measurement-v1.json": (
        "83477ebafb4643c225ed450c7c20cc51a35f56008f8a2baea80d65748119ece0"
    ),
    "docs/data/second-opportunity-execution-envelope-decision-v1.json": (
        "eb085da1236cf1755b1d7fe49c74543509c1a59f4d12fb92d6c60aced3a2ed05"
    ),
    "docs/data/second-opportunity-generation-headroom-policy-v1.json": (
        "91a71efa10ab01788992f3e6080136ded22a5d7ace660a8fee1bae4aae8743ff"
    ),
    "docs/data/second-opportunity-reasoning-summary-contract-decision-v1.json": (
        "f8aa8b525b87cf561b7a8eb181d6fb68ffe50da10a62cd153af37137ecee0886"
    ),
    "docs/data/second-opportunity-reasoning-summary-contract-v1.json": (
        "b6a620fa64eb438140b4dcbb417e97aa6961870d0f334e7a91938e8188793516"
    ),
}

#: Section 16, the deployment's catalog re-read on 2026-09-13 by this mission. CI cannot re-read a
#: deployment, so this block is the recorded observation, and gate 86's audit is what CI re-derives.
OBSERVED_DATABASE: dict[str, object] = {
    "observed_on": "2026-09-13",
    "observed_by": MISSION,
    "server_version": "16.4",
    "column": "research.opportunity_hypothesis_revisions.reasoning_summary",
    "data_type": "text",
    "character_maximum_length": None,
    "atttypmod": -1,
    "is_nullable": "NO",
    "check_constraints_naming_the_column": [],
    "triggers_on_the_table": [],
    "existing_rows": 2,
    "existing_longest_value_characters": 1456,
}

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


def _bounds() -> tuple[int, int]:
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    )

    def bound(schema: Mapping[str, Any]) -> int:
        return int(schema["properties"][SUMMARY]["maxLength"])

    return bound(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1), bound(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
    )


# ============================================================================= preconditions


def history() -> dict[str, str]:
    for relative, digest in HISTORY_SHA256.items():
        if file_sha(relative) != digest:
            raise ValidationError(f"{relative} is not the file that was merged")
    return dict(HISTORY_SHA256)


def gate_v1_4_frozen() -> dict[str, Any]:
    """Section 18: prompt v1.5.0 exists only after gate v1.4.0 is frozen and its differential passes.

    Gate 87 does the heavy re-derivation in CI; this reads its record and its pins and requires them
    to agree with the live implementation digest.
    """
    gate = _module("gate_87_for_gate_88", GATE_87)
    record = _load(gate.RECORD)
    live = gate.implementation_sha256()
    if not (
        record.get("GATE_V1_4_FROZEN") is True
        and record.get("SEMANTIC_GATE_V1_4_IMPLEMENTATION_SHA256") == live
        and live == gate.FROZEN_IMPLEMENTATION_SHA256
        and gate.file_sha(gate.TEST_FILE) == gate.FROZEN_TEST_SHA256
        and record.get("NON_STRUCTURAL_SEMANTIC_DIVERGENCES") == 0
        and record.get("COMMON_DOMAIN_SEMANTIC_DIVERGENCES") == 0
        and record["MATRIX_PARITY"]["DIVERGENCES"] == 0
    ):
        raise ValidationError("SEMANTIC_GATE_V1_4_NOT_FROZEN: prompt v1.5.0 may not be built yet")
    return {
        "gate": record["GATE_VERSION"],
        "implementation_sha256": live,
        "test_sha256": gate.FROZEN_TEST_SHA256,
        "output_schema": record["OUTPUT_SCHEMA"]["version"],
        "output_schema_sha256": record["OUTPUT_SCHEMA"]["sha256"],
        "freeze_record": gate.RECORD.name,
    }


# ============================================================================= the regions


def regions() -> dict[str, Any]:
    from sros_opportunity.second_opportunity_prompt_v1_4 import (
        render_second_opportunity_prompt_v1_4,
        second_opportunity_prompt_hash_v1_4,
    )
    from sros_opportunity.second_opportunity_prompt_v1_5 import (
        render_second_opportunity_prompt_v1_5,
    )

    snap = _module("gate_81_for_gate_88", GATE_81).snapshot()
    if snap.representation_sha256 != REPRESENTATION_SHA256:
        raise ValidationError("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")
    arguments = (snap.packet, snap.statements, snap.pairs)
    v1_4 = render_second_opportunity_prompt_v1_4(*arguments, source_metadata=snap.metadata)
    recorded = _load(PROMPT_V5_RECORD)["PROMPT_SHA256"]
    if second_opportunity_prompt_hash_v1_4(v1_4) != PROMPT_V1_4_SHA256 or recorded != (
        PROMPT_V1_4_SHA256
    ):
        raise ValidationError("prompt v1.4.0 no longer renders to its frozen digest")
    fx = _module("fixtures_for_gate_88", FIXTURES)
    return {
        "snap": snap,
        "v1_4": v1_4,
        "v1_5": render_second_opportunity_prompt_v1_5(*arguments, source_metadata=snap.metadata),
        "synthetic": render_second_opportunity_prompt_v1_5(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
        ),
    }


def _block_of(line_index: int, lines: list[str]) -> str:
    """Which part of the system region a line belongs to, by the headings that open each part."""
    headings = {
        "THE OUTPUT CONTRACT IS BOUNDED": "output contract",
        "GENERATION TARGETS: MARGIN BELOW THE HARD LIMITS.": "generation headroom",
    }
    found = "base system instruction"
    for index in range(line_index + 1):
        for heading, block in headings.items():
            if lines[index].startswith(heading):
                found = block
    return found


def prompt_differential(parts: Mapping[str, Any]) -> dict[str, Any]:
    """Section 19: what v1.5.0 moves against v1.4.0, line by line, and what it must not."""
    from sros_opportunity.generation_headroom import generation_target
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_SYSTEM
    from sros_opportunity.second_opportunity_prompt_v1_3 import SEMANTIC_GENERATION_RULES_BLOCK_V1_3

    v1_4, v1_5 = parts["v1_4"], parts["v1_5"]
    for region in ("trusted_context", "untrusted", "task"):
        if getattr(v1_4, region) != getattr(v1_5, region):
            raise ValidationError(f"the {region} moved between v1.4.0 and v1.5.0")
    if "SOURCE NAMES" not in str(v1_5.trusted_context):
        raise ValidationError("the SOURCE NAMES section is no longer in the trusted context")
    old_system, new_system = str(v1_4.system_instructions), str(v1_5.system_instructions)
    if not new_system.startswith(SECOND_OPPORTUNITY_SYSTEM + "\n"):
        raise ValidationError("the base system instruction is not a byte-identical prefix")
    if ("\n" + SEMANTIC_GENERATION_RULES_BLOCK_V1_3 + "\n") not in new_system:
        raise ValidationError("the semantic-policy block is not carried byte for byte")
    a, b = old_system.split("\n"), new_system.split("\n")
    if len(a) != len(b):
        raise ValidationError("v1.5.0 adds or removes system lines; it may only move two")
    old, new = _bounds()
    allowed_old = {str(old), str(generation_target(old))}
    allowed_new = {str(new), str(generation_target(new))}
    moved: list[dict[str, Any]] = []
    for index, (before, after) in enumerate(zip(a, b, strict=True)):
        if before == after:
            continue
        if re.sub(r"\d+", "#", before) != re.sub(r"\d+", "#", after):
            raise ValidationError(f"line {index + 1} moved in words, not only in its number")
        if (
            not set(re.findall(r"\d+", before)) <= allowed_old
            or not set(re.findall(r"\d+", after)) <= allowed_new
        ):
            raise ValidationError(f"line {index + 1} moves numbers other than the summary's")
        moved.append(
            {"line": index + 1, "block": _block_of(index, b), "v1_4_0": before, "v1_5_0": after}
        )
    blocks = sorted(m["block"] for m in moved)
    if blocks != ["generation headroom", "output contract"]:
        raise ValidationError(f"v1.5.0 moves lines in {blocks}; it moves one per bounded block")
    headroom_line = next(m for m in moved if m["block"] == "generation headroom")
    if not headroom_line["v1_5_0"].lstrip().startswith(f"{SUMMARY}:"):
        raise ValidationError("the moved headroom row is not the reasoning summary's")
    return {
        "REGIONS_BYTE_IDENTICAL_TO_V1_4_0": ["trusted_context", "untrusted", "task"],
        "TED_UNTRUSTED_REGION_BYTE_IDENTICAL": True,
        "TRUSTED_CONTEXT_AND_SOURCE_NAMES_BYTE_IDENTICAL": True,
        "TASK_BYTE_IDENTICAL": True,
        "BASE_SYSTEM_INSTRUCTION_BYTE_IDENTICAL": True,
        "SEMANTIC_POLICY_BLOCK_BYTE_IDENTICAL": True,
        "SYSTEM_LINES": len(b),
        "SYSTEM_LINES_ADDED": 0,
        "SYSTEM_LINES_REMOVED": 0,
        "SYSTEM_LINES_MOVED": moved,
        "WHAT_MOVED": (
            "the reasoning summary's hard maximum in the output contract and its row in the "
            "generation targets, both read from schema v1.2.0; every field role, commercial "
            "boundary, source-metadata and OBSERVED instruction is carried byte for byte"
        ),
        "IDENTITY_MOVED": {
            "output_schema": [
                "second-opportunity-synthesis-output@1.1.0",
                "second-opportunity-synthesis-output@1.2.0",
            ],
            "semantic_gate": [
                "second-opportunity-output-gate@1.3.0",
                "second-opportunity-output-gate@1.4.0",
            ],
        },
    }


def _integers(path: pathlib.Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) is int]


def prompt_checks(parts: Mapping[str, Any]) -> dict[str, Any]:
    """Section 20: nothing unstated, the checks discriminate, and no bound is hand-maintained."""
    from sros_opportunity.second_opportunity_prompt_v1_5 import (
        unstated_constraints_in,
        unstated_headroom_in,
        unstated_semantic_rules_in,
    )

    v1_4, v1_5 = parts["v1_4"], parts["v1_5"]
    unstated = (
        unstated_constraints_in(v1_5)
        + unstated_semantic_rules_in(v1_5)
        + unstated_headroom_in(v1_5)
    )
    if unstated:
        raise ValidationError(f"prompt v1.5.0 leaves {unstated} unstated")
    stale_constraints = unstated_constraints_in(v1_4)
    stale_targets = unstated_headroom_in(v1_4)
    if stale_constraints != [f"{SUMMARY} maxLength"] or stale_targets != [SUMMARY]:
        raise ValidationError(
            f"the checks do not catch prompt v1.4.0 under schema v1.2.0: {stale_constraints}, "
            f"{stale_targets}"
        )
    old, _new = _bounds()
    from sros_opportunity.generation_headroom import generation_target

    stale = 0
    for region in ("system_instructions", "trusted_context", "task"):
        text = str(getattr(v1_5, region))
        stale += len(re.findall(rf"\b({old}|{generation_target(old)})\b", text))
    stale += sum(
        len(re.findall(rf"\b({old}|{generation_target(old)})\b", str(value)))
        for pair in v1_5.untrusted
        for value in pair
    )
    if stale:
        raise ValidationError(f"the old bound or target occurs {stale} times in the v1.5.0 regions")
    if _integers(PROMPT_MODULE):
        raise ValidationError("the prompt v1.5.0 module carries a number of its own")
    exposure = {
        "HISTORICAL_EXECUTION_NAMED_IN_SYSTEM_REGION": re.search(
            r"\bV[1-6]\b", str(v1_5.system_instructions)
        )
        is not None,
        "SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION": "Tenders Electronic Daily"
        in str(v1_5.system_instructions),
        "SYSTEM_REGION_PACKET_INDEPENDENT": v1_5.system_instructions
        == parts["synthetic"].system_instructions,
    }
    if exposure != {
        "HISTORICAL_EXECUTION_NAMED_IN_SYSTEM_REGION": False,
        "SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION": False,
        "SYSTEM_REGION_PACKET_INDEPENDENT": True,
    }:
        raise ValidationError(f"the prompt exposes what it must not: {exposure}")
    return {
        "UNSTATED_GENERATION_CONSTRAINTS": 0,
        "UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES": 0,
        "UNSTATED_GENERATION_TARGETS": 0,
        "PROMPT_V1_4_0_UNDER_SCHEMA_V1_2_0": {
            "unstated_constraints": stale_constraints,
            "unstated_targets": stale_targets,
            "note": "the same checks refuse the predecessor under the new schema, so they discriminate",
        },
        "OLD_BOUND_OR_TARGET_OCCURRENCES_IN_V1_5_0_REGIONS": 0,
        "HAND_MAINTAINED_BOUNDS_IN_PROMPT_MODULE": 0,
        "PROMPT_DRIFT": 0,
        "EXPOSURE": exposure,
    }


def _untrusted_sha(parts: Any) -> str:
    return _sha(
        json.dumps([list(p) for p in parts.untrusted], ensure_ascii=False, separators=(",", ":"))
    )


def prompt_record(parts: Mapping[str, Any]) -> dict[str, Any]:
    from sros_opportunity.generation_headroom import (
        FIELD_ROLE_POLICY_VERSION,
        GENERATION_HEADROOM_POLICY,
        GENERATION_HEADROOM_RENDERER_VERSION,
        headroom_policy_digest,
    )
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        SECOND_OPPORTUNITY_PROMPT_ID,
    )
    from sros_opportunity.second_opportunity_prompt_v1_5 import (
        GENERATION_HEADROOM_BLOCK_V1_5,
        OUTPUT_CONTRACT_BLOCK_V1_5,
        PROMPT_V1_5_OUTPUT_SCHEMA,
        PROMPT_V1_5_OUTPUT_SCHEMA_VERSION,
        PROMPT_V1_5_SEMANTIC_GATE_VERSION,
        SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5,
        second_opportunity_prompt_hash_v1_5,
    )
    from sros_opportunity.second_opportunity_schema_v1_2 import output_schema_sha256

    v1_4, v1_5, snap = parts["v1_4"], parts["v1_5"], parts["snap"]
    system = str(v1_5.system_instructions)
    return {
        "$comment": (
            "Mission 1.84.17. The v1.5.0 prompt regions over the authenticated packet snapshot, "
            "frozen and hashed and never transmitted. Prompt v1.4.0 and its record are not edited. "
            "CI gate 88 re-derives every field."
        ),
        "record_version": "second-opportunity-synthesis-prompt@1.5.0",
        "mission": "1.84.17",
        "recorded_by": MISSION,
        "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
        "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5,
        "PROCEDURE": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        "PROMPT_SHA256": second_opportunity_prompt_hash_v1_5(v1_5),
        "PREDECESSOR_PROMPT_VERSION": "1.4.0",
        "PREDECESSOR_PROMPT_SHA256": PROMPT_V1_4_SHA256,
        "PREDECESSOR_UNCHANGED": True,
        "SUBJECT": SUBJECT,
        "PACKET_ID": snap.packet.packet_id,
        "OUTPUT_SCHEMA_VERSION": PROMPT_V1_5_OUTPUT_SCHEMA_VERSION,
        "OUTPUT_SCHEMA_SHA256": output_schema_sha256(PROMPT_V1_5_OUTPUT_SCHEMA),
        "SEMANTIC_GATE": gate_v1_4_frozen(),
        "SEMANTIC_GATE_VERSION": PROMPT_V1_5_SEMANTIC_GATE_VERSION,
        "GENERATION_HEADROOM_RENDERER": GENERATION_HEADROOM_RENDERER_VERSION,
        "GENERATION_HEADROOM_POLICY": GENERATION_HEADROOM_POLICY.name,
        "GENERATION_TARGET_RATIO": GENERATION_HEADROOM_POLICY.ratio_text,
        "FIELD_ROLE_POLICY": FIELD_ROLE_POLICY_VERSION,
        "GENERATION_HEADROOM_POLICY_DIGEST": headroom_policy_digest(),
        "SYSTEM_INSTRUCTION": system,
        "SYSTEM_SHA256": _sha(system),
        "PREDECESSOR_SYSTEM_SHA256": _sha(str(v1_4.system_instructions)),
        "OUTPUT_CONTRACT_BLOCK_SHA256": _sha(OUTPUT_CONTRACT_BLOCK_V1_5),
        "HEADROOM_BLOCK_SHA256": _sha(GENERATION_HEADROOM_BLOCK_V1_5),
        "TRUSTED_CONTEXT_SHA256": _sha(str(v1_5.trusted_context)),
        "TASK_SHA256": _sha(str(v1_5.task)),
        "UNTRUSTED_SHA256": _untrusted_sha(v1_5),
        "UNTRUSTED_ITEMS": len(v1_5.untrusted),
        "DIFFERENTIAL": prompt_differential(parts),
        "CHECKS": prompt_checks(parts),
        "TED_REPRESENTATION_SHA256": REPRESENTATION_SHA256,
        "TED_REPRESENTATION_CHARACTERS": REPRESENTATION_CHARACTERS,
        "TED_REPRESENTATION_UNCHANGED": True,
        "SENT": False,
        "sent_note": (
            "This document records regions that were frozen and never transmitted. Execution packet "
            "V6 binds this prompt version, no approval names V6, and 0 provider requests were made "
            "by the mission that wrote it"
        ),
    }


# ============================================================================= capacity, headroom, persistence


def capacity_block() -> dict[str, Any]:
    """Sections 13 and 14: schema v1.2.0 is finite, and its maximum instance, rebuilt and revalidated."""
    from sros_opportunity.schema_validation import schema_violations
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    )
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
        output_schema_sha256,
    )

    contract = _module("bounded_contract_for_gate_88", BOUNDED_CONTRACT)
    new_schema, old_schema = (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    )
    if contract.unbounded_paths(new_schema):
        raise ValidationError(
            f"OUTPUT_SCHEMA_V1_2_NOT_FINITE: {contract.unbounded_paths(new_schema)}"
        )

    def measure(schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        instance = contract.maximum_instance(schema, contract.WORST_FILL)
        if schema_violations(instance, schema):
            raise ValidationError("a maximum instance does not validate through the real validator")
        text = json.dumps(instance, sort_keys=True)
        ascii_text = json.dumps(
            contract.maximum_instance(schema, contract.ASCII_FILL), sort_keys=True
        )
        return instance, {
            "MAX_INSTANCE_SCHEMA_VALID": True,
            "fill": "U+1F600",
            "MAX_VALID_OUTPUT_CHARACTERS": len(text),
            "MAX_VALID_OUTPUT_UTF8_BYTES": len(text.encode("utf-8")),
            "MAX_VALID_OUTPUT_SHA256": _sha(text),
            "ASCII_FILL_MAXIMUM_CHARACTERS": len(ascii_text),
        }

    new_instance, new_block = measure(new_schema)
    old_instance, old_block = measure(old_schema)
    held = _load(CAPACITY_V2)["MAXIMUM_VALID_INSTANCE"]
    for key in (
        "MAX_VALID_OUTPUT_CHARACTERS",
        "MAX_VALID_OUTPUT_UTF8_BYTES",
        "MAX_VALID_OUTPUT_SHA256",
    ):
        if held[key] != old_block[key]:
            raise ValidationError(f"v1.1.0's rebuilt {key} is not the one Mission 1.84.4 recorded")
    contributions = []
    for field in sorted(new_instance):
        before = len(json.dumps({field: old_instance[field]}, sort_keys=True)) - 2
        after = len(json.dumps({field: new_instance[field]}, sort_keys=True)) - 2
        contributions.append(
            {"field": field, "v1_1_0": before, "v1_2_0": after, "delta": after - before}
        )
    moved = [row["field"] for row in contributions if row["delta"]]
    if moved != [SUMMARY]:
        raise ValidationError(f"fields other than the summary change the maximum: {moved}")
    old, new = _bounds()
    delta = new_block["MAX_VALID_OUTPUT_CHARACTERS"] - old_block["MAX_VALID_OUTPUT_CHARACTERS"]
    per_character = len(json.dumps(contract.WORST_FILL))
    if delta != (new - old) * (per_character - 2):
        raise ValidationError(f"the maximum moved by {delta}, which the one bound does not explain")
    return {
        "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
        "OUTPUT_SCHEMA_SHA256": output_schema_sha256(new_schema),
        "PREDECESSOR_OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        "PREDECESSOR_OUTPUT_SCHEMA_SHA256": output_schema_sha256(old_schema),
        "FINITE_BOUND": True,
        "unbounded_path_count": 0,
        "walker": "Mission 1.84.4's walker, render_second_opportunity_bounded_contract.unbounded_paths",
        "MAXIMUM_VALID_INSTANCE": {
            **new_block,
            "method": (
                "Mission 1.84.4's builder over schema v1.2.0: every string at its maxLength in the "
                "non-BMP fill, every array at its maxItems, serialized with sorted keys and ASCII "
                "escaping, then validated through the repository's own validator"
            ),
        },
        "PREDECESSOR_MAXIMUM_VALID_INSTANCE": old_block,
        "DELTA_FROM_V1_1_0": {
            "characters": delta,
            "utf8_bytes": new_block["MAX_VALID_OUTPUT_UTF8_BYTES"]
            - old_block["MAX_VALID_OUTPUT_UTF8_BYTES"],
            "explained_by": (
                f"{SUMMARY}: {new - old} more characters of the fill, each serialized as "
                f"{per_character - 2} characters"
            ),
        },
        "FIELD_CONTRIBUTIONS": contributions,
    }


def reachability_block(capacity: Mapping[str, Any]) -> dict[str, Any]:
    """Section 15: the full domain is not reachable, by monotonicity, and no token was counted."""
    from sros_opportunity.schema_validation import schema_violations
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    )

    contract = _module("bounded_contract_for_gate_88_reach", BOUNDED_CONTRACT)
    old_maximum = contract.maximum_instance(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, contract.WORST_FILL
    )
    if schema_violations(old_maximum, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2):
        raise ValidationError("v1.1.0's maximum instance is not valid under v1.2.0")
    measurement = _load(TOKEN_MEASUREMENT)
    envelope = _load(ENVELOPE)
    estimate = measurement["MEASUREMENT"]["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"]
    counted = measurement["MEASUREMENT"]["MEASUREMENT_TEXT_CHARACTERS"]
    ceiling = envelope["MAX_OUTPUT_TOKENS_SELECTED"]
    if counted != capacity["PREDECESSOR_MAXIMUM_VALID_INSTANCE"]["MAX_VALID_OUTPUT_CHARACTERS"]:
        raise ValidationError("the counted text is not v1.1.0's maximum instance")
    if not estimate > ceiling:
        raise ValidationError("the recorded estimate no longer exceeds the envelope")
    return {
        "CONTRACT_FULL_DOMAIN_REACHABLE": False,
        "reasoning": [
            "schema v1.2.0 relaxes one maxLength of v1.1.0 and tightens nothing, so every answer "
            "v1.1.0 admits, its maximum instance included, v1.2.0 admits too (checked here through "
            "the validator)",
            f"Mission 1.84.5 counted that {counted}-character instance at {estimate} input tokens, a "
            f"provider-native estimate, against an execution envelope of {ceiling} output tokens",
            "so v1.2.0's domain holds an answer the envelope cannot carry, whatever v1.2.0's own "
            "maximum counts to, and no new count is needed to say so",
        ],
        "STATE": "CONTRACT_LARGER_THAN_EXECUTION_ENVELOPE",
        "MAX_OUTPUT_TOKENS": ceiling,
        "MAX_OUTPUT_TOKENS_SOURCE": ENVELOPE.name,
        "V1_1_0_MAXIMUM_TOKEN_ESTIMATE": estimate,
        "V1_2_0_MAXIMUM_TOKEN_ESTIMATE": "NOT_COUNTED",
        "EXACT_MAX_OUTPUT_TOKEN_COUNT": "NOT_ESTABLISHED",
        "INPUT_TO_OUTPUT_TOKENIZATION_EQUIVALENCE": "NOT_ESTABLISHED",
        "TOKEN_COUNT_REQUESTS": 0,
    }


def headroom_block() -> dict[str, Any]:
    """Section 17: the 4/5 policy over v1.2.0; the summary's row moves and no other."""
    from sros_opportunity.generation_headroom import (
        GENERATION_HEADROOM_POLICY,
        generation_target,
        headroom_policy_digest,
        headroom_table,
    )
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    )

    old_rows = {r.path: r for r in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)}
    new_rows = {r.path: r for r in headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)}
    if set(old_rows) != set(new_rows):
        raise ValidationError("the headroom rows differ in which texts they cover")
    moved = sorted(
        p
        for p in new_rows
        if (old_rows[p].hard_maximum, old_rows[p].generation_target)
        != (new_rows[p].hard_maximum, new_rows[p].generation_target)
    )
    if moved != [SUMMARY]:
        raise ValidationError(f"OTHER_HEADROOM_ROW_DRIFT: {moved}")
    row = new_rows[SUMMARY]
    if row.generation_target != generation_target(row.hard_maximum):
        raise ValidationError("the summary's target is not derived from its hard maximum")
    return {
        "GENERATION_HEADROOM_POLICY": GENERATION_HEADROOM_POLICY.name,
        "GENERATION_TARGET_RATIO": GENERATION_HEADROOM_POLICY.ratio_text,
        "GENERATION_HEADROOM_POLICY_DIGEST": headroom_policy_digest(),
        "ARRAY_HEADROOM_POLICY": GENERATION_HEADROOM_POLICY.array_headroom,
        "ROWS": len(new_rows),
        "REASONING_SUMMARY": {
            "v1_1_0": [old_rows[SUMMARY].hard_maximum, old_rows[SUMMARY].generation_target],
            "v1_2_0": [row.hard_maximum, row.generation_target],
            "target_source": row.target_source,
        },
        "OTHER_HEADROOM_ROW_DRIFT": 0,
        "HAND_MAINTAINED_TARGETS": 0,
    }


def persistence_block() -> dict[str, Any]:
    """Section 16: gate 86's persistence audit, re-derived now, and the catalog re-read today."""
    gate = _module("gate_86_for_gate_88", GATE_86)
    try:
        audit = gate.persistence_block()
    except gate.ValidationError as error:
        raise ValidationError(f"PERSISTENCE_COMPATIBILITY_CHANGED: {error}") from error
    previous = {k: v for k, v in gate.OBSERVED_DATABASE.items() if k not in ("observed_by", "note")}
    today = {k: v for k, v in OBSERVED_DATABASE.items() if k != "observed_by"}
    if previous != today:
        raise ValidationError("PERSISTENCE_COMPATIBILITY_CHANGED: the catalog moved since 1.84.16")
    _old, new = _bounds()
    return {
        "PERSISTENCE_COMPATIBILITY": audit["PERSISTENCE_COMPATIBILITY"],
        "DATABASE_STORAGE_COMPATIBILITY": audit["DATABASE_STORAGE_COMPATIBILITY"],
        "PERSISTENCE_MAXIMUM_FOR_REASONING_SUMMARY": audit[
            "PERSISTENCE_MAXIMUM_FOR_REASONING_SUMMARY"
        ],
        "model_field": audit["A_model"],
        "database_column": audit["C_database_column"],
        "OBSERVED_DATABASE": OBSERVED_DATABASE,
        "CATALOG_UNCHANGED_SINCE_1_84_16": True,
        "SCHEMA_V1_2_0_BOUND": new,
        "COMPATIBLE_WITH_THE_BOUND": True,
        "PERSISTENCE_COMPATIBILITY_CHANGED": False,
    }


# ============================================================================= the records


def build_records() -> tuple[dict[str, Any], dict[str, Any]]:
    history()
    parts = regions()
    prompt = prompt_record(parts)
    capacity = capacity_block()
    record = {
        "$comment": (
            "Mission 1.84.17. Schema v1.2.0 as the V6 execution contract: finite, its maximum "
            "rebuilt and revalidated, its reachability, its headroom rows and its persistence. CI "
            "gate 88 re-derives every field. No token was counted and nothing was sent."
        ),
        "record_version": "second-opportunity-output-capacity@3.0.0",
        "mission": "1.84.17",
        "recorded_by": MISSION,
        "HISTORY_UNCHANGED": history(),
        **capacity,
        "REACHABILITY": reachability_block(capacity),
        "HEADROOM": headroom_block(),
        "PERSISTENCE": persistence_block(),
        "PROMPT_V1_5_SHA256": prompt["PROMPT_SHA256"],
        "accounting": dict(ZERO_ACCOUNTING),
    }
    return prompt, record


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    prompt, capacity = build_records()
    for path, built in ((PROMPT_RECORD, prompt), (CAPACITY, capacity)):
        if not path.exists():
            raise ValidationError(f"{path.name} does not exist; run --write")
        if _load(path) != json.loads(json.dumps(built)):
            raise ValidationError(f"{path.name} is not what the live code derives")
    return prompt, capacity


# ============================================================================= rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_prompt_v1_5.py from "
    "{source}. Do not edit by hand; re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def render_prompt(record: Mapping[str, Any]) -> str:
    diff = record["DIFFERENTIAL"]
    lines = [
        HEADER.format(source=PROMPT_RECORD.name)
        + f"# Second-Opportunity synthesis prompt v{record['PROMPT_VERSION']}",
        "",
        f"Mission {record['mission']}. Prompt `{record['PROMPT_SHA256']}`, successor of v"
        f"{record['PREDECESSOR_PROMPT_VERSION']} `{record['PREDECESSOR_PROMPT_SHA256']}`, which is "
        "not edited. Output schema "
        f"`{record['OUTPUT_SCHEMA_VERSION']}` `{record['OUTPUT_SCHEMA_SHA256']}`, judged by "
        f"`{record['SEMANTIC_GATE_VERSION']}` (implementation "
        f"`{record['SEMANTIC_GATE']['implementation_sha256']}`, frozen).",
        "",
        "## What moved, line by line",
        "",
        *[
            f"- line {m['line']} ({m['block']}): `{m['v1_4_0'].strip()}` became "
            f"`{m['v1_5_0'].strip()}`"
            for m in diff["SYSTEM_LINES_MOVED"]
        ],
        "",
        f"{diff['SYSTEM_LINES']} system lines, {diff['SYSTEM_LINES_ADDED']} added, "
        f"{diff['SYSTEM_LINES_REMOVED']} removed. Byte-identical to v1.4.0: "
        + ", ".join(diff["REGIONS_BYTE_IDENTICAL_TO_V1_4_0"])
        + ", the base system instruction and the semantic-policy block.",
        "",
        "## Checks",
        "",
        *_code([f"{k} = {v}" for k, v in record["CHECKS"].items() if not isinstance(v, dict)]),
        f"TED representation `{record['TED_REPRESENTATION_SHA256']}` "
        f"({record['TED_REPRESENTATION_CHARACTERS']} characters), unchanged. Sent: "
        f"{str(record['SENT']).lower()}.",
        "",
        "## System instruction",
        "",
        *_code(str(record["SYSTEM_INSTRUCTION"]).split("\n")),
    ]
    return "\n".join(lines)


def render_capacity(record: Mapping[str, Any]) -> str:
    block = record["MAXIMUM_VALID_INSTANCE"]
    old = record["PREDECESSOR_MAXIMUM_VALID_INSTANCE"]
    reach = record["REACHABILITY"]
    head = record["HEADROOM"]
    persistence = record["PERSISTENCE"]
    lines = [
        HEADER.format(source=CAPACITY.name) + "# Output capacity under schema v1.2.0",
        "",
        f"Mission {record['mission']}. `{record['OUTPUT_SCHEMA_VERSION']}` "
        f"`{record['OUTPUT_SCHEMA_SHA256']}`: finite ({record['unbounded_path_count']} unbounded "
        "paths).",
        "",
        "| instance | characters | UTF-8 bytes | sha256 |",
        "| --- | --- | --- | --- |",
        f"| v1.1.0 maximum | {old['MAX_VALID_OUTPUT_CHARACTERS']} | "
        f"{old['MAX_VALID_OUTPUT_UTF8_BYTES']} | `{old['MAX_VALID_OUTPUT_SHA256']}` |",
        f"| v1.2.0 maximum | {block['MAX_VALID_OUTPUT_CHARACTERS']} | "
        f"{block['MAX_VALID_OUTPUT_UTF8_BYTES']} | `{block['MAX_VALID_OUTPUT_SHA256']}` |",
        "",
        f"Delta {record['DELTA_FROM_V1_1_0']['characters']} characters: "
        f"{record['DELTA_FROM_V1_1_0']['explained_by']}.",
        "",
        "## Reachability",
        "",
        *(f"- {line}" for line in reach["reasoning"]),
        "",
        f"CONTRACT_FULL_DOMAIN_REACHABLE = {str(reach['CONTRACT_FULL_DOMAIN_REACHABLE']).lower()}; "
        f"MAX_OUTPUT_TOKENS = {reach['MAX_OUTPUT_TOKENS']}; token-count requests "
        f"{reach['TOKEN_COUNT_REQUESTS']}.",
        "",
        "## Headroom",
        "",
        f"{head['GENERATION_HEADROOM_POLICY']} at {head['GENERATION_TARGET_RATIO']}: the reasoning "
        f"summary moves from {head['REASONING_SUMMARY']['v1_1_0']} to "
        f"{head['REASONING_SUMMARY']['v1_2_0']} (hard maximum, target); "
        f"OTHER_HEADROOM_ROW_DRIFT = {head['OTHER_HEADROOM_ROW_DRIFT']} over {head['ROWS']} rows.",
        "",
        "## Persistence",
        "",
        f"PERSISTENCE_COMPATIBILITY = {persistence['PERSISTENCE_COMPATIBILITY']}; the column is "
        f"`{persistence['database_column']['definition']}`, the catalog re-read on "
        f"{persistence['OBSERVED_DATABASE']['observed_on']} is the one Mission 1.84.16 read "
        f"(longest stored value {persistence['OBSERVED_DATABASE']['existing_longest_value_characters']} "
        "characters).",
        "",
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
            prompt, capacity = build_records()
            _write_json(PROMPT_RECORD, prompt)
            _write_json(CAPACITY, capacity)
        prompt, capacity = validate()
    except ValidationError as error:
        print(f"FAIL: {error}")
        return 1
    pages = ((PROMPT_RECORD_MD, render_prompt(prompt)), (CAPACITY_MD, render_capacity(capacity)))
    for path, text in pages:
        if args.write:
            path.write_bytes(text.encode("utf-8"))
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            print(f"FAIL: {path.name} is stale; run with --write")
            return 1
    print("ok       prompt v1.5.0 and the v1.2.0 capacity are what the live code derives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
