"""Generation-contract policy v1.0.0: what an answer asserts, what it only names, and how a class is written.

Mission 1.84.27, operator decisions D3 and D5. It is the successor of
`second-opportunity-generation-surface-policy@1.0.0` for prompt v1.7.0, and it changes two things:

* **D3, the class of intervention.** The surface policy told the model to name a more neutral class
  wherever a richer label needed an unsupplied concept, so every hypothesis had to carry a class. This
  policy states schema v1.3.0's absence instead: a class the cited statements do not establish is
  written exactly as the sentinel, and that is a complete answer. An established class is one short
  noun phrase whose words the cited claims' statements use; a dimension's name is not a class.
* **D5, assertion rather than presence.** The surface policy told the model that every substantive
  concept in an asserting field comes from the supplied material, with no word about where a concept
  the packet does not establish may appear at all; the gate refuses such a concept only where it is
  asserted. This policy states the gate's actual rule, that an unsupported concept is refused when
  asserted, and names the fields whose structure frames a concept as not supported, not known or still
  to be observed. It keeps one instruction stricter than the gate and says so: a denial belongs in those
  framed fields, not in the prose of an asserting field, so an answer never depends on how a bounded
  reader parses a denial. Validation and confirmation words stay out of asserting fields even denied,
  because the gate refuses them there by presence.

The request section is the surface policy's own, rendered by its own function. Every line carries the
rule ids it states and how each rule is enforced, so a prompt that drops one is found, and a rule the
gate does not enforce is never presented as one it does. The block carries no digit and names no
private pattern of the gate. **The surface policy is not touched**: prompt v1.6.0 keeps resolving
against the block it sent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .assertion_context import Disposition, Shape, SupportCategory
from .generation_surface_policy import (
    GENERATION_SURFACE_POLICY,
    NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST,
    NO_IMPERATIVE_REQUEST,
    REQUEST_SURFACE_FORM,
    SUPPORT_CHANNEL_WORDING,
    UNRESOLVED_REQUEST_WORDING,
    GenerationSurfacePolicy,
    _joined,
    _request_section,
    _Tagged,
    _wrap,
    class_only_supported_fields,
    supported_assertion_fields,
)
from .intervention_class_grounding import MAX_CLASS_WORDS
from .second_opportunity_gate_v1_2 import SECOND_OPPORTUNITY_FIELD_POLICY
from .second_opportunity_schema_v1_3 import INTERVENTION_CLASS_NOT_ESTABLISHED

__all__ = [
    "GENERATION_CONTRACT_POLICY_VERSION",
    "GENERATION_CONTRACT_RENDERER_VERSION",
    "GATE_ENFORCED",
    "INSTRUCTION_BEYOND_THE_GATE",
    "GUIDANCE_ONLY",
    "CONTRACT_RULES",
    "CONTRACT_RULE_IDS",
    "contract_tagged_lines",
    "contract_rule_lines",
    "render_generation_contract_block",
    "unstated_contract_rules",
]

GENERATION_CONTRACT_POLICY_VERSION = "second-opportunity-generation-contract-policy@1.0.0"
GENERATION_CONTRACT_RENDERER_VERSION = "generation-contract-renderer@1.0.0"

GATE_ENFORCED = "GATE_ENFORCED"
INSTRUCTION_BEYOND_THE_GATE = "INSTRUCTION_BEYOND_THE_GATE"
GUIDANCE_ONLY = "GUIDANCE_ONLY"


@dataclass(frozen=True)
class ContractRule:
    rule_id: str
    enforcement: str
    statement: str


#: Every rule the block states, and how it is enforced. The ids of the request section are the
#: surface policy's own, enforced as it records them.
CONTRACT_RULES: tuple[ContractRule, ...] = (
    ContractRule(
        "UNSUPPORTED_CONCEPT_REFUSED_WHEN_ASSERTED",
        GATE_ENFORCED,
        "a concept the packet does not establish is refused where the answer asserts it",
    ),
    ContractRule(
        "SUPPORTED_ASSERTION_GROUNDING",
        GATE_ENFORCED,
        "an asserting field asserts only what the supplied channels establish",
    ),
    ContractRule(
        "UNSUPPORTED_CONCEPTS_HAVE_FRAMED_FIELDS",
        GUIDANCE_ONLY,
        "the fields that frame a concept as not supported, not known or still to be observed",
    ),
    ContractRule(
        "DENIALS_BELONG_IN_THE_FRAMED_FIELDS",
        INSTRUCTION_BEYOND_THE_GATE,
        "an asserting field is kept to what the packet establishes, and a denial is written in a "
        "framed field; the gate admits some denials in prose, and the answer does not rely on it",
    ),
    ContractRule(
        "NO_VALIDATION_WORDS_IN_ASSERTING_FIELDS",
        GATE_ENFORCED,
        "validation and confirmation words are refused in an asserting field even when denied",
    ),
    ContractRule(
        "CLASS_FIELD_IS_A_SUPPORTED_ASSERTION",
        GATE_ENFORCED,
        "the class of intervention is asserted as supported",
    ),
    ContractRule(
        "CLASS_ABSENCE_IS_THE_SENTINEL",
        GATE_ENFORCED,
        "a class the cited statements do not establish is written exactly as the sentinel",
    ),
    ContractRule(
        "CLASS_WORDS_FROM_CITED_STATEMENTS",
        GATE_ENFORCED,
        "every word of an established class occurs in a statement of a cited claim",
    ),
    ContractRule(
        "CLASS_IS_ONE_SHORT_NOUN_PHRASE",
        GATE_ENFORCED,
        "a class is one short noun phrase in plain words",
    ),
    ContractRule(
        "DIMENSION_NAME_IS_NOT_A_CLASS",
        GATE_ENFORCED,
        "a dimension's name licenses no word of a class",
    ),
    ContractRule(
        "GUIDANCE_IS_NOT_A_GUARANTEE",
        GUIDANCE_ONLY,
        "the deterministic audit still reads every field as written",
    ),
    ContractRule(REQUEST_SURFACE_FORM, GATE_ENFORCED, "a request is a noun phrase naming evidence"),
    ContractRule(NO_IMPERATIVE_REQUEST, GATE_ENFORCED, "a request is never an instruction"),
    ContractRule(UNRESOLVED_REQUEST_WORDING, GUIDANCE_ONLY, "a request leaves its result open"),
    ContractRule(
        NO_CERTAINTY_OR_CONFIRMATION_IN_A_REQUEST,
        GATE_ENFORCED,
        "a request carries no wording of certainty or confirmation",
    ),
)
CONTRACT_RULE_IDS: tuple[str, ...] = tuple(rule.rule_id for rule in CONTRACT_RULES)

_NUMBER_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}


def _fields_with(disposition: Disposition, shape: Shape | None = None) -> list[str]:
    return [
        fc.field_name
        for fc in SECOND_OPPORTUNITY_FIELD_POLICY
        if fc.disposition is disposition and (shape is None or fc.shape is shape)
    ]


def _assertion_section(policy: GenerationSurfacePolicy) -> list[_Tagged]:
    channels = [SUPPORT_CHANNEL_WORDING[c] for c in SupportCategory]
    asserting = supported_assertion_fields(policy)
    not_supported = _fields_with(Disposition.EXPLICITLY_NOT_SUPPORTED)
    unknown = _fields_with(Disposition.UNKNOWN_REQUIRES_EVIDENCE)
    requests = _fields_with(Disposition.FUTURE_EVIDENCE_REQUEST)
    out: list[_Tagged] = [("WHAT THE ANSWER ASSERTS, AND WHAT IT ONLY NAMES.", ())]
    out += _wrap(
        f"{_joined(asserting)} are asserted as supported. What they assert comes from "
        f"{_joined(channels, 'or')}; general knowledge of the world is not support, however likely "
        "it is to be true.",
        "  ",
        ("SUPPORTED_ASSERTION_GROUNDING",),
    )
    out += _wrap(
        "A concept the packet does not establish is not forbidden from the answer: it is forbidden "
        "from being asserted. Where the answer asserts it, the audit refuses it.",
        "  ",
        ("UNSUPPORTED_CONCEPT_REFUSED_WHEN_ASSERTED",),
    )
    out += _wrap(
        "Such a concept has its own places, whose structure already says what it is: a claim not "
        f"supported in {_joined(not_supported)}; something not known in {_joined(unknown)}, or in "
        "a statement classified HYPOTHESIS_TO_VALIDATE or UNKNOWN_REQUIRES_EVIDENCE; what would "
        f"have to be observed in {_joined(requests)}.",
        "  ",
        ("UNSUPPORTED_CONCEPTS_HAVE_FRAMED_FIELDS",),
    )
    out += _wrap(
        "When the answer needs to say that the packet does not establish something, it says so in "
        "those places, not in the prose of a field that asserts. Keep the asserting fields to what "
        "the packet establishes, in its own terms. This is stricter than the audit, deliberately: "
        "the answer never depends on how a denial written in prose is read.",
        "  ",
        ("DENIALS_BELONG_IN_THE_FRAMED_FIELDS",),
    )
    out += _wrap(
        "Words of validation or confirmation appear in no asserting field, not even denied.",
        "  ",
        ("NO_VALIDATION_WORDS_IN_ASSERTING_FIELDS",),
    )
    return out


def _class_section(policy: GenerationSurfacePolicy) -> list[_Tagged]:
    (field,) = class_only_supported_fields(policy)
    sentinel = INTERVENTION_CLASS_NOT_ESTABLISHED
    limit = _NUMBER_WORDS[MAX_CLASS_WORDS]
    out: list[_Tagged] = [("THE CLASS OF INTERVENTION.", ())]
    out += _wrap(
        f"{field} is itself asserted as supported: naming only the class does not make its "
        "vocabulary free, and the word candidate does not make it a hypothesis.",
        "  ",
        ("CLASS_FIELD_IS_A_SUPPORTED_ASSERTION",),
    )
    out += _wrap(
        f"Where the statements of the claims the answer cites do not establish a class of "
        f"intervention, {field} is exactly {sentinel}, with nothing before or after it. That is a "
        "complete and correct value, and the hypothesis stays valid without a class. Never invent "
        "a class, and never soften one into a more neutral label to fill the field.",
        "  ",
        ("CLASS_ABSENCE_IS_THE_SENTINEL",),
    )
    out += _wrap(
        "An established class takes every word from the statements of the claims the answer cites "
        "in supporting_claim_ids, apart from articles, prepositions and conjunctions. A word that "
        "is only in a source's name, in a claim the answer does not cite, or in prior knowledge "
        "does not enter a class.",
        "  ",
        ("CLASS_WORDS_FROM_CITED_STATEMENTS",),
    )
    out += _wrap(
        f"A class is one short noun phrase of no more than {limit} words in plain letters: no "
        "number, no code, no punctuation, no clause, no denial.",
        "  ",
        ("CLASS_IS_ONE_SHORT_NOUN_PHRASE",),
    )
    out += _wrap(
        "A dimension's name classifies the evidence; it does not describe an intervention, and it "
        "licenses no word of a class.",
        "  ",
        ("DIMENSION_NAME_IS_NOT_A_CLASS",),
    )
    return out


def contract_tagged_lines(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> list[_Tagged]:
    """Every line of the contract block, each with the rules it states."""
    out: list[_Tagged] = [
        ("GENERATION CONTRACT: WHAT IS ASSERTED, WHAT IS NAMED, AND THE FORMS FIELDS TAKE.", ()),
        ("", ()),
    ]
    out += _assertion_section(policy)
    out.append(("", ()))
    out += _class_section(policy)
    out.append(("", ()))
    out += _request_section(policy)
    out.append(("", ()))
    out += _wrap(
        "This is guidance for writing. The deterministic audit still reads every field as written, "
        "after it is written, and refuses what it refuses; no wording here replaces it.",
        "",
        ("GUIDANCE_IS_NOT_A_GUARANTEE",),
    )
    return out


def contract_rule_lines(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> dict[str, tuple[str, ...]]:
    """Rule id -> the rendered lines that state it."""
    found: dict[str, list[str]] = {}
    for text, rules in contract_tagged_lines(policy):
        for rule in rules:
            found.setdefault(rule, []).append(text)
    return {rule: tuple(lines) for rule, lines in found.items()}


def render_generation_contract_block(
    policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY,
) -> str:
    """The contract block, deterministically, from the policy objects only."""
    lines = contract_tagged_lines(policy)
    stated = {rule for _, rules in lines for rule in rules}
    missing = [rule for rule in CONTRACT_RULE_IDS if rule not in stated]
    unknown = sorted(stated - set(CONTRACT_RULE_IDS) - {policy.promotion_rule.rule_id})
    if missing or unknown:
        raise ValueError(
            f"the contract block states no line for {missing}, or unknown rules {unknown}"
        )
    text = "\n".join(line for line, _ in lines)
    if re.search(r"\d", text):
        raise ValueError(
            "the contract block carries a digit. Every number the model reads comes from the schema "
            "or the packet"
        )
    return text


def unstated_contract_rules(
    system: str, policy: GenerationSurfacePolicy = GENERATION_SURFACE_POLICY
) -> list[str]:
    """Every contract rule whose rendered lines the system region does not carry, in order."""
    rendered = contract_rule_lines(policy)
    system_lines = set(system.split("\n"))
    return [
        rule
        for rule in CONTRACT_RULE_IDS
        if not rendered.get(rule) or not set(rendered[rule]) <= system_lines
    ]
