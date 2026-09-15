"""Generation-surface policy: the bounded forms gate v1.4.0 already reads, stated for the model.

Mission 1.84.23. Gate v1.4.0 reads each output field by the disposition its field policy gives it,
and two of those readings are easy to meet in substance and miss in form:

* a field whose disposition is SUPPORTED_ASSERTION is asserted, whatever its name says, so every
  substantive concept in it must come from what the packet supplies. The class of intervention is
  such a field: naming only the class does not make its vocabulary free;
* a field whose disposition is FUTURE_EVIDENCE_REQUEST keeps the REQUEST shape: its head names the
  evidence or observation that would have to be obtained. An instruction to go and look is not that
  shape, and it is read as the assertion it has become.

Prompt v1.5.0 states both rules as propositions. This policy states their SURFACE: which fields
assert, where their words may come from, and what a request for evidence looks like as a phrase. It
is generation guidance and nothing else:

* **the gate is unchanged, and nothing here reads or copies its patterns.** The request shape is
  decided by `is_request_shaped` over private patterns that the semantic census classes as internal
  (class D). This policy does not import them, does not publish them, and does not widen them. It
  names three canonical request heads that are ordinary English noun phrases, and CI proves each of
  them, and every example it renders, against the frozen public function and the frozen gate;
* **no answer was read to write it.** No model output, execution record or report is an input: the
  fields, dispositions and roles are the first-class policy objects, and the examples are synthetic;
* **no word list.** The certainty and confirmation rule is stated as the census states it, as a
  category, and the lists the gate consults stay internal.

Every rendered line carries the rule ids it states, so a prompt that drops one is found by CI.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass

from .assertion_context import Disposition, FieldContext, Shape, SupportCategory
from .generation_headroom import FIELD_ROLES, FieldRole
from .second_opportunity_gate_v1_2 import SECOND_OPPORTUNITY_FIELD_POLICY
from .semantic_generation_rules import GATE_ENFORCED, SemanticGateRule, census_by_id

__all__ = [
    "GENERATION_SURFACE_POLICY_VERSION",
    "GENERATION_SURFACE_RENDERER_VERSION",
    "CLASS_ONLY_ROLE",
    "CANONICAL_REQUEST_HEADS",
    "UNRESOLVED_CONSTRUCTIONS",
    "IMPERATIVE_CONTRASTS",
    "PROMOTION_RULE_ID",
    "SURFACE_RULE_IDS",
    "GenerationSurfacePolicy",
    "GENERATION_SURFACE_POLICY",
    "supported_assertion_fields",
    "class_only_supported_fields",
    "request_fields",
    "surface_tagged_lines",
    "surface_rule_lines",
    "render_generation_surface_block",
    "unstated_surface_rules",
]

GENERATION_SURFACE_POLICY_VERSION = "second-opportunity-generation-surface-policy@1.0.0"
GENERATION_SURFACE_RENDERER_VERSION = "generation-surface-renderer@1.0.0"

#: The field role, from the generation-headroom policy, whose field names a class and only a class.
CLASS_ONLY_ROLE = "NAME_THE_CLASS_ONLY"

#: The request heads the prompt teaches. Ordinary noun phrases naming the evidence itself; CI proves
#: each against the frozen gate. They are the forms taught, not the forms the gate accepts.
CANONICAL_REQUEST_HEADS: tuple[str, ...] = ("Evidence of", "Observation of", "Identification of")

#: Neutral constructions that leave the result open. Guidance where they fit, not a grammar.
UNRESOLVED_CONSTRUCTIONS: tuple[str, ...] = (
    "whether",
    "the existence of",
    "the extent of",
    "the identity of",
    "the frequency of",
    "the relationship between",
)

#: Synthetic contrasts, instruction against request, over a placeholder. No answer supplied them.
IMPERATIVE_CONTRASTS: tuple[tuple[str, str], ...] = (
    ("Investigate whether X", "Evidence of whether X"),
    ("Find suppliers associated with X", "Identification of suppliers associated with X"),
)

#: The census rule the certainty and confirmation sentence restates, by id.
PROMOTION_RULE_ID = "NOTHING_PROMOTED_TO_A_CONCLUSION"

SUPPORTED_ASSERTION_GROUNDING = "SUPPORTED_ASSERTION_GROUNDING"
CLASS_FIELD_IS_A_SUPPORTED_ASSERTION = "CLASS_FIELD_IS_A_SUPPORTED_ASSERTION"
REQUEST_SURFACE_FORM = "FUTURE_EVIDENCE_REQUEST_SURFACE_FORM"
NO_IMPERATIVE_REQUEST = "NO_IMPERATIVE_FUTURE_EVIDENCE_REQUEST"
UNRESOLVED_REQUEST_WORDING = "UNRESOLVED_REQUEST_WORDING"
NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST = "NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST"
SURFACE_RULE_IDS: tuple[str, ...] = (
    SUPPORTED_ASSERTION_GROUNDING,
    CLASS_FIELD_IS_A_SUPPORTED_ASSERTION,
    REQUEST_SURFACE_FORM,
    NO_IMPERATIVE_REQUEST,
    UNRESOLVED_REQUEST_WORDING,
    NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST,
)

#: Where a supported assertion's words may come from, keyed by the support universe's own channels,
#: so a channel nobody has worded is refused rather than rendered silently.
SUPPORT_CHANNEL_WORDING: dict[SupportCategory, str] = {
    SupportCategory.SOURCE_STATEMENTS: "the supplied source content statements",
    SupportCategory.PACKET_STRUCTURAL_FACTS: "the structural facts the task states about the packet",
    SupportCategory.TRUSTED_LIMITING_OR_DEFINITIONAL_CONTEXT: (
        "the trusted limiting or definitional context, for what it defines"
    ),
}


@dataclass(frozen=True)
class GenerationSurfacePolicy:
    """Every object the surface block is rendered from, and nothing else."""

    version: str
    field_policy: tuple[FieldContext, ...]
    field_roles: tuple[FieldRole, ...]
    class_only_role: str
    support_channels: tuple[SupportCategory, ...]
    request_heads: tuple[str, ...]
    unresolved_constructions: tuple[str, ...]
    imperative_contrasts: tuple[tuple[str, str], ...]
    promotion_rule: SemanticGateRule

    def __post_init__(self) -> None:
        if not self.request_heads or not self.unresolved_constructions:
            raise ValueError(
                "a surface policy names the request heads and constructions it teaches"
            )
        for head in self.request_heads:
            if not re.fullmatch(r"[A-Z][a-z]+ of", head):
                raise ValueError(f"{head!r}: a request head is one capitalised noun and 'of'")
        for wrong, right in self.imperative_contrasts:
            if not any(right.startswith(head) for head in self.request_heads):
                raise ValueError(f"{right!r}: the request side of a contrast opens with a head")
            if any(wrong.startswith(head) for head in self.request_heads):
                raise ValueError(f"{wrong!r}: the instruction side of a contrast is not a request")
        rule = self.promotion_rule
        if (
            rule.rule_class != "A"
            or rule.enforcement != GATE_ENFORCED
            or "recommended_next_evidence" not in rule.fields
        ):
            raise ValueError(
                f"{rule.rule_id}: the certainty and confirmation sentence restates a class-A rule "
                "the gate enforces on requests for evidence"
            )


GENERATION_SURFACE_POLICY = GenerationSurfacePolicy(
    version=GENERATION_SURFACE_POLICY_VERSION,
    field_policy=SECOND_OPPORTUNITY_FIELD_POLICY,
    field_roles=FIELD_ROLES,
    class_only_role=CLASS_ONLY_ROLE,
    support_channels=tuple(SupportCategory),
    request_heads=CANONICAL_REQUEST_HEADS,
    unresolved_constructions=UNRESOLVED_CONSTRUCTIONS,
    imperative_contrasts=IMPERATIVE_CONTRASTS,
    promotion_rule=census_by_id()[PROMOTION_RULE_ID],
)


# ============================================================================= derived fields


def supported_assertion_fields(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> list[str]:
    """Every field the field policy reads as a supported assertion, in the policy's own order."""
    return [
        fc.field_name
        for fc in policy.field_policy
        if fc.disposition is Disposition.SUPPORTED_ASSERTION
    ]


def class_only_supported_fields(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> list[str]:
    """Every field whose role names a class only and whose disposition is a supported assertion."""
    asserting = set(supported_assertion_fields(policy))
    fields = [
        role.field
        for role in policy.field_roles
        if role.intent == policy.class_only_role and role.field in asserting
    ]
    if not fields:
        raise ValueError(f"no supported-assertion field carries the role {policy.class_only_role}")
    return fields


def request_fields(policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY) -> list[str]:
    """Every field the field policy reads as a request for future evidence, in REQUEST shape."""
    fields = [
        fc.field_name
        for fc in policy.field_policy
        if fc.disposition is Disposition.FUTURE_EVIDENCE_REQUEST and fc.shape is Shape.REQUEST
    ]
    if not fields:
        raise ValueError("the field policy names no request for future evidence")
    return fields


# ============================================================================= rendering

_Tagged = tuple[str, tuple[str, ...]]
_WIDTH = 96


def _wrap(text: str, indent: str, rules: tuple[str, ...]) -> list[_Tagged]:
    lines = textwrap.wrap(
        text,
        width=_WIDTH,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return [(line, rules) for line in lines]


def _joined(items: Sequence[str], last: str = "and") -> str:
    words = [str(item) for item in items]
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + f" {last} " + words[-1]


def _quoted(items: Sequence[str]) -> list[str]:
    return [f'"{item} ..."' for item in items]


def _assertion_section(policy: GenerationSurfacePolicy) -> list[_Tagged]:
    grounding = (SUPPORTED_ASSERTION_GROUNDING,)
    channels = []
    for channel in policy.support_channels:
        if channel not in SUPPORT_CHANNEL_WORDING:
            raise ValueError(f"no wording for the support channel {channel.value}")
        channels.append(SUPPORT_CHANNEL_WORDING[channel])
    classes = class_only_supported_fields(policy)
    class_rule = (CLASS_FIELD_IS_A_SUPPORTED_ASSERTION,)
    out: list[_Tagged] = [("FIELDS THAT ASSERT, AND WHERE THEIR WORDS MAY COME FROM.", ())]
    out += _wrap(
        f"{_joined(supported_assertion_fields(policy))} are asserted as supported. In each of "
        "them, every substantive concept that describes the domain comes from "
        f"{_joined(channels, 'or')}.",
        "  ",
        grounding,
    )
    out += _wrap(
        "General knowledge of the world is not support, however likely it is to be true, and a "
        "concept is not supplied because it sounds plausible for this kind of evidence. A field is "
        "read by what its text does, never by the words in its name.",
        "  ",
        grounding,
    )
    for field in classes:
        out += _wrap(
            f"{field} names the class and only the class, and {policy.class_only_role} does not "
            "mean free vocabulary: the class it names is itself asserted as supported, and the "
            "word candidate does not make it a hypothesis.",
            "  ",
            class_rule,
        )
    out += _wrap(
        "Name the class in terms the supplied statements and the packet's structural facts "
        "already use, concisely, with no rationale, no account of an actor, no list of features "
        "and no summary of the evidence. Where a richer category label would need a concept they "
        "do not supply, name a more neutral class grounded in what they do supply. No concept "
        "enters the class because it is plausible for this kind of evidence; it enters only where "
        "the supplied material supports it.",
        "  ",
        class_rule,
    )
    return out


def _request_section(policy: GenerationSurfacePolicy) -> list[_Tagged]:
    fields = _joined(request_fields(policy))
    form = (REQUEST_SURFACE_FORM,)
    imperative = (NO_IMPERATIVE_REQUEST,)
    unresolved = (UNRESOLVED_REQUEST_WORDING,)
    promotion = (NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST, policy.promotion_rule.rule_id)
    out: list[_Tagged] = [("WHAT A REQUEST FOR EVIDENCE LOOKS LIKE.", ())]
    out += _wrap(
        f"Each item of {fields} is a noun phrase that names the missing evidence or observation, "
        f"and it opens with that noun: {_joined(_quoted(policy.request_heads), 'or')}. Keep each "
        "item to that one phrase, with no second clause that states something.",
        "  ",
        form,
    )
    out += _wrap(
        "An item never opens as a command or an instruction to a person. It names the evidence "
        "needed; it does not tell anybody what to do.",
        "  ",
        imperative,
    )
    for wrong, right in policy.imperative_contrasts:
        out += _wrap(f'not "{wrong}", but "{right}"', "    ", imperative)
    out += _wrap(
        "An item leaves open the result it asks for. Where it fits, it names what is to be "
        "observed with a neutral construction such as "
        f"{_joined(_quoted(policy.unresolved_constructions), 'or')}. It states no finding and "
        "presupposes none: it does not say what the evidence will show.",
        "  ",
        unresolved,
    )
    out += _wrap(
        "An item carries no wording of certainty, confirmation or validation, not even inside the "
        "question it names: it describes the information that would resolve the uncertainty, "
        "never a result it presupposes is already known.",
        "  ",
        promotion,
    )
    return out


def surface_tagged_lines(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> list[_Tagged]:
    """Every line of the surface block, each with the rules it states."""
    out: list[_Tagged] = [
        ("GENERATION SURFACE: THE FORMS THE AUDITED FIELDS TAKE.", ()),
        ("", ()),
        (
            "The rules above say what each field's text does. These lines say what that text looks",
            (),
        ),
        (
            "like. The gate that audits the answer is the same, and it reads the answer as written.",
            (),
        ),
        ("", ()),
    ]
    out += _assertion_section(policy)
    out.append(("", ()))
    out += _request_section(policy)
    return out


def surface_rule_lines(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> dict[str, tuple[str, ...]]:
    """Rule id -> the rendered lines that state it."""
    found: dict[str, list[str]] = {}
    for text, rules in surface_tagged_lines(policy):
        for rule in rules:
            found.setdefault(rule, []).append(text)
    return {rule: tuple(lines) for rule, lines in found.items()}


def render_generation_surface_block(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> str:
    """The surface block, deterministically, from the policy objects only."""
    lines = surface_tagged_lines(policy)
    stated = {rule for _, rules in lines for rule in rules}
    missing = [rule for rule in SURFACE_RULE_IDS if rule not in stated]
    if missing:
        raise ValueError(f"the surface block states no line for {missing}")
    text = "\n".join(line for line, _ in lines)
    if re.search(r"\d", text):
        raise ValueError(
            "the surface block carries a digit. Every number the model reads comes from the "
            "schema or the packet"
        )
    return text


def unstated_surface_rules(
    system: str, policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY
) -> list[str]:
    """Every surface rule whose rendered lines the system region does not carry, in order."""
    rendered = surface_rule_lines(policy)
    system_lines = set(system.split("\n"))
    return [
        rule
        for rule in SURFACE_RULE_IDS
        if not rendered.get(rule) or not set(rendered[rule]) <= system_lines
    ]
