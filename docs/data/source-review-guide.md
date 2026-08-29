# Source review guide

**Status:** Operational procedure. Governed by
[`source-registry-v1.md`](source-registry-v1.md).
**Audience:** whoever is adding or re-reviewing a source.

This is how a review is actually conducted. It exists because a governance
process nobody can execute is a document, not a process.

---

## Before you start

Two things to hold on to, because everything below follows from them:

1. **You are recording what documents say, not deciding what is legal.** Your
   output is a set of enum values, the documents you read, and what remained
   unclear. It is not a legal conclusion, and nothing you write may be presented
   as one.
2. **Not reaching an answer is a valid outcome and the correct one when you have
   not reached an answer.** `REQUIRES_REVIEW` with a precise list of documents
   still to be read is a good result. An approval you are not sure about is not.

---

## Step 1 — Name the use case

Write down the one use the assessment covers, and put it in
`assessed_use_case`. Everything else in the review is scoped to it.

The catalog states it once, at the top, for all sources. If you are assessing
something else, that is a different review.

An assessment does not transfer. "Permitted for academic research" is not
permission for this system, and a permission granted for something narrower does
not widen.

---

## Step 2 — Record how the source can be reached

One `access_profile` per distinct route. Record:

- the access method (`OFFICIAL_API`, `PUBLIC_WEB`, …) — **technical fact only**
- what it requires: authentication, API key, OAuth, an account, a developer app,
  manual approval
- `secret_references`: configuration **key names** such as `REDDIT_CLIENT_ID`.
  Never a value. The model will refuse anything that looks like one
- rate limits **only if documented or observed**, with `rate_limit_origin` saying
  which. If you do not know, leave `rate_limit_known` false. An invented number
  is worse than none, because a collector will trust it
- `acquisition_cost`, `UNKNOWN` if you did not confirm it

Do not record a route that requires getting around a login wall, a CAPTCHA, an
API restriction, a robots directive or an anti-automation measure. Those are
limits, not obstacles. An official API being inconvenient is not a reason to
describe a scraper.

---

## Step 3 — Read the source's own documents

Acceptable evidence, and nothing else:

| Type | What it is |
|------|------------|
| `OFFICIAL_TERMS` | the platform's terms of service or use |
| `OFFICIAL_API_DOCS` | its published API documentation |
| `OFFICIAL_LICENCE` | the licence attached to the data |
| `OFFICIAL_PRIVACY` | its privacy policy |
| `OFFICIAL_ACCESS_CONTROL` | robots.txt, published access rules |
| `OPERATOR_CORRESPONDENCE` | a written answer from the operator |
| `LEGAL_REVIEW` | a recorded legal review |

**Not acceptable, ever:** blog posts, tutorials, forum threads, Stack Overflow
answers, "everyone does this", or anything an LLM recalls without a retrieved
document. The evidence type enum has no value for them, so the registry cannot
store one as the basis of an approval.

For each document you read, record: title, URL, the section you relied on, a
short paraphrase in your own words of what it says, and when you retrieved it.

### If you cannot reach a document

This is common: terms move, sites return 403 to automated fetches, links rot.

**Do not guess, and do not substitute a second-hand description of it.** Record
the source as `REQUIRES_REVIEW`, and list the exact documents still to be
checked in `open_questions` — the specific URL or document name, not "check the
terms".

---

## Step 4 — Assess each activity separately

Eleven verdicts, one per activity. Their conditions differ, and a single verdict
for the whole platform hides the case that matters most: automated API access
permitted, commercial use not.

Choosing the value:

| The documents… | Value |
|----------------|-------|
| permit it, plainly | `PERMITTED` |
| permit it subject to something specific | `PERMITTED_WITH_CONDITIONS` + a `conditions` entry |
| forbid it | `NOT_PERMITTED` |
| say nothing about it | `NOT_ADDRESSED` |
| say something you cannot settle | `UNCLEAR` |
| were not read on this point | `NOT_ASSESSED` |

The last three all block. They are kept apart because the next step differs:
`NOT_ADDRESSED` may need operator correspondence, `UNCLEAR` may need a legal
review, `NOT_ASSESSED` just needs someone to read.

Never write "scraping is legal" or "commercial use is allowed" unless that is
directly supported by terms you recorded as evidence. Never write a confidence
percentage.

---

## Step 5 — Classify personal-data handling

`personal_data_risk` plus the flags: user-generated content, user identifiers,
location, sensitive data possible, pseudonymisation expected, discard
identifiers after normalisation.

This is a **handling classification, not a legal ruling**. Leave
`jurisdiction_review_required` true; GDPR applicability is a human decision
(`data-retention-policy-v1.md` §7).

---

## Step 6 — Retention

Leave it alone unless the source imposes something stricter than the project
baseline (30 days raw, 365 days normalized).

If it does — for example an API whose terms cap storage at 30 days — record an
override with its `basis`. An override can only shorten; asking for longer is
refused, because the stricter rule always wins.

---

## Step 7 — Set the state

| State | When |
|-------|------|
| `APPROVED` | every activity you need is permitted, on authoritative evidence you recorded |
| `APPROVED_WITH_CONDITIONS` | the same, subject to conditions you wrote down |
| `RESTRICTED` | some needed activities are permitted and others are not |
| `PROHIBITED` | the documents forbid the assessed use |
| `REQUIRES_REVIEW` | you did not reach a conclusion. **The default** |
| `SUSPENDED` | it was usable and something changed |

Set `review_interval_days` from how often this platform actually revises its
terms. The approval expires then, and expiry blocks.

---

## Step 8 — Check your work

```bash
uv run sros-source validate
```

Then, against the database:

```bash
uv run sros-source load
```

```bash
uv run sros-source eligibility <source-id>
```

`eligibility` prints every blocking reason, not the first. If the source is
still blocked, the reasons say precisely what is missing.

Regenerate the human-readable catalog:

```bash
uv run sros-source render
```

---

## Step 9 — Enabling a collector

```bash
uv run sros-source enable <source-id>
```

This will refuse unless the gate passes, and the database will refuse too even
if the CLI is bypassed. That is intentional: enabling collection is the one
irreversible-feeling step, and it should require the review to be finished
rather than the reviewer to remember.

---

## The one anti-goal

**Do not optimise for the number of approved sources.** The registry is correct
when its verdicts match its evidence, not when it is full of green rows. A
catalog where every platform came back approved is a failed review, not a
successful one.
