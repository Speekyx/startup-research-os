# Mission 1.28 — Opportunity Engine Foundation V1

**Outcome: `OPPORTUNITY_ENGINE_READY_BUT_CURRENT_EVIDENCE_INSUFFICIENT`.**

The architecture is built, tested and runs end to end over the real 26 canonical
Evidence rows. It produced **nine packets, zero opportunity hypotheses and zero
model calls**, and it is blocked twice over for two unrelated reasons — which is
the useful part of the result.

| | |
|---|---|
| Evidence rows inspected | **26** |
| ELIGIBLE_CONTEXT / ELIGIBLE_SCORING | **26 / 0** |
| INELIGIBLE / REQUIRES_REVIEW | 0 / 0 |
| packets built / formable | **9 / 0** |
| opportunity hypotheses generated | **0** |
| model calls | **0** (cost 0.00 USD) |
| canonical counters | **unchanged** |
| tests | **72** new, 2 repaired, 0 failures |

---

## §0 — The Mission 1.27 correction

The report contradicted itself: §12 said `shared_problem_if_any` was *"left empty
on 1 of 24 development rows and 0 of 16 holdout rows"* while §14 said it was
empty **39 of 40** times.

**The persisted runs settle it, and the 39-of-40 figure is the correct one.** For
the frozen candidate V2-A, `docs/data/problem-family-v2-v2-dev-1.json` and
`problem-family-v2-v2-holdout-1.json` hold a non-empty `shared_problem_if_any` on
exactly **one** row — `78089075::78097003`, development — and empty on the other
39. The §12 sentence named the right numbers with the verb reversed: 1 and 0 are
the counts of rows where the field was **filled**.

Corrected in the report only, with the amendment recorded at its head. No
prediction, prompt version, cost or count was touched.
**`EXPLORATORY_V2_NOT_PROMISING` and `PARK_PROBLEM_FAMILY_CLASSIFIER` stand.**

A detail worth keeping: across all three variants and both splits the field was
filled **2 times in 88**. The 39-of-40 claim is correctly scoped to the frozen
candidate, which is the classifier the recommendation is about.

---

## §1 — What already existed

**`research.opportunities` has existed since Mission 0.1** and was not a
placeholder in the sense of being fake — it was a real, RLS-protected,
workspace-scoped table with identity, title, summary and a canonical
`MarketScope`, plus an `OpportunityRepository` that creates and reads rows and
records session observations. `research.claims.opportunity_id` already points at
it and has been nullable since ADR-024.

**What was missing was everything epistemic**: no status, no procedure version,
no evidence links, no dimensions, no limitations, no revision history, no
eligibility concept and no sufficiency concept. `services/scoring` is a README
and nothing else, and `scoring.scores` is not a table at all.

So the answer to *what can be reused without migration* is: the table, its
tenancy, its foreign keys and its repository. The answer to *what requires
forward migration* is: the four hypothesis columns and the two new tables. No
destructive change was made and none was needed.

---

## §2–§12 — What was built

`packages/opportunity-engine/python/sros_opportunity`, a new workspace member
depending on `sros-contracts` and nothing else. Not on `sros_acquisition`,
because an engine able to read the source registry could decide its own
authorization — the argument Mission 1.24 made for the classifier, unchanged. Not
on `sros_llm_gateway`, because a package that cannot import a provider cannot
call one by accident. Not on `sros_semantic_equivalence`, asserted over the AST.

Seven versioned procedures, each named and each recorded on every packet it
builds. The full contract is `docs/data/opportunity-engine-foundation-v1.md`;
three decisions are worth arguing here.

### `TREND_OR_CHANGE` cannot satisfy a diversity requirement

In this repository a Signal **is** a derivation over two or more observations, so
**every** Evidence row describes a change by construction. A dimension the whole
corpus carries separates nothing. If it counted, one measurement repeated six
times would look like two kinds of evidence, and the two-dimension rule would be
satisfied by every packet that exists.

**This qualifier was chosen with the 26 rows already inspected** — §3 of the brief
instructed inspection first — so it is declared rather than buried, reported under
both readings, and it is the difference between three packets being formable and
none being formable.

**It does not change the mission's outcome**, and that is the important part.
Under the literal reading the three Wikimedia packets would be
`HYPOTHESIS_FORMABLE`, and all three would still be
`UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS` at the §9 gate, so no hypothesis could be
generated either way. The qualifier decides a label, not the result.

### Three signal types map to nothing, on purpose

`numeric_period_change` is UNMAPPED because the signal type is the wrong
granularity: what a period change bears on depends on **which** indicator moved,
and a series of business registrations and a series of total population are the
same signal type and different evidence. The only indicator present is
`SP.POP.TOTL`, a demographic stock naming no actor, no need, no buyer and no
activity.

Both GDELT lexical types are UNMAPPED because a change in how often a term
appears in a news corpus measures what **media organisations published** — producer
behaviour, not audience behaviour — so it is not even `AUDIENCE_OR_USAGE`. No
dimension in the taxonomy asks about media publication volume, and adding one so
this source had somewhere to land would be adding a dimension to fit a source.

### Docker, Podman and Kubernetes stay three packets

Grouping is by exact source-native subject identifier and by nothing else. Merging
those three would assert they are the same thing, which is a
`SAME_PROBLEM_FAMILY`-shaped judgement — the relation Mission 1.27 parked — reached
by hand instead of by a classifier. **Doing it deterministically would not make it
deterministic; it would make it unargued.** The module has no string distance, no
token overlap, no stem, no synonym table and no threshold, asserted by a test.

---

## §16 — The real run

`python infrastructure/scripts/run_opportunity_preparation.py`, written to
`docs/data/opportunity-preparation-v1.json`.

**All 26 rows are `ELIGIBLE_CONTEXT`. None is `ELIGIBLE_SCORING`.** Every row
fails on one thing and it is the same thing: no reviewed reliability resolves for
its measurement-by-purpose scope, so every row is `NON_SCORABLE` with
`MISSING_RELIABILITY`. That is the design working, not a gap.

| source family | rows | dimensions |
|---|---|---|
| knowledge (`wikimedia-pageviews`) | 18 | `AUDIENCE_OR_USAGE` (+`TREND_OR_CHANGE`) |
| economic_data (`world-bank`) | 4 | none |
| news (`gdelt`) | 3 | none |
| public_procurement (`ted-eu`) | 1 | `MARKET_ACTIVITY`, `BUYER_OR_BUDGET_EXISTENCE`, `ECONOMIC_VALUE` |

| packet | rows | counting dimensions | status |
|---|---|---|---|
| `wikimedia:Docker_(software)` | 6 | 1 | INSUFFICIENT |
| `wikimedia:Kubernetes` | 6 | 1 | INSUFFICIENT |
| `wikimedia:Podman` | 6 | 1 | INSUFFICIENT |
| `world-bank:SP.POP.TOTL|DE` | 2 | 0 | INSUFFICIENT |
| `world-bank:SP.POP.TOTL|FR` | 2 | 0 | INSUFFICIENT |
| `gdelt:climate` / `climate|weather` / `weather` | 1 each | 0 | INSUFFICIENT |
| `ted-eu:CPV-division:90` | **1** | **3** | INSUFFICIENT |

### The failure is symmetric, and that is the finding

**The one packet with commercial dimensions has one row. The packets with many
rows have one dimension.** SROS's evidence is deep where it is narrow and broad
where it is shallow, and neither shape supports an opportunity hypothesis. Nothing
was forced: 26 rows exist and 0 opportunities were created.

### The second blocker is independent of the first

**Every one of the nine packets is `UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS`**, and not
because of the evidence. Under `local-private-research-v1`,
`external_model_transmission` is `NOT_ASSESSED` for `wikimedia-pageviews`,
`world-bank`, `gdelt` and `ted-eu` — every source that contributes Evidence. It is
`PERMITTED_WITH_CONDITIONS` for `stack-exchange` alone, which contributes none,
because Mission 1.23 assessed egress for the source Mission 1.24 was about.

**The one source cleared to leave this deployment is the one source with nothing
to send.** So even a coherent packet could not have reached a model, and §17's
1.00 USD ceiling was never approached: the run cost nothing because nothing was
sendable. This is an open question an operator can close, not a prohibition, and
it is now the cheapest unblocking act available.

### Independence

Every row carries `independence_state = UNKNOWN`, so no packet establishes that
its evidence is independent. Six Wikimedia rows about one article are six
observations of one stream, not six findings. The phrase *multiple independent
sources* is structurally unreachable from any packet here, and a test asserts it.

---

## §19 — Tests

**72 new tests** in `packages/opportunity-engine/python`, covering every property
§19 lists: dimension mapping, missing dimensions staying missing, NON_SCORABLE
staying NON_SCORABLE, source policy preserved, problem-family inference not
required, unsupported market claims refused, `UNKNOWN` independence never
upgraded, packet provenance, deterministic reproducibility, model authorization
before serialization, hypotheses unable to claim validation, no ranking score, no
opportunity quota, Evidence-to-Claim links preserved, and the parked
problem-family path never reachable.

Two are worth naming. The serialization test hands the gate a mapping that
**raises if read**, so a pass proves authorization came first rather than proving
the output happened to be empty. And the no-ranking test walks the AST of every
module for a field or function whose name contains `_score`, `rank`, `weight`,
`priority`, `leaderboard` or `percentile`.

Repository totals: **571** zero-dependency tests, all pytest suites across 9
packages, 0 failures. All nine validators, four generated-document `--check`
steps, ruff, ruff format, mypy, both CI inline greps and `migrate --plan` pass.

**Two existing tests failed and were repaired rather than weakened.** Migration
0029 adds two tenant tables, and `test_integration.py` and `test_rls.py` each hold
an explicit list of every tenant table. They failed because the schema changed and
the lists had not — which is the guard working. Both lists now name the new
tables, so RLS coverage over them is asserted rather than assumed
(`testing-strategy.md` §65).

---

## §20 — Counters

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 / 0 / 0 | **0 / 0 / 0** |
| Registered sources | 29 | **29** |

`research.opportunity_hypothesis_revisions` and
`research.opportunity_hypothesis_evidence` exist and hold **0 rows**.
`scoring.scores` is still not a table.

---

## §22 — The fifteen questions

1. **Is the Opportunity abstraction implemented?** Yes — package, seven versioned
   procedures, migration 0029, 72 tests.
2. **What evidence dimensions exist?** Fourteen, in
   `opportunity-evidence-dimensions@1.0.0`.
3. **How many Evidence rows map to each?** `AUDIENCE_OR_USAGE` 18,
   `TREND_OR_CHANGE` 18, `MARKET_ACTIVITY` 1, `BUYER_OR_BUDGET_EXISTENCE` 1,
   `ECONOMIC_VALUE` 1. The other nine: **zero**. Seven rows map to nothing.
4. **Context-only vs scoring-eligible?** **26 context, 0 scoring.**
5. **Can coherent packets be formed?** Nine group coherently by subject; **none
   meets the sufficiency rule**. `OPPORTUNITY_PACKET_FORMATION_INSUFFICIENT` for
   all 26 rows.
6. **Were any hypotheses generated?** **No.**
7. **What supports each hypothesis?** Not applicable — there are none.
8. **What dimensions remain unsupported?** Nine of fourteen are unsupported by
   any row, including every one that would make an opportunity commercially
   interesting: `PROBLEM_OR_NEED`, `RECURRENCE_OR_FREQUENCY`,
   `WILLINGNESS_TO_PAY`, `SOLUTION_GAP`, `SOLUTION_DISSATISFACTION`,
   `COMPETITIVE_SUPPLY`, `DISTRIBUTION_SIGNAL`,
   `REGULATORY_OR_STRUCTURAL_DRIVER`, `FEASIBILITY_SIGNAL`.
9. **Were any model calls made?** **No.** The package imports no Gateway and no
   provider.
10. **What did they cost?** **0.00 USD.**
11. **Did any unsupported commercial claim enter persistence?** No — nothing
    entered persistence at all, and the guard refuses the vocabulary at
    construction.
12. **Are any Opportunities validated?** No. `VALIDATED_OPPORTUNITY` is not a
    value in the enum or in the database CHECK.
13. **Did ranking or scoring occur?** **No.** No score, rank or weight exists in
    the package or the schema.
14. **Is problem-family inference still parked?** **Yes.**
    `PARK_PROBLEM_FAMILY_CLASSIFIER` stands, production stays `NOT_AUTHORISED`,
    and the engine has no dependency on it.
15. **Recommended next mission?** Below.

---

## Limitations

- The sufficiency rule is pre-registered but **untested against a passing case in
  real data**: no packet reached it, so only synthetic packets have exercised the
  FORMABLE branch.
- The dimension map covers the five implemented signal types. A sixth arrives
  unmapped and lands in `REQUIRES_REVIEW`, which is correct and means the map
  needs extending whenever a signal type does.
- `run_opportunity_preparation.py --check` needs the real database, so it cannot
  join the CI generated-document checks: the integration job builds an empty
  schema. It is a local gate, and the committed report is asserted by tests that
  read the file.
- The use profile is the runtime's declaration about itself. The Evidence rows do
  not record one, because most were collected before ADR-027 existed.

---

## Recommendation

**Outcome B, and the next mission is the cheap one.**

The architecture is not the blocker and neither, mostly, is the evidence. Two
things stand between this engine and its first hypothesis, and they cost very
different amounts:

1. **Assess `external_model_transmission` for the four sources that actually have
   Evidence** under `local-private-research-v1`. This is a governance mission of
   the shape Mission 1.23 already ran once, on sources whose licences are CC0
   (Wikimedia), a Commission Decision (TED) and open terms. It is reading and
   deciding, not collecting. Until it happens, **no packet from the current
   corpus can reach a model however good the evidence gets.**
2. **Acquire evidence that answers a second dimension for a subject that already
   has one.** The corpus fails on breadth per subject, not on volume: the
   Wikimedia packets need one non-usage dimension, and the TED packet needs one
   more row.

The reliability gap is real but is **not** what blocks a hypothesis — formability
never required scoring-eligibility. It blocks the *score*, which is a later
mission and correctly still blocked by D-03.

**Do not start ranking.** Nine packets, zero formable, and nine of fourteen
dimensions unanswered is exactly the state in which a leaderboard would be a
number with nothing behind it.
