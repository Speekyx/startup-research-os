# Mission 1.15.6 — TED-EU Authorization Bootstrap & Machine-Verifiable Compliance V1

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.6` · **ADR:** ADR-028

**Success criterion met.** TED under `local-private-research-v1` went from three
outstanding human confirmations to **one**, without a single policy conclusion
moving:

```text
ted-attribution                                 CAPABILITY          SATISFIED
ted-official-route-only                         CAPABILITY          SATISFIED
ted-personal-data-minimisation                  CAPABILITY          SATISFIED
ted-database-right-residual-exposure-accepted   HUMAN_CONFIRMATION  UNKNOWN

build_authorization('ted-eu', 'local-private-research-v1')
  review conditions not satisfied:
    ted-database-right-residual-exposure-accepted
```

**No acceptance was recorded. No collector was written. No TED data was
fetched.**

---

## 0. What the investigation found, up front

Two things, and the second is the one that mattered more than the mission's own
subject.

**The bootstrap was real and it broke in the wrong direction.** Two of TED's
three outstanding conditions described objective properties of a collector that
did not exist, and the readiness document said so plainly: *there is no collector
yet, so there is nothing whose route or field selection a person could confirm*.
A loop with one natural break — write the collector first, confirm it afterwards
— which inverts the order Mission 1.4 built.

**And `context.access` carried every registered access profile.** Not a design
gap noticed in passing: it is what the code did, and TED is the first approving
source with a route its own review refuses by name. Had an authorization been
buildable, the context would have handed a collector `ted-bulk-xml` with its
endpoint — and the transport's host allowlist is derived from `context.access`,
so the refused host would have arrived allowlisted. The existing collector's own
docstring had already named the hazard for GDELT and mitigated it with care
rather than with a mechanism.

The first finding was the brief's. The second was the reason the first mattered.

---

# The §32 questions

## Why was TED APPROVING_BUT_NOT_ELIGIBLE?

Because `APPROVED_WITH_CONDITIONS` says a collector **may be designed**, not that
one may run, and the gate blocks until every condition is satisfied. TED's review
was approving under the local profile and three of its four conditions were
`HUMAN_CONFIRMATION`, which no verifier can clear.

## Which three conditions were outstanding?

`ted-official-route-only`, `ted-personal-data-minimisation`, and
`ted-database-right-residual-exposure-accepted`. `ted-attribution` was already
`SATISFIED` by the `source-attribution-display` capability.

## Which condition is genuinely human?

**One.** `ted-database-right-residual-exposure-accepted`. It is not a property of
anything — it is a person deciding to carry a risk nobody has resolved. The other
two were never about a collector; they are properties of the **configuration
authorization is handed**, and that configuration exists before any code does.

## Did residual database-right acceptance remain HUMAN_CONFIRMATION?

**Yes.** Untouched, on v1 and on v2.

## Was operator acceptance recorded?

**No.** The operator supplied none, so none exists. The condition is outstanding,
TED is ineligible, and the gate refuses by name.

## Can code ever auto-accept that risk?

**No, and it is asserted four ways.** A `HUMAN_CONFIRMATION` condition dispatches
to the human branch *before* any configuration is consulted, so no route
authorization, minimisation profile or capability can reach it. Rewriting the
condition as a `CAPABILITY` naming either new capability makes it answer a
different question rather than this one. The database refuses a hand-set
`satisfied` boolean with no `SATISFIED` verification behind it. And no verifier
in this repository writes one.

**No CLI verb records a human confirmation, and none was built.** A command that
records them is one flag away from a script that records them.

## What exact operator statement will be needed later?

In full, in
[`ted-eu-authorization-bootstrap-v1.md`](../data/ted-eu-authorization-bootstrap-v1.md)
§6.2. Its seven numbered acknowledgements are: both documents read; **H-36A NOT
ESTABLISHED**; **H-36B NOT ADDRESSED**; the approval is deliberately narrow and
none of its four bases is a database-right grant; it further rests on bounded
queries, acquisition-time minimisation and no redistribution, and falls with any
of them; **it is not a legal clearance**; and the exposure is accepted for
`ted-eu` under `local-private-research-v1` at review version 2 **and nothing
else** — not the commercial profile, not a future public deployment, not the bulk
packages, not `ted-csv`, not another source, not a materially changed review.

**Writing that text down is not signing it**, and the existence of this mission
is not acceptance.

## Was `ted-official-route-only` reclassified?

**Yes**, to `CAPABILITY` / `source-route-binding`, on **appended** local review
v2.

## How is the authorized route enforced?

Two halves, and the second is the load-bearing one.

**Verified:** a `route_authorization` per `(source, profile)` names
`allowed_labels`, `blocked_labels`, a `preferred_label` and a `basis`. The
capability asserts the gate accepts the authorised routes — the control case —
and refuses the blocked ones by name, an unreviewed one, and acquisition that
names no route.

**Structural:** `build_authorization` puts **only the authorised routes** into
`context.access`. `ted-bulk-xml` is not in the tuple, so there is no endpoint to
read, no host to allowlist and nothing for the transport to be pointed at. A
collector selecting a route by label — the pattern
`GdeltWebNgramCollector._route` already uses — finds nothing.

**`ACCESS_METHOD` could not carry this, and the reason is worth keeping.** It
passes when the registry records *exactly* the approved access profiles: a
statement about **the source**. TED really is reachable by bulk XML, and making
the check pass would have meant deleting a true row from the registry —
falsifying a fact about a source in order to obtain a permission.

## Was `ted-personal-data-minimisation` reclassified?

**Yes**, to `CAPABILITY` / `source-field-minimisation`, on the same v2.

## How is the field allowlist enforced?

`context.authorize_fields(requested)` refuses: a field in `excluded` **by name**,
a field in neither list, a request stating no selection (`None` or empty), and a
profile that authorises nothing. Asked **before a request is composed**.

`DataMinimisationProfile` had held these categories since Mission 1.4 and
**nothing consulted them**: `permits()` had no caller in the gate.

## Can disallowed personal fields be requested?

**No.** Each excluded category is refused alone *and* when hidden among the
authorised set, which is the shape a real over-broad request has. And this is not
collect-then-filter: the Search API's `fields` parameter makes selection
possible, so a request that discarded the contact block afterwards would have
retrieved it. A test asserts the public callables on `DataMinimisationProfile`
are exactly `{permits, refusals}` — there is no method that strips fields from a
collected record.

## Can bulk XML be configured?

**No.** Blocked by name at the route gate, absent from `context.access`, and
`ted-bulk-xml-daily` / `ted-bulk-xml-monthly` are excluded dataset families at
the resource gate.

## Can historical TED CSV be configured?

**No.** `ted-csv-historical` is an excluded dataset family, `require_dataset_family`
is true so an unclassified resource is denied too, and no route exists for it.

## Can redistribution be enabled?

**No.** `raw_redistribution` is `false` on the local profile, and the review
assesses `redistribution` as `NOT_PERMITTED`. This is the condition that keeps
the Article 7(2)(b) re-utilisation limb structurally unengaged.

## Can model training be enabled?

**No.** `model_training` is `false` on **both** registered profiles, and the
review says model training was not assessed and is not authorised.

## Can embeddings be enabled?

**No.** `embeddings` is `false` on both profiles, and they are blocked
independently by D-12.

## Is Search API the preferred first implementation route?

**Yes**, as `preferred_label`. It is an **implementation preference and never a
permission**: it must name an authorised route, and a `RouteAuthorization` naming
an unauthorised preference is refused at load.

## Is ODS still authorised?

**Yes.** `ted-open-data-sparql` is in `allowed_labels` — and it was **registered
as an access profile** in this mission, because the review authorised a route the
registry had never recorded, so an authorised route had no endpoint, no
rate-limit record and nothing to check a host against.

## Does verification require a network call?

**No.** Both capabilities run against `SourceCompliance` alone. A test asserts no
module under `compliance/` imports a network client, and the compliance validator
pins the boundary at `collection/transport.py`.

## Does verification require an implemented collector?

**No**, and that is the point. It asks about the configuration, not about code.

## How many genuine human decisions remain?

**One.**

## Can `AcquisitionAuthorizationContext` currently be built?

**No.**

## If not, what exact condition remains?

```text
review conditions not satisfied: ted-database-right-residual-exposure-accepted
```

That string, and nothing else, asserted as the complete tuple.

## Were any collectors implemented?

**No.** No TED module, HTTP client, SPARQL client, parser, worker or normalizer —
asserted against the file tree and against `SPARQLWrapper` anywhere outside
tests. `IMPLEMENTED_COLLECTORS` is unchanged at `{world-bank, gdelt}`.

## Was any TED procurement data fetched?

**No.** No notice, award, contract, supplier, buyer or amount. Nothing was
fetched at all.

## Were production research counts unchanged?

**Yes — nothing was written and nothing removed**, confirmed by the suite's own
leak checks across 24 tenant tables and 17 global ones, and by the absence of any
write path in this mission's code.

**But the figures §27 asked me to preserve are not the figures in this
database, and that is worth stating plainly rather than restating them.**

| | §27 expected | Observed here, before and after |
|---|---|---|
| RawRecords | 12 | **0** |
| NormalizedRecords | 12 | **0** |
| Signals | 7 | **0** |
| Claims | 7 | **0** |
| ClaimRevisions | 7 | **0** |
| Evidence | 7 | **0** |
| ReliabilityAssessments · Opportunities · Embeddings · Scores | 0 | 0 |
| **TED rows** | **0** | **0** |

Checked with `row_security = off`, so it is not a row-level-security artefact,
and against every registered workspace.

**Nothing in this mission removed them.** No test asserts those figures and none
ever has — they appear only as prose, carried forward from Mission 1.5 onward.
And `README.md` §*Research data does not travel either* already states the rule
that explains it:

> Collected research is not [governance data]: raw records, normalized records,
> signals, claims and evidence live in whichever local PostgreSQL produced them.
> A second machine has whatever its own database holds, usually nothing. […] It
> matters the day a report states counts: **those numbers describe one database,
> not the repository.**

So the counts describe the database those missions ran in. Reproducing them here
means re-running collection, normalization, derivation and interpretation — and
that is a decision for a mission that says so, not a side effect of this one.

**What this mission needed from the database is true either way**: TED rows are
0, and no `SATISFIED` verification exists for the residual condition.

## Is the full test suite green?

See §3.

## Is the project ready for explicit operator residual-risk acceptance?

**Yes.** Everything an acceptance would need is in place: the statement is
written, the persistence mechanism exists and needed no extension, the scope is
structural rather than conventional, and the three conditions an acceptance would
have had to be taken on trust alongside are now checked.

## After that acceptance, is the next mission TED Official Search API Collector V1?

**Yes**, and not before. `build_authorization` refuses today, so a collector has
nothing to be built against — which is the correct order and the one the
bootstrap was blocking.

---

## 1. Four things worth recording

**The blocker was ours again, and smaller than it looked.** Mission 1.15.4 found
that every approval answered a use case the model did not record. This mission
found the same shape one level down: two conditions were unverifiable not because
the question was hard, but because they had been *written* as questions about
code when they were questions about configuration. Nothing legal moved. The
readiness state changed because the classification was wrong, and it had been
wrong since the review was written.

**The dangerous defect was not the one the brief was about.** The brief asked
whether two conditions could be configuration-verified. Answering it required
looking at what an authorization actually hands a collector, and that is where
`context.access` was carrying every registered route — including one a review
refuses by name. The brief's own §22 described the failure as something to
prevent; it was already possible.

**`AccessRestriction` looked like the answer for an hour.** It is the existing
mechanism, it has the right name, and it verifies routes. It could only have been
made to pass by deleting `ted-bulk-xml` from the registry. That is the shape of
mistake this repository is most exposed to: not inventing a permission, but
quietly editing a *fact* until an existing check returns the desired answer. The
two questions — *how can this source be reached* and *how do we bind to it* — are
both worth asking, and conflating them costs a true row.

**A missing key caught a bug the model had already fixed.** `SourceCompliance`
has been keyed by `(source, profile)` since Mission 1.15.5, and `get` has looked
it up that way since Mission 1.15.5 — but `load_compliance` still deduplicated on
the source alone, so a second profile's entry, which is the entire point of the
key, would have been refused as a duplicate before anything could read it. TED is
the first source that would ever have two. The same shape appeared in the
validator, which walked `source.review` — the legacy profile only — for four of
its eleven checks, and reported this mission's two new capabilities as
*registered but unused* because it could not see the review that names them.

Both are the cost of a migration that changed a key: the places that read it were
updated, and the places that *derive* it were not.

---

## 2. What changed, precisely

| | |
|---|---|
| **Contract** | nothing. `ConditionVerification` still has five values |
| **Schema** | nothing. No migration |
| **Catalog** | `ted-open-data-sparql` access profile added; TED local review **v2** appended. `catalog_version` 1.4 → 1.5 |
| **Compliance** | TED `route_authorization` added; `review_version` 1 → 2. `compliance_version` 1.1 → 1.2 |
| **Code** | `RouteAuthorization`; `DataMinimisationProfile.refusals`; `context.authorize_route` / `authorize_fields` / `authorized_route_labels`; `_reviewed_access`; two capabilities; the loader's dedupe key |
| **Validator** | checks 3, 6, 9 and 10 walk every `(source, profile)` pair; the context's routes are asserted against the review's |
| **Docs** | `ted-eu-authorization-bootstrap-v1.md` (new); ADR-028 (new); readiness, `acquisition-authorization-v1.md`, `source-review-guide.md`, `docs/data/README.md`, `testing-strategy.md` §45–§47, `quality-gates.md`, `docs/CLAUDE.md` 1.31, `PROJECT_MANIFEST.md` 1.30 |
| **Tests** | `test_ted_authorization_bootstrap.py` |

**Deliberately not done:** no route authorization for `world-bank`, `eurostat`,
`fred` or `gdelt` (§21 — a review act, not a configuration edit); no new
`ConditionVerification` value; no CLI verb for human confirmations; no
post-collection field filter; no change to TED's verdicts, assessments, open
questions or evidence.

---

## 3. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | **pass** — 515 tests across 8 packages |
| `validate_schema` | **pass** — 9 invariant groups, 41 tables |
| `validate_source_registry` | **pass** — 29 sources, 42 evidence records, 0 warnings |
| `validate_compliance_capabilities` | **pass** — 16 conditions across 6 approving (source, profile) pairs, 7 capabilities, 3 authorizable |
| `validate_normalization` | **pass** |
| `validate_signals` | **pass** |
| `validate_claims` | **pass** |
| `validate_evidence_aggregation` | **pass** |
| Contract generation `--check` | current |
| Generated catalog documents `--check` | current |
| `ruff format` / `ruff check` | **pass** |
| `mypy` | **pass** — 141 source files |
| Pytest suites | **pass** — all suites across 7 packages, 1068 passed / 9 skipped in the acquisition suite alone. Database unchanged by the run |
| New tests | 67 in `test_ted_authorization_bootstrap.py` |
| Superseded assertions | 4 **rewritten, none deleted** — see §4 |

---

## 4. Four Mission 1.15.5 assertions went red, and every one was right to

They are the mission's own evidence, and `testing-strategy.md` §26 requires
rewriting rather than weakening them.

| Assertion | Why it went red | Rewritten to |
|---|---|---|
| `local == [1]` — the local version line | v2 was appended | `[1, 2]`, **plus** an assertion that the legacy line still ends at 5: appending to one line must never disturb the other |
| the local review is by `mission-1.15.5` | the current local review is v2 | the current review is v2 by `mission-1.15.6`, **and** v1 is still by `mission-1.15.5` with the same verdict — the append-only guarantee tested from both sides |
| the refusal names three human decisions | two were reclassified | the refusal tuple asserted **in full** rather than by substring, so a condition silently leaving the queue fails here — plus a new test that the two left by being *checked*, not excused |
| every registered capability is named by some condition | it walked `source.review`, the legacy profile only | walks every `(source, profile)` pair. The same defect as the validator's, in the test that should have caught the validator's |

The last one is the one worth keeping. **A test and a validator shared a wrong
assumption, so neither could catch the other.** Both read the legacy profile
after Mission 1.15.5 made profiles plural, and both went red on the same day for
the same reason — which is the best outcome available once two checks agree
about something untrue.

---

## 5. Where this leaves TED

**One decision remains, and it is the only one that was ever a decision.**

The two conditions that moved did not move because the standard was lowered. They
moved because they had been filed under *things only a person can establish* when
they belonged under *things a person writes down and a gate checks* — and filing
them wrongly cost a mission of deadlock and would have cost the ordering rule
next.

What is left is a person reading two documents and accepting an exposure that
nobody has resolved, for one source, under one profile, at one review version.
Code cannot help with that, configuration cannot help with that, and this mission
did not try.

**The gate refuses TED today, by name, for the right reason.**
