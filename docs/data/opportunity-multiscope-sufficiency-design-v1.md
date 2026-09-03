# Multi-scope sufficiency — a design, deliberately not activated

**Status:** DESIGN ONLY. Nothing in this document is implemented, and
`opportunity-sufficiency@1.0.0` is unchanged and still the only rule that runs.
**Written by:** Mission 1.34 §10.

---

## 0. Why this is a document and not code

Mission 1.34 §10 says it plainly: existing packets must reproduce their current
formability results, and a future contextual category row must not automatically
satisfy a requirement intended for direct product evidence.

The safe way to guarantee that is not to write a careful multi-scope rule and
hope it is conservative. It is to give contextual evidence **no path at all** to
the input sufficiency reads, and then to write down what a future rule would have
to decide. That is what was built:

```text
ScopedOpportunityEvidencePacket
    .direct_dimensions            <- built ONLY from rows whose role is DIRECT
    .direct_counting_dimensions   <- what a sufficiency rule may read
    .contextual_dimensions_by_scope  <- keyed by scope, reachable by no union
```

There is no property on that class that unions the two, because the union is the
sentence *Docker supports MARKET_ACTIVITY*.

**So today's answer to "can contextual evidence make a packet formable?" is a
structural no, not a policy no.** A policy no can be relaxed by editing a
threshold. A structural no has to be built, which is a decision somebody makes on
purpose.

---

## 1. The question a future rule would have to answer

`opportunity-sufficiency@1.0.0` asks two things of a packet: at least 2 eligible
rows, and at least 2 distinct counting dimensions. Both were written when every
row in a packet observed the packet's subject. With scopes, each splits in two:

| | direct | contextual |
|---|---|---|
| row count | rows observing the subject | rows observing a broader scope |
| dimension diversity | dimensions of the subject | dimensions of a container |

A multi-scope rule has to say what it wants of each, and the honest starting
position is that **the existing two requirements keep their existing meaning and
apply to the direct half only.** Anything else changes what `HYPOTHESIS_FORMABLE`
has meant since Mission 1.28, retroactively, for every packet already recorded.

---

## 2. Three candidate rules, and what is wrong with each

**A. Contextual evidence counts toward diversity.** Rejected outright. It is the
scope laundering §16 forbids, arriving through the sufficiency rule instead of
through a sentence: a packet would become formable because a procurement category
was observed, and the hypothesis that followed would be about Docker.

**B. Contextual evidence counts toward the ROW requirement but not the DIMENSION
requirement.** Superficially attractive — it looks like it only measures
substance. It is still wrong: the row requirement exists so that a hypothesis
rests on more than one observation OF THE SUBJECT, and a category row satisfies
it without observing the subject at all. Two rows where one is context is one
row about the subject.

**C. A separate, additional gate that contextual evidence may only tighten.**
The only shape worth considering. A packet is formable on its direct half exactly
as today; contextual evidence can then only add limitations, never remove one,
and never move a packet from insufficient to formable. Its effect on the verdict
is monotonic in one direction, which is checkable.

Even C needs a decision this mission does not have the evidence to make: **what
is contextual evidence FOR, if it cannot make anything formable?** The honest
candidate answers are that it bounds a hypothesis's wording, that it tells a
reader what is known about the space the subject sits in, and that it makes an
absence visible — *the category shows procurement activity and nothing shows any
for the product*. None of those is a sufficiency question, which is itself a
finding: contextual evidence may belong in the hypothesis and not in the gate.

---

## 3. What would have to exist before a V2 rule is written

1. **At least one real, reviewed scope relation.** There are none
   (`scope-relation-registry-v1.json` is empty on purpose), so no packet in this
   deployment can hold contextual evidence, so no rule can be tested against
   anything real. Writing a rule now would be fitting to a case nobody has seen.
2. **A decision about what contextual evidence changes**, from §2 above.
3. **A statement of what a multi-scope hypothesis may conclude**, which is §26's
   wording contract taken one step further than Mission 1.34 took it.

---

## 4. What is frozen until then

- `opportunity-sufficiency@1.0.0` is unchanged, in version and in behaviour.
- `evaluate()` reads `OpportunityEvidencePacket`, which contains only direct
  membership as it always did.
- `ScopedOpportunityEvidencePacket.direct_counting_dimensions` is what a future
  rule would read, and it is built from direct rows alone.
- Every existing packet reproduces its Mission 1.28 result. Verified by
  regenerating `opportunity-preparation-v1.json` after this mission's changes:
  **exactly one field differed across the whole artifact**, the recorded
  `subject_registry` version, and every packet id, dimension set, eligibility
  count and sufficiency verdict was identical.
