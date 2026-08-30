# Source human-review queue V1

**Status:** Open items. Each entry is a concrete question, not a request to think about it.
**Version:** 1.3 (Mission 1.9 added H-27 and H-28; Mission 1.8 added H-25 and
H-26, resolved half of H-22 and promoted H-24 to a blocker)
**Date:** 2026-08-30
**Governed by:** [`source-registry-v1.md`](source-registry-v1.md)
**Results:** [`source-review-results-v1.md`](source-review-results-v1.md) ·
[`source-expansion-consumer-social-v1.md`](source-expansion-consumer-social-v1.md)

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
| [H-13](#h-13) | Mastodon / Lemmy | modelling | Can the registry express a federated source? |
| [H-14](#h-14) | X (Twitter) | REQUIRES_REVIEW | Agreement returned HTTP 402 |
| [H-15](#h-15) | Discord | REQUIRES_REVIEW | Developer Terms returned HTTP 403 |
| [H-16](#h-16) | Twitch | REQUIRES_REVIEW | Developer Services Agreement text unreadable |
| [H-17](#h-17) | Pinterest | REQUIRES_REVIEW | Developer terms did not return their text |
| [H-18](#h-18) | Bluesky | REQUIRES_REVIEW | Is there a developer terms document at all? |
| [H-19](#h-19) | Hugging Face | REQUIRES_REVIEW | Does anything govern Hub METADATA? |
| [H-20](#h-20) | Steam | RESTRICTED | Is analytical use inside the grant? |
| [H-21](#h-21) | Meta / Instagram | RESTRICTED | Does any endpoint expose public content? |
| [H-22](#h-22) | 5 newly approved | conditions | Compliance capabilities do not exist |
| [H-23](#h-23) | OpenAlex | condition | Metered API — spend ceiling undecided |
| [H-24](#h-24) | Wikimedia | **REQUIRES_REVIEW** | Do view COUNTS carry CC BY-SA? — **now the blocker** |
| [H-25](#h-25) | PyPI | REQUIRES_REVIEW | Is there any grant at all? |
| [H-26](#h-26) | npm | REQUIRES_REVIEW | Commercial reuse and analytics by a third party |
| [H-27](#h-27) | GDELT | **DOC API deferred** | Timeline JSON envelope is unobservable from here — [no longer the first-collector blocker](#h-27-update) |
| [H-28](#h-28) | GDELT | — | [**RESOLVED**](#h-28-update) — the model in Mission 1.9.1, the entries in Mission 1.9.2 |
| [H-29](#h-29) | GDELT | refinement | Is the WEB-NGRAM `DATE` column UTC? Nothing first-party says |
| [H-30](#h-30) | GDELT | refinement | Is there a CLD2-name-to-language-tag mapping? |
| [H-31](#h-31) | GDELT | refinement | How far back does the WEB-NGRAM directory reach? |

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


---

# Mission 1.7 additions

Twelve items. Four are retrieval failures, four are questions a source's own
documents do not answer, one is a modelling decision, and three are conditions
that cannot currently be cleared.

Nobody was contacted and no agreement was entered (§44). Each entry records the
action that would be required.

---

## H-13 — Can the registry express a federated source? {#h-13}

**Issue.** Mastodon and Lemmy are software, not services. Thousands of instances
are run by different operators under different policies; the Mastodon API
documentation confirms the API is per-instance and that no single terms document
governs the network.

**Why it is unresolved.** The registry models a source as **one operator with one
policy**, and a federated network is not that. Registering `mastodon` would
create an identity whose review can never conclude, and whose `REQUIRES_REVIEW`
state would read as "somebody should finish this" when the honest statement is
"this cannot be expressed at this level". §16 forbids flattening heterogeneous
instance policies into "Mastodon is allowed", so neither source was registered.

**Needed.** A decision between three options, none free:

1. **Register instances, not networks.** `mastodon-social` is one operator with
   one ToS and is perfectly governable. Review cost is per instance, and each
   instance is one community rather than a network.
2. **Add an instance layer to the model** — a source carrying per-instance
   policy records, with eligibility resolved per instance. Correct, and a schema
   change Mission 1.7 had no mandate to design.
3. **Leave federated sources out**, forfeiting the only social protocols whose
   data is structurally open.

**Vendor contact needed?** No.
**Legal counsel appropriate?** Not for the modelling decision. Probably yes for
whichever instances are eventually reviewed.
**Developer action needed?** Yes, for option 2.

---

## H-14 — The X Developer Agreement returned HTTP 402 {#h-14}

**Issue.** No evidence was gathered for X. Every activity is `NOT_ASSESSED`.

**Document.** `https://developer.x.com/en/developer-terms/agreement-and-policy`.

**Why it is unresolved.** The URL returned **HTTP 402 Payment Required** to this
environment on 2026-08-30. That is an environment limitation and not a statement
by X; it is recorded as such rather than as a refusal. The widely-held
understanding that X restricts commercial reuse is not evidence and was not
recorded as any.

**Needed.** Retrieve the agreement from an ordinary browser session and assess
commercial use, storage, retention, redistribution and model processing against
the recorded use case. Then determine which access tier applies to a commercial
multi-tenant SaaS, and what it costs.

**Vendor contact needed?** Probably, for tier and pricing.
**Legal counsel appropriate?** Only once the document has been read.

---

## H-15 — The Discord Developer Terms returned HTTP 403 {#h-15}

**Issue.** No evidence was gathered for Discord.

**Document.**
`https://support-dev.discord.com/hc/articles/8562894815383-Discord-Developer-Terms-of-Service`.

**Why it is unresolved.** HTTP 403 Forbidden on 2026-08-30.

**Needed.** Retrieve and assess. But answer the cheaper question first: most
Discord content sits in private servers, so even permissive terms would expose a
small and self-selected sample, and the Message Content privileged intent is
granted by Discord rather than self-selected. **If that intent would not be
granted for an analytics use case, the policy reading is moot.**

**Vendor contact needed?** Yes, for the privileged intent.
**Legal counsel appropriate?** Not yet.

---

## H-16 — The Twitch Developer Services Agreement could not be read {#h-16}

**Issue.** The Twitch API documentation was retrieved and establishes the access
model — OAuth 2.0, registered application. The document that would establish
PERMISSION was not.

**Document.** `https://legal.twitch.com/legal/developer-agreement/`. Two attempts
on 2026-08-30 returned the page navigation without the agreement text.

**Why it is unresolved.** A reviewer who read only the API documentation would
find a well-documented, openly described API and could easily mistake that for a
permission. Every policy activity stays `NOT_ASSESSED`.

**Needed.** Retrieve the agreement and assess storage, caching limits, commercial
use by a third-party analytics product, aggregation, derived analytics and
machine-learning processing — the last three separately, per §10. Also obtain
the documented rate limits, which the API documentation references without
stating.

**Vendor contact needed?** Not for retrieval.
**Legal counsel appropriate?** Once read.

**Why it matters.** Twitch is the strongest available creator-economy and
live-gaming source, and `creator` currently has no approving source at all.

---

## H-17 — The Pinterest developer terms did not return their text {#h-17}

**Issue.** No evidence was gathered for Pinterest.

**Document.** `https://developers.pinterest.com/terms/`.

**Why it is unresolved.** The developer site was reached on 2026-08-30; the terms
document itself returned navigation rather than content.

**Needed.** Retrieve and assess. Establish separately whether the API exposes
aggregate interest or trend data usable without access to individual accounts.

**Vendor contact needed?** Likely, for app review.
**Legal counsel appropriate?** Once read.

**Why it matters.** Pinterest is the strongest candidate in the catalog for
`desire` signals specifically: saving something is an expression of want with no
complaint and no purchase attached, which is exactly the signal shape the
portfolio is missing.

---

## H-18 — Does Bluesky publish developer terms at all? {#h-18}

**Issue.** Bluesky's Terms of Service were retrieved and read. They contain **no
provision** about automated access, crawling, the API, or machine-learning use of
content. Meanwhile the AT Protocol documentation states of the public firehose
that no API key is required.

**Documents.** `https://bsky.social/about/support/tos` (read, effective
2025-08-14) and `https://atproto.com/` (read).

**Why it is unresolved.** Silence is not permission
(`source-registry-v1.md` §1 rule 2). The user Terms govern the relationship with
account holders and say nothing to a third party reading public records. This is
the most technically open social platform available and it is blocked entirely
on the absence of a document.

**Needed.** Determine whether a developer or API terms document exists separate
from the user ToS. If it does, assess it. If it does not, that is itself the
answer, and the question becomes whether operator correspondence can establish
the position — `OPERATOR_CORRESPONDENCE` is an acceptable evidence type.

Separately: the Terms acknowledge that deletion may not propagate across the
network. A downstream holder of a deleted post is exactly the case that sentence
describes, and it creates an obligation the Terms do not specify.

**Vendor contact needed?** **Yes** — this is the single highest-value question in
the queue, and one answer would settle it.
**Legal counsel appropriate?** Only if a document turns up and is ambiguous.

---

## H-19 — Does anything govern Hugging Face Hub METADATA? {#h-19}

**Issue.** The Terms of Service address neither automated collection nor
commercial reuse of Hub metadata. They DO contain a broad licence grant — public
repositories grant every user rights to use, reproduce and make derivative works
— but that grant runs between **users** and covers repository **content**. What
this system would collect is platform metadata: download counts, likes, trending
placement. No clause mentions it.

**Document.** `https://huggingface.co/terms-of-service`, effective 2022-09-15.

**Why it is unresolved.** Reading the content grant as covering metadata would be
inferring permission from an adjacent one, which §12 forbids by name.

**Needed.** Determine whether any Hugging Face document addresses automated
collection and commercial reuse of Hub metadata. Determine separately whether the
2022 Terms have been superseded — every other source reviewed in this round
carries a materially more recent document, and a four-year-old ToS on a platform
that changed this much is itself a question.

**Vendor contact needed?** Possibly.
**Legal counsel appropriate?** For the content-versus-metadata boundary, yes.

---

## H-20 — Is analytical use inside Steam's grant? {#h-20}

**Issue.** Steam's API Terms grant permission to implement the Web API in an
Application and **distribute Steam Data to end users for their personal use via
that Application**. Accumulating Steam Data into an analytical corpus and selling
derived intelligence is not that. The terms separately prohibit presenting Steam
Data so that it appears to be available from a third party.

**Document.** `https://steamcommunity.com/dev/apiterms`, retrieved 2026-08-30.

**Why it is unresolved.** The verdict is `RESTRICTED` — the documents were read,
they permit some assessed activities, and ours is outside the grant they make.
Whether Valve would characterise analytical accumulation as inside or outside it
is a judgment the terms do not settle.

**Needed.** Three answers: whether accumulation for analysis falls inside the
licence; whether derived market intelligence sold to customers is "presenting
Steam Data so that it appears to be available from a third party"; and whether
Valve offers a commercial or data-partner arrangement covering analytical use.
No such route was found in the terms.

**Vendor contact needed?** **Yes**, for the third.
**Legal counsel appropriate?** **Yes**, for the first two.

**Why it matters.** `competition` and `collection` rest entirely on Steam and are
currently uncovered. It is the single richest gaming source available and there
is no substitute in the catalog.

---

## H-21 — Does any Meta endpoint expose public content? {#h-21}

**Issue.** Meta's Platform Terms authorise use only as the developer
documentation permits, and prohibit selling or licensing Platform Data, which
reaches the output of a commercial intelligence product directly.

**Document.** `https://developers.facebook.com/terms/`, effective 2026-02-03.

**Why it is unresolved.** There is a prior question that is **cheaper and may
settle the source outright**: Meta's APIs serve accounts a developer owns or
manages, not the public graph. If no endpoint exposes public content from
accounts we do not control, the policy analysis is moot for market research.

**Needed.** Establish the capability question first. Only if it passes: determine
whether market-intelligence output derived from Platform Data constitutes
granting a licence to Platform Data, and what "authorized applicable purposes
stated in Meta's developer documentation" includes.

**Vendor contact needed?** Only after the capability question.
**Legal counsel appropriate?** Only after the capability question.

---

## H-22 — Five approved sources have no capability to clear their conditions {#h-22}

**Issue.** `gdelt`, `wikimedia-pageviews`, `openalex`, `npm-registry` and `pypi`
are `APPROVED_WITH_CONDITIONS`, and **none is collector-eligible**. Their eleven
conditions name verifications that no capability implements.

**Why it is unresolved.** A condition is cleared by a verifier and by nothing else
(ADR-016). The compliance capabilities that would check an attribution surface or
an access restriction are parameterised for a *collector*, and Mission 1.7 §29
forbids writing one. Eight of the eleven conditions are therefore
`HUMAN_CONFIRMATION`, which no verifier can ever satisfy by design.

This is exactly the state Mission 1.3 left `world-bank`, `eurostat` and `fred`
in. Mission 1.4 resolved it by building capabilities and writing
`source-compliance-v1.json` entries.

**Needed.** For the two highest-value sources — `gdelt` and
`wikimedia-pageviews` — a `source-compliance-v1.json` entry describing their
attribution obligations, so the existing `source-attribution-display` capability
can verify them. That capability already describes itself as shared and
parameterised. **This is configuration rather than code, and it would move two
sources from approving to eligible without a line of collector.**

**Vendor contact needed?** No.
**Legal counsel appropriate?** No.
**Developer action needed?** **Yes**, and it is the cheapest large improvement
available.

---

## H-23 — OpenAlex is metered and no spend ceiling exists {#h-23}

**Issue.** OpenAlex data is CC0, which removes every licensing question at once.
Access is not free above an allowance: the documentation states a free API key
raises the daily budget tenfold, and that heavier use is pay-as-you-go returning
a `cost_usd` per call.

**Document.** `https://help.openalex.org/api/`, retrieved 2026-08-30.

**Why it is unresolved.** The help page describes the tiers without stating the
numbers. The exact free allowance, the allowance with a key, and the per-call
price above it were not established, and an unofficial figure must not be
recorded (§18, §19).

**Needed.** Obtain the official figures from `help.openalex.org/access/pricing/`.
Then set a spending ceiling and record who set it and where it is enforced.
Separately, configure `OPENALEX_CONTACT_EMAIL` — the one condition in this whole
expansion that a verifier can currently clear.

**Vendor contact needed?** No.
**Legal counsel appropriate?** No.

---

## H-24 — Do Wikimedia pageview COUNTS carry CC BY-SA? {#h-24}

**Issue.** The Wikimedia Foundation's terms state the content licences do allow
commercial use, and the Analytics API documentation labels its content
CC BY-SA 4.0 without distinguishing article text from aggregate view counts.

**Documents.** `https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use`
(effective 2023-06-07) and `https://doc.wikimedia.org/analytics-api/`, both
retrieved 2026-08-30.

**Why it is unresolved.** A chart of view counts is plausibly not a derivative of
the licensed text, and plausibly is not a finding. The answer decides whether
attribution is required on every surface derived from this source or only on
those displaying article content. The review records attribution as required, as
the stricter reading.

**Needed.** A determination of whether the licence attaches to aggregate counts.
Separately: whether Wikimedia Enterprise is **required** rather than merely
offered at a commercial reuser's volume — the APIs overview presents it as the
route for high-volume commercial reuse without stating a threshold at which it
becomes mandatory.

**Vendor contact needed?** For the Enterprise threshold, probably.
**Legal counsel appropriate?** **Yes**, for the licence scope question.

**Why it matters.** `wikimedia-pageviews` is the highest-priority collector in
the portfolio and the portfolio's only real answer to desire-driven discovery.


---

# Mission 1.8 additions and changes

Two new items, one half-resolved, and one promoted from a refinement to a
blocker.

## H-22 — half resolved {#h-22-update}

**GDELT is done.** Its attribution obligation is now a `CAPABILITY` verified by
`source-attribution-display`, and it is collector-eligible. See
[`gdelt-compliance-v1.md`](gdelt-compliance-v1.md).

**The other four are not, and three of them no longer can be**: `pypi`,
`npm-registry` and `wikimedia-pageviews` were downgraded on audit, so their
conditions are moot until their reviews are approving again. `openalex` remains
approving with two conditions, one of which a verifier can already clear.

## H-24 — promoted from refinement to blocker {#h-24-update}

Mission 1.7 recorded this as a question about whether attribution is required on
a chart of view counts. **It is now the single thing blocking the source.**

Mission 1.8 retrieved CC BY-SA 4.0 and confirmed Section 2 grants reproduction
and the production of Adapted Material, commercially and without a
text-and-data-mining restriction — for **Licensed Material**. It also found that
the evidence Mission 1.7 read as a data licence is the documentation site's
footer (`Content: CC BY-SA 4.0 · Code: MIT-0`), not a statement about the data
the API returns.

So the question is no longer "is attribution required here" but "is there a
grant here at all", and both answers to it are determinations about what
copyright subsists in.

**Needed.** A legal reading of whether aggregate pageview counts are Licensed
Material under CC BY-SA 4.0. If they are, Section 2 supplies the `storage` and
`model_processing` grants the Wikimedia terms do not state, and the source
becomes approvable immediately — the compliance work is specified in
[`wikimedia-pageviews-compliance-v1.md`](wikimedia-pageviews-compliance-v1.md)
§3. If they are not, a separate basis is needed for holding and processing them.

**Legal counsel appropriate?** **Yes.** This is the highest-value legal question
in the queue: one answer restores the portfolio's best `curiosity`,
`entertainment` and `trend` source.

---

## H-25 — Does anything in PyPI's documents grant anything? {#h-25}

**Issue.** PyPI was downgraded from `APPROVED_WITH_CONDITIONS` to
`REQUIRES_REVIEW`. Four of the six activities the assessed use materially
requires — `commercial_use`, `storage`, `derived_analytics`, `model_processing`
— are `NOT_ADDRESSED`, and the single cited document contains prohibitions and
no grant of any kind.

**Document.** `https://policies.python.org/pypi.org/Terms-of-Use/`, effective
2025-02-25, read 2026-08-30.

**Why it is unresolved.** Nothing about PyPI's terms changed; the reading of
them did. The Mission 1.7 review approved the source on "the absence of a
prohibition covering us plus the presence of a documented API" — its own words —
which is the inference `source-registry-v1.md` §1 rule 2 forbids.

**Needed.** Determine whether any PyPI or PSF document positively permits
commercial reuse of package metadata by a third-party product, addresses storage
of replicated metadata, or addresses derived analytics and model processing.
Check separately whether the published bulk dataset carries more explicit terms
than the API — a dataset distribution often does.

**Vendor contact needed?** Possibly, and the PSF is approachable.
**Legal counsel appropriate?** Only once it is established whether any document
speaks to this at all.

---

## H-26 — Does npm permit commercial reuse and analytics by a third party? {#h-26}

**Issue.** npm was downgraded for the same class of defect, milder in form. Two
Mission 1.7 assessments overstated their evidence:

- *"Commercial packages are welcomed expressly"* is about what may be
  **published to** npm, not about commercial reuse of registry data;
- the right to *"copy, publish and analyze content and share its analyses"* is
  granted **to npm**, which the Mission 1.7 evidence note said in so many words
  before the assessment recorded it as a permission of ours.

**Document.** `https://docs.npmjs.com/policies/open-source-terms`, effective
2022-03-10.

**Why it is unresolved.** What the terms genuinely grant is narrow and real —
*"You may replicate data from the Public Registry using the Public APIs"*, which
is storage plus API access. Commercial reuse, derived analytics and model
processing are all unaddressed.

**Needed.** Determine whether any npm or GitHub document permits commercial
reuse of public registry metadata by a third party, derived analytics over it by
anyone other than npm, or model processing of it. Also determine retention
obligations when a package is unpublished upstream.

**Why it matters.** npm and PyPI were the whole of the portfolio's
`developer_activity` coverage. Both are now pending, so that family rests on
nothing.

**Vendor contact needed?** The terms direct high-volume users to a sales team,
which is a route to the question.
**Legal counsel appropriate?** Not before the documents are found.


---

# Mission 1.9 additions

Two items, and between them they are why the GDELT collector was not written.
Neither is a policy question: GDELT's approval stands and is unchanged.

---

## H-27 — The GDELT timeline JSON envelope could not be observed {#h-27}

**Issue.** The DOC API mode that fits the authorised data categories is
`TimelineTone` — it returns tone over time, which maps onto `tone_score` plus
`observation_period` and contains no publisher content at all. Its JSON field
names are unknown.

**Why it is unresolved.** Two independent routes, both closed:

- **GDELT does not publish the schema.** Its own announcement documents the
  parameters and the modes' semantics — `TimelineVol` reports volume as a
  percentage of monitored coverage, `TimelineVolRaw` returns raw counts plus a
  `norm` field — and states that JSON output exists without listing the fields.
- **This environment cannot reach `api.gdeltproject.org`.** Fourteen attempts
  returned `ConnectTimeout`, `ECONNRESET`, `HTTP 429` and finally
  `ECONNREFUSED`, while `api.worldbank.org` returned HTTP 200 from the same
  client moments apart. One `ArtList` response was obtained through a proxied
  route before that route also began refusing.

A parser was not written against invented field names. It would have been
validated by fake responses composed from the same invention — a test passing by
checking a guess against itself.

**Needed.** One `TimelineTone` response and one `TimelineVolRaw` response,
captured as JSON from any environment that can reach the API, and committed as
test fixtures. That is the entire blocker.

```text
https://api.gdeltproject.org/api/v2/doc/doc?query=climate&mode=TimelineTone&format=json&timespan=1d
```

**Vendor contact needed?** No.
**Legal counsel appropriate?** No.
**Developer action needed?** **Yes**, and it is small: two saved responses.

---

## H-28 — What is a GDELT resource, and what licence identifies it? {#h-28}

**Issue.** `context.datasets` is empty for GDELT, so `authorized_dataset(...)`
returns `None` for everything and no RawRecord draft can be built. The resource
model is failing closed exactly as designed — a resource nobody reviewed has no
licence, no family and no content origin.

**Why it is unresolved.** Populating it means deciding what one GDELT resource
*is*, and the answer depends on which API mode the collector uses, which is
**H-27**. Guessing now would fix the symptom and lock in the wrong answer.

A second question sits inside it: `AuthorizedDataset.licence` is required and
non-empty, and **GDELT names no licence**. It grants unlimited use directly
rather than through a named instrument, which is the finding
`gdelt-compliance-v1.md` §2 records as the reason there is no
`LICENCE_IDENTIFIER` in its attribution. The honest value is an identifier for
the grant instrument rather than a licence name, and since `licence_allowlist`
is `null` nothing matches against it — so the choice is about being readable
later, not about enforcement.

**Needed.** After H-27: one authorised dataset entry per collected mode, with a
`basis` quoting the grant sentence, and a deliberate decision on the licence
field.

**Vendor contact needed?** No.
**Legal counsel appropriate?** No.
**Developer action needed?** Yes, after H-27.

---

# Mission 1.9.2 changes and additions

GDELT was re-reviewed against its WEB-NGRAM datasets. **No item was removed
because it became inconvenient**; one was genuinely resolved, one was
reclassified without being closed, and three new ones are refinements that block
nothing.

---

## H-27 — reclassified: still open, no longer the first-collector blocker {#h-27-update}

**Unchanged:** no `TimelineTone` or `TimelineVolRaw` envelope has ever been
observed, none was fabricated, and the entry above stands in full. Two saved
responses would still close it.

**What changed** is that nothing now waits on it. GDELT review 3 authorised two
resources on a **different route** — the WEB-NGRAM files, whose contract was
observed and then confirmed against GDELT's own documentation — so the source has
a usable acquisition path that does not touch the DOC API.

The DOC API route is **deferred**: reviewed, approved, its access profile kept
with its endpoint, and **no resource on it authorised**. The profile and the
capture script are deliberately not deleted — the Spanner migration will finish,
and deleting them would make a later un-deferral look like a new approval.

**Developer action needed?** Still yes, still two saved responses — but it is no
longer urgent and no longer blocks a collector.

---

## H-28 — resolved {#h-28-update}

Both halves, in two missions.

**"What licence identifies a GDELT resource?"** — Mission 1.9.1. The answer was
that the question does not apply: GDELT grants use directly and names no
instrument. `RightsBasis = NAMED_LICENCE | DIRECT_GRANT` ([ADR-018]) made that
statable, and the model refuses a licence identifier under a direct grant, so
none of `OTHER`, `NONE`, `N/A` or an invented name can be written.

**"What IS a GDELT resource?"** — Mission 1.9.2. `web-ngrams/1gram` and
`web-ngrams/2gram`, each `DIRECT_GRANT`, `PLATFORM_LICENSED`, with a `basis`
quoting the grant sentence. `context.datasets` is no longer empty, and the
resource that is still not in it is any DOC API mode — which is H-27, and is
correctly a different item.

**Nothing further is needed.**

[ADR-018]: ../architecture/adr/ADR-018-acquisition-rights-basis.md

---

## H-29 — Is the WEB-NGRAM `DATE` column UTC? {#h-29}

**Issue.** `DATE` is `YYYYMMDDHHMMSS` and marks a 15-minute bucket. **No
first-party document read in this review states a timezone** — not the dataset
announcement, not the data index. Mission 1.9.1 recorded it as UTC; that was not
established, and review 3 does not assert it.

**Why it is unresolved.** GDELT does not say. Inferring it from the delivery time
of one file would be a measurement of this machine's clock and this network's
latency, not of the source.

**Why it blocks nothing.** The collector must preserve the source label verbatim,
so answering this later is a re-derivation over records already held rather than
a re-collection. Until it is answered, no canonical period may claim a zone.

**Needed.** A first-party statement, or an operator answer.

**Vendor contact needed?** Possibly — this is a one-line question to GDELT.
**Legal counsel appropriate?** No.
**Developer action needed?** No, so long as the raw label is preserved.

---

## H-30 — Does GDELT publish a CLD2-name-to-language-tag mapping? {#h-30}

**Issue.** `LANG` is "the human-readable language name as output by CLD2" —
`ALBANIAN`, mostly uppercase, some titlecase, some with underscores. The
project's canonical language representation is a BCP-47 tag. No mapping between
the two was found.

**Why it is unresolved.** Composing one would be guessing, and the failure mode is
silent: a wrong tag looks exactly like a right one downstream. `LANG` must never
become `geography` either — that is settled and is not this question.

**Why it blocks nothing.** The source label is preserved honestly, the same way
`CanonicalGeography.unclassified` preserves a code nobody can map.

**Needed.** A published mapping from CLD2 language names to language tags, from
GDELT or from the CLD2 project.

**Vendor contact needed?** No. **Legal counsel appropriate?** No.
**Developer action needed?** Only when a normalizer is written.

---

## H-31 — How far back does the WEB-NGRAM publication directory reach? {#h-31}

**Issue.** GDELT documents coverage "spanning January 1, 2019 to present". It does
**not** say how long a given 15-minute file stays retrievable at
`data.gdeltproject.org/gdeltv3/web/ngrams/`.

**Why it is unresolved.** Nothing first-party addresses it, and probing the
directory to find out would be collection rather than documentation inspection.

**Why it blocks nothing.** No historical backfill window is assumed. A collector
bounded to eight files per job is asking for a recent window in any case.

**Needed.** A first-party statement, or a deliberate bounded probe under a future
mission's authority.

**Vendor contact needed?** No. **Legal counsel appropriate?** No.
**Developer action needed?** Only if historical backfill is ever wanted.
