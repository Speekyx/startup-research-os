# Mission 1.15.11 — TED Transaction Signal → OBSERVED Claim + Evidence

**Sprint 1. Authorized by the Mission 1.15.11 brief §1-§44.**

**Outcome A.** The existing deterministic Claim/Evidence architecture represents
the Signal truthfully, and one `OBSERVED` Claim, one ClaimRevision and one
Evidence row now exist. No contract was weakened to allow it.

**H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED. H-37 OPEN. H-38 OPEN.**

Full semantics: [`ted-eu-observed-claims-evidence-v1.md`](../data/ted-eu-observed-claims-evidence-v1.md).

---

## 0. A correction to Mission 1.15.10, made before anything was built

Reading the contributing observations first — which the brief §3 requires — the
provenance disagreed with the previous mission's report. The 1.15.10 report
stated an acquisition window of **2023-03-06 to 2023-03-08** and both notice
types. `raw_records.provenance` records what the collector actually sent:

```text
date_window   ["2023-03-01", "2023-03-01"]
notice_types  ["can-standard"]
expert_query  (notice-type IN (can-standard)) AND (publication-date>=20230301)
              AND (publication-date<=20230301) AND (classification-cpv=90*)
              SORT BY publication-date
```

Execution 1 also wrote **3 new records and 1 revision**, not 4 and 1.

Those details were written from memory after a context compaction instead of
being read back from the record that exists precisely so they need not be
remembered. The 1.15.10 report, the collector document, the transaction-signals
document and the manifest are corrected on the same branch, and the corrected
text now quotes `expert_query` and `date_window` and says where it is quoting
from.

**Two things this changed, and one it did not.** The one-day window makes the
comparability argument *stronger*: 2023-03-01 is the day that already held the
system's only division-90 EUR award total, which is why a cohort could grow
there. It also surfaced that the **bounds** are the one part of an acquisition
that leaves no trace in any record — a gap in the record rather than a property
of the run. Nothing about the Signal, its members or its magnitude changed.

`docs/CLAUDE.md` had also never been amended for 1.15.10, and its Blocked-work
prose had gone stale across three missions. Both are fixed on the same branch.

---

## 1. The Claim

### What exact proposition does the OBSERVED Claim make?

```text
Tenders Electronic Daily (EU public procurement) reported that, in its
"notices/eforms-contract-and-award" resource, within a bounded set of 3
"CONTRACT_AWARD_NOTICE" notices classified under "CPV" division "90", the
largest "TOTAL_VALUE" amount at "NOTICE" scope stated in "EUR" exceeded the
smallest by 686545.02.
```

Claim `1e00a6dc-051c-4431-b13b-cc879f01a526`, revision 1.

### What does it explicitly NOT claim?

Not strong or growing demand, not a large or attractive or profitable market,
not that anyone is willing to pay 686545.02 EUR, not that a SaaS could charge
it, not that the figure is a price, an average, a median, a contract value, a
budget or revenue, not that the market is growing, and not that buyers would pay
comparable amounts for a different product.

`TestWhatItRefusesToSay` asserts fifteen forbidden tokens absent from the
rendered statement. The **template** is the protection — no template contains one
of those words — and `build_claim`'s vocabulary guard is the backstop that
refuses any `OBSERVED` statement that acquires one later.

### Is the Claim bounded to the actual TED cohort?

Yes, and the bound is in the sentence rather than in a comment. *"within a
bounded set of 3"* is what separates this proposition from *"division 90
contracts vary by 686545.02 EUR"*, which is a claim about a population nobody
sampled. The notice class, amount type, amount scope, currency, classification
scheme and division are all named, because a restatement that drops a cohort
dimension has silently widened its subject.

### Is it source-attributed?

Yes. It begins with `registry.sources.canonical_name` and the words *reported
that*. It is a claim about a publication: false if TED did not publish those
notices, and still true if TED published a wrong figure.

### Is it OBSERVED rather than INFERRED?

`OBSERVED`, structurally. `_CLAIM_TYPE` is a module constant, `interpret()` takes
no claim-type parameter, and `validate_claims.py` fails the build on any
`ClaimType.X` attribute access in the package where `X` is not `OBSERVED` — over
the AST, so the prose explaining the rule cannot fail it.

### Was an additional interpretation support threshold required? Why or why not?

**No, and none was invented.**

The two questions are genuinely different and the brief was right to separate
them. The *derivation* threshold — is support enough to build a contrast at all —
is 2, and this cohort has 3. The *interpretation* threshold asks whether 3 is
enough to make this restatement, and the answer follows from what the
restatement adds: **nothing**. Every fact in the Claim is a property of the
Signal, and the step between them is a format string over structured facts.

A threshold here would be answering a different question — *is three enough to
believe something about the market* — which this Claim does not ask.
`claim-evidence-interpretation-contract-v1.md` §11 already forbids inventing
one: *"No universal thresholds: '3 Signals required' is an arbitrary number
wearing the costume of a rule."*

**No established threshold was lowered for TED**, because there is none to
lower. What support is *for* lives one layer down, in aggregation, where three
rows from one publisher are one group.

### How is `derivation_confidence = 1.0` interpreted? Was any epistemic probability inferred from it?

It means the deterministic derivation is mechanically established under the
extractor contract — the arithmetic is right. **Nothing was inferred from it.**

It did not become `reliability` (NULL), a claim probability, a source-reliability
value or a business confidence, and no code multiplies, copies or defaults one
from the other. `interpretation_confidence` is separately `1.0` and says only
that the interpreter read the Signal correctly.
`test_derivation_confidence_does_not_become_reliability` pins all of it.

### Does the Claim contain temporal semantics? Is `observed_at` still absent?

**No temporal semantics of any kind.** No date, no window, no ordering, no
"recently", no "increased", no "trend" — asserted token by token.

`observed_at` is NULL on the Evidence row and on all three contributing
normalized records. The template accepts temporal basis `NONE` **and nothing
else**; any other basis is refused with `INCOMPATIBLE_TEMPORAL_SEMANTICS` rather
than phrased with wording chosen for a different basis.

The acquisition window bounded **retrieval**, not the proposition. The period
label reaches the Signal's window and the contributing records and reaches the
Claim nowhere; `test_the_period_label_reaches_the_signal_and_not_the_claim`
asserts both halves in one test, so the distinction cannot be lost by deleting
the wrong assertion.

### Is H-37 still OPEN? Is H-38 still OPEN?

**Both OPEN, and neither was consulted.** The Claim is built so it does not
depend on either: nothing temporal is asserted, and the eligibility rule that
admitted only unambiguously paired amounts was applied one layer down and is not
revisited here. An extractor or an interpreter routing around a question does
not answer it.

### What monetary semantic is preserved? Is 686545.02 represented exactly? Is the magnitude clearly max-minus-min?

`TOTAL_VALUE`, at `NOTICE` scope, in `EUR`, magnitude kind
`ABSOLUTE_DIFFERENCE`, magnitude **686545.02** exactly — no float, no rounding,
no conversion.

The wording is **"the largest … exceeded the smallest by"**, which is
max-minus-min said in a sentence. It is never called a price, an average, a
median, a contract value or a willingness to pay, and
`test_it_is_a_maximum_minus_a_minimum_and_says_so` asserts those words absent.

A cohort whose amounts were all equal renders *"was equal to the smallest"*
instead, so the "exceeded" wording is never borrowed for a case it does not
describe.

### Is generic WTP, market size or market demand mentioned or implied?

None of the three, in the statement or in the fact set.

### Was CPV division 90 translated into an inferred market?

**No.** The statement says `"CPV" division "90"`. Division 90 is cleaning and
environmental services and the Claim does not know that; naming it would be a
classification with no reviewed mapping behind it, and it belongs to a later
layer. `test_the_cpv_division_is_not_translated_into_a_market_name` pins it, and
"cleaning" and "environmental" are in the forbidden-token list.

---

## 2. The interpreter

### Was the existing generic interpreter reused? If modified/versioned, why?

**Reused and versioned: `observed-signal-restatement@1.0.0` → `1.1.0`.** Brief
§15 outcome **B**.

- **Not a new interpreter (outcome C).** The proposition is a Signal restated
  with its source named, which is exactly what this interpreter is. A separate
  one would have been source-specific, and a template is specific to a **Signal
  type**, never to a publisher — as all three existing ones are.
- **Not an unversioned extension (outcome A).** The interpreter can now make a
  proposition it could not make before. That is version-worthy even though
  nothing existing moved.
- **Minor, because the addition is purely additive.** The three existing
  templates render byte-identical statements, fact sets and evidence.
  `TestTheExistingThreeTemplatesDidNotMove` pins the numeric statement, the
  numeric proposition key and the lexical statement, so *additive* is checked
  rather than promised.

The fourth template accepts basis `NONE` only, and there is still **no
fallback**: a Signal type with no template is `UNSUPPORTED_SIGNAL_TYPE`.

### How is Claim identity derived?

`proposition_key` = sha256 over the canonical JSON of `proposition_facts`:

```json
{"proposition":"source_reported_procurement_value_contrast",
 "source_id":"ted-eu","resource_id":"notices/eforms-contract-and-award",
 "notice_class":"CONTRACT_AWARD_NOTICE","amount_type":"TOTAL_VALUE",
 "amount_scope":"NOTICE","currency":"EUR","classification_scheme":"CPV",
 "classification_division":"90",
 "classification_codes":["90715200","90911200","90911300","90919300"],
 "notice_ids":["125972-2023","126676-2023","127668-2023"],
 "relation":"DIFFERS"}
```

**The cohort membership is the identity and the amount is wording**, and that
pair is where this template differs from the other three:

- a revised amount appends **revision 2** to this claim (revision 1 is never
  modified, because an aggregation that read it must still be able to);
- a **fourth** qualifying notice is a **different proposition**, because the
  cohort is the subject.

`relation` (`DIFFERS | EQUAL`) is carried because `direction` is
`NOT_APPLICABLE` by construction, so without it an all-equal cohort would be
indistinguishable from one whose amounts differ. Identity is not built from the
prose, an embedding, the Signal id, the session, the correlation id or a clock.

### Is Claim creation idempotent?

Yes, exercised against the real database rather than argued:

```text
first run    claims new 1   revised 0   unchanged 0   revisions 1   evidence 1
second run   claims new 0   revised 0   unchanged 1   revisions 0   evidence 0
```

A redelivery finds the statement unchanged and writes nothing. No TED-specific
versioning mechanism was invented; this is the existing rule — revise when the
statement differs, otherwise write nothing.

### Does Claim provenance point to the exact Signal revision? Are all 3 supporting observations still reachable?

Yes to both. The Evidence row's `signal_id` is
`97ff6d37-1a2d-5725-ad97-d846767b8631`, and
`research.claim_interpretation_inputs` records that Signal with role `CITED`.

All three observations are reachable and were counted in the live database:

```sql
Claim -> scoring.evidence.signal_id
      -> nlp.signal_inputs (role = 'CONTRIBUTED')
      -> acquisition.normalized_records
-- 3 distinct observation_key
```

Support cardinality is not reduced anywhere: it is in the statement ("a bounded
set of 3"), in `notice_ids`, and in the Signal's own inputs. The member
**values** are deliberately not duplicated into the Claim — they are one join
away, and one fact in two places eventually disagrees with itself.

---

## 3. The Evidence

### What Evidence row was created?

`d48e9694-c4d5-4a03-9a28-a4d6fa5053d0`.

| Field | Value |
|---|---|
| `direction` | `SUPPORTS` |
| `source_id` | `ted-eu` |
| `signal_id` | `97ff6d37-…` |
| `relevance` / `directness` / `extraction_confidence` | `1.0` / `1.0` / `1.0` |
| `reliability` | **NULL** |
| `observation_category` | `UNCATEGORISED` |
| `independence_state` | `UNKNOWN`, group NULL |
| `evidence_level` | `1` |
| `observed_at` | NULL |

### What Evidence level was assigned and why?

**1, "Weak Signal".** Not a judgement invented here: it is where the ladder's
own gates leave a single record whose category is `UNCATEGORISED` and whose
independence is `UNKNOWN`. Level 2 needs established independent groups, level 3
needs several across source families, and levels 4 and 5 are category-gated.
Level 0 would be wrong — an external observation exists.

**Support 3 did not raise it**, and that is the point of §19 of the brief. The
count of contributing observations is a property of the Signal; the Evidence is
one row from one publisher.

### What reliability value exists? Was any invented?

**NULL, and none was invented.** In particular it was not inferred from TED
being an official EU publication, from the support count, from
`derivation_confidence = 1.0`, or from the source's approving policy verdict
under this profile. No `ReliabilityAssessment` was created; none applies.

### What independence state/group exists? Is it correctly single-source?

`UNKNOWN`, with no `independence_group_id` — which the model requires to be
absent for anything but `KNOWN_DEPENDENT`.

**Correctly single-source.** Three TED notices are three records from one
publisher sharing a publication and selection process; counting them as three
independent sources would triple the apparent support for something observed
once. They are not declared *dependent* either, because that is a judgement this
layer cannot make. `test_support_three_is_still_one_source` asserts it.

### Is Evidence currently scorable?

**No — `NON_SCORABLE` with `MISSING_RELIABILITY`**, exactly like the other
seven. Aggregation for this claim produces no score, and that is the design
working rather than a gap: a system that stays capable of producing no score is
what makes a score mean something when one appears.

### `observation_category` — the mission's closest call, recorded rather than buried

It is `UNCATEGORISED`, and the alternative is genuinely arguable.

A `CONTRACT_AWARD_NOTICE` records a purchase that actually happened, which is
`MARKET_ACTIVITY`'s own first example, and TED was pursued across nine missions
precisely because it is the first source that could evidence a **transaction**
rather than a listed price. On that reading `UNCATEGORISED` under-records what is
known.

**What decided it:** this row does not carry a purchase. It carries a maximum
minus a minimum over a set of published notices, and a spread is a property of
records rather than economic activity. The category says what kind of thing was
observed *for this Claim*, and what was observed is a contrast.

**Why it matters beyond taste:** `MARKET_ACTIVITY` is the **only** gate to
`EvidenceLevel` 4, and that gate is reached independently of every count above
it. Setting it here would pre-authorise "Market Evidence" for a spread between
three cleaning contracts, and would do so silently — the level would appear the
moment a later mission supplied a reliability and an independence state.

**Left open deliberately:** the individual notices may well support
`MARKET_ACTIVITY` for a claim about a **purchase**. No such claim exists and no
template produces one. A mission that wants Level 4 from TED should write that
claim rather than recategorise this row.

---

## 4. What was not done

| | |
|---|---|
| Was an LLM called? | **No.** `validate_claims.py` fails the build on a model, network or embedder import anywhere in the interpretation layer, over the AST |
| Were `INFERRED` Claims created? | No. No module, no branch, no parameter would select one |
| Was an Opportunity created? | **No.** `opportunity_id` is NULL; a Claim may precede an Opportunity (ADR-024), so no placeholder was created to attach this one to |
| Were any scores created? | No. No `EvidenceScore`, no Opportunity score, no research completeness, no revenue or MRR estimate |
| Were ReliabilityAssessments created? | No, and none was mechanically required |
| Were embeddings created? | No. D-12 open |
| Were new TED RawRecords collected? | **No.** No TED API call. The collector, the CPV query, the resource policy and the route policy are untouched |
| Was the Gateway defect fixed? | No, still backlog |
| Were the existing seven Claims/Evidence changed? | **No.** All seven keep `interpreter_version = 1.0.0` and `current_revision = 1`; zero claims have a revision above 1 |

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 23 | 23 |
| NormalizedRecords | 23 | 23 |
| Signals | 8 | 8 |
| Claims | 7 | **8** |
| ClaimRevisions | 7 | **8** |
| Evidence | 7 | **8** |
| Opportunities | 0 | 0 |
| ReliabilityAssessments | 0 | 0 |
| Embeddings | 0 | 0 |
| Scores | 0 | 0 |

### The real execution

Through `run_claim_interpretation_job` — the function the Celery task calls —
over a tenant-scoped connection (`SET LOCAL ROLE` plus `app.workspace_id`),
scoped by `signal_type_ids = ["procurement_value_contrast"]` so the seven
existing claims were not read. **No row was inserted by hand.**

---

## 5. A guard was retired rather than moved a fourth time

`TestNothingWasCollected` asserted that TED had not reached a stage of the
pipeline. It was inverted in 1.15.7 (RawRecords), 1.15.8 (NormalizedRecords) and
1.15.10 (Signal), each time by moving the assertion one stage down. 1.15.10's own
comment said the next move would be the last.

A TED Claim and Evidence row now exist, so per brief §37 the two methods were
**deleted** rather than pointed at Opportunities — in all five files that carried
them. A guard that keeps retreating stops being a guard and becomes a record of
how far the work got: it passes at every step and fails only when a mission does
its job.

**What was kept** is the part that never moved: the same class already asserts
that no ReliabilityAssessment, no Opportunity and no embedding exists, and those
are still absences rather than counts. The class name stays historical on
purpose. Written up as testing-strategy §59.

---

## 6. Did all gates pass?

**Yes, every one, checked by exit code.**

```text
zero-dependency suites            515 tests, 8 packages      exit 0
all pytest suites                 7 packages                 exit 0
validate_schema                                              exit 0
validate_source_registry                                     exit 0
validate_compliance_capabilities                             exit 0
validate_normalization                                       exit 0
validate_signals                                             exit 0
validate_claims                                              exit 0
validate_evidence_aggregation                                exit 0
contract generation --check                                  exit 0
sros-source render --check                                   exit 0
render_review_results --check                                exit 0
render_signal_coverage --check                               exit 0
sensitivity --check                                          exit 0
ruff check / ruff format --check                             exit 0
mypy                              144 source files           exit 0
environment-template secret check                            exit 0
assert_registry_grants_nothing                               exit 0
```

`quality-gates.md` was reviewed and **not** changed: no gate was added, removed
or altered. `validate_claims.py` needed no change either — it already required
every supported signal type to be registered by a migration, and
`procurement_value_contrast` was registered in Mission 1.15.9.

---

## 7. Final pipeline state

```text
TED
  RAW                        11 records (3 at collector 1.0.0, 8 at 1.1.0)
  NORMALIZED                 11 records, all PARTIAL (the ceiling while H-37 is open)
  TRANSACTION_VALUE SIGNAL   1, support 3, 686545.02 EUR, procurement-value-contrast@1.0.1
  OBSERVED CLAIM             1, revision 1, observed-signal-restatement@1.1.0
  EVIDENCE                   1, level 1, UNCATEGORISED, UNKNOWN independence
  RELIABILITY                NONE -- NON_SCORABLE with MISSING_RELIABILITY
  OPPORTUNITY                NONE
  SCORING                    NONE

H-36A  NOT ESTABLISHED    H-36B  NOT ADDRESSED    H-37  OPEN    H-38  OPEN
```

---

## 8. Next mission

Outcome A succeeded, so the brief's §43 question applies: **TED Evidence
Reliability Assessment V1**, or **Model-derived INFERRED Claims V1**.

**Recommendation: A — TED Evidence Reliability Assessment V1**, and the
dependency graph rather than preference decides it.

The reason is that reliability is the only thing standing between the existing
evidence and any score at all. Eight Evidence rows exist and **all eight are
`NON_SCORABLE` for the same reason**: no reviewed assessment applies to any
scope in use. Mission 1.14 built the whole machinery — scope matching on
`(source_id, resource_id, record_kind_id, claim_type, proposition_kind)`, the
origins, the evidence requirements, the supersession rules — and then created
zero assessments, deliberately. It is the one blocker in D-03's list that a
mission can actually close, and closing it turns a framework that has never run
on real data into one that has.

**Option B is the wrong next step, for a specific reason rather than a general
caution.** An `INFERRED` claim needs a stated reasoning step, and the reasoning
it would state over the current evidence is *what does a procurement spread
imply about a product opportunity* — which is the willingness-to-pay leap this
mission and the two before it were built to prevent. Building the inference
layer before the evidence it reasons over can be weighed is how a plausible
number acquires authority it never earned.

**Three things Mission A will have to settle**, all visible from here:

1. **Whether one assessment can cover the procurement scope at all.** The scope
   is measurement × purpose, and the purpose here is
   `source_reported_procurement_value_contrast` — a proposition kind that did not
   exist when the reliability contract was written. Mission 1.14's ratio (seven
   Evidence rows collapsing to three scopes) needs re-checking with an eighth row
   that is a fourth scope.
2. **What "reliable" even means for a contract award notice.** Not whether TED
   is a reputable publisher: whether a published `TOTAL_VALUE` at `NOTICE` scope
   dependably reflects the concluded contract. That is a documented-method
   question with a first-party answer available in the eForms specification, and
   it is the kind of question the contract requires evidence for.
3. **That a reliability does not become a category.** Assessing this Evidence
   does not make it `MARKET_ACTIVITY`, and §11 of
   `ted-eu-observed-claims-evidence-v1.md` is the open question it must not close
   by side effect — because the two together are what unlock Level 4.
