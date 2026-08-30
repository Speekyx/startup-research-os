# New Source Compliance Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.8 §2–§6, **before** any
configuration or code changed, so the work can be checked against what was
measured rather than against what was hoped for.
**Date:** 2026-08-30
**Reads:** the current reviews and canonical conditions for `pypi`,
`npm-registry`, `wikimedia-pageviews` and `gdelt`; the compliance capability
registry; `source-compliance-v1.json`.
**Related:** [`source-registry-v1.md`](source-registry-v1.md) §1, §4,
[`source-review-guide.md`](source-review-guide.md) §4,
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
[ADR-016](../architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md).

---

## 0. Two questions, and the first one changes the second

Mission 1.8 asks whether PyPI's approval was consistent with *silence is not
permission*, and separately asks that Wikimedia Pageviews and GDELT be made
collector-eligible where their reviews genuinely permit it.

Those look independent and are not. Auditing PyPI requires stating the rule that
PyPI violated, and once the rule is stated it has to be applied to every
approving source — otherwise fixing PyPI **is** the one-off exception §4
forbids, pointed the other way.

Applying it changes the answer for two of the three sources this mission was
pointed at.

---

## 1. The rule, stated before it is applied

`source-registry-v1.md` §1 rule 2:

> **Uncertainty is never permission.** When the documents are silent, absent,
> unreachable, or ambiguous, the result is `NOT_ADDRESSED` / `UNCLEAR` and the
> source stays `REQUIRES_REVIEW`. There is no path from *we could not check* to
> *we may proceed*.

Mission 1.8 §4 restates it as an operational test:

> A materially unaddressed activity required by the assessed use must block an
> approval unless another authoritative grant covers it.

### 1.1 Which activities are materially required

The assessed use case, unchanged since Mission 1.0 and quoted in full in
[`source-review-results-v1.md`](source-review-results-v1.md): automated
collection of public content by a **commercial multi-tenant SaaS** for
**storage**, **derived analytics** and **LLM processing**.

Six of the eleven assessed activities are therefore load-bearing:

| Activity | Why it is required |
|---|---|
| `automated_access` | the collection is automated by definition |
| `api_use` | every approved access profile is an API |
| `commercial_use` | the product is a commercial SaaS, stated in the use case |
| `storage` | stated in the use case |
| `derived_analytics` | stated in the use case |
| `model_processing` | "LLM processing", stated in the use case |

Five are **not** load-bearing, and saying why matters as much:

- **`browser_automation`** — only if a browser profile is used, and none is.
- **`retention`** — a *limit*, not a permission. `NOT_ADDRESSED` means the
  source imposes nothing stricter than the project baseline, which is the
  baseline applying rather than a gap.
- **`redistribution`** — required only where source content is republished.
  Aggregated insight is `derived_analytics`; this is tracked but not gating.
- **`personal_data_handling`** — governed by `personal_data_risk` and by H-12,
  not by an approval gate this mission can close.
- **`attribution_required`** — an **obligation**, not a permission.
  `NOT_ADDRESSED` there means no attribution duty was found, which cannot block.

**Narrowing the use case to rescue a source is forbidden** (Mission 1.7 §9), so
the required set is fixed by the product rather than by convenience.

---

## 2. The rule applied to all eight approving sources

| Source | auto | api | comm | storage | derived | model | Verdict |
|---|---|---|---|---|---|---|---|
| `world-bank` | P | P | P | P | P | P | **holds** |
| `eurostat` | P | P | Pc | P | P | P | **holds** |
| `fred` | P | P | Pc | P | P | P | **holds** |
| `openalex` | P | Pc | P | P | P | P | **holds** |
| `gdelt` | P | P | P | P | P | P | **holds** |
| `npm-registry` | Pc | P | P | P | P | **—** | **fails** |
| `wikimedia-pageviews` | Pc | Pc | P | **—** | P | **—** | **fails** |
| `pypi` | Pc | Pc | **—** | **—** | **—** | **—** | **fails** |

`P` = PERMITTED · `Pc` = PERMITTED_WITH_CONDITIONS · `—` = NOT_ADDRESSED

### 2.1 The line the table draws is not arbitrary

Every source that holds has an **explicit licence or an explicit unlimited
grant**: CC-BY 4.0 (World Bank), the Eurostat copyright notice, the FRED terms,
CC0 (OpenAlex), and GDELT's "unlimited and unrestricted use for any academic,
commercial, or governmental use of any kind without fee".

Every source that fails rests on **terms-of-service silence**. That is the same
distinction §1 draws, arrived at from the data rather than assumed.

---

## 3. PyPI — the audit §2 asked for

**Does the authoritative evidence positively grant the assessed use? No.**

PyPI's current review cites exactly one document, the PyPI Terms of Service
(effective 2025-02-25). What it establishes, in the review's own words:

> abuse or excessively frequent requests … may result in … suspension … API
> tokens may not be shared in order to exceed PyPI's rate limitations … the API
> may not be used to download data or content for spamming purposes

Every one of those is a **prohibition**. The document contains no grant of any
kind. Consequently PyPI is the only approving source in the catalog where **not
one of the six required activities is positively permitted**: `commercial_use`,
`storage`, `derived_analytics` and `model_processing` are all `NOT_ADDRESSED`,
and the only positive findings are "the API may be called" and "do not harvest
contact details".

### 3.1 The Mission 1.7 review diagnosed this and approved anyway

Its own `review_notes`, committed:

> the approving state rests on the absence of a prohibition covering us plus the
> presence of a documented API, and commercial reuse itself is NOT_ADDRESSED

That sentence is a description of the exact move §12 of Mission 1.7 forbids —
*do not infer commercial permission from "API available" or "public content"* —
written by the reviewer who then recorded `APPROVED_WITH_CONDITIONS`. Being
precise about the failure mode in prose is not the same as acting on it, and
the state is what the gate reads.

**Outcome C.** No new documentation was retrieved that supplies the missing
grant, so PyPI is downgraded to `REQUIRES_REVIEW`. Review version 1 is preserved
unchanged as historical evidence.

---

## 4. npm — the same defect, milder in form and the same in kind

Not in the mission's scope, and unavoidable: leaving npm approving while
downgrading PyPI for a weaker version of the same defect would be precisely the
one-off exception §4 prohibits.

Two of npm's recorded assessments overstate its evidence:

| Recorded | What the cited document actually says |
|---|---|
| `commercial_use: PERMITTED` | "Commercial packages are welcomed expressly … from hobby projects to competitive products". That is about what may be **published to** npm. It says nothing about a third party building a commercial product **on registry data** |
| `derived_analytics: PERMITTED` | The terms grant **npm** the right to "copy, publish and analyze content and share its analyses". The Mission 1.7 evidence note itself flags this as "a statement about npm's rights and not a grant of ours" — and the assessment was recorded as a permission anyway |

What npm's evidence genuinely grants is narrow and real: *"You may replicate
data from the Public Registry using the Public APIs"* — replication, which is
`storage`, plus `api_use`. Corrected, npm reads `commercial_use: NOT_ADDRESSED`,
`derived_analytics: NOT_ADDRESSED`, `model_processing: NOT_ADDRESSED`, and it
fails the same test.

**npm is downgraded to `REQUIRES_REVIEW`**, review version 1 preserved.

---

## 5. Wikimedia Pageviews — condition inventory (§5)

Read from the catalog and the loaded registry, not reconstructed.

### 5.1 Conditions

| # | Key | Review | Verification | Obligation | Current state | Capability needed | Representable today? |
|---|---|---|---|---|---|---|---|
| 1 | `wikimedia-user-agent` | v1 | `HUMAN_CONFIRMATION` | Every request carries a User-Agent naming the client, its version and a contact address, per the Wikimedia User-Agent Policy | `UNKNOWN` (blocking; no verifier can ever clear a human condition) | a generic request-identification capability — **does not exist** | **No** |
| 2 | `wikimedia-attribution` | v1 | `HUMAN_CONFIRMATION` | Product surfaces displaying Wikimedia **article content**, as distinct from aggregate view counts, carry CC BY-SA attribution and a link | `UNKNOWN` (blocking) | `source-attribution-display` — **exists**, needs a config entry | Yes, mechanically |

### 5.2 Access and rate limits, as reviewed

One profile: `PUBLIC_API` / `wikimedia-analytics-api`. No authentication, no API
key, no OAuth. Documented limit **200 requests per minute**, `origin=DOCUMENTED`,
cost `FREE_WITH_LIMITS`. Capabilities: page-view counts, timestamps, per-project
and per-article breakdowns, top articles.

### 5.3 The blocker is not a condition

Both conditions could be made verifiable. **The source still cannot become
eligible, because its approval does not survive §2's test**: `storage` and
`model_processing` are `NOT_ADDRESSED`.

The obvious rescue was examined and rejected. CC BY-SA 4.0 §2 does grant
"reproduce and Share the Licensed Material" and "produce, reproduce, and Share
Adapted Material" with no commercial exclusion — so *if* pageview counts are
Licensed Material, storage and model processing are granted.

Two reasons that does not close it:

1. **The Mission 1.7 review's own open question is exactly this** — *"Determine
   whether aggregate pageview COUNTS are themselves subject to CC BY-SA, or
   whether the licence attaches only to article text"* (**H-24**). Answering it
   in our favour would be resolving an open question by preference.
2. **The evidence that looked like a data licence is a documentation footer.**
   Mission 1.7 cited the Analytics API documentation as labelling its content
   CC BY-SA 4.0. That page carries `Content: CC BY-SA 4.0 · Code: MIT-0` — the
   standard footer describing *the documentation site*, not a statement about
   the data the API returns. Reading it as a data licence was a misreading, and
   it is corrected here rather than relied on.

Either branch of H-24 is a **legal determination** — whether counts are
copyrightable subject matter — and `source-registry-v1.md` §0 states that this
system is not a legal decision engine.

**Wikimedia Pageviews is downgraded to `REQUIRES_REVIEW`**, blocked on H-24,
with CC BY-SA 4.0 recorded as evidence so the next reviewer has both halves of
the question in front of them. §18 anticipates this outcome exactly: *if it
remains blocked, record why; do not weaken the gate to achieve eligibility.*

### 5.4 Therefore no capability and no configuration is built for it

§7 says prefer configuration over code and **do not build unused abstractions**;
the compliance validator enforces the second mechanically, failing on "registered
capabilities that no condition names". A `required-request-identification`
capability built now would be named by no condition on any approving source and
would fail that check on the day it was written.

What it would need is recorded in
[`wikimedia-pageviews-compliance-v1.md`](wikimedia-pageviews-compliance-v1.md)
so the work is ready the moment H-24 is answered.

---

## 6. GDELT — condition inventory (§6)

### 6.1 Conditions

| # | Key | Review | Verification | Obligation | Current state | Capability needed | Representable today? |
|---|---|---|---|---|---|---|---|
| 1 | `gdelt-attribution` | v1 | `HUMAN_CONFIRMATION` | Product surfaces derived from GDELT carry a citation to the GDELT Project and a link to `https://www.gdeltproject.org/`, on use and on redistribution | `UNKNOWN` (blocking) | `source-attribution-display` — **exists** | **Yes** |

One condition. No credential condition, no access restriction condition, no
retention condition — and none is invented here, because §6 forbids adding
policy conditions merely because they sound sensible.

### 6.2 Access and rate limits, as reviewed

Two profiles: `PUBLIC_API` / `gdelt-doc-api` and `DATASET_DOWNLOAD` /
`gdelt-bulk-files`. Neither requires authentication or a key; both are `FREE`.
**No rate limit is documented on either**, and `rate_limit_known` is false for
both — which stays false. §11 is explicit: GDELT remains `UNKNOWN` where no
official limit was found, and local pacing is not a provider limit.

### 6.3 GDELT's approval survives the audit

All six required activities are positively permitted, on a single sentence that
grants rather than merely fails to prohibit:

> all datasets released by the GDELT Project are available for unlimited and
> unrestricted use for any academic, commercial or governmental use of any kind
> without fee

Its one obligation — citation plus a link — is a **prescribed attribution**, and
that is exactly what `source-attribution-display` was built to verify.

**GDELT is the source this mission can legitimately make collector-eligible.**

---

## 7. What GDELT's compliance configuration must contain

Derived from its evidence and from nothing else.

### 7.1 Attribution

Two elements, both with **exact wording available from the terms**:

| Element | Text | Supplied? |
|---|---|---|
| `SOURCE_CREDIT` | `The GDELT Project` | no — fixed by the terms |
| `EXACT_NOTICE` | the citation-and-link sentence, verbatim from the terms | no — the terms prescribe it |

No `MODIFICATION_STATEMENT`, no `LICENCE_IDENTIFIER`, no `DISCLAIMER`: the terms
require none, and §8 forbids inventing wording where none exists.

### 7.2 Resource scope — and why it is not source-wide

The grant covers "all datasets **released by** the GDELT Project". GDELT
aggregates worldwide news coverage, so a returned record can reference or quote
material the project did not itself release. The scope must therefore fail
closed for a resource whose content origin is not established:
`third_party_denied` with `require_notes` semantics equivalent to FRED's
marker-based exclusion.

§10: *do not convert a source-level general permission into a broader resource
grant than the evidence supports.* The grant is over GDELT's own datasets, so
`PLATFORM_LICENSED` resources are allowed and `THIRD_PARTY` and `UNKNOWN` are
denied.

### 7.3 Access restriction

Both reviewed profiles are approved, so the restriction names both and nothing
else. A third profile appearing on this source later — a browser path, an
undocumented endpoint — must fail the check rather than be ignored, which is
what the existing `access_restriction` mechanism already does.

---

## 8. What this mission will do

| Source | Action | Review version |
|---|---|---|
| `gdelt` | compliance configuration; `gdelt-attribution` becomes `CAPABILITY` | new version, same verdict |
| `wikimedia-pageviews` | CC BY-SA recorded as evidence; downgraded, H-24 elevated | new version, verdict lowered |
| `npm-registry` | assessments corrected to the evidence; downgraded | new version, verdict lowered |
| `pypi` | downgraded, outcome C | new version, verdict lowered |

Every previous review version is preserved. The source count stays **27**; only
states move.

**Expected end state: 5 sources approving, 4 collector-eligible** — the three
economic sources plus GDELT. That is one more than before, achieved by making a
real obligation verifiable rather than by relaxing anything.

## 9. The rule becomes mechanical

A prose rule that three sources violated is a prose rule. `validate_schema` and
the registry validator gain a check: **an approving review must positively
permit every materially-required activity.** Written so it fails on today's
catalog before the downgrades land, and probed against a deliberate violation
afterwards — a check that has never failed proves nothing.
