# Wikimedia Pageviews compliance readiness V1

**Status:** Readiness record. Produced by Mission 1.8 §5, §13.
**Date:** 2026-08-30
**Governs:** nothing yet — **there is deliberately no `wikimedia-pageviews`
entry in [`source-compliance-v1.json`](source-compliance-v1.json)**, and §4 of
this document says why.
**Related:** [`source-registry-v1.md`](source-registry-v1.md) §1 rule 2,
[`new-source-compliance-gap-analysis-v1.md`](new-source-compliance-gap-analysis-v1.md) §5,
`source-human-review-queue-v1.md` **H-24**.

---

## 0. Why a compliance document for a source that is not approved

Mission 1.8 set out to make Wikimedia Pageviews collector-eligible and did not,
because auditing it turned up a misreading in its own review. That work is not
wasted: the condition inventory is complete, the configuration it would need is
specified, and the single question standing between here and there is named.

This document exists so the work is ready the moment **H-24** is answered, and
so nobody repeats the analysis to reach the same place.

---

## 1. Why it is blocked

Its Mission 1.7 review recorded `storage` and `model_processing` as
`NOT_ADDRESSED`. Both are required by the assessed use, and
`source-registry-v1.md` §1 rule 2 admits no path from *we could not check* to
*we may proceed*.

Two attempts to close that gap were made and both failed honestly.

### 1.1 The evidence that looked like a data licence is a documentation footer

Mission 1.7 cited the Analytics API documentation as labelling its content
CC BY-SA 4.0. That page carries:

```text
Content: CC BY-SA 4.0 · Code: MIT-0
```

which is the standard footer describing **the documentation site itself**, not a
statement about the data the API returns. Reading it as a data licence was
wrong, and correcting it removed the only thing that looked like a grant.

### 1.2 The licence grants what is needed — for material we cannot confirm this is

CC BY-SA 4.0 was retrieved during this mission and recorded as evidence.
Section 2 grants the right to *"reproduce and Share the Licensed Material"* and
to *"produce, reproduce, and Share Adapted Material"*, with no commercial
exclusion and no text-and-data-mining restriction. That is precisely the
`storage` and `model_processing` grant the terms do not state.

It applies to **Licensed Material**. Whether aggregate pageview *counts* are
Licensed Material is **H-24**, recorded as an open question by the Mission 1.7
review that first read these documents.

Both answers are legal determinations — either the counts are copyrightable
subject matter carried by the licence, or they are facts outside it needing a
different basis — and `source-registry-v1.md` §0 states plainly that this system
is not a legal decision engine. Answering H-24 in our own favour to reach
eligibility is the single thing Mission 1.8 §18 forbids.

### 1.3 What is not in doubt

- **Commercial reuse.** The Wikimedia Foundation's Terms of Use state the
  licences "do allow commercial uses". `commercial_use` stays `PERMITTED`.
- **Derived analytics.** Unchanged at `PERMITTED`.
- **The documented rate limits.** 200 requests per minute for a client sending a
  User-Agent, `origin=DOCUMENTED`. These stand and are not re-litigated.

---

## 2. Condition inventory (§5), complete

Read from the catalog, not reconstructed.

| Key | Review | Verification | Obligation | State | What would verify it |
|---|---|---|---|---|---|
| `wikimedia-user-agent` | v1 | `HUMAN_CONFIRMATION` | every request carries a User-Agent naming the client, its version and a contact address | `UNKNOWN`, blocking | a generic request-identification capability — **does not exist** |
| `wikimedia-attribution` | v1 | `HUMAN_CONFIRMATION` | surfaces displaying article **content**, as distinct from view counts, carry CC BY-SA attribution and a link | `UNKNOWN`, blocking | `source-attribution-display` — **exists** |

Review version 2 carries **no conditions**, because it is not an approving
review and a condition is what an approving review depends on. Both obligations
are retained verbatim in v2's open questions, so nothing is lost.

---

## 3. The configuration it would need

Specified now so the work is mechanical later.

### 3.1 Attribution

| Element | Text | Supplied? |
|---|---|---|
| `SOURCE_CREDIT` | the project name, per-request (`English Wikipedia`, `Wikidata`, …) | **yes** — it varies per record |
| `LICENCE_IDENTIFIER` | `CC BY-SA 4.0` | no |
| `ARTICLE_LINK` | — | **no element exists for this** |

The last row is a real gap and is recorded rather than worked around. CC BY-SA
attribution is satisfied by a hyperlink to the article, and `AttributionElement`
has no value for a per-record link. Two options, neither taken here: add an
element to a closed contract enum, or express the link as a `SOURCE_CREDIT`
whose supplied text is a URL — which would be a value in the wrong field.

Note the obligation is narrower than it first appears: it attaches to surfaces
displaying **article content**, and a chart of view counts may not be one. That
is H-24 again, from the attribution side.

### 3.2 Request identification (§13)

**Not authentication.** Wikimedia's User-Agent Policy requires an informative
`User-Agent` naming the client, its version and a contact address, in the form:

```text
CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0
```

Requests without one "may be blocked without notice". This is an
**identification** requirement and modelling it as a `CONFIG_REFERENCE` would be
the confusion §12 warns against: no secret is involved, and a credential check
would report `SATISFIED` for the wrong reason.

The right shape is a small generic capability — semantically
`required-request-identification`, checking that a source's configuration
declares an identification header and that it is non-empty and contains contact
information. Generic because Wikimedia is unlikely to be the only source that
asks; **not** `wikimedia-user-agent-check`, which would be a hack wearing a
capability's name.

### 3.3 Resource scope

Narrow, and narrower than the source. The approved capabilities are page-view
counts, timestamps, per-project and per-article breakdowns, and top articles.
The scope should permit those and refuse anything else — the Analytics API also
exposes editor and device metrics that this review did not assess.

### 3.4 Minimisation

Project identifier, article identifier, period, view count, and the access or
device dimension where authorised. Nothing per-reader exists in this API, which
is why the source is `NONE_EXPECTED` for personal data — and §16 says that
classification stays as Mission 1.7 set it.

---

## 4. Why none of it was built

§7 says do not build unused abstractions, and the compliance validator enforces
that mechanically: it fails on *"registered capabilities that no condition
names"*.

A `required-request-identification` capability built today would be named by no
condition on any approving source — Wikimedia's conditions live on a
non-approving review — and would fail that check on the day it was written. §13
says it plainly: **only build it if an actual condition requires it.**

The same argument covers the compliance entry. Configuration for a source that
may not be collected from is the switch getting ahead of the thing it switches,
which is the pattern `source-registry-v1.md` §4 exists to prevent.

---

## 5. The exact path to eligibility

1. **Answer H-24** — are aggregate pageview counts Licensed Material under
   CC BY-SA 4.0? This is a legal reading, not an engineering task, and it
   governs everything below.
2. If yes: record a review version 3 assessing `storage` and `model_processing`
   against the licence, restoring the approving state.
3. Build `required-request-identification` and write the compliance entry from
   §3 above.
4. Re-express both conditions as `CAPABILITY`, and verify.
5. Resolve whether `AttributionElement` needs a per-record link value.

Steps 3 to 5 are a few hours. Step 1 is the mission.
