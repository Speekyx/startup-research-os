"""The deterministic audit, and the persistence gate frozen before the call.

Mission 1.31 §12 and §21. **No LLM judges this output.** Every check below is
arithmetic or set membership over the packet the model was given, which is the
only kind of check that can say something the model did not.

**The gate is frozen before the model runs and is not weakened afterwards.**
That is the discipline Missions 1.24 through 1.27 paid for repeatedly: a
criterion rewritten once the answer is visible was never binding.

Four audit verdicts, and the middle two are the ones worth having:

- `SUPPORTED`      -- every checkable element traces to the supplied statements.
- `UNSUPPORTED`    -- it asserts something nothing supplied establishes.
- `BOUND_EXCEEDED` -- it restates a supplied fact more strongly than the fact's
  own bound allows. The dangerous failure, because the sentence looks sourced.
- `NOT_FACTUAL`    -- hedged, definitional or procedural text with nothing to
  check. Recorded rather than silently passed, so "we found nothing to audit"
  cannot look like "we audited it".

**A term under a DENIAL is not an assertion** (audit@1.1.0). Mission 1.31's own
run was rejected by version 1.0.0 for the sentence *"No statement in the packet
establishes ... whether anyone would pay ... whether competitors already serve
this space"* -- which is the enumeration §6 and §16 require. The recorded verdict
for that run is NOT revised: §12 forbids weakening a gate after seeing the answer,
and the fix reaches the next mission rather than rescuing that one.

**The number check is the sharpest instrument here.** A model asserting scale
almost always does it with a figure, so every integer in the prose must appear in
a supplied statement or in the packet's own structural facts. `88` passes because
a statement contains it; `20 million` fails because nothing supplied it.
"""

from __future__ import annotations

import enum
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .dimensions import EvidenceDimension
from .guards import _asserted as _term_is_asserted
from .guards import check_no_validation_language, check_statement
from .packet import OpportunityEvidencePacket

__all__ = [
    "PERSISTENCE_GATE_VERSION",
    "AUDIT_VERSION",
    "EXTERNAL_KNOWLEDGE_MARKERS",
    "StatementSupport",
    "FieldAudit",
    "SynthesisAudit",
    "audit_synthesis",
    "PersistenceDecision",
    "evaluate_persistence",
]

PERSISTENCE_GATE_VERSION = "opportunity-synthesis-persistence-gate@1.0.0"
AUDIT_VERSION = "opportunity-synthesis-audit@1.1.0"

#: §7. World-knowledge tokens a model reaches for when it stops reading the
#: packet. Each is permitted only if a supplied statement actually contains it,
#: so the list is not a ban on words -- it is a ban on words nobody supplied.
EXTERNAL_KNOWLEDGE_MARKERS: tuple[str, ...] = (
    "kubernetes",
    "podman",
    "containerd",
    "desktop",
    "enterprise",
    "enterprises",
    "vendor",
    "vendors",
    "competitor",
    "competitors",
    "rival",
    "subscription",
    "license",
    "licence",
    "devops",
    "microservices",
    "orchestration",
    "security",
    "networking",
    "deployment",
    "popular",
    "popularity",
    "widely",
    "ubiquitous",
    "industry",
)

#: Structural facts about the packet that the model may legitimately restate as
#: numbers even though no claim statement contains them.
_STRUCTURAL_NUMBER_FIELDS = ("size", "families", "supported", "unsupported")

_PROSE_FIELDS = (
    "observed_need",
    "candidate_intervention_class",
    "hypothesis_statement",
    "evidence_bound_reasoning_summary",
    "target_actor_if_supported",
)


class StatementSupport(enum.Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    BOUND_EXCEEDED = "BOUND_EXCEEDED"
    NOT_FACTUAL = "NOT_FACTUAL"


@dataclass(frozen=True)
class FieldAudit:
    field_name: str
    verdict: StatementSupport
    findings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SynthesisAudit:
    audit_version: str
    fields: tuple[FieldAudit, ...]

    @property
    def failed(self) -> tuple[FieldAudit, ...]:
        return tuple(
            f
            for f in self.fields
            if f.verdict in (StatementSupport.UNSUPPORTED, StatementSupport.BOUND_EXCEEDED)
        )

    @property
    def accepted(self) -> bool:
        return not self.failed


def _string_list(value: object) -> tuple[str, ...]:
    """A list field from untyped provider JSON, or an empty tuple.

    The output arrives from a provider, so a field that should be a list may be
    a string, a number or missing. Returning empty for all of those lets the
    gate refuse on what the output SAYS rather than crash on its shape.
    """
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _numbers(text: str) -> set[str]:
    """Integers, with separators stripped so `20,000` and `20000` compare equal."""
    return {match.replace(",", "").replace(" ", "") for match in re.findall(r"\d[\d,]*", text)}


def audit_synthesis(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
) -> SynthesisAudit:
    """Audit the model's prose against what it was actually given."""
    supplied_text = " ".join(claim_statements.values())
    supplied_tokens = _tokens(supplied_text)
    supplied_numbers = _numbers(supplied_text) | {
        str(packet.size),
        str(len(packet.source_families)),
        str(len(packet.counting_dimensions)),
        str(len(packet.dimensions)),
    }
    supported_dimensions = frozenset(
        d
        for d in EvidenceDimension
        if d.value in set(_string_list(output.get("supported_dimensions")))
    )

    audits: list[FieldAudit] = []
    for name in _PROSE_FIELDS:
        text = str(output.get(name) or "")
        findings: list[str] = []
        verdict = StatementSupport.SUPPORTED

        if not text.strip() or text.strip() == "UNKNOWN_NOT_SUPPORTED":
            audits.append(FieldAudit(name, StatementSupport.NOT_FACTUAL))
            continue

        # -- numbers the packet never supplied ----------------------------
        for number in sorted(_numbers(text) - supplied_numbers):
            findings.append(
                f"the number {number} appears in no supplied statement and in no "
                "structural fact about the packet"
            )
            verdict = StatementSupport.UNSUPPORTED

        # -- world knowledge the packet never supplied --------------------
        text_tokens = _tokens(text)
        for marker in EXTERNAL_KNOWLEDGE_MARKERS:
            if (
                marker in text_tokens
                and marker not in supplied_tokens
                # Added in audit@1.1.0. Naming a thing the packet does NOT
                # establish is the enumeration §6 requires, not an import of
                # prior knowledge.
                and _term_is_asserted(text, marker)
            ):
                findings.append(
                    f"{marker!r} appears in no supplied statement; prior knowledge is "
                    "not available as factual support (§7)"
                )
                verdict = StatementSupport.UNSUPPORTED

        # -- commercial vocabulary without the dimension ------------------
        for violation in check_statement(text, supported_dimensions):
            findings.append(violation.message)
            verdict = StatementSupport.BOUND_EXCEEDED

        # -- validation vocabulary ----------------------------------------
        for violation in check_no_validation_language(text):
            findings.append(violation.message)
            verdict = StatementSupport.BOUND_EXCEEDED

        audits.append(FieldAudit(name, verdict, tuple(findings)))

    return SynthesisAudit(audit_version=AUDIT_VERSION, fields=tuple(audits))


@dataclass(frozen=True)
class PersistenceDecision:
    """Whether the output may become an Opportunity, and every reason it may not."""

    persist: bool
    gate_version: str
    refusal_reasons: tuple[str, ...] = ()
    audit: SynthesisAudit | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)


def evaluate_persistence(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    mandatory_unsupported: Sequence[EvidenceDimension],
) -> PersistenceDecision:
    """The gate, frozen before the model ran.

    Every condition is evaluated and every failure is returned. A caller told
    only the first would fix it and be refused again -- the lesson ADR-033's four
    gates recorded, applied to output validation.
    """
    reasons: list[str] = []
    notes: list[str] = []

    decision = str(output.get("decision") or "")
    if decision == "INSUFFICIENT_EVIDENCE":
        return PersistenceDecision(
            persist=False,
            gate_version=PERSISTENCE_GATE_VERSION,
            refusal_reasons=(
                "the model answered INSUFFICIENT_EVIDENCE. That is a correct and "
                "expected outcome, not a failure, and no Opportunity is created.",
            ),
        )
    if decision != "FORM_HYPOTHESIS":
        reasons.append(f"decision {decision!r} is not one of the two permitted values")

    # ---- every cited id must belong to this packet -----------------------
    cited_evidence = set(_string_list(output.get("supporting_evidence_ids")))
    cited_claims = set(_string_list(output.get("supporting_claim_ids")))
    stray_evidence = sorted(cited_evidence - set(packet.evidence_ids))
    stray_claims = sorted(cited_claims - set(packet.claim_ids))
    if stray_evidence:
        reasons.append(
            f"cited Evidence ids not in the packet: {stray_evidence}. A hypothesis may "
            "cite only what it was given"
        )
    if stray_claims:
        reasons.append(f"cited Claim ids not in the packet: {stray_claims}")
    if not cited_evidence:
        reasons.append("no supporting Evidence id was cited")
    if not cited_claims:
        reasons.append("no supporting Claim id was cited")

    # ---- and each cited claim must belong to a cited evidence row --------
    for evidence_id in sorted(cited_evidence):
        expected = evidence_to_claim.get(evidence_id)
        if expected is not None and expected not in cited_claims:
            reasons.append(
                f"Evidence {evidence_id} was cited without its Claim {expected}. Evidence "
                "is claim-relative, so a citation missing its claim cites nothing"
            )

    # ---- dimensions ------------------------------------------------------
    claimed_supported = set(_string_list(output.get("supported_dimensions")))
    packet_dimensions = {d.value for d in packet.dimensions}
    over_claimed = sorted(claimed_supported - packet_dimensions)
    if over_claimed:
        reasons.append(
            f"dimensions claimed as supported that this packet does not carry: {over_claimed}"
        )

    reported_unsupported = set(_string_list(output.get("unsupported_dimensions")))
    missing_report = sorted(
        d.value
        for d in mandatory_unsupported
        if d not in packet.dimensions and d.value not in reported_unsupported
    )
    if missing_report:
        reasons.append(
            f"§6 requires an explicit unsupported report for {missing_report}, and the "
            "output does not mark them. A dimension nobody mentioned reads as one nobody "
            "checked"
        )

    # ---- independence and reliability must survive verbatim in meaning ---
    independence = str(output.get("independence_status") or "").lower()
    if "unknown" not in independence:
        reasons.append(
            "independence_status does not record UNKNOWN. Two source families is "
            "diversity, never established independence"
        )
    for forbidden in ("independent source", "independent sources", "independently"):
        if forbidden in independence:
            reasons.append(
                f"independence_status contains {forbidden!r}; independence is UNKNOWN for "
                "every row in this packet"
            )
    reliability = str(output.get("reliability_status") or "").upper()
    if "NON_SCORABLE" not in reliability and "MISSING_RELIABILITY" not in reliability:
        reasons.append("reliability_status does not preserve NON_SCORABLE / MISSING_RELIABILITY")

    # ---- the prose audit --------------------------------------------------
    audit = audit_synthesis(output, packet, claim_statements)
    for failed in audit.failed:
        reasons.append(
            f"{failed.field_name} audited {failed.verdict.value}: {'; '.join(failed.findings)}"
        )
    if all(f.verdict is StatementSupport.NOT_FACTUAL for f in audit.fields):
        notes.append(
            "every prose field audited NOT_FACTUAL: there was nothing checkable in the "
            "output, which is recorded rather than read as a pass"
        )

    return PersistenceDecision(
        persist=not reasons,
        gate_version=PERSISTENCE_GATE_VERSION,
        refusal_reasons=tuple(reasons),
        audit=audit,
        notes=tuple(notes),
    )
