# Problem-Family Human Reference V1 — why a dataset mission came before a V2

**Authoritative for the DATASET.** Mission 1.26.
`problem-family-human-reference-v1`.

> **No model was called and no model output was read.** This mission built a
> reference set and nothing else: no classifier, no prompt, no evaluation, no
> Signal, no Claim, no Evidence. `DATASET_PREPARATION_COMPLETE` is not
> `MODEL_EVALUATION_PASSED`, and there was no model evaluation to pass.

---

## 1. Why Mission 1.25 failed

Its classifier was scored against a holdout of 10 pairs containing 2 positives,
under a criterion frozen before any prediction existed. It found **zero** of
them. Across all 20 pairs it said `SAME_PROBLEM_FAMILY` once, on the rubric's own
quoted worked example — in-sample by construction.

The criterion required a demonstrated true positive precisely so a classifier
answering DIFFERENT to everything could not pass, and that clause is what caught
it. `MODEL_EVALUATION_FAILED` stands and is not reinterpreted here.

## 2. Why the AI-assisted provisional labels were insufficient

Mission 1.25's reference set was supplied `AI_ASSISTED_PROVISIONAL`. When the
operator later reviewed the same 10 holdout pairs, **five of the ten labels
changed** — and on three of those the human moved **toward the classifier**. The
provisional reference had called two pairs a family the operator does not, and
one pair decidable that the operator finds undecidable.

So the earlier reading that the classifier was *far too conservative* was half an
artifact of the reference. Missed positives fell from 4 to 2.

**The general lesson, and it outlives this mission: a conclusion drawn about a
classifier from a provisional reference is partly a conclusion about the
reference.** An AI-assisted label set is cheap, blind and usable for scoring; it
is not ground truth, and where it is generous the classifier looks worse than it
is.

## 3. Why a human-labelled set comes before V2

Ten human-scored pairs with two positives are enough to **reject** a trivial
classifier — they did — and not enough to **build** one. Developing against two
positives is fitting to two examples; evaluating against two is measuring
nothing with an interval.

Building the reference first also removes a temptation that would otherwise
arrive with V2: if the dataset were assembled after a classifier existed, the
obvious pairs to show a reviewer are the ones the classifier got wrong. That
dataset can never measure anything again.

## 4. Why this sample is enriched, and what that forbids

40 pairs drawn from 711 available, in five deterministic bands, at deliberately
unequal rates:

| band | what the pair shares | available | drawn |
|---|---|---|---|
| A high specificity | a site tag on ~6 or fewer of 89 observations | 53 | 10 |
| B medium specificity | a tag of middling frequency | 136 | 8 |
| C low specificity | a common tag; eligible and weak | 275 | 8 |
| D diagnostic wrapper | a shared error fragment | 2 | 2 |
| E different tags | no shared tag; overlapping title words only | 245 | 12 |

The largest band contributes the fewest pairs per member and the smallest
contributes all of itself. That is deliberate — a reviewer's attention is the
scarce input, and it should be spent where the judgement is informative.

**So the proportion of any label in this set is not an estimate of anything.**
`ENRICHMENT_WARNING` rides on the dataset object and its JSON so a later report
cannot omit it: this set may be used to develop and evaluate a classifier, and
may never be used to state how often problem families occur in Stack Exchange.

## 5. Why development and holdout are separated before labels

Both partitions were fixed by `sha256(seed | pair_id)` before a single label
existed, **within each band**, so neither is short of a question shape. A split
decided later — however honestly — is a split that could have been decided to
help, and nobody reading the result afterwards can tell the difference.

**The isolation is structural rather than conventional.** The two splits' labels
live in **separate files**, and `load_development_labels` cannot reach a holdout
label because it does not open that file. A single labelled file with a `split`
column would place both a metre apart and rely on every future caller filtering
correctly, which is a rule, and rules get forgotten by whoever is in a hurry.

## 6. Why no model prediction was allowed during sampling

Because a dataset selected by a classifier's errors can only ever measure that
classifier. Every future evaluation on this set would be scored on a sample an
earlier model chose.

Enforced rather than promised: the sampler imports no gateway, no classifier and
no run artifact, and a test parses its **code** — docstrings excluded, because
the module says *not a prediction, not a confidence* precisely because it reads
neither — to assert that no prediction field name appears in anything it could
read.

## 7. Why UNCERTAIN is preserved

Because it is an answer about the published text, not a refusal to work. If a
question does not establish what its author was trying to do, then no family can
be assigned to it, and coercing that into SAME or DIFFERENT would put a guess
into the reference set that everything downstream then treats as truth. Mission
1.25's operator used it three times out of ten, and the classifier's one
abstention matched one of them.

## 8. Why HUMAN_OPERATOR is not expert ground truth

`ReferenceOrigin.HUMAN_OPERATOR` establishes human ground truth for the split it
covers, and is deliberately filed as neither expert nor non-expert. **The system
does not establish that fact and it is not ours to assert on someone's behalf.**

The wording used throughout is *human operator reference* or *human-labelled
reference*, never *expert review*, *domain expert*, or *independent expert
reviewer*. What makes this origin sufficient for this relation is that the family
question was designed to be answerable without the domain expertise the exact
relation needed.

**Mission 1.25's labels are never converted.** Its development split remains
`AI_ASSISTED_PROVISIONAL`, its full 20-pair set remains MIXED provenance, and
`human_ground_truth_established` is true only when *every* label in a set came
from a human.

## 9. Why building a dataset is not semantic inference

A complete, well-provenanced, leak-controlled reference set says nothing about
whether any classifier can find a problem family. It makes the next answer
*worth having*; it is not the answer.

**SROS already holds 26 canonical Evidence rows** from other source families. The
missing capability is specific and stays specific: **validated recurring-problem
semantic Evidence from Stack Exchange, under this relation, this rubric and this
candidate scope.** That is not the same statement as *SROS has no Evidence*, and
the broader wording must not be used.

---

## 10. What exists now, and what does not

| | |
|---|---|
| pairs | **40**, none shared with Mission 1.25 |
| split | **24 development / 16 holdout**, frozen before labels |
| labels | **40, `AI_ASSISTED_PROVISIONAL`** — see §12. The BATCH artifact still carries no label and no prediction; the labels live in two separate per-split files |
| model calls | **0** |
| Signals / Claims / Evidence / Opportunities created | **0** |

Mission 1.25's dataset stays separately queryable as
`problem-family-evaluation-v1`, with its own rubric version, sampling, label
origins and the predictions its labels were scored against. The two are never
merged: merging would lose mission origin and the association between a label and
what it scored.

**The two human-labelled positives from Mission 1.25 remain useful historical
evidence about V1** and count toward neither the 40 new pairs nor the 16-pair
holdout composition gate.

## 11. The composition gates, declared before the labels arrive

The dataset is *sufficiently informative for V2 work* only if, after labelling:

| | holdout | development |
|---|---|---|
| non-UNCERTAIN labels | ≥ 12 | ≥ 16 |
| `SAME_FAMILY` | ≥ 4 | ≥ 4 |
| `DIFFERENT_FAMILY` | ≥ 4 | ≥ 4 |

These are **dataset-composition gates, not classifier success criteria**. If
either split falls short the outcome is `REFERENCE_SET_INSUFFICIENT`, and the
response is a pre-registered supplementary batch — never moving a pair between
partitions, never relabelling, and never looking at a model prediction to decide.

If both hold, the outcome is `REFERENCE_SET_READY_FOR_V2_DEVELOPMENT`, which
still authorises no production inference.


---

## 12. The labels arrived, and the gate failed

**Outcome: `REFERENCE_SET_INSUFFICIENT`.** See `mission-1.26-report.md`.

**The 40 labels are `AI_ASSISTED_PROVISIONAL`, reviewer GPT-5.6 Sol.** They are
not the human reference this document was written to describe, and the wording
above about *what a human-labelled set would give us* stands as the reason the
mission was run rather than as a description of what it produced. The operator
chose to proceed with the provisional labels rather than spend another mission
hand-labelling; that decision is recorded and changes nothing about what they
are.

| | total | SAME_FAMILY | DIFFERENT_FAMILY | UNCERTAIN | non-UNCERTAIN |
|---|---|---|---|---|---|
| DEVELOPMENT | 24 | **2** | 18 | 4 | 20 |
| HOLDOUT | 16 | **4** | 11 | 1 | 15 |
| TOTAL | 40 | 6 | 29 | 5 | 35 |

Against §11's gates: **holdout PASSES**, **development FAILS on positives** (2
against a threshold of 4). Nothing was moved to change that — the value of a
preregistered gate is that it is allowed to fail.

Separately and independently, the **human reference requirement remains
NOT_ESTABLISHED**, because every label here is AI-assisted. The two results are
reported apart because they fail for unrelated reasons and one verdict would let
either hide the other.

**Mission 1.25's genuinely human holdout is not merged in** to help the
threshold. It stays `HUMAN_OPERATOR`, in its own file, as separate historical
evidence about V1.

**Backlog: acquire additional genuinely human problem-family reference labels
before any claim that a classifier V2 is production-validated.** This blocks the
word *validated* and blocks production inference; it does not block exploratory
development.
