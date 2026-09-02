"""Semantic problem equivalence over community questions.

Mission 1.24, from the design in `semantic-problem-equivalence-v1.md`.

The package is deliberately narrow: it generates candidates, holds a versioned
rubric, builds a prompt whose regions stay separated, classifies through the LLM
Gateway, and evaluates the result against human labels. It persists nothing,
opens no socket, and names no provider.
"""

from .batch import (
    BATCH_SELECTION_VERSION,
    ReviewBatch,
    ReviewItem,
    select_review_batch,
)
from .candidates import (
    CANDIDATE_GENERATOR_VERSION,
    CandidatePair,
    CandidateSet,
    QuestionObservation,
    generate_candidates,
)
from .classifier import (
    CLASSIFIER_TASK,
    SEMANTIC_TIER,
    ClassificationRefusedError,
    EquivalenceClassification,
    ExternalInferenceAuthorization,
    classify_pair,
)
from .evaluation import (
    ACCEPTANCE_CRITERIA,
    HOLDOUT_EXCLUSIONS,
    SPLIT_SEED,
    V1_ACCEPTANCE,
    V2_ACCEPTANCE,
    AcceptanceCriterion,
    EvaluationResult,
    HumanDecision,
    HumanLabel,
    LabelSet,
    Split,
    assign_split,
    evaluate,
)
from .prompt import (
    EQUIVALENCE_PROMPT,
    OUTPUT_SCHEMA,
    PROMPT_ID,
    PROMPT_VERSION,
    QuestionForPrompt,
    render_equivalence_prompt,
)
from .rubric import (
    GRANULARITY,
    INSUFFICIENT_ALONE,
    RUBRIC_TEXT,
    RUBRIC_VERSION,
    WORKED_EXAMPLES,
    EquivalenceDecision,
    ReasonCode,
    WorkedExample,
)

__all__ = [
    "BATCH_SELECTION_VERSION",
    "CANDIDATE_GENERATOR_VERSION",
    "CLASSIFIER_TASK",
    "EQUIVALENCE_PROMPT",
    "GRANULARITY",
    "HOLDOUT_EXCLUSIONS",
    "INSUFFICIENT_ALONE",
    "OUTPUT_SCHEMA",
    "PROMPT_ID",
    "PROMPT_VERSION",
    "RUBRIC_TEXT",
    "RUBRIC_VERSION",
    "SEMANTIC_TIER",
    "SPLIT_SEED",
    "ACCEPTANCE_CRITERIA",
    "V1_ACCEPTANCE",
    "V2_ACCEPTANCE",
    "WORKED_EXAMPLES",
    "AcceptanceCriterion",
    "CandidatePair",
    "CandidateSet",
    "ClassificationRefusedError",
    "EquivalenceClassification",
    "EquivalenceDecision",
    "EvaluationResult",
    "ExternalInferenceAuthorization",
    "HumanDecision",
    "HumanLabel",
    "LabelSet",
    "QuestionForPrompt",
    "QuestionObservation",
    "ReasonCode",
    "ReviewBatch",
    "ReviewItem",
    "Split",
    "WorkedExample",
    "assign_split",
    "classify_pair",
    "evaluate",
    "generate_candidates",
    "render_equivalence_prompt",
    "select_review_batch",
]
