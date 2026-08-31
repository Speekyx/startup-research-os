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

## Step 2.5 — Declare the assessed use profile, before anything else

**A review with no subject may not exist** (Mission 1.15.5, ADR-027). Before
assessing a single activity, state which use profile you are reviewing for:

| Profile | Assess against this when… |
|---|---|
| `commercial-multi-tenant-research-v1` | the question is what a public, customer-facing, multi-tenant Startup Research OS may do. The **widest** profile: nothing that fails here can be rescued by a narrower one |
| `local-private-research-v1` | the question is what the current local, single-operator deployment may do, with no redistribution and no customer-facing access |

Three rules follow, and none is negotiable:

- **The profile is not a way to rescue a blocked source.** It exists to persist
  the question a review answered. If you find yourself reaching for a narrower
  profile because a source failed under a wider one, ask whether the narrower
  use is what the system actually does — and if it is not, the source is blocked.
- **Local is not non-commercial.** `commercial_purpose` is true on both
  registered profiles. The research this system produces is used to launch
  commercial products, so a commercial-use right still has to be positively
  granted by the source's own evidence.
- **An approval never transfers.** A verdict under one profile says nothing
  about another, and the gate refuses a profile with no review rather than
  consulting one that has one.

Record the profile on the review. A source may hold different current verdicts
under different profiles, and that is not a contradiction — they are answers to
two questions.

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

## Step 9 — If the review is APPROVED_WITH_CONDITIONS

Added in Mission 1.4. Writing a condition down does not clear it, and you cannot
clear it yourself.

```bash
uv run sros-source conditions <source-id>
```

Each condition shows its verification kind and what a verifier found **now**.
`UNKNOWN` means nothing checked it — usually because the condition names a
capability that does not exist yet, which is work for an engineer rather than
for the reviewer.

```bash
uv run sros-source verify <source-id>          # dry run, writes nothing
uv run sros-source verify <source-id> --apply  # records the results
```

A `CONFIG_REFERENCE` condition is answered from the process environment.
`sros-source` folds the git-ignored `infrastructure/compose/.env` into its own
process first, so putting a real value there is enough; an explicitly exported
variable wins over the file. The command prints which file it read, never what
was in it.

Three rules govern what you may and may not do here.

**You cannot mark a condition satisfied.** There is no command for it and the
database refuses the `UPDATE`. A condition is cleared by a verifier that records
what it checked; if you believe a condition holds and no verifier says so, the
gap is a missing capability, not a missing permission.

**Write a mechanical condition or write `HUMAN_CONFIRMATION`.** If what must be
true is *"a lawyer confirmed X"* or *"the owner granted permission"*, say
`HUMAN_CONFIRMATION` and name the decision that has to be recorded. Do not
reword a legal obligation until it sounds checkable — that produces a verifier
that checks something else.

**Name what will be checked.** A `CAPABILITY` condition names a capability, a
`CONFIG_REFERENCE` names a configuration key. `verification_detail` is not a
description, and a condition whose detail names nothing real resolves `UNKNOWN`
forever.

Then say what the capability must *do*, in
[`source-compliance-v1.json`](source-compliance-v1.json): exact notices verbatim,
allowlists, exclusions, minimisation categories. If the terms prescribe wording
and you do not have it, make the element **supplied** rather than composing a
sentence — a validator checks that every exact notice appears in the evidence
that prescribed it.

---

## Step 10 — Enabling a collector

```bash
uv run sros-source enable <source-id>
```

This refuses unless the gate passes, **and** refuses when no collector is
implemented for the source. The database refuses too, even if the CLI is
bypassed. That is intentional: enabling collection is the one
irreversible-feeling step, and it should require the review to be finished
rather than the reviewer to remember.

Eligible, enabled and implemented are three different facts. Today two sources
are eligible, none is enabled, and none is implemented.

---

## The one anti-goal

**Do not optimise for the number of approved sources.** The registry is correct
when its verdicts match its evidence, not when it is full of green rows. A
catalog where every platform came back approved is a failed review, not a
successful one.
