"""Attribution: an obligation that follows the data, not a string in a template.

Mission 1.4 §6, §7, §8, §9. All three conditionally approved sources require
attribution and **each requires a different thing**, which is why this is a
model rather than a constant:

    World Bank   credit, the dataset's licence, and an indication of any change
                 -- including translation. CC-BY 4.0 grants commercial use
                 *provided* both are present
    Eurostat     the dataset DOI and the access date, per retrieval. Modified
                 data additionally carries a disclaimer whose exact wording is
                 not in the retrieved evidence and is therefore SUPPLIED
    FRED         one sentence, verbatim, including the registered trademark
                 symbol

Two properties are enforced rather than documented.

**A required element cannot be omitted.** `render` raises rather than dropping
it, and there is no partial rendering: a notice missing half its obligation
looks like attribution and is not. §8 asks for proof that required attribution
cannot silently disappear, and a renderer that returns `""` when it has nothing
would be the disappearance.

**An obligation survives transformation.** `AttributedArtifact.derive` carries
the obligations of everything it was derived from and can only add. Raw record →
normalized → evidence → claim → result is a chain in which any step could
otherwise be where the credit was lost (§9).

Rendering is deliberately plain text. §8 says not to build the final UI; what a
surface needs is the obligation and its resolved elements, which is what this
produces.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date

from sros_contracts import AttributionElement
from sros_contracts.errors import ContractError

from .config import AttributionObligation, AttributionRequirement

__all__ = [
    "AttributedArtifact",
    "AttributionFacts",
    "AttributionIncompleteError",
    "AttributionNotice",
    "render_attribution",
]


class AttributionIncompleteError(ContractError):
    """A required attribution element has no value.

    Raised rather than rendered around, because a notice that silently omits a
    required element is worse than no notice: it looks like the obligation was
    met.
    """

    def __init__(self, source_id: str, missing: Iterable[AttributionElement]) -> None:
        names = ", ".join(sorted(e.value for e in missing))
        super().__init__(
            f"attribution.{source_id}",
            f"required element(s) {names} have no value. Attribution is a condition of "
            "the licence, so a view that cannot render it must not be produced",
        )


@dataclass(frozen=True)
class AttributionFacts:
    """The per-artefact half of an attribution obligation.

    Everything here is a property of a specific retrieval or transformation and
    cannot be defaulted: a dataset DOI belongs to a dataset, an access date to a
    retrieval, a modification statement to a change somebody made.
    """

    licence_identifier: str | None = None
    dataset_doi: str | None = None
    # ADR-031. A link to the specific item, where the licence requires the
    # material itself to be locatable -- CC BY and CC BY-SA both do. Per item,
    # so it cannot be defaulted: a fixed link would attribute every item to one
    # place, which is what the clause is written against.
    source_item_link: str | None = None
    access_date: date | None = None
    modification_statement: str | None = None
    disclaimer: str | None = None
    modified: bool = False

    def value_for(self, element: AttributionElement) -> str | None:
        if element is AttributionElement.LICENCE_IDENTIFIER:
            return self.licence_identifier
        if element is AttributionElement.SOURCE_ITEM_LINK:
            return self.source_item_link
        if element is AttributionElement.DATASET_DOI:
            return self.dataset_doi
        if element is AttributionElement.ACCESS_DATE:
            return self.access_date.isoformat() if self.access_date else None
        if element is AttributionElement.MODIFICATION_STATEMENT:
            return self.modification_statement
        if element is AttributionElement.DISCLAIMER:
            return self.disclaimer
        # SOURCE_CREDIT and EXACT_NOTICE are configuration, never supplied.
        return None


@dataclass(frozen=True)
class AttributionNotice:
    """A resolved obligation: every required element with its value."""

    source_id: str
    elements: tuple[tuple[AttributionElement, str], ...]
    evidence_url: str

    @property
    def text(self) -> str:
        return " ".join(value for _, value in self.elements)

    @property
    def lines(self) -> tuple[str, ...]:
        return tuple(f"{element.value}: {value}" for element, value in self.elements)

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "elements": [{"element": e.value, "value": v} for e, v in self.elements],
            "text": self.text,
            "evidence_url": self.evidence_url,
        }


def render_attribution(
    obligation: AttributionObligation, facts: AttributionFacts | None = None
) -> AttributionNotice:
    """Resolve every required element, or refuse.

    A `when_modified` requirement is required exactly when the facts say the
    data was modified. That is not leniency: an unmodified artefact has nothing
    to state a modification about, and requiring a statement of a change that
    did not happen would train callers to write "none" into it.
    """
    supplied = facts or AttributionFacts()
    elements: list[tuple[AttributionElement, str]] = []
    missing: list[AttributionElement] = []

    for requirement in obligation.requirements:
        if requirement.when_modified and not supplied.modified:
            continue
        value = _resolve(requirement, supplied)
        if value is None or not value.strip():
            missing.append(requirement.element)
            continue
        elements.append((requirement.element, value))

    if missing:
        raise AttributionIncompleteError(obligation.source_id, missing)

    return AttributionNotice(
        source_id=obligation.source_id,
        elements=tuple(elements),
        evidence_url=obligation.evidence_url,
    )


def _resolve(requirement: AttributionRequirement, facts: AttributionFacts) -> str | None:
    """Configured text wins and is returned unmodified.

    Never `.strip()`-ed, never re-cased, never reflowed. Where the wording is
    prescribed by the terms, a transformation of it is a different sentence.
    """
    if not requirement.supplied:
        return requirement.text
    return facts.value_for(requirement.element)


@dataclass(frozen=True)
class AttributedArtifact:
    """Anything derived from source data, carrying what it owes.

    Mission 1.4 §9. The downstream data model is not built here -- there is no
    RawRecord and no collector. What is built is the pattern the chain has to
    follow, so that a future transformation cannot be written in a way that
    drops the obligation:

        raw = AttributedArtifact.of("RawRecord", obligation, facts)
        normalized = raw.derive("NormalizedRecord")
        evidence    = normalized.derive("Evidence")

    `derive` has no parameter that removes an obligation. Combining two
    artefacts unions their obligations, because data derived from two sources
    owes both.
    """

    kind: str
    obligations: tuple[AttributionObligation, ...] = ()
    facts: Mapping[str, AttributionFacts] = field(default_factory=dict)

    @classmethod
    def of(
        cls,
        kind: str,
        obligation: AttributionObligation,
        facts: AttributionFacts | None = None,
    ) -> AttributedArtifact:
        return cls(
            kind=kind,
            obligations=(obligation,),
            facts={obligation.source_id: facts or AttributionFacts()},
        )

    def derive(self, kind: str, *also: AttributedArtifact) -> AttributedArtifact:
        """A new artefact owing everything this one owed, plus anything merged in."""
        obligations: dict[str, AttributionObligation] = {o.source_id: o for o in self.obligations}
        facts: dict[str, AttributionFacts] = dict(self.facts)
        for other in also:
            for obligation in other.obligations:
                obligations.setdefault(obligation.source_id, obligation)
            for source_id, fact in other.facts.items():
                facts.setdefault(source_id, fact)
        return AttributedArtifact(kind=kind, obligations=tuple(obligations.values()), facts=facts)

    def notices(self) -> tuple[AttributionNotice, ...]:
        """Every notice this artefact must display, or an exception.

        Called by a surface before it renders. An artefact whose attribution
        cannot be resolved does not get displayed without it.
        """
        return tuple(
            render_attribution(obligation, self.facts.get(obligation.source_id))
            for obligation in self.obligations
        )

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(o.source_id for o in self.obligations))
