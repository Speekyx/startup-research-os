# Mission 1.15.13 — TED Evidence Reliability: Operator Review and Application

**Sprint 1. Authorized by the Mission 1.15.13 brief §1-§30.**

**Outcome A.** The first `ReliabilityAssessment` in the system exists, decided by
a named person. The TED Evidence resolves `RESOLVED` and is **scorable**, with
reliability as the limiting component. The other seven rows are untouched.

**The profile stays `UNCALIBRATED` and nothing downstream was persisted. H-36A
NOT ESTABLISHED, H-36B NOT ADDRESSED, H-37 OPEN, H-38 OPEN.**

Full write-up: [`ted-eu-evidence-reliability-operator-review-v1.md`](../data/ted-eu-evidence-reliability-operator-review-v1.md).

---

## 1. The review

### Who performed it?

**`thibchm`**, the local operator, supplying the value, the rationale and the
stated limitation explicitly.

### What exact scope was reviewed?

```json
{"source_id":"ted-eu","resource_id":"notices/eforms-contract-and-award",
 "record_kind_id":"procurement_notice","claim_type":"OBSERVED",
 "proposition_kind":"source_reported_procurement_value_contrast"}
```

### What value, and what limitation?

**0.5.** The stated limitation scopes the
assessment to TED's structured publication of BT-161, names the four material
findings (options and renewals, no independent verification, lawful withholding,
sensitivity of a max-minus-min to a missing extreme) and closes with an explicit
refusal: *"must not be interpreted as reliability of actual expenditure, market
size, willingness to pay, pricing potential, demand, or any other commercial
conclusion."* Both are quoted in full in the review document §4.

### Was any value suggested or defaulted by software?

**No, and it is structurally impossible rather than merely avoided.** The tool
has no default, suggestion, fallback or derivation for any judgement field. The
template ships `reliability: null` and three empty strings; a test asserts that,
so a helpful default cannot appear without a failing build. Another test asserts
no packet contains a `reliability` key at all.

The blank template was run through the tool before the operator filled it, and
refused, which is recorded rather than assumed.

### Was an LLM used as reviewer?

**No — and the boundary is worth stating exactly, because it is not "no model
was involved".**

| | |
|---|---|
| The numeric judgement, `0.5` | **the human's alone.** No model selected, derived, defaulted or recommended it, and the tool has no mechanism that could |
| The decision to record it | **the human's**, given explicitly and confirmed |
| The **wording** of the rationale and the stated limitation | **AI-assisted**, then reviewed and adopted by the human |

The review guide already licenses exactly this and draws the line in the same
place: *"A model may help you read documentation. It may summarise a methodology
page, point you at a section, or draft a paraphrase you then check against the
source. It may not be the epistemic source of the judgement."*

Drafting prose that a reviewer then reads, edits and adopts is help with
expression. Choosing the number would have been the epistemic act, and it is the
one thing no origin in the contract would let a model perform. `HUMAN_REVIEW` is
therefore the correct origin, and `reviewed_by` correctly names the person who
made the judgement and is accountable for the text they adopted.

Recorded here because "written by the operator" was the original wording and it
overstated the case in the one document a later reader would use to check it.

**One thing was raised rather than recorded silently.** The contract uses
`0.5 because unknown` as its own example of a non-judgement: *"A measurement
claiming the middle."* That was put to the reviewer with the quotation **before**
anything was written, and they kept the value. What the contract forbids is
`0.5 because unknown`, and the submitted rationale is a two-sided argument rather
than a shrug. Recorded in the review document §4.1 so the question does not have
to be asked twice.

### How was the confirmation given?

The tool requires a typed confirmation at a terminal and refuses when there is no
TTY, which is the guard that stops a pipeline running it. **The operator gave
that confirmation in this session and explicitly authorised its transcription**,
and the agent transcribed it. That is a different act from a person typing at
their own terminal, and it is written down here rather than left to be inferred —
the same distinction ADR-030 draws for the TED database-right acceptance.

---

## 2. What was persisted

| | |
|---|---|
| Assessment id | `3de2af10-60d1-4e3e-a9b6-d67e2345e020` |
| Origin | **`HUMAN_REVIEW`** |
| Version | **1**, current (`superseded_at` NULL) |
| Reviewer | `thibchm` |
| Reliability | **0.5** |
| Basis | **4 rows, all document-backed** |
| Calibration dataset | none — the contract refuses one for this origin |

The basis rows cite the eForms SDK 1.15.1 field repository, its business-term
definitions, BT-195 to BT-198, and the published business rules, each with a URL,
a section reference and a summarized finding.

**Written through the model**, which validated range, the calibration coupling,
the document-backed-basis requirement and the supersession halves before anything
reached the database. Not a hand-written `INSERT`.

### Append-only

A later review becomes version N+1 and marks the previous current row
`superseded_at` / `superseded_by` / `superseded_reason`; nothing is updated in
place, because an aggregation that used version N must still be able to read
version N. The tool computes the next version and the row it would supersede from
the database rather than from an argument.

### The Evidence row itself was not touched

`scoring.evidence.reliability` is still **NULL on all eight rows**, and that is
correct rather than an omission. Reliability is resolved **late** from the
class-level assessment with the binding recorded alongside it (ADR-026 Decision
2). A value written onto the row would win over the assessment and consult
nothing, creating a second answer to one question.

---

## 3. Application to the real Evidence

```text
current assessments in the database: 1

    gdelt       source_reported_term_frequency_change        NO_APPLICABLE_ASSESSMENT  rel=None
    gdelt       source_reported_term_frequency_change        NO_APPLICABLE_ASSESSMENT  rel=None
    gdelt       source_reported_term_frequency_contrast      NO_APPLICABLE_ASSESSMENT  rel=None
>>> ted-eu      source_reported_procurement_value_contrast   RESOLVED                  rel=0.5
      binding: 3de2af10-60d1-4e3e-a9b6-d67e2345e020 v1 HUMAN_REVIEW by thibchm
    world-bank  source_reported_metric_period_change         NO_APPLICABLE_ASSESSMENT  rel=None  (x4)
```

### Did it apply to the intended Evidence? Did it leak?

**Applied to exactly one row; leaked nowhere.** Scope matching did the work —
five parts, all or nothing — and there is no source-specific branch in the
matcher. Tests pin the refusals for another TED resource, another record kind, an
`INFERRED` claim, another proposition kind, World Bank and GDELT.

### Is `observation_category` still `UNCATEGORISED`? Is `independence_state` still `UNKNOWN`?

**Both unchanged**, and structurally so: `resolve_reliability` returns a
resolution rather than a mutated row, and an assessment has no field in which to
declare a category or an independence. There is nothing for reliability to
promote with.

### What Evidence level results? Can reliability alone produce Level 4?

**Level 1, "Weak Signal". No.** The canonical rules were run rather than
inspected, and three separate gates report why:

```text
Repeated Signal needs 2 supporting groups of established independence, found 0
  (plus 1 unknown-provenance group, which does not count)
Market Evidence needs a supporting record categorised MARKET_ACTIVITY or
  DIRECT_VALIDATION with established provenance
Direct Validation needs a supporting record categorised DIRECT_VALIDATION
```

The category gate is the one Mission 1.15.11 deliberately left at
`UNCATEGORISED`, and it holds.

---

## 4. Scorability

### Is the Evidence now scorable? What exactly is being scored?

**Yes.** Aggregation over the one claim under `reference-v1`:

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
component. The one reviewed number is the one that binds, which is the whole
argument for the design.

**What it scores:** support for one `OBSERVED` Claim — that TED reported a
686545.02 EUR spread between the largest and smallest `TOTAL_VALUE` in a bounded
set of three division-90 award notices.

**What it is not:** an Opportunity Score, a Market Score, a WTP Score, a Pricing
Score, an MRR Score or a revenue estimate. No Opportunity exists.

### What remains uncalibrated?

**Everything that was.** `reference-v1` is `UNCALIBRATED`, computing the result
required passing `allow_uncalibrated` explicitly, and the output carries its own
warning: *"its parameters were never fitted to labelled data. This result is not
calibrated and must not be presented as though it were."*

**No score row was written**, and none may be: `services/scoring` stays blocked
for production research and `validate_evidence_aggregation` asserts no
aggregation result is persisted. A human review is not a calibration however
careful it was, and D-03's remaining blockers are untouched — one reviewed value
now exists for one scope of four, no `CALIBRATED` profile exists, no authorised
half-life exists, and the level thresholds are still structural minimums.

---

## 5. What was not done

| | |
|---|---|
| H-36A / H-36B / H-37 / H-38 | **unchanged.** A reliability judgement resolves none of them |
| New RawRecords, NormalizedRecords, Signals, Claims, Evidence | **0** |
| `INFERRED` Claims | 0 |
| Opportunities | **0** |
| Embeddings | 0 |
| Opportunity / Market / WTP / MRR scores | 0 |
| Assessments for World Bank or GDELT | **none** — out of mission scope, and their seven rows are unchanged |
| Gateway defect | not fixed, still backlog |

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 23 / 23 | 23 / 23 |
| Signals | 8 | 8 |
| Claims / ClaimRevisions / Evidence | 8 / 8 / 8 | 8 / 8 / 8 |
| **ReliabilityAssessments** | **0** | **1** |
| Assessment basis rows | 0 | **4** |
| Opportunities / Embeddings / Scores | 0 | 0 |

---

## 6. Two things real use found

### A refusal the design missed

The reviewer's first submission put **`<MON IDENTITÉ RÉELLE>`** in `reviewed_by`
— a template shape. A blank was refused and a placeholder was recorded, so the
one field that exists to say who is accountable was **worse protected against a
template shape than against nothing at all**, and the shape reads as an identity
to anyone scanning the row later.

Fixed before recording anything: any value beginning `<` or `[` is now refused,
with a test. The general form is written up as testing-strategy §61 — *a
validator that rejects emptiness has not yet rejected meaninglessness*.

The identity actually recorded is `thibchm`, which the operator had supplied
explicitly in their preceding message and which is their git identity on this
repository. Nothing was inferred.

### A guard that had been legitimately crossed

`test_no_reliability_assessment_was_created` existed in four TED test files and
asserted the table was empty. It was **deleted**, for the reason
testing-strategy §59 gives: the absence had stopped being *"a source review is
not a reliability review"* — which is still true, and is asserted structurally by
the AST test keeping policy state out of the reliability package — and become
*"nobody has done the second one yet"*.

The gateway's `test_no_assessment_exists_in_production` was **replaced rather
than deleted**, because a real invariant sat underneath it. It now asserts that
**every** assessment in production names a reviewer, states a limitation, rests
on at least one document-backed basis row, carries an origin from the closed
enum, and names a calibration dataset only if it is calibrated. That survives
however many assessments accumulate, and it deliberately asserts nothing about
how many there are or what any value is — those are deployment state.

---

## 7. Did all gates pass?

**Yes, every one, checked by exit code, before and after the human decision.**

```text
zero-dependency suites            555 tests, 8 packages      exit 0   (was 538)
all pytest suites                 7 packages                 exit 0
validate_schema / source_registry / compliance_capabilities  exit 0
validate_normalization / signals / claims                    exit 0
validate_evidence_aggregation                                exit 0
contract generation --check                                  exit 0
all four generated-document checks                           exit 0
ruff check / ruff format --check                             exit 0
mypy                              144 source files           exit 0
environment-template secret check                            exit 0
assert_registry_grants_nothing                               exit 0
```

---

## 8. Next mission

The TED reference path is complete: **authorization → resource → collector →
raw → normalized → Signal → Claim → Evidence → reliability → a score**. Every
stage is real, every stage refused something on the way, and the number at the
end is limited by the one value a person reviewed.

**Recommendation: expand the source portfolio, not the inference layer.**

The reason is in Mission 1.15's own finding and nothing since has changed it:
**six of eight business evidence families have no approving source, and two have
no registered candidate at all.** The system can now weigh evidence it has. What
it has is one procurement contrast, four population changes and three news-corpus
frequencies — and none of those is evidence of a person wanting or paying for
anything.

Three candidates, and the dependency graph separates them clearly:

1. **Source expansion (recommended).** Every downstream layer is now proven on
   real data, so the binding constraint is input variety rather than machinery.
   This is also the only path that makes cross-source convergence possible later,
   since convergence needs two sources observing the same thing and no two
   current sources do.
2. **Cross-source inference / `INFERRED` Claims.** Blocked in practice by the
   above: an inference layer over a portfolio with one transaction source would
   have nothing to converge, and the first thing it would be asked to do is the
   willingness-to-pay leap three missions have refused.
3. **Opportunity architecture and scoring.** Furthest out, and the one with the
   loudest pull. **Explicitly not next:** a Level 1 Weak Signal from a single
   `UNCALIBRATED` profile is not a foundation for ranking product ideas, and
   building the layer that consumes it before there is anything worth consuming
   is how a plausible number acquires authority it never earned.

**What should not happen next is an Opportunity built from the TED spread.** It
is one bounded contrast over three cleaning contracts, its reliability is 0.5 by
the reviewer's own reasoning, and its stated limitation forbids reading it as
market size or willingness to pay in as many words.
