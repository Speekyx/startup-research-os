"""The v1.3.0 audit: v1.2.0's reading of assertions, one inflection policy, and support typed by origin.

Mission 1.84.11. Gate v1.2.0's diagnostic replay found that its marker licence applied a plural fold
on the answer's side of the check and exact tokens on the supplied side. The operator decided three
things, and this module is those three things and nothing else:

1. **ONE INFLECTION POLICY, BOTH SIDES.** Every lexical comparison, the answer's occurrence of a term
   and the supplied statements' licence for it, goes through `lexical_inflection.inflection_spans`.
   `ANSWER_MARKER_NORMALIZATION_POLICY == SUPPORT_TOKEN_NORMALIZATION_POLICY` is a value here, and
   CI gate 77 checks it by running every gated term through both sides.
2. **A SOURCE'S NAME IS NOT A DOMAIN FACT.** The supplied statements are split by origin
   (`support_origin`): a word that occurs only inside a source metadata label licenses nothing, and
   the refusal says so truthfully instead of claiming the word was never supplied. A label licenses
   exactly its own whole occurrence, read as a name.
3. **A DISJUNCTION CLASSIFIED OBSERVED FAILS CLOSED.** The gate evaluates vocabulary, never the truth
   of a proposition, so it cannot say which alternative of `A or B` one classification is about.
   `DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY`.

Everything else is v1.2.0's, reused rather than rewritten: the clause scoping, the denial reading,
the re-assertion rules, the request and uncertainty shapes, the identifier and canonical-term masks,
the field policy, the forbidden concepts. **A lexical licence is necessary and never sufficient**
(`LEXICAL_MATCH_IS_FACTUAL_SUPPORT = False`): it clears one finding, the marker's, and every other
rule still runs on the same text.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .assertion_context import (
    _CLAUSE_BOUNDARY,
    _IDENTIFIER,
    _MASK,
    _TOKEN,
    _UUID,
    CERTAINTY_MARKERS,
    SCORE_TERMS,
    SUPPORT_PREDICATES,
    Disposition,
    FieldContext,
    ForbiddenConcept,
    Occurrence,
    OccurrenceState,
    Shape,
    _clauses,
    _denies,
    _mask_dimension_terms,
    _norm,
    _reasserted,
    _state,
    is_request_shaped,
    is_uncertainty_shaped,
)
from .dimensions import EvidenceDimension
from .guards import FORBIDDEN_TERMS, VALIDATION_WORDS, _sentences
from .lexical_inflection import (
    LEXICAL_INFLECTION_POLICY_VERSION,
    inflection_spans,
    normalize_token,
    verbatim_spans,
)
from .support_origin import SourceMetadataLabel, TypedSupportUniverse, mask_labels
from .validation import (
    FieldAudit,
    PersistenceDecision,
    StatementSupport,
    SynthesisAudit,
    _numbers,
    _string_list,
)

__all__ = [
    "ASSERTION_GUARD_VERSION_V1_4",
    "ASSERTION_AUDIT_VERSION_V1_4",
    "PERSISTENCE_GATE_VERSION_V1_3",
    "DISJUNCTION_POLICY_VERSION",
    "DISJUNCTIVE_OBSERVED_STATEMENT",
    "SOURCE_METADATA_NOT_FACTUAL_SUPPORT",
    "ANSWER_MARKER_NORMALIZER",
    "SUPPORT_TOKEN_NORMALIZER",
    "ANSWER_MARKER_NORMALIZATION_POLICY",
    "SUPPORT_TOKEN_NORMALIZATION_POLICY",
    "LEXICAL_MATCH_IS_FACTUAL_SUPPORT",
    "classify",
    "is_asserted",
    "disjunctive_connectives",
    "maskable_labels",
    "audit_text",
    "audit_output",
    "evaluate_persistence_v1_3",
]

#: The successor of `opportunity-claim-guard@1.3.0`: the same reading, one inflection policy.
ASSERTION_GUARD_VERSION_V1_4 = "opportunity-claim-guard@1.4.0"
#: The successor of `opportunity-synthesis-audit@1.3.0`: support typed by origin.
ASSERTION_AUDIT_VERSION_V1_4 = "opportunity-synthesis-audit@1.4.0"
#: The successor of `opportunity-synthesis-persistence-gate@1.2.0`.
PERSISTENCE_GATE_VERSION_V1_3 = "opportunity-synthesis-persistence-gate@1.3.0"
DISJUNCTION_POLICY_VERSION = "observed-statement-disjunction-policy@1.0.0"

DISJUNCTIVE_OBSERVED_STATEMENT = "DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY"
SOURCE_METADATA_NOT_FACTUAL_SUPPORT = "SOURCE_METADATA_LABEL_IS_NOT_FACTUAL_SUPPORT"

#: §7. The same function on both sides, by name, so that folding one side and not the other has to
#: change one of these two bindings, which CI gate 77 refuses.
ANSWER_MARKER_NORMALIZER = normalize_token
SUPPORT_TOKEN_NORMALIZER = normalize_token
ANSWER_MARKER_NORMALIZATION_POLICY = LEXICAL_INFLECTION_POLICY_VERSION
SUPPORT_TOKEN_NORMALIZATION_POLICY = LEXICAL_INFLECTION_POLICY_VERSION

#: §13. A lexical match answers "is this vocabulary present in an eligible support channel", and
#: nothing more. It clears the marker finding only.
LEXICAL_MATCH_IS_FACTUAL_SUPPORT = False

_LABEL_MASK = " sourcelabel "
_DISJUNCTION = re.compile(r"(?<![a-z0-9'])(?:or|either)(?![a-z0-9'])")


# ============================================================================= the classifier


def classify(
    text: str, phrase: str, *, scoped_head: bool = False, verbatim: bool = False
) -> tuple[Occurrence, ...]:
    """v1.2.0's `classify`, with every occurrence found under the one inflection policy.

    `verbatim` is for `SUPPORT_PREDICATES` alone: a closed list of verb forms written out form by
    form, where noun number does not apply and `supports` must not fold onto the noun `support`.
    """
    spans = verbatim_spans if verbatim else inflection_spans
    found: list[Occurrence] = []
    for s_index, sentence in enumerate(_sentences(text)):
        clauses = _clauses(sentence)
        for c_index, clause in enumerate(clauses):
            for start, end in spans(clause.text, phrase):
                head = scoped_head and s_index == 0 and c_index == 0
                state, why = _state(clause.text, start, end, head)
                if state is not OccurrenceState.ASSERTED:
                    following = clauses[c_index + 1] if c_index + 1 < len(clauses) else None
                    again = _reasserted(clause.text, end, following)
                    if again is not None:
                        state, why = OccurrenceState.ASSERTED, again
                found.append(Occurrence(phrase, sentence.strip(), clause.text, state, why))
    return tuple(found)


def is_asserted(
    text: str, phrase: str, *, scoped_head: bool = False, verbatim: bool = False
) -> bool:
    return any(
        o.asserted for o in classify(text, phrase, scoped_head=scoped_head, verbatim=verbatim)
    )


def disjunctive_connectives(text: str) -> tuple[str, ...]:
    """Every `or` / `either` that joins alternatives outside a denial, sentence by sentence.

    A connective after a comma that opens a clause of its own (`..., or they were ...`) always
    counts: it joins two propositions. Any other connective joins alternatives inside one clause,
    and counts unless what precedes it in that clause has already denied or questioned (`no X or Y`,
    `not X or Y`, `whether X or Y`), where the alternatives are denied together and nothing is
    observed. v1.2.0's clause splitter also breaks at a comma-less `or` followed by a subject and a
    verb (`no X or Y were ...`); that is still one clause here, read under its denial.
    """
    found: list[str] = []
    for sentence in _sentences(text):
        lowered = _norm(sentence)
        boundaries = [(m.start(), m.end()) for m in _CLAUSE_BOUNDARY.finditer(lowered)]
        for match in _DISJUNCTION.finditer(lowered):
            at = match.start()
            inside = [(s, e) for s, e in boundaries if s <= at < e]
            if inside and "," in lowered[inside[0][0] : at]:
                found.append(match.group())
                continue
            before = inside[0][0] if inside else at
            opened = max((end for _start, end in boundaries if end <= before), default=0)
            if not _denies(lowered[opened:at]):
                found.append(match.group())
    return tuple(found)


# ============================================================================= the masks


def _form(phrase: str) -> str:
    return " ".join(normalize_token(t) for t in _TOKEN.findall(_norm(phrase)))


def maskable_labels(
    universe: TypedSupportUniverse, concepts: Sequence[ForbiddenConcept], markers: Sequence[str]
) -> tuple[SourceMetadataLabel, ...]:
    """The labels that may be read as a name in an answer: all of them, except a label whose words
    ARE a gated term. Such a label cannot be told apart from the term it spells, so it never masks."""
    gated = {
        *(_form(p) for c in concepts for p in c.phrases),
        *(_form(m) for m in markers),
        *(_form(t) for t in FORBIDDEN_TERMS),
        *(_form(t) for t in (*SCORE_TERMS, *VALIDATION_WORDS, *CERTAINTY_MARKERS)),
    }
    return tuple(label for label in universe.labels if _form(label.text) not in gated)


def _mask_identifiers(text: str, universe: TypedSupportUniverse) -> tuple[str, list[str]]:
    """v1.2.0's identifier mask: packet ids, and the trusted channel's definitional identifiers."""
    findings: list[str] = []
    known = set(universe.structural.evidence_ids) | set(universe.structural.claim_ids)
    masked = _UUID.sub(lambda m: _MASK if m.group() in known else m.group(), text)

    def replace(match: re.Match[str]) -> str:
        scheme, number = match.group(1).upper(), match.group(2)
        identifier = f"{scheme}-{number}"
        if identifier in universe.trusted.identifiers:
            return _MASK
        if scheme in universe.trusted.schemes:
            findings.append(
                f"the definitional identifier {identifier} is supplied by no trusted limiting or "
                "definitional fact; an external definition is prior knowledge (§7)"
            )
            return _MASK
        return match.group()

    return _IDENTIFIER.sub(replace, masked), findings


# ============================================================================= the audit


def _concept_findings(
    text: str,
    concepts: Sequence[ForbiddenConcept],
    universe: TypedSupportUniverse,
    *,
    scoped_head: bool,
) -> list[str]:
    findings: list[str] = []
    for concept in concepts:
        for phrase in concept.phrases:
            if universe.content_carries(phrase):
                continue
            for occurrence in classify(text, phrase, scoped_head=scoped_head):
                if not occurrence.asserted:
                    continue
                carrying = universe.metadata_labels_carrying(phrase)
                inside = (
                    f"; it occurs only inside the source metadata label(s) {list(carrying)}, which "
                    "name a source and establish nothing"
                    if carrying
                    else ""
                )
                findings.append(
                    f"{concept.name}: {phrase!r} is asserted ({occurrence.why}), and no source "
                    f"content statement asserts it{inside}. This packet is not {concept.never}"
                )
                for fact in universe.trusted.facts:
                    cited = [
                        i for i in fact.identifiers if i.lower() in occurrence.sentence.lower()
                    ]
                    if cited and concept.name in fact.never_supports:
                        findings.append(
                            f"{cited[0]} is restated from the trusted {fact.kind.value.lower()} "
                            f"fact {fact.fact_id}, which limits {concept.name} and can never "
                            "support it"
                        )
                break
    return findings


def _scoring_status_findings(text: str, *, scoped_head: bool) -> list[str]:
    for term in SCORE_TERMS:
        for occurrence in classify(text, term, scoped_head=scoped_head):
            if occurrence.asserted:
                return [
                    f"{term!r} is asserted ({occurrence.why}). Scoring-ready is not scored, no "
                    "score exists in this repository, and REFERENCE_PROFILE_V1 is UNCALIBRATED"
                ]
    return []


def _marker_findings(
    text: str, universe: TypedSupportUniverse, markers: Sequence[str]
) -> list[str]:
    """A marker is licensed by a source CONTENT statement under the inflection policy, and by
    nothing else. The refusal names the origin it found, so it cannot claim a word was never
    supplied when it was supplied inside a source's name."""
    findings: list[str] = []
    seen: set[str] = set()
    for marker in markers:
        form = _form(marker)
        if form in seen:
            continue
        seen.add(form)
        if universe.content_carries(marker) or not is_asserted(text, marker):
            continue
        carrying = universe.metadata_labels_carrying(marker)
        if carrying:
            findings.append(
                f"{SOURCE_METADATA_NOT_FACTUAL_SUPPORT}: {marker!r} is asserted, and its only "
                f"supplied occurrence is inside the source metadata label(s) {list(carrying)}. A "
                "source's name identifies where the data came from and does not establish a domain "
                "fact, and no source content statement carries the word "
                f"({LEXICAL_INFLECTION_POLICY_VERSION})"
            )
        else:
            findings.append(
                f"{marker!r} appears in no source content statement, compared under "
                f"{LEXICAL_INFLECTION_POLICY_VERSION}; prior knowledge is not available as "
                "factual support (§7)"
            )
    return findings


def audit_text(
    text: str,
    disposition: Disposition,
    shape: Shape,
    universe: TypedSupportUniverse,
    concepts: Sequence[ForbiddenConcept],
    markers: Sequence[str],
    supported: frozenset[EvidenceDimension],
    *,
    observed_statement: bool = False,
) -> tuple[StatementSupport, tuple[str, ...]]:
    """One piece of output text, read in its field's context. Returns a verdict and every finding.

    `observed_statement` marks an item the answer itself classified OBSERVED, which is where a
    disjunction is refused (§15).
    """
    if not text.strip() or text.strip() == "UNKNOWN_NOT_SUPPORTED":
        return StatementSupport.NOT_FACTUAL, ()
    unsupported: list[str] = []
    exceeded: list[str] = []

    # -- a source named by its whole label is a provenance reference, not a use of its words ------
    named = mask_labels(text, maskable_labels(universe, concepts, markers), _LABEL_MASK)

    # -- identifiers and numbers, whatever the disposition: nothing may introduce a figure --------
    masked, identifier_findings = _mask_identifiers(named, universe)
    unsupported += identifier_findings
    for number in sorted(_numbers(masked) - universe.supplied_numbers()):
        unsupported.append(
            f"the number {number} appears in no source content statement and in no structural "
            "fact about the packet"
        )

    asserting = disposition in (Disposition.SUPPORTED_ASSERTION, Disposition.STRUCTURAL_FACT) or (
        disposition is Disposition.HYPOTHESIS_TO_VALIDATE and shape is Shape.FREE
    )
    shaped = shape in (Shape.REQUEST, Shape.UNCERTAINTY)
    scoped_head = False
    if shaped:
        kept = is_request_shaped(text) if shape is Shape.REQUEST else is_uncertainty_shaped(text)
        if kept:
            scoped_head = True
        else:
            wanted, names = (
                ("request", "would have to be observed")
                if shape is Shape.REQUEST
                else ("uncertainty", "is not known")
            )
            exceeded.append(
                f"it is not {wanted}-shaped, so it is read as the assertion it has become. A "
                f"{disposition.value} names what {names}"
            )

    if asserting or shaped:
        exceeded += _concept_findings(named, concepts, universe, scoped_head=scoped_head)
        exceeded += _scoring_status_findings(named, scoped_head=scoped_head)

    if asserting:
        masked_terms = _mask_dimension_terms(masked, supported)
        unsupported += _marker_findings(masked_terms, universe, markers)
        for term, required in sorted(FORBIDDEN_TERMS.items()):
            if not is_asserted(masked_terms, term):
                continue
            if required is None:
                exceeded.append(
                    f"{term!r} is not supportable by any registered source: no observation in "
                    "this portfolio measures it"
                )
            elif required not in supported:
                exceeded.append(
                    f"{term!r} asserts {required.value}, which no eligible evidence in this "
                    "packet supports"
                )
        for word in sorted(VALIDATION_WORDS):
            if inflection_spans(named, word.replace("-", " ")):
                exceeded.append(f"{word!r} states a conclusion; this is a hypothesis record")

    if observed_statement:
        connectives = disjunctive_connectives(named)
        if connectives:
            unsupported.append(
                f"{DISJUNCTIVE_OBSERVED_STATEMENT}: this statement is classified OBSERVED and joins "
                f"alternatives with {sorted(set(connectives))} outside any denial. One "
                "classification cannot say which alternative the evidence supports, and the gate "
                f"evaluates no disjunction, so it fails closed ({DISJUNCTION_POLICY_VERSION})"
            )

    if disposition in (
        Disposition.HYPOTHESIS_TO_VALIDATE,
        Disposition.UNKNOWN_REQUIRES_EVIDENCE,
        Disposition.FUTURE_EVIDENCE_REQUEST,
    ):
        promoted = [w for w in CERTAINTY_MARKERS if is_asserted(named, w, scoped_head=False)]
        if not asserting:
            promoted += [
                w for w in sorted(VALIDATION_WORDS) if inflection_spans(named, w.replace("-", " "))
            ]
        if promoted:
            exceeded.append(
                f"{sorted(set(promoted))} promote a {disposition.value} to a conclusion"
            )

    if disposition is Disposition.EXPLICITLY_NOT_SUPPORTED and shape is Shape.FREE:
        claimed = [p for p in SUPPORT_PREDICATES if is_asserted(named, p, verbatim=True)]
        if claimed:
            exceeded.append(
                f"it says the claim is {claimed[0]!r}, which contradicts the NOT-supported field "
                "it sits in"
            )

    if unsupported:
        return StatementSupport.UNSUPPORTED, tuple(unsupported + exceeded)
    if exceeded:
        return StatementSupport.BOUND_EXCEEDED, tuple(exceeded)
    if asserting:
        return StatementSupport.SUPPORTED, ()
    return StatementSupport.NOT_FACTUAL, ()


def audit_output(
    output: Mapping[str, object],
    universe: TypedSupportUniverse,
    policy: Sequence[FieldContext],
    concepts: Sequence[ForbiddenConcept],
    markers: Sequence[str],
    label_dispositions: Mapping[str, Disposition],
) -> SynthesisAudit:
    """Every text in the output, each in its field's context. A field the policy does not name
    fails closed: text nobody classified is text nobody may assume harmless."""
    declared = frozenset(
        d
        for d in EvidenceDimension
        if d.value in set(_string_list(output.get("supported_dimensions")))
    )
    supported = declared & universe.structural.supported_dimensions
    by_name = {fc.field_name: fc for fc in policy}
    audits: list[FieldAudit] = []

    for key in output:
        if key not in by_name:
            audits.append(
                FieldAudit(
                    key,
                    StatementSupport.UNSUPPORTED,
                    (f"{key} has no field context, so its text cannot be read as anything",),
                )
            )

    for fc in policy:
        value = output.get(fc.field_name)
        if fc.shape is Shape.ENUMERATION or value is None:
            continue
        items: list[tuple[str, str, Disposition, Shape, bool]] = []
        if fc.item_label_key is not None:
            for index, item in enumerate(value if isinstance(value, list) else []):
                if not isinstance(item, Mapping):
                    continue
                label = str(item.get(fc.item_label_key) or "")
                disposition = label_dispositions.get(label)
                text = str(item.get(fc.item_text_key or "") or "")
                name = f"{fc.field_name}[{index}].{fc.item_text_key}"
                if disposition is None:
                    audits.append(
                        FieldAudit(
                            name, StatementSupport.UNSUPPORTED, (f"unknown label {label!r}",)
                        )
                    )
                    continue
                observed = disposition is Disposition.SUPPORTED_ASSERTION
                shape = Shape.FREE if observed else Shape.LABELLED
                items.append((name, text, disposition, shape, observed))
        elif isinstance(value, list):
            assert fc.disposition is not None  # noqa: S101 -- guaranteed by FieldContext
            items += [
                (f"{fc.field_name}[{i}]", str(v), fc.disposition, fc.shape, False)
                for i, v in enumerate(value)
                if isinstance(v, str)
            ]
        elif isinstance(value, str):
            assert fc.disposition is not None  # noqa: S101 -- guaranteed by FieldContext
            items.append((fc.field_name, value, fc.disposition, fc.shape, False))
        for name, text, disposition, shape, observed in items:
            verdict, findings = audit_text(
                text,
                disposition,
                shape,
                universe,
                concepts,
                markers,
                supported,
                observed_statement=observed,
            )
            audits.append(FieldAudit(name, verdict, findings))

    return SynthesisAudit(audit_version=ASSERTION_AUDIT_VERSION_V1_4, fields=tuple(audits))


def evaluate_persistence_v1_3(
    output: Mapping[str, object],
    universe: TypedSupportUniverse,
    evidence_to_claim: Mapping[str, str],
    mandatory_unsupported: Sequence[EvidenceDimension],
    *,
    policy: Sequence[FieldContext],
    concepts: Sequence[ForbiddenConcept],
    markers: Sequence[str],
    label_dispositions: Mapping[str, Disposition],
) -> PersistenceDecision:
    """persistence-gate@1.2.0's structural checks unchanged in meaning, over the typed universe,
    plus one it could not make: every packet source must declare its names."""
    facts = universe.structural
    reasons: list[str] = []
    notes: list[str] = []

    decision = str(output.get("decision") or "")
    if decision == "INSUFFICIENT_EVIDENCE":
        return PersistenceDecision(
            persist=False,
            gate_version=PERSISTENCE_GATE_VERSION_V1_3,
            refusal_reasons=(
                "the model answered INSUFFICIENT_EVIDENCE. That is a correct and expected "
                "outcome, not a failure, and no Opportunity is created.",
            ),
        )
    if decision != "FORM_HYPOTHESIS":
        reasons.append(f"decision {decision!r} is not one of the two permitted values")

    if universe.undeclared_sources:
        reasons.append(
            f"no source metadata is declared for {list(universe.undeclared_sources)}, so their "
            "statements cannot be split into what they reported and what they are called; a "
            "source's name must never be read as content silently"
        )

    if str(output.get("subject") or "") != facts.subject_label:
        reasons.append(
            f"subject is {output.get('subject')!r}; the packet's subject identity is "
            f"{facts.subject_label!r}"
        )

    cited_evidence = set(_string_list(output.get("supporting_evidence_ids")))
    cited_claims = set(_string_list(output.get("supporting_claim_ids")))
    stray_evidence = sorted(cited_evidence - set(facts.evidence_ids))
    stray_claims = sorted(cited_claims - set(facts.claim_ids))
    if stray_evidence:
        reasons.append(
            f"cited Evidence ids not in the packet: {stray_evidence}. A hypothesis may cite only "
            "what it was given"
        )
    if stray_claims:
        reasons.append(f"cited Claim ids not in the packet: {stray_claims}")
    if not cited_evidence:
        reasons.append("no supporting Evidence id was cited")
    if not cited_claims:
        reasons.append("no supporting Claim id was cited")
    for evidence_id in sorted(cited_evidence):
        expected = evidence_to_claim.get(evidence_id)
        if expected is not None and expected not in cited_claims:
            reasons.append(
                f"Evidence {evidence_id} was cited without its Claim {expected}. Evidence is "
                "claim-relative, so a citation missing its claim cites nothing"
            )

    stray_families = sorted(
        set(_string_list(output.get("source_families"))) - set(facts.source_families)
    )
    if stray_families:
        reasons.append(f"source families the packet does not carry: {stray_families}")

    claimed_supported = set(_string_list(output.get("supported_dimensions")))
    packet_dimensions = {d.value for d in facts.packet_dimensions}
    over_claimed = sorted(claimed_supported - packet_dimensions)
    if over_claimed:
        reasons.append(
            f"dimensions claimed as supported that this packet does not carry: {over_claimed}"
        )
    reported_unsupported = set(_string_list(output.get("unsupported_dimensions")))
    both = sorted(claimed_supported & reported_unsupported)
    if both:
        reasons.append(f"dimensions reported both supported and unsupported: {both}")
    missing_report = sorted(
        d.value
        for d in mandatory_unsupported
        if d not in facts.packet_dimensions and d.value not in reported_unsupported
    )
    if missing_report:
        reasons.append(
            f"§6 requires an explicit unsupported report for {missing_report}, and the output does "
            "not mark them. A dimension nobody mentioned reads as one nobody checked"
        )

    independence = str(output.get("independence_status") or "").lower()
    if "unknown" not in independence:
        reasons.append(
            "independence_status does not record UNKNOWN. Two source families is diversity, never "
            "established independence"
        )
    for forbidden in ("independent source", "independent sources", "independently"):
        if forbidden in independence:
            reasons.append(
                f"independence_status contains {forbidden!r}; independence is UNKNOWN for every "
                "row in this packet"
            )
    reliability = str(output.get("reliability_status") or "").upper()
    if facts.scoring_eligible_count == 0:
        if "NON_SCORABLE" not in reliability and "MISSING_RELIABILITY" not in reliability:
            reasons.append(
                "no row in this packet is scoring-eligible and reliability_status does not "
                "preserve NON_SCORABLE / MISSING_RELIABILITY"
            )
    elif "SCORABLE" not in reliability and "SCORING" not in reliability:
        reasons.append(
            f"{facts.scoring_eligible_count} of {facts.size} rows are scoring-eligible and "
            "reliability_status does not say so. A packet's scorability is a fact about it"
        )

    audit = audit_output(output, universe, policy, concepts, markers, label_dispositions)
    for failed in audit.failed:
        reasons.append(
            f"{failed.field_name} audited {failed.verdict.value}: {'; '.join(failed.findings)}"
        )
    if all(f.verdict is StatementSupport.NOT_FACTUAL for f in audit.fields):
        notes.append(
            "every audited text was NOT_FACTUAL: there was nothing checkable in the output, which "
            "is recorded rather than read as a pass"
        )

    return PersistenceDecision(
        persist=not reasons,
        gate_version=PERSISTENCE_GATE_VERSION_V1_3,
        refusal_reasons=tuple(reasons),
        audit=audit,
        notes=tuple(notes),
    )
