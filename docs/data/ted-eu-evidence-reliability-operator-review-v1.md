# TED-EU Evidence Reliability — Operator Review V1

**Authoritative.** Mission 1.15.13. The human half of the review Mission 1.15.12
deliberately left open, the tool that records it, and what resolving it did to
the real Evidence.

**Outcome A.** One `HUMAN_REVIEW` assessment exists, reviewed by **`thibchm`**,
value **0.5**. The TED Evidence now resolves `RESOLVED` and is **scorable**, with
**reliability as the limiting component**. The seven other rows are untouched.

**The aggregation profile stays `UNCALIBRATED`. H-36A NOT ESTABLISHED, H-36B NOT
ADDRESSED, H-37 OPEN, H-38 OPEN.**

---

## 1. Why a tool existed to be built

Mission 1.15.12 established that the reliability contract offers three origins,
that two of them were unavailable here, and that the third —`HUMAN_REVIEW`—
requires a named accountable reviewer whom no mission and no model may supply.

That left a real gap rather than a philosophical one: the judgement had nowhere
to go. `resolve_reliability` is the read path, the schema existed since Mission
1.14, and **nothing in the repository could write an assessment**. The only
recorded write was a test fixture's raw `INSERT`.

## 2. What the tool is, and the line it does not cross

`infrastructure/scripts/record_reliability_assessment.py`, generic rather than
TED-specific: the scope is data, not a branch.

**It has no defaults.** `reliability`, `reviewed_by`, `rationale` and
`stated_limitation` are refused when blank, and there is no suggestion, fallback
or derivation for any of them anywhere in the file. A test asserts the template
ships every one of them empty, so a helpful default cannot appear without a
failing build.

| | a `decide`-style tool | this one |
|---|---|---|
| Supplies a value | yes | **never** |
| Derives one from neighbouring confidences | possible | **structurally impossible** — it reads none |
| Records a limitation the software wrote | possible | **refused** — blank is refused, and nothing fills it |

### 2.1 The packet is facts; the file is judgement

`--packet <name>` prints what the repository has **already established** about a
scope — the retrieved documents and their findings — and emits a template whose
basis rows are filled in and whose judgement fields are empty.

The split is the whole design. Basis rows are retrieved documents, so pre-filling
them is transcription and the reviewer checks or removes them. A value or a
limitation is a judgement, so pre-filling either and recording it as though a
person wrote it would make the tool a forgery.

A test asserts no packet contains a `reliability` key at all.

### 2.2 A review file rather than flags

A rationale and a stated limitation are paragraphs. A reviewer who has to fit a
limitation into a shell argument writes a shorter one than they mean, and the
limitation is the field that stops a number being unarguable.

The file is also what the reviewer re-reads before confirming.

### 2.3 `reviewed_by` names a person

The guide says so; the contract enforces non-blank; the tool additionally refuses
`operator`, `system`, `admin`, `claude`, `ai`, `script` and their neighbours,
because those are what gets typed when nobody wants to be the reviewer.

**And it refuses placeholders**, which was found by real use rather than
designed: the reviewer first submitted `<MON IDENTITÉ RÉELLE>`, a template shape.
A blank is refused and a placeholder was not, which made it strictly worse than a
blank in the one field that exists to say who is accountable. Any value beginning
`<` or `[` is now refused.

## 3. The factual review packet the reviewer saw

Scope, five parts:

```json
{"source_id":"ted-eu","resource_id":"notices/eforms-contract-and-award",
 "record_kind_id":"procurement_notice","claim_type":"OBSERVED",
 "proposition_kind":"source_reported_procurement_value_contrast"}
```

What evidence in this scope supports: *that TED published a structured value the
buyer submitted. Not that the amount is an accurate account of the procurement.*

Four findings, presented before any decision:

1. **BT-161 includes options and renewals** — not what was paid, and options may
   never be exercised.
2. **The buyer supplies it; TED validates conformance only** — 60 published rules
   name BT-161, all presence or absence by notice type, none about correctness.
3. **It may be lawfully withheld** (BT-195 to BT-198), so the cohort covers the
   published subset and the missingness is not random.
4. **The statistic is a maximum minus a minimum**, the one most exposed to a
   missing extreme.

Four document-backed basis rows accompanied them, citing the eForms SDK 1.15.1
field repository, its business-term definitions, BT-195 to BT-198, and the
published business rules.

## 4. The decision

| | |
|---|---|
| Assessment id | `3de2af10-60d1-4e3e-a9b6-d67e2345e020` |
| Scope | as §3 |
| Origin | **`HUMAN_REVIEW`** |
| Version | 1, current |
| Reviewer | **`thibchm`** |
| Reliability | **0.5** |
| Basis | 4 rows, **4 document-backed** |
| Calibration dataset | none, and the contract refuses one for this origin |

**Rationale**, as recorded. The wording was AI-assisted and the reviewer read,
adopted and submitted it; the number it explains was theirs alone (§4.2):

> *"I assign a reliability of 0.5 because the structured meaning and publication
> process of BT-161 are documented, but the underlying economic amount is
> buyer-supplied rather than independently verified and the published cohort may
> omit values through lawful withholding. I therefore consider the evidence usable
> for the narrow claim that TED reported these values, while retaining substantial
> uncertainty around how completely and accurately the resulting contrast reflects
> the underlying procurement activity."*

**Stated limitation**, as recorded, in full. Same authorship as the rationale:

> *"This reliability assessment applies only to TED's structured publication of
> BT-161 values for the reviewed OBSERVED proposition. BT-161 includes options and
> renewals that may never be exercised, the value is supplied by the contracting
> authority and is not independently verified by TED for economic accuracy, some
> result values may lawfully be withheld from immediate publication, and the
> resulting published subset may therefore be incomplete in a non-random way.
> Because the proposition uses a maximum-minus-minimum contrast, it is particularly
> sensitive to missing extreme values. This assessment must not be interpreted as
> reliability of actual expenditure, market size, willingness to pay, pricing
> potential, demand, or any other commercial conclusion."*

### 4.1 On the value being 0.5

The contract uses `0.5 because unknown` as its own example of a non-judgement:
*"A measurement claiming the middle."* The coincidence was **put to the reviewer
before recording**, with the quotation, and they kept the value.

**What the contract forbids is `0.5 because unknown`, and that is not what was
submitted.** The rationale gives a specific two-sided argument — documented
structure and publication process on one side, an unverified buyer-supplied
amount and a possibly incomplete cohort on the other — and the stated limitation
bounds it. The number happens to land in the middle; the reasoning did not start
there.

Recorded here because a later reader sees the figure before the rationale, and
the question should not have to be asked twice.

### 4.2 Who wrote what

The distinction matters enough to state plainly rather than leave to the word
"submitted".

| | |
|---|---|
| The value `0.5` | **the reviewer's alone.** No model selected, derived, defaulted or recommended it |
| The decision to record it | **the reviewer's**, given explicitly |
| The wording of the rationale and stated limitation | **AI-assisted**, then reviewed and adopted by the reviewer |
| The four basis rows | retrieved documents, established in Mission 1.15.12 and checked by the reviewer |

`evidence-reliability-review-guide-v1.md` §5 draws the line in the same place:
*"A model may help you read documentation. It may summarise a methodology page,
point you at a section, or draft a paraphrase you then check against the source.
It may not be the epistemic source of the judgement."*

Help with expression is on one side of that line and choosing the number is on
the other. `HUMAN_REVIEW` remains the correct origin, and `reviewed_by` names the
person who made the judgement and is accountable for the text they adopted.

**Nothing persisted was changed by this clarification** — not the value, the
reviewer, the scope, the basis, the confirmation or the version. It corrects the
documentation only.

## 5. Persistence semantics

Written through the model, which validates before anything reaches the database:
range, the calibration coupling, at least one document-backed basis, and the
all-or-nothing supersession halves.

**Append-only.** A later review is version N+1; the previous current row gains
`superseded_at`, `superseded_by` and `superseded_reason`, and is never updated in
place. An aggregation that used version N must still be able to read version N. A
partial unique index enforces one current row per scope, and the resolver refuses
`AMBIGUOUS_ASSESSMENTS` anyway rather than trusting it.

**The Evidence row was not touched.** `scoring.evidence.reliability` is still
`NULL` on all eight rows, and that is correct: reliability is resolved **late**
from the class-level assessment, with the binding recorded alongside the value
(ADR-026 Decision 2). A value already on a row would win and consult nothing, so
writing one would have created a second answer to one question.

## 6. What resolution produced

```text
current assessments in the database: 1

    gdelt       source_reported_term_frequency_change        NO_APPLICABLE_ASSESSMENT  rel=None
    gdelt       source_reported_term_frequency_change        NO_APPLICABLE_ASSESSMENT  rel=None
    gdelt       source_reported_term_frequency_contrast      NO_APPLICABLE_ASSESSMENT  rel=None
>>> ted-eu      source_reported_procurement_value_contrast   RESOLVED                  rel=0.5
      binding: 3de2af10-60d1-4e3e-a9b6-d67e2345e020 v1 HUMAN_REVIEW by thibchm
    world-bank  source_reported_metric_period_change         NO_APPLICABLE_ASSESSMENT  rel=None  (x4)
```

**No leakage.** Scope matching did the work; there is no source-specific branch
in the matcher.

## 7. What the Evidence looks like now

| | Before | After |
|---|---|---|
| Reliability resolution | `NO_APPLICABLE_ASSESSMENT` | **`RESOLVED`, 0.5** |
| Scorability | `NON_SCORABLE` | **scorable** |
| `observation_category` | `UNCATEGORISED` | **`UNCATEGORISED`** |
| `independence_state` | `UNKNOWN` | **`UNKNOWN`**, group NULL |
| `evidence_level` | 1 | **1**, "Weak Signal" |

Aggregation over the one claim, under `reference-v1`:

```text
evidence_score           50.0
support_strength         0.5        contradiction_strength  0.0
supported_mass           0.5        uncertainty_mass        0.5
evidence_level           1  "Weak Signal"
aggregation_status       COMPLETE
profile status           UNCALIBRATED        calibrated: false
limiting_component       reliability
```

**`q_i = min(components)` did exactly what it is for.** Relevance, directness,
extraction confidence and freshness are all 1.0; reliability is 0.5; the item's
contribution is 0.5 and the engine names **reliability** as the limiting
component. The one reviewed number is the one that binds.

**The level did not move, and three separate gates say why:**

```text
Repeated Signal needs 2 supporting groups of established independence, found 0
  (plus 1 unknown-provenance group, which does not count)
Market Evidence needs a supporting record categorised MARKET_ACTIVITY or
  DIRECT_VALIDATION with established provenance
Direct Validation needs a supporting record categorised DIRECT_VALIDATION
```

Reliability alone cannot reach Level 4, and the reason is the category gate that
Mission 1.15.11 deliberately left at `UNCATEGORISED`.

## 8. What the score is, and what it is not

**It is support for one OBSERVED Claim**: that TED reported a 686545.02 EUR
spread between the largest and smallest `TOTAL_VALUE` in a bounded set of three
division-90 award notices.

It is **not** an Opportunity Score, a Market Score, a WTP Score, a Pricing Score,
an MRR Score or a revenue estimate. No Opportunity exists.

**And it is not calibrated.** `reference-v1` is `UNCALIBRATED`, computing it
required passing `allow_uncalibrated` explicitly, and the result carries its own
warning: *"its parameters were never fitted to labelled data. This result is not
calibrated and must not be presented as though it were."*

**Nothing was persisted.** No score row was written, and none may be:
`services/scoring` remains blocked for production research, and
`validate_evidence_aggregation` asserts no aggregation result is stored.

A human review is not a calibration, however careful. Mission 1.14 said so and
this mission does not change it: **one reviewed number now exists, and D-03's
four remaining blockers are exactly where they were.**
