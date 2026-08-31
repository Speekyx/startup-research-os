# Evidence Reliability Contract V1

**Authoritative.** Mission 1.14.

| Companion | Answers |
|-----------|---------|
| `evidence-reliability-gap-analysis-v1.md` | What could not be represented, written before the migration |
| `evidence-reliability-review-guide-v1.md` | How a reviewer actually writes one |
| `ADR-026-reliability-assessment-scope-and-binding.md` | Scope, binding and tenancy, with the alternatives rejected |
| `../domain/evidence-aggregation-framework-v1.md` §3–§6 | What consumes a reliability value |

**State when this was written:** 7 Claims, 7 Evidence rows, `reliability` `NULL`
on every one, all `NON_SCORABLE` with `MISSING_RELIABILITY`. Zero assessments
exist. **That is still true after this mission**, and §11 says why.

---

## 1. What reliability means

> **How dependable is this kind of measurement, for this kind of proposition?**

Not how permitted the source is. Not how well-known it is. Not how carefully we
read it. Not how much it bears on the claim. One question, about a measurement
and a purpose.

`evidence-aggregation-framework-v1.md` §3 states the semantics this contract
implements:

> Reliability is a property of **this evidence record, against this claim, given
> how it was collected**.

That is right, and taken literally it demands a human judgement per Evidence
row. This contract supplies the missing middle term: a **reusable scope** broad
enough to review and narrow enough that it never becomes a statement about a
source.

## 2. The scope — measurement × purpose

An assessment applies to exactly this, and matches only when **all five parts**
agree:

```text
source_id           who published it              ┐
resource_id         which published stream        ├─ the MEASUREMENT
record_kind_id      what shape it normalized to   ┘

claim_type          the epistemic type            ┐
proposition_kind    WHAT KIND of proposition      ┴─ the PURPOSE
```

`proposition_kind` is the `proposition_facts` discriminator Mission 1.13.1
already writes on every claim:

```text
source_reported_metric_period_change
source_reported_term_frequency_change
source_reported_term_frequency_contrast
```

It names what a claim asserts *in kind*, which is exactly what "purpose" means
in "reliability is purpose-relative". It was introduced so two proposition
shapes could not collide in a hash; it turns out to be the unit of purpose.

### 2.1 Why this is not a source coefficient

`world-bank` alone matches nothing. `world-bank` + `indicator/SP.POP.TOTL` +
`numeric_observation` matches nothing. The framework's own example resolves
correctly with no special case:

| Evidence | Purpose | Result |
|----------|---------|--------|
| World Bank population record | `source_reported_metric_period_change` | May have an assessment |
| The same record | a demand proposition | Different `proposition_kind`, matches nothing, `NON_SCORABLE` |

The purpose-relativity is **structural**. There is no path by which a value
reviewed for one purpose reaches another.

### 2.2 What the scope deliberately excludes

| Excluded | Why |
|----------|-----|
| `signal_type_id` | The derivation between measurement and proposition is the interpreter's business, and whether it read the Signal correctly is `extraction_confidence` |
| `workspace_id` | ADR-026 Decision 3 |
| The claim, revision or Evidence id | That is the per-row judgement the scope exists to avoid requiring |
| Source policy state | §3 below |

### 2.3 How much review this actually costs

The seven real Evidence rows fall under **three** scopes:

```text
world-bank / indicator/SP.POP.TOTL / numeric_observation
           / OBSERVED / source_reported_metric_period_change

gdelt / web-ngrams/1gram / lexical_frequency_observation
      / OBSERVED / source_reported_term_frequency_change

gdelt / web-ngrams/1gram / lexical_frequency_observation
      / OBSERVED / source_reported_term_frequency_contrast
```

Three reviews, not seven — and it stays three however many World Bank
observations arrive, because the scope is over the measurement and not over the
row. That ratio is the design's whole justification.

## 3. Compliance is not reliability

`APPROVED` and `APPROVED_WITH_CONDITIONS` are **legal and governance states
only**, and no formula converts one into a number. In both directions:

- an `APPROVED` source does not produce more reliable evidence;
- a `RESTRICTED` source does not produce less reliable evidence.

A permitted source may publish poor data. A source we may not touch might
publish excellent data and remain unusable.

**Enforced structurally, not by prose.** `epistemic.reliability_assessments`
lives in its own schema, has no column for a policy state, and
`packages/evidence-reliability` contains no approval-state literal — asserted
over the AST, excluding docstrings, so the paragraph explaining the rule cannot
fail it.

## 4. The value

`[0,1]`, the scale `evidence-aggregation-framework-v1.md` §4 already uses.
Presented as a percentage where presented at all.

- **Out of range is rejected, never clamped.** A value outside the interval
  means the reviewer is on a different scale, and clamping hides that behind a
  plausible number.
- **No threshold labels.** There is no `0.9 = authoritative`, no
  `0.7 = good`. A label would be a second scale nobody calibrated, and a
  reviewer would then target the label instead of the measurement.
- **No categorical mapping.** Not from source type, not from evidence level, not
  from anything.

## 5. Origin — who may establish one

`ReliabilityAssessmentOrigin`, closed:

| Origin | What it means |
|--------|---------------|
| `HUMAN_REVIEW` | A named reviewer's judgement, resting on retrieved first-party documents. The reviewer is accountable and identified |
| `DOCUMENTED_METHOD` | The value follows from a published methodology statement that specifies it — a documented sampling error, a stated completeness bound. The document supplies the number; the reviewer locates it |
| `CALIBRATED_EMPIRICALLY` | Fitted against labelled outcome data. Requires a `calibration_dataset_ref` |

**There is deliberately no `MODEL_GUESSED`, and closure is the point.** A model
may help a reviewer read documentation. It may not be the epistemic source of
the judgement, and a vocabulary with nowhere to record a guess is what makes
that enforceable rather than merely stated.

`reviewed_by` is required and non-blank. An unattributed judgement is one nobody
can be asked about.

**Human review is not calibration** (§22 of the mission, §14 of the aggregation
framework). A `HUMAN_REVIEW` or `DOCUMENTED_METHOD` assessment may not name a
calibration dataset — the database refuses it — and the aggregation profile
stays `UNCALIBRATED` regardless of how many assessments exist. Reviewing
reliability and fitting parameters to outcomes are different acts.

## 6. Basis — what a value must rest on

Every assessment carries at least one **document-backed** basis row.
`ReliabilityBasisType`:

`SOURCE_DOCUMENTATION` · `DATASET_METHODOLOGY` · `MEASUREMENT_METHODOLOGY` ·
`KNOWN_LIMITATION` · `INDEPENDENT_VALIDATION` · `OFFICIAL_STATISTICAL_METHOD` ·
`CORPUS_CONSTRUCTION_METHOD` · `REVIEWER_DOCUMENTED_JUDGEMENT`

A document-backed row names a retrieved document and when it was retrieved. A
methodology statement that cannot be re-fetched is a memory of one.

**`REVIEWER_DOCUMENTED_JUDGEMENT` may never stand alone.** Reasoning *about* the
documents is welcome; reasoning *instead of* them is an opinion with a citation
field — which is exactly what `"World Bank is trustworthy"` amounts to. Enforced
by a `DEFERRABLE INITIALLY DEFERRED` trigger, so an assessment and its basis
rows land in one transaction and neither has to exist first.

Shaped after `registry.source_policy_evidence` deliberately: the system already
has a pattern for "this judgement rests on these retrieved documents". Full
documents are **not** stored — a reference, a section pointer, a short
summarized finding, an excerpt capped at 1000 characters, and a fingerprint.
Copying third-party text wholesale would be the disregard for source terms the
registry exists to prevent.

`rationale` and `stated_limitation` are both required. **A reliability with no
stated limitation is a number nobody can argue with**, and the limitation is
what the value is discounted *for*.

## 7. Versioning

`(assessment_key, version)` is the row. `assessment_key` is a sha256 over the
five scope parts, so two reviewers assessing one scope collide on one key and a
reviewer revisiting a scope is recognised as revisiting it.

**Superseded, never updated.** A correction writes version N+1 and marks version
N `superseded_at` with a `superseded_reason`; version N stays readable, because
an aggregation that used it must still be able to read it.

At most **one current** assessment per scope, enforced by a partial unique index
where `superseded_at IS NULL`.

Supersession is all-or-nothing, spelled with `num_nonnulls` — the obvious
spelling returns NULL on a half-filled row, and a CHECK accepts NULL (migration
0017's lesson).

## 8. Applicability — fail closed

| Current matches | Outcome | Reliability |
|-----------------|---------|-------------|
| 0, none ever | `NO_APPLICABLE_ASSESSMENT` | `NULL` |
| 0, all superseded | `SUPERSEDED_ONLY` | `NULL` |
| 1 | `RESOLVED` | The value, with its binding |
| >1 | `AMBIGUOUS_ASSESSMENTS` | `NULL` — **refused** |

**Never the closest** — "closest" needs a distance nobody defined. **Never the
maximum** — optimism with a mechanism. **Never the mean** — averaging two
competing reviewed judgements produces a third that nobody made and nobody can
defend.

`SUPERSEDED_ONLY` is deliberately distinct from `NO_APPLICABLE_ASSESSMENT`:
*somebody reviewed this and withdrew it* is a different fact from *nobody has
looked*, and they call for different actions.

An Evidence row whose claim carries no `proposition` discriminator cannot state
its purpose, so no assessment can apply — `NO_APPLICABLE_ASSESSMENT`, rather
than a scope guessed for it.

## 9. NULL means unknown, and unknown produces no number

There is **no way to express "unknown" as a value.** An assessment that asserts
nothing is not an assessment; unknown is the *absence of a row*.

Forbidden, in every disguise:

```text
0.5   because unknown          a measurement claiming the middle
0.8   because reputable        reputation is not a property of a measurement
1.0   because official         official is a publisher, not a method
0.9   because government       the same, wearing a flag
0.0   because we do not know   a measured weakness, which is a different claim
```

An unknown reliability leaves the record `NON_SCORABLE` with
`MISSING_RELIABILITY`, retained in the evidence set, named in
`missing_requirements` and counted towards coverage. `q_i = min(components)`
never sees it.

**The system must remain capable of producing no score.** That capability is not
a limitation to be engineered away; it is what makes a score mean something when
one appears.

## 10. Binding — resolved late, recorded explicitly

Reliability for generated Evidence is **resolved at aggregation time**, and the
aggregation records **which assessment id and version it used for each row**
(ADR-026 Decision 2).

Precedence, so two answers cannot disagree:

```text
row.reliability IS NOT NULL  ->  DIRECTLY_SUPPLIED, no assessment consulted
row.reliability IS NULL      ->  resolution is attempted
```

A value on the row is a statement about *that record* and is more specific than
a class-level assessment. The two can never conflict because the second only
runs when the first is absent.

**Historical reproducibility.** Re-running against the recorded bindings
reproduces the number exactly. Re-running against current assessments produces a
*different* result with a different `evidence_snapshot_digest` — identifiable
**as** a recomputation rather than silently replacing the original. This does
not resolve D-08; it refuses to make it harder.

## 11. Aggregation provenance

A result must be able to answer, per contributing row:

- which assessment was applied (id and `assessment_key`)
- at which version
- with which origin, reviewed by whom, at what time
- and for every row without one, **which outcome** and therefore why it is
  non-scorable

`ReliabilityBinding.to_json()` carries exactly those fields.

**Do not produce a score whose coefficients cannot be reconstructed.** A bare
`0.9` in a column is not reconstructible, which is why late resolution with a
recorded binding beats copying the value forward.

## 12. What reliability is not

Five neighbouring quantities, each `1.0` on all seven real Evidence rows, and
none of them implies anything about reliability:

| Quantity | Asks | Why it does not imply reliability |
|----------|------|-----------------------------------|
| **Relevance** | Does this Evidence concern this Claim? | A perfectly reliable population statistic can have relevance 0 to a SaaS demand claim |
| **Directness** | Does it address the Claim itself or an adjacent premise? | A direct measurement can be a bad measurement |
| **Extraction confidence** | Did the interpreter read the Signal correctly? | Reading a flawed measurement perfectly is still a flawed measurement |
| **Claim interpretation confidence** | Does the sentence restate the Signal correctly? | Same, one layer up |
| **EvidenceScore** | What does all the evidence together say? | An aggregation *output*. Reliability is one of five inputs to `min()` |

**No propagation formula exists, and there is nowhere to put one.**
`resolve_reliability` takes exactly three arguments — `scope`, `candidates`,
`supplied` — and none of the five above is among them. A test asserts the
signature.

`EvidenceScore` is never stored on the Evidence row.

## 13. Tenancy

Assessments are **global**. An assessment is a statement about a published
dataset's measurement contract, evidenced by the publisher's own documentation —
not a statement about a tenant. Making it tenant-scoped would mean every
workspace re-reviewing the same methodology, producing several answers to one
question with nothing to say which is right.

No `workspace_id`, no RLS policy, `SELECT` for the runtime role, administered
through a review path rather than over HTTP. **No tenant data exists in this
schema, so no tenant leakage path exists** — a stronger property than a
correctly written policy.

A workspace-scoped assessment is imaginable and **is not built**. ADR-026
Decision 3 records what adding one would take.

## 14. Relationship to D-03

Reliability governance closes **one** of D-03's blockers and leaves the others
standing. D-03 is not closed by this mission.

| Blocker | State after Mission 1.14 |
|---------|--------------------------|
| No definition of what reliability means or who may set it | **Resolved.** This contract |
| No reviewed reliability value for any scope in use | **OPEN.** Zero assessments exist |
| No `CALIBRATED` profile — parameters fitted to no outcome data | **OPEN**, and untouched. Human review is not calibration |
| No authorised half-life for temporally sensitive claims | **OPEN.** `MISSING_TEMPORAL_PARAMETER`. Not reached today: all seven claims are `EVERGREEN` |
| Level thresholds are structural minimums, not fitted values | **OPEN** |

`services/scoring` remains unavailable for production research.

## 15. Where this is enforced

| Rule | Enforced in |
|------|-------------|
| Reliability on `[0,1]`, rejected not clamped | migration 0019, `ReliabilityAssessment` |
| No `MODEL_GUESSED` origin | the closed contract enum + a CHECK |
| Human review may not claim a calibration dataset | `reliability_assessments_calibration_ref_check` |
| A value rests on a retrieved document | `epistemic.require_documented_basis`, a deferred trigger |
| Reviewer reasoning may not stand alone | the same trigger |
| A value states what bounds it | `reliability_assessments_rationale_check` |
| At most one current assessment per scope | `idx_reliability_assessments_current` |
| Zero / one / many are all defined | `resolve_reliability` |
| Policy state cannot become reliability | a separate schema, no column, and an AST test |
| No source id in the aggregation package | `validate_evidence_aggregation.py`, unchanged |
| No source id in the resolver package | an AST test over string literals |
| Assessments are global | `validate_schema.py` global-table list |
