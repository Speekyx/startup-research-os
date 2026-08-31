"""The interpretation contract: how a Signal may become a Claim, and may not.

Mission 1.13. Full specification:
`docs/data/claim-evidence-interpretation-contract-v1.md`.

**This layer interprets, and it is the first layer that does.** Everything below
it renames, reshapes or computes: a RawRecord preserves, a NormalizedRecord
reshapes, a Signal states a relation between its own inputs. A Claim is the first
artifact that asserts something *about the world*, which is why it is the first
one that can be wrong in a way arithmetic cannot catch.

Three identities are kept apart, as at every layer below:

    proposition_key   WHICH proposition. Built from the structured facts the
                      claim asserts, never from its prose and never from an
                      embedding. Two revisions may reword a claim without
                      moving it
    claim id          the row
    revision          WHICH wording, append-only. An aggregation that evaluated
                      revision N must still be able to read revision N

**Nothing here reaches a network, a model, an embedder or a database.** The
package depends on `sros_contracts` and the standard library.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from sros_contracts import (
    ClaimEvidenceRefusalReason,
    ClaimInterpretationKind,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)

__all__ = [
    "AUTOMATED_ORIGINS",
    "INTERPRETIVE_PHRASES",
    "INTERPRETIVE_TOKENS",
    "INTERPRETIVE_VOCABULARY",
    "ClaimDraft",
    "ClaimInterpretation",
    "ClaimRefusedError",
    "ClaimRefusal",
    "EvidenceDraft",
    "build_claim",
    "canonical_json",
    "proposition_key",
    "requires_evidence",
]


# Origins where a MACHINE asserted the proposition. The evidence rule is about
# these: a person may assert something and look for evidence afterwards, which
# is the ordinary research motion.
AUTOMATED_ORIGINS: frozenset[ClaimOrigin] = frozenset(
    {
        ClaimOrigin.DETERMINISTIC_EXTRACTION,
        ClaimOrigin.LLM_EXTRACTION,
        ClaimOrigin.INFERRED,
        ClaimOrigin.SYSTEM_GENERATED,
    }
)

# Vocabulary that asserts a MARKET or USER reading of a measurement. An OBSERVED
# claim restates what a source reported; the moment it says one of these it has
# asserted something the source did not, and it is INFERRED at best.
#
# **Matched as TOKENS, not substrings** (Mission 1.13.1 §10). Mission 1.13 used
# `term in statement.lower()`, which refuses `supermarket` and `marketing` for
# containing `market`, and refuses the metric id `CM.MKT.LCAP.CD` for nothing at
# all. A guard with false positives gets loosened until it stops guarding.
#
# `growth` is deliberately ABSENT. "population growth" is the name of a
# demographic quantity a source publishes, and banning it would refuse a
# faithful restatement -- the guard has to catch interpretation, not vocabulary
# that happens to sound commercial. `growth opportunity` is a phrase below.
INTERPRETIVE_TOKENS: frozenset[str] = frozenset(
    {
        "attention",
        "demand",
        "demands",
        "desire",
        "desires",
        # A source metric whose published NAME contains one of these (World
        # Bank's `FR.INR.RINR`, "Real interest rate") is restated by metric id,
        # which is the more faithful wording anyway -- the id is what the
        # proposition's fact set carries. The cost is stated, not avoided.
        "interest",
        "interests",
        "market",
        "markets",
        "momentum",
        "monetisation",
        "monetization",
        "mrr",
        "arr",
        "opportunity",
        "opportunities",
        "pain",
        "pains",
        "popular",
        "popularity",
        "revenue",
        "revenues",
        "traction",
        "trending",
    }
)

# Multi-word vocabulary, matched over the token sequence so spacing and
# punctuation between the words do not decide the outcome.
INTERPRETIVE_PHRASES: tuple[tuple[str, ...], ...] = (
    ("willingness", "to", "pay"),
    ("customers", "want"),
    ("users", "want"),
    ("product", "market", "fit"),
    ("growth", "opportunity"),
)

# Retained as the union, for callers and documents that name one list.
INTERPRETIVE_VOCABULARY: tuple[str, ...] = tuple(
    sorted(INTERPRETIVE_TOKENS | {" ".join(p) for p in INTERPRETIVE_PHRASES})
)

# Tokens are maximal runs of letters and digits. Everything else -- spaces,
# hyphens, full stops inside a metric id, punctuation -- separates. So
# `SP.POP.TOTL` is three tokens none of which is vocabulary, and `supermarket`
# is one token that is not `market`.
_TOKEN = re.compile(r"[a-z0-9]+")

# Text inside double quotes is SOURCE DATA being reported, not a claim being
# made. A GDELT term is literally arbitrary text: `market`, `demand` and `pain`
# are all real English words a news corpus contains, and a guard that refused
# `GDELT reported that the term "demand" appeared 12 more times` would refuse
# the most faithful restatement available -- the exact thing it exists to
# protect. Every template puts source-supplied values in double quotes and its
# own prose outside them.
_QUOTED = re.compile(r'"[^"]*"')


def canonical_json(payload: object) -> str:
    """Sorted keys, no incidental whitespace, stable separators."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def proposition_key(facts: Mapping[str, object]) -> str:
    """WHICH proposition, from the structured facts it asserts.

    Never from the prose: two interpreters wording the same fact differently
    have produced one claim, and a claim reworded in revision 3 is still the
    same claim. Never from an embedding either -- **D-12 is open**, and an
    identity that depended on a vector would move when the model did.

    The facts are the ones the proposition is *about*: source, metric,
    geography, period labels, term, direction. Not the research question that
    prompted it -- two sessions asking different questions that both derive
    "World Bank reported Germany's population rose in 2019" have produced the
    same claim, and should.
    """
    if not facts:
        raise ValueError(
            "a proposition key is built from the facts the claim asserts. An empty "
            "fact set identifies every proposition equally, which is no identity"
        )
    serialised = canonical_json({str(k): v for k, v in facts.items()})
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def requires_evidence(claim_type: ClaimType, origin: ClaimOrigin) -> bool:
    """Whether this claim may be stored with nothing behind it.

    `HYPOTHESIS` is exempt **by definition rather than by exception**: it is the
    category for a proposition worth testing and not yet supported, and
    requiring evidence for one would make it unusable -- which would push
    unsupported ideas into `INFERRED`, the failure the rule exists to prevent.
    """
    if claim_type is ClaimType.HYPOTHESIS:
        return False
    return origin in AUTOMATED_ORIGINS


class ClaimRefusedError(Exception):
    """No Claim exists, and no row is written."""

    def __init__(self, refusal: ClaimRefusal) -> None:
        super().__init__(f"{refusal.reason.value}: {refusal.detail}")
        self.refusal = refusal


@dataclass(frozen=True)
class ClaimRefusal:
    """Why an interpretation produced nothing. A returned value, never a row."""

    reason: ClaimEvidenceRefusalReason
    detail: str

    def to_json(self) -> dict[str, object]:
        return {"reason": self.reason.value, "detail": self.detail}


@dataclass(frozen=True)
class ClaimInterpretation:
    """Who turned Signals into a proposition, at what version, by what method."""

    interpreter_id: str
    interpreter_version: str
    kind: ClaimInterpretationKind
    model_version: str | None = None
    prompt_version: str | None = None

    def __post_init__(self) -> None:
        if not self.interpreter_id.strip() or not self.interpreter_version.strip():
            raise ClaimRefusedError(
                ClaimRefusal(
                    reason=ClaimEvidenceRefusalReason.INTERPRETER_PROVENANCE_INCOMPLETE,
                    detail=(
                        "an interpretation names its interpreter and its version. Half an "
                        "identity is a version nobody can resolve"
                    ),
                )
            )
        deterministic = self.kind is ClaimInterpretationKind.DETERMINISTIC
        if deterministic and (self.model_version or self.prompt_version):
            raise ClaimRefusedError(
                ClaimRefusal(
                    reason=ClaimEvidenceRefusalReason.INTERPRETER_PROVENANCE_INCOMPLETE,
                    detail=(
                        "a DETERMINISTIC interpretation may not carry a model or prompt "
                        "version. A template applied to structured facts did not consult "
                        "a model, and a provenance field saying otherwise would be false"
                    ),
                )
            )
        if not deterministic and not self.model_version:
            raise ClaimRefusedError(
                ClaimRefusal(
                    reason=ClaimEvidenceRefusalReason.INTERPRETER_PROVENANCE_INCOMPLETE,
                    detail=(
                        "a MODEL_DERIVED interpretation must record its model version "
                        "(llm-reasoning-rules.md §9). The model is a reasoning mechanism "
                        "and never the evidence, and which one reasoned is part of the "
                        "record"
                    ),
                )
            )

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "interpreter_id": self.interpreter_id,
            "interpreter_version": self.interpreter_version,
            "kind": self.kind.value,
        }
        if self.model_version:
            payload["model_version"] = self.model_version
        if self.prompt_version:
            payload["prompt_version"] = self.prompt_version
        return payload


@dataclass(frozen=True)
class EvidenceDraft:
    """One Signal's bearing on ONE proposition.

    Every field here is **claim-relative**, which is why none of them lives on
    the Signal: the same Signal supports one claim, contradicts another and is
    irrelevant to a third, and a Signal that carried `relevance` would have to
    carry it relative to a claim it has never heard of.
    """

    signal_id: str
    direction: EvidenceDirection
    source_id: str
    observation_category: EvidenceObservationCategory = EvidenceObservationCategory.UNCATEGORISED
    independence_state: EvidenceIndependenceState = EvidenceIndependenceState.UNKNOWN
    independence_group_id: str | None = None
    relevance: float | None = None
    directness: float | None = None
    reliability: float | None = None
    extraction_confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.signal_id.strip():
            raise ClaimRefusedError(
                ClaimRefusal(
                    reason=ClaimEvidenceRefusalReason.SIGNAL_NOT_CITED,
                    detail=(
                        "an evidence draft names the Signal it is derived from. A claim "
                        "that cannot be traced to what produced it is an assertion"
                    ),
                )
            )
        if not self.source_id.strip():
            raise ValueError(
                "evidence records which source is behind it, so Evidence Aggregation can "
                "group by origin later. It does not compute independence here"
            )
        for name in ("relevance", "directness", "reliability", "extraction_confidence"):
            value: float | None = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} {value} is outside [0,1]. Out of range is rejected rather "
                    "than clamped: it means the producer is on a different scale, and "
                    "clamping would hide that behind a plausible result "
                    "(evidence-aggregation-framework-v1.md §4)"
                )
        # Migration 0005's shape rule, restated where a draft is built: a
        # dependency on nothing and a claim of independence with a group are
        # both unreadable, and neither is an incomplete record.
        dependent = self.independence_state is EvidenceIndependenceState.KNOWN_DEPENDENT
        if dependent and self.independence_group_id is None:
            raise ValueError("KNOWN_DEPENDENT evidence must name the group it depends on")
        if not dependent and self.independence_group_id is not None:
            raise ValueError(
                "only KNOWN_DEPENDENT evidence names a group; anything else claims "
                "independence and membership at once"
            )

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "signal_id": self.signal_id,
            "direction": self.direction.value,
            "source_id": self.source_id,
            "observation_category": self.observation_category.value,
            "independence_state": self.independence_state.value,
        }
        for name in ("relevance", "directness", "reliability", "extraction_confidence"):
            value = getattr(self, name)
            if value is not None:
                payload[name] = value
        if self.independence_group_id is not None:
            payload["independence_group_id"] = self.independence_group_id
        return payload


@dataclass(frozen=True)
class ClaimDraft:
    """A Claim, its first revision and its evidence, ready to persist together.

    Unpersisted on purpose. Mission 1.13 §4 asks whether interpretation needs a
    database entity between Signal and Claim, and it does not: a draft that is
    validated and then written as claim + revision + evidence in ONE transaction
    preserves every provenance fact a persisted candidate would, and leaves no
    table of proposals nobody consumes. The same shape `SignalDraft` uses.
    """

    workspace_id: str
    claim_type: ClaimType
    temporality: ClaimTemporality
    origin: ClaimOrigin
    statement: str
    proposition_key: str
    evidence: tuple[EvidenceDraft, ...] = ()
    interpretation: ClaimInterpretation | None = None
    interpretation_confidence: float | None = None
    claim_feature: str | None = None
    opportunity_id: str | None = None
    research_session_id: str | None = None
    rationale: str | None = None
    cited_facts: Mapping[str, object] = field(default_factory=dict)

    @property
    def cited_signal_ids(self) -> tuple[str, ...]:
        return tuple(e.signal_id for e in self.evidence)

    @property
    def is_automated(self) -> bool:
        return self.origin in AUTOMATED_ORIGINS

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "workspace_id": self.workspace_id,
            "claim_type": self.claim_type.value,
            "temporality": self.temporality.value,
            "origin": self.origin.value,
            "statement": self.statement,
            "proposition_key": self.proposition_key,
            "evidence": [e.to_json() for e in self.evidence],
        }
        if self.interpretation is not None:
            payload["interpretation"] = self.interpretation.to_json()
        if self.interpretation_confidence is not None:
            payload["interpretation_confidence"] = self.interpretation_confidence
        for name in ("claim_feature", "opportunity_id", "research_session_id", "rationale"):
            value = getattr(self, name)
            if value is not None:
                payload[name] = value
        if self.cited_facts:
            payload["cited_facts"] = dict(self.cited_facts)
        return payload


def _refuse(reason: ClaimEvidenceRefusalReason, detail: str) -> ClaimRefusedError:
    return ClaimRefusedError(ClaimRefusal(reason=reason, detail=detail))


def build_claim(
    *,
    workspace_id: str,
    claim_type: ClaimType,
    temporality: ClaimTemporality,
    origin: ClaimOrigin,
    statement: str,
    facts: Mapping[str, object],
    evidence: Sequence[EvidenceDraft] = (),
    interpretation: ClaimInterpretation | None = None,
    interpretation_confidence: float | None = None,
    claim_feature: str | None = None,
    opportunity_id: str | None = None,
    research_session_id: str | None = None,
    rationale: str | None = None,
) -> ClaimDraft:
    """One ClaimDraft, or `ClaimRefusedError`.

    A `ValueError` means the CALLER is wrong -- a confidence out of range, a
    blank statement. A `ClaimRefusedError` means the INTERPRETATION is not permitted:
    it cites nothing, or it asserts more than its Signals establish.
    """
    if not workspace_id.strip():
        raise ValueError("a claim is workspace-scoped and workspace_id is never defaulted")
    if not statement.strip():
        raise ValueError("a claim nobody can read is a claim nobody can dispute")
    if interpretation_confidence is not None and not 0.0 <= interpretation_confidence <= 1.0:
        raise ValueError(f"interpretation_confidence {interpretation_confidence} is outside [0,1]")

    try:
        key = proposition_key(facts)
    except ValueError as exc:
        raise _refuse(ClaimEvidenceRefusalReason.PROPOSITION_NOT_IDENTIFIABLE, str(exc)) from exc

    automated = origin in AUTOMATED_ORIGINS

    if automated and interpretation is None:
        raise _refuse(
            ClaimEvidenceRefusalReason.INTERPRETER_PROVENANCE_INCOMPLETE,
            "an automatically generated claim names the interpreter that produced it. "
            "Without it the proposition cannot be reproduced or re-examined when the "
            "interpreter changes",
        )
    if automated and interpretation_confidence is None:
        raise _refuse(
            ClaimEvidenceRefusalReason.INTERPRETER_PROVENANCE_INCOMPLETE,
            "an automatically generated claim states how confident its interpretation "
            "was. That is confidence the SENTENCE reads the Signals correctly, and it is "
            "not an evidence strength",
        )

    # §22, in the model as well as in the database. The trigger is the guarantee;
    # this is where a caller finds out before the transaction reaches COMMIT.
    if requires_evidence(claim_type, origin) and not evidence:
        raise _refuse(
            ClaimEvidenceRefusalReason.NO_SUPPORTING_SIGNAL,
            f"a {claim_type.value} claim of origin {origin.value} cites no evidence. A "
            "proposition a machine asserts with nothing behind it is the unsupported "
            "market claim this layer exists to prevent; HYPOTHESIS is where an "
            "unsupported proposition belongs, and it says so on its face",
        )

    for item in evidence:
        if automated and item.direction is EvidenceDirection.NEUTRAL:
            raise _refuse(
                ClaimEvidenceRefusalReason.UNSUPPORTED_INTERPRETATION,
                "an automatically generated evidence row may not be NEUTRAL. A Signal "
                "that bears on nothing produces no row: attaching it would inflate the "
                "record without changing what is supported (§12)",
            )
        if item.source_id and workspace_id and not item.signal_id:  # pragma: no cover
            raise _refuse(ClaimEvidenceRefusalReason.SIGNAL_NOT_CITED, "evidence cites no signal")

    if claim_type is ClaimType.OBSERVED:
        offending = _interpretive_terms(statement)
        if offending:
            raise _refuse(
                ClaimEvidenceRefusalReason.UNSUPPORTED_INTERPRETATION,
                f"an OBSERVED claim may not say {sorted(offending)}. OBSERVED restates "
                "what a source reported; the moment a proposition says demand, interest, "
                "attention or a market, it asserts something the source did not measure "
                "and it is INFERRED at best",
            )

    return ClaimDraft(
        workspace_id=workspace_id,
        claim_type=claim_type,
        temporality=temporality,
        origin=origin,
        statement=statement.strip(),
        proposition_key=key,
        evidence=tuple(evidence),
        interpretation=interpretation,
        interpretation_confidence=interpretation_confidence,
        claim_feature=claim_feature,
        opportunity_id=opportunity_id,
        research_session_id=research_session_id,
        rationale=rationale,
        cited_facts=dict(facts),
    )


def _interpretive_terms(statement: str) -> set[str]:
    """Market or user vocabulary an OBSERVED claim may not use.

    Blunt, and deliberately so. It cannot tell a faithful restatement from a
    subtle over-reach, and it does not try: it catches the obvious failure -- an
    arithmetic relation rewritten as a market fact -- which is the one that would
    otherwise ship. The subtle cases are what review is for, and what `INFERRED`
    exists for.

    Two things make it blunt rather than wrong (Mission 1.13.1 §10):

    **Tokens, not substrings.** `supermarket` and `marketing` are not `market`.

    **Quoted spans are data.** What a source published is quoted and exempt;
    what the interpreter wrote about it is not.
    """
    prose = _QUOTED.sub(" ", statement.lower())
    tokens = _TOKEN.findall(prose)
    found = {token for token in tokens if token in INTERPRETIVE_TOKENS}
    for phrase in INTERPRETIVE_PHRASES:
        width = len(phrase)
        if any(tuple(tokens[i : i + width]) == phrase for i in range(len(tokens) - width + 1)):
            found.add(" ".join(phrase))
    return found
