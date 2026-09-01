# Stack Exchange Questions V1 — Review and Authorisation

**Authoritative.** Mission 1.18. The first approving review for a
community-content source, and the first where the positive rights come from a
**content licence** rather than from a platform's terms.

**Verdict: `APPROVED_WITH_CONDITIONS` under `local-private-research-v1`.**
ELIGIBLE and resource-ready. Collected and normalized:
`stack-exchange-questions@1.0.0` and `stack-exchange-question@1.0.0` both exist
and have run, over the `community_question` record kind — **15 RawRecords, 15
NormalizedRecords, all `VALID`** (§12, §13).

**Zero Signals, zero Claims, zero Evidence, and that is the finding** (§14). The
15 real questions were read; they share no repeated problem a deterministic rule
could see. **Outcome S0** is recorded with the tag structure that produced it, so
a later reader can check the decision rather than take it.

---

## 1. The three open questions, and what closed them

| | Question | Outcome |
|---|---|---|
| 1 | Retrieve the Public Network Terms and the Responsible AI policy and assess commercial reuse, storage and model processing | **Closed.** ToS operator-supplied; RAI policy retrieved directly and found normatively empty for a third party |
| 2 | The precise attribution obligations CC BY-SA imposes on derived analytics, and whether share-alike reaches aggregated outputs | **Avoided, not answered** — see §4 |
| 3 | Whether Stack Data Licensing is the required route | **Closed narrowly** — see §5 |

## 2. Evidence provenance, stated exactly

| Document | How it was obtained |
|---|---|
| Public Network Terms of Service | **Operator-supplied first-party evidence.** This environment received HTTP 403 |
| API Terms of Use | **Operator-supplied first-party evidence.** This environment received HTTP 403 |
| Consolidated Responsible AI policy | **Retrieved directly** by this environment, HTTP 200, 2026-09-01 |

The two 403s came from one ordinary HTTPS request each, with a truthful
User-Agent naming the project. **Neither was retried, and no header was varied to
look like a browser.** Varying it would have been the circumvention the mission
brief and the registry contract both forbid, and the resulting approval would
have been indistinguishable from a correct one until it mattered.

The documents are official Stack Overflow pages; their retrieval into this
repository was operator-mediated, and the evidence records say so in their own
text rather than leaving a reader to assume otherwise.

## 3. The two layers, kept apart

**This is what the review turns on.** API access permission and content reuse
permission are different questions with different sources:

- **The API Terms decide ACCESS.** They permit an Application to programmatically
  query and connect to the Network, and they are **silent** on storage,
  analytics and commercial use. Silence is recorded as silence.
- **The content licence decides REUSE.** Subscriber Content — which is what
  questions are — is **CC BY-SA 4.0**, which permits reproduction and adaptation
  for any purpose including commercial, subject to attribution and ShareAlike.

**The API carve-out removes an obstacle; it grants nothing.** The Terms' storage
restriction expressly excludes *"other than Subscriber Content or content made
available via the Stack Overflow API"*, so it does not reach what this collector
would acquire. Read as a standalone licence it would be a grant by absence, which
is the reading rule 8 of the registry contract forbids.

**Commercial use is positively granted, by the licence.** That mattered because
local is not non-commercial: the research evaluates commercial products, so the
right had to be granted rather than assumed away by the deployment being a laptop.

## 4. ShareAlike is avoided by the profile, not answered by the review

CC BY-SA 4.0's ShareAlike obligation attaches to Adapted Material that is
**Shared**. `local-private-research-v1` shares nothing: no redistribution, no
resale, no customer-facing access.

So the classification question — *is a derived analytic artefact Adapted Material
at all* — **does not have to be decided**, and it was not.

It is carried as an open question rather than closed, because a review that
quietly relied on *"we do not publish"* without writing it down would be one
deployment change away from being wrong. **The moment any output is published,
this review must be redone.**

## 5. Stack Data Licensing, narrowly

Neither governing document states that a separate Stack Data Licensing agreement
is required for ordinary official-API use.

**That is the whole finding.** It does not generalise to *"Stack Data Licensing is
never required"* — a different volume, purpose or route could be governed
differently, and the existence of a paid product is neither a prohibition on the
free API nor a permission for anything.

## 6. Model processing

**Inference is permitted; training is neither assessed nor authorised.**

Reading and classifying licensed text is use within CC BY-SA's own grant to
reproduce and to produce Adapted Material. Training is a contested and materially
different act, the profile forbids it, and the review deliberately did not reach
for a basis it does not need.

**The AI Addendum is not the answer either way.** It is scoped to Stack's own AI
Features, AI Inputs and AI Outputs. It is not a third-party grant, and it is not
on its face a prohibition on an external party analysing ordinary Subscriber
Content.

**The Responsible AI policy is normatively empty for us**, and this is worth
recording because the document exists and a later reader will find it. Every
operative sentence has Stack as its subject: *"Stack is responsible for
implementing this policy"*, *"We ensure AI systems are designed and trained to be
fair and unbiased"*, *"The Stack Legal Team ensures that our business understands
and complies with applicable law"*. It is corporate governance about how Stack
builds AI. It grants a third party nothing and forbids a third party nothing, and
it was used as neither.

## 7. The resource

```text
questions/stackoverflow          family: stack-exchange-questions
route:      stack-exchange-api   (OFFICIAL_API, https://api.stackexchange.com/2.3/)
licence:    CC-BY-SA-4.0         rights basis: NAMED_LICENCE
origin:     PLATFORM_LICENSED    (§8)
```

**One site, one content type.** Stack Overflow questions. The opportunity domain
is software and developer tooling, and that is where those problems are asked.
The other ~180 network sites are **not** authorised and are not assumed to carry
equal opportunity value — `cooking` and `scifi` are the same platform and a
different subject, and a review that said "Stack Exchange" would have approved
them without looking.

**Refused by name**, at two gates: the Data Dump (route authorisation **and**
excluded dataset family), and users, Teams, chat, jobs and companies (excluded
families). The Data Dump route was **registered in this mission so that it could
be refused** — it genuinely exists, and deleting it to keep the registry tidy
would falsify a fact about the source to obtain a permission (ADR-028).

## 8. `PLATFORM_LICENSED`, and why it was the closest call

The content is written by users. **Stack Exchange does not own it**, and this
field must not be read as saying it does.

But the enum is not asking who owns the material. `THIRD_PARTY` means *"the
platform's approval grants nothing over it, and separate permission from the owner
is required"* — and that permission already exists and already reaches us: each
contributor grants CC BY-SA 4.0 to everyone by contributing under the Terms, and
there is nobody left to ask.

`PLATFORM_LICENSED`'s own test is *"the platform produces or licenses this
resource, and **the reviewed terms cover it**"*. The Public Network Terms are the
reviewed terms and they cover Subscriber Content explicitly, by naming its
licence. The documentary link holds at both ends — the same reasoning Mission
1.15.7 recorded for TED under a different instrument.

Classified `THIRD_PARTY`, the resource is refused by `third_party_denied` and the
source is approving but unreachable: the wrong answer for a right-sounding
reason, which is why the field is argued rather than set.

## 9. Personal data — the first source where it is the point

A Stack Exchange question is authored by an identifiable person, and the API
returns an `owner` object by default: display name, account id, profile link,
reputation, avatar. **None of it is needed to observe that somebody asked how to
accomplish something.**

| Allowed | Excluded |
|---|---|
| `question_id`, `site`, `title`, `body`, `tags`, `creation_label`, `answer_count`, `is_answered`, `accepted_answer_id`, `score`, `view_count`, `question_url`, `content_licence` | `owner` and every field under it, `last_editor`, `comments`, `natural_person_name`, `personal_identifier` |

**Excluded at acquisition**, through the API's own `filter` mechanism — not
dropped afterwards. A request that fetched the owner object and discarded it has
still fetched it, and no method removes a field from a record already collected.

`comments` is excluded for that reason and a second one: a comment is a different
utterance by a different person, and acquiring it would widen the personal-data
surface without widening what the evidence establishes.

## 10. Attribution — two obligations from two documents

They are not the same one said twice:

- **API Terms**: an Application must *"visually indicate that the Stack Exchange
  Network is the source"* — an obligation about the **product surface**, owed
  because of how the data was reached.
- **CC BY-SA 4.0**: attribution and a licence identifier — an obligation about
  the **content**, owed because of what the data is.

A surface satisfying one would not satisfy the other. Configured as
`SOURCE_CREDIT` (*Stack Exchange Network*), `LICENCE_IDENTIFIER` (*CC BY-SA 4.0*)
and `MODIFICATION_STATEMENT` (supplied per artefact, when modified).

### A gap the first CC BY-SA source exposed

CC BY-SA 4.0 also requires *"a URI or hyperlink to the Licensed Material to the
extent reasonably practicable"*, and **`AttributionElement` has no member for a
per-item link.** `DATASET_DOI` is the nearest and is wrong — it names a DOI for a
dataset, not a link to one contributed item.

The gap is **not specific to this source**: World Bank and Eurostat are CC BY 4.0
and carry the same requirement, configured with the same three elements. Adding a
member to a closed enum is a contract change with an ADR behind it, and doing it
as a side effect of a source mission is the change-control violation
`docs/CLAUDE.md` describes. Recorded as an open question.

**Nothing is lost meanwhile**: the per-question canonical URL is in the allowed
field list, so the link a future element would render is already held. The gap is
in what the attribution *contract* can express, not in what the data supports.

## 11. Conditions

| Key | Verification | What it enforces |
|---|---|---|
| `stack-exchange-attribution` | CAPABILITY `source-attribution-display` | Both attribution obligations on every derived surface |
| `stack-exchange-official-api-only` | CAPABILITY `source-route-binding` | Official API only; Data Dump refused by name |
| `stack-exchange-personal-data-minimisation` | CAPABILITY `source-field-minimisation` | Owner and account objects excluded at acquisition |

All three verify **satisfied**. Stack Exchange is ELIGIBLE.

## 12. The collector, and the acquisition

**`stack-exchange-questions@1.0.0` exists and has run.** One real bounded
acquisition: `stackoverflow`, tagged `python`, 2024-03-04 to 2024-03-05,
`page_size` 10, `max_pages` 2, `max_records` 15. Two HTTP requests, 16 items
returned, **15 RawRecords**, quota 294/300, no `backoff`. Re-run identically:
`new: 0, unchanged: 15`.

`has_more` came back **true** and collection stopped anyway, at `max_pages` —
which is what makes the no-exhaustion rule a property rather than a promise.

Field minimisation is performed by the API's own `/filters/create` filter
`!SyjNl4V)kvv2kw3Qt6`, verified by reading it back: `question.owner` is absent
from `included_fields`. No owner field was received. New records carry
`use_profile` in provenance (Mission 1.17's gap, closed prospectively).

**Collected in this mission and normalized in the same one**, which does not
weaken the rule that collection and normalization are separate facts: the
collector shipped, ran and was tested before a record kind existed to hold what it
returned.

## 13. The record kind and the normalizer

**`community_question`, and the name is the decision.** Migration 0024 inserts one
registry row and changes no schema, because `normalized_records` already carries
`payload JSONB` and a `record_kind_id` with a foreign key into the registry. It is
the **fourth** kind and the first named for a SHAPE rather than for the first
source to reach it: a question asked on a public Q&A site is a shape other sources
share, and `stack_exchange_question` would have made the vocabulary a list of
vendors. The SITE is a field; the source is provenance.

The three existing kinds could not hold it without getting worse. A question
carries no measured value, so `numeric_observation` would have to make
`observation.value_state` meaningless for it; it counts no term, so
`lexical_frequency_observation` would have to lose its term and its language; and
it is nobody's procurement, so `procurement_notice` would have to make monetary
amounts optional and give a question a buyer.

**`stack-exchange-question@1.0.0`**, run over all 15 records. Idempotent:
re-running produced `new: 0`, and a forced re-normalization after a later code fix
produced `unchanged: 15, conflicted: 0` — so the output is proven byte-identical
rather than asserted to be.

**Every record is `VALID`, and that is new.** Every GDELT record is `PARTIAL`
because H-29 and H-30 are open; every TED record is `PARTIAL` because H-37 is.
Nothing is open here. **This is the first adapter whose period is `ESTABLISHED` on
the source's own evidence**: `creation_date` is a Unix epoch second, an
unambiguous instant, unlike TED's offset-without-a-time or GDELT's unzoned bucket.
So `observed_at` is a real moment for the first time in this repository.

What one normalized record asserts, in full: *Stack Exchange published this public
question on Stack Overflow with these source fields.* Four things it does not
assert, each written into the payload rather than left to a reader:

- **the tags are the SITE's vocabulary** and are never mapped to a taxonomy of
  ours, carried under `scheme: stack-exchange-tags:stackoverflow`;
- **an accepted answer means the ASKER accepted one**, carried beside
  `accepted_answer_semantics`, which says in the record itself that it is *"not a
  statement that the problem is objectively resolved"*;
- **score and view count are source counters**, carried under
  `engagement.semantics`: *"not importance, not demand, not market size"*;
- **`author: null`** — not omitted for tidiness, never acquired.

A raw record carrying `owner`, `last_editor` or `comments` is **refused at
normalization**, not quietly stripped. The collector refuses such a response and
this refuses such a record, because they are different moments and a record
already in the database can only be caught here. A record with no canonical URL is
refused too: CC BY-SA needs the link, so a record that cannot be attributed is
never normalized into one that cannot be displayed.

## 14. Zero Signals, and why that is the answer

**The 15 real questions were read before anything was designed.** The Signal
semantics were never going to be decidable against imagined data, and the decision
below rests on what the sample actually contains.

| Fact | Value |
|---|---|
| Questions | 15 |
| Distinct tags | 35 |
| Tags appearing on 2 or more questions | **3** |
| Questions sharing a complete tag set | **0** |
| Repeated quoted identifier in a title | **0** |
| Title word on 3 or more questions | `python` — the query term, and nothing else |

The three repeated tags are the whole cohort space, and each one fails:

- **`python` — all 15.** It is the term the query asked for, so it is a property
  of the retrieval and not a finding about the world. A cohort built on it says
  *these are the questions we asked for.*
- **`google-cloud-platform` — 3.** Eventarc firing duplicate Cloud Run processes
  (`78098392`), a `setup.py` `install_requires` type error (`78098469`), and
  extracting text from a Google Doc (`78098567`). Three unrelated problems that
  share a platform.
- **`deep-learning` — 2.** The same `setup.py` packaging error (`78098469`) and
  whether padded rows affect backpropagation (`78098740`). Two unrelated problems
  that share a field.

**`78098469` is in both cohorts**, which is the clearest evidence available that
these groupings are about subject rather than about problem: one question cannot
be two repeated problems.

**A tag identifies a SUBJECT. It does not identify a PROBLEM.** Any deterministic
rule over this sample — shared tag, shared tag pair, shared title token — groups
questions that share a technology and nothing else. Reading further would take
semantic inference over question text, which is an INFERRED step this mission does
not authorise and which no Signal may rest on.

**So: 0 Signals, 0 Claims, 0 Evidence.** Not blocked, not deferred, not
insufficient data — a derivation was considered against real data and correctly
produced nothing. **The cohort was not weakened to get output**, and a second query
was not run to look for a friendlier sample: a support threshold lowered until
something appears is a threshold that measures the analyst.

**What would change the answer** is a different acquisition shape, not a different
rule: many questions about ONE narrow tool, where a repeated concrete failure could
recur. That is a mission with its own bounded acquisition and its own review of
what the query selects for, not a parameter on this one.

## 15. Known limitations

1. ShareAlike classification is avoided by the profile, not resolved (§4).
2. Model training is not assessed and not authorised (§6).
3. The Stack Data Licensing finding is narrow (§5).
4. The Public Network Terms and API Terms were operator-supplied; re-read them
   directly at the next review.
5. `AttributionElement` cannot express a per-item link (§10).
6. Only `stackoverflow` is authorised; no other network site is.
7. No job-size ceiling has been reviewed, which is an unasked question rather
   than a licence.
8. The empirical finding in §14 is about **this sample**: 15 questions, one day,
   one tag. It is evidence that a tag is not a problem; it is not a proof that no
   Stack Overflow cohort could ever carry a Signal.
9. A missing question body leaves the record `VALID` with `question.body: null`.
   `NormalizationQualityReason` has no member that would truthfully name that
   absence, and adding one to a generated closed enum is a contract change with an
   ADR behind it that no record in the real sample calls for.
