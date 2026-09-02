# Mission 1.19 — Behavioural & Market Evidence Portfolio Expansion

**Sprint 1. Authorized by the Mission 1.19 brief §0-§32.**

> ## OUTCOME S1 — 18 SIGNALS, AND THE BLOCKER WAS A QUESTION SOMEBODY ANSWERED
>
> Wikimedia Analytics pageviews joins the portfolio: approved under the local
> profile, collected, normalized, derived from, claimed and evidenced. **21
> RawRecords, 21 NormalizedRecords all `VALID`, 18 Signals, 18 OBSERVED Claims,
> 18 Evidence rows — every one `NON_SCORABLE`.**
>
> The source was blocked by a **named open question** from Mission 1.8: are
> aggregate pageview counts Licensed Material under CC BY-SA? The answer, on the
> operator's own access-policy page under a heading called *Data licensing*, is
> that they are **not CC BY-SA at all — they are CC0 1.0**.
>
> Mission 1.18 was S0 because a truthful derivation did not exist. This one is
> S1 because it does, and §12 records exactly which confounder it carries.

Full review: [`wikimedia-pageviews-v1.md`](../data/wikimedia-pageviews-v1.md).

---

## 0. Two documentation corrections, made before any new source work

Both were overstatements in Mission 1.18's own output, and both are corrected in
the prose rather than by acquiring anything.

### Correction A — distinct people

The report read *"15 questions asked on one day about one tag are 15 people
asking 15 things once"*. **Author identity was deliberately never acquired**, so
this deployment cannot count distinct askers and no document may word itself as
though it could.

Corrected to **15 distinct published solution-seeking observations**, in the
1.18 report, in `docs/CLAUDE.md`, in the Stack Exchange review, in the
normalizer's own docstring and in its test. The repair is the sentence; acquiring
an owner object to make the old sentence true would have inverted the whole point
of that review.

### Correction B — the repeated-observation gap

The report read *"no source in the portfolio observes the same subject twice"*.
That contradicts semantics this repository already implements:
`lexical-frequency-change@1.0.0` compares the SAME lexical stream across adjacent
source buckets, and `numeric-period-change@1.0.0` compares the SAME
source-reported metric across periods.

The precise gap is: **SROS holds no Evidence establishing repeated comparable
USER-PROBLEM instances for one narrowly defined problem.** A frequency series and
a metric series both re-observe a stream; neither re-observes a user meeting the
same difficulty.

`mission-1.15-report.md` contains a looser version of the same sentence, scoped
to retention. **It was left as written**: a mission report is a record of what a
mission found, and rewriting history is what `docs/CLAUDE.md` §Versioning
forbids. The correction lives where the claim is still authoritative.

---

## 1. PORTFOLIO — what actually existed before

Recomputed from the live catalog and the live database, not carried forward.

### What was merely approved, versus evidence-producing

| Source | Local review | Collector | Normalized | Signals | Evidence |
|---|---|---|---|---|---|
| `world-bank` | APPROVED | yes | 6 `VALID` | 4 | 4 |
| `gdelt` | APPROVED | yes | 6 `PARTIAL` | 3 | 3 |
| `ted-eu` | APPROVED | yes | 11 `PARTIAL` | 1 | 1 |
| `stack-exchange` | APPROVED | yes | 15 `VALID` | **0** | **0** |
| `eurostat` | APPROVED | **no** | — | — | — |
| `fred` | APPROVED | **no** | — | — | — |
| `openalex` | APPROVED, 2 conditions unsatisfied | **no** | — | — | — |
| 22 others | **no local review at all** | — | — | — | — |

**Seven states, not one.** Registered, approved, eligible, resource-ready,
collected, normalized, signal-producing, evidence-producing — and Stack Exchange
is the canonical demonstration that the last two do not follow from the first
six. It is approved, eligible, collected and normalized, and produces no
evidence at all.

### What the existing evidence could and could not answer

| Dimension | Source | Can answer | Cannot answer |
|---|---|---|---|
| Macro context | World Bank | did a reported national metric move | anything about a product or a person |
| Publication volume | GDELT | how often a token appeared in news text | who read it, or whether anyone wanted anything |
| Public procurement | TED | what one public buyer paid one supplier | whether a private market exists |
| Solution-seeking | Stack Exchange | that somebody published a question | that the problem repeats, or that anyone would pay |

**Nothing in that table observes an interaction.** Every row is either a
publication, a document, or a state of the world reported by an institution.

### The gap selected, and why it beats a source count

The gap was **not** "one more `problem` source". Mission 1.18 proved that
direction is exhausted: `problem` gained an approving, collected, normalized
source and still gained no evidence.

The selected gap is **repeated, comparable observation of an interaction** — a
dimension where the same entity is measured again and again by a platform that
publishes what it counted. It beats a thirtieth source because it is the first
axis on which the portfolio has **no observation at all**, rather than a fifth
variant of an axis it already covers.

---

## 2. SELECTION

Ranked on §9's twelve criteria, on retrieved evidence. No numeric score was
invented: the repository has no canonical selection framework that supports one,
and a single figure would hide which criterion decided.

### Winner — `wikimedia-pageviews`

**Unique information it adds:** daily counts of requests for a named content
item, split by requester class, on a platform that **separates bot traffic from
the rest** — the only source in the catalog that does. It is the first repeated,
comparable, per-entity interaction series the portfolio holds.

Decisive on criterion 4 (legal confidence): **CC0 1.0**, a waiver that grants
storage, derived analytics, commercial use and model processing in one
instrument, and waives the sui generis database right **by name**.

### Runner-up — `npm-registry`

**Higher marginal novelty and blocked by rule 8.** The download-counts API is
genuinely official, documented in npm's own registry repository, returns one row
per package per day, contains no personal data at all, and its Open-Source Terms
grant automated access explicitly — *"You may replicate data from the Public
Registry using the Public APIs per this Agreement"* — while forbidding automation
of the **website**, which is a distinction the terms themselves draw.

It fails on the assessed use, not on interest: **`derived_analytics` and
`model_processing` are `NOT_ADDRESSED`.** The Terms say nothing about what a
reuser may do with replicated data, and *nobody prohibited it* is not *a licensor
granted it* (`source-registry-v1.md` rule 8). Reading the commercial-projects
sentence in the content-neutrality section as a general grant over registry DATA
would have been exactly the over-read that produced Mission 1.7's three
withdrawn approvals.

A second reason it loses even where it does not fail: npm's own documentation
says its counts *"are definitely not the same as the number of 'users' of a
package"* and include *"automated build servers, downloads by mirrors, robots
that download every package for analysis"*, with **no way to separate them**.
Wikimedia publishes an `agent` class; npm explicitly refuses to.

**Its evidence is recorded rather than discarded**, so a later mission starts from
retrieved documents instead of repeating the retrieval.

### Third — `pypi`

Same dimension as npm and weaker on both halves. Its official JSON API publishes
release metadata and **not download counts**; those live in a Google BigQuery
public dataset needing cloud credentials, or on a third-party host — and §14
excludes both. It also carries this repository's own cautionary history: Mission
1.7 approved it with four of six activities unaddressed, and Mission 1.8
withdrew that approval on audit.

### What the winner still cannot support

Product adoption, user counts, customers, demand, willingness to pay, competitive
supply, retention, or a repeated user problem. A request for an encyclopedia
article is a request for an encyclopedia article.

---

## 3. GOVERNANCE

**`APPROVED_WITH_CONDITIONS` under `local-private-research-v1`**, version 1 of
its own profile line. The commercial profile stays `REQUIRES_REVIEW`, and that is
ADR-027 working rather than an oversight: the finding below answers H-24 for the
profile that was reviewed, and applying it to the other one is a review act
nobody has performed.

### The finding that unblocked it

Mission 1.8 wrote the question down precisely, and had one possibility it did not
consider. The Analytics API access policy, section **Data licensing**, in full:

> Data provided by the API is available under the CC0 1.0 license

Not the documentation-site footer Mission 1.7 misread and Mission 1.8 correctly
rejected — a dedicated heading on the API's own access-policy page, about the
data the API returns.

CC0's own text supplies the rest. Section 1 defines Copyright and Related Rights
to include *"rights protecting the extraction, dissemination, use and reuse of
data in a Work"* and *"database rights (such as those arising under Directive
96/9/EC)"*; Section 2 waives them *"overtly, fully, permanently, irrevocably and
unconditionally"* and *"for any purpose whatsoever, including without limitation
commercial"*.

**The sui generis database right is waived by name** — the first time any source
in this catalog addresses the right that has blocked TED for eleven missions. It
resolves nothing about TED. It shows what a resolution looks like.

| Activity | State |
|---|---|
| `automated_access`, `api_use` | PERMITTED_WITH_CONDITIONS (User-Agent, pacing) |
| `commercial_use`, `storage`, `retention`, `derived_analytics`, `redistribution` | PERMITTED (CC0 §2) |
| `model_processing` | PERMITTED_WITH_CONDITIONS — inference only; training and embeddings are not performed and nothing rests on the permission |
| `browser_automation` | NOT_PERMITTED |

### Conditions, and the capability built because one named it

| Key | Verification | Result |
|---|---|---|
| `wikimedia-client-identification` | CAPABILITY `source-client-identification` | SATISFIED |
| `wikimedia-official-api-only` | CAPABILITY `source-route-binding` | SATISFIED |
| `wikimedia-aggregate-only` | CAPABILITY `source-field-minimisation` | SATISFIED |

**The obligations here run the opposite way from every earlier source.** CC0
imposes nothing on the output. What the operator imposes is a condition on the
REQUEST: *"The API requires an HTTP User-Agent header for all requests"* and
*"Clients making requests without a User-Agent header may be blocked without
notice"*, with the Foundation's User-Agent Policy refusing non-descriptive
defaults **by name** (`python-requests/x` is its own example).

That is an objective property of collector configuration, so ADR-028 puts it in a
mechanical verification kind rather than on a person. `source-client-identification`
was built **because a condition named it**, in that order — and Mission 1.8's
assertion that no such capability existed moved rather than being deleted, since
a capability with no condition behind it would still be the unused abstraction §7
forbids.

**The collector refuses to open a socket when the transport would send a
User-Agent the review did not declare.** A declaration nobody sends verifies
against a document instead of against behaviour.

### Attribution is a courtesy here, not a condition — a portfolio first

CC0 contains no attribution requirement, and Section 2 surrenders the rights that
would let one be imposed. A credit is still rendered onto every record — because
a derived surface should say where its numbers came from, and because the
pipeline refuses a record with no notice attached — but **no condition asserts an
obligation the licence does not create.** A later reader can tell the two apart.

### Resource and personal-data posture

One resource: `metrics/pageviews/per-article/en.wikipedia.org`, family
`wikimedia-pageviews-per-article`, `NAMED_LICENCE` / `CC0-1.0`,
`PLATFORM_LICENSED` — and unlike Stack Exchange that classification is not a
close call, because the Foundation produces the aggregate from its own logs.

**Refused by name**: the bulk dumps route (registered in this mission so that it
could be refused), and the editors, edits, unique-devices, by-country,
top-articles, media and Commons families. CC0 would permit the bulk download,
which is exactly why the restriction has to be ours and has to be written down.

**Personal data is the opposite shape from Stack Exchange**: there is none to
exclude. The endpoint returns a project, an article, a granularity, a day, an
access method, an agent class and a count.

---

## 4. REAL DATA

**`wikimedia-pageviews-per-article@1.0.0`.** Five gates before a socket — bounds,
route, resource, fields, and the identity gate no earlier collector has.

```text
project      en.wikipedia.org      articles  Kubernetes, Docker_(software), Podman
window       2024-03-01 → 2024-03-07         access all-access, agent user
max_articles 3                     max_days  7
```

| | |
|---|---|
| HTTP requests | **3** — one per article |
| Articles returned / absent | 3 / 0 |
| RawRecords | **21 new** |
| Idempotency | identical re-run → `new: 0, unchanged: 21, revised: 0` |
| NormalizedRecords | **21**, kind `content_request_count`, **all `VALID`** |

**The sample was chosen to validate the semantic, not to manufacture a Signal.**
Three narrow tool articles over one bounded week — enough to see whether a
truthful multi-observation derivation exists, and short enough that the answer
could have been no.

**`agent=user` is a constant, not a parameter**, and that is a semantic decision
rather than a scope one: `all-agents` would silently fold in bots and answer a
different question under the same field name.

**A 404 is an ABSENCE, not a zero** (ADR-023). The endpoint returns 404 for an
article with no recorded views, and writing a zero would be indistinguishable
from a real measurement of zero.

### The fifth record kind

**`content_request_count`** (migration 0025), named for a SHAPE again — any
platform publishing how many times a named item was requested has it.

**The name says REQUEST, not VIEW.** The operator's own definition is *"a request
for content of a page that receives a response of 200 OK or 304 Not Modified"*.
"View" implies a person looked, and in the vocabulary that implication is one
nothing downstream could unmake.

**`audience.class` is REQUIRED**, which is the design decision worth arguing: the
same item on the same day carries a different count for `user` than for
`all-agents`, and a record that could not say which one it held would be two
measurements wearing one name.

**The period is a UTC DAY, `ESTABLISHED` on documentation rather than on shape.**
The API's concepts page designates `Research:Page view` as the complete
definition, and that page states a *"UTC timestamp of the request"* and *"daily
partitioning 0:00 UTC - 23:59 UTC"*. GDELT's H-29 stays open for the opposite
reason: nothing there states the zone at all. Recorded as an open question that
the API **reference** does not restate it.

---

## 5. SIGNAL — S1, and the confounder is in the record

### What the real data showed

Read back before anything was designed:

| Article | 03-01 | 03-02 | 03-03 | 03-04 | 03-05 | 03-06 | 03-07 |
|---|---|---|---|---|---|---|---|
| Kubernetes | 2058 | 1188 | 1139 | 2051 | 2101 | 2183 | 2133 |
| Docker_(software) | 1641 | 1014 | 1027 | 1762 | 1741 | 1777 | 1832 |
| Podman | 38 | 23 | 17 | 30 | 26 | 28 | 38 |

**2024-03-02 and 2024-03-03 are a Saturday and a Sunday**, and the two larger
articles fall roughly 40 per cent across them and recover on the Monday. That is
visible in the data before any rule is written, and it decided the design.

### The semantic, defined before implementation

**`content-request-change@1.0.0`** — the change in one item's request count
between two **adjacent** periods, under one requester class and one access
channel.

| | |
|---|---|
| Qualifying | two observations of the same item, platform, requester class, access channel and period type, exactly one period apart |
| Non-qualifying | two items; two requester classes; two access channels; a gap; two rows for one period |
| Cohort key | source, kind, item, platform, requester class, access channel, period type |
| Minimum support | 2 |
| Temporal basis | `COMPARABLE_INSTANTS` — earned, because the day bucket's zone is documented |
| Magnitude | `ABSOLUTE_CHANGE`, exact, unit `requests`. No percentage and no ratio |
| Confounders | the calendar and news events, both stated on the type and on every Claim |
| Explicit non-claims | readers, people, users, customers, interest, demand, adoption, popularity, a trend, a market |

### Why this derivation and not the cross-item contrast

**Both members are the SAME item, so every item-level confounder cancels
exactly**: prominence, title, age, link structure and disambiguation are
identical on both sides of the subtraction.

An item-to-item contrast on one day cancels the calendar instead — and carries
every one of those item-level confounders, which nothing in the record can
measure. "Kubernetes gets 54× the requests of Podman" is a fact about two
Wikipedia articles before it is a fact about two tools. **It was considered and
not implemented**, and that refusal is part of the result.

### What the Signals establish, and what they do not

**18 Signals**, three articles × six adjacent day pairs, quantity family
`CONTENT_REQUEST_VOLUME`, derivation confidence 1.0.

They establish that a platform counted a different number of requests for one
named item on two adjacent UTC days, under a named requester class.

They establish **nothing** about readers, users, customers, adoption, interest or
demand — and a Sunday-to-Monday change is mostly a statement about the week.
**Neither confounder makes the subtraction untrue**; they make an inference from
it unsound, which is a different failure at a different layer.

### The fourth quantity family (ADR-032)

`MEASURED_SERIES` was the tempting reuse and is wrong for a **different reason**
than a procurement value was. A request count really is a series, so widening
would not have cost `metric` its meaning — it would have cost the FAMILY its
meaning, by making a page-request change and a population change the same kind of
quantity. The field would still validate and would no longer discriminate, which
is worse than a field that breaks.

`LEXICAL_FREQUENCY` is structurally closer than it looks and still wrong: it
carries a term and a language, and a request count has an item and a requester
class.

---

## 6. CLAIM / EVIDENCE

**18 OBSERVED Claims, 18 revisions, 18 Evidence rows**, through a fifth template
on the existing interpreter — `observed-signal-restatement@1.2.0`, not a
Wikimedia interpreter, because a template is specific to a SIGNAL TYPE and never
to a publisher.

Read back from the database:

> Wikimedia Analytics (Pageviews) counted 912 more requests for "Kubernetes" on
> "en.wikipedia.org" on "2024-03-04" than on "2024-03-03", under its own
> requester class "user".

**COUNTED** — not measured, observed or recorded. And the requester class is **in
the sentence**, not only in the scope: a reader who meets this claim without it
cannot know whether the number includes bots, and the platform's own class name
is the only honest way to say it. "Human" would be a promotion the platform
explicitly refuses to make about its own heuristic.

Every Evidence row: `SUPPORTS`, relevance 1.0, directness 1.0, extraction
confidence 1.0, observation category `UNCATEGORISED`, independence `UNKNOWN`,
evidence level 1, **reliability NULL → `NON_SCORABLE`**.

**No reliability was invented and no reliability mission was started.** §24 is
explicit, and leaving eighteen rows `NON_SCORABLE` is the design working rather
than a gap: reliability scopes get reviewed when they become relevant to an
actual inference, in batches, not one per source.

### Convergence, documented and not implemented

Recorded because §23 asks for it and forbids the inference: this per-entity
request series could **eventually** converge with problem evidence about the same
tool — a repeated concrete failure in a narrow tool, beside a request series for
that tool's article. Two independent observations of one subject would support
something neither supports alone.

**No such inference is made here, and no mechanism for it exists.** The two
sources are not independent in any sense this system has established, and
`independence_state` is `UNKNOWN` on every row.

---

## 7. BOUNDARIES

| | |
|---|---|
| INFERRED Claims | **0** |
| Opportunities | **0** |
| Embeddings | **0** |
| Product / market / WTP / pricing / MRR scores | **0** |
| ReliabilityAssessments created | **0** |
| Other Wikimedia projects, endpoints, bulk dumps | **not touched, refused by name** |
| World Bank, GDELT, TED, Stack Exchange data or semantics | **unchanged**; nothing recollected, nothing rewritten |
| A friendlier Stack Exchange query | **not run.** S0 remains part of the evidence about that source |
| Historical RawRecord `use_profile` | **not backfilled** |
| Gateway profile-blind duplicate rows | **not fixed**; the tripwire grew from seven sources to eight, as its own comment predicted |
| `SOURCE_ITEM_LINK` follow-up for World Bank and Eurostat | **not done** |

---

## 8. QUALITY

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 38 | **59** (+21) |
| NormalizedRecords | 38 | **59** (+21, all `VALID`) |
| Record kinds | 4 | **5** |
| Normalizers | 4 | **5** |
| Signal quantity families | 3 | **4** |
| Extractors | 4 | **5** |
| Signals | 8 | **26** (+18) |
| Claims / ClaimRevisions / Evidence | 8 / 8 / 8 | **26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |

Normalized coverage by source and kind: `world-bank / numeric_observation /
VALID / 6`, `gdelt / lexical_frequency_observation / PARTIAL / 6`, `ted-eu /
procurement_notice / PARTIAL / 11`, `stack-exchange / community_question / VALID
/ 15`, `wikimedia-pageviews / content_request_count / VALID / 21`.

### Did all gates pass?

**Yes.** Zero-dependency suites (555 tests across 8 packages), all pytest suites
across 7 packages, the seven validators plus `check_env_template` and
`assert_registry_grants_nothing`, contract generation `--check`, all four
generated-document checks, ruff check, ruff format, and mypy.

**A latent defect in `validate_schema.py`, exposed by this migration.**
`strip_constraint` scanned forward from a superseded constraint definition and
stopped only at a **depth-zero comma** — which exists inside a `CREATE TABLE`
body and never inside an `ALTER TABLE … ADD CONSTRAINT` folded in from a later
migration, because the captured ALTER text stops before its own semicolon. So
stripping a superseded ALTER definition ran to the end of the body and deleted
every later ALTER with it.

Invisible while the newest definition was also the last one — true from Mission
1.15.9 until a **third** migration widened the same constraint. Then the strip
removed the CURRENT definition too, and the column reported *no CHECK constraint*
for a closed enum that had one. A silent over-reach rather than an error, fixed
at the scanner: a definition now ends when its own parentheses close.

**One guard caught something my local run did not, and the gap was mine.** CI
greps `sros_acquisition` for a network-client import outside
`collection/transport.py`, and the first version of this collector imported
`urllib.parse.quote` to percent-encode an article title. `urllib.parse` is string
manipulation rather than a network client, but the guard is a coarse import
pattern **on purpose** — a narrow one would have to know which submodules are
safe, and the day it is wrong is the day a collector opens a socket. So the
encoding moved into `transport.py` as `path_segment`, beside `host_of`, which is
where composing a safe URL belonged anyway.

The lesson is about verification, not about the guard: I ran the validators, the
generated-document checks, ruff, mypy and every suite, and **CI also has inline
grep steps that are not any of those**. They are now part of what gets run before
a push.

**Eighteen existing assertions were repointed and none was weakened.** Five
inventory equalities (`IMPLEMENTED_COLLECTORS`, `IMPLEMENTED_NORMALIZERS`,
`RECORD_KINDS`, `NORMALIZER_REGISTRY`, `EXTRACTOR_REGISTRY`) grew by one entry
each and stay equalities. `SIGNAL_TYPES` and `SignalQuantityFamily` grew by one
and the family test gained a list of the names it refuses — `CONTENT_VIEWS`,
`ATTENTION`, `CONTENT_POPULARITY`, `ADOPTION` — so the distinction is asserted
rather than assumed. The interpreter version moved to 1.2.0 in three places.

**One assertion's conclusion flipped while its rule held.** Mission 1.8 asserted
that no request-identification capability existed, because building one then
would have registered an abstraction no condition named. It now asserts that
`source-client-identification` exists **and that no other identification
capability does** — the same rule, the other side of it.

**One substring scan became structural.** A test scanned `model.py` for the
literal `"requests"` to prove the module reaches no network, and the new record
kind's description contains the English word. `testing-strategy.md` §23 names
that exact shape: a substring scan fails on the prose that explains the rule, and
weakening the prose is how a structural check stops checking. The check now walks
the AST's imports, which loses nothing — a module cannot reach a network without
importing something that can.

---

## 9. The next marginal evidence gap

Recomputed, and it is not the one this mission closed.

**The portfolio now observes an interaction, and still observes no PERSON.** A
pageview is one request; nothing links two requests to one requester, and
Wikimedia deliberately publishes no such link. So the gap Mission 1.19 §0
restated remains exactly where it was: **no Evidence establishes repeated
comparable USER-PROBLEM instances for one narrowly defined problem.**

What this mission changes is which half is missing. The portfolio now has one
half of the convergence §23 describes — a repeated, comparable, per-entity series
with an established timeline and a documented population. The other half is a
source that observes the same *difficulty* recurring, and Mission 1.18 measured
why the obvious candidate does not supply it: a public Q&A tag is a subject, not
a problem.

Two shapes could supply it, and both are review questions rather than engineering
ones:

- **A narrow-tool acquisition over an already-approving source**, designed so
  that a concrete failure can actually recur — many questions about one tool
  rather than many tools in one day. Mission 1.18's own §14 names this as the
  thing that would change its answer, and it needs its own review of what the
  query selects for.
- **A source that publishes issue or defect records per product**, where the same
  fault is reported by different people. Every registered candidate for that
  today is `RESTRICTED` on retrieved terms.

`WILLINGNESS_TO_PAY` and `PRICING` are where Mission 1.16 left them, the second
still with no registered candidate at all. **No source is selected here**, because
selecting one is a review act with its own mission and its own retrieved
evidence.
