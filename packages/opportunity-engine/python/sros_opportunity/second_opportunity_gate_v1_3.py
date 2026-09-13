"""The second-Opportunity output gate v1.3.0: one inflection policy, and a source's name is not a fact.

Mission 1.84.11. The operator's decision, verbatim as data in `OPERATOR_DECISION_V1_3`: repair the
inflection asymmetry gate v1.2.0's diagnostic replay found, decide that a source name, publisher
name, registry display label or provenance label is NOT factual support because a domain word occurs
inside it, and keep everything else. **v1.1.0 and v1.2.0 are not touched**: `assertion_context.py`
and `second_opportunity_gate_v1_2.py` are byte-identical to the v1.2.0 freeze, and the modules
v1.0.0 and v1.1.0 run on are byte-identical to bb0f50a, so every historical verdict still resolves
against the code that produced it.

This module composes the successor beside them:

* the same v1.1.0 schema validation, first, through the same validator;
* `opportunity-synthesis-persistence-gate@1.3.0` over `opportunity-synthesis-audit@1.4.0`, where
  every lexical comparison goes through one inflection function on both sides and the supplied
  statements are split into what a source REPORTED and what it is CALLED;
* v1.2.0's field policy, forbidden concepts, classification dispositions and trusted context,
  imported unchanged;
* the v1.0.0 checks on confidence, next evidence and statement classifications, unchanged.

**Source metadata is an explicit channel, as trusted context is.** `evaluate_second_opportunity_
output_v1_3` requires a `SourceMetadataContext`, which `build_source_metadata_context` derives from
registry entries (a source's identifier, its canonical name, its datasets), each label with the
document it came from. Nothing reads a label out of an answer or out of a prompt.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .assertion_audit_v1_3 import (
    ASSERTION_AUDIT_VERSION_V1_4,
    ASSERTION_GUARD_VERSION_V1_4,
    DISJUNCTION_POLICY_VERSION,
    PERSISTENCE_GATE_VERSION_V1_3,
    evaluate_persistence_v1_3,
)
from .assertion_context import TrustedContext
from .dimensions import EvidenceDimension
from .lexical_inflection import LEXICAL_INFLECTION_POLICY_VERSION
from .packet import OpportunityEvidencePacket
from .schema_validation import schema_violations
from .second_opportunity import (
    CONFIDENCE_CLASSIFICATIONS,
    PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
)
from .second_opportunity_gate_v1_2 import (
    CLASSIFICATION_DISPOSITIONS,
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
    SECOND_OPPORTUNITY_FIELD_POLICY_VERSION,
    TRUSTED_CONTEXT_VERSION,
)
from .support_origin import (
    SUPPORT_UNIVERSE_VERSION_V2,
    SourceMetadataContext,
    SourceMetadataLabel,
    SourceMetadataLabelKind,
    build_typed_support_universe,
)
from .synthesis import MANDATORY_UNSUPPORTED_REPORT
from .validation import PersistenceDecision

__all__ = [
    "SECOND_OPPORTUNITY_GATE_VERSION_V1_3",
    "SOURCE_METADATA_CONTEXT_VERSION",
    "OPERATOR_DECISION_V1_3",
    "SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION",
    "COMPONENT_VERSIONS_V1_3",
    "source_metadata_labels",
    "build_source_metadata_context",
    "evaluate_second_opportunity_output_v1_3",
]

SECOND_OPPORTUNITY_GATE_VERSION_V1_3 = "second-opportunity-output-gate@1.3.0"
SOURCE_METADATA_CONTEXT_VERSION = "second-opportunity-source-metadata@1.0.0"

#: §0, as the operator decided it. Carried as data so a record can be checked against it.
OPERATOR_DECISION_V1_3: tuple[str, ...] = (
    "FIX_SYMMETRIC_INFLECTION_NORMALIZATION = true",
    "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false",
    "SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = true",
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_PROMPT_V1_2_0_UNCHANGED",
    "KEEP_HISTORICAL_GATE_V1_1_0_UNCHANGED",
    "KEEP_FROZEN_GATE_V1_2_0_UNCHANGED",
    "DO_NOT_WHITELIST_THE_V3_ANSWER",
    "DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES",
)

#: §16. The evidence-boundary decision, first-class and independent of any answer.
SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION: dict[str, object] = {
    "decision_id": "SOURCE-METADATA-EVIDENCE-BOUNDARY-V1",
    "SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT": False,
    "SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS": True,
    "decision_owner": "OPERATOR",
    "decision_type": "EVIDENCE_BOUNDARY",
    "mathematically_derived": False,
    "reason": (
        "provenance metadata identifies where data came from; it does not establish domain facts "
        "through accidental lexical overlap"
    ),
    "metadata_is": [
        "publisher name",
        "source name",
        "registry display name",
        "dataset title",
        "provider label",
        "provenance label",
    ],
    "metadata_may_support": [
        "a statement about provenance itself, naming the source by its whole label",
    ],
    "metadata_may_not_support": [
        "a domain proposition, through any word inside a label",
        "a number, through any figure inside a label",
        "a forbidden concept, through any phrase inside a label",
    ],
    "moved_into_packet_structural_facts": False,
    "independent_of_any_answer": True,
}

#: Every versioned component the v1.3.0 gate is made of.
COMPONENT_VERSIONS_V1_3: dict[str, str] = {
    "gate": SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
    "output_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    "persistence_gate": PERSISTENCE_GATE_VERSION_V1_3,
    "audit": ASSERTION_AUDIT_VERSION_V1_4,
    "claim_guard": ASSERTION_GUARD_VERSION_V1_4,
    "field_context_policy": SECOND_OPPORTUNITY_FIELD_POLICY_VERSION,
    "support_universe": SUPPORT_UNIVERSE_VERSION_V2,
    "trusted_context": TRUSTED_CONTEXT_VERSION,
    "source_metadata": SOURCE_METADATA_CONTEXT_VERSION,
    "lexical_inflection": LEXICAL_INFLECTION_POLICY_VERSION,
    "observed_statement_disjunction": DISJUNCTION_POLICY_VERSION,
}

_QUALIFIER = re.compile(r"\s*\([^()]*\)\s*$")


def source_metadata_labels(
    source_id: str,
    canonical_name: str,
    datasets: Sequence[Mapping[str, object]],
    provenance: str,
) -> tuple[SourceMetadataLabel, ...]:
    """Every name one registry entry gives a source, typed, each with where it came from.

    A canonical name `X (Y)` also yields `X`: the parenthetical is a qualifier the registry adds,
    and the source is still named by `X` alone. Nothing is abbreviated or guessed.
    """
    candidates: list[tuple[SourceMetadataLabelKind, str, str]] = [
        (SourceMetadataLabelKind.PROVENANCE_LABEL, source_id, "the registry's source identifier"),
        (SourceMetadataLabelKind.REGISTRY_DISPLAY_NAME, canonical_name, "canonical_name"),
    ]
    short = _QUALIFIER.sub("", canonical_name).strip()
    if short and short != canonical_name.strip():
        candidates.append(
            (SourceMetadataLabelKind.SOURCE_NAME, short, "canonical_name without its qualifier")
        )
    for dataset in datasets:
        resource = str(dataset.get("resource_id") or "").strip()
        title = str(dataset.get("name") or "").strip()
        if resource:
            candidates.append(
                (SourceMetadataLabelKind.PROVENANCE_LABEL, resource, "a dataset's resource_id")
            )
        if title:
            candidates.append((SourceMetadataLabelKind.DATASET_TITLE, title, "a dataset's name"))
    labels: list[SourceMetadataLabel] = []
    seen: set[str] = set()
    for kind, text, field in candidates:
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        labels.append(
            SourceMetadataLabel(
                label_id=f"{source_id}:{kind.value}:{len(labels)}",
                source_id=source_id,
                kind=kind,
                text=text,
                provenance=f"{provenance}: {field}",
            )
        )
    return tuple(labels)


def build_source_metadata_context(
    entries: Sequence[Mapping[str, object]],
) -> SourceMetadataContext:
    """The metadata channel, from registry entries: `source_id`, `canonical_name`, `datasets`
    (each with `resource_id` and `name`) and `provenance`, the document the entry was read from."""
    labels: list[SourceMetadataLabel] = []
    for entry in entries:
        datasets = entry.get("datasets") or []
        labels += source_metadata_labels(
            str(entry["source_id"]),
            str(entry["canonical_name"]),
            [d for d in datasets if isinstance(d, Mapping)] if isinstance(datasets, list) else [],
            str(entry["provenance"]),
        )
    return SourceMetadataContext(version=SOURCE_METADATA_CONTEXT_VERSION, labels=tuple(labels))


def evaluate_second_opportunity_output_v1_3(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    trusted_context: TrustedContext,
    source_metadata: SourceMetadataContext,
    mandatory_unsupported: Sequence[EvidenceDimension] = MANDATORY_UNSUPPORTED_REPORT,
) -> PersistenceDecision:
    """The v1.3.0 gate. Both channels are required: there is no default trusted context and no
    default metadata, because a default is where a label would quietly become content.

    Structure first, through the v1.1.0 validator, and the semantic gate still runs, so a caller
    learns every reason at once. Then the persistence gate v1.3.0 with its audit, then v1.0.0's
    checks on the three fields that version added.
    """
    structural = schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    universe = build_typed_support_universe(
        packet, claim_statements, trusted_context, source_metadata
    )
    decision = evaluate_persistence_v1_3(
        output,
        universe,
        evidence_to_claim,
        mandatory_unsupported,
        policy=SECOND_OPPORTUNITY_FIELD_POLICY,
        concepts=FORBIDDEN_CONCEPTS_V1_2,
        markers=PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
        label_dispositions=CLASSIFICATION_DISPOSITIONS,
    )
    reasons = [
        *(f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1}: {v}" for v in structural),
        *decision.refusal_reasons,
    ]
    if str(output.get("decision") or "") != "INSUFFICIENT_EVIDENCE":
        classification = str(output.get("confidence_classification") or "")
        if classification not in CONFIDENCE_CLASSIFICATIONS:
            reasons.append(
                f"confidence_classification is {classification!r}; the only permitted value is "
                "EXPLORATORY, and a number here would be a probability nobody calibrated"
            )
        recommended = output.get("recommended_next_evidence")
        if not isinstance(recommended, list) or not recommended:
            reasons.append(
                "recommended_next_evidence is empty. An exploratory hypothesis that names nothing "
                "to observe next is not exploratory, it is finished"
            )
        classifications = output.get("statement_classifications")
        if not isinstance(classifications, list) or not classifications:
            reasons.append(
                "statement_classifications is empty; every substantive statement is one of three"
            )
        else:
            kinds = {
                str(item.get("classification"))
                for item in classifications
                if isinstance(item, Mapping)
            }
            if kinds - set(CLASSIFICATION_DISPOSITIONS):
                reasons.append(f"statement_classifications carries unknown kinds: {sorted(kinds)}")
            if "HYPOTHESIS_TO_VALIDATE" not in kinds and "UNKNOWN_REQUIRES_EVIDENCE" not in kinds:
                reasons.append(
                    "every statement is classified as observed. A packet establishing three "
                    "dimensions and no problem, intervention or willingness to pay leaves "
                    "something unknown, and an output that finds nothing unknown has stopped "
                    "reading"
                )
    return PersistenceDecision(
        persist=not reasons,
        gate_version=SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
        refusal_reasons=tuple(reasons),
        audit=decision.audit,
        notes=decision.notes,
    )
