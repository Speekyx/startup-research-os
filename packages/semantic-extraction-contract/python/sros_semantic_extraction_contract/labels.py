"""The semantic label registry, version 1.

Smallest set that is (1) a missing or thin evidence dimension, (2) expressible by the held Stack Overflow
corpus, and (3) representable by the existing ontology without a new member. Two labels are EXTRACTABLE.
The rest are recorded so their absence is a decision, not an oversight:

- ANNOTATION_ONLY: a human marks it so its incidence is measured; the extractor may never emit it.
- BLOCKED: needs a taxonomy extension or a scope decision first; annotators flag incidence only.
- NOT_SAFE: not represented at all, because every reading of it is a prohibited inference.

A label NAME states what the text contains and never what a consumer should conclude (signal taxonomy
§4). The dimension and category names are the existing ontology members, as strings, so this package
does not import the Opportunity engine; a test in that package checks they exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "LABEL_SET_ID",
    "LABEL_SET_VERSION",
    "LABELS",
    "PROHIBITED_INFERENCES",
    "LabelStatus",
    "OntologyFit",
    "SemanticLabel",
    "extractable_labels",
]

LABEL_SET_ID = "first-person-semantic-labels"
LABEL_SET_VERSION = "1.0.0"


class LabelStatus(StrEnum):
    EXTRACTABLE = "EXTRACTABLE"
    ANNOTATION_ONLY = "ANNOTATION_ONLY"
    BLOCKED = "BLOCKED"
    NOT_SAFE = "NOT_SAFE"


class OntologyFit(StrEnum):
    SUPPORTED_BY_EXISTING_ONTOLOGY = "SUPPORTED_BY_EXISTING_ONTOLOGY"
    REQUIRES_TAXONOMY_EXTENSION = "REQUIRES_TAXONOMY_EXTENSION"
    REQUIRES_SCOPE_DECISION = "REQUIRES_SCOPE_DECISION"
    NOT_SAFE_TO_REPRESENT = "NOT_SAFE_TO_REPRESENT"


@dataclass(frozen=True)
class SemanticLabel:
    label_id: str
    status: LabelStatus
    ontology_fit: OntologyFit
    definition: str
    evidence_dimension: str | None
    observation_category: str | None
    requires_subject: bool
    evidence_may_be_in_code: bool
    does_not_establish: tuple[str, ...]
    blocker: str | None = None


_ALWAYS_NOT = (
    "that the problem recurs, or that any other record states the same problem",
    "how many people are affected, severity, or pain",
    "demand, willingness to pay, purchase intent or a market",
    "that the asker's statement is true",
    "independence from any other finding",
)

LABELS: tuple[SemanticLabel, ...] = (
    SemanticLabel(
        label_id="REPORTED_FAILED_ATTEMPT",
        status=LabelStatus.EXTRACTABLE,
        ontology_fit=OntologyFit.SUPPORTED_BY_EXISTING_ONTOLOGY,
        definition=(
            "The asker states, in their own words, that they tried a specific approach and it did not work: "
            "an error, a wrong result, or no effect. A question that only asks how to do something, with no "
            "attempt reported as failing, is not this label. A failed workaround is this label."
        ),
        evidence_dimension="PROBLEM_OR_NEED",
        observation_category="REPORTED_BEHAVIOUR",
        requires_subject=False,
        evidence_may_be_in_code=True,
        does_not_establish=(
            *_ALWAYS_NOT,
            "that the tool or approach tried is inadequate (SOLUTION_GAP)",
            "dissatisfaction with any solution",
        ),
    ),
    SemanticLabel(
        label_id="NEGATIVE_EVALUATION_OF_NAMED_SOLUTION",
        status=LabelStatus.EXTRACTABLE,
        ontology_fit=OntologyFit.SUPPORTED_BY_EXISTING_ONTOLOGY,
        definition=(
            "The asker states, in their own words and outside code or quoted material, a negative evaluation "
            "of a solution named in the text (a tool, library, service or product), not merely that it "
            "produced an error. Asking why a tool behaves a certain way is not an evaluation."
        ),
        evidence_dimension="SOLUTION_DISSATISFACTION",
        observation_category="STATED_OPINION",
        requires_subject=True,
        evidence_may_be_in_code=False,
        does_not_establish=(
            *_ALWAYS_NOT,
            "that the asker would switch",
            "that the complaint is representative of any population",
            "which canonical subject the named solution is (held as a verbatim string only)",
        ),
    ),
    SemanticLabel(
        label_id="SUCCESSFUL_WORKAROUND",
        status=LabelStatus.ANNOTATION_ONLY,
        ontology_fit=OntologyFit.REQUIRES_SCOPE_DECISION,
        definition="The asker states that an alternative approach they used does work.",
        evidence_dimension=None,
        observation_category="REPORTED_BEHAVIOUR",
        requires_subject=False,
        evidence_may_be_in_code=True,
        does_not_establish=(
            *_ALWAYS_NOT,
            "SOLUTION_GAP: a working workaround is evidence that a solution exists",
        ),
        blocker="whether a burdensome but working workaround bears on PROBLEM_OR_NEED is undecided",
    ),
    SemanticLabel(
        label_id="EXPLICIT_FEATURE_REQUEST",
        status=LabelStatus.ANNOTATION_ONLY,
        ontology_fit=OntologyFit.SUPPORTED_BY_EXISTING_ONTOLOGY,
        definition="The asker asks that a named tool add a capability it is stated to lack.",
        evidence_dimension="PROBLEM_OR_NEED",
        observation_category="STATED_OPINION",
        requires_subject=True,
        evidence_may_be_in_code=False,
        does_not_establish=(*_ALWAYS_NOT, "that the capability does not already exist"),
        blocker="'is there a way to' is the ordinary question form on this site; incidence is measured first",
    ),
    SemanticLabel(
        label_id="REPEATED_DIFFICULTY_SAME_AUTHOR",
        status=LabelStatus.BLOCKED,
        ontology_fit=OntologyFit.REQUIRES_SCOPE_DECISION,
        definition="The asker states that the same difficulty happens to them repeatedly.",
        evidence_dimension=None,
        observation_category="REPORTED_BEHAVIOUR",
        requires_subject=False,
        evidence_may_be_in_code=False,
        does_not_establish=_ALWAYS_NOT,
        blocker="RECURRENCE_OR_FREQUENCY was written for recurrence across observations, not one author",
    ),
    SemanticLabel(
        label_id="SWITCHING_INTENT",
        status=LabelStatus.BLOCKED,
        ontology_fit=OntologyFit.REQUIRES_TAXONOMY_EXTENSION,
        definition="The asker states an intention to replace one named solution with another.",
        evidence_dimension=None,
        observation_category="STATED_OPINION",
        requires_subject=True,
        evidence_may_be_in_code=False,
        does_not_establish=_ALWAYS_NOT,
        blocker="no dimension asks about switching; SOLUTION_DISSATISFACTION never means that they would switch",
    ),
    SemanticLabel(
        label_id="STATED_HYPOTHETICAL_PAYMENT",
        status=LabelStatus.BLOCKED,
        ontology_fit=OntologyFit.REQUIRES_TAXONOMY_EXTENSION,
        definition="The asker states they would pay for something.",
        evidence_dimension=None,
        observation_category="STATED_OPINION",
        requires_subject=False,
        evidence_may_be_in_code=False,
        does_not_establish=(
            *_ALWAYS_NOT,
            "that anyone paid or committed to pay (WILLINGNESS_TO_PAY)",
        ),
        blocker="WILLINGNESS_TO_PAY asks whether an actor paid or committed to pay; a hypothetical is neither",
    ),
    SemanticLabel(
        label_id="STATED_PAST_PAYMENT",
        status=LabelStatus.BLOCKED,
        ontology_fit=OntologyFit.REQUIRES_SCOPE_DECISION,
        definition="The asker states they paid for a named product or service.",
        evidence_dimension=None,
        observation_category="REPORTED_BEHAVIOUR",
        requires_subject=True,
        evidence_may_be_in_code=False,
        does_not_establish=(*_ALWAYS_NOT, "a verified transaction, an amount or a price"),
        blocker="whether an unidentified actor's self-report counts as 'paid', and linking it to a need (G7)",
    ),
    SemanticLabel(
        label_id="UNMET_NEED_AS_SOLUTION_GAP",
        status=LabelStatus.NOT_SAFE,
        ontology_fit=OntologyFit.NOT_SAFE_TO_REPRESENT,
        definition="A statement that no solution exists.",
        evidence_dimension=None,
        observation_category=None,
        requires_subject=False,
        evidence_may_be_in_code=False,
        does_not_establish=_ALWAYS_NOT,
        blocker="SOLUTION_GAP never means that absence of evidence of a solution is evidence of its absence",
    ),
)

PROHIBITED_INFERENCES: tuple[tuple[str, str], ...] = (
    ("asking a question", "market demand"),
    ("popularity, score or view count", "importance, market size or willingness to pay"),
    ("a tag", "a product category or the subject of a finding"),
    ("an accepted answer", "an objectively solved problem"),
    ("one asker's statement", "population frequency"),
    ("a hypothetical purchase", "actual spend"),
    ("model confidence or model agreement", "evidence reliability"),
    ("two findings from one record, or re-runs, or different models", "independent evidence"),
    ("two differently worded questions", "the same problem"),
    ("an error message containing emotional words", "a negative evaluation"),
    ("text inside a quote, a pasted issue or code", "the asker's own statement"),
)


def extractable_labels() -> tuple[SemanticLabel, ...]:
    return tuple(label for label in LABELS if label.status is LabelStatus.EXTRACTABLE)
