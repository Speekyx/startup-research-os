# Source human-review queue V1

**Status:** Open items. Each entry is a concrete question, not a request to think about it.
**Version:** 1.0
**Date:** 2026-08-29 (Mission 1.3)
**Governed by:** [`source-registry-v1.md`](source-registry-v1.md)
**Results:** [`source-review-results-v1.md`](source-review-results-v1.md)

---

## How to read this

Every entry names the **exact document**, the **exact question**, and the
**exact next action**. Mission 1.3 §36 forbids the generic version — "ask a
lawyer" tells nobody what to ask — so each item below can be picked up and acted
on without re-deriving the analysis.

Two things are deliberately absent. Nobody was contacted and no agreement was
entered: §37 asks for the required next action to be *recorded*, not taken.

| Item | Source | Blocks | Needs |
|------|--------|--------|-------|
| [H-1](#h-1) | Reddit | REQUIRES_REVIEW | Documents unreachable from this environment |
| [H-2](#h-2) | Reddit | REQUIRES_REVIEW | Commercial eligibility decision |
| [H-3](#h-3) | Stack Exchange | REQUIRES_REVIEW | Documents behind an anti-bot interstitial |
| [H-4](#h-4) | Stack Exchange | REQUIRES_REVIEW | CC BY-SA share-alike scope — legal reading |
| [H-5](#h-5) | Hacker News | REQUIRES_REVIEW | Operator clarification |
| [H-6](#h-6) | Google Trends | REQUIRES_REVIEW | Alpha programme application |
| [H-7](#h-7) | Product Hunt | RESTRICTED | Commercial permission request |
| [H-8](#h-8) | GitHub | RESTRICTED | Whether a commercial route exists at all |
| [H-9](#h-9) | Apple / Google Play | RESTRICTED | Whether any authorised mechanism exists |
| [H-10](#h-10) | World Bank | condition | Per-dataset licence determination |
| [H-11](#h-11) | FRED | condition | Third-party series permission |
| [H-12](#h-12) | All | cross-cutting | Jurisdiction / GDPR — still deferred |

---

## H-1 — Reddit's governing policies could not be retrieved {#h-1}

**Issue.** The Reddit Data API Wiki names three governing documents — the Data
API Terms, the Developer Terms and the Responsible Builder Policy — and none of
them could be read. `redditinc.com` is blocked by this environment's browsing
policy.

**Documents.** `https://redditinc.com/policies/data-api-terms`, plus the
Developer Terms and Responsible Builder Policy linked from the same site.

**Why it is unresolved.** This is an environment limitation, not a statement
about Reddit and not a refusal by Reddit. The documents were named but not read,
so nothing about commercial use, storage, retention, redistribution or model
processing can be asserted.

**Needed.** Retrieve all three from an environment that can reach
`redditinc.com` and assess them against the recorded use case.

**Vendor contact needed?** Not for this item.
**Legal counsel appropriate?** Not until the documents have been read.

---

## H-2 — Is a commercial multi-tenant SaaS eligible for Reddit's free tier? {#h-2}

**Issue.** The Data API Wiki states the 100 QPM limit applies to "those
**eligible for** free access usage" and does not define eligibility.

**Document.** Reddit Data API Wiki,
`https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki`,
section *Rate limits*.

**Why it is unresolved.** The phrasing implies an eligibility condition the wiki
does not state. A commercial product proceeding on the free tier without
establishing eligibility would be assuming a permission.

**Needed.** A determination of which access tier applies to this use case, and
what a commercial arrangement would require.

**Vendor contact needed?** **Yes** — the wiki directs prospective users to
Reddit's contact form to request access. That request has not been made.
**Legal counsel appropriate?** Only if the terms turn out to be ambiguous.

---

## H-3 — Stack Exchange terms are behind an anti-bot interstitial {#h-3}

**Issue.** The API Terms of Use were retrieved. The Public Network Terms of
Service and the Consolidated Responsible AI policy were not: `stackoverflow.com`
served a security interstitial for those paths.

**Documents.** `https://stackoverflow.com/legal/terms-of-service/public` and
`https://stackoverflow.com/legal/consolidated-responsible-ai-policy`.

**Why it is unresolved.** This review did not attempt to bypass the check (§8),
so the two documents that would settle commercial reuse, storage and model
processing remain unread. The API Terms are silent on all three.

**Needed.** Retrieve both from an ordinary browser session and assess.

**Vendor contact needed?** Not for retrieval.
**Legal counsel appropriate?** See H-4.

---

## H-4 — Does CC BY-SA share-alike reach derived analytics? {#h-4}

**Issue.** Stack Exchange user contributions are licensed CC BY-SA. Whether the
share-alike obligation attaches to aggregated analytical outputs derived from
that content — as opposed to reproductions of it — determines whether this use
case is possible at all.

**Documents.** The Stack Exchange footer licence statement, the Public Network
Terms of Service (H-3), and the CC BY-SA licence text itself.

**Why it is unresolved.** This is a legal question about the scope of a copyleft
obligation applied to derived statistics. It is not answerable by reading a
platform's help pages, and guessing at it would be exactly the kind of
conclusion the registry forbids inventing.

**Needed.** A determination of whether share-alike attaches to aggregated
derived outputs, and if so what it obliges.

**Vendor contact needed?** Possibly — Stack Exchange sells a **Stack Data
Licensing** product, which suggests a licensed route exists for uses the free
API does not cover.
**Legal counsel appropriate?** **Yes.** This is the clearest legal question in
the queue.

---

## H-5 — Does Hacker News's official API authorise commercial derived analytics? {#h-5}

**Issue.** Y Combinator publishes an official API specifically to make public HN
data programmatically available. The Terms of Use separately prohibit creating
derivative works based on Site Content "except as expressly authorized by Y
Combinator". Whether publishing the API constitutes that authorisation for
commercial storage and derived analytics is not stated anywhere.

**Documents.** `https://github.com/HackerNews/API` (official API documentation)
and `https://www.ycombinator.com/legal/`, section *Site Content, Software and
Trademarks*.

**Why it is unresolved.** Both readings are defensible and the documents do not
choose. Silence is not permission, so the source stays blocked — but the
question is narrow enough to be answered by the operator directly.

**Needed.** A yes or no from Y Combinator.

**Vendor contact needed?** **Yes** — `api@ycombinator.com`, the address the API
documentation itself publishes for API questions. Not contacted.
**Legal counsel appropriate?** Only if the answer is ambiguous.

---

## H-6 — Google Trends API is alpha-only and has no published terms {#h-6}

**Issue.** An official Trends API was announced on 24 July 2025 and is limited
to "a very limited number of testers" by application. No terms of use were
published with the announcement.

**Document.**
`https://developers.google.com/search/blog/2025/07/trends-api`.

**Why it is unresolved.** Mission 1.0 recorded that no official mechanism
existed; one now does, but it is not generally available and its terms are
unknown. Nothing about the assessed use case can be established from a blog
post.

**Needed.** Apply to the alpha programme; obtain and assess the API terms.

**Vendor contact needed?** **Yes** — submit the alpha tester application. Not
submitted.
**Legal counsel appropriate?** No.

**Standing condition, unchanged:** the undocumented endpoints behind the Trends
web interface must not be called, and an unofficial library that happens to work
is not an authorisation.

---

## H-7 — Product Hunt commercial use requires permission {#h-7}

**Issue.** The API documentation states twice that the API "must not be used for
commercial purposes" and names the route to change that.

**Document.** `https://api.producthunt.com/v2/docs`, section *May I use the API
for my business?*

**Why it is unresolved.** It is not ambiguous — it is simply not granted. The
platform has stated the condition and the contact.

**Needed.** Written permission from Product Hunt for commercial use, recorded as
`OPERATOR_CORRESPONDENCE` evidence before any collection.

**Vendor contact needed?** **Yes** — `hello@producthunt.com`. Not contacted.
**Legal counsel appropriate?** Only to review whatever terms come back.

---

## H-8 — Does GitHub offer any commercial route? {#h-8}

**Issue.** GitHub's Acceptable Use Policies enumerate the permitted uses of
information from the Service — open-access research and archival — and state
that the enumeration applies regardless of whether the information was scraped
or collected through the API. Commercial market research is not among them.

**Document.**
`https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies`,
section *7. Information Usage Restrictions*.

**Why it is unresolved.** The verdict itself is not unresolved — RESTRICTED is
well supported. What is unknown is whether a licensed commercial route exists at
all, because the Acceptable Use Policies do not mention one.

**Needed.** Determine whether GitHub offers a commercial data licence or
enterprise arrangement covering this use.

**Vendor contact needed?** Possibly, and only if GitHub data becomes necessary.
**Legal counsel appropriate?** No.

---

## H-9 — Is there any authorised app-store mechanism for market research? {#h-9}

**Issue.** For both stores, the documented mechanisms serve a materially
narrower purpose. Apple's public search API is published under the Performance
Partners (affiliate) programme and exists to promote store content and earn
commission on partner links. Google's Play Developer API manages the caller's
own applications. Neither is a market-research mechanism, and App Store Connect
likewise concerns one's own apps.

**Documents.** `https://performance-partners.apple.com/search-api` and
`https://developers.google.com/android-publisher`.

**Why it is unresolved.** Absence of evidence in one API's documentation is not
evidence that no authorised mechanism exists anywhere.

**Needed.** Determine whether either vendor publishes a mechanism — a data
licence, a partner programme, anything — covering third-party app metadata,
ratings or reviews for market research.

**Vendor contact needed?** Possibly.
**Legal counsel appropriate?** No.

**Explicitly out of scope:** collecting the public store pages. That route was
not pursued, not documented, and is not an alternative this queue proposes.

---

## H-10 — World Bank licensing is per dataset, not per platform {#h-10}

**Issue.** CC-BY 4.0 is the default for datasets the World Bank produces, but
the same platform also distributes ODbL datasets (share-alike on
redistribution), Microdata under a research-only licence that forbids
redistribution, and third-party datasets under external or custom terms.

**Document.** `https://datacatalog.worldbank.org/public-licenses`.

**Why it is unresolved.** The approval covers CC-BY 4.0 indicator data. Applying
it to a dataset without checking that dataset's licence would extend an approval
beyond what was assessed.

**Needed.** A per-dataset licence check at collection time. This is captured as
the machine-checkable condition `dataset-licence-allowlist`, so it is a design
requirement for a future collector rather than a standing human task.

**Vendor contact needed?** No.
**Legal counsel appropriate?** Only for ODbL share-alike scope, if an ODbL
dataset is ever used.

---

## H-11 — FRED redistributes series it does not own {#h-11}

**Issue.** The FRED API Terms state plainly that series available through the
API may be owned by third parties, that API access does not override those
owners' rights, and that permission must be obtained from the owner before any
non-personal use.

**Document.** `https://fred.stlouisfed.org/docs/api/terms_of_use.html`, section
*Property Rights*.

**Why it is unresolved.** Which series the research use case actually needs is
unknown, so whether any of them are copyrighted is unknown. Copyrighted series
are mechanically identifiable — their notes contain "Copyright" — which is why
the default is to exclude them rather than to ask.

**Needed.** If a copyrighted series turns out to be necessary, contact that
series' owner individually. The Federal Reserve Bank of St. Louis explicitly
cannot grant that permission.

**Vendor contact needed?** Per series owner, if and when one is needed.
**Legal counsel appropriate?** No.

---

## H-12 — Jurisdiction and GDPR remain deferred {#h-12}

**Issue.** Several sources carry user-generated content and user identifiers.
Whether and how GDPR and equivalent regimes apply to collecting, storing and
processing that content is unresolved project-wide.

**Why it is unresolved.** Deliberately. `data-retention-policy-v1.md` §7 defers
it to human or legal input, and Mission 1.3 §38 explicitly does not attempt to
resolve it.

**Needed.** A jurisdiction analysis, as its own piece of work.

**What this mission did instead.** Recorded personal-data risk per source, kept
`jurisdiction_review_required` true on every review, and made no source approved
for personal-data collection. The three approving reviews are all economic
statistics with `NONE_EXPECTED` personal-data risk — which is not a coincidence
and not a workaround: they are the sources where the question does not arise.

**Vendor contact needed?** No.
**Legal counsel appropriate?** **Yes**, and this is the item that most clearly
needs it.
