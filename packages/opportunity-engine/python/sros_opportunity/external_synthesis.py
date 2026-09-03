"""The gate a packet must pass before any of it can reach an external model.

Mission 1.28 §9, resting on ADR-033. **A permission to PROCESS is not a
permission to SEND**, and the opportunity layer inherits that boundary rather
than re-deciding it.

Three properties, and each exists because the obvious shortcut is wrong.

**Authorization is resolved before serialization, not before the socket.**
`serialize_packet_for_model` refuses on an unauthorized decision before it builds
any string, so a refused packet leaves no serialised evidence for a later bug to
send. That is the shape Mission 1.24 used for `classify_pair` and the reason is
identical.

**A packet is authorised whole or not at all.** If one contributing source may
not be transmitted, the packet becomes `UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS`. It
is NOT quietly trimmed to the authorised rows: a packet that dropped a source and
still called itself the packet would let a model reason over a corpus while a
report described a different one. §9 names both failures and this refuses both.

**`NOT_ASSESSED` refuses, and says so by name.** A source whose review never
answered the transmission question is not permitted and is not prohibited --
nobody looked. It blocks, and the refusal distinguishes itself from a decision
somebody made, because the registry exists to keep those apart and an operator
can act on one of them.

This module imports no provider, no Gateway and no registry. The standing is
handed in by a caller that has the registry, so an engine cannot decide its own
authorization.
"""

from __future__ import annotations

import enum
import json
from collections.abc import Mapping
from dataclasses import dataclass

from .eligibility import SourcePolicyStanding
from .packet import OpportunityEvidencePacket

__all__ = [
    "EGRESS_PROCEDURE_VERSION",
    "SynthesisAvailability",
    "ExternalSynthesisDecision",
    "authorize_packet_for_external_synthesis",
    "serialize_packet_for_model",
    "ExternalSynthesisRefusedError",
]

EGRESS_PROCEDURE_VERSION = "opportunity-external-synthesis-gate@1.0.0"


class SynthesisAvailability(enum.Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS = "UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS"


class ExternalSynthesisRefusedError(RuntimeError):
    """Raised if serialization is attempted without an authorising decision."""

    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__(
            "external synthesis is not authorised for this packet: " + "; ".join(reasons)
        )
        self.reasons = reasons


@dataclass(frozen=True)
class ExternalSynthesisDecision:
    availability: SynthesisAvailability
    packet_id: str
    refusal_reasons: tuple[str, ...]
    #: Every source examined and what was found, including the permitted ones.
    #: A decision that listed only its blockers would let a later reader think
    #: the rest were checked when they were skipped.
    per_source: tuple[tuple[str, str], ...]
    procedure_version: str = EGRESS_PROCEDURE_VERSION

    @property
    def authorized(self) -> bool:
        return self.availability is SynthesisAvailability.AVAILABLE


def authorize_packet_for_external_synthesis(
    packet: OpportunityEvidencePacket,
    standings: Mapping[str, SourcePolicyStanding],
    *,
    provider_configured: bool,
    provider_posture: str,
) -> ExternalSynthesisDecision:
    """Decide whether this packet may leave the deployment.

    Every gate is evaluated even after one refuses, each with its own reason.
    An operator told only the first failure fixes it and is refused again.
    """
    reasons: list[str] = []
    per_source: list[tuple[str, str]] = []

    for source_id in packet.source_ids:
        standing = standings.get(source_id)
        if standing is None:
            per_source.append((source_id, "NO_STANDING_SUPPLIED"))
            reasons.append(
                f"{source_id}: no policy standing supplied; uncertainty is never permission"
            )
            continue
        permitted = standing.permits_external_model_transmission
        if permitted is None:
            per_source.append((source_id, "NOT_ASSESSED"))
            reasons.append(
                f"{source_id}: external_model_transmission is NOT_ASSESSED under "
                f"{standing.use_profile_id}. Nobody has decided whether this source's "
                "material may leave the deployment, which refuses -- and is an open "
                "question an operator can close, not a prohibition."
            )
        elif not permitted:
            per_source.append((source_id, "REFUSED"))
            reasons.append(
                f"{source_id}: external_model_transmission is refused under "
                f"{standing.use_profile_id}: {standing.basis}"
            )
        else:
            per_source.append((source_id, "PERMITTED"))

    if provider_posture != "APPROVED":
        reasons.append(
            f"provider posture is {provider_posture!r}, not APPROVED; a provider is "
            "approved on its own contract text and never on preference"
        )
    if not provider_configured:
        reasons.append("PROVIDER_NOT_CONFIGURED: no approved provider is configured")

    availability = (
        SynthesisAvailability.AVAILABLE
        if not reasons
        else SynthesisAvailability.UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS
    )
    return ExternalSynthesisDecision(
        availability=availability,
        packet_id=packet.packet_id,
        refusal_reasons=tuple(reasons),
        per_source=tuple(per_source),
    )


def serialize_packet_for_model(
    packet: OpportunityEvidencePacket,
    decision: ExternalSynthesisDecision,
    claim_statements: Mapping[str, str],
) -> str:
    """The packet as text for a model, or a refusal.

    The authorization check is the FIRST statement, before any claim statement is
    read out of the mapping. A refused packet therefore produces no string
    containing source-derived text at all.
    """
    if not decision.authorized:
        raise ExternalSynthesisRefusedError(decision.refusal_reasons)
    if decision.packet_id != packet.packet_id:
        raise ExternalSynthesisRefusedError(
            (
                f"the decision authorises packet {decision.packet_id} but this is "
                f"{packet.packet_id}; an authorization is not transferable between packets",
            )
        )

    missing = [cid for cid in packet.claim_ids if cid not in claim_statements]
    if missing:
        raise ExternalSynthesisRefusedError(
            (
                f"{len(missing)} claim statements were not supplied. A packet "
                "serialised without them would be silently incomplete, which §9 "
                "forbids as explicitly as it forbids a leak.",
            )
        )

    return json.dumps(
        {
            "packet_id": packet.packet_id,
            "subject": packet.subject_label,
            "procedures": packet.procedures,
            "source_families": list(packet.source_families),
            "dimensions": sorted(d.value for d in packet.dimensions),
            "dimension_bounds": list(packet.dimension_bounds),
            "independence": packet.independence_summary(),
            "claims": [
                {"claim_id": cid, "statement": claim_statements[cid]} for cid in packet.claim_ids
            ],
            "evidence_ids": list(packet.evidence_ids),
        },
        indent=2,
        sort_keys=True,
    )
