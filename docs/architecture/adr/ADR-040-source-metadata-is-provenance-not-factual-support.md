# ADR-040: A source's name is provenance, never factual support

- **Status:** Accepted
- **Date:** 2026-09-13
- **Deciders:** the operator (decision owner), recorded in Mission 1.84.11
- **Supersedes:** none
- **Related:** ADR-024, ADR-025, `docs/data/source-metadata-evidence-boundary-decision-v1.json`,
  `docs/reports/mission-1.84.11-report.md`, `docs/reports/mission-1.84.10-report.md`

---

## Context

The interpretation template writes the source's registry name at the head of an OBSERVED claim
statement: *"Tenders Electronic Daily (EU public procurement) reported that, in its ... resource,
..."*. The claim statements are what the second-Opportunity output gate treats as supplied support.
Until gate v1.2.0 they were one undifferentiated string, so every word of a source's NAME licensed
the same things as every word of what the source REPORTED.

Mission 1.84.10's diagnostic replay made the consequence visible. A marker the answer asserted
appeared in the supplied statements only inside the publisher's name. Gate v1.2.0 refused it, for
the wrong reason: its supplied-side check compared exact tokens while its answer-side check folded
plurals. Repairing that asymmetry alone would have let the name license the word. Whether it should
was a question about evidence, not about morphology, and the operator decided it.

This decision was not open to derivation. No arithmetic says what a name supplies. It is an
evidence-boundary decision, and it belongs to the operator.

## Decision

`SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false`.
`SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = true`.

A publisher name, source name, registry display name, dataset title, provider label or provenance
label identifies where data came from. It may support a statement about provenance itself, where the
answer names the source by its whole label. It never licenses a domain proposition through a word
inside it, never licenses a number through a figure inside it, and never licenses a forbidden
concept through a phrase inside it. Labels reach the gate through an explicit, typed channel with a
provenance (`SourceMetadataContext`), never from an answer or a prompt. A packet source with no
declared labels is refused by name, because its statements cannot be split, and reading them whole
would put its name back into the content channel.

## Alternatives considered

### Alternative A: let every word of a claim statement license (gate v1.2.0's reading)

Plausible because it is simple and it is what the gate did. Rejected because it makes support depend
on what a publisher happens to be called: a register named for tenders would license the word
"tenders" in every answer about it, whatever the register reported.

### Alternative B: move source labels into the packet's structural facts

Plausible because a source's identity is a fact about the packet. Rejected because structural facts
license things (ids, counts, canonical dimension terms), and moving a label there would hide the
same leak one channel along. The structural channel keeps exactly the facts it had.

### Alternative C: drop label words from the support universe entirely

Plausible because it closes the leak with the least machinery. Rejected because it would refuse a
true provenance statement (*"The source is Tenders Electronic Daily."*), which the evidence plainly
supports. The label is kept, typed, and licenses its own whole occurrence as a name.

### Alternative D: special-case the one publisher whose name caused the finding

Rejected without much deliberation: a rule written for one name protects nothing against the next
one (*Contracts Daily*, *Buyers Weekly*, *Market Activity Observatory*), and it would be tuning the
gate on the answer that prompted it.

## Pros

- Support depends on what a source reported, not on what it is called.
- The refusal is truthful. It no longer claims a word was never supplied when it was supplied inside
  a name. It says the only supplied occurrence is inside a metadata label.
- Provenance statements stay supportable.
- Labels are auditable: each one names the registry document it came from.

## Cons

- An answer that names a source by a partial or abbreviated form (an acronym, a shortened title) is
  not read as naming it, so the words of that form are read as words. Only the registry's own names,
  and the canonical name without its trailing qualifier, are labels. Abbreviations are not guessed.
- A label whose words ARE a gated term (a provider literally called *Market Demand*) cannot be told
  apart from the term, so it never masks in an answer. Such a source's name, used as a name, would be
  refused.
- Every caller of the v1.3.0 gate must now build a metadata context. There is no default, by design.

## Consequences

Gate `second-opportunity-output-gate@1.3.0` implements this decision through
`opportunity-support-universe@2.0.0`, which splits supplied statements into
`SOURCE_CONTENT_STATEMENT` and `SOURCE_METADATA_LABEL` beside the unchanged
`PACKET_STRUCTURAL_FACT` and `TRUSTED_LIMITING_OR_DEFINITIONAL_FACT`. Gates v1.1.0 and v1.2.0 are not
changed, and historical verdicts still resolve against the code that produced them.

## Compliance

CI gate 77 re-derives the decision record from the code constant
`SOURCE_METADATA_EVIDENCE_BOUNDARY_DECISION` and refuses a record whose owner, type, derivation flag
or boolean has moved. The frozen v1.3.0 tests include the brief's metadata matrix on synthetic
labels, and the adversarial probe of Mission 1.84.11 includes a label treated as a factual statement,
a publisher label treated as domain evidence and a dataset title treated as domain evidence.
