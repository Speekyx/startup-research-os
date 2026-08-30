# Consumer, social and emerging-trend source expansion V1

**Status:** Review record. Produced by Mission 1.7.
**Date:** 2026-08-30
**Reviewer:** `mission-1.7`
**Governed by:** [`source-registry-v1.md`](source-registry-v1.md),
[`source-review-guide.md`](source-review-guide.md)
**Results:** [`source-review-results-v1.md`](source-review-results-v1.md) ·
[`source-signal-coverage-v1.md`](source-signal-coverage-v1.md) ·
[`source-portfolio-v1.md`](source-portfolio-v1.md)
**Open items:** [`source-human-review-queue-v1.md`](source-human-review-queue-v1.md)

---

## 0. Why this round happened

The catalog after Mission 1.3 held thirteen sources, and the three that reached
an approving state were all macroeconomic statistics agencies. That is a
defensible outcome of an honest review — statistics agencies publish their
licences and social platforms restrict reuse — and it produces a research engine
that can only see what national accounts can see.

`PROJECT_MANIFEST.md` commits the system to opportunities in gaming,
entertainment, creator economy, social products and hobby products.
`docs/CLAUDE.md` states that desire, curiosity, entertainment, creativity,
learning, competition and social interaction are first-class opportunity
drivers, and that problem-first is valid but not mandatory. A portfolio of three
economic sources cannot serve either statement.

So the question this round asked was not "can we approve more sources". It was
**which signal families can the system see at all, and which can it not**, with
the second half being the answer that matters.

---

## 1. What was assessed, and against what

The use case is unchanged, deliberately, and is quoted in full at the top of
[`source-review-results-v1.md`](source-review-results-v1.md): automated
collection of public content by a **commercial multi-tenant SaaS** for storage,
derived analytics and LLM processing. Narrowing it — to research, to
non-commercial, to internal-only — would have produced more approvals and made
every one of them useless, because the assessment would no longer describe what
the product does.

**Twenty-six platforms were examined; fourteen were registered.** The twelve that
were not are covered in §5.

Every governance verdict rests on a document retrieved from the source's own
site on 2026-08-30. Search results, community discussion and model recall were
used to FIND candidate documents and never to establish what one says: the
evidence type enum has no value for a blog post, so the registry cannot store
one as the basis of an approval even if a reviewer wanted it to.

---

## 2. The results, in the order that matters

### 2.1 Five sources reached an approving state

| Source | Family | What settled it |
|---|---|---|
| `gdelt` | news | "unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee" |
| `wikimedia-pageviews` | knowledge | The Foundation's own terms state the licences "do allow commercial uses" |
| `openalex` | knowledge | All data is CC0 — public domain, no attribution obligation at all |
| `npm-registry` | developer | "You may replicate data from the Public Registry using the Public APIs" |
| `pypi` | developer | Prohibits named misuses; automated API access is not among them |

**None of the five is collector-eligible**, and that is not a technicality. Each
carries conditions, and a condition is cleared by a verifier and by nothing else
(ADR-016). The eleven conditions these five carry name verifications no
capability implements, because the compliance capabilities that would check them
are parameterised for a *collector*, and §29 forbids writing one. This is
precisely the state Mission 1.3 left `world-bank`, `eurostat` and `fred` in;
Mission 1.4 resolved it by building the capabilities, and the same step is what
these five now need.

### 2.2 npm and PyPI are not equivalent, despite matching verdicts

Worth stating because the states are identical and the footing is not.

**npm grants** replication through the public API in as many words, in a
document that separately prohibits automating the *website*. A reader skimming
for "is scraping allowed" would get that backwards in both directions.

**PyPI prohibits** a short list of named misuses — API abuse, token sharing to
evade limits, harvesting personal information for recruiters — and says nothing
about whether a commercial product may be built on the data. Its
`commercial_use` verdict is `NOT_ADDRESSED`, not `PERMITTED`. The approving
state rests on the absence of a prohibition that reaches us plus the presence of
a documented API, which is materially weaker than a grant.

Reading two `APPROVED_WITH_CONDITIONS` labels as the same fact is the error this
paragraph exists to prevent.

### 2.3 The two most accessible platforms are both blocked, by silence

This is the finding that best justifies the registry's existence.

**Bluesky** publishes an open protocol, and its own documentation states of the
public firehose: *no API key is required*. Every public post, like and follow is
reachable by anyone. Its Terms of Service, retrieved and read, contain **no
provision at all** about automated access, the API, or machine-learning use of
content.

**Hugging Face** documents open endpoints and publishes exact numeric rate
limits per account tier. Its Terms of Service, retrieved and read, address
neither automated collection nor commercial reuse of Hub metadata.

Both are `REQUIRES_REVIEW`. Not because anyone refused — because nobody
addressed it, and `source-registry-v1.md` §1 rule 2 admits no path from *we
could not check* to *we may proceed*. The distance between "we can reach this
trivially" and "we may use it" is the whole point of the gate, and no pair of
sources in the catalog illustrates it better.

Hugging Face has a near-miss worth naming. Its ToS **does** contain a broad
licence grant — public repositories grant every user rights to use, reproduce
and make derivative works. That grant runs between *users* and covers repository
*content*. What this system would collect is platform metadata: download counts,
likes, trending placement. No clause mentions it. Reading the content grant as
covering metadata would be inferring permission from an adjacent one, which is
the move §12 forbids by name.

### 2.4 Spotify is the only clean prohibition

Assessed and closed on its own words. The Developer Terms forbid storing,
aggregating or creating databases of Spotify Content; forbid using the platform
or its content to train a machine-learning or AI model; forbid robots and
spiders retrieving or indexing any portion; and forbid transferring content to
third parties **including as aggregate, anonymous or derivative data** — which
closes the usual fallback of keeping only statistics.

Four of the activities this system requires are prohibited by name. No condition
could make the use permissible, so none is written.

### 2.5 Steam is the expensive one

The single richest gaming source available, and `RESTRICTED`.

Its API Terms were retrieved and read. They plainly permit things: automated API
access with a key, storage subject to a disclosed country, distribution of Steam
Data to end users through an Application, one hundred thousand calls per day.
What they grant is *distribution to end users for their personal use via your
Application*. Accumulating Steam Data into an analytical corpus and selling
derived intelligence is not that, and the terms separately prohibit presenting
Steam Data so that it appears to be available from a third party.

`RESTRICTED` rather than `REQUIRES_REVIEW` is deliberate: the documents were
read, some assessed activities are permitted, and ours is outside the grant they
make. That is the definition of the state.

The consequence is that `competition` and `collection` — two signal families
Steam is almost alone in exposing — have **no usable source at all**.

### 2.6 Meta is blocked twice over, and the cheaper check comes first

The Platform Terms authorise use only as the developer documentation permits and
prohibit selling or licensing Platform Data, which reaches the output of a
commercial intelligence product directly.

But the prior question is a capability one: Meta's APIs serve accounts a
developer owns or manages, not the public graph. If no endpoint exposes public
content from accounts we do not control, the policy analysis is moot for market
research. That question is listed first in the source's open questions because
answering it would close the source without any further legal reading — and
establishing a capability fact is cheaper than establishing a permission.

---

## 3. Four documents could not be retrieved

| Source | What happened |
|---|---|
| `x-twitter` | The Developer Agreement returned **HTTP 402 Payment Required** |
| `discord` | The Developer Terms returned **HTTP 403 Forbidden** |
| `twitch` | Two attempts returned page navigation without the agreement text |
| `pinterest` | The developer site was reached; the terms document did not return its text |

Each is recorded as an environment limitation, not as a statement by the
platform. None is treated as a refusal, and none as a permission.

`reddit` and `stack-exchange` were retried and remain unreachable for the same
reasons Mission 1.3 recorded. Their verdicts and open questions stand unchanged,
and the retry itself is recorded — a blocker confirmed to persist is worth more
to the next reviewer than silence.

**No alternative route was considered for any of them.** Difficulty obtaining
terms is not a reason to bypass them, and an inconvenient API is not a reason to
describe a scraper (`source-registry-v1.md` §1 rule 5).

---

## 4. Federated networks: the modelling gap, left open

Mastodon and Lemmy were investigated and **deliberately not registered**.

The Mastodon API documentation establishes that the API is per-instance and that
no single terms-of-service document governs the network. That is not a
retrieval failure; it is a property of the design. Thousands of instances are
operated by different people under different policies, and several explicitly
forbid the indexing that others permit.

The registry's unit is a source whose policy can be reviewed and whose review
can conclude. A protocol with thousands of independent policies is not one.
Registering `mastodon` would create an identity whose review can never finish,
and whose `REQUIRES_REVIEW` state would read as "somebody should get around to
this" when the honest statement is "this cannot be expressed at this level".

§16 asks for the modelling gap to be documented rather than flattened, so:

> **MODEL-01.** The registry models a source as one operator with one policy.
> Federated networks are one protocol with many operators and many policies, and
> the model cannot express eligibility for one. Three resolutions are available
> and none is free:
>
> 1. **Register instances, not networks** — `mastodon-social` is one operator
>    with one ToS and is perfectly governable. It is also one community of a
>    few hundred thousand people, and the review cost is per instance.
> 2. **Add an instance layer** — a source that carries per-instance policy
>    records, with eligibility resolved per instance. Correct, and a schema
>    change that Mission 1.7 has no mandate to design.
> 3. **Leave federated sources out** — cheap, and it forfeits the only social
>    protocols whose data is structurally open.
>
> Recorded in the human review queue as **H-13**. Not decided here.

Bluesky is deliberately treated differently and the distinction is real: Bluesky
PBC operates the service under one Terms of Service, so the source identity is
coherent even though the underlying protocol is open. It is registered, and it
is blocked on silence rather than on modelling.

---

## 5. Candidates examined and not registered

| Candidate | Why not |
|---|---|
| Mastodon, Lemmy | Federated. §4 above, MODEL-01 |
| Instagram (separately from Meta) | Not a separate governable identity: one Platform Terms document governs both, and they are registered as `meta-instagram` |

The remaining §7 candidates were all registered, including the ones expected to
fail, because a recorded `PROHIBITED` or `RESTRICTED` verdict with its evidence
is worth more than an absence. The next person to propose Spotify will find the
reason it was rejected rather than repeating the review.

---

## 6. AI and ML processing, assessed separately

§10 asks that "AI use" not be treated as one activity. Across the fourteen
reviews the documents themselves rarely make the distinctions:

| What the documents did | Sources |
|---|---|
| Prohibited model training **by name** | `spotify` |
| Granted use so broadly it covers processing without mentioning AI | `gdelt`, `openalex` (CC0) |
| Said **nothing** about model processing | `bluesky`, `huggingface`, `npm-registry`, `pypi`, `steam`, `twitch`, `wikimedia-pageviews` |
| Could not be read | `x-twitter`, `discord`, `pinterest`, `meta-instagram` (partially) |

**Ten of fourteen are `NOT_ADDRESSED` on `model_processing`.** The distinctions
§10 asks for — training versus embeddings versus inference versus summarisation
— are almost never drawn by the source documents, so drawing them in the review
would be inventing structure the evidence does not have.

Two exceptions are worth recording precisely.

`gdelt` and `openalex` are marked `PERMITTED` for model processing on the
strength of general grants — "any kind" and CC0 respectively — rather than on
AI-specific language. That inference is recorded in each review's notes rather
than buried, because it is an inference: a grant written before this question
was current may not have contemplated it, and a reader should be able to see
that the permission is general rather than specific.

`huggingface` is the reverse case and the more instructive one: an AI platform
whose Terms of Service, dated 2022, do not address AI processing of its own
platform metadata.

---

## 7. Personal data

Six of the fourteen new sources carry `IDENTIFIABLE` or higher exposure:
`bluesky`, `discord`, `meta-instagram`, `pinterest`, `x-twitter`, `openalex`.

The last is the surprising one and is worth naming. OpenAlex is CC0 — the
strongest licensing position in the catalog — and it is a corpus of **named
researchers with institutional affiliations**. A CC0 licence settles copyright
and says nothing whatever about privacy. Recording it as `NONE_EXPECTED` because
the licence is permissive would conflate two unrelated questions, so it is
`IDENTIFIABLE`.

`jurisdiction_review_required` remains true on every source in the catalog. GDPR
applicability is a human decision (`data-retention-policy-v1.md` §7) and no code
sets it false. Nothing in this round changed that, and nothing in this round
should be read as having assessed it.

---

## 8. What this round did NOT do

- **No collector was implemented**, for any source, eligible or not.
- **No platform content was collected.** The only external requests made were
  for official documentation *about* sources. `acquisition.raw_records` holds
  the same six World Bank records it held before this mission, unchanged, and
  `normalized_records` the same six.
- **No source became collector-eligible.** The environment view shows the same
  three it showed before: `world-bank`, `eurostat`, `fred`.
- **No reliability weight was assigned** to any source (§35).
- **No opportunity was scored** and evidence aggregation is untouched and still
  uncalibrated (§36).
- **No signal was extracted, nothing was embedded**, and D-12 is still open.
- **No vendor was contacted**, no application submitted, no agreement accepted
  and no plan purchased (§44). Every action that would be required is recorded
  in the human review queue instead.
