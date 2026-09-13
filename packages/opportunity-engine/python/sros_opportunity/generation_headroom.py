"""Generation headroom: a target below each composed text's hard maximum, and what each field carries.

Mission 1.84.14. Execution V4 was refused by the v1.1.0 schema on two lengths the prompt stated in
words (`candidate_intervention_class` and `evidence_bound_reasoning_summary`). The operator kept the
schema, the semantic gate and the representation, and chose a GENERATION policy:

    GENERATION_HEADROOM_POLICY = TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH
    GENERATION_TARGET_RATIO    = 4/5

**The ratio is an operator decision, not a derivation.** It is not a schema bound, not a provider
guarantee, and it was not estimated from any answer: nothing in this module reads an execution record,
a response, or any file at all. Every target is computed from two inputs only, the live schema's hard
bound and the policy's ratio, by one function, with integer arithmetic:

    generation_target(max_length) = floor(max_length * 4 / 5)

**A target is guidance for writing, never validation.** The schema validator, the semantic gate and
the persistence model do not know targets exist. A text between its target and its hard maximum is
valid; only a text over the hard maximum is refused, exactly as before this module existed.

**Which bounds get a target.** Only a `maxLength` the output-constraint classification (Mission 1.84.8)
marks `composed_length`: text the model composes and whose length it controls while writing. A copied
identifier, a closed choice or a sentinel is classified otherwise and gets none. One field the
constraint classifier reads as composed, because its schema carries no pattern, is fixed by the
semantic census to a supplied identity copied exactly (`SUBJECT_IS_THE_PACKET_IDENTITY`); the census
rule is named in the policy, and its fields get no target either. **No target applies to a count of
elements**: `ARRAY_HEADROOM_POLICY = NONE`.

**What each field carries, once.** Two composed fields get a role, stated as what the field is for and
where the rest belongs: `candidate_intervention_class` names a class and only a class, and
`evidence_bound_reasoning_summary` synthesises rather than repeating the structured lists. Concision
never costs information: the block says so in words, and says a field may exceed its target, never its
hard maximum, to stay complete.
"""

from __future__ import annotations

import hashlib
import json
import re
import textwrap
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .output_constraints import constraint_inventory
from .semantic_generation_rules import SEMANTIC_RULE_CENSUS, SemanticGateRule

__all__ = [
    "GENERATION_HEADROOM_POLICY_VERSION",
    "GENERATION_HEADROOM_RENDERER_VERSION",
    "FIELD_ROLE_POLICY_VERSION",
    "GENERATION_HEADROOM_POLICY_NAME",
    "GENERATION_TARGET_RATIO",
    "ARRAY_HEADROOM_POLICY",
    "OPERATOR_DECISION_GENERATION_HEADROOM",
    "GenerationHeadroomPolicy",
    "FieldRole",
    "HeadroomRow",
    "GENERATION_HEADROOM_POLICY",
    "FIELD_ROLES",
    "generation_target",
    "headroom_table",
    "untargeted_bounds",
    "render_generation_headroom_block",
    "unstated_headroom",
    "headroom_policy_digest",
]

GENERATION_HEADROOM_POLICY_VERSION = "second-opportunity-generation-headroom-policy@1.0.0"
GENERATION_HEADROOM_RENDERER_VERSION = "generation-headroom-renderer@1.0.0"
FIELD_ROLE_POLICY_VERSION = "second-opportunity-field-role-policy@1.0.0"

GENERATION_HEADROOM_POLICY_NAME = "TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH"
#: The operator's ratio, held exactly. Never a float: 0.8 has no exact binary representation.
GENERATION_TARGET_RATIO = Fraction(4, 5)
ARRAY_HEADROOM_POLICY = "NONE"

#: The operator's decision in Mission 1.84.14, verbatim, carried as data.
OPERATOR_DECISION_GENERATION_HEADROOM: tuple[str, ...] = (
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_SEMANTIC_GATE_V1_3_0_UNCHANGED",
    "KEEP_TED_REPRESENTATION_UNCHANGED",
    "DO_NOT_RAISE_MAX_LENGTHS_FROM_V4",
    "DO_NOT_TRUNCATE_MODEL_OUTPUT",
    "DO_NOT_POST_PROCESS_MODEL_OUTPUT_TO_FIT",
    "ADD_SCHEMA_DERIVED_GENERATION_HEADROOM",
    "ADD_NON_REDUNDANT_FIELD_GUIDANCE",
    "GENERATION_HEADROOM_POLICY = TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH",
    "GENERATION_TARGET_RATIO = 0.80",
)

#: A token that looks like a field name. A role that names one must name a real field.
_FIELD_TOKEN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")


@dataclass(frozen=True)
class GenerationHeadroomPolicy:
    """The operator's generation policy, and the existing classifications it reads."""

    version: str
    name: str
    ratio: Fraction
    applies_to_keyword: str
    applies_to_rule: str
    identity_rules: tuple[str, ...]
    array_headroom: str

    def __post_init__(self) -> None:
        if not isinstance(self.ratio, Fraction):
            raise TypeError("the ratio is held as an exact Fraction, never as a float")
        if not 0 < self.ratio < 1:
            raise ValueError("a generation target lies strictly below its hard maximum")
        if self.applies_to_keyword != "maxLength":
            raise ValueError("headroom applies to string lengths only; element counts keep theirs")
        if self.array_headroom != ARRAY_HEADROOM_POLICY:
            raise ValueError("no target applies to a count of elements in this policy")

    @property
    def ratio_text(self) -> str:
        return f"{self.ratio.numerator}/{self.ratio.denominator}"


@dataclass(frozen=True)
class FieldRole:
    """What one composed field carries, and where the rest belongs. No digit, no invented field."""

    field: str
    intent: str
    lines: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.lines or not all(line.strip() for line in self.lines):
            raise ValueError(f"the role of {self.field} is empty")
        for line in self.lines:
            if re.search(r"\d", line):
                raise ValueError(
                    f"the role of {self.field} carries a digit, which only the schema may"
                )


@dataclass(frozen=True)
class HeadroomRow:
    """One composed text's hard maximum and its derived generation target."""

    path: str
    hard_maximum: int
    generation_target: int
    constraint_rule: str
    constraint_class: str
    target_source: str
    hard_bound_source: str

    @property
    def label(self) -> str:
        field, marker, rest = self.path.partition("[]")
        if not marker:
            return field
        child = rest.lstrip(".")
        return f"{child}, in each element of {field}" if child else f"each element of {field}"

    def to_json(self) -> dict[str, object]:
        return {
            "field": self.path,
            "hard_maximum": self.hard_maximum,
            "generation_target": self.generation_target,
            "constraint_classification": f"{self.constraint_rule} ({self.constraint_class})",
            "target_source": self.target_source,
            "hard_bound_source": self.hard_bound_source,
        }


GENERATION_HEADROOM_POLICY = GenerationHeadroomPolicy(
    version=GENERATION_HEADROOM_POLICY_VERSION,
    name=GENERATION_HEADROOM_POLICY_NAME,
    ratio=GENERATION_TARGET_RATIO,
    applies_to_keyword="maxLength",
    applies_to_rule="composed_length",
    identity_rules=("SUBJECT_IS_THE_PACKET_IDENTITY",),
    array_headroom=ARRAY_HEADROOM_POLICY,
)

#: The roles, stated as what each field is for. Written from the schema's field names and the existing
#: semantic policy; no answer was read to write them.
FIELD_ROLES: tuple[FieldRole, ...] = (
    FieldRole(
        field="candidate_intervention_class",
        intent="NAME_THE_CLASS_ONLY",
        lines=(
            "names the class of intervention, and only the class: a short category. It is not a "
            "business plan, a product description, a justification, a summary of the evidence, an "
            "account of the target actor or a list of features.",
            "The reasons belong in evidence_bound_reasoning_summary, and the actor in "
            "target_actor_if_supported.",
        ),
    ),
    FieldRole(
        field="evidence_bound_reasoning_summary",
        intent="COMPACT_SYNTHESIS_NOT_DUPLICATE_LEDGER",
        lines=(
            "a synthesis, not a ledger: what the evidence establishes, why the hypothesis remains "
            "exploratory, and the most important evidence boundary. It stays substantive.",
            "It does not repeat item by item what critical_uncertainties, "
            "commercial_claims_not_supported, recommended_next_evidence and "
            "statement_classifications already list, and it does not enumerate every Evidence and "
            "Claim id that supporting_evidence_ids and supporting_claim_ids carry; it may still "
            "name the Evidence a point rests on.",
        ),
    ),
)

#: What concision may never remove. Rendered verbatim; the gate checks each item is stated.
QUALITY_FLOOR: tuple[str, ...] = (
    "an uncertainty",
    "an unsupported claim",
    "a source's provenance",
    "a relevant limitation",
    "the difference between what is observed and what is unknown",
    "an Evidence reference the answer needs",
)

_WIDTH = 96


# ------------------------------------------------------------------------------ the one derivation


def generation_target(max_length: int, ratio: Fraction = GENERATION_TARGET_RATIO) -> int:
    """floor(max_length * ratio), in integer arithmetic, so no binary rounding can move a target."""
    if isinstance(max_length, bool) or not isinstance(max_length, int) or max_length < 1:
        raise ValueError(f"a hard maximum is a positive integer, not {max_length!r}")
    if not isinstance(ratio, Fraction) or not 0 < ratio < 1:
        raise ValueError("the ratio is an exact Fraction strictly between 0 and 1")
    return (max_length * ratio.numerator) // ratio.denominator


def _census(rules: tuple[SemanticGateRule, ...]) -> dict[str, SemanticGateRule]:
    return {rule.rule_id: rule for rule in rules}


def _identity_fields(
    policy: GenerationHeadroomPolicy, census: tuple[SemanticGateRule, ...]
) -> frozenset[str]:
    known = _census(census)
    fields: set[str] = set()
    for rule_id in policy.identity_rules:
        if rule_id not in known:
            raise ValueError(f"{rule_id} is not in the semantic census")
        fields.update(known[rule_id].fields)
    return frozenset(fields)


def headroom_table(
    schema: Mapping[str, Any],
    policy: GenerationHeadroomPolicy = GENERATION_HEADROOM_POLICY,
    census: tuple[SemanticGateRule, ...] = SEMANTIC_RULE_CENSUS,
) -> tuple[HeadroomRow, ...]:
    """Every composed text's target, in the schema's own order, from the live schema and the policy."""
    identity = _identity_fields(policy, census)
    rows: list[HeadroomRow] = []
    for constraint in constraint_inventory(schema):
        if constraint.keyword != policy.applies_to_keyword:
            continue
        if constraint.rule != policy.applies_to_rule:
            continue
        if constraint.path.partition("[]")[0].partition(".")[0] in identity:
            continue
        hard = int(constraint.value)
        rows.append(
            HeadroomRow(
                path=constraint.path,
                hard_maximum=hard,
                generation_target=generation_target(hard, policy.ratio),
                constraint_rule=constraint.rule,
                constraint_class=constraint.constraint_class,
                target_source=f"floor({hard} * {policy.ratio_text}) under {policy.name}",
                hard_bound_source=f"output schema {constraint.path} maxLength",
            )
        )
    return tuple(rows)


def untargeted_bounds(
    schema: Mapping[str, Any],
    policy: GenerationHeadroomPolicy = GENERATION_HEADROOM_POLICY,
    census: tuple[SemanticGateRule, ...] = SEMANTIC_RULE_CENSUS,
) -> tuple[dict[str, object], ...]:
    """Every length or count bound that gets no target, and why."""
    identity = _identity_fields(policy, census)
    out: list[dict[str, object]] = []
    for constraint in constraint_inventory(schema):
        if constraint.keyword not in ("maxLength", "maxItems"):
            continue
        field = constraint.path.partition("[]")[0].partition(".")[0]
        if constraint.keyword == "maxItems":
            reason = (
                f"ARRAY_HEADROOM_POLICY = {policy.array_headroom}: element counts keep their limit"
            )
        elif constraint.rule != policy.applies_to_rule:
            reason = f"{constraint.rule}: generation does not choose this length"
        elif field in identity:
            reason = "a supplied identity copied exactly, under " + ", ".join(policy.identity_rules)
        else:
            continue
        out.append(
            {
                "field": constraint.path,
                "keyword": constraint.keyword,
                "hard_bound": constraint.value,
                "constraint_rule": constraint.rule,
                "reason": reason,
            }
        )
    return tuple(out)


# ------------------------------------------------------------------------------ rendering


def _para(text: str, indent: str = "") -> list[str]:
    return textwrap.wrap(
        text,
        width=_WIDTH,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _row_line(row: HeadroomRow) -> str:
    return (
        f"  {row.label}: generation target {row.generation_target} characters; "
        f"hard maximum {row.hard_maximum} characters"
    )


def _check_roles(schema: Mapping[str, Any], roles: tuple[FieldRole, ...]) -> None:
    fields = set(schema.get("properties") or {})
    for role in roles:
        if role.field not in fields:
            raise ValueError(f"a role names {role.field!r}, which the schema does not carry")
        for line in role.lines:
            for token in _FIELD_TOKEN.findall(line):
                if token not in fields:
                    raise ValueError(f"the role of {role.field} names {token!r}, not a field")


def render_generation_headroom_block(
    schema: Mapping[str, Any],
    policy: GenerationHeadroomPolicy = GENERATION_HEADROOM_POLICY,
    roles: tuple[FieldRole, ...] = FIELD_ROLES,
    census: tuple[SemanticGateRule, ...] = SEMANTIC_RULE_CENSUS,
) -> str:
    """The generation-headroom block, deterministically, from the schema and the policy objects."""
    rows = headroom_table(schema, policy, census)
    if not rows:
        raise ValueError("the schema carries no composed text, so there is nothing to target")
    _check_roles(schema, roles)
    untargeted = sorted(
        {
            str(entry["field"]).partition("[]")[0]
            for entry in untargeted_bounds(schema, policy, census)
            if entry["keyword"] == "maxLength"
        }
    )
    out = [
        "GENERATION TARGETS: MARGIN BELOW THE HARD LIMITS.",
        "",
        *_para(
            "The hard maxima in the output contract above are what the validator enforces, and an "
            "answer over one is refused, never trimmed. Your own count of characters while writing "
            "is only approximate, so every text you compose has a generation target below its hard "
            f"maximum: {policy.ratio_text} of the hard maximum, rounded down. Aim for the target. A "
            "text longer than its target but within its hard maximum is still valid and is not "
            "refused for that; only a text longer than its hard maximum is refused. The target is "
            "guidance for writing, never a limit of the contract."
        ),
        "",
        *(_row_line(row) for row in rows),
        "",
        *_para(
            "No target applies to how many elements an array holds: element counts keep the exact "
            "limits stated above. No target applies to a value you copy ("
            + ", ".join(untargeted)
            + ") or choose from a closed list, because its length is not yours to compose."
        ),
        "",
        "WHAT EACH COMPOSED FIELD CARRIES, ONCE.",
        *_para(
            "Each field carries its own information once, and no field restates what another "
            "field already carries.",
            "  ",
        ),
    ]
    for role in roles:
        out.append(f"  {role.field}")
        for line in role.lines:
            out.extend(_para(line, "    "))
    out += [
        "",
        "CONCISION NEVER COSTS INFORMATION.",
        *_para(
            "Being concise never removes "
            + ", ".join(QUALITY_FLOOR[:-1])
            + f", or {QUALITY_FLOOR[-1]}; and it never makes the answer sound more confident than "
            "the evidence allows, or harder to audit. Where a field needs more than its target to "
            "stay complete and auditable, it may exceed the target, and it still stays within its "
            "hard maximum.",
            "  ",
        ),
        "",
        "BEFORE SUBMITTING THE ANSWER.",
        *_para(
            "Reread every text you composed for a bounded field, prefer the more concise wording, "
            "keep each within its generation target where you can, and never let one exceed its "
            "hard maximum. This reread happens inside the one answer you give: write no count, "
            "draft or working anywhere in it.",
            "  ",
        ),
    ]
    return "\n".join(out)


def unstated_headroom(
    system: str,
    schema: Mapping[str, Any],
    policy: GenerationHeadroomPolicy = GENERATION_HEADROOM_POLICY,
    census: tuple[SemanticGateRule, ...] = SEMANTIC_RULE_CENSUS,
) -> list[str]:
    """Every composed text whose target and hard maximum the system region does not state together."""
    lines = set(system.split("\n"))
    return [
        row.path for row in headroom_table(schema, policy, census) if _row_line(row) not in lines
    ]


def headroom_policy_digest(
    policy: GenerationHeadroomPolicy = GENERATION_HEADROOM_POLICY,
    roles: tuple[FieldRole, ...] = FIELD_ROLES,
) -> str:
    payload = json.dumps(
        {
            "version": policy.version,
            "name": policy.name,
            "ratio": policy.ratio_text,
            "applies_to_keyword": policy.applies_to_keyword,
            "applies_to_rule": policy.applies_to_rule,
            "identity_rules": list(policy.identity_rules),
            "array_headroom": policy.array_headroom,
            "field_role_policy": FIELD_ROLE_POLICY_VERSION,
            "roles": [[r.field, r.intent, list(r.lines)] for r in roles],
            "quality_floor": list(QUALITY_FLOOR),
            "renderer": GENERATION_HEADROOM_RENDERER_VERSION,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
