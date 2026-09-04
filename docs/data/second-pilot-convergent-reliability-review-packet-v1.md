# Second pilot — the convergent TED reliability question

**Status:** `READY_FOR_SECOND_PILOT_RELIABILITY_REVIEW`. Prepared by Mission
1.42, 2026-09-04. **No value is supplied, suggested or implied.**
**Machine-readable:** [second-pilot-convergent-reliability-review-packet-v1.json](second-pilot-convergent-reliability-review-packet-v1.json)

---

## 0. One correction to the premise, before anything else

The mission brief expected **4 Evidence rows across 2 Claims**. The live
deployment holds **6 rows across 4 Claims** — and the scope is still exactly one,
exactly the five expected fields, resolving `NO_APPLICABLE_ASSESSMENT`.

| claim | class | currency | division | evidence |
|---|---|---|---|---:|
| `02248c91` | CONTRACT_AWARD_NOTICE | EUR | **92** | 2 |
| `bf4e4b48` | CONTRACT_NOTICE | EUR | **92** | 2 |
| `6389d1bf` | CONTRACT_NOTICE | SEK | 92 | 1 |
| `73e834c4` | CONTRACT_AWARD_NOTICE | EUR | **90** | 1 |

**Why: a reliability scope carries no classification division and no currency.**
It is five fields — source, resource, record kind, claim type, proposition kind —
so it reaches *every* convergent claim from this measurement, including the
**division-90** one and the SEK one, not just the two multi-Evidence claims.

This is the scope contract working exactly as ADR-026 specifies, and it is not
drift. But it changes what you are being asked: **one judgement here binds six
Evidence rows across four Claims and two CPV divisions.** The division-90 Claim's
only witness is the Signal derived in Mission 1.15.10, before the second pilot
existed, so this judgement reaches back past the pilot that prompted it.

---

## 1. The question

> **How dependable is this kind of measurement for this kind of proposition?**

It is **not**: whether TED is trustworthy · whether TED is legally approved ·
whether procurement is reliable · whether CPV 92 is attractive · whether the
market is real · whether the Claim is true · whether the Opportunity is good ·
whether the Evidence is independent · whether EUR is reliable.

The scale is `[0.0, 1.0]` with **no threshold labels**, because the architecture
defines none.

**The scope, all five fields, matched in full or not at all:**

```text
source_id         ted-eu
resource_id       notices/eforms-contract-and-award
record_kind_id    procurement_notice
claim_type        OBSERVED
proposition_kind  source_published_classification_value_contrast_witnessed
```

---

## 2. Why the existing TED 0.5 does not answer this

There is already a `HUMAN_REVIEW` assessment at `0.5` for
`source_reported_procurement_value_contrast`. **It does not bind here, it must not
be copied, and it is not a baseline** — it appears in this packet only as
historical other-scope context.

**The proposition kinds differ, and that field is load-bearing.** The resolver
correctly returns `NO_APPLICABLE_ASSESSMENT`, and 6 leak checks confirm neither
assessment reaches the other's scope.

| | detailed | convergent |
|---|---|---|
| asserts | that within a **named** set of notices, the largest stated amount exceeded the smallest | that the source published **at least one bounded set** of notices in a named class and division whose stated amounts stand in the named relation |
| cohort membership | part of the **identity** | moved to Evidence **provenance** |

**Shared measurement semantics** — same source, resource and record kind; same
BT-161 amount; same field and companion currency; same reading direction (what
TED *stated*, never what anyone paid); same conformance boundary.

**What convergence newly raises:**

- an **existential is monotone** — once a qualifying cohort is published, no later
  notice can falsify it. Whether that makes the proposition more dependable or
  merely **harder to falsify** is a judgement, and they are not the same thing;
- it carries **no period**, because H-37 leaves TED's publication-date semantics
  unestablished;
- it asserts about a **class**, so it depends on the classification being what the
  source says it is;
- **two cohorts are asserted to witness one proposition** — an SROS step that does
  not exist for the detailed claim.

---

## 3. What the documents establish

All four are first-party eForms SDK 1.15.1, already held. **Nothing new was
retrieved**, because nothing new was needed.

| question | answer | open? |
|---|---|---|
| What does the amount mean? | BT-161 is *"the value of all contracts awarded in this notice, including options and renewals"* | no |
| How is it represented? | notice level, non-repeatable, `efac:NoticeResult/cbc:TotalAmount`, with a companion currency field | no |
| Does TED validate correctness? | **No.** 60 rules govern where BT-161 may appear; all are presence, absence or notice-type constraints, **none concerns the amount's correctness** | no |
| Can a value be withheld? | Yes, with justification and a later date (BT-195–BT-198) | no |
| **Can a published notice be corrected or amended?** | **nothing held answers this** | **OPEN** |
| Who assigns the CPV code, and can it change? | a contracting authority assigns one to **its own contract**; whether it can later change is not established | **half open** |
| Does the source report the values? | yes — read as published, nothing computed, no currency converted, nothing imputed | no |

### Applicability of the four existing basis rows

| document | verdict |
|---|---|
| BT-161 definition | **REUSED** — defines what the amount means, unchanged by whether the cohort is named |
| `fields.json` BT-161-NoticeResult | **REUSED** — and more load-bearing now: the companion currency field is what makes a currency-pure cohort expressible |
| 60 business rules, none about correctness | **REUSED** — identical limitation under either proposition |
| BT-195–BT-198 withholding | **PARTIALLY_APPLICABLE** — the fact is unchanged, its *weight* is not. Under the detailed claim, withholding bounds what a named cohort represents; under an existential it cannot falsify the claim. **You decide how much that matters.** |

---

## 4. Failure modes, by origin

| failure mode | origin | documented | mitigation |
|---|---|---|---|
| a stated amount is wrong and conforms anyway | SOURCE | yes | the claim's wording is bounded to what was *stated* |
| a result value is withheld | SOURCE | yes | the proposition is existential |
| **a published notice is later corrected or superseded** | **HISTORICAL_REVISION** | **no** | **none** |
| two currencies compared as one | EXTRACTOR | yes | currency is a cohort-key field since 1.1.0, plus the validation that catches a forced mixture |
| per-lot compared with whole-notice | EXTRACTOR | yes | amount scope, same double guard |
| classification projected to the wrong division | NORMALIZER | yes | a multi-division notice joins **no** cohort rather than the first listed |
| **two cohorts treated as witnessing one proposition when they do not** | **CONVERGENCE_CONTRACT** | yes | ten fixed identity fields, deterministic, refuses unclassified facts. **This mode does not exist for the detailed proposition** |
| one witness counted twice | CONVERGENCE_CONTRACT | yes | `witness_key`, plus the Mission 1.41 Evidence-identity repair |
| the acquisition window shaped which cohorts exist | COLLECTOR | yes | existential wording; the risk is entirely in how a reader summarises it |

**The largest residual unknown is the correction policy.** It has no document, no
mitigation, and it bears directly on whether a witnessing cohort still witnesses.

---

## 5. Engineering validation is recorded separately, and is not basis

Mission 1.41 reproduced the historical division-90 Signal semantically under the
new extractor. Mission 1.39 proved the convergence contract through the real
repository. Mission 1.41 repaired Evidence identity. The currency and scope
guards are tested.

**None of this may be used as documentary basis.** It establishes that the
implementation does what its specification says. It establishes **nothing** about
how dependable TED's source-reported amounts are, and rewarding the system
numerically because its tests pass is exactly the error to avoid.

**Currency grain being correctly bounded does not imply reliability**, and
**`DISJOINT` observation overlap does not imply independence** — independence
stays `UNKNOWN` on all six rows with zero groups.

---

## 6. Operator worksheet

**Scope — TED convergent procurement value contrast**

```text
source_id         ted-eu
resource_id       notices/eforms-contract-and-award
record_kind_id    procurement_notice
claim_type        OBSERVED
proposition_kind  source_published_classification_value_contrast_witnessed
```

**Question 1 — Do you have enough documented information to make an accountable
reliability judgement for this exact measurement and this exact proposition?**

```text
YES / NO   ______
```

**If NO** — leave the assessment absent. The six Evidence rows stay
`NON_SCORABLE`, the resolver keeps returning `NO_APPLICABLE_ASSESSMENT`, and the
two multi-Evidence Claims remain unavailable. **That is the designed behaviour,
not a gap.** NO is a real answer.

**If YES:**

```text
Reliability [0.0, 1.0]  ______________________________

Rationale               ______________________________

Stated limitation       ______________________________

Reviewer                ______________________________
```

**Confirm:**

- [ ] This is not a source-wide TED score.
- [ ] This is not a probability the Claim is true.
- [ ] This is not copied from the existing TED 0.5.
- [ ] This is not a score for CPV division 92.
- [ ] This does not establish independence.
- [ ] This does not calibrate the aggregation profile.
- [ ] This judgement was made by the named reviewer.

**Nothing above is pre-filled**, and the reviewer is not inferred from a git
author, a PR author, an OS username, the existing assessment or this
conversation. You must supply it for this scope.

---

## 7. What a value here would not do

It would not calibrate anything — `REFERENCE_PROFILE_V1` stays `UNCALIBRATED`, and
reliability review is not calibration. It would not establish independence. It
would not become a TED-wide coefficient. It would not apply to CPV division 92 as
a category — **the scope carries no division at all**. It would not make the
Claims true, and it would not make the aggregation output a probability.
