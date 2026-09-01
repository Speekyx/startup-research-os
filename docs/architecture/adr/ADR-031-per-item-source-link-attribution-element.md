# ADR-031 — A Per-Item Source Link in the Attribution Vocabulary

**Status:** Accepted · **Date:** 2026-09-01 · **Mission:** Sprint 1 / 1.18
**Amends:** `AttributionElement` (Mission 1.4 §6,
`acquisition-authorization-v1.md`). **Supersedes:** nothing.

---

## Context

### The rule this ADR exists to satisfy

`AttributionElement` is a closed enum, and its own description says why:

> A closed enum because the renderer branches exhaustively: an element it does
> not recognise must be a contract change, never a silently dropped requirement.

Adding a member is therefore a contract change with an ADR, exactly as Ontology
V2 §14.2 requires. This is that ADR.

### What the vocabulary could not express

Mission 1.18 reviewed Stack Exchange, whose Subscriber Content is CC BY-SA 4.0.
That licence's attribution clause requires, among other things:

> a URI or hyperlink to the Licensed Material to the extent reasonably
> practicable

The seven existing members are `SOURCE_CREDIT`, `LICENCE_IDENTIFIER`,
`EXACT_NOTICE`, `MODIFICATION_STATEMENT`, `DATASET_DOI`, `ACCESS_DATE` and
`DISCLAIMER`. **None of them is a link to the specific item the content came
from.**

`DATASET_DOI` is the nearest and is wrong twice over: it is a DOI rather than a
URL, and it identifies a **dataset** rather than one contributed item. A Stack
Exchange question is not a dataset, and forcing the question URL into that
member would make every consumer that branches on `DATASET_DOI` wrong about what
it is holding.

### Why this was not obvious sooner, and why that is the worrying part

**It is not a Stack Exchange problem.** World Bank and Eurostat are both CC BY
4.0, whose attribution clause carries the same URI requirement, and both are
configured with `SOURCE_CREDIT`, `LICENCE_IDENTIFIER` and
`MODIFICATION_STATEMENT` only. The gap has been in the configuration since
Mission 1.3.

**And the condition reported SATISFIED throughout.** The
`source-attribution-display` capability verifies that the **declared** elements
resolve and that a missing one is refused. It has no knowledge of what any
licence requires, and cannot: it is a mechanism check, and it was working
correctly.

So the failure shape is the dangerous one. Not a broken check reporting failure,
but a correct check reporting success over an **under-declared obligation**. A
capability that verifies "the elements you listed can be rendered" says nothing
about whether you listed the right elements, and nothing in the system was
asking the second question.

## Decision

**Add one generic member: `SOURCE_ITEM_LINK`.**

> A link to the specific item the content came from, where the licence requires
> the material itself to be locatable. A per-item value; it cannot be defaulted.

### Why this name

- **Generic, not source-specific.** `STACK_EXCHANGE_URL` would have been a
  vocabulary member for one publisher, which is the shape the enum exists to
  prevent — the same argument Mission 1.17 made for keeping a loader fix generic
  rather than renaming one source's conditions.
- **Not licence-specific either.** `LICENSED_MATERIAL_URI` is CC's own wording
  and would read as a CC member. The concept — *link to the item this came
  from* — is general, and a future source could require it under terms that are
  not Creative Commons at all.
- **Parallel to the existing style.** `SOURCE_CREDIT` credits the source;
  `SOURCE_ITEM_LINK` links to one item of it.

### It is supplied, never configured

Like `DATASET_DOI` and `ACCESS_DATE`, and for the same reason: the value belongs
to a specific record. A fixed string here would attribute every item to one
place, which is precisely the failure the licence's clause is written against.

`AttributionFacts` gains `source_item_link`, and `value_for` returns it.

## Consequences

**What this permits.** The Stack Exchange attribution obligation can now be
declared in full, so the `stack-exchange-attribution` condition means what it
says. **The mission's own gate was that it must not be marked satisfied over an
obligation the contract could not represent**, and this is what clears it.

**What it corrects elsewhere.** World Bank and Eurostat declare the element too,
in the same change. Their obligation did not change — CC BY 4.0 always required
this — only the configuration's ability to record it. **No historical research
data is touched**: this is what a product surface must render, and the
per-record values were always held in provenance.

**What it does not reach.** GDELT and FRED are not amended. GDELT requires *"a
citation to the GDELT Project and a link to this website"* — a link to the
publisher, not to an item, which `SOURCE_CREDIT` already carries. FRED's
obligation is an endorsement notice, which is `EXACT_NOTICE` shaped. Adding a
member does not mean adding it everywhere, and each source's obligation is still
read from that source's own terms.

**What stays unsolved, and is the real lesson.** Nothing in the system checks
that a declared attribution obligation is **complete** against the licence it
comes from. The capability checks the mechanism; a reviewer checks the licence;
nothing joins them. This ADR fixes one instance and does not fix the class, and a
future mission that wants to could compare declared elements against a licence's
known requirements — but that needs a machine-readable model of licence
obligations, which does not exist and is a larger question than this.

## Alternatives considered

**Use `DATASET_DOI` for the question URL.** Rejected. It is neither a DOI nor a
dataset, and every consumer branching on that member would be wrong about what it
holds. This is the alternative that costs nothing today and produces a wrong
render later.

**Leave the element out and note it.** Rejected, and it was the position Mission
1.18's first half took. It was defensible while the mission was writing a review;
it stops being defensible once the same mission marks the attribution condition
satisfied and proceeds to acquire under it. Recording a gap is not the same as
declining to rely on it.

**Add a free-text element.** Rejected. The enum's whole property is exhaustive
branching, and a member meaning "something else" makes the renderer's
completeness unprovable.
