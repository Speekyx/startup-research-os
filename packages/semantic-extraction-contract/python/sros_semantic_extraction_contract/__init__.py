"""First-person semantic extraction contract, roadmap N08-A (Mission 1.85.3).

What a model may infer from ONE authorised first-person text record, how that interpretation is
represented, and the deterministic validator it must pass. This package holds no prompt, calls no model,
opens no socket and writes nothing: `MODEL_CALLS = 0` is a property of what it imports.

A validated extraction is a non-canonical artifact. It is not a Signal (one record is one observation,
and the Signal contract requires two), not a Claim and not Evidence.
"""

from .finding import (
    CONTRACT_ID,
    CONTRACT_VERSION,
    DERIVATION_KIND,
    ExtractionContext,
    ExtractionState,
    RefusalReason,
    ValidatedExtraction,
    ValidatedFinding,
    ValidationReport,
    validate_extraction,
)
from .labels import (
    LABEL_SET_ID,
    LABEL_SET_VERSION,
    LABELS,
    PROHIBITED_INFERENCES,
    LabelStatus,
    OntologyFit,
)
from .surface import (
    SURFACE_ID,
    SURFACE_VERSION,
    marker_regions,
    render_question_surface,
    surface_sha256,
)

__all__ = [
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "DERIVATION_KIND",
    "LABELS",
    "LABEL_SET_ID",
    "LABEL_SET_VERSION",
    "PROHIBITED_INFERENCES",
    "SURFACE_ID",
    "SURFACE_VERSION",
    "ExtractionContext",
    "ExtractionState",
    "LabelStatus",
    "OntologyFit",
    "RefusalReason",
    "ValidatedExtraction",
    "ValidatedFinding",
    "ValidationReport",
    "marker_regions",
    "render_question_surface",
    "surface_sha256",
    "validate_extraction",
]
