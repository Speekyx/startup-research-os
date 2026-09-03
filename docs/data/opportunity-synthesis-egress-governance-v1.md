# Opportunity Synthesis Egress Governance V1

Version: 1.0
Status: Authoritative
Created: 2026-09-02 (Sprint 1 / Mission 1.29)
Use profile: `local-private-research-v1`
Processing purpose: **bounded external inference for Opportunity hypothesis synthesis**

---

## §1 What this document decides, and what it does not

Mission 1.28 found the Opportunity Engine blocked twice over: by evidence
breadth, and by external-model transmission governance. This addresses the second
and **does not pretend to solve the first**.

It answers one question for four sources under one profile:

> May the derived canonical representation of this source's Evidence be
> transmitted to an approved external inference provider, for the purpose of
> constructing a bounded Opportunity hypothesis?

**Not** public redistribution, **not** customer-facing redistribution, **not**
model training, **not** fine-tuning, **not** embedding, **not** raw-source
resale. A different purpose is a different assessment.

Four questions stay independent, as ADR-033 requires:

| question | where it is answered |
|---|---|
| may a model READ this material? | `model_processing`, per source review |
| may it LEAVE this deployment? | `external_model_transmission`, per source review |
| what does the processor DO with it? | `model-provider-policy-v1.json` |
| does this deployment permit that class of egress? | `external_model_egress`, per use profile |

`model_processing = PERMITTED` implies nothing about transmission, and an
acquisition permission implies nothing about either.

---

## §2 What would actually be transmitted

Established by reading `serialize_packet_for_model`, not by imagining a whole
source. The payload carries exactly nine top-level keys:

`packet_id`, `subject`, `procedures`, `source_families`, `dimensions`,
`dimension_bounds`, `independence`, `claims`, `evidence_ids`.

Of those, only `claims` and `subject` carry anything source-derived, and both are
**canonical representations this repository composed**:

```text
World Bank Open Data reported that "SP.POP.TOTL" for "France" increased
between "2018" and "2019" by 223713.

The GDELT Project reported that, in its "web-ngrams/1gram" stream under source
language label "ENGLISH", the term "climate" appeared 11 more times in source
bucket "20260830190000" than in the preceding source bucket "20260830184500".
```

**There is no raw source payload anywhere in it.** No collected record, no API
response body, no article text, no notice payload, no personal data. That is not
a mitigation applied at transmission time; it is a property the Opportunity
packet already had, because a packet holds references rather than copied truth
(Mission 1.28 §7).

The bound is enforced rather than described. `transmission.py` holds
`opportunity-transmission-representation@1.0.0`: an **allowlist** of permitted
keys, a list of named prohibited representations, and a set of personal-data
markers checked at every depth. An unrecognised key refuses — a denylist is a
list somebody must remember to extend, and the field nobody remembered is the
one that leaks. The serializer calls the check on the assembled payload and
raises rather than trimming: a trimmed payload is a different packet from the one
the decision authorised.

---

## §3 The decisions

| source | decision | recorded |
|---|---|---|
| `wikimedia-pageviews` | **PERMITTED** | local review v2 |
| `world-bank` | **PERMITTED_WITH_CONDITIONS** | local review v2 |
| `gdelt` | **PERMITTED_WITH_CONDITIONS** | local review v2 |
| `ted-eu` | **UNRESOLVED — assessed here, NOT recorded in the registry** | §7 below |

The brief's `REQUIRES_REVIEW` maps onto the existing `PolicyAssessment` value
**`UNCLEAR`**, whose own definition is *"The documents address it ambiguously.
The correct result when a reading requires legal judgment this system must not
make."* No enum member was added: `PolicyAssessment` is a generated closed enum
and extending one is a contract change with an ADR behind it.

---

## §4 Wikimedia Pageviews — PERMITTED

The only unconditional permission in this catalog, and it is unconditional
because the instrument leaves nothing to condition.

The authorised resource `metrics/pageviews/per-article/en.wikipedia.org` is
licensed **CC0 1.0** by the operator's own Analytics API access policy, under a
heading reading *Data licensing*. CC0 Section 1 defines Copyright and Related
Rights to include database rights under Directive 96/9/EC **by name**; Section 2
waives them *"overtly, fully, permanently, irrevocably and unconditionally"*,
*"in all territories worldwide"*, *"in any current or future medium"* and *"for
any purpose whatsoever, including without limitation commercial"*.

There is no act of reproduction, transfer or communication left for a licence to
restrict. **No attribution condition is written**, deliberately: Mission 1.19
established that CC0 creates no attribution obligation, that a rendered credit is
a courtesy, and that writing a condition asserting an obligation the licence does
not create leaves a later reader unable to tell a duty from a habit. Every
transmitted Claim names Wikimedia Analytics in its own wording regardless.

**The permission is governance, not epistemics.** The measurement stays a count
of requests for one article on one wiki in one day under the platform's own
requester class. It does not become a reader count, a customer count, demand,
adoption, popularity or willingness to pay. The operator's own automated-traffic
classification remains heuristic by its own documentation.

**Unresolved:** transmission of a bulk-dumps payload is not assessed; that route
is refused by name and no such payload is held.

---

## §5 World Bank — PERMITTED_WITH_CONDITIONS

Decided on the **CC BY 4.0 legal code**, retrieved for this mission rather than
on the Data Catalog summary page the existing review rests on.

Section 2(a)(1) grants the right to *"reproduce and Share the Licensed Material,
in whole or in part"* — two acts joined by *and*, so **reproduction is granted in
its own right and does not depend on Sharing**. Section 1 defines Share as
providing material *"to the public"*. A contracted processor performing inference
for one operator is not the public, so transmission is at most reproduction, and
reproduction is granted.

**The attribution obligation is not triggered, and attribution happens anyway.**
Section 3(a)(1) opens *"If You Share the Licensed Material"*, so an act that is
not Sharing carries no credit obligation and no licence boilerplate needs pasting
into a prompt. The obligation on derived product surfaces is unchanged and still
carried by the `attribution-surface` condition. Separately, every transmitted
Claim opens *"World Bank Open Data reported that"*.

**The database right is addressed by the instrument rather than left open.**
Section 4 grants extraction and reuse where sui generis database rights apply.
Unlike TED, there is no unresolved question here, because the licence speaks to
it.

**The condition, and it is NARROWER than acquisition's.** Acquisition authorises
datasets licensed `CC-BY-4.0` **or** `ODbL-1.0`. This transmission decision
covers **CC-BY-4.0 only**. ODbL is excluded: its share-alike obligations attach
to Derivative and Collective Databases and its definition of *Publicly Use* is a
question this review has not answered, and an unanswered question is not a
permission. Every authorised indicator — including `indicator/SP.POP.TOTL`, the
only one with canonical Evidence — records `licence: CC-BY-4.0`, so the narrowing
costs nothing today and stops a later ODbL dataset inheriting a permission nobody
assessed.

**That the transmission allowlist is tighter than the acquisition allowlist is
the point**, not an inconsistency: they are different questions.

**The permission is governance, not epistemics.** A population change is not
market demand, buyer count, customer count or a commercial opportunity.

**Unresolved:** whether transmission to a processor is Sharing (nothing rests on
it — reproduction is granted either way, and a future PUBLIC surface would have
to answer it); whether ODbL permits this transmission (NOT ADDRESSED, and no ODbL
resource is held).

---

## §6 GDELT — PERMITTED_WITH_CONDITIONS

GDELT's Terms of Use, re-retrieved for this mission and unchanged, state that
*"all datasets released by the GDELT Project are available for unlimited and
unrestricted use for any academic, commercial, or governmental use of any kind
without fee"*, that users *"may redistribute, rehost, republish, and mirror any
of the GDELT datasets in any form"*, and that *"any use or redistribution of the
data must include a citation to the GDELT Project and a link to this website"*.

A grant permitting redistribution **in any form** comfortably contains a
transmission to a processor, which is far less than redistribution.

**The condition is about SCOPE, and it is the whole point of this entry.** The
grant runs to datasets **the GDELT Project releases**. The authorised resources
are `web-ngrams/1gram` and `web-ngrams/2gram`: counts of how often a term
appeared, which are GDELT's own aggregation and are recorded as
`content_origin: PLATFORM_LICENSED`.

**Third-party news article text is not a GDELT-released dataset.** A permission
over an aggregate measurement is not a permission over the articles the aggregate
was computed from. So:

- **permitted representation** — the aggregate lexical measurement and the Claim
  derived from it;
- **prohibited representation** — article bodies, headlines, publisher-attributed
  text and article URLs.

**That condition costs nothing to meet and is still worth writing.** This
deployment holds no article text at all: the collector reads gzipped ngram files
and nothing else. The condition therefore constrains a future collector rather
than the present one, which is exactly when a scope limit should be written down.

**The citation obligation IS triggered here, unlike the others.** GDELT attaches
it to *"any use or redistribution"*, not only to redistribution — so unlike
CC BY 4.0, whose obligation begins *"If You Share"*, this one is live for a
transmission. It is met as a property of the payload: every transmitted Claim
opens *"The GDELT Project reported that"*.

**The permission is governance, not epistemics.** A change in how often a term
appeared in a news corpus measures what media organisations published. The
standing invariant is unaltered: GDELT lexical frequency alone never satisfies a
demand claim, not weakly, not with low relevance and not with a caveat.

---

## §7 TED — assessed, unresolved, and deliberately not recorded

**This is the most interesting result in the mission, and it is a refusal to
write something down.**

### The decision the evidence supports

`UNCLEAR`. Three arguments point toward permission and none is sufficient.
Mission 1.15.2 closed H-34 PERMITTED: Commission Decision 2011/833/EU defines
reuse by **purpose** and enumerates no acts, so method does not enter. The
transmitted object contains **no TED document text** — one sentence this
repository composed about an aggregate over three notices, naming no notice, no
buyer and no supplier. And sending to a contracted processor is not making
available to the public, so Article 7(2)(b) re-utilisation is not obviously
engaged.

**What defeats all three is not a legal argument but a scope one.** TED is
collectable only because a named operator recorded acceptance of
`ted-database-right-residual-exposure-accepted`, whose own text reads: a named
operator *"has read ted-eu-local-official-route-readiness-v1.md and accepted the
residual, unresolved database-right exposure **for bounded queries under this
profile**"*.

A transmission to a third party is not a bounded query. H-36A — whether a sui
generis database right **subsists** — is NOT ESTABLISHED in either direction, and
H-36B — whether it is granted or waived — is NOT ADDRESSED. The exposure the
operator accepted is still open, and transmission reaches a **new counterparty**
with it. **This repository may not widen a human acceptance on the operator's
behalf.**

### Why the decision is not in the registry

Recording it required appending local review v3. Appending one **orphans the
operator's acceptance**: a verification is pinned to the review version it was
recorded against, because a re-review can change what a condition means. That
condition is `HUMAN_CONFIRMATION`, and **no verifier in this repository may
satisfy one, by design**.

The consequence was verified against the real deployment, not predicted: with v3
in place, `build_authorization('ted-eu')` raised
`review conditions not satisfied: ted-database-right-residual-exposure-accepted`,
and TED stopped being acquirable.

**Mission 1.29 §0 forbids exactly that**: *"Do not rewrite source acquisition
eligibility merely because model transmission is being assessed. These are
separate questions."* Flipping TED from acquirable to not-acquirable as a side
effect of assessing egress is the collapse that sentence exists to prevent. So
the append was **withdrawn**, and TED's local review line is untouched at v2.

**Nothing operational was traded away.** `NOT_ASSESSED` and `UNCLEAR` both refuse
at the runtime gate, so TED's transmission standing is identical either way. What
the registry loses is the *distinction*, and this document carries it instead.

**The asymmetry is the general finding.** The other three sources' conditions are
all CAPABILITY-verified, so a version bump costs a re-check and nothing else.
TED's rests on a human acceptance. **A source whose approval rests on a human
decision is a source whose review cannot be cheaply amended** — and that cost is
invisible until a mission tries to amend one.

### H-39, the named blocker

> **H-39.** Does the operator's accepted residual database-right exposure extend
> from bounded QUERIES to TRANSMISSION of derived material to a third-party
> processor? The existing acceptance is scoped to bounded queries in its own
> words, so the answer is NO by default, and only the operator can change it.

### The operator act that would close it, written down and not recorded

> A named operator reads this document, and accepts the residual, unresolved
> database-right exposure for TRANSMISSION of the derived canonical
> representation to an APPROVED external model provider under
> `local-private-research-v1`, having understood that H-36A and H-36B remain open
> and that the counterparty is new.

Exactly as Mission 1.15.6 wrote an acceptance statement without recording it:
**writing that sentence here is not recording it**, and nothing in this mission
has recorded it. Acting on it means appending review v3 *and* re-recording the
acceptance against v3, in that order, in a mission that owns TED.

### Preserved, explicitly

H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED. Local approval
APPROVED_WITH_CONDITIONS with all four conditions intact and verified. Search API
and Open Data SPARQL the only routes; `ted-bulk-xml` and the historical CSV
refused by name. Training not authorised. Commercial profile still
REQUIRES_REVIEW. No circumvention of anything.

**And what the TED dimensions do not mean**, restated because a governance entry
is where this gets forgotten: the single TED Evidence row carries
`MARKET_ACTIVITY`, `BUYER_OR_BUDGET_EXISTENCE` and `ECONOMIC_VALUE`. None of them
is willingness to pay for a SaaS, supplier revenue, an amount actually paid to
one supplier, market size, or demand for any proposed product. eForms BT-161 is
the value of all contracts awarded in a notice **including options and renewals**
and may be lawfully withheld.

---

## §8 Provider route

Reused unchanged from Mission 1.23. `anthropic` is `APPROVED` on its Commercial
Terms of Service route, on the contractual sentence *"Anthropic may not train
models on Customer Content from Services"*, with retention recorded as
`BOUNDED_30_DAYS` rather than smoothed into a stronger word.

**No provider authorization was broadened and no provider was re-reviewed.** No
source review names a vendor; the two domains meet once, at runtime. No model
call was made and none is needed to record a permission.

The requirement every `PERMITTED_WITH_CONDITIONS` decision here depends on — a
provider that does not train on submitted content and documents bounded
retention — matches the recorded posture. No mismatch found.

---

## §9 Personal data

None of the four representations contains personal data, and none needs to.

- **Wikimedia** — aggregate request counts for an article. No requester identity
  is acquired or held.
- **World Bank** — an indicator code, a country, two years, a number.
- **GDELT** — a term, a language label, bucket ids, a count.
- **TED** — an aggregate over three notices; the natural-person contact block was
  excluded **at acquisition** by `ted-personal-data-minimisation`, so it is not in
  the corpus to transmit.

`PERSONAL_DATA_MARKERS` refuses `owner`, `author`, `editor`, `username`, `email`,
`contact`, `phone`, `address`, `ip_address`, `person`, `supplier_name`,
`buyer_name` and `winner_name` at any depth of the payload — a bound on a future
serializer, since today's emits none of them.

---

## §10 A refusal reason that was wrong

Mission 1.23 built `InferenceRefusalReason` with codes for `NOT_ASSESSED` and for
a refusal. `UNCLEAR` and `NOT_ADDRESSED` had no code of their own and fell through
to `SOURCE_EXTERNAL_MODEL_TRANSMISSION_REFUSED` — telling an operator a reviewer
decided against them when a reviewer actually decided the question needs a human.

`SOURCE_EXTERNAL_MODEL_TRANSMISSION_UNRESOLVED` was added, and the packet gate
reports `UNRESOLVED` rather than `REFUSED` for those states. **An operator can
close an open question and cannot argue with a decision**, so the two must not
share a code — the same argument ADR-033 made for `NOT_ASSESSED`, one state
further along.
