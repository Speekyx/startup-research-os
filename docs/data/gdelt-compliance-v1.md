# GDELT compliance configuration V1

**Status:** Governance record. Produced by Mission 1.8 §7–§11.
**Date:** 2026-08-30
**Governs:** the `gdelt` entry in
[`source-compliance-v1.json`](source-compliance-v1.json), review version 2.
**Related:** [`source-registry-v1.md`](source-registry-v1.md) §4,
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
[`new-source-compliance-gap-analysis-v1.md`](new-source-compliance-gap-analysis-v1.md) §6.

---

## 0. What this configuration is, and what it is not

It carries the **parameters of one obligation** so that satisfying GDELT's
condition is a configuration fact rather than a branch in collector code. It
grants nothing: like every entry in `source-compliance-v1.json`, everything here
describes a restriction, and a source with no entry is denied by the resource
gate rather than allowed.

GDELT is the only source added in Mission 1.7 whose approval survived the
materiality audit, and the reason is one sentence in its terms:

> all datasets released by the GDELT Project are available for unlimited and
> unrestricted use for any academic, commercial or governmental use of any kind
> without fee

That **grants** rather than merely failing to prohibit, which is what separates
it from `pypi`, `npm-registry` and `wikimedia-pageviews`.

---

## 1. The one condition

| | |
|---|---|
| Key | `gdelt-attribution` |
| Review version | 2 |
| Verification | `CAPABILITY` → `source-attribution-display` |
| Obligation | Every product surface derived from GDELT carries a citation to the GDELT Project and a link to `https://www.gdeltproject.org/`, on use and on redistribution |
| State | **SATISFIED**, by a verifier, on review version 2 |

Version 1 expressed this as `HUMAN_CONFIRMATION` — not because the obligation
needed a person, but because no compliance configuration existed for the source
and a condition naming a capability that cannot see any parameters resolves
`UNKNOWN` for ever. The obligation is identical; only its enforceability
changed.

### 1.1 Two conditions that were considered and not written

§6 forbids inferring conditions merely because they sound sensible, and both of
these sounded sensible.

- **An access restriction** (`ACCESS_METHOD`), by analogy with World Bank's
  `indicators-api-only`. Rejected: World Bank's exists because its review
  identified a specific carve-out — the Microdata Library — that had to be kept
  out of the request path. GDELT's review identifies no carve-out. The two
  approved profiles are recorded on the source, and that is the representation
  §9 asks for.
- **A dataset allowlist** (`CAPABILITY` → `dataset-licence-filter`). Rejected:
  World Bank needs one because its platform distributes datasets under several
  licences and the licence is a per-dataset property. GDELT names **no licence
  at all** — it grants unlimited use directly — so there is no identifier to
  match and an allowlist would deny everything for a reason the terms do not
  give.

---

## 2. Attribution (§8)

Two elements, both with wording the terms prescribe:

| Element | Text | Supplied per artefact? |
|---|---|---|
| `SOURCE_CREDIT` | `The GDELT Project` | no — fixed by the terms |
| `EXACT_NOTICE` | the citation-and-link sentence, verbatim | no — fixed by the terms |

Neither is `supplied`, which is the opposite of Eurostat's shape: its DOI and
access date are per-retrieval values that cannot be defaulted, while GDELT's
obligation is the same two strings every time.

**Three elements deliberately absent.** No `MODIFICATION_STATEMENT` (the terms
require none), no `DISCLAIMER` (the terms require none), and no
`LICENCE_IDENTIFIER` — GDELT names no licence, which is unusual enough to be
worth stating: it grants unlimited use directly rather than through a named
instrument, so there is nothing to identify. §8 forbids inventing wording where
none exists, and an empty licence field would be an invitation to fill it in.

A validator asserts the exact notice appears in the evidence that prescribed it,
so a notice composed here rather than quoted would fail.

---

## 2.1 The licence field, and why there is none (Mission 1.9.1)

The absence of a `LICENCE_IDENTIFIER` above was a finding before it was a
design: GDELT names no licence. Until Mission 1.9.1 that also made a GDELT
dataset entry **unwritable**, because `AuthorizedDataset` required a non-empty
`licence` and every candidate value was a fabrication of a different shape.

A resource now records its **rights basis** — `NAMED_LICENCE` or `DIRECT_GRANT`
— and GDELT's is `DIRECT_GRANT`, with the licence field required to be *absent*
rather than filled. See [ADR-018](../architecture/adr/ADR-018-acquisition-rights-basis.md).

A direct grant does **not** satisfy a licence allowlist. GDELT has none, so this
does not affect it; World Bank does, and its enforcement got stricter rather than
looser.

## 3. Resource scope (§10)

One rule, and it is the only one the evidence supports:

```json
"third_party_denied": true
```

**The grant is over datasets GDELT RELEASES.** GDELT aggregates worldwide news
coverage, so a record can reference or describe material the project does not
own and holds no rights over. A source-level permission must not be widened into
a resource grant the evidence does not support.

`third_party_denied` gives both halves of fail-closed:

| Resource content origin | Outcome | Why |
|---|---|---|
| `PLATFORM_LICENSED` | allowed | inside the grant |
| `THIRD_PARTY` | **refused** | the platform's approval grants no rights over it |
| `UNKNOWN` | **refused** | an unestablished origin is not an established one |

Everything else is `null` or empty, each for a stated reason rather than by
omission: no licence allowlist (no licence identifiers exist), no dataset-family
requirement (the terms draw no such distinction), no geography allowlist, no
enumerated exclusions, no note markers.

**Source-level approval is still not resource-level approval.** A future
collector receives a resource descriptor per request and each is authorised
separately, whatever the scope rules happen to be.

---

## 4. Access and rate limits (§9, §11)

Two reviewed profiles, and no others:

| Method | Label | Auth | Cost | Documented limit |
|---|---|---|---|---|
| `PUBLIC_API` | `gdelt-doc-api` | none | `FREE` | **UNKNOWN** |
| `DATASET_DOWNLOAD` | `gdelt-bulk-files` | none | `FREE` | **UNKNOWN** |

**No rate limit is invented.** GDELT publishes none on the documentation read
during Mission 1.7, so `rate_limit_known` is false on both profiles and every
numeric field is null. §11 is explicit that local pacing is not a provider
limit; a "reasonable default" recorded here would be read by a collector as the
provider's number.

Pacing a future collector is therefore an engineering decision that must not be
laundered through this file. It is recorded as an open question on the review
instead.

## 4.1 A second access route exists and is NOT authorised by this entry

Added after Mission 1.9.1's continuation found the DOC API unreachable from two
independent environments and GDELT asking researchers to use its ngram files
instead.

The WEB-NGRAM datasets live on **`data.gdeltproject.org`** and are fetched as
files, which is the **`gdelt-bulk-files`** profile — `DATASET_DOWNLOAD`, not
`PUBLIC_API`. That profile deliberately records no `endpoint_url`, so it
authorises no host, and nothing in this configuration reaches it.

**The `gdelt-doc-api` profile does not cover it.** A different host over a
different access method is a different route, and stretching an API profile to
cover a file download would be exactly the widening §10 refuses. The rights
basis carries over unchanged — GDELT's grant covers everything it releases — but
a rights grant is not an access authorisation, and the two have been kept apart
since Mission 1.0.

What that route would need is in
[`gdelt-resource-model-v1.md`](gdelt-resource-model-v1.md) §8.4: a new review
version, a reviewed minimisation category for term frequencies, and an endpoint
on the bulk profile. None of it is done here.

## 5. Authentication (§12)

None. No key, no OAuth, no account, no developer application, and therefore **no
`CONFIG_REFERENCE` condition** — §12 forbids manufacturing one where no
credential is required. `runtime_credential_references` on the authorization
context is empty, which is the correct and checkable representation of "nothing
is needed".

## 6. Retention and minimisation (§14, §15)

**Retention is the project baseline**: 30 days raw, 365 normalized. GDELT
imposes nothing stricter, so no `source_retention_policies` override exists —
an override may only shorten, and there is nothing to shorten to. The resolved
values are delivered by `AcquisitionAuthorizationContext`, not by a collector.

**No minimisation profile is written.** GDELT's terms address personal data not
at all, and the review classifies the source `PSEUDONYMOUS` on the shape of the
data rather than on a statement by the project. A minimisation profile written
now would encode a first collector's field list before a first collector exists,
which is the abstraction §7 tells us not to build. The open question about
whether extracted entity mentions constitute personal data stays on the review
where a reviewer will see it.

## 7. What is verified, and what remains a human matter

`sros-source verify` runs `source-attribution-display` against this
configuration and records `SATISFIED` with what it inspected. That clears
GDELT's only condition, and with it the last blocker on the eligibility gate.

**GDELT is collector-eligible and `collector_enabled` is false**, because no
collector exists. Eligible, enabled and implemented remain three separate facts,
and `sros-source enable` refuses a source with no implemented collector.
