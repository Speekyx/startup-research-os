"""`observed-signal-restatement@1.0.0` -- a Signal, said back with its source named.

`deterministic-observed-claim-interpreter-v1.md`. Mission 1.13.1.

**What every claim here asserts, in full:** that a named source reported a named
quantity, over named source periods, with this exact magnitude and this
direction.

**What none of them asserts:** demand, interest, attention, popularity, a
market, a want, a willingness to pay, an opportunity, or that the source was
right. `OBSERVED` is about the publication: it is false if the source did not
say that, and it stays true if the source was wrong
(`claim-epistemic-semantics-v1.md` §3).

Three templates, one per implemented Signal type, and **no fallback**. A Signal
type with no template is `UNSUPPORTED_SIGNAL_TYPE`. Generic prose over an
unknown Signal is the one thing a deterministic interpreter must not do: it
would emit a proposition nobody specified and nobody reviewed.

**Structurally OBSERVED.** `_CLAIM_TYPE` is a module constant read by every
template, and no code path in this package passes any other value to
`build_claim`. There is no low-confidence-inferred escape hatch, and adding one
is a version bump with a document behind it (§5).

**No network, no model, no embedder, no clock arithmetic.** A template is a
format string applied to structured facts. `validate_claims.py` asserts it over
the AST.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from sros_claim_model import (
    ClaimDraft,
    ClaimInterpretation,
    ClaimRefusal,
    ClaimRefusedError,
    EvidenceDraft,
    build_claim,
)
from sros_contracts import (
    ClaimEvidenceRefusalReason,
    ClaimInterpretationKind,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
    SignalDirection,
)

from .base import (
    InterpretationRefusedError,
    InterpretationRequest,
    SignalView,
    TemplateOutcome,
    lineage_fact,
)

__all__ = [
    "INTERPRETER_ID",
    "INTERPRETER_VERSION",
    "OBSERVED_EVIDENCE_LEVEL",
    "SUPPORTED_SIGNAL_TYPES",
    "ObservedSignalRestatementInterpreter",
]

INTERPRETER_ID = "observed-signal-restatement"
INTERPRETER_VERSION = "1.0.0"

SUPPORTED_SIGNAL_TYPES: tuple[str, ...] = (
    "numeric_period_change",
    "lexical_frequency_change",
    "lexical_frequency_contrast",
)

# Read by every template and passed by no caller. The claim type this
# interpreter produces is a property of the interpreter, not a parameter of a
# request (§5).
_CLAIM_TYPE = ClaimType.OBSERVED
_ORIGIN = ClaimOrigin.DETERMINISTIC_EXTRACTION

# A claim about a FIXED pair of source periods does not decay. "World Bank
# reported that SP.POP.TOTL for Germany increased between 2018 and 2019" is as
# true in 2030 as today; it is a statement about a publication, not about an
# ongoing state (`claim-epistemic-semantics-v1.md` §9). Reading temporality off
# the source's cadence -- 15-minute buckets must be perishable -- is the mistake
# that section names.
_TEMPORALITY = ClaimTemporality.EVERGREEN

# A template applied to structured facts is certain it read them correctly, and
# that is the only thing this number says. It is NOT how strong the evidence is,
# NOT how likely the source is to be right, and NOT an EvidenceScore
# (`claim-evidence-interpretation-contract-v1.md` §11).
_INTERPRETATION_CONFIDENCE = 1.0

# `EvidenceLevel` 1, "Weak Signal": a small or isolated indication
# (`evidence-confidence-framework-v1.md` §2). Not a judgement invented here --
# it is where the ladder's own gates leave a single record whose category is
# UNCATEGORISED and whose independence is UNKNOWN. Levels 2 and 3 need
# established independent groups; 4 and 5 are category-gated to MARKET_ACTIVITY
# and DIRECT_VALIDATION. Level 0 would be wrong: an external observation exists.
OBSERVED_EVIDENCE_LEVEL = 1

# What kind of thing was observed. UNCATEGORISED for BOTH sources, and
# deliberately (`signal-to-evidence-semantics-v1.md` §7):
#
#   a population count is not MARKET_ACTIVITY -- it is context;
#   a news-corpus frequency is not REPORTED_ or OBSERVED_BEHAVIOUR -- nobody's
#   behaviour was observed. It is journalists publishing.
#
# Inventing a category for publication activity here would be a taxonomy change
# made in passing.
_OBSERVATION_CATEGORY = EvidenceObservationCategory.UNCATEGORISED

_DETERMINISTIC = ClaimInterpretation(
    interpreter_id=INTERPRETER_ID,
    interpreter_version=INTERPRETER_VERSION,
    kind=ClaimInterpretationKind.DETERMINISTIC,
    # model_version and prompt_version stay None, and the model refuses a
    # DETERMINISTIC interpretation that carries either. "Deterministic" promises
    # the claim can be regenerated and compared; a model in the path voids it.
)

# Which temporal bases each template can phrase. Strict, so an unexpected basis
# FAILS CLOSED rather than being described by wording chosen for a different
# one. A `lexical_frequency_change` Signal carrying COMPARABLE_INSTANTS would
# mean H-29 had closed, and the sentence to write for it is a decision, not a
# default (§25).
_ACCEPTED_BASES: Mapping[str, frozenset[str]] = {
    "numeric_period_change": frozenset({"COMPARABLE_INSTANTS", "ORDERED_PERIODS"}),
    "lexical_frequency_change": frozenset({"ORDERED_PERIODS"}),
    "lexical_frequency_contrast": frozenset({"SAME_PERIOD_LABEL"}),
}


def _refuse(reason: ClaimEvidenceRefusalReason, detail: str) -> InterpretationRefusedError:
    return InterpretationRefusedError(ClaimRefusal(reason=reason, detail=detail))


def _plain(value: Decimal) -> str:
    """A decimal as a person would write it, never in exponent form."""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _evidence(signal: SignalView, source_id: str) -> EvidenceDraft:
    """The one Evidence row a restatement produces.

    Every factor below is a decision with a reason, and the two that are absent
    are the important ones.
    """
    return EvidenceDraft(
        signal_id=signal.signal_id,
        # The claim IS this Signal said back. It cannot bear against itself, and
        # a NEUTRAL row would assert the Signal bears on nothing.
        direction=EvidenceDirection.SUPPORTS,
        source_id=source_id,
        observation_category=_OBSERVATION_CATEGORY,
        # UNKNOWN, always. Two Signals from one publication stream are not
        # independent because they are two Signals, and declaring them dependent
        # is a judgement this layer cannot make either. Record what you know,
        # promote nothing (§19, `signal-to-evidence-semantics-v1.md` §6).
        independence_state=EvidenceIndependenceState.UNKNOWN,
        # 1.0: how much what the Signal is about overlaps what the Claim is
        # about. They are the same subject BY CONSTRUCTION -- the claim restates
        # this Signal and nothing else -- so any lower value would describe a
        # gap that does not exist.
        relevance=1.0,
        # 1.0: whether the Signal bears on the Claim itself or on something
        # adjacent. It bears on the Claim itself; the Claim asserts exactly what
        # the Signal measured. Directness is not source truthfulness (§16).
        directness=1.0,
        # ABSENT, and this is the deliberate one. Reliability is purpose-relative
        # and D-03 is blocked: there is no reviewed value for "World Bank
        # population data, for a claim about what World Bank reported", and a
        # constant here would be the per-source coefficient the framework
        # refuses. Approval status is not reliability either (§17).
        #
        # The consequence is stated rather than worked around: every one of
        # these records is NON_SCORABLE with MISSING_RELIABILITY, and that is
        # the honest answer, not a gap to fill (§30).
        reliability=None,
        # 1.0: the interpreter correctly READ the Signal. A format string over
        # structured facts either read them or raised. Says nothing about
        # whether the source captured reality (§18).
        extraction_confidence=1.0,
    )


class ObservedSignalRestatementInterpreter:
    """Three propositions, each a faithful restatement of one Signal."""

    interpreter_id = INTERPRETER_ID
    interpreter_version = INTERPRETER_VERSION
    kind = ClaimInterpretationKind.DETERMINISTIC
    supported_signal_types = SUPPORTED_SIGNAL_TYPES

    def supports(self, signal_type_id: str) -> bool:
        return signal_type_id in SUPPORTED_SIGNAL_TYPES

    def interpret(self, signal: SignalView, request: InterpretationRequest) -> TemplateOutcome:
        """One Signal in, one ClaimDraft or one refusal out. Never both."""
        try:
            return TemplateOutcome(draft=self._render(signal, request))
        except InterpretationRefusedError as refused:
            return TemplateOutcome(refusal=refused.refusal)
        except ClaimRefusedError as refused:
            # The MODEL refused the draft the template built -- the vocabulary
            # guard, the evidence rule, the provenance rule. Reported with the
            # model's own reason rather than reworded, so the run log says which
            # rule stopped it.
            return TemplateOutcome(refusal=refused.refusal)

    # -------------------------------------------------------------- dispatch

    def _render(self, signal: SignalView, request: InterpretationRequest) -> ClaimDraft:
        if not self.supports(signal.signal_type_id):
            raise _refuse(
                ClaimEvidenceRefusalReason.UNSUPPORTED_SIGNAL_TYPE,
                f"{signal.signal_type_id!r} has no template. Supported: "
                f"{list(SUPPORTED_SIGNAL_TYPES)}. There is no generic fallback: a "
                "sentence nobody specified is a proposition nobody reviewed",
            )
        accepted = _ACCEPTED_BASES[signal.signal_type_id]
        if signal.temporal_basis not in accepted:
            raise _refuse(
                ClaimEvidenceRefusalReason.INCOMPATIBLE_TEMPORAL_SEMANTICS,
                f"a {signal.signal_type_id} Signal on basis {signal.temporal_basis} cannot "
                f"be phrased by this template, which knows {sorted(accepted)}. Describing "
                "it with wording chosen for a different basis is how an unzoned bucket "
                "becomes an instant",
            )
        if signal.signal_type_id == "numeric_period_change":
            return self._numeric_period_change(signal, request)
        if signal.signal_type_id == "lexical_frequency_change":
            return self._lexical_frequency_change(signal, request)
        return self._lexical_frequency_contrast(signal, request)

    # ------------------------------------------------------ numeric templates

    def _numeric_period_change(
        self, signal: SignalView, request: InterpretationRequest
    ) -> ClaimDraft:
        """ "{Source} reported that "{metric}" for "{geography}" increased …"

        The geography is the source's OWN name for it, not our canonical code.
        `geography.source_name` is what World Bank called the entity; `DE` is
        what a reviewed mapping decided it is, and an OBSERVED claim reports the
        first (`normalized-record-v1.md`: an aggregate is never a country, and
        classification comes from the reviewed map rather than from a label).
        """
        source_id = signal.single_source()
        source_name = _source_name(signal, source_id)
        metric_id = lineage_fact(signal, "metric", "id", label="the metric id")
        metric_scheme = lineage_fact(signal, "metric", "scheme", label="the metric scheme")
        geography = lineage_fact(signal, "geography", "source_name", label="the geography name")
        geography_code = lineage_fact(
            signal, "geography", "source_code", label="the geography code"
        )
        resource_id = lineage_fact(signal, "series", "resource_id", label="the resource id")
        earlier, later = _two_labels(signal)

        facts = {
            "proposition": "source_reported_metric_period_change",
            "source_id": source_id,
            "resource_id": resource_id,
            "metric_scheme": metric_scheme,
            "metric_id": metric_id,
            "geography_source_code": geography_code,
            "period_label_from": earlier,
            "period_label_to": later,
            "direction": signal.direction.value,
        }

        if signal.direction is SignalDirection.UNCHANGED:
            statement = (
                f'{source_name} reported that "{metric_id}" for "{geography}" was unchanged '
                f'between "{earlier}" and "{later}".'
            )
        else:
            statement = (
                f'{source_name} reported that "{metric_id}" for "{geography}" '
                f"{_movement(signal)} "
                f'between "{earlier}" and "{later}" by {_plain(abs(signal.magnitude))}.'
            )
        return self._build(signal, request, source_id, statement, facts)

    # ------------------------------------------------------ lexical templates

    def _lexical_frequency_change(
        self, signal: SignalView, request: InterpretationRequest
    ) -> ClaimDraft:
        """Source-relative wording only. No clock, no date, no canonical language.

        The two source bucket labels are named, because a claim that cannot say
        WHICH buckets is not checkable. They are named as *source bucket labels*
        and never as times: "the preceding source bucket" is the entire temporal
        vocabulary ADR-022 licenses, and H-29 leaves everything else
        unestablished (§25).
        """
        source_id = signal.single_source()
        source_name = _source_name(signal, source_id)
        stream, language_label, language_scheme, term_scheme, gram_size = _lexical_lineage(signal)
        terms = signal.scope_list("terms")
        if len(terms) != 1:
            raise _refuse(
                ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE,
                f"a frequency-change Signal is about ONE term; this one names {list(terms)}",
            )
        term = terms[0]
        earlier, later = _two_labels(signal)

        facts = {
            "proposition": "source_reported_term_frequency_change",
            "source_id": source_id,
            "resource_id": stream,
            "term_scheme": term_scheme,
            "term": term,
            "gram_size": gram_size,
            "language_source_scheme": language_scheme,
            "language_source_label": language_label,
            "period_label_from": earlier,
            "period_label_to": later,
            "direction": signal.direction.value,
        }

        preamble = (
            f'{source_name} reported that, in its "{stream}" stream under source language '
            f'label "{language_label}", the term "{term}"'
        )
        if signal.direction is SignalDirection.UNCHANGED:
            statement = (
                f'{preamble} appeared the same number of times in source bucket "{later}" '
                f'as in the preceding source bucket "{earlier}".'
            )
        else:
            comparative = "more" if signal.direction is SignalDirection.INCREASING else "fewer"
            statement = (
                f"{preamble} appeared {_plain(abs(signal.magnitude))} {comparative} times in "
                f'source bucket "{later}" than in the preceding source bucket "{earlier}".'
            )
        return self._build(signal, request, source_id, statement, facts)

    def _lexical_frequency_contrast(
        self, signal: SignalView, request: InterpretationRequest
    ) -> ClaimDraft:
        """Two terms, one bucket. No ordering is asserted and none is available.

        The Signal's `direction` is `NOT_APPLICABLE` by construction -- nothing
        changed -- so the relation between the two terms lives in the SIGN of
        the magnitude, which the extractor computes as `terms[0] - terms[1]`
        over terms sorted by text. The sign is a semantic fact and enters the
        proposition identity; the value is wording, and does not.
        """
        source_id = signal.single_source()
        source_name = _source_name(signal, source_id)
        stream, language_label, language_scheme, term_scheme, gram_size = _lexical_lineage(signal)
        terms = signal.scope_list("terms")
        if len(terms) != 2:
            raise _refuse(
                ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE,
                f"a frequency contrast is between TWO terms; this one names {list(terms)}",
            )
        first, second = terms
        labels = signal.period_labels
        if len(set(labels)) != 1:
            raise _refuse(
                ClaimEvidenceRefusalReason.INCOMPATIBLE_TEMPORAL_SEMANTICS,
                f"a same-bucket contrast must carry ONE source bucket label; got "
                f"{sorted(set(labels))}. Two labels would make it a change over time, "
                "which is a different proposition on a basis this Signal does not have",
            )
        label = labels[0]
        relation = (
            "GREATER" if signal.magnitude > 0 else "FEWER" if signal.magnitude < 0 else "EQUAL"
        )

        facts = {
            "proposition": "source_reported_term_frequency_contrast",
            "source_id": source_id,
            "resource_id": stream,
            "term_scheme": term_scheme,
            "term_a": first,
            "term_b": second,
            "gram_size": gram_size,
            "language_source_scheme": language_scheme,
            "language_source_label": language_label,
            "period_label": label,
            "relation": relation,
        }

        preamble = (
            f'{source_name} reported that, in its "{stream}" stream under source language '
            f'label "{language_label}", within source bucket "{label}", the term "{first}"'
        )
        if relation == "EQUAL":
            statement = f'{preamble} appeared the same number of times as the term "{second}".'
        else:
            comparative = "more" if relation == "GREATER" else "fewer"
            statement = (
                f"{preamble} appeared {_plain(abs(signal.magnitude))} {comparative} times "
                f'than the term "{second}".'
            )
        return self._build(signal, request, source_id, statement, facts)

    # ----------------------------------------------------------------- build

    def _build(
        self,
        signal: SignalView,
        request: InterpretationRequest,
        source_id: str,
        statement: str,
        facts: Mapping[str, object],
    ) -> ClaimDraft:
        """Hand the rendered proposition to the model, which decides.

        Every constant this passes is a module constant, so no call site can ask
        for a different claim type, a different origin or a model version.
        """
        return build_claim(
            workspace_id=request.workspace_id,
            claim_type=_CLAIM_TYPE,
            temporality=_TEMPORALITY,
            origin=_ORIGIN,
            statement=statement,
            facts=facts,
            evidence=[_evidence(signal, source_id)],
            interpretation=_DETERMINISTIC,
            interpretation_confidence=_INTERPRETATION_CONFIDENCE,
            research_session_id=request.research_session_id,
            rationale=(
                f"Restated from signal {signal.signal_id} "
                f"({signal.extractor_id}@{signal.extractor_version})."
            ),
        )


# --------------------------------------------------------------------- helpers


def _source_name(signal: SignalView, source_id: str) -> str:
    """The registry's canonical name, or the id.

    Read from `registry.sources` by the repository and carried on the view, so
    the display name comes from the authoritative registry rather than from a
    map in this file. Falling back to the id keeps the interpreter usable
    against a source the registry has not named, and the id is never wrong --
    only terser.
    """
    return signal.source_name or source_id


def _lexical_lineage(signal: SignalView) -> tuple[str, str, str, str, str]:
    """Stream, language label, language scheme, term scheme, gram size.

    **`language.canonical_tag` is never read**, here or anywhere in this
    package. H-30 is open: a GDELT label is its own identity, and reading the
    canonical tag would assert a reviewed mapping that does not exist (§26).
    `validate_claims.py` asserts the absence structurally.
    """
    return (
        lineage_fact(signal, "series", "resource_id", label="the resource id"),
        lineage_fact(signal, "language", "source_label", label="the source language label"),
        lineage_fact(signal, "language", "source_scheme", label="the source language scheme"),
        lineage_fact(signal, "term", "scheme", label="the term scheme"),
        lineage_fact(signal, "term", "gram_size", label="the gram size"),
    )


def _two_labels(signal: SignalView) -> tuple[str, str]:
    """The earlier and later source period labels, in the Signal's own order.

    The order is the extractor's, recorded in the window when the Signal was
    derived. It is never recomputed here by comparing labels: label order is a
    certification (ADR-022), not a property of a string that happens to sort.
    """
    labels = signal.period_labels
    if len(labels) != 2:
        raise _refuse(
            ClaimEvidenceRefusalReason.INCOMPATIBLE_TEMPORAL_SEMANTICS,
            f"this template restates a relation between exactly two source periods; the "
            f"Signal's window names {list(labels)}",
        )
    return labels[0], labels[1]


def _movement(signal: SignalView) -> str:
    if signal.direction is SignalDirection.INCREASING:
        return "increased"
    if signal.direction is SignalDirection.DECREASING:
        return "decreased"
    raise _refuse(
        ClaimEvidenceRefusalReason.UNSUPPORTED_INTERPRETATION,
        f"direction {signal.direction.value} has no faithful restatement in this template. "
        "INDETERMINATE means the extractor could not say which way it moved, and a "
        "sentence that picked one would assert what the derivation refused to",
    )
