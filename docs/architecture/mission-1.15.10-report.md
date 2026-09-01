# Mission 1.15.10 — Collector Decimal Repair + Comparability-Designed TED Acquisition

**Sprint 1. Authorized by the Mission 1.15.10 brief §1-§45.**

Phase A repaired the collector's Decimal invariant with a version bump. Phase B
executed one bounded acquisition designed for comparability and ran it through
Raw → Normalized → Signal.

**Result: one real `TRANSACTION_VALUE` Signal exists**, magnitude 686 545.02 EUR
over three award notices in CPV division 90.

**H-36A, H-36B, H-37 and H-38 are all exactly where the mission found them.**

---

## 1. Phase A — the collector repair

### What exact defect existed in `ted-search-api@1.0.0`?

It parsed the HTTP response with a bare `json.loads`. Every JSON number carrying
a fractional part therefore became a **binary float** before it was persisted,
and the manifest's own invariant is that a number crossing a boundary keeps its
decimal identity. `0.1 + 0.2 == 0.30000000000000004` is the standard
demonstration; a tender value is exactly the kind of number where the last cents
are the point of the figure.

The defect was recorded in the Mission 1.15.8 report and Mission 1.15.9 §13 made
repairing it a **blocking rule on the next TED acquisition**. That rule is what
Phase A discharges, and it was discharged before Phase B opened a socket.

### What new collector version was created?

**`ted-search-api@1.1.0`.** A minor bump, not a patch, because the shape of the
persisted payload changes: the same notice collected under the two versions does
not produce byte-identical bytes.

### Are JSON numeric values now parsed with Decimal?

Yes. `json.loads(response.text, parse_float=Decimal)`, and every `Decimal` is
then rendered back through `canonical_number` before persistence, so what reaches
`jsonb` is a fixed-point **string**.

Verified end to end against the real database rather than asserted in a fixture:

```text
jsonb_typeof(value) for a fractional amount   ->  string   ("73415.22")
jsonb_typeof(value) for an integral amount    ->  number   (440000)
```

`parse_int` is deliberately **not** set. A JSON integer is already exact in
Python, and wrapping it would change the representation of a value that was never
at risk. The asymmetry is intentional and is pinned by a test.

### Can a binary float enter new RawRecord construction?

No, and the guard is not a review habit. `TestExactNumericParsing` scans the
constructed record for any `float` instance and fails if one is present, and it
includes a long decimal (`12345678901234567.89`) that a float64 cannot hold
unrounded, plus the specific float-artefact value `0.30000000000000004`.

### Were the existing three V1.0 RawRecords rewritten?

**No.** Nothing was migrated, rewritten or backfilled. They stand as collected,
still recording `collector_version = 1.0.0`, and they are still lossy in the
sense the repair addresses. A record is what a named collector version actually
produced at a moment; rewriting it would make the provenance say something that
never happened.

### Are they still supported by normalization?

Yes. The normalizer declares `supported_collector_versions = {"1.0.0", "1.1.0"}`
and reads both payload shapes. The database holds both today:

| Collector version | TED RawRecords | TED NormalizedRecords |
|---|---|---|
| `1.0.0` | 3 | 3 |
| `1.1.0` | 8 | 8 |

### Was a normalizer version bump needed? Why or why not?

**No, and this was the more interesting half of the decision.**

A version on a component announces that its **output** changed. The normalizer's
output did not: it already routed every amount through `canonical_number` on the
way out, so a notice normalized from a `1.0.0` payload and the same notice
normalized from a `1.1.0` payload produce the same canonical decimal string. What
changed is the set of **inputs** it accepts, and that is declared where it
belongs — in `supported_collector_versions`, which is a compatibility statement
rather than an identity.

Bumping it would have announced a difference that does not exist, and every
consumer comparing normalizer versions would then have had to work out that the
two were equivalent. A version that changes for a reason invisible in the output
is a version nobody can reason with.

### Did any source policy change?

No. No registry entry, no compliance capability, no route, no resource, no field
list, no profile, no retention rule and no human decision was touched.
`assert_registry_grants_nothing` passes.

### Did H-36A / H-36B change?

**No.** H-36A remains **NOT ESTABLISHED** and H-36B remains **NOT ADDRESSED**.
Nothing in this mission touched the database-right question, and a collector
parsing numbers more carefully says nothing about who holds rights over the
collection.

### Did H-37 change?

**No. OPEN.** `observed_at` is still NULL on every TED normalized record, and the
Signal derived here is `NON_TEMPORAL` precisely so that it does not depend on the
answer. An extractor being able to route around a question does not answer it.

### Did H-38 change?

**No. OPEN.** The eligibility rule still admits an amount only when the notice
carries exactly one amount and exactly one currency, because that is the only
configuration where the pairing needs no assumption about positional alignment.
Nothing in this mission looked for evidence about arrays with several entries.

---

## 2. Phase B — the acquisition, defined before execution

### What CPV division was targeted? Why was it selected?

**Division 90**, cleaning and environmental services.

It was selected because Mission 1.15.9 established that the cohort key includes
the CPV division, and its zero result came from having exactly one EUR award
total in division 90 and one in division 66. Division 90 was where comparable
observations were **most likely to already exist**, since one was already held,
and a plausible market for repeated award notices denominated in EUR.

It was **not** selected for volume. No division was probed to see which returned
the most notices, no counts were compared, and the choice was written down before
any request was sent.

### What notice class was targeted?

`CONTRACT_AWARD_NOTICE`. An award notice states what a contract was actually
worth; a contract notice states what a buyer expects to spend. Mixing them would
be the flattening this Signal family exists to prevent.

### What amount semantic / scope / currency was targeted?

`TOTAL_VALUE`, at `NOTICE` scope, in `EUR`. Chosen before execution, and they are
three of the dimensions of the cohort key.

### What exact bounded query was defined BEFORE execution?

```text
(notice-type IN (can-standard))
  AND (publication-date>=20230301)
  AND (publication-date<=20230301)
  AND (classification-cpv=90*)
SORT BY publication-date
```

on route `ted-search-api`, resource `notices/eforms-contract-and-award`, profile
`local-private-research-v1`, one page.

**This query is quoted from `raw_records.provenance.expert_query`**, which is the
collector's own record of what it sent, and the window from `provenance.date_window`.
An earlier draft of this report stated a three-day window in March and both
notice types; neither is what the collector sent, and the record is what settles
it. The bounds are declared in the job payload and are the one part of the
acquisition that leaves **no trace in the record** — noted here as a gap rather
than restated from memory.

The window is a **single day, 2023-03-01**, and it was chosen for the reason the
division was: that day already held the one division-90 EUR award total the
system had (`125972-2023`), so it was the day on which a cohort could plausibly
grow. Only award notices were requested; `cn-standard` was dropped, because a
contract notice states what a buyer expects to spend and cannot join a cohort of
concluded values.

### Was the query widened after seeing the result?

**No.** The window was never extended, the division was never dropped, the bounds
were never raised and no second division was tried. The brief's rule — a failed
attempt to reach minimum support is a valid result — was accepted before
execution, and Mission 1.15.9's zero is the evidence that this is honoured in
practice rather than only in writing.

### One execution disagreed with its own declaration, and that is recorded here

The **first** Phase B execution ran a query **without** `(classification-cpv=90*)`
in it. `cpv_division` reached the request dataclass, the composed query and the
idempotency key, but `TedSearchJobPayload.from_payload` **never read it from the
job payload**, so the value the job was given never became the value the request
used.

- It was **broader** than declared, not narrower: it asked for every notice type
  in the window rather than only division 90.
- Nothing unauthorised was collected. Same route, same resource, same bounds,
  same field list, same profile; the extra notices are ordinary TED notices
  inside the authorised resource.
- **It is still a defect that matters.** A narrowing that exists only in the
  caller's intent is not a narrowing, and had the declared scope been narrower
  for a *compliance* reason rather than a comparability one, the same defect
  would have been a breach rather than an inconvenience.

The fix wired `from_payload`, and the test that now guards it asserts the
**composed query string** rather than the dataclass field, because the query
string is the only artefact the source ever receives. This is written up as
testing-strategy §58.

The second execution ran the declared query exactly.

### How many HTTP requests occurred?

**One per execution, two in total.** No pagination, no retry, no probe of the
service's limits, no exploratory request.

### How many notices were returned? How many new RawRecords were persisted?

| | Execution 1 (broader than declared) | Execution 2 (as declared) |
|---|---|---|
| HTTP requests | 1 | 1 |
| Window sent | 2023-03-01 to 2023-03-01 | 2023-03-01 to 2023-03-01 |
| Notice types sent | `can-standard` | `can-standard` |
| CPV in the query | **absent** | `classification-cpv=90*` |
| Notices returned | 4 | 4 |
| New RawRecords | **3** | **4** |
| Revised RawRecords | 1 (`125972-2023`) | 0 |
| Natural-person fields requested | none | none |
| Natural-person data received | none | none |

Every row above is read back from `raw_records.provenance`, not from the job
that was submitted.

Execution 2 re-run identically: **0 new, unchanged**.

### How many new NormalizedRecords resulted?

**8** (7 new plus the revision of `125972-2023`), all `PARTIAL`. `PARTIAL` is the ceiling for this adapter while H-37 is
open, and that is a truthful quality statement rather than a defect.

### What collector version do the new RawRecords record?

**`1.1.0`**, all eight.

---

## 3. The Signal

### How many monetary observations were eligible after normalization?

Of the 10 TED normalized records the derivation considered, **4** carried a
`TOTAL_VALUE` paired with exactly one currency. Three were EUR in division 90 and
formed the cohort; the fourth was PLN.

### How many cohorts were formed? How many met minimum support?

**3 cohorts formed, 1 met minimum support**, per monetary semantic:

```text
TOTAL_VALUE        3 groups considered   1 derived   2 refused
ESTIMATED_VALUE    3 groups considered   0 derived   3 refused
TENDER_VALUE       3 groups considered   0 derived   3 refused
FRAMEWORK_MAXIMUM  3 groups considered   0 derived   3 refused
```

Every refusal is `INSUFFICIENT_INPUT_OBSERVATIONS`, and every one is recorded as
a run, never as a row in a table of signals (ADR-021).

### How many `TRANSACTION_VALUE` Signals were created?

**One.**

| | |
|---|---|
| Id | `97ff6d37-1a2d-5725-ad97-d846767b8631` |
| Magnitude | **686545.02** |
| Magnitude kind | `ABSOLUTE_DIFFERENCE` |
| Unit | `EUR`, state `INHERITED` |
| Direction | `NOT_APPLICABLE` |
| Temporal basis | `NONE` |
| Derivation confidence | 1.0 |
| Extractor | `procurement-value-contrast@1.0.1` |

### What are its support count and scope?

**Support 3.**

| Notice | Amount (EUR) |
|---|---|
| `125972-2023` | 73 415.22 |
| `126676-2023` | 440 000 |
| `127668-2023` | 759 960.24 |

```json
{"currencies":["EUR"],"source_ids":["ted-eu"],"amount_types":["TOTAL_VALUE"],
 "amount_scopes":["NOTICE"],"notice_classes":["CONTRACT_AWARD_NOTICE"],
 "classification_codes":["90715200","90911200","90911300","90919300"],
 "classification_scheme":"CPV"}
```

Re-derived identically: **0 new, 1 unchanged.** The derivation is idempotent.

### Two notices in the window were excluded, and they show the rule doing real work

- `127009-2023` — spans CPV divisions 77 and 90, denominated in **PLN**;
- `127459-2023` — spans divisions 45 and 90, EUR.

Neither was admitted. A cohort mixing currencies would subtract numbers that are
not comparable, and a notice spanning two divisions has no single subject. This
is the same rule that produced zero in Mission 1.15.9, applied unchanged to a
dataset where it now excludes rather than blocks.

### Was the existing extractor changed?

**Yes, and the brief's success criterion 6 expected it to run unchanged. It is
recorded here rather than smoothed over.**

The extractor was bumped `1.0.0` → `1.0.1` for one reason: the cohort **scope**
carried only the **first** member's CPV codes. With one member per cohort — which
is every cohort Mission 1.15.9 ever formed — "first member's codes" and "all
members' codes" are the same value, so no fixture and no assertion in the suite
could tell the two rules apart. The first cohort with three members and four
distinct codes separated them immediately.

The scope is what tells a reader which market a contrast is about. A scope naming
one code while the contrast spans four is a **false description of the Signal's
own subject**, and shipping it would have been worse than a version bump.

**What the change is not:** it does not alter eligibility, the cohort key, the
minimum support, the magnitude, the magnitude kind, the direction, the temporal
basis or the currency rule. The same inputs form the same cohort and produce the
same number; only the scope's `classification_codes` differ. The `1.0.0` row was
deleted after checking its foreign-key closure — nothing referenced it, since no
Claim and no Evidence exists — and the Signal re-derived, rather than left
standing beside its successor.

### Were any cohort dimensions weakened?

**No.** Source, notice class, amount type, amount scope, currency and CPV division
all still key the cohort, and the minimum support is still 2. Nothing was relaxed
to make a Signal appear; the observations were changed instead, which was the
mission's whole point.

### Was any currency converted?

**No.** No rate, no table, no arithmetic across currencies. The PLN notice was
excluded rather than converted.

### Was H-38 bypassed?

**No.** Only amounts with exactly one amount and one currency were admitted,
which is the configuration where no positional-alignment assumption is needed.

### Was any temporal ordering used?

**No.** Members are ordered by amount. `temporal_basis` is `NONE`, no window is
recorded, no publication date was read by the extractor, and `observed_at` is
NULL on every input.

---

## 4. Boundaries, and what this Signal does not say

It supports exactly this: *among division-90 award notices in this bounded query,
the largest EUR total value exceeded the smallest by 686 545.02 EUR.*

It does not support:

- **growth, decline or any trend.** Three notices all published on one day are
  `NON_TEMPORAL`, and H-37 blocks a temporal reading regardless;
- **willingness to pay.** The magnitude is a spread between two contracts, not a
  price anyone offered or accepted. That named buyers paid named amounts is
  established; that a comparable buyer would pay a comparable amount for a
  different product is not, and the family exists to keep those apart;
- **market representativeness.** The cohort is every qualifying notice **in this
  query**, not in the market.

---

## 5. What was not created

| | |
|---|---|
| Claims | **0 created**, 7 unchanged, none citing a TED Signal |
| Evidence | **0 created**, 7 unchanged, none referencing a TED Signal |
| Opportunities | 0, unchanged |
| ReliabilityAssessments | 0, unchanged |
| Embeddings | 0, unchanged |
| Scores | 0, unchanged |
| Gateway duplicate-row defect | **not fixed**, still backlog |

### Counts at mission end

| | Start | End |
|---|---|---|
| RawRecords | 15 (3 TED) | **23 (11 TED)** |
| NormalizedRecords | 15 (3 TED) | **23 (11 TED)** |
| Signals | 7 (0 TED) | **8 (1 TED)** |
| Claims / ClaimRevisions | 7 / 7 | 7 / 7 |
| Evidence | 7 | 7 |
| Opportunities / Reliability / Embeddings | 0 | 0 |

---

## 6. Did all gates pass?

**Yes, every one, checked by exit code rather than by reading the tail of the
output.**

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
contracts generate --check                                   exit 0
sros-source render --check                                   exit 0
render_review_results --check                                exit 0
render_signal_coverage --check                               exit 0
sensitivity --check                                          exit 0
migrate --plan                                               exit 0
ruff check / ruff format --check                             exit 0
mypy                              144 source files           exit 0
assert_registry_grants_nothing                               exit 0
```

`quality-gates.md` was reviewed and **not** changed: no gate was added, removed
or altered by this mission.

### Five guards were inverted, and one of them has nowhere left to go

The `TestNothingWasCollected` family asserts what TED has **not** reached yet. It
was inverted in 1.15.7 (raw records appeared), in 1.15.8 (normalized records
appeared), and now again: a TED **Signal** exists.

It now asserts that nothing **interprets** a TED signal — no Claim cites one, no
Evidence references one — which is this mission's own stop condition. The comment
records that this is the **last** move available: there is no stage below
Evidence that TED has not reached, so when this stops being true the assertion
should be deleted rather than moved a fourth time.

---

## 7. Final TED stage state

```text
SOURCE AUTHORIZATION      READY   local-private-research-v1, review v2, 4/4 conditions
RESOURCE READY            YES     notices/eforms-contract-and-award
COLLECTOR V1.1            YES     ted-search-api@1.1.0, exact decimals, CPV narrowing in the query
RAW DATA                  YES     11 records, 3 at 1.0.0 and 8 at 1.1.0
NORMALIZER                YES     ted-search-api-notice@1.0.0, accepts both collector versions
NORMALIZED DATA           YES     11 records, all PARTIAL (the ceiling while H-37 is open)
TRANSACTION_VALUE SIGNAL  YES     1, support 3, 686545.02 EUR, procurement-value-contrast@1.0.1

H-36A  NOT ESTABLISHED    H-36B  NOT ADDRESSED    H-37  OPEN    H-38  OPEN
```

---

## 8. Next mission

At least one valid real TED Signal exists, so the brief's §43 branch applies:

> **Sprint 1 — Mission 1.15.11 — TED Transaction Signal → OBSERVED Claim +
> Evidence V1**

Three things that mission will have to settle before it writes anything, all
visible from here:

1. **What an OBSERVED Claim over this Signal is allowed to say.** §4 above is the
   boundary, and a Claim is exactly the layer where a spread quietly becomes a
   market size if nobody stops it.
2. **What a Claim does with `observed_at` being NULL.** H-37 is open, the Signal
   is `NON_TEMPORAL`, and a Claim asserting anything dated would reintroduce the
   assumption three missions have refused.
3. **Whether support 3 is enough to interpret**, which is a different question
   from whether it was enough to derive. The derivation floor exists to stop one
   observation being called a contrast; an interpretation floor, if there is one,
   protects something else.
