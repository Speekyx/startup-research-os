# Wikimedia Pageviews V1 — Review, Collector, Normalizer and Signal

**Authoritative.** Mission 1.19. The first source in the portfolio whose rights
basis is a **waiver** rather than a licence with conditions, and the first whose
governing obligation is on the REQUEST rather than on the output.

**Verdict: `APPROVED_WITH_CONDITIONS` under `local-private-research-v1`.**
ELIGIBLE, resource-ready, collected, normalized and derived from. **21
RawRecords, 21 NormalizedRecords all `VALID`, 18 Signals, 18 OBSERVED Claims, 18
Evidence rows** — all `NON_SCORABLE`, because no reliability applies and none was
invented.

---

## 1. The blocker was a named question, and the answer was one page away

Mission 1.8 downgraded this source to `REQUIRES_REVIEW` under the commercial
profile, on a question it wrote down precisely:

> determine whether aggregate pageview COUNTS are Licensed Material under CC
> BY-SA 4.0. If they are, Section 2 grants storage and the production of Adapted
> Material and this source is approvable.

That framing had one possibility it did not consider, and it is the true one:
**the counts are not CC BY-SA at all.**

The Analytics API's **Access policy** page carries a section headed *Data
licensing* whose entire content is:

> Data provided by the API is available under the CC0 1.0 license

That is not the documentation-site footer Mission 1.7 misread and Mission 1.8
correctly rejected. It is a dedicated heading on the API's own access-policy
page, about the data the API returns. **H-24 is answered for this profile.**

## 2. CC0 1.0, and why it is the strongest basis in this catalog

Retrieved and read in full. Section 1 defines *Copyright and Related Rights* to
include *"rights protecting the extraction, dissemination, use and reuse of data
in a Work"* and *"database rights (such as those arising under Directive
96/9/EC)"*. Section 2 waives all of them *"overtly, fully, permanently,
irrevocably and unconditionally"* and *"for any purpose whatsoever, including
without limitation commercial"*. Section 3 supplies a licence if the waiver is
ever judged ineffective.

So storage, retention, commercial use, derived analytics, model processing and
redistribution are granted by **one instrument**, and the **sui generis database
right is waived by name** — the first time any source in this catalog addresses
the right that has blocked TED for eleven missions. It resolves nothing about
TED; it shows what a resolution looks like.

## 3. What is conditional is the MANNER of access

The obligations here run the opposite way from every earlier source. CC0 imposes
nothing on the output. What the operator does impose is a condition on the
**request**:

> The API requires an HTTP User-Agent header for all requests

> Clients making requests without a User-Agent header may be blocked without
> notice

and the Foundation's User-Agent Policy refuses non-descriptive defaults **by
name** — `python-requests/x` is the example it gives — and directs clients not to
copy a browser string.

**That is an objective property of collector configuration, so it is verified by
a capability rather than confirmed by a person** (ADR-028). Writing it as
`HUMAN_CONFIRMATION` would have created the bootstrap ADR-028 exists to name:
nothing authorised until somebody confirms behaviour, and nobody able to confirm
behaviour until the collector exists.

`source-client-identification` was built in this mission **because a condition
named it**, in that order. Mission 1.8 had asserted that no such capability
existed, on the rule that an abstraction no condition names must not be built;
that assertion moved rather than being deleted.

## 4. Attribution is a courtesy here, not a condition — a portfolio first

CC0 contains no attribution requirement anywhere, and Section 2 surrenders the
rights that would let one be imposed.

A credit is rendered anyway — `SOURCE_CREDIT`, `LICENCE_IDENTIFIER` and a
per-item `SOURCE_ITEM_LINK` — for two reasons, **neither of which is an
obligation**: a derived surface should say where its numbers came from, and the
pipeline refuses to normalize a raw record carrying no rendered notice.

**So no condition asserts an attribution obligation.** Writing one would record a
duty the instrument does not create, and a later reader would have no way to tell
an obligation from a courtesy. The CC BY-SA notice that Wikimedia **article
text** carries is a different question about different material, and no article
text is acquired.

## 5. The resource

```text
metrics/pageviews/per-article/en.wikipedia.org
  family:  wikimedia-pageviews-per-article
  route:   wikimedia-analytics-api   (OFFICIAL_API, https://wikimedia.org/api/rest_v1/)
  licence: CC0-1.0                   rights basis: NAMED_LICENCE
  origin:  PLATFORM_LICENSED         (§6)
```

**One project, one endpoint, one granularity.** Wikimedia runs over 300
Wikipedias plus Commons, Wiktionary and Wikisource; they are the same platform
and different corpora with different editorial communities and different reader
populations. A review that said "Wikimedia" would have approved all of them
without looking.

**Refused by name**: the bulk dumps route (registered in this mission **so that
it could be refused**, because the access policy names it in its own words), and
the editors, edits, unique-devices, by-country, top-articles, media and Commons
dataset families.

**CC0 would permit the bulk download**, which is exactly why the restriction has
to be ours and has to be written down: the reason to stay on the API is a
bounded, checkable acquisition posture, not a limit the licence imposes.

## 6. `PLATFORM_LICENSED`, and why it is not a close call here

Unlike Stack Exchange, where the content is written by users and the
classification had to be argued at length, a pageview count is **produced by the
Wikimedia Foundation from its own request logs**. The Foundation is the producer
and the licensor, it states the licence on its own access-policy page, and there
is no third party with a claim over the aggregate. The documentary link holds at
both ends with nothing left over.

## 7. Personal data — the opposite shape from Stack Exchange

There is nothing to exclude. The per-article endpoint returns `project`,
`article`, `granularity`, `timestamp`, `access`, `agent` and `views`. No user
object, no identifier, no location.

| Allowed | Excluded |
|---|---|
| `project`, `article`, `granularity`, `timestamp`, `access`, `agent`, `views` | `editor`, `user_text`, `user_id`, `user_name`, `ip`, `country`, `natural_person_name`, `personal_identifier` |

The excluded names are the fields the endpoints **next door** return. None is
reachable through the authorised resource, and each is refused by name so that a
later widening has to be a review act rather than a parameter change.

**`agent` is allowed and is load-bearing.** It is the field that lets a record
say whether a count is the `user` class or includes spiders and automated
traffic. Dropping it would make every count mean less while looking cleaner.

## 8. Conditions

| Key | Verification | What it enforces |
|---|---|---|
| `wikimedia-client-identification` | CAPABILITY `source-client-identification` | The declared User-Agent names the client and a contact, and is not a generic default or a browser string |
| `wikimedia-official-api-only` | CAPABILITY `source-route-binding` | Analytics API only; bulk dumps refused by name |
| `wikimedia-aggregate-only` | CAPABILITY `source-field-minimisation` | Aggregate per-article counts only; any per-person or per-country field refused by name |

All three verify **satisfied**.

## 9. The collector

**`wikimedia-pageviews-per-article@1.0.0`**, official API only, one project, no
fallback.

| | |
|---|---|
| Route | `wikimedia-analytics-api`, by label; bulk dumps blocked and absent from the context |
| Constants, not parameters | `project`, `agent`, `access`, `granularity` — each hides a different mistake if it becomes an argument |
| Bounds | `articles`, `from_date`, `to_date`, `max_articles`, `max_days` all **required**; `WikimediaPageviewsBounds()` is a `TypeError` |
| Two floors | 2015-07-01 is the **source's** earliest day; ten requests per job is **ours** |
| Discovery | **impossible.** `articles` is an explicit tuple: no pattern, no category, no search. A collector that could enumerate articles could enumerate the encyclopedia |
| Fifth gate | **identity** — the collector refuses when the transport would send a User-Agent the review did not declare |
| 404 | an **ABSENCE**, not a failure and never a zero (ADR-023) |

**`agent=user` is not a parameter, and that is a semantic decision rather than a
scope one.** `all-agents` would silently fold in self-identified bots and
detected automation, and the resulting number would answer a different question
under the same field name.

## 10. The real bounded acquisition

```text
project      en.wikipedia.org      endpoint  https://wikimedia.org/api/rest_v1/
articles     Kubernetes, Docker_(software), Podman
window       2024-03-01 to 2024-03-07        access all-access, agent user
max_articles 3                     max_days  7
```

| | |
|---|---|
| HTTP requests | **3** — one per article |
| Articles returned / absent | 3 / 0 |
| RawRecords persisted | **21 new** (3 articles × 7 days) |
| Fields received the review did not assess | **none** |

**Idempotency verified**: the identical acquisition re-run gave
`new: 0, unchanged: 21, revised: 0`.

## 11. The record kind and the normalizer

**`content_request_count`** — migration 0025, one registry row, no schema change.
The **fifth** kind, and named for a SHAPE again: any platform publishing how many
times a named item was requested has this shape.

**The name says REQUEST, not VIEW.** The operator's definition is *"a request for
content of a page that receives a response of 200 OK or 304 Not Modified"*.
"View" implies a person looked, and in the vocabulary that implication is one
nothing downstream could unmake.

**`audience.class` is REQUIRED**, which is the design decision worth arguing. The
same item on the same day carries a different count for `user` than for
`all-agents`; a record that could not say which one it held would be two
measurements wearing one name.

**`wikimedia-pageview@1.0.0`**, run over all 21 records, all `VALID`. Idempotent.

**The period is a UTC DAY and the timezone is `ESTABLISHED` on documentation, not
on shape.** The API's concepts page designates `Research:Page view` as the
complete definition, and that page states a *"UTC timestamp of the request"* and
*"daily partitioning 0:00 UTC - 23:59 UTC"*. GDELT's H-29 stays open for the
opposite reason: nothing there states the zone at all. Recorded as an open
question that the API **reference** does not restate it.

A day is an interval, so `[start, start + 1 day)` half-open, and `observed_at` is
the interval's start — never the instant a request happened.

## 12. The Signal — outcome S1, and the confounder is in the record

**`content-request-change@1.0.0`** (ADR-032, migration 0026): the change in one
item's request count between two **adjacent** periods, under one requester class
and one access channel. **18 real Signals**, three articles × six adjacent day
pairs.

**Both members are the SAME item, so every item-level confounder cancels
exactly**: prominence, title, age, link structure and disambiguation are
identical on both sides of the subtraction. That is why this derivation was
implemented and the cross-item contrast was not — an item-to-item comparison
carries every one of those confounders and nothing in the record can measure
them.

**What does not cancel is the calendar, and the sample makes it unmissable.**
2024-03-02 and 2024-03-03 are a Saturday and a Sunday; Kubernetes falls from
2,058 to 1,188 to 1,139 and recovers to 2,051 on the Monday. Docker moves the
same way. A Sunday-to-Monday change here is mostly a statement about the week.
News events do not cancel either.

**Neither confounder makes the subtraction untrue.** They make an inference from
it unsound, which is a different failure at a different layer — and it is why the
signal type's own summary, the migration's comment and every Claim built on it
say so rather than relying on a reader's caution.

**A gap is never bridged** (ADR-023): two periods must be exactly consecutive,
and a daily request series has gaps whenever an item drew no requests at all.

## 13. Claims and Evidence

**18 OBSERVED Claims and 18 Evidence rows**, through a fifth template on the
existing interpreter — `observed-signal-restatement@1.2.0`, not a Wikimedia
interpreter, because a template is specific to a SIGNAL TYPE and never to a
publisher.

A real statement, read back from the database:

> Wikimedia Analytics (Pageviews) counted 912 more requests for "Kubernetes" on
> "en.wikipedia.org" on "2024-03-04" than on "2024-03-03", under its own
> requester class "user".

**COUNTED**, not measured, observed or recorded. And the requester class is **in
the sentence**, not only in the scope: a reader who meets this claim without it
cannot know whether the number includes bots, and the platform's own class name
is the only honest way to say it.

Every Evidence row: `SUPPORTS`, relevance 1.0, directness 1.0, extraction
confidence 1.0, `UNCATEGORISED`, independence `UNKNOWN`, evidence level 1,
**reliability NULL → `NON_SCORABLE`**. No reliability was invented and none was
reviewed; that is Mission 1.19 §24 working, not a gap.

## 14. Known limitations

1. The UTC day boundary rests on a definition page the API documentation
   designates rather than on the API reference itself (§11).
2. **H-24 is answered for the LOCAL profile only.** The commercial review stays
   `REQUIRES_REVIEW`; applying this finding there is a commercial-profile review
   act that has not happened, and approval never transfers (ADR-027).
3. Only `en.wikipedia.org` is authorised, and only the per-article endpoint.
4. The `automated` agent detection is documented by the operator as heuristic, so
   `user` means *not identified as automated*, never *human*.
5. Wikimedia Enterprise is presented as the route for high-volume commercial
   reuse with no stated threshold. Nothing here rests on the free route being
   adequate above single-digit requests per job.
6. **A page request is not a reader, a user, a customer or a market.** This
   source adds a behavioural dimension the portfolio lacked; it does not add
   demand evidence, and no Claim here says otherwise.
7. The same ENTITY measured repeatedly is not the same USER PROBLEM recurring.
   This source supplies the first and says nothing about the second.
