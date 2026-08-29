# Mission 1.4 — Completion Report

**Mission:** Conditional Source Eligibility Enablement — World Bank, Eurostat & FRED Compliance Capabilities
**Sprint:** 1
**Date:** 2026-08-29
**Branch:** `sprint-1/mission-1.3`
**Outcome:** 9 conditions inventoried · 8 satisfied by verifiers · **2 sources collector-eligible** · **0 collectors implemented, 0 enabled, 0 records collected**
**Introduces:** migration `0007_condition_verification`, the `sros_acquisition.compliance` package, `ConditionVerificationResult` / `AttributionElement` / `ResourceContentOrigin`, [`source-condition-gap-analysis-v1.md`](../data/source-condition-gap-analysis-v1.md), [`acquisition-authorization-v1.md`](../data/acquisition-authorization-v1.md), [`source-compliance-v1.json`](../data/source-compliance-v1.json), [ADR-016](adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md)

---

## 1. The nine-condition inventory

Read from the canonical catalog and the database, not reconstructed from the
brief. Full analysis:
[`source-condition-gap-analysis-v1.md`](../data/source-condition-gap-analysis-v1.md),
written **before** any code, so the capabilities could be checked against what
the conditions say rather than against what was convenient to build.

| # | Condition id | Source | Key | Verification | Detail |
|---|---|---|---|---|---|
| 1 | `b2de8714…a4f6` | `world-bank` | `attribution-surface` | `CAPABILITY` | `source-attribution-display` |
| 2 | `84abbfa8…21e3` | `world-bank` | `dataset-licence-allowlist` | `CAPABILITY` | `dataset-licence-filter` |
| 3 | `265cf376…05eb` | `world-bank` | `microdata-excluded` | `ACCESS_METHOD` | `indicators-api-only` |
| 4 | `9aa31970…a2ae` | `eurostat` | `attribution-surface` | `CAPABILITY` | `source-attribution-display` |
| 5 | `d7627b89…8483` | `eurostat` | `geographic-exclusion` | `CAPABILITY` | `eurostat-geographic-filter` |
| 6 | `feda2c31…ecfb` | `eurostat` | `trade-data-exclusion` | `CAPABILITY` | `eurostat-trade-exclusion` |
| 7 | `217b656c…dd91` | `fred` | `fred-api-key` | `CONFIG_REFERENCE` | `FRED_API_KEY` |
| 8 | `7aab7679…29f9` | `fred` | `fred-endorsement-notice` | `CAPABILITY` | `source-attribution-display` |
| 9 | `25aa1cb3…f206` | `fred` | `copyrighted-series-excluded` | `CAPABILITY` | `fred-copyright-series-filter` |

## 2. Classification

| Classification | Count | Which |
|---|---|---|
| `MACHINE_VERIFIABLE` | **8** | 1–6, 8, 9 |
| `CONFIGURATION_DEPENDENT` | **1** | 7 — `FRED_API_KEY` |
| `HUMAN_CONFIRMATION` | 0 | — |
| `EXTERNAL_VENDOR_ACTION` | 0 | — |
| `NOT_IMPLEMENTABLE_YET` | 0 | — |

Zero vendor actions is not luck. Mission 1.3 left the vendor-action sources
(Reddit, Product Hunt, Hacker News, Google Trends, Stack Exchange) in
`REQUIRES_REVIEW`, so they never reached a condition list.

**Eight obligations were deliberately left out of code** — the ODbL share-alike
rule for an activity nobody has designed, the FRED trademark and hostname
prohibitions, the "or records per-owner permission" half of condition 9, the
Eurostat disclaimer whose wording is not in the evidence, and the open questions
each review recorded. §5 of the gap analysis lists each with the reason it stays
out. §4 of the brief forbids translating a legal sentence into a machine rule
Mission 1.3 did not already state, and this is where that rule bit.

## 3. Compliance capability architecture

```text
services/acquisition/python/sros_acquisition/compliance/
    config.py         obligations as governance data, never branches
    attribution.py    what attribution follows the data, and how it survives
    resources.py      which resources the approval actually covers
    credentials.py    whether a key is configured, never what it is
    capabilities.py   named capabilities, and the checks that make them real
    verification.py   running a verifier against a Mission 1.3 condition
    authorization.py  what a collector must hold before it may run
    repositories.py   recording a verification, syncing the gate's boolean
```

**Nothing here grants anything.** Every rule is a restriction, every optional
field defaults to the strict value, and a source, resource or element that was
never established is refused. The package imports no network client and CI
asserts it.

Six capabilities were implied by the nine conditions, deduplicated to **five
registered capabilities plus one access restriction**:

| Capability | Conditions | Mechanism |
|---|---|---|
| `source-attribution-display` | 1, 4, 8 | attribution rendering, parameterised by three different obligations |
| `dataset-licence-filter` | 2 | licence allowlist |
| `indicators-api-only` | 3 | access-method restriction + dataset-family exclusion |
| `eurostat-geographic-filter` | 5 | geography allowlist |
| `eurostat-trade-exclusion` | 6 | enumerated exclusions |
| `fred-copyright-series-filter` | 9 | note-marker exclusion |

Three names carry a source. Those names are Mission 1.3's and were **not**
renamed — a condition whose key changed would look like a new requirement. What
is shared is the implementation: `eurostat-geographic-filter` binds that name to
a generic geography-allowlist check, and a second source needing one would bind
to the same function.

No capability was built that no condition names, and the validator fails if one
appears (§5: no unused abstractions).

### A capability is checked, not registered

Registering a capability is not evidence that it exists. Each check runs the real
gate against the source's real configuration and asserts, for every case the
review evidence names, that it answers correctly — **including allowing its own
control case**. A filter that denied everything would otherwise satisfy every
denial assertion, and would be a permanent refusal dressed as a check.

## 4. Attribution architecture

All three sources require attribution and each requires something different,
which is why this is a model rather than a constant.

| Source | Required elements |
|---|---|
| World Bank | `SOURCE_CREDIT` (fixed) · `LICENCE_IDENTIFIER` (supplied, per dataset) · `MODIFICATION_STATEMENT` (supplied, when modified) |
| Eurostat | `SOURCE_CREDIT` (fixed) · `DATASET_DOI` · `ACCESS_DATE` · `MODIFICATION_STATEMENT` · `DISCLAIMER` (the last four supplied) |
| FRED | `EXACT_NOTICE` (fixed, verbatim) |

**A required element cannot be omitted.** Rendering raises rather than dropping
it; there is no partial rendering, because a notice missing half its obligation
looks like attribution and is not.

**The FRED sentence is reproduced byte for byte**, registered trademark symbol
included, and a test compares it literally. A validator additionally asserts
that every exact notice appears in the evidence record that prescribed it — so
the wording is traceable to the document rather than to us.

**An obligation survives transformation.** `AttributedArtifact.derive` carries
obligations forward and has no parameter that removes one; combining two
artefacts unions their obligations. Raw record → normalized → evidence → claim →
result is tested end to end, including that a derived artefact with incomplete
facts still refuses to render.

**The Eurostat disclaimer was not written.** Its exact wording is not in the
retrieved evidence, so it is a required *supplied* element and rendering refuses
without it. Composing the sentence would have been the opposite of preserving a
required notice exactly.

## 5. Licence and resource-scope architecture

Six rule kinds, each demanded by an actual condition. Not a rule language: a
general expression grammar in configuration is exactly where a vague legal
sentence gets encoded as a boolean.

| Rule | Denies |
|---|---|
| Content origin | `THIRD_PARTY`, and `UNKNOWN` where licensing scope matters |
| Licence allowlist | A licence outside the list, and one never recorded |
| Dataset family | An excluded family, and an unrecorded one |
| Geography allowlist | A geography outside the set, and a resource naming none |
| Enumerated exclusion | A named carve-out, including one whose other dimension is unrecorded |
| Note marker | A third-party ownership marker, and notes never read |

`ResourceContentOrigin` is `PLATFORM_LICENSED | THIRD_PARTY | UNKNOWN`. The
third exists because it is the common case for an aggregator and must fail
closed.

**One deliberate conservatism, recorded rather than silent.** The Eurostat
geography allowlist is EU-27 plus EFTA, **without** acceding and candidate
countries. The terms permit their data; the set changes and the copyright notice
does not enumerate it. Stricter than required, never more permissive, and
widening it needs a re-read and a recorded decision rather than a code edit.

## 6. Credential architecture

The registry stores a configuration **key name**. `credential_status` reads
presence and emptiness and answers `CONFIGURED` / `NOT_CONFIGURED`. The returned
object holds the name and a boolean and **has no field a value could occupy**,
so it cannot leak from a `repr`, a log line, a JSON response or an exception —
it was never in it.

Three layers guard it: the model refuses a reference that looks like a value, a
CHECK constraint refuses credential-shaped text in a verification's `reason` or
`reference`, and a sentinel test asserts that a value set in the environment
appears in no verification, no eligibility output and no authorization context.

An empty variable counts as `NOT_CONFIGURED`. That is what a half-finished
deployment leaves behind, and treating it as present would move the failure from
a gate that explains itself to a 401 from a third party.

## 7. Condition verification

Migration `0007` adds `registry.source_condition_verifications`, an append-only
log recording which condition, which verifier, at which version, when, the
result, why and what was inspected.

`source_review_conditions.satisfied` stays where it is and keeps the meaning the
eligibility view already gives it — the view is untouched. What changed is that
a `BEFORE` trigger now refuses to set it true with no `SATISFIED` verification
record behind it, **whoever issues the UPDATE and from whatever client**.
Clearing back to false is deliberately unguarded: failing closed must never need
permission.

Results are `SATISFIED | UNSATISFIED | UNKNOWN | NOT_APPLICABLE`. Only
`SATISFIED` clears. `UNKNOWN` blocks exactly as a failure does and is filtered
out in one function rather than by each caller, so promoting it would mean
editing that function rather than forgetting a condition somewhere.

| Verification kind | Verifier | Establishes |
|---|---|---|
| `CAPABILITY` | `capability:<name>` | Registered, and its conformance check passes |
| `ACCESS_METHOD` | `access-restriction:<name>` | The registry holds exactly the approved profiles, and the excluded material is refused |
| `CONFIG_REFERENCE` | `credential-availability` | The named key is present and non-empty |
| `RETENTION_LIMIT` | *none* | Nothing. `UNKNOWN`, and it blocks |
| `HUMAN_CONFIRMATION` | `human-confirmation` | Nothing, unconditionally. `UNKNOWN` |

`RETENTION_LIMIT` has no verifier because no condition uses one. Building it
would be an unused abstraction, and `UNKNOWN` is the honest answer for a check
that does not exist.

**No verifier writes a human confirmation.** The branch returns `UNKNOWN` before
any argument is consulted, and the validator probes it on every source.

### What a `CAPABILITY` verification does not establish

Stated plainly, because it is the load-bearing limitation of the whole layer.

Seven of the nine conditions are phrased as claims about a **collector**, and no
collector exists. A `CAPABILITY` verification asserts exactly what the contract
says the value means: *a named product capability is implemented and enabled*.
It asserts the gate exists, is configured, and refuses what it must. **It does
not assert that a collector went through it.**

The gap is closed structurally — a collector may only run with an authorization
context and the rules travel inside it — and the verification reasons say so in
their own text. **Mission 1.5 owes a conformance test** that its collector
reaches every resource through `authorize_resource` and has no other path to a
URL. Until then the guarantee is architectural, not observed. Recorded in the
gap analysis, in ADR-016, in `docs/CLAUDE.md` and here.

## 8. `AcquisitionAuthorizationContext`

What a collector receives: source and review version, approved access paths with
credential key names and rate-limit metadata, the resource scope, the resolved
retention, the attribution obligation, the data-minimisation profile, and the
verification snapshot the authorization rests on.

`authorize_resource(descriptor)` is the only sanctioned way to reach a specific
dataset. Holding the context permits nothing on its own.

**`build_authorization` runs the canonical gate and raises when it does not
pass.** That is the enforcement mechanism: not a flag the collector is asked to
check, but the absence of the object it needs. A source that passes the gate and
has no compliance entry is also refused — there would be no obligation, no rules
and no profile to hand a collector, and handing one nothing is not the same as
handing it permission.

Rate limits are exposed as `known: false` for all three sources, because none
documents one. §29 forbids inventing a figure a collector would then trust.
Retention is governance input: the context carries the resolved rule with the
stricter constraint already applied, and there is no setter.

## 9. Source-by-source results

### World Bank — **collector-eligible**

All three conditions satisfied. Attribution renders credit, the per-dataset
licence and a modification statement, and refuses without the supplied ones. The
licence allowlist accepts CC-BY-4.0 and ODbL-1.0 and denies an unrecorded
licence. The access restriction is verified against the registry: exactly the
`indicators-api-v2` profile and no other, with the Microdata Library excluded
and an unclassified dataset denied.

### Eurostat — **collector-eligible**

All three satisfied. Attribution requires the dataset DOI and the access date
per retrieval and cannot default either. Geography is restricted to EU-27 plus
EFTA, denying the USA, Japan and China the notice names, and denying a resource
that states no geography. The two named trade carve-outs are enforced, including
the case where one dimension is unrecorded.

### FRED — **design-eligible, not runnable**

Two of three. The exact notice renders verbatim; the copyrighted-series filter
denies a series marked `Copyright` **and** a series whose notes were never read.
`FRED_API_KEY` is `NOT_CONFIGURED`, so the source is blocked by exactly one
reason.

This is the §24 distinction, working: every policy capability its approval
requires exists, and the runtime credential does not. The canonical gate still
refuses it, and no `design_eligible` flag is consulted before building an
authorization.

### The other ten

Untouched. None has an approving review, so no capability built here can move
one: a test hands every non-approving source a fully satisfied condition set and
asserts each stays blocked by its state.

## 10. Eligibility before and after

| Source | Mission 1.3 | Mission 1.4 (verified environment) |
|---|---|---|
| `world-bank` | blocked — 3 conditions | **eligible** |
| `eurostat` | blocked — 3 conditions | **eligible** |
| `fred` | blocked — 3 conditions | blocked — 1 (`fred-api-key`) |
| 10 others | blocked | blocked, unchanged |

**From the catalog alone, zero remain eligible** and always will: a catalog can
never assert its own conditions satisfied. Two views now exist and each says
which it is — the committed `source-catalog-v1.md` shows the catalog view, and
`sros-source eligibility` / the API show the environment view. A committed file
whose contents depended on whether the generating machine had a credential
configured would fail for reasons unrelated to the change under review.

**Eligible is not enabled and neither is implemented.** `collector_enabled` is
false for all thirteen, `IMPLEMENTED_COLLECTORS` is empty, and
`acquisition.raw_records` is empty.

## 11. Tests

`services/acquisition/python/tests`: **127**, up from 68. The new
`test_compliance.py` covers conditions, attribution, dataset scope, secrets,
gates and the recorded verification path.

Three worth naming:

`TestGates.test_authorization_cannot_be_built_for_an_ineligible_source` — the
§27 property across all thirteen sources, asserting in both directions that the
gate and the boundary agree.

`TestConditions.test_satisfying_a_condition_on_a_prohibited_source_changes_nothing`
— every non-approving source is handed a fully satisfied condition set and must
stay blocked by its state. Verification must not become a route around an
approval.

`TestRecordedVerification.test_a_condition_cannot_be_satisfied_without_a_verification`
— the SQL bypass, closed. A manual boolean is refused by the database.

`TestSecrets.test_no_secret_value_appears_in_any_output` sets a sentinel and
searches every verification, the eligibility output and the whole authorization
context for it.

The orchestrator suite gained three tests for the second acquisition gate,
including that a collector for a *different* source unblocks nothing.

## 12. CI

| Job | Added |
|---|---|
| `source-registry` | `validate_compliance_capabilities.py` (zero-dependency); an explicit "no collector exists" check |
| `integration` | `sros-source verify --apply` between `load` and the assertion, so the gate is asserted against the state a real deployment would have |
| `integration` | `FRED_API_KEY` added to the "no credential in CI" check; a new check that `.env.example` holds no value for any credential key |

`assert_registry_grants_nothing.py` was **deliberately updated rather than
relaxed**. Its previous version said: *"If a source genuinely passed review, this
script is the wrong place to change: update the catalog, and update this
expectation deliberately."* This is that update. Three assertions stay absolute
(no collector enabled, no raw record, registry not empty) and two are new: a
condition marked satisfied with no verification behind it, and a source the view
clears while one of its conditions is unsatisfied.

## 13. Database changes

Migration `0007_condition_verification` — one table, one trigger, additive.
Migration 0006 and earlier are untouched, and the eligibility view is not
modified.

The gap was documented before the migration, as the project's convention
requires. `satisfied`, `satisfied_at` and `satisfied_by` answer *is it* and *who
said so*. They cannot answer which verifier decided it, at what version, what it
looked at, why, what the answer was when it was not a clean yes, or what the
previous answer had been. All six are needed the moment a condition can actually
be cleared.

The `no_secret_value` CHECK is worth naming: this is the one table a verifier
writes free text into, so the prohibition is mechanical rather than remembered.

## 14. New issues found

**The planner would have dispatched a job nothing could run.** Making two
sources eligible cleared `acquisition_block`, which returned `None` and made
`acquire.collect` dispatchable — with no collector behind it. It had never been
reachable because no source had ever passed the gate. Fixed by giving
acquisition a second gate, `NO-COLLECTOR-IMPLEMENTED`, with a fail-closed
default; the two are kept distinct because different work clears them.
`PLANNER_VERSION` moved to 1.1.0.

**Six tests were asserting a moment rather than a property.** They passed only
on a database nobody had verified, and failed the first time `verify --apply`
ran. `test_every_condition_is_stored_unsatisfied` was really *"nobody has
verified this database yet"*; the Python-versus-SQL comparisons were evaluating
the same rule on different inputs. Rewritten to derive their expectations, and
`testing-strategy.md` §10 records the pattern. The whole suite now passes both
before and after verification, which was checked in both states.

**A specification bug carried since Mission 1.0.** `source-registry-v1.md`
documented `PersonalDataRisk` as `NONE_EXPECTED / LOW / MEDIUM / HIGH /
UNKNOWN`. That was never the contract vocabulary. Mission 1.3 found and fixed
the same mistake in nine draft reviews; the specification kept it until now.
Corrected, with a note saying so. `SourceAcquisitionCost` had the same problem
(`PAID_ENTERPRISE` for `USAGE_BASED`).

**Two guards now stand where one did.** Mission 1.4's trigger fires before
Mission 1.3's CHECK, so the old provenance test stopped reaching the constraint
it was named after. Both are now asserted, on deterministically chosen rows.

**Nothing else opened.**

## 15. Remaining blockers

| Blocker | Status |
|---|---|
| **No collector exists** | The only thing standing between two eligible sources and data. Mission 1.5 |
| **The collector conformance test** | Owed by Mission 1.5. Until it exists, "the rules are honoured" is architectural, not observed |
| **FRED runtime credential** | `FRED_API_KEY` unconfigured. A deployment decision, not an engineering one |
| **Vendor actions** | 5 sources need a request or application. Unchanged, and none was taken |
| **Eurostat disclaimer wording** | Not in the retrieved evidence. Requires re-reading the notice |
| **Acceding/candidate countries** | Deliberately excluded, stricter than the terms. Widening needs a recorded decision |
| **Calibration** | Open. No `CALIBRATED` profile; production scoring unavailable |
| **D-08** | Open. Recomputation policy |
| **D-12** | Open. No embeddings, no NLP, no semantic deduplication — untouched |
| **A-12** | Open. `MarketScope` untouched |
| **Opportunity identity resolution** | Open |
| **Jurisdiction / GDPR** | Open (H-12). Requires legal input |

## 16. Readiness for Mission 1.5

Ready, with one obligation attached.

The database rebuilds from empty through seven migrations, every gate is green
in both a verified and an unverified state, and two sources have an
authorization context that says precisely what a collector may request, from
which resources, how long it may keep it, what attribution follows it and what
it must not ask for.

**What Mission 1.5 must do beyond writing a collector:** obtain the context from
`build_authorization`, reach every resource through
`context.authorize_resource(...)`, and add the conformance test that it has no
other path to a URL. Without that test the compliance layer is a gate a
collector is trusted to walk through rather than one it cannot walk around.

**What Mission 1.5 may not assume:** that eligible means enabled, that a source
being approved covers all of its datasets, or that a `SATISFIED` capability
condition means anything was observed collecting.

---

## Explicit answers

| Question | Answer |
|---|---|
| Were all nine conditions inventoried? | **Yes**, read from the canonical catalog and database, before any code was written |
| Which are machine-verifiable? | **Eight.** 1–6, 8, 9 |
| Which require human or vendor action? | **None of the nine.** One (7) is configuration-dependent. Eight *related* obligations stay human or legal and are listed in the gap analysis §5 |
| Which capabilities were implemented? | Five registered capabilities plus one access restriction, all named by an actual condition. No unused abstraction, and the validator fails if one appears |
| Can attribution obligations be enforced? | **Yes.** Rendering raises on a missing required element, exact notices are byte-identical and traceable to their evidence, and `derive` cannot drop an obligation |
| Can excluded and third-party datasets fail closed? | **Yes.** `THIRD_PARTY` and `UNKNOWN` origin, unrecorded licences, unstated geographies, unread notes and unclassified datasets are all denied |
| Can credentials be checked without storing them? | **Yes.** Presence and emptiness only; the status object has no field for a value; a sentinel test asserts it appears nowhere |
| Which of World Bank, Eurostat and FRED are now collector-eligible? | **World Bank and Eurostat.** FRED is design-eligible and blocked |
| Why is the remaining approving source still blocked? | `fred-api-key` is `NOT_CONFIGURED`. Exactly one blocking reason |
| Do Python and SQL eligibility agree? | **Yes**, on all 13 sources, with conditions verified on both sides and compared on the same inputs |
| Is `collector_enabled` still false everywhere? | **Yes**, all 13. `sros-source enable` refuses a source with no implemented collector |
| Was any collector implemented? | **No.** No collector module, no data-fetching client, `IMPLEMENTED_COLLECTORS` empty — asserted in CI and in tests |
| Was any external research data fetched? | **No.** `acquisition.raw_records` and `normalized_records` are empty; the package imports no network client |
| Was any condition manually marked satisfied? | **No.** Every satisfied condition has a `SATISFIED` verification record, and the database refuses one without |
| Was a human confirmation fabricated? | **No.** No code path writes one, and the validator probes every source |
| Is production scoring still blocked? | **Yes.** No `CALIBRATED` profile, no `services/scoring` implementation |
| Is D-12 still open? | **Yes.** No embeddings, no NLP, no clustering — untouched |
| Is Mission 1.5 safe to begin? | **Yes**, with the conformance-test obligation in §16 |

## Validation

Against a database **rebuilt from empty**, and run twice — before and after
`verify --apply` — because the eligibility answer is now environment-dependent
and a suite that only passed in one state would be hiding a dependency.

| Check | Result |
|---|---|
| `migrate --apply --seed` from empty | **7 migrations**, 2 seeds; idempotent on a second run |
| `run_python_tests.py` (zero-dependency) | 312 tests, 5 packages |
| `run_pytest_suites.py` | 6 packages, green in **both** states |
| `services/acquisition` suite | **127 tests**, up from 68 |
| `validate_schema.py` | 8 invariant groups, **32 tables** |
| `validate_source_registry.py` | 13 sources, 14 evidence records, 0 warnings |
| `validate_compliance_capabilities.py` | 9 conditions, 5 capabilities, 2 authorizable |
| `validate_evidence_aggregation.py` | 8 checks, 0 warnings; unchanged and uncalibrated |
| `assert_registry_grants_nothing.py` | 13 registered, 2 eligible, **8/9 conditions satisfied and every one verified**, 0 enabled, 0 raw records |
| Python ↔ SQL eligibility | **0 divergences across 13 sources** |
| Review history | 13 current, 13 superseded — unchanged |
| `sros-source render --check`, `render_review_results.py --check`, `sensitivity --check` | in sync |
| `ruff`, `ruff format`, `mypy --strict` | clean; **93 source files** |
| `tsc` ×2, `eslint`, `next build`, TS conformance | clean; 21 + 18 tests |

## Mission boundary

Stopped here, as §45 requires. **Mission 1.5 was not begun.** No collector was
implemented, no external research data was fetched, no condition was marked
satisfied by hand, no human confirmation was fabricated, and no vendor was
contacted.

The honest one-line summary: two sources may now be collected from, nothing can
collect from them, and the reason each of the nine conditions stands where it
does is written down by the program that checked it.
