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
| [H-29](#h-29) | GDELT | refinement | Is the WEB-NGRAM `DATE` column UTC? **Re-checked in Mission 1.12 and still open** — [why](#h-29-update) |
| [H-30](#h-30) | GDELT | refinement | Is there a CLD2-name-to-language-tag mapping? |
| [H-31](#h-31) | GDELT | — | [**RESOLVED & REFINED**](#h-31-update) — coverage vs current extent, both answered |
| [H-32](#h-32) | GDELT | — | [**RESOLVED**](#h-32-update) — GDELT orders this stream itself |

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

---

## H-32 — Are the WEB-NGRAM `DATE` stamps monotonic within one stream? {#h-32}

**Issue.** Mission 1.11 needed to know whether two observations from the same
GDELT access path can be placed in ORDER without anyone asserting what timezone
their labels are in. That is a different question from [H-29](#h-29), and a
strictly weaker one.

**Why it looked answerable from here.** `YYYYMMDDHHMMSS` is fixed-width, so
lexicographic order equals chronological order within any single fixed offset.
The label is also the published filename, and two files in one directory cannot
share a name -- so a repeated label would be a collision a system publishing
every fifteen minutes for years would not survive unnoticed.

**Why it is unresolved.** That is an inference about the publisher's mechanism,
not a retrieved statement about the data. If the stamps were local time in a zone
observing daylight saving, one hour per year would repeat and order would invert
inside it; the filename argument says GDELT would have noticed *something*, not
that this system may assume what they did about it. It is the class of reasoning
`geography-mapping-v1.json` exists to replace.

**What it blocks.** Every within-stream sequential derivation: frequency change,
growth, decline, moving averages, rolling and baseline windows. A signal may not
carry a direction without it. What stays available is label EQUALITY -- a
contrast between terms inside one bucket -- and set cardinality over buckets.

**Why it is worth asking separately.** A first-party page stating the zone
answers H-29 and this together. A page stating only that the stamps are monotonic
and non-repeating answers this one alone, and unblocks six blocked operations
without anyone asserting UTC.

**Needed.** A first-party statement, or an operator answer. One line.

**Vendor contact needed?** Possibly -- the same message that would ask H-29.
**Legal counsel appropriate?** No.
**Developer action needed?** No. The exact label is preserved, so answering this
later is a re-derivation over records already held.

---

## H-29 — update after Mission 1.12 {#h-29-update}

**Re-checked against first-party material on 2026-08-30 and still OPEN.**

The words UTC, GMT, timezone and "time zone" appear **nowhere** on the WEB-NGRAM
announcement, and `gdeltproject.org/data.html` states none for any dataset.

**GDELT does document UTC — for a different dataset**, and the difference is the
whole point:

| | WEB-NGRAM (ours) | Web News NGrams 3.0 |
|---|---|---|
| path | `gdeltv3/web/ngrams/` | `gdeltv3/webngrams/` |
| BigQuery | `web_1grams` / `web_2grams` | `webngrams` |
| cadence | every 15 minutes | every minute |
| what `date` MEANS | the **15-minute bucket** the counts aggregate | "the JSON timestamp **when the article was seen**" |
| timezone | unstated | **UTC, stated** |

A timezone documented for an article-observation instant says nothing about an
aggregation window in another dataset, and the 3.0 announcement never mentions
`gdeltv3/web/ngrams`. A third family, `gdeltv5/weblegacy/ngrams/`, states none
either.

**A timing observation was available and was refused.** `LASTUPDATE` named
bucket `20260830184500` while the response carried `last-modified: 18:50:30
GMT`. That compares a Google Cloud Storage object's write time against this
machine's clock, from one sample, and even a clean result would not distinguish
UTC from a fixed-offset zone that equals it today.

**Needed, unchanged.** A first-party statement, or an operator answer.

---

## H-31 — update after Mission 1.12 {#h-31-update}

**RESOLVED, and refined into the two questions it was.**

| | Question | Answer |
|---|---|---|
| **H-31a** | Dataset **semantic coverage** | **2019-01-01.** The announcement: "January 1, 2019 through present" |
| **H-31b** | Current **download directory extent** | **`20190101000000`.** A bounded read of `MASTERFILELIST.TXT` shows the current index beginning at the dataset's first bucket |

**H-31b is an observation, not a guarantee.** GDELT publishes no retention
commitment for this directory, so no backfill plan may assume a file will still
be fetchable later. The acquisition bounds are unchanged.

The same index also lists a **third** file per bucket, `chargram`, which the
announcement does not document and no review has assessed. Recorded so its
existence is a known fact; it is not authorised.

---

## H-32 — update after Mission 1.12 {#h-32-update}

**RESOLVED. Ordering is established; the timezone is not.**

Three first-party artifacts, retrieved 2026-08-30:

1. **GDELT orders this column itself.** Its published BigQuery analysis over
   `gdelt-bq.gdeltv2.web_1grams` reads `SUBSTR(CAST(DATE AS STRING), 0, 8)` as a
   calendar day and `ORDER BY DATE ASC` to chart a nine-month series.
2. **GDELT sequences its own directory by the label.** `MASTERFILELIST.TXT` is
   published in ascending label order at **15-minute resolution**, across 7.6
   years.
3. **GDELT calls the maximal label the newest.** `LASTUPDATE.TXT` names exactly
   the last entry of `MASTERFILELIST`.

The daylight-saving objection is answered by the artifacts rather than argued
away: a repeating wall-clock label would need a duplicate filename in one flat
directory, and would break the "newest = largest" invariant `LASTUPDATE` is
built on.

**Scope.** `gdelt`, resources `web-ngrams/1gram` and `web-ngrams/2gram` **named
exactly**, label scheme `gdelt-web-ngram-bucket`, review 3. It grants
`SOURCE_RELATIVE_ORDER` and nothing else. It is not a rule about
`YYYYMMDDHHMMSS` strings and no other GDELT dataset inherits it.

Full record: [`gdelt-web-ngram-temporal-evidence-v1.md`](gdelt-web-ngram-temporal-evidence-v1.md),
[ADR-022](../architecture/adr/ADR-022-web-ngram-source-relative-order.md).


---

## H-5 — update after Mission 1.15 {#h-5-update}

**Resolved, against us.** The Y Combinator Terms of Use were retrieved on
2026-08-31 and the ambiguity H-5 recorded is not there. Two clauses settle it
without needing the API question answered:

> *"you will not engage in or use any data mining, robots, scraping or similar
> data gathering or extraction methods"*

> *"you agree not to display, distribute, license, perform, publish, reproduce,
> duplicate, copy, create derivative works from, modify, sell, resell, exploit,
> transfer or upload for any commercial purposes, any portion of the Site"*

The Terms also state that use of certain Site components is subject to the Hacker
News Guidelines, which places `news.ycombinator.com` in scope explicitly.

H-5 asked whether publishing an API constitutes authorisation for commercial
derived analytics. The first clause makes it moot: the **collection method** is
prohibited regardless of what the API's publication implies about the output.

`hacker-news` moved to **RESTRICTED** at review v3. The vendor contact remains
available — `api@ycombinator.com` — but it is now a request for a written
exception rather than a clarifying question, which is a different kind of ask.

**Status:** closed. Superseded by the v3 review.

---

## H-33 — Bluesky publishes developer guidelines that cannot be retrieved {#h-33}

**Issue.** Bluesky's documentation domain names a *Bluesky Developer Guidelines*
document — the guidelines developers who federate apps or services on the AT
Protocol must follow to communicate with Bluesky services. Its canonical URL,
`https://docs.bsky.app/docs/support/developer-guidelines`, returns HTTP 301 to
`https://bsky.network/docs/support/developer-guidelines`, and that URL returned
an empty body on 2026-08-31. The documentation root at `bsky.network` links to no
terms, guidelines or legal document at all.

**Why it matters.** Bluesky's user Terms of Service are silent on all ten
activities that matter to a third party reading public records — re-confirmed at
the current version, updated effective 15 September 2025. If the developer
guidelines address commercial use, storage, automated access and machine
learning, Bluesky becomes assessable; if they do not, it is silent everywhere and
the question closes. Either answer moves the catalog's most-cited open question.

**Why it is unresolved.** A retrieval failure. No mirror, cached copy or
third-party transcription was consulted, because a failed retrieval leaves a
question open rather than licensing a substitute.

**Needed.** The document text, from `bsky.network` or `docs.bsky.app`, retrieved
in an ordinary browser session.

**Vendor contact needed?** Only if the document stays unreachable.
**Legal counsel appropriate?** Not yet — this is a retrieval problem, not an
interpretation one.

---

## H-34 — Does the EU's reuse framework address machine-learning processing of TED notices? {#h-34}

**Issue.** The TED legal notice grants, verbatim:

> *"Unless otherwise noted, the procurement notices published in the Supplement
> to the Official Journal of the European Union can be freely reused, for
> commercial or non-commercial purposes."*

That grants five of the six load-bearing activities directly:
`automated_access`, `api_use`, `commercial_use`, `storage`, `derived_analytics`.
It names machine learning, text mining, training and inference **nowhere**.

**Why it matters.** This is the single activity standing between `ted-eu` and an
approving verdict, and `ted-eu` would be the portfolio's **first
WILLINGNESS_TO_PAY source** — a family with no registered candidate at all before
Mission 1.15. A contract award notice records what a buyer paid a named supplier,
which is a transaction rather than a listed price.

**Why it is unresolved.** Silence is not permission (`source-registry-v1.md` §1
rule 2), and rule 8 blocks an approving state when any materially required
activity is `NOT_ADDRESSED`. The assessed use case includes LLM processing and
must not be narrowed to rescue a source.

**Needed.** A first-party instrument addressing further processing of reused
Official Journal material — the Publications Office's reuse decision or an
equivalent. A general legal principle about EU open data is not a source
document and cannot settle this.

**Vendor contact needed?** Possibly — the Publications Office publishes a contact
route. Not contacted.
**Legal counsel appropriate?** **Yes**, if the instrument is silent too. The
question then becomes whether a broad reuse grant covers ML processing by
default, which is a legal reading rather than a document retrieval.

---

## H-35 — USAspending publishes no licence or terms document {#h-35}

**Issue.** Three first-party locations were tried on 2026-08-31 and none carried
a licence, terms of use, attribution requirement or rate limit:

- `https://api.usaspending.gov/` — states the data *"is open source and provided
  to the public as part of the DATA Act"* and nothing further;
- `https://www.usaspending.gov/about` — returned no page content;
- the operating agency's own repository README — repeats the DATA Act sentence.

**Why it matters.** USAspending is the second lawful-looking route to
`WILLINGNESS_TO_PAY` as a transaction, and corroboration from a second
independent procurement system is a materially different evidential position from
one source alone.

**Why it is unresolved.** The DATA Act sentence establishes that the data must be
publicly **accessible**. That is a statement about publication, not a grant of
reuse rights to a commercial product — the same distinction that keeps Bluesky's
public firehose from being permission.

**Needed.** A licence or terms-of-use document, or a first-party statement of the
data's copyright status. A reviewer might reasonably expect US federal works to
be uncopyrighted; that is a general legal principle and no verdict may rest on
one.

**Vendor contact needed?** Possibly.
**Legal counsel appropriate?** Yes, if no document exists — the question becomes
whether the absence of copyright is itself the grant.

---

## H-34 — update after Mission 1.15.1 {#h-34-update}

**Still open, and now precise.** Mission 1.15.1 was a narrow mission to close
H-34 in either direction. It could not, and the reason changed the question.

**What is now established.** TED's own legal notice names the governing
instrument:

> *"The European Commission's reuse policy is implemented by the Commission
> Decision of 12 December 2011 on the reuse of Commission documents."*

That is **Commission Decision 2011/833/EU**, published in Official Journal L 330,
linked by TED at `https://eur-lex.europa.eu/eli/dec/2011/833/oj`. The link is
proven from first-party material rather than assumed, which is what H-34's
original wording — *"the Publications Office's reuse decision, or another
first-party instrument"* — could not say.

**What blocks it.** The Decision could not be retrieved. Five first-party EUR-Lex
addresses were attempted on 2026-08-31 — the ELI URL, the ELI English URL, the
CELEX text URL, the CELEX HTML URL and the Official Journal PDF — and every one
returned an empty body. The Publications Office's own copyright notice does not
restate it and is silent on text and data mining, machine learning and automated
processing. The TED Developer Docs link back to the same legal notice.

**Why this is worse than silence, not better.** The grant reads *"can be freely
reused, for commercial or non-commercial purposes"*. The operative word is
**reused**, and its scope is defined in the instrument that could not be read.
Treating the grant as covering machine-learning inference would mean assuming a
definition from an unread document — which is a weaker basis than inferring from
observed silence, because silence is at least established.

**Needed.** Commission Decision 2011/833/EU, retrieved from EUR-Lex in an
environment that renders it. Specifically the scope article and the definition of
"reuse", plus anything on databases, extraction, text and data mining or
automated processing.

**Vendor contact needed?** No. This is a public legal instrument at a canonical
address.
**Legal counsel appropriate?** Only if the Decision's definition is itself
ambiguous once read.

**Status:** open, refined. TED-EU review v2 records it.

---

## H-36 — Does the TED reuse grant reach the sui generis database right? {#h-36}

**Issue.** TED is a database, and the documented reuse route is bulk daily and
monthly XML packages — extraction and re-utilisation of substantial portions of
it. The sui generis database right is independent of copyright, and a reuse grant
framed around *documents* does not automatically carry it.

**Why it matters.** It bears on `automated_access` (bulk) and `redistribution`
more than on `model_processing`, so **it could block TED even if H-34 closes
favourably**. Mission 1.15's review recorded seven activities as `PERMITTED` on
one sentence and did not ask this question.

**Why it is unresolved.** Nothing retrieved addresses it. The TED legal notice
does not mention databases, extraction or re-utilisation. The Publications Office
copyright notice does not either. Commission Decision 2011/833/EU could not be
read (H-34).

**Needed.** Whether Decision 2011/833/EU, or another instrument it references,
addresses database rights, extraction or re-utilisation of substantial portions.
Likely answered by the same retrieval that answers H-34.

**Note on process.** This was recorded as a new open question rather than used to
downgrade Mission 1.15's activity findings. It is a question nobody has answered,
not evidence that the earlier review was wrong, and rewriting a prior review on a
suspicion is what the append-only rule exists to prevent.

**Vendor contact needed?** No.
**Legal counsel appropriate?** Yes, if the instrument is silent on database
rights — the question then becomes whether a documents reuse policy carries the
database right by implication.

---

## H-34 — CLOSED after Mission 1.15.2 {#h-34-closed}

**Closed PERMITTED**, on the operative text of Commission Decision 2011/833/EU,
retrieved and read in full on 2026-08-31.

**How it was retrieved.** EUR-Lex failed again — five representations in Mission
1.15.1, plus the Official Journal L 330 full-issue HTML this round.
`publications.europa.eu/resource/celex/32011D0833` redirects to an RDF metadata
object. The text came from the **Publications Office's own Cellar repository**,
addressed by the Cellar identifier `cb76d4a0-c886-40bd-99d7-8db018a723d0` that
the Publications Office publication record itself publishes. Four pages,
Articles 1–13.

**What closed it.** Article 3(2):

> *"'reuse' means the use of documents by persons or legal entities of
> documents, for commercial or non-commercial purposes other than the initial
> purpose for which the documents were produced."*

The definition is framed by **purpose** and enumerates no acts. Article 4 makes
all in-scope documents available for reuse on that footing; Article 6(2) says
conditions *"shall not unnecessarily restrict possibilities for reuse"* and
lists three, none of them about method; the Article 2(2) exclusions are classes
of document rather than methods of use; and the only manner-of-use prohibition
in the instrument is Article 2(4)'s reuse *"calculated to deceive or to
defraud"*.

This is not silence about machine learning. It is a grant whose operative term is
defined broadly enough that method does not enter.

**Scope of what closed.** Inference, extraction, classification and structured
analysis. **Model training was not assessed and is not authorised**; embeddings
are unassessed for implementation and blocked independently by D-12. Recorded as
a condition on review v3 rather than left to prose.

**Status:** closed. See `ted-eu-governing-decision-review-v1.md`.

---

## H-36 — update after Mission 1.15.2 {#h-36-update}

**Still open, and the unknown became an established absence.**

Mission 1.15.1 recorded H-36 as *"the instrument might address database rights
and we cannot read the instrument"*. The instrument has now been read in full and
**does not address them**:

| Term | Occurrences in Decision 2011/833/EU |
|------|------------------------------------:|
| `sui generis` | **0** |
| `extraction` | **0** |
| `re-utilisation` / `reutilisation` | **0** |
| `Directive 96/9` | **0** |
| `database` | 2 — an exclusion for unpublished research, and an example inside the definition of *structured data* |

The Decision is framed throughout around **documents** (Articles 1, 2(1), 3(1)).
The collection those documents sit in is never mentioned. Article 2(2)(a)
excludes industrial property *"such as patents, trademarks, registered designs,
logos and names"*; the database right is not in that list and not elsewhere. The
instrument neither grants over it nor excludes it — **it does not reach it**.

**One fact cuts the other way and is recorded honestly.** SIMAP *system metadata*
is dedicated to the public domain under CC0 1.0, and CC0 waives sui generis
database rights where the dedicator holds them. That shows the Publications
Office addresses this class of right when it means to — and it applies to
metadata, not to the notice corpus a collector would extract. Reading it across
would extend a stated grant past its stated subject.

**Why silence is not permission here.** The maker of the assembled collection is
not established — notices are filed by contracting authorities across the Union.
The Decision enumerates rights it *cannot* grant over, so its silence is not
naturally read as a grant. And the engine's documented route is bulk daily and
monthly packages, which is the paradigm case of repeated and systematic
extraction of substantial parts rather than a marginal one.

**This is now the only question standing between TED and an approving verdict.**
All six load-bearing activities are positively granted at review v3 and the
source remains `REQUIRES_REVIEW`.

**Needed**, cheapest first:

1. A first-party statement from the Publications Office on whether it asserts or
   waives database rights in TED, or whether the reuse policy is intended to
   cover extraction of the corpus.
2. A licence attached to the bulk packages themselves, if one exists — the
   data-reuse page carries none.
3. Legal review of whether a documents reuse policy carries the database right by
   implication, and whether the right subsists in TED at all given who assembles
   it.

**Vendor contact needed?** **Yes** — the Publications Office publishes a contact
route. Not contacted.
**Legal counsel appropriate?** **Yes.** This is no longer a retrieval problem.
It is the first question in the queue that a further document search cannot
answer, because the documents have been read.

**Status:** open. See `ted-eu-database-right-review-v1.md`, and the
Mission 1.15.3 update below.

---

## H-36 — update after Mission 1.15.3: split into H-36A and H-36B {#h-36-split}

**Still open, and now answerable by a named person rather than by more reading.**

Mission 1.15.3 asked the one question Mission 1.15.2 had not: is there a licence
attached to the assembled **dataset**, as opposed to the individual documents?
**There is**, and it changes the shape of the question without changing the
answer.

### What was found

| | |
|---|---|
| `ted-1` DCAT record, publisher **Publications Office** | `dct:license = COM_REUSE` on **every** distribution, including the bulk XML download. No dataset-level licence, no `dct:rights`, **no `dct:creator`** |
| `COM_REUSE` authority concept | `skos:exactMatch` → `http://data.europa.eu/eli/dec/2011/833/oj` — **the licence IS the Decision** |
| TED Search API OpenAPI document | "Terms of Usage" section = one link, to the TED legal notice |
| Bulk page, package HTTP headers, PO notice, europa.eu notice, data.europa.eu notice | **zero** occurrences of `sui generis`, `database right`, `extraction`, `re-utilisation` or 96/9 |

So the silence is not an artefact of reading the wrong document. **The whole
chain has now been read and it closes without ever mentioning the right.**

### The two halves, tracked separately from here

**H-36A — does the right subsist?** **NOT ESTABLISHED, either way.** Directive
96/9/EC Article 7(1) gives the right to a **maker** showing **substantial
investment**; nothing retrieved names a maker or asserts an investment. The
catalogue names a *publisher* and carries **no creator at all**, and notices are
filed by contracting authorities across the Union. Article 11 then makes
subsistence turn on facts about that maker. **A legal question about facts nobody
has published, not a retrieval gap.**

**H-36B — does the right holder grant or waive?** **NOT ADDRESSED for either
route.** Article 7(3) confirms the right *can* be granted by contractual licence.
`COM_REUSE` does not, and it governs both routes.

### The fact that makes it answerable

The same portal declares **CC BY 4.0** — whose Section 4 expressly grants the
right *"to extract, reuse, reproduce, and Share all or a substantial portion of
the contents of the database"* — on **12 of 48** distributions of the separate
`ted-csv` dataset published by **DG GROW**. The other 36 are `COM_REUSE`, and the
two **overlap**: `ted-contract-award-notices-2017-2021.zip` is CC BY 4.0 while
`ted-contract-award-notices-2018-2023.zip` is `COM_REUSE`.

**Not relied on** — a different dataset, a different publisher, and an assignment
inconsistent enough that choosing the favourable licence would mean choosing a
licence by choosing a filename. **But it is a question one person can answer in a
sentence:** is the difference deliberate?

### Needed

1. **Send the prepared clarification** to `op-copyright@publications.europa.eu`,
   the address the TED legal notice publishes for SIMAP copyright issues.
   `GROW-D2@ec.europa.eu` is the route for the CSV-subset question. The message
   is written: `ted-eu-database-right-clarification-request-v1.md`. **Nothing has
   been sent.**
2. **Legal review** if the answer does not settle it:
   `ted-eu-h36-legal-review-packet-v1.md` holds the facts and the questions with
   no conclusion attached.

**Vendor contact needed?** **Yes, and the message is drafted and unsent.**
**Legal counsel appropriate?** **Yes**, and the packet exists to make it cheap.

**Status:** open, `EXTERNAL_CLARIFICATION_REQUIRED`. TED stays
`REQUIRES_REVIEW` at review **v4**. See
`ted-eu-database-right-clarification-v1.md`.
