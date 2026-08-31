# Evidence Reliability Review Guide V1

**Authoritative.** Mission 1.14. How a human actually writes a reliability
assessment, and when to write none.

Contract: `evidence-reliability-contract-v1.md`. Scope and binding: ADR-026.

This is the counterpart of `source-review-guide.md`, which covers *may we
collect this*. This covers *how dependable is this measurement for this
purpose*. **The two reviews are separate, and neither's outcome may influence
the other's.**

---

## 0. Before you start

You are answering one question:

> For evidence derived from **this measurement**, bearing on **this kind of
> proposition**, how dependable is it?

You are **not** answering: is this source reputable, is it official, are we
allowed to use it, did we read it correctly, or does it bear on the claim. Those
are five different questions with five different homes, and §12 of the contract
says which.

**The default outcome is no assessment.** Writing none leaves the evidence
`NON_SCORABLE`, which is an honest state the system is built to carry. Writing
one you cannot defend puts a number into `min()` that nobody can argue with.

## 1. Identify the scope

Five parts, all required. Get them from the data, not from memory:

```sql
SELECT DISTINCT
       e.source_id,
       n.payload->'series'->>'resource_id'  AS resource_id,
       i.record_kind_id,
       c.claim_type,
       c.proposition_facts->>'proposition'  AS proposition_kind
  FROM scoring.evidence e
  JOIN research.claims c        ON c.id = e.claim_id
  JOIN nlp.signal_inputs i      ON i.signal_id = e.signal_id
  JOIN acquisition.normalized_records n ON n.id = i.normalized_record_id
 WHERE e.reliability IS NULL;
```

Each distinct row is one review. The seven Evidence rows in the system today
collapse to **three**.

If two scopes differ in any part, they are two reviews. Resist the urge to write
one assessment "covering both" — a scope broad enough to cover two measurements
is the source coefficient the contract forbids, reached by a shorter route.

## 2. Read the publisher's own material

**First-party only**, and the same rule the source registry applies: a blog
post, a tutorial, a forum answer or model recall is not a basis. Retrieve the
document, record its URL, its section and when you fetched it.

What to look for, by basis type:

| Basis type | What you are looking for |
|------------|-------------------------|
| `SOURCE_DOCUMENTATION` | What the resource contains and how the publisher says to read it |
| `DATASET_METHODOLOGY` | How it is assembled, **and how it is revised** — revision policy is what makes a snapshot claim age |
| `MEASUREMENT_METHODOLOGY` | How the quantity is measured, sampled or estimated |
| `KNOWN_LIMITATION` | What the publisher says it does *not* capture |
| `CORPUS_CONSTRUCTION_METHOD` | For text-derived counts: what was crawled, filtered, de-duplicated. **What the frequency is a frequency OVER** |
| `OFFICIAL_STATISTICAL_METHOD` | A published standard the resource states it follows |
| `INDEPENDENT_VALIDATION` | Someone other than the publisher measuring the same quantity |

If you cannot retrieve any of these, **stop**. There is no assessment to write.

## 3. Write down the failure mode first

Before choosing a number, finish this sentence:

> *This evidence would be misleading if …*

That sentence becomes `stated_limitation`, and it is required. A reliability with
no stated failure mode is a number nobody can argue with, which is the same as a
number nobody can check.

If you cannot complete the sentence, you have not understood the measurement
well enough to assess it.

## 4. Then choose the value

`[0,1]`. There is no label scale and you should not invent one.

The value should be defensible as *an answer to the failure mode you just
wrote*, not as a general impression. Two useful discipline checks:

- **Could you defend this number to the publisher?** If your reasoning is "it is
  an official statistical agency", you have described the publisher and not the
  measurement.
- **Would you give the same number for a different purpose?** If yes, your scope
  is probably too broad — reliability that does not move with purpose is a source
  coefficient.

`DOCUMENTED_METHOD` is the strongest origin available short of calibration: use
it when the *document supplies the number* — a stated sampling error, a
documented completeness bound — and you are only locating it. Most reviews will
be `HUMAN_REVIEW`.

**Do not use `CALIBRATED_EMPIRICALLY`** unless you fitted the value to labelled
outcome data and can name the dataset. The database refuses it otherwise, and
however careful your review was, it was not a calibration.

## 5. Attribute it

`reviewed_by` names a person. Not a team, not a script, not a model.

**A model may help you read documentation.** It may summarise a methodology
page, point you at a section, or draft a paraphrase you then check against the
source. It may not be the epistemic source of the judgement, and there is no
origin value that would let you record it as one. If your reasoning traces back
to something a model asserted rather than to something a document says, you have
no assessment.

Set `review_interval_days` and `next_review_at` where the measurement is one
whose methodology changes. A dataset that is revised has an assessment that
ages.

## 6. Superseding

Never update an assessment. Write version N+1 and mark version N with
`superseded_at` and a `superseded_reason`.

An aggregation that ran against version N must still be able to read version N,
and a result carrying a binding to it must stay explicable. Correcting in place
would silently change every historical score that used it.

Supersede when:

- the publisher's methodology changes;
- a limitation is discovered that the original review missed;
- the resource's contract changes (a new file format, a changed cadence);
- your own reasoning turns out to be wrong.

Do **not** supersede because a downstream score came out lower than someone
wanted.

## 7. The two reviews stay apart

| | Source policy review | Reliability assessment |
|---|---|---|
| Question | May we collect this? | How dependable is this measurement for this purpose? |
| Home | `registry.source_policy_reviews` | `epistemic.reliability_assessments` |
| Outcome | `APPROVED`, `RESTRICTED`, … | A value on `[0,1]`, or none |
| Basis | Terms, licences, operator correspondence | Methodology, limitations, corpus construction |

Reading methodology documents **does not** change a policy verdict, and a policy
verdict **does not** feed a reliability value. If a methodology document reveals
a licensing fact, that is a separate policy review with its own evidence rows.

## 8. When to write nothing

All of these are correct outcomes:

- The publisher documents no methodology you could retrieve.
- The documentation exists but does not bear on the failure mode you identified.
- You can describe the measurement but cannot defend any particular number.
- The purpose is one the measurement plainly does not serve — in which case the
  right answer is that the *claim* should not have been made, not that the
  evidence needs a low reliability.

In every case: no row. The evidence stays `NON_SCORABLE`, the aggregation
reports `UNAVAILABLE`, and nothing downstream pretends otherwise.

## 9. Worked shape — the three scopes in the system today

Written as a **checklist for a future reviewer**, not as an assessment. No
assessment exists for any of these, and this document does not propose values.

### `world-bank / indicator/SP.POP.TOTL / numeric_observation / OBSERVED / source_reported_metric_period_change`

The claim says *"World Bank Open Data reported that `SP.POP.TOTL` for
`"Germany"` increased between `"2018"` and `"2019"` by 187180."* The proposition
is about **the publication**, not about Germany's population.

So the failure mode is **not** "was the population estimate correct". It is:

> *Is the persisted canonical observation a dependable representation of what
> the source published?*

A reviewer would need to establish, from World Bank's own material:

- the **indicator revision policy** — this is the load-bearing one. If figures
  are revised after publication, a claim carrying a magnitude and no vintage
  ages, and the reviewer must decide whether that bounds the value;
- whether the API response we normalized is the authoritative surface for the
  indicator;
- what `SP.POP.TOTL` counts, well enough to confirm the metric id names one
  quantity.

**A caution the mission states directly.** It is tempting to reason "the claim
is only about what the source reported, our transcription is exact, therefore
1.0". That is exploiting the wording. Exact transcription of a snapshot is not
the whole question when the snapshot is revisable and the claim does not carry
its vintage.

### `gdelt / web-ngrams/1gram / lexical_frequency_observation / OBSERVED / source_reported_term_frequency_change`

The claim says *"The GDELT Project reported that, in its `"web-ngrams/1gram"`
stream under source language label `"ENGLISH"`, the term `"climate"` appeared 11
more times in source bucket X than in the preceding source bucket."*

Reliability here concerns **the corpus output under the reviewed resource
contract**. It is emphatically not the reliability of news truth, public
opinion, market demand, attention or user behaviour — a GDELT frequency measures
its corpus, and the claim says so.

A reviewer would need:

- the **corpus construction method** — what is crawled, what is filtered, how
  duplicates are handled. What the frequency is a frequency *over*;
- whether a bucket is ever **republished or backfilled**, which would make two
  reads of one label disagree;
- whether the count is complete for the bucket or sampled;
- the language-labelling step's own behaviour, **without** treating the label as
  a language (H-30 is open).

### `gdelt / web-ngrams/1gram / lexical_frequency_observation / OBSERVED / source_reported_term_frequency_contrast`

Same measurement, **different purpose**: two terms within one bucket rather than
one term across two. It is a separate assessment because a corpus whose *bucket
boundaries* are unstable affects the change proposition and not the contrast
one, and a reviewer may reach different values for the two.

That two scopes over one measurement can legitimately differ is the whole reason
purpose is in the scope.
