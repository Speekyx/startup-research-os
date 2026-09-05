# Mission 1.62 — Anchor Operational Closure & Partner Package Completion V1

**Outcome: `ANCHOR_ENQUIRY_REQUIRED_PARTNER_PACKAGES_COMPLETE`.** Three complete
packages, no qualified apparatus, no pair compared, ranked or selected.

---

## 0. Three complete packages, three different failures

Mission 1.60 left all three candidates at a documentation wall. That told us
nothing about any of them. Each is now decided on its own merits:

| candidate | package | individual | decided by |
|---|---|---|---|
| LeakIX | `COMPLETE` | `NOT_QUALIFIED` | B2, last-seen timestamp semantics |
| ONYPHE | `COMPLETE` | `UNRESOLVED` | four partial slots |
| Shadowserver | `COMPLETE` | `NOT_QUALIFIED` | B4, a per-requester frame |

**Two complete packages concluding NOT_QUALIFIED is the mission succeeding.**
Complete means every slot has an answer; qualified means every slot passes.

## 1. Baseline

Verified live, no drift: 325 / 325 / 33 records, 44 Claims, 45 revisions, 58
Evidence, 1 INFERRED Claim, 1 threshold, 1 derivation, 0 refusals, `SUPPORTS 57 /
CONTRADICTS 1`, 0 Claims carrying both, 4 reliability assessments, 0 independence
groups, `scoring.scores` absent, head `0035`, main `8f2ad45`.

## 2. It scans everything and can show us only ours

Shadowserver performs its own daily internet-wide scanning. Its reporting API:

> You only get the data on the networks you are responsible for. You will not be
> able to get data on other networks or systems.

Access is limited to members of the reports group; a general requester cannot
obtain internet-wide results. Its scan API requires special authorization and is
documented over SSL scan data.

**Its observation-window selector is the cleanest of the three candidates** — an
explicit `date` parameter taking a date or a range — and it is recorded as a
`PASS`, because a gate is judged on its own question.

And its **frame is the requester's own networks**, so two requesters retrieve two
different populations and no proposition about the internet can be witnessed
through it. That is a `FAIL` rather than an `UNKNOWN`: an affirmative documented
statement, not a silence.

**This is a rule the arc had not yet named.** `FRAME_INSIDE_THE_DEFINITION`
covers an apparatus measuring within its own reach.
`LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS` separates who produced an
observation from which addresses were reached. Neither covers a global **measured**
frame with a per-requester **retrievable** one.

## 3. B2 has now decided three apparatuses

LeakIX documents three date fields: an indexing date, a first-detection date and a
last-detection date. None is an observation event.

A window filter over a last-detection field selects hosts whose **last** detection
fell inside the window — so a host detected both before and after it is missing
from the set. That is Mission 1.59's failure exactly, in a third apparatus.

**Its B3 passes**, on a documented SSH banner field, and the pass is recorded even
though the package fails. §43 forbids letting one compensate for the other: a
perfect banner with no pre-retrieval observation-window selector still fails.

Across 1.59, 1.60 and 1.62, observation-addressability is the gate this class
fails on, and for the same reason each time — a maintained current-state view is a
good product and the wrong temporal object.

## 4. An ambiguity that was not resolved favourably

ONYPHE's B3 now **passes**: the data model documents a `data` field holding the
raw application response, full-text searchable up to 1 MB, kept distinct from a
normalised `summary`. That closes the field-name gap Mission 1.61 recorded.

Its B2 turns on one sentence. The timestamp field is documented as the moment the
data was **collected**, and in the same sentence as allowing tracking of when a
service was **last observed**. Those are two different temporal objects, and the
wording supports both readings.

**Neither was chosen.** Resolving an ambiguity in the direction that keeps a
candidate alive is the refusal this arc has made four missions running.

It also documents a scanner node id and country **per record**, with weekly scans
alternating origin country — so its vantage is `MULTI_VANTAGE_SEPARABLE`, which is
more than the anchor publishes about itself. That asymmetry is recorded as a fact
about two documentation sets and not as a preference.

## 5. The anchor: one downgrade, one reclassification

Ten topics: **2 answered, 4 partial, 4 unknown.** A8 stays `PARTIAL`.

**FRAME moved `ANSWERED` → `PARTIAL`.** Separating eligible frame from attempted
frame showed only the first is documented: the address range is declared, and
which addresses were actually probed in a cycle is not.

**RETRY moved `PARTIAL` → `UNKNOWN`.** The API documents client-side throttling
and retry parameters. Those govern the **client retrying the API**, not the
**scanner retrying a probe**. Answering a measurement question with a
transport-library setting was the easiest mistake available here.

Sampling, vantage and missingness remain unknown, and the data collection policy —
the most likely remaining first-party document — closes none of them.

## 6. Two retrieval-surface constraints nobody knew

**The default surface, confirmed verbatim.** The API reference states that if the
index parameter is not supplied, the search is conducted using the latest publicly
available internet scan data. Mission 1.61 inferred this bound; it is now the
provider's own sentence, and it is why the second new registry rule exists.

**The count endpoint is an estimate.** Below a thousand results it is exact; above
it, documented as an estimate with an error margin not exceeding three per cent.

The construct is a count of distinct addresses across public IPv4 and will exceed
a thousand. A threshold evaluated against that endpoint would compare a bound
against an error band that could decide the direction — **a `SUPPORTS` or
`CONTRADICTS` produced by the estimator rather than by the world.** That is the
artefact-recorded-as-a-finding failure this layer must not have.

It bounds **how** the value must be obtained, not whether it can be: the
documented download endpoint retrieves without pagination limits, over which an
exact distinct count is computable.

## 7. The enquiry was not edited and no duplicate hash was manufactured

All seven questions compared against the updated matrix. All seven
`STILL_UNRESOLVED`. So v1 remains current, no v2 was cut, and Mission 1.61's hash
stays authoritative:

```
APPROVE MISSION 1.61 ENQUIRY 310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4
```

**The count-estimate finding was deliberately not added to it.** It is documented
rather than missing — an answered constraint, not a question — and adding it would
ask the provider to restate its own documentation.

The validator hashes the frozen enquiry on every run. Three of the probe's
violations edited it, and all three were caught.

## 8. A contact page, and no invented address

A first-party legal page carries a printed contact instruction. The address is
served through an obfuscation mechanism, so the retrieval returned a placeholder
and **the address was not resolved**.

Recorded as `FIRST_PARTY_CONTACT_CHANNEL_NOT_ESTABLISHED`, beside the page that
carries it. A valid question and a valid channel are two different facts, and
guessing would fabricate a fact about a provider. The operator can read it in a
browser in one step.

## 9. The brief's own instruction caught an error in the brief

§21 and §22 each attributed a blocker to a candidate and said *resolve exact
candidate from artifact*. Doing so found both attributed the other way round:

| blocker | brief said | artifact says |
|---|---|---|
| vetted / private API | ONYPHE | **Shadowserver** |
| 30-day field removal | LeakIX | **ONYPHE** |

Both were pursued against the candidate that actually carries them.

## 10. Registry now thirteen

| requirement | from |
|---|---|
| `THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME` | 1.62 |
| `DEFAULT_DATA_SURFACE_MUST_NOT_OVERRIDE_QUALIFIED_EXPOSURE_PATH` | 1.62 |

The second governs **implementation** where `OBSERVATION_ADDRESSABLE_EXPOSURE`
governs **selection**: a collector must bind explicitly to the qualifying surface,
because omitting the selector is silent.

Earlier missions' records were **not rewritten**.

## 11. What did not happen

```
measurement queries   0        trials         0
target counts         0        purchases      0
host records          0        facets         0
banners               0        downloads      0
enquiries sent        0
first-party requests  24 of 24  (5 returned nothing usable, counted anyway)
```

0 canonical mutations, 0 sources registered, 0 governance reviews, 0 threshold
registrations, 0 Claims, 0 Evidence, 0 reliability values, 0 independence groups,
0 Scores, 0 model calls, 0 embeddings. The Mission 1.56 Claim is untouched, the
profile is still `UNCALIBRATED`, Problem-Family is still `PARKED`.

## 12. Verification

| | |
|---|---|
| CI gates | 30, all green |
| bare-python | 1656 tests across 9 packages |
| pytest | 3310 tests, all suites passed |
| database after the pytest run | unchanged across 29 tenant tables and 17 global tables |
| validator probe | 126 deliberate violations, 126 caught |

The validator refused this mission's own records twice before they were right: a
genuinely blank package slot, and a field enumerating the vocabulary it forbids.

**One pytest failure occurred and it was diagnosed rather than re-run.** Two
suites were started against the same live database, and the registry-snapshot
stability test failed on a `core.workspaces` row named `test signal-probe` that
appeared between its two consecutive reads. That row belongs to the other run's
own fixture, and the test exists precisely to notice a concurrent mutation — its
docstring says that if it is flaky the check is worthless. The cause was operator
concurrency during verification, not a change in this mission. Re-run once with
nothing else against the database: exit 0, no residue, canonical counters at
baseline.

## 13. Next

**`STOP_ON_ENQUIRY_CHECKPOINT`.** §62 permits Mission 1.63 to proceed on qualified
apparatuses without the anchor only if **two** independently qualify. Zero do.

**A8 was not weakened to get past it.** The alternative to stopping was declaring
A8 reviewable with sampling and vantage unanswered.

Four precisely named documentation reads would move the most: the anchor's indices
endpoint, whether an ONYPHE record is appended per scan or maintained per service,
that candidate's scanned-ports list, and which fields it removes after thirty days.
Each has a known URL and none needs an enquiry.
