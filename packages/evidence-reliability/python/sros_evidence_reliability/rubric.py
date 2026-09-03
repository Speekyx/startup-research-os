"""The human reliability assessment rubric (Mission 1.42a).

Mission 1.14 defined what reliability MEANS, ADR-026 defined the SCOPE it
applies to, and `evidence-reliability-review-guide-v1.md` told a reviewer to
write the failure mode down before choosing a number. None of them defines the
step in between:

    DOCUMENTED FACTS  ->  [ nothing ]  ->  HUMAN JUDGEMENT  ->  Assessment

This module is that middle term. It is a **decision procedure**, not a scoring
function: there is no weight, no sum, no average and no mapping from any state
to any number anywhere in this file, and a test asserts it.

**It names no source.** The rubric is generic by construction, and the
package-level guard that forbids a source id here is what enforces it -- a
rubric that mentioned one publisher would be a scoring table for that publisher.
The worked example lives outside this package for exactly that reason.

Nothing here is persisted. The review states are a vocabulary for a REVIEW, not
for a row, so they are defined locally rather than added to the generated
contract enums: adding a member to a closed persisted enum is a contract change
with an ADR behind it, and no row stores one of these today.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

RUBRIC_ID = "human-reliability-assessment-rubric"
RUBRIC_VERSION = "1.0.0"

# The definition is FROZEN, quoted from `evidence-reliability-contract-v1.md` §1.
# A rubric that restated it in its own words would be a second definition.
RELIABILITY_QUESTION = "How dependable is this kind of measurement, for this kind of proposition?"

# §1. What a reliability value never answers. Restated here because a review
# procedure is where a reviewer is most likely to reach for one of them.
EXCLUDED_CONCEPTS: tuple[str, ...] = (
    "the probability that the Claim is true",
    "the reputation or prominence of the publisher",
    "whether the source is legally permitted to be used",
    "the quality or attractiveness of an Opportunity",
    "market size, demand, or commercial value",
    "whether SROS's downstream business conclusions are correct",
    "whether two Evidence rows are independent",
    "whether our extractor read the Signal correctly",
    "how directly the Evidence bears on the Claim",
    "how recently the observation was made",
)


class ReviewState(StrEnum):
    """What the held documents establish about one dimension.

    Three of these are ordered. Two are deliberately **off the order**, and that
    is the structural form of *UNKNOWN is not LOW*: a state with no rank cannot
    be interpolated, averaged, or quietly treated as the bottom of the scale.
    """

    DOCUMENTED_AND_BOUNDED = "DOCUMENTED_AND_BOUNDED"
    DOCUMENTED_WITH_UNBOUNDED_LIMITATION = "DOCUMENTED_WITH_UNBOUNDED_LIMITATION"
    PARTIALLY_DOCUMENTED = "PARTIALLY_DOCUMENTED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    CONTRADICTED = "CONTRADICTED"


ORDINAL_RANK: Mapping[ReviewState, int | None] = {
    ReviewState.DOCUMENTED_AND_BOUNDED: 3,
    ReviewState.DOCUMENTED_WITH_UNBOUNDED_LIMITATION: 2,
    ReviewState.PARTIALLY_DOCUMENTED: 1,
    # No rank. `NOT_ESTABLISHED` says the documents do not answer the question,
    # which is not a worse answer than a partial one -- it is the absence of one.
    ReviewState.NOT_ESTABLISHED: None,
    # No rank. A contradiction between authoritative documents is a review
    # blocker, not a weak position on a line.
    ReviewState.CONTRADICTED: None,
}

# The ranks ORDER the three documented states and are never arithmetic. Nothing
# in this module sums them, averages them, weights them or maps one to a
# reliability value, and a test asserts that no such operation exists.
ORDINAL_RANKS_ARE_NEVER_SUMMED = True

# The ONE state software may assert, because it is a claim about what the
# reviewed document set CONTAINS rather than a judgement about sufficiency:
# "none of the documents in this review's basis addresses this question" is
# mechanically checkable. Every other state judges whether what IS documented is
# enough, and that is the reviewer's.
SOFTWARE_ASSIGNABLE_STATES: tuple[ReviewState, ...] = (ReviewState.NOT_ESTABLISHED,)


@dataclass(frozen=True)
class Dimension:
    """One question about the measurement, answerable from retrieved documents."""

    id: str
    question: str
    why_reliability_native: str
    not_to_be_confused_with: str
    observable: Mapping[ReviewState, str]


DIMENSIONS: tuple[Dimension, ...] = (
    Dimension(
        id="MEASUREMENT_DEFINITION",
        question="Does first-party documentation define what is measured?",
        why_reliability_native=(
            "It is the precondition for the reliability question being answerable at "
            "all. If nobody has said what the number counts, there is nothing to be "
            "dependable ABOUT."
        ),
        not_to_be_confused_with=(
            "extraction confidence, which asks whether we read the published value "
            "correctly. A perfectly read value of an undefined quantity is still an "
            "undefined quantity."
        ),
        observable={
            ReviewState.DOCUMENTED_AND_BOUNDED: (
                "A retrieved first-party document defines the measurement and states "
                "what it includes and excludes."
            ),
            ReviewState.DOCUMENTED_WITH_UNBOUNDED_LIMITATION: (
                "The definition is documented and names an inclusion or exclusion "
                "whose extent the documents do not establish."
            ),
            ReviewState.PARTIALLY_DOCUMENTED: (
                "The documents define part of the measurement and are silent on a "
                "part the reviewer can name."
            ),
            ReviewState.NOT_ESTABLISHED: (
                "No document in this review's basis defines what is measured."
            ),
            ReviewState.CONTRADICTED: (
                "Two retrieved documents define the measurement differently, and the "
                "difference is not reconciled by either."
            ),
        },
    ),
    Dimension(
        id="SOURCE_SIDE_VALIDATION",
        question="What does the source itself validate before publishing the value?",
        why_reliability_native=(
            "It is the difference between a value that passed a correctness check and "
            "one that only passed a format check, which is the single most "
            "load-bearing fact in every review this repository has performed."
        ),
        not_to_be_confused_with=(
            "governance status. An APPROVED source does not validate its data more "
            "carefully than a RESTRICTED one; permission and correctness are decided "
            "by different people for different reasons."
        ),
        observable={
            ReviewState.DOCUMENTED_AND_BOUNDED: (
                "The documents state what is validated, and the validation covers the "
                "correctness of the published value."
            ),
            ReviewState.DOCUMENTED_WITH_UNBOUNDED_LIMITATION: (
                "The documents state what is validated, the validation does NOT reach "
                "correctness, and how far the published values may depart from the "
                "underlying facts is not established."
            ),
            ReviewState.PARTIALLY_DOCUMENTED: (
                "Some validation is documented and the reviewer can name a published "
                "field whose treatment is not covered."
            ),
            ReviewState.NOT_ESTABLISHED: (
                "No document in this review's basis says what, if anything, the source validates."
            ),
            ReviewState.CONTRADICTED: (
                "A documented validation rule is contradicted by another document or "
                "by observed published data."
            ),
        },
    ),
    Dimension(
        id="HISTORICAL_MUTABILITY",
        question=(
            "Can a published measurement later be corrected, amended, superseded or "
            "withdrawn, and is that practice documented?"
        ),
        why_reliability_native=(
            "It decides whether re-reading the same observation would yield the same "
            "value. A measurement that can silently change underneath a Claim is less "
            "dependable for that Claim however well defined it is."
        ),
        not_to_be_confused_with=(
            "freshness, which asks whether a Claim decays as the WORLD moves on. This "
            "asks whether the RECORD is stable. A permanently true statement about an "
            "unstable record is still resting on an unstable record."
        ),
        observable={
            ReviewState.DOCUMENTED_AND_BOUNDED: (
                "The documents state the revision practice, and state how a consumer "
                "can tell that a value has been revised."
            ),
            ReviewState.DOCUMENTED_WITH_UNBOUNDED_LIMITATION: (
                "Revision is documented as possible, and how often or how far values "
                "move is not established."
            ),
            ReviewState.PARTIALLY_DOCUMENTED: (
                "Some revision behaviour is documented and the reviewer can name a "
                "case the documents do not cover."
            ),
            ReviewState.NOT_ESTABLISHED: (
                "No document in this review's basis states whether published values "
                "may later change. An absence of documented revision is not evidence "
                "of stability."
            ),
            ReviewState.CONTRADICTED: (
                "A documented revision policy is contradicted by another document or "
                "by observed published data."
            ),
        },
    ),
    Dimension(
        id="COMPLETENESS_AND_MISSINGNESS",
        question=(
            "Are omissions, withholding, exclusions and censoring documented, and is "
            "their effect on the published subset bounded?"
        ),
        why_reliability_native=(
            "A published subset assembled by a documented rule and one assembled by an "
            "undocumented one are different measurements. Where missingness is not "
            "random, it can move a summary without moving any single value."
        ),
        not_to_be_confused_with=(
            "relevance, which asks whether the evidence bears on the Claim at all. "
            "This asks what the source left out of what it did publish."
        ),
        observable={
            ReviewState.DOCUMENTED_AND_BOUNDED: (
                "The documents state which observations are excluded and the reviewer "
                "can say what the exclusion does and does not affect."
            ),
            ReviewState.DOCUMENTED_WITH_UNBOUNDED_LIMITATION: (
                "Exclusion or withholding is documented as possible and its extent is "
                "not established."
            ),
            ReviewState.PARTIALLY_DOCUMENTED: (
                "Some exclusions are documented and the reviewer can name a class of "
                "omission the documents do not address."
            ),
            ReviewState.NOT_ESTABLISHED: (
                "No document in this review's basis addresses what is omitted from "
                "the published set."
            ),
            ReviewState.CONTRADICTED: (
                "A documented exclusion rule is contradicted by another document or by "
                "observed published data."
            ),
        },
    ),
    Dimension(
        id="SOURCE_SIDE_CHECKABILITY",
        question=(
            "Can a person go to the source and inspect the published observations "
            "this proposition rests on?"
        ),
        why_reliability_native=(
            "`claim-epistemic-semantics-v1.md` §2 makes this the test of an OBSERVED "
            "proposition. A measurement nobody outside this deployment can re-inspect "
            "is one whose failures nobody outside this deployment can find."
        ),
        not_to_be_confused_with=(
            "SROS-internal lineage. Whether OUR pipeline can recover which records fed "
            "a Signal is a precondition for reviewing at all -- its absence is a hard "
            "stop, not a low value -- while this asks what the SOURCE exposes."
        ),
        observable={
            ReviewState.DOCUMENTED_AND_BOUNDED: (
                "The source publishes the individual observations, addressably, and "
                "the documents say for how long."
            ),
            ReviewState.DOCUMENTED_WITH_UNBOUNDED_LIMITATION: (
                "The observations are inspectable and how long they remain so is not established."
            ),
            ReviewState.PARTIALLY_DOCUMENTED: (
                "The source exposes an aggregate that can be re-requested but not the "
                "individual observations behind it."
            ),
            ReviewState.NOT_ESTABLISHED: (
                "No document in this review's basis establishes what the source "
                "exposes for inspection."
            ),
            ReviewState.CONTRADICTED: (
                "Documented availability is contradicted by another document or by "
                "observed behaviour."
            ),
        },
    ),
)


@dataclass(frozen=True)
class RejectedDimension:
    """A candidate that was considered and refused, with the reason.

    Recorded rather than dropped: the reasons are the boundary between
    reliability and the other Evidence components, and a boundary nobody wrote
    down is one the next rubric version will cross.
    """

    id: str
    verdict: str
    reason: str


BELONGS_TO_OTHER_COMPONENT = "BELONGS_TO_OTHER_COMPONENT"
FOLDED_INTO_ANOTHER_DIMENSION = "FOLDED_INTO_ANOTHER_DIMENSION"
REJECTED_AS_DUPLICATE_QUESTION = "REJECTED_AS_DUPLICATE_QUESTION"
RECLASSIFIED_AS_HARD_STOP = "RECLASSIFIED_AS_HARD_STOP"

REJECTED_DIMENSIONS: tuple[RejectedDimension, ...] = (
    RejectedDimension(
        id="MEASUREMENT_TO_PROPOSITION_FIT",
        verdict=BELONGS_TO_OTHER_COMPONENT,
        reason=(
            "How directly a measurement supports a Claim is `directness`, which is "
            "already a component of `q = min(components)`. Scoring it here would make "
            "one weakness count twice. The reliability-native residue is not a "
            "gradient at all: the scope is measurement CROSSED WITH proposition, so a "
            "proposition asking more than the measurement observes is a mis-specified "
            "scope rather than a low value -- reclassified as a hard stop."
        ),
    ),
    RejectedDimension(
        id="CLASSIFICATION_DEPENDABILITY",
        verdict=FOLDED_INTO_ANOTHER_DIMENSION,
        reason=(
            "Where a proposition names a source-native class, that classification IS "
            "part of what is measured, so it is assessed on the existing dimensions in "
            "its own right rather than given a dimension of its own. A separate "
            "classification dimension would be a rubric shaped around one publisher's "
            "taxonomy, which is the TED-specific scoring table this rubric must not be."
        ),
    ),
    RejectedDimension(
        id="KNOWN_FAILURE_MODES",
        verdict=REJECTED_AS_DUPLICATE_QUESTION,
        reason=(
            "Every failure mode a reviewer finds lands under one of the accepted "
            "dimensions, so scoring it separately counts the same finding twice. It is "
            "kept as a required ENUMERATION the reviewer produces, attached to the "
            "dimension it belongs to."
        ),
    ),
    RejectedDimension(
        id="RESIDUAL_UNKNOWN",
        verdict=REJECTED_AS_DUPLICATE_QUESTION,
        reason=(
            "This is the `NOT_ESTABLISHED` state plus the materiality test, not a "
            "sixth question. Made a dimension, it would need its own states, and the "
            "state of an unknown is that it is unknown."
        ),
    ),
    RejectedDimension(
        id="REVIEWER_CONFIDENCE_FIELD",
        verdict=REJECTED_AS_DUPLICATE_QUESTION,
        reason=(
            "A separate reviewer-confidence field would be a second answer to a "
            "question the dimension profile already answers: basis completeness is "
            "READ OFF the profile rather than asked again. Two fields answering one "
            "question eventually disagree, and then a reader has to decide which is "
            "the real one."
        ),
    ),
    RejectedDimension(
        id="SOURCE_REPUTATION",
        verdict=BELONGS_TO_OTHER_COMPONENT,
        reason=(
            "It belongs to no component. A publisher's standing is not a property of a "
            "measurement, and a reliability derived from it is the per-source "
            "coefficient ADR-026 exists to prevent."
        ),
    ),
)


@dataclass(frozen=True)
class HardStop:
    """A finding that makes a numeric judgement unavailable however strong the rest.

    Each one exists because the reliability QUESTION has no answer in that
    situation -- not because the answer would be low.
    """

    id: str
    condition: str
    why: str


HARD_STOPS: tuple[HardStop, ...] = (
    HardStop(
        id="MEASUREMENT_SEMANTICS_NOT_ESTABLISHED",
        condition="`MEASUREMENT_DEFINITION` is `NOT_ESTABLISHED`.",
        why=(
            "If nothing establishes what is measured, there is no measurement for a "
            "value to be about. A low number here would assert that we know it is "
            "undependable, and we do not know anything."
        ),
    ),
    HardStop(
        id="PROPOSITION_EXCEEDS_MEASUREMENT",
        condition=("The proposition asserts something the measurement does not observe."),
        why=(
            "The scope is mis-specified, and the repair is to the proposition or the "
            "scope. A discounted reliability would let an over-reaching Claim keep "
            "standing with a smaller number attached."
        ),
    ),
    HardStop(
        id="AUTHORITATIVE_DOCUMENTS_CONTRADICT",
        condition="Any dimension is `CONTRADICTED` and the conflict is unreconciled.",
        why=(
            "A value chosen across an unreconciled contradiction turns a conflict into "
            "a number, and the number is then the only thing anyone reads."
        ),
    ),
    HardStop(
        id="SOURCE_OBSERVATIONS_NOT_RECOVERABLE",
        condition=(
            "The Evidence rows in scope cannot be traced back to the observations the "
            "source published."
        ),
        why=(
            "The review would have no object. This is about OUR lineage, and it is a "
            "precondition rather than a dimension."
        ),
    ),
)


class NumericJudgementGate(StrEnum):
    """The outcome of the review. Chosen by the reviewer, never computed."""

    NUMERIC_JUDGEMENT_PERMITTED = "NUMERIC_JUDGEMENT_PERMITTED"
    NUMERIC_JUDGEMENT_NOT_JUSTIFIED = "NUMERIC_JUDGEMENT_NOT_JUSTIFIED"
    DOCUMENTATION_INSUFFICIENT = "DOCUMENTATION_INSUFFICIENT"
    REVIEW_BLOCKED_BY_CONTRADICTION = "REVIEW_BLOCKED_BY_CONTRADICTION"
    REVIEWER_DISAGREEMENT_UNRESOLVED = "REVIEWER_DISAGREEMENT_UNRESOLVED"


# A gate outcome other than PERMITTED is a complete review. The scope keeps no
# assessment, the resolver keeps returning NO_APPLICABLE_ASSESSMENT, and the
# Evidence stays NON_SCORABLE -- the designed behaviour, not a gap.
NUMERIC_JUDGEMENT_IS_NEVER_REQUIRED = True


@dataclass(frozen=True)
class MaterialUnknown:
    """The register entry for one thing the documents do not establish."""

    dimension_id: str
    what_is_not_established: str
    # Answered by the reviewer. Software prepares the question and never the answer.
    could_resolution_change_the_assessment: str | None = None


MATERIAL_UNKNOWN_DEFINITION = (
    "An unknown is MATERIAL when its resolution could reasonably change the "
    "reviewer's assessment of how dependable this measurement is for this "
    "proposition. It is not material merely because something is undocumented: "
    "most things are undocumented, and a rubric that blocked on every one of them "
    "would never permit a judgement about anything."
)

MATERIALITY_QUESTION = (
    "Could resolution of this unknown reasonably alter how dependable this "
    "measurement is for this proposition?"
)

MATERIALITY_ANSWERS: tuple[str, ...] = ("YES", "NO", "UNSURE")


@dataclass(frozen=True)
class Anchor:
    """A point on `[0, 1]` defined by its ROLE IN THE ARITHMETIC.

    Defined this way because the repository anchors the absolute scale nowhere
    -- `evidence-reliability-contract-v1.md` §4 forbids threshold labels for that
    reason, and Mission 1.37 recorded that only the ORDINAL construct is defined.
    An anchor described by an adjective would be the threshold vocabulary that
    contract refuses; an anchor described by what the number DOES to
    `q = min(components)` is checkable.
    """

    value: float
    means: str
    justified_when: str


ANCHORS: tuple[Anchor, ...] = (
    Anchor(
        value=1.0,
        means=(
            "Reliability imposes no limit on this Evidence. In `q = "
            "min(components)`, this value can never be the limiting component, so the "
            "Evidence is bounded only by relevance, directness, extraction confidence "
            "and freshness."
        ),
        justified_when=(
            "Every dimension is `DOCUMENTED_AND_BOUNDED` and no material unknown "
            "remains. Reviewers should expect this to be close to unreachable in "
            "practice, and that is the point rather than a defect."
        ),
    ),
    Anchor(
        value=0.0,
        means=(
            "The measurement cannot dependably support this proposition. `q` becomes "
            "0 and the Evidence contributes nothing."
        ),
        justified_when=(
            "The reviewer has established a failure mode that defeats the proposition, "
            "and can name it. **This is a positive finding and is not the same as "
            "having no assessment**: absence means nobody judged, and 0.0 means "
            "somebody judged and found the measurement unable to bear the weight."
        ),
    ),
)

# §9. There are none, deliberately. An intermediate anchor would have to be
# invented, and inventing one is replacing arbitrary numbers with different
# arbitrary numbers -- which is the thing this rubric exists to stop.
INTERMEDIATE_ANCHORS: tuple[Anchor, ...] = ()

SCALE_STRATEGY = "KEEP_NUMERIC_FIELD_BUT_REQUIRE_ORDINAL_REVIEW_PROFILE_FIRST"


class ReviewAgreement(StrEnum):
    """How two human reviews of one scope relate. Semantics only; not persisted."""

    AGREEMENT = "AGREEMENT"
    DISAGREEMENT_OPEN = "DISAGREEMENT_OPEN"
    ADJUDICATED = "ADJUDICATED"
    IRRECONCILABLE = "IRRECONCILABLE"


# Averaging two reviews is forbidden and always will be: the mean of two
# judgements is a judgement nobody made and nobody can be asked about.
DISAGREEMENT_IS_NEVER_AVERAGED = True

MODEL_MAY: tuple[str, ...] = (
    "retrieve and organise the first-party documents",
    "extract factual findings and quote them with their section references",
    "assert `NOT_ESTABLISHED` where no document in the basis addresses a question",
    "enumerate candidate failure modes for the reviewer to accept or reject",
    "prepare a worksheet with every judgement field blank",
)

MODEL_MAY_NOT: tuple[str, ...] = (
    "assign any review state other than `NOT_ESTABLISHED`",
    "answer whether an unknown is material",
    "answer the numeric-judgement gate",
    "choose a reliability value, a range, or an anchored state",
    "supply or infer a reviewer identity",
    "adjudicate a disagreement between reviewers",
)


class FilledBy(StrEnum):
    SOFTWARE_FACT = "SOFTWARE_FACT"
    REVIEWER_JUDGEMENT = "REVIEWER_JUDGEMENT"


@dataclass(frozen=True)
class WorksheetField:
    id: str
    prompt: str
    filled_by: FilledBy


WORKSHEET_SCHEMA: tuple[WorksheetField, ...] = (
    WorksheetField("scope", "The exact five-part reliability scope.", FilledBy.SOFTWARE_FACT),
    WorksheetField(
        "measurement",
        "What the source publishes, as its documents define it.",
        FilledBy.SOFTWARE_FACT,
    ),
    WorksheetField(
        "proposition", "What the Claim asserts, in its own wording.", FilledBy.SOFTWARE_FACT
    ),
    WorksheetField(
        "documentary_basis",
        "The retrieved documents and their findings.",
        FilledBy.SOFTWARE_FACT,
    ),
    WorksheetField(
        "dimension_findings",
        "The factual findings under each dimension, quoted from those documents.",
        FilledBy.SOFTWARE_FACT,
    ),
    WorksheetField(
        "dimension_states",
        "The review state you assign to each dimension.",
        FilledBy.REVIEWER_JUDGEMENT,
    ),
    WorksheetField(
        "material_unknowns",
        "For each thing the documents do not establish: is it material?",
        FilledBy.REVIEWER_JUDGEMENT,
    ),
    WorksheetField(
        "hard_stops_triggered",
        "Which hard stops, if any, you find to be triggered.",
        FilledBy.REVIEWER_JUDGEMENT,
    ),
    WorksheetField(
        "numeric_judgement_gate",
        "Is a numeric reliability judgement justified for this scope?",
        FilledBy.REVIEWER_JUDGEMENT,
    ),
    WorksheetField(
        "reliability",
        "Only if the gate is PERMITTED: the value on [0.0, 1.0].",
        FilledBy.REVIEWER_JUDGEMENT,
    ),
    WorksheetField("rationale", "Why, against the profile above.", FilledBy.REVIEWER_JUDGEMENT),
    WorksheetField(
        "stated_limitation", "What the value is discounted for.", FilledBy.REVIEWER_JUDGEMENT
    ),
    WorksheetField(
        "reviewed_by", "Who is accountable for this judgement.", FilledBy.REVIEWER_JUDGEMENT
    ),
    WorksheetField("reviewed_at", "When the judgement was made.", FilledBy.REVIEWER_JUDGEMENT),
)

# §17. What a second reviewer needs in order to follow the first one's reasoning.
# Agreement is not required; traceability is.
REPRODUCIBILITY_REQUIREMENTS: tuple[str, ...] = (
    "the exact five-part scope",
    "the rubric id and version the review was performed under",
    "the documentary basis, each document with its section reference and retrieval date",
    "the review state assigned to every dimension",
    "every material unknown, with the reviewer's materiality answer",
    "the numeric-judgement gate outcome",
    "the rationale and the stated limitation",
    "the reviewer's identity",
)


def blank_reviewer_fields() -> dict[str, None]:
    """Every field this rubric refuses to fill in, as an explicit object.

    Returned as one mapping so that a caller can see there is no other slot for
    a judgement, and so that a test can assert every one of them is `None`.
    """
    return {
        field.id: None
        for field in WORKSHEET_SCHEMA
        if field.filled_by is FilledBy.REVIEWER_JUDGEMENT
    }
