"""The Claim / Evidence interpretation contract for Startup Research OS.

`docs/data/claim-evidence-interpretation-contract-v1.md`,
`docs/data/claim-epistemic-semantics-v1.md`,
`docs/data/signal-to-evidence-semantics-v1.md`, ADR-024.

**This package contains no interpreter.** It defines what a Claim is, what
Evidence is, and which interpretations are permitted. No Claim, ClaimRevision or
Evidence row exists.

It is the model package the way `sros_signal_model` is: imported by whatever
implements interpretation, and not a runtime dependency of a service until one
exists.
"""

from __future__ import annotations

from .convergence import (
    CONVERGENCE_CONTRACTS,
    ObservationOverlap,
    PropositionConvergenceContract,
    QualificationOutcome,
    SourceBoundary,
    contract_for,
    convergent_proposition_key,
    distinct_witnesses,
    identity_facts,
    overlap_between,
    qualify,
    witness_facts,
    witness_key,
)
from .model import (
    AUTOMATED_ORIGINS,
    INTERPRETIVE_VOCABULARY,
    ClaimDraft,
    ClaimInterpretation,
    ClaimRefusal,
    ClaimRefusedError,
    EvidenceDraft,
    build_claim,
    canonical_json,
    proposition_key,
    requires_evidence,
)

__all__ = [
    "CONVERGENCE_CONTRACTS",
    "ObservationOverlap",
    "PropositionConvergenceContract",
    "QualificationOutcome",
    "SourceBoundary",
    "contract_for",
    "convergent_proposition_key",
    "distinct_witnesses",
    "identity_facts",
    "overlap_between",
    "qualify",
    "witness_facts",
    "witness_key",
    "AUTOMATED_ORIGINS",
    "INTERPRETIVE_VOCABULARY",
    "ClaimDraft",
    "ClaimInterpretation",
    "ClaimRefusal",
    "ClaimRefusedError",
    "EvidenceDraft",
    "build_claim",
    "canonical_json",
    "proposition_key",
    "requires_evidence",
]
