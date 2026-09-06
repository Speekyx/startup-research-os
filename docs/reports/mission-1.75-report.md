# Mission 1.75 — Acquisition Gateway use-profile integrity

**Primary outcome: `GATEWAY_USE_PROFILE_SCOPING_REPAIRED`.**

The profile-blindness Mission 1.15.7 found and Mission 1.17 grew is closed. Governance
reads now require an explicit `use_profile`, there is no default, and no fact crosses a
profile boundary.

---

## The 45 answers

| # | question | answer |
|---|---|---|
| 1 | main commit at start | `5e3c4e6` |
| 2 | branch | `sprint-1/mission-1.75` |
| 3 | affected routes | `GET /api/v1/sources`, `GET /api/v1/sources/{source_id}`, `GET /api/v1/sources/{source_id}/eligibility` — **three, not two** |
| 4 | pre-change cause | `JOIN registry.source_eligibility e ON e.source_id = s.id` with no `use_profile_id` predicate, against a view keyed `(source_id, use_profile_id)`; plus a conditions query joining every non-superseded review regardless of profile |
| 5 | why profile-blind | the view became profile-keyed in Mission 1.15.5 and the HTTP layer was not re-checked. Mission 1.17 recorded it as a defect because choosing the profile is a design decision with no default |
| 6 | alternatives considered | local default, commercial default, environment default, workspace-derived, first available review, fall back to the other profile — all refused, see the design artifact §3 |
| 7 | why explicit required | both profiles are real deployments with different verdicts for the same sources; any default answers a question the caller did not ask and looks like an answer |
| 8 | default profile | **none** |
| 9 | missing profile | **422**, FastAPI's required-parameter refusal |
| 10 | unknown profile | **422 `contract_violation`**, validated against `registry.use_profiles` |
| 11 | `/sources` duplicates before | **8** sources duplicated (37 view rows for 29 sources) |
| 12 | `/sources` duplicates after | **0**, under every profile |
| 13 | one source, two reviews, twice? | no — the profile is a join predicate |
| 14 | can LOCAL read COMMERCIAL's verdict? | no |
| 15 | can COMMERCIAL read LOCAL's verdict? | no |
| 16 | conditions union across profiles? | no |
| 17 | requested profile has no review | source still listed; `approval_state: null`, `collector_eligible: false`, one blocking reason naming the profile |
| 18 | response identifies its profile | yes — envelope **and** each source object |
| 19 | `use_profile` in OpenAPI as required | yes, asserted against the rendered `/openapi.json` |
| 20 | callers updated | none needed: **no production HTTP caller exists**. `read_sources` in the acquisition registry repository had a hard-coded commercial profile and now takes one explicitly |
| 21 | caller profile that could not be established | **none**. `read_sources` had zero callers, so nothing had to be guessed |
| 22 | historical RawRecords backfilled | **no** |
| 23 | new RawRecords still record use_profile | **yes**, `build_raw_record` untouched |
| 24 | migration added | **yes, one**: `0036_grant_use_profile_vocabulary.sql` — a single `GRANT SELECT`. See below |
| 25 | canonical counters before/after | identical, see the baseline table |
| 26 | registered sources before/after | **29 / 29** |
| 27 | Globalping state before/after | unchanged: R1 `R1_PASS_PROVIDER_DECLARED_NO_REDIRECT`, R2 PARTIAL, **11 PASS / 1 PARTIAL / 0 FAIL**, `COUNTERPART_UNRESOLVED` |
| 28 | research API requests | **0** |
| 29 | external provider contacts | **0** |
| 30 | model calls | **0** |
| 31 | embeddings | **0** |
| 32 | Opportunities changed | **no** (1 / 1 / 7) |
| 33 | scores changed | **no** (none exist) |
| 34 | independence groups changed | **no** (0) |
| 35 | violation probe | **14 attempted, 14 caught, 0 escaped** |
| 36 | positive controls | **3 of 3** |
| 37 | bare-python tests | **3029** |
| 38 | pytest | green across 9 packages |
| 39 | ruff format | clean |
| 40 | ruff check | clean |
| 41 | mypy | 197 files, no issues |
| 42 | CI-equivalent gates | **48 of 48** |
| 43 | primary outcome | `GATEWAY_USE_PROFILE_SCOPING_REPAIRED` |
| 44 | remaining limitations | below |
| 45 | recommended next mission | **1.76 — Opportunity Evidence Breadth Prioritization V1** |

## The migration, explained before it was written

§11 asked for a stop-and-explain before any migration. This one is a **single
`GRANT SELECT`** and no DDL.

- **Missing fact.** The runtime role could not read `registry.use_profiles`, so the
  Gateway could not validate a submitted profile against the canonical vocabulary.
- **Why existing structures cannot express it.** Profile identifiers also appear in
  `source_eligibility.use_profile_id` and `source_policy_reviews.assessed_use_profile`,
  but both enumerate the profiles that have **been used**, not the profiles that are
  **registered**. Validating against them would refuse a registered profile that no source
  has been reviewed under — the state every new profile begins in — and would make the
  vocabulary a function of review data.
- **Why not a list in Python.** Two implementations of one vocabulary, and it would fail
  closed against a third profile the registry knows.
- **Historical-data consequences.** None. No row is inserted, updated or deleted. Every
  other table in `registry` was already readable by the runtime role; `use_profiles` was
  the one migration 0021 created and forgot to grant, and nothing noticed because nothing
  read it at runtime.

The runtime role still cannot write anywhere in `registry`, which is what keeps source
review administered through `sros-source`.

## Three findings the audit produced

**The defect reached a third route.** The brief named two. `GET /sources/{id}` had the
same unscoped join **and** an unscoped review lookup, which made it the worst of the
three: it returns the review body and its evidence URLs, so an arbitrary profile's row
there does not merely mislabel a verdict — it hands back the documents behind an
assessment the caller is not asking about.

**`collector_enabled` is profile-relative too.** It is a column on the source carrying its
own `collector_use_profile`, and the database trigger checks eligibility under *that*
profile. Served flat beside a scoped verdict it reads as "enabled for you". `ted-eu` is
enabled under local and appears under commercial, where it is not eligible — so the
re-pointed tripwire's first form, *enabled implies eligible*, was still asserting a
property the database never had. The route now returns `collector_use_profile` and
`collector_enabled_for_requested_profile` beside the flag.

**A hard-coded default was hiding in dead code.** `read_sources` in the acquisition
registry repository wrote `commercial-multi-tenant-research-v1` into its SQL. Nothing
called it, so nothing had chosen that profile — and the first caller would have inherited
an answer it never asked for. It takes an explicit profile now.

## The two tripwires, re-pointed and not deleted

Mission 1.17 encoded the defect as failing assertions so that fixing it would break them.
Both were re-pointed onto the repaired property, with the history kept.

The duplicate-set assertion listed eight source ids and grew with every profile alignment.
It is now **relational**: no profile returns a source twice. A test pinned to eight names
would fail the next time the registry legitimately grows, which is a test asserting that
the project may never progress.

The conditions assertion pinned `fred` at six — the union of three conditions under each
of two profiles. It is now the relation that matters: each profile returns its own
conditions, and the count is strictly less than the union. Worth noting why the old
number was dangerous: the six collapsed to **three distinct `condition_key`s**, so a
reader deduplicating by key would have seen a plausible answer assembled from two
profiles' facts.

## Three places that pinned a moving fact

Applying migration 0036 broke **three** assertions comparing the **live** migration head
against the literal `0035_refusal_provenance`: two CI gates and one pytest test. Each was
asserting a historical fact — *this mission created no migration*, *this record describes
the newest migration*, *0035 is applied* — through a measurement of the present, so any
later migration would break them.

The third only surfaced on the full pytest run, and only because its exit code was
checked rather than trusted: an earlier background run of the same command reported
success, and the pass line was missing from its output. Re-running to resolve the
ambiguity is what produced the failure.

Repaired the same way: each now asserts that the migration it **names** exists and that
its own record still says what it said. Being the newest was never the property that made
any of them correct.

## Cross-profile leakage matrix

All ten cases covered, and **five are constructed rather than found**. The seeded registry
gives CASE A for free — commercial has reviewed every source — and cannot give CASE B at
all, because no source is local-only. Skipping the direction the data happens not to lean
would have left the leak that direction could carry untested.

| case | covered by |
|---|---|
| A local-only review, commercial requested | live registry + constructed |
| B commercial-only review, local requested | **constructed fixture** |
| C both profiles, different verdicts | **constructed fixture** |
| D same `condition_key`, both profiles | **constructed fixture** |
| E one APPROVED, one REQUIRES_REVIEW | **constructed fixture** |
| F missing profile | all three routes |
| G unknown profile | all three routes |
| H multiple reviewed profiles | one row, both profiles |
| I zero conditions under one profile | **constructed fixture** |
| J two profiles sequentially | repeated and alternating |

The fixtures obey the rules they test around: the registry refuses an approval with no
evidence and a condition satisfied by a bare boolean, so the fixture inserts as
`REQUIRES_REVIEW`, adds evidence, clears the condition through a verification record and
then promotes. They also purge **before** inserting, because a setup that raises halfway
leaves a row behind and the next run then fails on something unrelated to what it tests.

## The probe, and the two escapes it found

Fourteen mutations, each reintroducing one form of profile-blindness into the router and
requiring the suite to fail. **Two escaped on the first run**, and both were the ones §7
and §17 warn about:

- resolving profile validity from `source_eligibility` instead of the vocabulary;
- hard-coding the two profile names.

Both pass against a suite that only ever names the two live profiles. Closing them needed
a fixture that **registers a third profile with no reviews** — the only case that tells
the three implementations apart, and the state every new profile begins in.

Final: **14 attempted, 14 caught, 0 escaped, 3 of 3 positive controls**, the router
restored byte for byte.

## RawRecord provenance

    NEW_RECORD_PROFILE_PROVENANCE = EXPLICIT
    HISTORICAL_PROFILE_PROVENANCE = NOT_ESTABLISHED_AND_NOT_BACKFILLED

`build_raw_record` is untouched and still writes `use_profile` on new records. No
historical record was backfilled, no migration populates one, and nothing infers a profile
from review version, eligibility or collection date. Inventing them would create
provenance that was never recorded.

## Canonical state

| | before | after |
|---|---|---|
| RawRecords / Normalized | 325 / 325 | 325 / 325 |
| Signals | 33 | 33 |
| Claims / revisions | 44 / 45 | 44 / 45 |
| Evidence | 58 | 58 |
| INFERRED Claims | 1 | 1 |
| threshold_registrations | 1 | 1 |
| claim_derivations | 1 | 1 |
| proposition_evaluation_refusals | 0 | 0 |
| ReliabilityAssessments | 4 | 4 |
| EvidenceIndependenceGroups | 0 | 0 |
| Opportunities / revisions / links | 1 / 1 / 7 | 1 / 1 / 7 |
| Embeddings | 0 | 0 |
| Registered sources | 29 | 29 |
| use_profiles | 2 | 2 |

The test fixtures move the source and review tables during a run and delete on the way
out, and the teardown asserts the delete removed what the setup added. The migration head
moved from `0035_refusal_provenance` to `0036_grant_use_profile_vocabulary`, which is the
only intended change to the database.

## Remaining limitations

- **No caller is forced to choose correctly.** The API refuses a missing profile; it
  cannot tell whether the caller named the one they meant. There is still no
  authentication, so naming a profile is not being entitled to it.
- **`sros-source` and the CLI reporting paths were not audited** beyond the one function
  that carried a hard-coded default. They were profile-aware from Mission 1.15.6; that was
  not re-verified here.
- **The response shape grew by three fields.** Any consumer reading these bodies gains
  `use_profile`, `reviewed_under_requested_profile`, `collector_use_profile` and
  `collector_enabled_for_requested_profile`; none is removed, but a strict schema
  validator downstream would see new keys.
- **Sources unreviewed under a profile are now listed** where they were previously absent.
  That is the intended fix, and it changes what a caller counting rows sees.

## Next

**Mission 1.76 — Opportunity Evidence Breadth Prioritization V1.** Measure which existing
subjects and opportunity packets are closest to gaining genuinely different evidence
dimensions, and rank the next bounded evidence-completion move by missing dimension,
source availability, governance readiness, collector availability, independence potential,
commercial relevance and expected information gain. **It must select no acquisition merely
because a source exists.**

**Mission 1.76 was not started.**
