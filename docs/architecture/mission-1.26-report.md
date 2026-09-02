# Mission 1.26 — Human Problem-Family Reference Set V1

**Outcome: `REFERENCE_SET_INSUFFICIENT`.** The development split holds **2**
`SAME_FAMILY` labels against a preregistered threshold of 4. The gate was
declared before the labels existed and was not moved to meet them.

**And a second, independent result: the human reference requirement remains
`NOT_ESTABLISHED`.** The 40 labels are `AI_ASSISTED_PROVISIONAL`, produced by
GPT-5.6 Sol. The operator chose to proceed with them rather than spend another
mission hand-labelling — a real decision, recorded — and that decision does not
change what the labels are.

**Zero external model calls.** No classifier, no prompt, no evaluation, no
Signal, no Claim, no Evidence, no Opportunity.

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |
| Registered sources | 29 | **29** |
| **Model calls** | 0 | **0** |

---

## Provenance, stated before the numbers

| | |
|---|---|
| `reference_origin` | **`AI_ASSISTED_PROVISIONAL`** |
| `reference_reviewer` | **GPT-5.6 Sol** |
| `human_ground_truth_established` | **false** |
| operator decision | proceed with the provisional reference, recorded at document level |

These 40 labels are **never** to be described as `HUMAN_OPERATOR`, human ground
truth, expert labels, or independently human-reviewed labels. A loader asked for
`HUMAN_OPERATOR` refuses them, and a test asserts that refusal for both splits —
so the guarantee is structural rather than a promise in prose.

`operator_accepted` was **not** added to the label schema. The decision is about
a whole file, so it lives as a document-level `operator_decision` note; a
per-label flag would need a migration for nothing and would eventually be read as
per-label approval.

**Mission 1.25's human holdout is a different thing and stays one.** Its 10 pairs
are genuinely `HUMAN_OPERATOR`, they sit in their own file, and they are merged
into nothing here. A test asserts no overlap.

---

## The persisted distributions

Computed from the two label files, not restated from the request.

| | total | SAME_FAMILY | DIFFERENT_FAMILY | UNCERTAIN | non-UNCERTAIN |
|---|---|---|---|---|---|
| DEVELOPMENT | 24 | **2** | 18 | 4 | 20 |
| HOLDOUT | 16 | **4** | 11 | 1 | 15 |
| **TOTAL** | **40** | **6** | **29** | **5** | **35** |

The request's expected totals — 6 / 29 / 5 — were checked against the import and
agree.

---

## A. Structural composition result

| gate | required | DEVELOPMENT | HOLDOUT |
|---|---|---|---|
| non-UNCERTAIN | ≥ 16 dev, ≥ 12 holdout | 20 ✅ | 15 ✅ |
| `SAME_FAMILY` | ≥ 4 | **2 ❌** | 4 ✅ |
| `DIFFERENT_FAMILY` | ≥ 4 | 18 ✅ | 11 ✅ |
| | | **FAIL** | **PASS** |

**Holdout composition: PASS. Development composition: FAIL, on positives.**
Therefore the preregistered gate is **`REFERENCE_SET_INSUFFICIENT`**.

Nothing was moved to change this. No pair changed split, no label was revised, no
threshold was lowered, and the sampling was not re-run with different quotas. The
whole value of a preregistered gate is that it is allowed to fail.

## B. Epistemic result

**`HUMAN_REFERENCE_NOT_ESTABLISHED`.** Independent of the composition arithmetic:
every label in this set is AI-assisted, so even a passing composition would not
have produced validated human reference evidence.

The two results are reported separately because they fail for unrelated reasons,
and a single verdict would let one hide the other.

---

## What this failure does not mean

It does **not** mean the relation is invalid, that a V2 classifier cannot work,
that Stack Exchange cannot contribute recurring-problem evidence, that there are
only six problem families in the corpus, or that `SAME_FAMILY` is rare.

**The sample is enriched and is not prevalence-representative.** Bands were drawn
at deliberately unequal rates — the low-similarity band holds 275 of 711
available pairs and contributed 8; the wrapper band holds 2 and contributed both.
The proportion of any label here estimates nothing about the corpus, and
`ENRICHMENT_WARNING` rides on the dataset so a later reader cannot miss it.

What it means is narrower: **under the frozen sampling and these provisional
labels, the development split does not hold enough positives for the
preregistered composition requirement.**

---

## The stronger historical fact, preserved

Mission 1.25's genuinely human-scored V1 holdout:

- 10 pairs,
- **2 `HUMAN_OPERATOR` `SAME_FAMILY` references**,
- **0 true SAME predictions** from classifier V1,
- **`MODEL_EVALUATION_FAILED`**.

That remains the strongest evidence about V1 and is untouched by this mission. It
is **not** merged into the 40-pair split to help a threshold, and it may later
serve as separate historical evaluation evidence.

---

## What Mission 1.26 did deliver

The infrastructure, which was the point:

- **blind reference-batch creation** — 40 pairs, no label, no prediction, no
  suggested answer in the artifact;
- **deterministic stratified sampling** over five feature bands, reproducible
  from a fixed seed, with quotas declared before any pair was drawn;
- **a split frozen before labels**, assigned within each band so neither
  partition is short of a question shape;
- **structural holdout isolation** — the splits' labels live in separate files,
  so `load_development_labels` cannot reach a holdout label because it never
  opens that file;
- **provenance that works**, mandatory on load with no default, and demonstrably
  able to refuse a caller who asks for human labels and would otherwise have been
  handed these.

**The provisional batch is useful for exploratory DEVELOPMENT work.** It is not
sufficient as validated human holdout evidence, and **production problem-family
inference remains NOT_AUTHORISED.**

---

## Backlog

> **Acquire additional genuinely human problem-family reference labels before any
> claim that classifier V2 is production-validated.**
>
> This does not block exploratory classifier development. It blocks the word
> *validated*, and it blocks production inference.

---

## Quality

**114 tests** in `packages/semantic-equivalence`, **571** across the
zero-dependency suites, all pytest suites across 8 packages, 0 failures.

Nine validators, seven generated-doc `--check` steps including the new reference
batch, `ruff check`, `ruff format --check`, `mypy`, both CI inline greps,
`migrate --plan`, and both dependency boundaries verified separately — the second
checked explicitly since Mission 1.24 shipped a `pytest` import into a suite that
runs under stdlib `unittest`.

Regression tests added for: exact batch size, uniqueness, no Mission 1.25
overlap, deterministic rerun, the frozen 24/16 split, the absence of any
model or Gateway import in the sampler, no model field name reachable in its
code, mandatory provenance, `HUMAN_OPERATOR` semantics, `AI_ASSISTED_PROVISIONAL`
preservation, holdout isolation, and the refusal of a caller requiring human
labels.

**Canonical research counters are unchanged and no inference row was created.**
The only new persisted artifacts are the reference dataset and its two label
files, which are evaluation infrastructure rather than research records.

---

## Recommendation for a future Mission 1.27

**Exploratory Problem-Family Classifier V2, on DEVELOPMENT-only provisional
labels.**

The 20 development pairs that are not UNCERTAIN — 2 positive, 18 negative — are
enough to *inspect* where V1's rubric and a reader diverge, and to draft a V2
prompt or rubric revision against. They are not enough to claim anything.

Restrictions that must hold, and each has already cost this project a mission to
learn:

- **HOLDOUT must not be used for prompt tuning**, or for anything else, until a
  final evaluation. It is 16 pairs and it is spent the first time it is looked at.
- **Provisional labels do not establish semantic truth.** A V2 that agrees with
  them has agreed with an assistant. Mission 1.25 measured exactly that and read
  it as accuracy until the operator's review moved five labels.
- **No production inference**, no Signal, no INFERRED Claim, no Evidence.
- **No cross-source convergence** from this relation, and **no Opportunity
  generation** from it.
- **Production authorization requires genuinely human validation** — the backlog
  item above, not a larger provisional set.

Two further things worth carrying into that mission. First, the development split
holds **2** positives, so any V2 developed against it is fitted to two examples;
that is a reason to treat V2 as a *hypothesis about the rubric* rather than a
model improvement. Second, the most informative artifact available is not a
label count but the **disagreement pattern**: in Mission 1.25 every divergence
ran one way, and human review halved it. Where a V2 and the provisional
references disagree is where the next human labelling effort should be spent.
