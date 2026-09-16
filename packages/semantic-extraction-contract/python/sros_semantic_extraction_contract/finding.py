"""The extraction payload a model may return, and the deterministic validator that is the only way in.

Architecture B (Mission 1.85.3): model -> payload -> THIS validator -> a non-canonical extraction
artifact. The model writes nothing. It returns quotes, never offsets; the validator finds the quote in the
surface it recomputed from the held record, and refuses on any mismatch. A finding is not a Signal: the
Signal contract requires two distinct observations (S-1) and one record is one observation.

Every check runs even after one fails, and any failure refuses the whole extraction, so a model cannot pad
a response with a few valid findings around an invented one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from sros_contracts import SignalDerivationKind

from .labels import LABEL_SET_ID, LABEL_SET_VERSION, LABELS, LabelStatus
from .surface import MARKERS, SURFACE_ID, SURFACE_VERSION, marker_regions, surface_sha256

__all__ = [
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "DERIVATION_KIND",
    "MAX_FINDINGS",
    "ExtractionContext",
    "ExtractionState",
    "RefusalReason",
    "ValidatedExtraction",
    "ValidatedFinding",
    "ValidationReport",
    "validate_extraction",
]

CONTRACT_ID = "first-person-semantic-extraction"
CONTRACT_VERSION = "1.0.0"
# The repository's existing term for a model in the derivation path. The artifact carries it; it does not
# thereby become a Signal.
DERIVATION_KIND = SignalDerivationKind.MODEL_DERIVED.value
MAX_FINDINGS = 8
MIN_QUOTE = 8
MAX_QUOTE = 400

_PAYLOAD_KEYS = {"extraction_state", "findings"}
_FINDING_KEYS = {
    "finding_type",
    "evidence_quote",
    "evidence_occurrence",
    "subject_quote",
    "subject_occurrence",
}


class ExtractionState(StrEnum):
    FINDINGS_PRESENT = "FINDINGS_PRESENT"
    NO_FINDING_ESTABLISHED = "NO_FINDING_ESTABLISHED"
    ABSTAINED_TEXT_INSUFFICIENT = "ABSTAINED_TEXT_INSUFFICIENT"


class RefusalReason(StrEnum):
    PAYLOAD_NOT_AN_OBJECT = "PAYLOAD_NOT_AN_OBJECT"
    UNKNOWN_OR_MISSING_KEY = "UNKNOWN_OR_MISSING_KEY"
    UNKNOWN_EXTRACTION_STATE = "UNKNOWN_EXTRACTION_STATE"
    STATE_FINDINGS_MISMATCH = "STATE_FINDINGS_MISMATCH"
    TOO_MANY_FINDINGS = "TOO_MANY_FINDINGS"
    LABEL_NOT_EXTRACTABLE = "LABEL_NOT_EXTRACTABLE"
    QUOTE_INVALID = "QUOTE_INVALID"
    QUOTE_CONTAINS_MARKER = "QUOTE_CONTAINS_MARKER"
    QUOTE_NOT_IN_SURFACE = "QUOTE_NOT_IN_SURFACE"
    OCCURRENCE_INVALID = "OCCURRENCE_INVALID"
    SPAN_BEYOND_VISIBLE_TEXT = "SPAN_BEYOND_VISIBLE_TEXT"
    SPAN_IN_QUOTED_MATERIAL = "SPAN_IN_QUOTED_MATERIAL"
    SPAN_IN_CODE_NOT_PERMITTED = "SPAN_IN_CODE_NOT_PERMITTED"
    SUBJECT_REQUIRED = "SUBJECT_REQUIRED"
    SUBJECT_NOT_PERMITTED = "SUBJECT_NOT_PERMITTED"
    DUPLICATE_FINDING = "DUPLICATE_FINDING"
    SURFACE_DIGEST_MISMATCH = "SURFACE_DIGEST_MISMATCH"
    PROVENANCE_INCOMPLETE = "PROVENANCE_INCOMPLETE"


@dataclass(frozen=True)
class ExtractionContext:
    """Everything the validator knows that did NOT come from the model."""

    workspace_id: str
    normalized_record_id: str
    observation_key: str
    source_id: str
    surface: str
    expected_surface_sha256: str
    visible_length: int  # characters the model was shown; spans past it are refused
    extractor_id: str
    extractor_version: str
    prompt_id: str
    prompt_version: str
    provider: str
    model: str


@dataclass(frozen=True)
class ValidatedFinding:
    finding_id: str
    finding_type: str
    evidence_start: int
    evidence_end: int
    evidence_quote: str
    subject_start: int | None
    subject_end: int | None
    subject_quote: str | None
    evidence_dimension: str | None
    observation_category: str | None
    does_not_establish: tuple[str, ...]


@dataclass(frozen=True)
class ValidatedExtraction:
    extraction_id: str
    extraction_state: ExtractionState
    findings: tuple[ValidatedFinding, ...]
    lineage: dict[str, str]
    provenance: dict[str, str]
    derivation_kind: str = DERIVATION_KIND
    is_signal: bool = False
    independent_witness_count: int = 1


@dataclass
class ValidationReport:
    refusals: list[tuple[RefusalReason, str]] = field(default_factory=list)
    extraction: ValidatedExtraction | None = None

    @property
    def accepted(self) -> bool:
        return not self.refusals and self.extraction is not None


def _fingerprint(parts: dict[str, Any]) -> str:
    canonical = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _locate(
    surface: str, quote: Any, occurrence: Any, *, min_len: int = MIN_QUOTE, max_len: int = MAX_QUOTE
) -> tuple[int, int] | str:
    if (
        not isinstance(quote, str)
        or len(quote) < min_len
        or len(quote) > max_len
        or not quote.strip()
    ):
        return RefusalReason.QUOTE_INVALID
    if any(marker in quote for marker in MARKERS):
        return RefusalReason.QUOTE_CONTAINS_MARKER
    if not isinstance(occurrence, int) or isinstance(occurrence, bool) or occurrence < 1:
        return RefusalReason.OCCURRENCE_INVALID
    starts: list[int] = []
    index = surface.find(quote)
    while index != -1:
        starts.append(index)
        index = surface.find(quote, index + 1)
    if not starts:
        return RefusalReason.QUOTE_NOT_IN_SURFACE
    if occurrence > len(starts):
        return RefusalReason.OCCURRENCE_INVALID
    start = starts[occurrence - 1]
    return start, start + len(quote)


def _overlaps(regions: list[tuple[str, int, int]], kind: str, start: int, end: int) -> bool:
    return any(k == kind and start < b and a < end for k, a, b in regions)


def validate_extraction(payload: Any, context: ExtractionContext) -> ValidationReport:
    report = ValidationReport()
    refuse = report.refusals.append
    labels = {label.label_id: label for label in LABELS}

    for name in (
        "extractor_id",
        "extractor_version",
        "prompt_id",
        "prompt_version",
        "provider",
        "model",
    ):
        if not str(getattr(context, name)).strip():
            refuse((RefusalReason.PROVENANCE_INCOMPLETE, name))
    if surface_sha256(context.surface) != context.expected_surface_sha256:
        refuse(
            (
                RefusalReason.SURFACE_DIGEST_MISMATCH,
                "the surface changed between prompt and validation",
            )
        )

    if not isinstance(payload, dict):
        refuse((RefusalReason.PAYLOAD_NOT_AN_OBJECT, type(payload).__name__))
        return report
    if set(payload) != _PAYLOAD_KEYS:
        refuse(
            (RefusalReason.UNKNOWN_OR_MISSING_KEY, ",".join(sorted(set(payload) ^ _PAYLOAD_KEYS)))
        )
    raw_state = payload.get("extraction_state")
    state: ExtractionState | None = None
    if isinstance(raw_state, str) and raw_state in ExtractionState.__members__:
        state = ExtractionState(raw_state)
    else:
        refuse((RefusalReason.UNKNOWN_EXTRACTION_STATE, repr(raw_state)))
    raw_findings = payload.get("findings")
    if not isinstance(raw_findings, list):
        refuse((RefusalReason.UNKNOWN_OR_MISSING_KEY, "findings must be a list"))
        raw_findings = []
    if len(raw_findings) > MAX_FINDINGS:
        refuse((RefusalReason.TOO_MANY_FINDINGS, str(len(raw_findings))))
    if state is not None and (state is ExtractionState.FINDINGS_PRESENT) != bool(raw_findings):
        refuse(
            (
                RefusalReason.STATE_FINDINGS_MISMATCH,
                f"{state.value} with {len(raw_findings)} findings",
            )
        )

    lineage = {
        "workspace_id": context.workspace_id,
        "normalized_record_id": context.normalized_record_id,
        "observation_key": context.observation_key,
        "source_id": context.source_id,
    }
    provenance = {
        "contract": f"{CONTRACT_ID}@{CONTRACT_VERSION}",
        "label_set": f"{LABEL_SET_ID}@{LABEL_SET_VERSION}",
        "surface": f"{SURFACE_ID}@{SURFACE_VERSION}",
        "surface_sha256": context.expected_surface_sha256,
        "extractor": f"{context.extractor_id}@{context.extractor_version}",
        "prompt": f"{context.prompt_id}@{context.prompt_version}",
        "provider": context.provider,
        "model": context.model,
        "visible_length": str(context.visible_length),
    }
    extraction_fingerprint = _fingerprint({**lineage, **provenance})
    regions = marker_regions(context.surface)

    findings: list[ValidatedFinding] = []
    seen: set[str] = set()
    for position, raw in enumerate(raw_findings):
        where = f"findings[{position}]"
        if not isinstance(raw, dict) or set(raw) != _FINDING_KEYS:
            refuse((RefusalReason.UNKNOWN_OR_MISSING_KEY, where))
            continue
        label = labels.get(raw["finding_type"]) if isinstance(raw["finding_type"], str) else None
        if label is None or label.status is not LabelStatus.EXTRACTABLE:
            refuse((RefusalReason.LABEL_NOT_EXTRACTABLE, f"{where}: {raw['finding_type']!r}"))
            continue
        span = _locate(context.surface, raw["evidence_quote"], raw["evidence_occurrence"])
        if not isinstance(span, tuple):
            refuse((RefusalReason(span), f"{where}.evidence"))
            continue
        start, end = span
        if end > context.visible_length:
            refuse((RefusalReason.SPAN_BEYOND_VISIBLE_TEXT, where))
        if _overlaps(regions, "QUOTE", start, end):
            refuse((RefusalReason.SPAN_IN_QUOTED_MATERIAL, where))
        if not label.evidence_may_be_in_code and _overlaps(regions, "CODE", start, end):
            refuse((RefusalReason.SPAN_IN_CODE_NOT_PERMITTED, where))

        subject: tuple[int, int] | None = None
        if raw["subject_quote"] is None:
            if raw["subject_occurrence"] is not None:
                refuse((RefusalReason.OCCURRENCE_INVALID, f"{where}.subject"))
            if label.requires_subject:
                refuse((RefusalReason.SUBJECT_REQUIRED, where))
        elif not label.requires_subject:
            refuse((RefusalReason.SUBJECT_NOT_PERMITTED, where))
        else:
            located = _locate(
                context.surface,
                raw["subject_quote"],
                raw["subject_occurrence"],
                min_len=2,
                max_len=120,
            )
            if not isinstance(located, tuple):
                refuse((RefusalReason(located), f"{where}.subject"))
            else:
                subject = located
                if subject[1] > context.visible_length:
                    refuse((RefusalReason.SPAN_BEYOND_VISIBLE_TEXT, f"{where}.subject"))
                if _overlaps(regions, "QUOTE", *subject) or _overlaps(regions, "CODE", *subject):
                    refuse(
                        (RefusalReason.SPAN_IN_QUOTED_MATERIAL, f"{where}.subject outside prose")
                    )

        finding_fingerprint = _fingerprint(
            {
                "extraction": extraction_fingerprint,
                "finding_type": label.label_id,
                "evidence": [start, end],
                "subject": list(subject) if subject else None,
            }
        )
        if finding_fingerprint in seen:
            refuse((RefusalReason.DUPLICATE_FINDING, where))
            continue
        seen.add(finding_fingerprint)
        findings.append(
            ValidatedFinding(
                finding_id=finding_fingerprint,
                finding_type=label.label_id,
                evidence_start=start,
                evidence_end=end,
                evidence_quote=context.surface[start:end],
                subject_start=subject[0] if subject else None,
                subject_end=subject[1] if subject else None,
                subject_quote=context.surface[subject[0] : subject[1]] if subject else None,
                evidence_dimension=label.evidence_dimension,
                observation_category=label.observation_category,
                does_not_establish=label.does_not_establish,
            )
        )

    if not report.refusals and state is not None:
        report.extraction = ValidatedExtraction(
            extraction_id=extraction_fingerprint,
            extraction_state=state,
            findings=tuple(sorted(findings, key=lambda f: (f.evidence_start, f.finding_type))),
            lineage=lineage,
            provenance=provenance,
        )
    return report
