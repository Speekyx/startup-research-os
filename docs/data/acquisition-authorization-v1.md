# Acquisition Authorization V1

**Status:** Authoritative. Created in Mission 1.4.
**Version:** 1.0
**Date:** 2026-08-29
**Governs:** the compliance capability layer, condition verification, and the
context a collector must hold before it may run.
**Related:** [`source-registry-v1.md`](source-registry-v1.md),
[`source-condition-gap-analysis-v1.md`](source-condition-gap-analysis-v1.md),
[`source-compliance-v1.json`](source-compliance-v1.json),
[ADR-016](../architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md),
[`data-retention-policy-v1.md`](data-retention-policy-v1.md).

---

## 0. What this document is for

The Source Registry (Mission 1.0) answers *may we collect from this source*.
Mission 1.3 made three reviews approving and left nine conditions standing
between those approvals and a collector.

This document specifies what happens between those two facts:

```text
APPROVED_WITH_CONDITIONS
        ↓
condition records                  Mission 1.3, one row each
        ↓
compliance capabilities            what the condition requires to exist
        ↓
verification records               who checked, when, what, and why
        ↓
the eligibility gate               unchanged; it just has an input now
        ↓
AcquisitionAuthorizationContext    what a collector receives, or nothing
```

**The registry gate stays authoritative.** Nothing here is a second gate, an
override or a fast path. A verification changes one input to the existing gate —
whether a named condition is satisfied — and the gate decides as it always did.

---

## 1. The rules that cannot be traded away

Invariants, in the sense `source-registry-v1.md` §1 uses the word.

1. **No source becomes eligible through a boolean.** Not a manual UPDATE, not a
   catalog field, not a test fixture, not a developer shortcut. A condition is
   cleared by a verifier that records what it checked, and the database refuses
   the boolean without one.
2. **A vague legal sentence never becomes a machine rule.** If Mission 1.3 did
   not state a condition mechanically, no code invents one. Human and legal
   obligations stay human and legal, and the honest verification kind for them
   is `HUMAN_CONFIRMATION`.
3. **`UNKNOWN` never becomes `SATISFIED`.** A verifier that could not run says
   so, and the result blocks exactly as a failure does. The two are kept apart
   because they call for different work.
4. **No verifier writes a human confirmation.** Recording one is a person's act
   with a document behind it. There is no code path in this repository that
   creates one.
5. **A source-level approval is not a resource-level one.** Each dataset, series
   or record is authorised separately, and one whose licensing scope was never
   established is refused.
6. **The registry stores credential key names, never values.** A verification
   answers `CONFIGURED` / `NOT_CONFIGURED` and the value never enters the
   process.
7. **Eligible is not enabled, and neither is a collector existing.** Three
   distinct facts, and the system reports all three separately.

---

## 2. Compliance configuration

[`source-compliance-v1.json`](source-compliance-v1.json) holds the parameters of
each obligation: required attribution elements and their exact texts, licence
allowlists, geographic allowlists, enumerated exclusions, note markers, access
restrictions and data-minimisation profiles.

It is **data, not branches**. There is no `if source_id == "fred"` anywhere in
the compliance package; there is a configuration entry holding FRED's exact
required notice, and code that renders whatever notice a source's entry names.

Three properties follow:

- **Exact wording survives.** Where the terms prescribe a sentence, it is stored
  verbatim and rendered unmodified. A validator asserts that every exact notice
  appears in the evidence that established it, so nobody can quietly reword one.
- **A source with no entry is denied.** Nothing in the file grants anything.
- **An entry names the review version it was written against.** A re-review can
  change what a condition means, so configuration written against an older
  version yields `UNKNOWN` rather than continuing to clear the condition.

---

## 3. Attribution

All three approving sources require attribution and **each requires something
different**, which is why attribution is a model rather than a constant.

| Element | Meaning |
|---|---|
| `SOURCE_CREDIT` | Credit to the source, in the wording its terms require |
| `LICENCE_IDENTIFIER` | The licence the *resource* is distributed under |
| `EXACT_NOTICE` | A sentence the terms prescribe. Verbatim, never composed |
| `MODIFICATION_STATEMENT` | What was changed, where the licence requires changes to be indicated |
| `DATASET_DOI` | The persistent identifier of the specific dataset |
| `ACCESS_DATE` | When the data was retrieved |
| `DISCLAIMER` | A disclaimer required alongside modified data |

A requirement is either **configured** — it carries its text and is identical
for every artefact — or **supplied**, meaning it must come from whoever produced
the artefact. A dataset DOI belongs to a dataset and an access date to a
retrieval; neither can be defaulted, and rendering fails without them.

`EXACT_NOTICE` can never be supplied. Its entire point is that our wording does
not enter it.

### Enforcement, not documentation

**A required element cannot be omitted.** Rendering raises rather than dropping
it. There is no partial rendering, because a notice missing half its obligation
looks like attribution and is not.

**An obligation survives transformation.** An `AttributedArtifact` carries the
obligations of everything it was derived from, `derive` has no parameter that
removes one, and combining two artefacts unions their obligations:

```text
RawRecord → NormalizedRecord → Evidence → Claim → ResearchResult
```

The downstream model is not built here — there is no raw record and no
collector. What is built is the pattern the chain has to follow, so that a
future transformation cannot be written in a way that loses the credit.

### What was deliberately not written

The Eurostat non-responsibility disclaimer. Its exact wording is not in the
retrieved evidence, so it is a **supplied** element and rendering refuses
without it. Composing the sentence would be the opposite of preserving a
required notice exactly.

---

## 4. Resource scope

Seven rule kinds, each demanded by an actual condition. Not a rule language: a
general expression grammar would be a place to encode a legal sentence as a
boolean, which §1.2 forbids.

| Rule | Denies |
|---|---|
| **Rights basis** | A resource with **none established**. Unconditional — see §4.1 |
| Content origin | `THIRD_PARTY`, and `UNKNOWN` where licensing scope matters |
| Licence allowlist | A licence outside the list, a basis that is not `NAMED_LICENCE`, and a resource with no licence recorded |
| Dataset family | An excluded family, an unrecorded family where the scope requires one, and — since Mission 1.9.2 — a family **outside the reviewed set** |
| Geography allowlist | A geography outside the set, and a resource naming none |
| Enumerated exclusion | A named carve-out, including one whose other dimension is unrecorded |
| Note marker | A third-party ownership marker, and notes that were never read |

**Every rule denies; none permits.** A resource is allowed only when no rule
objected, and a descriptor that omits what a rule needs is denied by that rule.

### 4.1 Two rules Mission 1.9.2 added, and the holes they closed

Both were reachable only by a hand-made descriptor — a collector builds one
*from* an authorised entry, which always carries these fields. That is the same
standing the transport's host check has, and the argument for writing them is the
one the transport already makes: *a guard that only exists further up is a guard
a future caller can route around.*

**An unestablished rights basis is now a refusal in its own right.** It had been
checked only inside the licence-allowlist rule, so a descriptor with **no basis
at all** passed for every source whose scope enumerates no licences — Eurostat,
FRED, and pointedly GDELT, the one source whose resources are authorised by a
direct grant rather than by a licence. "Nothing established" read as approval on
exactly the source where the basis is the whole story. The rule is unconditional
because every other rule answers a question a particular review may or may not
have asked, and *what authorises this at all* is not one of those.

**A positive family allowlist.** `require_dataset_family` refused a resource that
could not say what it is; it did not refuse one that says something nobody
reviewed, because a family no reviewer had rejected was indistinguishable from
one a reviewer had approved. `allowed_dataset_families` answers *did a reviewer
look at that kind of thing*, and `excluded_dataset_families` continues to answer
*was it looked at and rejected* — both are kept, because an empty exclusion list
would say nobody had looked. `None` on the other three sources, which is
unchanged behaviour.

### `ResourceContentOrigin`

`PLATFORM_LICENSED` · `THIRD_PARTY` · `UNKNOWN`

The third value exists because it is the common case for an aggregator, and
guessing it either way would be wrong. It fails closed.

### The enumerated-exclusion rule, stated precisely

Each dimension an exclusion states resolves to one of three answers. One
**negative** answer clears the exclusion outright — Austrian CN-8 data is not
excluded by the Liechtenstein rule. Otherwise, if at least one dimension
positively matched and any other is **unrecorded**, the exclusion applies: a
resource that is trade data in an excluded classification and does not say who
declared it is not a resource known to be declared by someone else.

A descriptor matching nothing positively — an ordinary statistics dataset with
no trade classification — is not excluded. Denying it would turn the rule into a
blanket refusal, which is a check that has stopped checking anything.

---

## 5. Credentials

The registry stores a configuration **key name**. A verification reads presence
and emptiness from the environment and answers `CONFIGURED` / `NOT_CONFIGURED`.

The returned object holds the name and a boolean and has no field a value could
occupy, so it cannot leak from a `repr`, a log line, a JSON response or an
exception message — it was never in it. A key set to an empty string counts as
`NOT_CONFIGURED`, because that is what a half-finished deployment leaves behind
and treating it as present would move the failure from a gate that explains
itself to a 401 from a third party.

**A missing credential is a normal answer, not an error.** §17 of the mission
brief names the distinction this preserves:

> compliance capability satisfied **versus** runtime credential currently
> available

FRED is the case: every policy capability its approval requires exists, and the
credential does not. It is **design-eligible** and not collector-eligible, and
the canonical gate still refuses it.

---

## 6. Condition verification

A verification records: which condition, which verifier, at which version, when,
the result, why, and what was inspected.

### Results

`SATISFIED` · `UNSATISFIED` · `UNKNOWN` · `NOT_APPLICABLE`

Four values rather than a boolean. **Only `SATISFIED` clears a condition.**
`UNKNOWN` blocks exactly as `UNSATISFIED` does, and the two are kept apart
because one is a bug and the other is missing work.

### Dispatch

| Verification kind | Verifier | Establishes |
|---|---|---|
| `CAPABILITY` | `capability:<name>` | The named capability is registered and its conformance check passes |
| `ACCESS_METHOD` | `access-restriction:<name>` | The registry holds exactly the approved access profiles, and the excluded material is refused |
| `CONFIG_REFERENCE` | `credential-availability` | The named key is present and non-empty |
| `RETENTION_LIMIT` | *(none registered)* | Nothing. Returns `UNKNOWN` and blocks |
| `HUMAN_CONFIRMATION` | `human-confirmation` | Nothing, unconditionally. Returns `UNKNOWN` |

`RETENTION_LIMIT` has no verifier because no condition uses it. Building one
would be an unused abstraction, and `UNKNOWN` is the honest answer for a check
that does not exist.

### What a `CAPABILITY` verification does and does not establish

Stated here because it is the load-bearing limitation of the whole layer.

Seven of the nine conditions are phrased as claims about a **collector**, and no
collector exists. A `CAPABILITY` verification asserts exactly what the contract
says the value means: *a named product capability is implemented and enabled*.
It asserts the gate exists, is configured, and refuses what it must — including
the unknown case. It does **not** assert that a collector went through it.

That gap is closed structurally rather than by verification: a collector may
only run with an authorization context, and the resource rules travel inside it.
**Mission 1.5 must add a conformance test that its collector obtains every
resource through the context's resource gate and has no other path to a URL.**
Until then the guarantee is architectural, not observed.

### Persistence

`registry.source_condition_verifications` is an append-only log; the history of
a condition is part of what makes its current state trustworthy.
`registry.source_review_conditions.satisfied` remains the gate's input, synced
from the latest verification, and a `BEFORE` trigger refuses to set it true with
no `SATISFIED` record behind it.

Re-verification takes a source **out** of eligibility as readily as into it. A
capability that was removed produces `UNSATISFIED` on the next run and the
boolean is cleared.

### Two views, kept apart

| View | What it shows | Where |
|---|---|---|
| Catalog | The reviews, with no condition verified | `source-catalog-v1.md`, generated and committed |
| Environment | The same reviews with the verifiers run here | `sros-source eligibility`, `conditions`, the API |

A committed file cannot hold the environment view without drifting with the
machine that produced it, and a catalog can never assert its own conditions
satisfied. The two legitimately disagree, and each says which it is.

---

## 7. `AcquisitionAuthorizationContext`

What a collector receives, and the only thing that lets it do anything.

| Field | Answers |
|---|---|
| `source_id`, `canonical_name` | which source |
| `approval_state`, `review_version`, `reviewed_at`, `next_review_at` | under which review |
| `access` | the approved paths, with credential key names and rate-limit metadata |
| `resource_scope` | which resources are in scope, and which are excluded |
| `retention` | the resolved rule, stricter constraint already applied |
| `attribution` | what attribution follows this data |
| `data_minimisation` | what may be requested, and what must not |
| `acquisition_bounds` | how much of the source one job may take |
| `verifications` | the condition snapshot the authorization rests on |
| `issued_at` | when |

`authorize_resource(descriptor)` is the only sanctioned way to reach a specific
dataset. Holding the context permits nothing on its own.

### 7.1 Acquisition bounds — *how much*, kept apart from *what*

Mission 1.9.2. Every rule in §4 answers **what** may be reached. A published
bulk dataset raises a second question — **how much of it** — and GDELT's
WEB-NGRAM files are the first case where nothing in the terms answers it: two
files every fifteen minutes since 2019, and a grant that limits none of it.

`context.authorize_job_size(file_count)` returns the reasons a job exceeds the
reviewed ceiling, or nothing. Three properties, and each is the point:

- **the ceiling belongs to the review.** A collector that chose its own bound
  would be setting its own permissions;
- **a bound with no stated basis is refused at load time**, because a number that
  nobody can re-check survives every later review by looking deliberate;
- **`None` means no ceiling was reviewed, not that any size is fine.** Every
  source that predates this mission is in that state, and spelling it
  `unlimited` would turn an unasked question into an answer.

The unit is whatever the review found meaningful. For GDELT it is the **file**,
because that is what the source publishes and what a request costs — and because
the observed contract removed the obvious alternative: each file spans every
language, so a job cannot ask for fewer languages and language is not a dimension
of the request at all.

### 7.2 Acquisition readiness — four facts, derived

`evaluate_readiness(source, config)` reports, and refuses nothing:

```text
eligible         may we collect from this source at all
resource_ready   is there a concrete resource the review actually authorises
implemented      does a collector exist
enabled          is collection switched on here
```

`resource_ready` is the one that did not exist. Between Missions 1.7 and 1.9.1,
GDELT was eligible with an empty `datasets` tuple: the gate said yes, the
resource layer refused everything, and "eligible" was the most specific word
available — which read as further along than it was. Eurostat is in that state
today, and the diagnostic now says so.

**Nothing is stored.** A persisted `resource_ready` would be a copy of a
derivation, which is the argument `source-registry-v1.md` §3 already makes for
eligibility being a view. `enabled` reflects the record it is handed: the catalog
file is the governance record and `sros-source enable` writes the deployment
switch to `registry.sources`, so the two can differ and the CLI says which it
read.

### The boundary

```text
request collection
    → load the registry
    → verify conditions
    → evaluate eligibility
    → build AcquisitionAuthorizationContext    ← fails here, or not at all
    → collector
```

`build_authorization` runs the canonical gate and raises when it does not pass.
That is the enforcement mechanism: not a flag the collector is asked to check,
but the absence of the object it needs.

A source that passes the gate and has no compliance entry is **also** refused.
There would be no attribution obligation, no resource rules and no minimisation
profile to hand a collector, and handing one nothing is not the same as handing
it permission.

### Rate limits

Exposed as `known: false` when no limit is documented, which is the case for all
three approving sources. A number here would be a guess a collector would then
trust. A collector told `known=False` must throttle conservatively on its own,
which is a different instruction from being handed an invented figure.

### Retention

Governance input, never a collector's choice. The context carries the resolved
`EffectiveRetention` and the stricter constraint has already won; there is no
setter.

---

## 8. Eligible, enabled, implemented

Three facts, reported separately, and the distinction is the one most likely to
be collapsed by someone in a hurry.

| Fact | Means | Where it lives |
|---|---|---|
| **collector-eligible** | The governance gate passes | `registry.source_eligibility`, derived |
| **collector-enabled** | The operational switch is on | `registry.sources.collector_enabled` |
| **collector implemented** | Code exists that can collect from it | `sros_acquisition.IMPLEMENTED_COLLECTORS` |

`IMPLEMENTED_COLLECTORS` is empty. `sros-source enable` refuses a source that is
not in it, because a switch that gets ahead of the thing it switches reads, to
anyone looking at the registry, as "this is running". The orchestrator answers
the same question with its own fail-closed default and blocks acquisition under
`NO-COLLECTOR-IMPLEMENTED`; it cannot import the acquisition package
(`service-boundaries.md`), so the two agree by both defaulting to refusal rather
than by sharing a constant.

---

## 9. Current state

| | |
|---|---|
A snapshot, refreshed at Mission 1.9.2. Anything counted here is derived, so
`sros-source readiness` is the current answer and this is the shape of it.

| | |
|---|---|
| Conditions | 12, across 5 approving sources |
| Verifiers | 3 kinds registered, 1 deliberately absent, 1 deliberately inert |
| Capabilities | 5, each asserted by its own conformance check |
| Collector-eligible | **world-bank, eurostat, gdelt** — with no credential configured |
| Design-eligible, not runnable | **fred** — `FRED_API_KEY` not configured |
| **Resource-ready** | **world-bank, gdelt.** Eurostat is eligible and has no authorised resource |
| Collectors implemented | 1 — `world-bank` |
| Collectors enabled | per deployment; the catalog record enables none |
| Raw records | 6, all World Bank |

---

## 10. Still open

- **Eurostat has no authorised resource.** It has been collector-eligible since
  Mission 1.4 and `context.datasets` is empty, so every Eurostat resource fails
  closed. That is the gate working, and it is also the reason "eligible" was
  never the last word.
- **No acquisition bound exists for any source but GDELT** (§7.1). The question
  has not been asked for the other three, which is different from having been
  answered permissively.
- **Eurostat's disclaimer wording** — not in the retrieved evidence, so it is
  required as supplied text rather than composed. Resolving it means re-reading
  the copyright notice, not editing configuration.
- **Acceding and candidate countries** are absent from the Eurostat geography
  allowlist, deliberately and more strictly than the terms require. Widening it
  needs a re-read and a recorded decision.
- **Jurisdiction analysis** — unchanged and still human (H-12).
- **Per-workspace source configuration** — an organisation's own credentials and
  quotas would be a tenant-scoped table. Source identity stays global; nothing
  here anticipates one.
