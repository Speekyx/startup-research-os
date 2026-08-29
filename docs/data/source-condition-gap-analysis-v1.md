# Source Condition Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.4 §3 **before** any code was
written, so the capabilities built afterwards can be checked against what the
conditions actually say rather than against what was convenient to build.
**Date:** 2026-08-29
**Reads:** the nine condition records created by Mission 1.3, taken from
[`source-catalog-v1.json`](source-catalog-v1.json) (review version 2 of each
approving source) and `registry.source_review_conditions`.
**Related:** [`source-registry-v1.md`](source-registry-v1.md) §4,
[`source-review-results-v1.md`](source-review-results-v1.md),
[`mission-1.3-report.md`](../architecture/mission-1.3-report.md) §12–§14.

---

## 0. What this document is and is not

It is an inventory of every condition standing between an approving review and a
collector, with an honest statement of what could mechanically establish each
one.

**It is not a plan to satisfy them.** Several are satisfiable, one is not
satisfiable in any environment that lacks a credential, and a handful of
obligations recorded by Mission 1.3 are deliberately **not** conditions at all
and must not be turned into code. §5 lists those separately, because the most
likely way this project could go wrong is by quietly promoting a legal sentence
into a boolean.

Nothing was changed while this analysis was written.

---

## 1. The nine conditions

Three approving sources, three conditions each. `condition id` is the
deterministic `uuid5` the loader writes, so a row can be found in the database
without a join; the composite key `source / review version / key` is the one a
human should quote.

| # | Condition id | Source | Rev | Key | Verification | Detail | State |
|---|---|---|---|---|---|---|---|
| 1 | `b2de8714-b5cf-5c2d-b118-287eafa9a4f6` | `world-bank` | 2 | `attribution-surface` | `CAPABILITY` | `source-attribution-display` | UNSATISFIED |
| 2 | `84abbfa8-8964-50ab-9b33-7f6d0fa621e3` | `world-bank` | 2 | `dataset-licence-allowlist` | `CAPABILITY` | `dataset-licence-filter` | UNSATISFIED |
| 3 | `265cf376-168c-52a1-b6ff-5bbe7d805eb6` | `world-bank` | 2 | `microdata-excluded` | `ACCESS_METHOD` | `indicators-api-only` | UNSATISFIED |
| 4 | `9aa31970-79ee-56c3-9250-c0c23a4a2bae` | `eurostat` | 2 | `attribution-surface` | `CAPABILITY` | `source-attribution-display` | UNSATISFIED |
| 5 | `d7627b89-38c6-58b5-a7bf-c2f60a5e8483` | `eurostat` | 2 | `geographic-exclusion` | `CAPABILITY` | `eurostat-geographic-filter` | UNSATISFIED |
| 6 | `feda2c31-ba9b-5a01-a181-4a1edbec6cbb` | `eurostat` | 2 | `trade-data-exclusion` | `CAPABILITY` | `eurostat-trade-exclusion` | UNSATISFIED |
| 7 | `217b656c-422e-5d14-a4d7-64493eebdd91` | `fred` | 2 | `fred-api-key` | `CONFIG_REFERENCE` | `FRED_API_KEY` | UNSATISFIED |
| 8 | `7aab7679-6b64-5dcd-927a-aa03ca9429e9` | `fred` | 2 | `fred-endorsement-notice` | `CAPABILITY` | `source-attribution-display` | UNSATISFIED |
| 9 | `25aa1cb3-28f0-5bee-b1d4-52f1b28ff206` | `fred` | 2 | `copyrighted-series-excluded` | `CAPABILITY` | `fred-copyright-series-filter` | UNSATISFIED |

All nine are unsatisfied. That is the state Mission 1.3 left and the state a
catalog load always produces: `satisfied` is environment state and a catalog can
never assert it.

---

## 2. Condition by condition

Each entry quotes the condition **verbatim** from the record, then says what
would have to be true for a machine to establish it.

### 1 — `world-bank / attribution-surface`

> A product surface exists that displays the required World Bank attribution and
> a statement of any modifications, on every view derived from this source.

**Requires:** a first-class attribution model that can hold the World Bank
credit, the licence identifier and a modification statement; a renderer that
refuses to produce output when a required element is missing; and a surface that
returns it. The evidence behind the review is the Data Catalog licensing page:
CC-BY 4.0 permits commercial use *provided appropriate credit is given and
changes are indicated*, so credit and change-indication are both load-bearing,
not decorative.

**Classification: MACHINE_VERIFIABLE.** What a machine can check is that the
named capability is implemented, enabled and passes its own conformance check.
See §4 for what that does *not* prove.

### 2 — `world-bank / dataset-licence-allowlist`

> The collector requests only datasets whose recorded licence is CC-BY 4.0 or
> ODbL, and skips every other licence.

**Requires:** a per-resource licence gate with an explicit allowlist, and a
fail-closed answer for a resource whose licence is unrecorded. The review is
explicit that **licensing is per dataset, not per platform** — the same platform
distributes Microdata under a research-only licence and third-party data under
external terms — so a source-level approval must not be readable as a
resource-level one.

**Classification: MACHINE_VERIFIABLE.**

### 3 — `world-bank / microdata-excluded`

> The Microdata Library is excluded from every request path.

**Requires:** two facts, both readable from the registry and the compliance
configuration. First, the source's approved access scope is the indicators API
and nothing else. Second, an exclusion rule for the Microdata Library exists and
denies. The Microdata Research License permits statistical and scientific
research only and forbids redistribution without a prior written agreement, so
this is not a preference.

**Classification: MACHINE_VERIFIABLE.** This is the strongest of the nine: both
halves are registry facts today, independent of any collector.

### 4 — `eurostat / attribution-surface`

> A product surface displays the Eurostat citation — dataset DOI and access date
> — on every view derived from this source.

**Requires:** the same attribution capability as #1, with two *additional
required elements* the condition names explicitly: the dataset DOI and the
access date. Both are per-resource values a collector must supply; neither can
be defaulted.

**Classification: MACHINE_VERIFIABLE.**

### 5 — `eurostat / geographic-exclusion`

> The collector excludes data for countries outside the EU, EFTA and official
> acceding/candidate countries.

**Requires:** a geography gate over the resource descriptor. The copyright
notice makes this a condition of **commercial** reuse specifically, which is our
assessed use case, and names the USA, Japan and China as examples of what must
be removed.

**Classification: MACHINE_VERIFIABLE**, with one deliberate conservatism
recorded in §3.

### 6 — `eurostat / trade-data-exclusion`

> The collector excludes the named Liechtenstein, Switzerland and Austria
> trade-data exceptions.

**Requires:** three enumerated rules, which the evidence states precisely:
Liechtenstein and Switzerland as **declaring countries** from 1995 for the
HS/SITC/BEC/NSTR classifications, and Austria at CN 8-digit. Precise enough to
encode without interpretation, which is why it is a condition.

**Classification: MACHINE_VERIFIABLE.**

### 7 — `fred / fred-api-key`

> A FRED API key is configured in the environment.

**Requires:** a check that the configuration key `FRED_API_KEY` is present and
non-empty, answering `CONFIGURED` / `NOT_CONFIGURED` **without reading, logging
or returning the value**. The registry stores the key *name*; it has never
stored and must never store the value.

**Classification: CONFIGURATION_DEPENDENT.** Mechanically checkable, but the
answer is a property of the deployment rather than of the code. It is
`NOT_CONFIGURED` in CI and in every development environment that has not been
given a key, and no capability can change that.

### 8 — `fred / fred-endorsement-notice`

> The product prominently displays the exact notice the terms require.

**Requires:** the exact sentence held **verbatim** in compliance configuration
and rendered unmodified:

> This product uses the FRED® API but is not endorsed or certified by the
> Federal Reserve Bank of St. Louis.

The registered trademark symbol and the wording are part of the requirement. A
paraphrase is a different sentence and does not satisfy the terms.

**Classification: MACHINE_VERIFIABLE** — including a byte-for-byte comparison
against the recorded notice, which is a genuinely mechanical check rather than a
judgement about adequacy.

### 9 — `fred / copyrighted-series-excluded`

> The collector excludes every series whose notes contain 'Copyright', or
> records per-owner permission for it.

**Requires:** a per-series gate that denies when the notes contain the marker,
and denies when the notes are absent — an unread series is not a series known to
be uncopyrighted. The terms are the reason: *"before using data series owned by
third parties for anything other than your own personal use, you must contact
the data owner to obtain permission"*, and the Bank cannot grant that permission
on the owner's behalf.

The clause **"or records per-owner permission for it"** is the half that must
not be automated. Recording a permission is a human act with a document behind
it; a code path that could grant it would be the system manufacturing a right it
does not have.

**Classification: MACHINE_VERIFIABLE for the exclusion half**; the permission
half is `HUMAN_CONFIRMATION` by nature and is deliberately left unimplemented
(§5).

---

## 3. Summary

| Classification | Count | Conditions |
|---|---|---|
| `MACHINE_VERIFIABLE` | **8** | 1, 2, 3, 4, 5, 6, 8, 9 |
| `CONFIGURATION_DEPENDENT` | **1** | 7 (`fred-api-key`) |
| `HUMAN_CONFIRMATION` | 0 | — |
| `EXTERNAL_VENDOR_ACTION` | 0 | — |
| `NOT_IMPLEMENTABLE_YET` | 0 | — |

Zero conditions require a vendor action. That is not luck: Mission 1.3 put the
vendor-action sources (Reddit, Product Hunt, Hacker News, Google Trends, Stack
Exchange) in `REQUIRES_REVIEW`, so they never reached a condition list. The
sources that reached one are the three whose terms already permit the assessed
use.

**Capabilities implied by the nine, deduplicated:**

| Capability | Conditions | Kind |
|---|---|---|
| `source-attribution-display` | 1, 4, 8 | attribution rendering and surface |
| `dataset-licence-filter` | 2 | licence allowlist over resources |
| `indicators-api-only` | 3 | access-method restriction + resource exclusion |
| `eurostat-geographic-filter` | 5 | geographic exclusion over resources |
| `eurostat-trade-exclusion` | 6 | enumerated resource exclusions |
| `fred-copyright-series-filter` | 9 | third-party-content exclusion |
| `FRED_API_KEY` | 7 | credential availability |

Six capabilities and one credential check. `source-attribution-display` is
shared by all three sources and carries **different required elements** for
each, which is why it is one capability parameterised by configuration rather
than three.

### One deliberate conservatism

Condition 5 names *"the EU, EFTA and official acceding/candidate countries"*.
The EU-27 and the four EFTA states are a stable, enumerable list. The set of
official acceding and candidate countries is not — it changes, and the copyright
notice does not enumerate it.

The allowlist will therefore contain **EU-27 and EFTA only**. Candidate-country
data will be denied even though the terms would permit it. That is stricter than
required and never more permissive, and it is recorded here so nobody later
mistakes the omission for an oversight. Widening it needs a re-read of the
notice and a recorded decision, not a code edit.

---

## 4. What a `CAPABILITY` verification does and does not establish

This distinction decides whether the whole exercise is honest, so it is stated
once, plainly.

Seven of the nine conditions are phrased as claims about a **collector** — *"the
collector requests only…"*, *"the collector excludes…"*. No collector exists.
A verifier therefore cannot observe a collector obeying anything.

What a `CAPABILITY` verification asserts is exactly what the contract says the
value means: **a named product capability is implemented and enabled.** It
asserts that the gate exists, is wired, and gives the right answers to the cases
the review evidence names — including denying the unknown case.

It does **not** assert that a future collector went through it.

That gap is closed structurally rather than by verification: a collector may
only execute with an `AcquisitionAuthorizationContext`, the context can only be
built for a source that passes the canonical gate, and the resource rules travel
inside it. A collector that reached a dataset by another path would be a
collector that bypassed its own authorization.

**This places a requirement on Mission 1.5**, recorded here so it is not
discovered later: the first collector must obtain every resource through the
authorization context's resource gate, and a conformance test must assert that
it has no other path to a URL. Until such a test exists, the guarantee is
architectural, not observed.

---

## 5. Obligations that are NOT conditions, and must not become code

Mission 1.3 recorded these in the reviewers' prose `conditions` and
`open_questions`. None of them is a `required_condition`, and §4 of the Mission
1.4 brief forbids translating a vague legal sentence into a machine rule that
Mission 1.3 did not already define. They are listed so they stay visible.

| Source | Obligation | Why it stays out of code |
|---|---|---|
| `world-bank` | *"If any ODbL dataset is used, honour its share-alike obligation on redistribution."* | Share-alike binds **redistribution**. The assessed use case is derived analytics, not redistribution. Encoding a redistribution rule now would be encoding a rule for an activity nobody has designed |
| `world-bank` | *"Confirm per dataset, at collection time, which licence applies."* | This is the licence allowlist's input, not a rule. The gate denies an unrecorded licence; deciding what a dataset's licence actually is remains a per-dataset fact a collector must carry |
| `eurostat` | *"…state any modification with the Eurostat non-responsibility disclaimer."* | The exact disclaimer wording is not in the retrieved evidence. Inventing it would violate the rule that exact required notices are preserved, not composed. The attribution model therefore requires a **supplied** disclaimer for modified data and refuses to render without one |
| `eurostat` | *"Record the SDMX endpoint base URL and its documented query-size and rate limits."* | Unknown. Recorded as unknown; no limit is invented, and the authorization context reports the absence rather than a number |
| `fred` | *"Do not use FRED, ALFRED or Federal Reserve Bank in a hostname, do not use their marks, and do not imply endorsement."* | A product and branding decision about a product that does not exist. No code path chooses a hostname |
| `fred` | *"…or records per-owner permission for it."* | Obtaining permission from a third-party copyright owner is a human act with a document behind it. A code path that could record one would let the system grant itself a right |
| `fred` | *"Determine whether any series the research use case needs is copyrighted."* | Requires knowing which series the use case needs, which requires a research design that does not exist yet |
| all three | Jurisdiction / GDPR applicability (H-12) | Requires legal input. `jurisdiction_review_required` stays true and no code sets it false |

---

## 6. Expected outcome of satisfying what is satisfiable

Stated in advance, so the result cannot be rationalised afterwards.

| Source | Conditions | Satisfiable by capability | Outcome |
|---|---|---|---|
| `world-bank` | 3 | 3 | would become **collector-eligible** |
| `eurostat` | 3 | 3 | would become **collector-eligible** |
| `fred` | 3 | 2 | stays **blocked** on the runtime credential |

The other ten sources are untouched. None of them has an approving review, so no
capability built here can move them: satisfying a condition on a `RESTRICTED`
source changes nothing, because the state blocks first.

**Collector-eligible is not collector-enabled, and neither is a collector.**
Even for a source that clears the gate, `collector_enabled` stays false, no
collector module exists, and the planner must continue to refuse to dispatch an
acquisition job.
