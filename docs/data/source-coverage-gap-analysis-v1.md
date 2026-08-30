# Source Coverage Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.7 §47, **before** migration
0010, so the schema change can be checked against what was measured rather than
against what was assumed.
**Date:** 2026-08-30
**Reads:** `registry.sources`, `registry.source_capabilities`, the
`registry.registry_entries` vocabularies, and Ontology V2 §3.3–§3.6 / §14.
**Related:** [`source-registry-v1.md`](source-registry-v1.md) §2, §3,
[`opportunity-ontology-v2.md`](../domain/opportunity-ontology-v2.md) §3, §14,
[ADR-017](../architecture/adr/ADR-017-source-signal-coverage.md).

---

## 0. The question

Mission 1.7 §4 asks for a taxonomy answering *"what kinds of opportunity signal
could this source potentially expose?"*, and §22 asks for a matrix that makes it
obvious when the portfolio holds "20 economic sources and 0 entertainment
sources".

Before adding a column anywhere, three questions have to be answered in order:

1. Can the existing model already express this?
2. If not, does the concept belong in a vocabulary that already exists?
3. Does it need to be persisted at all, or is a document enough?

§47 requires this document to exist first because the honest answer to (1)
turned out to be "partly, and the part it can express is the part that matters
least".

---

## 1. What the registry can express today

| Column / table | Answers | Can it carry signal coverage? |
|---|---|---|
| `sources.source_family` | which kind of platform this is | **No.** One value per source, and it is a *provenance* label. `community` says where the data comes from, not what can be learned from it |
| `source_capabilities.capability` | which DATA the source can supply (`reviews`, `ratings`, `vote-counts`) | **No — and this is the near miss.** §2 below |
| `sources.coverage_*` | geographic and language reach | No. Orthogonal |
| `sources.quality_notes` | observable limitations | No. Deliberately not analytical |
| `source_policy_reviews.*` | what the documents permit | No, and it must stay that way — §4 |

### 1.1 Nothing in the registry answers §22's question

Asked today, "how many registered sources could expose entertainment signals"
has no query. The closest available is `source_family = 'content_platform'`,
which returns YouTube — a **PROHIBITED** source. §23 forbids counting that as
coverage, so the closest available answer is also a wrong one.

---

## 2. Why `source_capabilities` is the wrong place, though it looks right

`source_capabilities` already holds a per-source list of open strings, already
has a `description` and `notes`, and adding `reviews-signal-entertainment` to it
would need no migration at all. That is the tempting option and it is wrong.

**It records a different kind of fact.** A capability is *what data comes back*:
`reviews`, `ratings`, `timestamps`, `vote-counts`. Signal coverage is *what could
be learned from it*. The two are not the same relation, and one does not
determine the other:

| Capability | Signal coverage it does NOT determine |
|---|---|
| `reviews` on an app store | PROBLEM if the reviews complain, DESIRE if they request, ENTERTAINMENT if the app is a game. Same capability, three different answers |
| `timestamps` on World Bank | nothing at all. It is a structural field |
| `page-view-counts` | CURIOSITY and TREND — from a capability that mentions neither |

Merging them would give the column two meanings, and the second would be
inferred from the first by whoever read it next. That is the mistake
`source-registry-v1.md` §0 exists to prevent, applied one table over: a single
field that lets a technical fact be read as an analytical one.

**It is also free text with no vocabulary.** `source_capabilities.capability`
has no foreign key and no controlled set, which is right for "what fields does
this API return" and wrong for a taxonomy that §22 wants to aggregate over.
Aggregating over free text produces `reviews` and `review` as two categories.

---

## 3. Where the concepts already exist — and this is most of them

**§5's behaviour list is Ontology V2 §3.4, verbatim.** All seventeen:

```text
CREATE DISCOVER CONSUME PLAY LEARN COMPARE PREDICT COLLECT SHARE
COMPETE CUSTOMIZE TRACK DISCUSS BUY SELL COLLABORATE AUTOMATE
```

There is no gap here at all. `user_behavior` is an established **registry**
(§14.3) whose canonical initial entries are exactly this list. Creating a second
behaviour vocabulary would be the "overlapping vocabularies" §5 forbids, in its
purest form.

**The registry is under-seeded, which is a different problem.** Migration 0004
seeded `user_behavior` with **one** entry (`create`) and `user_motivation` with
**three** (`creativity`, `money`, `problem`) as illustrative rows. The ontology
specifies seventeen behaviours and seventeen motivations as *initial canonical
entries*. Seeding the remainder is authorised by §14.3 and needs no ontology
change: they are already canonical, just not yet loaded.

### 3.1 §4's signal families against the existing vocabularies

| §4 asks for | Already canonical as | Verdict |
|---|---|---|
| PROBLEM | `user_motivation` PROBLEM | exists |
| ENTERTAINMENT | `user_motivation` ENTERTAINMENT | exists |
| CREATIVITY | `user_motivation` CREATIVITY | exists |
| CURIOSITY | `user_motivation` CURIOSITY | exists |
| COMPETITION | `user_motivation` COMPETITION | exists |
| SOCIAL | `user_motivation` SOCIAL | exists |
| DISCOVERY | `user_motivation` DISCOVERY | exists |
| LEARNING | `user_motivation` LEARNING | exists |
| COLLECTION | `user_motivation` COLLECTION | exists |
| PERSONALIZATION | `user_motivation` PERSONALIZATION | exists |
| STATUS | `user_motivation` STATUS | exists |
| DESIRE | demand signal **family** DESIRE (§3.6, **CLOSED enum**) | exists, unreferenceable — §4.2 |
| COMMERCIAL | nearest: `user_motivation` MONEY; demand family MARKET | **partial** |
| TREND | nearest: demand family MARKET | **partial** |
| COMMUNITY | nearest: `user_motivation` SOCIAL; `retention_mechanism` COMMUNITY | **partial** |
| DEVELOPER_ACTIVITY | nothing | **absent** |

**Eleven of sixteen already exist by name and meaning.** That is the finding
that shapes the decision, and it points away from a fresh vocabulary.

---

## 4. The subject problem, and why reuse is not free either

`user_motivation` describes **a user**, inside an Opportunity: *why does this
person want this*. Source signal coverage describes **a source**: *what could be
learned from this platform's data*.

Attaching `user_motivation` rows directly to `registry.sources` would assert
that a source has a motivation, which is a category error. It would also couple
two things that must move independently: the day someone adds a motivation for
opportunity modelling, every source's coverage profile silently gains a value it
was never reviewed for.

So neither pure option is right:

| Option | Fails on |
|---|---|
| Reuse `user_motivation` as source coverage | category error; the two vocabularies would be forced to evolve together |
| A fresh `signal_family` with 16 new names | eleven duplicate an existing vocabulary by name and meaning — the overlap §5 forbids |

### 4.1 What is actually being decided

The resolution taken, and recorded in
[ADR-017](../architecture/adr/ADR-017-source-signal-coverage.md):

**A `signal_family` registry whose every entry names the canonical vocabulary
entry it corresponds to.** One new vocabulary, sixteen entries, and each row
carries `maps_to_registry` / `maps_to_id` pointing into `user_motivation` or
nothing.

The mapping column is the whole point. It is what makes this a *projection* of
the canonical ontology rather than a competitor to it: the relationship between
`signal_family:entertainment` and `user_motivation:entertainment` is written
down and queryable, instead of being a coincidence of spelling that a future
reader has to guess at. Five entries map to nothing, and that is recorded as
`NULL` rather than forced into a near-match — `DEVELOPER_ACTIVITY` is not a
motivation and pretending otherwise would corrupt the vocabulary it was pushed
into.

### 4.2 One of the five is a limit of the mechanism, not a gap

`DESIRE` has an exact canonical counterpart: the demand signal family of the
same name. It still maps to `NULL`, because **§3.6 makes the signal family a
CLOSED enum** and `registry_entries` holds registries. There is no row to point
at, and manufacturing a `demand_signal_family` registry so the pointer would
resolve would reclassify a closed enum as extensible — a material ontology
change (§14.2), made silently, to satisfy a foreign key.

The correspondence is therefore recorded in the entry's description. This is
worth stating plainly because it is the one case where the model knows something
it cannot express structurally, and a later reader finding `maps_to = NULL` on
`desire` would otherwise conclude no counterpart exists.

**Behaviour coverage introduces no vocabulary at all.** It references
`user_behavior` directly, because there the subject problem does not arise: a
source *records* behaviours, which is a statement about the data, not about the
source's own psychology.

---

## 5. Does it need persistence?

§47 prefers catalog/config additions and asks the question explicitly.

**Yes, and the reason is §22 plus §23 together.** The matrix must be derivable
from *reviewed and eligible* capabilities only — a PROHIBITED source must not
count as coverage. That is a join between coverage and the eligibility view, and
a join needs both sides in the database. A markdown table would answer the
question on the day it was written and drift from the next review onward, which
is precisely the drift `source-registry-v1.md` §3 refuses for eligibility
itself.

Two tables, in `registry`, global like everything around them:

```text
registry.source_signal_coverage     source -> signal_family (+ basis)
registry.source_behavior_coverage   source -> user_behavior (+ basis)
```

### 5.1 What these tables must NOT become

Recorded here because the gap between "coverage metadata" and "a source quality
score" is one sentence wide, and §35 and §36 both close it from the other side:

- **No weight, no score, no confidence.** Not now and not by later addition. A
  numeric column here would be a per-source reliability coefficient under
  another name, which is D-03, which is blocked. §35 names the exact shape of
  the mistake: `Reddit = 0.7`.
- **Not in an evidence or scoring table** (§47). These sit beside the source,
  not beside the evidence.
- **Coverage is potential, never permission.** A source may cover
  `ENTERTAINMENT` and be `PROHIBITED`. The two columns are in different tables
  and no view joins them into a single verdict.
- **`basis` is mandatory.** Every coverage row records which capability or
  documented data the claim rests on, for the same reason a retention override
  records one: a row with no stated justification cannot be re-checked when the
  source changes, and is indistinguishable from someone having wanted the
  category filled in.

---

## 6. Summary of what migration 0010 must do

| Change | Because |
|---|---|
| Seed the remaining 16 `user_behavior` entries | Ontology V2 §3.4 canonical list; 1 of 17 is loaded |
| Seed the remaining 14 `user_motivation` entries | Ontology V2 §3.3 canonical list; 3 of 17 are loaded |
| Add `signal_family` registry, 16 entries, each with its canonical mapping | §4, ADR-017 |
| Add 3 `source_family` entries: `gaming`, `creator`, `knowledge` | §34; the existing 11 have no home for Steam, Twitch or OpenAlex |
| `registry.source_signal_coverage` | §22, §23 need it joinable to eligibility |
| `registry.source_behavior_coverage` | §5, referencing `user_behavior` |
| No column on `registry.sources` | coverage is many-valued; a column would force one value or an array with no referential integrity |
| **No numeric column anywhere** | §35, §36, D-03 |
