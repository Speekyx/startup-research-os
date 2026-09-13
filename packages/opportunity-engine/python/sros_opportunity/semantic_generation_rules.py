"""What gate v1.3.0 checks that generation can comply with, and the prompt block rendered from it.

Mission 1.84.12. Under gate v1.3.0, V3's one remaining refusal is true: an item classified OBSERVED
joined two alternatives and asserted a word the supplied statements carry only inside a source's
name. The gate is right, and prompt v1.2.0 told the model neither rule. A gate the model is not told
about refuses answers the prompt never asked it to avoid, so this module does two things.

**1. The census.** `SEMANTIC_RULE_CENSUS` lists every deterministic semantic rule in gate v1.3.0,
each with its component, the fields it reads, what it accepts and refuses, whether generation can
control it, whether prompt v1.2.0 states it, and one class:

    A  MUST_BE_EXPLICIT_IN_PROMPT
    B  STRUCTURAL_AND_ALREADY_EXPRESSED_BY_OUTPUT_CONTRACT
    C  VALIDATOR_ONLY_NOT_USEFUL_AS_GENERATION_PROSE
    D  INTERNAL_SAFETY_RULE_NOT_TO_BE_EXPOSED_AS_AN_EVASION_RECIPE

Every refusal site in the two frozen v1.3.0 modules is mapped to a rule in `REFUSAL_SITE_RULES`, and
CI proves the census against the frozen gate behaviourally: each enforced rule's refusal is produced by
a synthetic fixture, and every refusal the fixtures produce is claimed by exactly one rule.

**2. The renderer.** `render_semantic_generation_rules(policy)` renders the class-A rules prompt
v1.2.0 does not already state, from first-class policy objects: the field-context policy, the
classification dispositions, the forbidden concepts' own `never` texts, the operator's
evidence-boundary decision, the source-metadata label kinds and the disjunction policy. Where a rule's
only prior representation was a refusal branch in frozen code, its census entry carries the
instruction, and the census is that rule's first-class representation. **Nothing here parses source
code to render text, and nothing reads an answer**: not V3's, not any execution record.

**Class D is not rendered, and CI proves it.** The gated vocabulary lists, the inflection rules, the
denial and clause-scope reading, the request and uncertainty patterns and the label-matching order
are how the gate reads, and a prompt that published them would be teaching the model to phrase around
them. Mutating any of them leaves the rendered block byte-identical; mutating any class-A input moves
it.

**The prompt communicates; the gate decides.** Nothing here changes what gate v1.3.0 accepts, and
an answer that breaks a stated rule is refused, never repaired.
"""

from __future__ import annotations

import hashlib
import json
import re
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .assertion_audit_v1_3 import (
    ASSERTION_AUDIT_VERSION_V1_4,
    ASSERTION_GUARD_VERSION_V1_4,
    DISJUNCTION_POLICY_VERSION,
    DISJUNCTIVE_OBSERVED_STATEMENT,
    PERSISTENCE_GATE_VERSION_V1_3,
    SOURCE_METADATA_NOT_FACTUAL_SUPPORT,
)
from .assertion_context import Disposition, FieldContext, ForbiddenConcept, Shape
from .lexical_inflection import LEXICAL_INFLECTION_POLICY_VERSION
from .packet import OpportunityEvidencePacket
from .second_opportunity import (
    FORBIDDEN_TRANSFORMATIONS,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
)
from .second_opportunity_gate_v1_2 import (
    CLASSIFICATION_DISPOSITIONS,
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
    SECOND_OPPORTUNITY_FIELD_POLICY_VERSION,
    TRUSTED_CONTEXT_VERSION,
)
from .second_opportunity_gate_v1_3 import (
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
    SOURCE_METADATA_CONTEXT_VERSION,
    SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION,
)
from .support_origin import (
    SUPPORT_UNIVERSE_VERSION_V2,
    SourceMetadataContext,
    SourceMetadataLabel,
    label_spans,
)

__all__ = [
    "SEMANTIC_RULE_CENSUS_VERSION",
    "SEMANTIC_GENERATION_RULES_RENDERER_VERSION",
    "SOURCE_LABEL_BLOCK_RENDERER_VERSION",
    "SEMANTIC_GENERATION_POLICY_VERSION",
    "OPERATOR_DECISION_SEMANTIC_PROMPT_ALIGNMENT",
    "MUST_BE_EXPLICIT_IN_PROMPT",
    "STRUCTURAL_AND_ALREADY_EXPRESSED_BY_OUTPUT_CONTRACT",
    "VALIDATOR_ONLY_NOT_USEFUL_AS_GENERATION_PROSE",
    "INTERNAL_SAFETY_RULE_NOT_TO_BE_EXPOSED_AS_AN_EVASION_RECIPE",
    "RULE_CLASSES",
    "GATE_ENFORCED",
    "GATE_MECHANISM",
    "INSTRUCTION_BEYOND_THE_GATE",
    "SemanticGateRule",
    "SEMANTIC_RULE_CENSUS",
    "REFUSAL_SITE_RULES",
    "ObservedDisjunctionGenerationPolicy",
    "SemanticGenerationPolicy",
    "SEMANTIC_GENERATION_POLICY",
    "DISPOSITION_WORDING",
    "CLASSIFICATION_MEANING",
    "census_by_id",
    "tagged_lines",
    "semantic_rule_lines",
    "render_semantic_generation_rules",
    "source_labels_in_statements",
    "render_source_label_block",
    "unstated_semantic_rules",
    "policy_digest",
]

SEMANTIC_RULE_CENSUS_VERSION = "second-opportunity-semantic-rule-census@1.0.0"
SEMANTIC_GENERATION_RULES_RENDERER_VERSION = "semantic-generation-rules-renderer@1.0.0"
SOURCE_LABEL_BLOCK_RENDERER_VERSION = "source-label-block-renderer@1.0.0"
SEMANTIC_GENERATION_POLICY_VERSION = "second-opportunity-semantic-generation-policy@1.0.0"

#: §0 of Mission 1.84.12, as the operator decided it. Carried as data so a record can be checked
#: against it.
OPERATOR_DECISION_SEMANTIC_PROMPT_ALIGNMENT: tuple[str, ...] = (
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_SEMANTIC_GATE_V1_3_0_UNCHANGED",
    "DO_NOT_REPAIR_GATE_TO_RESCUE_V3",
    "DO_NOT_WHITELIST_V3",
    "DO_NOT_TREAT_SOURCE_METADATA_AS_FACTUAL_SUPPORT",
    "ALIGN_THE_PROMPT_WITH_GENERATION_RELEVANT_SEMANTIC_GATE_RULES",
    "OBSERVED_STATEMENTS_MUST_BE_ATOMIC_AND_DIRECTLY_SUPPORTED",
    "OBSERVED_DISJUNCTIONS_MUST_BE_SPLIT_OR_DOWNCLASSIFIED",
    "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false",
    "SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = true",
)

MUST_BE_EXPLICIT_IN_PROMPT = "MUST_BE_EXPLICIT_IN_PROMPT"
STRUCTURAL_AND_ALREADY_EXPRESSED_BY_OUTPUT_CONTRACT = (
    "STRUCTURAL_AND_ALREADY_EXPRESSED_BY_OUTPUT_CONTRACT"
)
VALIDATOR_ONLY_NOT_USEFUL_AS_GENERATION_PROSE = "VALIDATOR_ONLY_NOT_USEFUL_AS_GENERATION_PROSE"
INTERNAL_SAFETY_RULE_NOT_TO_BE_EXPOSED_AS_AN_EVASION_RECIPE = (
    "INTERNAL_SAFETY_RULE_NOT_TO_BE_EXPOSED_AS_AN_EVASION_RECIPE"
)
RULE_CLASSES: dict[str, str] = {
    "A": MUST_BE_EXPLICIT_IN_PROMPT,
    "B": STRUCTURAL_AND_ALREADY_EXPRESSED_BY_OUTPUT_CONTRACT,
    "C": VALIDATOR_ONLY_NOT_USEFUL_AS_GENERATION_PROSE,
    "D": INTERNAL_SAFETY_RULE_NOT_TO_BE_EXPOSED_AS_AN_EVASION_RECIPE,
}

#: The gate refuses an answer that breaks the rule.
GATE_ENFORCED = "GATE_ENFORCED"
#: How the gate reads an answer; it refuses nothing on its own.
GATE_MECHANISM = "GATE_MECHANISM"
#: Stated to the model under the operator's decision; the gate does not evaluate it.
INSTRUCTION_BEYOND_THE_GATE = "INSTRUCTION_BEYOND_THE_GATE"
_ENFORCEMENTS = (GATE_ENFORCED, GATE_MECHANISM, INSTRUCTION_BEYOND_THE_GATE)

_REGIONS = ("system", "trusted_context", "task")

_GATE = SECOND_OPPORTUNITY_GATE_VERSION_V1_3
_PERSISTENCE = PERSISTENCE_GATE_VERSION_V1_3
_AUDIT = ASSERTION_AUDIT_VERSION_V1_4
_GUARD = ASSERTION_GUARD_VERSION_V1_4
_FIELDS = SECOND_OPPORTUNITY_FIELD_POLICY_VERSION
_UNIVERSE = SUPPORT_UNIVERSE_VERSION_V2
_TRUSTED = TRUSTED_CONTEXT_VERSION
_META = SOURCE_METADATA_CONTEXT_VERSION
_INFLECTION = LEXICAL_INFLECTION_POLICY_VERSION
_DISJUNCTION = DISJUNCTION_POLICY_VERSION
_SCHEMA = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1

_TRANSFORMATION_NAMES: tuple[str, ...] = tuple(name for name, _, _ in FORBIDDEN_TRANSFORMATIONS)
_ADDED_CONCEPT_NAMES: tuple[str, ...] = tuple(
    c.name for c in FORBIDDEN_CONCEPTS_V1_2 if c.name not in _TRANSFORMATION_NAMES
)


@dataclass(frozen=True)
class SemanticGateRule:
    """One deterministic semantic rule of gate v1.3.0, and what the prompt owes it.

    `v1_2_evidence` is (region, exact text) where prompt v1.2.0 already states the rule, and CI
    checks the text is really there. `instruction` is the census's own wording for a class-A rule
    whose only prior representation was a refusal branch in frozen code; a rule derived from a
    first-class policy object is rendered from that object instead and carries no instruction.
    `refusal_signature` matches the refusal the frozen gate produces for this rule, and nothing
    else, so a fixture corpus can prove the census claims every refusal exactly once.
    """

    rule_id: str
    component: str
    fields: tuple[str, ...]
    disposition: str
    accepts: str
    refuses: str
    model_controllable: bool
    explicit_in_v1_2: bool
    rule_class: str
    enforcement: str
    canonical_policy_source: tuple[str, ...]
    rationale: str
    v1_2_evidence: tuple[str, str] | None = None
    instruction: str | None = None
    refusal_signature: str | None = None

    def __post_init__(self) -> None:
        if self.rule_class not in RULE_CLASSES:
            raise ValueError(f"{self.rule_id}: class {self.rule_class!r} is not one of A, B, C, D")
        if self.enforcement not in _ENFORCEMENTS:
            raise ValueError(f"{self.rule_id}: enforcement {self.enforcement!r}")
        if not self.rationale.strip() or not self.canonical_policy_source:
            raise ValueError(f"{self.rule_id}: a rule states why and where it lives")
        if self.explicit_in_v1_2 != (self.v1_2_evidence is not None):
            raise ValueError(f"{self.rule_id}: explicit in v1.2.0 exactly when evidence is quoted")
        if self.v1_2_evidence is not None and self.v1_2_evidence[0] not in _REGIONS:
            raise ValueError(f"{self.rule_id}: evidence region {self.v1_2_evidence[0]!r}")
        if self.instruction is not None:
            if self.rule_class != "A" or self.explicit_in_v1_2:
                raise ValueError(
                    f"{self.rule_id}: only a class-A rule v1.2.0 does not state carries wording"
                )
            if re.search(r"\d", self.instruction):
                raise ValueError(
                    f"{self.rule_id}: an instruction carries no digit; every number the model reads "
                    "comes from the schema or the packet"
                )
        if self.enforcement == GATE_ENFORCED and self.refusal_signature is None:
            raise ValueError(f"{self.rule_id}: an enforced rule names the refusal it produces")
        if self.enforcement != GATE_ENFORCED and self.refusal_signature is not None:
            raise ValueError(f"{self.rule_id}: only an enforced rule produces a refusal")

    @property
    def class_name(self) -> str:
        return RULE_CLASSES[self.rule_class]

    @property
    def must_be_explicit_in_v1_3(self) -> bool:
        return self.rule_class == "A"

    def to_json(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "component": self.component,
            "fields": list(self.fields),
            "disposition": self.disposition,
            "accepts": self.accepts,
            "refuses": self.refuses,
            "model_controllable": self.model_controllable,
            "explicit_in_v1_2": self.explicit_in_v1_2,
            "v1_2_evidence": list(self.v1_2_evidence) if self.v1_2_evidence else None,
            "must_be_explicit_in_v1_3": self.must_be_explicit_in_v1_3,
            "class": self.rule_class,
            "class_name": self.class_name,
            "enforcement": self.enforcement,
            "canonical_policy_source": list(self.canonical_policy_source),
            "rationale": self.rationale,
            "instruction": self.instruction,
            "refusal_signature": self.refusal_signature,
        }


def _names(names: Sequence[str]) -> str:
    return "|".join(re.escape(n) for n in names)


_R = SemanticGateRule
_ALL = ("*",)
_TEXT_FIELDS = (
    "target_actor_if_supported",
    "observed_need",
    "candidate_intervention_class",
    "hypothesis_statement",
    "independence_status",
    "reliability_status",
    "evidence_bound_reasoning_summary",
    "critical_uncertainties",
    "commercial_claims_supported",
    "commercial_claims_not_supported",
    "recommended_next_evidence",
    "statement_classifications",
)
_ASSERTING_FIELDS = (
    "target_actor_if_supported",
    "observed_need",
    "candidate_intervention_class",
    "hypothesis_statement",
    "independence_status",
    "reliability_status",
    "evidence_bound_reasoning_summary",
    "commercial_claims_supported",
    "statement_classifications",
)
_USE_ONLY_SUPPLIED = ("system", "USE ONLY THE SUPPLIED EVIDENCE.")

#: The census. Order is the order a reader meets the gate in: the schema and the v1.0.0 checks the
#: gate composes, the persistence gate's structural checks, the audit's findings, and the mechanisms
#: that decide how the audit reads.
SEMANTIC_RULE_CENSUS: tuple[SemanticGateRule, ...] = (
    # -- the gate's own composition ----------------------------------------------------------
    _R(
        "SCHEMA_V1_1_0_VALIDATION",
        _GATE,
        _ALL,
        "STRUCTURAL",
        "an answer the v1.1.0 schema validates",
        "a missing, extra or out-of-bound field, reported by the v1.1.0 validator",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity:SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1",),
        "the output-contract block v1.2.0 renders from the schema states every generation-relevant "
        "bound, so the schema needs no semantic prose",
        v1_2_evidence=(
            "system",
            "THE OUTPUT CONTRACT IS BOUNDED, AND AN ANSWER THAT EXCEEDS A BOUND IS REFUSED RATHER "
            "THAN TRIMMED.",
        ),
        refusal_signature=rf"^{re.escape(_SCHEMA)}: ",
    ),
    _R(
        "CONFIDENCE_IS_EXPLORATORY",
        _GATE,
        ("confidence_classification",),
        "STRUCTURAL_FACT",
        "EXPLORATORY",
        "any other value on a FORM_HYPOTHESIS answer",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity:CONFIDENCE_CLASSIFICATIONS",),
        "a closed choice of one, rendered by the contract and restated by v1.2.0",
        v1_2_evidence=("system", "CONFIDENCE. `confidence_classification` is EXPLORATORY and"),
        refusal_signature=r"^confidence_classification is ",
    ),
    _R(
        "NEXT_EVIDENCE_NOT_EMPTY",
        _GATE,
        ("recommended_next_evidence",),
        "FUTURE_EVIDENCE_REQUEST",
        "at least one item",
        "an empty list on a FORM_HYPOTHESIS answer",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_3:evaluate_second_opportunity_output_v1_3",),
        "the schema sets no minimum, and v1.2.0 says what the field names but not that it may not "
        "be empty",
        instruction="recommended_next_evidence has at least one item",
        refusal_signature=r"^recommended_next_evidence is empty",
    ),
    _R(
        "CLASSIFICATIONS_NOT_EMPTY",
        _GATE,
        ("statement_classifications",),
        "LABELLED",
        "at least one classified statement",
        "an empty list on a FORM_HYPOTHESIS answer",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_3:evaluate_second_opportunity_output_v1_3",),
        "the schema sets no minimum, and 'classify every substantive statement' does not say the "
        "list may not be empty",
        instruction="statement_classifications has at least one item",
        refusal_signature=r"^statement_classifications is empty",
    ),
    _R(
        "CLASSIFICATION_KINDS_CLOSED",
        _GATE,
        ("statement_classifications",),
        "LABELLED",
        "the three classification labels",
        "any other label",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_2:CLASSIFICATION_DISPOSITIONS",),
        "a closed choice the contract renders member by member",
        v1_2_evidence=(
            "system",
            "classification: exactly one of: OBSERVED_OR_EVIDENCE_SUPPORTED, "
            "HYPOTHESIS_TO_VALIDATE, UNKNOWN_REQUIRES_EVIDENCE",
        ),
        refusal_signature=r"^statement_classifications carries unknown kinds",
    ),
    _R(
        "SOMETHING_REMAINS_UNKNOWN",
        _GATE,
        ("statement_classifications",),
        "LABELLED",
        "at least one HYPOTHESIS_TO_VALIDATE or UNKNOWN_REQUIRES_EVIDENCE item",
        "a list in which every item is classified OBSERVED_OR_EVIDENCE_SUPPORTED",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_3:evaluate_second_opportunity_output_v1_3",),
        "v1.2.0 defines the three classifications and never says one of the other two is required",
        instruction=(
            "at least one item of statement_classifications is HYPOTHESIS_TO_VALIDATE or "
            "UNKNOWN_REQUIRES_EVIDENCE: a packet this narrow always leaves something to test or "
            "something unknown"
        ),
        refusal_signature=r"^every statement is classified as observed",
    ),
    # -- the persistence gate's structural checks ---------------------------------------------
    _R(
        "INSUFFICIENT_EVIDENCE_IS_AN_OUTCOME",
        _PERSISTENCE,
        ("decision",),
        "STRUCTURAL_FACT",
        "INSUFFICIENT_EVIDENCE, recorded as a correct outcome that creates no Opportunity",
        "nothing: it ends the gate with no hypothesis formed",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "v1.2.0's DECIDE paragraph states both answers and prefers the refusal to a hypothesis "
        "that needs an unsupplied fact",
        v1_2_evidence=(
            "system",
            "DECIDE. If the packet supports a narrow hypothesis, answer FORM_HYPOTHESIS.",
        ),
        refusal_signature=r"^the model answered INSUFFICIENT_EVIDENCE",
    ),
    _R(
        "DECISION_IS_ONE_OF_TWO",
        _PERSISTENCE,
        ("decision",),
        "STRUCTURAL_FACT",
        "FORM_HYPOTHESIS or INSUFFICIENT_EVIDENCE",
        "any other value",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity:SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1",),
        "a closed choice the contract renders",
        v1_2_evidence=("system", "exactly one of: FORM_HYPOTHESIS, INSUFFICIENT_EVIDENCE"),
        refusal_signature=r"^decision .* is not one of the two permitted values",
    ),
    _R(
        "EVERY_SOURCE_DECLARES_ITS_NAMES",
        _PERSISTENCE,
        _ALL,
        "STRUCTURAL",
        "a packet whose every source has registry labels in the metadata channel",
        "a packet source the caller declared no names for",
        False,
        False,
        "C",
        GATE_ENFORCED,
        ("sros_opportunity.support_origin:TypedSupportUniverse.undeclared_sources",),
        "the caller builds the metadata channel from the registry; no answer can satisfy or "
        "break it",
        refusal_signature=r"^no source metadata is declared for",
    ),
    _R(
        "SUBJECT_IS_THE_PACKET_IDENTITY",
        _PERSISTENCE,
        ("subject",),
        "STRUCTURAL_FACT",
        "the packet's subject label, exactly",
        "any other subject",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "the task prints the SUBJECT and never says the field must carry it unchanged",
        instruction="subject is the SUBJECT the task names, copied exactly",
        refusal_signature=r"^subject is ",
    ),
    _R(
        "CITED_EVIDENCE_IN_PACKET",
        _PERSISTENCE,
        ("supporting_evidence_ids",),
        "STRUCTURAL_FACT",
        "Evidence ids the packet supplied",
        "an Evidence id the packet does not carry",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity:OUTPUT_CONSTRAINT_NOTES_V1_2",),
        "the contract's own note says to copy the supplied ids verbatim",
        v1_2_evidence=(
            "system",
            "the ids supplied to you, copied verbatim. No prose, no description, no partial id.",
        ),
        refusal_signature=r"^cited Evidence ids not in the packet",
    ),
    _R(
        "CITED_CLAIMS_IN_PACKET",
        _PERSISTENCE,
        ("supporting_claim_ids",),
        "STRUCTURAL_FACT",
        "Claim ids the packet supplied",
        "a Claim id the packet does not carry",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity:OUTPUT_CONSTRAINT_NOTES_V1_2",),
        "the contract's own note says to copy the supplied ids verbatim",
        v1_2_evidence=(
            "system",
            "the ids supplied to you, copied verbatim. No prose, no description, no partial id.",
        ),
        refusal_signature=r"^cited Claim ids not in the packet",
    ),
    _R(
        "AT_LEAST_ONE_EVIDENCE_CITED",
        _PERSISTENCE,
        ("supporting_evidence_ids",),
        "STRUCTURAL_FACT",
        "at least one cited Evidence id",
        "no Evidence id cited",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "the schema sets no minimum, and v1.2.0 says which ids may be cited but not that one must be",
        instruction="supporting_evidence_ids cites at least one Evidence id",
        refusal_signature=r"^no supporting Evidence id was cited",
    ),
    _R(
        "AT_LEAST_ONE_CLAIM_CITED",
        _PERSISTENCE,
        ("supporting_claim_ids",),
        "STRUCTURAL_FACT",
        "at least one cited Claim id",
        "no Claim id cited",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "the schema sets no minimum, and v1.2.0 says which ids may be cited but not that one must be",
        instruction="supporting_claim_ids cites at least one Claim id",
        refusal_signature=r"^no supporting Claim id was cited",
    ),
    _R(
        "EVIDENCE_CITED_WITH_ITS_CLAIM",
        _PERSISTENCE,
        ("supporting_evidence_ids", "supporting_claim_ids"),
        "STRUCTURAL_FACT",
        "every cited Evidence id together with the Claim id it is labelled with",
        "an Evidence id cited without its Claim",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "Evidence is claim-relative; the task labels each pair and never says the pair travels "
        "together",
        instruction=(
            "every Evidence id in supporting_evidence_ids has the Claim id it is labelled with in "
            "supporting_claim_ids"
        ),
        refusal_signature=r"^Evidence \S+ was cited without its Claim",
    ),
    _R(
        "SOURCE_FAMILIES_FROM_PACKET",
        _PERSISTENCE,
        ("source_families",),
        "STRUCTURAL_FACT",
        "family names the packet supplied",
        "a family the packet does not carry",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity:OUTPUT_CONSTRAINT_NOTES_V1_2",),
        "the contract's own note says to copy the supplied family names verbatim",
        v1_2_evidence=(
            "system",
            "the family names supplied to you as a packet fact, copied verbatim.",
        ),
        refusal_signature=r"^source families the packet does not carry",
    ),
    _R(
        "SUPPORTED_DIMENSIONS_FROM_PACKET",
        _PERSISTENCE,
        ("supported_dimensions",),
        "STRUCTURAL_FACT",
        "dimensions the packet carries",
        "a dimension claimed as supported that the packet does not carry",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_context:PacketStructuralFacts",),
        "v1.2.0 says a dimension without evidence is unsupported, and the task lists the supported "
        "ones",
        v1_2_evidence=("system", "A dimension you were not given evidence for is UNSUPPORTED"),
        refusal_signature=r"^dimensions claimed as supported that this packet does not carry",
    ),
    _R(
        "SUPPORTED_AND_UNSUPPORTED_DISJOINT",
        _PERSISTENCE,
        ("supported_dimensions", "unsupported_dimensions"),
        "STRUCTURAL_FACT",
        "two disjoint lists",
        "a dimension listed as both supported and unsupported",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "nothing in v1.2.0 says the two lists may not share a name",
        instruction=(
            "no dimension appears both in supported_dimensions and in unsupported_dimensions"
        ),
        refusal_signature=r"^dimensions reported both supported and unsupported",
    ),
    _R(
        "MANDATORY_UNSUPPORTED_REPORTED",
        _PERSISTENCE,
        ("unsupported_dimensions",),
        "EXPLICITLY_NOT_SUPPORTED",
        "every mandatory dimension the packet does not carry, listed as unsupported",
        "a mandatory dimension left unmentioned",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.synthesis:MANDATORY_UNSUPPORTED_REPORT",),
        "the task names the dimensions that must be reported and marked unsupported",
        v1_2_evidence=(
            "task",
            "dimensions you MUST report on and mark unsupported unless a supplied",
        ),
        refusal_signature=r"^§6 requires an explicit unsupported report",
    ),
    _R(
        "INDEPENDENCE_RECORDS_UNKNOWN",
        _PERSISTENCE,
        ("independence_status",),
        "STRUCTURAL_FACT",
        "a restatement recording UNKNOWN",
        "a status without UNKNOWN, or one calling the sources independent",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "v1.2.0 says to repeat the packet's independence fact as given and never to call source "
        "families independent sources",
        v1_2_evidence=(
            "system",
            "INDEPENDENCE AND RELIABILITY are supplied to you as facts about the packet.",
        ),
        refusal_signature=r"^independence_status (?:does not record UNKNOWN|contains )",
    ),
    _R(
        "RELIABILITY_RESTATES_SCORABILITY",
        _PERSISTENCE,
        ("reliability_status",),
        "STRUCTURAL_FACT",
        "a restatement of the packet's scorability in the task's own terms",
        "a status that drops the scorability the packet has",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "v1.2.0 says to repeat the reliability fact as given, and the task gives it",
        v1_2_evidence=("system", "Repeat them as given."),
        refusal_signature=(
            r"^(?:no row in this packet is scoring-eligible and reliability_status|"
            r"\d+ of \d+ rows are scoring-eligible and reliability_status)"
        ),
    ),
    # -- the audit ----------------------------------------------------------------------------
    _R(
        "AUDIT_READS_EVERY_FIELD",
        _AUDIT,
        _TEXT_FIELDS,
        "ANY",
        "every text, each read in its field's context",
        "nothing on its own: it collects the findings the rules below produce",
        False,
        False,
        "C",
        GATE_MECHANISM,
        ("sros_opportunity.assertion_audit_v1_3:audit_output",),
        "the aggregation that turns findings into refusals; the rules it aggregates are listed on "
        "their own",
    ),
    _R(
        "FIELD_HAS_A_CONTEXT",
        _AUDIT,
        _ALL,
        "STRUCTURAL",
        "only the contract's fields",
        "a field the field-context policy does not name",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_2:SECOND_OPPORTUNITY_FIELD_POLICY",),
        "the contract says the object carries no other field",
        v1_2_evidence=("system", "every one required, and no other field."),
        refusal_signature=r"has no field context, so its text cannot be read as anything",
    ),
    _R(
        "CLASSIFICATION_LABEL_KNOWN",
        _AUDIT,
        ("statement_classifications",),
        "LABELLED",
        "an item carrying one of the three labels",
        "an item whose label has no disposition",
        True,
        True,
        "B",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_2:CLASSIFICATION_DISPOSITIONS",),
        "a closed choice the contract renders member by member",
        v1_2_evidence=(
            "system",
            "classification: exactly one of: OBSERVED_OR_EVIDENCE_SUPPORTED, "
            "HYPOTHESIS_TO_VALIDATE, UNKNOWN_REQUIRES_EVIDENCE",
        ),
        refusal_signature=r"^unknown label ",
    ),
    _R(
        "DEFINITIONAL_IDENTIFIER_SUPPLIED",
        _AUDIT,
        _TEXT_FIELDS,
        "ANY",
        "a definitional identifier a trusted fact carries",
        "an identifier of a trusted scheme that no trusted fact supplies",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_context:TrustedContext",),
        "an external definition is prior knowledge, which v1.2.0 says is unavailable",
        v1_2_evidence=_USE_ONLY_SUPPLIED,
        refusal_signature=r"^the definitional identifier \S+ is supplied by no trusted",
    ),
    _R(
        "NUMBERS_ARE_SUPPLIED",
        _AUDIT,
        _TEXT_FIELDS,
        "ANY",
        "a number a source content statement or a packet structural fact carries",
        "any other number, including a figure that occurs only inside a source name",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.support_origin:TypedSupportUniverse.supplied_numbers",),
        "v1.2.0 states the rule for numbers; the source-name part is rendered with the metadata "
        "rule",
        v1_2_evidence=(
            "system",
            "NUMBERS. You may restate a number that appears in a supplied statement.",
        ),
        refusal_signature=r"^the number \S+ appears in no source content statement",
    ),
    _R(
        "FIELD_SHAPE_KEPT",
        _FIELDS,
        ("critical_uncertainties", "recommended_next_evidence"),
        "UNKNOWN_REQUIRES_EVIDENCE / FUTURE_EVIDENCE_REQUEST",
        "an uncertainty that states what is not known; a request that names what would have to "
        "be observed",
        "an item that asserts instead, which is then read as the assertion it became",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_2:SECOND_OPPORTUNITY_FIELD_POLICY",),
        "v1.2.0 names what the fields are for and never says their text keeps that shape; rendered "
        "from the field policy at proposition level, without the patterns that read it",
        refusal_signature=r"^it is not (?:request|uncertainty)-shaped",
    ),
    _R(
        "FIELD_TEXT_READ_BY_ITS_DISPOSITION",
        _FIELDS,
        _TEXT_FIELDS,
        "ANY",
        "text that does what its field does",
        "nothing on its own: each field's disposition decides which rules read its text",
        True,
        False,
        "A",
        GATE_MECHANISM,
        ("sros_opportunity.second_opportunity_gate_v1_2:SECOND_OPPORTUNITY_FIELD_POLICY",),
        "which fields assert, which propose a test and which only name an unknown decides what a "
        "word may do in each; v1.2.0 never says so, and the field policy is its first-class source",
    ),
    _R(
        "TRANSFORMATION_CONCEPTS_NOT_ASSERTED",
        _AUDIT,
        _TEXT_FIELDS,
        "ASSERTING OR SHAPED",
        "a transformation concept denied, listed as not supported, or named as unknown",
        "a transformation concept asserted with no source content statement asserting it",
        True,
        True,
        "A",
        GATE_ENFORCED,
        (
            "sros_opportunity.second_opportunity:FORBIDDEN_TRANSFORMATIONS",
            "sros_opportunity.second_opportunity_gate_v1_2:FORBIDDEN_CONCEPTS_V1_2",
        ),
        "v1.2.0's anti-distortion block states each transformation and what it is not",
        v1_2_evidence=(
            "system",
            "WHAT THIS PACKET IS AND IS NOT. Each line is refused by a deterministic gate.",
        ),
        refusal_signature=rf"^(?:{_names(_TRANSFORMATION_NAMES)}): '.*' is asserted \(",
    ),
    _R(
        "ADDED_CONCEPTS_NOT_ASSERTED",
        _AUDIT,
        _TEXT_FIELDS,
        "ASSERTING OR SHAPED",
        "an added concept denied, listed as not supported, or named as unknown",
        "an added concept asserted with no source content statement asserting it",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_2:FORBIDDEN_CONCEPTS_V1_2",),
        "gate v1.2.0 added concepts the v1.2.0 prompt never names; rendered from each concept's "
        "own name and never-text, and never from its phrases",
        refusal_signature=rf"^(?:{_names(_ADDED_CONCEPT_NAMES)}): '.*' is asserted \(",
    ),
    _R(
        "LIMITING_FACT_NEVER_SUPPORTS_ITS_CONCEPT",
        _TRUSTED,
        _TEXT_FIELDS,
        "ASSERTING OR SHAPED",
        "a trusted identifier restated as the limit it is",
        "a trusted identifier cited for the concept its fact limits",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_context:TrustedFact.never_supports",),
        "v1.2.0's anti-distortion block pairs each definition with what it is not",
        v1_2_evidence=(
            "system",
            "WHAT THIS PACKET IS AND IS NOT. Each line is refused by a deterministic gate.",
        ),
        refusal_signature=r"^[A-Z]+-\d+ is restated from the trusted ",
    ),
    _R(
        "NO_SCORE_ASSERTED",
        _AUDIT,
        _TEXT_FIELDS,
        "ASSERTING OR SHAPED",
        "a score denied",
        "a score asserted",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_context:SCORE_TERMS",),
        "v1.2.0 says there is no score anywhere in this task",
        v1_2_evidence=("system", "no probability and no score anywhere in this task."),
        refusal_signature=r"^'(?:scored|score)' is asserted \(",
    ),
    _R(
        "SOURCE_NAME_IS_NOT_A_SUPPLIED_WORD",
        _UNIVERSE,
        _ASSERTING_FIELDS,
        "SUPPORTED_ASSERTION / STRUCTURAL_FACT / HYPOTHESIS_TO_VALIDATE",
        "a domain word a source content statement carries",
        "a domain word whose only supplied occurrence is inside a source metadata label",
        True,
        False,
        "A",
        GATE_ENFORCED,
        (
            "sros_opportunity.second_opportunity_gate_v1_3:SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION",
            "sros_opportunity.support_origin:SupportOrigin",
        ),
        "the operator's evidence-boundary decision (ADR-040); v1.2.0 predates it and never "
        "separates what a source reported from what it is called",
        refusal_signature=rf"^{re.escape(SOURCE_METADATA_NOT_FACTUAL_SUPPORT)}: ",
    ),
    _R(
        "SOURCE_NAME_LICENSES_ITS_WHOLE_OCCURRENCE",
        _META,
        _TEXT_FIELDS,
        "ANY",
        "a source named by its whole label, as provenance",
        "nothing on its own: the gate reads the whole label as a name before reading words",
        True,
        False,
        "A",
        GATE_MECHANISM,
        (
            "sros_opportunity.second_opportunity_gate_v1_3:SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION",
            "sros_opportunity.support_origin:SourceMetadataLabelKind",
        ),
        "naming where a statement came from is always allowed, and a model told only that names "
        "are not evidence would stop attributing",
    ),
    _R(
        "PRIOR_KNOWLEDGE_IS_NOT_SUPPORT",
        _AUDIT,
        _ASSERTING_FIELDS,
        "SUPPORTED_ASSERTION / STRUCTURAL_FACT / HYPOTHESIS_TO_VALIDATE",
        "domain vocabulary a source content statement carries",
        "domain vocabulary no supplied statement carries at all",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity:PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS",),
        "v1.2.0 says prior knowledge is unavailable as factual support; the vocabulary list itself "
        "is class D",
        v1_2_evidence=_USE_ONLY_SUPPLIED,
        refusal_signature=r"^'[^']*' appears in no source content statement, compared under ",
    ),
    _R(
        "UNMEASURED_COMMERCIAL_QUANTITIES_NEVER_ASSERTED",
        _GUARD,
        _ASSERTING_FIELDS,
        "SUPPORTED_ASSERTION / STRUCTURAL_FACT / HYPOTHESIS_TO_VALIDATE",
        "such a quantity denied or named as unknown",
        "a quantity no registered source measures, asserted",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.guards:FORBIDDEN_TERMS",),
        "v1.2.0 lists at proposition level what may not be asserted; the term list itself is "
        "class D",
        v1_2_evidence=(
            "system",
            "Specifically, you may not assert anything about: how many people or organisations",
        ),
        refusal_signature=r"is not supportable by any registered source",
    ),
    _R(
        "COMMERCIAL_TERMS_NEED_THEIR_DIMENSION",
        _GUARD,
        _ASSERTING_FIELDS,
        "SUPPORTED_ASSERTION / STRUCTURAL_FACT / HYPOTHESIS_TO_VALIDATE",
        "a commercial term whose dimension the answer lists as supported and the packet carries",
        "a commercial term asserting a dimension no eligible evidence supports",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.guards:FORBIDDEN_TERMS",),
        "v1.2.0 forbids asserting these subjects at all, which is stricter than the gate",
        v1_2_evidence=(
            "system",
            "Specifically, you may not assert anything about: how many people or organisations",
        ),
        refusal_signature=r"^'[^']*' asserts [A-Z_]+, which no eligible evidence in this packet",
    ),
    _R(
        "NO_VALIDATION_LANGUAGE",
        _GUARD,
        _ASSERTING_FIELDS,
        "SUPPORTED_ASSERTION / STRUCTURAL_FACT / HYPOTHESIS_TO_VALIDATE",
        "a hypothesis record",
        "wording that states a conclusion",
        True,
        True,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.guards:VALIDATION_WORDS",),
        "v1.2.0 forbids describing anything as validated, proven or high-confidence",
        v1_2_evidence=("system", "anything as high-confidence, validated, proven or significant."),
        refusal_signature=r"^'[^']*' states a conclusion; this is a hypothesis record",
    ),
    _R(
        "OBSERVED_DISJUNCTION_FAILS_CLOSED",
        _DISJUNCTION,
        ("statement_classifications",),
        "SUPPORTED_ASSERTION",
        "an OBSERVED item that states one proposition, or denies alternatives together",
        "an OBSERVED item that joins alternatives outside any denial",
        True,
        False,
        "A",
        GATE_ENFORCED,
        (
            "sros_opportunity.assertion_audit_v1_3:DISJUNCTION_POLICY_VERSION",
            "sros_opportunity.assertion_audit_v1_3:DISJUNCTIVE_OBSERVED_STATEMENT",
            "docs/data/second-opportunity-output-gate-v1.3-freeze-v1.json:DISJUNCTION_POLICY",
        ),
        "the gate evaluates no disjunction, so one classification over two alternatives fails "
        "closed; v1.2.0 predates the rule",
        refusal_signature=rf"^{re.escape(DISJUNCTIVE_OBSERVED_STATEMENT)}: ",
    ),
    _R(
        "NOTHING_PROMOTED_TO_A_CONCLUSION",
        _AUDIT,
        (
            "hypothesis_statement",
            "critical_uncertainties",
            "recommended_next_evidence",
            "statement_classifications",
        ),
        "HYPOTHESIS_TO_VALIDATE / UNKNOWN_REQUIRES_EVIDENCE / FUTURE_EVIDENCE_REQUEST",
        "a hypothesis, an unknown or a request kept as what it is",
        "one promoted to a conclusion by certainty or validation wording",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.assertion_context:CERTAINTY_MARKERS",),
        "v1.2.0 forbids writing a hypothesis as an observation and never mentions certainty; the "
        "word list itself is class D",
        instruction=(
            "a hypothesis, an unknown and a request for evidence stay what they are: no adverb of "
            "certainty and no wording of confirmation turns one into a conclusion"
        ),
        refusal_signature=r"^\[.*\] promote a [A-Z_]+ to a conclusion",
    ),
    _R(
        "NOT_SUPPORTED_ITEM_NEVER_CLAIMS_SUPPORT",
        _AUDIT,
        ("commercial_claims_not_supported",),
        "EXPLICITLY_NOT_SUPPORTED",
        "an item that names a claim the packet does not support",
        "an item that says the claim it names is established",
        True,
        False,
        "A",
        GATE_ENFORCED,
        ("sros_opportunity.second_opportunity_gate_v1_2:SECOND_OPPORTUNITY_FIELD_POLICY",),
        "rendered from the field's disposition; the predicate list that reads it is class D",
        refusal_signature=r"^it says the claim is '",
    ),
    _R(
        "OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED",
        _AUDIT,
        ("statement_classifications",),
        "SUPPORTED_ASSERTION",
        "one proposition a source content statement or a packet structural fact states itself",
        "nothing beyond the vocabulary, number and disjunction rules: the gate evaluates no "
        "proposition's truth",
        True,
        False,
        "A",
        INSTRUCTION_BEYOND_THE_GATE,
        (
            "sros_opportunity.assertion_audit_v1_3:LEXICAL_MATCH_IS_FACTUAL_SUPPORT",
            "operator decision OBSERVED_STATEMENTS_MUST_BE_ATOMIC_AND_DIRECTLY_SUPPORTED",
        ),
        "a lexical match is necessary and never sufficient; the operator decided an OBSERVED "
        "statement is atomic and directly supported, which the gate cannot check and the prompt "
        "must say",
    ),
    # -- how the gate reads, and what it never publishes --------------------------------------
    _R(
        "LABEL_EQUAL_TO_A_GATED_TERM_NEVER_MASKS",
        _AUDIT,
        _TEXT_FIELDS,
        "ANY",
        "a label that is not itself a gated term, read as a name",
        "nothing on its own: such a label is read as the term it spells",
        False,
        False,
        "C",
        GATE_MECHANISM,
        ("sros_opportunity.assertion_audit_v1_3:maskable_labels",),
        "depends on what the registry calls a source, which no answer controls",
    ),
    _R(
        "DIMENSION_NAME_OF_A_SUPPORTED_DIMENSION",
        _AUDIT,
        _ASSERTING_FIELDS,
        "ANY",
        "the canonical name of a dimension listed as supported and carried by the packet",
        "nothing on its own: the name is read as a structural fact",
        True,
        True,
        "B",
        GATE_MECHANISM,
        ("sros_opportunity.assertion_context:canonical_dimension_phrase",),
        "the contract renders the dimension names, spelled exactly",
        v1_2_evidence=("system", "exactly these names, spelled exactly: PROBLEM_OR_NEED"),
    ),
    _R(
        "EMPTY_OR_SENTINEL_TEXT_ASSERTS_NOTHING",
        _AUDIT,
        _TEXT_FIELDS,
        "ANY",
        "an empty text or the sentinel UNKNOWN_NOT_SUPPORTED",
        "nothing: such a text is not factual",
        True,
        True,
        "B",
        GATE_MECHANISM,
        ("sros_opportunity.second_opportunity:SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1",),
        "the contract renders the sentinel verbatim",
        v1_2_evidence=("system", "or the exact string UNKNOWN_NOT_SUPPORTED if they name none."),
    ),
    _R(
        "NOTHING_CHECKABLE_IS_NOTED",
        _PERSISTENCE,
        _TEXT_FIELDS,
        "ANY",
        "nothing: a note, never a refusal",
        "nothing",
        False,
        False,
        "C",
        GATE_MECHANISM,
        ("sros_opportunity.assertion_audit_v1_3:evaluate_persistence_v1_3",),
        "a record of an answer with nothing checkable in it, not a rule an answer follows",
    ),
    _R(
        "INFLECTION_POLICY",
        _INFLECTION,
        _TEXT_FIELDS,
        "ANY",
        "a word in any number its written rules fold",
        "nothing on its own: both sides of every comparison use one function",
        True,
        False,
        "D",
        GATE_MECHANISM,
        ("sros_opportunity.lexical_inflection:INFLECTION_RULES",),
        "a normalizer rule; publishing it teaches which forms are compared and which are not",
    ),
    _R(
        "SUPPORT_PREDICATES_VERBATIM",
        _GUARD,
        ("commercial_claims_not_supported",),
        "EXPLICITLY_NOT_SUPPORTED",
        "nothing on its own",
        "nothing on its own: the verb forms a not-supported item may not use are matched verbatim",
        True,
        False,
        "D",
        GATE_MECHANISM,
        ("sros_opportunity.assertion_context:SUPPORT_PREDICATES",),
        "a word list; the proposition it enforces is rendered with the field's disposition",
    ),
    _R(
        "CLAUSE_SCOPED_DENIAL_READING",
        _GUARD,
        _TEXT_FIELDS,
        "ANY",
        "nothing on its own",
        "nothing on its own: denials scope their clause, and a contrast after a denial re-asserts",
        True,
        False,
        "D",
        GATE_MECHANISM,
        (
            "sros_opportunity.assertion_context:DENIAL_MARKERS_V1_3",
            "sros_opportunity.assertion_context:_CLAUSE_BOUNDARY",
        ),
        "how the gate reads grammar; publishing it would teach phrasing, and the propositions it "
        "protects are stated as propositions",
    ),
    _R(
        "REQUEST_AND_UNCERTAINTY_PATTERNS",
        _FIELDS,
        ("critical_uncertainties", "recommended_next_evidence"),
        "UNKNOWN_REQUIRES_EVIDENCE / FUTURE_EVIDENCE_REQUEST",
        "nothing on its own",
        "nothing on its own: the patterns that decide whether a shape was kept",
        True,
        False,
        "D",
        GATE_MECHANISM,
        (
            "sros_opportunity.assertion_context:is_request_shaped",
            "sros_opportunity.assertion_context:is_uncertainty_shaped",
        ),
        "patterns; the shapes they protect are rendered from the field policy",
    ),
    _R(
        "GATED_VOCABULARY_LISTS",
        _AUDIT,
        _TEXT_FIELDS,
        "ANY",
        "nothing on its own",
        "nothing on its own: the lists the vocabulary rules above consult",
        True,
        False,
        "D",
        GATE_MECHANISM,
        (
            "sros_opportunity.second_opportunity:PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS",
            "sros_opportunity.second_opportunity_gate_v1_2:FORBIDDEN_CONCEPTS_V1_2 phrases",
            "sros_opportunity.guards:FORBIDDEN_TERMS",
            "sros_opportunity.guards:VALIDATION_WORDS",
            "sros_opportunity.assertion_context:CERTAINTY_MARKERS",
            "sros_opportunity.assertion_context:SCORE_TERMS",
        ),
        "a published list is a list of words to avoid, and a model that avoids the words has not "
        "stopped asserting the thing",
    ),
    _R(
        "LABEL_MATCHING_ORDER",
        _META,
        _TEXT_FIELDS,
        "ANY",
        "nothing on its own",
        "nothing on its own: labels are matched whole, longest first, never overlapping",
        False,
        False,
        "D",
        GATE_MECHANISM,
        ("sros_opportunity.support_origin:label_spans",),
        "a matching rule; publishing it would teach how to hide a word inside something shaped "
        "like a name",
    ),
    _R(
        "DISJUNCTION_BOUNDARY_READING",
        _DISJUNCTION,
        ("statement_classifications",),
        "SUPPORTED_ASSERTION",
        "nothing on its own",
        "nothing on its own: where a connective counts as joining alternatives",
        True,
        False,
        "D",
        GATE_MECHANISM,
        ("sros_opportunity.assertion_audit_v1_3:disjunctive_connectives",),
        "a boundary rule; the proposition it enforces is rendered as a proposition",
    ),
)

#: Every refusal site in the two frozen v1.3.0 modules, keyed (module, function, line) and mapped to
#: the rule, or rules, it produces. Lines are stable because gate 77 pins both files by digest; CI
#: recomputes the sites from the syntax tree and refuses one this map does not name.
REFUSAL_SITE_RULES: dict[tuple[str, str, int], tuple[str, ...]] = {
    ("assertion_audit_v1_3.py", "_mask_identifiers", 216): ("DEFINITIONAL_IDENTIFIER_SUPPLIED",),
    ("assertion_audit_v1_3.py", "_concept_findings", 251): (
        "TRANSFORMATION_CONCEPTS_NOT_ASSERTED",
        "ADDED_CONCEPTS_NOT_ASSERTED",
    ),
    ("assertion_audit_v1_3.py", "_concept_findings", 260): (
        "LIMITING_FACT_NEVER_SUPPORTS_ITS_CONCEPT",
    ),
    ("assertion_audit_v1_3.py", "_scoring_status_findings", 273): ("NO_SCORE_ASSERTED",),
    ("assertion_audit_v1_3.py", "_marker_findings", 297): ("SOURCE_NAME_IS_NOT_A_SUPPLIED_WORD",),
    ("assertion_audit_v1_3.py", "_marker_findings", 305): ("PRIOR_KNOWLEDGE_IS_NOT_SUPPORT",),
    ("assertion_audit_v1_3.py", "audit_text", 339): ("AUDIT_READS_EVERY_FIELD",),
    ("assertion_audit_v1_3.py", "audit_text", 341): ("NUMBERS_ARE_SUPPLIED",),
    ("assertion_audit_v1_3.py", "audit_text", 361): ("FIELD_SHAPE_KEPT",),
    ("assertion_audit_v1_3.py", "audit_text", 367): ("AUDIT_READS_EVERY_FIELD",),
    ("assertion_audit_v1_3.py", "audit_text", 368): ("AUDIT_READS_EVERY_FIELD",),
    ("assertion_audit_v1_3.py", "audit_text", 372): ("AUDIT_READS_EVERY_FIELD",),
    ("assertion_audit_v1_3.py", "audit_text", 377): (
        "UNMEASURED_COMMERCIAL_QUANTITIES_NEVER_ASSERTED",
    ),
    ("assertion_audit_v1_3.py", "audit_text", 382): ("COMMERCIAL_TERMS_NEED_THEIR_DIMENSION",),
    ("assertion_audit_v1_3.py", "audit_text", 388): ("NO_VALIDATION_LANGUAGE",),
    ("assertion_audit_v1_3.py", "audit_text", 393): ("OBSERVED_DISJUNCTION_FAILS_CLOSED",),
    ("assertion_audit_v1_3.py", "audit_text", 411): ("NOTHING_PROMOTED_TO_A_CONCLUSION",),
    ("assertion_audit_v1_3.py", "audit_text", 418): ("NOT_SUPPORTED_ITEM_NEVER_CLAIMS_SUPPORT",),
    ("assertion_audit_v1_3.py", "audit_output", 453): ("FIELD_HAS_A_CONTEXT",),
    ("assertion_audit_v1_3.py", "audit_output", 475): ("CLASSIFICATION_LABEL_KNOWN",),
    ("assertion_audit_v1_3.py", "audit_output", 505): ("AUDIT_READS_EVERY_FIELD",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 532): (
        "INSUFFICIENT_EVIDENCE_IS_AN_OUTCOME",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 538): ("DECISION_IS_ONE_OF_TWO",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 541): (
        "EVERY_SOURCE_DECLARES_ITS_NAMES",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 548): (
        "SUBJECT_IS_THE_PACKET_IDENTITY",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 558): ("CITED_EVIDENCE_IN_PACKET",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 563): ("CITED_CLAIMS_IN_PACKET",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 565): ("AT_LEAST_ONE_EVIDENCE_CITED",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 567): ("AT_LEAST_ONE_CLAIM_CITED",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 571): (
        "EVIDENCE_CITED_WITH_ITS_CLAIM",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 580): ("SOURCE_FAMILIES_FROM_PACKET",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 586): (
        "SUPPORTED_DIMENSIONS_FROM_PACKET",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 592): (
        "SUPPORTED_AND_UNSUPPORTED_DISJOINT",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 599): (
        "MANDATORY_UNSUPPORTED_REPORTED",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 606): (
        "INDEPENDENCE_RECORDS_UNKNOWN",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 612): (
        "INDEPENDENCE_RECORDS_UNKNOWN",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 619): (
        "RELIABILITY_RESTATES_SCORABILITY",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 624): (
        "RELIABILITY_RESTATES_SCORABILITY",
    ),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 631): ("AUDIT_READS_EVERY_FIELD",),
    ("assertion_audit_v1_3.py", "evaluate_persistence_v1_3", 635): ("NOTHING_CHECKABLE_IS_NOTED",),
    ("second_opportunity_gate_v1_3.py", "evaluate_second_opportunity_output_v1_3", 239): (
        "SCHEMA_V1_1_0_VALIDATION",
    ),
    ("second_opportunity_gate_v1_3.py", "evaluate_second_opportunity_output_v1_3", 246): (
        "CONFIDENCE_IS_EXPLORATORY",
    ),
    ("second_opportunity_gate_v1_3.py", "evaluate_second_opportunity_output_v1_3", 252): (
        "NEXT_EVIDENCE_NOT_EMPTY",
    ),
    ("second_opportunity_gate_v1_3.py", "evaluate_second_opportunity_output_v1_3", 258): (
        "CLASSIFICATIONS_NOT_EMPTY",
    ),
    ("second_opportunity_gate_v1_3.py", "evaluate_second_opportunity_output_v1_3", 268): (
        "CLASSIFICATION_KINDS_CLOSED",
    ),
    ("second_opportunity_gate_v1_3.py", "evaluate_second_opportunity_output_v1_3", 270): (
        "SOMETHING_REMAINS_UNKNOWN",
    ),
}


def census_by_id() -> dict[str, SemanticGateRule]:
    found: dict[str, SemanticGateRule] = {}
    for rule in SEMANTIC_RULE_CENSUS:
        if rule.rule_id in found:
            raise ValueError(f"{rule.rule_id} is in the census twice")
        found[rule.rule_id] = rule
    return found


# ============================================================================= the policy


@dataclass(frozen=True)
class ObservedDisjunctionGenerationPolicy:
    """The disjunction rule as the prompt states it. The version and code are the frozen gate's;
    the connectives are the ones the operator's decision names, and CI checks each against the
    frozen detector, both joining alternatives and denied together."""

    version: str
    code: str
    connectives: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.connectives:
            raise ValueError("a disjunction policy names the connectives it concerns")


@dataclass(frozen=True)
class SemanticGenerationPolicy:
    """Every first-class object the semantic block is rendered from, and nothing else."""

    version: str
    field_policy: tuple[FieldContext, ...]
    classification_dispositions: Mapping[str, Disposition]
    forbidden_concepts: tuple[ForbiddenConcept, ...]
    transformation_names: tuple[str, ...]
    metadata_decision: Mapping[str, object]
    disjunction: ObservedDisjunctionGenerationPolicy
    census: tuple[SemanticGateRule, ...]


SEMANTIC_GENERATION_POLICY = SemanticGenerationPolicy(
    version=SEMANTIC_GENERATION_POLICY_VERSION,
    field_policy=SECOND_OPPORTUNITY_FIELD_POLICY,
    classification_dispositions=CLASSIFICATION_DISPOSITIONS,
    forbidden_concepts=FORBIDDEN_CONCEPTS_V1_2,
    transformation_names=_TRANSFORMATION_NAMES,
    metadata_decision=SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION,
    disjunction=ObservedDisjunctionGenerationPolicy(
        version=DISJUNCTION_POLICY_VERSION,
        code=DISJUNCTIVE_OBSERVED_STATEMENT,
        connectives=("or", "either ... or"),
    ),
    census=SEMANTIC_RULE_CENSUS,
)

#: What a field's text does, by its disposition and the shape it must keep. Keyed by the enums, so a
#: field policy that reaches a pair nobody has worded is refused rather than rendered silently.
DISPOSITION_WORDING: dict[tuple[Disposition, Shape], str] = {
    (Disposition.SUPPORTED_ASSERTION, Shape.FREE): (
        "asserted as supported: every clause is a claim about the packet, and every word "
        "describing the domain comes from what a source reported, never from a source name or "
        "from prior knowledge"
    ),
    (Disposition.HYPOTHESIS_TO_VALIDATE, Shape.FREE): (
        "a hypothesis to test, read clause by clause: each clause is framed as something to "
        "test, and every word describing the domain still comes from what a source reported"
    ),
    (Disposition.STRUCTURAL_FACT, Shape.FREE): (
        "restates a fact the task gives about the packet, in the task's own terms"
    ),
    (Disposition.UNKNOWN_REQUIRES_EVIDENCE, Shape.UNCERTAINTY): (
        "each item states something that is not known, as an open question or as a statement "
        "that it is not established, and never asserts it"
    ),
    (Disposition.EXPLICITLY_NOT_SUPPORTED, Shape.FREE): (
        "each item names a claim this packet does not support, and never says that the claim is "
        "established or supported"
    ),
    (Disposition.FUTURE_EVIDENCE_REQUEST, Shape.REQUEST): (
        "each item names the evidence or observation that would have to be obtained, and states "
        "no finding"
    ),
}

#: What each classification does to the statement it labels, keyed by the disposition it maps to.
CLASSIFICATION_MEANING: dict[Disposition, str] = {
    Disposition.SUPPORTED_ASSERTION: "asserts what a source content statement establishes",
    Disposition.HYPOTHESIS_TO_VALIDATE: "proposes something to test",
    Disposition.UNKNOWN_REQUIRES_EVIDENCE: "states something that is not established",
}

#: Which rules each field stanza states, by disposition and shape.
_STANZA_RULES: dict[tuple[Disposition, Shape], tuple[str, ...]] = {
    (Disposition.UNKNOWN_REQUIRES_EVIDENCE, Shape.UNCERTAINTY): ("FIELD_SHAPE_KEPT",),
    (Disposition.FUTURE_EVIDENCE_REQUEST, Shape.REQUEST): ("FIELD_SHAPE_KEPT",),
    (Disposition.EXPLICITLY_NOT_SUPPORTED, Shape.FREE): (
        "NOT_SUPPORTED_ITEM_NEVER_CLAIMS_SUPPORT",
    ),
}


# ============================================================================= rendering

_Tagged = tuple[str, tuple[str, ...]]
_WIDTH = 96


def _wrap(
    text: str, indent: str, rules: tuple[str, ...], first: str | None = None
) -> list[_Tagged]:
    """`text` wrapped at a fixed width, every line tagged with the same rules."""
    lines = textwrap.wrap(
        text,
        width=_WIDTH,
        initial_indent=indent if first is None else first,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return [(line, rules) for line in lines]


def _quoted(items: Sequence[str]) -> str:
    return " or ".join(f'"{item}"' for item in items)


def _joined(items: Sequence[str]) -> str:
    words = [str(item) for item in items]
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " or " + words[-1]


def _label_for(policy: SemanticGenerationPolicy, disposition: Disposition) -> str:
    labels = [k for k, v in policy.classification_dispositions.items() if v is disposition]
    if len(labels) != 1:
        raise ValueError(f"no single classification carries the disposition {disposition.value}")
    return labels[0]


def _labelled_field(policy: SemanticGenerationPolicy) -> FieldContext:
    fields = [fc for fc in policy.field_policy if fc.item_label_key is not None]
    if len(fields) != 1:
        raise ValueError("the field policy names no single labelled field")
    return fields[0]


def _listed(decision: Mapping[str, object], key: str) -> list[str]:
    value = decision.get(key)
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError(f"the evidence-boundary decision has no list {key!r}")
    return [str(item) for item in value]


def _source_name_section(policy: SemanticGenerationPolicy) -> list[_Tagged]:
    decision = policy.metadata_decision
    if decision.get("SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT") is not False:
        raise ValueError("the evidence-boundary decision no longer says a name is not evidence")
    kinds = _listed(decision, "metadata_is")
    may = _listed(decision, "metadata_may_support")
    may_not = _listed(decision, "metadata_may_not_support")
    word = "SOURCE_NAME_IS_NOT_A_SUPPLIED_WORD"
    name = "SOURCE_NAME_LICENSES_ITS_WHOLE_OCCURRENCE"
    return [
        ("SOURCE NAMES ARE PROVENANCE, NEVER EVIDENCE.", ()),
        *_wrap(
            "A supplied statement carries two different things: what a source reported, and the "
            "name of the source or dataset it came from. The names that occur in the supplied "
            "statements are listed in the trusted context under SOURCE NAMES.",
            "  ",
            (word,),
        ),
        *_wrap(f"A {_joined(kinds)} identifies where data came from.", "  ", (word,)),
        *_wrap(f"It may support {_joined(may)}.", "  ", (name,)),
        ("  It never supports:", (word,)),
        *[(f"    - {item}", (word,)) for item in may_not],
        *_wrap(
            "So a word that occurs in the supplied statements only inside a name has not been "
            "supplied, and neither has a figure inside one.",
            "  ",
            (word,),
        ),
        *_wrap(
            "Naming a source by its whole name, to say where a statement came from, is always "
            "allowed.",
            "  ",
            (name,),
        ),
    ]


def _observed_section(policy: SemanticGenerationPolicy) -> list[_Tagged]:
    field = _labelled_field(policy).field_name
    observed = _label_for(policy, Disposition.SUPPORTED_ASSERTION)
    hypothesis = _label_for(policy, Disposition.HYPOTHESIS_TO_VALIDATE)
    unknown = _label_for(policy, Disposition.UNKNOWN_REQUIRES_EVIDENCE)
    atomic = "OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED"
    disjunction = "OBSERVED_DISJUNCTION_FAILS_CLOSED"
    return [
        ("OBSERVED STATEMENTS ARE ATOMIC AND DIRECTLY SUPPORTED.", ()),
        *_wrap(
            f"An item of {field} classified {observed} states exactly one proposition, and a "
            "source content statement, or a fact the task states about the packet, states that "
            "proposition itself. Sharing words with a supplied statement is not support.",
            "  ",
            (atomic,),
        ),
        *_wrap(
            f"Such an item never joins alternatives with {_quoted(policy.disjunction.connectives)}: "
            "one classification cannot say which alternative the evidence establishes. Write each "
            "alternative the statements do establish as its own item, or classify the joined "
            f"statement {hypothesis} or {unknown}. This concerns items classified {observed} only: "
            "alternatives such an item denies together, and every other field, may use the word "
            "in its ordinary sense.",
            "  ",
            (disjunction,),
        ),
        *_wrap(
            f"Where support is incomplete, the item is {hypothesis} or {unknown}, never "
            f"{observed}.",
            "  ",
            (atomic,),
        ),
    ]


def _field_section(policy: SemanticGenerationPolicy) -> list[_Tagged]:
    """One stanza per distinct wording, at the position of its first field, naming every field
    that shares it."""
    stanzas: list[tuple[list[str], list[str], tuple[str, ...]]] = []
    for fc in policy.field_policy:
        if fc.shape is Shape.ENUMERATION:
            continue
        if fc.item_label_key is not None:
            parts = []
            for label, disposition in policy.classification_dispositions.items():
                if disposition not in CLASSIFICATION_MEANING:
                    raise ValueError(f"no meaning is worded for {disposition.value}")
                parts.append(f"{label} {CLASSIFICATION_MEANING[disposition]}")
            lines = [
                "each item takes the meaning of the classification it carries: " + "; ".join(parts)
            ]
            rules: tuple[str, ...] = ("FIELD_TEXT_READ_BY_ITS_DISPOSITION",)
        else:
            assert fc.disposition is not None  # noqa: S101 -- guaranteed by FieldContext
            key = (fc.disposition, fc.shape)
            if key not in DISPOSITION_WORDING:
                raise ValueError(
                    f"{fc.field_name}: no wording for {fc.disposition.value} with {fc.shape.value}"
                )
            lines = [DISPOSITION_WORDING[key]]
            rules = ("FIELD_TEXT_READ_BY_ITS_DISPOSITION", *_STANZA_RULES.get(key, ()))
        shared = next((s for s in stanzas if s[1] == lines), None)
        if shared is not None:
            shared[0].append(fc.field_name)
        else:
            stanzas.append(([fc.field_name], lines, rules))
    out: list[_Tagged] = [("WHAT EACH FIELD'S TEXT DOES.", ())]
    for names, lines, rules in stanzas:
        out.extend(_wrap(", ".join(names), "  ", rules))
        for line in lines:
            out.extend(_wrap(line, "    ", rules))
    return out


def _concept_section(policy: SemanticGenerationPolicy) -> list[_Tagged]:
    rule = "ADDED_CONCEPTS_NOT_ASSERTED"
    added = [c for c in policy.forbidden_concepts if c.name not in policy.transformation_names]
    if not added:
        return []
    out: list[_Tagged] = [
        (
            "CONCEPTS THIS PACKET NEVER ESTABLISHES, beside the transformations above. Naming one",
            (rule,),
        ),
        (
            "as unknown, as not supported, or as something to observe is allowed; asserting it is",
            (rule,),
        ),
        ("refused.", (rule,)),
    ]
    for concept in added:
        out.append((f"  {concept.name}", (rule,)))
        out.append((f"    it is NOT: {concept.never}", (rule,)))
    return out


def _instruction_section(policy: SemanticGenerationPolicy) -> list[_Tagged]:
    out: list[_Tagged] = [("A FORM_HYPOTHESIS ANSWER ALSO SATISFIES EACH OF THESE.", ())]
    for rule in policy.census:
        if rule.instruction is not None:
            out.extend(_wrap(rule.instruction, "    ", (rule.rule_id,), first="  - "))
    return out


def tagged_lines(policy: SemanticGenerationPolicy = SEMANTIC_GENERATION_POLICY) -> list[_Tagged]:
    """Every line of the semantic block, each with the rules it states."""
    out: list[_Tagged] = [
        ("SEMANTIC RULES THE ANSWER IS AUDITED AGAINST.", ()),
        ("", ()),
        (
            "These rules are stated as propositions about what the answer may assert. A deterministic",
            (),
        ),
        (
            "gate checks the answer against the supplied statements after it is written; an answer",
            (),
        ),
        ("that breaks a rule is refused, never repaired, and nothing rewrites it to pass.", ()),
    ]
    for section in (
        _source_name_section(policy),
        _observed_section(policy),
        _field_section(policy),
        _concept_section(policy),
        _instruction_section(policy),
    ):
        if section:
            out.append(("", ()))
            out.extend(section)
    return out


def semantic_rule_lines(
    policy: SemanticGenerationPolicy = SEMANTIC_GENERATION_POLICY,
) -> dict[str, tuple[str, ...]]:
    """Rule id -> the rendered lines that state it."""
    found: dict[str, list[str]] = {}
    for text, rules in tagged_lines(policy):
        for rule in rules:
            found.setdefault(rule, []).append(text)
    return {rule: tuple(lines) for rule, lines in found.items()}


def render_semantic_generation_rules(
    policy: SemanticGenerationPolicy = SEMANTIC_GENERATION_POLICY,
) -> str:
    """The semantic-policy block, deterministically, from first-class policy objects only."""
    known = census_by_id()
    for rule in policy.census:
        if rule.rule_id not in known:
            raise ValueError(f"{rule.rule_id} is not in the census")
    text = "\n".join(line for line, _ in tagged_lines(policy))
    if re.search(r"\d", text):
        raise ValueError(
            "the semantic block carries a digit. Every number the model reads comes from the "
            "schema or the packet"
        )
    return text


def policy_digest(policy: SemanticGenerationPolicy = SEMANTIC_GENERATION_POLICY) -> str:
    """A digest over every class-A input the block is rendered from."""
    payload = {
        "version": policy.version,
        "fields": [
            [
                fc.field_name,
                fc.disposition.value if fc.disposition else None,
                fc.shape.value,
                fc.item_label_key,
            ]
            for fc in policy.field_policy
        ],
        "classifications": {k: v.value for k, v in policy.classification_dispositions.items()},
        "concepts": [[c.name, c.never] for c in policy.forbidden_concepts],
        "transformations": list(policy.transformation_names),
        "metadata_decision": {
            k: policy.metadata_decision[k]
            for k in (
                "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT",
                "metadata_is",
                "metadata_may_support",
                "metadata_may_not_support",
            )
        },
        "disjunction": [
            policy.disjunction.version,
            policy.disjunction.code,
            list(policy.disjunction.connectives),
        ],
        "instructions": [[r.rule_id, r.instruction] for r in policy.census if r.instruction],
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


# ============================================================================= source names


def source_labels_in_statements(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    metadata: SourceMetadataContext,
) -> tuple[SourceMetadataLabel, ...]:
    """The registry labels of the packet's sources that occur, whole, in its supplied statements.

    A packet source with no declared label is refused: its statements cannot be split, and the
    prompt would present its name as content.
    """
    undeclared = sorted(set(packet.source_ids) - metadata.declared_sources)
    if undeclared:
        raise ValueError(
            f"no source metadata is declared for {undeclared}; a source's name must never reach "
            "the model as content silently"
        )
    statements = [claim_statements[cid] for cid in packet.claim_ids if cid in claim_statements]
    lowered = [s.lower().replace("’", "'") for s in statements]
    return tuple(
        label
        for label in metadata.labels_for(packet.source_ids)
        if any(label_spans(text, label.text) for text in lowered)
    )


def render_source_label_block(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    metadata: SourceMetadataContext,
) -> str:
    """The trusted SOURCE NAMES section: every registry name the supplied statements carry.

    Each string is the registry's own and occurs in the supplied statements already, so the
    section adds no source content; it tells the model which of those words are a name.
    """
    labels = source_labels_in_statements(packet, claim_statements, metadata)
    out = [
        "SOURCE NAMES. These exact strings occur in the supplied statements as the name of a",
        "source or of one of its datasets. A name says where a statement came from: it is",
        "provenance, never evidence, and a word or a figure inside it is not a supplied fact.",
        "",
    ]
    if not labels:
        out.append("  No source name occurs in the supplied statements.")
    for label in labels:
        kind = label.kind.value.lower().replace("_", " ")
        out.append(f'  "{label.text}"')
        out.append(f'    {kind} of source "{label.source_id}"')
    return "\n".join(out)


# ============================================================================= the drift property


def unstated_semantic_rules(
    system: str,
    trusted_context: str,
    task: str,
    policy: SemanticGenerationPolicy = SEMANTIC_GENERATION_POLICY,
) -> list[str]:
    """Every class-A rule the given prompt regions do not state.

    A rule prompt v1.2.0 states is stated where its quoted evidence is; any other class-A rule is
    stated where its rendered lines are, in order, inside the system region.
    """
    regions = {"system": system, "trusted_context": trusted_context, "task": task}
    rendered = semantic_rule_lines(policy)
    system_lines = set(system.split("\n"))
    missing: list[str] = []
    for rule in policy.census:
        if not rule.must_be_explicit_in_v1_3:
            continue
        if rule.v1_2_evidence is not None:
            region, text = rule.v1_2_evidence
            if text not in regions[region]:
                missing.append(rule.rule_id)
            continue
        lines = rendered.get(rule.rule_id)
        if not lines or not set(lines) <= system_lines:
            missing.append(rule.rule_id)
    return missing
