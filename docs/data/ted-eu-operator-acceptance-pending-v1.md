# TED-EU Operator Acceptance — Pending V1

**Superseded, and kept as the record of a refusal.** Mission 1.15.6.1, first
attempt. **The acceptance was recorded at the second attempt** — see
[`ted-eu-operator-risk-acceptance-v1.md`](ted-eu-operator-risk-acceptance-v1.md).

This document is preserved unchanged below because a refusal that gets deleted
once it is resolved teaches nobody why it happened. Everything it says was true
of the **first** statement.

---

**Authoritative when written.** An operator acceptance was **supplied**, and
it was **not recorded**.

**State: `APPROVING_BUT_NOT_ELIGIBLE`, unchanged.** The condition
`ted-database-right-residual-exposure-accepted` is still **OUTSTANDING**,
`AcquisitionAuthorizationContext` still **cannot be built**, and no verification
row was written.

**This is not a rejection of the operator's decision.** The decision is real,
specific and recorded verbatim below. What is missing is part of the
acknowledgement set the condition requires, and it is missing because the
statement supplied is shorter than that set — not because the decision is in
doubt.

---

## 1. What the operator supplied

Verbatim, in the original French, which is the authoritative text:

> J’accepte le risque résiduel TED pour `local-private-research-v1`, en
> comprenant que l’utilisation 100 % locale réduit l’exposition mais ne
> constitue pas une garantie juridique ni une résolution de H-36.

As supplied in English by the operator alongside it:

> I accept the residual TED risk for `local-private-research-v1`, understanding
> that 100% local use reduces the exposure but does not constitute a legal
> guarantee or a resolution of H-36.

**This is an operator-supplied statement, not a generated one.** It is reproduced
here unchanged, and nothing in this document rewords it into stronger or weaker
language than the operator used.

## 2. What it establishes, and it is not nothing

Four things, explicitly and in the operator's own words:

| | |
|---|---|
| **The residual TED risk is accepted** | *"J’accepte le risque résiduel TED"* |
| **Scoped to one profile, named exactly** | *"pour `local-private-research-v1`"* |
| **It is not a legal guarantee** | *"ne constitue pas une garantie juridique"* |
| **H-36 is not resolved by it** | *"ni une résolution de H-36"* — the operator names the open question and says the acceptance does not close it |

The fourth is the one that matters most and it is unambiguous. The operator did
not accept the risk *because they believed it resolved*; they accepted it
**knowing it is unresolved**, which is exactly the shape a residual-risk
acceptance has to have.

The statement also records a correct understanding that **local deployment
reduces exposure without eliminating it** — the half of the deployment model
`docs/CLAUDE.md` warns is most easily taken backwards, stated the right way
round.

## 3. What the condition requires

The requirement is the condition itself, which is versioned data on TED local
review v2 and is what the gate names:

> A named operator **has read `ted-eu-local-official-route-readiness-v1.md`** and
> **accepted the residual, unresolved database-right exposure for bounded
> queries** under this profile. No verifier can satisfy this, by design.

It is a conjunction, and
[`ted-eu-authorization-bootstrap-v1.md`](ted-eu-authorization-bootstrap-v1.md)
§6.2 renders it as the acknowledgement an operator records.

## 4. The comparison, item by item

| §6.2 | Requirement | Supplied? |
|---|---|---|
| 1 | has read `ted-eu-local-official-route-readiness-v1.md` and `ted-eu-authorization-bootstrap-v1.md` in full | **no** |
| 2 | **H-36A is NOT ESTABLISHED** — nothing determines whether a sui generis right subsists, or who holds it | not named; *"H-36"* is named as unresolved, without the A limb |
| 3 | **H-36B is NOT ADDRESSED** for broad corpus extraction | not named; same |
| 4 | the approval is deliberately narrow; it rests on four instruments and **none of them is a database-right grant** | **no** |
| 5 | it further rests on **bounded queries, minimisation at acquisition and no redistribution — and falls if any of those stops being true** | **no** |
| 6 | not a legal clearance, **no lawyer has reviewed it**, resolves neither limb | partly — *"pas une garantie juridique"* is supplied; the absence of legal review is not |
| 7 | accepted for `ted-eu` under `local-private-research-v1`, **at review version 2, and for nothing else** | profile supplied; **review version and the "nothing else" limit are not** |
| — | does not extend to the commercial profile, a public deployment, bulk XML, `ted-csv`, another source, or a materially changed review | **no** |

**Three of the seven are absent entirely**, and one of those three is the one
that gives the acceptance a boundary.

## 5. Why this was not recorded

**Two absences are load-bearing rather than ceremonial.**

**Item 5 is the boundary condition.** It says the acceptance *falls* if bounded
queries, acquisition-time minimisation or the absence of redistribution stops
being true. Without it, what would be recorded is an acceptance with no stated
conditions of validity — and a residual-risk acceptance that does not say what it
depends on is one that survives the disappearance of what it depended on.

**Item 1 is the informed-consent half of the conjunction.** The readiness
document is where the *specific* limits live: bulk XML blocked, `ted-csv`
blocked, coverage from 1 March 2023 with a six-form-type slice before it, the
authenticity limit that makes every future claim *"TED reported…"* rather than a
statement about the underlying contract, and the monetary semantics that must not
be flattened. An acceptance of a risk whose shape the accepter has not confirmed
reading is a different act from the one the condition describes.

**And inferring the rest is the one thing this mechanism exists to prevent.** The
supplied statement demonstrates real understanding, and it would be easy to
reason that somebody who names H-36 and disclaims legal guarantee has evidently
read the document. **That reasoning is exactly the failure mode.** It would be
this repository supplying the part of an acceptance the human did not supply,
which is what a `HUMAN_CONFIRMATION` condition exists to make impossible. The
house rule applies unchanged: *uncertainty is never permission*, and a two-part
requirement with one part unaddressed is not satisfied — `NOT_ADDRESSED` on any
load-bearing element blocks, whatever the others say.

**What was NOT the reason.** Not that seven items exist and seven must be
recited. The comparison above was made against the condition's own text and
against what each item does, not against a count.

## 6. What is structurally guaranteed either way

Recorded because it narrows what still has to be said, and because two of §6.2's
clauses ask the operator to recite what the machinery already enforces:

- **Profile scoping is structural.** A verification row hangs off a condition,
  the condition hangs off exactly one review, and that review names exactly one
  `assessed_use_profile`. An acceptance against TED's local review cannot reach
  `commercial-multi-tenant-research-v1`, which does not carry the condition an
  acceptance would clear.
- **Review-version scoping is structural.** Each review version gets **its own
  condition rows** — `registry.source_review_conditions` is keyed
  `(review_id, condition_key)`, and the row id derives from the review version.
  A future local review v3 would create fresh rows with `satisfied = FALSE`, so
  a v2 acceptance cannot carry into it. **Fail-closed, with no architecture
  change needed.**
- **The route, field, redistribution, training and embedding restrictions are
  enforced by the gates Mission 1.15.6 built**, not by anything the operator
  promises. An acceptance does not widen them and could not.

So items 5 and 7 are worth recording for what they say about the operator's
understanding, not because the system depends on them being said.

## 7. The exact text still required

From [`ted-eu-authorization-bootstrap-v1.md`](ted-eu-authorization-bootstrap-v1.md)
§6.2, unchanged and reproduced in full so that nothing here is a new requirement:

> I, ⟨full name⟩, operating Startup Research OS as its single local operator,
> record the following.
>
> 1. I have read `ted-eu-local-official-route-readiness-v1.md` and
>    `ted-eu-authorization-bootstrap-v1.md` in full.
> 2. I understand that **H-36A is NOT ESTABLISHED**: nothing determines whether
>    a sui generis database right subsists in the TED corpus, or who would hold
>    it.
> 3. I understand that **H-36B is NOT ADDRESSED** for broad corpus extraction:
>    nothing establishes that such a right, if it subsists, has been granted or
>    waived.
> 4. I understand that the local approval of `ted-eu` is **deliberately narrow**.
>    It rests on Commission Decision 2011/833/EU, the TED and SIMAP legal notice,
>    the `COM_REUSE` dataset metadata and the Publications Office's own published
>    intended use for its two query routes — and that **none of those four is a
>    database-right grant**.
> 5. I understand that it further rests on bounded, purpose-scoped queries
>    through the official routes, on field minimisation at acquisition, and on
>    the fact that nothing is redistributed — and that **if any of those three
>    stops being true, the basis for this acceptance stops with it**.
> 6. I understand that **this is not a legal clearance**, that no lawyer has
>    reviewed it, and that it resolves neither H-36A nor H-36B.
> 7. I accept the residual, unresolved database-right exposure for **`ted-eu`
>    under `local-private-research-v1`, at review version 2, and for nothing
>    else**.
>
> This acceptance does **not** extend to `commercial-multi-tenant-research-v1`;
> to any future public, customer-facing, sold, subscription-based or
> multi-tenant deployment; to the bulk XML packages; to the `ted-csv` historical
> subset; to any other source; or to a materially changed future TED review.
>
> Recorded by: ⟨identifier⟩ · Date: ⟨ISO 8601⟩

**Items 6 and 7 are already substantially covered** by the statement in §1: the
operator has said it is not a legal guarantee and has scoped it to
`local-private-research-v1`. What remains genuinely unsaid is items 1, 4 and 5,
the A/B split in 2 and 3, the absence of legal review in 6, the review version in
7, and the exclusion paragraph.

**Reading the two documents is the substance of item 1**, and it is the step the
rest depends on. Items 2 to 5 are what those documents establish; an operator who
has read them can record the acknowledgement truthfully in a few minutes, and one
who has not should read them first — which is the whole point of the condition
being written as a conjunction.

## 8. What did not change

- **H-36A remains NOT ESTABLISHED. H-36B remains NOT ADDRESSED**, under both
  profiles. No acceptance could change either, and none was recorded.
- **`ted-eu` + `commercial-multi-tenant-research-v1` = `REQUIRES_REVIEW`.**
- **`ted-eu` + `local-private-research-v1` = `APPROVED_WITH_CONDITIONS`**, not
  eligible.
- **No verification row was written.** The registry holds zero verifications for
  `ted-eu`, of any result, at any version.
- **No policy, condition, route authorization, minimisation profile, verdict or
  evidence row was touched.**
- **No collector, no network call, no TED research data.**

## 9. The current refusal

```text
build_authorization('ted-eu', 'local-private-research-v1')
  review conditions not satisfied:
    ted-database-right-residual-exposure-accepted
```

Unchanged from Mission 1.15.6. **One condition, one decision, and it is a
person's to make.**

## 10. Next step

The operator records the acknowledgement in §7, as a **separate, explicit act**.
When they do, Mission 1.15.6.1 can be re-run to write the single verification
row, and the next mission after that is **TED Official Search API Collector V1 —
Local Private Research Profile**.

Until then the collector is not written, because `build_authorization` refuses
and there is nothing to build against.
